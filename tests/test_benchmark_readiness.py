import unittest

from lp_engine.benchmark_pool import BenchmarkPool, build_tournament_plan


class BenchmarkReadinessTest(unittest.TestCase):
    def test_mobile_unverified_catalog_is_not_tournament_ready(self):
        pools = {
            "LOCAL_SME_TRANSFER": BenchmarkPool(
                name="LOCAL_SME_TRANSFER",
                benchmark_ids=["a", "b", "c"],
                critical_axes=["trust", "mobile_quality"],
            )
        }
        catalog = {
            "a": {"stage": "VERIFIED", "desktop_verified": True, "mobile_verified": False},
            "b": {"stage": "VERIFIED", "desktop_verified": True, "mobile_verified": False},
            "c": {"stage": "VERIFIED", "desktop_verified": True, "mobile_verified": True},
        }
        plan = build_tournament_plan(
            ["NO_WEB", "SME", "LOCAL"],
            pools,
            catalog=catalog,
            require_mobile_verified=True,
        )
        self.assertEqual(plan["status"], "REVIEW")
        self.assertEqual(plan["benchmark_ids"], ["c"])
        self.assertEqual(len(plan["blocked_benchmarks"]), 2)

    def test_three_mobile_verified_benchmarks_are_ready(self):
        pools = {
            "LOCAL_SME_TRANSFER": BenchmarkPool(
                name="LOCAL_SME_TRANSFER",
                benchmark_ids=["a", "b", "c"],
                critical_axes=["trust", "mobile_quality"],
            )
        }
        catalog = {
            key: {"stage": "VERIFIED", "desktop_verified": True, "mobile_verified": True}
            for key in ["a", "b", "c"]
        }
        plan = build_tournament_plan(
            ["NO_WEB", "SME", "LOCAL"],
            pools,
            catalog=catalog,
            require_mobile_verified=True,
        )
        self.assertEqual(plan["status"], "READY")
        self.assertEqual(plan["benchmark_ids"], ["a", "b", "c"])
        self.assertEqual(plan["blocked_benchmarks"], [])

    def test_research_plan_can_exist_without_mobile_gate(self):
        pools = {
            "LOCAL_SME_TRANSFER": BenchmarkPool(
                name="LOCAL_SME_TRANSFER",
                benchmark_ids=["a", "b", "c"],
                critical_axes=["trust"],
            )
        }
        catalog = {
            key: {"stage": "VERIFIED", "desktop_verified": True, "mobile_verified": False}
            for key in ["a", "b", "c"]
        }
        plan = build_tournament_plan(
            ["NO_WEB", "SME", "LOCAL"],
            pools,
            catalog=catalog,
            require_mobile_verified=False,
        )
        self.assertEqual(plan["status"], "READY")
        self.assertEqual(len(plan["benchmark_ids"]), 3)


if __name__ == "__main__":
    unittest.main()
