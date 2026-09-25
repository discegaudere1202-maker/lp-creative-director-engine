from __future__ import annotations

import json

from lp_engine.controlled_production import nagi_reference_input, run_controlled_nagi_production, _select_module_grammar
from lp_engine.production_generation import run_generation


def test_issue53_nagi_path_uses_runtime_inference_and_freezes_family(tmp_path):
    result = run_controlled_nagi_production(tmp_path / "nagi")
    assert result["status"] == "PASS"
    trace = result["trace"]
    assert trace["integration_contract_version"] == "issue53-controlled-production-v1"
    assert trace["runtime_inference"]["dominant_family"] == "BW-F08"
    assert trace["selection"]["selection_basis"] == "creative_fit"
    assert trace["selection"]["family_change_allowed"] is False
    assert trace["production_feasibility"]["schema_version"] == "production_feasibility_profile_v1"
    assert trace["module_grammar"]["selection_basis"].startswith("dominant_family")
    html = (tmp_path / "nagi" / "site" / "index.html").read_text(encoding="utf-8")
    assert 'data-creative-family="BW-F08"' in html
    assert "module-grammar" in html
    assert 'architecture_pattern_id&quot;: &quot;M-HERO-01&quot;' in html
    compositions = json.loads((tmp_path / "nagi" / "site" / "compositions.json").read_text(encoding="utf-8"))
    assert all(item["architecture_pattern_id"] for item in compositions)


def test_issue53_reference_input_keeps_truth_and_feasibility_separate():
    raw = nagi_reference_input()
    assert raw["company"]["company_name"] == "なぎのみらい"
    assert "photo_asset_quantity" not in json.dumps(raw["customer_decision_state"])
    assert raw["customer_decision_state"]["signal"] == "category education"
    assert raw["evidence_ledger"][0]["verification_status"] == "VERIFIED"


def test_same_family_compatible_grammar_changes_generation_not_just_metadata(tmp_path):
    raw = nagi_reference_input()
    base = _select_module_grammar("BW-F08", raw["customer_decision_state"])
    alternative = dict(base)
    alternative["selected_patterns"] = [
        {"pattern_id": "M-HERO-03", "name": "Guided-choice Hero", "mobile_principle": "one readable route at a time"},
        *base["selected_patterns"][1:],
    ]
    first = {"dominant_family": "BW-F08", "module_grammar": base}
    second = {"dominant_family": "BW-F08", "module_grammar": alternative}
    raw["validation_context"] = "NO_WEB_FIELD_VALIDATION"
    a = run_generation(raw, tmp_path / "a", generation_id="issue53-a", architecture=first)
    b = run_generation(raw, tmp_path / "b", generation_id="issue53-b", architecture=second)
    html_a = (tmp_path / "a" / "index.html").read_text(encoding="utf-8")
    html_b = (tmp_path / "b" / "index.html").read_text(encoding="utf-8")
    assert a.production_output_allowed and b.production_output_allowed
    assert 'architecture_pattern_id&quot;: &quot;M-HERO-01&quot;' in html_a
    assert 'architecture_pattern_id&quot;: &quot;M-HERO-03&quot;' in html_b
    assert html_a != html_b
    assert first["dominant_family"] == second["dominant_family"] == "BW-F08"