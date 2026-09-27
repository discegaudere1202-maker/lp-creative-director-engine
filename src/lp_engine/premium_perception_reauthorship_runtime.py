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


def _preserve_legacy_binding_crop_safety(rendered: str) -> str:
    """Keep Issue #111 source-binding crop safety without weakening its gate.

    The HS1 R2 desktop overlay deliberately narrows the hero card. Between the
    legacy 900px mobile breakpoint and the full desktop layout that can collapse
    the hero's first internal grid track to zero width, which makes the original
    rights-gated source binding fail Issue #111's aspect-ratio visibility gate.
    Recompose only that tablet/intermediate range to a one-column internal hero
    while retaining the R2 outer overlap and page silhouette.
    """
    if 'data-r2-profile="salon_material_workbench"' not in rendered:
        return rendered
    css = r'''
@media(min-width:901px) and (max-width:1150px){
 body[data-r2-profile="salon_material_workbench"] .r2-opening>.hero-route{
  grid-template-columns:1fr!important;
  grid-template-areas:"orientation" "routes" "media" "action"!important;
  gap:22px!important;
 }
 body[data-r2-profile="salon_material_workbench"] .r2-opening>.hero-route .hero-route__media{
  max-width:100%!important;
  width:100%!important;
 }
}
'''
    if "</style>" not in rendered:
        raise RuntimeError("ISSUE132_COMPAT_STYLE_ANCHOR_MISSING")
    return rendered.replace("</style>", css + "</style>", 1)


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
    rendered = _preserve_legacy_binding_crop_safety(rendered)
    return rendered, media_plan, spine_v2, perceptual_trace


def install_runtime_adapter() -> None:
    """Install exactly once after the Issue #129 narrative namespace adapter."""
    if getattr(_base, "_issue132_runtime_installed", False):
        return
    _base.apply_premium_perception_recovery = _apply_issue132_wrapper
    _base._issue132_runtime_installed = True


__all__ = ["install_runtime_adapter"]
