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
        cls.mobile = json.loads(
            (ROOT / "config/mobile_benchmark_verification_v1.json").read_text(encoding="utf-8")
        )
        cls.ids = {item["id"] for item in cls.catalog["benchmarks"]}
        cls.catalog_by_id = {item["id"]: item for item in cls.catalog["benchmarks"]}
        cls.mobile_by_id = {item["benchmark_id"]: item for item in cls.mobile["records"]}

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

    def test_local_sme_transfer_has_three_traceable_m3_benchmarks(self):
        pool_ids = self.pools["pools"]["LOCAL_SME_TRANSFER"]["benchmark_ids"]
        ready = []
        for benchmark_id in pool_ids:
            catalog = self.catalog_by_id[benchmark_id]
            mobile = self.mobile_by_id.get(benchmark_id)
            if not mobile:
                continue
            review = mobile.get("mobile_review", {})
            capture = mobile.get("live_capture", {})
            if (
                catalog.get("stage") in {"VERIFIED", "CORE"}
                and catalog.get("desktop_verified") is True
                and catalog.get("mobile_verified") is True
                and catalog.get("mobile_evidence_grade") == "M3"
                and review.get("evidence_grade") == "M3"
                and capture.get("review_status") == "PASS"
                and capture.get("viewport") == "390x844"
                and capture.get("http_status") == 200
            ):
                ready.append(benchmark_id)

        self.assertGreaterEqual(
            len(ready),
            3,
            "LOCAL_SME_TRANSFER must contain at least three visually reviewed, traceable M3 benchmarks before formal SME tournament use",
        )


if __name__ == "__main__":
    unittest.main()
