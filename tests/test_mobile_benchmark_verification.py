import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MobileBenchmarkVerificationTest(unittest.TestCase):
    def _load(self, relative_path):
        return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))

    def test_mobile_evidence_links_to_ready_catalog_items(self):
        mobile = self._load("config/mobile_benchmark_verification_v1.json")
        catalog = self._load("config/benchmark_pool_v1.json")
        by_id = {item["id"]: item for item in catalog["benchmarks"]}

        self.assertGreaterEqual(len(mobile["records"]), 1)
        for record in mobile["records"]:
            benchmark_id = record["benchmark_id"]
            self.assertIn(benchmark_id, by_id)
            benchmark = by_id[benchmark_id]
            self.assertTrue(benchmark["desktop_verified"])
            self.assertTrue(benchmark["mobile_verified"])
            self.assertEqual(benchmark["stage"], "CORE")

            review = record["mobile_review"]
            self.assertIn(review["evidence_grade"], {"M2", "M3"})
            self.assertTrue(review["hierarchy_preserved"])
            self.assertTrue(review["purposeful_recomposition"])
            self.assertTrue(review["primary_message_survives"])
            self.assertTrue(review["cta_or_next_action_survives"])
            self.assertGreaterEqual(len(record["sources"]), 2)

    def test_mobile_evidence_is_synchronized_with_strict_frame_registry(self):
        mobile = self._load("config/mobile_benchmark_verification_v1.json")
        registry = self._load("config/frame_registry_v1.json")
        by_frame_id = {item["frame_id"]: item for item in registry["frames"]}

        for record in mobile["records"]:
            frame_id = record["frame_id"]
            grade = record["mobile_review"]["evidence_grade"]
            self.assertIn(frame_id, by_frame_id, f"mobile evidence missing from strict registry: {frame_id}")
            frame = by_frame_id[frame_id]
            self.assertTrue(frame["visual_verified"], frame_id)
            self.assertTrue(frame["mobile_verified"], frame_id)
            self.assertEqual(frame.get("mobile_evidence_grade"), grade, frame_id)
            self.assertEqual(frame["stage"], "CORE", frame_id)

    def test_m3_is_not_claimed_without_live_review(self):
        mobile = self._load("config/mobile_benchmark_verification_v1.json")
        grades = [record["mobile_review"]["evidence_grade"] for record in mobile["records"]]
        self.assertTrue(all(grade in {"M2", "M3"} for grade in grades))
        # Current corpus intentionally remains M2 until live/captured 390px review is performed.
        self.assertNotIn("M3", grades)


if __name__ == "__main__":
    unittest.main()
