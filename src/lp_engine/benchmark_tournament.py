from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from random import Random
from typing import Any


CRITICAL_AXES = {"owner_specificity", "share_impulse"}
REQUIRED_VIEWPORTS = {"1440", "390"}
VALID_VOTE_VALUES = {-1, 0, 1}
MIN_BENCHMARKS = 3
MAX_BENCHMARKS = 5
MIN_REVIEWER_TYPES = 2


@dataclass
class BlindPairing:
    pairing_id: str
    benchmark_id: str
    left_id: str
    right_id: str
    candidate_side: str


@dataclass
class TournamentResult:
    status: str
    classification: str
    win_rate: float
    wins: int
    ties: int
    losses: int
    benchmark_count: int
    reviewer_types: list[str]
    viewport_results: dict[str, Any]
    axis_means: dict[str, float]
    review_reasons: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_blind_pairings(
    candidate_id: str,
    benchmark_ids: list[str],
    *,
    seed: int = 0,
) -> list[BlindPairing]:
    rng = Random(seed)
    pairings: list[BlindPairing] = []
    for idx, benchmark_id in enumerate(benchmark_ids, start=1):
        candidate_left = bool(rng.getrandbits(1))
        pairings.append(
            BlindPairing(
                pairing_id=f"pair-{idx:02d}",
                benchmark_id=benchmark_id,
                left_id=candidate_id if candidate_left else benchmark_id,
                right_id=benchmark_id if candidate_left else candidate_id,
                candidate_side="left" if candidate_left else "right",
            )
        )
    return pairings


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate_tournament(payload: dict[str, Any]) -> TournamentResult:
    """Aggregate formal blind pairwise votes.

    Vote schema:
    {
      "benchmark_id": "ryden",
      "reviewer_type": "creative",
      "viewport": "1440",
      "overall": -1 | 0 | 1,
      "axes": {"owner_specificity": -1 | 0 | 1, ...}
    }

    +1 means candidate wins, 0 tie, -1 benchmark wins.

    A formal verdict requires a complete comparison matrix:
    - 3–5 benchmarks
    - at least two reviewer types
    - every benchmark reviewed at both 1440 and 390
    - every benchmark × viewport cell reviewed by at least two reviewer types
    - Owner Specificity and Share Impulse present in every vote
    - all vote values are -1 / 0 / +1

    Incomplete evidence always returns HOLD. It must never become PASS or FAIL merely
    because the partial votes happen to be strong or weak.
    """
    votes = payload.get("votes", [])
    benchmark_ids = sorted({
        str(v.get("benchmark_id"))
        for v in votes
        if str(v.get("benchmark_id") or "").strip()
    })
    reviewer_types = sorted({
        str(v.get("reviewer_type"))
        for v in votes
        if str(v.get("reviewer_type") or "").strip()
    })

    valid_overall_values: list[int] = []
    axis_values: dict[str, list[float]] = defaultdict(list)
    viewport_values: dict[str, list[int]] = defaultdict(list)
    per_benchmark: dict[str, list[int]] = defaultdict(list)
    cell_reviewers: dict[tuple[str, str], set[str]] = defaultdict(set)
    review_reasons: list[str] = []

    malformed_vote_count = 0
    missing_critical_axis_count = 0

    for vote in votes:
        benchmark_id = str(vote.get("benchmark_id") or "").strip()
        reviewer_type = str(vote.get("reviewer_type") or "").strip()
        viewport = str(vote.get("viewport") or "unknown")

        try:
            overall = int(vote.get("overall", 0))
        except (TypeError, ValueError):
            overall = 99

        if overall not in VALID_VOTE_VALUES:
            malformed_vote_count += 1
            continue

        valid_overall_values.append(overall)
        viewport_values[viewport].append(overall)
        if benchmark_id:
            per_benchmark[benchmark_id].append(overall)
        if benchmark_id and reviewer_type:
            cell_reviewers[(benchmark_id, viewport)].add(reviewer_type)

        axes = vote.get("axes") or {}
        if not CRITICAL_AXES.issubset(set(axes)):
            missing_critical_axis_count += 1

        for axis, value in axes.items():
            if value is None:
                continue
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                malformed_vote_count += 1
                continue
            if numeric not in VALID_VOTE_VALUES:
                malformed_vote_count += 1
                continue
            axis_values[str(axis)].append(numeric)

    wins = sum(1 for x in valid_overall_values if x > 0)
    ties = sum(1 for x in valid_overall_values if x == 0)
    losses = sum(1 for x in valid_overall_values if x < 0)
    comparisons = len(valid_overall_values)
    win_rate = (wins + ties * 0.5) / comparisons if comparisons else 0.0

    axis_means = {
        axis: round(_mean(vals), 4)
        for axis, vals in sorted(axis_values.items())
    }

    viewport_results: dict[str, Any] = {}
    for viewport, vals in sorted(viewport_values.items()):
        vp_wins = sum(1 for x in vals if x > 0)
        vp_ties = sum(1 for x in vals if x == 0)
        vp_losses = sum(1 for x in vals if x < 0)
        total = len(vals)
        viewport_results[viewport] = {
            "wins": vp_wins,
            "ties": vp_ties,
            "losses": vp_losses,
            "win_rate": round((vp_wins + vp_ties * 0.5) / total, 4) if total else 0.0,
        }

    clearly_lost_benchmarks = sum(
        1 for vals in per_benchmark.values()
        if vals and _mean(vals) <= -0.5
    )

    if len(benchmark_ids) < MIN_BENCHMARKS:
        review_reasons.append(f"fewer than {MIN_BENCHMARKS} benchmarks")
    if len(benchmark_ids) > MAX_BENCHMARKS:
        review_reasons.append(f"more than {MAX_BENCHMARKS} benchmarks")
    if len(reviewer_types) < MIN_REVIEWER_TYPES:
        review_reasons.append(f"fewer than {MIN_REVIEWER_TYPES} reviewer types")

    for viewport in sorted(REQUIRED_VIEWPORTS, reverse=True):
        if viewport not in viewport_results:
            review_reasons.append(f"missing required viewport {viewport}")

    incomplete_cells: list[str] = []
    for benchmark_id in benchmark_ids:
        for viewport in sorted(REQUIRED_VIEWPORTS, reverse=True):
            reviewers = cell_reviewers.get((benchmark_id, viewport), set())
            if len(reviewers) < MIN_REVIEWER_TYPES:
                incomplete_cells.append(f"{benchmark_id}@{viewport}")
    if incomplete_cells:
        review_reasons.append("incomplete reviewer matrix: " + ", ".join(incomplete_cells))

    if missing_critical_axis_count:
        review_reasons.append(
            "votes missing critical axes owner_specificity/share_impulse: "
            f"{missing_critical_axis_count}"
        )
    if malformed_vote_count:
        review_reasons.append(f"invalid vote values: {malformed_vote_count}")

    critical_losses = [
        axis
        for axis in CRITICAL_AXES
        if axis_means.get(axis, 0.0) <= -0.35
    ]
    if critical_losses:
        review_reasons.append("critical axis loss: " + ", ".join(sorted(critical_losses)))

    if clearly_lost_benchmarks >= 2:
        review_reasons.append(f"clearly lost to {clearly_lost_benchmarks} benchmarks")

    mobile = viewport_results.get("390", {}).get("win_rate")
    desktop = viewport_results.get("1440", {}).get("win_rate")
    if mobile is not None and desktop is not None and desktop >= 0.60 and mobile < 0.45:
        review_reasons.append("desktop competitive but mobile outclassed")

    requirements_complete = (
        MIN_BENCHMARKS <= len(benchmark_ids) <= MAX_BENCHMARKS
        and len(reviewer_types) >= MIN_REVIEWER_TYPES
        and REQUIRED_VIEWPORTS.issubset(viewport_results)
        and not incomplete_cells
        and missing_critical_axis_count == 0
        and malformed_vote_count == 0
    )

    if not requirements_complete:
        status = "HOLD"
        classification = "REVIEW_REQUIRED"
    elif win_rate >= 0.60 and not critical_losses and clearly_lost_benchmarks < 2:
        status = "PASS"
        classification = "COMPETITIVE_OR_SUPERIOR"
    elif win_rate < 0.45 or clearly_lost_benchmarks >= 2 or len(critical_losses) >= 2:
        status = "FAIL"
        classification = "OUTCLASSED"
    else:
        status = "HOLD"
        classification = "REVIEW_REQUIRED"

    return TournamentResult(
        status=status,
        classification=classification,
        win_rate=round(win_rate, 4),
        wins=wins,
        ties=ties,
        losses=losses,
        benchmark_count=len(benchmark_ids),
        reviewer_types=reviewer_types,
        viewport_results=viewport_results,
        axis_means=axis_means,
        review_reasons=review_reasons,
    )
