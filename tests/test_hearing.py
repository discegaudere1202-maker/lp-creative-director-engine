import unittest

from lp_engine.evidence_safety import evaluate_evidence_selection
from lp_engine.hearing import (
    answer_to_evidence_candidate,
    complete_evidence_candidate,
    plan_hearing,
)


def safety_gap(goal, objections, missing, blocked=None):
    return {
        "conversion_goal": goal,
        "primary_objections": objections,
        "missing_evidence": [
            {"target_objection": objection, "preferred_evidence_types": types, "status": "MISSING"}
            for objection, types in missing
        ],
        "blocked_claims": blocked or [],
        "hearing_required": [
            {"target_objection": objection, "missing_evidence_type": types, "status": "HEARING_REQUIRED"}
            for objection, types in missing
        ],
        "eligible_evidence": [],
    }


class HearingPlannerTest(unittest.TestCase):
    def test_missing_evidence_maps_to_natural_minimum_questions(self):
        plan = plan_hearing(
            safety_gap("consultation", ["O7_RISK", "O4_NEXT"], [
                ("O7_RISK", ["RISK_POLICY"]),
                ("O4_NEXT", ["POST_CLICK_FLOW"]),
            ]),
            domain="相談サービス",
        )
        fields = {item["field_id"] for item in plan.minimum_question_set}
        self.assertEqual(fields, {"risk_and_privacy_policy", "post_click_flow"})
        self.assertTrue(all("O7" not in item["question"] for item in plan.minimum_question_set))
        self.assertEqual(plan.to_dict()["question_count"], 2)

    def test_existing_evidence_suppresses_question(self):
        plan = plan_hearing(
            safety_gap("reservation", ["O4_NEXT"], [("O4_NEXT", ["POST_CLICK_FLOW"])]),
            current_ledger=[{"evidence_type": "POST_CLICK_FLOW", "verification_status": "VERIFIED"}],
        )
        self.assertEqual(plan.minimum_question_set, [])

    def test_question_dedup_uses_answerable_meaning_unit(self):
        plan = plan_hearing(safety_gap("inquiry", ["O4_NEXT"], [("O4_NEXT", ["POST_CLICK_FLOW", "RESPONSE_EXPECTATION"])]))
        self.assertEqual(len(plan.minimum_question_set), 1)
        self.assertEqual(plan.redundant_questions, ["response_expectation"])

    def test_answer_is_candidate_not_production_evidence(self):
        candidate = answer_to_evidence_candidate("risk_and_privacy_policy", "相談後の契約は内容確認後に判断します。", company_id="x", case_id="y")
        self.assertEqual(candidate["verification_status"], "UNVERIFIED_CUSTOMER_INPUT")
        self.assertEqual(candidate["usage_status"], "UNKNOWN")
        self.assertTrue(candidate["safety_recheck_required"])

    def test_vague_answer_stays_unverified(self):
        candidate = answer_to_evidence_candidate("risk_and_privacy_policy", "たぶん勧誘はしません")
        self.assertEqual(candidate["completion_status"], "NEEDS_VERIFICATION")

    def test_document_required_answer_requests_document(self):
        candidate = answer_to_evidence_candidate("ability_proof", "地域No.1です")
        self.assertEqual(candidate["completion_status"], "NEEDS_DOCUMENT")
        self.assertEqual(candidate["next_action"], "NEEDS_DOCUMENT")

    def test_rights_required_answer_requests_rights(self):
        candidate = answer_to_evidence_candidate("visual_rights", "公式サイトの写真です")
        self.assertEqual(candidate["completion_status"], "NEEDS_RIGHTS")
        self.assertEqual(candidate["rights_status"], "UNKNOWN")

    def test_conflict_returns_hold(self):
        candidate = answer_to_evidence_candidate("service_process", {"value": "A", "conflict": True})
        self.assertEqual(candidate["completion_status"], "CONFLICT")
        self.assertEqual(candidate["next_action"], "HOLD")

    def test_unverified_candidate_cannot_be_completed_by_answer_alone(self):
        candidate = answer_to_evidence_candidate("service_process", "内容を確認して説明します。")
        completed = complete_evidence_candidate(
            candidate,
            source="https://example.com/official",
            source_type="customer_statement",
            verification_status="UNVERIFIED_CUSTOMER_INPUT",
            verification_date="2026-09-16",
            rights_status="NOT_APPLICABLE",
            usage_status="UNKNOWN",
        )
        self.assertNotEqual(completed["completion_status"], "COMPLETE")
        self.assertEqual(completed["next_action"], "VERIFY_SOURCE")

    def test_verified_completion_still_requires_safety_selector(self):
        candidate = answer_to_evidence_candidate("service_process", "公式工程を説明します。")
        completed = complete_evidence_candidate(
            candidate,
            source="https://example.com/official",
            source_type="official_company_site",
            verification_status="VERIFIED",
            verification_date="2026-09-16",
            rights_status="NOT_APPLICABLE",
            usage_status="PRODUCTION_ELIGIBLE",
        )
        self.assertEqual(completed["completion_status"], "COMPLETE")
        decision = evaluate_evidence_selection("consultation", ["O3_PROCESS"], [completed])
        self.assertEqual(decision.safety_status, "PASS")

    def test_three_valid_answers_round_trip_through_safety(self):
        cases = [
            ("service_process", "consultation", "O3_PROCESS", "公式工程を説明します。"),
            ("post_click_flow", "inquiry", "O4_NEXT", "内容確認後に日程を案内します。"),
            ("fee_conditions", "quote_request", "O6_COST", "見積確認後に費用が発生します。"),
        ]
        for field_id, goal, objection, answer in cases:
            with self.subTest(field_id=field_id):
                candidate = answer_to_evidence_candidate(field_id, answer)
                completed = complete_evidence_candidate(
                    candidate,
                    source="https://example.com/official",
                    source_type="official_company_site",
                    verification_status="VERIFIED",
                    verification_date="2026-09-16",
                    rights_status="NOT_APPLICABLE",
                    usage_status="PRODUCTION_ELIGIBLE",
                )
                self.assertEqual(completed["completion_status"], "COMPLETE")
                decision = evaluate_evidence_selection(goal, [objection], [completed])
                self.assertEqual(decision.safety_status, "PASS")

    def test_third_party_claim_does_not_pass_with_customer_statement(self):
        candidate = answer_to_evidence_candidate("ability_proof", "昔から地域No.1と言われています")
        completed = complete_evidence_candidate(
            candidate,
            source="customer_statement",
            source_type="customer_statement",
            verification_status="VERIFIED",
            verification_date="2026-09-16",
            rights_status="NOT_APPLICABLE",
            usage_status="PRODUCTION_ELIGIBLE",
            verification_class="THIRD_PARTY_EVIDENCE_REQUIRED",
        )
        self.assertEqual(completed["completion_status"], "NEEDS_DOCUMENT")

    def test_missing_safety_gap_is_not_invented(self):
        plan = plan_hearing(safety_gap("consultation", ["O7_RISK"], [("O7_RISK", ["RISK_POLICY"])]))
        self.assertNotIn("秘密厳守", " ".join(item["question"] for item in plan.minimum_question_set))


if __name__ == "__main__":
    unittest.main()
