from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any


ALLOWED_FORM_DECISIONS = {
    "typography",
    "composition",
    "motion",
    "image_direction",
    "spacing",
    "navigation",
    "section_transition",
    "data_visualization",
    "interaction",
    "copy_structure",
}


@dataclass
class FormDecision:
    id: str
    decision_type: str
    description: str
    company_truth_keys: list[str] = field(default_factory=list)
    causal_explanation: str = ""
    frame_id: str = ""
    mobile_manifestation: str = ""
    transferable_by_name_swap: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_form_causality(
    decisions: list[FormDecision],
    confirmed_fact_keys: set[str],
    *,
    minimum_causal_decisions: int = 2,
    required_frames: list[str] | None = None,
    require_mobile_manifestation: bool = False,
) -> dict[str, Any]:
    """Check whether major visual decisions are actually caused by company truths.

    This is intentionally stricter than merely placing facts on the page.
    Premium quality requires the truth to change form, not only copy.
    """
    required_frames = required_frames or []
    results: list[dict[str, Any]] = []
    causal_count = 0
    passing_frames: set[str] = set()
    hard_issues: list[str] = []

    for decision in decisions:
        valid_truths = [key for key in decision.company_truth_keys if key in confirmed_fact_keys]
        issues: list[str] = []
        if decision.decision_type not in ALLOWED_FORM_DECISIONS:
            issues.append("unknown decision_type")
        if len(decision.description.strip()) < 8:
            issues.append("decision description is missing or too vague")
        if len(decision.causal_explanation.strip()) < 16:
            issues.append("causal explanation is missing or too vague")
        if not valid_truths:
            issues.append("no confirmed company truth causes this form decision")
        if decision.transferable_by_name_swap:
            issues.append("visual decision is transferable by simple company-name swap")
            hard_issues.append(f"{decision.id}: name-swappable form")
        if require_mobile_manifestation and decision.frame_id in required_frames:
            if not decision.mobile_manifestation.strip():
                issues.append("required frame has no mobile manifestation")

        status = "PASS" if not issues else "REVIEW"
        if status == "PASS":
            causal_count += 1
            if decision.frame_id:
                passing_frames.add(decision.frame_id)

        results.append({
            "id": decision.id,
            "decision_type": decision.decision_type,
            "frame_id": decision.frame_id,
            "status": status,
            "valid_company_truth_keys": valid_truths,
            "issues": issues,
        })

    missing_frames = [frame for frame in required_frames if frame not in passing_frames]
    if missing_frames:
        hard_issues.append("required frames lack strong causality: " + ", ".join(missing_frames))

    premium_ready = (
        causal_count >= minimum_causal_decisions
        and not missing_frames
        and not hard_issues
    )

    return {
        "status": "PASS" if premium_ready else "REVIEW",
        "premium_ready": premium_ready,
        "causal_decision_count": causal_count,
        "minimum_required": minimum_causal_decisions,
        "required_frames": required_frames,
        "missing_frames": missing_frames,
        "hard_issues": hard_issues,
        "decisions": results,
        "rule": (
            "Premium form must be caused by confirmed company truth, survive mobile re-art-direction, "
            "and resist simple company-name substitution."
        ),
    }
