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

    def test_ablation_and_external_result_are_traceable(self):
        ablation = json.loads((ROOT / "data/evidence_selection_ablation_results_v1.json").read_text(encoding="utf-8"))
        self.assertEqual({item["variant_id"] for item in ablation["variants"]}, {
            "P10_ACCOUNTABILITY", "P10_CONTINUITY", "P10_BUSINESS_MODEL", "P02_PROCESS", "P02_AUTHORITY"
        })
        self.assertEqual(len(ablation["comparisons"]), 6)
        self.assertTrue(all(len(item["votes"]) == 4 for item in ablation["comparisons"][:5]))
        formal = json.loads((ROOT / "data/formal_tournament_results/P10_CONTINUITY_formal_blind_tournament_v1.json").read_text(encoding="utf-8"))
        self.assertTrue(all(formal["formal_completeness"].values()))
        self.assertEqual(len(formal["votes"]), 12)
        self.assertEqual(formal["candidate_capture"]["artifact_id"], 10398639415)
        self.assertEqual(formal["blind_bundle"]["identity_masking"], "PASS")


if __name__ == "__main__":
    unittest.main()
