"""Issue #132 runtime adapter over the accepted Issue #129 pixel layer.

The package installs the Issue #129 namespace adapter first. This adapter then
wraps the Issue #129 application function so only Aoi-returned continuation
variants receive structural re-authorship. PASS continuation variants return the
Issue #129 HTML byte-for-byte unchanged.
"""
from __future__ import annotations

from typing import Any, Mapping

from . import premium_perception_recovery as _base
from .premium_perception_reauthorship import apply_premium_perception_reauthorship


_BASE_APPLY = _base.apply_premium_perception_recovery


def _apply_issue132_wrapper(
    rendered: str,
    plan: Mapping[str, Any],
    ensemble: Mapping[str, Any],
    whole_trace: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
):
    rendered, media_plan, spine_v2, perceptual_trace = _BASE_APPLY(
        rendered, plan, ensemble, whole_trace, asset_bindings
    )
    rendered, media_plan, perceptual_trace = apply_premium_perception_reauthorship(
        rendered,
        whole_trace,
        asset_bindings,
        media_plan,
        perceptual_trace,
    )
    return rendered, media_plan, spine_v2, perceptual_trace


def install_runtime_adapter() -> None:
    """Install exactly once after the Issue #129 narrative namespace adapter."""
    if getattr(_base, "_issue132_runtime_installed", False):
        return
    _base.apply_premium_perception_recovery = _apply_issue132_wrapper
    _base._issue132_runtime_installed = True


__all__ = ["install_runtime_adapter"]
