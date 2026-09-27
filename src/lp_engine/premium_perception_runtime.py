"""Issue #129 integration adapter for legacy Issue #111 cardinality locks.

Issue #111 intentionally audits the two *source binding placements* rendered by
its historical Production surface.  Issue #129 reuses those same rights-gated
sources in additional Media Narrative scenes.  Those authored reuses are not
new bindings and must therefore not masquerade as additional legacy
``production-asset`` bindings.

This adapter keeps the source/evidence data attributes and captions intact, but
marks narrative reuses as ``ppr-production-asset``.  Issue #111 continues to
inspect exactly the original binding placements; Issue #129 separately inspects
all narrative placements at 81 widths.  No rights/evidence gate is weakened.
"""
from __future__ import annotations

from typing import Any, Mapping

from . import premium_perception_recovery as _base
from .visual_asset_library import render_asset_binding as _render_asset_binding


def _narrative_figure(binding: Mapping[str, Any], beat: Mapping[str, Any], index: int) -> str:
    rendered = _render_asset_binding(binding).replace(
        'class="production-asset"',
        'class="ppr-production-asset"',
        1,
    )
    return (
        f'<div class="ppr-media ppr-media--{_base._esc(beat["prominence_intent"])} '
        f'ppr-crop--{_base._esc(beat["crop_geometry"])}" '
        f'data-media-role="{_base._esc(beat["narrative_role"])}" data-media-beat="{index:02d}" '
        f'data-evidence-status="{_base._esc(beat["evidence_status"])}">{rendered}</div>'
    )


def _css() -> str:
    css = _BASE_CSS()
    # Only selectors scoped inside the Issue #129 narrative surface are
    # rewritten. Original Production bindings keep .production-asset unchanged.
    return css.replace(".ppr-media .production-asset", ".ppr-media .ppr-production-asset").replace(
        ".ppr-media--dominant .production-asset", ".ppr-media--dominant .ppr-production-asset"
    ).replace(
        ".ppr-media--co-dominant .production-asset", ".ppr-media--co-dominant .ppr-production-asset"
    ).replace(
        ".ppr-media--supporting .production-asset", ".ppr-media--supporting .ppr-production-asset"
    ).replace(
        ".ppr-crop--detail_strip .production-asset", ".ppr-crop--detail_strip .ppr-production-asset"
    ).replace(
        ".ppr-crop--macro_detail_strip .production-asset", ".ppr-crop--macro_detail_strip .ppr-production-asset"
    ).replace(
        ".ppr-crop--detail_matrix_cut .production-asset", ".ppr-crop--detail_matrix_cut .ppr-production-asset"
    ).replace(
        ".ppr-crop--macro_process_detail .production-asset", ".ppr-crop--macro_process_detail .ppr-production-asset"
    ).replace(
        ".ppr-crop--portrait_offset .production-asset", ".ppr-crop--portrait_offset .ppr-production-asset"
    ).replace(
        ".ppr-crop--portrait_or_square_anchor .production-asset", ".ppr-crop--portrait_or_square_anchor .ppr-production-asset"
    ).replace(
        ".ppr-crop--paired_equal_a .production-asset", ".ppr-crop--paired_equal_a .ppr-production-asset"
    ).replace(
        ".ppr-crop--paired_equal_b .production-asset", ".ppr-crop--paired_equal_b .ppr-production-asset"
    )


_BASE_FIGURE = _base._narrative_figure
_BASE_CSS = _base._css


def apply_premium_perception_recovery(
    rendered: str,
    plan: Mapping[str, Any],
    ensemble: Mapping[str, Any],
    whole_trace: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
):
    old_figure = _base._narrative_figure
    old_css = _base._css
    _base._narrative_figure = _narrative_figure
    _base._css = _css
    try:
        return _base.apply_premium_perception_recovery(
            rendered, plan, ensemble, whole_trace, asset_bindings
        )
    finally:
        _base._narrative_figure = old_figure
        _base._css = old_css


__all__ = ["apply_premium_perception_recovery"]
