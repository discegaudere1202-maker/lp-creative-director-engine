import json
import subprocess
import sys
import unittest
from pathlib import Path
from lp_engine.photography import resolve_local_asset


ROOT = Path(__file__).parents[1]


class PhotographyAssetPreflightTest(unittest.TestCase):
    def test_all_six_generated_binaries_are_available(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/preflight_photography_assets.py")], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(len(payload["generated"]), 6)
        self.assertTrue(all(item["status"] == "AVAILABLE_BINARY" for item in payload["generated"]))

    def test_local_resolver_requires_approved_binary(self):
        manifest = json.loads((ROOT / "data/photography/photography_asset_manifest_v1.json").read_text(encoding="utf-8"))
        asset = resolve_local_asset(manifest, "hero_home_finish", ROOT)
        self.assertTrue(asset["binary_available"])
        self.assertTrue(Path(asset["local_asset_path"]).is_file())
        unsafe = dict(manifest)
        unsafe["assets"] = [dict(item) for item in manifest["assets"]]
        unsafe["assets"][0]["rights_status"] = "UNAPPROVED"
        with self.assertRaises(PermissionError):
            resolve_local_asset(unsafe, "hero_home_finish", ROOT)


if __name__ == "__main__":
    unittest.main()
