import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MobileBenchmarkVerificationTest(unittest.TestCase):
    def test_mobile_evidence_links_to_ready_catalog_items(self):
        mobile = json.loads(
            (ROOT / "config/mobile_benchmark_verification_v1.json").read_text(encoding="utf-8")
        )
        catalog = json.loads(
            (ROOT / "config/benchmark_pool_v1.json").read_text(encoding="utf-8")
        )
        by_id = {item["id"]: item for item in catalog["benchmarks"]}

        self.assertGreaterEqual(len(mobile["records"]), 1)
        for record in mobile["records"]:
            benchmark_id = record["benchmark_id"]
            self.assertIn(benchmark_id, by_id)
            benchmark = by_id[benchmark_id]
            self.assertTrue(benchmark["desktop_verified"])
            self.assertTrue(benchmark["mobile_verified"])
            self.assertIn(benchmark["stage"], {"VERIFIED", "CORE"})

            review = record["mobile_review"]
            self.assertIn(review["evidence_grade"], {"M2", "M3"})
            self.assertEqual(
                benchmark.get("mobile_evidence_grade"),
                review["evidence_grade"],
                f"mobile evidence grade drift for {benchmark_id}",
            )
            self.assertTrue(review["hierarchy_preserved"])
            self.assertTrue(review["purposeful_recomposition"])
            self.assertTrue(review["primary_message_survives"])
            self.assertTrue(review["cta_or_next_action_survives"])
            self.assertGreaterEqual(len(record["sources"]), 2)

    def test_catalog_mobile_flags_match_evidence_grade(self):
        catalog = json.loads(
            (ROOT / "config/benchmark_pool_v1.json").read_text(encoding="utf-8")
        )
        for benchmark in catalog["benchmarks"]:
            grade = benchmark.get("mobile_evidence_grade", "M0")
            self.assertIn(grade, {"M0", "M1", "M2", "M3"})
            if benchmark.get("mobile_verified", False):
                self.assertIn(grade, {"M2", "M3"})
            if grade in {"M2", "M3"}:
                self.assertTrue(benchmark.get("mobile_verified", False))
            if benchmark.get("stage") == "CORE":
                self.assertEqual(grade, "M3")

    def test_m3_is_not_claimed_without_live_review(self):
        mobile = json.loads(
            (ROOT / "config/mobile_benchmark_verification_v1.json").read_text(encoding="utf-8")
        )
        grades = [record["mobile_review"]["evidence_grade"] for record in mobile["records"]]
        self.assertTrue(all(grade in {"M2", "M3"} for grade in grades))
        # Current corpus intentionally remains M2 until live/captured 390px review is performed.
        self.assertNotIn("M3", grades)


if __name__ == "__main__":
    unittest.main()
