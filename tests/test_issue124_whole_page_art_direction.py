import copy
import unittest

from lp_engine.production_cutover import consume_current_industry_production, plan_current_industry_production
from lp_engine.production_variant_bridge import render_variant_faithful_page, select_variant_ensemble
from lp_engine.whole_page_art_direction import (
    CONTINUATION_REGISTRY,
    SPINE_FIELDS,
    WholePageArtDirectionError,
    apply_whole_page_art_direction,
    registry_manifest,
    select_whole_page_continuation,
)


def truth(value, confidence="verified"):
    return {"value": value, "confidence": confidence, "sources": ["issue124-test"]}


def fixture(*, job="choose", offers=3, family="family-alpha", category="beauty_cosmetics"):
    return {
        "company_id": "company-a",
        "reference_id": "reference-a",
        "company_truth": {
            "category": truth(category),
            "name": truth("Whole Page Fixture"),
            "offers": [{"id": f"offer-{i}", "name": f"選択肢 {i}", "job": "choose"} for i in range(1, offers + 1)],
            "contact": truth({"channel": "form", "destination": "https://example.com/contact"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": job,
            "tensions": ["判断前の不安"],
            "questions": ["price", "process", "difference"],
            "risk_sensitivity": "high" if job == "trust" else "medium",
            "decision_stage": "consider",
        },
        "creative_family": {"family_id": family, "version": "1", "rationale": ["frozen"], "frozen": True},
        "evidence": {"facts": [{"id": "process", "claim": "確認済み工程", "scope": "process", "sources": ["issue124-test"], "confidence": "verified", "usable_for_persuasion": False}], "proof_gaps": [], "contradictions": []},
        "media_roles": [{"role_id": "primary", "role": "process", "required_content_class": "generic", "rights": "licensed"}],
        "renderer_capabilities": ["responsive"],
    }


def media_binding(content_class="product_packshot_generic", posture="portrait"):
    dimensions = [1200, 1800] if posture == "portrait" else [1800, 1000] if posture == "landscape" else [1200, 1200]
    return {
        "asset_id": f"asset-{content_class}-{posture}",
        "binary_sha256": "a" * 64,
        "media_role": "tools_material_detail",
        "scene_id": "choose",
        "evidence_status": "GENERIC_ILLUSTRATIVE_ONLY",
        "rights_gate": "PASS",
        "trace": {
            "required_content_conditions": {"content_class": content_class},
            "source_dimensions": dimensions,
        },
    }


def build(raw, bindings=None):
    bindings = bindings or {}
    plan = plan_current_industry_production(raw)
    directives = consume_current_industry_production(plan)
    ensemble = select_variant_ensemble(plan, directives, bindings)
    html, _ = render_variant_faithful_page(plan, directives, bindings, ensemble)
    return plan, directives, ensemble, html


class Issue124WholePageArtDirectionTest(unittest.TestCase):
    def test_registry_covers_required_continuation_families(self):
        manifest = registry_manifest()
        self.assertTrue(manifest["all_renderer_identities_implemented"])
        self.assertTrue({"recognition", "evidence", "route", "compare", "prepare", "act"}.issubset(set(manifest["continuation_families"])))
        self.assertGreaterEqual(len(CONTINUATION_REGISTRY), 9)

    def test_all_nine_spine_fields_are_required_and_propagated(self):
        plan, _, ensemble, _ = build(fixture(job="choose", offers=3))
        trace = select_whole_page_continuation(plan, ensemble, {"choose": media_binding()})
        self.assertEqual(set(trace["spine_fields_propagated"]), set(SPINE_FIELDS))
        self.assertEqual(set(trace["selection_inputs"]["page_art_direction_spine"]), set(SPINE_FIELDS))
        broken = copy.deepcopy(ensemble)
        del broken["page_art_direction_spine"]["density_arc"]
        with self.assertRaises(WholePageArtDirectionError):
            select_whole_page_continuation(plan, broken, {})

    def test_selection_never_uses_identity_family_or_category_as_layout_lookup(self):
        raw = fixture(job="choose", offers=3, family="family-alpha", category="beauty_cosmetics")
        bindings = {"choose": media_binding("product_packshot_generic", "portrait")}
        plan1, _, ensemble1, _ = build(raw, bindings)
        trace1 = select_whole_page_continuation(plan1, ensemble1, bindings)

        changed = copy.deepcopy(raw)
        changed["company_id"] = "completely-different-company"
        changed["reference_id"] = "different-reference"
        changed["creative_family"]["family_id"] = "different-frozen-family"
        changed["company_truth"]["category"] = truth("unrelated_category")
        plan2, _, ensemble2, _ = build(changed, bindings)
        trace2 = select_whole_page_continuation(plan2, ensemble2, bindings)

        self.assertEqual(trace1["continuation_variant_id"], trace2["continuation_variant_id"])
        self.assertEqual(trace1["identity_routing"], {
            "company_id_used": False,
            "reference_id_used": False,
            "family_id_used_as_layout_lookup": False,
            "business_category_used_as_layout_lookup": False,
            "randomness_used": False,
        })

    def test_route_continuations_have_materially_different_selection_and_css(self):
        raw = fixture(job="choose", offers=3)
        plan, _, ensemble, html = build(raw)
        specimen = select_whole_page_continuation(plan, ensemble, {"choose": media_binding("product_packshot_generic", "portrait")})
        workbench = select_whole_page_continuation(plan, ensemble, {"choose": media_binding("tools_detail_generic", "landscape")})
        self.assertEqual(specimen["continuation_variant_id"], "WP-ROUTE-SPECIMEN-v1")
        self.assertEqual(workbench["continuation_variant_id"], "WP-ROUTE-WORKBENCH-v1")
        self.assertNotEqual(specimen["propagation"], workbench["propagation"])
        rendered, _ = apply_whole_page_art_direction(html, plan, ensemble, {"choose": media_binding("tools_detail_generic", "landscape")})
        self.assertIn("wp-route-workbench", rendered)
        self.assertIn("grid-template-columns:repeat(12,1fr)", rendered)
        self.assertIn("data-mobile-authored=\"true\"", rendered)

    def test_evidence_continuations_distinguish_specimen_salon_and_open_studio(self):
        plan, _, ensemble, _ = build(fixture(job="trust", offers=1))
        variants = {
            select_whole_page_continuation(plan, ensemble, {"trust": media_binding("product_packshot_generic", "portrait")})["continuation_variant_id"],
            select_whole_page_continuation(plan, ensemble, {"trust": media_binding("salon_interior_generic", "portrait")})["continuation_variant_id"],
            select_whole_page_continuation(plan, ensemble, {"trust": media_binding("studio_interior_generic", "portrait")})["continuation_variant_id"],
        }
        self.assertEqual(variants, {"WP-EVIDENCE-SPECIMEN-v1", "WP-EVIDENCE-SALON-RAIL-v1", "WP-EVIDENCE-OPEN-STUDIO-v1"})

    def test_compare_replaces_second_intent_route_with_real_paired_mechanism(self):
        plan, _, ensemble, html = build(fixture(job="compare", offers=2))
        bindings = {"choose": media_binding("product_packshot_generic", "portrait")}
        rendered, trace = apply_whole_page_art_direction(html, plan, ensemble, bindings)
        self.assertEqual(trace["continuation_variant_id"], "WP-COMPARE-PAIRED-SPECIMEN-v1")
        self.assertIn('data-compare-mechanism="paired-contrast"', rendered)
        self.assertIn("PAIRED / CONTRAST", rendered)
        self.assertIn("wp-compare-axis", rendered)
        self.assertEqual(rendered.count('class="variant-scene service-field premium-scene"'), 0)
        self.assertEqual(rendered.count("compare-contrast-field"), 1)

    def test_compare_product_and_instrument_are_not_cross_family_clones(self):
        plan, _, ensemble, _ = build(fixture(job="compare", offers=2))
        specimen = select_whole_page_continuation(plan, ensemble, {"choose": media_binding("product_packshot_generic", "portrait")})
        instrument = select_whole_page_continuation(plan, ensemble, {"choose": media_binding("tools_detail_generic", "portrait")})
        self.assertEqual(specimen["continuation_variant_id"], "WP-COMPARE-PAIRED-SPECIMEN-v1")
        self.assertEqual(instrument["continuation_variant_id"], "WP-COMPARE-PAIRED-INSTRUMENT-v1")
        self.assertNotEqual(specimen["renderer_implementation_identity"], instrument["renderer_implementation_identity"])

    def test_prepare_and_act_own_distinct_body_closing_and_mobile_contracts(self):
        prepare_plan, _, prepare_ensemble, prepare_html = build(fixture(job="prepare", offers=1))
        act_plan, _, act_ensemble, act_html = build(fixture(job="act", offers=2))
        prepare_rendered, prepare_trace = apply_whole_page_art_direction(prepare_html, prepare_plan, prepare_ensemble, {})
        act_rendered, act_trace = apply_whole_page_art_direction(act_html, act_plan, act_ensemble, {})
        self.assertEqual(prepare_trace["continuation_variant_id"], "WP-PREPARE-PROCESS-v1")
        self.assertEqual(act_trace["continuation_variant_id"], "WP-ACT-OPEN-FIELD-v1")
        self.assertIn("wp-prepare-process", prepare_rendered)
        self.assertIn("wp-act-open-field", act_rendered)
        self.assertIn("margin-top:-86px", act_rendered)
        self.assertNotEqual(prepare_trace["propagation"]["ending"], act_trace["propagation"]["ending"])

    def test_truth_and_evidence_boundary_stays_fail_closed(self):
        plan, _, ensemble, _ = build(fixture(job="trust", offers=1))
        trace = select_whole_page_continuation(plan, ensemble, {"trust": media_binding("studio_interior_generic", "landscape")})
        self.assertFalse(trace["evidence_boundary"]["illustrative_media_promoted_to_proof"])
        self.assertFalse(trace["evidence_boundary"]["new_factual_claims_introduced"])
        self.assertTrue(trace["evidence_boundary"]["verified_cta_contract_preserved"])
        self.assertTrue(trace["family_frozen"])
        self.assertFalse(trace["composition_plan_mutated"])


if __name__ == "__main__":
    unittest.main()
