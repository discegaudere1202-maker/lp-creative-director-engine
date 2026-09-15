import unittest

from lp_engine.blind_tournament import AXES, PairwiseReview, evaluate_tournament


def scores(value=1, critical=None):
    result = {axis: value for axis in AXES}
    if critical:
        result.update(critical)
    return result


class BlindTournamentTest(unittest.TestCase):
    def test_pass_requires_strong_relative_performance(self):
        reviews = []
        for benchmark in ["a", "b", "c"]:
            for reviewer in ["creative", "cro"]:
                for viewport in ["1440", "390"]:
                    reviews.append(
                        PairwiseReview(benchmark, reviewer, viewport, scores(1))
                    )
        result = evaluate_tournament(reviews)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["win_rate"], 1.0)

    def test_critical_axis_loss_fails(self):
        reviews = []
        for benchmark in ["a", "b", "c"]:
            for reviewer in ["creative", "cro"]:
                for viewport in ["1440", "390"]:
                    reviews.append(
                        PairwiseReview(
                            benchmark,
                            reviewer,
                            viewport,
                            scores(1, {
                                "owner_specificity": -1,
                                "share_impulse": -1,
                            }),
                        )
                    )
        result = evaluate_tournament(reviews)
        self.assertEqual(result["status"], "FAIL")

    def test_incomplete_tournament_holds(self):
        reviews = [
            PairwiseReview("a", "creative", "1440", scores(1)),
            PairwiseReview("a", "cro", "390", scores(1)),
        ]
        result = evaluate_tournament(reviews)
        self.assertEqual(result["status"], "HOLD")


if __name__ == "__main__":
    unittest.main()
