"""Asset-bound wrapper around the authoritative current-industry Production renderer.

This layer is deliberately post-CompositionPlan: it may realize frozen media
placements, but it cannot mutate Family, topology, scene order, or decision logic.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from .authored_composition_contract import plan_digest
from .production_cutover import render_authoritative_html, run_authoritative_generation
from .visual_asset_library import asset_binding_css, render_asset_binding


class AssetBoundProductionError(RuntimeError):
    pass


def _binding_markup(bindings: Mapping[str, Mapping[str, Any]] | None, key: str) -> str:
    if not bindings or key not in bindings:
        return ""
    return render_asset_binding(bindings[key])


def render_asset_bound_authoritative_html(
    plan: Mapping[str, Any],
    directives: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> str:
    """Inject approved AssetBinding markup without re-inferring authored structure."""
    if plan.get("production_authority") != "composition_plan":
        raise AssetBoundProductionError("COMPOSITION_PLAN_NOT_AUTHORITATIVE")
    if plan.get("input", {}).get("creative_family", {}).get("frozen") is not True:
        raise AssetBoundProductionError("FAMILY_NOT_FROZEN")
    original_topology = deepcopy(plan.get("topology"))
    original_scenes = deepcopy(plan.get("scene_intents"))
    rendered = render_authoritative_html(plan, directives)

    hero = _binding_markup(asset_bindings, "hero")
    if hero:
        marker = '<div><small>core: '
        idx = rendered.find(marker)
        if idx < 0:
            raise AssetBoundProductionError("HERO_BINDING_ANCHOR_MISSING")
        insert_at = idx + len("<div>")
        rendered = rendered[:insert_at] + f'<div class="asset-realization asset-realization--hero">{hero}</div>' + rendered[insert_at:]

    for scene in directives.get("scene_intents", []):
        scene_id = str(scene.get("id") or "")
        markup = _binding_markup(asset_bindings, scene_id)
        if not markup:
            continue
        closing = "</section>"
        anchor = f'data-scene="{scene_id}"'
        start = rendered.find(anchor)
        if start < 0:
            raise AssetBoundProductionError(f"SCENE_BINDING_ANCHOR_MISSING:{scene_id}")
        end = rendered.find(closing, start)
        if end < 0:
            raise AssetBoundProductionError(f"SCENE_BINDING_CLOSE_MISSING:{scene_id}")
        rendered = rendered[:end] + f'<div class="asset-realization asset-realization--scene">{markup}</div>' + rendered[end:]

    css = (
        asset_binding_css()
        + ".asset-realization{min-width:0}.asset-realization--scene{grid-column:2}"
        + "@media(max-width:480px){footer{flex-direction:column;gap:8px;align-items:flex-start}"
        + "footer span{display:block;max-width:100%;overflow-wrap:anywhere}}"
    )
    rendered = rendered.replace("</style>", css + "</style>", 1)
    if plan.get("topology") != original_topology or plan.get("scene_intents") != original_scenes:
        raise AssetBoundProductionError("ASSET_LAYER_MUTATED_AUTHORSHIP")
    return rendered


def run_asset_bound_generation(
    raw: Mapping[str, Any],
    output_dir: str | Path,
    *,
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Run authoritative generation, then bind only pre-selected visual assets."""
    result = run_authoritative_generation(raw, output_dir)
    plan = result["plan"]
    directives = result["directives"]
    output = Path(output_dir)
    html = render_asset_bound_authoritative_html(plan, directives, asset_bindings)
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
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result["manifest"] = manifest
    result["asset_bindings"] = deepcopy(dict(asset_bindings))
    return result


__all__ = ["AssetBoundProductionError", "render_asset_bound_authoritative_html", "run_asset_bound_generation"]
