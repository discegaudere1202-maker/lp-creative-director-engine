import unittest

from lp_engine.form_causality import FormDecision, evaluate_form_causality


class FormCausalityTest(unittest.TestCase):
    def test_required_frames_and_mobile_pass(self):
        decisions = [
            FormDecision(
                id="hero-translation",
                decision_type="motion",
                description="Technical terms reorganize into plain-language problem statements.",
                company_truth_keys=["explanation_policy"],
                causal_explanation="The owner's confirmed promise of understandable explanation directly causes the translation motion.",
                frame_id="hero",
                mobile_manifestation="On mobile the same transformation runs vertically rather than side by side.",
            ),
            FormDecision(
                id="mid-accumulation",
                decision_type="composition",
                description="Many consultation fragments accumulate into a small set of recognizable issues.",
                company_truth_keys=["supported_companies"],
                causal_explanation="The confirmed experience across many companies causes an accumulation-to-clarity composition rather than a giant number alone.",
                frame_id="mid-peak",
                mobile_manifestation="Fragments stack in one column before resolving into grouped issues.",
            ),
        ]
        result = evaluate_form_causality(
            decisions,
            {"explanation_policy", "supported_companies"},
            required_frames=["hero", "mid-peak"],
            require_mobile_manifestation=True,
        )
        self.assertTrue(result["premium_ready"])
        self.assertEqual(result["status"], "PASS")

    def test_name_swappable_form_is_not_premium_ready(self):
        decision = FormDecision(
            id="generic-number",
            decision_type="typography",
            description="A large experience number is placed in the center of the frame.",
            company_truth_keys=["supported_companies"],
            causal_explanation="The support count is visually emphasized as a large number in the evidence frame.",
            frame_id="hero",
            mobile_manifestation="The same large number is centered on mobile.",
            transferable_by_name_swap=True,
        )
        result = evaluate_form_causality(
            [decision],
            {"supported_companies"},
            minimum_causal_decisions=1,
            required_frames=["hero"],
            require_mobile_manifestation=True,
        )
        self.assertFalse(result["premium_ready"])
        self.assertIn("hero", result["missing_frames"])

    def test_missing_mobile_manifestation_reviews(self):
        decision = FormDecision(
            id="hero-doc",
            decision_type="composition",
            description="A technical document is annotated into understandable language.",
            company_truth_keys=["explanation_policy"],
            causal_explanation="The owner's explanation policy causes the document annotation composition.",
            frame_id="hero",
        )
        result = evaluate_form_causality(
            [decision],
            {"explanation_policy"},
            minimum_causal_decisions=1,
            required_frames=["hero"],
            require_mobile_manifestation=True,
        )
        self.assertFalse(result["premium_ready"])


if __name__ == "__main__":
    unittest.main()
