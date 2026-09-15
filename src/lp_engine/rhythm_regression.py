from __future__ import annotations

from typing import Any
import re

_GENERIC_ID = re.compile(r"^section[-_]?\d+$", re.I)


def _section_map(metrics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(r.get("id")): r
        for r in metrics.get("regions", [])
        if r.get("id")
    }


def _density(row: dict[str, Any]) -> float:
    return float(row.get("edge_mean", 0.0)) + float(row.get("luminance_std", 0.0))


def section_identity_report(metrics: dict[str, Any]) -> dict[str, Any]:
    ids = [str(r.get("id") or "") for r in metrics.get("regions", [])]
    nonempty = [x for x in ids if x]
    duplicates = sorted({x for x in nonempty if nonempty.count(x) > 1})
    generic = [x for x in nonempty if _GENERIC_ID.match(x)]
    meaningful = [x for x in nonempty if not _GENERIC_ID.match(x)]
    ratio = len(meaningful) / len(nonempty) if nonempty else 0.0
    return {
        "section_count": len(ids),
        "meaningful_id_ratio": round(ratio, 4),
        "generic_ids": generic,
        "duplicate_ids": duplicates,
        "status": "PASS" if nonempty and ratio >= 0.8 and not duplicates else "REVIEW",
    }


def compare_section_rhythm(
    baseline: dict[str, Any],
    current: dict[str, Any],
    *,
    quiet_delta_review: float = 0.18,
    density_delta_review: float = 0.12,
    transition_relative_review: float = 0.35,
) -> dict[str, Any]:
    """Advisory regression comparison for section-level pixel rhythm.

    This function never produces creative FAIL. It returns STABLE or REVIEW.
    """
    bmap = _section_map(baseline)
    cmap = _section_map(current)
    shared = sorted(set(bmap) & set(cmap))
    missing = sorted(set(bmap) - set(cmap))
    new = sorted(set(cmap) - set(bmap))

    changes: list[dict[str, Any]] = []
    review_reasons: list[str] = []

    for sid in shared:
        b, c = bmap[sid], cmap[sid]
        q_delta = float(c.get("quiet_score", 0.0)) - float(b.get("quiet_score", 0.0))
        d_delta = _density(c) - _density(b)
        edge_delta = float(c.get("edge_mean", 0.0)) - float(b.get("edge_mean", 0.0))
        height_delta = float(c.get("height_ratio", 0.0)) - float(b.get("height_ratio", 0.0))
        severity = "OK"
        flags = []
        if abs(q_delta) >= quiet_delta_review:
            flags.append("quiet_shift")
        if abs(d_delta) >= density_delta_review:
            flags.append("density_shift")
        if flags:
            severity = "REVIEW"
            review_reasons.append(f"{sid}: {', '.join(flags)}")
        changes.append({
            "id": sid,
            "quiet_delta": round(q_delta, 4),
            "density_delta": round(d_delta, 4),
            "edge_delta": round(edge_delta, 4),
            "height_ratio_delta": round(height_delta, 4),
            "status": severity,
            "flags": flags,
        })

    bte = float(baseline.get("summary", {}).get("transition_energy_avg", 0.0))
    cte = float(current.get("summary", {}).get("transition_energy_avg", 0.0))
    if bte > 1e-9:
        transition_relative_delta = (cte - bte) / bte
    else:
        transition_relative_delta = 0.0 if abs(cte) < 1e-9 else 1.0
    if abs(transition_relative_delta) >= transition_relative_review:
        review_reasons.append(
            f"transition_energy changed {transition_relative_delta:+.1%} from baseline"
        )

    if missing:
        review_reasons.append(f"missing baseline sections: {', '.join(missing)}")

    baseline_identity = section_identity_report(baseline)
    current_identity = section_identity_report(current)
    if current_identity["status"] == "REVIEW":
        review_reasons.append(
            "current section IDs are not stable/meaningful enough for reliable regression"
        )

    status = "REVIEW" if review_reasons else "STABLE"
    return {
        "status": status,
        "mode": "OBSERVATION_ONLY",
        "shared_sections": shared,
        "missing_sections": missing,
        "new_sections": new,
        "transition_energy": {
            "baseline": round(bte, 4),
            "current": round(cte, 4),
            "relative_delta": round(transition_relative_delta, 4),
        },
        "section_changes": changes,
        "baseline_identity": baseline_identity,
        "current_identity": current_identity,
        "review_reasons": review_reasons,
        "warning": "REVIEW is an advisory for Creative Red Team, never an automatic creative FAIL.",
    }
