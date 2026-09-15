from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter, ImageStat


@dataclass
class BandMetric:
    index: int
    y_start_ratio: float
    y_end_ratio: float
    edge_mean: float
    luminance_std: float
    quiet_score: float


def analyze_vertical_rhythm(path: str | Path, bands: int = 20) -> dict[str, Any]:
    """Pixel-derived rhythm proxy. Observation aid, not a hard creative score."""
    path = Path(path)
    with Image.open(path) as im:
        gray = im.convert("L")
        if gray.width > 480:
            new_h = max(1, round(gray.height * 480 / gray.width))
            gray = gray.resize((480, new_h))
        edge = gray.filter(ImageFilter.FIND_EDGES)
        h = gray.height
        metrics: list[BandMetric] = []
        for i in range(bands):
            y0 = round(i * h / bands)
            y1 = round((i + 1) * h / bands)
            crop_g = gray.crop((0, y0, gray.width, max(y0 + 1, y1)))
            crop_e = edge.crop((0, y0, edge.width, max(y0 + 1, y1)))
            edge_mean = float(ImageStat.Stat(crop_e).mean[0]) / 255.0
            lum_std = float(ImageStat.Stat(crop_g).stddev[0]) / 255.0
            quiet = max(0.0, min(1.0, 1.0 - (edge_mean * 3.2 + lum_std * 1.6)))
            metrics.append(BandMetric(
                index=i,
                y_start_ratio=round(i / bands, 3),
                y_end_ratio=round((i + 1) / bands, 3),
                edge_mean=round(edge_mean, 4),
                luminance_std=round(lum_std, 4),
                quiet_score=round(quiet, 4),
            ))

        edge_values = [m.edge_mean for m in metrics]
        quiet_values = [m.quiet_score for m in metrics]
        return {
            "path": str(path),
            "bands": [asdict(m) for m in metrics],
            "summary": {
                "edge_mean_avg": round(sum(edge_values) / len(edge_values), 4),
                "edge_mean_min": round(min(edge_values), 4),
                "edge_mean_max": round(max(edge_values), 4),
                "quiet_score_avg": round(sum(quiet_values) / len(quiet_values), 4),
                "very_quiet_bands": [m.index for m in metrics if m.quiet_score >= 0.82],
                "high_detail_bands": [m.index for m in metrics if m.edge_mean >= 0.08],
            },
            "warning": "Pixel rhythm proxy only. Do not hard-pass/fail creative quality without section/context review."
        }


@dataclass
class RegionMetric:
    id: str
    y_start_ratio: float
    y_end_ratio: float
    height_ratio: float
    edge_mean: float
    luminance_std: float
    quiet_score: float


def analyze_regions(path: str | Path, regions: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze named vertical regions using normalized y coordinates.

    `regions` items require id, y_start_ratio and y_end_ratio in document space.
    This keeps analysis stable even when screenshot pixel height differs from CSS scroll height.
    """
    path = Path(path)
    with Image.open(path) as im:
        gray = im.convert('L')
        if gray.width > 640:
            new_h = max(1, round(gray.height * 640 / gray.width))
            gray = gray.resize((640, new_h))
        edge = gray.filter(ImageFilter.FIND_EDGES)
        h = gray.height
        out: list[RegionMetric] = []
        for i, region in enumerate(regions):
            start = max(0.0, min(1.0, float(region.get('y_start_ratio', 0.0))))
            end = max(start, min(1.0, float(region.get('y_end_ratio', start))))
            y0 = min(h - 1, max(0, round(start * h))) if h > 1 else 0
            y1 = min(h, max(y0 + 1, round(end * h)))
            crop_g = gray.crop((0, y0, gray.width, y1))
            crop_e = edge.crop((0, y0, edge.width, y1))
            edge_mean = float(ImageStat.Stat(crop_e).mean[0]) / 255.0
            lum_std = float(ImageStat.Stat(crop_g).stddev[0]) / 255.0
            quiet = max(0.0, min(1.0, 1.0 - (edge_mean * 3.2 + lum_std * 1.6)))
            out.append(RegionMetric(
                id=str(region.get('id') or f'region-{i+1:02d}'),
                y_start_ratio=round(start, 4),
                y_end_ratio=round(end, 4),
                height_ratio=round(end-start, 4),
                edge_mean=round(edge_mean, 4),
                luminance_std=round(lum_std, 4),
                quiet_score=round(quiet, 4),
            ))

        transitions = []
        for a, b in zip(out, out[1:]):
            energy = (
                abs(b.edge_mean-a.edge_mean) * 1.8
                + abs(b.luminance_std-a.luminance_std) * 0.8
                + abs(b.quiet_score-a.quiet_score) * 0.6
            )
            transitions.append({
                'from': a.id,
                'to': b.id,
                'transition_energy': round(energy, 4),
                'direction': {
                    'edge': 'up' if b.edge_mean > a.edge_mean else ('down' if b.edge_mean < a.edge_mean else 'flat'),
                    'quiet': 'up' if b.quiet_score > a.quiet_score else ('down' if b.quiet_score < a.quiet_score else 'flat'),
                },
            })

        rows = [asdict(x) for x in out]
        if rows:
            quietest = max(rows, key=lambda x: x['quiet_score'])['id']
            densest = max(rows, key=lambda x: x['edge_mean'] + x['luminance_std'])['id']
        else:
            quietest = densest = None
        return {
            'regions': rows,
            'transitions': transitions,
            'summary': {
                'region_count': len(rows),
                'quietest_region': quietest,
                'densest_region': densest,
                'transition_energy_avg': round(sum(x['transition_energy'] for x in transitions)/len(transitions),4) if transitions else 0.0,
                'strongest_transition': max(transitions, key=lambda x:x['transition_energy']) if transitions else None,
            },
            'warning': 'Section pixel metrics are observation aids, not standalone creative-quality gates.'
        }
