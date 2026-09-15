import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BenchmarkPoolConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(
            (ROOT / "config/benchmark_pool_v1.json").read_text(encoding="utf-8")
        )
        cls.pools = json.loads(
            (ROOT / "config/benchmark_pools_v1.json").read_text(encoding="utf-8")
        )
        cls.ids = {item["id"] for item in cls.catalog["benchmarks"]}

    def test_catalog_ids_are_unique(self):
        ids = [item["id"] for item in self.catalog["benchmarks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_benchmark_has_sources_and_axes(self):
        for item in self.catalog["benchmarks"]:
            with self.subTest(item=item["id"]):
                self.assertGreaterEqual(len(item.get("source_urls", [])), 1)
                self.assertGreaterEqual(len(item.get("comparison_axes", [])), 2)

    def test_pool_ids_exist_and_are_unique(self):
        for name, pool in self.pools["pools"].items():
            ids = pool["benchmark_ids"]
            with self.subTest(pool=name):
                self.assertGreaterEqual(len(ids), 3)
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(set(ids).issubset(self.ids))

    def test_pool_has_critical_axes(self):
        for name, pool in self.pools["pools"].items():
            with self.subTest(pool=name):
                self.assertGreaterEqual(len(pool.get("critical_axes", [])), 2)


if __name__ == "__main__":
    unittest.main()
