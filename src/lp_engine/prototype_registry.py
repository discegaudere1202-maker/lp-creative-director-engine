from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


VALID_STAGES = {
    "DRAFT",
    "CRAFT_VERIFIED",
    "BENCHMARK_CHALLENGED",
    "COMPETITIVE",
    "REJECTED",
}


@dataclass
class PrototypeRecord:
    prototype_id: str
    name: str
    principle: str
    target_sales_contexts: list[str] = field(default_factory=list)
    visual_authority: list[str] = field(default_factory=list)
    desktop_verified: bool = False
    mobile_verified: bool = False
    form_causality_verified: bool = False
    benchmark_tournament_status: str = "NOT_RUN"
    benchmark_win_rate: float | None = None
    stage: str = "DRAFT"
    rejection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_prototype(record: PrototypeRecord) -> list[str]:
    issues: list[str] = []
    if not record.prototype_id.strip():
        issues.append("missing prototype_id")
    if not record.name.strip():
        issues.append("missing name")
    if len(record.principle.strip()) < 12:
        issues.append("principle is too vague")
    if not record.target_sales_contexts:
        issues.append("target_sales_contexts is empty")
    if not record.visual_authority:
        issues.append("visual_authority is empty")
    if record.stage not in VALID_STAGES:
        issues.append(f"invalid stage: {record.stage}")

    if record.stage in {"CRAFT_VERIFIED", "BENCHMARK_CHALLENGED", "COMPETITIVE"}:
        if not record.desktop_verified:
            issues.append(f"{record.stage} requires desktop_verified=true")
        if not record.mobile_verified:
            issues.append(f"{record.stage} requires mobile_verified=true")
        if not record.form_causality_verified:
            issues.append(f"{record.stage} requires form_causality_verified=true")

    if record.stage in {"BENCHMARK_CHALLENGED", "COMPETITIVE"}:
        if record.benchmark_tournament_status == "NOT_RUN":
            issues.append(f"{record.stage} requires a benchmark tournament")

    if record.stage == "COMPETITIVE":
        if record.benchmark_tournament_status != "PASS":
            issues.append("COMPETITIVE requires tournament PASS")
        if record.benchmark_win_rate is None or record.benchmark_win_rate < 0.60:
            issues.append("COMPETITIVE requires benchmark_win_rate >= 0.60")

    if record.stage == "REJECTED" and not record.rejection_reason.strip():
        issues.append("REJECTED requires rejection_reason")

    return issues


def audit_prototypes(records: list[PrototypeRecord]) -> dict[str, Any]:
    ids = [r.prototype_id for r in records]
    duplicates = sorted({x for x in ids if ids.count(x) > 1})
    rows: list[dict[str, Any]] = []
    counts = {stage: 0 for stage in VALID_STAGES}
    valid = 0

    for record in records:
        issues = validate_prototype(record)
        counts[record.stage] = counts.get(record.stage, 0) + 1
        if not issues:
            valid += 1
        rows.append({
            "prototype_id": record.prototype_id,
            "stage": record.stage,
            "valid": not issues,
            "issues": issues,
        })

    return {
        "status": "PASS" if valid == len(records) and not duplicates else "REVIEW",
        "total": len(records),
        "valid": valid,
        "counts": counts,
        "duplicate_ids": duplicates,
        "golden_sample_importable": [
            r.prototype_id
            for r in records
            if r.stage == "COMPETITIVE" and not validate_prototype(r)
        ],
        "records": rows,
        "rule": "Only COMPETITIVE prototypes may be imported into new Golden Samples as validated craft patterns.",
    }
