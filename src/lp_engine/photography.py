"""Photography Direction / Visual Evidence contracts.

This module is intentionally asset-source agnostic. Round 1B establishes the
machine-readable role, selection, rights and renderer contracts; actual stock
asset discovery is performed by the following asset-selection round.
"""

from __future__ import annotations

from copy import deepcopy
import html
from typing import Any, Mapping, Sequence

PHOTO_ROLE_FIELDS = (
    "photo_role",
    "visual_subject",
    "business_purpose",
    "replacement_target",
    "preferred_orientation",
    "crop_tolerance",
    "people_distance",
    "proof_intent",
)

ASSET_MANIFEST_FIELDS = (
    "asset_id",
    "photo_role",
    "source_type",
    "provider",
    "source",
    "asset_url",
    "creator",
    "rights_status",
    "license_terms_url",
    "checked_at",
    "visual_subject",
    "placement",
    "replacement_target",
    "crop",
    "alt",
)

ASSET_SOURCE_PRIORITY = {"free_stock": 0, "generated": 1, "vector": 2}
PHOTO_PLACEMENTS = (
    "hero_dominant_image",
    "mid_frame_proof_experience",
    "craft_detail_image",
    "quiet_chapter_image",
    "pre_cta_trust_image",
)

FAKE_EVIDENCE_TERMS = (
    "当社施工事例",
    "実際の施術風景",
    "生徒作品",
    "お客様写真",
    "実績写真",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _family_roles(family: str, category: str) -> list[dict[str, str]]:
    family = _text(family)
    category = _text(category)
    if family == "material_field":
        specs = [
            ("hero_home_finish", "住宅外観と仕上がりの素材感", "家を任せる仕事だと瞬時に伝える", "実施工後の住宅外観", "landscape", "medium", "none", "visual_context_only"),
            ("craft_handwork", "ローラー・刷毛・施工中の手元", "職人仕事と丁寧さを視覚化する", "実作業中の手元写真", "portrait", "tight", "close", "craft_context_only"),
            ("material_detail", "施工面・素材・仕上げの細部", "品質をディテールで理解させる", "実施工ディテール", "square", "tight", "none", "material_context_only"),
            ("trust_consultation", "住まいについて相談する人の距離感", "相談前の心理的ハードルを下げる", "実打ち合わせ・相談風景", "landscape", "medium", "mid", "human_context_only"),
        ]
    elif family == "care_experience":
        specs = [
            ("hero_treatment_space", "静かな施術空間と施術の気配", "安心感と体験の温度を最初に伝える", "実店舗と実施術シーン", "landscape", "medium", "mid", "experience_context_only"),
            ("hand_technique", "頭部への手技と施術者の手元", "技術感と身体感覚を伝える", "実施術中の手元", "portrait", "tight", "close", "craft_context_only"),
            ("sensory_detail", "タオル・照明・ベッド周りの静かなディテール", "リラックスの感覚を補強する", "実店舗ディテール", "square", "tight", "none", "sensory_context_only"),
            ("welcome_human", "相談・迎え入れの人間的な距離感", "初回来店の不安を下げる", "実接客・相談風景", "landscape", "medium", "mid", "human_context_only"),
        ]
    elif family == "learning_studio":
        specs = [
            ("hero_shared_cooking", "手を動かしながら学ぶ共有時間", "完成品だけでなく教室体験を伝える", "実教室・レッスン風景", "landscape", "medium", "mid", "experience_context_only"),
            ("ingredient_story", "食材・道具・下準備の手触り", "素材への関心と暮らしの温度を伝える", "実食材・実テーブル", "square", "tight", "none", "material_context_only"),
            ("hands_in_action", "包丁・混ぜる・盛り付け等の手元", "学びの具体性を見せる", "実レッスン中の手元", "portrait", "tight", "close", "craft_context_only"),
            ("finished_table", "完成物と共有する場", "体験後の達成感を想起させる", "実教室の完成物・食卓", "landscape", "medium", "far", "outcome_context_only"),
        ]
    else:
        specs = [
            ("hero_context", f"{category or 'サービス'}の第一印象を伝える場面", "何の事業かを一瞬で理解させる", "同じ役割の実事業写真", "landscape", "medium", "mid", "visual_context_only"),
            ("mid_experience", f"{category or 'サービス'}を利用する体験の場面", "中盤で理解と感情を補強する", "同じ役割の実体験写真", "landscape", "medium", "mid", "experience_context_only"),
            ("craft_detail", "手元・素材・道具などの細部", "仕事の具体性を伝える", "実作業・実商品ディテール", "portrait", "tight", "close", "craft_context_only"),
            ("trust_human", "相談・迎え入れ・人の気配", "CTA前の信頼を補強する", "実人物・実接客写真", "landscape", "medium", "mid", "human_context_only"),
        ]
    return [dict(zip(PHOTO_ROLE_FIELDS, spec)) for spec in specs]


def build_photo_role_map(understanding: Mapping[str, Any], strategy: Mapping[str, Any], ia: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    roles = _family_roles(_text(understanding.get("industry_visual_family")), _text(understanding.get("service_category")))
    placements = list(PHOTO_PLACEMENTS)
    for index, role in enumerate(roles):
        role["placement"] = placements[min(index, len(placements) - 1)]
    # A quiet frame is a composition option, never a forced extra photo count.
    if len(roles) >= 3:
        roles[2]["secondary_placement"] = "quiet_chapter_image"
    return {
        "schema_version": "photo_role_map_v1",
        "selection_mode": "role_driven_not_fixed_count",
        "roles": roles,
        "section_role_map": {
            "hero_orientation": roles[0]["photo_role"] if roles else "",
            "company_truth": roles[1]["photo_role"] if len(roles) > 1 else roles[0]["photo_role"],
            "service_process": roles[2]["photo_role"] if len(roles) > 2 else "",
            "next_step": roles[-1]["photo_role"] if roles else "",
            "cta_zone": roles[-1]["photo_role"] if roles else "",
        },
    }


def _normalized_asset(item: Mapping[str, Any]) -> dict[str, str]:
    normalized = {field: _text(item.get(field)) for field in ASSET_MANIFEST_FIELDS}
    source_type = normalized["source_type"]
    if source_type not in ASSET_SOURCE_PRIORITY:
        raise ValueError(f"unsupported photography source_type: {source_type}")
    normalized["vector_role"] = "supporting_only" if source_type == "vector" else "photography_candidate"
    return normalized


def build_asset_manifest(candidates: Sequence[Mapping[str, Any]], photo_role_map: Mapping[str, Any]) -> dict[str, Any]:
    assets = [_normalized_asset(item) for item in candidates]
    assets.sort(key=lambda item: (ASSET_SOURCE_PRIORITY[item["source_type"]], item["asset_id"]))
    role_names = [_text(item.get("photo_role")) for item in photo_role_map.get("roles", [])]
    selected_roles = {_text(item.get("photo_role")) for item in assets if _text(item.get("asset_url"))}
    return {
        "schema_version": "photography_asset_manifest_v1",
        "source_priority": ["free_stock", "generated", "vector"],
        "vector_policy": "supporting_only_not_primary_photography",
        "assets": assets,
        "pending_roles": [role for role in role_names if role and role not in selected_roles],
    }


def select_asset_for_role(asset_manifest: Mapping[str, Any], photo_role: str) -> dict[str, str] | None:
    candidates = [dict(item) for item in asset_manifest.get("assets", []) if _text(item.get("photo_role")) == _text(photo_role) and _text(item.get("asset_url"))]
    if not candidates:
        return None
    candidates.sort(key=lambda item: ASSET_SOURCE_PRIORITY.get(_text(item.get("source_type")), 99))
    primary = [item for item in candidates if _text(item.get("source_type")) != "vector"]
    return primary[0] if primary else candidates[0]


def connect_photo_roles_to_compositions(compositions: Sequence[Mapping[str, Any]], photo_role_map: Mapping[str, Any], asset_manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    section_map = dict(photo_role_map.get("section_role_map") or {})
    placement_by_section = {
        "hero_orientation": "hero_dominant_image",
        "company_truth": "mid_frame_proof_experience",
        "service_process": "craft_detail_image",
        "next_step": "quiet_chapter_image",
        "cta_zone": "pre_cta_trust_image",
    }
    result: list[dict[str, Any]] = []
    for composition in compositions:
        item = dict(composition)
        section_role = _text(item.get("section_role"))
        role = _text(section_map.get(section_role))
        asset = select_asset_for_role(asset_manifest, role) if role else None
        item["photo_role"] = role
        item["photo_placement"] = placement_by_section.get(section_role, "")
        item["photo_asset_id"] = _text((asset or {}).get("asset_id"))
        item["photo_source_type"] = _text((asset or {}).get("source_type"))
        item["vector_role"] = "supporting_only"
        result.append(item)
    return result


def guard_fake_evidence_copy(payload: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    approved_text = "\n".join(_text(item.get("claim")) for item in approved_evidence)

    def visit(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item) for item in value]
        if isinstance(value, str):
            for term in FAKE_EVIDENCE_TERMS:
                if term in value and term not in approved_text:
                    raise ValueError(f"unsupported fake-evidence photo copy blocked: {term}")
        return value

    return visit(deepcopy(dict(payload)))


def render_photo_asset(asset: Mapping[str, Any] | None) -> str:
    if not asset or not _text(asset.get("asset_url")):
        return ""
    orientation = _text(asset.get("preferred_orientation")) or _text(asset.get("orientation")) or "landscape"
    crop = _text(asset.get("crop")) or "50% 50%"
    source_type = _text(asset.get("source_type"))
    if source_type == "vector":
        return ""
    return (
        f'<figure class="photo-frame photo-frame--{html.escape(orientation, quote=True)}" '
        f'data-photo-role="{html.escape(_text(asset.get("photo_role")), quote=True)}" '
        f'data-source-type="{html.escape(source_type, quote=True)}">'
        f'<img src="{html.escape(_text(asset.get("asset_url")), quote=True)}" '
        f'alt="{html.escape(_text(asset.get("alt")), quote=True)}" loading="eager" '
        f'style="object-position:{html.escape(crop, quote=True)}" /></figure>'
    )


def photography_css() -> str:
    return """
.photo-frame{margin:0;overflow:hidden;min-height:260px;background:rgba(0,0,0,.04)}
.photo-frame img{display:block;width:100%;height:100%;min-height:260px;object-fit:cover}
.photo-frame--portrait{aspect-ratio:4/5}.photo-frame--square{aspect-ratio:1/1}.photo-frame--landscape{aspect-ratio:16/10}
@media(max-width:640px){.photo-frame,.photo-frame img{min-height:220px}.photo-frame--landscape{aspect-ratio:4/3}.photo-frame img{object-position:50% 50%}}
""".strip()
