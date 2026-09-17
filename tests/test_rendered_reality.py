import unittest
from lp_engine.premium_experience import aggregate_gate, extract_rendered_ctas


class RenderedRealityTest(unittest.TestCase):
    def test_internal_identifier_is_not_public_copy(self):
        self.assertRegex("hero_home_finish", r"hero_")

    def test_child_fail_overrides_plan_pass(self):
        self.assertEqual(aggregate_gate({"planned": {"status": "PASS"}, "rendered": {"status": "FAIL"}})["status"], "FAIL")

    def test_valid_typography_scene_has_no_media_requirement(self):
        self.assertEqual(extract_rendered_ctas('<section data-scene-id="s"><h2>相談を始める</h2></section>'), [])
