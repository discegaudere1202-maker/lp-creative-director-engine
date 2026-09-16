"""Photography Direction / Visual Evidence Pipeline contracts.

This module keeps photography planning, asset selection, provenance, and
photo-linked copy safety separate from factual Evidence. Photography assets may
create visual context and emotional authority, but they do not become proof of
a real result, real customer, real place, or real work unless Safety-approved
Evidence explicitly supports that claim.
"""

from __future__ import annotations

from copy import deepcopy
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

ASSET_FIELDS = (
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

SOURCE_PRIORITY = {"free_stock": 0, "generated": 1, "vector": 2}
PHOTO_PRIMARY_SOURCE_TYPES = {"free_stock", "generated"}

FAKE_EVIDENCE_REPLACEMENTS = {
    "当社施工事例": "施工イメージ",
    "実際の施術風景": "施術イメージ",
    "生徒作品": "料理・制作イメージ",
    "お客様写真": "体験イメージ",
    "実績写真": "サービスイメージ",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _category_family(understanding: Mapping[str, Any]) -> str:
    family = _text(understanding.get("industry_visual_family"))
    if family and family not in {"default", "local_service"}:
        return family
    category = _text(understanding.get("service_category"))
    rules = (
        (("外壁塗装", "屋根", "造園", "害虫", "不用品", "ハウスクリーニング", "エアコンクリーニング"), "material_field"),
        (("鍼灸", "脱毛", "ヘッドスパ", "ヨガ", "ピラティス"), "care_experience"),
        (("音楽教室", "ダンス", "料理教室", "フラワー", "ハンドメイド"), "learning_studio"),
        (("結婚相談", "相談所"), "relationship_consultation"),
        (("フォトグラファー", "出張撮影", "写真スタジオ"), "image_story"),
        (("カーコーティング", "car detailing", "バイク", "自動車板金", "デントリペア"), "machine_craft"),
        (("家事代行", "生活支援", "ドッグ", "ペット"), "local_care"),
    )
    folded = category.casefold()
    for needles, result in rules:
        if any(needle.casefold() in folded for needle in needles):
            return result
    return family or "local_service"


def _role(photo_role: str, visual_subject: str, business_purpose: str, replacement_target: str,
          preferred_orientation: str, crop_tolerance: str, people_distance: str,
          proof_intent: str, placements: Sequence[str]) -> dict[str, Any]:
    return {
        "photo_role": photo_role,
        "visual_subject": visual_subject,
        "business_purpose": business_purpose,
        "replacement_target": replacement_target,
        "preferred_orientation": preferred_orientation,
        "crop_tolerance": crop_tolerance,
        "people_distance": people_distance,
        "proof_intent": proof_intent,
        "placement_candidates": list(placements),
    }


def build_photo_role_map(understanding: Mapping[str, Any], strategy: Mapping[str, Any],
                         ia: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Create role-first photography direction before any concrete asset search."""
    family = _category_family(understanding)
    by_family: dict[str, list[dict[str, Any]]] = {
        "material_field": [
            _role("hero_place_finish", "住宅・建物外観と仕上がりの素材感", "家や現場を任せる仕事であることを一瞬で伝える", "実施工後の住宅・建物外観", "landscape", "medium", "none_or_far", "visual_context_only", ("opening",)),
            _role("midframe_material_context", "施工対象・素材・現場の広がり", "サービス対象と施工価値を具体化する", "実施工現場または実施工対象", "landscape", "medium", "none_or_far", "visual_context_only", ("truth",)),
            _role("craft_handwork", "ローラー・刷毛・工具など作業中の手元", "職人仕事・丁寧さ・工程の具体性を伝える", "実作業中の手元・職人写真", "portrait", "tight", "close", "craft_context_not_result_proof", ("way_in",)),
            _role("material_detail", "表面・塗装面・素材ディテール", "品質を触感のある画面として見せる", "実施工ディテール", "square", "tight", "none", "material_context_not_result_proof", ("way_in", "truth")),
            _role("trust_consultation", "住宅・現場について相談している穏やかな接点", "問い合わせ前の心理的距離を縮める", "実打ち合わせ・現地確認風景", "landscape", "medium", "mid", "human_context_only", ("contact", "close")),
        ],
        "care_experience": [
            _role("hero_treatment_space", "静かな施術空間とケアを受ける時間", "施術サービスと安心できる世界観を一瞬で伝える", "実店舗・実施術シーン", "landscape", "medium", "mid", "experience_context_only", ("opening",)),
            _role("midframe_care_experience", "施術者と利用者の落ち着いた距離感", "サービスを受ける時間のイメージを具体化する", "実施術・実接客風景", "landscape", "medium", "mid", "experience_context_only", ("truth",)),
            _role("hand_technique", "頭部・手元・施術者の動き", "手技・専門性・身体感覚を伝える", "実施術手元", "portrait", "tight", "close", "craft_context_not_treatment_proof", ("way_in",)),
            _role("sensory_detail", "タオル・照明・ベッド周りなど空間ディテール", "静けさ・温度感・リラックスの感覚をつくる", "実空間ディテール", "square", "tight", "none", "sensory_context_only", ("way_in", "truth")),
            _role("welcome_human", "相談・迎え入れ・予約前の自然な接点", "初回来店の不安を下げる", "実接客・カウンセリング風景", "landscape", "medium", "mid", "human_context_only", ("contact", "close")),
        ],
        "learning_studio": [
            _role("hero_shared_cooking", "手を動かしながら料理・制作を学ぶ時間", "完成物だけでなく教室体験そのものを一瞬で伝える", "実教室・実レッスン風景", "landscape", "medium", "mid", "class_context_only", ("opening",)),
            _role("midframe_shared_table", "食材・道具・人が集まるテーブル", "人との時間と学びの場を具体化する", "実教室テーブル・参加風景", "landscape", "medium", "mid", "class_context_only", ("truth",)),
            _role("hands_in_action", "包丁・混ぜる・盛り付けなど作業中の手元", "学びのプロセスと手仕事の楽しさを伝える", "実レッスン手元", "portrait", "tight", "close", "craft_context_not_student_proof", ("way_in",)),
            _role("ingredient_story", "食材・下準備・道具・料理のディテール", "素材感と日常へつながる具体性をつくる", "実食材・実料理・実道具", "square", "tight", "none", "product_context_not_student_work_proof", ("way_in", "truth")),
            _role("trust_human", "講師と参加者が自然に会話する距離感", "初参加の不安を下げ教室の温度を伝える", "実講師・実参加風景", "landscape", "medium", "mid", "human_context_only", ("contact", "close")),
        ],
    }
    generic = [
        _role("hero_context", "サービスが行われる場所・対象・時間", "何のサービスかを一瞬で伝える", "同じ役割の実店舗・実現場・実商品・実人物写真", "landscape", "medium", "mid_or_none", "visual_context_only", ("opening",)),
        _role("midframe_experience", "サービスを受ける・選ぶ・使う具体的な場面", "Hero以降の理解と感情を支える", "同じ役割の実体験・実サービス写真", "landscape", "medium", "mid", "experience_context_only", ("truth",)),
        _role("craft_or_detail", "仕事の手元・道具・素材・商品ディテール", "仕事の具体性とCraftを伝える", "同じ役割の実作業・実素材・実商品写真", "portrait", "tight", "close_or_none", "craft_context_only", ("way_in",)),
        _role("pre_cta_trust", "問い合わせ前の人・場所・接点", "行動直前の心理的距離を縮める", "同じ役割の実人物・実接客・実場所写真", "landscape", "medium", "mid", "human_context_only", ("contact", "close")),
    ]
    roles = by_family.get(family, generic)
    valid_sections = {_text(item.get("section_id")) for item in ia}
    filtered = []
    for item in roles:
        role = dict(item)
        placements = [p for p in role["placement_candidates"] if p in valid_sections]
        if placements:
            role["placement_candidates"] = placements
            filtered.append(role)
    return {
        "schema_version": "photo_role_map_v1",
        "industry_visual_family": family,
        "company_truth": _text(understanding.get("company_truth")),
        "customer_state": dict(understanding.get("customer_state") or {}),
        "selection_basis": "company_truth + customer_state + service_category + section_role",
        "roles": filtered,
    }


def _normalize_asset(candidate: Mapping[str, Any], role: Mapping[str, Any], *, default_placement: str) -> dict[str, Any]:
    source_type = _text(candidate.get("source_type")).lower()
    if source_type not in SOURCE_PRIORITY:
        source_type = "vector"
    item = {
        "asset_id": _text(candidate.get("asset_id")) or f"{_text(role.get('photo_role'))}-{source_type}",
        "photo_role": _text(role.get("photo_role")),
        "source_type": source_type,
        "provider": _text(candidate.get("provider")),
        "source": _text(candidate.get("source")),
        "asset_url": _text(candidate.get("asset_url")),
        "creator": _text(candidate.get("creator")),
        "rights_status": _text(candidate.get("rights_status")),
        "license_terms_url": _text(candidate.get("license_terms_url")),
        "checked_at": _text(candidate.get("checked_at")),
        "visual_subject": _text(candidate.get("visual_subject")) or _text(role.get("visual_subject")),
        "placement": _text(candidate.get("placement")) or default_placement,
        "replacement_target": _text(candidate.get("replacement_target")) or _text(role.get("replacement_target")),
        "crop": candidate.get("crop") if candidate.get("crop") not in (None, "") else "center center",
        "alt": _text(candidate.get("alt")) or _text(role.get("visual_subject")),
        "preferred_orientation": _text(candidate.get("preferred_orientation")) or _text(role.get("preferred_orientation")),
        "crop_tolerance": _text(candidate.get("crop_tolerance")) or _text(role.get("crop_tolerance")),
        "people_distance": _text(candidate.get("people_distance")) or _text(role.get("people_distance")),
        "proof_intent": _text(candidate.get("proof_intent")) or _text(role.get("proof_intent")),
    }
    item["photography_authority"] = source_type in PHOTO_PRIMARY_SOURCE_TYPES and bool(item["asset_url"])
    item["supporting_only"] = source_type == "vector"
    item["selection_rank"] = SOURCE_PRIORITY[source_type]
    return item


def _vector_support_asset(role: Mapping[str, Any], *, placement: str, scene: str) -> dict[str, Any]:
    return _normalize_asset({
        "asset_id": f"{_text(role.get('photo_role'))}-vector-support",
        "source_type": "vector", "provider": "lp_engine",
        "source": f"engine_generated_vector_scene:{scene or 'calibration'}", "asset_url": "",
        "creator": "lp_engine", "rights_status": "ENGINE_GENERATED_SUPPORT_ONLY",
        "license_terms_url": "", "checked_at": "", "placement": placement,
        "crop": "center center", "alt": "",
    }, role, default_placement=placement)


def build_asset_manifest(raw: Mapping[str, Any], photo_role_map: Mapping[str, Any], *, visual_scene: str = "") -> dict[str, Any]:
    """Select free_stock > generated > vector without discovering assets in Round 1B."""
    supplied = raw.get("photo_assets")
    if not isinstance(supplied, Sequence) or isinstance(supplied, (str, bytes)):
        supplied = []
    supplied = [item for item in supplied if isinstance(item, Mapping)]
    selected_items: list[dict[str, Any]] = []
    candidate_records: list[dict[str, Any]] = []
    for role in photo_role_map.get("roles", []):
        if not isinstance(role, Mapping):
            continue
        placements = list(role.get("placement_candidates") or [])
        placement = _text(placements[0] if placements else "")
        photo_role = _text(role.get("photo_role"))
        matches = [_normalize_asset(item, role, default_placement=placement) for item in supplied if _text(item.get("photo_role")) == photo_role]
        matches.sort(key=lambda item: (SOURCE_PRIORITY.get(_text(item.get("source_type")), 99), _text(item.get("asset_id"))))
        candidate_records.extend(matches)
        usable_photo = next((item for item in matches if item["source_type"] in PHOTO_PRIMARY_SOURCE_TYPES and bool(item["asset_url"]) and bool(item["rights_status"])), None)
        selected = usable_photo or (matches[0] if matches and matches[0]["source_type"] == "vector" else None)
        if selected is None:
            selected = _vector_support_asset(role, placement=placement, scene=visual_scene)
        selected = dict(selected)
        selected["selected"] = True
        selected_items.append(selected)
    return {
        "schema_version": "asset_manifest_v1",
        "selection_policy": {
            "priority": ["free_stock", "generated", "vector"],
            "photography_primary_source_types": ["free_stock", "generated"],
            "vector_role": "supporting_only",
            "rights_required_for_photo_selection": True,
            "fake_evidence_policy": "visual context is not factual proof",
        },
        "items": selected_items,
        "candidates": candidate_records,
    }


def selected_asset_for_section(asset_manifest: Mapping[str, Any], photo_role_map: Mapping[str, Any], section_id: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    roles = [item for item in photo_role_map.get("roles", []) if isinstance(item, Mapping)]
    role = next((item for item in roles if section_id in (item.get("placement_candidates") or [])), None)
    if role is None:
        return None, None
    role_name = _text(role.get("photo_role"))
    assets = [item for item in asset_manifest.get("items", []) if isinstance(item, Mapping)]
    asset = next((item for item in assets if _text(item.get("photo_role")) == role_name and item.get("selected", True)), None)
    return dict(role), dict(asset) if asset else None


def has_photo_authority(asset: Mapping[str, Any] | None) -> bool:
    return bool(asset and _text(asset.get("source_type")) in PHOTO_PRIMARY_SOURCE_TYPES and _text(asset.get("asset_url")) and _text(asset.get("rights_status")))


def _supported_fake_phrases(approved_evidence: Sequence[Mapping[str, Any]]) -> set[str]:
    claims = [_text(item.get("claim")) for item in approved_evidence]
    return {phrase for phrase in FAKE_EVIDENCE_REPLACEMENTS if any(phrase in claim for claim in claims)}


def guard_fake_evidence_copy(payload: Any, approved_evidence: Sequence[Mapping[str, Any]]) -> Any:
    """Neutralize evidence-sounding photo labels unless approved Evidence supports them."""
    supported = _supported_fake_phrases(approved_evidence)
    def sanitize(value: Any) -> Any:
        if isinstance(value, str):
            result = value
            for phrase, replacement in FAKE_EVIDENCE_REPLACEMENTS.items():
                if phrase not in supported:
                    result = result.replace(phrase, replacement)
            return result
        if isinstance(value, list):
            return [sanitize(item) for item in value]
        if isinstance(value, tuple):
            return tuple(sanitize(item) for item in value)
        if isinstance(value, Mapping):
            return {key: sanitize(item) for key, item in value.items()}
        return value
    return sanitize(deepcopy(payload))


def validate_photo_role_map(photo_role_map: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for index, role in enumerate(photo_role_map.get("roles", [])):
        if not isinstance(role, Mapping):
            errors.append(f"roles[{index}] must be an object")
            continue
        for field in PHOTO_ROLE_FIELDS:
            if field not in role or role[field] in (None, ""):
                errors.append(f"roles[{index}].{field} is required")
    return errors


def validate_asset_manifest(asset_manifest: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = asset_manifest.get("selection_policy") or {}
    if list(policy.get("priority") or []) != ["free_stock", "generated", "vector"]:
        errors.append("selection_policy.priority must be free_stock > generated > vector")
    if _text(policy.get("vector_role")) != "supporting_only":
        errors.append("selection_policy.vector_role must be supporting_only")
    for index, item in enumerate(asset_manifest.get("items", [])):
        if not isinstance(item, Mapping):
            errors.append(f"items[{index}] must be an object")
            continue
        for field in ASSET_FIELDS:
            if field not in item:
                errors.append(f"items[{index}].{field} is required")
        if _text(item.get("source_type")) == "vector" and item.get("photography_authority"):
            errors.append(f"items[{index}] vector cannot be photography authority")
    return errors
