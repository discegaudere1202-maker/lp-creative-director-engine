import unittest

from lp_engine.human_translation import (
    CTA_DESTINATION_TYPES, EXPRESSION_MODES, build_art_direction_token_profile,
    build_cta_closure, build_human_translation, build_peak_candidates,
    build_photo_binding, build_premium_copy_translation, definition_score,
    derive_signature_anchors, evaluate_definition_gate,
)


class HumanTranslationTest(unittest.TestCase):
    def setUp(self):
        self.u = {"company_id": "synthetic", "company_name": "Synthetic", "location": "福岡市", "service_category": "料理教室", "company_truth": "少人数で料理を学ぶ教室。", "customer_state": {"before": "何を確認すればよいか分からない", "barrier": "自分に合う入口か分からない", "after": "まず内容を伝えてみようと思える"}, "contact_channels": {"href": "https://example.test/contact", "primary": "公式サイト"}}
        self.strategy = {"layout_profile": "studio_invitation", "creative_genome": {"cta_progression": [{"stage": "discovery", "visible_label": "内容を見る"}, {"stage": "reassurance", "visible_label": "流れを知る"}, {"stage": "action", "visible_label": "参加を相談する"}]}}
        self.evidence = [{"evidence_id": "e1", "evidence_type": "SERVICE_SCOPE", "claim": "少人数で料理を学ぶ教室。", "verification_status": "VERIFIED"}, {"evidence_id": "e2", "evidence_type": "CTA_CHANNEL", "claim": "公式サイトから参加を相談する。", "verification_status": "VERIFIED"}]
        self.plan = {"scene_plan": [{"scene_id": "s1", "narrative_state": "observe", "narrative_function": "SHOW_DETAIL", "visual_authority": "PRODUCT", "copy_intent": "PROVE", "expected_media": True, "focal_entity": "hero_shared_cooking", "evidence_ids": ["e1"], "dominance_level": "dominant", "visual_grammar": {"name": "table_scene", "topology": "full_bleed"}}, {"scene_id": "s2", "narrative_state": "try", "narrative_function": "SHOW_PROCESS", "visual_authority": "MATERIAL", "copy_intent": "PROVE", "expected_media": True, "focal_entity": "hands_in_action", "evidence_ids": ["e1"], "dominance_level": "standard", "visual_grammar": {"name": "process_sequence", "topology": "sequence"}}, {"scene_id": "s3", "narrative_state": "join", "narrative_function": "ENABLE_ACTION", "visual_authority": "TYPOGRAPHY", "copy_intent": "CONVERT", "expected_media": False, "focal_entity": "typography", "evidence_ids": [], "dominance_level": "display", "visual_grammar": {"name": "asymmetric_editorial", "topology": "layered"}}]}
        self.copy = {"hero": {"microcopy": "福岡市｜食材と手を動かす時間から次の案内へ。"}, "sections": [{"section_id": "opening", "headline": "料理教室", "body": "福岡市の料理教室。少人数で料理を学ぶ教室。"}, {"section_id": "truth", "headline": "手を動かす", "body": "食材を確かめます。"}, {"section_id": "close", "headline": "参加を考える", "body": "内容を確認して参加を相談します。"}]}
        self.assets = {"assets": [{"photo_role": "hero_shared_cooking"}, {"photo_role": "ingredient_story"}, {"photo_role": "hands_in_action"}, {"photo_role": "finished_table"}]}

    def test_expression_modes_and_destinations_are_bounded(self):
        self.assertEqual(len(EXPRESSION_MODES), 7)
        self.assertIn("PAGE_SECTION", CTA_DESTINATION_TYPES)
        self.assertNotIn("javascript", CTA_DESTINATION_TYPES)

    def test_signature_has_five_channels(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        self.assertGreaterEqual(len(anchors), 3)
        self.assertTrue(all(len(x["expression_channels"]) >= 3 for x in anchors))
        self.assertNotIn("synthetic", str(anchors[0].get("value")))

    def test_generic_definition_is_hard_fail(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        row = definition_score("サービスを提供する事業者", anchors)
        self.assertGreaterEqual(row["score"], 4)
        self.assertEqual(row["status"], "FAIL")

    def test_specific_definition_passes(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        row = definition_score("福岡市の料理教室で、食材を確かめます", anchors)
        self.assertEqual(row["status"], "PASS")

    def test_definition_gate_collects_only_failures(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        gate = evaluate_definition_gate(["福岡市の料理教室", "幅広く対応するサービス事業者"], anchors)
        self.assertEqual(gate["status"], "FAIL")
        self.assertEqual(len(gate["violations"]), 1)

    def test_copy_translation_is_traceable(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        result = build_premium_copy_translation(self.u, self.strategy, self.plan, self.evidence, self.copy, anchors)
        self.assertEqual(len(result["scenes"]), 3)
        self.assertTrue(all("expression_mode" in x and x["expression_mode"] in EXPRESSION_MODES for x in result["scenes"]))
        self.assertEqual(result["scenes"][0]["truth_atoms"][0]["claim_trace_id"], "e1")

    def test_copy_swap_can_be_detected_by_definition(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        self.assertEqual(definition_score("福岡市の料理教室", anchors)["status"], "PASS")
        self.assertEqual(definition_score("高品質なサービスを提供する事業者", anchors)["status"], "FAIL")

    def test_cta_closure_uses_verified_action(self):
        result = build_cta_closure(self.u, self.strategy, self.plan, self.evidence)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["closures"][-1]["destination_type"], "VERIFIED_NATIVE")
        self.assertFalse(result["closures"][-1]["hard_violation"])

    def test_cta_closure_fails_fake_action(self):
        u = {**self.u, "contact_channels": {}}
        result = build_cta_closure(u, self.strategy, self.plan, [{"evidence_id": "e1", "evidence_type": "SERVICE_SCOPE", "claim": "料理", "verification_status": "VERIFIED"}])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["closures"][-1]["destination_type"], "INFORMATIONAL_ONLY")

    def test_cta_discovery_and_reassurance_have_page_targets(self):
        rows = build_cta_closure(self.u, self.strategy, self.plan, self.evidence)["closures"]
        self.assertEqual([x["href"] for x in rows[:2]], ["#way-in", "#reassurance"])

    def test_photo_binding_is_demand_driven(self):
        result = build_photo_binding(self.plan, self.assets, self.u)
        roles = [x["photo_role"] for x in result["bindings"]]
        self.assertEqual(roles[:2], ["hero_shared_cooking", "hands_in_action"])
        self.assertEqual(result["semantic_mismatch_count"], 0)

    def test_photo_binding_temporal_stages_are_ordered(self):
        stages = [x["temporal_stage"] for x in build_photo_binding(self.plan, self.assets)["bindings"]]
        self.assertEqual(stages, ["arrival", "orientation", "understanding"])

    def test_typography_closure_has_no_photo_requirement(self):
        result = build_photo_binding(self.plan, self.assets)
        self.assertEqual(result["bindings"][-1]["photo_role"], "typography")
        self.assertEqual(result["bindings"][-1]["status"], "PASS")

    def test_token_profile_is_finite_and_derived(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        profile = build_art_direction_token_profile(self.u, self.strategy, anchors)
        self.assertEqual(profile["schema_version"], "art_direction_token_profile_v2")
        self.assertFalse(profile["derivation"]["slug_dependency"])
        self.assertIn(profile["type_voice"], {"open", "quiet", "measured"})

    def test_profiles_have_multiple_macro_axis_differences(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        one = build_art_direction_token_profile(self.u, {"layout_profile": "studio_invitation"}, anchors)
        two = build_art_direction_token_profile(self.u, {"layout_profile": "care_rhythm"}, anchors)
        self.assertGreaterEqual(sum(one.get(k) != two.get(k) for k in ("type_voice", "surface_language", "edge_language", "image_behavior", "spatial_language", "cta_language", "decorative_grammar", "rhythm_character")), 4)

    def test_peak_candidates_rank_multiple_scenes(self):
        result = build_peak_candidates(self.plan, build_premium_copy_translation(self.u, self.strategy, self.plan, self.evidence, self.copy))
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(len(result["selected"]), 2)
        self.assertTrue(all(x["total"] >= 9 for x in result["selected"]))

    def test_peak_candidates_do_not_require_final_scene(self):
        result = build_peak_candidates(self.plan)
        self.assertNotEqual(result["selected"][0]["scene_id"], self.plan["scene_plan"][-1]["scene_id"])

    def test_human_translation_contains_all_ir(self):
        result = build_human_translation(self.u, self.strategy, self.plan, self.evidence, self.assets, self.copy)
        for key in ("signature_anchors", "copy_translation", "cta_closure", "photo_binding", "art_direction_token_profile", "peak_candidates", "cross_modal_consistency"):
            self.assertIn(key, result)
        self.assertEqual(result["cross_modal_consistency"]["status"], "PASS")

    def test_mutation_missing_anchor_channel_fails_consistency(self):
        result = build_human_translation(self.u, self.strategy, self.plan, self.evidence, self.assets, self.copy)
        result["signature_anchors"][0]["expression_channels"] = ["COPY"]
        self.assertNotEqual(len(result["signature_anchors"][0]["expression_channels"]), 3)

    def test_mutation_missing_action_href_is_visible(self):
        u = {**self.u, "contact_channels": {"href": ""}}
        result = build_cta_closure(u, self.strategy, self.plan, [])
        self.assertTrue(result["hard_violations"])

    def test_mutation_wrong_photo_role_is_not_silently_approved(self):
        plan = {**self.plan, "scene_plan": [{**self.plan["scene_plan"][0], "focal_entity": "unknown_role"}] + self.plan["scene_plan"][1:]}
        result = build_photo_binding(plan, self.assets)
        self.assertEqual(result["bindings"][0]["status"], "FAIL")

    def test_mutation_text_only_peak_is_not_concentrated(self):
        plan = {**self.plan, "scene_plan": [{**self.plan["scene_plan"][-1], "expected_media": False, "focal_entity": "typography", "dominance_level": "standard"}]}
        result = build_peak_candidates(plan)
        self.assertFalse(result["selected"])

    def test_mutation_token_profile_cannot_depend_on_slug(self):
        anchors = derive_signature_anchors(self.u, self.strategy, self.evidence)
        profile = build_art_direction_token_profile({**self.u, "company_id": "maylynn_paint"}, self.strategy, anchors)
        self.assertNotIn("maylynn", str(profile))

    def test_ten_synthetic_categories_do_not_emit_company_slug(self):
        for index in range(10):
            u = {**self.u, "company_id": f"case-{index}", "service_category": f"service-{index}"}
            anchors = derive_signature_anchors(u, self.strategy, self.evidence)
            self.assertNotIn("maylynn_paint", str(build_art_direction_token_profile(u, self.strategy, anchors)))


if __name__ == "__main__":
    unittest.main()
