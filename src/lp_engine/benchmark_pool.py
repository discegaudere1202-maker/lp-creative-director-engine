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


def load_benchmark_catalog(path: str | Path) -> dict[str, dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        str(item["id"]): item
        for item in payload.get("benchmarks", [])
        if item.get("id")
    }


def recommend_pool_names(tags: list[str]) -> list[str]:
    """Map project/problem tags to benchmark comparison pools.

    This chooses opponents only. It must never choose the candidate's style.
    Problem/behavior tags are deliberately allowed so SME prototypes can be
    compared by the problem they solve rather than by superficial visual similarity.
    """
    normalized = {t.strip().upper() for t in tags if t and t.strip()}
    ranked: list[str] = []

    rules: list[tuple[set[str], str]] = [
        ({"PERSON", "EDITORIAL", "AUTHORSHIP", "OWNER_VOICE"}, "PERSON_EDITORIAL"),
        ({"MATERIAL", "PHOTO", "CRAFT"}, "MATERIAL_PHOTO_CRAFT"),
        ({"PRODUCT", "PRODUCT_BEHAVIOR", "DEMO"}, "PRODUCT_BEHAVIOR"),
        ({"PLACE", "HOSPITALITY", "SHOP", "RESTAURANT"}, "PLACE_HOSPITALITY"),
        ({"B2B", "DOCUMENT", "EXPLAINER", "TECHNICAL", "TRANSLATION"}, "B2B_EXPLAINER_DOCUMENT"),
        ({"WORLD", "CATEGORY", "CATEGORY_REFRAME", "SYSTEM"}, "WORLD_CATEGORY"),
        ({"TYPOGRAPHY", "TYPE", "MOTION", "SEMANTIC_MOTION"}, "TYPOGRAPHY_MOTION"),
        ({"UTILITY", "ACCESSIBILITY", "TRUST"}, "UTILITY_ACCESSIBILITY_TRUST"),
        ({"CONVERSION", "CTA", "ACTION", "CRO", "PRICE_TRANSPARENCY"}, "CONVERSION_ACTION"),
        ({"MOBILE", "MOBILE_FIRST", "RESPONSIVE"}, "MOBILE_FIRST"),
        ({"ASSET_LIGHT", "NO_WEB"}, "ASSET_LIGHT"),
        ({"SME", "LOCAL", "NO_WEB", "WEAK_WEB"}, "LOCAL_SME_TRANSFER"),
        ({"BUSINESS_VERB", "BRAND_VERB", "BEHAVIOR_GRAMMAR"}, "BUSINESS_VERB"),
        ({"EMOTIONAL_BARRIER", "HESITATION", "PSYCHOLOGICAL_FRICTION", "TRUST_HEAVY"}, "EMOTIONAL_BARRIER"),
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
    catalog: dict[str, dict[str, Any]] | None = None,
    require_mobile_verified: bool = True,
) -> dict[str, Any]:
    """Build a comparison plan without leaking benchmark style into generation.

    Pool membership is a research classification. If a catalog is supplied, only
    benchmarks that are actually ready for the requested tournament are selected.
    For production Benchmark Supremacy, mobile verification is required by default.
    """
    pool_names = [name for name in recommend_pool_names(tags) if name in pools]
    research_ids: list[str] = []
    critical_axes: list[str] = []

    for name in pool_names:
        pool = pools[name]
        for benchmark_id in pool.benchmark_ids:
            if benchmark_id not in research_ids:
                research_ids.append(benchmark_id)
        for axis in pool.critical_axes:
            if axis not in critical_axes:
                critical_axes.append(axis)

    ready_ids: list[str] = []
    blocked: list[dict[str, Any]] = []

    for benchmark_id in research_ids:
        if catalog is None:
            ready_ids.append(benchmark_id)
            continue

        item = catalog.get(benchmark_id)
        reasons: list[str] = []
        if item is None:
            reasons.append("missing from benchmark catalog")
        else:
            if item.get("stage") not in {"VERIFIED", "CORE"}:
                reasons.append("not source/desktop verified")
            if not item.get("desktop_verified", False):
                reasons.append("desktop not verified")
            if require_mobile_verified and not item.get("mobile_verified", False):
                reasons.append("mobile not verified")

        if reasons:
            blocked.append({"benchmark_id": benchmark_id, "reasons": reasons})
        else:
            ready_ids.append(benchmark_id)

    selected = ready_ids[:max_benchmarks]
    return {
        "pool_names": pool_names,
        "research_benchmark_ids": research_ids,
        "benchmark_ids": selected,
        "blocked_benchmarks": blocked,
        "critical_axes": critical_axes,
        "status": "READY" if len(selected) >= minimum_benchmarks else "REVIEW",
        "warning": (
            "Research pool membership does not mean tournament readiness. Production blind review "
            "requires verified comparison assets for all required viewports. Benchmark pools choose "
            "opponents only; they must never determine style."
        ),
    }
