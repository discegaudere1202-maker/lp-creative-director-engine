import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
VARIANTS = {
    "P02_ENRICHED": ("examples/prototypes/p02_customer_world_translation_enriched_v1.html", ".cta"),
    "P10_ENRICHED": ("examples/prototypes/p10_customer_state_transition_enriched_v1.html", ".action"),
}

class EnrichedEvidenceRuntimeQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def test_nine_widths_have_no_overflow_and_exact_actions_are_visible(self):
        for variant, (relative_path, action_selector) in VARIANTS.items():
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
                            box = page.locator(action_selector).bounding_box()
                            self.assertIsNotNone(box)
                            self.assertLessEqual(box["y"] + box["height"], height + 2)
                    finally:
                        page.close()

if __name__ == "__main__":
    unittest.main()
