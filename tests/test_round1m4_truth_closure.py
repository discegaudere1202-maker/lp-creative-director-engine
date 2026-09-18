import tempfile
import unittest
from pathlib import Path

from scripts.run_round1m2_validation import parse_sections
from scripts.run_round1m4_validation import audit_adjacent_asset_reuse, audit_contact_information_gain
from lp_engine.production_generation import normalize_japanese_particles


class Round1M4TruthClosureTest(unittest.TestCase):
    def _plan(self, touch_role="ingredient_story", make_role="hands_in_action"):
        return {"scene_plan": [
            {"scene_id": "scene-02-touch", "narrative_state": "touch", "focal_entity": touch_role, "expected_media": True},
            {"scene_id": "scene-03-make", "narrative_state": "make", "focal_entity": make_role, "expected_media": True},
        ]}

    def test_01_duplicate_particle_fails_at_normalization_contract(self):
        self.assertEqual(normalize_japanese_particles("外壁塗装についてについて相談できます"), "外壁塗装について相談できます")

    def test_02_natural_particle_sentence_passes(self):
        self.assertEqual(normalize_japanese_particles("外壁塗装について相談できます"), "外壁塗装について相談できます")

    def test_03_particle_ending_template_is_normalized(self):
        self.assertEqual(normalize_japanese_particles("素材に関してに関して案内します"), "素材に関して案内します")

    def test_04_contact_label_only_has_zero_information_gain(self):
        sections = parse_sections('<section data-scene-id="source"><a data-cta-stage="action" data-actionability="QUIET_CONVERSION_END" data-destination-type="INFORMATIONAL_ONLY" href="#contact">連絡先を確認する</a></section><section id="contact" data-contact-datum-count="0"><h2>公式窓口</h2></section>')
        result = audit_contact_information_gain("x", sections)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["fake_information_gain_count"], 1)

    def test_05_actual_phone_is_information_gain(self):
        sections = parse_sections('<section data-scene-id="source"><a data-cta-stage="action" data-actionability="QUIET_CONVERSION_END" data-destination-type="INFORMATIONAL_ONLY" href="#contact">連絡先を確認する</a></section><section id="contact" data-contact-datum-count="1"><p data-contact-datum="verified">092-123-4567</p></section>')
        self.assertEqual(audit_contact_information_gain("x", sections)["status"], "PASS")

    def test_06_actual_verified_url_is_information_gain(self):
        sections = parse_sections('<section data-scene-id="source"><a data-cta-stage="action" data-actionability="ACTION" data-destination-type="VERIFIED_EXTERNAL" data-verified-external-href="https://example.test/contact" href="https://example.test/contact">連絡する</a></section><section id="contact" data-contact-datum-count="1"><p data-contact-datum="verified">https://example.test/contact</p></section>')
        result = audit_contact_information_gain("x", sections)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["fake_information_gain_count"], 0)

    def test_07_no_contact_datum_is_quiet_end(self):
        sections = parse_sections('<section data-scene-id="source"><p>静かに閉じます</p></section><section id="contact" data-contact-datum-count="0"><h2>次の案内</h2></section>')
        result = audit_contact_information_gain("x", sections)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["no_verified_contact_final_button_count"], 1)

    def test_08_no_datum_contact_button_fails(self):
        sections = parse_sections('<section data-scene-id="source"><a data-cta-stage="action" href="#contact">連絡先を確認する</a></section><section id="contact" data-contact-datum-count="0"><h2>次の案内</h2></section>')
        self.assertEqual(audit_contact_information_gain("x", sections)["status"], "FAIL")

    def test_09_touch_make_same_asset_fails(self):
        sections = parse_sections('<section data-scene-id="scene-02-touch"><figure data-photo-role="hands_in_action"><img src="same.jpg" style="object-position:50% 50%"></figure></section><section data-scene-id="scene-03-make"><figure data-photo-role="hands_in_action"><img src="same.jpg" style="object-position:50% 50%"></figure></section>')
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(audit_adjacent_asset_reuse("watashi_no_daidokoro", sections, self._plan("hands_in_action", "hands_in_action"), Path(directory))["status"], "FAIL")

    def test_10_touch_preparation_make_action_are_distinct(self):
        sections = parse_sections('<section data-scene-id="scene-02-touch"><figure data-photo-role="ingredient_story"><img src="ingredient.jpg" style="object-position:50% 50%"></figure></section><section data-scene-id="scene-03-make"><figure data-photo-role="hands_in_action"><img src="hands.jpg" style="object-position:50% 50%"></figure></section>')
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(audit_adjacent_asset_reuse("watashi_no_daidokoro", sections, self._plan(), Path(directory))["status"], "PASS")

    def test_11_adjacent_same_asset_without_delta_fails(self):
        sections = parse_sections('<section data-scene-id="scene-02-touch"><figure data-photo-role="ingredient_story"><img src="same.jpg" style="object-position:50% 50%"></figure></section><section data-scene-id="scene-03-make"><figure data-photo-role="ingredient_story"><img src="same.jpg" style="object-position:50% 50%"></figure></section>')
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(audit_adjacent_asset_reuse("watashi_no_daidokoro", sections, self._plan(), Path(directory))["status"], "FAIL")

    def test_12_previous_regression_suite_remains_in_scope(self):
        self.assertTrue(Path("tests/test_round1m3_truth_closure.py").exists())


if __name__ == "__main__":
    unittest.main()
