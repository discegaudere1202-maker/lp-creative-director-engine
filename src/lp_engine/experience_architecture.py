"""Decision-first IA and viewport architecture for Round 2C."""
from __future__ import annotations

from typing import Any


def build_experience_architecture(snapshot: dict[str, Any], decisions: dict[str, Any]) -> dict[str, Any]:
    sections = [
        ("V01", "hero", "Hero / proposition", ["D01", "D02"], "condition_first_entry", "LOW", "WORLD + CONTEXT", "attention/reveal", "状態を見る会社として入る。"),
        ("V02", "signs", "Exterior warning signs", ["D03"], "self_diagnosis", "MEDIUM", "DETAIL", "explanation", "これ相談していい、を自己判定する。"),
        ("V03", "scope", "Service scope", ["D02", "D03"], "scope_clarity", "MEDIUM", "EXPLANATION", "reveal", "外壁だけに閉じない相談範囲を理解する。"),
        ("V04", "proof", "Inspection & quantified public proof", ["D04", "D06", "D07"], "inspection_authority", "HIGH", "EXPLANATION + DATA", "proof", "ドローンと公開情報で信頼の理由を掴む。"),
        ("V05", "process", "Work process / craft", ["D05", "D06"], "process_transparency", "HIGH", "PROCESS", "process", "相談後に起きることを想像できる。"),
        ("V06", "evidence", "Public project & review evidence", ["D06", "D09"], "public_verification", "HIGH", "DATA + DOCUMENT", "proof", "公開された仕事とレビューで確かめる。"),
        ("V07", "material", "Paint / color decision support", ["D02", "D07"], "choice_support", "MEDIUM", "MATERIAL", "material", "色と塗料の選択情報を持ち帰る。"),
        ("V08", "faq", "FAQ / reassurance", ["D07", "D08", "D09"], "last_uncertainty", "MEDIUM", "DOCUMENT", "transition", "問い合わせ直前の不安を残さない。"),
        ("V09", "action", "Verified contact / close", ["D10"], "real_action", "LOW", "TYPOGRAPHY + ACTION", "action", "状態を見せるという実Actionへ進む。"),
    ]
    viewports = []
    for viewport_id, section_id, label, question_ids, complete_idea, density, focal, motion, benchmark_reason in sections:
        viewports.append({
            "viewport_id": viewport_id,
            "section_id": section_id,
            "label": label,
            "user_questions": question_ids,
            "information_gain": [row["answer"] for row in decisions["decisions"] if row["decision_id"] in question_ids],
            "emotional_role": complete_idea,
            "proof_role": "verified_public_facts" if section_id not in {"hero", "scope", "material"} else "context_or_explanation",
            "density": density,
            "viewport_count": 1,
            "cta_relation": "real_action" if section_id == "action" else "supporting_information",
            "complete_idea": complete_idea,
            "primary_focal": focal,
            "secondary_focal": "editorial copy + source label",
            "main_message": benchmark_reason,
            "copy_roles": [],
            "visual_roles": [],
            "proof_roles": [],
            "micro_craft": [],
            "motion_intent": motion.upper(),
            "entry_state": "resting_surface",
            "exit_state": "decision_clear",
            "desktop_composition": {},
            "mobile_composition": {},
            "benchmark_reason": benchmark_reason,
        })
    return {"schema_version": "experience_architecture_v2", "company_id": snapshot.get("company_id"), "architecture_principles": ["decision_before_scene", "viewport_is_creative_unit", "one_viewport_one_complete_idea", "information_supports_premium"], "section_count": 9, "viewport_count": 9, "sections": viewports, "density_rhythm": ["LOW", "MEDIUM", "MEDIUM", "HIGH", "HIGH", "HIGH", "MEDIUM", "MEDIUM", "LOW"], "dynamic_section_rule": "A section exists only when it answers a decision, increases trust, changes emotional state, or raises action readiness."}
