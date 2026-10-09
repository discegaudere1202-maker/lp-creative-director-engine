"""Extract explicitly named pool originals from already received local ZIPs.

This is byte retrieval, not candidate selection, rights review or adoption.
No URL, historical local path or remote storage ID is followed.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from typing import Any
import zipfile

from PIL import Image, UnidentifiedImageError

from .pilot_asset_selection import _index


class AssetExtractionError(ValueError):
    """A local retrieval failure; never a production Stage/Gate result."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise AssetExtractionError(code, message)


def _safe_member(value: Any) -> str:
    _require(isinstance(value, str) and bool(value), "UNSAFE_MEMBER_PATH", "An explicit relative member path is required")
    path = PurePosixPath(value)
    _require(bool(path.parts) and not path.is_absolute() and value == path.as_posix()
             and all(part not in {".", ".."} for part in path.parts)
             and not any(char in value for char in ("\\", ":", "\x00")),
             "UNSAFE_MEMBER_PATH", value)
    return value


def _local_path(value: Any) -> Path:
    _require(isinstance(value, (str, Path)), "INVALID_LOCAL_PATH", "Supply a local filesystem path")
    path = Path(value)
    _require(path.is_absolute() and ".." not in path.parts,
             "INVALID_LOCAL_PATH", "Supply an absolute local path without parent traversal")
    _require(not any(part.is_symlink() for part in (path, *path.parents)),
             "INVALID_LOCAL_PATH", "Local archive and output paths must not follow symlinks")
    return path


def _pin_valid(value: Mapping[str, Any]) -> bool:
    return (type(value.get("bytes")) is int and value["bytes"] > 0
            and isinstance(value.get("sha256"), str)
            and re.fullmatch(r"[a-f0-9]{64}", value["sha256"]) is not None)


def _matches(raw: bytes, expected: Mapping[str, Any]) -> bool:
    return len(raw) == expected["bytes"] and hashlib.sha256(raw).hexdigest() == expected["sha256"]


def _archive_bytes(path: Path, expected: Mapping[str, Any]) -> bytes:
    # Verify the bytes subsequently opened by ZipFile, not a second path read.
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
        try:
            _require(stat.S_ISREG(os.fstat(descriptor).st_mode),
                     "INVALID_LOCAL_ARCHIVE", "The supplied archive must be an ordinary file")
            with os.fdopen(descriptor, "rb", closefd=False) as source:
                raw = source.read(expected["bytes"] + 1)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise AssetExtractionError("LOCAL_ARCHIVE_UNAVAILABLE", str(path)) from exc
    _require(_matches(raw, expected), "ARCHIVE_IDENTITY_MISMATCH", str(path))
    return raw


def _image_check(raw: bytes, record: Mapping[str, Any]) -> dict[str, Any]:
    _require(_matches(raw, record), "MEMBER_IDENTITY_MISMATCH", record["asset_id"])
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image_format = image.format
            image.verify()
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            dimensions = image.size
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise AssetExtractionError("INVALID_IMAGE_BYTES", record["asset_id"]) from exc
    _require(image_format in {"JPEG", "PNG", "WEBP"}
             and dimensions == (record["width"], record["height"]),
             "IMAGE_METADATA_MISMATCH", record["asset_id"])
    return {"bytes": len(raw), "sha256": record["sha256"],
            "width": dimensions[0], "height": dimensions[1], "format": image_format}


def extract_pool_originals(
    pool: Mapping[str, Any], *, asset_ids: Sequence[str],
    archive_files: Mapping[str, str | Path], output_dir: str | Path,
) -> dict[str, Any]:
    """Extract selected IDs without changing any source record or its status.

    ``archive_files`` maps the exact recorded archive names to already
    received local ZIPs. Supply precisely the archives needed by ``asset_ids``.
    ``output_dir`` must be new and its parent must already exist. Only the
    requested image members and an extraction receipt are written there.
    The returned ``local_files`` goes directly to build_preview_asset_selection.
    """
    _require(isinstance(pool, Mapping), "INVALID_POOL", "Supply a loaded pool")
    source_pool = deepcopy(dict(pool))
    index = _index(source_pool)  # Reuse the existing source/snapshot seal checks.
    _require(isinstance(asset_ids, (list, tuple)) and bool(asset_ids)
             and all(isinstance(value, str) and bool(value.strip()) for value in asset_ids),
             "INVALID_ASSET_IDS", "Select at least one source asset ID explicitly")
    ids = list(asset_ids)
    _require(len(ids) == len(set(ids)), "DUPLICATE_ASSET_ID", "Asset IDs must be unique")
    records = {record["asset_id"]: record for record in index["records"]}
    _require(all(asset_id in records for asset_id in ids), "ASSET_NOT_IN_POOL", "An asset ID is absent from the source pool")
    _require(isinstance(archive_files, Mapping), "INVALID_ARCHIVE_FILES", "Supply the selected local archives explicitly")
    supplied_archives = dict(archive_files)
    archive_rows = index.get("archive_parts")
    _require(isinstance(archive_rows, list), "ARCHIVE_METADATA_MISSING", "The source pool has no archive_parts list")
    parts: dict[str, dict] = {}
    for row in archive_rows:
        _require(isinstance(row, dict), "INVALID_ARCHIVE_METADATA", "Archive rows must be objects")
        name = row.get("file") or row.get("name")  # Original catalog's partName rule.
        _require(isinstance(name, str) and bool(name.strip()), "INVALID_ARCHIVE_METADATA", "Archive name is missing")
        _require(not (row.get("file") and row.get("name") and row["file"] != row["name"]),
                 "AMBIGUOUS_ARCHIVE_NAME", name)
        _require(name not in parts, "DUPLICATE_ARCHIVE_NAME", name)
        parts[name] = row

    selected, needed, output_names = [], set(), set()
    for asset_id in ids:
        record = records[asset_id]
        storage = record["storage"]
        name = storage.get("archive_part")
        _require(isinstance(name, str) and name in parts, "ARCHIVE_METADATA_MISSING", asset_id)
        archive = parts[name]
        _require(_pin_valid(archive), "INVALID_ARCHIVE_METADATA", name)
        member = _safe_member(storage.get("member_path"))
        _require(record.get("archive_part") == name and record.get("asset_file") == member
                 and storage.get("archive_sha256") == archive["sha256"]
                 and storage.get("member_sha256") == record["sha256"],
                 "SOURCE_STORAGE_MISMATCH", asset_id)
        relative = "assets/" + PurePosixPath(member).name
        folded = relative.casefold()
        _require(folded not in output_names, "OUTPUT_NAME_CONFLICT", relative)
        output_names.add(folded)
        selected.append((record, archive, member, relative))
        needed.add(name)
    _require(set(supplied_archives) == needed, "ARCHIVE_SET_MISMATCH", "Supply exactly the needed recorded archive names")
    output = _local_path(output_dir)
    _require(not output.exists(), "OUTPUT_EXISTS", "Use a new output directory; prior results are preserved")
    _require(output.parent.is_dir(), "OUTPUT_PARENT_MISSING", "The output parent must already exist")

    binaries, checks = {}, {}
    for name in sorted(needed):
        archive_path = _local_path(supplied_archives[name])
        raw = _archive_bytes(archive_path, parts[name])
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                members = archive.infolist()
                for record, _, member, _ in selected:
                    if record["storage"]["archive_part"] != name:
                        continue
                    matches = [entry for entry in members if entry.filename.casefold() == member.casefold()]
                    _require(len(matches) == 1 and matches[0].filename == member,
                             "MEMBER_NOT_UNIQUE", member)
                    info = matches[0]
                    # ZipInfo.filename can truncate a raw name at NUL; the
                    # original member name must also be safe and exact.
                    _require(_safe_member(info.orig_filename) == member,
                             "MEMBER_NOT_UNIQUE", member)
                    kind = stat.S_IFMT(info.external_attr >> 16)
                    _require(not info.is_dir() and not (info.external_attr & 0x10)
                             and kind in {0, stat.S_IFREG} and not (info.flag_bits & 1),
                             "INVALID_ARCHIVE_MEMBER", member)
                    _require(info.file_size == record["bytes"], "MEMBER_IDENTITY_MISMATCH", record["asset_id"])
                    binary = archive.read(info)
                    checks[record["asset_id"]] = _image_check(binary, record)
                    binaries[record["asset_id"]] = binary
        except (zipfile.BadZipFile, NotImplementedError, RuntimeError, OSError, EOFError) as exc:
            raise AssetExtractionError("INVALID_ARCHIVE_BYTES", name) from exc

    local_files = {record["asset_id"]: str(output / relative) for record, _, _, relative in selected}
    receipt = {
        "scope": "ARTIFACT_ONLY", "status": "LOCAL_BYTES_VERIFIED", "quality_status": "NOT_RUN",
        "stage_receipt_issued": False, "formal_gate_issued": False, "production_ready": False,
        "source": deepcopy(source_pool["source"]),
        "source_index_snapshot_sha256": source_pool["index_snapshot_sha256"],
        "files": [{"asset_id": record["asset_id"], "path": relative,
                   "local_path": local_files[record["asset_id"]], "binary_check": checks[record["asset_id"]],
                   "source_record": deepcopy(record), "source_archive": deepcopy(part)}
                  for record, part, _, relative in selected],
        "source_conditions_changed": False, "rights_reassessment": "NOT_RUN",
        "visual_approval": "NOT_ASSERTED", "crop_validation": "NOT_RUN",
        "transformation": "NONE", "network_requests": 0,
    }
    receipt_bytes = (json.dumps(receipt, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    owned = False
    try:
        output.mkdir(mode=0o700)  # Exclusive creation also protects an output created during validation.
        owned = True
        (output / "assets").mkdir(mode=0o700)
        writes = [(output / relative, binaries[record["asset_id"]]) for record, _, _, relative in selected]
        writes.append((output / "extraction_receipt.json", receipt_bytes))
        for destination, binary in writes:
            with destination.open("xb") as target:
                target.write(binary)
            destination.chmod(0o600)
            _require(destination.read_bytes() == binary, "OUTPUT_IDENTITY_MISMATCH", destination.name)
    except Exception:
        if owned:
            shutil.rmtree(output)
        raise
    return {"local_files": local_files, "extraction_receipt": receipt}
