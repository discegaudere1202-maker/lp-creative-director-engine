import copy
import unittest

from lp_engine.premium_perception_recovery import (
    MEDIA_BEAT_FIELDS,
    MEDIA_NARRATIVE_TEMPLATES,
    SPINE_V2_FIELDS,
    PremiumPerceptionRecoveryError,
    apply_premium_perception_recovery,
    compile_media_narrative_plan,
    compile_page_art_direction_spine_v2,
    validate_owner_delivery_integrity,
)
from lp_engine.production_cutover import consume_current_industry_production, plan_current_industry_production
from lp_engine.production_variant_bridge import render_variant_faithful_page, select_variant_ensemble
from lp_engine.whole_page_art_direction import apply_whole_page_art_direction
from lp_engine.visual_asset_production import render_asset_bound_authoritative_html


def truth(value, confidence="verified"):
    return {"value": value, "confidence": confidence, "sources": ["issue129-test"]}


def fixture(*, job="choose", offers=3, family="family-alpha", category="beauty_cosmetics"):
    return {
        "company_id": "company-a",
        "reference_id": "reference-a",
        "company_truth": {
            "category": truth(category),
            "name": truth("Issue129 Fixture"),
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
        "evidence": {
            "facts": [{"id": "process", "claim": "確認済み工程", "scope": "process", "sources": ["issue129-test"], "confidence": "verified", "usable_for_persuasion": False}],
            "proof_gaps": [],
            "contradictions": [],
        },
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


def build(raw, bound=None):
    bound = bound or bindings()
    plan = plan_current_industry_production(raw)
    directives = consume_current_industry_production(plan)
    ensemble = select_variant_ensemble(plan, directives, bound)
    rendered, _ = render_variant_faithful_page(plan, directives, bound, ensemble)
    rendered, whole = apply_whole_page_art_direction(rendered, plan, ensemble, bound)
    return plan, directives, ensemble, whole, rendered, bound


class Issue129PremiumPerceptionRecoveryTest(unittest.TestCase):
    def test_all_six_mechanism_families_have_authored_media_narratives(self):
        self.assertEqual(set(MEDIA_NARRATIVE_TEMPLATES), {"route", "evidence", "compare", "prepare", "act", "recognition"})
        counts = {family: len(beats) for family, beats in MEDIA_NARRATIVE_TEMPLATES.items()}
        self.assertGreater(len(set(counts.values())), 1)
        for beats in MEDIA_NARRATIVE_TEMPLATES.values():
            self.assertTrue(any(row["prominence_intent"] in {"dominant", "co-dominant"} for row in beats))

    def test_media_narrative_plan_has_required_fields_and_preserves_evidence_boundary(self):
        plan, _, ensemble, whole, _, bound = build(fixture(job="choose", offers=3))
        media = compile_media_narrative_plan(plan, ensemble, whole, bound)
        self.assertFalse(media["arbitrary_global_image_floor_used"])
        self.assertFalse(media["illustrative_media_promoted_to_proof"])
        self.assertFalse(media["identity_routing_used"])
        self.assertFalse(media["category_layout_routing_used"])
        self.assertFalse(media["randomness_used"])
        self.assertGreaterEqual(media["beat_count"], 3)
        for beat in media["beats"]:
            self.assertTrue(set(MEDIA_BEAT_FIELDS).issubset(beat))
            self.assertEqual(beat["evidence_status"], "GENERIC_ILLUSTRATIVE_STOCK")
            self.assertIn("never promote illustrative media", beat["fallback_restriction"])

    def test_spine_v2_is_complete_and_pixel_authoritative(self):
        plan, _, ensemble, whole, _, bound = build(fixture(job="trust", offers=1))
        media = compile_media_narrative_plan(plan, ensemble, whole, bound)
        spine = compile_page_art_direction_spine_v2(ensemble, whole, media)
        self.assertEqual(set(SPINE_V2_FIELDS), {field for field in SPINE_V2_FIELDS if field in spine})
        self.assertEqual(spine["media_narrative_arc"], [row["narrative_role"] for row in media["beats"]])
        self.assertTrue(spine["family_frozen"])
        self.assertFalse(spine["composition_plan_mutated"])
        self.assertFalse(spine["identity_routing_used"])
        self.assertFalse(spine["random_diversity_used"])

    def test_apply_recovery_adds_media_led_authored_scenes_and_mobile_contract(self):
        plan, _, ensemble, whole, rendered, bound = build(fixture(job="choose", offers=3))
        result, media, spine, trace = apply_premium_perception_recovery(rendered, plan, ensemble, whole, bound)
        self.assertIn('data-premium-perception-recovery="issue129"', result)
        self.assertIn('data-media-narrative="true"', result)
        self.assertGreaterEqual(result.count('data-premium-authored-scene="true"'), 2)
        self.assertGreater(result.count("<img "), 2)
        self.assertIn("@media(max-width:700px)", result)
        self.assertIn("prefers-reduced-motion:reduce", result)
        self.assertGreaterEqual(trace["dominant_or_codominant_beat_count"], 1)
        self.assertFalse(trace["human_visible_premium_declared"])
        self.assertTrue(trace["aoi_v2_required"])
        self.assertEqual(spine["media_narrative_arc"], [row["narrative_role"] for row in media["beats"]])

    def test_final_authoritative_html_uses_issue129_surface(self):
        raw = fixture(job="choose", offers=3)
        bound = bindings()
        plan = plan_current_industry_production(raw)
        directives = consume_current_industry_production(plan)
        before = copy.deepcopy((plan.get("family_id"), plan.get("topology"), plan.get("scene_intents")))
        rendered = render_asset_bound_authoritative_html(plan, directives, bound)
        after = (plan.get("family_id"), plan.get("topology"), plan.get("scene_intents"))
        self.assertEqual(before, after)
        self.assertIn('data-premium-perception-recovery="issue129"', rendered)
        self.assertIn("ppr-family--route", rendered)

    def test_media_required_mechanism_fails_closed_without_binding(self):
        plan = plan_current_industry_production(fixture(job="choose", offers=3))
        directives = consume_current_industry_production(plan)
        ensemble = select_variant_ensemble(plan, directives, {})
        rendered, _ = render_variant_faithful_page(plan, directives, {}, ensemble)
        rendered, whole = apply_whole_page_art_direction(rendered, plan, ensemble, {})
        with self.assertRaises(PremiumPerceptionRecoveryError):
            apply_premium_perception_recovery(rendered, plan, ensemble, whole, {})

    def test_identity_family_category_changes_do_not_drive_media_layout(self):
        raw1 = fixture(job="choose", offers=3, family="family-a", category="beauty_cosmetics")
        raw2 = copy.deepcopy(raw1)
        raw2["company_id"] = "other-company"
        raw2["reference_id"] = "other-reference"
        raw2["creative_family"]["family_id"] = "family-b"
        raw2["company_truth"]["category"] = truth("hair_salon_barber")
        p1, _, e1, w1, _, bound = build(raw1)
        p2, _, e2, w2, _, _ = build(raw2)
        m1 = compile_media_narrative_plan(p1, e1, w1, bound)
        m2 = compile_media_narrative_plan(p2, e2, w2, bound)
        shape1 = [(row["narrative_role"], row["compositional_role"], row["prominence_intent"]) for row in m1["beats"]]
        shape2 = [(row["narrative_role"], row["compositional_role"], row["prominence_intent"]) for row in m2["beats"]]
        self.assertEqual(shape1, shape2)

    def test_owner_delivery_integrity_fails_on_baseline_collision_or_screenshot_mismatch(self):
        current = {"SK1": "a" * 64, "SK2": "b" * 64}
        rejected = {"SK1": "c" * 64, "SK2": "b" * 64}
        screenshot = {"SK1": {"390": "a" * 64, "1440": "a" * 64}, "SK2": {"390": "x" * 64}}
        report = validate_owner_delivery_integrity(current, rejected, screenshot)
        self.assertFalse(report["pass"])
        reasons = {row["reason"] for row in report["failures"]}
        self.assertIn("CURRENT_REJECTED_BASELINE_COLLISION", reasons)
        self.assertIn("SCREENSHOT_HTML_MISMATCH:390", reasons)

    def test_owner_delivery_integrity_passes_only_for_exact_distinct_chain(self):
        current = {"SK1": "a" * 64}
        rejected = {"SK1": "b" * 64}
        screenshot = {"SK1": {str(width): "a" * 64 for width in (320, 390, 1440)}}
        report = validate_owner_delivery_integrity(current, rejected, screenshot)
        self.assertTrue(report["pass"])
        self.assertTrue(report["owner_html_equals_screenshot_input"])
        self.assertTrue(report["rejected_baseline_independently_distinct"])


if __name__ == "__main__":
    unittest.main()
