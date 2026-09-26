import copy
import unittest

from lp_engine.premium_authorship import (
    BANNED_VALIDATION_COPY,
    INTERNAL_INTENT_TOKENS,
    MOBILE_WIDTHS,
    build_premium_uplift,
    render_premium_asset_bound_html,
)
from lp_engine.production_cutover import consume_current_industry_production, plan_current_industry_production


def truth(value, confidence="verified"):
    return {"value": value, "confidence": confidence, "sources": ["issue116-fixture"]}


def fixture(
    *,
    category="beauty_cosmetics",
    job="choose",
    family="family-alpha",
    offers=3,
    contact=True,
    risk=None,
):
    risk = risk or ("high" if job == "trust" else "medium")
    return {
        "company_truth": {
            "category": truth(category),
            "name": truth("Premium Fixture"),
            "offers": [
                {"id": f"offer-{i}", "name": f"メニュー {i}", "job": "choose"}
                for i in range(1, offers + 1)
            ],
            "contact": truth(
                {"channel": "form", "destination": "https://example.com/contact"}
                if contact
                else {"channel": "form"}
            ),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": job,
            "tensions": ["選ぶ前に不安がある"],
            "questions": ["price", "process"],
            "risk_sensitivity": risk,
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": family,
            "version": "1",
            "rationale": ["premium fixture family frozen"],
            "frozen": True,
        },
        "evidence": {
            "facts": [
                {
                    "id": "process",
                    "claim": "確認済みの流れがあります",
                    "scope": "process",
                    "sources": ["issue116-fixture"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                }
            ],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [
            {
                "role_id": "primary",
                "role": "process",
                "required_content_class": "generic",
                "rights": "licensed",
            }
        ],
        "renderer_capabilities": ["responsive"],
    }


class PremiumAuthorshipTest(unittest.TestCase):
    def _build(self, raw):
        plan = plan_current_industry_production(raw)
        directives = consume_current_industry_production(plan)
        premium = build_premium_uplift(plan, directives, {})
        html = render_premium_asset_bound_html(plan, directives, {}, premium)
        return plan, directives, premium, html

    def test_pu1_removes_internal_tokens_and_validation_copy(self):
        _, _, premium, html = self._build(fixture(job="choose"))
        public = premium["PU1_public_copy"]
        for token in INTERNAL_INTENT_TOKENS:
            self.assertNotIn(f">{token}<", html)
            self.assertNotIn(f">{token}のための", html)
        for phrase in BANNED_VALIDATION_COPY:
            self.assertNotIn(phrase, html)
        self.assertTrue(public["trace"]["validation_copy_removed"])
        self.assertTrue(public["trace"]["internal_intent_tokens_are_private"])

    def test_verified_factual_copy_has_evidence_trace(self):
        _, _, premium, _ = self._build(fixture())
        claims = premium["PU1_public_copy"]["trace"]["factual_claims"]
        self.assertTrue(claims)
        self.assertTrue(all(row["fact_id"] and row["sources"] for row in claims))
        self.assertEqual({row["fact_id"] for row in claims}, {"process"})

    def test_positive_cta_requires_verified_destination(self):
        _, _, premium, html = self._build(fixture(contact=True))
        cta = premium["PU5_proof_cta"]["cta"]
        self.assertTrue(cta["actionable"])
        self.assertEqual(cta["verified_destination"], "https://example.com/contact")
        self.assertIn('class="cta-primary"', html)
        self.assertIn('href="https://example.com/contact"', html)

        _, _, blocked, blocked_html = self._build(fixture(contact=False))
        blocked_cta = blocked["PU5_proof_cta"]["cta"]
        self.assertFalse(blocked_cta["actionable"])
        self.assertIsNone(blocked_cta["verified_destination"])
        self.assertIn('aria-disabled="true"', blocked_html)
        self.assertNotIn('href="https://example.com/contact"', blocked_html)

    def test_same_family_semantic_changes_create_visible_divergence(self):
        first = self._build(fixture(job="choose", family="same-family", offers=3))[2]
        second = self._build(fixture(job="trust", family="same-family", offers=1))[2]
        self.assertNotEqual(
            first["PU2_hero_authority"]["hero_composition_intent"],
            second["PU2_hero_authority"]["hero_composition_intent"],
        )
        self.assertNotEqual(
            first["PU6_visual_voice"]["voice_mode"],
            second["PU6_visual_voice"]["voice_mode"],
        )
        self.assertNotEqual(
            first["PU3_scene_dramaturgy"]["same_family_divergence_inputs"],
            second["PU3_scene_dramaturgy"]["same_family_divergence_inputs"],
        )

    def test_category_does_not_directly_select_visual_template(self):
        first = self._build(fixture(category="beauty_cosmetics", job="trust", offers=1))[2]
        second = self._build(fixture(category="pilates_fitness", job="trust", offers=1))[2]
        self.assertEqual(
            first["PU2_hero_authority"]["hero_composition_intent"],
            second["PU2_hero_authority"]["hero_composition_intent"],
        )
        self.assertEqual(
            first["PU6_visual_voice"]["voice_mode"],
            second["PU6_visual_voice"]["voice_mode"],
        )
        self.assertFalse(first["category_direct_visual_template_lookup"])
        self.assertFalse(second["category_direct_visual_template_lookup"])

    def test_composition_plan_and_review_gate_are_preserved(self):
        raw = fixture(job="trust")
        plan = plan_current_industry_production(raw)
        directives = consume_current_industry_production(plan)
        topology_before = copy.deepcopy(plan["topology"])
        scenes_before = copy.deepcopy(plan["scene_intents"])
        review_before = copy.deepcopy(plan["review_gate"])
        premium = build_premium_uplift(plan, directives, {})
        self.assertEqual(plan["topology"], topology_before)
        self.assertEqual(plan["scene_intents"], scenes_before)
        self.assertEqual(premium["review_gate_preserved"], review_before)
        self.assertTrue(premium["family_frozen"])
        self.assertFalse(premium["asset_scarcity_family_switch"])

    def test_motion_has_purpose_and_reduced_motion_fallback(self):
        _, _, premium, html = self._build(fixture())
        motion = premium["PU7_motion"]
        self.assertTrue(motion["intents"])
        self.assertTrue(all(row["purpose"] in {"hierarchy", "sequence", "comparison", "feedback"} for row in motion["intents"]))
        self.assertTrue(all(row["reduced_motion_fallback"] for row in motion["intents"]))
        self.assertIn("@media(prefers-reduced-motion:reduce)", html)
        self.assertIn("animation:none!important", html)

    def test_mobile_has_explicit_authorship_for_all_five_widths(self):
        _, _, premium, html = self._build(fixture(job="trust", offers=1))
        mobile = premium["PU8_mobile"]
        self.assertEqual({int(width) for width in mobile["widths"]}, set(MOBILE_WIDTHS))
        self.assertFalse(mobile["desktop_dom_stack_only"])
        self.assertTrue(mobile["hero_media_first"])
        self.assertIn("@media(max-width:430px)", html)
        self.assertIn("data-mobile-media-first=", html)

    def test_scene_dramaturgy_is_not_uniform_stack(self):
        _, _, premium, _ = self._build(fixture(job="choose", offers=3))
        rows = list(premium["PU3_scene_dramaturgy"]["scenes"].values())
        signatures = {
            (row["scene_weight"], row["density_mode"], row["canvas_width_mode"], row["media_text_relationship"])
            for row in rows
        }
        self.assertGreaterEqual(len(signatures), 2)

    def test_generic_stock_can_never_become_company_evidence(self):
        raw = fixture()
        plan = plan_current_industry_production(raw)
        directives = consume_current_industry_production(plan)
        binding = {
            "asset_id": "generic-1",
            "binary_sha256": "a" * 64,
            "media_role": "hero",
            "scene_id": "recognize",
            "evidence_status": "GENERIC_ILLUSTRATIVE_STOCK",
            "rights_gate": "RIGHTS_PASS",
            "local_asset_path": "generic.jpg",
            "focal_point": [0.5, 0.5],
            "alt": "",
        }
        premium = build_premium_uplift(plan, directives, {"hero": binding})
        story = premium["PU4_media_story"]["bindings"]["hero"]
        self.assertFalse(story["generic_stock_promoted_to_evidence"])
        self.assertEqual(story["claim_adjacency"], [])
        self.assertEqual(story["caption_mode"], "illustrative_explicit")


if __name__ == "__main__":
    unittest.main()
