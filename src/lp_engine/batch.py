"""Failure-isolated batch orchestration for Production Generation.

Phase 4 owns one project's lifecycle.  This module owns the boundary around
many projects: input validation, deduplication, durable checkpoints,
idempotent item processing, bounded retries, and aggregate quality reporting.
It deliberately does not loosen the generation, Safety, rights, or QA gates.

The registry is a small JSON reference implementation.  It is restartable and
provider-neutral; a database can replace it later without changing the item
contract or the orchestrator's invariants.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import threading
import time
from typing import Any, Callable, Iterable, Mapping
from uuid import uuid4


BATCH_SCHEMA_VERSION = "batch_generation_v1"
BATCH_ENGINE_CONTRACT_VERSION = "phase5_batch_contract_v1"
RUBRIC_VERSION = "structured_review_roles_v1"

BATCH_STATES = ("QUEUED", "RUNNING", "COMPLETED", "HOLD", "BLOCKED", "FAILED", "RETRY_PENDING", "CANCELLED")
ITEM_STATES = ("QUEUED", "RUNNING", "COMPLETED", "HOLD", "BLOCKED", "FAILED", "RETRY_PENDING", "CANCELLED")
FAILURE_TYPES = (
    "INPUT_ERROR", "RESEARCH_ERROR", "SAFETY_BLOCK", "RIGHTS_BLOCK",
    "GENERATION_ERROR", "RENDER_ERROR", "QA_ERROR", "BROWSER_ERROR",
    "REGISTRY_ERROR", "UNKNOWN",
)
RETRYABLE_FAILURES = {"GENERATION_ERROR", "RENDER_ERROR", "BROWSER_ERROR", "REGISTRY_ERROR"}
NON_RETRYABLE_FAILURES = {"INPUT_ERROR", "RESEARCH_ERROR", "SAFETY_BLOCK", "RIGHTS_BLOCK", "QA_ERROR"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def _digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


class BatchError(RuntimeError):
    """Base class for a batch contract error."""


class BatchValidationError(BatchError):
    """The batch input is invalid or contains duplicates."""


class BatchProcessingError(BatchError):
    """A classified item failure; deterministic blocks are never retried."""

    def __init__(self, message: str, failure_type: str, *, retryable: bool | None = None, terminal_state: str = "FAILED"):
        if failure_type not in FAILURE_TYPES:
            raise ValueError(f"unsupported failure type: {failure_type}")
        self.failure_type = failure_type
        self.retryable = failure_type in RETRYABLE_FAILURES if retryable is None else retryable
        self.terminal_state = terminal_state
        super().__init__(message)


@dataclass
class BatchItem:
    batch_id: str
    item_id: str
    company_id: str
    company_name: str
    source_urls: list[str]
    industry: str
    location: str
    conversion_goal: str
    evidence_density: str
    input_version: str
    input_payload: dict[str, Any]
    test_only: bool = False
    status: str = "QUEUED"
    project_id: str | None = None
    generation_id: str | None = None
    output_dir: str | None = None
    attempts: int = 0
    retry_count: int = 0
    retry_audit: list[dict[str, Any]] = field(default_factory=list)
    failure_type: str | None = None
    last_error: str | None = None
    project_status: str | None = None
    safety_status: str | None = None
    rights_status: str | None = None
    qa_status: str | None = None
    browser_qa_status: str | None = None
    browser_qa_mode: str | None = None
    quality: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    artifact_ids: list[str] = field(default_factory=list)
    completed_at: str | None = None
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BatchJob:
    batch_id: str
    requested_count: int
    items: list[str]
    engine_version: str
    schema_version: str = BATCH_SCHEMA_VERSION
    status: str = "QUEUED"
    actual_count: int = 0
    start_time: str | None = None
    end_time: str | None = None
    success_count: int = 0
    hold_count: int = 0
    blocked_count: int = 0
    failed_count: int = 0
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    stage_reports: list[dict[str, Any]] = field(default_factory=list)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BatchRegistry:
    """Durable JSON registry with one atomic checkpoint per item update."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.batches_dir = self.root / "batches"
        self.batches_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _batch_dir(self, batch_id: str) -> Path:
        return self.batches_dir / batch_id

    def _job_path(self, batch_id: str) -> Path:
        return self._batch_dir(batch_id) / "batch.json"

    def _item_path(self, batch_id: str, item_id: str) -> Path:
        return self._batch_dir(batch_id) / "items" / f"{item_id}.json"

    def _write_atomic(self, path: Path, value: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)

    def create(self, job: BatchJob, items: Iterable[BatchItem]) -> BatchJob:
        items = list(items)
        with self._lock:
            existing = self.load_job(job.batch_id)
            if existing:
                old_items = {item.item_id: item for item in self.load_items(job.batch_id)}
                new_items = {item.item_id: item for item in items}
                if existing.to_dict() and {key: _digest(value.input_payload) for key, value in old_items.items()} != {key: _digest(value.input_payload) for key, value in new_items.items()}:
                    raise BatchValidationError(f"batch_id already exists with different inputs: {job.batch_id}")
                return existing
            job.actual_count = len(items)
            self._write_atomic(self._job_path(job.batch_id), job.to_dict())
            for item in items:
                self._write_atomic(self._item_path(job.batch_id, item.item_id), item.to_dict())
            return deepcopy(job)

    def load_job(self, batch_id: str) -> BatchJob | None:
        path = self._job_path(batch_id)
        if not path.exists():
            return None
        return BatchJob(**json.loads(path.read_text(encoding="utf-8")))

    def load_item(self, batch_id: str, item_id: str) -> BatchItem:
        path = self._item_path(batch_id, item_id)
        if not path.exists():
            raise BatchError(f"unknown batch item: {batch_id}/{item_id}")
        return BatchItem(**json.loads(path.read_text(encoding="utf-8")))

    def load_items(self, batch_id: str) -> list[BatchItem]:
        job = self.load_job(batch_id)
        if not job:
            raise BatchError(f"unknown batch: {batch_id}")
        return [self.load_item(batch_id, item_id) for item_id in job.items]

    def save_job(self, job: BatchJob) -> None:
        with self._lock:
            job.updated_at = _now()
            self._write_atomic(self._job_path(job.batch_id), job.to_dict())

    def save_item(self, item: BatchItem) -> None:
        with self._lock:
            item.updated_at = _now()
            self._write_atomic(self._item_path(item.batch_id, item.item_id), item.to_dict())

    def checkpoint(self, batch_id: str, *, item: BatchItem | None = None, job: BatchJob | None = None) -> None:
        with self._lock:
            if item:
                self.save_item(item)
            if job:
                self.save_job(job)

    def recover(self, batch_id: str) -> dict[str, Any]:
        job = self.load_job(batch_id)
        if not job:
            raise BatchError(f"unknown batch: {batch_id}")
        items = self.load_items(batch_id)
        return {"job": job.to_dict(), "items": [item.to_dict() for item in items], "recovered_at": _now()}


def validate_batch_items(items: Iterable[BatchItem]) -> list[BatchItem]:
    items = list(items)
    if not items:
        raise BatchValidationError("batch must contain at least one item")
    seen: dict[str, str] = {}
    for item in items:
        if item.status not in ITEM_STATES:
            raise BatchValidationError(f"invalid item state: {item.item_id}/{item.status}")
        for field_name in ("batch_id", "item_id", "company_id", "company_name", "industry", "location", "conversion_goal", "evidence_density", "input_version"):
            if not str(getattr(item, field_name, "")).strip():
                raise BatchValidationError(f"{item.item_id}: missing {field_name}")
        if item.evidence_density not in {"LOW", "MEDIUM", "HIGH"}:
            raise BatchValidationError(f"{item.item_id}: invalid evidence_density")
        if not item.source_urls:
            raise BatchValidationError(f"{item.item_id}: source_urls must not be empty")
        if not isinstance(item.input_payload, dict):
            raise BatchValidationError(f"{item.item_id}: input_payload must be an object")
        identity_values = {
            "company_id": _norm(item.company_id),
            "company_name": _norm(item.company_name),
            "location": _norm(item.location),
            "source_url": _norm(item.source_urls[0]),
        }
        for identity, value in identity_values.items():
            if not value:
                continue
            if value in seen and seen[value] != item.item_id:
                raise BatchValidationError(f"duplicate {identity}: {item.item_id} and {seen[value]}")
            seen[value] = item.item_id
        if _norm(item.input_payload.get("company_id")) != _norm(item.company_id):
            raise BatchValidationError(f"{item.item_id}: input company_id does not match batch item")
        payload_company = item.input_payload.get("company") or {}
        if _norm(payload_company.get("company_name")) != _norm(item.company_name):
            raise BatchValidationError(f"{item.item_id}: input company_name does not match batch item")
    return items


def _classify_exception(exc: Exception) -> BatchProcessingError:
    if isinstance(exc, BatchProcessingError):
        return exc
    return BatchProcessingError(str(exc) or exc.__class__.__name__, "UNKNOWN", retryable=False)


class BatchOrchestrator:
    """Run isolated items with durable checkpoints and bounded retries."""

    def __init__(
        self,
        registry: BatchRegistry,
        processor: Callable[[BatchItem, Path, int], Mapping[str, Any]],
        *,
        engine_version: str = "unknown",
        max_retries: int = 2,
        max_workers: int = 1,
    ):
        if max_retries < 0 or max_workers < 1:
            raise ValueError("max_retries must be >= 0 and max_workers must be >= 1")
        self.registry = registry
        self.processor = processor
        self.engine_version = engine_version
        self.max_retries = max_retries
        self.max_workers = max_workers

    def create_batch(self, batch_id: str, items: Iterable[BatchItem], *, metadata: Mapping[str, Any] | None = None) -> BatchJob:
        items = validate_batch_items(items)
        if any(item.batch_id != batch_id for item in items):
            raise BatchValidationError("all items must use the requested batch_id")
        job = BatchJob(batch_id=batch_id, requested_count=len(items), items=[item.item_id for item in items], engine_version=self.engine_version, metadata=dict(metadata or {}))
        return self.registry.create(job, items)

    def _process_one(self, batch_id: str, item_id: str) -> BatchItem:
        item = self.registry.load_item(batch_id, item_id)
        if item.status in {"COMPLETED", "HOLD", "BLOCKED", "CANCELLED"}:
            return item
        while True:
            item = self.registry.load_item(batch_id, item_id)
            item.status = "RUNNING"
            item.attempts += 1
            self.registry.save_item(item)
            started = time.monotonic()
            attempt = item.attempts
            output_dir = self.registry._batch_dir(batch_id) / "items" / item_id / f"attempt-{attempt}"
            try:
                result = dict(self.processor(deepcopy(item), output_dir, attempt))
                status = str(result.get("status", "COMPLETED"))
                if status not in {"COMPLETED", "HOLD", "BLOCKED"}:
                    raise BatchProcessingError(f"processor returned invalid terminal status: {status}", "UNKNOWN")
                item.status = status
                item.output_dir = str(output_dir)
                item.generation_id = result.get("generation_id", item.generation_id)
                item.project_id = result.get("project_id", item.project_id)
                item.project_status = result.get("project_status", item.project_status)
                item.safety_status = result.get("safety_status", item.safety_status)
                item.rights_status = result.get("rights_status", item.rights_status)
                item.qa_status = result.get("qa_status", item.qa_status)
                item.browser_qa_status = result.get("browser_qa_status", item.browser_qa_status)
                item.browser_qa_mode = result.get("browser_qa_mode", item.browser_qa_mode)
                item.quality = dict(result.get("quality") or {})
                item.metrics = {**item.metrics, **dict(result.get("metrics") or {}), "item_duration_seconds": round(time.monotonic() - started, 4)}
                item.artifact_ids = list(result.get("artifact_ids") or item.artifact_ids)
                item.failure_type = result.get("failure_type")
                item.last_error = result.get("last_error")
                item.completed_at = _now()
                self.registry.save_item(item)
                return item
            except Exception as raw_exc:
                exc = _classify_exception(raw_exc)
                item.last_error = str(exc)
                item.failure_type = exc.failure_type
                retry_record = {"attempt": attempt, "reason": str(exc), "failure_type": exc.failure_type, "retryable": exc.retryable, "timestamp": _now()}
                if exc.retryable and item.retry_count < self.max_retries:
                    item.retry_count += 1
                    item.status = "RETRY_PENDING"
                    item.retry_audit.append(retry_record)
                    item.metrics = {**item.metrics, "last_attempt_duration_seconds": round(time.monotonic() - started, 4)}
                    self.registry.save_item(item)
                    continue
                item.status = exc.terminal_state if exc.terminal_state in {"HOLD", "BLOCKED", "FAILED"} else "FAILED"
                item.retry_audit.append(retry_record)
                item.completed_at = _now()
                item.metrics = {**item.metrics, "item_duration_seconds": round(time.monotonic() - started, 4)}
                self.registry.save_item(item)
                return item

    def _refresh_job(self, job: BatchJob) -> BatchJob:
        items = self.registry.load_items(job.batch_id)
        job.actual_count = len(items)
        job.success_count = sum(item.status == "COMPLETED" for item in items)
        job.hold_count = sum(item.status == "HOLD" for item in items)
        job.blocked_count = sum(item.status == "BLOCKED" for item in items)
        job.failed_count = sum(item.status == "FAILED" for item in items)
        job.retry_count = sum(item.retry_count for item in items)
        if any(item.status == "FAILED" for item in items):
            job.status = "FAILED"
        elif any(item.status in {"QUEUED", "RUNNING", "RETRY_PENDING"} for item in items):
            job.status = "RUNNING"
        elif any(item.status == "HOLD" for item in items):
            job.status = "HOLD"
        elif any(item.status == "BLOCKED" for item in items):
            job.status = "BLOCKED"
        else:
            job.status = "COMPLETED"
        job.updated_at = _now()
        self.registry.save_job(job)
        return job

    def run_batch(self, batch_id: str, *, item_ids: Iterable[str] | None = None, resume: bool = True) -> dict[str, Any]:
        job = self.registry.load_job(batch_id)
        if not job:
            raise BatchError(f"unknown batch: {batch_id}")
        if not job.start_time:
            job.start_time = _now()
        job.status = "RUNNING"
        self.registry.save_job(job)
        requested = list(item_ids or job.items)
        unknown = sorted(set(requested) - set(job.items))
        if unknown:
            raise BatchValidationError("unknown item ids: " + ", ".join(unknown))
        todo = []
        for item_id in requested:
            item = self.registry.load_item(batch_id, item_id)
            if resume and item.status in {"COMPLETED", "HOLD", "BLOCKED", "CANCELLED"}:
                continue
            todo.append(item_id)
        if self.max_workers == 1:
            for item_id in todo:
                self._process_one(batch_id, item_id)
        else:
            with ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="lp-batch") as pool:
                futures = [pool.submit(self._process_one, batch_id, item_id) for item_id in todo]
                for future in as_completed(futures):
                    future.result()
        job = self._refresh_job(job)
        if job.status in {"COMPLETED", "HOLD", "BLOCKED", "FAILED"}:
            job.end_time = _now()
            self.registry.save_job(job)
        return self.report(batch_id)

    def retry_items(self, batch_id: str, item_ids: Iterable[str]) -> dict[str, Any]:
        selected = list(item_ids)
        for item_id in selected:
            item = self.registry.load_item(batch_id, item_id)
            if item.status != "FAILED":
                raise BatchValidationError(f"only FAILED items can be targeted for retry: {item_id}/{item.status}")
            item.status = "QUEUED"
            item.failure_type = None
            item.last_error = None
            item.completed_at = None
            self.registry.save_item(item)
        return self.run_batch(batch_id, item_ids=selected, resume=False)

    def cancel_batch(self, batch_id: str) -> dict[str, Any]:
        job = self.registry.load_job(batch_id)
        if not job:
            raise BatchError(f"unknown batch: {batch_id}")
        for item in self.registry.load_items(batch_id):
            if item.status in {"QUEUED", "RETRY_PENDING"}:
                item.status = "CANCELLED"
                item.completed_at = _now()
                self.registry.save_item(item)
        job = self._refresh_job(job)
        job.status = "CANCELLED"
        job.end_time = _now()
        self.registry.save_job(job)
        return self.report(batch_id)

    def audit_isolation(self, batch_id: str) -> dict[str, Any]:
        items = self.registry.load_items(batch_id)
        errors: list[str] = []
        ids: dict[str, str] = {}
        for item in items:
            if item.status not in {"COMPLETED", "HOLD", "BLOCKED"} or not item.output_dir:
                continue
            manifest_path = Path(item.output_dir) / "generation_manifest.json"
            if not manifest_path.exists():
                errors.append(f"{item.item_id}: generation_manifest.json missing")
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if _norm(manifest.get("company_id")) != _norm(item.company_id):
                errors.append(f"{item.item_id}: output company_id mismatch")
            for evidence in manifest.get("evidence_used", []):
                if _norm(evidence.get("company_id")) not in {"", _norm(item.company_id)}:
                    errors.append(f"{item.item_id}: cross-project evidence company_id {evidence.get('company_id')}")
                evidence_id = str(evidence.get("evidence_id", ""))
                if evidence_id:
                    if evidence_id in ids and ids[evidence_id] != item.item_id:
                        errors.append(f"evidence id collision: {evidence_id}")
                    ids[evidence_id] = item.item_id
            html_path = Path(item.output_dir) / "index.html"
            if html_path.exists():
                html = html_path.read_text(encoding="utf-8")
                other_names = {other.company_name for other in items if other.item_id != item.item_id}
                for name in other_names:
                    if name and name in html:
                        errors.append(f"{item.item_id}: other company name leaked: {name}")
        project_ids = [item.project_id for item in items if item.project_id]
        generation_ids = [item.generation_id for item in items if item.generation_id]
        if len(project_ids) != len(set(project_ids)):
            errors.append("project_id collision")
        if len(generation_ids) != len(set(generation_ids)):
            errors.append("generation_id collision")
        return {"status": "PASS" if not errors else "FAIL", "errors": errors, "checked_items": len(items), "evidence_ids": len(ids)}

    def report(self, batch_id: str) -> dict[str, Any]:
        job = self.registry.load_job(batch_id)
        if not job:
            raise BatchError(f"unknown batch: {batch_id}")
        items = self.registry.load_items(batch_id)
        axes = ("Immediate Read", "Distinctness", "Owner Specificity", "Visual Hierarchy", "Craft Detail", "Emotional Pull", "Trust", "Share Impulse", "Mobile Quality", "Conversion Intent")
        scores = {axis: [] for axis in axes}
        profiles: dict[str, int] = {}
        densities: dict[str, int] = {}
        failures: dict[str, int] = {}
        browser = {"PASS": 0, "FAIL": 0, "PENDING": 0}
        premium: dict[str, int] = {}
        for item in items:
            densities[item.evidence_density] = densities.get(item.evidence_density, 0) + 1
            profile = str(item.quality.get("layout_profile") or item.metrics.get("layout_profile") or "UNKNOWN")
            profiles[profile] = profiles.get(profile, 0) + 1
            gate = str(item.quality.get("sales_sample_gate") or "UNKNOWN")
            premium[gate] = premium.get(gate, 0) + 1
            for axis in axes:
                value = item.quality.get("creative_scores", {}).get(axis)
                if isinstance(value, (int, float)):
                    scores[axis].append(value)
            if item.failure_type:
                failures[item.failure_type] = failures.get(item.failure_type, 0) + 1
            if item.browser_qa_status in {"PASS", "FAIL"}:
                browser[item.browser_qa_status] += 1
            else:
                browser["PENDING"] += 1
        averages = {axis: round(sum(values) / len(values), 2) if values else None for axis, values in scores.items()}
        drift: dict[str, dict[str, Any]] = {}
        for start in range(0, len(items), 20):
            window = items[start:start + 20]
            drift[f"{start + 1}-{start + len(window)}"] = {
                "count": len(window),
                "average_axes": {
                    axis: round(sum(float(item.quality.get("creative_scores", {}).get(axis, 0)) for item in window) / len(window), 2) if window and any(axis in item.quality.get("creative_scores", {}) for item in window) else None
                    for axis in ("Distinctness", "Owner Specificity", "Trust", "Mobile Quality", "Conversion Intent")
                },
                "premium_gate": {gate: sum(item.quality.get("sales_sample_gate") == gate for item in window) for gate in ("PASS", "HOLD", "FAIL")},
            }
        isolation = self.audit_isolation(batch_id)
        return {
            "schema_version": BATCH_SCHEMA_VERSION,
            "batch_id": batch_id,
            "status": job.status,
            "manifest": job.to_dict(),
            "items": [item.to_dict() for item in items],
            "failure_taxonomy": failures,
            "quality": {"average_axes": averages, "premium_gate": premium, "evidence_density": densities, "layout_profiles": profiles, "drift_windows": drift},
            "browser_qa": browser,
            "isolation": isolation,
            "manual_intervention": sum(len(item.metrics.get("manual_intervention", [])) for item in items),
            "external_production_changes": 0,
            "generated_at": _now(),
        }


__all__ = [
    "BATCH_ENGINE_CONTRACT_VERSION", "BATCH_SCHEMA_VERSION", "BATCH_STATES", "BatchError", "BatchItem", "BatchJob", "BatchOrchestrator", "BatchProcessingError", "BatchRegistry", "BatchValidationError", "FAILURE_TYPES", "ITEM_STATES", "NON_RETRYABLE_FAILURES", "RETRYABLE_FAILURES", "RUBRIC_VERSION", "validate_batch_items",
]
