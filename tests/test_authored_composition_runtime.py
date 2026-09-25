import copy
import unittest

from lp_engine.authored_composition_contract import infer_authored_composition
from lp_engine.authored_composition_runtime import (
    MigrationGuardError,
    consume_composition_plan,
    migration_guard,
)
from tests.test_authored_composition_contract import fixture


class AuthoredCompositionRuntimeTest(unittest.TestCase):
    def test_shadow_consumption_preserves_frozen_family_and_topology(self):
        plan = infer_authored_composition(fixture())
        directives = consume_composition_plan(plan)
        self.assertEqual(directives["mode"], "shadow")
        self.assertEqual(directives["family_id"], plan["family_id"])
        self.assertEqual(directives["topology"], plan["topology"])
        self.assertTrue(directives["renderer_must_not_reinfer"])
        self.assertEqual(len(directives["responsive_authorship"]["widths"]), 9)

    def test_migration_guard_is_fail_closed_for_production_mode(self):
        plan = infer_authored_composition(fixture())
        with self.assertRaises(MigrationGuardError):
            consume_composition_plan(plan, mode="production")
        guard = migration_guard(plan)
        self.assertEqual(guard["status"], "SHADOW_ONLY")
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
