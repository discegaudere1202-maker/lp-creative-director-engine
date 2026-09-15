from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import math
import statistics

from .visual_metrics import analyze_vertical_rhythm


@dataclass
class RhythmFeatureSet:
    source: str
    bands: int
    edge_avg: float
    edge_range: float
    quiet_avg: float
    quiet_fraction: float
    transition_energy: float
    peak_clusters: int
    quiet_clusters: int
    longest_quiet_run: int
    alternation_count: int
    flatness_risk: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clusters(flags: list[bool]) -> tuple[int, int]:
    count = 0
    longest = 0
    run = 0
    for flag in flags:
        if flag:
            run += 1
            longest = max(longest, run)
        else:
            if run:
                count += 1
            run = 0
    if run:
        count += 1
    return count, longest


def _alternation_count(states: list[int]) -> int:
    compact = [s for s in states if s != 0]
    if len(compact) < 2:
        return 0
    return sum(1 for a, b in zip(compact, compact[1:]) if a != b)


def extract_rhythm_features(path: str | Path, bands: int = 24) -> RhythmFeatureSet:
    report = analyze_vertical_rhythm(path, bands=bands)
    rows = report['bands']
    edges = [float(r['edge_mean']) for r in rows]
    quiets = [float(r['quiet_score']) for r in rows]
    lums = [float(r['luminance_std']) for r in rows]

    edge_avg = statistics.fmean(edges) if edges else 0.0
    edge_std = statistics.pstdev(edges) if len(edges) > 1 else 0.0
    quiet_avg = statistics.fmean(quiets) if quiets else 0.0
    quiet_std = statistics.pstdev(quiets) if len(quiets) > 1 else 0.0

    peak_threshold = edge_avg + max(0.006, edge_std * 0.65)
    quiet_threshold = quiet_avg + max(0.03, quiet_std * 0.45)
    peak_flags = [x >= peak_threshold for x in edges]
    quiet_flags = [x >= quiet_threshold for x in quiets]

    peak_clusters, _ = _clusters(peak_flags)
    quiet_clusters, longest_quiet = _clusters(quiet_flags)

    deltas = []
    for i in range(1, len(rows)):
        edge_delta = abs(edges[i] - edges[i-1])
        lum_delta = abs(lums[i] - lums[i-1])
        quiet_delta = abs(quiets[i] - quiets[i-1])
        deltas.append(edge_delta * 1.8 + lum_delta * 0.8 + quiet_delta * 0.6)
    transition_energy = statistics.fmean(deltas) if deltas else 0.0

    states = [1 if p else (-1 if q else 0) for p, q in zip(peak_flags, quiet_flags)]
    alternations = _alternation_count(states)
    edge_range = (max(edges) - min(edges)) if edges else 0.0
    quiet_fraction = sum(quiet_flags) / len(quiet_flags) if quiet_flags else 0.0

    flatness_risk = (
        len(edges) >= 12
        and edge_range < 0.035
        and transition_energy < 0.045
        and alternations <= 1
    )

    return RhythmFeatureSet(
        source=str(path),
        bands=bands,
        edge_avg=round(edge_avg, 4),
        edge_range=round(edge_range, 4),
        quiet_avg=round(quiet_avg, 4),
        quiet_fraction=round(quiet_fraction, 4),
        transition_energy=round(transition_energy, 4),
        peak_clusters=peak_clusters,
        quiet_clusters=quiet_clusters,
        longest_quiet_run=longest_quiet,
        alternation_count=alternations,
        flatness_risk=flatness_risk,
    )


def _normalized_vector(path: str | Path, bands: int = 24) -> list[float]:
    report = analyze_vertical_rhythm(path, bands=bands)
    vec = [float(r['edge_mean']) * 1.6 + float(r['luminance_std']) for r in report['bands']]
    if not vec:
        return []
    lo, hi = min(vec), max(vec)
    if math.isclose(lo, hi):
        return [0.0 for _ in vec]
    return [(v - lo) / (hi - lo) for v in vec]


def compare_rhythm(a: str | Path, b: str | Path, bands: int = 24) -> dict[str, Any]:
    fa = extract_rhythm_features(a, bands=bands)
    fb = extract_rhythm_features(b, bands=bands)
    va = _normalized_vector(a, bands=bands)
    vb = _normalized_vector(b, bands=bands)
    n = min(len(va), len(vb))
    l1 = statistics.fmean(abs(va[i] - vb[i]) for i in range(n)) if n else 0.0

    return {
        'status': 'OBSERVATION_ONLY',
        'bands': bands,
        'a': fa.to_dict(),
        'b': fb.to_dict(),
        'normalized_density_distance': round(l1, 4),
        'interpretation': {
            'higher_transition_energy': 'a' if fa.transition_energy > fb.transition_energy else ('b' if fb.transition_energy > fa.transition_energy else 'tie'),
            'more_peak_clusters': 'a' if fa.peak_clusters > fb.peak_clusters else ('b' if fb.peak_clusters > fa.peak_clusters else 'tie'),
            'more_quiet_clusters': 'a' if fa.quiet_clusters > fb.quiet_clusters else ('b' if fb.quiet_clusters > fa.quiet_clusters else 'tie'),
            'warning': 'Do not rank creative quality from pixel rhythm alone. Use section context, Screenshot Score, CRO and owner-specificity together.'
        }
    }
