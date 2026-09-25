from __future__ import annotations

import json

from lp_engine.controlled_transfer import _feasibility, load_reference_contracts, reference_input, run_reference_company
from lp_engine.production_architecture import infer_and_select_family


def test_issue59_contracts_select_expected_families_without_company_lookup():
    for contract in load_reference_contracts():
        raw = reference_input(contract)
        truth = {"verified": True, "company": contract["company_name"], "facts": [raw["company"]["company_truth"]], "prohibited_families": contract["prohibited_families"]}
        fit = {"schema_version": "creative_fit_profile_v1", "profile_id": "test", "dimensions": {name: 0.5 for name in __import__("lp_engine.production_architecture", fromlist=["FIT_DIMENSIONS"]).FIT_DIMENSIONS}, "source_refs": contract["source_refs"]}
        selected = infer_and_select_family(company_truth=truth, customer_decision_state=contract["customer_state"], creative_fit=fit, feasibility=_feasibility(contract), candidates=[{"family_id": f} for f in ("BW-F01", "BW-F02", "BW-F03", "BW-F04", "BW-F05", "BW-F06", "BW-F07", "BW-F08")])
        assert selected["selection"]["dominant_family"] == contract["expected_family"]
        assert selected["selection"]["family_change_allowed"] is False


def test_issue59_feasibility_counterfactual_cannot_change_family(tmp_path):
    for contract in load_reference_contracts():
        result = run_reference_company(contract, tmp_path / contract["company_id"])
        assert result["status"] == "PASS"
        trace = result["trace"]
        assert trace["feasibility_counterfactual"]["family_unchanged"] is True
        assert trace["no_company_lookup"] is True
        assert trace["no_family_fixed_layout"] is True
        assert json.loads((tmp_path / contract["company_id"] / "site" / "render_spec.json").read_text(encoding="utf-8"))["controlled_architecture"]["family_frozen_before_feasibility"] is True
