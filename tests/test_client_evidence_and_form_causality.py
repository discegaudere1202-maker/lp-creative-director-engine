import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.client_evidence import (
    ClientEvidenceSlot,
    EvidenceSlotKind,
    PhotoDirection,
    validate_slot,
    interview_questions,
)
from lp_engine.form_causality import FormDecision, evaluate_form_causality


class ClientEvidenceTest(unittest.TestCase):
    def test_visual_slot_requires_photo_direction(self):
        slot = ClientEvidenceSlot(
            id="hero",
            kind=EvidenceSlotKind.HERO_REALITY,
            section_id="hero",
            required_for_delivery=True,
            purpose="real owner/place evidence",
            sales_state_fallback="fact-driven visual",
        )
        issues = validate_slot(slot)
        self.assertTrue(any("photo_direction" in x for x in issues))

    def test_interview_is_generated_from_slots(self):
        slot = ClientEvidenceSlot(
            id="hero-storefront",
            kind=EvidenceSlotKind.HERO_REALITY,
            section_id="hero",
            required_for_delivery=True,
            purpose="show the real storefront",
            sales_state_fallback="verified process visual",
            question_prompt="店舗外観を撮影してください",
            accepted_formats=["image/jpeg"],
            photo_direction=PhotoDirection(
                purpose="sign + entrance evidence",
                focal_subject="sign",
                focal_relationship="sign + entrance",
                minimum_resolution_px=1800,
            ),
        )
        questions = interview_questions([slot])
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0]["slot_id"], "hero-storefront")
        self.assertEqual(questions[0]["photo_direction"]["focal_subject"], "sign")


class FormCausalityTest(unittest.TestCase):
    def test_requires_two_confirmed_causal_decisions(self):
        decisions = [
            FormDecision(
                id="translation-weight",
                decision_type="typography",
                description="technical terms visually resolve into plain-language labels",
                company_truth_keys=["explanation_policy"],
                causal_explanation="The representative explicitly values explanations anyone can understand.",
            ),
            FormDecision(
                id="case-fragments",
                decision_type="composition",
                description="many issue fragments converge into a small set of understandable categories",
                company_truth_keys=["supported_companies"],
                causal_explanation="300+ company experience is represented as accumulated individual issues rather than a stat card.",
            ),
        ]
        result = evaluate_form_causality(
            decisions,
            {"explanation_policy", "supported_companies"},
        )
        self.assertEqual(result["status"], "PASS")

    def test_generic_premium_decision_does_not_pass(self):
        decisions = [
            FormDecision(
                id="big-serif",
                decision_type="typography",
                description="large serif headline because it looks premium",
                company_truth_keys=[],
                causal_explanation="",
            )
        ]
        result = evaluate_form_causality(decisions, set())
        self.assertEqual(result["status"], "REVIEW")


if __name__ == "__main__":
    unittest.main()
