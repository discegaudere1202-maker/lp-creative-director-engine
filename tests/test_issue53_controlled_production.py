from __future__ import annotations

import json

from lp_engine.controlled_production import nagi_reference_input, run_controlled_nagi_production


def test_issue53_nagi_path_uses_runtime_inference_and_freezes_family(tmp_path):
    result = run_controlled_nagi_production(tmp_path / "nagi")
    assert result["status"] == "PASS"
    trace = result["trace"]
    assert trace["runtime_inference"]["dominant_family"] == "BW-F08"
    assert trace["selection"]["selection_basis"] == "creative_fit"
    assert trace["selection"]["family_change_allowed"] is False
    assert trace["production_feasibility"]["schema_version"] == "production_feasibility_profile_v1"
    assert trace["module_grammar"]["selection_basis"].startswith("dominant_family")
    html = (tmp_path / "nagi" / "site" / "index.html").read_text(encoding="utf-8")
    assert 'data-creative-family="BW-F08"' in html
    assert "module-grammar" in html


def test_issue53_reference_input_keeps_truth_and_feasibility_separate():
    raw = nagi_reference_input()
    assert raw["company"]["company_name"] == "なぎのみらい"
    assert "photo_asset_quantity" not in json.dumps(raw["customer_decision_state"])
    assert raw["customer_decision_state"]["signal"] == "category education"
    assert raw["evidence_ledger"][0]["verification_status"] == "VERIFIED"
