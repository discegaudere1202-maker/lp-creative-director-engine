import json
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WIDTHS=[320,360,375,390,430,768,1024,1280,1440]

class CrossDomainValidationRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright=sync_playwright().start(); cls.browser=cls.playwright.chromium.launch(headless=True)
    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.playwright.stop()
    def test_targets_and_ledgers_are_complete(self):
        config=json.loads((ROOT/"config/cross_domain_validation_targets_v1.json").read_text(encoding="utf-8"))
        self.assertEqual({(x["width"],x["height"]) for x in config["viewports"]},{(390,844),(1440,1000)})
        self.assertEqual(len(config["cases"]),2)
        for case in config["cases"]:
            self.assertTrue((ROOT/case["baseline_path"]).is_file())
            self.assertTrue((ROOT/case["variant_path"]).is_file())
            self.assertGreaterEqual(len(case["primary_objections"]),2)
    def test_result_is_traceable_and_keeps_structured_review_boundary(self):
        result=json.loads((ROOT/"data/cross_domain_validation_results_v1.json").read_text(encoding="utf-8"))
        self.assertEqual({case["case_id"] for case in result["cases"]},{"CROSS_P09_SIGNAGE","CROSS_MORIBITO_VISIT"})
        self.assertEqual(result["provenance"]["capture_artifact_id"],10400574684)
        self.assertIn("not causal",result["review_scope"])
        for case in result["cases"]:
            self.assertEqual(len(case["votes"]),4)
            self.assertEqual(set(case["summary"]["axis_win_rate"]),set(result["axes"]))
            self.assertTrue(case["primary_objections"])
    def test_nine_widths_have_no_overflow_and_action_zone_survives(self):
        config=json.loads((ROOT/"config/cross_domain_validation_targets_v1.json").read_text(encoding="utf-8"))
        for case in config["cases"]:
            for path_key in ("baseline_path","variant_path"):
                html=(ROOT/case[path_key]).read_text(encoding="utf-8")
                for width in WIDTHS:
                    with self.subTest(case=case["case_id"],path=path_key,width=width):
                        height=844 if width<=430 else 1000
                        page=self.browser.new_page(viewport={"width":width,"height":height})
                        try:
                            page.set_content(html,wait_until="load")
                            self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"),width)
                            self.assertEqual(page.evaluate("document.documentElement.clientWidth"),width)
                            if width in (390,1440):
                                box=page.locator("footer").bounding_box(); self.assertIsNotNone(box)
                                # P09 is an existing quote-oriented sales sample without a real button;
                                # require the action zone to enter the viewport, while recording its
                                # below-the-fold tail as a research finding rather than hiding it in QA.
                                self.assertLess(box["y"],height+2)
                        finally: page.close()

if __name__=="__main__": unittest.main()
