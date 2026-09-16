import json
from pathlib import Path
import tempfile
import unittest

from lp_engine.photography import (
    ASSET_FIELDS,
    PHOTO_ROLE_FIELDS,
    build_asset_manifest,
    build_photo_role_map,
    guard_fake_evidence_copy,
    validate_asset_manifest,
    validate_photo_role_map,
)
from lp_engine.production_generation import run_generation


FIXTURE = Path(__file__).parents[1] / "examples/production/andy_motorcycle/andy_motorcycle_production_input_v1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class PhotographyPipelineContractTest(unittest.TestCase):
    def _role_map(self):
        understanding = {
            "industry_visual_family": "material_field",
            "service_category": "外壁塗装",
            "company_truth": "住宅の外壁塗装を相談できる。",
            "customer_state": {"before": "塗り替え時期が分からない", "barrier": "どこまで頼めるか分からない"},
        }
        strategy = {"layout_profile": "field_ledger"}
        ia = [{"section_id": value} for value in ("opening", "truth", "way_in", "contact", "close")]
        return build_photo_role_map(understanding, strategy, ia)

    def test_photo_role_map_has_required_contract_fields(self):
        role_map = self._role_map()
        self.assertEqual(validate_photo_role_map(role_map), [])
        self.assertGreaterEqual(len(role_map["roles"]), 4)
        for role in role_map["roles"]:
            self.assertTrue(set(PHOTO_ROLE_FIELDS).issubset(role))
        placements = {placement for role in role_map["roles"] for placement in role.get("placement_candidates", [])}
        self.assertTrue({"opening", "truth", "way_in", "contact", "close"}.issubset(placements))

    def test_asset_manifest_prefers_free_stock_then_generated_then_vector(self):
        role_map = self._role_map()
        hero_role = role_map["roles"][0]["photo_role"]
        raw = {"photo_assets": [
            {"asset_id": "vector-1", "photo_role": hero_role, "source_type": "vector", "provider": "lp_engine", "source": "engine", "rights_status": "ENGINE_GENERATED_SUPPORT_ONLY"},
            {"asset_id": "generated-1", "photo_role": hero_role, "source_type": "generated", "provider": "image_generator", "source": "generated", "asset_url": "https://images.example.test/generated.jpg", "creator": "engine", "rights_status": "GENERATED_OWNED"},
            {"asset_id": "stock-1", "photo_role": hero_role, "source_type": "free_stock", "provider": "stock_provider", "source": "https://stock.example.test/photo/1", "asset_url": "https://images.example.test/stock.jpg", "creator": "creator", "rights_status": "LICENSE_VERIFIED", "license_terms_url": "https://stock.example.test/license", "checked_at": "2026-09-16T00:00:00Z"},
        ]}
        manifest = build_asset_manifest(raw, role_map, visual_scene="material_field")
        self.assertEqual(validate_asset_manifest(manifest), [])
        self.assertEqual(manifest["selection_policy"]["priority"], ["free_stock", "generated", "vector"])
        selected = next(item for item in manifest["items"] if item["photo_role"] == hero_role)
        self.assertEqual(selected["source_type"], "free_stock")
        self.assertTrue(selected["photography_authority"])
        self.assertFalse(selected["supporting_only"])
        self.assertTrue(set(ASSET_FIELDS).issubset(selected))

    def test_unresolved_role_falls_back_to_vector_support_only(self):
        manifest = build_asset_manifest({}, self._role_map(), visual_scene="material_field")
        self.assertEqual(validate_asset_manifest(manifest), [])
        self.assertTrue(manifest["items"])
        self.assertTrue(all(item["source_type"] == "vector" for item in manifest["items"]))
        self.assertTrue(all(item["supporting_only"] for item in manifest["items"]))
        self.assertTrue(all(not item["photography_authority"] for item in manifest["items"]))

    def test_fake_evidence_photo_copy_is_neutralized_without_evidence(self):
        payload = {"headline": "当社施工事例", "body": "実際の施術風景と生徒作品、お客様写真、実績写真をご覧ください。"}
        guarded = guard_fake_evidence_copy(payload, [])
        serialized = json.dumps(guarded, ensure_ascii=False)
        for phrase in ("当社施工事例", "実際の施術風景", "生徒作品", "お客様写真", "実績写真"):
            self.assertNotIn(phrase, serialized)
        self.assertIn("施工イメージ", serialized)
        self.assertIn("施術イメージ", serialized)

    def test_generation_writes_photography_contract_and_keeps_replacement_metadata(self):
        raw = load_fixture()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "production"
            result = run_generation(raw, output, generation_id="photography-contract-1")
            self.assertTrue(result.production_output_allowed)
            role_map = json.loads((output / "photo_role_map.json").read_text(encoding="utf-8"))
            manifest = json.loads((output / "asset_manifest.json").read_text(encoding="utf-8"))
            generation = json.loads((output / "generation_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(validate_photo_role_map(role_map), [])
            self.assertEqual(validate_asset_manifest(manifest), [])
            self.assertEqual(generation["manual_intervention"], [])
            self.assertEqual(generation["photography_outputs"]["asset_selection_priority"], ["free_stock", "generated", "vector"])
            readiness = generation["photo_replacement_readiness"]
            self.assertEqual(readiness["vector_role"], "supporting_only")
            self.assertTrue(readiness["replacement_targets"])

    def test_renderer_uses_rights_cleared_photo_asset_with_alt_and_crop(self):
        raw = load_fixture()
        raw["photo_assets"] = [{
            "asset_id": "hero-stock", "photo_role": "hero_context", "source_type": "free_stock",
            "provider": "stock_provider", "source": "https://stock.example.test/photo/hero",
            "asset_url": "https://images.example.test/hero.jpg", "creator": "creator",
            "rights_status": "LICENSE_VERIFIED", "license_terms_url": "https://stock.example.test/license",
            "checked_at": "2026-09-16T00:00:00Z", "visual_subject": "バイク整備を想起させる作業空間",
            "placement": "opening", "replacement_target": "実作業場写真", "crop": "50% 42%",
            "alt": "バイク整備を想起させる作業空間",
        }]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "production"
            run_generation(raw, output, generation_id="photography-render-1")
            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('src="https://images.example.test/hero.jpg"', html)
            self.assertIn('alt="バイク整備を想起させる作業空間"', html)
            self.assertIn("object-position:50% 42%", html)
            self.assertIn('data-source-type="free_stock"', html)
            self.assertIn("vector-support", html)


if __name__ == "__main__":
    unittest.main()
