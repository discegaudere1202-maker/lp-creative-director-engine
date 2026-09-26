"""Guarded consumption boundary for authored CompositionPlans.

Shadow mode remains available for regression. Production mode is explicit and
fail-closed: it accepts only a complete frozen plan and never falls back to a
legacy profile or re-infers authored form.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .authored_composition_contract import (
    RESPONSIVE_WIDTHS,
    assert_no_identity_routing,
)


class MigrationGuardError(ValueError):
    """Raised when a plan attempts to bypass the fit/feasibility boundary."""


def consume_composition_plan(
    plan: Mapping[str, Any],
    *,
    mode: str = "shadow",
) -> dict[str, Any]:
    """Return renderer directives without performing new creative inference.

    Only shadow mode is enabled by this issue. The returned directives are
    derived exclusively from the frozen authored plan and are safe to compare
    with accepted outputs before production routing is switched.
    """
    if mode not in {"shadow", "production"}:
        raise MigrationGuardError("unsupported composition-plan mode")
    if mode == "production" and (plan.get("review_gate", {}).get("status") == "HUMAN_REVIEW_REQUIRED"):
        raise MigrationGuardError("production plan requires human review before rendering")
    if not plan.get("family_frozen") or plan.get("fit_trace", {}).get("identity_used"):
        raise MigrationGuardError("composition plan is not migration-safe")
    assert_no_identity_routing(plan)
    responsive = plan.get("responsive_authorship") or {}
    widths = tuple(responsive.get("widths") or ())
    if widths != RESPONSIVE_WIDTHS:
        raise MigrationGuardError("all 9 responsive widths are required")
    topology = deepcopy(dict(plan.get("topology") or {}))
    variation = deepcopy(dict(plan.get("variation_vector") or {}))
    if not topology or not variation:
        raise MigrationGuardError("authored topology and variation are required")
    required_topology = {"hero", "core_decision", "trust_proof", "closing", "scene_order"}
    if mode == "production" and not required_topology.issubset(topology):
        raise MigrationGuardError("production plan is missing mandatory topology directives")
    return {
        "mode": mode,
        "family_id": plan["family_id"],
        "family_version": plan["family_version"],
        "scene_intents": deepcopy(plan.get("scene_intents") or []),
        "topology": topology,
        "variation_vector": variation,
        "responsive_authorship": deepcopy(responsive),
        "feasibility": deepcopy(plan.get("feasibility") or {}),
        "review_gate": deepcopy(plan.get("review_gate") or {}),
        "renderer_must_not_reinfer": True,
    }


def migration_guard(plan: Mapping[str, Any], *, mode: str = "shadow") -> dict[str, Any]:
    """Emit auditable guards for shadow or guarded Production consumption."""
    directives = consume_composition_plan(plan, mode=mode)
    return {
        "status": "PRODUCTION_AUTHORITY" if mode == "production" else "SHADOW_ONLY",
        "family_frozen": directives["family_id"] == plan["family_id"],
        "identity_routing": False,
        "reference_lookup": False,
        "random_variation": False,
        "responsive_widths": list(RESPONSIVE_WIDTHS),
        "renderer_must_not_reinfer": True,
    }


__all__ = ["MigrationGuardError", "consume_composition_plan", "migration_guard"]
