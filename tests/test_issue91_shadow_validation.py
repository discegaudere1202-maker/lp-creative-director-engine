import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_issue91_shadow_validation import run_validation


class Issue91ShadowValidationTest(unittest.TestCase):
    def test_current_domain_matrix_produces_machine_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_validation(directory)
            self.assertEqual(result["overall_technical_status"], "PASS")
            self.assertEqual(result["identity_invariance"], "PASS")
            self.assertEqual(result["decision_sensitivity"], "PASS")
            self.assertEqual(result["same_family_material_difference"], "PASS")
            self.assertTrue(result["contradiction_fail_closed"])
            self.assertTrue(result["feasibility_family_preserved"])
            self.assertEqual(result["reference_regression_guard"], "PASS")
            self.assertEqual(result["shadow_consumer"], "PASS")
            evidence = json.loads(
                (Path(directory) / "issue91_shadow_validation.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(evidence["screenshot_validation"], "DOWNSTREAM_NOT_APPLICABLE_TO_SHADOW_OUTPUT")
            self.assertEqual(evidence["human_visible_template_resemblance"], "NOT_SELF_DECLARED")
            self.assertEqual(len(evidence["responsive_widths"]), 9)


if __name__ == "__main__":
    unittest.main()
