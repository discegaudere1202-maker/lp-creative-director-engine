from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkPool:
    name: str
    benchmark_ids: list[str]
    critical_axes: list[str]
    description: str = ""


def load_benchmark_pools(path: str | Path) -> dict[str, BenchmarkPool]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    pools: dict[str, BenchmarkPool] = {}
    for name, raw in payload.get("pools", {}).items():
        pools[name] = BenchmarkPool(
            name=name,
            benchmark_ids=list(raw.get("benchmark_ids", [])),
            critical_axes=list(raw.get("critical_axes", [])),
            description=str(raw.get("description", "")),
        )
    return pools


def recommend_pool_names(tags: list[str]) -> list[str]:
    """Map project authority tags to benchmark comparison pools.

    This is intentionally conservative. It returns comparison families,
    not design templates or automatic art-direction choices.
    """
    normalized = {t.strip().upper() for t in tags if t and t.strip()}
    ranked: list[str] = []

    rules: list[tuple[set[str], str]] = [
        ({"PERSON", "EDITORIAL", "AUTHORSHIP"}, "PERSON_EDITORIAL"),
        ({"MATERIAL", "PHOTO", "CRAFT"}, "MATERIAL_PHOTO_CRAFT"),
        ({"PRODUCT", "PRODUCT_BEHAVIOR", "DEMO"}, "PRODUCT_BEHAVIOR"),
        ({"PLACE", "HOSPITALITY", "SHOP", "RESTAURANT"}, "PLACE_HOSPITALITY"),
        ({"B2B", "DOCUMENT", "EXPLAINER", "TECHNICAL"}, "B2B_EXPLAINER_DOCUMENT"),
        ({"WORLD", "CATEGORY", "CATEGORY_REFRAME", "SYSTEM"}, "WORLD_CATEGORY"),
        ({"TYPOGRAPHY", "TYPE", "MOTION", "SEMANTIC_MOTION"}, "TYPOGRAPHY_MOTION"),
        ({"UTILITY", "ACCESSIBILITY", "TRUST"}, "UTILITY_ACCESSIBILITY_TRUST"),
        ({"CONVERSION", "CTA", "ACTION", "CRO"}, "CONVERSION_ACTION"),
        ({"MOBILE", "MOBILE_FIRST"}, "MOBILE_FIRST"),
        ({"ASSET_LIGHT", "NO_WEB"}, "ASSET_LIGHT"),
        ({"SME", "LOCAL", "NO_WEB", "WEAK_WEB"}, "LOCAL_SME_TRANSFER"),
    ]

    for trigger_tags, pool_name in rules:
        if normalized & trigger_tags and pool_name not in ranked:
            ranked.append(pool_name)

    return ranked


def build_tournament_plan(
    tags: list[str],
    pools: dict[str, BenchmarkPool],
    *,
    max_benchmarks: int = 7,
    minimum_benchmarks: int = 3,
) -> dict[str, Any]:
    pool_names = [name for name in recommend_pool_names(tags) if name in pools]
    benchmark_ids: list[str] = []
    critical_axes: list[str] = []

    for name in pool_names:
        pool = pools[name]
        for benchmark_id in pool.benchmark_ids:
            if benchmark_id not in benchmark_ids:
                benchmark_ids.append(benchmark_id)
            if len(benchmark_ids) >= max_benchmarks:
                break
        for axis in pool.critical_axes:
            if axis not in critical_axes:
                critical_axes.append(axis)
        if len(benchmark_ids) >= max_benchmarks:
            break

    return {
        "pool_names": pool_names,
        "benchmark_ids": benchmark_ids[:max_benchmarks],
        "critical_axes": critical_axes,
        "status": "READY" if len(benchmark_ids) >= minimum_benchmarks else "REVIEW",
        "warning": (
            "Benchmark pools choose comparison opponents only; they must never determine style."
        ),
    }
