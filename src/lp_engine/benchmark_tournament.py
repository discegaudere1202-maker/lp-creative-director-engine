from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, asdict
from random import Random
from typing import Any


CRITICAL_AXES = {"owner_specificity", "share_impulse"}


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
    """Aggregate blind pairwise votes.

    Vote schema:
    {
      "benchmark_id": "ryden",
      "reviewer_type": "creative",
      "viewport": "1440",
      "overall": -1 | 0 | 1,
      "axes": {"owner_specificity": -1 | 0 | 1, ...}
    }

    +1 means candidate wins, 0 tie, -1 benchmark wins.
    """
    votes = payload.get("votes", [])
    benchmark_ids = sorted({str(v.get("benchmark_id")) for v in votes if v.get("benchmark_id")})
    reviewer_types = sorted({str(v.get("reviewer_type")) for v in votes if v.get("reviewer_type")})

    wins = sum(1 for v in votes if int(v.get("overall", 0)) > 0)
    ties = sum(1 for v in votes if int(v.get("overall", 0)) == 0)
    losses = sum(1 for v in votes if int(v.get("overall", 0)) < 0)
    comparisons = wins + ties + losses
    win_rate = (wins + ties * 0.5) / comparisons if comparisons else 0.0

    axis_values: dict[str, list[float]] = defaultdict(list)
    viewport_values: dict[str, list[int]] = defaultdict(list)
    per_benchmark: dict[str, list[int]] = defaultdict(list)

    for vote in votes:
        viewport = str(vote.get("viewport") or "unknown")
        overall = int(vote.get("overall", 0))
        viewport_values[viewport].append(overall)
        benchmark_id = str(vote.get("benchmark_id") or "unknown")
        per_benchmark[benchmark_id].append(overall)
        for axis, value in (vote.get("axes") or {}).items():
            if value is None:
                continue
            axis_values[str(axis)].append(float(value))

    axis_means = {axis: round(_mean(vals), 4) for axis, vals in sorted(axis_values.items())}
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

    clearly_lost_benchmarks = 0
    for vals in per_benchmark.values():
        if _mean(vals) <= -0.5:
            clearly_lost_benchmarks += 1

    review_reasons: list[str] = []

    if len(benchmark_ids) < 3:
        review_reasons.append("fewer than 3 benchmarks")
    if len(reviewer_types) < 2:
        review_reasons.append("fewer than 2 reviewer types")

    for viewport in ("1440", "390"):
        if viewport not in viewport_results:
            review_reasons.append(f"missing required viewport {viewport}")

    critical_losses = [axis for axis in CRITICAL_AXES if axis_means.get(axis, 0.0) <= -0.35]
    if critical_losses:
        review_reasons.append("critical axis loss: " + ", ".join(sorted(critical_losses)))

    if clearly_lost_benchmarks >= 2:
        review_reasons.append(f"clearly lost to {clearly_lost_benchmarks} benchmarks")

    mobile = viewport_results.get("390", {}).get("win_rate")
    desktop = viewport_results.get("1440", {}).get("win_rate")
    if mobile is not None and desktop is not None and desktop >= 0.60 and mobile < 0.45:
        review_reasons.append("desktop competitive but mobile outclassed")

    requirements_complete = (
        len(benchmark_ids) >= 3
        and len(reviewer_types) >= 2
        and "1440" in viewport_results
        and "390" in viewport_results
    )

    if requirements_complete and win_rate >= 0.60 and not critical_losses and clearly_lost_benchmarks < 2:
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
