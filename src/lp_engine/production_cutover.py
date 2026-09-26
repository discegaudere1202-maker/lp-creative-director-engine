"""Current-industry Production cutover boundary for Issue #99.

This module is the normal-path authority for the three supported industry
scopes. It derives semantic input, freezes CompositionPlan, consumes only its
directives, and fails closed before any legacy profile can be selected.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any, Mapping

from .authored_composition_contract import ContractError, infer_authored_composition, plan_digest
from .authored_composition_runtime import MigrationGuardError, consume_composition_plan

CURRENT_INDUSTRIES = {"beauty_cosmetics", "hair_salon_barber", "pilates_fitness"}
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)


class ProductionCutoverError(RuntimeError):
    """Raised when current-industry Production cannot be rendered safely."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def derive_current_industry_authorship_input(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize semantic truth; identity fields are never consulted."""
    source = raw.get("authorship_input", raw)
    if not isinstance(source, Mapping):
        raise ProductionCutoverError("INPUT_TRUTH_INSUFFICIENT")
    try:
        normalized = deepcopy(dict(source))
        category = normalized["company_truth"]["category"]["value"]
        if category not in CURRENT_INDUSTRIES:
            raise ProductionCutoverError("INDUSTRY_OUT_OF_SCOPE")
        normalized.pop("company_id", None)
        normalized.pop("reference_id", None)
        normalized.pop("fixture_id", None)
        normalized["production_scope"] = "current_industry"
        normalized["asset_pool_scope"] = category
        return normalized
    except (KeyError, TypeError) as exc:
        raise ProductionCutoverError("INPUT_TRUTH_INSUFFICIENT") from exc


def plan_current_industry_production(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Create a deterministic Production CompositionPlan and trace."""
    normalized = derive_current_industry_authorship_input(raw)
    try:
        plan = infer_authored_composition(normalized)
    except ContractError as exc:
        raise ProductionCutoverError(f"INPUT_CONTRACT_INVALID: {exc}") from exc
    plan["production_authority"] = "composition_plan"
    plan["production_scope"] = "current_industry"
    plan["asset_pool_scope"] = normalized["company_truth"]["category"]["value"]
    plan["cutover_trace"] = {
        "order": [
            "verified_company_truth", "customer_decision_state", "creative_fit",
            "family_frozen", "composition_plan", "production_feasibility",
            "renderer_directives",
        ],
        "identity_used": False,
        "reference_lookup_used": False,
        "category_used_for": "asset_pool_scope_only",
        "legacy_profile_fallback": False,
        "plan_digest": plan_digest(plan),
    }
    return plan


def consume_current_industry_production(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Consume Production directives without creative re-inference."""
    try:
        directives = consume_composition_plan(plan, mode="production")
    except MigrationGuardError as exc:
        raise ProductionCutoverError(str(exc)) from exc
    directives["production_authority"] = "composition_plan"
    directives["renderer_must_not_reinfer"] = True
    return directives


def _esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def semantic_headline_units(primary_job: str) -> tuple[str, ...]:
    """Return meaning-preserving headline units for narrow mobile rendering."""
    if not primary_job:
        raise ProductionCutoverError("HEADLINE_TEXT_EMPTY")
    return (f"{primary_job}のための", "入口")


def semantic_body_units(text: str) -> tuple[str, ...]:
    """Keep complete Japanese sentence units together at narrow widths."""
    units = tuple(part for part in re.findall(r"[^。！？]+[。！？]|[^。！？]+$", text) if part)
    if not units or any(len(unit.strip()) < 3 for unit in units):
        raise ProductionCutoverError("BODY_SEMANTIC_UNIT_TOO_SHORT")
    return units


def _unit_markup(units: tuple[str, ...], class_name: str) -> str:
    return "".join(
        f'<span class="{class_name}">{_esc(unit)}</span>'
        for unit in units
    )


def render_authoritative_html(plan: Mapping[str, Any], directives: Mapping[str, Any]) -> str:
    """Render evidence HTML from directives, not industry profiles."""
    topology = directives["topology"]
    scenes = directives["scene_intents"]
    decision = plan["input"]["customer_decision_state"]
    offers = plan["input"]["company_truth"]["offers"]
    body_units = semantic_body_units("決めるための情報を整理します。")
    scene_markup = "".join(
        f'<section class="scene" data-scene="{_esc(scene["id"])}" data-intent="{_esc(scene["intent"])}"><span>{index:02d}</span><h2>{_esc(scene["intent"])}</h2><p>{_unit_markup(body_units, "semantic-body-unit")}</p></section>'
        for index, scene in enumerate(scenes, 1)
    )
    offer_markup = "".join(
        f'<li><strong>{_esc(item.get("name"))}</strong><span>{_esc(item.get("job"))}</span></li>'
        for item in offers
    )
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CompositionPlan Production Evidence</title>
<style>
:root{{font-family:system-ui,sans-serif;color:#171a18;background:#f3f4f1}}
*{{box-sizing:border-box}}body{{margin:0}}main{{max-width:1440px;margin:auto;padding:0 clamp(20px,6vw,96px);min-width:0;overflow-x:clip}}
header,footer{{padding:22px 0;border-bottom:1px solid #c9d2cc;display:flex;justify-content:space-between}}
.hero{{min-height:72svh;display:grid;grid-template-columns:1fr 1fr;gap:clamp(24px,8vw,120px);align-items:center}}
.hero[data-topology="guided_choice"]{{grid-template-columns:.8fr 1.2fr}}
.hero[data-topology="text_led_field"]{{grid-template-columns:1fr;max-width:840px}}
.hero[data-topology="relationship_media"]{{background:#e1ebe6}}
h1{{font-size:clamp(32px,6vw,78px);line-height:1.08;overflow-wrap:anywhere}}.lead{{font-size:clamp(17px,2vw,24px);line-height:1.7;overflow-wrap:anywhere}}
.offers{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;padding:0;list-style:none;min-width:0}}
.offers li{{background:#fff;border:1px solid #aebdb3;min-height:120px;padding:20px;display:grid;align-content:space-between;min-width:0;overflow-wrap:anywhere}}
.scene{{min-height:42svh;border-top:1px solid #bbc8c0;padding:clamp(44px,8vw,110px) 0;display:grid;grid-template-columns:64px 1fr;gap:20px}}
.scene h2{{font-size:clamp(28px,5vw,62px);margin:0;min-width:0;overflow-wrap:anywhere}}.scene p{{grid-column:2;line-height:1.8;min-width:0;overflow-wrap:anywhere}}
@media(max-width:767px){{.hero,.hero[data-topology="guided_choice"],.hero[data-topology="relationship_media"]{{grid-template-columns:1fr;min-height:70svh;padding:54px 0}}.hero[data-topology="text_led_field"]{{min-height:56svh}}.offers{{grid-template-columns:1fr}}.semantic-headline-unit,.semantic-body-unit{{display:inline-block;white-space:nowrap}}.scene{{grid-template-columns:40px 1fr;min-height:48svh}}}}
</style></head><body data-production-authority="composition_plan" data-plan-digest="{_esc(plan_digest(plan))}">
<main><header><strong>Current-industry Production</strong><span>authoritative plan render</span></header>
<section class="hero" data-topology="{_esc(topology["hero"])}" data-decision-job="{_esc(decision["primary_job"])}">
<div><small>authored decision</small><h1>{_unit_markup(semantic_headline_units(decision["primary_job"]), "semantic-headline-unit")}</h1><p class="lead">CompositionPlanの意図から、確認すべき情報を順に案内します。</p></div>
<div><small>core: {_esc(topology["core_decision"])}</small><ul class="offers">{offer_markup}</ul></div></section>
{scene_markup}<footer><span>scene order: {_esc(topology["scene_order"])}</span><span>CTA: {_esc(topology["closing"])}</span></footer></main></body></html>"""


def run_authoritative_generation(raw: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    """Generate one fail-closed current-industry Production evidence bundle."""
    plan = plan_current_industry_production(raw)
    directives = consume_current_industry_production(plan)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(render_authoritative_html(plan, directives), encoding="utf-8")
    manifest = {
        "schema_version": "issue99_current_industry_production_v1",
        "production_authority": "composition_plan",
        "input_digest": hashlib.sha256(_canonical(plan["input"]).encode("utf-8")).hexdigest(),
        "plan_digest": plan_digest(plan),
        "directives": {
            "topology": directives["topology"],
            "variation_vector": directives["variation_vector"],
            "scene_order": [item["id"] for item in directives["scene_intents"]],
            "responsive_widths": list(WIDTHS),
        },
        "trace": plan["cutover_trace"],
        "identity_routing": False,
        "reference_lookup": False,
        "legacy_profile_fallback": False,
        "human_visible_status": "PENDING_AOI_NOT_SELF_DECLARED",
    }
    (output / "production_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    return {"plan": plan, "directives": directives, "manifest": manifest, "output_dir": str(output)}


__all__ = [
    "CURRENT_INDUSTRIES", "WIDTHS", "ProductionCutoverError",
    "derive_current_industry_authorship_input", "plan_current_industry_production",
    "consume_current_industry_production", "render_authoritative_html",
    "run_authoritative_generation",
]
