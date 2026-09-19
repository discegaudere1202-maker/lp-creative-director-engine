"""Fail-closed contracts for relationships between co-visible media."""
from __future__ import annotations

from typing import Any

RELATION_TYPES = {
    "CROP_FROM_MASTER",
    "BEFORE_AFTER",
    "WHOLE_DETAIL",
    "PROCESS_SEQUENCE",
    "CAUSE_EFFECT",
    "CONTEXT_EVIDENCE",
    "ALTERNATIVE_VIEW",
    "INDEPENDENT_EDITORIAL",
    "SECONDARY_CONTEXT",
    "NONE",
}


def _rect_inside(rect: dict[str, Any] | None, width: int, height: int) -> bool:
    if not isinstance(rect, dict):
        return False
    try:
        x, y = float(rect["x"]), float(rect["y"])
        w, h = float(rect["width"]), float(rect["height"])
    except (KeyError, TypeError, ValueError):
        return False
    return x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height


def validate_visual_relationship(contract: dict[str, Any]) -> dict[str, Any]:
    """Validate a visual relationship without accepting decorative intent."""
    relation = contract.get("visual_relation_type") or contract.get("relation_type")
    main = contract.get("main_asset_id")
    detail = contract.get("detail_asset_id")
    dimensions = contract.get("asset_dimensions") or {}
    errors: list[str] = []
    warnings: list[str] = []
    if relation not in RELATION_TYPES:
        errors.append("unknown_relation_type")
    if not main:
        errors.append("missing_main_asset_id")

    if relation == "CROP_FROM_MASTER":
        master = contract.get("master_asset_id")
        source = contract.get("source_crop_rect")
        detail_rect = contract.get("detail_crop_rect")
        if master != main or detail != master:
            errors.append("crop_master_must_match_main_and_detail")
        width, height = dimensions.get(master, (0, 0))
        if not _rect_inside(source, width, height):
            errors.append("source_crop_outside_master")
        if not _rect_inside(detail_rect, width, height):
            errors.append("detail_crop_outside_master")
        if source and detail_rect and source != detail_rect:
            warnings.append("detail_crop_is_rendered_projection_of_source_region")

    elif relation == "SECONDARY_CONTEXT":
        if not detail or detail == main:
            errors.append("secondary_must_use_distinct_asset")
        if not contract.get("semantic_relation"):
            errors.append("missing_semantic_relation")
        if not contract.get("narrative_function"):
            errors.append("missing_narrative_function")
        if contract.get("display_treatment") in {"zoom_crop", "magnification", "source_point"}:
            errors.append("secondary_cannot_use_magnification_treatment")

    elif relation == "NONE":
        if detail or contract.get("narrative_function"):
            errors.append("none_relation_cannot_have_secondary_media")

    elif detail and not contract.get("semantic_relation"):
        warnings.append("secondary_media_has_no_semantic_role")

    return {
        "status": "FAIL" if errors else ("WARNING" if warnings else "PASS"),
        "relation_type": relation,
        "errors": errors,
        "warnings": warnings,
        "contract": contract,
        "hard_gate": relation == "CROP_FROM_MASTER",
    }
