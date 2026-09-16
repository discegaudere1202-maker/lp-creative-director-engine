import json
from pathlib import Path
import tempfile
import unittest

from lp_engine.production_generation import run_generation
from lp_engine.quality_diagnosis import build_structured_review


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "examples/production/phase2_fixtures"
HOLDOUT = ROOT / "examples/production/phase2b_holdout/worsal_fukuoka_production_input_v1.json"


class Phase2BQualityUpliftTest(unittest.TestCase):
    def _load(self, path):
        return json.loads(path.read_text(encoding="utf-8"))

    def test_gen3_strategy_exposes_generic_premium_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "gen3"
            result = run_generation(self._load(HOLDOUT), output, generation_id="test-phase2b-gen3", iteration=3)
            self.assertTrue(result.production_output_allowed)
            strategy = json.loads((output / "creative_strategy.json").read_text(encoding="utf-8"))
            self.assertEqual(strategy["quality_calibration"], "premium_causality_and_conversion")
            self.assertTrue(strategy["premium_quality_strategy"]["enabled"])
            self.assertGreaterEqual(len(strategy["form_causality"]), 5)
            self.assertTrue((output / "form_causality_manifest.json").exists())

    def test_rich_fixture_can_clear_premium_gate_after_browser_qa(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "chikushi"
            run_generation(self._load(FIXTURES / "chikushi_industries_production_input_v1.json"), output, generation_id="test-phase2b-rich", iteration=3)
            review = build_structured_review(output, {"status": "PASS", "mode": "static_and_browser"})
            self.assertEqual(review["sales_sample_gate"], "PASS")
            self.assertTrue(all(review["premium_gate_checks"].values()))

    def test_holdout_is_generic_and_has_no_fixture_branch(self):
        text = (ROOT / "src/lp_engine/production_generation.py").read_text(encoding="utf-8")
        self.assertNotIn("worsal-fukuoka-school", text)
        self.assertNotIn("chikushi-industries", text)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "holdout"
            result = run_generation(self._load(HOLDOUT), output, generation_id="test-phase2b-holdout", iteration=3)
            self.assertEqual(result.safety_report["safety_status"], "PASS")
            manifest = json.loads((output / "generation_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["manual_intervention"], [])
            self.assertEqual(manifest["output_status"], "PRODUCTION_APPROVED")


if __name__ == "__main__":
    unittest.main()
