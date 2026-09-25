from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lp_engine.production_architecture import (
    CREATIVE_FIT_SCHEMA, FEASIBILITY_SCHEMA, FAMILY_IDS, FIT_DIMENSIONS,
    RESEMBLANCE_DIMENSIONS, evaluate_resemblance, load_json, select_family,
    validate_creative_fit, validate_production_feasibility, validate_provenance,
    validate_resemblance_contract, validate_selection_contract,
)

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "data" / "production_architecture"


def fit():
    return {"schema_version": CREATIVE_FIT_SCHEMA, "profile_id": "fixture-fit", "dimensions": {name: 0.5 for name in FIT_DIMENSIONS}, "dominant_family": "BW-F05", "secondary_families": ["BW-F08"], "source_refs": ["issue44:creative_profile_recommendation"]}


def feasibility():
    return {"schema_version": FEASIBILITY_SCHEMA, "profile_id": "fixture-feasibility", "dimensions": {name: 0.5 for name in ("photo_asset_quantity", "evidence_quantity_available", "scraping_difficulty", "source_coverage", "rights_clarity", "staff_photo_availability", "facility_photo_availability", "pricing_completeness", "social_proof_availability")}, "adaptation_policy": {"may_change_family": False, "notes": ["use safe realization within selected family"]}, "source_refs": ["issue44:feasibility-gap"]}


def test_fit_and_feasibility_are_separate_and_versioned():
    validate_creative_fit(fit())
    validate_production_feasibility(feasibility())
    bad = copy.deepcopy(fit()); bad["dimensions"].pop("warmth"); bad["dimensions"]["evidence_quantity_available"] = 0.2
    with pytest.raises(ValueError, match="feasibility leaked"):
        validate_creative_fit(bad)
    bad = copy.deepcopy(feasibility()); bad["dominant_family"] = "BW-F01"
    with pytest.raises(ValueError, match="embedded"):
        validate_production_feasibility(bad)


def test_selector_is_fit_led_and_feasibility_cannot_change_family():
    candidates = [{"family_id": family} for family in FAMILY_IDS]
    result = select_family(fit=fit(), feasibility=feasibility(), candidates=candidates)
    validate_selection_contract(result)
    assert result["dominant_family"] == "BW-F05"
    assert result["selection_basis"] == "creative_fit"
    assert result["family_change_allowed"] is False


def test_taxonomy_is_eight_candidates_without_fixed_layout():
    taxonomy = load_json(ARCH / "family_taxonomy_candidates_v1.json")
    assert taxonomy["not_templates"] is True
    assert {row["family_id"] for row in taxonomy["families"]} == set(FAMILY_IDS)
    assert all("fit_signals" in row and "prohibited_shortcuts" in row for row in taxonomy["families"])
    assert not any("layout" in json.dumps(row).lower() for row in taxonomy["families"])


def test_module_registry_is_grammar_and_has_compatibility():
    registry = load_json(ARCH / "module_composition_registry_v1.json")
    assert registry["status"] == "RESEARCH_GRAMMAR_NOT_COMPONENT_LIBRARY"
    assert len(registry["patterns"]) >= 14
    assert all(row["compatible_families"] and row["mobile_principle"] for row in registry["patterns"])
    assert any(row["pattern_id"] == "M-HUMAN-01" and "evidence" in row["incompatible_conditions"][0] for row in registry["patterns"])


def test_resemblance_rejects_token_swaps_and_preserves_human_review():
    contract = load_json(ARCH / "template_resemblance_contract_v0.json")
    validate_resemblance_contract(contract)
    basis = contract["labeled_pair_basis"]
    assert basis["source_artifact"] == "artifacts/issue44_riko/closure/template_resemblance_labeled_pairs_v1.json"
    assert basis["pair_count"] == 24
    assert sum(basis["class_counts"].values()) == 24
    assert basis["same_template_looking_pairs"] == "obvious_same_template_skin_swap"
    observed = {name: "same" for name in RESEMBLANCE_DIMENSIONS}
    assert evaluate_resemblance(observed=observed, token_only_change=True)["status"] == "FAIL"
    assert evaluate_resemblance(observed=observed, token_only_change=False)["status"] == "HUMAN_REVIEW_REQUIRED"


def test_provenance_points_to_issue44_and_contracts():
    manifest = load_json(ARCH / "provenance_manifest_v1.json")
    validate_provenance(manifest)
    assert manifest["research_head"] == "135e15276da07279731d48ff2b1306fae2411db4"
    assert len(manifest["source_artifacts"]) >= 8


def test_contract_jsons_have_expected_schema_versions():
    assert load_json(ARCH / "creative_fit_profile_schema_v1.json")["schema_version"] == CREATIVE_FIT_SCHEMA
    assert load_json(ARCH / "production_feasibility_schema_v1.json")["schema_version"] == FEASIBILITY_SCHEMA
