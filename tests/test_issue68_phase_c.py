import json
from lp_engine.phase_c_expansion import FAMILY_DIMENSIONS, WIDTHS, load_phase_c_contracts, _fit, _feasibility, reference_input
from lp_engine.production_architecture import FEASIBILITY_DIMENSIONS, FIT_DIMENSIONS

def test_issue68_has_eight_references_and_four_families():
    rows = load_phase_c_contracts()
    assert len(rows) == 8
    assert {r["expected_family"] for r in rows} == {"BW-F01", "BW-F03", "BW-F05", "BW-F07"}
    assert len({r["reference_id"] for r in rows}) == 8
    assert tuple(WIDTHS) == (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)

def test_issue68_rows_are_not_company_selector_rules():
    for row in load_phase_c_contracts():
        assert row["company_id"] not in row["customer_state"]
        assert "company lookup" not in json.dumps(row).lower()

def test_issue68_fit_and_feasibility_are_separate():
    for row in load_phase_c_contracts():
        fit, feasibility = _fit(row), _feasibility(row)
        assert set(fit["dimensions"]) == set(FIT_DIMENSIONS)
        assert not set(fit["dimensions"]) & set(FEASIBILITY_DIMENSIONS)
        assert set(feasibility["dimensions"]) == set(FEASIBILITY_DIMENSIONS)
        assert feasibility["adaptation_policy"]["may_change_family"] is False

def test_issue68_generation_input_is_truth_bounded():
    for row in load_phase_c_contracts():
        payload = reference_input(row)
        assert payload["requested_claims"] == []
        assert payload["company_id"] == row["company_id"]
        assert all(x["rights_status"] == "PROJECT_OWNED_GENERATED" for x in payload["photo_assets"])
        assert all(x["alt"] == "参考ビジュアル" for x in payload["photo_assets"])
