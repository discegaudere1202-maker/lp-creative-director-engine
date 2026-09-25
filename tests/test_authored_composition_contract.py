import copy
import unittest

from lp_engine.authored_composition_contract import (
    ContractError,
    RESPONSIVE_WIDTHS,
    assert_decision_sensitivity,
    assert_identity_invariance,
    assert_no_identity_routing,
    infer_authored_composition,
    plan_digest,
)


def truth(value, confidence="verified"):
    return {"value": value, "confidence": confidence, "sources": ["fixture-source"]}


def fixture():
    return {
        "company_truth": {
            "category": truth("hair_salon"),
            "name": truth("Example Studio"),
            "offers": [
                {"id": "receive", "name": "施術", "job": "receive"},
                {"id": "learn", "name": "スクール", "job": "learn"},
            ],
            "contact": truth({"channel": "form"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": "choose",
            "tensions": ["どれを選ぶか迷う"],
            "questions": ["料金", "流れ"],
            "risk_sensitivity": "medium",
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": "family-alpha",
            "version": "1",
            "rationale": ["choice clarity", "human trust"],
            "frozen": True,
        },
        "evidence": {
            "facts": [
                {
                    "id": "price",
                    "claim": "verified price",
                    "scope": "offer",
                    "sources": ["official"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                },
                {
                    "id": "process",
                    "claim": "verified process",
                    "scope": "process",
                    "sources": ["official"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                },
                {
                    "id": "review",
                    "claim": "verified review",
                    "scope": "person",
                    "sources": ["official"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                },
            ],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [
            {
                "role_id": "process-1",
                "role": "process",
                "required_content_class": "human_scale_detail",
                "rights": "licensed",
            },
            {
                "role_id": "space-1",
                "role": "space",
                "required_content_class": "non_identifying_space",
                "rights": "generated",
            },
        ],
        "offer_conditions": {},
        "renderer_capabilities": ["responsive"],
    }


class AuthoredCompositionContractTest(unittest.TestCase):
    def test_normalized_plan_is_deterministic(self):
        raw = fixture()
        first = infer_authored_composition(raw)
        second = infer_authored_composition(copy.deepcopy(raw))
        self.assertEqual(plan_digest(first), plan_digest(second))
        self.assertEqual(first["responsive_authorship"]["widths"], list(RESPONSIVE_WIDTHS))
        self.assertTrue(first["family_frozen"])
        self.assertFalse(first["fit_trace"]["identity_used"])

    def test_identity_mutation_does_not_change_authorship(self):
        raw = fixture()
        changed = copy.deepcopy(raw)
        assert_identity_invariance(raw, changed)
        assert_no_identity_routing(infer_authored_composition(raw))

    def test_decision_state_mutation_changes_composition(self):
        raw = fixture()
        changed = copy.deepcopy(raw)
        changed["customer_decision_state"]["primary_job"] = "trust"
        changed["customer_decision_state"]["risk_sensitivity"] = "high"
        assert_decision_sensitivity(raw, changed)

    def test_feasibility_never_switches_family(self):
        raw = fixture()
        raw["media_roles"][0]["rights"] = "unknown"
        plan = infer_authored_composition(raw)
        self.assertEqual(plan["family_id"], "family-alpha")
        self.assertTrue(plan["feasibility"]["missing_media_roles"])
        self.assertIn("media_rights_unknown", plan["review_gate"]["reasons"])

    def test_unknown_or_contradictory_truth_fails_closed_to_review(self):
        raw = fixture()
        raw["company_truth"]["name"]["confidence"] = "unknown"
        raw["evidence"]["contradictions"] = ["price differs across sources"]
        plan = infer_authored_composition(raw)
        self.assertEqual(plan["review_gate"]["status"], "HUMAN_REVIEW_REQUIRED")
        self.assertIn("contradictory_evidence", plan["review_gate"]["reasons"])

    def test_invalid_family_or_decision_is_rejected(self):
        raw = fixture()
        raw["creative_family"]["frozen"] = False
        with self.assertRaises(ContractError):
            infer_authored_composition(raw)
        raw = fixture()
        raw["customer_decision_state"]["primary_job"] = "unknown"
        with self.assertRaises(ContractError):
            infer_authored_composition(raw)


if __name__ == "__main__":
    unittest.main()
