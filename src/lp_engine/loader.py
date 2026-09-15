from __future__ import annotations
from .models import (
    Fact, CompanyProfile, CreativeConcept, SectionSpec,
    MotionSpec, ScreenshotScore
)


def from_dict(data):
    p = data["profile"]
    profile = CompanyProfile(
        company_name=p["company_name"],
        industry=p["industry"],
        facts=[Fact(**x) for x in p.get("facts", [])],
        has_owner_photos=p.get("has_owner_photos", False),
        has_place_photos=p.get("has_place_photos", False),
        has_material_photos=p.get("has_material_photos", False),
        has_product_behavior=p.get("has_product_behavior", False),
        has_strong_numeric_evidence=p.get("has_strong_numeric_evidence", False),
        has_complex_documents_or_rules=p.get("has_complex_documents_or_rules", False),
        has_distinct_founder_voice=p.get("has_distinct_founder_voice", False),
    )
    concept = CreativeConcept(**data["concept"])
    sections = [SectionSpec(**x) for x in data.get("sections", [])]
    motions = [MotionSpec(**x) for x in data.get("motions", [])]
    screenshots = [ScreenshotScore(**x) for x in data.get("screenshot_scores", [])]
    return profile, concept, sections, motions, screenshots
