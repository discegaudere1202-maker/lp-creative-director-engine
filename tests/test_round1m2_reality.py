import unittest

from scripts.run_round1m2_validation import (
    actual_signature_channels,
    anchor_in_text,
    parse_sections,
    photo_semantic_score,
    rendered_copy_quality,
    resolve_cta_target,
    select_rendered_peaks,
)


class Round1M2RealityTest(unittest.TestCase):
    def html(self):
        return (
            '<section id="source" data-scene-id="scene-source"><h2>入口</h2>'
            '<a data-cta-stage="action" data-actionability="QUIET_CONVERSION_END" data-destination-type="INFORMATIONAL_ONLY" data-state-before="迷い" data-state-after="確認できる" href="#contact">案内を確認する</a></section>'
            '<section id="contact"><h2>公式窓口の案内</h2><p>福岡市の相談先</p></section>'
        )

    def cta(self, html=None):
        sections = parse_sections(html or self.html())
        return sections[0]["ctas"][0]

    def test_01_parse_sections_keeps_source_id(self):
        self.assertEqual(parse_sections(self.html())[0]["id"], "source")

    def test_02_parse_sections_keeps_scene_id(self):
        self.assertEqual(parse_sections(self.html())[0]["scene_id"], "scene-source")

    def test_03_parse_sections_extracts_cta(self):
        self.assertEqual(self.cta()["data-cta-stage"], "action")

    def test_04_parse_sections_extracts_label(self):
        self.assertEqual(self.cta()["label"], "案内を確認する")

    def test_05_resolve_cta_target_exists(self):
        self.assertTrue(resolve_cta_target(parse_sections(self.html()), self.cta())["target_exists"])

    def test_06_resolve_cta_target_is_not_self(self):
        self.assertFalse(resolve_cta_target(parse_sections(self.html()), self.cta())["same_section"])

    def test_07_resolve_cta_target_has_information_gain(self):
        self.assertEqual(resolve_cta_target(parse_sections(self.html()), self.cta())["information_gain"], 1)

    def test_08_resolve_cta_target_passes(self):
        self.assertEqual(resolve_cta_target(parse_sections(self.html()), self.cta())["verdict"], "PASS")

    def test_09_self_anchor_fails(self):
        html = '<section id="same" data-scene-id="s"><a data-cta-stage="action" href="#same">案内</a></section>'
        row = resolve_cta_target(parse_sections(html), parse_sections(html)[0]["ctas"][0])
        self.assertIn("self_anchor", row["hard_reasons"])

    def test_10_missing_target_fails(self):
        html = '<section id="source" data-scene-id="s"><a data-cta-stage="action" href="#missing">案内</a></section>'
        row = resolve_cta_target(parse_sections(html), parse_sections(html)[0]["ctas"][0])
        self.assertEqual(row["verdict"], "FAIL")

    def test_11_same_content_fails(self):
        html = '<section id="a" data-scene-id="a"><p>同じ内容</p><a data-cta-stage="discovery" href="#b">見る</a></section><section id="b"><p>同じ内容</p></section>'
        row = resolve_cta_target(parse_sections(html), parse_sections(html)[0]["ctas"][0])
        self.assertIn("target_content_same", row["hard_reasons"])

    def test_12_external_href_is_verified_only_with_marker(self):
        html = '<section id="a" data-scene-id="a"><a data-cta-stage="action" data-actionability="ACTION" data-verified-external-href="https://example.test" href="https://example.test">相談</a></section>'
        row = resolve_cta_target(parse_sections(html), parse_sections(html)[0]["ctas"][0])
        self.assertEqual(row["verified_external_href"], "https://example.test")

    def test_13_external_href_without_marker_is_not_verified_action(self):
        html = '<section id="a" data-scene-id="a"><a data-cta-stage="action" data-actionability="ACTION" href="https://example.test">相談</a></section>'
        row = resolve_cta_target(parse_sections(html), parse_sections(html)[0]["ctas"][0])
        self.assertTrue(row["fake_action"])

    def test_14_user_state_before_is_rendered(self):
        self.assertEqual(resolve_cta_target(parse_sections(self.html()), self.cta())["user_state_before"], "迷い")

    def test_15_user_state_after_is_rendered(self):
        self.assertEqual(resolve_cta_target(parse_sections(self.html()), self.cta())["user_state_after"], "確認できる")

    def test_16_anchor_exact_match(self):
        self.assertTrue(anchor_in_text("福岡市", "福岡市の相談先"))

    def test_17_anchor_fragment_match(self):
        self.assertTrue(anchor_in_text("外壁塗装・屋根", "外壁塗装の相談"))

    def test_18_anchor_missing(self):
        self.assertFalse(anchor_in_text("京都", "福岡市の相談先"))

    def test_19_maylynn_hero_score_passes(self):
        self.assertEqual(photo_semantic_score("maylynn_paint", "observe", "hero_home_finish")["status"], "PASS")

    def test_20_maylynn_material_score_passes(self):
        self.assertEqual(photo_semantic_score("maylynn_paint", "read_material", "material_detail")["status"], "PASS")

    def test_21_nagi_sensory_score_passes(self):
        self.assertEqual(photo_semantic_score("nagi_no_mirai", "settle", "sensory_detail")["status"], "PASS")

    def test_22_watashi_hands_score_passes(self):
        self.assertEqual(photo_semantic_score("watashi_no_daidokoro", "touch", "hands_in_action")["status"], "PASS")

    def test_23_wrong_share_role_fails(self):
        self.assertEqual(photo_semantic_score("watashi_no_daidokoro", "share", "hands_in_action")["status"], "FAIL")

    def test_24_photo_score_threshold_is_explicit(self):
        self.assertGreaterEqual(photo_semantic_score("nagi_no_mirai", "arrive", "hero_treatment_space")["score"], 0.65)

    def test_25_copy_quality_passes_natural_copy(self):
        self.assertEqual(rendered_copy_quality([{"scene_id": "s", "text": "手を動かし、火を入れる順序を確かめます。"}])["status"], "PASS")

    def test_26_copy_quality_rejects_engine_phrase(self):
        self.assertEqual(rendered_copy_quality([{"scene_id": "s", "text": "内容を確認してから案内へ進む"}])["status"], "FAIL")

    def test_27_copy_quality_rejects_definition_repetition(self):
        self.assertEqual(rendered_copy_quality([{"scene_id": "s", "text": "料理教室。料理教室"}])["status"], "FAIL")

    def test_28_copy_quality_reports_trace_coverage(self):
        self.assertEqual(rendered_copy_quality([{"scene_id": "s", "text": "確認", "evidence_trace": "e1"}])["trace_coverage"], 100)

    def test_29_peak_selection_excludes_quiet_typography_end(self):
        plan = {"scene_plan": [{"scene_id": "s1", "narrative_state": "observe", "copy_intent": "PROVE", "expected_media": True, "focal_entity": "hero", "evidence_ids": ["e"], "visual_grammar": {"topology": "full", "media_scale": "dominant"}}, {"scene_id": "s2", "narrative_state": "join", "copy_intent": "CONVERT", "expected_media": False, "focal_entity": "typography", "visual_authority": "TYPOGRAPHY", "evidence_ids": [], "visual_grammar": {"topology": "type", "media_scale": "none"}}]}
        selected = select_rendered_peaks(plan, {"copy_translation": {"scenes": []}}, parse_sections('<section data-scene-id="s1"><img src="x"></section><section data-scene-id="s2"><h2>終わり</h2></section>'))
        self.assertNotIn("s2", {x["scene_id"] for x in selected["peaks"]})

    def test_30_peak_selection_is_ranked_not_fixed(self):
        self.assertEqual(select_rendered_peaks({"scene_plan": []}, {}, [])["status"], "FAIL")

    def test_31_signature_excludes_customer_state(self):
        anchors = [{"anchor_id": "a-place", "anchor_type": "PLACE", "value": "福岡市"}, {"anchor_id": "a-service", "anchor_type": "SERVICE", "value": "料理教室"}]
        rows = actual_signature_channels(anchors, parse_sections('<section id="s" data-scene-id="s" data-signature-anchor-ids="a-place,a-service"><p>福岡市の料理教室</p><img src="hero.png"></section>'), {"peaks": [{"signature_anchor_ids": ["a-place"]}]}, {"ctas": []}, "watashi_no_daidokoro")
        self.assertTrue(all(not row["generic_customer_state"] for row in rows))

    def test_32_signature_requires_non_copy_channel(self):
        anchors = [{"anchor_id": "a", "anchor_type": "SERVICE", "value": "料理教室"}]
        rows = actual_signature_channels(anchors, parse_sections('<section id="s" data-scene-id="s"><p>料理教室</p></section>'), {"peaks": []}, {"ctas": []}, "x")
        self.assertEqual(rows[0]["status"], "FAIL")

    def test_33_signature_visual_is_dom_derived(self):
        anchors = [{"anchor_id": "a", "anchor_type": "SERVICE", "value": "料理教室"}]
        rows = actual_signature_channels(anchors, parse_sections('<section id="s" data-scene-id="s" data-signature-anchor-ids="a"><p>料理教室</p><img src="x"></section>'), {"peaks": []}, {"ctas": []}, "x")
        self.assertTrue(rows[0]["visual"])


if __name__ == "__main__":
    unittest.main()
