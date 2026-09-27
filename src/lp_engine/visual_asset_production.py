"""Asset-bound wrapper around the authoritative current-industry Production renderer.

Issue #116 keeps this layer post-CompositionPlan, then applies the premium
authorship system (PU1-PU8).  Media realization may not mutate Family,
topology, scene order, decision logic, or evidence state.
"""
from __future__ import annotations

from copy import deepcopy
import html as html_lib
import json
from pathlib import Path
from typing import Any, Mapping

from .authored_composition_contract import plan_digest
from .premium_authorship import build_premium_uplift, render_premium_asset_bound_html
from .production_cutover import run_authoritative_generation


class AssetBoundProductionError(RuntimeError):
    pass


# 320px requires headline meaning units to stay whole without clipping. These
# are public-copy semantic refinements only; they do not touch CompositionPlan.
_MOBILE_SAFE_HERO_UNITS = {
    "choose": ["違いが見える", "選びやすく", "なる。"],
    "understand": ["はじめる前に", "流れを", "わかりやすく"],
    "trust": ["任せる前に", "安心できる", "理由を。"],
    "compare": ["比べるほど", "自分の基準が", "見えてくる。"],
    "prepare": ["迷いを減らし", "気持ちよく", "はじめる。"],
    "act": ["考えすぎる", "その前に", "次の一歩を", "軽く。"],
}

# Sarah PM RETURN / Aoi Human-visible QA: public display headings outside Hero
# must also be authored as semantic chunks.  Each chunk is deliberately short
# enough for the 320px canvas while keeping Japanese meaning units intact.
# This is NOT a global nowrap rule: only explicitly authored chunks are atomic.
_DISPLAY_HEADING_CHUNKS = {
    "選ぶ前に、違いを見渡す。": ("選ぶ前に、", "違いを", "見渡す。"),
    "まず、選ぶ基準を整える": ("まず、", "選ぶ基準を", "整える"),
    "選択肢を、違いで見る": ("選択肢を、", "違いで", "見る"),
    "体験の流れを、順番に": ("体験の流れを、", "順番に"),
    "安心につながる情報を、近くに": ("安心につながる", "情報を、", "近くに"),
    "比べるポイントを、ひと目で": ("比べる", "ポイントを、", "ひと目で"),
    "はじめる前の不安を、小さくする": ("はじめる前の", "不安を、", "小さくする"),
    "次の一歩は、ここから": ("次の一歩は、", "ここから"),
    "必要な情報を、わかりやすく": ("必要な", "情報を、", "わかりやすく"),
    "納得してから、次へ。": ("納得して", "から、", "次へ。"),
}


def _apply_mobile_headline_guard(plan: Mapping[str, Any], premium: dict[str, Any]) -> dict[str, Any]:
    """Refine public headline units so every atomic unit fits the 320px canvas."""
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
        "source": "public_copy_semantic_refinement_only",
        "composition_plan_mutated": False,
    }
    premium["PU2_hero_authority"]["authority_statement"] = "".join(units)
    return premium


def _semantic_heading_markup(chunks: tuple[str, ...]) -> str:
    """Render authored semantic chunks with explicit break opportunities."""
    rows = []
    for index, chunk in enumerate(chunks):
        rows.append(
            f'<span class="premium-display-unit">{html_lib.escape(chunk, quote=True)}</span>'
        )
        if index < len(chunks) - 1:
            rows.append("<wbr>")
    return "".join(rows)


def _apply_display_heading_semantic_guard(rendered: str) -> str:
    """Protect all known public display headings without blanket nowrap."""
    replaced = 0
    for heading, chunks in _DISPLAY_HEADING_CHUNKS.items():
        escaped = html_lib.escape(heading, quote=True)
        old = f"<h2>{escaped}</h2>"
        if old not in rendered:
            continue
        new = (
            '<h2 data-semantic-heading="authored">'
            f'{_semantic_heading_markup(chunks)}</h2>'
        )
        occurrences = rendered.count(old)
        rendered = rendered.replace(old, new)
        replaced += occurrences
    # Every current Issue #116 page must expose at least the offer-guide and
    # final CTA headings through this guard. Scene headings add further rows.
    if replaced < 2:
        raise AssetBoundProductionError("PREMIUM_DISPLAY_HEADING_GUARD_MISSING")
    return rendered


def _apply_headline_optical_css_guard(rendered: str) -> str:
    """Keep authored semantic units atomic without making whole headings nowrap."""
    css = (
        ".premium-headline-unit,.premium-display-unit{white-space:nowrap}"
        ".premium-display-unit{display:inline-block}"
        "@media(min-width:431px){.premium-hero h1{font-size:clamp(46px,5.4vw,80px)}}"
    )
    if "</style>" not in rendered:
        raise AssetBoundProductionError("PREMIUM_STYLE_ANCHOR_MISSING")
    return rendered.replace("</style>", css + "</style>", 1)


def render_asset_bound_authoritative_html(
    plan: Mapping[str, Any],
    directives: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> str:
    """Render approved media through the premium authored surface."""
    if plan.get("production_authority") != "composition_plan":
        raise AssetBoundProductionError("COMPOSITION_PLAN_NOT_AUTHORITATIVE")
    if plan.get("input", {}).get("creative_family", {}).get("frozen") is not True:
        raise AssetBoundProductionError("FAMILY_NOT_FROZEN")
    original_topology = deepcopy(plan.get("topology"))
    original_scenes = deepcopy(plan.get("scene_intents"))
    original_family = plan.get("family_id")

    premium = build_premium_uplift(plan, directives, asset_bindings)
    premium = _apply_mobile_headline_guard(plan, premium)
    rendered = render_premium_asset_bound_html(plan, directives, asset_bindings, premium)
    rendered = _apply_display_heading_semantic_guard(rendered)
    rendered = _apply_headline_optical_css_guard(rendered)

    if (
        plan.get("family_id") != original_family
        or plan.get("topology") != original_topology
        or plan.get("scene_intents") != original_scenes
    ):
        raise AssetBoundProductionError("ASSET_OR_PREMIUM_LAYER_MUTATED_AUTHORSHIP")
    return rendered


def run_asset_bound_generation(
    raw: Mapping[str, Any],
    output_dir: str | Path,
    *,
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Run authoritative generation, then bind media and PU1-PU8 after Family freeze."""
    result = run_authoritative_generation(raw, output_dir)
    plan = result["plan"]
    directives = result["directives"]
    output = Path(output_dir)

    premium = build_premium_uplift(plan, directives, asset_bindings)
    premium = _apply_mobile_headline_guard(plan, premium)
    premium["PU1_public_copy"]["trace"]["display_heading_semantic_guard"] = {
        "scope": "all_current_public_display_headings_and_final_cta",
        "strategy": "authored_inline_chunks_with_explicit_break_opportunities",
        "blanket_global_nowrap": False,
        "protected_units": ["から", "次へ", "ここから", "違い", "情報", "ポイント"],
        "composition_plan_mutated": False,
    }
    html = render_premium_asset_bound_html(plan, directives, asset_bindings, premium)
    html = _apply_display_heading_semantic_guard(html)
    html = _apply_headline_optical_css_guard(html)
    (output / "index.html").write_text(html, encoding="utf-8")

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
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result["manifest"] = manifest
    result["asset_bindings"] = deepcopy(dict(asset_bindings))
    result["premium_uplift"] = deepcopy(premium)
    return result


__all__ = ["AssetBoundProductionError", "render_asset_bound_authoritative_html", "run_asset_bound_generation"]
