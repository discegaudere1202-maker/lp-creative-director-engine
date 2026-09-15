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

    def test_build_plan_dedupes_benchmarks(self):
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
        self.assertIn("trust", plan["critical_axes"])
        self.assertIn("owner_specificity", plan["critical_axes"])

    def test_empty_tags_require_review(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pools.json"
            path.write_text(json.dumps({"pools": {}}), encoding="utf-8")
            pools = load_benchmark_pools(path)
            plan = build_tournament_plan([], pools)
        self.assertEqual(plan["status"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
