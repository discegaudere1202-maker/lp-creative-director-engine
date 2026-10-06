import copy
import unittest

from lp_engine.premium_perception_reauthorship import (
    FROZEN_PASS_VARIANTS,
    R2_PROFILES,
    _apply_structural_markup,
    _reselect_pilates_media,
    apply_premium_perception_reauthorship,
)
from lp_engine.production_cutover import consume_current_industry_production, plan_current_industry_production
from lp_engine.visual_asset_library import render_asset_binding
from lp_engine.visual_asset_production import render_asset_bound_authoritative_html


RETURN_VARIANTS = {
    "WP-ROUTE-SPECIMEN-v1",
    "WP-COMPARE-PAIRED-SPECIMEN-v1",
    "WP-ROUTE-WORKBENCH-v1",
    "WP-PREPARE-PROCESS-v1",
    "WP-COMPARE-PAIRED-INSTRUMENT-v1",
    "WP-ACT-OPEN-FIELD-v1",
}
PASS_VARIANTS = {
    "WP-EVIDENCE-SPECIMEN-v1",
    "WP-EVIDENCE-SALON-RAIL-v1",
    "WP-EVIDENCE-OPEN-STUDIO-v1",
}


def truth(value, confidence="verified"):
    return {"value": value, "confidence": confidence, "sources": ["issue132-test"]}


def fixture(*, job="choose", offers=3):
    return {
        "company_id": "fixture-company",
        "reference_id": "fixture-reference",
        "company_truth": {
            "category": truth("beauty_cosmetics"),
            "name": truth("Issue132 Fixture"),
            "offers": [{"id": f"offer-{i}", "name": f"選択肢 {i}", "job": job} for i in range(1, offers + 1)],
            "contact": truth({"channel": "form", "destination": "https://example.com/contact"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": job,
            "tensions": ["判断前の不安"],
            "questions": ["price", "process", "difference"],
            "risk_sensitivity": "medium",
            "decision_stage": "consider",
        },
        "creative_family": {"family_id": "frozen-family", "version": "1", "rationale": ["frozen"], "frozen": True},
        "evidence": {"facts": [], "proof_gaps": [], "contradictions": []},
        "media_roles": [{"role_id": "primary", "role": "process", "required_content_class": "generic", "rights": "licensed"}],
        "renderer_capabilities": ["responsive"],
    }


def binding(asset_id, *, role, scene_id, content_class, local_path):
    return {
        "asset_id": asset_id,
        "binary_sha256": ("a" if asset_id.endswith("a") else "b") * 64,
        "media_role": role,
        "scene_id": scene_id,
        "evidence_status": "GENERIC_ILLUSTRATIVE_STOCK",
        "source_provider": "Pexels",
        "source_url": f"https://example.test/{asset_id}",
        "rights_gate": "RIGHTS_PASS_WITH_RENDER_CONDITIONS",
        "local_asset_path": local_path,
        "alt": "カテゴリを伝えるイメージ写真",
        "focal_point": [0.5, 0.5],
        "trace": {
            "required_content_conditions": {"content_class": content_class, "illustrative_only": True},
            "source_dimensions": [1800, 1200],
            "source_provider": "Pexels",
            "source_url": f"https://example.test/{asset_id}",
            "rights_gate_state": "RIGHTS_PASS_WITH_RENDER_CONDITIONS",
        },
    }


def bindings():
    return {
        "hero": binding("asset-a", role="hero", scene_id="hero", content_class="lifestyle_context_generic", local_path="assets/hero.jpg"),
        "choose": binding("asset-b", role="tools_material_detail", scene_id="choose", content_class="product_packshot_generic", local_path="assets/body.jpg"),
    }


def synthetic_html(variant):
    profile, groups = R2_PROFILES[variant]
    slots = [slot for _, members in groups for slot in members]
    section = {
        "hero": '<section class="variant-hero hero-route"><h1>Hero</h1></section>',
        "media1": '<section class="ppr-scene ppr-scene--1"><div class="ppr-scene__media"><div class="ppr-media"><img src="a.jpg"></div><div class="ppr-media"><img src="b.jpg"></div></div></section>',
        "media2": '<section class="ppr-scene ppr-scene--2"><div class="ppr-scene__media"><div class="ppr-media"><img src="a.jpg"></div><div class="ppr-media"><img src="b.jpg"></div></div></section>',
        "process": '<section class="variant-scene process-sequence">Process</section>',
        "compare": '<section class="variant-scene wp-compare">Compare</section>',
        "body": '<section class="variant-scene wp-body">Body</section>',
        "trust": '<section class="variant-scene wp-trust">Trust</section>',
        "action": '<section class="variant-scene wp-action-event">Action</section>',
        "cta": '<section class="variant-scene wp-cta">CTA</section>',
        "ending": '<section class="variant-scene wp-ending">Ending</section>',
    }
    if profile == "pilates_studio_action":
        section["hero"] = '<section class="variant-hero hero-recognition"><h1>Hero</h1></section>'
    return '<html><head><style>base{}</style></head><body class="x"><main><header>H</header>' + ''.join(section[s] for s in slots) + '<footer>F</footer></main></body></html>'


class Issue132PremiumPerceptionReauthorshipTest(unittest.TestCase):
    def test_scope_is_six_return_variants_and_three_frozen_pass_variants(self):
        self.assertEqual(set(R2_PROFILES), RETURN_VARIANTS)
        self.assertEqual(FROZEN_PASS_VARIANTS, PASS_VARIANTS)
        self.assertTrue(all("SK" not in key and "HS" not in key and "BR" not in key and "PI" not in key for key in R2_PROFILES))

    def test_each_return_variant_is_structurally_reauthored_not_css_only(self):
        for variant in RETURN_VARIANTS:
            source = synthetic_html(variant)
            result, profile, chapters = _apply_structural_markup(source, variant)
            self.assertNotEqual(source, result)
            self.assertIn('data-premium-reauthorship-r2="issue132"', result)
            self.assertIn(f'data-r2-profile="{profile}"', result)
            self.assertIn('data-r2-structural-reauthorship="true"', result)
            self.assertEqual(result.count('class="r2-chapter '), len(chapters))
            main_markup = result[result.find("<main"):result.rfind("</main>")]
            for _, members in R2_PROFILES[variant][1]:
                for slot in members:
                    marker = {
                        "hero": "variant-hero", "media1": "ppr-scene--1", "media2": "ppr-scene--2",
                        "process": "process-sequence", "compare": "wp-compare", "body": "wp-body",
                        "trust": "wp-trust", "action": "wp-action-event", "cta": "wp-cta", "ending": "wp-ending",
                    }[slot]
                    self.assertEqual(main_markup.count(marker), 1)
            self.assertIn("@media(max-width:700px)", result)

    def test_frozen_pass_variant_returns_owner_html_byte_identical(self):
        source = "<html><body>accepted issue129 owner html</body></html>"
        for variant in PASS_VARIANTS:
            rendered, media, trace = apply_premium_perception_reauthorship(
                source,
                {"continuation_variant_id": variant},
                {},
                {"beats": [], "family_frozen": True},
                {"family_reopened": False, "composition_plan_mutated": False},
            )
            self.assertEqual(rendered, source)
            self.assertEqual(media["beats"], [])
            r2 = trace["issue132_reauthorship"]
            self.assertFalse(r2["applied"])
            self.assertTrue(r2["pass_sample_freeze_variant"])
            self.assertFalse(r2["html_byte_mutated"])

    def test_return_trace_preserves_family_composition_and_forbids_identity_random_routing(self):
        variant = "WP-ROUTE-SPECIMEN-v1"
        rendered, _, trace = apply_premium_perception_reauthorship(
            synthetic_html(variant),
            {"continuation_variant_id": variant},
            {},
            {"beats": [], "family_frozen": True},
            {"family_reopened": False, "composition_plan_mutated": False},
        )
        self.assertIn('data-r2-profile="route_editorial_reframe"', rendered)
        r2 = trace["issue132_reauthorship"]
        self.assertTrue(r2["applied"])
        self.assertTrue(r2["macro_silhouette_reauthored"])
        self.assertTrue(r2["mobile_390_independent_recomposition"])
        self.assertFalse(r2["family_reopened"])
        self.assertFalse(r2["composition_plan_mutated"])
        self.assertFalse(r2["identity_routing_used"])
        self.assertFalse(r2["category_layout_routing_used"])
        self.assertFalse(r2["randomness_used"])
        self.assertFalse(r2["arbitrary_image_count_inflation_used"])
        self.assertFalse(r2["illustrative_media_promoted_to_proof"])
        self.assertFalse(r2["human_visible_pass_declared"])

    def test_pi1_reselection_preserves_legacy_binding_and_rebinds_only_authored_media(self):
        bound = bindings()
        original_body = render_asset_binding(bound["choose"])
        ppr_body = original_body.replace('class="production-asset"', 'class="ppr-production-asset"', 1)
        hero_ppr = render_asset_binding(bound["hero"]).replace('class="production-asset"', 'class="ppr-production-asset"', 1)
        rendered = '<div class="legacy">' + original_body + '</div><div class="narrative">' + ppr_body + '</div>'
        media_plan = {
            "beats": [{
                "source_binding_key": "choose",
                "source_asset_id": "asset-b",
                "source_rights_identity": {},
                "source_reused_for_composition": False,
            }]
        }
        revised_html, revised_plan, proof = _reselect_pilates_media(rendered, bound, media_plan)
        self.assertTrue(proof["applied"])
        self.assertTrue(proof["legacy_source_binding_preserved"])
        self.assertTrue(proof["decorative_legacy_slot_hidden_by_profile"])
        self.assertFalse(proof["client_evidence_promoted"])
        self.assertIn(original_body, revised_html)
        self.assertIn(hero_ppr, revised_html)
        self.assertNotIn(ppr_body, revised_html)
        beat = revised_plan["beats"][0]
        self.assertEqual(beat["source_binding_key"], "hero")
        self.assertEqual(beat["source_asset_id"], "asset-a")
        self.assertEqual(beat["source_rights_identity"]["rights_gate"], "RIGHTS_PASS_WITH_RENDER_CONDITIONS")

    def test_normal_production_route_surface_receives_issue132_after_issue129(self):
        raw = fixture(job="choose", offers=3)
        plan = plan_current_industry_production(raw)
        directives = consume_current_industry_production(plan)
        before = copy.deepcopy((plan.get("family_id"), plan.get("topology"), plan.get("scene_intents")))
        rendered = render_asset_bound_authoritative_html(plan, directives, bindings())
        after = (plan.get("family_id"), plan.get("topology"), plan.get("scene_intents"))
        self.assertEqual(before, after)
        self.assertIn('data-premium-perception-recovery="issue129"', rendered)
        self.assertIn('data-premium-reauthorship-r2="issue132"', rendered)
        self.assertIn('data-r2-structural-reauthorship="true"', rendered)


if __name__ == "__main__":
    unittest.main()
