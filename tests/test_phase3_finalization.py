import unittest

from lp_engine.evidence_safety import evaluate_evidence_selection
from lp_engine.finalization import (
    analyze_evidence_gaps,
    build_finalization_spec,
    build_hearing_plan,
    detect_answer_conflicts,
    ingest_hearing_answers,
    promote_answer_candidate,
    recheck_safety,
)


def gap_report():
    safety = evaluate_evidence_selection("purchase", ["O3_PROCESS", "O6_COST"], [
        {
            "evidence_id": "base-process",
            "company_id": "test",
            "case_id": "test",
            "evidence_type": "SERVICE_SCOPE",
            "evidence_strength": "E3_OPERATIONAL",
            "target_objections": ["O3_PROCESS"],
            "claim": "用途と予算から提案します。",
            "source": "https://example.com",
            "source_type": "official_company_site",
            "verification_status": "VERIFIED",
            "verification_date": "2026-09-16",
            "usage_status": "PRODUCTION_ELIGIBLE",
            "placement_candidates": ["MIDDLE"],
            "rights_status": "NOT_APPLICABLE",
            "hearing_required": False,
            "blocking_status": "NON_BLOCKING",
            "notes": "test",
        }
    ])
    return safety, analyze_evidence_gaps(safety, [
        {
            "gap_id": "process-detail",
            "required_field": "service_process",
            "required_evidence_types": ["PURCHASE_PROCESS"],
            "target_objections": ["O3_PROCESS"],
            "affected_section": "process",
            "blocking_level": "SECTION_BLOCKING",
            "priority": "P1",
            "verification_class": "SELF_DECLARABLE",
        },
        {
            "gap_id": "fee",
            "required_field": "fee_conditions",
            "required_evidence_types": ["FEE_CONDITION"],
            "target_objections": ["O6_COST"],
            "affected_section": "price",
            "blocking_level": "SECTION_BLOCKING",
            "priority": "P1",
            "verification_class": "DOCUMENT_REQUIRED",
        },
    ], current_ledger=[])


class Phase3FinalizationTest(unittest.TestCase):
    def test_gap_analysis_does_not_treat_related_evidence_as_sufficient(self):
        safety, gaps = gap_report()
        self.assertEqual(gaps["missing_evidence_count"], 2)
        self.assertEqual({x["gap_id"] for x in gaps["missing_evidence"]}, {"process-detail", "fee"})

    def test_minimum_questions_are_value_ranked_and_natural(self):
        _, gaps = gap_report()
        plan = build_hearing_plan(gaps)
        self.assertEqual(plan["question_count"], 2)
        self.assertTrue(plan["minimum_question_set"][0]["expected_information_gain"] >= 0.8)
        self.assertTrue(all("O3_" not in q["question"] and "O6_" not in q["question"] for q in plan["minimum_question_set"]))

    def test_synthetic_answer_is_not_production_until_completion(self):
        _, gaps = gap_report()
        plan = build_hearing_plan(gaps)
        candidates = ingest_hearing_answers(plan, [
            {"question_id": "Q-service_process", "answer": "内容を確認し、予算を聞いて提案します。", "simulation_mode": True},
            {"question_id": "Q-fee_conditions", "answer": "3,300円から。注文確認後に確定します。", "simulation_mode": True},
        ], company_id="test", case_id="test", mode="simulation")
        self.assertTrue(all(x["verification_status"] == "UNVERIFIED_CUSTOMER_INPUT" for x in candidates))
        self.assertTrue(all(x["simulation_mode"] for x in candidates))

    def test_valid_round_trip_rechecks_canonical_safety(self):
        _, gaps = gap_report()
        plan = build_hearing_plan(gaps)
        candidates = ingest_hearing_answers(plan, [
            {"question_id": "Q-service_process", "answer": "内容を確認し、予算を聞いて提案します。", "simulation_mode": True},
            {"question_id": "Q-fee_conditions", "answer": "3,300円から。注文確認後に確定します。", "simulation_mode": True},
        ], company_id="test", case_id="test", mode="simulation")
        completed = []
        for c in candidates:
            completed.append(promote_answer_candidate(
                c,
                source="synthetic://test/answer",
                source_type="synthetic_fixture",
                verification_status="VERIFIED",
                verification_date="2026-09-16",
                rights_status="NOT_APPLICABLE",
                usage_status="PRODUCTION_ELIGIBLE",
                verification_class="SELF_DECLARABLE",
            ))
        self.assertTrue(all(x["completion_status"] == "COMPLETE" for x in completed))
        final_input = {"conversion_goal": "purchase", "primary_objections": ["O3_PROCESS", "O6_COST"], "requested_claims": []}
        safety = recheck_safety(final_input, completed, mode="test")
        self.assertEqual(safety["safety_status"], "PASS")
        spec = build_finalization_spec({"eligible_evidence": []}, safety, gaps, completed_candidates=completed)
        self.assertEqual(spec["status"], "READY_FOR_FINALIZATION")
        self.assertEqual(spec["unlocked_sections"], ["price", "process"])

    def test_unverified_and_rights_unknown_do_not_complete(self):
        _, gaps = gap_report()
        plan = build_hearing_plan(gaps)
        candidate = ingest_hearing_answers(plan, [{"question_id": "Q-fee_conditions", "answer": "だいたい無料です", "simulation_mode": True}], company_id="test", case_id="test", mode="simulation")[0]
        incomplete = promote_answer_candidate(
            candidate,
            source="synthetic://test/answer",
            source_type="synthetic_fixture",
            verification_status="UNVERIFIED_CUSTOMER_INPUT",
            verification_date="2026-09-16",
            rights_status="UNKNOWN",
            usage_status="UNKNOWN",
            verification_class="DOCUMENT_REQUIRED",
        )
        self.assertNotEqual(incomplete["completion_status"], "COMPLETE")

    def test_conflict_is_hold_not_newer_answer_wins(self):
        conflicts = detect_answer_conflicts(
            [{"answer_id": "a1", "evidence_type": "SERVICE_SCOPE", "claim": "別の内容"}],
            [{"evidence_type": "SERVICE_SCOPE", "claim": "既存の内容"}],
        )
        self.assertEqual(conflicts[0]["status"], "CONFLICT")
        self.assertEqual(conflicts[0]["next_action"], "HOLD")

    def test_synthetic_answer_cannot_enter_production_intake(self):
        _, gaps = gap_report()
        plan = build_hearing_plan(gaps)
        with self.assertRaises(ValueError):
            ingest_hearing_answers(plan, [{"question_id": "Q-service_process", "answer": "内容", "simulation_mode": True}], company_id="test", case_id="test", mode="production")

    def test_overclaim_is_rejected_even_with_completion_metadata(self):
        _, gaps = gap_report()
        plan = build_hearing_plan(gaps)
        candidate = ingest_hearing_answers(plan, [{"question_id": "Q-service_process", "answer": "絶対に治ります", "simulation_mode": True}], company_id="test", case_id="test", mode="simulation")[0]
        rejected = promote_answer_candidate(
            candidate,
            source="synthetic://test/answer",
            source_type="synthetic_fixture",
            verification_status="VERIFIED",
            verification_date="2026-09-16",
            rights_status="NOT_APPLICABLE",
            usage_status="PRODUCTION_ELIGIBLE",
            verification_class="SELF_DECLARABLE",
        )
        self.assertEqual(rejected["completion_status"], "REJECTED")
        self.assertEqual(rejected["next_action"], "HOLD")


if __name__ == "__main__":
    unittest.main()
