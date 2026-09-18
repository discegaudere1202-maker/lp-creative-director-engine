from __future__ import annotations

import sys
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lp_engine.company_research_v2 import build_maylynn_research_snapshot
from lp_engine.creative_composition import build_creative_composition
from lp_engine.customer_decision import build_customer_decision_model
from lp_engine.evidence_graph_v2 import build_evidence_graph
from lp_engine.experience_architecture import build_experience_architecture
import run_round2e_b_maylynn as round2e


REQUIRED_P0 = {"A01", "A02", "A03", "A04", "A05", "A07", "A08", "A09", "A10", "A11", "A12", "A13", "A14", "A16"}
REQUIRED_P1 = {"A06", "A15"}


class Round2EBVisualMotionTests(unittest.TestCase):
    def source_ir(self) -> tuple[dict, dict, dict]:
        snapshot = build_maylynn_research_snapshot()
        graph = build_evidence_graph(snapshot)
        decisions = build_customer_decision_model(snapshot, graph)
        experience = build_experience_architecture(snapshot, decisions)
        creative = build_creative_composition(snapshot, experience)
        return snapshot, experience, creative

    def test_media_manifest_and_motion_contract(self) -> None:
        media = round2e.load_media()
        completion = round2e.build_completion_manifest("test-head", media)
        self.assertEqual(set(media), REQUIRED_P0 | REQUIRED_P1)
        self.assertEqual(completion["physical_media_assets"], 14)
        self.assertEqual(completion["distinct_photographs"], 14)
        self.assertEqual(completion["human_visual_moments"], 9)
        self.assertEqual(len(completion["motion"]["implemented"]), 7)
        self.assertGreaterEqual(completion["motion"]["autonomous_count"], 4)
        self.assertEqual(completion["asset_provenance"]["status"], "PASS")
        self.assertEqual(completion["evidence_safety"]["status"], "PASS")
        self.assertEqual(completion["optional_p2_assets"]["A17"]["status"], "OMITTED")
        self.assertTrue(all(view["status"] == "FINAL" for view in completion["viewports"]))
        self.assertEqual([view["viewport"] for view in completion["viewports"]], [f"V0{i}" for i in range(1, 10)])

    def test_renderer_contains_all_visual_contracts(self) -> None:
        snapshot, experience, creative = self.source_ir()
        media = round2e.load_media()
        rendered = round2e.render_html(snapshot, experience, creative, media)
        for asset_id in sorted(media):
            if media[asset_id].get("source_type") == "custom_diagram":
                continue
            self.assertIn(f'data-asset-id="{asset_id}"', rendered)
        for viewport_id in [f"V0{i}" for i in range(1, 10)]:
            self.assertIn(f'data-viewport-id="{viewport_id}"', rendered)
        for marker in ("scope-illustration", "evidence-map", "roof-path", "craft-stage", "material-preview", "prefers-reduced-motion", "参考イメージ", "表面のサインを読む", "工程を追う"):
            self.assertIn(marker, rendered)
        self.assertNotIn("NOT EVIDENCE", rendered)
        self.assertNotIn("FIELD OBSERVATION", rendered)
        self.assertNotIn("nagi_no_mirai", rendered)
        self.assertNotIn("watashi_no_daidokoro", rendered)
        self.assertNotIn("TODO", rendered)

    def test_media_files_are_present_and_optimized(self) -> None:
        media = round2e.load_media()
        for asset_id, item in media.items():
            if not item.get("local_asset_path"):
                continue
            path = ROOT / item["local_asset_path"]
            self.assertTrue(path.exists(), asset_id)
            self.assertLess(path.stat().st_size, 5_000_000, asset_id)
            if path.suffix.lower() in {".jpg", ".jpeg"}:
                with Image.open(path) as image:
                    self.assertGreaterEqual(image.width, 1000)
                    self.assertGreaterEqual(image.height, 600)


if __name__ == "__main__":
    unittest.main()
