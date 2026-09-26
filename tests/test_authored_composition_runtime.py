import copy
import unittest

from lp_engine.authored_composition_contract import infer_authored_composition
from lp_engine.authored_composition_runtime import (
    MigrationGuardError,
    consume_composition_plan,
    migration_guard,
)


def fixture():
    truth = lambda value: {"value": value, "confidence": "verified", "sources": ["fixture"]}
    return {
        "company_truth": {
            "category": truth("hair_salon"),
            "name": truth("Example"),
            "offers": [{"id": "receive", "job": "receive"}, {"id": "learn", "job": "learn"}],
            "contact": truth({"channel": "form"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": "choose",
            "tensions": ["choice"],
            "questions": ["price"],
            "risk_sensitivity": "medium",
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": "family-alpha",
            "version": "1",
            "rationale": ["choice clarity"],
            "frozen": True,
        },
        "evidence": {
            "facts": [{
                "id": "process",
                "claim": "verified process",
                "scope": "process",
                "sources": ["official"],
                "confidence": "verified",
                "usable_for_persuasion": True,
            }],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [{
            "role_id": "process-1",
            "role": "process",
            "required_content_class": "human_detail",
            "rights": "licensed",
        }],
    }


class AuthoredCompositionRuntimeTest(unittest.TestCase):
    def test_shadow_consumption_preserves_frozen_family_and_topology(self):
        plan = infer_authored_composition(fixture())
        directives = consume_composition_plan(plan)
        self.assertEqual(directives["mode"], "shadow")
        self.assertEqual(directives["family_id"], plan["family_id"])
        self.assertEqual(directives["topology"], plan["topology"])
        self.assertTrue(directives["renderer_must_not_reinfer"])
        self.assertEqual(len(directives["responsive_authorship"]["widths"]), 9)

    def test_production_mode_consumes_complete_plan_authoritatively(self):
        plan = infer_authored_composition(fixture())
        directives = consume_composition_plan(plan, mode="production")
        self.assertEqual(directives["mode"], "production")
        self.assertEqual(directives["topology"], plan["topology"])
        guard = migration_guard(plan, mode="production")
        self.assertEqual(guard["status"], "PRODUCTION_AUTHORITY")
        self.assertFalse(guard["identity_routing"])
        self.assertFalse(guard["reference_lookup"])
        self.assertFalse(guard["random_variation"])

    def test_migration_guard_rejects_identity_rerouting(self):
        plan = infer_authored_composition(fixture())
        mutated = copy.deepcopy(plan)
        mutated["fit_trace"]["identity_used"] = True
        with self.assertRaises(MigrationGuardError):
            consume_composition_plan(mutated)


if __name__ == "__main__":
    unittest.main()
