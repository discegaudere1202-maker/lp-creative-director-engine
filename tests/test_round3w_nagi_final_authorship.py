import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "artifacts/round3w_nagi_final_authorship"

def test_round3w_contract_and_artifact():
    qa = json.loads((OUT / "browser_qa.json").read_text(encoding="utf-8"))
    assert qa["status"] == "PASS" and qa["total"] == 9 and qa["pass"] == 9
    assert json.loads((OUT / "fixed_header_geometry.json").read_text(encoding="utf-8"))["status"] == "PASS"
    assert json.loads((OUT / "round3w_contract_report.json").read_text(encoding="utf-8"))["AC-09"] == "PASS"

def test_round3w_holds_human_gate():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "HOLD — SARAH HUMAN VISUAL REVIEW PENDING"
    assert summary["formal_human_quality_pass"] is False
    assert summary["human_review_ready"] == "YES"

def test_round3w_preserves_six_and_eight():
    html = (OUT / "site/index.html").read_text(encoding="utf-8")
    assert all(f'id="s{i}"' in html for i in range(1, 9))
    assert 'class="scene trust"' in html and 'class="scene ending"' in html
    assert "うまく聞こうと、" not in html
