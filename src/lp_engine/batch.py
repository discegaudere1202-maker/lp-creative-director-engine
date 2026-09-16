"""Phase 5 batch-generation contract.

The module is deliberately persistence-light: a JSON registry is enough for
the reference implementation, while the boundaries are suitable for a DB or
queue later.  Every item owns its input snapshot, output directory, state,
IDs, retry audit, and quality result.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Callable, Mapping
from uuid import uuid4

BATCH_STATES = ("QUEUED", "RUNNING", "COMPLETED", "HOLD", "BLOCKED", "FAILED", "RETRY_PENDING", "CANCELLED")
FAILURE_TYPES = ("INPUT_ERROR", "RESEARCH_ERROR", "SAFETY_BLOCK", "RIGHTS_BLOCK", "GENERATION_ERROR", "RENDER_ERROR", "QA_ERROR", "BROWSER_ERROR", "REGISTRY_ERROR", "UNKNOWN")
RETRYABLE = {"GENERATION_ERROR", "RENDER_ERROR", "BROWSER_ERROR", "REGISTRY_ERROR"}
QUALITY_AXES = ("Immediate Read", "Distinctness", "Owner Specificity", "Visual Hierarchy", "Craft Detail", "Emotional Pull", "Trust", "Share Impulse", "Mobile Quality", "Conversion Intent")

def _now() -> str:
    return datetime.now(UTC).isoformat()

def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"

def _digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(raw.encode()).hexdigest()

class BatchError(RuntimeError): pass
class InvalidBatch(BatchError): pass
class TransientBatchError(BatchError):
    def __init__(self, message: str, failure_type: str = "GENERATION_ERROR"):
        super().__init__(message); self.failure_type = failure_type
class DeterministicBatchError(BatchError):
    def __init__(self, message: str, failure_type: str = "UNKNOWN", status: str = "BLOCKED"):
        super().__init__(message); self.failure_type = failure_type; self.status = status

@dataclass(frozen=True)
class BatchInput:
    batch_id: str
    item_id: str
    company_id: str
    company_name: str
    source_urls: tuple[str, ...]
    industry: str
    location: str
    conversion_goal: str
    evidence_density: str
    input_version: str = "batch-input-v1"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass
class BatchItem:
    item_id: str
    company_id: str
    company_name: str
    state: str = "QUEUED"
    project_id: str = ""
    generation_id: str = ""
    artifact_id: str = ""
    output_dir: str = ""
    failure_type: str | None = None
    error: str | None = None
    retry_count: int = 0
    retry_audit: list[dict[str, Any]] = field(default_factory=list)
    quality: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    qa: dict[str, Any] = field(default_factory=dict)
    checkpoint_at: str | None = None
    updated_at: str = field(default_factory=_now)

@dataclass
class BatchManifest:
    batch_id: str
    requested_count: int
    actual_count: int
    engine_version: str
    schema_version: str = "phase5-batch-v1"
    state: str = "QUEUED"
    start_time: str | None = None
    end_time: str | None = None
    success_count: int = 0
    hold_count: int = 0
    blocked_count: int = 0
    failed_count: int = 0
    retry_count: int = 0
    browser_qa_count: int = 0
    manual_intervention: int = 0
    external_production_changes: int = 0
    metrics: dict[str, Any] = field(default_factory=dict)

class BatchRegistry:
    """Thread-safe JSON checkpoint registry; one directory per batch/item."""
    def __init__(self, root: str | Path):
        self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.manifest: BatchManifest | None = None
        self.inputs: dict[str, BatchInput] = {}
        self.items: dict[str, BatchItem] = {}

    def _path(self, name: str) -> Path: return self.root / name
    def initialize(self, manifest: BatchManifest, inputs: list[BatchInput]) -> None:
        with self._lock:
            if self.manifest and self.manifest.batch_id == manifest.batch_id:
                if set(self.inputs) != {x.item_id for x in inputs}: raise InvalidBatch("existing batch input set differs")
                return
            if self.manifest: raise InvalidBatch("registry already contains another batch")
            seen: set[str] = set(); company_keys: set[str] = set()
            for item in inputs:
                if item.batch_id != manifest.batch_id or not item.item_id or not item.company_id: raise InvalidBatch("invalid batch input")
                key = item.company_id.lower()
                if item.item_id in seen or key in company_keys: raise InvalidBatch("duplicate item or company")
                seen.add(item.item_id); company_keys.add(key)
            self.manifest = manifest; self.inputs = {x.item_id: x for x in inputs}
            self.items = {x.item_id: BatchItem(x.item_id, x.company_id, x.company_name) for x in inputs}
            self._save()

    def load(self, batch_id: str) -> None:
        with self._lock:
            raw = json.loads(self._path("registry.json").read_text())
            if raw["manifest"]["batch_id"] != batch_id: raise InvalidBatch("batch id mismatch")
            self.manifest = BatchManifest(**raw["manifest"])
            self.inputs = {k: BatchInput(**v) for k, v in raw["inputs"].items()}
            self.items = {k: BatchItem(**v) for k, v in raw["items"].items()}

    def _save(self) -> None:
        payload = {"manifest": asdict(self.manifest), "inputs": {k: asdict(v) for k, v in self.inputs.items()}, "items": {k: asdict(v) for k, v in self.items.items()}}
        tmp = self._path("registry.json.tmp"); tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n"); tmp.replace(self._path("registry.json"))

    def checkpoint(self, item: BatchItem) -> None:
        with self._lock:
            item.checkpoint_at = _now(); item.updated_at = item.checkpoint_at; self.items[item.item_id] = item; self._save()

    def summary(self) -> dict[str, Any]:
        counts = {state: sum(x.state == state for x in self.items.values()) for state in BATCH_STATES}
        return {"batch_id": self.manifest.batch_id, "counts": counts, "items": {k: asdict(v) for k, v in self.items.items()}}

Processor = Callable[[BatchInput, Path], Mapping[str, Any]]
BrowserQA = Callable[[BatchInput, Path], Mapping[str, Any]]

def _validate(inputs: list[BatchInput], batch_id: str, requested: int) -> None:
    if not inputs or len(inputs) != requested: raise InvalidBatch("requested count and inputs differ")
    if len({x.item_id for x in inputs}) != len(inputs) or len({x.company_id.lower() for x in inputs}) != len(inputs): raise InvalidBatch("duplicate batch identity")
    if any(x.batch_id != batch_id for x in inputs): raise InvalidBatch("input batch_id mismatch")

def run_batch(*, batch_id: str, inputs: list[BatchInput], registry: BatchRegistry, processor: Processor, engine_version: str, requested_count: int | None = None, max_retries: int = 1, concurrency: int = 1, browser_qa: BrowserQA | None = None, stop_after: int | None = None) -> BatchManifest:
    requested_count = requested_count or len(inputs); _validate(inputs, batch_id, requested_count)
    registry.initialize(BatchManifest(batch_id, requested_count, len(inputs), engine_version), inputs)
    manifest = registry.manifest; assert manifest
    manifest.state = "RUNNING"; manifest.start_time = manifest.start_time or _now(); registry._save()
    pending = [x for x in inputs if registry.items[x.item_id].state not in {"COMPLETED", "HOLD", "BLOCKED", "CANCELLED"}]
    if stop_after is not None: pending = pending[:stop_after]

    def one(inp: BatchInput) -> BatchItem:
        item = registry.items[inp.item_id]
        if item.state in {"COMPLETED", "HOLD", "BLOCKED"}: return item
        item.state = "RUNNING"; item.project_id = f"project_{inp.company_id}"; item.output_dir = str(registry.root / inp.item_id); registry.checkpoint(item)
        while True:
            try:
                result = dict(processor(inp, Path(item.output_dir)))
                item.generation_id = str(result.get("generation_id", _id("generation"))); item.artifact_id = str(result.get("artifact_id", _id("artifact")))
                item.safety = dict(result.get("safety", {"status": "PASS"})); item.qa = dict(result.get("qa", {"status": "PASS"})); item.quality = dict(result.get("quality", {}))
                item.state = str(result.get("state", "COMPLETED")); item.failure_type = None; item.error = None
                if browser_qa: item.qa["browser"] = dict(browser_qa(inp, Path(item.output_dir))); item.qa["browser"]["status"] = item.qa["browser"].get("status", "PASS")
                registry.checkpoint(item); return item
            except TransientBatchError as exc:
                item.retry_count += 1; item.retry_audit.append({"reason": str(exc), "failure_type": exc.failure_type, "retry_count": item.retry_count, "at": _now()}); manifest.retry_count += 1
                if item.retry_count > max_retries:
                    item.state = "FAILED"; item.failure_type = exc.failure_type; item.error = str(exc); registry.checkpoint(item); return item
                item.state = "RETRY_PENDING"; registry.checkpoint(item)
            except DeterministicBatchError as exc:
                item.state = exc.status; item.failure_type = exc.failure_type; item.error = str(exc); registry.checkpoint(item); return item
            except Exception as exc:
                item.state = "FAILED"; item.failure_type = "UNKNOWN"; item.error = repr(exc); registry.checkpoint(item); return item

    if concurrency <= 1:
        for inp in pending: one(inp)
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(one, inp) for inp in pending]
            for future in as_completed(futures): future.result()
    counts = {state: sum(x.state == state for x in registry.items.values()) for state in BATCH_STATES}
    manifest.success_count = counts["COMPLETED"]; manifest.hold_count = counts["HOLD"]; manifest.blocked_count = counts["BLOCKED"]; manifest.failed_count = counts["FAILED"]
    incomplete = counts["QUEUED"] + counts["RUNNING"] + counts["RETRY_PENDING"]
    manifest.state = "RUNNING" if incomplete else ("FAILED" if manifest.failed_count else ("HOLD" if manifest.hold_count or manifest.blocked_count else "COMPLETED")); manifest.end_time = None if incomplete else _now()
    manifest.browser_qa_count = sum(bool(x.qa.get("browser")) for x in registry.items.values()); registry._save(); return manifest

def aggregate_quality(registry: BatchRegistry) -> dict[str, Any]:
    completed = [x for x in registry.items.values() if x.state == "COMPLETED"]
    scores = [float(x.quality.get("premium_score", 0)) for x in completed if "premium_score" in x.quality]
    profiles: dict[str, int] = {}; evidence: dict[str, int] = {}
    for x in completed:
        profiles[str(x.quality.get("layout_profile", "unknown"))] = profiles.get(str(x.quality.get("layout_profile", "unknown")), 0) + 1
        key = str(registry.inputs[x.item_id].evidence_density); evidence[key] = evidence.get(key, 0) + 1
    return {"total": len(registry.items), "completed": len(completed), "hold": sum(x.state == "HOLD" for x in registry.items.values()), "blocked": sum(x.state == "BLOCKED" for x in registry.items.values()), "failed": sum(x.state == "FAILED" for x in registry.items.values()), "average_premium_score": sum(scores) / len(scores) if scores else 0, "premium_pass_rate": sum(s >= 4.0 for s in scores) / len(scores) if scores else 0, "design_profiles": profiles, "evidence_density": evidence, "browser_qa": sum(bool(x.qa.get("browser", {}).get("status") == "PASS") for x in registry.items.values())}
