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

        expected = payload.get("expected_counts", {})
        stage_counts = {
            "CANDIDATE": sum(1 for item in payload["frames"] if item["stage"] == "CANDIDATE"),
            "VERIFIED": sum(1 for item in payload["frames"] if item["stage"] == "VERIFIED"),
            "CORE": sum(1 for item in payload["frames"] if item["stage"] == "CORE"),
            "REJECTED": sum(1 for item in payload["frames"] if item["stage"] == "REJECTED"),
        }

        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["total_records"], len(payload["frames"]))
        self.assertEqual(
            audit["strict_verified_count"],
            stage_counts["VERIFIED"] + stage_counts["CORE"],
        )
        self.assertEqual(audit["candidate_count"], stage_counts["CANDIDATE"])
        self.assertEqual(audit["core_count"], stage_counts["CORE"])
        self.assertEqual(audit["rejected_count"], stage_counts["REJECTED"])

        if expected:
            self.assertEqual(expected.get("total_records"), len(payload["frames"]))
            self.assertEqual(expected.get("candidate_count"), stage_counts["CANDIDATE"])
            self.assertEqual(expected.get("verified_count"), stage_counts["VERIFIED"])
            self.assertEqual(expected.get("core_count"), stage_counts["CORE"])
            self.assertEqual(expected.get("rejected_count"), stage_counts["REJECTED"])

    def test_core_requires_live_390px_m3_verification(self):
        payload = json.loads(
            (ROOT / "config/frame_registry_v1.json").read_text(encoding="utf-8")
        )
        self.assertTrue(
            all(
                item["stage"] != "CORE"
                or (
                    item["mobile_verified"]
                    and item.get("mobile_evidence_grade", "M0") == "M3"
                )
                for item in payload["frames"]
            )
        )


if __name__ == "__main__":
    unittest.main()
