"""Read the existing landscape pool without promoting candidates to approvals.

This adapter uses the fields actually present in the collected photo index.
It deliberately does not translate that index into the older three-industry
rights schema, invent focal/crop metadata, or choose an image from industry
alone. Its output is a private internal-preview input, never an adoption.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
import zipfile

from PIL import Image, UnidentifiedImageError


INDEX_MEMBER = "output-196-final/LANDSCAPING_ASSET_POOL_196_INDEX.json"
ILLUSTRATIVE_DISCLOSURE = "第三者のイメージ写真です。自社の施工・人物・実績を示すものではありません。"
MATCH_FIELDS = ("scene", "visual_notes", "日本の地域造園LPへの適合理由")
CLASSIFICATIONS = {"READY_FOR_SELECTION", "CONTEXT_LIMITED", "REJECT"}


class AssetSelectionError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _fail(code: str, message: str) -> None:
    raise AssetSelectionError(code, message)


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (ValueError, TypeError) as exc:
        raise AssetSelectionError("INVALID_JSON", "Only ordinary JSON values are supported") from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail("INVALID_INPUT", f"{field} must be a nonempty string")
    return value


def _strings(values: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(values, (list, tuple)) or (nonempty and not values):
        _fail("INVALID_INPUT", f"{field} must be an explicit list")
    result = [_text(value, field) for value in values]
    if len(result) != len(set(result)):
        _fail("INVALID_INPUT", f"{field} must not contain duplicates")
    return result


def _validate_index(index: Any) -> None:
    if not isinstance(index, dict) or not isinstance(index.get("records"), list):
        _fail("INVALID_POOL", "The collected index must contain its original records list")
    _text(index.get("version"), "version")
    ids = set()
    for record in index["records"]:
        if not isinstance(record, dict):
            _fail("INVALID_POOL", "Every source record must be an object")
        asset_id = _text(record.get("asset_id"), "asset_id")
        if asset_id in ids:
            _fail("DUPLICATE_ASSET_ID", asset_id)
        ids.add(asset_id)
        classification = record.get("classification")
        if not isinstance(classification, dict) or classification.get("asset_id") != asset_id:
            _fail("CLASSIFICATION_ID_MISMATCH", asset_id)
        if classification.get("status") not in CLASSIFICATIONS:
            _fail("INVALID_CLASSIFICATION", asset_id)
        for field in (*MATCH_FIELDS, "usable_roles", "excluded_uses", "人物や会社実績誤認防止"):
            _text(classification.get(field), f"classification.{field}")
        for field in ("source_page", "license_url", "adoption_status"):
            _text(record.get(field), field)
        if not re.fullmatch(r"[a-f0-9]{64}", str(record.get("sha256", ""))):
            _fail("INVALID_IMAGE_HASH", asset_id)
        for field in ("width", "height", "bytes"):
            if type(record.get(field)) is not int or record[field] <= 0:
                _fail("INVALID_IMAGE_METADATA", f"{asset_id}: {field}")
        storage = record.get("storage")
        if not isinstance(storage, dict) or storage.get("member_sha256") != record["sha256"]:
            _fail("STORAGE_HASH_MISMATCH", asset_id)
        # This bridge handles the observed third-party illustrative pool only.
        if record.get("company_project_staff_evidence_allowed") is not False:
            _fail("UNSUPPORTED_EVIDENCE_BOUNDARY", asset_id)


def load_landscaping_pool(path: str | Path, *, expected_sha256: str) -> dict:
    """Read an already materialized original ZIP/index with its expected hash.

    The complete source index (including unknown fields and storage pointers)
    is retained in memory. Do not put the returned private object in Git.
    """
    source = Path(path)
    if not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        _fail("INVALID_SOURCE_HASH", "An exact source SHA-256 is required")
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        _fail("SOURCE_HASH_MISMATCH", "Source bytes changed")
    if zipfile.is_zipfile(io.BytesIO(raw)):
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if archive.namelist().count(INDEX_MEMBER) != 1:
                _fail("INVALID_POOL_ARCHIVE", "The canonical index member is missing or duplicated")
            index_bytes = archive.read(INDEX_MEMBER)
        member = INDEX_MEMBER
    else:
        index_bytes, member = raw, None
    try:
        index = json.loads(index_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        raise AssetSelectionError("INVALID_POOL", "The source index is not JSON") from exc
    _validate_index(index)
    pool = {
        "schema_version": "pilot-landscaping-pool/v1",
        "industry": "landscape",
        "source": {"path": str(source), "sha256": expected_sha256, "bytes": len(raw),
                   "index_member": member, "index_sha256": hashlib.sha256(index_bytes).hexdigest()},
        "index_snapshot_sha256": _hash(index), "index": index,
    }
    pool["pool_sha256"] = _hash(pool)
    return pool


def _index(pool: Mapping[str, Any]) -> dict:
    sealed = dict(pool)
    expected = sealed.pop("pool_sha256", None)
    if _hash(sealed) != expected:
        _fail("POOL_SNAPSHOT_CHANGED", "The source identity or index was modified after loading")
    if pool.get("schema_version") != "pilot-landscaping-pool/v1" or pool.get("industry") != "landscape":
        _fail("INVALID_POOL", "Expected the landscape collection adapter")
    index = pool.get("index")
    if _hash(index) != pool.get("index_snapshot_sha256"):
        _fail("POOL_SNAPSHOT_CHANGED", "The source index was modified after loading")
    _validate_index(index)
    return index


def rank_landscaping_candidates(
    pool: Mapping[str, Any], *, industry: str, media_role: str,
    context_terms: Sequence[str], preferred_orientation: str | None = None,
    used_asset_ids: Sequence[str] = (), used_near_duplicate_groups: Sequence[str] = (),
    include_context_limited: bool = False,
) -> dict:
    """Rank role-compatible, context-matching candidates; never auto-adopt.

    Context terms come from the business/design brief. Matches are literal
    evidence in the recorded scene/notes/fit text, not new visual judgements.
    Empty matches return an empty pool rather than an industry-default Hero.
    """
    index = _index(pool)
    if industry != "landscape":
        _fail("INDUSTRY_POOL_UNAVAILABLE", f"No source pool for {industry} is connected here")
    _text(media_role, "media_role")
    terms = _strings(context_terms, "context_terms", nonempty=True)
    used_ids = set(_strings(used_asset_ids, "used_asset_ids"))
    used_groups = set(_strings(used_near_duplicate_groups, "used_near_duplicate_groups"))
    if preferred_orientation not in {None, "landscape", "portrait", "square"}:
        _fail("INVALID_INPUT", "preferred_orientation is invalid")
    if type(include_context_limited) is not bool:
        _fail("INVALID_INPUT", "include_context_limited must be boolean")
    if used_groups & {"NONE", "none"}:
        _fail("INVALID_INPUT", "NONE is not a globally verified duplicate-group identifier")
    candidates, excluded = [], []
    for record in index["records"]:
        cl = record["classification"]
        reasons = []
        if cl["status"] == "REJECT" or record["adoption_status"] == "REJECTED":
            reasons.append("SOURCE_REJECTED")
        if cl["status"] == "CONTEXT_LIMITED" and not include_context_limited:
            reasons.append("CONTEXT_LIMITED_NOT_REQUESTED")
        if record.get("validation_issues"):
            reasons.append("SOURCE_VALIDATION_ISSUES")
        if media_role not in [role.strip() for role in cl["usable_roles"].split(",")]:
            reasons.append("ROLE_MISMATCH")
        if record["asset_id"] in used_ids:
            reasons.append("ALREADY_USED_ASSET")
        if record.get("near_duplicate_group") in used_groups:
            reasons.append("ALREADY_USED_NEAR_GROUP")
        matches = [{"term": term, "field": field, "source_text": cl[field]}
                   for term in terms for field in MATCH_FIELDS if term.casefold() in cl[field].casefold()]
        if not matches:
            reasons.append("NO_RECORDED_CONTEXT_MATCH")
        if reasons:
            excluded.append({"asset_id": record["asset_id"], "reasons": reasons})
            continue
        orientation = "square" if record["width"] == record["height"] else "landscape" if record["width"] > record["height"] else "portrait"
        candidates.append({
            "asset_id": record["asset_id"], "source_record_sha256": _hash(record),
            "context_matches": matches,
            "matched_term_count": len({match["term"] for match in matches}),
            "orientation": orientation,
            "preferred_orientation_match": orientation == preferred_orientation if preferred_orientation else None,
            "source_classification": deepcopy(cl),
            "source_adoption_status": record["adoption_status"],
            "selection_status": "CANDIDATE_ONLY",
        })
    candidates.sort(key=lambda candidate: (-candidate["matched_term_count"],
                    -int(candidate["preferred_orientation_match"] is True), candidate["asset_id"]))
    return {
        "schema_version": "pilot-asset-candidates/v1",
        "source": deepcopy(pool["source"]), "source_version": index["version"],
        "source_record_count": len(index["records"]),
        "source_classification_counts": dict(Counter(r["classification"]["status"] for r in index["records"])),
        "request": {"industry": industry, "media_role": media_role, "context_terms": terms,
                    "preferred_orientation": preferred_orientation, "used_asset_ids": sorted(used_ids),
                    "used_near_duplicate_groups": sorted(used_groups), "include_context_limited": include_context_limited},
        "candidates": candidates, "excluded": excluded,
        "auto_selection": False, "source_classifications_changed": False,
        "visual_qa": "NOT_RUN", "rights_reassessment": "NOT_RUN", "production_ready": False,
    }


def build_preview_asset_selection(
    pool: Mapping[str, Any], *, placements: Sequence[Mapping[str, Any]],
    local_files: Mapping[str, str | Path], context: Mapping[str, Any],
) -> dict:
    """Pin explicit chosen originals and return LP54's slot/path/hash mapping.

    Every placement supplies slot, asset_id, media_role, context_terms, parts,
    selection_reason, and optionally context_limit_handling. An image marked
    CONTEXT_LIMITED needs an explicit explanation, which is retained as an
    unreviewed author statement rather than converted to a permission.
    """
    index = _index(pool)
    records = {record["asset_id"]: record for record in index["records"]}
    if not isinstance(placements, (list, tuple)) or not placements or not isinstance(context, Mapping):
        _fail("INVALID_INPUT", "Explicit placements and a context object are required")
    if not isinstance(local_files, Mapping):
        _fail("INVALID_INPUT", "local_files must map selected asset IDs to local originals")
    images, selections, used_ids, used_groups = {}, [], set(), set()
    for supplied in placements:
        if not isinstance(supplied, Mapping):
            _fail("INVALID_INPUT", "Each placement must be an object")
        placement = deepcopy(dict(supplied))
        required = {"slot", "asset_id", "media_role", "context_terms", "parts", "selection_reason"}
        if not required <= set(placement) or set(placement) - required - {"context_limit_handling"}:
            _fail("INVALID_PLACEMENT", "Unsupported or missing placement fields")
        slot = _text(placement["slot"], "slot")
        if not re.fullmatch(r"[a-z][a-zA-Z0-9]*", slot) or slot in images:
            _fail("INVALID_IMAGE_SLOT", "Image slots must be unique safe identifiers")
        asset_id = _text(placement["asset_id"], "asset_id")
        if asset_id not in records:
            _fail("ASSET_NOT_IN_POOL", asset_id)
        if asset_id in used_ids:
            _fail("REPEATED_ORIGINAL_IMAGE", "Select distinct originals for distinct placements")
        used_ids.add(asset_id)
        _strings(placement["parts"], "parts", nonempty=True)
        _text(placement["selection_reason"], "selection_reason")
        record = records[asset_id]
        group = record.get("near_duplicate_group")
        if group and group not in {"NONE", "none"}:
            if group in used_groups:
                _fail("REPEATED_NEAR_GROUP", "Selected originals belong to the same recorded near-duplicate group")
            used_groups.add(group)
        limited = record["classification"]["status"] == "CONTEXT_LIMITED"
        if limited:
            _text(placement.get("context_limit_handling"), "context_limit_handling")
        ranked = rank_landscaping_candidates(pool, industry="landscape", media_role=placement["media_role"],
                                             context_terms=placement["context_terms"], include_context_limited=limited)
        candidate = next((item for item in ranked["candidates"] if item["asset_id"] == asset_id), None)
        if candidate is None:
            _fail("INELIGIBLE_ASSET_SELECTION", asset_id)
        if asset_id not in local_files:
            _fail("LOCAL_ORIGINAL_MISSING", asset_id)
        raw_path = str(local_files[asset_id])
        path = Path(raw_path)
        if not path.is_absolute() or path.is_symlink() or not path.is_file():
            _fail("INVALID_LOCAL_IMAGE", "Supply an absolute ordinary local original file")
        binary = path.read_bytes()
        if hashlib.sha256(binary).hexdigest() != record["sha256"] or len(binary) != record["bytes"]:
            _fail("IMAGE_IDENTITY_MISMATCH", asset_id)
        try:
            with Image.open(io.BytesIO(binary)) as image:
                image_format = image.format
                image.verify()
            with Image.open(io.BytesIO(binary)) as image:
                image.load()
                dimensions = image.size
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise AssetSelectionError("INVALID_IMAGE_BYTES", asset_id) from exc
        if image_format not in {"JPEG", "PNG", "WEBP"} or dimensions != (record["width"], record["height"]):
            _fail("IMAGE_METADATA_MISMATCH", asset_id)
        images[slot] = {"path": raw_path, "sha256": record["sha256"]}
        selections.append({
            "placement": placement, "candidate": candidate, "source_record": deepcopy(record),
            "binary_check": {"bytes": len(binary), "sha256": record["sha256"],
                             "width": dimensions[0], "height": dimensions[1], "format": image_format},
            "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK",
            "required_disclosure": ILLUSTRATIVE_DISCLOSURE,
        })
    if set(local_files) != used_ids:
        _fail("UNSELECTED_LOCAL_IMAGE", "Do not silently discard supplied images")
    manifest = {
        "schema_version": "pilot-asset-selection/v1", "scope": "INTERNAL_COMPOSITION_PREVIEW",
        "industry": "landscape", "source": deepcopy(pool["source"]),
        "source_index_snapshot_sha256": pool["index_snapshot_sha256"],
        "context": deepcopy(dict(context)), "images": images, "selections": selections,
        "source_adoption_changed": False, "formal_gate_issued": False, "production_ready": False,
        "visual_approval": "NOT_ASSERTED", "crop_validation": "NOT_RUN", "rights_reassessment": "NOT_RUN",
        "source_conditions_preserved": True, "transformation": "NONE",
    }
    manifest["manifest_sha256"] = _hash(manifest)
    return manifest


def attach_preview_assets(composition_input: Mapping[str, Any], selection: Mapping[str, Any]) -> dict:
    """Attach a sealed selection after checking the authored nearby labels.

    This does not write or shorten copy. The caller supplies the disclosure in
    each declared part's existing note, so the normal copy-retention checker
    will also verify its presence in rendered HTML. Semantic/crop QA remains
    outstanding. Existing image bindings are never silently replaced.
    """
    manifest = deepcopy(dict(selection))
    expected = manifest.pop("manifest_sha256", None)
    if manifest.get("schema_version") != "pilot-asset-selection/v1" or _hash(manifest) != expected:
        _fail("SELECTION_MANIFEST_CHANGED", "Selection contents changed after verification")
    manifest["manifest_sha256"] = expected
    payload = deepcopy(dict(composition_input))
    if payload.get("schema_version") != "lp54-composition-input/v1":
        _fail("INVALID_COMPOSITION_INPUT", "Expected an LP54 composition input")
    if payload.get("images") != {}:
        _fail("EXISTING_IMAGE_BINDINGS", "Use an explicit empty image mapping before attachment")
    company = payload.get("company", {})
    if company.get("industry") != "landscape":
        _fail("INDUSTRY_POOL_UNAVAILABLE", "The source pool only covers landscape")
    selected_parts = {design.rsplit("-", 1)[0] for design in payload.get("selection", {}).get("design_ids", [])}
    for item in manifest["selections"]:
        for part in item["placement"]["parts"]:
            if part not in selected_parts:
                _fail("UNSELECTED_IMAGE_PART", part)
            note = company.get("parts", {}).get(part, {}).get("note")
            if not isinstance(note, str) or ILLUSTRATIVE_DISCLOSURE not in note:
                _fail("ILLUSTRATIVE_LABEL_MISSING", f"The authored {part} note must identify the third-party image")
    context = payload.setdefault("context", {})
    if not isinstance(context, dict) or "asset_selection" in context:
        _fail("EXISTING_SELECTION_CONTEXT", "Existing asset-selection context is preserved")
    payload["images"] = deepcopy(manifest["images"])
    context["asset_selection"] = manifest
    return payload


def validate_composed_asset_usage(selection: Mapping[str, Any], composition_trace: Mapping[str, Any]) -> dict:
    """Check declared image/part uses against the renderer's actual slot trace.

    Run after ``compose_preview`` and before handing its files downstream.
    This static binding check neither issues a formal Gate nor approves image
    rights, appearance, cropping, company truth or publication.
    """
    manifest = deepcopy(dict(selection))
    expected = manifest.pop("manifest_sha256", None)
    if manifest.get("schema_version") != "pilot-asset-selection/v1" or _hash(manifest) != expected:
        _fail("SELECTION_MANIFEST_CHANGED", "Selection contents changed after verification")
    manifest["manifest_sha256"] = expected
    if composition_trace.get("context", {}).get("asset_selection") != manifest:
        _fail("COMPOSED_SELECTION_CONTEXT_MISMATCH", "The rendered selection context differs")
    images = composition_trace.get("images")
    sections = composition_trace.get("sections")
    if not isinstance(images, list) or not isinstance(sections, list):
        _fail("INVALID_COMPOSITION_TRACE", "Actual image and section traces are required")
    image_hashes = {}
    for image in images:
        if not isinstance(image, dict) or image.get("slot") in image_hashes:
            _fail("INVALID_COMPOSITION_TRACE", "Rendered image slots must be unique")
        image_hashes[image.get("slot")] = image.get("sha256")
    expected_hashes = {slot: image["sha256"] for slot, image in manifest["images"].items()}
    if image_hashes != expected_hashes:
        _fail("COMPOSED_IMAGE_IDENTITY_MISMATCH", "Actual rendered slots/hashes differ from the selected originals")
    actual_parts = {slot: set() for slot in expected_hashes}
    seen_parts = set()
    for section in sections:
        if not isinstance(section, dict):
            _fail("INVALID_COMPOSITION_TRACE", "Rendered sections must be objects")
        part = _text(section.get("part"), "section.part")
        if part in seen_parts:
            _fail("INVALID_COMPOSITION_TRACE", "Rendered sections contain a duplicate part")
        seen_parts.add(part)
        slots = _strings(section.get("image_slots"), "section.image_slots")
        for slot in slots:
            if slot not in actual_parts:
                _fail("COMPOSED_IMAGE_IDENTITY_MISMATCH", "A section references an unselected image slot")
            actual_parts[slot].add(part)
    bindings = []
    for item in manifest["selections"]:
        placement = item["placement"]
        slot = placement["slot"]
        if set(placement["parts"]) != actual_parts[slot]:
            _fail("COMPOSED_IMAGE_PART_MISMATCH", f"Actual uses of {slot} differ from the declared parts")
        bindings.append({"slot": slot, "parts": sorted(actual_parts[slot]), "sha256": expected_hashes[slot]})
    return {
        "schema_version": "pilot-asset-usage-check/v1", "state": "STATIC_BINDING_MATCH",
        "selection_manifest_sha256": expected, "bindings": bindings,
        "formal_gate_issued": False, "quality_status": "NOT_RUN", "production_ready": False,
        "visual_approval": "NOT_ASSERTED", "crop_validation": "NOT_RUN",
    }
