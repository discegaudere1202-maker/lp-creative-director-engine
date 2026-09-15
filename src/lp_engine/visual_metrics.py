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
    """Pixel-derived rhythm proxy. Observation aid, not a hard creative score.

    edge_mean: normalized edge energy (0..1-ish)
    luminance_std: normalized grayscale variance (0..1)
    quiet_score: higher means visually quieter / less edge-dense
    """
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
