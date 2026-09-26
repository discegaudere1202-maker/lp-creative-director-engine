import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_issue111_stage_a_sales_sample_qa_final as final


class Issue111FinalPolicyTest(unittest.TestCase):
    def test_two_thirds_portrait_cover_boundary_passes_with_narrow_tolerance(self):
        raw = 0.41665346639210094
        self.assertLess(raw, final.CROP_GATE_THRESHOLD)
        self.assertTrue(final.crop_gate_passes(raw))
        self.assertLessEqual(final.CROP_NUMERIC_TOLERANCE, 0.005)

    def test_meaningfully_destructive_crop_still_fails(self):
        self.assertFalse(final.crop_gate_passes(0.40))
        self.assertFalse(final.crop_gate_passes(0.414))
        self.assertTrue(final.crop_gate_passes(0.415))

    def test_source_dimension_precheck_rejects_extreme_portrait_and_keeps_two_thirds(self):
        extreme = final.candidate_crop_fit({"source_dimensions": [1600, 2842]})
        two_thirds = final.candidate_crop_fit({"source_dimensions": [1600, 2400]})
        landscape = final.candidate_crop_fit({"source_dimensions": [1600, 1067]})
        self.assertFalse(extreme["pass"])
        self.assertEqual(extreme["reason"], "ISSUE111_CROP_FIT_PRECHECK_FAILED")
        self.assertTrue(two_thirds["pass"])
        self.assertTrue(landscape["pass"])
        self.assertLess(extreme["minimum_raw_fraction"], two_thirds["minimum_raw_fraction"])

    def test_missing_source_dimensions_fail_closed(self):
        result = final.candidate_crop_fit({})
        self.assertFalse(result["pass"])
        self.assertEqual(result["reason"], "SOURCE_DIMENSIONS_MISSING")


if __name__ == "__main__":
    unittest.main()
