import json
import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
VARIANTS = {
    "P10_ACCOUNTABILITY": ("examples/prototypes/p10_customer_state_transition_accountability_v1.html", ".action"),
    "P10_CONTINUITY": ("examples/prototypes/p10_customer_state_transition_continuity_v1.html", ".action"),
    "P10_BUSINESS_MODEL": ("examples/prototypes/p10_customer_state_transition_business_model_v1.html", ".action"),
    "P02_PROCESS": ("examples/prototypes/p02_customer_world_translation_process_v1.html", ".cta"),
    "P02_AUTHORITY": ("examples/prototypes/p02_customer_world_translation_authority_v1.html", ".cta"),
}


class EvidenceSelectionRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_targets_and_variant_files_are_complete(self):
        config = json.loads((ROOT / "config/evidence_selection_capture_targets_v1.json").read_text(encoding="utf-8"))
        self.assertEqual({(v["width"], v["height"]) for v in config["viewports"]}, {(390, 844), (1440, 1000)})
        self.assertEqual({v["prototype_id"] for v in config["variants"]}, set(VARIANTS))
        for item in config["variants"]:
            self.assertTrue((ROOT / item["path"]).is_file())
            self.assertTrue(item["target_objections"])

    def test_nine_widths_have_no_overflow_and_exact_actions_are_visible(self):
        for variant, (relative_path, selector) in VARIANTS.items():
            html = (ROOT / relative_path).read_text(encoding="utf-8")
            for width in WIDTHS:
                with self.subTest(variant=variant, width=width):
                    height = 844 if width <= 430 else 1000
                    page = self.browser.new_page(viewport={"width": width, "height": height})
                    try:
                        page.set_content(html, wait_until="load")
                        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width)
                        self.assertEqual(page.evaluate("document.documentElement.clientWidth"), width)
                        if width in (390, 1440):
                            box = page.locator(selector).bounding_box()
                            self.assertIsNotNone(box)
                            self.assertLessEqual(box["y"] + box["height"], height + 2)
                    finally:
                        page.close()


if __name__ == "__main__":
    unittest.main()
