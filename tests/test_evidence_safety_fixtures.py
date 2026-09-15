import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EvidenceSafetyFixtureTest(unittest.TestCase):
    def test_dry_run_has_five_traceable_cases(self):
        payload = json.loads((ROOT / "data/evidence_safety_dry_run_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"]["case_count"], 5)
        self.assertTrue(payload["summary"]["all_have_decisions"])
        self.assertGreaterEqual(payload["summary"]["customer_facing_approved_blocked_claims"], 1)
        self.assertEqual(
            {item["case_id"] for item in payload["cases"]},
            {"P02", "P09", "P10", "MORIBITO", "INDEPENDENT_KOKORO_SEITAI"},
        )

    def test_adversarial_result_has_zero_dangerous_approval(self):
        payload = json.loads((ROOT / "data/evidence_safety_adversarial_results_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"]["dangerous_customer_facing_approved"], 0)
        self.assertEqual(payload["summary"]["status"], "PASS")
        self.assertTrue(all(item["pass"] for item in payload["cases"]))

    def test_contract_keeps_copy_generation_out_of_scope(self):
        payload = json.loads((ROOT / "config/evidence_selection_engine_contract_v1.json").read_text(encoding="utf-8"))
        self.assertIn("generate_unsupported_reassurance", payload["responsibility_boundary"]["engine_must_not"])
        self.assertIn("future batch/render caller integration", payload["not_yet_implemented"])


if __name__ == "__main__":
    unittest.main()
