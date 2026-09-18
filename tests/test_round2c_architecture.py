import unittest

from lp_engine.company_research_v2 import build_maylynn_research_snapshot, validate_research_snapshot
from lp_engine.creative_composition import build_creative_composition
from lp_engine.customer_decision import build_customer_decision_model
from lp_engine.evidence_graph_v2 import build_evidence_graph
from lp_engine.experience_architecture import build_experience_architecture
from lp_engine.quality_review_contract_v2 import build_quality_review_contract


class Round2CArchitectureTest(unittest.TestCase):
    def setUp(self):
        self.snapshot = build_maylynn_research_snapshot()
        self.graph = build_evidence_graph(self.snapshot)
        self.decisions = build_customer_decision_model(self.snapshot, self.graph)
        self.experience = build_experience_architecture(self.snapshot, self.decisions)
        self.creative = build_creative_composition(self.snapshot, self.experience)
        self.contract = build_quality_review_contract(
            self.snapshot, self.graph, self.decisions, self.experience, self.creative
        )

    def test_research_is_source_locked_and_preserves_address_conflict(self):
        validation = validate_research_snapshot(self.snapshot)
        self.assertEqual(validation["status"], "PASS")
        self.assertEqual(self.snapshot["company_id"], "maylynn_paint")
        self.assertEqual(self.snapshot["primary_display_policy"], "小山市を中心に周辺エリア。競合する正確な住所は表示しない。")
        self.assertEqual(self.snapshot["conflicts"][0]["status"], "CONFLICTED")
        self.assertEqual(self.snapshot["conflicts"][0]["fact_ids"], ["address.official_old", "address.official_new"])

    def test_evidence_graph_blocks_conflicted_nodes_from_eligible_edges(self):
        conflicted = {node["node_id"]: node for node in self.graph["nodes"] if node["status"] == "CONFLICTED"}
        self.assertEqual(set(conflicted), {"address.official_old", "address.official_new"})
        self.assertTrue(all(not edge["eligible"] for edge in self.graph["edges"] if edge["from"] in conflicted))
        self.assertIn("CONFLICTED facts never enter Hero or Main proof", self.graph["conflict_policy"])

    def test_decision_model_covers_action_and_unknowns(self):
        self.assertEqual(self.decisions["decision_count"], 10)
        by_id = {row["decision_id"]: row for row in self.decisions["decisions"]}
        self.assertEqual(by_id["D10"]["evidence_ids"], ["action.phone", "action.hours", "action.form"])
        self.assertTrue(by_id["D08"]["unknown"])
        self.assertTrue(by_id["D08"]["hearing_needed"])
        self.assertFalse(by_id["D08"]["hero_eligible"])

    def test_experience_is_decision_first_and_one_idea_per_viewport(self):
        self.assertEqual(self.experience["viewport_count"], 9)
        self.assertEqual(len(self.experience["sections"]), 9)
        self.assertTrue(all(section["user_questions"] for section in self.experience["sections"]))
        self.assertTrue(all(section["complete_idea"] for section in self.experience["sections"]))

    def test_creative_composition_has_exact_copy_motion_and_mobile_contracts(self):
        copy = self.creative["copy"]
        self.assertEqual(copy["V01"]["headline"], ["塗る前に、", "まず状態を見る。"])
        self.assertEqual(copy["V09"]["phone"], "0800-8080-886")
        self.assertEqual(len(self.creative["motion"]), 6)
        self.assertTrue(all(item["reduced_motion"] for item in self.creative["motion"]))
        self.assertEqual(self.creative["mobile"]["primary_width"], 390)
        self.assertEqual(self.creative["mobile"]["technical_widths"], [320, 360, 375, 430])
        self.assertGreaterEqual(len(self.creative["microcraft"]["decisions"]), 20)

    def test_quality_contract_passes_without_final_yen_gate(self):
        self.assertEqual(self.contract["status"], "PASS")
        self.assertTrue(all(self.contract["checks"].values()))
        self.assertEqual(self.contract["review_stage"], "MACHINE_TECHNICAL_VERIFICATION_BEFORE_SHUN")
        self.assertEqual(self.contract["one_million_yen_pass"], "NOT_ASSESSED")
        self.assertEqual(self.contract["human_final_judge"], "Shun")


if __name__ == "__main__":
    unittest.main()
