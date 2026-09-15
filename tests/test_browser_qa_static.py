import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from lp_engine.browser_qa import DEFAULT_WIDTHS, TEXT_SELECTOR


class BrowserQAStaticTest(unittest.TestCase):
    def test_required_widths(self):
        self.assertEqual(DEFAULT_WIDTHS, [320,360,375,390,430,768,1024,1280,1440])

    def test_text_selector_covers_headings_and_ctas(self):
        for token in ['h1','h2','h3','button','.btn']:
            self.assertIn(token, TEXT_SELECTOR)


if __name__ == '__main__':
    unittest.main()
