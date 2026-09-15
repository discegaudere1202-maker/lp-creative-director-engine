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

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["kind"] = self.kind.value
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
        issues.append("sales_state_fallback is required so the sales sample is complete without client evidence")
    if slot.kind in {
        EvidenceSlotKind.HERO_REALITY,
        EvidenceSlotKind.OWNER_PORTRAIT,
        EvidenceSlotKind.CRAFT_ACTION,
        EvidenceSlotKind.PLACE_WIDE,
        EvidenceSlotKind.PRODUCT_DETAIL,
        EvidenceSlotKind.RESULT_CASE,
    } and slot.photo_direction is None:
        issues.append("visual evidence slot requires photo_direction")
    if slot.photo_direction and slot.photo_direction.minimum_resolution_px is not None:
        if slot.photo_direction.minimum_resolution_px < 800:
            issues.append("minimum_resolution_px below 800 requires manual review")
    return issues


def required_delivery_slots(slots: list[ClientEvidenceSlot]) -> list[ClientEvidenceSlot]:
    return [slot for slot in slots if slot.required_for_delivery]


def interview_questions(slots: list[ClientEvidenceSlot]) -> list[dict[str, Any]]:
    """Generate only questions that are actually required by the LP slot contract.

    This is the seed for the future interview app. It deliberately does not generate
    a generic website questionnaire.
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
            "accepted_formats": slot.accepted_formats,
            "max_items": slot.max_items,
        }
        if slot.photo_direction:
            item["photo_direction"] = asdict(slot.photo_direction)
        questions.append(item)
    return questions
