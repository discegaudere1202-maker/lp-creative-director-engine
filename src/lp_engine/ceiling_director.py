"""Generic Quality Ceiling Director contract.

This module is intentionally company-agnostic.  A company-specific creative
instance supplies the values; the engine only validates the decision shape and
keeps Floor and Ceiling status separate.
"""
from __future__ import annotations

from typing import Mapping

CEILING_CONTRACT_FIELDS = (
    "customer_tension",
    "owned_thesis",
    "copy_signature",
    "hero_topology_candidates",
    "selected_hero_topology",
    "photo_series_contract",
    "motion_thesis",
    "motion_peaks",
    "screenshot_peaks",
    "memorability_target",
    "secondary_visual_justification",
    "cross_lp_similarity_signature",
)


def validate_ceiling_director_contract(contract: Mapping[str, object]) -> dict[str, object]:
    """Validate the generic shape without supplying a Nagi-specific default."""

    missing = [field for field in CEILING_CONTRACT_FIELDS if field not in contract]
    empty = [field for field in CEILING_CONTRACT_FIELDS if field in contract and contract[field] in (None, "", [], {})]
    errors = [f"missing:{field}" for field in missing] + [f"empty:{field}" for field in empty]
    return {
        "schema_version": "quality_ceiling_director_contract_v1",
        "status": "PASS" if not errors else "FAIL",
        "required_fields": list(CEILING_CONTRACT_FIELDS),
        "errors": errors,
        "company_specific_defaults": False,
    }
