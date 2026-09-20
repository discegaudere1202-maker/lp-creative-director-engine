import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2qb", ROOT / "scripts" / "run_round2q_b_public_leak_closure.py")
assert spec and spec.loader
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


class Round2QPublicLeakTests(unittest.TestCase):
    def test_only_public_annotation_is_removed(self):
        manifest = {key: {"output": f"assets/{key}.png", "source": "generated", "evidence_state": "PROVISIONAL"} for key in ("A01", "A02", "A04", "A05", "A06", "A07")}
        before, after = B.build_html_qb(manifest)
        self.assertIn("DETAIL → RELATIONSHIP", B.visible_text(before))
        self.assertNotIn("DETAIL → RELATIONSHIP", B.visible_text(after))
        self.assertIn("hero-motion-note", after)
        self.assertEqual(B.public_leak_audit(after)["status"], "PASS")

    def test_before_after_contract_has_no_layout_edit(self):
        manifest = {key: {"output": f"assets/{key}.png", "source": "generated", "evidence_state": "PROVISIONAL"} for key in ("A01", "A02", "A04", "A05", "A06", "A07")}
        before, after = B.build_html_qb(manifest)
        self.assertEqual(before.replace('<p class="hero-motion-note">DETAIL → RELATIONSHIP</p>', ""), after)


if __name__ == "__main__":
    unittest.main()
