"""Synthetic delivery tests; no real company, browser, or network request."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from lp_engine.artifact_handoff import HandoffError, build_handoff_manifest, receive_artifacts
from lp_engine.pilot_asset_selection import (
    AssetSelectionError, ILLUSTRATIVE_DISCLOSURE, build_preview_asset_selection,
    load_landscaping_pool,
)
from lp_engine.pilot_authoring import AuthoringError, build_theme_design_brief
from lp_engine.pilot_composition import CompositionError, compose_preview
from lp_engine.pilot_delivery import DeliveryError, PREVIEW_FILES, deliver_selected_preview
from test_pilot_authoring import synthetic_authoring, synthetic_intake
from test_pilot_composition import payload_for, synthetic_source


@unittest.skipUnless(shutil.which("node"), "Node.js is required for the static composition bridge")
class SelectedPreviewDeliveryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.staging = self.root / "staging"
        self.staging.mkdir()
        self.receiver = self.root / "receiver"
        self.source = self.root / "synthetic-source"
        synthetic_source(self.source)
        self.image = self.root / "synthetic.png"
        Image.new("RGB", (8, 6), "#123456").save(self.image)
        self.image_bytes = self.image.read_bytes()
        self.image_sha = hashlib.sha256(self.image_bytes).hexdigest()
        # Establish the synthetic source's baseline before later failure tests
        # change its bytes or supply a different expected pin.
        baseline = compose_preview(payload_for(self.image), source_root=self.source,
                                   output_dir=self.root / "source-baseline")
        self.source_sha = baseline["source_bundle_sha256"]
        self.intake = synthetic_intake("landscape")
        authoring = synthetic_authoring(self.intake)
        authoring["fields"][0]["value"] = "造園を題材にした合成テストの事業領域"
        self.brief = build_theme_design_brief(self.intake, authoring)
        self.composition = payload_for(self.image)
        self.composition["images"] = {}
        for part in self.composition["company"]["parts"].values():
            part["note"] += ILLUSTRATIVE_DISCLOSURE
        self.context = {"intake_id": self.intake["intake_id"], "existing_attempt": 1}
        record = {
            "asset_id": "SYNTHETIC-A", "source_page": "https://example.test/photo",
            "license_url": "https://example.test/license", "sha256": self.image_sha,
            "bytes": len(self.image_bytes), "width": 8, "height": 6,
            "adoption_status": "CANDIDATE", "company_project_staff_evidence_allowed": False,
            "full_resolution_visual_review": False, "pc_sp_crop_validation": "NOT_PERFORMED",
            "classification": {
                "asset_id": "SYNTHETIC-A", "scene": "住宅と庭の全景",
                "usable_roles": "HERO_BRAND", "excluded_uses": "会社施工実績の証拠",
                "visual_notes": "住宅と植栽を表す合成入力。",
                "日本の地域造園LPへの適合理由": "住宅と庭の導入用。",
                "人物や会社実績誤認防止": "第三者イメージ。施工会社の実績ではない。",
                "status": "READY_FOR_SELECTION",
            },
            "storage": {"archive_part": "SYNTHETIC.zip", "member_path": "synthetic.png",
                        "member_sha256": self.image_sha},
            "near_duplicate_group": None, "validation_issues": [],
        }
        pool_path = self.root / "synthetic-pool.json"
        pool_path.write_text(json.dumps({"version": "SYNTHETIC_POOL", "records": [record]}, ensure_ascii=False))
        self.pool = load_landscaping_pool(pool_path, expected_sha256=hashlib.sha256(pool_path.read_bytes()).hexdigest())
        self.selection = self.select(["hero"])

    def select(self, parts):
        return build_preview_asset_selection(
            self.pool,
            placements=[{"slot": "hero", "asset_id": "SYNTHETIC-A", "media_role": "HERO_BRAND",
                         "context_terms": ["住宅", "庭"], "parts": parts,
                         "selection_reason": "住宅の庭を考える合成入力のため。"}],
            local_files={"SYNTHETIC-A": self.image}, context=self.context,
        )

    def deliver(self, **overrides):
        args = {
            "brief": self.brief, "composition": self.composition, "asset_selection": self.selection,
            "source_root": self.source, "expected_source_sha256": self.source_sha,
            "receiver_dir": self.receiver, "revision": "synthetic-r1", "expected_revision": "synthetic-r1",
            "handoff_context": self.context, "expected_context": self.context, "staging_parent": self.staging,
        }
        args.update(overrides)
        return deliver_selected_preview(**args)

    def receipt_count(self):
        if not (self.receiver / "handoff.sqlite").exists():
            return 0
        with sqlite3.connect(self.receiver / "handoff.sqlite") as db:
            return db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]

    def assert_empty_attempt(self):
        self.assertEqual(list(self.staging.iterdir()), [])
        self.assertEqual(self.receipt_count(), 0)
        if (self.receiver / "deliveries").exists():
            self.assertEqual(list((self.receiver / "deliveries").iterdir()), [])

    def test_receipt_pins_checked_preview_and_preserves_original_inputs(self):
        originals = deepcopy((self.brief, self.composition, self.selection, self.context))
        result = self.deliver()
        receipt = result["artifact_receipt"]
        saved = Path(result["preview_dir"])
        self.assertEqual({path.name for path in saved.iterdir()}, set(PREVIEW_FILES))
        self.assertEqual({pin["path"] for pin in receipt["manifest"]["files"]}, set(PREVIEW_FILES))
        self.assertEqual(receipt["scope"], "ARTIFACT_ONLY")
        self.assertEqual(receipt["quality_status"], "NOT_RUN")
        self.assertFalse(receipt["stage_receipt_issued"])
        self.assertEqual(result["scope"], "INTERNAL_COMPOSITION_PREVIEW")
        self.assertFalse(result["production_ready"])
        self.assertEqual(receipt["manifest"]["context"], self.context)
        request = json.loads((saved / "composition_input.json").read_bytes())
        trace = json.loads((saved / "composition_manifest.json").read_bytes())
        usage = json.loads((saved / "asset_usage_check.json").read_bytes())
        self.assertEqual(request["context"]["p01_design_brief"], self.brief)
        self.assertEqual(request["context"]["asset_selection"], self.selection)
        self.assertEqual(request["company"], self.composition["company"])
        self.assertEqual(request["images"]["hero"]["path"], str(self.image))
        self.assertEqual(trace["context"], request["context"])
        self.assertEqual(trace["source_bundle_sha256"], self.source_sha)
        self.assertEqual(usage["state"], "STATIC_BINDING_MATCH")
        self.assertEqual(usage["selection_manifest_sha256"], self.selection["manifest_sha256"])
        self.assertEqual(usage["bindings"], [{"slot": "hero", "parts": ["hero"], "sha256": self.image_sha}])
        self.assertFalse(usage["formal_gate_issued"])
        for pin in receipt["manifest"]["files"]:
            binary = (saved / pin["path"]).read_bytes()
            self.assertEqual(len(binary), pin["bytes"])
            self.assertEqual(hashlib.sha256(binary).hexdigest(), pin["sha256"])
            self.assertNotIn(b".lp-selected-delivery-", binary)
        self.assertEqual((self.brief, self.composition, self.selection, self.context), originals)
        self.assertEqual(list(self.staging.iterdir()), [])

    def test_same_inputs_regenerate_and_return_exact_first_receipt(self):
        first = self.deliver()
        before = {path.name: path.read_bytes() for path in Path(first["preview_dir"]).iterdir()}
        second = self.deliver()
        self.assertEqual(first, second)
        self.assertEqual(self.receipt_count(), 1)
        self.assertEqual(before, {path.name: path.read_bytes() for path in Path(second["preview_dir"]).iterdir()})

    def test_actual_image_part_mismatch_never_calls_receiver(self):
        selection = self.select(["faq"])
        with patch("lp_engine.pilot_delivery.receive_artifacts") as receiver:
            with self.assertRaises(AssetSelectionError) as caught:
                self.deliver(asset_selection=selection)
            self.assertEqual(caught.exception.code, "COMPOSED_IMAGE_PART_MISMATCH")
            receiver.assert_not_called()
        self.assert_empty_attempt()

    def test_changed_brief_selection_and_reserved_context_fail_before_receive(self):
        changed_brief = deepcopy(self.brief)
        changed_brief["design_reference"]["keywords"] = ["後から改変した方向"]
        changed_selection = deepcopy(self.selection)
        changed_selection["context"]["existing_attempt"] = 2
        reserved_brief = deepcopy(self.composition)
        reserved_brief["context"]["p01_design_brief"] = deepcopy(self.brief)
        reserved_selection = deepcopy(self.composition)
        reserved_selection["context"]["asset_selection"] = deepcopy(self.selection)
        for overrides in ({"brief": changed_brief}, {"asset_selection": changed_selection},
                          {"composition": reserved_brief}, {"composition": reserved_selection}):
            with self.subTest(overrides=list(overrides)), patch("lp_engine.pilot_delivery.receive_artifacts") as receiver:
                with self.assertRaises((AuthoringError, AssetSelectionError)):
                    self.deliver(**overrides)
                receiver.assert_not_called()
                self.assert_empty_attempt()

    def test_missing_or_changed_images_and_sources_never_issue_a_receipt(self):
        runtime = self.source / "src/runtime.js"
        runtime_bytes = runtime.read_bytes()
        cases = [
            (lambda: self.image.unlink(), {}, "IMAGE_READ_ERROR"),
            (lambda: self.image.write_bytes(b"changed original"), {}, "IMAGE_HASH_MISMATCH"),
            (lambda: runtime.unlink(), {}, "SOURCE_READ_ERROR"),
            (lambda: runtime.write_bytes(runtime_bytes + b"\n/* changed */"), {}, "SOURCE_HASH_MISMATCH"),
            (lambda: None, {"expected_source_sha256": None}, "SOURCE_PIN_REQUIRED"),
        ]
        for prepare, overrides, code in cases:
            with self.subTest(code=code), patch("lp_engine.pilot_delivery.receive_artifacts") as receiver:
                self.image.write_bytes(self.image_bytes)
                runtime.write_bytes(runtime_bytes)
                prepare()
                with self.assertRaises((CompositionError, DeliveryError)) as caught:
                    self.deliver(**overrides)
                self.assertEqual(caught.exception.code, code)
                receiver.assert_not_called()
                self.assert_empty_attempt()

    def test_expected_revision_and_context_are_checked_by_existing_receiver(self):
        for overrides, code in [({"expected_revision": "synthetic-r2"}, "REVISION_MISMATCH"),
                                ({"expected_context": {"existing_attempt": 2}}, "CONTEXT_MISMATCH")]:
            with self.subTest(code=code), self.assertRaises(HandoffError) as caught:
                self.deliver(**overrides)
            self.assertEqual(caught.exception.code, code)
            self.assert_empty_attempt()

    def test_staged_change_before_pinning_is_not_reaccepted_as_new_content(self):
        for name in PREVIEW_FILES:
            def changed_manifest(source_dir, files, **kwargs):
                path = Path(source_dir) / name
                path.write_bytes(path.read_bytes() + b" ")
                return build_handoff_manifest(source_dir, files, **kwargs)

            with self.subTest(file=name), patch("lp_engine.pilot_delivery.build_handoff_manifest", side_effect=changed_manifest):
                with patch("lp_engine.pilot_delivery.receive_artifacts") as receiver:
                    with self.assertRaises(DeliveryError) as caught:
                        self.deliver()
                    self.assertEqual(caught.exception.code, "STAGED_CONTENT_MISMATCH")
                    receiver.assert_not_called()
                self.assert_empty_attempt()

    def test_change_after_pinning_is_rejected_during_copy(self):
        def changed_receive(**kwargs):
            (Path(kwargs["source_dir"]) / "index.html").write_bytes(b"changed after producer pin")
            return receive_artifacts(**kwargs)

        with patch("lp_engine.pilot_delivery.receive_artifacts", side_effect=changed_receive):
            with self.assertRaises(HandoffError) as caught:
                self.deliver()
            self.assertEqual(caught.exception.code, "CONTENT_MISMATCH")
        self.assert_empty_attempt()

    def test_resolved_receiver_and_staging_overlap_is_rejected_without_deleting_existing_files(self):
        self.receiver.mkdir()
        existing = self.receiver / "existing.txt"
        existing.write_bytes(b"prior output must survive")
        alias = self.root / "receiver-alias"
        alias.symlink_to(self.receiver, target_is_directory=True)
        for staging_parent in (self.receiver, alias):
            with self.subTest(path=str(staging_parent)), patch("lp_engine.pilot_delivery.receive_artifacts") as receiver:
                with self.assertRaises(DeliveryError) as caught:
                    self.deliver(staging_parent=staging_parent)
                self.assertEqual(caught.exception.code, "OVERLAPPING_DELIVERY_PATHS")
                receiver.assert_not_called()
                self.assertEqual(existing.read_bytes(), b"prior output must survive")
                self.assertEqual([path.name for path in self.receiver.iterdir()], ["existing.txt"])
        self.assert_empty_attempt()

    def test_failed_retry_preserves_completed_files_and_historical_receipt(self):
        first = self.deliver()
        saved = Path(first["preview_dir"])
        before = {path.name: path.read_bytes() for path in saved.iterdir()}
        receipt_path = saved.parent / "receipt.json"
        prior_receipt = receipt_path.read_bytes()
        self.image.unlink()
        with self.assertRaises(CompositionError):
            self.deliver()
        self.assertEqual(self.receipt_count(), 1)
        self.assertEqual(prior_receipt, receipt_path.read_bytes())
        self.assertEqual(before, {path.name: path.read_bytes() for path in saved.iterdir()})
        self.assertEqual(list(self.staging.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
