import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_VIEWPORTS = {(390, 844), (1440, 1000)}


class CaptureTargetConfigTest(unittest.TestCase):
    def _load(self, path):
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_benchmark_capture_has_exact_formal_viewports_and_unique_ids(self):
        payload = self._load("config/m3_capture_targets_v1.json")
        viewports = {(v["width"], v["height"]) for v in payload["viewports"]}
        self.assertEqual(viewports, REQUIRED_VIEWPORTS)
        ids = [item["benchmark_id"] for item in payload["targets"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in payload["targets"]:
            with self.subTest(item=item["benchmark_id"]):
                self.assertTrue(item["url"].startswith("https://"))
                self.assertTrue(item.get("frame_role", "").strip())

    def test_price_transparency_targets_request_a_matched_frame(self):
        payload = self._load("config/m3_capture_targets_v1.json")
        pricing = [
            item for item in payload["targets"]
            if item.get("frame_role") == "PRICE_TRANSPARENCY"
        ]
        self.assertGreaterEqual(len(pricing), 3)
        for item in pricing:
            with self.subTest(item=item["benchmark_id"]):
                self.assertTrue(item.get("focus_text", "").strip())

    def test_prototype_capture_is_reproducible_and_frame_matched(self):
        payload = self._load("config/prototype_capture_targets_v1.json")
        viewports = {(v["width"], v["height"]) for v in payload["viewports"]}
        self.assertEqual(viewports, REQUIRED_VIEWPORTS)
        ids = [item["prototype_id"] for item in payload["targets"]]
        self.assertEqual(ids, ["P02", "P09", "P10"])
        self.assertEqual(len(ids), len(set(ids)))
        for item in payload["targets"]:
            with self.subTest(item=item["prototype_id"]):
                self.assertTrue(item.get("frame_role", "").strip())
                self.assertTrue((ROOT / item["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
