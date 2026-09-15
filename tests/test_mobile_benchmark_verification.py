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

    def test_m3_requires_traceable_live_capture_and_visual_pass(self):
        mobile = json.loads(
            (ROOT / "config/mobile_benchmark_verification_v1.json").read_text(encoding="utf-8")
        )
        m3_records = [
            record for record in mobile["records"]
            if record["mobile_review"]["evidence_grade"] == "M3"
        ]
        self.assertGreaterEqual(len(m3_records), 1)
        for record in m3_records:
            capture = record.get("live_capture")
            self.assertIsInstance(capture, dict)
            self.assertIsInstance(capture.get("run_id"), int)
            self.assertIsInstance(capture.get("artifact_id"), int)
            self.assertEqual(capture.get("viewport"), "390x844")
            self.assertEqual(capture.get("http_status"), 200)
            self.assertEqual(capture.get("review_status"), "PASS")
            self.assertEqual(len(capture.get("screenshot_sha256", "")), 64)
            self.assertEqual(len(capture.get("desktop_screenshot_sha256", "")), 64)

    def test_failed_or_uncertain_live_capture_does_not_auto_promote_m3(self):
        mobile = json.loads(
            (ROOT / "config/mobile_benchmark_verification_v1.json").read_text(encoding="utf-8")
        )
        for record in mobile["records"]:
            capture = record.get("live_capture")
            if capture and capture.get("review_status") != "PASS":
                self.assertNotEqual(record["mobile_review"]["evidence_grade"], "M3")


if __name__ == "__main__":
    unittest.main()
