from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lp_engine.company_research_v2 import build_maylynn_research_snapshot  # noqa: E402
from lp_engine.creative_composition import build_creative_composition  # noqa: E402
from lp_engine.customer_decision import build_customer_decision_model  # noqa: E402
from lp_engine.evidence_graph_v2 import build_evidence_graph  # noqa: E402
from lp_engine.experience_architecture import build_experience_architecture  # noqa: E402
import run_round2f_b_maylynn as round2f  # noqa: E402


class Round2FBMaylynnPremiumTests(unittest.TestCase):
    def source_ir(self) -> tuple[dict, dict, dict]:
        snapshot = build_maylynn_research_snapshot()
        graph = build_evidence_graph(snapshot)
        decisions = build_customer_decision_model(snapshot, graph)
        experience = build_experience_architecture(snapshot, decisions)
        creative = build_creative_composition(snapshot, experience)
        return snapshot, experience, creative

    def test_round2f_assets_and_font_licenses_are_present(self) -> None:
        media = round2f.load_media()
        self.assertIn("A10", media)
        self.assertIn("A14", media)
        for asset_id in ("A10", "A14"):
            path = ROOT / media[asset_id]["local_asset_path"]
            self.assertTrue(path.is_file(), asset_id)
            self.assertLess(path.stat().st_size, 5_000_000, asset_id)
        for filename in (
            "ZenKakuGothicNew-600.ttf",
            "NotoSansJP-Variable.ttf",
            "InterTight-Variable.ttf",
            "IBMPlexMono-400.ttf",
        ):
            path = ROOT / "assets" / "fonts" / "round2f" / filename
            self.assertTrue(path.is_file(), filename)
            self.assertGreater(path.stat().st_size, 1000, filename)
        licenses = ROOT / "assets" / "fonts" / "round2f" / "licenses"
        self.assertEqual(len(list(licenses.glob("OFL-*.txt"))), 4)

    def test_renderer_public_contract_is_round2f_and_internal_labels_are_hidden(self) -> None:
        snapshot, experience, creative = self.source_ir()
        rendered = round2f.render_html(snapshot, experience, creative, round2f.load_media())
        self.assertIn('data-round="2F-B"', rendered)
        self.assertIn("塗る前に、まず状態を見る。", rendered)
        self.assertIn('data-viewport-id="V01"', rendered)
        self.assertIn('data-viewport-id="V09"', rendered)
        self.assertIn("a10_roller_application.png", rendered)
        self.assertIn("a14_paint_film_grazing_light.png", rendered)
        for family, filename in (
            ("Zen Kaku Gothic New", "ZenKakuGothicNew-600.ttf"),
            ("Noto Sans JP", "NotoSansJP-Variable.ttf"),
            ("Inter Tight", "InterTight-Variable.ttf"),
            ("IBM Plex Mono", "IBMPlexMono-400.ttf"),
        ):
            self.assertIn(f'font-family:"{family}"', rendered)
            self.assertIn(filename, rendered)
        for forbidden in (
            "HERO / PROPOSITION",
            "SERVICE SCOPE",
            "INSPECTION & QUANTIFIED PUBLIC PROOF",
            "PAINT / COLOR DECISION SUPPORT",
            "VERIFIED CONTACT / CLOSE",
            "PUBLIC EVIDENCE",
            "nagi_no_mirai",
            "watashi_no_daidokoro",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_self_contained_html_inlines_font_and_media_dependencies(self) -> None:
        snapshot, experience, creative = self.source_ir()
        media = round2f.load_media()
        rendered = round2f.render_html(snapshot, experience, creative, media)
        self_contained = round2f.self_contained_html(rendered, media)
        self.assertIn("data-round=\"2F-B\"", self_contained)
        self.assertIn("data:font/ttf;base64,", self_contained)
        self.assertIn("data:image/", self_contained)
        self.assertNotIn("/assets/photography/", self_contained)
        self.assertNotIn("/assets/fonts/", self_contained)


if __name__ == "__main__":
    unittest.main()
