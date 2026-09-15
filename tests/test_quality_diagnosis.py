import json
from pathlib import Path
import tempfile
import unittest

from lp_engine.production_generation import run_generation
from lp_engine.quality_diagnosis import build_structured_review, diagnose_quality


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "examples/production/phase2_fixtures"


class QualityDiagnosisTest(unittest.TestCase):
    def _fixture(self, name):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def _run(self, name, iteration):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            raw = self._fixture(name)
            result = run_generation(raw, output, generation_id=f"test-{iteration}", iteration=iteration)
            review = build_structured_review(output, {"status": "PASS", "mode": "static_only"})
            diagnosis = diagnose_quality(output, qa_report={"status": "PASS", "mode": "static_only"}, review=review)
            return result, review, diagnosis, json.loads((output / "creative_strategy.json").read_text(encoding="utf-8"))

    def test_gen1_diagnosis_becomes_clean_after_generic_calibration(self):
        _, review1, diagnosis1, _ = self._run("chikushi_industries_production_input_v1.json", 1)
        _, review2, diagnosis2, strategy2 = self._run("chikushi_industries_production_input_v1.json", 2)
        self.assertEqual(diagnosis1["status"], "IMPROVEMENT_REQUIRED")
        self.assertIn("COPY", diagnosis1["root_cause_summary"])
        self.assertEqual(diagnosis2["status"], "PASS")
        self.assertGreater(review2["average_scores"]["business_owner_conversion"], review1["average_scores"]["business_owner_conversion"])
        self.assertEqual(strategy2["quality_calibration"], "customer_state_bridge_and_profile_composition")

    def test_cross_fixture_profiles_are_not_one_layout(self):
        profiles = set()
        with tempfile.TemporaryDirectory() as directory:
            for name in sorted(path.name for path in FIXTURES.glob("*_production_input_v1.json")):
                raw = self._fixture(name)
                output = Path(directory) / raw["company_id"]
                run_generation(raw, output, generation_id=f"diversity-{raw['company_id']}", iteration=2)
                strategy = json.loads((output / "creative_strategy.json").read_text(encoding="utf-8"))
                compositions = json.loads((output / "compositions.json").read_text(encoding="utf-8"))
                profiles.add(strategy["layout_profile"])
                self.assertGreaterEqual(len({item["layout_type"] for item in compositions}), 3)
            self.assertEqual(profiles, {"technical_drawing", "experience_calendar", "catalogue_spread"})

    def test_role_reviews_are_not_copied(self):
        _, review, _, _ = self._run("lovst_photo_studio_production_input_v1.json", 2)
        creative = review["reviewer_roles"]["creative_art_direction"]["scores"]
        business = review["reviewer_roles"]["business_owner_conversion"]["scores"]
        self.assertNotEqual(creative, business)
        self.assertIn("not an independent human review", review["method"])
