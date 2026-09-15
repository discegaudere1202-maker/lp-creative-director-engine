import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.benchmark_pool import (
    build_tournament_plan,
    load_benchmark_pools,
    recommend_pool_names,
)


class BenchmarkPoolTest(unittest.TestCase):
    def test_recommend_asset_light_local_b2b(self):
        names = recommend_pool_names(["NO_WEB", "SME", "B2B", "DOCUMENT"])
        self.assertIn("B2B_EXPLAINER_DOCUMENT", names)
        self.assertIn("ASSET_LIGHT", names)
        self.assertIn("LOCAL_SME_TRANSFER", names)

    def test_problem_tags_choose_problem_pools(self):
        names = recommend_pool_names([
            "NO_WEB", "SME", "BUSINESS_VERB", "EMOTIONAL_BARRIER"
        ])
        self.assertIn("BUSINESS_VERB", names)
        self.assertIn("EMOTIONAL_BARRIER", names)
        self.assertIn("ASSET_LIGHT", names)
        self.assertIn("LOCAL_SME_TRANSFER", names)

    def test_build_plan_dedupes_and_caps_formal_benchmarks(self):
        data = {
            "pools": {
                "B2B_EXPLAINER_DOCUMENT": {
                    "benchmark_ids": ["C23", "C24", "C25"],
                    "critical_axes": ["trust"],
                },
                "ASSET_LIGHT": {
                    "benchmark_ids": ["C23", "C31", "C32"],
                    "critical_axes": ["owner_specificity"],
                },
                "LOCAL_SME_TRANSFER": {
                    "benchmark_ids": ["C04", "C07", "C23"],
                    "critical_axes": ["conversion_intent"],
                },
            }
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pools.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            pools = load_benchmark_pools(path)
            plan = build_tournament_plan(
                ["NO_WEB", "SME", "B2B", "DOCUMENT"], pools, max_benchmarks=7
            )
        self.assertEqual(plan["status"], "READY")
        self.assertEqual(len(plan["benchmark_ids"]), len(set(plan["benchmark_ids"])))
        self.assertLessEqual(len(plan["benchmark_ids"]), 5)
        self.assertEqual(len(plan["benchmark_ids"]), 5)
        self.assertIn("trust", plan["critical_axes"])
        self.assertIn("owner_specificity", plan["critical_axes"])

    def test_m2_is_research_ready_but_blocked_from_production_tournament(self):
        data = {
            "pools": {
                "MOBILE_FIRST": {
                    "benchmark_ids": ["m2-a", "m3-a", "m3-b", "m3-c"],
                    "critical_axes": ["mobile_quality"],
                }
            }
        }
        catalog = {
            "m2-a": {
                "stage": "VERIFIED",
                "desktop_verified": True,
                "mobile_verified": True,
                "mobile_evidence_grade": "M2",
            },
            "m3-a": {
                "stage": "VERIFIED",
                "desktop_verified": True,
                "mobile_verified": True,
                "mobile_evidence_grade": "M3",
            },
            "m3-b": {
                "stage": "CORE",
                "desktop_verified": True,
                "mobile_verified": True,
                "mobile_evidence_grade": "M3",
            },
            "m3-c": {
                "stage": "VERIFIED",
                "desktop_verified": True,
                "mobile_verified": True,
                "mobile_evidence_grade": "M3",
            },
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pools.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            pools = load_benchmark_pools(path)
            plan = build_tournament_plan(["MOBILE_FIRST"], pools, catalog=catalog)

        self.assertEqual(plan["status"], "READY")
        self.assertNotIn("m2-a", plan["benchmark_ids"])
        self.assertEqual(plan["benchmark_ids"], ["m3-a", "m3-b", "m3-c"])
        blocked = {item["benchmark_id"]: item["reasons"] for item in plan["blocked_benchmarks"]}
        self.assertIn("production tournament requires M3 live/captured 390px evidence", blocked["m2-a"])

    def test_empty_tags_require_review(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pools.json"
            path.write_text(json.dumps({"pools": {}}), encoding="utf-8")
            pools = load_benchmark_pools(path)
            plan = build_tournament_plan([], pools)
        self.assertEqual(plan["status"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
