"""Verified SQLite snapshots; no GitHub, migration, dispatch or quality approval.

External LP files, media, credentials and source code are NOT included. Restore
by opening a saved standalone database at a new path, never by replacing a live
production database. Existing different targets are preserved.
"""
from __future__ import annotations

from contextlib import closing
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from typing import Any

from .persistence import SCHEMA_VERSION


class BackupError(RuntimeError):
    """A backup failure, not a production Gate result."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code


def checksum(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _plain_path(value: str | Path) -> Path:
    path = Path(os.path.abspath(value))
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise BackupError("UNSAFE_PATH", "Symbolic links are not backup paths")
    return path


def _readonly(path: Path, timeout: float) -> sqlite3.Connection:
    # mode=ro must not silently create or migrate a missing/old source.
    return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True,
                           timeout=timeout, isolation_level=None)


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"),
                      allow_nan=False).encode("ascii")


def _value(value: Any) -> list[Any]:
    # Preserve types, BLOB bytes, Unicode, NULL and non-finite SQLite reals.
    if isinstance(value, bytes):
        return ["blob", value.hex()]
    if isinstance(value, float):
        return ["real", value.hex()]
    return [type(value).__name__, value]


def _snapshot(connection: sqlite3.Connection, deadline: float) -> dict[str, Any]:
    def check_time() -> None:
        if time.monotonic() >= deadline:
            raise BackupError("BACKUP_TIMEOUT", "Snapshot verification exceeded its time budget")

    check_time()
    integrity = [r[0] for r in connection.execute("PRAGMA integrity_check")]
    if integrity != ["ok"]:
        raise BackupError("DATABASE_CORRUPT", "SQLite integrity check did not return ok")
    schema = connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ).fetchall()
    names = [r[1] for r in schema if r[0] == "table"]
    required = {"schema_migrations", "candidates", "projects", "generations", "artifacts"}
    if not required.issubset(names):
        raise BackupError("UNSUPPORTED_SCHEMA", "Expected existing production tables are missing")
    versions = [r[0] for r in connection.execute("SELECT version FROM schema_migrations")]
    if SCHEMA_VERSION not in versions:
        raise BackupError("UNSUPPORTED_SCHEMA", "Expected migration is absent; backup will not migrate")
    tables = {}
    for name in names:
        check_time()
        rows = []
        for row in connection.execute("SELECT * FROM " + _quote(name)):
            rows.append(hashlib.sha256(_json_bytes([_value(v) for v in row])).digest())
            if len(rows) % 1000 == 0:
                check_time()
        # Order independent, but duplicates retain their multiplicity.
        rows.sort()
        h = hashlib.sha256()
        for digest in rows:
            h.update(digest)
        tables[name] = {"rows": len(rows), "sha256": h.hexdigest()}
    health = {"schema_version": SCHEMA_VERSION, "integrity": "ok",
              **{k: tables[k]["rows"] for k in ("candidates", "projects", "generations", "artifacts")}}
    signature = hashlib.sha256(_json_bytes({"schema": schema, "tables": tables,
        "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
        "application_id": connection.execute("PRAGMA application_id").fetchone()[0]})).hexdigest()
    return {"health": health, "tables": tables, "content_sha256": signature}


def _budget(connection: sqlite3.Connection, deadline: float) -> None:
    connection.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)


def backup_restore(source: str | Path, target: str | Path, *,
                   timeout_seconds: float = 30.0) -> dict[str, Any]:
    """Save and read back one consistent SQLite snapshot.

    Open WAL writes are included only when committed before the pinned read
    snapshot. Writes committed after that boundary belong to the next backup.
    Source data and schema are never migrated by this function. A reused equal
    target is accepted; a different target is never overwritten. Raises on any
    failed verification, without returning a misleading data_loss=0 result.
    """
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) \
            or not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be a positive finite number")
    src, dst = _plain_path(source), _plain_path(target)
    if not src.is_file():
        raise BackupError("SOURCE_MISSING", "Source must be an existing regular database")
    if src == dst or (dst.exists() and os.path.samefile(src, dst)):
        raise BackupError("SOURCE_TARGET_ALIAS", "Source and target must be different files")
    if dst.exists() and not dst.is_file():
        raise BackupError("TARGET_CONFLICT", "Target is not a regular file")
    # Existing SQLite sidecars may represent a live target, not a saved snapshot.
    if any(Path(str(dst) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise BackupError("TARGET_IN_USE", "Target has SQLite sidecars; use a new snapshot path")
    dst.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_seconds
    fd, temporary = tempfile.mkstemp(prefix=".lp-snapshot-", suffix=".db", dir=dst.parent)
    os.close(fd)
    staged = Path(temporary)
    reused = False
    try:
        with closing(_readonly(src, min(timeout_seconds, 1.0))) as original:
            _budget(original, deadline)
            original.execute("BEGIN")
            before = _snapshot(original, deadline)
            with closing(sqlite3.connect(staged)) as copied:
                def progress(status: int, remaining: int, total: int) -> None:
                    if time.monotonic() >= deadline:
                        raise BackupError("BACKUP_TIMEOUT", "SQLite backup exceeded its time budget")
                original.backup(copied, pages=128, progress=progress, sleep=0.01)
                # Make the backup self-contained, not dependent on a WAL file.
                copied.execute("PRAGMA journal_mode=DELETE")
            original.execute("ROLLBACK")
        with closing(_readonly(staged, 1.0)) as restored:
            _budget(restored, deadline)
            after = _snapshot(restored, deadline)
        if before != after:
            raise BackupError("SNAPSHOT_MISMATCH", "Restored rows/schema differ from the pinned snapshot")
        with staged.open("rb") as saved:
            os.fsync(saved.fileno())
        try:
            # Atomic, exclusive publication; unlike replace(), never clobbers.
            os.link(staged, dst)
        except FileExistsError:
            _plain_path(dst)
            if any(Path(str(dst) + s).exists() for s in ("-wal", "-shm", "-journal")):
                raise BackupError("TARGET_IN_USE", "An existing target has SQLite sidecars")
            with closing(_readonly(dst, 1.0)) as existing:
                _budget(existing, deadline)
                same = _snapshot(existing, deadline)
            if same != after:
                raise BackupError("TARGET_CONFLICT", "A different snapshot already exists; it was preserved")
            reused = True
        # Reopen the published path as well; do not rely on the staging result.
        with closing(_readonly(dst, 1.0)) as saved:
            _budget(saved, deadline)
            published = _snapshot(saved, deadline)
        if published != after:
            raise BackupError("PUBLISHED_MISMATCH", "Published snapshot did not match readback")
        return {"backup": str(target), "checksum": checksum(dst),
                "before": before["health"], "after": published["health"],
                "integrity": True, "data_loss": 0, "reused": reused,
                "content_sha256": after["content_sha256"], "tables": after["tables"],
                "scope": "DATABASE_SNAPSHOT_ONLY", "external_files_included": False,
                "quality_status": "NOT_RUN", "stage_receipt_issued": False}
    except sqlite3.DatabaseError as exc:
        code = "BACKUP_TIMEOUT" if time.monotonic() >= deadline else "DATABASE_ERROR"
        raise BackupError(code, "SQLite snapshot failed; no success result was issued") from exc
    finally:
        for file in (staged, *(Path(str(staged) + s) for s in ("-wal", "-shm", "-journal"))):
            file.unlink(missing_ok=True)
