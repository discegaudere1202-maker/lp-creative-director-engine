import json
from pathlib import Path

import unittest

from lp_engine.production_generation import run_generation


FIXTURE = Path(__file__).parents[1] / "examples/production/andy_motorcycle/andy_motorcycle_production_input_v1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class ProductionGenerationTest(unittest.TestCase):
    def test_production_generation_runs_all_structured_stages(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            result = run_generation(load_fixture(), tmp_path / "andy", generation_id="test-gen-1")

            self.assertTrue(result.production_output_allowed)
            self.assertEqual(result.safety_report["safety_status"], "PASS")
            self.assertEqual(set(result.stage_outputs), {
                "company_understanding", "creative_strategy", "information_architecture", "copy",
                "form_causality_manifest", "creative_genome", "narrative_architecture", "premium_scene_plan", "photo_role_map", "asset_manifest", "art_direction", "design_tokens", "compositions", "render_spec",
            })
            self.assertTrue((tmp_path / "andy" / "index.html").exists())
            manifest = json.loads((tmp_path / "andy" / "generation_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["manual_intervention"], [])
            self.assertEqual(manifest["output_status"], "PRODUCTION_APPROVED")
            self.assertEqual({item["evidence_id"] for item in manifest["evidence_used"]}, {"andy-e-001", "andy-e-002", "andy-e-003"})
            self.assertTrue(all(item["source"] for item in manifest["evidence_used"]))
            html = (tmp_path / "andy" / "index.html").read_text(encoding="utf-8")
            self.assertFalse(any(marker in html for marker in ("無理な勧誘", "秘密厳守", "完全無料", "No.1", "保証", "決めきらなくても")))
            self.assertGreaterEqual(html.count('data-cta-stage="'), 3)
            self.assertEqual({stage for stage in ("discovery", "reassurance", "action") if f'data-cta-stage="{stage}"' in html}, {"discovery", "reassurance", "action"})


    def test_research_mode_is_never_production_approved(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            result = run_generation(load_fixture(), Path(directory) / "research", generation_id="research-1", mode="research")
            self.assertFalse(result.production_output_allowed)
            self.assertEqual(result.manifest["output_status"], "NOT_PRODUCTION_APPROVED")


    def test_third_party_research_evidence_does_not_reach_customer_output(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            result = run_generation(load_fixture(), tmp_path / "andy", generation_id="test-gen-2")
            html = (tmp_path / "andy" / "index.html").read_text(encoding="utf-8")
            manifest = json.loads((tmp_path / "andy" / "generation_manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn("10年", html)
            self.assertNotIn("andy-e-research-001", html)
            self.assertNotIn("andy-e-research-001", {item["evidence_id"] for item in manifest["evidence_used"]})
            self.assertEqual(result.safety_report["hearing_required"], [])


    def test_missing_required_objection_fails_closed(self):
        import tempfile
        raw = load_fixture()
        raw["primary_objections"] = ["O1_ABILITY"]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "HEARING_REQUIRED"):
                run_generation(raw, Path(directory) / "blocked", generation_id="blocked-1")


    def test_malformed_evidence_fails_closed(self):
        import tempfile
        raw = load_fixture()
        raw["evidence_ledger"] = [{"evidence_id": "broken"}]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "INVALID_INPUT|HEARING_REQUIRED"):
                run_generation(raw, Path(directory) / "blocked", generation_id="blocked-2")


    def test_renderer_is_generic_for_another_company(self):
        import tempfile
        raw = load_fixture()
        raw["company_id"] = "north-fork-cycles"
        raw["company"] = {
            **raw["company"],
            "company_name": "North Fork Cycles",
            "industry": "自転車修理",
            "service_category": "自転車の修理相談",
            "location": "札幌市中央区",
            "company_truth": "走行状態を聞いてから、修理の入口を考える地域の窓口。",
            "differentiators": ["状態を伝えるところから相談できる。"],
            "contact_channels": {"href": "mailto:hello@example.test", "email": "hello@example.test"},
        }
        for item in raw["evidence_ledger"]:
            item["company_id"] = raw["company_id"]
            item["case_id"] = "north-fork-cycles-production"
            item["source"] = "https://example.test/official"
        raw["evidence_ledger"][0]["claim"] = "走行状態を聞いてから、修理の入口を考えます。"
        raw["evidence_ledger"][1]["claim"] = "札幌市中央区にあるNorth Fork Cycles。"
        raw["evidence_ledger"][2]["claim"] = "メール hello@example.test"
        with tempfile.TemporaryDirectory() as directory:
            result = run_generation(raw, Path(directory) / "north-fork", generation_id="generic-1")
            html = (Path(directory) / "north-fork" / "index.html").read_text(encoding="utf-8")
            self.assertTrue(result.production_output_allowed)
            self.assertIn("North Fork Cycles", html)
            self.assertNotIn("Andy motorcycle", html)
            self.assertNotIn("andy.motorcycle.co@gmail.com", html)
