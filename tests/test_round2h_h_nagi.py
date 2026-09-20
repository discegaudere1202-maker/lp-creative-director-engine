from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("round2h_h_nagi", ROOT / "scripts" / "run_round2h_h_nagi.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class Round2HHContractTests(unittest.TestCase):
    def test_fact_ssot_propagates_to_public_guide_and_faq(self) -> None:
        html = MODULE.build_html_h({key: {"output": f"assets/{key}.png"} for key in MODULE.F.ASSETS})
        self.assertIn("60分 8,800円 / 90分 12,100円", html)
        self.assertIn("1日講座 33,000円、約5時間", html)
        self.assertIn("ヒアリング → 施術 → 余韻の確認", html)
        self.assertNotIn("料金を相談時に確認", html)
        self.assertNotIn("施術・講座の時間を事前に確認", html)

    def test_every_derived_copy_has_trace(self) -> None:
        report = MODULE.provisional_propagation_gate(MODULE.FACTS, MODULE.DERIVED_COPY)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(all(row["source_fact_keys"] for row in report["records"]))

    def test_mobile_priority_contract_is_source_level(self) -> None:
        html = MODULE.build_html_h({key: {"output": f"assets/{key}.png"} for key in MODULE.F.ASSETS})
        self.assertIn("body.in-entry .sticky-cta", html)
        self.assertIn("anchor-active .header", html)
        self.assertIn("scroll-margin-top", html)
        self.assertIn("cta_entry_interference_count", MODULE.__file__ and (ROOT / "scripts" / "run_round2h_h_nagi.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
