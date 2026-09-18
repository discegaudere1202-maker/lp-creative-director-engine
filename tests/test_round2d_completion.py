import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lp_engine.company_research_v2 import build_maylynn_research_snapshot
from lp_engine.customer_decision import build_customer_decision_model
from lp_engine.evidence_graph_v2 import build_evidence_graph
from lp_engine.experience_architecture import build_experience_architecture
from lp_engine.creative_composition import build_creative_composition
from run_round2d_maylynn import completion_manifest, enhance_html
import run_round2c_maylynn as prototype


class Round2DCompletionTest(unittest.TestCase):
    def setUp(self):
        snapshot = build_maylynn_research_snapshot()
        graph = build_evidence_graph(snapshot)
        decisions = build_customer_decision_model(snapshot, graph)
        experience = build_experience_architecture(snapshot, decisions)
        creative = build_creative_composition(snapshot, experience)
        self.assets = prototype.load_assets()
        self.html = enhance_html(prototype.render_html(snapshot, experience, creative, self.assets), self.assets)
        self.manifest = completion_manifest("round2d-test-head", self.assets)

    def test_all_nine_viewports_are_final(self):
        self.assertEqual(self.manifest["completion_status"], "ALL_FINAL")
        self.assertEqual(len(self.manifest["viewports"]), 9)
        self.assertTrue(all(item["state"] == "FINAL" for item in self.manifest["viewports"]))

    def test_visual_moments_images_and_motion_have_distinct_roles(self):
        self.assertGreaterEqual(self.manifest["visual_moments"]["count"], 6)
        self.assertEqual(self.manifest["image_provenance"]["count"], 3)
        self.assertEqual(self.manifest["motion"]["count"], 6)
        self.assertTrue(self.manifest["motion"]["reduced_motion_required"])
        self.assertFalse(self.manifest["motion"]["scroll_hijack"])

    def test_html_contains_completion_layer_and_no_unresolved_copy(self):
        required = (
            'data-round="2D"',
            "inspection-target",
            "warning-detail",
            "scope-path",
            "scan-line",
            "process-steps",
            "source-timeline",
            "material-preview-surface",
            "action-route",
            "prefers-reduced-motion:reduce",
        )
        for token in required:
            self.assertIn(token, self.html)
        self.assertNotIn("TODO", self.html)
        self.assertNotIn("placeholder", self.html.lower())

    def test_mobile_and_safety_contracts_are_explicit(self):
        self.assertEqual(self.manifest["mobile"]["status"], "PASS")
        self.assertTrue(self.manifest["mobile"]["recomposed"])
        self.assertEqual(self.manifest["mobile"]["overflow_px"], 0)
        self.assertEqual(self.manifest["safety"]["unsupported_claims"], 0)
        self.assertEqual(self.manifest["safety"]["actual_project_image_claims"], 0)
        self.assertIn("maylynn_paint", self.html)
        self.assertNotIn("nagi_no_mirai", self.html)
        self.assertNotIn("watashi_no_daidokoro", self.html)


if __name__ == "__main__":
    unittest.main()
