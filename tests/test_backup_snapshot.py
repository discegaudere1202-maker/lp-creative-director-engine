"""Regression tests with synthetic local data; no production or visual claims."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from lp_engine.backup import BackupError, backup_restore, checksum
import lp_engine.backup as backup
from lp_engine.persistence import ProductionRepository


class BackupSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source, self.target = self.root / "source.db", self.root / "saved.db"
        self.repo = ProductionRepository(self.source)
        self.repo.upsert_candidate("c1", "company1", {"company_name": "Synthetic garden"})
        self.repo.create_project("p1", "c1", "company1")
        self.repo.record_generation("g1", "p1", "company1")
        self.repo.audit("run1", "CHECKPOINT", {"next_stage": "COPY"}, project_id="p1")

    def tearDown(self):
        self.repo.close()
        self.temp.cleanup()

    def wal(self):
        self.repo.db.execute("PRAGMA journal_mode=WAL")
        self.repo.db.execute("PRAGMA wal_autocheckpoint=0")
        self.repo.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def read(self, path, sql):
        with closing(sqlite3.connect(path)) as db:
            return db.execute(sql).fetchall()

    def test_legacy_closed_database_and_resume(self):
        result = backup_restore(self.source, self.target)
        self.assertEqual(result["before"], result["after"])
        self.assertTrue(result["integrity"])
        self.assertEqual(result["data_loss"], 0)
        with closing(ProductionRepository(self.target)) as r:
            self.assertEqual(r.get_project("p1")["company_id"], "company1")
            r.record_generation("g2", "p1", "company1", {"resumed": True})
            self.assertEqual(r.health()["generations"], 2)
        self.assertEqual(self.repo.health()["generations"], 1)

    def test_committed_wal_insert_included(self):
        self.wal()
        self.repo.upsert_candidate("c2", "company2", {"company_name": "Second"})
        self.assertGreater(Path(str(self.source) + "-wal").stat().st_size, 0)
        result = backup_restore(self.source, self.target)
        self.assertEqual(result["after"]["candidates"], 2)
        self.assertEqual(self.read(self.target, "SELECT company_name FROM candidates ORDER BY candidate_id")[-1][0], "Second")

    def test_committed_wal_update_same_row_count(self):
        self.wal()
        self.repo.upsert_candidate("c1", "company1", {"company_name": "Updated garden"})
        result = backup_restore(self.source, self.target)
        self.assertEqual(result["after"]["candidates"], 1)
        self.assertEqual(json.loads(self.read(self.target, "SELECT payload FROM candidates")[0][0])["company_name"], "Updated garden")

    def test_uncommitted_wal_change_excluded(self):
        self.wal()
        self.repo.db.execute("BEGIN")
        self.repo.db.execute("UPDATE candidates SET company_name='uncommitted'")
        try:
            backup_restore(self.source, self.target)
            self.assertEqual(self.read(self.target, "SELECT company_name FROM candidates")[0][0], "Synthetic garden")
        finally:
            self.repo.db.rollback()

    def test_audit_log_is_verified_and_retained(self):
        result = backup_restore(self.source, self.target)
        self.assertEqual(result["tables"]["audit_events"]["rows"], 1)
        self.assertEqual(self.read(self.source, "SELECT * FROM audit_events"), self.read(self.target, "SELECT * FROM audit_events"))

    def test_blob_null_unicode_and_quoted_table(self):
        self.repo.db.execute('CREATE TABLE "odd""table"(a BLOB,b TEXT,c REAL,d INTEGER)')
        self.repo.db.execute('INSERT INTO "odd""table" VALUES(?,?,?,?)', (b"\x00\xff", "庭🌿", float("inf"), None))
        self.repo.db.commit()
        result = backup_restore(self.source, self.target)
        self.assertEqual(result["tables"]['odd"table']["rows"], 1)
        self.assertEqual(self.read(self.source, 'SELECT * FROM "odd""table"'), self.read(self.target, 'SELECT * FROM "odd""table"'))

    def test_missing_source_is_not_created(self):
        missing = self.root / "missing.db"
        with self.assertRaises(BackupError) as error:
            backup_restore(missing, self.target)
        self.assertEqual(error.exception.code, "SOURCE_MISSING")
        self.assertFalse(missing.exists())
        self.assertFalse(self.target.exists())

    def test_empty_database_not_migrated(self):
        empty = self.root / "empty.db"
        sqlite3.connect(empty).close()
        original = empty.read_bytes()
        with self.assertRaises(BackupError) as error:
            backup_restore(empty, self.target)
        self.assertEqual(error.exception.code, "UNSUPPORTED_SCHEMA")
        self.assertEqual(empty.read_bytes(), original)
        self.assertFalse(self.target.exists())

    def test_bad_bytes_rejected(self):
        bad = self.root / "broken.db"
        bad.write_bytes(b"not a sqlite database" * 30)
        with self.assertRaises(BackupError):
            backup_restore(bad, self.target)
        self.assertFalse(self.target.exists())
        self.assertFalse(list(self.root.glob(".lp-snapshot-*")))

    def test_different_existing_target_preserved(self):
        backup_restore(self.source, self.target)
        original = checksum(self.target)
        self.repo.upsert_candidate("c2", "company2", {})
        with self.assertRaises(BackupError) as error:
            backup_restore(self.source, self.target)
        self.assertEqual(error.exception.code, "TARGET_CONFLICT")
        self.assertEqual(checksum(self.target), original)

    def test_equal_target_reused(self):
        one = backup_restore(self.source, self.target)
        two = backup_restore(self.source, self.target)
        self.assertFalse(one["reused"])
        self.assertTrue(two["reused"])
        self.assertEqual(one["checksum"], two["checksum"])

    def test_source_alias_rejected(self):
        for target in [self.source, self.root / "hardlink.db"]:
            if target != self.source:
                os.link(self.source, target)
            with self.assertRaises(BackupError) as error:
                backup_restore(self.source, target)
            self.assertEqual(error.exception.code, "SOURCE_TARGET_ALIAS")

    def test_symlink_source_and_target_rejected(self):
        link = self.root / "link.db"
        link.symlink_to(self.source)
        for source, target in [(link, self.target), (self.source, link)]:
            with self.assertRaises(BackupError) as error:
                backup_restore(source, target)
            self.assertEqual(error.exception.code, "UNSAFE_PATH")

    def test_symlink_parent_rejected(self):
        folder = self.root / "real"
        folder.mkdir()
        alias = self.root / "alias"
        alias.symlink_to(folder, target_is_directory=True)
        with self.assertRaises(BackupError):
            backup_restore(self.source, alias / "target.db")

    def test_live_target_sidecar_rejected(self):
        Path(str(self.target) + "-wal").write_bytes(b"reserved")
        with self.assertRaises(BackupError) as error:
            backup_restore(self.source, self.target)
        self.assertEqual(error.exception.code, "TARGET_IN_USE")

    def test_timeout_argument(self):
        for value in [0, -1, True, None, "1", float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                backup_restore(self.source, self.target, timeout_seconds=value)

    def test_tiny_deadline_does_not_publish(self):
        with self.assertRaises(BackupError) as error:
            backup_restore(self.source, self.target, timeout_seconds=1e-10)
        self.assertEqual(error.exception.code, "BACKUP_TIMEOUT")
        self.assertFalse(self.target.exists())

    def test_copy_mismatch_has_no_success_result(self):
        actual = backup._snapshot
        counter = 0
        def altered(connection, deadline):
            nonlocal counter
            result = actual(connection, deadline)
            counter += 1
            if counter == 2:
                result["content_sha256"] = "wrong"
            return result
        with patch.object(backup, "_snapshot", altered), self.assertRaises(BackupError) as error:
            backup_restore(self.source, self.target)
        self.assertEqual(error.exception.code, "SNAPSHOT_MISMATCH")
        self.assertFalse(self.target.exists())

    def test_writer_after_snapshot_boundary(self):
        self.wal()
        actual = backup._snapshot
        first = True
        def write_after_read(connection, deadline):
            nonlocal first
            result = actual(connection, deadline)
            if first:
                first = False
                self.repo.upsert_candidate("c2", "company2", {"company_name": "After boundary"})
            return result
        with patch.object(backup, "_snapshot", write_after_read):
            result = backup_restore(self.source, self.target)
        self.assertEqual(result["after"]["candidates"], 1)
        self.assertEqual(self.repo.health()["candidates"], 2)
        later = backup_restore(self.source, self.root / "later.db")
        self.assertEqual(later["after"]["candidates"], 2)

    def test_two_backup_callers_do_not_clobber(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: backup_restore(self.source, self.target), range(2)))
        self.assertEqual(sum(r["reused"] for r in results), 1)
        self.assertEqual(results[0]["content_sha256"], results[1]["content_sha256"])

    def test_original_schema_and_bytes_unchanged(self):
        before = self.source.read_bytes()
        before_schema = self.read(self.source, "SELECT sql FROM sqlite_master ORDER BY name")
        backup_restore(self.source, self.target)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(self.read(self.source, "SELECT sql FROM sqlite_master ORDER BY name"), before_schema)

    def test_standalone_snapshot_without_sidecars(self):
        self.wal()
        self.repo.upsert_candidate("c2", "company2", {})
        result = backup_restore(self.source, self.target)
        self.assertFalse(any(Path(str(self.target) + s).exists() for s in ["-wal", "-shm", "-journal"]))
        self.assertEqual(result["scope"], "DATABASE_SNAPSHOT_ONLY")
        self.assertFalse(result["external_files_included"])
        self.assertEqual(result["quality_status"], "NOT_RUN")
        self.assertFalse(result["stage_receipt_issued"])


if __name__ == "__main__":
    unittest.main()
