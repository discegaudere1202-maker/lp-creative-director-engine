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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_form_causality(
    decisions: list[FormDecision],
    confirmed_fact_keys: set[str],
    *,
    minimum_causal_decisions: int = 2,
) -> dict[str, Any]:
    """Check whether major visual decisions are actually caused by company truths.

    This is intentionally stricter than merely placing facts on the page.
    """
    results: list[dict[str, Any]] = []
    causal_count = 0

    for decision in decisions:
        valid_truths = [k for k in decision.company_truth_keys if k in confirmed_fact_keys]
        issues: list[str] = []
        if decision.decision_type not in ALLOWED_FORM_DECISIONS:
            issues.append("unknown decision_type")
        if not decision.description.strip():
            issues.append("missing decision description")
        if not decision.causal_explanation.strip():
            issues.append("missing causal explanation")
        if not valid_truths:
            issues.append("no confirmed company truth causes this form decision")

        status = "PASS" if not issues else "REVIEW"
        if status == "PASS":
            causal_count += 1

        results.append({
            "id": decision.id,
            "decision_type": decision.decision_type,
            "status": status,
            "valid_company_truth_keys": valid_truths,
            "issues": issues,
        })

    overall = "PASS" if causal_count >= minimum_causal_decisions else "REVIEW"
    return {
        "status": overall,
        "causal_decision_count": causal_count,
        "minimum_required": minimum_causal_decisions,
        "decisions": results,
        "rule": "Premium form must be caused by company truth, not merely decorated with company facts.",
    }
