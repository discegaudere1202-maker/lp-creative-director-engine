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


def _preserve_r2_regression_safety(rendered: str) -> str:
    """Preserve accepted source/semantic hard gates without undoing R2 authorship.

    R2 deliberately changes silhouette, hierarchy and material rhythm. Those
    changes must still keep every rights-gated legacy source geometrically real
    and every semantic headline unit atomic *and* inside its target viewport.
    These rules re-art-direct narrow/intermediate widths; no legacy gate is
    weakened and no semantic unit is split mechanically.
    """
    css_parts: list[str] = []
    if 'data-premium-reauthorship-r2="issue132"' in rendered:
        css_parts.append(r'''
@media(max-width:700px){
 body[data-premium-reauthorship-r2="issue132"] .r2-page-flow .premium-headline-unit.semantic-headline-unit{
  font-size:clamp(28px,8.5vw,34px)!important;
  line-height:.98!important;
  letter-spacing:-.045em!important;
  display:block!important;
  width:max-content!important;
  max-width:calc(100vw - 48px)!important;
 }
 body[data-premium-reauthorship-r2="issue132"] .r2-page-flow .premium-display-unit{
  font-size:clamp(24px,7vw,30px)!important;
  line-height:1.02!important;
  letter-spacing:-.035em!important;
  display:block!important;
  width:max-content!important;
  max-width:calc(100vw - 36px)!important;
 }
 body[data-premium-reauthorship-r2="issue132"] .r2-page-flow .wp-trust{
  grid-column:1/7!important;
  max-width:100%!important;
 }
 body[data-premium-reauthorship-r2="issue132"] .r2-page-flow .r2-closing>.wp-cta{
  grid-column:1/7!important;
  margin-left:0!important;
  margin-right:0!important;
  max-width:100%!important;
 }
}
''')
    if 'data-r2-profile="salon_material_workbench"' in rendered:
        css_parts.append(r'''
body[data-r2-profile="salon_material_workbench"] .r2-workbench>.wp-trust{
 grid-column:7/13!important;
 max-width:100%!important;
}
body[data-r2-profile="salon_material_workbench"] .r2-workbench .premium-display-unit{
 font-size:clamp(28px,3vw,40px)!important;
 line-height:1.02!important;
}
@media(min-width:701px) and (max-width:1360px){
 body[data-r2-profile="salon_material_workbench"] .r2-opening>.hero-route{
  grid-template-columns:1fr!important;
  grid-template-areas:"orientation" "routes" "media" "action"!important;
  gap:22px!important;
 }
 body[data-r2-profile="salon_material_workbench"] .r2-opening>.hero-route .hero-route__media{
  max-width:100%!important;
  width:100%!important;
 }
 body[data-r2-profile="salon_material_workbench"] .r2-opening>.hero-route .premium-headline-unit.semantic-headline-unit{
  font-size:clamp(38px,4vw,52px)!important;
  line-height:.96!important;
  display:block!important;
  width:max-content!important;
  max-width:100%!important;
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
 body[data-r2-profile="pilates_studio_action"] .r2-opening>.hero-recognition .hero-recognition__copy{
  left:18px!important;
  width:calc(100% - 36px)!important;
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
    rendered = _preserve_r2_regression_safety(rendered)
    return rendered, media_plan, spine_v2, perceptual_trace


def install_runtime_adapter() -> None:
    """Install exactly once after the Issue #129 narrative namespace adapter."""
    if getattr(_base, "_issue132_runtime_installed", False):
        return
    _base.apply_premium_perception_recovery = _apply_issue132_wrapper
    _base._issue132_runtime_installed = True


__all__ = ["install_runtime_adapter"]
