"""Asset-bound wrapper around authoritative current-industry Production.

Issue #121 preserves the semantic/safety authority established by the current
Production path but replaces the final shared premium visual skeleton with the
research-derived Production Variant bridge. Issue #124 then propagates the
Page Art Direction Spine through body/trust/media/CTA/ending/mobile without
reopening Family or weakening truth/rights boundaries.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from .authored_composition_contract import plan_digest
from .premium_authorship import build_premium_uplift
from .production_cutover import run_authoritative_generation
from .production_variant_bridge import (
    registry_manifest,
    render_variant_faithful_page,
    select_variant_ensemble,
)
from .whole_page_art_direction import (
    apply_whole_page_art_direction,
    registry_manifest as whole_page_registry_manifest,
)


class AssetBoundProductionError(RuntimeError):
    pass


_MOBILE_SAFE_HERO_UNITS = {
    "choose": ["違いが見える", "選びやすく", "なる。"],
    "understand": ["はじめる前に", "流れを", "わかりやすく"],
    "trust": ["任せる前に", "安心できる", "理由を。"],
    "compare": ["比べるほど", "自分の基準が", "見えてくる。"],
    "prepare": ["迷いを減らし", "気持ちよく", "はじめる。"],
    "act": ["考えすぎる", "その前に", "次の一歩を", "軽く。"],
}


def _apply_mobile_headline_guard(plan: Mapping[str, Any], premium: dict[str, Any]) -> dict[str, Any]:
    job = str(plan["input"]["customer_decision_state"]["primary_job"])
    units = _MOBILE_SAFE_HERO_UNITS.get(job)
    if not units:
        raise AssetBoundProductionError("PREMIUM_HEADLINE_SEMANTIC_UNITS_MISSING")
    public = premium["PU1_public_copy"]
    public["hero_headline_units"] = list(units)
    public["trace"]["mobile_semantic_unit_guard"] = {
        "minimum_width": 320,
        "decision_job": job,
        "units": list(units),
        "source": "issue116_regression_reference_only",
        "composition_plan_mutated": False,
    }
    public["trace"]["display_heading_semantic_guard"] = {
        "scope": "final_renderer_owned_by_issue121_variant_bridge_plus_issue124_spine_propagation",
        "strategy": "variant-authored semantic chunks",
        "blanket_global_nowrap": False,
        "protected_units": ["から", "次へ", "ここから", "違い", "情報", "ポイント"],
        "composition_plan_mutated": False,
    }
    premium["PU2_hero_authority"]["authority_statement"] = "".join(units)
    return premium


def _assert_architecture_preserved(
    plan: Mapping[str, Any],
    *,
    original_family: Any,
    original_topology: Any,
    original_scenes: Any,
) -> None:
    if (
        plan.get("family_id") != original_family
        or plan.get("topology") != original_topology
        or plan.get("scene_intents") != original_scenes
    ):
        raise AssetBoundProductionError("ASSET_OR_VARIANT_LAYER_MUTATED_AUTHORSHIP")


def _apply_regression_render_compatibility(rendered: str) -> str:
    """Keep accepted Issue #116/#111 visual safety hooks.

    Issue #124 may recompose body geometry, but the established destructive-crop,
    semantic-unit and narrow-footer protections remain hard constraints.
    """
    rendered = rendered.replace(
        'class="semantic-headline-unit premium-display-unit"',
        'class="premium-display-unit"',
    )
    compatibility_css = (
        ".hero-route .production-asset img{aspect-ratio:4/3!important;object-fit:cover}"
        ".hero-evidence .production-asset img{aspect-ratio:3/4!important;object-fit:cover}"
        ".wp-evidence-salon-rail .wp-trust .trust-ledger__media img{aspect-ratio:16/9!important;object-fit:cover}"
        ".wp-compare-paired-instrument .wp-compare .service-field__media img{aspect-ratio:16/9!important;object-fit:cover}"
        "@media(max-width:900px){"
        ".variant-scene .production-asset img{aspect-ratio:4/3!important;object-fit:cover}"
        "}"
        "@media(max-width:430px){"
        ".hero-recognition .production-asset img{aspect-ratio:4/3!important;object-fit:cover}"
        ".hero-recognition h1,.hero-route h1{font-size:clamp(34px,10.5vw,44px)!important;max-width:100%!important;min-width:0}"
        ".hero-recognition .premium-headline-unit,.hero-route .premium-headline-unit{display:table!important;width:max-content;max-width:100%!important}"
        "}"
        "@media(max-width:480px){footer{flex-direction:column;gap:8px;align-items:flex-start}"
        "footer span{display:block;max-width:100%;overflow-wrap:anywhere}}"
    )
    if "</style>" not in rendered:
        raise AssetBoundProductionError("VARIANT_STYLE_ANCHOR_MISSING")
    rendered = rendered.replace("</style>", compatibility_css + "</style>", 1)
    return rendered


def _render_with_whole_page_spine(
    plan: Mapping[str, Any],
    directives: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    ensemble = select_variant_ensemble(plan, directives, asset_bindings)
    rendered, bridge_trace = render_variant_faithful_page(
        plan, directives, asset_bindings, ensemble
    )
    rendered, whole_trace = apply_whole_page_art_direction(
        rendered, plan, ensemble, asset_bindings
    )
    bridge_trace["whole_page_art_direction"] = deepcopy(whole_trace)
    rendered = _apply_regression_render_compatibility(rendered)
    return rendered, bridge_trace, whole_trace


def render_asset_bound_authoritative_html(
    plan: Mapping[str, Any],
    directives: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> str:
    """Render through Issue #121 authority plus Issue #124 whole-page propagation."""
    if plan.get("production_authority") != "composition_plan":
        raise AssetBoundProductionError("COMPOSITION_PLAN_NOT_AUTHORITATIVE")
    if plan.get("input", {}).get("creative_family", {}).get("frozen") is not True:
        raise AssetBoundProductionError("FAMILY_NOT_FROZEN")
    original_topology = deepcopy(plan.get("topology"))
    original_scenes = deepcopy(plan.get("scene_intents"))
    original_family = plan.get("family_id")

    rendered, bridge_trace, whole_trace = _render_with_whole_page_spine(
        plan, directives, asset_bindings
    )
    if bridge_trace.get("renderer", {}).get("final_visual_authority") != "production_variant_dispatch":
        raise AssetBoundProductionError("VARIANT_RENDERER_NOT_FINAL_AUTHORITY")
    if bridge_trace.get("renderer", {}).get("silent_generic_fallback") is not False:
        raise AssetBoundProductionError("SILENT_GENERIC_FALLBACK_FORBIDDEN")
    if whole_trace.get("family_frozen") is not True:
        raise AssetBoundProductionError("WHOLE_PAGE_PROPAGATION_REOPENED_FAMILY")

    _assert_architecture_preserved(
        plan,
        original_family=original_family,
        original_topology=original_topology,
        original_scenes=original_scenes,
    )
    return rendered


def run_asset_bound_generation(
    raw: Mapping[str, Any],
    output_dir: str | Path,
    *,
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Run authoritative generation, Variant dispatch and whole-page propagation."""
    result = run_authoritative_generation(raw, output_dir)
    plan = result["plan"]
    directives = result["directives"]
    output = Path(output_dir)

    if plan.get("production_authority") != "composition_plan":
        raise AssetBoundProductionError("COMPOSITION_PLAN_NOT_AUTHORITATIVE")
    if plan.get("input", {}).get("creative_family", {}).get("frozen") is not True:
        raise AssetBoundProductionError("FAMILY_NOT_FROZEN")

    original_topology = deepcopy(plan.get("topology"))
    original_scenes = deepcopy(plan.get("scene_intents"))
    original_family = plan.get("family_id")

    premium = build_premium_uplift(plan, directives, asset_bindings)
    premium = _apply_mobile_headline_guard(plan, premium)
    premium["visual_authority"] = "REGRESSION_REFERENCE_ONLY_NOT_FINAL_RENDERER"

    html, bridge_trace, whole_trace = _render_with_whole_page_spine(
        plan, directives, asset_bindings
    )
    (output / "index.html").write_text(html, encoding="utf-8")

    _assert_architecture_preserved(
        plan,
        original_family=original_family,
        original_topology=original_topology,
        original_scenes=original_scenes,
    )

    manifest_path = output / "production_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["visual_asset_library"] = {
        "integration_mode": "post_family_freeze_asset_binding",
        "composition_plan_digest": plan_digest(plan),
        "family_id": plan["input"]["creative_family"]["family_id"],
        "family_frozen": True,
        "bindings": {
            key: {
                "asset_id": value.get("asset_id"),
                "binary_sha256": value.get("binary_sha256"),
                "media_role": value.get("media_role"),
                "scene_id": value.get("scene_id"),
                "evidence_status": value.get("evidence_status"),
                "rights_gate": value.get("rights_gate"),
                "trace": deepcopy(value.get("trace")),
            }
            for key, value in asset_bindings.items()
        },
        "architecture_mutation": False,
    }
    manifest["premium_authorship"] = deepcopy(premium)
    manifest["premium_authorship"]["production_authority"] = "composition_plan"
    manifest["premium_authorship"]["architecture_mutation"] = False
    manifest["research_to_production_bridge"] = deepcopy(bridge_trace)
    manifest["production_variant_registry"] = registry_manifest()
    manifest["whole_page_art_direction"] = deepcopy(whole_trace)
    manifest["whole_page_continuation_registry"] = whole_page_registry_manifest()
    manifest["final_visual_authority"] = "production_variant_dispatch"
    manifest["whole_page_art_direction_propagation"] = "issue124"
    manifest["legacy_generic_premium_renderer_final_authority"] = False
    manifest["silent_generic_variant_fallback"] = False
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    result["manifest"] = manifest
    result["asset_bindings"] = deepcopy(dict(asset_bindings))
    result["premium_uplift"] = deepcopy(premium)
    result["variant_bridge"] = deepcopy(bridge_trace)
    result["whole_page_art_direction"] = deepcopy(whole_trace)
    return result


__all__ = [
    "AssetBoundProductionError",
    "render_asset_bound_authoritative_html",
    "run_asset_bound_generation",
]
