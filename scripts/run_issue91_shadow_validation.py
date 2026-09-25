"""Generate Issue #91 current-domain shadow validation evidence.

Fixtures are semantic audit labels only. They are never passed to routing logic
as company or reference identifiers.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from lp_engine.authored_composition_contract import (
    assert_decision_sensitivity,
    assert_identity_invariance,
    infer_authored_composition,
    plan_digest,
)
from lp_engine.authored_composition_runtime import consume_composition_plan


def _truth(value: Any, confidence: str = "verified") -> dict[str, Any]:
    return {"value": value, "confidence": confidence, "sources": ["synthetic-verified-fixture"]}


def fixture(
    fixture_id: str,
    *,
    family_id: str,
    category: str,
    primary_job: str,
    offer_count: int,
    media_role: str,
    risk: str = "medium",
    contradiction: bool = False,
) -> dict[str, Any]:
    offers = [
        {"id": f"offer-{index}", "name": f"offer-{index}", "job": "receive"}
        for index in range(offer_count)
    ]
    if offer_count > 1:
        offers[-1]["job"] = "learn"
    facts = [
        {
            "id": f"{fixture_id}-price",
            "claim": "verified price",
            "scope": "offer",
            "sources": ["synthetic-verified-fixture"],
            "confidence": "verified",
            "usable_for_persuasion": True,
        },
        {
            "id": f"{fixture_id}-process",
            "claim": "verified process",
            "scope": "process",
            "sources": ["synthetic-verified-fixture"],
            "confidence": "verified",
            "usable_for_persuasion": True,
        },
    ]
    return {
        "audit_fixture_id": fixture_id,
        "company_truth": {
            "category": _truth(category),
            "name": _truth("Synthetic business"),
            "offers": offers,
            "contact": _truth({"channel": "form"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": primary_job,
            "tensions": ["decision tension"],
            "questions": ["price", "process"],
            "risk_sensitivity": risk,
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": family_id,
            "version": "1",
            "rationale": ["verified decision shape"],
            "frozen": True,
        },
        "evidence": {
            "facts": facts,
            "proof_gaps": ["missing-room-photo"] if media_role == "space" else [],
            "contradictions": ["conflicting price"] if contradiction else [],
        },
        "media_roles": [{
            "role_id": f"{fixture_id}-media",
            "role": media_role,
            "required_content_class": "non_identifying_context",
            "rights": "generated",
        }],
        "renderer_capabilities": ["responsive"],
    }


def _semantic_summary(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "family_frozen": plan["family_frozen"],
        "family_id": plan["family_id"],
        "plan_digest": plan_digest(plan),
        "variation_vector": plan["variation_vector"],
        "topology": plan["topology"],
        "review_gate": plan["review_gate"],
        "scene_intents": [scene["intent"] for scene in plan["scene_intents"]],
    }


def run_validation(output_dir: str | Path) -> dict[str, Any]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    same_family_a = fixture(
        "beauty-choice-shape",
        family_id="family-alpha",
        category="beauty",
        primary_job="choose",
        offer_count=3,
        media_role="person",
    )
    same_family_b = fixture(
        "pilates-trust-shape",
        family_id="family-alpha",
        category="pilates-fitness",
        primary_job="trust",
        offer_count=1,
        media_role="process",
        risk="high",
    )
    collision_a = fixture(
        "cosmetics-compare-shape",
        family_id="family-beta",
        category="cosmetics",
        primary_job="compare",
        offer_count=2,
        media_role="material",
    )
    collision_b = fixture(
        "hair-consider-shape",
        family_id="family-gamma",
        category="hair_salon",
        primary_job="compare",
        offer_count=2,
        media_role="material",
    )
    fail_closed = fixture(
        "beauty-contradiction-shape",
        family_id="family-alpha",
        category="beauty",
        primary_job="trust",
        offer_count=1,
        media_role="space",
        contradiction=True,
    )

    plans = {key: infer_authored_composition(value) for key, value in {
        "same_family_a": same_family_a,
        "same_family_b": same_family_b,
        "collision_a": collision_a,
        "collision_b": collision_b,
        "fail_closed": fail_closed,
    }.items()}

    identity_changed = deepcopy(same_family_a)
    identity_changed["company_truth"]["name"]["value"] = "Different identity"
    identity_changed["company_truth"]["name"]["sources"] = ["different-source"]
    assert_identity_invariance(same_family_a, identity_changed)

    decision_changed = deepcopy(same_family_a)
    decision_changed["customer_decision_state"]["primary_job"] = "trust"
    decision_changed["customer_decision_state"]["risk_sensitivity"] = "high"
    assert_decision_sensitivity(same_family_a, decision_changed)

    same_family_differs = (
        plans["same_family_a"]["family_id"] == plans["same_family_b"]["family_id"]
        and (
            plans["same_family_a"]["topology"] != plans["same_family_b"]["topology"]
            or plans["same_family_a"]["variation_vector"] != plans["same_family_b"]["variation_vector"]
        )
    )
    collision_same_shape = (
        plans["collision_a"]["topology"] == plans["collision_b"]["topology"]
        and plans["collision_a"]["variation_vector"] == plans["collision_b"]["variation_vector"]
    )
    collision_result = "HUMAN_REVIEW_REQUIRED" if collision_same_shape else "EXPLICIT_DISCRIMINATOR"
    feasibility_preserves_family = (
        plans["fail_closed"]["feasibility"]["family_id"]
        == plans["fail_closed"]["family_id"]
    )
    reference_guard = all(
        "company_id" not in plan["fit_trace"]
        and "reference_name" not in plan["fit_trace"]
        and plan["fit_trace"]["identity_used"] is False
        and plan["fit_trace"]["reference_lookup_used"] is False
        for plan in plans.values()
    )
    shadow_consumed = all(
        consume_composition_plan(plan)["renderer_must_not_reinfer"] for plan in plans.values()
    )

    evidence = {
        "schema_version": "issue91_shadow_validation_v1",
        "fixture_ids_are_audit_labels_only": True,
        "domain_scope": ["beauty", "cosmetics", "hair_salon", "pilates_fitness"],
        "fixtures": {
            key: _semantic_summary(plan) for key, plan in plans.items()
        },
        "identity_invariance": "PASS",
        "decision_sensitivity": "PASS",
        "same_family_material_difference": "PASS" if same_family_differs else "FAIL",
        "cross_family_collision": {
            "result": collision_result,
            "family_a": plans["collision_a"]["family_id"],
            "family_b": plans["collision_b"]["family_id"],
        },
        "contradiction_fail_closed": plans["fail_closed"]["review_gate"]["status"] == "HUMAN_REVIEW_REQUIRED",
        "feasibility_family_preserved": feasibility_preserves_family,
        "reference_regression_guard": "PASS" if reference_guard else "FAIL",
        "shadow_consumer": "PASS" if shadow_consumed else "FAIL",
        "responsive_widths": [320, 360, 375, 390, 430, 768, 1024, 1280, 1440],
        "screenshot_validation": "DOWNSTREAM_NOT_APPLICABLE_TO_SHADOW_OUTPUT",
        "human_visible_template_resemblance": "NOT_SELF_DECLARED",
    }
    evidence["overall_technical_status"] = "PASS" if all([
        evidence["same_family_material_difference"] == "PASS",
        evidence["contradiction_fail_closed"],
        evidence["feasibility_family_preserved"],
        evidence["reference_regression_guard"] == "PASS",
        evidence["shadow_consumer"] == "PASS",
    ]) else "FAIL"
    (out / "issue91_shadow_validation.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts/issue91_shadow_validation")
    args = parser.parse_args()
    result = run_validation(args.out)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall_technical_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
