import unittest
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "examples/prototypes/p10_customer_state_transition_v1.html"
WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
MOBILE_WIDTHS = [320, 360, 375, 390, 430]
DESKTOP_WIDTHS = [768, 1024, 1280, 1440]
DISALLOWED = {"は、", "で、", "を。", "る。", "か。", "い？", "たい？", "する。", "れる。", "す。"}

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
          chars.push({ch, top: Math.round(rect.top * 2) / 2});
        }
      }
    }
    const lines = [];
    for (const char of chars) {
      let line = lines.find((item) => Math.abs(item.top - char.top) < 1);
      if (!line) {
        line = {top: char.top, text: ""};
        lines.push(line);
      }
      line.text += char.ch;
    }
    results.push(lines.map((line) => line.text.trim()).filter(Boolean));
  });
  return results;
}
"""


class P10CustomerStateTransitionTest(unittest.TestCase):
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

    def _assert_line_shape(self, page, width: int, selector: str):
        for lines in page.evaluate(LINE_TEXT_JS, selector):
            for line in lines:
                self.assertNotIn(
                    line,
                    DISALLOWED,
                    f"semantic fragment at {width}px in {selector}: {line}",
                )
                jp = [
                    ch for ch in line
                    if "\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff"
                ]
                if 0 < len(jp) <= 2:
                    self.fail(
                        f"short Japanese fragment at {width}px in {selector}: {line}"
                    )

    def test_no_horizontal_overflow_across_nine_widths(self):
        for width in WIDTHS:
            with self.subTest(width=width):
                page = self._page(width)
                try:
                    self.assertLessEqual(
                        page.evaluate("document.documentElement.scrollWidth"), width
                    )
                finally:
                    page.close()

    def test_customer_copy_keeps_semantic_line_shape(self):
        prose_selectors = [
            "h1 span", ".intro-note", ".resolved-row strong",
            ".resolved-row small", ".closing .proof span", ".closing .cta"
        ]
        for width in WIDTHS:
            with self.subTest(width=width):
                page = self._page(width)
                try:
                    for selector in prose_selectors:
                        self._assert_line_shape(page, width, selector)
                    # On mobile the scattered thoughts become a normal reading list,
                    # so they must obey ordinary line-shape rules.
                    if width in MOBILE_WIDTHS:
                        self._assert_line_shape(page, width, ".fragment")
                finally:
                    page.close()

    def test_desktop_fragment_cloud_stays_spatially_intact(self):
        # Desktop deliberately rotates the BEFORE thoughts. Character line boxes are
        # therefore not a valid semantic-line signal; spatial containment is.
        for width in DESKTOP_WIDTHS:
            with self.subTest(width=width):
                page = self._page(width)
                try:
                    before = page.locator(".before").bounding_box()
                    self.assertIsNotNone(before)
                    fragment_rects = page.locator(".fragment").evaluate_all(
                        "els => els.map(e => { const r=e.getBoundingClientRect(); return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,whiteSpace:getComputedStyle(e).whiteSpace}; })"
                    )
                    self.assertEqual(len(fragment_rects), 4)
                    for rect in fragment_rects:
                        self.assertEqual(rect["whiteSpace"], "nowrap")
                        self.assertGreaterEqual(rect["left"], before["x"] - 2)
                        self.assertLessEqual(rect["right"], before["x"] + before["width"] + 2)
                        self.assertGreaterEqual(rect["top"], before["y"] - 2)
                        self.assertLessEqual(rect["bottom"], before["y"] + before["height"] + 2)
                finally:
                    page.close()

    def test_source_backed_state_transition_is_visible(self):
        page = self._page(1440)
        try:
            text = page.locator("body").inner_text().replace("\n", " ")
            self.assertIn("モヤモヤ", text)
            self.assertIn("価値観", text)
            self.assertIn("転職しない方がよい場合", text)
            self.assertIn("無料", text)
            self.assertIn("次の一歩", text)
            self.assertEqual(page.locator(".fragment").count(), 4)
            self.assertEqual(page.locator(".resolved-row").count(), 3)
        finally:
            page.close()

    def test_mobile_re_art_direction_changes_transition_axis(self):
        desktop = self._page(1440)
        mobile = self._page(390)
        try:
            self.assertEqual(
                desktop.locator(".transition").evaluate("e => getComputedStyle(e).display"),
                "grid",
            )
            self.assertEqual(
                mobile.locator(".transition").evaluate("e => getComputedStyle(e).display"),
                "block",
            )
            self.assertNotEqual(
                desktop.locator(".axis").evaluate("e => getComputedStyle(e).display"),
                "none",
            )
            self.assertEqual(
                mobile.locator(".axis").evaluate("e => getComputedStyle(e).display"),
                "none",
            )
            self.assertEqual(
                desktop.locator(".mobile-only").evaluate("e => getComputedStyle(e).display"),
                "none",
            )
            self.assertNotEqual(
                mobile.locator(".mobile-only").evaluate("e => getComputedStyle(e).display"),
                "none",
            )
        finally:
            desktop.close()
            mobile.close()


if __name__ == "__main__":
    unittest.main()
