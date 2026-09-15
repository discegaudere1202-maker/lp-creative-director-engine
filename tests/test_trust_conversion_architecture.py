import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TrustConversionArchitectureTest(unittest.TestCase):
    def test_rule_file_is_reusable_and_evidence_safe(self):
        payload = json.loads((ROOT / "config/trust_conversion_architecture_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], 2)
        self.assertEqual(payload["causal_chain"], ["COMPANY_TRUTH","TRUST_EVIDENCE","CUSTOMER_RELEVANCE","REASON_TO_CONSULT","PSYCHOLOGICAL_SAFETY","ACTION"])
        rule_ids = {rule["id"] for rule in payload["rules"]}
        self.assertEqual(rule_ids, {"PROOF_TO_PROCESS","PERMISSION_BEFORE_ASK","AFTER_CLICK_CERTAINTY","EVIDENCE_ECONOMY","MOBILE_ACTION_BUDGET","WHO_HOW_NEXT_BRIDGE","UNKNOWN_BOUNDARY","EVIDENCE_STRENGTH_MODEL"})
        self.assertIn("OWNER_IDENTITY", payload["evidence_slots"])
        self.assertEqual(payload["status"], "OBSERVED_NOT_ENGINE_IMPLEMENTED")
        self.assertEqual([item["level"] for item in payload["evidence_strength_model"]], ["E1_WEAK","E2_SPECIFIC","E3_OPERATIONAL","E4_RISK_REDUCING","E5_DECISION_ENABLING"])
        self.assertTrue(payload["hearing_requirements"]["REQUIRED"])

if __name__ == "__main__":
    unittest.main()
