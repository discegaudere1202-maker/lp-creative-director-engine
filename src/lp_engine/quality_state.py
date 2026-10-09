"""Keep recorded checks and quality decisions separate from missing results.

These helpers do not evaluate a rubric or set a release threshold. A processor's
explicit work state and quality decision have different meanings: completing a
job does not supply a quality score, and a numeric score does not supply a gate.
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping


def normalize_check(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Copy a check, marking only an absent status as not run."""
    result = dict(value) if value is not None else {}
    if result.get("status") in (None, ""):
        result["status"] = "NOT_RUN"
    return result


def normalize_quality(value: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Preserve supplied results without inventing scores or a review schema."""
    result = dict(value) if value is not None else {}
    if result.get("premium_gate") in (None, ""):
        result["premium_gate"] = "NOT_RUN"
    result.setdefault("premium_score", None)
    return result


def summarize_quality(values: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate recorded results across work states, including HOLD and FAIL.

    Scores and explicit gate decisions use independent denominators. Missing,
    nonnumeric and nonfinite scores do not become zero. PASS is counted from an
    existing decision, never inferred by comparing a score with a threshold.
    """
    results = list(values)
    scores = [
        value["premium_score"]
        for value in results
        if isinstance(value.get("premium_score"), (int, float))
        and not isinstance(value["premium_score"], bool)
        and math.isfinite(value["premium_score"])
    ]
    decisions = [
        value.get("premium_gate")
        for value in results
        if value.get("premium_gate") in ("PASS", "HOLD", "FAIL")
    ]
    return {
        "average_premium_score": sum(scores) / len(scores) if scores else None,
        "premium_score_count": len(scores),
        "premium_unscored_count": len(results) - len(scores),
        "premium_pass_rate": decisions.count("PASS") / len(decisions) if decisions else None,
        "premium_pass_count": decisions.count("PASS"),
        "premium_decision_count": len(decisions),
        "premium_no_decision_count": len(results) - len(decisions),
    }
