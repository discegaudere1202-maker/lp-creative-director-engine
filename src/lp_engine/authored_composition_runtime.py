"""Shadow consumption boundary for authored composition plans.

Production routing remains unchanged until shadow validation is complete. This
adapter proves that a renderer can consume a plan without re-selecting Family,
profile, or topology from identity.
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
    if mode != "shadow":
        raise MigrationGuardError(
            "production routing is disabled until shadow validation passes"
        )
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
    return {
        "mode": "shadow",
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


def migration_guard(plan: Mapping[str, Any]) -> dict[str, Any]:
    """Emit auditable guards for the pre-production migration stage."""
    directives = consume_composition_plan(plan, mode="shadow")
    return {
        "status": "SHADOW_ONLY",
        "family_frozen": directives["family_id"] == plan["family_id"],
        "identity_routing": False,
        "reference_lookup": False,
        "random_variation": False,
        "responsive_widths": list(RESPONSIVE_WIDTHS),
        "renderer_must_not_reinfer": True,
    }


__all__ = ["MigrationGuardError", "consume_composition_plan", "migration_guard"]
