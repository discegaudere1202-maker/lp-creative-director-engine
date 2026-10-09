"""Connect a preserved authored P01 brief to an explicit private composition.

This is an internal, static-preview connection. It does not select a theme,
generate public copy from internal hypotheses, run stage Gates, or publish.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from .pilot_authoring import AuthoringError, validate_theme_design_brief
from .pilot_composition import compose_preview


def build_authored_composition_input(
    brief: Mapping[str, Any], composition: Mapping[str, Any]
) -> dict[str, Any]:
    """Retain the whole original brief beside caller-supplied display content.

    The embedded brief is trace context, not renderable company copy. The
    composition renderer still requires an explicit theme, ordered parts,
    text, and image bytes. Transported publication policies remain intact.
    """
    validate_theme_design_brief(brief)
    if not isinstance(composition, Mapping):
        raise AuthoringError("Composition must be an explicit object")
    company = composition.get("company")
    if not isinstance(company, Mapping):
        raise AuthoringError("Composition must provide explicit company data")
    if company.get("industry") != brief["industry"]["key"]:
        raise AuthoringError("Composition industry differs from the source-linked P01 brief")
    context = composition.get("context", {})
    if not isinstance(context, Mapping):
        raise AuthoringError("Composition context must be an object")
    if "p01_design_brief" in context:
        raise AuthoringError("p01_design_brief is reserved for the validated original packet")
    result = deepcopy(dict(composition))
    result["context"] = deepcopy(dict(context))
    result["context"]["p01_design_brief"] = deepcopy(dict(brief))
    return result


def compose_authored_preview(
    brief: Mapping[str, Any],
    composition: Mapping[str, Any],
    *,
    source_root: str | Path,
    output_dir: str | Path,
    image_root: str | Path | None = None,
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate P01 provenance, then run the existing static composition API."""
    payload = build_authored_composition_input(brief, composition)
    return compose_preview(
        payload,
        source_root=source_root,
        output_dir=output_dir,
        image_root=image_root,
        expected_source_sha256=expected_source_sha256,
    )
