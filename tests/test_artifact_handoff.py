import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from lp_engine.artifact_handoff import HandoffError, build_handoff_manifest, receive_artifacts


class ArtifactHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.producer = self.root / "producer"
        (self.producer / "assets").mkdir(parents=True)
        self.payloads = {
            "index.html": b'<html lang="ja"><h1>Fixture only</h1></html>',
            "assets/style.css": b"h1 { color: #123; }\n",
            "stage_receipt.json": b'{"status":"READY_FOR_GATE","self_check_completed":true,"known_issues":["fixture"]}\n',
        }
        for name, body in self.payloads.items():
            (self.producer / name).write_bytes(body)
        self.context = {"company_id": "fixture-company", "batch_id": "fixture-batch", "stage_id": "P20", "attempt": 1}
        self.sources = {"index.html": {"source_ref": "fixture:source", "version": 0}}
        self.manifest = build_handoff_manifest(self.producer, list(self.payloads), revision="fixture-r1",
                                               context=self.context, sources=self.sources)
        self.receiver = self.root / "receiver"

    def receive(self, **overrides):
        args = {"source_dir": self.producer, "manifest": self.manifest, "receiver_dir": self.receiver,
                "expected_revision": "fixture-r1", "expected_context": self.context}
        args.update(overrides)
        return receive_artifacts(**args)

    def receipt_count(self):
        if not (self.receiver / "handoff.sqlite").exists():
            return 0
        with sqlite3.connect(self.receiver / "handoff.sqlite") as db:
            return db.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]

    def test_receive_preserves_bytes_sources_and_quality_boundary(self):
        original_manifest = copy.deepcopy(self.manifest)
        receipt = self.receive()
        self.assertEqual(receipt["status"], "ARTIFACT_RECEIVED")
        self.assertEqual(receipt["scope"], "ARTIFACT_ONLY")
        self.assertEqual(receipt["quality_status"], "NOT_RUN")
        self.assertFalse(receipt["automatic_downstream_execution"])
        self.assertFalse(receipt["stage_receipt_issued"])
        self.assertEqual(self.manifest, original_manifest)
        for pin in receipt["manifest"]["files"]:
            data = (self.receiver / receipt["storage_subdir"] / pin["path"]).read_bytes()
            self.assertEqual(data, self.payloads[pin["path"]])
            self.assertEqual(hashlib.sha256(data).hexdigest(), pin["sha256"])
        self.assertEqual(next(p for p in receipt["manifest"]["files"] if p["path"] == "index.html")["source"], self.sources["index.html"])
        self.assertIsNone(next(p for p in receipt["manifest"]["files"] if p["path"] == "assets/style.css")["source"])
        self.assertEqual((self.producer / "stage_receipt.json").read_bytes(), self.payloads["stage_receipt.json"])

    def test_redelivery_returns_first_receipt_across_new_connections(self):
        first = self.receive()
        second = self.receive()
        self.assertEqual(first, second)
        self.assertEqual(self.receipt_count(), 1)
        stored = self.receiver / "deliveries" / first["delivery_key"] / "receipt.json"
        self.assertEqual(json.loads(stored.read_bytes()), first)

    def test_revision_or_context_mismatch_creates_no_receipt(self):
        for overrides, code in [({"expected_revision": "fixture-r2"}, "REVISION_MISMATCH"),
                                ({"expected_context": {"company_id": "another-fixture"}}, "CONTEXT_MISMATCH"),
                                ({"expected_context": {"attempt": True}}, "CONTEXT_MISMATCH")]:
            with self.subTest(code=code), self.assertRaises(HandoffError) as raised:
                self.receive(**overrides)
            self.assertEqual(raised.exception.code, code)
            self.assertEqual(self.receipt_count(), 0)

    def test_changed_source_rejects_first_receive_and_redelivery(self):
        (self.producer / "index.html").write_bytes(b"changed input")
        with self.assertRaises(HandoffError) as raised:
            self.receive()
        self.assertEqual(raised.exception.code, "CONTENT_MISMATCH")
        self.assertEqual(self.receipt_count(), 0)
        (self.producer / "index.html").write_bytes(self.payloads["index.html"])
        first = self.receive()
        (self.producer / "index.html").write_bytes(b"changed again")
        with self.assertRaises(HandoffError) as raised:
            self.receive()
        self.assertEqual(raised.exception.code, "CONTENT_MISMATCH")
        self.assertEqual(self.receipt_count(), 1)
        self.assertEqual(json.loads((self.receiver / "deliveries" / first["delivery_key"] / "receipt.json").read_bytes()), first)

    def test_missing_source_rejects_without_partial_acceptance(self):
        (self.producer / "assets/style.css").unlink()
        with self.assertRaises(HandoffError) as raised:
            self.receive()
        self.assertEqual(raised.exception.code, "MISSING_FILE")
        self.assertEqual(self.receipt_count(), 0)
        self.assertEqual(list((self.receiver / "deliveries").iterdir()), [])

    def test_saved_copy_corruption_preserves_historical_receipt(self):
        first = self.receive()
        (self.receiver / first["storage_subdir"] / "index.html").write_bytes(b"damaged received copy")
        with self.assertRaises(HandoffError) as raised:
            self.receive()
        self.assertEqual(raised.exception.code, "STORE_CORRUPT")
        self.assertEqual(self.receipt_count(), 1)

    def test_source_version_is_preserved_and_part_of_delivery_identity(self):
        first = self.receive()
        newer = copy.deepcopy(self.manifest)
        next(p for p in newer["files"] if p["path"] == "index.html")["source"]["version"] = 1
        second = self.receive(manifest=newer)
        self.assertNotEqual(first["receipt_id"], second["receipt_id"])
        self.assertEqual(self.receipt_count(), 2)

    def test_two_concurrent_receivers_share_one_immutable_receipt(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = list(pool.map(lambda _: self.receive(), range(2)))
        self.assertEqual(first, second)
        self.assertEqual(self.receipt_count(), 1)

    def test_complete_orphan_delivery_recovers_without_new_receipt(self):
        first = self.receive()
        # Simulate the file installation surviving an uncommitted DB record.
        (self.receiver / "handoff.sqlite").unlink()
        recovered = self.receive()
        self.assertEqual(first, recovered)
        self.assertEqual(self.receipt_count(), 1)

    def test_orphan_receipt_cannot_be_promoted_to_stage_completion(self):
        first = self.receive()
        (self.receiver / "handoff.sqlite").unlink()
        first["stage_receipt_issued"] = True
        path = self.receiver / "deliveries" / first["delivery_key"] / "receipt.json"
        path.write_text(json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        with self.assertRaises(HandoffError) as raised:
            self.receive()
        self.assertEqual(raised.exception.code, "STORE_CORRUPT")
        self.assertEqual(self.receipt_count(), 0)

    def test_unsafe_paths_and_symlink_inputs_are_rejected(self):
        for name in ["../outside", "/absolute", "assets/../index.html", "assets\\style.css"]:
            with self.subTest(name=name), self.assertRaises(HandoffError) as raised:
                build_handoff_manifest(self.producer, [name], revision="fixture-r1")
            self.assertEqual(raised.exception.code, "UNSAFE_PATH")
        (self.producer / "alias.html").symlink_to(self.producer / "index.html")
        with self.assertRaises(HandoffError) as raised:
            build_handoff_manifest(self.producer, ["alias.html"], revision="fixture-r1")
        self.assertEqual(raised.exception.code, "UNSAFE_PATH")

    def test_cli_pin_receive_redelivery_and_mismatch(self):
        manifest = self.root / "pinned.json"
        base = [sys.executable, "-m", "lp_engine.artifact_handoff"]
        pinned = subprocess.run(base + ["pin", "--source-root", str(self.producer), "--file", "index.html",
                                        "--revision", "fixture-r1", "--out", str(manifest)], capture_output=True, text=True)
        self.assertEqual(pinned.returncode, 0, pinned.stderr)
        args = ["receive", "--source-root", str(self.producer), "--manifest", str(manifest),
                "--receiver-root", str(self.receiver), "--expected-revision", "fixture-r1"]
        first = subprocess.run(base + args, capture_output=True, text=True)
        second = subprocess.run(base + args, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
        failed = subprocess.run(base + args[:-1] + ["fixture-r2"], capture_output=True, text=True)
        self.assertEqual(failed.returncode, 2)
        self.assertEqual(json.loads(failed.stderr)["error"]["code"], "REVISION_MISMATCH")


if __name__ == "__main__":
    unittest.main()
