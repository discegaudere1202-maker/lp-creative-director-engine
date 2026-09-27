import copy
import unittest

from lp_engine.production_cutover import consume_current_industry_production, plan_current_industry_production
from lp_engine.production_variant_bridge import (
    PATTERN_TO_VARIANT,
    VARIANT_REGISTRY,
    ProductionVariantBridgeError,
    render_variant_faithful_page,
    select_variant_ensemble,
)
from lp_engine.visual_asset_production import render_asset_bound_authoritative_html


def truth(value, confidence="verified"):
    return {"value": value, "confidence": confidence, "sources": ["issue121-test"]}


def fixture(*, job="choose", offers=3, family="family-alpha", contact=True, persuasive=False):
    return {
        "company_truth": {
            "category": truth("beauty_cosmetics"),
            "name": truth("Variant Fixture"),
            "offers": [
                {"id": f"offer-{i}", "name": f"選択肢 {i}", "job": "choose"}
                for i in range(1, offers + 1)
            ],
            "contact": truth(
                {"channel": "form", "destination": "https://example.com/contact"}
                if contact else {"channel": "form"}
            ),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": job,
            "tensions": ["選ぶ前に不安がある"],
            "questions": ["price", "process", "difference"],
            "risk_sensitivity": "high" if job == "trust" else "medium",
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": family,
            "version": "1",
            "rationale": ["issue121 family frozen"],
            "frozen": True,
        },
        "evidence": {
            "facts": [
                {
                    "id": "process",
                    "claim": "確認済みの工程情報があります",
                    "scope": "process",
                    "sources": ["issue121-test"],
                    "confidence": "verified",
                    "usable_for_persuasion": persuasive,
                }
            ],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [
            {"role_id": "primary", "role": "process", "required_content_class": "generic", "rights": "licensed"}
        ],
        "renderer_capabilities": ["responsive"],
    }


def build(raw):
    plan = plan_current_industry_production(raw)
    directives = consume_current_industry_production(plan)
    ensemble = select_variant_ensemble(plan, directives, {})
    html, trace = render_variant_faithful_page(plan, directives, {}, ensemble)
    return plan, directives, ensemble, html, trace


class Issue121VariantBridgeTest(unittest.TestCase):
    def test_registry_covers_exact_accepted_15_patterns(self):
        expected = {
            "M-HERO-01", "M-HERO-02", "M-HERO-03", "M-TRUST-01", "M-TRUST-02",
            "M-PROBLEM-01", "M-STORY-01", "M-SERVICE-01", "M-PROCESS-01",
            "M-HUMAN-01", "M-GALLERY-01", "M-OFFER-01", "M-CTA-01", "M-END-01", "M-END-02",
        }
        self.assertEqual(set(PATTERN_TO_VARIANT), expected)
        self.assertEqual(len(VARIANT_REGISTRY), 15)
        self.assertTrue(all(row["renderer_implementation_identity"] for row in VARIANT_REGISTRY.values()))
        self.assertFalse(any(row["renderer_implementation_identity"] == "UNIMPLEMENTED_REQUIRED" for row in VARIANT_REGISTRY.values()))

    def test_stage_a_semantics_reach_all_three_real_hero_variants(self):
        choose = build(fixture(job="choose", offers=3))[2]["hero"]
        trust = build(fixture(job="trust", offers=1))[2]["hero"]
        act = build(fixture(job="act", offers=2))[2]["hero"]
        self.assertEqual(choose["selected_production_variant_id"], "PV-HERO-GUIDED-ROUTE-CANVAS-v1")
        self.assertEqual(trust["selected_production_variant_id"], "PV-HERO-EVIDENCE-ANCHOR-v1")
        self.assertEqual(act["selected_production_variant_id"], "PV-HERO-RECOGNITION-FIELD-v1")
        self.assertEqual(choose["source_pattern_ids"], ["M-HERO-03"])
        self.assertEqual(trust["source_pattern_ids"], ["M-HERO-02"])
        self.assertEqual(act["source_pattern_ids"], ["M-HERO-01"])

    def test_same_family_can_select_materially_different_hero_mechanisms(self):
        guided = build(fixture(job="choose", offers=3, family="same-family"))[2]
        evidence = build(fixture(job="trust", offers=1, family="same-family"))[2]
        recognition = build(fixture(job="prepare", offers=1, family="same-family"))[2]
        ids = {
            guided["hero"]["selected_production_variant_id"],
            evidence["hero"]["selected_production_variant_id"],
            recognition["hero"]["selected_production_variant_id"],
        }
        self.assertEqual(len(ids), 3)
        for ensemble in (guided, evidence, recognition):
            spine = ensemble["page_art_direction_spine"]
            self.assertFalse(spine["company_identity_used_for_routing"])
            self.assertFalse(spine["category_fixed_template_lookup_used"])
            self.assertFalse(spine["random_diversity_used"])

    def test_hero_renderers_have_materially_different_structures(self):
        choose_html = build(fixture(job="choose", offers=3))[3]
        trust_html = build(fixture(job="trust", offers=1))[3]
        act_html = build(fixture(job="act", offers=2))[3]
        self.assertIn("hero-route__routes", choose_html)
        self.assertNotIn("hero-evidence__ledger", choose_html)
        self.assertIn("hero-evidence__ledger", trust_html)
        self.assertNotIn("hero-recognition__side-note", trust_html)
        self.assertIn("hero-recognition__side-note", act_html)
        self.assertNotIn("hero-route__routes", act_html)

    def test_selected_scene_trace_is_research_to_renderer_complete(self):
        _, _, ensemble, html, trace = build(fixture(job="choose", offers=3))
        rows = [ensemble["hero"], *ensemble["scenes"], ensemble["cta"], ensemble["ending"]]
        for row in rows:
            self.assertTrue(row["source_pattern_ids"])
            self.assertTrue(row["selected_production_variant_id"])
            self.assertTrue(row["selection_reason"])
            self.assertIn("rejected_alternatives", row)
            self.assertTrue(row["renderer_implementation_identity"])
            self.assertEqual(set(map(int, row["responsive_variant_transform"])), {320,360,375,390,430,768,1024,1280,1440})
            self.assertIn(f'data-production-variant="{row["selected_production_variant_id"]}"', html)
        self.assertEqual(trace["renderer"]["final_visual_authority"], "production_variant_dispatch")
        self.assertFalse(trace["renderer"]["legacy_generic_premium_scene_final_authority"])
        self.assertFalse(trace["renderer"]["silent_generic_fallback"])

    def test_body_cta_and_ending_are_variant_owned(self):
        _, _, ensemble, html, _ = build(fixture(job="choose", offers=3))
        body_ids = {row["selected_production_variant_id"] for row in ensemble["scenes"]}
        self.assertIn("PV-SERVICE-INTENT-ROUTED-FIELD-v1", body_ids)
        self.assertIn("service-field__routes", html)
        self.assertEqual(ensemble["cta"]["selected_production_variant_id"], "PV-CTA-STATE-SPECIFIC-EVENT-v1")
        self.assertIn("state-event-cta", html)
        self.assertEqual(ensemble["ending"]["selected_production_variant_id"], "PV-END-EMOTIONAL-RESOLUTION-v1")
        self.assertIn("ending-emotional", html)

    def test_trust_without_persuasive_proof_fails_honestly_into_boundary_ledger(self):
        _, _, ensemble, html, _ = build(fixture(job="trust", offers=1, persuasive=False))
        selected = [row["selected_production_variant_id"] for row in ensemble["scenes"]]
        self.assertIn("PV-TRUST-BOUNDARY-LEDGER-v1", selected)
        self.assertIn("trust-ledger__table", html)
        self.assertNotIn("proof-thread__node", html)

    def test_trust_with_persuasive_verified_fact_uses_distributed_proof(self):
        _, _, ensemble, html, _ = build(fixture(job="trust", offers=1, persuasive=True))
        selected = [row["selected_production_variant_id"] for row in ensemble["scenes"]]
        self.assertIn("PV-TRUST-DISTRIBUTED-PROOF-THREAD-v1", selected)
        self.assertIn("proof-thread__node", html)

    def test_verified_positive_cta_and_non_action_boundary(self):
        actionable = build(fixture(job="act", contact=True))[3]
        blocked = build(fixture(job="act", contact=False))[3]
        self.assertIn('href="https://example.com/contact"', actionable)
        self.assertIn('aria-disabled="true"', blocked)
        self.assertNotIn('href="https://example.com/contact"', blocked)

    def test_semantic_heading_units_and_reduced_motion_survive_cutover(self):
        html = render_asset_bound_authoritative_html(*build(fixture(job="choose", offers=3))[:2], {})
        self.assertIn('data-semantic-heading="authored"', html)
        self.assertIn('>違いで</span>', html)
        self.assertIn('>ここから</span>', html)
        self.assertIn('>から、</span>', html)
        self.assertIn('>次へ。</span>', html)
        self.assertIn("@media(prefers-reduced-motion:reduce)", html)
        self.assertIn("animation:none!important", html)
        self.assertNotIn(".scene-copy h2{white-space:nowrap}", html)

    def test_selection_and_rendering_do_not_mutate_frozen_plan(self):
        raw = fixture(job="compare", offers=2)
        plan = plan_current_industry_production(raw)
        directives = consume_current_industry_production(plan)
        before = copy.deepcopy(plan)
        ensemble = select_variant_ensemble(plan, directives, {})
        render_variant_faithful_page(plan, directives, {}, ensemble)
        self.assertEqual(plan, before)
        self.assertTrue(plan["input"]["creative_family"]["frozen"])

    def test_unknown_selected_variant_fails_closed_without_generic_fallback(self):
        plan, directives, ensemble, _, _ = build(fixture(job="choose", offers=3))
        broken = copy.deepcopy(ensemble)
        broken["hero"]["selected_production_variant_id"] = "PV-UNKNOWN-v1"
        with self.assertRaises(ProductionVariantBridgeError):
            render_variant_faithful_page(plan, directives, {}, broken)


if __name__ == "__main__":
    unittest.main()
