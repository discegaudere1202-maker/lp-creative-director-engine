import json
import unittest
from pathlib import Path

from lp_engine.loader import from_dict
from lp_engine.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]


def safety_evidence(**overrides):
    item = {
        "evidence_id": "PIPE-001",
        "company_id": "company-1",
        "case_id": "case-1",
        "evidence_type": "SERVICE_PROCESS",
        "evidence_strength": "E3_OPERATIONAL",
        "target_objections": ["O3_PROCESS"],
        "claim": "相談内容を確認し、必要な工程を説明します。",
        "source": "https://example.com/official",
        "source_type": "official_company_site",
        "verification_status": "VERIFIED",
        "verification_date": "2026-09-15",
        "usage_status": "ELIGIBLE",
        "placement_candidates": ["MIDDLE", "CTA_ZONE"],
        "rights_status": "NOT_APPLICABLE",
        "hearing_required": False,
        "blocking_status": "NON_BLOCKING",
        "notes": "Official text fact.",
    }
    item.update(overrides)
    return item


class PipelineEvidenceSafetyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "examples/mahora_v2.json").read_text(encoding="utf-8"))
        cls.args = from_dict(data)

    def run_with_safety(self, safety):
        return run_pipeline(*self.args, evidence_safety=safety)

    def safety_gate(self, report):
        return next(result for result in report.results if result.gate == "EvidenceSafetyGate")

    def test_verified_safety_input_is_wired_as_a_pass_gate(self):
        report = self.run_with_safety({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [safety_evidence()],
        })
        gate = self.safety_gate(report)
        self.assertEqual(gate.status, "PASS")
        self.assertEqual(gate.details["safety_status"], "PASS")
        self.assertEqual(gate.details["approved_claims"], [safety_evidence()["claim"]])

    def test_missing_evidence_holds_pipeline_without_generating_copy(self):
        report = self.run_with_safety({
            "conversion_goal": "consultation",
            "primary_objections": ["O7_RISK"],
            "evidence_ledger": [],
            "requested_claims": ["秘密厳守"],
        })
        gate = self.safety_gate(report)
        self.assertEqual(gate.status, "FAIL")
        self.assertEqual(gate.details["approved_claims"], [])
        self.assertEqual(gate.details["blocked_claims"][0]["claim_id"], "CONFIDENTIALITY")
        self.assertTrue(gate.details["hearing_required"])

    def test_existing_pipeline_is_unchanged_without_safety_input(self):
        report = run_pipeline(*self.args)
        self.assertFalse(any(result.gate == "EvidenceSafetyGate" for result in report.results))


if __name__ == "__main__":
    unittest.main()
