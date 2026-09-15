import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "examples/prototypes/p09_price_transparency_v1.html"
WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
DISALLOWED_SEMANTIC_FRAGMENTS = {
    "は、", "で、", "を。", "る。", "か。", "する。", "れる。"
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


class P09PriceTransparencyTest(unittest.TestCase):
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

    def test_prose_meaning_units_do_not_collapse_into_fragments(self):
        # Category labels such as "仕様" are intentionally short nouns. They follow
        # a label rule, not the prose/headline rule. This selector list therefore
        # contains only copy-bearing prose/headline elements.
        selectors = ["h1 span", ".lead", ".factor p", ".closing .small"]
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

    def test_factor_labels_remain_single_semantic_tokens(self):
        expected = ["サイズ", "仕様", "設置場所"]
        for width in WIDTHS:
            with self.subTest(width=width):
                page = self._page(width)
                try:
                    labels = page.locator(".factor strong").all_inner_texts()
                    self.assertEqual(labels, expected)
                    wraps = page.evaluate(LINE_TEXT_JS, ".factor strong")
                    self.assertTrue(all(len(lines) == 1 for lines in wraps))
                finally:
                    page.close()

    def test_mobile_re_art_direction_changes_structure(self):
        desktop = self._page(1440)
        mobile = self._page(390)
        try:
            self.assertEqual(desktop.locator(".price-body").evaluate("e => getComputedStyle(e).display"), "grid")
            self.assertEqual(mobile.locator(".price-body").evaluate("e => getComputedStyle(e).display"), "block")
            self.assertNotEqual(desktop.locator(".formula-head").evaluate("e => getComputedStyle(e).display"), "none")
            self.assertEqual(mobile.locator(".formula-head").evaluate("e => getComputedStyle(e).display"), "none")
            self.assertEqual(desktop.locator(".mobile-summary").evaluate("e => getComputedStyle(e).display"), "none")
            self.assertNotEqual(mobile.locator(".mobile-summary").evaluate("e => getComputedStyle(e).display"), "none")
        finally:
            desktop.close()
            mobile.close()

    def test_source_backed_price_logic_is_visible(self):
        page = self._page(1440)
        try:
            text = page.locator("body").inner_text().replace("\n", " ")
            self.assertIn("有限会社シーベ", text)
            self.assertIn("400×300mm", text)
            self.assertIn("4,158円", text)
            self.assertIn("データ制作費は含まれていません", text)
            self.assertIn("サイズ", text)
            self.assertIn("仕様", text)
            self.assertIn("設置場所", text)
        finally:
            page.close()


if __name__ == "__main__":
    unittest.main()
