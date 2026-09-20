import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("round2q", ROOT / "scripts" / "run_round2q_nagi_growth.py")
assert spec and spec.loader
Q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Q)


class Round2QContractTests(unittest.TestCase):
    def test_growth_event_contract_is_closed_and_verified_contact_is_single(self):
        expected = {"service_preview", "service_selected", "price_view", "faq_open", "cta_impression", "instagram_click", "scroll_depth", "landing_variant"}
        self.assertEqual(set(expected), {"service_preview", "service_selected", "price_view", "faq_open", "cta_impression", "instagram_click", "scroll_depth", "landing_variant"})
        self.assertEqual(Q.INSTAGRAM, "https://www.instagram.com/happyfuture_02/")

    def test_contract_builder_contains_growth_signatures(self):
        html = Q.build_html_q({
            key: {"output": f"assets/{key}.png", "source": "generated", "evidence_state": "PROVISIONAL"}
            for key in ("A01", "A02", "A04", "A05", "A06", "A07")
        })
        for token in ("DETAIL_TO_RELATIONSHIP", "guided-preview-click-lock", "path-merge", "dataLayer", "@happyfuture_02"):
            self.assertIn(token, html)
        self.assertIn("ドライヘッドスパ</span><span class=\"purpose-intent\">受けたい", html)
        self.assertNotIn("入口を見る", html)


if __name__ == "__main__":
    unittest.main()
