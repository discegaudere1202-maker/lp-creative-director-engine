"""Local file-integrity handoff, independent of production and quality states.

The producer pins selected files.  The receiver checks those fixed pins and
its expected revision/context, keeps a byte-identical copy, and records one
immutable receipt per delivery.  No provider, Chat, Gate or batch is invoked.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import sys
import tempfile
from typing import Any
from uuid import uuid4


MANIFEST_SCHEMA = "local-artifact-handoff-v1"
RECEIPT_SCHEMA = "local-artifact-receipt-v1"


class HandoffError(RuntimeError):
    """A transport failure; its code is not a production Stage/Gate state."""

    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code


def _require(condition: bool, code: str, detail: str) -> None:
    if not condition:
        raise HandoffError(code, detail)


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise HandoffError("INVALID_METADATA", "Metadata must be finite JSON values") from exc


def _metadata(value: Mapping[str, Any] | None) -> dict[str, Any]:
    _require(value is None or isinstance(value, Mapping), "INVALID_METADATA", "Expected an object")
    value = dict(value or {})

    def check_keys(item: Any) -> None:
        if isinstance(item, Mapping):
            _require(all(isinstance(key, str) for key in item), "INVALID_METADATA", "JSON keys must be strings")
            for child in item.values():
                check_keys(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                check_keys(child)

    check_keys(value)
    return json.loads(_canonical(value))


def _revision(value: Any) -> str:
    _require(isinstance(value, str) and bool(value.strip()), "INVALID_REVISION", "An explicit revision is required")
    return value


def _relative_path(value: Any) -> str:
    _require(isinstance(value, str) and bool(value), "UNSAFE_PATH", "Expected a relative file path")
    path = PurePosixPath(value)
    _require(bool(path.parts) and not path.is_absolute() and value == path.as_posix()
             and all(part not in {".", ".."} for part in path.parts)
             and not any(char in value for char in ("\\", ":", "\x00")),
             "UNSAFE_PATH", value)
    return value


def _paths(paths: Sequence[str]) -> list[str]:
    _require(isinstance(paths, Sequence) and not isinstance(paths, (str, bytes)) and bool(paths),
             "INVALID_FILES", "Select at least one file explicitly")
    result = sorted(_relative_path(path) for path in paths)
    folded = [path.casefold() for path in result]
    _require(len(set(folded)) == len(folded), "PATH_CONFLICT", "Duplicate or case-alias paths")
    for name in folded:
        _require(not any(other.startswith(name + "/") for other in folded),
                 "PATH_CONFLICT", "A file path cannot also be a parent directory")
    return result


def _regular_file(root: Path, relative: str) -> Path:
    path = root
    try:
        for part in PurePosixPath(relative).parts:
            path = path / part
            _require(not path.is_symlink(), "UNSAFE_PATH", relative)
        _require(path.is_file(), "MISSING_FILE", relative)
    except OSError as exc:
        raise HandoffError("FILE_ACCESS_ERROR", relative) from exc
    return path


def _measure(path: Path, destination: Path | None = None) -> dict[str, Any]:
    """Hash bytes actually read; optional receiver copy contains those bytes."""
    digest = hashlib.sha256()
    size = 0
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        with os.fdopen(os.open(path, flags), "rb") as source:
            _require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), "INVALID_FILE", str(path))
            if destination is not None:
                destination.parent.mkdir(parents=True, exist_ok=True)
            target = destination.open("xb") if destination is not None else None
            try:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
                    size += len(block)
                    if target is not None:
                        target.write(block)
                if target is not None:
                    target.flush()
                    os.fsync(target.fileno())
            finally:
                if target is not None:
                    target.close()
    except OSError as exc:
        raise HandoffError("FILE_ACCESS_ERROR", str(path)) from exc
    return {"bytes": size, "sha256": digest.hexdigest()}


def _matches(observed: Mapping[str, Any], pin: Mapping[str, Any], code: str) -> None:
    _require(observed["bytes"] == pin["bytes"] and observed["sha256"] == pin["sha256"], code, pin["path"])


def build_handoff_manifest(source_dir: str | Path, files: Sequence[str], *, revision: str,
                           context: Mapping[str, Any] | None = None,
                           sources: Mapping[str, Mapping[str, Any] | None] | None = None) -> dict[str, Any]:
    """Pin producer files; pass this saved result unchanged to the receiver.

    ``revision`` is the caller's existing input/package revision, not an
    invented production revision.  Optional source metadata preserves known
    IDs/versions; an unprovided source remains null.
    """
    paths = _paths(files)
    root = Path(source_dir).resolve()
    metadata = _metadata(sources)
    _require(set(metadata).issubset(paths), "INVALID_METADATA", "Source metadata names an unselected file")
    pins = []
    for name in paths:
        origin = metadata.get(name)
        _require(origin is None or isinstance(origin, dict), "INVALID_METADATA", "File source must be an object or null")
        pins.append({"path": name, **_measure(_regular_file(root, name)), "source": origin})
    return {"schema_version": MANIFEST_SCHEMA, "revision": _revision(revision),
            "context": _metadata(context), "files": pins}


def _manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    value = _metadata(value)
    _require(set(value) == {"schema_version", "revision", "context", "files"}
             and value.get("schema_version") == MANIFEST_SCHEMA,
             "INVALID_MANIFEST", "Unsupported local handoff manifest")
    _revision(value["revision"])
    value["context"] = _metadata(value["context"])
    files = value["files"]
    _require(isinstance(files, list) and bool(files) and all(isinstance(pin, dict) for pin in files),
             "INVALID_FILES", "Expected file pins")
    names = _paths([pin.get("path") for pin in files])
    for pin in files:
        _require(set(pin) == {"path", "bytes", "sha256", "source"}, "INVALID_PIN", "Unexpected file-pin fields")
        _require(type(pin["bytes"]) is int and pin["bytes"] >= 0
                 and isinstance(pin["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None,
                 "INVALID_PIN", pin["path"])
        _require(pin["source"] is None or isinstance(pin["source"], dict), "INVALID_PIN", "Source must be an object or null")
    value["files"] = sorted(files, key=lambda pin: pin["path"])
    _require([pin["path"] for pin in value["files"]] == names, "INVALID_FILES", "Invalid file ordering")
    return value


def _encoded(value: Any) -> bytes:
    return (_canonical(value) + "\n").encode("utf-8")


def _write_new_json(path: Path, value: Any) -> None:
    with path.open("xb") as output:
        output.write(_encoded(value))
        output.flush()
        os.fsync(output.fileno())


def _store(root: Path) -> sqlite3.Connection:
    _require(not (root / "handoff.sqlite").is_symlink(), "UNSAFE_PATH", "Receipt database is a link")
    connection = sqlite3.connect(root / "handoff.sqlite", timeout=15, isolation_level=None)
    connection.execute("PRAGMA synchronous=FULL")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS receipts (
            delivery_key TEXT PRIMARY KEY,
            receipt_id TEXT UNIQUE NOT NULL,
            body TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS handoff_receipt_no_update
        BEFORE UPDATE ON receipts BEGIN SELECT RAISE(ABORT, 'immutable handoff receipt'); END;
        CREATE TRIGGER IF NOT EXISTS handoff_receipt_no_delete
        BEFORE DELETE ON receipts BEGIN SELECT RAISE(ABORT, 'immutable handoff receipt'); END;
    """)
    return connection


def _verify_delivery(directory: Path, manifest: dict[str, Any], key: str,
                     expected_receipt: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        _require(not directory.is_symlink(), "STORE_CORRUPT", "Delivery directory is a link")
        receipt_path = _regular_file(directory, "receipt.json")
        receipt_bytes = receipt_path.read_bytes()
        receipt = json.loads(receipt_bytes)
        _require(set(receipt) == {"schema_version", "receipt_id", "delivery_key", "received_at", "status",
                                 "scope", "quality_status", "automatic_downstream_execution",
                                 "stage_receipt_issued", "manifest", "storage_subdir"}
                 and receipt.get("schema_version") == RECEIPT_SCHEMA and receipt.get("delivery_key") == key
                 and _canonical(receipt.get("manifest")) == _canonical(manifest)
                 and receipt.get("status") == "ARTIFACT_RECEIVED"
                 and receipt.get("scope") == "ARTIFACT_ONLY" and receipt.get("quality_status") == "NOT_RUN"
                 and receipt.get("automatic_downstream_execution") is False
                 and receipt.get("stage_receipt_issued") is False
                 and receipt.get("storage_subdir") == f"deliveries/{key}/files"
                 and isinstance(receipt.get("receipt_id"), str) and bool(receipt["receipt_id"])
                 and receipt_bytes == _encoded(receipt), "STORE_CORRUPT", "Receipt does not match the pinned delivery")
        if expected_receipt is not None:
            _require(receipt_bytes == _encoded(expected_receipt), "STORE_CORRUPT", "Receipt differs from the immutable ledger")
        for pin in manifest["files"]:
            received = _regular_file(directory, "files/" + pin["path"])
            _matches(_measure(received), pin, "STORE_CORRUPT")
        return receipt
    except (OSError, ValueError, TypeError, AttributeError, HandoffError) as exc:
        if isinstance(exc, HandoffError) and exc.code == "STORE_CORRUPT":
            raise
        raise HandoffError("STORE_CORRUPT", "Saved receipt or file is missing/corrupt") from exc


def receive_artifacts(*, source_dir: str | Path, manifest: Mapping[str, Any],
                      receiver_dir: str | Path, expected_revision: str,
                      expected_context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Receive fixed files, returning the exact first receipt on redelivery.

    Every receive checks the supplied source bytes again.  Redelivery also
    verifies the saved copy.  Missing/corrupt copies never erase historical
    receipts.  This function does not issue a Stage Receipt or call a Gate.
    """
    pinned = _manifest(manifest)
    _require(pinned["revision"] == _revision(expected_revision), "REVISION_MISMATCH", "Unexpected input/package revision")
    for name, value in _metadata(expected_context).items():
        _require(name in pinned["context"] and _canonical(pinned["context"][name]) == _canonical(value),
                 "CONTEXT_MISMATCH", name)
    key = hashlib.sha256(_canonical(pinned).encode("utf-8")).hexdigest()
    source_root = Path(source_dir).resolve()
    root = Path(receiver_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    deliveries = root / "deliveries"
    _require(not deliveries.is_symlink(), "UNSAFE_PATH", "Deliveries directory is a link")
    deliveries.mkdir(exist_ok=True)
    directory = deliveries / key
    connection = None
    with tempfile.TemporaryDirectory(prefix=".incoming-", dir=root) as temporary:
        staged = Path(temporary)
        for pin in pinned["files"]:
            source = _regular_file(source_root, pin["path"])
            observed = _measure(source, staged / "files" / pin["path"])
            _matches(observed, pin, "CONTENT_MISMATCH")
        try:
            connection = _store(root)
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute("SELECT body FROM receipts WHERE delivery_key=?", (key,)).fetchone()
            if existing:
                receipt = _verify_delivery(directory, pinned, key, json.loads(existing[0]))
            elif directory.exists() or directory.is_symlink():
                # A previous process may have installed the complete files
                # immediately before its DB transaction was interrupted.
                receipt = _verify_delivery(directory, pinned, key)
                connection.execute("INSERT INTO receipts VALUES (?, ?, ?)",
                                   (key, receipt["receipt_id"], _canonical(receipt)))
            else:
                receipt = {"schema_version": RECEIPT_SCHEMA, "receipt_id": "handoff_" + uuid4().hex,
                           "delivery_key": key, "received_at": datetime.now(UTC).isoformat(),
                           "status": "ARTIFACT_RECEIVED", "scope": "ARTIFACT_ONLY",
                           "quality_status": "NOT_RUN", "automatic_downstream_execution": False,
                           "stage_receipt_issued": False, "manifest": pinned,
                           "storage_subdir": f"deliveries/{key}/files"}
                _write_new_json(staged / "receipt.json", receipt)
                staged.rename(directory)
                connection.execute("INSERT INTO receipts VALUES (?, ?, ?)",
                                   (key, receipt["receipt_id"], _canonical(receipt)))
            connection.execute("COMMIT")
            return receipt
        except BaseException:
            if connection is not None and connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            if connection is not None:
                connection.close()


def _read_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HandoffError("JSON_INPUT_ERROR", path) from exc


def _save_cli_json(path: str, payload: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # An explicit output is immutable too: reuse equal bytes, reject conflict.
    try:
        _write_new_json(destination, payload)
    except FileExistsError:
        _require(not destination.is_symlink() and destination.read_bytes() == _encoded(payload),
                 "OUTPUT_CONFLICT", path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pin/receive local artifacts; no quality approval or automatic dispatch")
    commands = parser.add_subparsers(dest="command", required=True)
    pin = commands.add_parser("pin", help="Measure selected producer files")
    pin.add_argument("--source-root", required=True)
    pin.add_argument("--file", action="append", required=True, dest="files")
    pin.add_argument("--revision", required=True)
    pin.add_argument("--context", help="JSON object of existing IDs/context")
    pin.add_argument("--sources", help="JSON object mapping file paths to known source metadata")
    pin.add_argument("--out")
    receive = commands.add_parser("receive", help="Receive against a saved manifest")
    receive.add_argument("--source-root", required=True)
    receive.add_argument("--manifest", required=True)
    receive.add_argument("--receiver-root", required=True)
    receive.add_argument("--expected-revision", required=True)
    receive.add_argument("--expected-context", help="JSON object of required existing context values")
    receive.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.command == "pin":
            result = build_handoff_manifest(args.source_root, args.files, revision=args.revision,
                                            context=_read_json(args.context) if args.context else None,
                                            sources=_read_json(args.sources) if args.sources else None)
        else:
            result = receive_artifacts(source_dir=args.source_root, manifest=_read_json(args.manifest),
                                       receiver_dir=args.receiver_root, expected_revision=args.expected_revision,
                                       expected_context=_read_json(args.expected_context) if args.expected_context else None)
        if args.out:
            _save_cli_json(args.out, result)
        print(_canonical(result))
        return 0
    except (HandoffError, OSError, sqlite3.Error) as exc:
        print(_canonical({"error": {"code": getattr(exc, "code", "LOCAL_IO_ERROR"), "detail": str(exc)}}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
