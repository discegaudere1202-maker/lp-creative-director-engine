import json
import unittest
from pathlib import Path

from lp_engine.frame_registry import FrameRecord, audit_registry


ROOT = Path(__file__).resolve().parents[1]


class FrameRegistryConfigTest(unittest.TestCase):
    def test_registry_schema_and_counts(self):
        payload = json.loads(
            (ROOT / "config/frame_registry_v1.json").read_text(encoding="utf-8")
        )
        records = [FrameRecord(**item) for item in payload["frames"]]
        audit = audit_registry(records)
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["total_records"], 15)
        self.assertEqual(audit["strict_verified_count"], 11)
        self.assertEqual(audit["candidate_count"], 4)
        self.assertEqual(audit["core_count"], 0)

    def test_core_requires_mobile_verification(self):
        payload = json.loads(
            (ROOT / "config/frame_registry_v1.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            all(
                item["stage"] != "CORE" or item["mobile_verified"]
                for item in payload["frames"]
            )
        )


if __name__ == "__main__":
    unittest.main()
