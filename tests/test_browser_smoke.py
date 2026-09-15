import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from lp_engine.browser_qa import run_browser_qa_sync


class BrowserSmokeTest(unittest.TestCase):
    def test_simple_responsive_page_passes(self):
        html = '''<!doctype html><html><head><meta charset="utf-8"><style>
        *{box-sizing:border-box} body{margin:0;font-family:sans-serif}.wrap{width:min(100% - 32px,900px);margin:auto}
        h1{font-size:clamp(36px,7vw,72px);line-height:1.1} a{display:inline-block;padding:12px 18px}
        </style></head><body><main class="wrap"><h1>伝わる言葉</h1><a class="btn">相談する</a></main></body></html>'''
        with tempfile.TemporaryDirectory() as td:
            html_path = Path(td) / 'sample.html'
            html_path.write_text(html, encoding='utf-8')
            report = run_browser_qa_sync(
                str(html_path),
                Path(td) / 'qa',
                widths=[320, 390, 1440],
                screenshot_widths=[],
            )
            self.assertEqual(report.status, 'PASS')


if __name__ == '__main__':
    unittest.main()
