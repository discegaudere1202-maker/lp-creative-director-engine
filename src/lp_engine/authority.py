from __future__ import annotations
from .models import CompanyProfile


AUTHORITY_KEYS = [
    "PERSON",
    "MATERIAL",
    "PRODUCT",
    "PLACE",
    "DATA",
    "DOCUMENT",
    "WORLD",
    "TYPOGRAPHY",
    "SENSORY",
]


def score_authorities(profile: CompanyProfile) -> dict[str, int]:
    scores = {k: 0 for k in AUTHORITY_KEYS}

    if profile.has_owner_photos:
        scores["PERSON"] += 5
    if profile.has_distinct_founder_voice:
        scores["PERSON"] += 4
        scores["TYPOGRAPHY"] += 2
    if profile.has_material_photos:
        scores["MATERIAL"] += 6
        scores["SENSORY"] += 2
    if profile.has_product_behavior:
        scores["PRODUCT"] += 6
    if profile.has_place_photos:
        scores["PLACE"] += 6
    if profile.has_strong_numeric_evidence:
        scores["DATA"] += 5
    if profile.has_complex_documents_or_rules:
        scores["DOCUMENT"] += 6
        scores["TYPOGRAPHY"] += 2

    industry = profile.industry.lower()
    if any(x in industry for x in ["社労士", "税理士", "法律", "士業"]):
        scores["DOCUMENT"] += 3
        scores["TYPOGRAPHY"] += 2
    if any(x in industry for x in ["製造", "工芸", "施工", "看板", "塗装"]):
        scores["MATERIAL"] += 2
        scores["PRODUCT"] += 1
    if any(x in industry for x in ["ホテル", "旅館", "宿泊", "観光"]):
        scores["PLACE"] += 3
    if any(x in industry for x in ["飲食", "レストラン", "食品"]):
        scores["SENSORY"] += 4
    if any(x in industry for x in ["saas", "ソフト", "システム"]):
        scores["DOCUMENT"] += 2
        scores["PRODUCT"] += 2
        scores["WORLD"] += 1

    return scores


def choose_primary_authority(profile: CompanyProfile) -> tuple[str, dict[str, int]]:
    scores = score_authorities(profile)
    primary = max(scores, key=lambda k: scores[k])
    return primary, scores
