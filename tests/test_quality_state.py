"""Regression checks for missing data and recorded quality, without a browser."""
import unittest

from lp_engine.quality_state import normalize_check, normalize_quality, summarize_quality


class QualityStateTest(unittest.TestCase):
    def test_missing_data_does_not_make_a_decision_or_score(self):
        self.assertEqual(normalize_check(None),{"status":"NOT_RUN"})
        quality=normalize_quality()
        self.assertEqual(quality,{"premium_gate":"NOT_RUN","premium_score":None})
        report=summarize_quality([quality])
        self.assertIsNone(report["average_premium_score"])
        self.assertIsNone(report["premium_pass_rate"])
        self.assertEqual(report["premium_no_decision_count"],1)
        self.assertEqual(report["premium_pass_count"],0)

    def test_only_finite_numeric_scores_contribute_and_zero_is_a_real_score(self):
        values=[{"premium_score":value} for value in (None,True,False,"4.0",float("nan"),float("inf"),-float("inf"),0,4.0)]
        report=summarize_quality(values)
        self.assertEqual(report["premium_score_count"],2)
        self.assertEqual(report["premium_unscored_count"],7)
        self.assertEqual(report["average_premium_score"],2.0)
        self.assertIsNone(report["premium_pass_rate"])
        self.assertEqual(report["premium_pass_count"],0)

    def test_recorded_gate_does_not_require_or_follow_a_score(self):
        values=[{"premium_gate":"PASS"},{"premium_gate":"FAIL","premium_score":4.9},{"premium_gate":"HOLD"},{"premium_score":5.0}]
        report=summarize_quality(values)
        self.assertEqual(report["premium_decision_count"],3)
        self.assertEqual(report["premium_no_decision_count"],1)
        self.assertEqual(report["premium_pass_count"],1)
        self.assertAlmostEqual(report["premium_pass_rate"],1/3)
        self.assertEqual(report["premium_score_count"],2)


if __name__=="__main__": unittest.main()
