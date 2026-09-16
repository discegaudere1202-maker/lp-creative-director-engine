"""Production Generation with Photography Direction / Visual Evidence Pipeline.

The pre-Round-1B generator is kept as a compatibility core. This module adds
role-first photography planning, asset selection/provenance, photo-aware
composition/rendering, and fake-evidence copy guards without changing the
existing factual Evidence/Safety boundary.
"""

from __future__ import annotations

from datetime import UTC, datetime
import html
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from . import production_generation_legacy as _legacy
from .photography import (
    build_asset_manifest,
    build_photo_role_map,
    guard_fake_evidence_copy,
    has_photo_authority,
    selected_asset_for_section,
    validate_asset_manifest,
    validate_photo_role_map,
)

SCHEMA_VERSION = _legacy.SCHEMA_VERSION
ENGINE_VERSION = _legacy.ENGINE_VERSION
RENDERER_VERSION = _legacy.RENDERER_VERSION
SUPPORTED_AUTHORITIES = _legacy.SUPPORTED_AUTHORITIES
GOAL_LABELS = _legacy.GOAL_LABELS
GOAL_NOUNS = _legacy.GOAL_NOUNS
GenerationResult = _legacy.GenerationResult
build_information_architecture = _legacy.build_information_architecture
build_design_tokens = _legacy.build_design_tokens


def build_company_understanding(raw: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    understanding = _legacy.build_company_understanding(raw, approved_evidence)
    readiness = dict(understanding.get("photo_replacement_readiness") or {})
    readiness.update({
        "status": "READY_FOR_ROLE_MATCHED_PHOTOGRAPHY",
        "proxy_role": "role_matched_photo_then_vector_support",
        "replacement_targets": ["実店舗・実現場・実商品・実人物・実作業・実作品写真"],
        "layout_constraints": ["同一photo_roleの実写真へ同じ構図意図で差し替え可能", "文字重なりなし", "mobile crop安全域を保持"],
        "proof_role": "visual_context_only_until_supported_by_approved_evidence",
        "asset_priority": ["free_stock", "generated", "vector"],
        "vector_role": "supporting_only",
    })
    understanding["photo_replacement_readiness"] = readiness
    return understanding


def build_creative_strategy(understanding: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    strategy = _legacy.build_creative_strategy(understanding, approved_evidence)
    strategy["photography_strategy"] = {
        "authority": "Photography is primary when a role-matched rights-cleared photo asset exists.",
        "selection_priority": ["free_stock", "generated", "vector"],
        "vector_role": "supporting_only",
        "evidence_boundary": "Photography creates visual context; factual proof still requires Safety-approved Evidence.",
    }
    return strategy


def build_copy(understanding: Mapping[str, Any], strategy: Mapping[str, Any], ia: Sequence[Mapping[str, Any]], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    copy = _legacy.build_copy(understanding, strategy, ia, approved_evidence)
    copy = guard_fake_evidence_copy(copy, approved_evidence)
    constraints = dict(copy.get("global_constraints") or {})
    constraints.update({
        "photo_linked_fake_evidence": "blocked_without_approved_evidence",
        "blocked_photo_labels": ["当社施工事例", "実際の施術風景", "生徒作品", "お客様写真", "実績写真"],
    })
    copy["global_constraints"] = constraints
    return copy


def build_art_direction(understanding: Mapping[str, Any], strategy: Mapping[str, Any], photo_role_map: Mapping[str, Any] | None = None) -> dict[str, Any]:
    art = _legacy.build_art_direction(understanding, strategy)
    art["photography_logic"] = (
        "Role-matched photography is the primary visual authority. Use rights-cleared free_stock first, "
        "generated imagery second, and engine vector scenes only as supporting fallback. Photography never "
        "becomes factual proof without approved Evidence."
    )
    art["visual_source"] = "asset_manifest_role_matched_photography"
    art["photo_role_map"] = dict(photo_role_map or {})
    art["photo_replacement_readiness"] = understanding.get("photo_replacement_readiness", {})
    forbidden = [item for item in art.get("forbidden_patterns", []) if item != "stock person"]
    forbidden.extend(["generic stock photo presented as company evidence", "photo implying an unverified result", "vector scene used as photography authority"])
    art["forbidden_patterns"] = list(dict.fromkeys(forbidden))
    dimensions = dict(art.get("art_direction_dimensions") or {})
    dimensions["crop_logic"] = "Respect photo role orientation and crop tolerance; preserve subject focus on mobile; vector geometry is supporting-only."
    dimensions["photography_authority"] = "free_stock_or_generated_when_rights_cleared"
    art["art_direction_dimensions"] = dimensions
    return art


def build_compositions(ia: Sequence[Mapping[str, Any]], art_direction: Mapping[str, Any], photo_role_map: Mapping[str, Any] | None = None, asset_manifest: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    compositions = _legacy.build_compositions(ia, art_direction)
    role_map = photo_role_map or {}
    manifest = asset_manifest or {}
    placement_type = {
        "opening": "hero_dominant_image",
        "truth": "midframe_proof_or_experience_image",
        "way_in": "craft_detail_or_quiet_chapter_image",
        "contact": "pre_cta_trust_image",
        "close": "cta_trust_support_image",
    }
    for item in compositions:
        section_id = str(item.get("section_id") or "")
        role, asset = selected_asset_for_section(manifest, role_map, section_id)
        if role:
            item["photo_role"] = role.get("photo_role")
            item["visual_subject"] = role.get("visual_subject")
            item["photo_business_purpose"] = role.get("business_purpose")
            item["photo_placement_type"] = placement_type.get(section_id, "supporting_image")
            item["preferred_orientation"] = role.get("preferred_orientation")
            item["crop_tolerance"] = role.get("crop_tolerance")
            item["people_distance"] = role.get("people_distance")
            item["proof_intent"] = role.get("proof_intent")
            item["photo_replacement_role"] = role.get("replacement_target")
        if asset:
            item["asset_id"] = asset.get("asset_id")
            item["asset_source_type"] = asset.get("source_type")
            item["photography_authority"] = has_photo_authority(asset)
        else:
            item["asset_id"] = ""
            item["asset_source_type"] = ""
            item["photography_authority"] = False
        item["image_role"] = str(item.get("photo_role") or "photography_slot") if item["photography_authority"] else "photography_slot_pending"
        item["vector_role"] = "supporting_only"
    return compositions


def build_render_spec(understanding: Mapping[str, Any], strategy: Mapping[str, Any], ia: Sequence[Mapping[str, Any]], copy: Mapping[str, Any], art_direction: Mapping[str, Any], tokens: Mapping[str, Any], compositions: Sequence[Mapping[str, Any]], safety_report: Mapping[str, Any], photo_role_map: Mapping[str, Any] | None = None, asset_manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
    spec = _legacy.build_render_spec(understanding, strategy, ia, copy, art_direction, tokens, compositions, safety_report)
    spec["photo_role_map"] = dict(photo_role_map or {})
    spec["asset_manifest"] = dict(asset_manifest or {})
    spec["photography_contract"] = {
        "asset_priority": ["free_stock", "generated", "vector"],
        "vector_role": "supporting_only",
        "photo_is_evidence": False,
        "fake_evidence_copy_guard": True,
    }
    return spec


def _esc(value: Any) -> str:
    return html.escape(str(value or "").strip(), quote=True)


def _safe_object_position(value: Any) -> str:
    if isinstance(value, Mapping):
        value = value.get("object_position") or value.get("position") or "center center"
    text = str(value or "center center").strip().lower()
    keyword = r"(?:left|center|right|top|bottom)"
    percent = r"(?:100|[0-9]{1,2})(?:\.\d+)?%"
    if re.fullmatch(fr"(?:{keyword}|{percent})(?:\s+(?:{keyword}|{percent}))?", text):
        return text
    return "center center"


def _photo_markup(asset: Mapping[str, Any] | None, role: Mapping[str, Any] | None, scene: str, *, hero: bool = False) -> str:
    if asset and has_photo_authority(asset):
        orientation = _esc(asset.get("preferred_orientation") or (role or {}).get("preferred_orientation") or "landscape")
        position = _safe_object_position(asset.get("crop"))
        loading = "eager" if hero else "lazy"
        fetchpriority = ' fetchpriority="high"' if hero else ""
        return (
            f'<figure class="photo-asset photo-asset--{orientation}" data-photo-role="{_esc(asset.get("photo_role"))}" '
            f'data-asset-id="{_esc(asset.get("asset_id"))}" data-source-type="{_esc(asset.get("source_type"))}" '
            f'data-proof-intent="{_esc((role or {}).get("proof_intent"))}">'
            f'<img src="{_esc(asset.get("asset_url"))}" alt="{_esc(asset.get("alt"))}" loading="{loading}"{fetchpriority} '
            f'style="object-position:{_esc(position)}"></figure>'
        )
    vector = _legacy._visual_scene_markup(scene)
    return f'<div class="vector-support" data-vector-role="supporting_only" data-photo-role="{_esc((role or {}).get("photo_role"))}">{vector}</div>'


def _append_photo_css(document: str) -> str:
    css = """
    .photo-asset{position:relative;overflow:hidden;margin:0;min-height:clamp(240px,34vw,500px);border:1px solid var(--ink);background:color-mix(in srgb,var(--paper) 88%,var(--ink));}
    .photo-asset img{display:block;width:100%;height:100%;min-height:inherit;object-fit:cover;}
    .photo-asset--portrait{aspect-ratio:4/5;max-height:620px}.photo-asset--square{aspect-ratio:1/1}.photo-asset--landscape{aspect-ratio:16/10}
    .vector-support{opacity:.72;position:relative}.vector-support::before{content:"";position:absolute;inset:0;z-index:4;pointer-events:none;border:1px dashed color-mix(in srgb,var(--ink) 20%,transparent)}
    .section[data-role="service_process"]>.photo-asset,.section[data-role="next_step"]>.photo-asset,.section[data-role="cta_zone"]>.photo-asset{margin-top:clamp(2rem,5vw,5rem)}
    @media(max-width:760px){.photo-asset,.photo-asset--portrait,.photo-asset--square,.photo-asset--landscape{aspect-ratio:4/3;min-height:clamp(210px,64vw,320px);max-height:none}.photo-asset img{object-fit:cover}.vector-support{opacity:.58}}
    """
    return document.replace("</style>", css + "</style>", 1)


def _inject_section_support(document: str, data_role: str, markup: str) -> str:
    if not markup:
        return document
    pattern = re.compile(rf'(<section\b[^>]*data-role="{re.escape(data_role)}"[^>]*>.*?)(</section>)', re.DOTALL)
    return pattern.sub(lambda match: match.group(1) + markup + match.group(2), document, count=1)


def render_html(spec: Mapping[str, Any]) -> str:
    document = _legacy.render_html(spec)
    role_map = spec.get("photo_role_map") or {}
    manifest = spec.get("asset_manifest") or {}
    scene = str(spec.get("art_direction", {}).get("visual_scene") or "calibration")
    legacy_scene = _legacy._visual_scene_markup(scene)
    opening_role, opening_asset = selected_asset_for_section(manifest, role_map, "opening")
    truth_role, truth_asset = selected_asset_for_section(manifest, role_map, "truth")
    document = document.replace(legacy_scene, _photo_markup(opening_asset, opening_role, scene, hero=True), 1)
    document = document.replace(legacy_scene, _photo_markup(truth_asset, truth_role, scene), 1)
    for section_id, data_role in (("way_in", "service_process"), ("contact", "next_step"), ("close", "cta_zone")):
        role, asset = selected_asset_for_section(manifest, role_map, section_id)
        if asset and has_photo_authority(asset):
            document = _inject_section_support(document, data_role, _photo_markup(asset, role, scene))
    return _append_photo_css(document)


def run_generation(raw: Mapping[str, Any], output_dir: str | Path, *, generation_id: str | None = None, mode: str = "production", iteration: int | None = None) -> GenerationResult:
    """Run the Production generator with role-first Photography Pipeline."""
    if mode not in {"production", "research", "test"}:
        raise ValueError(f"unsupported generation mode: {mode}")
    if not isinstance(raw, Mapping):
        raise ValueError("production input must be an object")
    raw = dict(raw)
    if iteration is not None:
        raw["generation_iteration"] = iteration
    _legacy._company(raw)
    goal = _legacy._text(raw.get("conversion_goal"))
    objections = raw.get("primary_objections") or []
    ledger = raw.get("evidence_ledger") or []
    safety = _legacy.evaluate_evidence_selection(goal, objections, ledger, requested_claims=raw.get("requested_claims") or [], require_production_clearance=mode == "production").to_dict()
    safety["hearing_plan"] = _legacy.plan_hearing(safety, conversion_goal=goal, primary_objections=objections, domain=_legacy._text(_legacy._company(raw).get("industry"))).to_dict()
    if mode == "production" and safety["safety_status"] in {"INVALID_INPUT", "HEARING_REQUIRED"}:
        raise RuntimeError("production generation blocked by Safety / Hearing: " + safety["safety_status"])
    approved = list(safety.get("eligible_evidence") or [])
    understanding = build_company_understanding(raw, approved)
    strategy = build_creative_strategy(understanding, approved)
    ia = build_information_architecture(understanding, strategy, approved)
    photo_role_map = build_photo_role_map(understanding, strategy, ia)
    role_errors = validate_photo_role_map(photo_role_map)
    if role_errors:
        raise RuntimeError("invalid photo_role_map: " + "; ".join(role_errors))
    asset_manifest = build_asset_manifest(raw, photo_role_map, visual_scene=_legacy._text(understanding.get("visual_scene")))
    asset_errors = validate_asset_manifest(asset_manifest)
    if asset_errors:
        raise RuntimeError("invalid asset_manifest: " + "; ".join(asset_errors))
    copy = build_copy(understanding, strategy, ia, approved)
    art = build_art_direction(understanding, strategy, photo_role_map)
    tokens = build_design_tokens(art)
    compositions = build_compositions(ia, art, photo_role_map, asset_manifest)
    render_spec = build_render_spec(understanding, strategy, ia, copy, art, tokens, compositions, safety, photo_role_map, asset_manifest)
    render_spec["approved_evidence"] = approved
    generation_id = generation_id or f"gen-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{_legacy._input_digest(raw)[:8]}"
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stages = {
        "company_understanding": understanding,
        "creative_strategy": strategy,
        "form_causality_manifest": {"schema_version": "form_causality_manifest_v1", "items": strategy.get("form_causality", []), "source": "Company Truth + Customer State + Conversion Goal"},
        "information_architecture": ia,
        "copy": copy,
        "art_direction": art,
        "design_tokens": tokens,
        "compositions": compositions,
        "render_spec": render_spec,
    }
    for name, value in stages.items():
        _legacy._write_json(output / f"{name}.json", value)
    _legacy._write_json(output / "photo_role_map.json", photo_role_map)
    _legacy._write_json(output / "asset_manifest.json", asset_manifest)
    (output / "index.html").write_text(render_html(render_spec), encoding="utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generation_id": generation_id,
        "company_id": understanding["company_id"],
        "company_name": understanding["company_name"],
        "mode": mode,
        "engine_version": ENGINE_VERSION,
        "renderer_version": RENDERER_VERSION,
        "generation_iteration": understanding["generation_iteration"],
        "input_digest": _legacy._input_digest(raw),
        "input_references": {"input_file": _legacy._text(raw.get("input_file")) or "inline_fixture", "source_urls": understanding["source_references"]},
        "strategy_output": "creative_strategy.json",
        "evidence_used": [{"claim": item.get("claim"), "evidence_id": item.get("evidence_id"), "source": item.get("source"), "verification_status": item.get("verification_status"), "rights_status": item.get("rights_status"), "placement": item.get("placement_candidates")} for item in approved],
        "photography_outputs": {"photo_role_map": "photo_role_map.json", "asset_manifest": "asset_manifest.json", "asset_selection_priority": ["free_stock", "generated", "vector"], "vector_role": "supporting_only"},
        "photo_replacement_readiness": understanding.get("photo_replacement_readiness", {}),
        "hearing_required": safety.get("hearing_required", []),
        "blocked_claims": safety.get("blocked_claims", []),
        "safety_status": safety.get("safety_status"),
        "output_status": "PRODUCTION_APPROVED" if mode == "production" else "NOT_PRODUCTION_APPROVED",
        "renderer_output": ["index.html"],
        "stage_outputs": [f"{name}.json" for name in stages],
        "manual_intervention": [],
        "generated_at": datetime.now(UTC).isoformat(),
    }
    _legacy._write_json(output / "evidence_manifest.json", {"generation_id": generation_id, "items": manifest["evidence_used"]})
    _legacy._write_json(output / "generation_manifest.json", manifest)
    return GenerationResult(generation_id, str(output), mode == "production", safety, stages, manifest)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run the structured Production Generation MVP")
    parser.add_argument("input", help="Production input JSON")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--generation-id")
    parser.add_argument("--iteration", type=int, default=None, help="Generic QA-loop iteration number")
    parser.add_argument("--mode", choices=("production", "research", "test"), default="production")
    args = parser.parse_args(argv)
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    raw = dict(raw)
    raw["input_file"] = args.input
    result = run_generation(raw, args.out, generation_id=args.generation_id, mode=args.mode, iteration=args.iteration)
    print(json.dumps({"generation_id": result.generation_id, "output_dir": result.output_dir, "safety_status": result.safety_report["safety_status"], "production_output_allowed": result.production_output_allowed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
