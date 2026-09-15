from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


AXES = (
    "immediate_read",
    "distinctness",
    "owner_specificity",
    "visual_hierarchy",
    "craft_detail",
    "emotional_pull",
    "trust",
    "share_impulse",
    "mobile_quality",
    "conversion_intent",
)

CRITICAL_AXES = {"owner_specificity", "share_impulse"}


@dataclass
class PairwiseReview:
    benchmark_id: str
    reviewer: str
    viewport: str
    scores: dict[str, int | None]  # -1 benchmark wins, 0 tie, +1 candidate wins


@dataclass
class AxisSummary:
    axis: str
    wins: int = 0
    ties: int = 0
    losses: int = 0
    comparisons: int = 0

    @property
    def win_rate(self) -> float:
        if not self.comparisons:
            return 0.0
        return (self.wins + 0.5 * self.ties) / self.comparisons


def summarize_axis(reviews: Iterable[PairwiseReview], axis: str) -> AxisSummary:
    summary = AxisSummary(axis=axis)
    for review in reviews:
        value = review.scores.get(axis)
        if value is None:
            continue
        if value not in (-1, 0, 1):
            raise ValueError(f"{axis}: score must be -1, 0, 1 or None")
        summary.comparisons += 1
        if value == 1:
            summary.wins += 1
        elif value == 0:
            summary.ties += 1
        else:
            summary.losses += 1
    return summary


def evaluate_tournament(
    reviews: list[PairwiseReview],
    *,
    pass_rate: float = 0.60,
    fail_rate: float = 0.45,
) -> dict:
    if not reviews:
        return {
            "status": "REVIEW",
            "reason": "No reviews supplied.",
            "win_rate": 0.0,
            "axes": {},
        }

    benchmarks = {review.benchmark_id for review in reviews}
    reviewers = {review.reviewer for review in reviews}
    viewports = {review.viewport for review in reviews}

    axis_summaries = {axis: summarize_axis(reviews, axis) for axis in AXES}
    comparisons = sum(summary.comparisons for summary in axis_summaries.values())
    equivalent_wins = sum(
        summary.wins + 0.5 * summary.ties for summary in axis_summaries.values()
    )
    overall_rate = equivalent_wins / comparisons if comparisons else 0.0

    critical_losses = {
        axis: axis_summaries[axis].losses
        for axis in CRITICAL_AXES
        if axis_summaries[axis].losses > axis_summaries[axis].wins
    }

    reasons: list[str] = []
    if len(benchmarks) < 3:
        reasons.append("Need at least 3 benchmark frames.")
    if len(reviewers) < 2:
        reasons.append("Need at least 2 reviewer roles.")
    if not {"1440", "390"}.issubset(viewports):
        reasons.append("Need both 1440 and 390 viewport reviews.")

    if overall_rate >= pass_rate and not critical_losses and not reasons:
        status = "PASS"
    elif overall_rate < fail_rate or critical_losses:
        status = "FAIL"
    else:
        status = "HOLD"

    if critical_losses:
        reasons.append(
            "Critical axes are losing: "
            + ", ".join(
                f"{axis}({losses} losses)"
                for axis, losses in sorted(critical_losses.items())
            )
        )

    return {
        "status": status,
        "win_rate": round(overall_rate, 4),
        "benchmark_count": len(benchmarks),
        "reviewer_count": len(reviewers),
        "viewports": sorted(viewports),
        "critical_axis_losses": critical_losses,
        "reasons": reasons,
        "axes": {
            axis: {
                **asdict(summary),
                "win_rate": round(summary.win_rate, 4),
            }
            for axis, summary in axis_summaries.items()
        },
        "rule": (
            "PASS requires >=60% equivalent win-rate, 3+ benchmarks, 2+ reviewer roles, "
            "desktop/mobile, and no persistent loss on owner-specificity/share-impulse."
        ),
    }
