"""Company-truth-derived creative decisions shared by IA and the renderer.

The genome is deliberately evidence/profile driven.  It contains no company
identity branching, so the same truth deterministically produces the same
creative form for any input.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def _text(value: Any) -> str:
    return str(value or "").strip()


def _evidence_types(evidence: Sequence[Mapping[str, Any]]) -> set[str]:
    return {_text(item.get("evidence_type")) for item in evidence}


def derive_creative_genome(
    understanding: Mapping[str, Any],
    strategy: Mapping[str, Any],
    evidence: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    profile = _text(strategy.get("layout_profile")) or "editorial_rail"
    authorities = list(strategy.get("visual_authority_priority") or understanding.get("visual_authority") or ["TYPOGRAPHY"])
    types = _evidence_types(evidence)
    if "CRAFT_ACTION" in types or profile in {"technical_drawing", "field_ledger"}:
        narrative, tempo = "craft", "grounded"
    elif "PRODUCT_DETAIL" in types or profile in {"catalogue_spread", "machine_catalogue"}:
        narrative, tempo = "mastery", "precise"
    elif "PLACE_EXPERIENCE" in types or profile in {"experience_calendar", "care_rhythm"}:
        narrative, tempo = "sensory_experience", "gentle"
    elif "TEAM_IDENTITY" in types or "OWNER_IDENTITY" in types:
        narrative, tempo = "guidance", "intimate"
    elif _text(understanding.get("conversion_goal")) in {"application", "visit"}:
        narrative, tempo = "participation", "warm"
    else:
        narrative, tempo = "discovery", "confident"

    forms = {
        "technical_drawing": ["immersive_image", "material_detail", "process_sequence", "asymmetric_editorial"],
        "field_ledger": ["editorial_split", "material_detail", "process_sequence", "progressive_story"],
        "experience_calendar": ["immersive_image", "sensory_pause", "human_dialogue", "progressive_story"],
        "care_rhythm": ["sensory_pause", "immersive_image", "human_dialogue", "progressive_story"],
        "studio_invitation": ["table_scene", "human_dialogue", "process_sequence", "progressive_story"],
        "catalogue_spread": ["editorial_split", "material_detail", "progressive_story", "asymmetric_editorial"],
        "machine_catalogue": ["material_detail", "editorial_split", "process_sequence", "asymmetric_editorial"],
        "conversation_rail": ["human_dialogue", "editorial_split", "progressive_story", "sensory_pause"],
        "image_story": ["immersive_image", "asymmetric_editorial", "progressive_story", "sensory_pause"],
        "local_route": ["editorial_split", "progressive_story", "human_dialogue", "asymmetric_editorial"],
    }
    composition = forms.get(profile, ["editorial_split", "progressive_story", "human_dialogue", "asymmetric_editorial"])
    goal = _text(understanding.get("conversion_goal")) or "inquiry"
    cta_progression = [
        {"stage": "discovery", "section_role": "hero_orientation", "user_hesitation": "自分に関係する入口か分からない", "evidence_already_seen": [], "action_reason": "まず状況を見渡す"},
        {"stage": "reassurance", "section_role": "company_truth", "user_hesitation": "この会社へ相談してよいか迷う", "evidence_already_seen": [item.get("evidence_id") for item in evidence[:2]], "action_reason": "会社固有の範囲を確かめる"},
        {"stage": "action", "section_role": "cta_zone", "user_hesitation": "何を伝えればよいか分からない", "evidence_already_seen": [item.get("evidence_id") for item in evidence], "action_reason": f"{goal}の確認へ進む"},
    ]
    return {
        "schema_version": "creative_genome_v1",
        "dominant_narrative": narrative,
        "emotional_tempo": tempo,
        "visual_authority_priority": authorities,
        "composition_logic": composition,
        "signature_moment": {"section_role": "company_truth", "reason": "Company Truthと主役のVisual Authorityが同じ画面で結び付く瞬間"},
        "screenshot_peak_plan": [
            {"section_role": "hero_orientation", "visual_authority": authorities[0], "composition": composition[0], "reason": "最初の認識を決める"},
            {"section_role": "company_truth", "visual_authority": authorities[min(1, len(authorities) - 1)], "composition": composition[1], "reason": "固有のTruthを記憶に残す"},
            {"section_role": "service_process", "visual_authority": authorities[0], "composition": composition[2], "reason": "行動の順番を見せる"},
        ],
        "cta_progression": cta_progression,
        "mobile_redirection": {
            "hero_crop": "focus_primary_authority",
            "visual_text_order": "authority_before_explanation",
            "whitespace": "preserve_tempo_pause",
            "section_density": "reduce_supporting_density",
            "image_prominence": "promote_signature_moment",
            "cta_timing": "after_reassurance",
        },
        "derivation": {
            "source": "Company Truth + evidence types + conversion goal + visual authority",
            "profile": profile,
            "evidence_types": sorted(types),
            "deterministic": True,
        },
    }


def public_copy_gate(html: str) -> dict[str, Any]:
    markers = ("photo_role", "provenance", "generation_id", "debug", "verification workflow", "未確認の対応内容は書きません", "company_id")
    leaked = [marker for marker in markers if marker.casefold() in html.casefold()]
    return {"status": "PASS" if not leaked else "FAIL", "leaked_visible_internal_fields": leaked}
