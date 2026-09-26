"""Production Visual Asset Library runtime for current industries (Issue #106).

Asset selection happens only after CompositionPlan/Family freeze. Category may
scope the candidate pool but must never choose Family/topology/scene order.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
import hashlib
import html
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.request import Request, urlopen

CURRENT_INDUSTRIES = {"beauty_cosmetics", "hair_salon_barber", "pilates_fitness"}
REQUIRED_FIELDS = (
    "asset_id", "media_type", "source_provider", "source_id", "source_url", "creator",
    "license_status", "license_terms_url", "license_terms_checked_at",
    "commercial_use_status", "modification_status", "crop_status",
    "attribution_requirement", "person_release_status", "property_release_status",
    "trademark_logo_risk", "acquired_at", "checked_at", "content_class",
    "industry_tags", "business_category_tags", "eligible_scene_intents",
    "eligible_media_roles", "orientation", "aspect_ratio", "people_count", "people_type",
    "visual_tone_tags", "material_quality_tags", "evidence_status", "prohibited_uses",
    "provenance_confidence", "recheck_policy", "binary_sha256",
)
ENUMS = {
    "media_type": {"still_image", "video"},
    "license_status": {"VERIFIED_PROVIDER_LICENSE", "VERIFIED_COMPANY_PERMISSION", "PROJECT_OWNED_GENERATED", "UNKNOWN", "REVOKED_OR_EXPIRED"},
    "commercial_use_status": {"ALLOWED", "ALLOWED_WITH_CONDITIONS", "NOT_ALLOWED", "UNKNOWN"},
    "modification_status": {"ALLOWED", "LIMITED", "NOT_ALLOWED", "UNKNOWN"},
    "crop_status": {"ALLOWED", "LIMITED", "NOT_ALLOWED", "UNKNOWN"},
    "attribution_requirement": {"NONE_REQUIRED", "REQUIRED", "RECOMMENDED", "UNKNOWN"},
    "person_release_status": {"NOT_APPLICABLE", "PROVIDER_STATES_RELEASED", "VERIFIED_RELEASE", "UNVERIFIED", "UNKNOWN"},
    "property_release_status": {"NOT_APPLICABLE", "VERIFIED_RELEASE", "UNVERIFIED", "UNKNOWN"},
    "trademark_logo_risk": {"NONE_VISIBLE", "REMOVABLE_BY_CROP", "PRESENT_REVIEW_REQUIRED", "PROHIBITIVE"},
    "orientation": {"landscape", "portrait", "square", "flexible"},
    "people_type": {"none", "single_adult", "multiple_adults", "staff_like_generic", "customer_like_generic", "mixed_group", "unknown"},
    "evidence_status": {"ACTUAL_COMPANY_EVIDENCE", "GENERIC_ILLUSTRATIVE_STOCK", "PROJECT_OWNED_GENERATED_ILLUSTRATION", "ARCHITECTURE_VALIDATION_ONLY"},
    "provenance_confidence": {"HIGH", "MEDIUM", "LOW", "UNKNOWN"},
}
PASS_STATES = {"RIGHTS_PASS", "RIGHTS_PASS_WITH_RENDER_CONDITIONS"}
ILLUSTRATIVE_STATES = {"GENERIC_ILLUSTRATIVE_STOCK", "PROJECT_OWNED_GENERATED_ILLUSTRATION"}
SCENE_ROLE_PREFERENCES = {
    "recognize": ("hero",),
    "choose": ("lifestyle_context", "tools_material_detail", "consultation"),
    "understand": ("process", "tools_material_detail", "interior_environment"),
    "trust": ("interior_environment", "lifestyle_context", "consultation", "person_staff"),
    "compare": ("tools_material_detail", "lifestyle_context", "process"),
    "act": ("lifestyle_context", "interior_environment", "tools_material_detail"),
}


class VisualAssetError(ValueError):
    pass


def _text(value: Any) -> str:
    return str(value or "").strip()


def _list_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise VisualAssetError("expected list")
    return sorted({_text(item) for item in value if _text(item)})


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _iso_date(value: str, field: str) -> str:
    try:
        date.fromisoformat(value[:10])
    except Exception as exc:
        raise VisualAssetError(f"{field} must be ISO-8601 date") from exc
    return value


def normalize_visual_asset_record(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise VisualAssetError("asset record must be an object")
    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise VisualAssetError("missing required fields: " + ", ".join(missing))
    item = deepcopy(dict(raw))
    for field in ("asset_id", "source_provider", "source_id", "source_url", "creator", "license_terms_url", "content_class", "aspect_ratio"):
        if not _text(item.get(field)):
            raise VisualAssetError(f"{field} is required")
        item[field] = _text(item[field])
    for field, allowed in ENUMS.items():
        value = _text(item.get(field))
        if value not in allowed:
            raise VisualAssetError(f"{field} is invalid: {value}")
        item[field] = value
    for field in ("industry_tags", "business_category_tags", "eligible_scene_intents", "eligible_media_roles", "visual_tone_tags", "material_quality_tags", "prohibited_uses"):
        item[field] = _list_text(item.get(field))
    if not item["industry_tags"] or any(value not in CURRENT_INDUSTRIES for value in item["industry_tags"]):
        raise VisualAssetError("industry_tags must stay inside current-industry scope")
    if not item["business_category_tags"] or not item["eligible_scene_intents"] or not item["eligible_media_roles"]:
        raise VisualAssetError("category/scene/media-role tags are required")
    try:
        item["people_count"] = int(item["people_count"])
    except Exception as exc:
        raise VisualAssetError("people_count must be an integer") from exc
    if item["people_count"] < 0:
        raise VisualAssetError("people_count must be >= 0")
    item["license_terms_checked_at"] = _iso_date(_text(item["license_terms_checked_at"]), "license_terms_checked_at")
    item["acquired_at"] = _iso_date(_text(item["acquired_at"]), "acquired_at")
    item["checked_at"] = _iso_date(_text(item["checked_at"]), "checked_at")
    if not isinstance(item["recheck_policy"], Mapping):
        raise VisualAssetError("recheck_policy must be an object")
    item["recheck_policy"] = deepcopy(dict(item["recheck_policy"]))
    if not item["recheck_policy"].get("triggers"):
        raise VisualAssetError("recheck_policy.triggers is required")
    sha = _text(item["binary_sha256"]).lower()
    if len(sha) != 64 or any(ch not in "0123456789abcdef" for ch in sha):
        raise VisualAssetError("binary_sha256 must be an exact SHA-256")
    item["binary_sha256"] = sha
    item["raw_provenance"] = deepcopy(dict(raw.get("raw_provenance") or {}))
    return item


def ingest_provider_asset(raw: Mapping[str, Any], binary: bytes, *, acquired_at: str | None = None) -> dict[str, Any]:
    """Provider-neutral ingestion: preserve raw provenance and normalize only after bytes exist."""
    if not binary:
        raise VisualAssetError("empty binary")
    metadata = deepcopy(dict(raw.get("metadata") or raw))
    metadata["binary_sha256"] = hashlib.sha256(binary).hexdigest()
    metadata["acquired_at"] = acquired_at or _text(metadata.get("acquired_at")) or date.today().isoformat()
    metadata.setdefault("checked_at", metadata["acquired_at"])
    metadata["raw_provenance"] = deepcopy(dict(raw.get("raw_provenance") or {}))
    return normalize_visual_asset_record(metadata)


def evaluate_visual_asset_rights(asset: Mapping[str, Any], target_use: Mapping[str, Any]) -> dict[str, Any]:
    item = normalize_visual_asset_record(asset)
    crop_required = bool(target_use.get("crop_required", True))
    can_attribute = bool(target_use.get("can_render_attribution", True))
    evidence_boundary = _text(target_use.get("evidence_boundary", "GENERIC_ILLUSTRATIVE_STOCK"))
    current_hash = _text(target_use.get("current_binary_sha256", item["binary_sha256"])).lower()
    conditions: list[str] = []
    if not item["source_provider"] or not item["source_id"] or not item["source_url"].startswith("http"):
        return {"state": "MEDIA_SOURCE_UNKNOWN", "conditions": []}
    if item["license_status"] in {"UNKNOWN", "REVOKED_OR_EXPIRED"} or not item["license_terms_url"].startswith("http"):
        return {"state": "MEDIA_LICENSE_UNKNOWN", "conditions": []}
    if item["commercial_use_status"] not in {"ALLOWED", "ALLOWED_WITH_CONDITIONS"}:
        return {"state": "MEDIA_COMMERCIAL_USE_BLOCKED", "conditions": []}
    if item["commercial_use_status"] == "ALLOWED_WITH_CONDITIONS":
        conditions.append("commercial_use_conditions")
    if crop_required and item["crop_status"] not in {"ALLOWED", "LIMITED"}:
        return {"state": "MEDIA_MODIFICATION_BLOCKED", "conditions": []}
    if crop_required and item["modification_status"] not in {"ALLOWED", "LIMITED"}:
        return {"state": "MEDIA_MODIFICATION_BLOCKED", "conditions": []}
    if item["crop_status"] == "LIMITED" or item["modification_status"] == "LIMITED":
        conditions.append("respect_limited_modification")
    if item["attribution_requirement"] == "UNKNOWN":
        return {"state": "MEDIA_ATTRIBUTION_UNSATISFIED", "conditions": []}
    if item["attribution_requirement"] == "REQUIRED" and not can_attribute:
        return {"state": "MEDIA_ATTRIBUTION_UNSATISFIED", "conditions": []}
    if item["attribution_requirement"] == "REQUIRED":
        conditions.append("render_attribution")
    if item["people_count"] > 0 and item["person_release_status"] not in {"PROVIDER_STATES_RELEASED", "VERIFIED_RELEASE"}:
        return {"state": "MEDIA_PERSON_RIGHTS_REVIEW_REQUIRED", "conditions": []}
    if item["property_release_status"] in {"UNVERIFIED", "UNKNOWN"}:
        return {"state": "MEDIA_PROPERTY_RIGHTS_REVIEW_REQUIRED", "conditions": []}
    if item["trademark_logo_risk"] in {"PRESENT_REVIEW_REQUIRED", "PROHIBITIVE"}:
        return {"state": "MEDIA_TRADEMARK_REVIEW_REQUIRED", "conditions": []}
    if item["trademark_logo_risk"] == "REMOVABLE_BY_CROP":
        if not crop_required or item["crop_status"] not in {"ALLOWED", "LIMITED"}:
            return {"state": "MEDIA_TRADEMARK_REVIEW_REQUIRED", "conditions": []}
        conditions.append("crop_out_trademark")
    if evidence_boundary == "ACTUAL_COMPANY_EVIDENCE" and item["evidence_status"] != "ACTUAL_COMPANY_EVIDENCE":
        return {"state": "MEDIA_EVIDENCE_BOUNDARY_MISMATCH", "conditions": []}
    if item["evidence_status"] == "ARCHITECTURE_VALIDATION_ONLY":
        return {"state": "MEDIA_EVIDENCE_BOUNDARY_MISMATCH", "conditions": []}
    if current_hash != item["binary_sha256"]:
        return {"state": "MEDIA_BINARY_CHANGED", "conditions": []}
    if bool(item["recheck_policy"].get("invalidated")) or bool(target_use.get("recheck_triggered")):
        return {"state": "MEDIA_RIGHTS_STALE", "conditions": []}
    if item["provenance_confidence"] in {"LOW", "UNKNOWN"}:
        return {"state": "HUMAN_REVIEW_REQUIRED", "conditions": []}
    if item["evidence_status"] in ILLUSTRATIVE_STATES:
        conditions.append("illustrative_only")
    return {"state": "RIGHTS_PASS_WITH_RENDER_CONDITIONS" if conditions else "RIGHTS_PASS", "conditions": sorted(set(conditions))}


def query_asset_candidates(catalog: Sequence[Mapping[str, Any]], *, industry: str, business_category: str, scene_intent: str, media_role: str, required_content_classes: Sequence[str], evidence_boundary: str) -> list[dict[str, Any]]:
    if industry not in CURRENT_INDUSTRIES:
        raise VisualAssetError("INDUSTRY_OUT_OF_SCOPE")
    required = set(required_content_classes)
    result: list[dict[str, Any]] = []
    for raw in catalog:
        item = normalize_visual_asset_record(raw)
        if industry not in item["industry_tags"] or business_category not in item["business_category_tags"]:
            continue
        if scene_intent not in item["eligible_scene_intents"] or media_role not in item["eligible_media_roles"]:
            continue
        if required and item["content_class"] not in required:
            continue
        if evidence_boundary == "ACTUAL_COMPANY_EVIDENCE" and item["evidence_status"] != "ACTUAL_COMPANY_EVIDENCE":
            continue
        result.append(item)
    return sorted(result, key=lambda item: item["asset_id"])


def usage_ledger_snapshot_id(entries: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(_canonical([dict(item) for item in entries]).encode("utf-8")).hexdigest()


def _reuse_penalty(asset: Mapping[str, Any], ledger: Sequence[Mapping[str, Any]], *, media_role: str, business_category: str, crop_fingerprint: str, active_batch_id: str) -> tuple[int, list[str], str | None]:
    penalty = 0
    factors: list[str] = []
    hard_block: str | None = None
    for use in ledger:
        same_asset = _text(use.get("asset_id")) == asset["asset_id"]
        if not same_asset:
            continue
        same_role = _text(use.get("media_role")) == media_role
        same_crop = _text(use.get("crop_fingerprint")) == crop_fingerprint
        same_batch = bool(active_batch_id) and _text(use.get("batch_id")) == active_batch_id
        if media_role == "hero" and same_role and same_batch:
            hard_block = "BATCH_HERO_REUSE_BLOCKED"
            factors.append(hard_block)
        if same_role and same_crop:
            hard_block = hard_block or "REUSE_ROLE_CROP_BLOCKED"
            factors.append("same_crop_fingerprint_use")
        if same_role:
            penalty += 4
            factors.append("recent_same_role_use")
        if _text(use.get("business_category")) == business_category:
            penalty += 2
            factors.append("recent_same_category_use")
        if same_crop:
            penalty += 6
            factors.append("same_crop_fingerprint_use")
    return penalty, sorted(set(factors)), hard_block


def select_visual_asset(candidates: Sequence[Mapping[str, Any]], *, frozen_composition_plan: Mapping[str, Any], scene: Mapping[str, Any], media_role: str, target_placement: Mapping[str, Any], usage_ledger_snapshot: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    family = frozen_composition_plan.get("input", {}).get("creative_family", {})
    if family.get("frozen") is not True:
        raise VisualAssetError("FAMILY_NOT_FROZEN")
    target_classes = set(target_placement.get("required_content_classes") or [])
    target_orientation = _text(target_placement.get("orientation", "flexible"))
    target_tones = set(target_placement.get("visual_tone_tags") or [])
    target_material = set(target_placement.get("material_quality_tags") or [])
    target_people = _text(target_placement.get("people_type", "none"))
    crop_fingerprint = _text(target_placement.get("crop_fingerprint", "center-cover"))
    business_category = _text(target_placement.get("business_category"))
    active_batch_id = _text(target_placement.get("batch_id"))
    allow_orientation_mismatch = bool(target_placement.get("allow_orientation_mismatch", False))
    trace_rejections: list[dict[str, str]] = []
    scored: list[tuple[tuple[Any, ...], dict[str, Any], dict[str, Any], list[str]]] = []
    for raw in candidates:
        item = normalize_visual_asset_record(raw)
        rights = evaluate_visual_asset_rights(item, {
            "crop_required": True,
            "can_render_attribution": bool(target_placement.get("can_render_attribution", True)),
            "evidence_boundary": _text(target_placement.get("evidence_boundary", "GENERIC_ILLUSTRATIVE_STOCK")),
            "current_binary_sha256": item["binary_sha256"],
        })
        if rights["state"] not in PASS_STATES:
            trace_rejections.append({"asset_id": item["asset_id"], "reason": rights["state"]})
            continue
        orientation_fit = 0 if item["orientation"] in {target_orientation, "flexible"} or target_orientation == "flexible" else 1
        if orientation_fit and not allow_orientation_mismatch:
            trace_rejections.append({"asset_id": item["asset_id"], "reason": "ORIENTATION_CROP_BLOCKED"})
            continue
        penalty, factors, hard_block = _reuse_penalty(
            item, usage_ledger_snapshot, media_role=media_role, business_category=business_category,
            crop_fingerprint=crop_fingerprint, active_batch_id=active_batch_id,
        )
        if hard_block:
            trace_rejections.append({"asset_id": item["asset_id"], "reason": hard_block})
            continue
        exact_class = 0 if (not target_classes or item["content_class"] in target_classes) else 1
        scene_fit = 0 if _text(scene.get("intent")) in item["eligible_scene_intents"] else 1
        role_fit = 0 if media_role in item["eligible_media_roles"] else 1
        tone_fit = -len(target_tones.intersection(item["visual_tone_tags"]))
        material_fit = -len(target_material.intersection(item["material_quality_tags"]))
        people_fit = 0 if target_people in {"", "any", item["people_type"]} else 1
        score = (exact_class, scene_fit, role_fit, orientation_fit, tone_fit, material_fit, people_fit, penalty, item["asset_id"])
        scored.append((score, item, rights, factors))
    if not scored:
        return {"state": "MEDIA_ROLE_UNSATISFIED", "selected": None, "candidate_rejections": trace_rejections}
    scored.sort(key=lambda row: row[0])
    score, selected, rights, factors = scored[0]
    return {
        "state": "SELECTED", "selected": selected, "rights": rights,
        "visual_fit_sort_keys": list(score[:-1]), "reuse_penalty_factors": factors,
        "candidate_rejections": trace_rejections,
    }


def choose_media_role(scene_intent: str, role_inventory: Mapping[str, Any]) -> tuple[str, list[str]]:
    roles = dict(role_inventory.get("roles") or {})
    for role in SCENE_ROLE_PREFERENCES.get(scene_intent, ("lifestyle_context", "tools_material_detail")):
        spec = roles.get(role)
        if isinstance(spec, Mapping) and spec.get("allowed", True) is not False:
            classes = list(spec.get("required_content_classes") or [])
            if classes:
                return role, classes
    raise VisualAssetError("MEDIA_ROLE_UNSATISFIED")


def make_asset_binding(*, generation_id: str, plan: Mapping[str, Any], scene: Mapping[str, Any], media_role: str, business_category: str, selection: Mapping[str, Any], catalog_version: str, usage_ledger: Sequence[Mapping[str, Any]], crop_variant_id: str, focal_point: Sequence[float], local_asset_path: str, source_path: str | None = None) -> dict[str, Any]:
    if selection.get("state") != "SELECTED" or not selection.get("selected"):
        raise VisualAssetError("cannot bind unselected asset")
    asset = selection["selected"]
    family = plan["input"]["creative_family"]
    if family.get("frozen") is not True:
        raise VisualAssetError("FAMILY_NOT_FROZEN")
    trace = {
        "generation_id": generation_id,
        "composition_plan_id": hashlib.sha256(_canonical(plan).encode("utf-8")).hexdigest(),
        "family_id": family["family_id"], "family_frozen": True,
        "scene_id": _text(scene.get("id")), "scene_intent": _text(scene.get("intent")),
        "media_role": media_role,
        "required_content_conditions": {"content_class": asset["content_class"], "illustrative_only": asset["evidence_status"] in ILLUSTRATIVE_STATES},
        "industry": plan.get("asset_pool_scope") or plan["input"]["company_truth"]["category"]["value"],
        "business_category": business_category, "catalog_version": catalog_version,
        "candidate_query_fingerprint": hashlib.sha256(_canonical({"industry": plan.get("asset_pool_scope"), "business_category": business_category, "scene": scene.get("intent"), "role": media_role}).encode("utf-8")).hexdigest(),
        "candidate_asset_ids": sorted({asset["asset_id"]} | {row["asset_id"] for row in selection.get("candidate_rejections", [])}),
        "candidate_rejections": deepcopy(list(selection.get("candidate_rejections") or [])),
        "selected_asset_id": asset["asset_id"], "source_provider": asset["source_provider"],
        "source_id": asset["source_id"], "source_url": asset["source_url"],
        "license_terms_url": asset["license_terms_url"], "license_terms_checked_at": asset["license_terms_checked_at"],
        "rights_gate_state": selection["rights"]["state"], "rights_conditions": list(selection["rights"].get("conditions") or []),
        "evidence_status": asset["evidence_status"], "usage_ledger_snapshot_id": usage_ledger_snapshot_id(usage_ledger),
        "reuse_penalty_factors": list(selection.get("reuse_penalty_factors") or []),
        "crop_variant_id": crop_variant_id, "focal_point": [float(focal_point[0]), float(focal_point[1])],
        "binary_sha256": asset["binary_sha256"],
        "renderer_binding_id": hashlib.sha256(f"{generation_id}:{scene.get('id')}:{media_role}:{asset['asset_id']}:{crop_variant_id}".encode("utf-8")).hexdigest(),
    }
    return {
        "asset_id": asset["asset_id"], "binary_sha256": asset["binary_sha256"], "media_role": media_role,
        "scene_id": _text(scene.get("id")), "evidence_status": asset["evidence_status"],
        "source_provider": asset["source_provider"], "source_url": asset["source_url"],
        "rights_gate": selection["rights"]["state"], "crop_variant_id": crop_variant_id,
        "focal_point": trace["focal_point"],
        "alt_text_mode": "illustrative" if asset["evidence_status"] in ILLUSTRATIVE_STATES else "evidence",
        "alt": "カテゴリを伝えるイメージ写真" if asset["evidence_status"] in ILLUSTRATIVE_STATES else "確認済み事業写真",
        "attribution_payload": f"Photo: {asset['creator']} / {asset['source_provider']}" if asset["attribution_requirement"] == "REQUIRED" else None,
        "local_asset_path": local_asset_path, "source_path": source_path or local_asset_path, "trace": trace,
    }


def append_usage_entry(ledger: list[dict[str, Any]], *, binding: Mapping[str, Any], generation_id: str, batch_id: str, business_category: str, placement_prominence: str, crop_fingerprint: str) -> None:
    ledger.append({
        "generation_id": generation_id, "batch_id": batch_id, "asset_id": binding["asset_id"],
        "media_role": binding["media_role"], "scene_id": binding["scene_id"],
        "crop_fingerprint": crop_fingerprint, "placement_prominence": placement_prominence,
        "business_category": business_category, "binary_sha256": binding["binary_sha256"],
    })


def validate_asset_bundle(bindings: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dominant = [item for item in bindings if item.get("media_role") == "hero" or item.get("placement_prominence") == "dominant"]
    hashes = [_text(item.get("binary_sha256")) for item in dominant]
    if len(hashes) != len(set(hashes)):
        return {"state": "MEDIA_REUSE_REVIEW_REQUIRED", "reason": "duplicate dominant binary"}
    sequence = [(item.get("asset_id"), item.get("media_role"), item.get("crop_variant_id")) for item in bindings]
    return {"state": "PASS", "sequence_fingerprint": hashlib.sha256(_canonical(sequence).encode("utf-8")).hexdigest()}


def verify_asset_binary(path: str | Path, expected_sha256: str) -> str:
    target = Path(path)
    if not target.is_file() or target.stat().st_size == 0:
        raise VisualAssetError("MEDIA_BINARY_MISSING")
    actual = hashlib.sha256(target.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise VisualAssetError("MEDIA_BINARY_CHANGED")
    return actual


def acquire_remote_binary(url: str, output_path: str | Path, *, timeout: int = 30, attempts: int = 3) -> dict[str, Any]:
    if not url.startswith("https://"):
        raise VisualAssetError("acquisition requires https")
    last_error: Exception | None = None
    for _ in range(max(1, attempts)):
        try:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0 LPVisualAssetLibrary/1.0"})
            with urlopen(request, timeout=timeout) as response:
                payload = response.read()
                content_type = _text(response.headers.get("Content-Type"))
            if not payload or not content_type.startswith("image/"):
                raise VisualAssetError("acquired response is not an image")
            target = Path(output_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            return {"path": str(target), "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "content_type": content_type}
        except Exception as exc:
            last_error = exc
    raise VisualAssetError(f"asset acquisition failed: {last_error}")


def render_asset_binding(binding: Mapping[str, Any] | None) -> str:
    if not binding:
        return ""
    src = _text(binding.get("local_asset_path"))
    if not src:
        raise VisualAssetError("binding local_asset_path is required")
    evidence_status = _text(binding.get("evidence_status"))
    caption = "<figcaption>イメージ写真</figcaption>" if evidence_status in ILLUSTRATIVE_STATES else ""
    attribution = _text(binding.get("attribution_payload"))
    if attribution:
        caption += f'<small class="asset-attribution">{html.escape(attribution)}</small>'
    focal = binding.get("focal_point") or [0.5, 0.5]
    object_position = f"{float(focal[0]) * 100:.0f}% {float(focal[1]) * 100:.0f}%"
    return (
        f'<figure class="production-asset" data-asset-id="{html.escape(_text(binding.get("asset_id")), quote=True)}" '
        f'data-binary-sha="{html.escape(_text(binding.get("binary_sha256")), quote=True)}" '
        f'data-evidence-status="{html.escape(evidence_status, quote=True)}">'
        f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(_text(binding.get("alt")), quote=True)}" '
        f'loading="eager" style="object-position:{object_position}">{caption}</figure>'
    )


def asset_binding_css() -> str:
    return (
        ".production-asset{margin:12px 0;min-width:0}.production-asset img{display:block;width:100%;"
        "aspect-ratio:16/10;object-fit:cover;border-radius:2px;background:#e8ebe8}.production-asset figcaption,"
        ".asset-attribution{display:block;margin-top:6px;font-size:11px;line-height:1.4;color:#66706a}"
        "@media(max-width:767px){.production-asset img{aspect-ratio:4/3}}"
    )


__all__ = [
    "CURRENT_INDUSTRIES", "REQUIRED_FIELDS", "PASS_STATES", "VisualAssetError",
    "normalize_visual_asset_record", "ingest_provider_asset", "evaluate_visual_asset_rights",
    "query_asset_candidates", "usage_ledger_snapshot_id", "select_visual_asset", "choose_media_role",
    "make_asset_binding", "append_usage_entry", "validate_asset_bundle", "verify_asset_binary",
    "acquire_remote_binary", "render_asset_binding", "asset_binding_css",
]
