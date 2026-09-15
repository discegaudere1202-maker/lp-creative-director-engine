import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvidenceSelectionLogicTest(unittest.TestCase):
    def test_objection_model_and_mapping_are_complete(self):
        payload = json.loads((ROOT / "config/evidence_selection_logic_v1.json").read_text(encoding="utf-8"))
        self.assertEqual({item["id"] for item in payload["objection_model"]}, {f"O{i}_{name}" for i, name in enumerate(["ABILITY", "ACCOUNTABILITY", "PROCESS", "NEXT", "DECISION", "COST", "RISK", "CONTINUITY"], 1)})
        self.assertEqual({item["objection"] for item in payload["objection_to_evidence_mapping"]}, {f"O{i}_{name}" for i, name in enumerate(["ABILITY", "ACCOUNTABILITY", "PROCESS", "NEXT", "DECISION", "COST", "RISK", "CONTINUITY"], 1)})
        for item in payload["objection_to_evidence_mapping"]:
            self.assertTrue(item["preferred_placement"])
            self.assertIn("HEARING_REQUIRED", item["fallback"])

    def test_safety_and_trust_rules_have_separate_statuses(self):
        payload = json.loads((ROOT / "config/evidence_selection_logic_v1.json").read_text(encoding="utf-8"))
        self.assertIn("safety_integrity", payload["rules"])
        self.assertIn("trust_optimization", payload["rules"])
        self.assertTrue(all(item["status"] == "REPLICATED" for item in payload["rules"]["safety_integrity"]))
        self.assertTrue(any(item["status"] == "HYPOTHESIS" for item in payload["rules"]["trust_optimization"]))


if __name__ == "__main__":
    unittest.main()
