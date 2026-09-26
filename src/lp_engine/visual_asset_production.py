"""Asset-bound wrapper around the authoritative current-industry Production renderer.

Issue #116 keeps this layer post-CompositionPlan, then applies the premium
authorship system (PU1-PU8).  Media realization may not mutate Family,
topology, scene order, decision logic, or evidence state.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from .authored_composition_contract import plan_digest
from .premium_authorship import build_premium_uplift, render_premium_asset_bound_html
from .production_cutover import run_authoritative_generation


class AssetBoundProductionError(RuntimeError):
    pass


# 320px requires headline meaning units to stay whole without clipping.  These
# are public-copy semantic refinements only; they do not touch CompositionPlan.
_MOBILE_SAFE_HERO_UNITS = {
    "choose": ["違いが見える", "選びやすく", "なる。"],
    "understand": ["はじめる前に", "流れを", "わかりやすく"],
    "trust": ["任せる前に", "安心できる", "理由を。"],
    "compare": ["比べるほど", "自分の基準が", "見えてくる。"],
    "prepare": ["迷いを減らし", "気持ちよく", "はじめる。"],
    "act": ["考えすぎる", "その前に", "次の一歩を", "軽く。"],
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
    html = render_premium_asset_bound_html(plan, directives, asset_bindings, premium)
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
