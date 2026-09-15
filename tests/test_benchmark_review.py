import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.benchmark_review import build_review_manifest, render_review_html, write_review_bundle


PAYLOAD = {
    "candidate": {
        "id": "candidate",
        "images": {"1440": "candidate-1440.png", "390": "candidate-390.png"},
    },
    "benchmarks": [
        {"id": "C23", "images": {"1440": "c23-1440.png", "390": "c23-390.png"}},
        {"id": "C24", "images": {"1440": "c24-1440.png", "390": "c24-390.png"}},
        {"id": "C26", "images": {"1440": "c26-1440.png", "390": "c26-390.png"}},
    ],
    "viewports": [1440, 390],
    "context": "B2B professional service / inquiry",
}


class BenchmarkReviewTest(unittest.TestCase):
    def test_manifest_has_both_viewports_and_randomized_candidate_side(self):
        manifest = build_review_manifest(PAYLOAD, seed=7)
        self.assertEqual(len(manifest["rows"]), 6)
        self.assertEqual({r["viewport"] for r in manifest["rows"]}, {1440, 390})
        self.assertTrue(all(r["candidate_side"] in {"left", "right"} for r in manifest["rows"]))

    def test_html_hides_source_identity_text(self):
        manifest = build_review_manifest(PAYLOAD, seed=2)
        html = render_review_html(manifest)
        self.assertIn("Anonymous pair", html)
        self.assertNotIn("C23</", html)
        self.assertNotIn("candidate</", html)
        self.assertIn("Immediate Read", html)
        self.assertIn("Owner Specificity", html)

    def test_bundle_writes_html_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "review.html"
            result = write_review_bundle(PAYLOAD, output, seed=1)
            self.assertTrue(output.exists())
            self.assertTrue(Path(result["manifest"]).exists())
            self.assertEqual(result["pair_count"], 6)

    def test_missing_viewport_image_raises(self):
        payload = json.loads(json.dumps(PAYLOAD))
        del payload["benchmarks"][0]["images"]["390"]
        with self.assertRaises(ValueError):
            build_review_manifest(payload)


if __name__ == "__main__":
    unittest.main()
