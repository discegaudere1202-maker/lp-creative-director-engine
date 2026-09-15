import json
import unittest
from pathlib import Path

from lp_engine.benchmark_pool import (
    build_tournament_plan,
    load_benchmark_catalog,
    load_benchmark_pools,
)


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkReadinessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pools = load_benchmark_pools(ROOT / "config/benchmark_pools_v1.json")
        cls.catalog = load_benchmark_catalog(ROOT / "config/benchmark_pool_v1.json")

    def test_mobile_unverified_pool_is_not_tournament_ready(self):
        plan = build_tournament_plan(
            ["NO_WEB", "SME", "LOCAL"],
            self.pools,
            catalog=self.catalog,
            require_mobile_verified=True,
        )
        self.assertEqual(plan["status"], "REVIEW")
        self.assertLess(len(plan["benchmark_ids"]), 3)
        self.assertTrue(plan["blocked_benchmarks"])

    def test_research_plan_can_exist_without_mobile_gate(self):
        plan = build_tournament_plan(
            ["NO_WEB", "SME", "LOCAL"],
            self.pools,
            catalog=self.catalog,
            require_mobile_verified=False,
        )
        self.assertGreaterEqual(len(plan["research_benchmark_ids"]), 3)
        self.assertIn("LOCAL_SME_TRANSFER", plan["pool_names"])


if __name__ == "__main__":
    unittest.main()
