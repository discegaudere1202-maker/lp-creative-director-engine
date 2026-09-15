from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_STAGES = {"CANDIDATE", "VERIFIED", "CORE", "REJECTED"}
VALID_MOBILE_GRADES = {"M0", "M1", "M2", "M3"}


@dataclass
class FrameRecord:
    frame_id: str
    site_name: str
    source_url: str
    frame_role: str
    visual_authority: list[str]
    lesson: str
    transfer_to_sales_sample: str
    source_support: str
    visual_verified: bool = False
    mobile_verified: bool = False
    mobile_evidence_grade: str = "M0"
    stage: str = "CANDIDATE"
    rejection_reason: str = ""


def validate_frame(frame: FrameRecord) -> list[str]:
    issues: list[str] = []

    if not frame.frame_id.strip():
        issues.append("missing frame_id")
    if not frame.site_name.strip():
        issues.append("missing site_name")
    if not frame.source_url.startswith(("https://", "http://")):
        issues.append("source_url must be an absolute http(s) URL")
    if not frame.frame_role.strip():
        issues.append("missing frame_role")
    if not frame.visual_authority:
        issues.append("visual_authority is empty")
    if len(frame.lesson.strip()) < 12:
        issues.append("lesson is too vague")
    if len(frame.transfer_to_sales_sample.strip()) < 12:
        issues.append("sales-sample transfer note is too vague")
    if len(frame.source_support.strip()) < 8:
        issues.append("source_support is insufficient")
    if frame.stage not in VALID_STAGES:
        issues.append(f"invalid stage: {frame.stage}")
    if frame.mobile_evidence_grade not in VALID_MOBILE_GRADES:
        issues.append(f"invalid mobile_evidence_grade: {frame.mobile_evidence_grade}")

    if frame.stage in {"VERIFIED", "CORE"} and not frame.visual_verified:
        issues.append("VERIFIED/CORE requires visual_verified=true")

    if frame.mobile_verified and frame.mobile_evidence_grade not in {"M2", "M3"}:
        issues.append("mobile_verified=true requires mobile evidence grade M2 or M3")
    if frame.mobile_evidence_grade in {"M2", "M3"} and not frame.mobile_verified:
        issues.append("M2/M3 requires mobile_verified=true")

    if frame.stage == "CORE":
        if not frame.mobile_verified:
            issues.append("CORE requires mobile_verified=true")
        if frame.mobile_evidence_grade not in {"M2", "M3"}:
            issues.append("CORE requires mobile evidence grade M2 or M3")

    if frame.stage == "REJECTED" and not frame.rejection_reason.strip():
        issues.append("REJECTED requires rejection_reason")

    return issues


def audit_registry(records: list[FrameRecord]) -> dict[str, Any]:
    ids = [r.frame_id for r in records]
    duplicates = sorted({x for x in ids if ids.count(x) > 1})

    rows = []
    counts = {stage: 0 for stage in VALID_STAGES}
    valid_count = 0

    for record in records:
        issues = validate_frame(record)
        counts[record.stage] = counts.get(record.stage, 0) + 1
        if not issues:
            valid_count += 1
        rows.append({
            "frame_id": record.frame_id,
            "stage": record.stage,
            "mobile_evidence_grade": record.mobile_evidence_grade,
            "valid": not issues,
            "issues": issues,
        })

    strict_verified = sum(
        1 for r in records
        if r.stage in {"VERIFIED", "CORE"} and not validate_frame(r)
    )
    core_m2 = sum(
        1 for r in records
        if r.stage == "CORE" and r.mobile_evidence_grade == "M2" and not validate_frame(r)
    )
    core_m3 = sum(
        1 for r in records
        if r.stage == "CORE" and r.mobile_evidence_grade == "M3" and not validate_frame(r)
    )

    return {
        "status": "PASS" if not duplicates and valid_count == len(records) else "REVIEW",
        "total_records": len(records),
        "valid_records": valid_count,
        "candidate_count": counts.get("CANDIDATE", 0),
        "strict_verified_count": strict_verified,
        "core_count": core_m2 + core_m3,
        "core_m2_count": core_m2,
        "core_m3_count": core_m3,
        "rejected_count": counts.get("REJECTED", 0),
        "duplicate_ids": duplicates,
        "records": rows,
        "rule": (
            "Research volume and strict quality count are separate. VERIFIED is desktop/source verified. "
            "CORE additionally requires explicit mobile evidence: M2 published mobile visual review or M3 live 390px review."
        ),
    }
