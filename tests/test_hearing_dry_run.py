import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HearingDryRunTest(unittest.TestCase):
    def test_five_named_cases_have_minimum_question_packages(self):
        payload = json.loads((ROOT / "data/hearing_dry_run_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(set(payload["cases"]), {"P02", "P09", "P10", "MORIBITO", "INDEPENDENT_KOKORO_SEITAI"})
        for case in payload["cases"].values():
            self.assertEqual(case["plan"]["question_count"], 2)
            self.assertTrue(case["plan"]["blocking_questions"])
            self.assertEqual(case["resulting_evidence_candidates"], [])


if __name__ == "__main__":
    unittest.main()
