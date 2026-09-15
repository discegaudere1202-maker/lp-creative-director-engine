import unittest

from lp_engine.evidence_safety import evaluate_evidence_selection, production_approved


def record(evidence_type, targets, *, verification="UNKNOWN", rights="NOT_APPLICABLE", claim="fact", source="https://official.example", date="2026-09-15", usage="ELIGIBLE", hearing=False):
    return {
        "evidence_id": "ADV-001",
        "company_id": "adversarial",
        "case_id": "adversarial",
        "evidence_type": evidence_type,
        "evidence_strength": "E2_SPECIFIC",
        "target_objections": targets,
        "claim": claim,
        "source": source,
        "source_type": "official_company_site",
        "verification_status": verification,
        "verification_date": date,
        "usage_status": usage,
        "placement_candidates": ["CTA_ZONE"],
        "rights_status": rights,
        "hearing_required": hearing,
        "blocking_status": "NON_BLOCKING",
        "notes": "adversarial fixture",
    }


class EvidenceSafetyAdversarialTest(unittest.TestCase):
    def test_guess_no_pressure_is_zero_approved(self):
        result = evaluate_evidence_selection(
            "consultation", ["O7_RISK"],
            [record("RISK_POLICY", ["O7_RISK"], claim="たぶん勧誘しません")],
            requested_claims=["たぶん勧誘しません"],
        )
        self.assertEqual(result.blocked_claims[0]["status"], "BLOCKED")

    def test_review_cannot_prove_confidentiality(self):
        result = evaluate_evidence_selection(
            "consultation", ["O7_RISK"],
            [record("TESTIMONIAL", ["O7_RISK"], verification="VERIFIED", claim="満足しました")],
            requested_claims=["秘密厳守"],
        )
        self.assertEqual(result.blocked_claims[0]["claim_id"], "CONFIDENTIALITY")

    def test_unverified_response_speed_is_blocked(self):
        result = evaluate_evidence_selection(
            "inquiry", ["O4_NEXT"],
            [record("RESPONSE_EXPECTATION", ["O4_NEXT"], claim="返信は早いと思います")],
            requested_claims=["返信は24時間以内"],
        )
        self.assertEqual(result.blocked_claims[0]["claim_id"], "RESPONSE_TIME")

    def test_unknown_photo_rights_never_production_approved(self):
        self.assertFalse(production_approved(record("OWNER_PORTRAIT", ["O2_ACCOUNTABILITY"], verification="VERIFIED", rights="UNKNOWN")))

    def test_sns_metric_without_verification_is_not_eligible(self):
        result = evaluate_evidence_selection(
            "inquiry", ["O1_ABILITY"],
            [record("VERIFIED_METRIC", ["O1_ABILITY"], source="https://social.example/post", verification="UNKNOWN", date="")],
        )
        self.assertEqual(result.eligible_evidence, [])
        self.assertEqual(result.safety_status, "HEARING_REQUIRED")

    def test_conditional_free_does_not_support_full_free(self):
        result = evaluate_evidence_selection(
            "consultation", ["O6_COST"],
            [record("FEE_CONDITION", ["O6_COST"], verification="VERIFIED", claim="初回相談のみ無料（条件あり）")],
            requested_claims=["完全無料"],
        )
        self.assertEqual(result.blocked_claims[0]["claim_id"], "FULLY_FREE")

    def test_unsupported_rank_claim_is_blocked(self):
        result = evaluate_evidence_selection(
            "inquiry", ["O1_ABILITY"],
            [record("VERIFIED_METRIC", ["O1_ABILITY"], verification="VERIFIED", claim="10件の事例")],
            requested_claims=["地域No.1"],
        )
        self.assertEqual(result.blocked_claims[0]["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
