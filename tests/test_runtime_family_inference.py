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
    infer_and_select_family,
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
        assert result["dominant_family"] == expected["dominant"], f"case={expected['case_id']} result={result}"
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

    leaked_truth = {"verified": True, "facts": {"photo_asset_quantity": 0.9}}
    with pytest.raises(ValueError, match="feasibility"):
        infer_creative_family(company_truth=leaked_truth, customer_decision_state="choose", creative_fit=_fit(expected))


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


def test_collision_rules_are_executed_and_unresolved_pairs_stop_for_review():
    expected, company = next(row for row in _records() if row[0]["case_id"] == "V49-03")
    result = infer_creative_family(
        company_truth={"verified": True, "facts": company["company_intelligence"]},
        customer_decision_state=company["customer_decision_state"],
        creative_fit=_fit(expected),
    )
    assert result["dominant_family"] == "BW-F02"
    assert result["collision_rule"] is None

    unresolved = infer_creative_family(
        company_truth={"verified": True, "facts": ["safety and measurable mechanism evidence are both central"]},
        customer_decision_state="the customer needs safety reassurance and measurable mechanism proof equally",
        creative_fit=_fit(expected),
    )
    assert unresolved["dominant_family"] is None
    assert unresolved["collision_rule"] == "C02_C06"
    assert unresolved["human_review_required"] is True


def _neutral_fit():
    return {
        "schema_version": "creative_fit_profile_v1",
        "profile_id": "synthetic-collision-matrix",
        "dimensions": {name: 0.5 for name in FIT_DIMENSIONS},
        "source_refs": ["test:collision-matrix"],
    }


@pytest.mark.parametrize(
    "rule_id,left_family,left_signal,right_family,right_signal",
    [
        ("C02_C06", "BW-F02", "safety", "BW-F06", "measurable"),
        ("C05_C08", "BW-F05", "self-select", "BW-F08", "first-timer"),
        ("C01_C04", "BW-F01", "sensory", "BW-F04", "provenance"),
        ("C03_C04", "BW-F03", "aspirational", "BW-F04", "maker"),
        ("C04_C07", "BW-F04", "craft", "BW-F07", "community"),
        ("C06_C08", "BW-F06", "measurable", "BW-F08", "category education"),
    ],
)
def test_each_collision_pair_resolves_both_directions(
    _rule_id, left_family, left_signal, right_family, right_signal
):
    for expected_family, signal in ((left_family, left_signal), (right_family, right_signal)):
        result = infer_creative_family(
            company_truth={"verified": True, "facts": ["synthetic service"]},
            customer_decision_state=f"the primary decision job is {signal}",
            creative_fit=_neutral_fit(),
        )
        assert result["dominant_family"] == expected_family, result
        assert result["human_review_required"] is False


@pytest.mark.parametrize(
    "rule_id,left_signal,right_signal",
    [
        ("C02_C06", "safety", "measurable"),
        ("C05_C08", "self-select", "first-timer"),
        ("C01_C04", "sensory", "provenance"),
        ("C03_C04", "aspirational", "maker"),
        ("C04_C07", "craft", "community"),
        ("C06_C08", "measurable", "category education"),
    ],
)
def test_each_collision_pair_requires_human_review_when_both_sides_remain(
    rule_id, left_signal, right_signal
):
    result = infer_creative_family(
        company_truth={"verified": True, "facts": ["synthetic service"]},
        customer_decision_state=f"{left_signal} and {right_signal} are equally important",
        creative_fit=_neutral_fit(),
    )
    assert result["dominant_family"] is None
    assert result["collision_rule"] == rule_id
    assert result["ambiguity_state"] == "CO_DOMINANT_HUMAN_REVIEW"
    assert result["human_review_required"] is True


@pytest.mark.parametrize(
    "decision_state",
    [
        {"summary": "route care", "photo_asset_quantity": 0.9},
        {"signals": {"source_coverage": 0.5}},
    ],
)
def test_customer_decision_state_cannot_leak_production_feasibility(decision_state):
    expected, _company = next(_records())
    with pytest.raises(ValueError, match="feasibility"):
        infer_creative_family(
            company_truth={"verified": True, "facts": ["synthetic service"]},
            customer_decision_state=decision_state,
            creative_fit=_fit(expected),
        )


def test_inference_freezes_fit_before_feasibility_selection():
    expected, company = next(_records())
    feasibility = {
        "schema_version": "production_feasibility_profile_v1",
        "profile_id": "separate-feasibility",
        "dimensions": {name: 0.9 for name in FEASIBILITY_DIMENSIONS},
        "adaptation_policy": {"may_change_family": False},
        "source_refs": ["test:separate-feasibility"],
    }
    output = infer_and_select_family(
        company_truth={"verified": True, "facts": company["company_intelligence"]},
        customer_decision_state=company["customer_decision_state"],
        creative_fit=_fit(expected),
        feasibility=feasibility,
        candidates=[{"family_id": family} for family in FAMILY_IDS],
    )
    assert output["selection"]["dominant_family"] == expected["dominant"]
    assert output["selection"]["family_change_allowed"] is False
