"""Synthetic original bytes and source-schema fixtures; no external services."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

from PIL import Image

from lp_engine.pilot_asset_extraction import AssetExtractionError, extract_pool_originals
from lp_engine.pilot_asset_selection import AssetSelectionError, build_preview_asset_selection, load_landscaping_pool


class PilotAssetExtractionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = self.root / "extracted"
        self.index = {"schema_version": 1, "version": "SYNTHETIC_POOL", "records": [], "archive_parts": [],
                      "collection_closed": {"new_search_download_allowed": False}}
        self.local_archives, self.images = {}, {}
        for number, image_format in enumerate(("PNG", "JPEG")):
            asset_id = f"SYNTHETIC-{number}"
            member = f"assets/synthetic-{number}." + ("png" if image_format == "PNG" else "jpg")
            archive_name = f"synthetic-{number}.zip"
            stream = io.BytesIO()
            Image.new("RGB", (8 + number, 6), (20, 60, 90)).save(stream, format=image_format)
            raw = stream.getvalue()
            self.images[asset_id] = raw
            record = {
                "asset_id": asset_id, "source_page": "https://example.test/photo",
                "license_url": "https://example.test/license", "author": "Synthetic fixture",
                "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "width": 8 + number, "height": 6,
                "file_name": member.rsplit("/", 1)[-1], "asset_file": member, "archive_part": archive_name,
                "adoption_status": "CANDIDATE", "company_project_staff_evidence_allowed": False,
                "full_resolution_visual_review": False, "pc_sp_crop_validation": "NOT_PERFORMED",
                "classification": {"asset_id": asset_id, "scene": "住宅と庭の全景", "usable_roles": "HERO_BRAND,DETAIL_QUALITY",
                    "excluded_uses": "会社施工実績", "visual_notes": "住宅と庭の合成入力",
                    "日本の地域造園LPへの適合理由": "住宅と庭の導入用",
                    "人物や会社実績誤認防止": "第三者イメージ", "status": "READY_FOR_SELECTION"},
                "storage": {"archive_part": archive_name, "member_path": member,
                            "member_sha256": hashlib.sha256(raw).hexdigest(), "local_original": "NOT_MATERIALIZED"},
                "validation_issues": [], "near_duplicate_group": None, "unknown_source_field": {"keep": [1, 2]},
            }
            self.index["records"].append(record)
            self.index["archive_parts"].append({"file" if number == 0 else "name": archive_name,
                                                "count": 1, "storage_receipt": {"status": "INHERITED_VERIFIED"}})
            path = self.root / archive_name
            self.local_archives[archive_name] = path
            self.replace_archive(number, [(member, raw), ("unrequested.txt", b"not an image or a selected member")])
        self.pool = self.load()

    def replace_archive(self, number, entries=None, *, raw=None):
        part = self.index["archive_parts"][number]
        name = part.get("file") or part.get("name")
        path = self.local_archives[name]
        if raw is None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
                    for member, content in entries:
                        archive.writestr(member, content)
            raw = path.read_bytes()
        else:
            path.write_bytes(raw)
        part.update({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        for record in self.index["records"]:
            if record["archive_part"] == name:
                record["storage"]["archive_sha256"] = part["sha256"]

    def load(self):
        raw = json.dumps(self.index, ensure_ascii=False).encode()
        path = self.root / "pool.json"
        path.write_bytes(raw)
        return load_landscaping_pool(path, expected_sha256=hashlib.sha256(raw).hexdigest())

    def extract(self, **changes):
        args = {"pool": self.pool, "asset_ids": ["SYNTHETIC-0", "SYNTHETIC-1"],
                "archive_files": self.local_archives, "output_dir": self.output}
        args.update(changes)
        return extract_pool_originals(**args)

    def reject(self, code, **changes):
        with self.assertRaises(AssetExtractionError) as caught:
            self.extract(**changes)
        self.assertEqual(caught.exception.code, code)
        self.assertFalse(self.output.exists())

    def test_png_jpeg_extract_exact_originals_and_connect_to_existing_selection(self):
        before = deepcopy(self.pool)
        result = self.extract()
        self.assertEqual(set(result), {"local_files", "extraction_receipt"})
        for asset_id, path in result["local_files"].items():
            self.assertEqual(Path(path).read_bytes(), self.images[asset_id])
        self.assertEqual(sorted(p.name for p in (self.output / "assets").iterdir()), ["synthetic-0.png", "synthetic-1.jpg"])
        self.assertFalse((self.output / "unrequested.txt").exists())
        receipt = result["extraction_receipt"]
        self.assertEqual(json.loads((self.output / "extraction_receipt.json").read_text()), receipt)
        self.assertEqual([item["source_record"] for item in receipt["files"]], self.pool["index"]["records"])
        self.assertEqual([item["source_archive"] for item in receipt["files"]], self.pool["index"]["archive_parts"])
        self.assertEqual([item["binary_check"]["format"] for item in receipt["files"]], ["PNG", "JPEG"])
        self.assertEqual((receipt["scope"], receipt["quality_status"]), ("ARTIFACT_ONLY", "NOT_RUN"))
        self.assertFalse(receipt["stage_receipt_issued"])
        self.assertFalse(receipt["formal_gate_issued"])
        self.assertFalse(receipt["production_ready"])
        self.assertEqual(self.pool, before)
        placements = [{"asset_id": f"SYNTHETIC-{n}", "slot": slot, "media_role": "HERO_BRAND",
                       "context_terms": ["住宅"], "parts": ["hero"], "selection_reason": "Synthetic placement rationale"}
                      for n, slot in enumerate(("hero", "detail"))]
        selected = build_preview_asset_selection(self.pool, placements=placements, local_files=result["local_files"],
                                                context={"status": "SYNTHETIC_ONLY"})
        self.assertEqual(selected["selections"][0]["source_record"], before["index"]["records"][0])
        self.assertFalse(selected["source_adoption_changed"])

    def test_one_requested_image_does_not_read_other_archive_or_adopt_rejected_source(self):
        self.index["records"][0]["classification"]["status"] = "REJECT"
        self.index["records"][0]["adoption_status"] = "REJECTED"
        pool = self.load()
        self.local_archives["synthetic-1.zip"].unlink()
        result = self.extract(pool=pool, asset_ids=["SYNTHETIC-0"],
                              archive_files={"synthetic-0.zip": self.local_archives["synthetic-0.zip"]})
        self.assertEqual(list(result["local_files"]), ["SYNTHETIC-0"])
        record = result["extraction_receipt"]["files"][0]["source_record"]
        self.assertEqual(record["adoption_status"], "REJECTED")
        self.assertEqual(record["classification"]["status"], "REJECT")
        with self.assertRaises(AssetSelectionError) as caught:
            build_preview_asset_selection(pool, placements=[{"asset_id": "SYNTHETIC-0", "slot": "hero",
                "media_role": "HERO_BRAND", "context_terms": ["住宅"], "parts": ["hero"], "selection_reason": "Fixture"}],
                local_files=result["local_files"], context={})
        self.assertEqual(caught.exception.code, "INELIGIBLE_ASSET_SELECTION")

    def test_changed_pool_unknown_duplicate_ids_and_archive_set_are_rejected(self):
        changed = deepcopy(self.pool)
        changed["index"]["records"][0]["storage"]["member_path"] = "different.png"
        with self.assertRaises(AssetSelectionError) as caught:
            self.extract(pool=changed)
        self.assertEqual(caught.exception.code, "POOL_SNAPSHOT_CHANGED")
        for code, changes in [
            ("INVALID_ASSET_IDS", {"asset_ids": []}), ("INVALID_ASSET_IDS", {"asset_ids": "SYNTHETIC-0"}),
            ("DUPLICATE_ASSET_ID", {"asset_ids": ["SYNTHETIC-0", "SYNTHETIC-0"]}),
            ("ASSET_NOT_IN_POOL", {"asset_ids": ["UNKNOWN"]}),
            ("ARCHIVE_SET_MISMATCH", {"archive_files": {}}),
            ("ARCHIVE_SET_MISMATCH", {"archive_files": {**self.local_archives, "extra.zip": self.root / "unused.zip"}}),
        ]:
            with self.subTest(code=code, changes=changes):
                self.reject(code, **changes)

    def test_source_archive_metadata_and_record_storage_must_agree(self):
        original = deepcopy(self.index)
        cases = [
            ("ARCHIVE_METADATA_MISSING", lambda d: d.pop("archive_parts")),
            ("DUPLICATE_ARCHIVE_NAME", lambda d: d["archive_parts"].append(deepcopy(d["archive_parts"][0]))),
            ("AMBIGUOUS_ARCHIVE_NAME", lambda d: d["archive_parts"][0].update(name="other.zip")),
            ("INVALID_ARCHIVE_METADATA", lambda d: d["archive_parts"][0].update(bytes=True)),
            ("SOURCE_STORAGE_MISMATCH", lambda d: d["records"][0]["storage"].update(archive_sha256="0" * 64)),
            ("SOURCE_STORAGE_MISMATCH", lambda d: d["records"][0].update(asset_file="different.png")),
        ]
        for code, edit in cases:
            with self.subTest(code=code):
                self.index = deepcopy(original)
                edit(self.index)
                self.reject(code, pool=self.load())

    def test_local_archive_hash_size_missing_file_and_symlink_are_rejected(self):
        path = self.local_archives["synthetic-0.zip"]
        original = path.read_bytes()
        for binary in (original + b"extra", b"x" * len(original)):
            path.write_bytes(binary)
            self.reject("ARCHIVE_IDENTITY_MISMATCH")
        path.unlink()
        self.reject("LOCAL_ARCHIVE_UNAVAILABLE")
        target = self.root / "other.zip"
        target.write_bytes(original)
        path.symlink_to(target)
        self.reject("INVALID_LOCAL_PATH")
        path.unlink()
        path.mkdir()
        self.reject("INVALID_LOCAL_ARCHIVE")

    def test_member_path_escape_and_output_name_collision_are_rejected(self):
        original = deepcopy(self.index)
        for member in ("../escape.png", "/absolute.png", "assets/../../escape.png", "assets\\escape.png", "C:escape.png", "assets/./same.png", "assets/one\x00two.png"):
            with self.subTest(member=member):
                self.index = deepcopy(original)
                self.index["records"][0]["storage"]["member_path"] = member
                self.index["records"][0]["asset_file"] = member
                self.reject("UNSAFE_MEMBER_PATH", pool=self.load())
        self.index = deepcopy(original)
        second = self.index["records"][1]
        second["storage"]["member_path"] = second["asset_file"] = "another/SYNTHETIC-0.PNG"
        self.reject("OUTPUT_NAME_CONFLICT", pool=self.load())
        self.assertFalse((self.root / "escape.png").exists())

    def test_missing_duplicate_case_alias_and_nonregular_members_are_rejected(self):
        member = self.index["records"][0]["storage"]["member_path"]
        image = self.images["SYNTHETIC-0"]
        cases = [("MEMBER_NOT_UNIQUE", [("unrelated.txt", b"unused")]),
                 ("MEMBER_NOT_UNIQUE", [(member, image), (member, image)]),
                 ("MEMBER_NOT_UNIQUE", [(member, image), (member.upper(), image)])]
        for kind in (stat.S_IFLNK, stat.S_IFDIR, stat.S_IFIFO):
            info = zipfile.ZipInfo(member)
            info.create_system = 3
            info.external_attr = (kind | 0o600) << 16
            cases.append(("INVALID_ARCHIVE_MEMBER", [(info, image)]))
        for code, entries in cases:
            with self.subTest(code=code, entries=str(entries)[:90]):
                self.replace_archive(0, entries)
                self.reject(code, pool=self.load())

    def test_invalid_zip_crc_and_member_hash_do_not_leave_partial_output(self):
        self.replace_archive(1, raw=b"not a zip")
        self.reject("INVALID_ARCHIVE_BYTES", pool=self.load())
        member = self.index["records"][1]["storage"]["member_path"]
        image = self.images["SYNTHETIC-1"]
        self.replace_archive(1, [(member, image)])
        path = self.local_archives["synthetic-1.zip"]
        raw = bytearray(path.read_bytes())
        start = raw.index(image)
        raw[start + 8] ^= 1
        self.replace_archive(1, raw=bytes(raw))
        self.reject("INVALID_ARCHIVE_BYTES", pool=self.load())
        self.replace_archive(1, [(member, image)])
        self.index["records"][1]["sha256"] = self.index["records"][1]["storage"]["member_sha256"] = "0" * 64
        self.reject("MEMBER_IDENTITY_MISMATCH", pool=self.load())

    def test_raw_member_name_with_nul_cannot_alias_safe_recorded_prefix(self):
        # Both the local header and central directory keep the same lengths.
        # ZipInfo.filename truncates this raw name while orig_filename does not.
        path = self.local_archives["synthetic-0.zip"]
        raw = path.read_bytes().replace(b"assets/synthetic-0.png", b"assets/synthetic-0\x00png")
        self.replace_archive(0, raw=raw)
        self.index["records"][0]["storage"]["member_path"] = "assets/synthetic-0"
        self.index["records"][0]["asset_file"] = "assets/synthetic-0"
        self.reject("UNSAFE_MEMBER_PATH", pool=self.load())

    def test_valid_pins_do_not_turn_nonimages_wrong_dimensions_or_gif_into_images(self):
        original = deepcopy(self.index)
        member = self.index["records"][0]["storage"]["member_path"]
        gif = io.BytesIO()
        Image.new("RGB", (8, 6)).save(gif, format="GIF")
        for raw, code in [(b"not an image", "INVALID_IMAGE_BYTES"), (gif.getvalue(), "IMAGE_METADATA_MISMATCH")]:
            with self.subTest(code=code):
                self.index = deepcopy(original)
                self.replace_archive(0, [(member, raw)])
                self.index["records"][0].update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                self.index["records"][0]["storage"]["member_sha256"] = hashlib.sha256(raw).hexdigest()
                self.reject(code, pool=self.load())
        self.index = deepcopy(original)
        self.replace_archive(0, [(member, self.images["SYNTHETIC-0"])])
        self.index["records"][0]["width"] += 1
        self.reject("IMAGE_METADATA_MISMATCH", pool=self.load())

    def test_existing_output_is_preserved_even_if_created_during_validation(self):
        self.output.mkdir()
        sentinel = self.output / "prior.txt"
        sentinel.write_bytes(b"prior output")
        with self.assertRaises(AssetExtractionError) as caught:
            self.extract()
        self.assertEqual(caught.exception.code, "OUTPUT_EXISTS")
        self.assertEqual(sentinel.read_bytes(), b"prior output")
        sentinel.unlink()
        self.output.rmdir()
        from lp_engine.pilot_asset_extraction import _image_check
        def concurrent_output(raw, record):
            result = _image_check(raw, record)
            if not self.output.exists():
                self.output.mkdir()
                sentinel.write_bytes(b"concurrent output")
            return result
        with patch("lp_engine.pilot_asset_extraction._image_check", side_effect=concurrent_output):
            with self.assertRaises(FileExistsError):
                self.extract()
        self.assertEqual(sentinel.read_bytes(), b"concurrent output")

    def test_write_failure_and_written_byte_change_clean_only_new_output(self):
        original_open = Path.open
        def fail_receipt(path, *args, **kwargs):
            if path == self.output / "extraction_receipt.json":
                raise OSError("Synthetic write failure")
            return original_open(path, *args, **kwargs)
        with patch.object(Path, "open", fail_receipt):
            with self.assertRaises(OSError):
                self.extract()
        self.assertFalse(self.output.exists())
        original_read = Path.read_bytes
        def corrupt_written_image(path):
            raw = original_read(path)
            if path.parent == self.output / "assets":
                path.write_bytes(raw + b"unexpected")
                return original_read(path)
            return raw
        with patch.object(Path, "read_bytes", corrupt_written_image):
            self.reject("OUTPUT_IDENTITY_MISMATCH")
        self.assertTrue(all(path.is_file() for path in self.local_archives.values()))

    def test_zip_uses_the_verified_snapshot_even_if_source_path_later_changes(self):
        original_zipfile = zipfile.ZipFile
        archive_path = self.local_archives["synthetic-0.zip"]
        def changed_path(snapshot, *args, **kwargs):
            archive_path.write_bytes(b"source path replaced after snapshot")
            return original_zipfile(snapshot, *args, **kwargs)
        with patch("lp_engine.pilot_asset_extraction.zipfile.ZipFile", side_effect=changed_path):
            result = self.extract()
        self.assertEqual(Path(result["local_files"]["SYNTHETIC-0"]).read_bytes(), self.images["SYNTHETIC-0"])


if __name__ == "__main__":
    unittest.main()
