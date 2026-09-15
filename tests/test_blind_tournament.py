import unittest

from lp_engine.benchmark_tournament import aggregate_tournament


AXES = [
    "immediate_read",
    "distinctness",
    "owner_specificity",
    "visual_hierarchy",
    "craft_detail",
    "emotional_pull",
    "trust",
    "share_impulse",
    "mobile_quality",
    "conversion_intent",
]


def vote(benchmark, reviewer, viewport, overall=1, axis_value=1, overrides=None):
    axes = {axis: axis_value for axis in AXES}
    if overrides:
        axes.update(overrides)
    return {
        "benchmark_id": benchmark,
        "reviewer_type": reviewer,
        "viewport": viewport,
        "overall": overall,
        "axes": axes,
    }


class BlindTournamentTest(unittest.TestCase):
    def test_pass_requires_strong_relative_performance(self):
        votes = []
        for benchmark in ["a", "b", "c"]:
            for reviewer in ["creative", "cro"]:
                for viewport in ["1440", "390"]:
                    votes.append(vote(benchmark, reviewer, viewport))
        result = aggregate_tournament({"votes": votes})
        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.win_rate, 1.0)

    def test_critical_axis_loss_fails(self):
        votes = []
        for benchmark in ["a", "b", "c"]:
            for reviewer in ["creative", "cro"]:
                for viewport in ["1440", "390"]:
                    votes.append(
                        vote(
                            benchmark,
                            reviewer,
                            viewport,
                            overrides={
                                "owner_specificity": -1,
                                "share_impulse": -1,
                            },
                        )
                    )
        result = aggregate_tournament({"votes": votes})
        self.assertEqual(result.status, "FAIL")

    def test_incomplete_tournament_holds(self):
        votes = [
            vote("a", "creative", "1440"),
            vote("a", "cro", "390"),
        ]
        result = aggregate_tournament({"votes": votes})
        self.assertEqual(result.status, "HOLD")


if __name__ == "__main__":
    unittest.main()
