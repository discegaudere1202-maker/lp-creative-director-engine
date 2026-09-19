from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_round2e_b_maylynn as base
import run_round2f_b_maylynn as round2f


class Round2FB2CreativeFidelityTest(unittest.TestCase):
    def test_b2_creative_copy_is_the_approved_direction(self):
        snapshot = base.build_maylynn_research_snapshot()
        graph = base.build_evidence_graph(snapshot)
        decisions = base.build_customer_decision_model(snapshot, graph)
        experience = base.build_experience_architecture(snapshot, decisions)
        creative = round2f.apply_b2_creative(base.build_creative_composition(snapshot, experience))
        self.assertEqual(creative["copy"]["V06"]["headline"], ["施工実績と、", "公開レビュー。"])
        self.assertEqual(
            creative["copy"]["V06"]["lead"],
            "公式に掲載されている施工実績と、第三者サイトの公開レビュー。確認できる事実を、判断材料としてまとめます。",
        )
        self.assertEqual(creative["copy"]["V07"]["headline"], ["654色から、", "住まいに合う色を。"])
        self.assertEqual(creative["copy"]["V08"]["headline"], ["保証も、工期も。", "相談する前に。"])

    def test_old_direction_negative_fixtures_fail_closed(self):
        fixtures = round2f.negative_fidelity_fixtures()
        self.assertEqual(fixtures["status"], "PASS")
        self.assertTrue(fixtures["all_expected_failures"])
        self.assertEqual({item["status"] for item in fixtures["fixtures"]}, {"FAIL"})

    def test_rendered_b2_markup_meets_static_contract(self):
        snapshot = base.build_maylynn_research_snapshot()
        graph = base.build_evidence_graph(snapshot)
        decisions = base.build_customer_decision_model(snapshot, graph)
        experience = base.build_experience_architecture(snapshot, decisions)
        creative = round2f.apply_b2_creative(base.build_creative_composition(snapshot, experience))
        media = round2f.load_media()
        before = round2f.IS_B2
        round2f.IS_B2 = True
        try:
            rendered = round2f.render_html(snapshot, experience, creative, media)
        finally:
            round2f.IS_B2 = before
        report = round2f.static_fidelity_report(rendered)
        self.assertEqual(report["status"], "PASS")
        self.assertIn("施工実績と、", rendered)
        self.assertIn("654色から、", rendered)
        self.assertNotIn("warm mineral", rendered.lower())
        self.assertNotIn("<figcaption", rendered.lower())


if __name__ == "__main__":
    unittest.main()
