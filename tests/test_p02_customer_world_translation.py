import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "examples/prototypes/p02_customer_world_translation_v3.html"
WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
DISALLOWED_SEMANTIC_FRAGMENTS = {
    "ります。",
    "ら。",
    "か。",
    "たい",
    "く、",
    "る？",
}

LINE_TEXT_JS = r"""
(selector) => {
  const results = [];
  document.querySelectorAll(selector).forEach((el) => {
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    const chars = [];
    let node;
    while ((node = walker.nextNode())) {
      for (let i = 0; i < node.data.length; i++) {
        const ch = node.data[i];
        if (ch === "\n") continue;
        const range = document.createRange();
        range.setStart(node, i);
        range.setEnd(node, i + 1);
        const rect = range.getBoundingClientRect();
        if (rect.width > 0 && rect.height > 0) {
          chars.push({ ch, top: Math.round(rect.top * 2) / 2 });
        }
      }
    }
    const lines = [];
    for (const char of chars) {
      let line = lines.find((item) => Math.abs(item.top - char.top) < 1);
      if (!line) {
        line = { top: char.top, text: "" };
        lines.push(line);
      }
      line.text += char.ch;
    }
    results.push(lines.map((line) => line.text.trim()).filter(Boolean));
  });
  return results;
}
"""


class P02CustomerWorldTranslationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = HTML_PATH.read_text(encoding="utf-8")
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def _page(self, width: int):
        height = 844 if width <= 430 else 1000
        page = self.browser.new_page(viewport={"width": width, "height": height})
        page.set_content(self.html, wait_until="load")
        return page

    def test_no_horizontal_overflow_across_nine_widths(self):
        for width in WIDTHS:
            with self.subTest(width=width):
                page = self._page(width)
                try:
                    scroll_width = page.evaluate("document.documentElement.scrollWidth")
                    self.assertLessEqual(scroll_width, width)
                finally:
                    page.close()

    def test_meaning_units_do_not_collapse_into_fragments(self):
        selectors = ["h1 span", "h1 em", ".lead", ".world", ".closure .big"]
        for width in WIDTHS:
            with self.subTest(width=width):
                page = self._page(width)
                try:
                    for selector in selectors:
                        line_groups = page.evaluate(LINE_TEXT_JS, selector)
                        for lines in line_groups:
                            for line in lines:
                                self.assertNotIn(
                                    line,
                                    DISALLOWED_SEMANTIC_FRAGMENTS,
                                    f"semantic fragment at {width}px in {selector}: {line}",
                                )
                                # One- or two-character Japanese line fragments are never acceptable
                                # in the copy-bearing selectors used by this prototype.
                                japanese_chars = [
                                    ch for ch in line
                                    if "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff"
                                ]
                                if len(japanese_chars) <= 2 and japanese_chars:
                                    self.fail(
                                        f"short Japanese fragment at {width}px in {selector}: {line}"
                                    )
                finally:
                    page.close()

    def test_mobile_is_re_art_directed_not_scaled_desktop(self):
        desktop = self._page(1440)
        mobile = self._page(390)
        try:
            self.assertNotEqual(desktop.locator(".labels").evaluate("e => getComputedStyle(e).display"), "none")
            self.assertEqual(mobile.locator(".labels").evaluate("e => getComputedStyle(e).display"), "none")

            self.assertNotEqual(desktop.locator(".logic").evaluate("e => getComputedStyle(e).display"), "none")
            self.assertEqual(mobile.locator(".logic").evaluate("e => getComputedStyle(e).display"), "none")

            self.assertEqual(desktop.locator(".row").first.evaluate("e => getComputedStyle(e).display"), "grid")
            self.assertEqual(mobile.locator(".row").first.evaluate("e => getComputedStyle(e).display"), "block")
        finally:
            desktop.close()
            mobile.close()

    def test_company_truth_drives_visible_translation_form(self):
        page = self._page(1440)
        try:
            text = page.locator("body").inner_text()
            self.assertIn("20年 / 300社以上の支援経験", text)
            self.assertIn("36協定・時間外労働", text)
            self.assertIn("残業、このままで", text)
            self.assertIn("就業規則・服務規律", text)
            self.assertIn("社内のルールを", text)
            self.assertIn("制度名ではなく、いまの状況を。", text.replace("\n", ""))
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
