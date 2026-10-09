"""Source-schema fixtures only: no private pool, browser, or network access."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from PIL import Image

from lp_engine.pilot_asset_selection import (
    AssetSelectionError, ILLUSTRATIVE_DISCLOSURE, INDEX_MEMBER,
    attach_preview_assets, build_preview_asset_selection,
    load_landscaping_pool, rank_landscaping_candidates, validate_composed_asset_usage,
)
from lp_engine.pilot_composition import compose_preview
from test_pilot_composition import payload_for, synthetic_source


class PilotAssetSelectionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.image = self.root / "synthetic.png"
        Image.new("RGB", (8, 6), "#123456").save(self.image)
        self.image_bytes = self.image.read_bytes()
        self.record = {
            "asset_id": "SYNTHETIC-A", "source_photo_id": "SYNTHETIC-A",
            "source_page": "https://example.test/synthetic-photo", "license_url": "https://example.test/synthetic-license",
            "author": "synthetic fixture", "sha256": hashlib.sha256(self.image_bytes).hexdigest(),
            "bytes": len(self.image_bytes), "width": 8, "height": 6,
            "adoption_status": "CANDIDATE", "company_project_staff_evidence_allowed": False,
            "full_resolution_visual_review": False, "pc_sp_crop_validation": "NOT_PERFORMED",
            "classification": {
                "asset_id": "SYNTHETIC-A", "scene": "住宅と庭の全景",
                "usable_roles": "HERO_BRAND,EMOTIONAL_SCENE", "excluded_uses": "会社施工実績・剪定作業の証拠",
                "visual_notes": "暮らしと植栽の関係を表す合成入力。", "日本の地域造園LPへの適合理由": "住宅と庭の導入用。",
                "人物や会社実績誤認防止": "第三者イメージ。施工会社の実績ではない。",
                "status": "READY_FOR_SELECTION",
            },
            "storage": {"archive_part": "SYNTHETIC.zip", "member_path": "synthetic.png",
                        "member_sha256": hashlib.sha256(self.image_bytes).hexdigest()},
            "near_duplicate_group": None, "validation_issues": [],
            "original_unknown_field": {"preserve": ["all", "values"]},
        }
        self.pool = self.load([self.record])
        self.placement = {"slot": "hero", "asset_id": "SYNTHETIC-A", "media_role": "HERO_BRAND",
                          "context_terms": ["住宅", "庭"], "parts": ["hero"],
                          "selection_reason": "住宅と庭の関係が事業者仮説の導入に合うため。"}

    def load(self, records, *, zipped=False):
        raw = json.dumps({"schema_version": 1, "version": "SYNTHETIC_POOL", "records": records,
                          "collection_closed": True}, ensure_ascii=False).encode()
        path = self.root / ("pool.zip" if zipped else "pool.json")
        if zipped:
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(INDEX_MEMBER, raw)
        else:
            path.write_bytes(raw)
        return load_landscaping_pool(path, expected_sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def rank(self, pool=None, **kwargs):
        params = {"industry": "landscape", "media_role": "HERO_BRAND", "context_terms": ["住宅"]}
        params.update(kwargs)
        return rank_landscaping_candidates(pool or self.pool, **params)

    def build(self, placements=None, **kwargs):
        params = {"pool": self.pool, "placements": placements or [self.placement],
                  "local_files": {"SYNTHETIC-A": self.image}, "context": {"intake_id": "SYNTHETIC-BUSINESS"}}
        params.update(kwargs)
        return build_preview_asset_selection(**params)

    def reject(self, code, fn, *args, **kwargs):
        with self.assertRaises(AssetSelectionError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_canonical_zip_preserves_every_source_field_and_state(self):
        pool = self.load([self.record], zipped=True)
        self.assertEqual(pool["index"]["records"], [self.record])
        ranked = self.rank(pool)
        self.assertEqual(ranked["source_record_count"], 1)
        candidate = ranked["candidates"][0]
        self.assertEqual(candidate["source_classification"], self.record["classification"])
        self.assertEqual(candidate["source_adoption_status"], "CANDIDATE")
        self.assertEqual(candidate["selection_status"], "CANDIDATE_ONLY")
        self.assertEqual(ranked["visual_qa"], "NOT_RUN")
        self.assertFalse(ranked["auto_selection"])

    def test_source_and_loaded_snapshot_changes_fail_closed(self):
        self.reject("SOURCE_HASH_MISMATCH", load_landscaping_pool, self.root / "pool.json", expected_sha256="0" * 64)
        changed = deepcopy(self.pool)
        changed["index"]["records"][0]["classification"]["status"] = "REJECT"
        self.reject("POOL_SNAPSHOT_CHANGED", self.rank, changed)
        changed = deepcopy(self.pool)
        changed["source"]["sha256"] = "0" * 64
        changed["source"]["index_sha256"] = "1" * 64
        self.reject("POOL_SNAPSHOT_CHANGED", self.rank, changed)
        self.reject("POOL_SNAPSHOT_CHANGED", self.build, pool=changed)

    def test_source_ids_and_recorded_storage_hash_are_checked(self):
        self.reject("DUPLICATE_ASSET_ID", self.load, [self.record, self.record])
        bad = deepcopy(self.record)
        bad["classification"]["asset_id"] = "WRONG"
        self.reject("CLASSIFICATION_ID_MISMATCH", self.load, [bad])
        bad = deepcopy(self.record)
        bad["storage"]["member_sha256"] = "0" * 64
        self.reject("STORAGE_HASH_MISMATCH", self.load, [bad])

    def test_industry_and_no_context_do_not_produce_default_hero(self):
        for industry in ("painting", "bar"):
            self.reject("INDUSTRY_POOL_UNAVAILABLE", self.rank, industry=industry)
        self.reject("INVALID_INPUT", self.rank, context_terms=[])
        self.assertEqual(self.rank(context_terms=["未収録の場面"])["candidates"], [])
        self.assertEqual(self.rank(media_role="WORK_EXPLANATION")["candidates"], [])

    def test_excluded_text_is_not_mistaken_for_positive_suitability(self):
        result = self.rank(context_terms=["剪定"])
        self.assertEqual(result["candidates"], [])
        self.assertIn("NO_RECORDED_CONTEXT_MATCH", result["excluded"][0]["reasons"])

    def test_limited_reject_and_source_issues_are_not_auto_promoted(self):
        for status, code in [("CONTEXT_LIMITED", "CONTEXT_LIMITED_NOT_REQUESTED"), ("REJECT", "SOURCE_REJECTED")]:
            record = deepcopy(self.record)
            record["classification"]["status"] = status
            pool = self.load([record])
            self.assertEqual(self.rank(pool)["candidates"], [])
            self.assertIn(code, self.rank(pool)["excluded"][0]["reasons"])
        record = deepcopy(self.record)
        record["validation_issues"] = ["source issue"]
        self.assertEqual(self.rank(self.load([record]))["candidates"], [])

    def test_recorded_matching_and_usage_exclusions_change_results(self):
        record_b = deepcopy(self.record)
        record_b["asset_id"] = record_b["classification"]["asset_id"] = "SYNTHETIC-B"
        record_b["classification"]["scene"] = "石の庭"
        record_b["classification"]["visual_notes"] = "和風の石材"
        record_b["classification"]["日本の地域造園LPへの適合理由"] = "石組みの情景"
        record_b["near_duplicate_group"] = "SYNTHETIC-GROUP"
        pool = self.load([self.record, record_b])
        self.assertEqual(self.rank(pool, context_terms=["石"])["candidates"][0]["asset_id"], "SYNTHETIC-B")
        self.assertEqual(self.rank(pool, context_terms=["石"], used_near_duplicate_groups=["SYNTHETIC-GROUP"])["candidates"], [])
        self.assertEqual(self.rank(used_asset_ids=["SYNTHETIC-A"])["candidates"], [])
        self.reject("INVALID_INPUT", self.rank, used_near_duplicate_groups=["NONE"])

    def test_pin_local_original_and_preserve_hypothesis_and_nonapproval(self):
        source_before = deepcopy(self.pool)
        manifest = self.build()
        self.assertEqual(manifest["images"]["hero"], {"path": str(self.image), "sha256": self.record["sha256"]})
        self.assertEqual(manifest["selections"][0]["source_record"], self.record)
        self.assertEqual(manifest["selections"][0]["placement"], self.placement)
        self.assertEqual(manifest["context"], {"intake_id": "SYNTHETIC-BUSINESS"})
        self.assertEqual(manifest["crop_validation"], "NOT_RUN")
        self.assertFalse(manifest["production_ready"])
        self.assertFalse(manifest["source_adoption_changed"])
        self.assertEqual(self.pool, source_before)

    def test_missing_wrong_and_replaced_image_bytes_are_rejected(self):
        self.reject("LOCAL_ORIGINAL_MISSING", self.build, local_files={})
        self.image.write_bytes(b"wrong original")
        self.reject("IMAGE_IDENTITY_MISMATCH", self.build)
        self.image.write_bytes(self.image_bytes)
        changed = deepcopy(self.record)
        changed["width"] = 9
        self.reject("IMAGE_METADATA_MISMATCH", self.build, pool=self.load([changed]))

    def test_explicit_limited_rationale_is_retained_but_not_approved(self):
        record = deepcopy(self.record)
        record["classification"]["status"] = "CONTEXT_LIMITED"
        pool = self.load([record])
        self.reject("INVALID_INPUT", self.build, pool=pool)
        placement = {**self.placement, "context_limit_handling": "限定条件を守る仮の配置案。目視確認は未実施。"}
        manifest = self.build([placement], pool=pool)
        self.assertEqual(manifest["selections"][0]["source_record"]["classification"]["status"], "CONTEXT_LIMITED")
        self.assertEqual(manifest["visual_approval"], "NOT_ASSERTED")

    def test_distinct_slots_cannot_silently_repeat_one_original(self):
        repeated = {**self.placement, "slot": "detail"}
        self.reject("REPEATED_ORIGINAL_IMAGE", self.build, [self.placement, repeated])
        self.reject("UNSELECTED_LOCAL_IMAGE", self.build, local_files={"SYNTHETIC-A": self.image, "EXTRA": self.image})

    def test_recorded_near_duplicates_are_not_used_together(self):
        record_a = deepcopy(self.record)
        record_a["near_duplicate_group"] = "KNOWN-NEAR-GROUP"
        record_b = deepcopy(record_a)
        record_b["asset_id"] = record_b["classification"]["asset_id"] = "SYNTHETIC-B"
        pool = self.load([record_a, record_b])
        placements = [self.placement, {**self.placement, "asset_id": "SYNTHETIC-B", "slot": "detail"}]
        self.reject("REPEATED_NEAR_GROUP", self.build, placements, pool=pool,
                    local_files={"SYNTHETIC-A": self.image, "SYNTHETIC-B": self.image})

    def composition(self):
        return {"schema_version": "lp54-composition-input/v1", "company": {"industry": "landscape", "parts": {
            "hero": {"title": "元の見出し", "body": "元の長い説明。", "note": "既存の注記。" + ILLUSTRATIVE_DISCLOSURE}}},
            "selection": {"theme_id": "garden-life", "design_ids": ["hero-02"]}, "images": {},
            "context": {"p01": {"status": "HYPOTHESIS"}}}

    def test_attachment_retains_copy_and_context_and_checks_visible_label(self):
        payload = self.composition()
        before = deepcopy(payload)
        selection = self.build()
        attached = attach_preview_assets(payload, selection)
        self.assertEqual(attached["company"], payload["company"])
        self.assertEqual(attached["context"]["p01"], payload["context"]["p01"])
        self.assertEqual(attached["context"]["asset_selection"], selection)
        self.assertEqual(attached["images"], selection["images"])
        self.assertEqual(payload, before)
        payload["company"]["parts"]["hero"]["note"] = ""
        self.reject("ILLUSTRATIVE_LABEL_MISSING", attach_preview_assets, payload, selection)

    def test_manifest_tamper_and_existing_bindings_are_not_accepted(self):
        selection = self.build()
        changed = deepcopy(selection)
        changed["production_ready"] = True
        self.reject("SELECTION_MANIFEST_CHANGED", attach_preview_assets, self.composition(), changed)
        payload = self.composition()
        payload["images"] = {"hero": {"path": "old.png", "sha256": "0" * 64}}
        self.reject("EXISTING_IMAGE_BINDINGS", attach_preview_assets, payload, selection)
        payload = self.composition()
        payload["context"]["asset_selection"] = {"previous": True}
        self.reject("EXISTING_SELECTION_CONTEXT", attach_preview_assets, payload, selection)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the static composition bridge")
    def test_pool_original_to_selection_to_composition_keeps_image_and_conditions(self):
        source = self.root / "synthetic-source"
        synthetic_source(source)
        payload = payload_for(self.image)
        payload["images"] = {}
        payload["company"]["parts"]["hero"]["note"] += ILLUSTRATIVE_DISCLOSURE
        selection = self.build()
        attached = attach_preview_assets(payload, selection)
        output = self.root / "composition"
        trace = compose_preview(attached, source_root=source, output_dir=output)
        binding = validate_composed_asset_usage(selection, trace)
        self.assertEqual(trace["images"][0]["sha256"], self.record["sha256"])
        self.assertEqual(trace["context"]["asset_selection"], selection)
        self.assertEqual(trace["quality_status"], "NOT_RUN")
        self.assertIn(ILLUSTRATIVE_DISCLOSURE, (output / "index.html").read_text())
        self.assertFalse(trace["production_ready"])
        self.assertEqual(binding["bindings"], [{"slot": "hero", "parts": ["hero"], "sha256": self.record["sha256"]}])
        self.assertEqual(binding["quality_status"], "NOT_RUN")

    @unittest.skipUnless(shutil.which("node"), "Node.js is required for the static composition bridge")
    def test_wrong_declared_part_passes_no_actual_usage_check(self):
        source = self.root / "synthetic-source"
        synthetic_source(source)
        payload = payload_for(self.image)
        payload["images"] = {}
        payload["company"]["parts"]["faq"]["note"] += ILLUSTRATIVE_DISCLOSURE
        selection = self.build([{**self.placement, "parts": ["faq"]}])
        attached = attach_preview_assets(payload, selection)
        trace = compose_preview(attached, source_root=source, output_dir=self.root / "wrong-part")
        self.reject("COMPOSED_IMAGE_PART_MISMATCH", validate_composed_asset_usage, selection, trace)

    def test_undeclared_reuse_and_hash_or_context_changes_are_rejected(self):
        selection = self.build()
        trace = {"context": {"asset_selection": selection},
                 "images": [{"slot": "hero", "sha256": self.record["sha256"]}],
                 "sections": [{"part": "hero", "image_slots": ["hero"]},
                              {"part": "faq", "image_slots": ["hero"]}]}
        self.reject("COMPOSED_IMAGE_PART_MISMATCH", validate_composed_asset_usage, selection, trace)
        trace["sections"][1]["image_slots"] = []
        self.assertEqual(validate_composed_asset_usage(selection, trace)["state"], "STATIC_BINDING_MATCH")
        trace["images"][0]["sha256"] = "0" * 64
        self.reject("COMPOSED_IMAGE_IDENTITY_MISMATCH", validate_composed_asset_usage, selection, trace)
        trace["context"] = {}
        self.reject("COMPOSED_SELECTION_CONTEXT_MISMATCH", validate_composed_asset_usage, selection, trace)
