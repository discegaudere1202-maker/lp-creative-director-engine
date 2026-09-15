import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class EnrichedEvidenceValidationTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config/prototype_enriched_capture_targets_v1.json").read_text(encoding="utf-8"))

    def test_variants_are_separate_from_baselines(self):
        for item in self.config["variants"]:
            with self.subTest(item=item["prototype_id"]):
                self.assertTrue((ROOT / item["path"]).is_file())
                self.assertTrue((ROOT / item["baseline_path"]).is_file())
                self.assertNotEqual(item["path"], item["baseline_path"])

    def test_capture_config_has_formal_viewports(self):
        self.assertEqual({(v["width"], v["height"]) for v in self.config["viewports"]}, {(390, 844), (1440, 1000)})
        self.assertEqual({v["prototype_id"] for v in self.config["variants"]}, {"P02_ENRICHED", "P10_ENRICHED"})

    def test_evidence_ledgers_are_source_bound_and_unknown_safe(self):
        for item in self.config["variants"]:
            payload = json.loads((ROOT / item["evidence_ledger"]).read_text(encoding="utf-8"))
            for fact in payload["facts"]:
                self.assertIn(fact["verification_status"], {"VERIFIED", "UNKNOWN"})
                if fact["verification_status"] == "VERIFIED":
                    self.assertTrue(fact["source_url"].startswith("https://"))
                    self.assertTrue(fact["source_excerpt"].strip())
            self.assertTrue(payload["unknowns"])

    def test_variant_copy_contains_only_researched_proof_hooks(self):
        p02 = (ROOT / "examples/prototypes/p02_customer_world_translation_enriched_v1.html").read_text(encoding="utf-8")
        p10 = (ROOT / "examples/prototypes/p10_customer_state_transition_enriched_v1.html").read_text(encoding="utf-8")
        self.assertIn("緒方 幸一", p02)
        self.assertIn("サービス説明・見積", p02)
        self.assertNotIn("守秘", p02)
        self.assertIn("宮原 彩乃", p10)
        self.assertIn("転職後もキャリアに無料で伴走します。", p10)
        self.assertNotIn("無理な勧誘", p10)

if __name__ == "__main__":
    unittest.main()
