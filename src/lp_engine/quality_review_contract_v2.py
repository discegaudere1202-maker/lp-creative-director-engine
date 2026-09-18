"""Machine contract for Round 2C before Shun review."""
from __future__ import annotations

from typing import Any


def build_quality_review_contract(snapshot: dict[str, Any], evidence: dict[str, Any], decisions: dict[str, Any], experience: dict[str, Any], creative: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "research_schema": bool(snapshot.get("facts") and snapshot.get("sources")),
        "conflicts_preserved": any(item.get("status") == "CONFLICTED" for item in snapshot.get("conflicts", [])),
        "no_conflicted_hero_proof": not any(node.get("status") == "CONFLICTED" and ("HERO" in node.get("allowed_usage", []) or "PROOF" in node.get("allowed_usage", [])) for node in evidence.get("nodes", [])),
        "decision_first": experience.get("viewport_count") == 9 and all(view.get("user_questions") for view in experience.get("sections", [])),
        "one_viewport_one_complete_idea": all(view.get("complete_idea") for view in experience.get("sections", [])),
        "copy_roles_composed": all(view.get("copy_roles") for view in experience.get("sections", [])),
        "shot_contracts_complete": all(all(shot.get(key) for key in ("shot_id", "shot_type", "subject", "moment", "information_purpose", "evidence_status", "replacement_target")) for shot in creative.get("shots", [])),
        "motion_intent_bounded": all(item.get("intent") and item.get("reduced_motion") for item in creative.get("motion", [])),
        "microcraft_minimum": len(creative.get("microcraft", {}).get("decisions", [])) >= 20,
        "mobile_recomposition": bool(creative.get("mobile", {}).get("global")) and len(creative.get("mobile", {}).get("technical_widths", [])) == 4,
        "real_contact_only": any(fact.get("fact_id") == "action.phone" for fact in snapshot.get("facts", [])) and any(fact.get("fact_id") == "action.form" for fact in snapshot.get("facts", [])),
        "no_invented_price": any("標準料金" in unknown for unknown in snapshot.get("unknowns", [])),
        "actual_evidence_pending": creative.get("asset_policy", {}).get("actual_evidence_images") == "HEARING_REQUIRED_BEFORE_USE",
    }
    return {"schema_version": "quality_review_contract_v2", "review_stage": "MACHINE_TECHNICAL_VERIFICATION_BEFORE_SHUN", "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "constitution": "PROVISIONAL_NOT_FINAL", "human_final_judge": "Shun", "one_million_yen_pass": "NOT_ASSESSED"}
