from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


path = Path("src/lp_engine/production_generation.py")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    "from .hearing import plan_hearing\n",
    "from .hearing import plan_hearing\nfrom .photography import (\n    build_asset_manifest,\n    build_photo_role_map,\n    connect_photo_roles_to_compositions,\n    guard_fake_evidence_copy,\n    photography_css,\n    render_photo_asset,\n    select_asset_for_role,\n)\n",
    "photography imports",
)

text = replace_once(
    text,
    "    copy = build_copy(understanding, strategy, ia, approved)\n    art = build_art_direction(understanding, strategy)\n    tokens = build_design_tokens(art)\n    compositions = build_compositions(ia, art)\n    render_spec = build_render_spec(understanding, strategy, ia, copy, art, tokens, compositions, safety)\n    render_spec[\"approved_evidence\"] = approved\n",
    "    copy = guard_fake_evidence_copy(build_copy(understanding, strategy, ia, approved), approved)\n    photo_role_map = build_photo_role_map(understanding, strategy, ia)\n    asset_manifest = build_asset_manifest(raw.get(\"photo_assets\") or [], photo_role_map)\n    understanding[\"photo_replacement_readiness\"] = {\n        **dict(understanding.get(\"photo_replacement_readiness\") or {}),\n        \"proxy_role\": \"role_selected_photography_asset\",\n        \"source_priority\": [\"free_stock\", \"generated\", \"vector\"],\n        \"vector_role\": \"supporting_only\",\n    }\n    art = build_art_direction(understanding, strategy)\n    art[\"photo_role_map\"] = photo_role_map\n    art[\"asset_selection_policy\"] = {\n        \"priority\": [\"free_stock\", \"generated\", \"vector\"],\n        \"vector_role\": \"supporting_only_not_primary_photography\",\n    }\n    art[\"visual_source\"] = \"photography_pipeline\"\n    art[\"vector_role\"] = \"supporting_only\"\n    art[\"photography_logic\"] = \"Role-driven photography is the primary visual authority; vector scenes are support only.\"\n    tokens = build_design_tokens(art)\n    base_compositions = build_compositions(ia, art)\n    ia_by_id = {_text(item.get(\"section_id\")): item for item in ia}\n    compositions_with_roles = [\n        {**item, \"section_role\": _text(ia_by_id.get(_text(item.get(\"section_id\")), {}).get(\"section_role\"))}\n        for item in base_compositions\n    ]\n    compositions = connect_photo_roles_to_compositions(compositions_with_roles, photo_role_map, asset_manifest)\n    render_spec = build_render_spec(understanding, strategy, ia, copy, art, tokens, compositions, safety)\n    render_spec[\"approved_evidence\"] = approved\n    render_spec[\"photo_role_map\"] = photo_role_map\n    render_spec[\"asset_manifest\"] = asset_manifest\n",
    "run_generation photography stages",
)

text = replace_once(
    text,
    "        \"copy\": copy,\n        \"art_direction\": art,\n",
    "        \"copy\": copy,\n        \"photo_role_map\": photo_role_map,\n        \"asset_manifest\": asset_manifest,\n        \"art_direction\": art,\n",
    "stage outputs",
)

text = replace_once(
    text,
    "        \"strategy_output\": \"creative_strategy.json\",\n",
    "        \"strategy_output\": \"creative_strategy.json\",\n        \"photo_role_map_output\": \"photo_role_map.json\",\n        \"asset_manifest_output\": \"asset_manifest.json\",\n",
    "manifest photography outputs",
)

text = replace_once(
    text,
    "    scene_markup = _visual_scene_markup(_text(art.get(\"visual_scene\")))\n    return f'''<!doctype html>\n<html lang=\"ja\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><meta name=\"robots\" content=\"noindex\"><title>{name}｜{_esc(hero[\"headline\"])}</title><style>{_render_styles(tokens)}</style></head>\n",
    "    photo_role_map = dict(spec.get(\"photo_role_map\") or {})\n    asset_manifest = dict(spec.get(\"asset_manifest\") or {})\n    hero_role = _text((photo_role_map.get(\"section_role_map\") or {}).get(\"hero_orientation\"))\n    hero_asset = select_asset_for_role(asset_manifest, hero_role) if hero_role else None\n    photo_markup = render_photo_asset(hero_asset)\n    vector_markup = _visual_scene_markup(_text(art.get(\"visual_scene\")))\n    scene_markup = photo_markup or f'<div data-vector-role=\"supporting_only\">{vector_markup}</div>'\n    return f'''<!doctype html>\n<html lang=\"ja\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><meta name=\"robots\" content=\"noindex\"><title>{name}｜{_esc(hero[\"headline\"])}</title><style>{_render_styles(tokens)}{photography_css()}</style></head>\n",
    "renderer photography asset",
)

path.write_text(text, encoding="utf-8")


test_path = Path("tests/test_production_generation.py")
test_text = test_path.read_text(encoding="utf-8")
test_text = replace_once(
    test_text,
    '                "company_understanding", "creative_strategy", "information_architecture", "copy",\n                "form_causality_manifest", "art_direction", "design_tokens", "compositions", "render_spec",\n',
    '                "company_understanding", "creative_strategy", "information_architecture", "copy",\n                "form_causality_manifest", "photo_role_map", "asset_manifest", "art_direction", "design_tokens", "compositions", "render_spec",\n',
    "production generation expected stages",
)
test_path.write_text(test_text, encoding="utf-8")
