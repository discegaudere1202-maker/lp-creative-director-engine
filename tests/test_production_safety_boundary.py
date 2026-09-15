import json
import unittest
from pathlib import Path
from unittest.mock import patch

from lp_engine.loader import from_dict
from lp_engine.pipeline import run_pipeline
from lp_engine.evidence_safety import evaluate_evidence_selection


ROOT = Path(__file__).resolve().parents[1]


def evidence(**overrides):
    item = {
        "evidence_id": "BOUNDARY-001",
        "company_id": "company-1",
        "case_id": "case-1",
        "evidence_type": "SERVICE_PROCESS",
        "evidence_strength": "E3_OPERATIONAL",
        "target_objections": ["O3_PROCESS"],
        "claim": "相談内容を確認し、必要な工程を説明します。",
        "source": "https://example.com/official",
        "source_type": "official_company_site",
        "verification_status": "VERIFIED",
        "verification_date": "2026-09-16",
        "usage_status": "ELIGIBLE",
        "placement_candidates": ["MIDDLE", "CTA_ZONE"],
        "rights_status": "NOT_APPLICABLE",
        "hearing_required": False,
        "blocking_status": "NON_BLOCKING",
        "notes": "Official text fact.",
    }
    item.update(overrides)
    return item


class ProductionSafetyBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / "examples/mahora_v2.json").read_text(encoding="utf-8"))
        cls.args = from_dict(data)

    def run_production(self, safety):
        return run_pipeline(*self.args, mode="production", evidence_safety=safety)

    def gate(self, report):
        return next(result for result in report.results if result.gate == "EvidenceSafetyGate")

    def test_production_without_safety_is_not_executable(self):
        report = run_pipeline(*self.args, mode="production")
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(self.gate(report).status, "FAIL")

    def test_research_only_evidence_cannot_enter_production_output(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [evidence(usage_status="RESEARCH_ONLY")],
        })
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(report.evidence_manifest, [])

    def test_low_level_selector_is_fail_closed_by_default(self):
        record = evidence(usage_status="RESEARCH_ONLY")
        default = evaluate_evidence_selection("consultation", ["O3_PROCESS"], [record])
        research = evaluate_evidence_selection(
            "consultation",
            ["O3_PROCESS"],
            [record],
            require_production_clearance=False,
        )
        self.assertEqual(default.eligible_evidence, [])
        self.assertEqual(research.eligible_evidence[0]["evidence_id"], "BOUNDARY-001")

    def test_raw_unsupported_claim_is_blocked(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O7_RISK"],
            "evidence_ledger": [],
            "requested_claims": ["秘密厳守"],
        })
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(report.blocked_claims[0]["claim_id"], "CONFIDENTIALITY")

    def test_research_only_evidence_cannot_support_production_claim(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O7_RISK"],
            "evidence_ledger": [evidence(
                evidence_type="RISK_POLICY",
                target_objections=["O7_RISK"],
                claim="秘密厳守",
                usage_status="RESEARCH_ONLY",
            )],
            "requested_claims": ["秘密厳守"],
        })
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(report.blocked_claims[0]["claim_id"], "CONFIDENTIALITY")

    def test_claim_block_can_continue_with_other_safe_evidence(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [evidence()],
            "requested_claims": ["無理な勧誘はありません"],
        })
        self.assertEqual(report.safety_scope, "CLAIM_BLOCK")
        self.assertTrue(report.production_output_allowed)
        self.assertEqual(report.status, "HOLD")
        self.assertEqual(report.evidence_manifest[0]["evidence_id"], "BOUNDARY-001")

    def test_missing_provenance_blocks_output(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [evidence(source="", verification_date="")],
        })
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(report.evidence_manifest, [])

    def test_unknown_rights_blocks_output(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O2_ACCOUNTABILITY"],
            "evidence_ledger": [evidence(
                evidence_type="OWNER_PORTRAIT",
                target_objections=["O2_ACCOUNTABILITY"],
                rights_status="UNKNOWN",
            )],
        })
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(report.evidence_manifest, [])

    def test_malformed_ledger_holds_without_crashing(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": ["malformed"],
        })
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(self.gate(report).status, "HOLD")

    def test_selector_exception_fails_closed(self):
        with patch("lp_engine.pipeline.evaluate_evidence_selection", side_effect=RuntimeError("boom")):
            report = self.run_production({
                "conversion_goal": "consultation",
                "primary_objections": ["O3_PROCESS"],
                "evidence_ledger": [evidence()],
            })
        self.assertFalse(report.production_output_allowed)
        self.assertEqual(self.gate(report).status, "FAIL")

    def test_non_primary_missing_does_not_stop_verified_section(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [evidence()],
        })
        self.assertTrue(report.production_output_allowed)
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.evidence_manifest[0]["evidence_id"], "BOUNDARY-001")

    def test_hearing_required_is_connected_to_minimum_question_plan(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O7_RISK"],
            "evidence_ledger": [],
            "requested_claims": ["秘密厳守"],
        })
        self.assertEqual(report.hearing_plan["question_count"], 1)
        self.assertEqual(report.hearing_plan["minimum_question_set"][0]["field_id"], "risk_and_privacy_policy")

    def test_legacy_path_still_requires_safety_selection(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [{
                "id": "LEGACY-001",
                "company_id": "company-1",
                "case_id": "case-1",
                "slot": "SERVICE_PROCESS",
                "strength": "E3_OPERATIONAL",
                "target_objections": ["O3_PROCESS"],
                "claim": "公式サイトに掲載された相談工程。",
                "source_url": "https://example.com/official",
                "verified": True,
                "verification_date": "2026-09-16",
                "usage_status": "ELIGIBLE",
                "rights_status": "NOT_APPLICABLE",
                "placement": "MIDDLE",
            }],
        })
        self.assertTrue(report.production_output_allowed)
        self.assertEqual(report.evidence_manifest[0]["evidence_id"], "LEGACY-001")

    def test_manifest_contains_only_safety_eligible_ids(self):
        report = self.run_production({
            "conversion_goal": "consultation",
            "primary_objections": ["O3_PROCESS"],
            "evidence_ledger": [evidence(), evidence(
                evidence_id="BOUNDARY-BLOCKED",
                verification_status="UNKNOWN",
            )],
        })
        ids = {item["evidence_id"] for item in report.evidence_manifest}
        self.assertEqual(ids, {"BOUNDARY-001"})
        self.assertTrue(all(item["verification_status"] == "VERIFIED" for item in report.evidence_manifest))


if __name__ == "__main__":
    unittest.main()
