import json
import unittest
from pathlib import Path

from lp_engine.benchmark_pool import build_tournament_plan, load_benchmark_catalog, load_benchmark_pools


ROOT = Path(__file__).resolve().parents[1]


class PrototypeTournamentPlanTest(unittest.TestCase):
    def test_plans_have_three_or_more_mobile_ready_opponents(self):
        payload = json.loads(
            (ROOT / "config/prototype_tournament_plans_v1.json").read_text(encoding="utf-8")
        )
        pools = load_benchmark_pools(ROOT / "config/benchmark_pools_v1.json")
        catalog = load_benchmark_catalog(ROOT / "config/benchmark_pool_v1.json")

        self.assertGreaterEqual(len(payload["plans"]), 5)
        for configured in payload["plans"]:
            plan = build_tournament_plan(
                configured["problem_tags"],
                pools,
                catalog=catalog,
                require_mobile_verified=True,
            )
            self.assertEqual(plan["status"], "READY", configured["prototype_id"])
            self.assertGreaterEqual(len(plan["benchmark_ids"]), 3, configured["prototype_id"])
            self.assertEqual(plan["benchmark_ids"], configured["benchmark_ids"], configured["prototype_id"])
            self.assertEqual(configured["required_viewports"], [1440, 390])
            self.assertEqual(configured["plan_status"], "READY_FOR_SCREENSHOT_BUNDLE")
            self.assertEqual(configured["candidate_screenshot_status"], "MISSING_FROM_REPOSITORY")

    def test_no_tournament_result_is_claimed_without_candidate_screenshots(self):
        payload = json.loads(
            (ROOT / "config/prototype_tournament_plans_v1.json").read_text(encoding="utf-8")
        )
        for configured in payload["plans"]:
            if configured["candidate_screenshot_status"] != "READY":
                self.assertNotIn(configured["plan_status"], {"PASS", "FAIL", "HOLD"})


if __name__ == "__main__":
    unittest.main()
