import copy
import unittest

from lp_engine.production_cutover import (
    CURRENT_INDUSTRIES,
    ProductionCutoverError,
    consume_current_industry_production,
    derive_current_industry_authorship_input,
    plan_current_industry_production,
    semantic_body_units,
    semantic_headline_units,
)


def truth(value, confidence="verified"):
    return {"value": value, "confidence": confidence, "sources": ["issue99-fixture"]}


def fixture(category="beauty_cosmetics", job="choose", family="family-alpha", offers=2, rights="generated"):
    return {
        "company_truth": {
            "category": truth(category),
            "name": truth("Fixture business"),
            "offers": [{"id": f"offer-{i}", "name": f"Offer {i}", "job": "choose"} for i in range(offers)],
            "contact": truth({"channel": "form"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": job,
            "tensions": ["verified decision tension"],
            "questions": ["price", "process"],
            "risk_sensitivity": "high" if job == "trust" else "medium",
            "decision_stage": "consider",
        },
        "creative_family": {"family_id": family, "version": "1", "rationale": ["verified grammar"], "frozen": True},
        "evidence": {
            "facts": [
                {"id": "price", "claim": "verified price", "scope": "offer", "sources": ["fixture"], "confidence": "verified", "usable_for_persuasion": True},
                {"id": "process", "claim": "verified process", "scope": "process", "sources": ["fixture"], "confidence": "verified", "usable_for_persuasion": True},
            ],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [{"role_id": "primary", "role": "process", "required_content_class": "human_scale_detail", "rights": rights}],
        "renderer_capabilities": ["responsive"],
    }


class ProductionCutoverTest(unittest.TestCase):
    def test_320_semantic_headline_and_body_units(self):
        headline = semantic_headline_units("trust")
        body = semantic_body_units("決めるための情報を整理します。")
        self.assertEqual(headline, ("trustのための", "入口"))
        self.assertTrue(all(len(unit) > 1 for unit in headline))
        self.assertTrue(all(unit.strip() != "す。" for unit in body))
        self.assertTrue(all(unit.endswith(("。", "！", "？")) for unit in body))

    def test_supported_scopes_and_authority(self):
        for category in CURRENT_INDUSTRIES:
            plan = plan_current_industry_production(fixture(category=category))
            directives = consume_current_industry_production(plan)
            self.assertEqual(plan["production_authority"], "composition_plan")
            self.assertEqual(directives["production_authority"], "composition_plan")
            self.assertFalse(plan["cutover_trace"]["identity_used"])

    def test_identity_fields_do_not_change_semantic_plan(self):
        first = plan_current_industry_production(fixture())
        changed = fixture()
        changed["company_id"] = "other-company"
        changed["reference_id"] = "other-reference"
        second = plan_current_industry_production(changed)
        for key in ("family_id", "topology", "variation_vector", "scene_intents"):
            self.assertEqual(first[key], second[key])

    def test_category_only_changes_asset_scope(self):
        first = plan_current_industry_production(fixture(category="beauty_cosmetics"))
        second = plan_current_industry_production(fixture(category="pilates_fitness"))
        self.assertEqual(first["topology"], second["topology"])
        self.assertEqual(first["variation_vector"], second["variation_vector"])
        self.assertNotEqual(first["asset_pool_scope"], second["asset_pool_scope"])

    def test_feasibility_does_not_change_family_and_blocks_unknown_rights(self):
        raw = fixture(rights="unknown")
        plan = plan_current_industry_production(raw)
        self.assertEqual(plan["family_id"], "family-alpha")
        with self.assertRaises(ProductionCutoverError):
            consume_current_industry_production(plan)

    def test_contradiction_fails_closed(self):
        raw = fixture()
        raw["evidence"]["contradictions"] = ["price conflict"]
        plan = plan_current_industry_production(raw)
        with self.assertRaises(ProductionCutoverError):
            consume_current_industry_production(plan)


if __name__ == "__main__":
    unittest.main()
