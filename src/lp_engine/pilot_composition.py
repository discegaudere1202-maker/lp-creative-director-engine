"""Bind explicit LP54 candidate selections to private, caller-supplied content.

This is a local composition adapter, not a production approval or a P01 author.
The trusted LP54 source bundle remains outside this public repository.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

from PIL import Image, UnidentifiedImageError


INPUT_SCHEMA = "lp54-composition-input/v1"
OUTPUT_SCHEMA = "lp54-composition-trace/v1"
SOURCE_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "render_lp54_composition.cjs"


class CompositionError(ValueError):
    """A rejected technical composition input or source, before output is saved."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class _StaticMarkup(HTMLParser):
    """Check the output surface without opening it or running any browser."""

    def __init__(self, image_urls: set[str]):
        super().__init__(convert_charrefs=True)
        self.image_urls = image_urls
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "iframe", "frame", "frameset", "object", "embed", "form", "input", "textarea", "select", "base", "link", "video", "audio", "source"}:
            raise CompositionError("NON_STATIC_MARKUP", f"Unexpected executable, external, or submission element: {tag}")
        attrs = dict(attributes)
        if len(attrs) != len(attributes):
            raise CompositionError("INVALID_MARKUP", "Duplicate HTML attributes are not supported")
        for name, value in attributes:
            if name.startswith("on") or name in {"srcset", "action", "formaction", "poster", "background"}:
                raise CompositionError("NON_STATIC_MARKUP", f"Unexpected active or resource attribute: {name}")
            if name in {"href", "xlink:href"} and (not isinstance(value, str) or not value.startswith("#")):
                raise CompositionError("EXTERNAL_MARKUP_RESOURCE", "Only internal fragment links are supported")
            if name == "src" and (tag != "img" or value not in self.image_urls):
                raise CompositionError("UNPINNED_MARKUP_IMAGE", "Rendered images must use exactly the caller-pinned bytes")
            if name == "style" and value and re.search(r"url\s*\(|@import|expression\s*\(", value, re.I):
                raise CompositionError("NON_STATIC_MARKUP", "Inline styles cannot load resources or execute code")
        if tag == "img" and "src" not in attrs:
            raise CompositionError("INVALID_MARKUP", "Image source is missing")
        if attrs.get("id"):
            if attrs["id"] in self.ids:
                raise CompositionError("INVALID_MARKUP", "Duplicate HTML IDs are not supported")
            self.ids.add(attrs["id"])

    handle_startendtag = handle_starttag


def _json_bytes(value: Any) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CompositionError("INVALID_JSON", "Input must contain ordinary JSON values") from exc


def _image_inputs(images: Any, image_root: Path | None) -> tuple[dict, list]:
    if not isinstance(images, dict):
        raise CompositionError("INVALID_IMAGES", "images must be an explicit slot-to-local-file mapping")
    assets: dict[str, dict] = {}
    receipts: list[dict] = []
    formats = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}
    for slot, supplied in images.items():
        if not isinstance(slot, str) or not re.fullmatch(r"[a-z][a-zA-Z0-9]*", slot):
            raise CompositionError("INVALID_IMAGE_SLOT", "Image slots must be safe identifiers")
        if not isinstance(supplied, dict) or set(supplied) != {"path", "sha256"}:
            raise CompositionError("INVALID_IMAGE", f"images.{slot} requires exactly path and sha256")
        raw_path, expected = supplied["path"], supplied["sha256"]
        if not isinstance(raw_path, str) or not raw_path or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw_path):
            raise CompositionError("INVALID_IMAGE_PATH", f"images.{slot}.path must identify a local file")
        if not isinstance(expected, str) or not re.fullmatch(r"[a-f0-9]{64}", expected):
            raise CompositionError("INVALID_IMAGE_HASH", f"images.{slot}.sha256 must pin the supplied bytes")
        path = Path(raw_path)
        if not path.is_absolute():
            if image_root is None:
                raise CompositionError("IMAGE_ROOT_REQUIRED", "Relative image paths require an explicit image_root")
            path = image_root / path
        try:
            if not path.is_file() or path.is_symlink():
                raise OSError("Not an ordinary local file")
            raw = path.read_bytes()
        except OSError as exc:
            raise CompositionError("IMAGE_READ_ERROR", f"Unable to read images.{slot}") from exc
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise CompositionError("IMAGE_HASH_MISMATCH", f"Image bytes differ from images.{slot}.sha256")
        try:
            with Image.open(io.BytesIO(raw)) as im:
                image_format = im.format
                im.verify()
            with Image.open(io.BytesIO(raw)) as im:
                im.load()
                width, height = im.size
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise CompositionError("INVALID_IMAGE_BYTES", f"Unable to decode images.{slot}") from exc
        if image_format not in formats or width <= 0 or height <= 0:
            raise CompositionError("UNSUPPORTED_IMAGE", f"images.{slot} must be PNG, JPEG, or WebP")
        assets[slot] = {
            "data_url": "data:" + formats[image_format] + ";base64," + base64.b64encode(raw).decode("ascii"),
            "width": width,
            "height": height,
        }
        receipts.append({
            "slot": slot, "source_path": raw_path, "bytes": len(raw),
            "sha256": actual, "mime_type": formats[image_format],
            "width": width, "height": height, "transformation": "NONE",
        })
    return assets, receipts


def compose_preview(
    payload: dict,
    *,
    source_root: str | Path,
    output_dir: str | Path,
    image_root: str | Path | None = None,
    expected_source_sha256: str | None = None,
    node_executable: str = "node",
) -> dict:
    """Write a new private HTML/input/trace directory, using no browser or network.

    ``source_root`` is an explicitly trusted, already materialized LP54 bundle.
    Its code is evaluated as local code; the VM is not a security sandbox for
    arbitrary third-party code. No source bundle is copied into the repository.
    ``expected_source_sha256`` can pin a previously recorded source-bundle hash.
    """
    if not isinstance(payload, dict) or payload.get("schema_version") != INPUT_SCHEMA:
        raise CompositionError("INVALID_SCHEMA", f"Expected {INPUT_SCHEMA}")
    allowed = {"schema_version", "company", "selection", "images", "context"}
    if set(payload) - allowed or not {"company", "selection", "images"} <= set(payload):
        raise CompositionError("INVALID_INPUT_FIELDS", "Input requires company, selection and images; extra fields are not dropped")
    if "context" in payload and not isinstance(payload["context"], dict):
        raise CompositionError("INVALID_CONTEXT", "context must be an object; it is preserved and not interpreted")
    input_bytes = _json_bytes(payload)
    if expected_source_sha256 is not None and not re.fullmatch(r"[a-f0-9]{64}", expected_source_sha256):
        raise CompositionError("INVALID_SOURCE_HASH", "Expected source hash must be lowercase SHA-256")
    target = Path(output_dir).absolute()
    if target.exists() or target.is_symlink():
        raise CompositionError("OUTPUT_EXISTS", "Use a new output directory; previous previews are not overwritten")
    assets, image_receipts = _image_inputs(payload["images"], Path(image_root) if image_root is not None else None)
    command_input = {
        "source_root": str(Path(source_root).absolute()),
        "expected_source_sha256": expected_source_sha256,
        "company": payload["company"], "selection": payload["selection"], "assets": assets,
    }
    try:
        run = subprocess.run(
            [node_executable, str(SOURCE_SCRIPT)], input=_json_bytes(command_input),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=45,
        )
    except FileNotFoundError as exc:
        raise CompositionError("NODE_UNAVAILABLE", "Node.js and the repository's composition script are required") from exc
    except subprocess.TimeoutExpired as exc:
        raise CompositionError("RENDER_TIMEOUT", "Static composition did not finish within the local execution limit") from exc
    try:
        result = json.loads(run.stdout)
    except (ValueError, UnicodeDecodeError) as exc:
        raise CompositionError("RENDER_PROTOCOL_ERROR", "The source renderer did not return a valid composition result") from exc
    if run.returncode or "error" in result:
        error = result.get("error", {})
        raise CompositionError(error.get("code", "RENDER_ERROR"), error.get("message", "Static composition failed"))
    parser = _StaticMarkup({asset["data_url"] for asset in assets.values()})
    parser.feed(result["html"])
    parser.close()
    html_bytes = result["html"].encode("utf-8")
    manifest = {
        "schema_version": OUTPUT_SCHEMA,
        "scope": "INTERNAL_COMPOSITION_PREVIEW",
        "quality_status": "NOT_RUN", "production_ready": False,
        "browser_qa": "NOT_RUN", "visual_approval": "NOT_ASSERTED",
        "formal_contract_binding": "NOT_ASSERTED",
        "automatic_downstream_execution": False,
        "published": False, "external_actions": 0,
        "input": {"path": "composition_input.json", "bytes": len(input_bytes), "sha256": hashlib.sha256(input_bytes).hexdigest()},
        "html": {"path": "index.html", "bytes": len(html_bytes), "sha256": hashlib.sha256(html_bytes).hexdigest()},
        "context": payload.get("context", {}),
        "images": image_receipts,
        **result["trace"],
    }
    # Produce all three files only after every source/input/image validation passes.
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".lp54-composition-", dir=target.parent) as temp:
        staging = Path(temp) / "ready"
        staging.mkdir(mode=0o700)
        for name, raw in [("index.html", html_bytes), ("composition_input.json", input_bytes), ("composition_manifest.json", _json_bytes(manifest))]:
            path = staging / name
            path.write_bytes(raw)
            path.chmod(0o600)
        if target.exists() or target.is_symlink():
            raise CompositionError("OUTPUT_EXISTS", "Output was created concurrently; previous work was retained")
        os.rename(staging, target)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compose an internal LP54 preview from explicit private inputs")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-source-sha256")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        manifest = compose_preview(
            payload, source_root=args.source_root, output_dir=args.out,
            image_root=args.input.parent, expected_source_sha256=args.expected_source_sha256,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": {"code": getattr(exc, "code", "INPUT_READ_ERROR"), "message": str(exc)}}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"scope": manifest["scope"], "quality_status": manifest["quality_status"], "section_count": len(manifest["sections"]), "output_dir": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
