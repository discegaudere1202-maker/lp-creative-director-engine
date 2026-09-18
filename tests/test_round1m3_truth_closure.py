import unittest

from scripts.run_round1m2_validation import parse_sections
from scripts.run_round1m3_validation import (
    audit_ctas,
    audit_editorial,
    audit_peaks,
    audit_photos,
    build_consistency,
)
from lp_engine.human_translation import build_cta_closure, build_peak_candidates, derive_signature_anchors


class Round1M3TruthClosureTest(unittest.TestCase):
    def _info_cta(self):
        return parse_sections('<section id="source" data-scene-id="source"><a data-cta-stage="action" data-actionability="QUIET_CONVERSION_END" data-destination-type="INFORMATIONAL_ONLY" href="#contact">見積を相談する</a></section><section id="contact"><h2>公式窓口の案内</h2></section>')

    def test_01_root_summary_contradiction_fails(self):
        result = build_consistency({"status": "HOLD", "human_review_ready": False, "round1m3_machine_ready": False, "capture_provenance": "FAIL"}, {"child": {"status": "PASS"}}, {"status": "FAIL"}, {"status": "PASS"})
        self.assertEqual(result["status"], "FAIL")

    def test_02_capture_fail_ready_yes_fails(self):
        result = build_consistency({"status": "PASS", "human_review_ready": True, "round1m3_machine_ready": True, "capture_provenance": "FAIL"}, {"child": {"status": "PASS"}}, {"status": "PASS"}, {"status": "PASS"})
        self.assertEqual(result["status"], "FAIL")

    def test_03_duplicate_particle_fails(self):
        result = audit_editorial("x", parse_sections('<section data-scene-id="s"><p>外壁塗装をについて相談できます。</p></section>'), [])
        self.assertEqual(result["status"], "FAIL")

    def test_04_double_particle_fails(self):
        result = audit_editorial("x", parse_sections('<section data-scene-id="s"><p>内容をを確認します。</p></section>'), [])
        self.assertEqual(result["status"], "FAIL")

    def test_05_natural_japanese_passes(self):
        result = audit_editorial("x", parse_sections('<section data-scene-id="s"><p>手を動かし、火を入れる順序を確かめます。</p></section>'), [])
        self.assertEqual(result["status"], "PASS")

    def test_06_procedural_phrase_fails(self):
        result = audit_editorial("x", parse_sections('<section data-scene-id="s"><p>内容を確認してから案内へ進む</p></section>'), [])
        self.assertEqual(result["status"], "FAIL")

    def test_07_action_label_in_info_destination_fails(self):
        result = audit_ctas("x", self._info_cta())
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["fake_action_count"], 1)

    def test_08_informational_label_passes(self):
        sections = parse_sections('<section id="source" data-scene-id="source"><a data-cta-stage="action" data-actionability="QUIET_CONVERSION_END" data-destination-type="INFORMATIONAL_ONLY" href="#contact">連絡先を確認する</a></section><section id="contact"><h2>公式窓口の案内</h2></section>')
        self.assertEqual(audit_ctas("x", sections)["status"], "PASS")

    def test_09_verified_booking_action_passes(self):
        sections = parse_sections('<section id="source" data-scene-id="source"><a data-cta-stage="action" data-actionability="ACTION" data-destination-type="VERIFIED_EXTERNAL" data-verified-external-href="https://example.test/book" href="https://example.test/book">予約する</a></section>')
        result = audit_ctas("x", sections)
        self.assertEqual(result["status"], "FAIL")  # discovery/reassurance are required for a complete CTA contract

    def test_10_verified_action_contract_is_supported_by_ir(self):
        result = build_cta_closure({"contact_channels": {"href": "https://example.test/book", "primary": "booking"}, "customer_state": {}}, {"creative_genome": {"cta_progression": []}}, {"scene_plan": []}, [{"evidence_type": "CTA_CHANNEL", "verification_status": "VERIFIED"}])
        self.assertEqual(result["closures"][-1]["actionability"], "ACTION")

    def test_11_make_ingredient_still_life_fails(self):
        plan = {"scene_plan": [{"scene_id": "scene-01-make", "narrative_state": "make", "expected_media": True, "focal_entity": "ingredient_story"}]}
        sections = parse_sections('<section data-scene-id="scene-01-make"><figure data-photo-role="ingredient_story"><img src="ingredient.jpg"></figure></section>')
        self.assertEqual(audit_photos("watashi_no_daidokoro", sections, plan)["status"], "FAIL")

    def test_12_make_active_cooking_passes(self):
        plan = {"scene_plan": [{"scene_id": "scene-01-make", "narrative_state": "make", "expected_media": True, "focal_entity": "hands_in_action"}]}
        sections = parse_sections('<section data-scene-id="scene-01-make"><figure data-photo-role="hands_in_action"><img src="hands.jpg"></figure></section>')
        self.assertEqual(audit_photos("watashi_no_daidokoro", sections, plan)["status"], "PASS")

    def test_13_share_finished_table_passes(self):
        plan = {"scene_plan": [{"scene_id": "scene-01-share", "narrative_state": "share", "expected_media": True, "focal_entity": "finished_table"}]}
        sections = parse_sections('<section data-scene-id="scene-01-share"><figure data-photo-role="finished_table"><img src="table.jpg"></figure></section>')
        self.assertEqual(audit_photos("watashi_no_daidokoro", sections, plan)["status"], "PASS")

    def test_14_peak_empty_signature_is_ineligible(self):
        plan = {"scene_plan": [{"scene_id": "s1", "narrative_state": "observe", "copy_intent": "PROVE", "expected_media": True, "focal_entity": "hero", "evidence_ids": ["e1"], "narrative_function": "SHOW_DETAIL", "dominance_level": "dominant", "visual_grammar": {"topology": "full"}}]}
        result = build_peak_candidates(plan, {"scenes": [{"scene_id": "s1", "signature_anchor_ids": []}]})
        self.assertFalse(result["selected"])

    def test_15_place_anchor_is_not_company_signature(self):
        anchors = derive_signature_anchors({"location": "福岡市", "service_category": "料理教室", "company_truth": "少人数で料理を学ぶ教室。"}, {}, [])
        self.assertEqual(next(x for x in anchors if x["anchor_type"] == "PLACE")["classification"], "PLACE_FACT")

    def test_16_customer_state_is_not_an_anchor(self):
        anchors = derive_signature_anchors({"location": "福岡市", "service_category": "料理教室", "company_truth": "少人数で料理を学ぶ教室。", "customer_state": {"barrier": "不安"}}, {}, [])
        self.assertNotIn("不安", [x["value"] for x in anchors])

    def test_17_company_truth_is_signature(self):
        anchors = derive_signature_anchors({"location": "福岡市", "service_category": "料理教室", "company_truth": "少人数で料理を学ぶ教室。"}, {}, [])
        self.assertEqual(next(x for x in anchors if x["anchor_type"] == "TRUTH")["classification"], "COMPANY_SIGNATURE")

    def test_18_signature_channel_requirement_keeps_noncopy_rule(self):
        sections = parse_sections('<section data-scene-id="s" data-signature-anchor-ids="a"><p>固有の教室</p></section>')
        self.assertEqual(sections[0]["attrs"]["data-signature-anchor-ids"], "a")

    def test_19_claim_required_missing_trace_fails(self):
        evidence = [{"evidence_id": "e1", "claim": "福岡市で活動する事業者。"}]
        result = audit_editorial("x", parse_sections('<section data-scene-id="s"><p>福岡市で活動する事業者です。</p></section>'), evidence)
        self.assertEqual(result["status"], "FAIL")

    def test_20_nonclaim_missing_trace_passes(self):
        result = audit_editorial("x", parse_sections('<section data-scene-id="s"><p>手を動かす時間を思い描きます。</p></section>'), [])
        self.assertEqual(result["status"], "PASS")

    def test_21_claim_trace_with_trace_id_passes(self):
        evidence = [{"evidence_id": "e1", "claim": "福岡市で活動する事業者。"}]
        html = '<section data-scene-id="s" data-evidence-trace="e1"><p>福岡市で活動する事業者です。</p></section>'
        self.assertEqual(audit_editorial("x", parse_sections(html), evidence)["status"], "PASS")

    def test_22_cross_consistency_passes_when_all_children_pass(self):
        result = build_consistency({"status": "PASS", "human_review_ready": True, "round1m3_machine_ready": True, "capture_provenance": "PASS"}, {"child": {"status": "PASS"}}, {"status": "PASS"}, {"status": "PASS"})
        self.assertEqual(result["status"], "PASS")

    def test_23_cross_consistency_catches_child_fail(self):
        result = build_consistency({"status": "PASS", "human_review_ready": True, "round1m3_machine_ready": True, "capture_provenance": "PASS"}, {"child": {"status": "FAIL"}}, {"status": "PASS"}, {"status": "PASS"})
        self.assertEqual(result["status"], "FAIL")

    def test_24_photo_missing_asset_fails(self):
        plan = {"scene_plan": [{"scene_id": "s", "narrative_state": "make", "expected_media": True, "focal_entity": "hands_in_action"}]}
        self.assertEqual(audit_photos("watashi_no_daidokoro", parse_sections('<section data-scene-id="s"></section>'), plan)["status"], "FAIL")

    def test_25_cta_self_anchor_fails(self):
        sections = parse_sections('<section id="same" data-scene-id="same"><a data-cta-stage="action" href="#same">連絡先を確認する</a></section>')
        result = audit_ctas("x", sections)
        self.assertEqual(result["status"], "FAIL")

    def test_26_peak_requires_two_to_four_selected(self):
        result = audit_peaks("x", [], {"scene_plan": []}, {"copy_translation": {"scenes": []}})
        self.assertEqual(result["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
