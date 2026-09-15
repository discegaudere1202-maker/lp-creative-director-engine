import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.loader import from_dict
from lp_engine.pipeline import run_pipeline


class PipelineTest(unittest.TestCase):
    def test_mahora_sample_passes(self):
        data = json.loads((ROOT / "examples/mahora_v2.json").read_text(encoding="utf-8"))
        profile, concept, sections, motions, screenshots = from_dict(data)
        report = run_pipeline(profile, concept, sections, motions, screenshots)
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.primary_authority, "DOCUMENT")

    def test_two_screenshot_peaks_required(self):
        data = json.loads((ROOT / "examples/mahora_v2.json").read_text(encoding="utf-8"))
        data["screenshot_scores"] = data["screenshot_scores"][:1]
        profile, concept, sections, motions, screenshots = from_dict(data)
        report = run_pipeline(profile, concept, sections, motions, screenshots)
        screenshot = [r for r in report.results if r.gate == "ScreenshotPeakGate"][0]
        self.assertEqual(screenshot.status, "HOLD")


if __name__ == "__main__":
    unittest.main()
