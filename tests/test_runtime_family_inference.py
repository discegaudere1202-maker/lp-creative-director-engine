from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from lp_engine.production_architecture import (
    FEASIBILITY_DIMENSIONS,
    FIT_DIMENSIONS,
    FAMILY_IDS,
    infer_creative_family,
    select_family,
)

ROOT = Path(__file__).resolve().parents[1]
ISSUE49 = ROOT / "artifacts" / "issue49_riko"


def _load_issue49_json(path: Path):
    # The accepted Issue #49 ordinal fixture uses JSON-like shorthand such as .75.
    # Keep the SSOT unchanged and normalize only at the test boundary.
    raw = path.read_text(encoding="utf-8")
    return json.loads(re.sub(r"(?<![0-9A-Za-z_])\.(\d+)", r"0.\1", raw))


def _records():
    labels = _load_issue49_json(ISSUE49 / "creative_fit_expected_labels.json")["records"]
    companies = _load_issue49_json(ISSUE49 / "validation_company_registry.json")["companies"]
    by_id = {row["case_id"]: row for row in companies}
    for row in labels:
        company = by_id[row["case_id"]]
        yield row, company


def _fit(record):
    return {
        "schema_version": "creative_fit_profile_v1",
        "profile_id": f"fixture-{record['case_id']}",
        "dimensions": dict(zip(FIT_DIMENSIONS, record["scores"])),
        "source_refs": ["issue49:creative_fit_expected_labels"],
    }


def test_issue49_16_cases_infer_two_per_family_without_case_lookup():
    results = []
    for expected, company in _records():
        result = infer_creative_family(
            company_truth={"verified": True, "company": company["company"], "facts": company["company_intelligence"]},
            customer_decision_state=company["customer_decision_state"],
            creative_fit=_fit(expected),
        )
        assert result["dominant_family"] == expected["dominant"]
        assert result["feasibility_ignored_at_selection"] is True
        assert "layout_id" not in result
        assert set(result["fit_dimensions_used"]) == set(FIT_DIMENSIONS)
        results.append(result["dominant_family"])
    assert {family: results.count(family) for family in FAMILY_IDS} == {family: 2 for family in FAMILY_IDS}


def test_feasibility_is_post_selection_and_cannot_change_family():
    expected, company = next(_records())
    result = infer_creative_family(
        company_truth={"verified": True, "facts": company["company_intelligence"]},
        customer_decision_state=company["customer_decision_state"],
        creative_fit=_fit(expected),
    )
    selected_fit = {**_fit(expected), "dominant_family": result["dominant_family"], "secondary_families": result["secondary_influences"]}
    base = {name: 0.1 for name in FEASIBILITY_DIMENSIONS}
    rich = {name: 0.9 for name in FEASIBILITY_DIMENSIONS}
    base_profile = {"schema_version": "production_feasibility_profile_v1", "profile_id": "sparse", "dimensions": base, "adaptation_policy": {"may_change_family": False}, "source_refs": ["issue49:feasibility_invariance_checks"]}
    rich_profile = {"schema_version": "production_feasibility_profile_v1", "profile_id": "rich", "dimensions": rich, "adaptation_policy": {"may_change_family": False}, "source_refs": ["issue49:feasibility_invariance_checks"]}
    candidates = [{"family_id": family} for family in FAMILY_IDS]
    assert select_family(fit=selected_fit, feasibility=base_profile, candidates=candidates)["dominant_family"] == result["dominant_family"]
    assert select_family(fit=selected_fit, feasibility=rich_profile, candidates=candidates)["dominant_family"] == result["dominant_family"]


def test_inference_hard_fails_on_feasibility_leakage_and_unverified_truth():
    expected, company = next(_records())
    leaked = _fit(expected)
    leaked["dimensions"]["photo_asset_quantity"] = 0.5
    with pytest.raises(ValueError, match="feasibility"):
        infer_creative_family(company_truth={"verified": True}, customer_decision_state="choose", creative_fit=leaked)
    with pytest.raises(ValueError, match="verified"):
        infer_creative_family(company_truth={"verified": False}, customer_decision_state="choose", creative_fit=_fit(expected))


def test_unresolved_co_dominance_is_human_review_not_a_forced_winner():
    expected, _company = next(_records())
    fit = _fit(expected)
    fit["dimensions"] = {name: 0.5 for name in FIT_DIMENSIONS}
    result = infer_creative_family(
        company_truth={"verified": True, "facts": ["a service"]},
        customer_decision_state={"state": "a new context with no established decision job"},
        creative_fit=fit,
    )
    assert result["dominant_family"] is None
    assert result["ambiguity_state"] == "CO_DOMINANT_HUMAN_REVIEW"
    assert result["human_review_required"] is True


def test_prohibited_families_remain_explicit_and_are_not_substituted():
    expected, company = next(_records())
    result = infer_creative_family(
        company_truth={"verified": True, "facts": company["company_intelligence"], "prohibited_families": expected["prohibited"]},
        customer_decision_state=company["customer_decision_state"],
        creative_fit=_fit(expected),
    )
    assert result["prohibited_or_misfit"] == expected["prohibited"]
    assert result["dominant_family"] not in result["prohibited_or_misfit"]
