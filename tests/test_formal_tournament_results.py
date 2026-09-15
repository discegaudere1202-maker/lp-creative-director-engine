import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AXES = {
    "immediate_read", "distinctness", "owner_specificity", "visual_hierarchy",
    "craft_detail", "emotional_pull", "trust", "share_impulse", "mobile_quality",
    "conversion_intent",
}


class FormalTournamentResultsTest(unittest.TestCase):
    def test_all_formal_results_are_complete_and_traceable(self):
        expected = {"P02": ("PASS", 12), "P09": ("PASS", 16), "P10": ("PASS", 12)}
        for prototype_id, (status, vote_count) in expected.items():
            with self.subTest(prototype_id=prototype_id):
                path = ROOT / "data" / "formal_tournament_results" / f"{prototype_id}_formal_blind_tournament_v1.json"
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(payload["tournament_type"], "FORMAL_BLIND_TOURNAMENT")
                self.assertEqual(payload["aggregate"]["status"], status)
                self.assertEqual(len(payload["votes"]), vote_count)
                self.assertTrue(all(payload["formal_completeness"].values()))
                self.assertEqual(set(payload["axes"]), AXES)
                cells = {(v["benchmark_id"], v["viewport"]) for v in payload["votes"]}
                self.assertEqual(len(cells), vote_count // 2)
                for benchmark, viewport in cells:
                    roles = {v["reviewer_type"] for v in payload["votes"] if v["benchmark_id"] == benchmark and v["viewport"] == viewport}
                    self.assertGreaterEqual(len(roles), 2)
                self.assertEqual(payload["candidate_capture"]["artifact_id"], 10393223767)

    def test_registry_index_has_three_final_verdicts(self):
        index = json.loads((ROOT / "config" / "prototype_tournament_results_v1.json").read_text(encoding="utf-8"))
        self.assertEqual({r["prototype_id"] for r in index["results"]}, {"P02", "P09", "P10"})
        self.assertEqual({r["status"] for r in index["results"]}, {"PASS"})


if __name__ == "__main__":
    unittest.main()
