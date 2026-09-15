import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.benchmark_tournament import make_blind_pairings, aggregate_tournament


AXES_WIN = {
    "immediate_read": 1,
    "distinctness": 1,
    "owner_specificity": 1,
    "visual_hierarchy": 1,
    "craft_detail": 1,
    "emotional_pull": 1,
    "trust": 0,
    "share_impulse": 1,
    "mobile_quality": 1,
    "conversion_intent": 0,
}

AXES_LOSE = {
    "immediate_read": -1,
    "distinctness": -1,
    "owner_specificity": -1,
    "visual_hierarchy": -1,
    "craft_detail": -1,
    "emotional_pull": -1,
    "trust": 0,
    "share_impulse": -1,
    "mobile_quality": -1,
    "conversion_intent": 0,
}


def vote(benchmark, reviewer, viewport, overall, axes):
    return {
        "benchmark_id": benchmark,
        "reviewer_type": reviewer,
        "viewport": viewport,
        "overall": overall,
        "axes": axes,
    }


class BenchmarkTournamentTest(unittest.TestCase):
    def test_blind_pairings_are_repeatable(self):
        a = make_blind_pairings("candidate", ["b1", "b2", "b3"], seed=42)
        b = make_blind_pairings("candidate", ["b1", "b2", "b3"], seed=42)
        self.assertEqual([x.candidate_side for x in a], [x.candidate_side for x in b])

    def test_candidate_can_pass(self):
        votes = []
        for benchmark in ("b1", "b2", "b3"):
            for reviewer in ("creative", "cro"):
                for viewport in ("1440", "390"):
                    votes.append(vote(benchmark, reviewer, viewport, 1, AXES_WIN))
        result = aggregate_tournament({"votes": votes})
        self.assertEqual(result.status, "PASS")
        self.assertGreaterEqual(result.win_rate, 0.60)

    def test_outclassed_candidate_fails(self):
        votes = []
        for benchmark in ("b1", "b2", "b3"):
            for reviewer in ("creative", "cro"):
                for viewport in ("1440", "390"):
                    votes.append(vote(benchmark, reviewer, viewport, -1, AXES_LOSE))
        result = aggregate_tournament({"votes": votes})
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.classification, "OUTCLASSED")

    def test_missing_mobile_holds(self):
        votes = []
        for benchmark in ("b1", "b2", "b3"):
            for reviewer in ("creative", "cro"):
                votes.append(vote(benchmark, reviewer, "1440", 1, AXES_WIN))
        result = aggregate_tournament({"votes": votes})
        self.assertEqual(result.status, "HOLD")
        self.assertIn("missing required viewport 390", result.review_reasons)


if __name__ == "__main__":
    unittest.main()
