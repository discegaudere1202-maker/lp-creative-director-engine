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

    Issue #132 is downstream of the accepted source-binding contract, so R2 may
    change hierarchy but must not collapse a rights-gated source image to zero
    geometry. Two narrow compatibility rules preserve that invariant while the
    new authored media remains the perceptual authority.
    """
    css_parts: list[str] = []
    if 'data-r2-profile="salon_material_workbench"' in rendered:
        css_parts.append(r'''
@media(min-width:901px) and (max-width:1360px){
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
''')
    if 'data-r2-profile="pilates_studio_action"' in rendered:
        css_parts.append(r'''
body[data-r2-profile="pilates_studio_action"] .r2-studio_path .service-field__media{
 display:block!important;
 width:clamp(112px,15vw,176px)!important;
 max-width:32%!important;
 margin:28px 0 0 auto!important;
 opacity:.52!important;
 filter:saturate(.68) contrast(.92)!important;
}
body[data-r2-profile="pilates_studio_action"] .r2-studio_path .service-field__media .production-asset{
 width:100%!important;
 margin:0!important;
}
body[data-r2-profile="pilates_studio_action"] .r2-studio_path .service-field__media .production-asset img{
 display:block!important;
 width:100%!important;
 height:auto!important;
 aspect-ratio:16/9!important;
 object-fit:cover!important;
}
body[data-r2-profile="pilates_studio_action"] .r2-studio_path .service-field__media .production-asset figcaption{
 font-size:8px!important;
 line-height:1.2!important;
 opacity:.72!important;
}
@media(max-width:700px){
 body[data-r2-profile="pilates_studio_action"] .r2-studio_path .service-field__media{
  width:118px!important;
  max-width:38%!important;
  margin:20px 0 0 auto!important;
 }
}
''')
    if not css_parts:
        return rendered
    if "</style>" not in rendered:
        raise RuntimeError("ISSUE132_COMPAT_STYLE_ANCHOR_MISSING")
    return rendered.replace("</style>", "".join(css_parts) + "</style>", 1)


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
