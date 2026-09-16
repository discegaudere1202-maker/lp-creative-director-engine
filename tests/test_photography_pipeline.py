import json
from pathlib import Path
import tempfile
import unittest

from lp_engine.photography import (
    ASSET_MANIFEST_FIELDS,
    PHOTO_ROLE_FIELDS,
    build_asset_manifest,
    build_photo_role_map,
    connect_photo_roles_to_compositions,
    guard_fake_evidence_copy,
    render_photo_asset,
    select_asset_for_role,
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
        }
        ia = [
            {"section_role": "hero_orientation"},
            {"section_role": "company_truth"},
            {"section_role": "service_process"},
            {"section_role": "next_step"},
            {"section_role": "cta_zone"},
        ]
        return build_photo_role_map(understanding, {}, ia)

    def test_photo_role_map_has_required_contract_fields(self):
        role_map = self._role_map()
        self.assertGreaterEqual(len(role_map["roles"]), 3)
        for role in role_map["roles"]:
            for field in PHOTO_ROLE_FIELDS:
                self.assertIn(field, role)
                self.assertTrue(role[field])
        self.assertEqual(role_map["selection_mode"], "role_driven_not_fixed_count")

    def test_asset_manifest_has_required_fields_and_source_priority(self):
        role_map = self._role_map()
        role = role_map["roles"][0]["photo_role"]
        base = {
            "photo_role": role,
            "provider": "fixture",
            "source": "https://example.test/source",
            "creator": "fixture creator",
            "rights_status": "COMMERCIAL_USE_CONFIRMED",
            "license_terms_url": "https://example.test/terms",
            "checked_at": "2026-09-16T00:00:00Z",
            "visual_subject": "住宅外観",
            "placement": "hero_dominant_image",
            "replacement_target": "実施工後住宅",
            "crop": "50% 50%",
            "alt": "住宅外観のイメージ",
        }
        candidates = [
            {**base, "asset_id": "v", "source_type": "vector", "asset_url": "https://example.test/v.svg"},
            {**base, "asset_id": "g", "source_type": "generated", "asset_url": "https://example.test/g.webp"},
            {**base, "asset_id": "f", "source_type": "free_stock", "asset_url": "https://example.test/f.webp"},
        ]
        manifest = build_asset_manifest(candidates, role_map)
        self.assertEqual([item["source_type"] for item in manifest["assets"]], ["free_stock", "generated", "vector"])
        for asset in manifest["assets"]:
            for field in ASSET_MANIFEST_FIELDS:
                self.assertIn(field, asset)
        self.assertEqual(select_asset_for_role(manifest, role)["asset_id"], "f")
        self.assertEqual(manifest["vector_policy"], "supporting_only_not_primary_photography")

    def test_composition_receives_photography_role_and_replacement_metadata_is_preserved(self):
        role_map = self._role_map()
        role = role_map["roles"][0]
        manifest = build_asset_manifest([], role_map)
        compositions = connect_photo_roles_to_compositions(
            [{"section_id": "opening", "section_role": "hero_orientation", "photo_replacement_role": "same-role-approved-real-image"}],
            role_map,
            manifest,
        )
        self.assertEqual(compositions[0]["photo_role"], role["photo_role"])
        self.assertEqual(compositions[0]["photo_placement"], "hero_dominant_image")
        self.assertEqual(compositions[0]["photo_replacement_role"], "same-role-approved-real-image")
        self.assertEqual(compositions[0]["vector_role"], "supporting_only")

    def test_fake_evidence_copy_is_blocked_without_matching_approved_evidence(self):
        with self.assertRaisesRegex(ValueError, "fake-evidence"):
            guard_fake_evidence_copy({"headline": "当社施工事例"}, [])
        allowed = guard_fake_evidence_copy(
            {"headline": "当社施工事例"},
            [{"claim": "当社施工事例", "evidence_id": "e-1"}],
        )
        self.assertEqual(allowed["headline"], "当社施工事例")

    def test_renderer_can_render_rights_tracked_photo_asset_with_alt_and_crop(self):
        markup = render_photo_asset({
            "asset_url": "https://example.test/hero.webp",
            "photo_role": "hero_context",
            "source_type": "free_stock",
            "alt": "作業風景のイメージ",
            "crop": "60% 40%",
            "preferred_orientation": "landscape",
        })
        self.assertIn("<img", markup)
        self.assertIn('alt="作業風景のイメージ"', markup)
        self.assertIn("object-position:60% 40%", markup)
        self.assertEqual(render_photo_asset({"asset_url": "https://example.test/v.svg", "source_type": "vector"}), "")

    def test_existing_generation_emits_photography_contract_without_manual_edit(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_generation(load_fixture(), Path(directory) / "generation", generation_id="photo-contract")
            self.assertTrue(result.production_output_allowed)
            self.assertIn("photo_role_map", result.stage_outputs)
            self.assertIn("asset_manifest", result.stage_outputs)
            self.assertEqual(result.manifest["manual_intervention"], [])
            self.assertEqual(result.stage_outputs["asset_manifest"]["source_priority"], ["free_stock", "generated", "vector"])
            self.assertEqual(result.stage_outputs["art_direction"]["photo_replacement_readiness"]["replacement_targets"], ["実店舗・実現場・実商品・実人物写真"])

    def test_generation_with_photo_asset_renders_image_and_keeps_vector_supporting(self):
        raw = load_fixture()
        # Use the generic first role. Asset selection itself is supplied by the
        # next round; this fixture only proves the renderer contract now exists.
        raw["photo_assets"] = [{
            "asset_id": "fixture-photo",
            "photo_role": "hero_context",
            "source_type": "free_stock",
            "provider": "fixture",
            "source": "https://example.test/source",
            "asset_url": "https://example.test/photo.webp",
            "creator": "fixture",
            "rights_status": "COMMERCIAL_USE_CONFIRMED",
            "license_terms_url": "https://example.test/terms",
            "checked_at": "2026-09-16T00:00:00Z",
            "visual_subject": "service context",
            "placement": "hero_dominant_image",
            "replacement_target": "actual business photo",
            "crop": "50% 50%",
            "alt": "サービスイメージ",
        }]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generation"
            result = run_generation(raw, output, generation_id="photo-render")
            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertTrue(result.production_output_allowed)
            self.assertIn("https://example.test/photo.webp", html)
            self.assertIn('alt="サービスイメージ"', html)
            self.assertIn("supporting_only", json.dumps(result.stage_outputs["compositions"], ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
