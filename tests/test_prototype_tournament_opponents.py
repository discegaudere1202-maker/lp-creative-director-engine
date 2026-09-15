import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class PrototypeTournamentOpponentsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(
            (ROOT / "config/prototype_tournament_opponents_v1.json").read_text(encoding="utf-8")
        )
        cls.capture = json.loads(
            (ROOT / "config/prototype_capture_targets_v1.json").read_text(encoding="utf-8")
        )
        cls.capture_roles = {
            item["prototype_id"]: item["frame_role"] for item in cls.capture["targets"]
        }

    def test_research_prototypes_have_explicit_task_specific_sets(self):
        self.assertEqual(set(self.payload["prototypes"]), {"P02", "P09", "P10"})

    def test_frame_roles_match_candidate_capture_roles(self):
        for prototype_id, item in self.payload["prototypes"].items():
            with self.subTest(prototype_id=prototype_id):
                self.assertEqual(item["frame_role"], self.capture_roles[prototype_id])

    def test_all_research_sets_are_formal_ready(self):
        self.assertTrue(
            all(item["status"] == "READY" for item in self.payload["prototypes"].values()),
            "P02/P09/P10 must all have explicit human-approved formal opponent sets before blind package generation",
        )

    def test_ready_sets_have_three_to_five_unique_human_approved_m3_opponents(self):
        for prototype_id, item in self.payload["prototypes"].items():
            benchmarks = item["benchmarks"]
            ids = [b["benchmark_id"] for b in benchmarks]
            with self.subTest(prototype_id=prototype_id):
                self.assertEqual(item["status"], "READY")
                self.assertGreaterEqual(len(ids), 3)
                self.assertLessEqual(len(ids), 5)
                self.assertEqual(len(ids), len(set(ids)))
                for benchmark in benchmarks:
                    self.assertEqual(benchmark["evidence_grade"], "M3")
                    self.assertEqual(benchmark["review_status"], "PASS")
                    self.assertIsInstance(benchmark["run_id"], int)
                    self.assertIsInstance(benchmark["artifact_id"], int)
                    self.assertRegex(benchmark["mobile_sha256"], SHA256)
                    self.assertRegex(benchmark["desktop_sha256"], SHA256)
                    self.assertTrue(benchmark["review_note"].strip())

    def test_known_invalid_mobile_capture_is_not_an_approved_opponent(self):
        approved = {
            benchmark["benchmark_id"]
            for item in self.payload["prototypes"].values()
            for benchmark in item["benchmarks"]
        }
        self.assertNotIn("u-do-u", approved)
        self.assertNotIn("mhand-price", approved)
        self.assertNotIn("alotof-price", approved)
        self.assertNotIn("cndoor-price", approved)


if __name__ == "__main__":
    unittest.main()
