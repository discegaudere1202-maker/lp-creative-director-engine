from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any


class AssetState(str, Enum):
    SALES_STATE = "SALES_STATE"
    ENRICHED_STATE = "ENRICHED_STATE"


class EvidenceSlotKind(str, Enum):
    HERO_REALITY = "HERO_REALITY"
    OWNER_PORTRAIT = "OWNER_PORTRAIT"
    CRAFT_ACTION = "CRAFT_ACTION"
    PLACE_WIDE = "PLACE_WIDE"
    PRODUCT_DETAIL = "PRODUCT_DETAIL"
    RESULT_CASE = "RESULT_CASE"
    TESTIMONIAL = "TESTIMONIAL"
    OWNER_QUOTE = "OWNER_QUOTE"
    VERIFIED_METRIC = "VERIFIED_METRIC"
    SERVICE_DETAIL = "SERVICE_DETAIL"
    CTA_CHANNEL = "CTA_CHANNEL"
    TRUST_CREDENTIAL = "TRUST_CREDENTIAL"


class SalesStateStrategy(str, Enum):
    HIDDEN = "HIDDEN"
    FACT_SAFE_CONTEXT = "FACT_SAFE_CONTEXT"
    ABSTRACT_FORM = "ABSTRACT_FORM"
    LICENSED_CONTEXT = "LICENSED_CONTEXT"
    PUBLIC_AUTHENTIC_ASSET = "PUBLIC_AUTHENTIC_ASSET"


VERIFIED_ONLY_KINDS = {
    EvidenceSlotKind.RESULT_CASE,
    EvidenceSlotKind.TESTIMONIAL,
    EvidenceSlotKind.OWNER_QUOTE,
    EvidenceSlotKind.VERIFIED_METRIC,
    EvidenceSlotKind.TRUST_CREDENTIAL,
}

VISUAL_KINDS = {
    EvidenceSlotKind.HERO_REALITY,
    EvidenceSlotKind.OWNER_PORTRAIT,
    EvidenceSlotKind.CRAFT_ACTION,
    EvidenceSlotKind.PLACE_WIDE,
    EvidenceSlotKind.PRODUCT_DETAIL,
    EvidenceSlotKind.RESULT_CASE,
}


@dataclass
class PhotoDirection:
    purpose: str
    preferred_orientation: str = "any"
    preferred_aspect_ratio: str = ""
    focal_subject: str = ""
    focal_relationship: str = ""
    shot_distance: str = ""
    copy_safe_zone: str = ""
    light_direction: str = ""
    minimum_resolution_px: int | None = None
    crop_tolerance: str = ""
    avoid: list[str] = field(default_factory=list)
    mobile_variant: str = ""


@dataclass
class ClientEvidenceSlot:
    id: str
    kind: EvidenceSlotKind
    section_id: str
    required_for_delivery: bool
    purpose: str
    sales_state_fallback: str
    photo_direction: PhotoDirection | None = None
    question_prompt: str = ""
    confirmation_prompt: str = ""
    accepted_formats: list[str] = field(default_factory=list)
    max_items: int = 1
    sales_state_strategy: SalesStateStrategy = SalesStateStrategy.HIDDEN
    sales_state_complete: bool = True
    replacement_preserves_hierarchy: bool = True
    misleading_proxy: bool = False
    verification_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["sales_state_strategy"] = self.sales_state_strategy.value
        return data


def validate_slot(slot: ClientEvidenceSlot) -> list[str]:
    issues: list[str] = []
    if not slot.id.strip():
        issues.append("slot id is required")
    if not slot.section_id.strip():
        issues.append("section_id is required")
    if not slot.purpose.strip():
        issues.append("purpose is required")
    if not slot.sales_state_fallback.strip():
        issues.append(
            "sales_state_fallback is required so the sales sample is complete without client evidence"
        )
    if not slot.sales_state_complete:
        issues.append("sales state depends on future client evidence")
    if not slot.replacement_preserves_hierarchy:
        issues.append("client evidence replacement may change copy/layout hierarchy")
    if slot.misleading_proxy:
        issues.append("sales state uses a misleading proxy for client reality")

    if slot.kind in VISUAL_KINDS and slot.photo_direction is None:
        issues.append("visual evidence slot requires photo_direction")

    if slot.photo_direction:
        if slot.photo_direction.minimum_resolution_px is not None:
            if slot.photo_direction.minimum_resolution_px < 800:
                issues.append("minimum_resolution_px below 800 requires manual review")
        if not slot.photo_direction.focal_subject.strip():
            issues.append("photo_direction requires focal_subject")
        if not slot.photo_direction.crop_tolerance.strip():
            issues.append("photo_direction requires crop_tolerance")
        if not slot.photo_direction.mobile_variant.strip():
            issues.append("photo_direction requires mobile_variant")

    if slot.kind in VERIFIED_ONLY_KINDS:
        if slot.sales_state_strategy not in {
            SalesStateStrategy.HIDDEN,
            SalesStateStrategy.PUBLIC_AUTHENTIC_ASSET,
        }:
            issues.append("verified-only evidence cannot be simulated in sales state")
        if not slot.verification_required:
            issues.append("verified-only evidence must require verification")

    return issues


def evaluate_sales_to_enriched_contract(
    slots: list[ClientEvidenceSlot],
    *,
    required_section_ids: list[str] | None = None,
) -> dict[str, Any]:
    required_section_ids = required_section_ids or []
    rows: list[dict[str, Any]] = []
    valid_sections: set[str] = set()

    for slot in slots:
        issues = validate_slot(slot)
        if not issues:
            valid_sections.add(slot.section_id)
        rows.append({
            "slot_id": slot.id,
            "section_id": slot.section_id,
            "kind": slot.kind.value,
            "status": "PASS" if not issues else "REVIEW",
            "issues": issues,
        })

    missing_sections = [
        section_id for section_id in required_section_ids if section_id not in valid_sections
    ]
    all_valid = all(not row["issues"] for row in rows)
    status = "PASS" if all_valid and not missing_sections else "REVIEW"

    return {
        "status": status,
        "premium_ready": status == "PASS",
        "slot_count": len(slots),
        "required_section_ids": required_section_ids,
        "missing_required_sections": missing_sections,
        "slots": rows,
        "rule": (
            "Client evidence enriches a complete sales sample; it must never rescue an incomplete frame. "
            "Verified-only evidence must never be simulated, and real asset insertion must preserve hierarchy."
        ),
    }


def required_delivery_slots(slots: list[ClientEvidenceSlot]) -> list[ClientEvidenceSlot]:
    return [slot for slot in slots if slot.required_for_delivery]


def interview_questions(slots: list[ClientEvidenceSlot]) -> list[dict[str, Any]]:
    """Generate only questions that are actually required by the LP slot contract.

    This is a data seed for the future interview app, not the app itself.
    It deliberately avoids a generic website questionnaire.
    """
    questions: list[dict[str, Any]] = []
    for slot in slots:
        if not slot.question_prompt:
            continue
        item: dict[str, Any] = {
            "slot_id": slot.id,
            "kind": slot.kind.value,
            "section_id": slot.section_id,
            "required_for_delivery": slot.required_for_delivery,
            "question": slot.question_prompt,
            "confirmation": slot.confirmation_prompt,
            "accepted_formats": slot.accepted_formats,
            "max_items": slot.max_items,
        }
        if slot.photo_direction:
            item["photo_direction"] = asdict(slot.photo_direction)
        questions.append(item)
    return questions
