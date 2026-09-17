import unittest

from lp_engine.premium_experience import aggregate_gate_status, authority_contract, cta_destination_contract, rendered_media_contract, rhythm_contract


class Round1KB4Test(unittest.TestCase):
    def test_recursive_grandchild_fail_overrides_root(self):
        report = {"status": "PASS", "child": {"status": "PASS", "items": [{"verdict": "FAIL"}]}}
        self.assertEqual(aggregate_gate_status(report)["status"], "FAIL")

    def test_all_nested_passes(self):
        self.assertEqual(aggregate_gate_status({"status": "PASS", "children": [{"status": "PASS"}]} )["status"], "PASS")

    def test_warning_is_not_hard_fail(self):
        self.assertEqual(aggregate_gate_status({"status": "PASS", "warning": "review"})["status"], "PASS")

    def test_media_contract_empty_expected_media_is_fail(self):
        self.assertEqual(rendered_media_contract(True, False, 0)["verdict"], "FAIL")

    def test_typography_led_scene_is_media_false(self):
        self.assertEqual(rendered_media_contract(False, False, 0)["verdict"], "PASS")

    def test_authority_mismatch_is_fail(self):
        self.assertEqual(authority_contract("DATA", "TYPOGRAPHY")["verdict"], "FAIL")

    def test_same_rendered_rhythm_is_fail(self):
        rows = [{"density_band": "pause", "media_band": "0", "topology": "split"}]
        self.assertEqual(rhythm_contract(rows, rows)["verdict"], "FAIL")

    def test_same_cta_target_content_is_fail(self):
        rows = [{"stage": "discovery", "target_exists": True, "target_content_hash": "a"}, {"stage": "reassurance", "target_exists": True, "target_content_hash": "x"}, {"stage": "action", "target_exists": True, "target_content_hash": "x"}]
        self.assertEqual(cta_destination_contract(rows)["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
