from __future__ import annotations

import unittest

from lp_engine.ceiling_director import CEILING_CONTRACT_FIELDS, validate_ceiling_director_contract


class CeilingDirectorContractTests(unittest.TestCase):
    def test_generic_contract_requires_all_decision_fields(self) -> None:
        contract = {field: [field] for field in CEILING_CONTRACT_FIELDS}
        report = validate_ceiling_director_contract(contract)
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["company_specific_defaults"])

    def test_missing_field_fails_closed(self) -> None:
        report = validate_ceiling_director_contract({field: [field] for field in CEILING_CONTRACT_FIELDS[:-1]})
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("missing:cross_lp_similarity_signature", report["errors"])


if __name__ == "__main__":
    unittest.main()
