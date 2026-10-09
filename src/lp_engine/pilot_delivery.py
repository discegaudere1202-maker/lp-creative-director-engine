"""Deliver a selected, authored preview only after its image uses are checked.

This joins existing internal-preview adapters. It issues only the existing
artifact receipt, never a production Stage Receipt or a design approval.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import tempfile
from typing import Any

from .artifact_handoff import build_handoff_manifest, receive_artifacts
from .pilot_asset_selection import attach_preview_assets, validate_composed_asset_usage
from .pilot_composition import compose_preview
from .pilot_pipeline import build_authored_composition_input


PREVIEW_FILES = (
    "index.html", "composition_input.json", "composition_manifest.json",
    "asset_usage_check.json",
)


class DeliveryError(ValueError):
    """A local connection failure, not a formal production Gate result."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _document_bytes(value: Any) -> bytes:
    # Match the composition adapter's saved JSON representation, so the
    # receiver pins the exact input and trace that were checked in this call.
    try:
        return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise DeliveryError("INVALID_JSON", "Only finite JSON values can be delivered") from exc


def _pin(raw: bytes) -> dict[str, Any]:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def deliver_selected_preview(
    brief: Mapping[str, Any],
    composition: Mapping[str, Any],
    asset_selection: Mapping[str, Any],
    *,
    source_root: str | Path,
    expected_source_sha256: str,
    receiver_dir: str | Path,
    revision: str,
    expected_revision: str,
    handoff_context: Mapping[str, Any],
    expected_context: Mapping[str, Any],
    staging_parent: str | Path | None = None,
) -> dict[str, Any]:
    """Attach, compose, check actual image uses, then receive fixed artifacts.

    The completed output lives in the existing receiver's immutable delivery
    directory. Each call owns one temporary producer directory; no existing
    preview is reused, overwritten, or deleted. Identical inputs and handoff
    metadata use the receiver's existing idempotent redelivery behavior.

    ``asset_selection`` is an already-built explicit selection, not a pool or
    a candidate request. ``composition.images`` must be explicitly empty.
    This API requires the caller's existing source-bundle pin and package
    revision. It does not calculate preferences, choose images, or interpret
    caller handoff metadata as new formal Stage fields.
    """
    if not isinstance(expected_source_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_source_sha256):
        raise DeliveryError("SOURCE_PIN_REQUIRED", "Supply the previously pinned source-bundle SHA-256")
    if not all(isinstance(value, Mapping) for value in (brief, composition, asset_selection, handoff_context, expected_context)):
        raise DeliveryError("INVALID_INPUT", "Brief, composition, selection, and handoff contexts must be objects")

    selected = deepcopy(dict(asset_selection))
    supplied = attach_preview_assets(composition, selected)
    payload = build_authored_composition_input(brief, supplied)
    # Metadata remains exactly caller-authored. The receiver applies its
    # existing revision and expected-context checks, without injected fields.
    handoff_context = deepcopy(dict(handoff_context))
    expected_context = deepcopy(dict(expected_context))
    receiver_root = Path(receiver_dir).resolve()

    with tempfile.TemporaryDirectory(prefix=".lp-selected-delivery-", dir=staging_parent) as temporary:
        temporary_root = Path(temporary).resolve()
        if receiver_root.is_relative_to(temporary_root) or temporary_root.is_relative_to(receiver_root):
            raise DeliveryError("OVERLAPPING_DELIVERY_PATHS", "Temporary producer and receiver directories must be disjoint after resolving aliases")
        staged = temporary_root / "preview"
        trace = compose_preview(
            payload, source_root=source_root, output_dir=staged,
            expected_source_sha256=expected_source_sha256,
        )
        usage = validate_composed_asset_usage(selected, trace)
        usage_bytes = _document_bytes(usage)
        usage_path = staged / "asset_usage_check.json"
        with usage_path.open("xb") as output:
            output.write(usage_bytes)
        usage_path.chmod(0o600)

        manifest = build_handoff_manifest(
            staged, PREVIEW_FILES, revision=revision, context=handoff_context,
        )
        expected = {
            "index.html": {key: trace["html"][key] for key in ("bytes", "sha256")},
            "composition_input.json": _pin(_document_bytes(payload)),
            "composition_manifest.json": _pin(_document_bytes(trace)),
            "asset_usage_check.json": _pin(usage_bytes),
        }
        # A change between composition/validation and producer pinning must
        # not be re-pinned as a newly valid delivery. Later changes are caught
        # while the existing receiver copies and checks the pinned bytes.
        if any({key: pin[key] for key in ("bytes", "sha256")} != expected[pin["path"]]
               for pin in manifest["files"]):
            raise DeliveryError("STAGED_CONTENT_MISMATCH", "Staged artifacts differ from the checked input, trace, or image-usage result")
        receipt = receive_artifacts(
            source_dir=staged, manifest=manifest, receiver_dir=receiver_root,
            expected_revision=expected_revision, expected_context=expected_context,
        )

    return {
        "scope": "INTERNAL_COMPOSITION_PREVIEW", "quality_status": "NOT_RUN",
        "production_ready": False,
        "preview_dir": str(receiver_root / receipt["storage_subdir"]),
        "artifact_receipt": receipt,
    }
