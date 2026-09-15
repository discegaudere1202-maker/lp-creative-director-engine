import unittest

from lp_engine.evidence_safety import (
    evaluate_evidence_selection,
    normalize_evidence_record,
    production_approved,
)


def evidence(**overrides):
    item = {
        "evidence_id": "E-001",
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


class EvidenceSafetyTest(unittest.TestCase):
    def test_provenance_missing_is_not_eligible(self):
        item = evidence(source="", verification_date="")
        result = evaluate_evidence_selection("consultation", ["O3_PROCESS"], [item])
        self.assertEqual(result.safety_status, "HEARING_REQUIRED")
        self.assertEqual(result.eligible_evidence, [])
        self.assertEqual(result.hearing_required[0]["status"], "HEARING_REQUIRED")

    def test_unknown_confidentiality_is_blocked(self):
        result = evaluate_evidence_selection(
            "consultation",
            ["O7_RISK"],
            [evidence(
                evidence_type="RISK_POLICY",
                target_objections=["O7_RISK"],
                verification_status="UNKNOWN",
            )],
            requested_claims=["秘密厳守"],
        )
        self.assertEqual(result.safety_status, "BLOCKED")
        self.assertEqual(result.blocked_claims[0]["claim_id"], "CONFIDENTIALITY")

    def test_unknown_no_pressure_is_blocked(self):
        result = evaluate_evidence_selection(
            "consultation",
            ["O7_RISK"],
            [evidence(
                evidence_type="RISK_POLICY",
                target_objections=["O7_RISK"],
                verification_status="UNKNOWN",
            )],
            requested_claims=["無理な勧誘はありません"],
        )
        self.assertEqual(result.safety_status, "BLOCKED")
        self.assertEqual(result.blocked_claims[0]["claim_id"], "NO_PRESSURE")

    def test_missing_primary_objection_routes_to_hearing(self):
        result = evaluate_evidence_selection("reservation", ["O4_NEXT"], [evidence()])
        self.assertEqual(result.safety_status, "HEARING_REQUIRED")
        self.assertEqual(result.missing_evidence[0]["target_objection"], "O4_NEXT")
        self.assertEqual(result.hearing_required[0]["suggested_hearing_field"], "post_click_flow")

    def test_verified_evidence_is_eligible(self):
        result = evaluate_evidence_selection("inquiry", ["O3_PROCESS"], [evidence()])
        self.assertEqual(result.safety_status, "PASS")
        self.assertEqual(result.eligible_evidence[0]["evidence_id"], "E-001")
        self.assertIn("CTA_ZONE", result.allowed_placements)

    def test_mismatched_objection_is_not_universal(self):
        result = evaluate_evidence_selection(
            "quote_request",
            ["O6_COST"],
            [evidence(evidence_type="EXPERIENCE", target_objections=["O1_ABILITY"])],
        )
        self.assertEqual(result.safety_status, "HEARING_REQUIRED")
        self.assertEqual(result.eligible_evidence, [])
        self.assertEqual(result.missing_evidence[0]["target_objection"], "O6_COST")

    def test_missing_non_primary_objection_does_not_stop(self):
        result = evaluate_evidence_selection("inquiry", ["O3_PROCESS"], [evidence()])
        self.assertEqual(result.safety_status, "PASS")
        self.assertEqual(result.missing_evidence, [])

    def test_unknown_rights_visual_is_not_production_approved(self):
        item = evidence(
            evidence_type="OWNER_PORTRAIT",
            target_objections=["O2_ACCOUNTABILITY"],
            rights_status="UNKNOWN",
        )
        self.assertFalse(production_approved(item))
        result = evaluate_evidence_selection("consultation", ["O2_ACCOUNTABILITY"], [item])
        self.assertEqual(result.safety_status, "HEARING_REQUIRED")

    def test_conditional_free_cannot_become_fully_free(self):
        result = evaluate_evidence_selection(
            "consultation",
            ["O6_COST"],
            [evidence(
                evidence_type="FEE_CONDITION",
                target_objections=["O6_COST"],
                claim="初回相談原則無料（条件あり）",
            )],
            requested_claims=["完全無料"],
        )
        self.assertEqual(result.safety_status, "BLOCKED")
        self.assertEqual(result.blocked_claims[0]["claim_id"], "FULLY_FREE")

    def test_invalid_goal_is_rejected(self):
        result = evaluate_evidence_selection("lead_generation", ["O3_PROCESS"], [evidence()])
        self.assertEqual(result.safety_status, "INVALID_INPUT")

    def test_legacy_ledger_is_normalized_without_inference(self):
        normalized = normalize_evidence_record(
            {
                "id": "LEGACY-1",
                "claim": "公式サイトの事実",
                "source_url": "https://example.com",
                "verified": True,
                "strength": "E2_SPECIFIC",
                "slot": "OWNER_IDENTITY",
                "placement": "MIDDLE / CTA_ZONE",
                "captured_at": "2026-09-15T00:00:00Z",
            },
            company_id="legacy-company",
            case_id="legacy-case",
        )
        self.assertEqual(normalized.evidence_id, "LEGACY-1")
        self.assertEqual(normalized.verification_status, "VERIFIED")
        self.assertEqual(normalized.verification_date, "2026-09-15")
        self.assertEqual(normalized.target_objections, ())
        self.assertFalse(production_approved(normalized))


if __name__ == "__main__":
    unittest.main()
