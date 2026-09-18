import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts.run_round1e_b_generation import CASES, build_input
from lp_engine.production_generation import build_design_tokens, run_generation


class Round1NCreativeCorrectionTest(unittest.TestCase):
    def _generate(self, company: str):
        directory = tempfile.TemporaryDirectory()
        result = run_generation(build_input(company, CASES[company]), Path(directory.name) / company, mode="research", generation_id=f"test-round1n-{company}")
        folder = Path(directory.name) / company
        return directory, result, folder

    def test_profile_font_radius_and_cadence_are_consumed(self):
        field = build_design_tokens({"layout_profile": "field_ledger", "color_logic": {}})
        care = build_design_tokens({"layout_profile": "care_rhythm", "color_logic": {}})
        studio = build_design_tokens({"layout_profile": "studio_invitation", "color_logic": {}})
        self.assertNotEqual(field["typography"]["display"], care["typography"]["display"])
        self.assertNotEqual(care["radius"]["media"], studio["radius"]["media"])
        self.assertNotEqual(field["rhythm"]["cadence"], care["rhythm"]["cadence"])
        self.assertNotEqual(field["grid"], studio["grid"])

    def test_three_truth_patterns_produce_distinct_profile_tokens(self):
        generated = []
        for company in CASES:
            directory, result, folder = self._generate(company)
            self.addCleanup(directory.cleanup)
            generated.append(json.loads((folder / "design_tokens.json").read_text(encoding="utf-8")))
            self.assertTrue(result.manifest["manual_intervention"] == [])
        self.assertEqual(len({row["profile_id"] for row in generated}), 3)
        self.assertEqual(len({row["ending"]["variant"] for row in generated}), 3)

    def test_final_major_copy_and_generic_next_ui(self):
        expected = {
            "maylynn_paint": "住まいの「気になる」から、話せる。",
            "nagi_no_mirai": "静けさに、頭を預ける。",
            "watashi_no_daidokoro": "ストウブを囲んで、手を動かす。",
        }
        for company, headline in expected.items():
            directory, result, folder = self._generate(company)
            self.addCleanup(directory.cleanup)
            html = (folder / "index.html").read_text(encoding="utf-8")
            self.assertIn(headline, re.sub(r"<[^>]+>", "", html))
            self.assertNotIn("次の案内", html)
            self.assertNotIn('data-cta-stage="action"', html)

    def test_human_peak_presentation_is_profile_derived(self):
        expected = {"field_ledger": 2, "care_rhythm": 2, "studio_invitation": 3}
        for company, count in (("maylynn_paint", 2), ("nagi_no_mirai", 2), ("watashi_no_daidokoro", 3)):
            directory, result, folder = self._generate(company)
            self.addCleanup(directory.cleanup)
            translation = json.loads((folder / "premium_human_translation.json").read_text(encoding="utf-8"))
            plan = translation["human_peak_presentation"]
            profile = translation["art_direction_token_profile"]["profile_id"]
            self.assertEqual(plan["status"], "PASS")
            self.assertEqual(plan["selected_count"], expected[profile])
            self.assertEqual(len(plan["selected"]), count)
            self.assertTrue(plan["machine_peak_scoring_unchanged"])


if __name__ == "__main__":
    unittest.main()
