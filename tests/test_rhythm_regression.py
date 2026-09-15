import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.rhythm_regression import compare_section_rhythm, section_identity_report


def metric(ids, trans=0.1, quiet=0.5, edge=0.05, lum=0.1):
    return {
        "regions": [
            {"id": sid, "quiet_score": quiet, "edge_mean": edge, "luminance_std": lum, "height_ratio": 0.2}
            for sid in ids
        ],
        "summary": {"transition_energy_avg": trans},
    }


class RegressionTest(unittest.TestCase):
    def test_stable(self):
        a = metric(["hero", "evidence", "services", "cta"])
        b = metric(["hero", "evidence", "services", "cta"], trans=0.11, quiet=0.53)
        self.assertEqual(compare_section_rhythm(a, b)["status"], "STABLE")

    def test_large_shift_reviews(self):
        a = metric(["hero", "services", "cta"], trans=0.1)
        b = metric(["hero", "services", "cta"], trans=0.18, quiet=0.8)
        self.assertEqual(compare_section_rhythm(a, b)["status"], "REVIEW")

    def test_generic_ids_review(self):
        self.assertEqual(
            section_identity_report(metric(["section-1", "section-2", "cta"]))["status"],
            "REVIEW",
        )

    def test_missing_section_reviews(self):
        a = metric(["hero", "evidence", "cta"])
        b = metric(["hero", "cta"])
        result = compare_section_rhythm(a, b)
        self.assertEqual(result["status"], "REVIEW")
        self.assertIn("evidence", result["missing_sections"])


if __name__ == "__main__":
    unittest.main()
