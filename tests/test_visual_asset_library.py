import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from lp_engine.production_cutover import plan_current_industry_production
from lp_engine.visual_asset_library import (
    VisualAssetError,
    evaluate_visual_asset_rights,
    ingest_provider_asset,
    make_asset_binding,
    normalize_visual_asset_record,
    query_asset_candidates,
    render_asset_binding,
    select_visual_asset,
    validate_asset_bundle,
    verify_asset_binary,
)


def truth(value):
    return {"value": value, "confidence": "verified", "sources": ["fixture"]}


def production_fixture(category="beauty_cosmetics", family="family-alpha"):
    return {
        "company_truth": {
            "category": truth(category), "name": truth("Fixture business"),
            "offers": [{"id": "offer-1", "name": "Offer", "job": "choose"}],
            "contact": truth({"channel": "form"}), "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": "trust", "tensions": ["uncertainty"], "questions": ["process"],
            "risk_sensitivity": "high", "decision_stage": "consider",
        },
        "creative_family": {"family_id": family, "version": "1", "rationale": ["fixture"], "frozen": True},
        "evidence": {
            "facts": [{"id": "process", "claim": "verified process", "scope": "process", "sources": ["fixture"], "confidence": "verified", "usable_for_persuasion": True}],
            "proof_gaps": [], "contradictions": [],
        },
        "media_roles": [{"role_id": "primary", "role": "process", "required_content_class": "generic", "rights": "generated"}],
        "renderer_capabilities": ["responsive"],
    }


def asset(asset_id="asset-a", **overrides):
    binary = overrides.pop("binary", b"fixture-image-bytes")
    base = {
        "asset_id": asset_id, "media_type": "still_image", "source_provider": "Pexels", "source_id": asset_id,
        "source_url": f"https://example.test/assets/{asset_id}", "creator": "Fixture creator",
        "license_status": "VERIFIED_PROVIDER_LICENSE", "license_terms_url": "https://example.test/license", "license_terms_checked_at": "2026-09-26",
        "commercial_use_status": "ALLOWED", "modification_status": "ALLOWED", "crop_status": "ALLOWED", "attribution_requirement": "NONE_REQUIRED",
        "person_release_status": "NOT_APPLICABLE", "property_release_status": "NOT_APPLICABLE", "trademark_logo_risk": "NONE_VISIBLE",
        "acquired_at": "2026-09-26", "checked_at": "2026-09-26", "content_class": "product_packshot_generic",
        "industry_tags": ["beauty_cosmetics"], "business_category_tags": ["skincare_cosmetics_product"],
        "eligible_scene_intents": ["recognize"], "eligible_media_roles": ["hero"], "orientation": "flexible", "aspect_ratio": "source",
        "people_count": 0, "people_type": "none", "visual_tone_tags": ["clean"], "material_quality_tags": ["glass"],
        "evidence_status": "GENERIC_ILLUSTRATIVE_STOCK", "prohibited_uses": ["actual company evidence"], "provenance_confidence": "HIGH",
        "recheck_policy": {"triggers": ["provider terms changed", "binary hash changed"]},
        "binary_sha256": hashlib.sha256(binary).hexdigest(),
    }
    base.update(overrides)
    return base


class VisualAssetLibraryTest(unittest.TestCase):
    def test_schema_completeness_and_ingestion_keeps_raw_provenance(self):
        normalized = normalize_visual_asset_record(asset())
        self.assertEqual(normalized["asset_id"], "asset-a")
        broken = asset(); broken.pop("license_terms_url")
        with self.assertRaises(VisualAssetError):
            normalize_visual_asset_record(broken)
        provider = {"metadata": {**asset(), "binary_sha256": "0" * 64}, "raw_provenance": {"provider_payload": {"id": 10}}}
        ingested = ingest_provider_asset(provider, b"exact-binary", acquired_at="2026-09-26")
        self.assertEqual(ingested["binary_sha256"], hashlib.sha256(b"exact-binary").hexdigest())
        self.assertEqual(ingested["raw_provenance"]["provider_payload"]["id"], 10)

    def test_rights_fail_closed_matrix(self):
        target = {"crop_required": True, "can_render_attribution": True, "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK"}
        cases = [
            ({"license_status": "UNKNOWN"}, "MEDIA_LICENSE_UNKNOWN"),
            ({"commercial_use_status": "NOT_ALLOWED"}, "MEDIA_COMMERCIAL_USE_BLOCKED"),
            ({"crop_status": "NOT_ALLOWED"}, "MEDIA_MODIFICATION_BLOCKED"),
            ({"attribution_requirement": "REQUIRED"}, "MEDIA_ATTRIBUTION_UNSATISFIED"),
            ({"people_count": 1, "people_type": "single_adult", "person_release_status": "UNVERIFIED"}, "MEDIA_PERSON_RIGHTS_REVIEW_REQUIRED"),
            ({"trademark_logo_risk": "PRESENT_REVIEW_REQUIRED"}, "MEDIA_TRADEMARK_REVIEW_REQUIRED"),
            ({"property_release_status": "UNKNOWN"}, "MEDIA_PROPERTY_RIGHTS_REVIEW_REQUIRED"),
        ]
        for patch, expected in cases:
            use = dict(target)
            if patch.get("attribution_requirement") == "REQUIRED":
                use["can_render_attribution"] = False
            self.assertEqual(evaluate_visual_asset_rights(asset(**patch), use)["state"], expected)
        self.assertEqual(evaluate_visual_asset_rights(asset(), {**target, "evidence_boundary": "ACTUAL_COMPANY_EVIDENCE"})["state"], "MEDIA_EVIDENCE_BOUNDARY_MISMATCH")
        self.assertEqual(evaluate_visual_asset_rights(asset(), {**target, "current_binary_sha256": "0" * 64})["state"], "MEDIA_BINARY_CHANGED")
        self.assertEqual(evaluate_visual_asset_rights(asset(), {**target, "recheck_triggered": True})["state"], "MEDIA_RIGHTS_STALE")

    def test_attribution_can_be_preserved(self):
        rights = evaluate_visual_asset_rights(asset(attribution_requirement="REQUIRED"), {"crop_required": True, "can_render_attribution": True, "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK"})
        self.assertEqual(rights["state"], "RIGHTS_PASS_WITH_RENDER_CONDITIONS")
        self.assertIn("render_attribution", rights["conditions"])

    def test_deterministic_selection_and_identity_invariance(self):
        plan = plan_current_industry_production(production_fixture())
        candidates = [asset("asset-b"), asset("asset-a")]
        placement = {"required_content_classes": ["product_packshot_generic"], "orientation": "flexible", "business_category": "skincare_cosmetics_product", "crop_fingerprint": "hero-v1", "batch_id": "batch-1", "can_render_attribution": True, "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK", "people_type": "none"}
        scene = {"id": "recognize", "intent": "recognize"}
        first = select_visual_asset(candidates, frozen_composition_plan=plan, scene=scene, media_role="hero", target_placement=placement, usage_ledger_snapshot=[])
        second = select_visual_asset(list(reversed(candidates)), frozen_composition_plan=plan, scene=scene, media_role="hero", target_placement=placement, usage_ledger_snapshot=[])
        self.assertEqual(first["selected"]["asset_id"], "asset-a")
        self.assertEqual(first["selected"]["asset_id"], second["selected"]["asset_id"])
        changed = production_fixture(); changed["company_id"] = "identity-b"; changed["reference_id"] = "ref-b"
        other = plan_current_industry_production(changed)
        self.assertEqual(plan["family_id"], other["family_id"])
        self.assertEqual(plan["topology"], other["topology"])

    def test_category_mutation_and_scarcity_never_switch_family_topology(self):
        first = plan_current_industry_production(production_fixture("beauty_cosmetics"))
        second = plan_current_industry_production(production_fixture("pilates_fitness"))
        self.assertEqual(first["family_id"], second["family_id"])
        self.assertEqual(first["topology"], second["topology"])
        empty = query_asset_candidates([], industry="beauty_cosmetics", business_category="skincare_cosmetics_product", scene_intent="recognize", media_role="hero", required_content_classes=["product_packshot_generic"], evidence_boundary="GENERIC_ILLUSTRATIVE_STOCK")
        result = select_visual_asset(empty, frozen_composition_plan=first, scene={"id": "recognize", "intent": "recognize"}, media_role="hero", target_placement={"business_category": "skincare_cosmetics_product", "orientation": "flexible", "batch_id": "batch"}, usage_ledger_snapshot=[])
        self.assertEqual(result["state"], "MEDIA_ROLE_UNSATISFIED")
        self.assertEqual(first["family_id"], "family-alpha")

    def test_hero_reuse_and_same_role_crop_repetition_are_blocked(self):
        plan = plan_current_industry_production(production_fixture())
        placement = {"required_content_classes": ["product_packshot_generic"], "orientation": "flexible", "business_category": "skincare_cosmetics_product", "crop_fingerprint": "hero-v1", "batch_id": "batch-1", "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK"}
        ledger = [{"asset_id": "asset-a", "media_role": "hero", "crop_fingerprint": "hero-v1", "business_category": "skincare_cosmetics_product", "batch_id": "batch-1"}]
        selected = select_visual_asset([asset("asset-a"), asset("asset-b")], frozen_composition_plan=plan, scene={"id": "recognize", "intent": "recognize"}, media_role="hero", target_placement=placement, usage_ledger_snapshot=ledger)
        self.assertEqual(selected["selected"]["asset_id"], "asset-b")
        only = select_visual_asset([asset("asset-a")], frozen_composition_plan=plan, scene={"id": "recognize", "intent": "recognize"}, media_role="hero", target_placement=placement, usage_ledger_snapshot=ledger)
        self.assertEqual(only["state"], "MEDIA_ROLE_UNSATISFIED")
        self.assertIn(only["candidate_rejections"][0]["reason"], {"BATCH_HERO_REUSE_BLOCKED", "REUSE_ROLE_CROP_BLOCKED"})

    def test_orientation_crop_mismatch_fails_closed(self):
        plan = plan_current_industry_production(production_fixture())
        result = select_visual_asset([asset(orientation="portrait")], frozen_composition_plan=plan, scene={"id": "recognize", "intent": "recognize"}, media_role="hero", target_placement={"required_content_classes": ["product_packshot_generic"], "orientation": "landscape", "business_category": "skincare_cosmetics_product", "crop_fingerprint": "hero", "batch_id": "batch"}, usage_ledger_snapshot=[])
        self.assertEqual(result["state"], "MEDIA_ROLE_UNSATISFIED")
        self.assertEqual(result["candidate_rejections"][0]["reason"], "ORIENTATION_CROP_BLOCKED")

    def test_binding_trace_hash_generic_semantics_and_bundle_guard(self):
        plan = plan_current_industry_production(production_fixture())
        selection = {"state": "SELECTED", "selected": asset(), "rights": {"state": "RIGHTS_PASS_WITH_RENDER_CONDITIONS", "conditions": ["illustrative_only"]}, "reuse_penalty_factors": [], "candidate_rejections": [], "visual_fit_sort_keys": []}
        binding = make_asset_binding(generation_id="g1", plan=plan, scene={"id": "recognize", "intent": "recognize"}, media_role="hero", business_category="skincare_cosmetics_product", selection=selection, catalog_version="cat-v1", usage_ledger=[], crop_variant_id="hero-center-v1", focal_point=[0.5, 0.5], local_asset_path="asset.jpg")
        self.assertEqual(binding["trace"]["binary_sha256"], asset()["binary_sha256"])
        markup = render_asset_binding(binding)
        self.assertIn("イメージ写真", markup)
        self.assertIn(binding["binary_sha256"], markup)
        clone = copy.deepcopy(binding); clone["asset_id"] = "other-id"
        self.assertEqual(validate_asset_bundle([binding, clone])["state"], "MEDIA_REUSE_REVIEW_REQUIRED")

    def test_exact_binary_integrity(self):
        payload = b"exact-selected-binary"; expected = hashlib.sha256(payload).hexdigest()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "asset.bin"; path.write_bytes(payload)
            self.assertEqual(verify_asset_binary(path, expected), expected)
            with self.assertRaises(VisualAssetError):
                verify_asset_binary(path, "0" * 64)


if __name__ == "__main__":
    unittest.main()
