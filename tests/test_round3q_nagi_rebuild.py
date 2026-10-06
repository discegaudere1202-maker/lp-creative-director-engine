import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round3q_nagi_rebuild"

def test_round3q_artifact_contract():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "HOLD — SARAH HUMAN VISUAL REVIEW PENDING"
    assert summary["gates"]["G0"] == "PASS"
    assert summary["gates"]["G4"] == "PASS"
    assert summary["gates"]["G5"] == "HUMAN_REVIEW_PENDING"
    assert summary["gates"]["G6"] == "NOT_STARTED"
    assert summary["manual_lp_edit"] == 0

def test_preservation_and_quality_ledgers():
    for name in ("approved_baseline_manifest.json", "preserve_ledger.json", "intentional_change_ledger.json", "copy_semantic_diff.json", "section_regression_matrix.json", "responsive_regression.json", "evidence_safety_regression.json", "quality_gain_loss_ledger.json"):
        assert (OUT / name).is_file(), name
    matrix = json.loads((OUT / "section_regression_matrix.json").read_text(encoding="utf-8"))
    assert matrix["regression_count"] == 0
    assert matrix["incidental_change_count"] == 0

def test_machine_browser_qa_is_green_without_promoting_human_gate():
    qa = json.loads((OUT / "browser_qa.json").read_text(encoding="utf-8"))
    assert qa["status"] == "PASS"
    assert qa["total"] == 9 and qa["pass"] == 9 and qa["fail"] == 0
    final = json.loads((OUT / "final_qa.json").read_text(encoding="utf-8"))
    assert final["human_visible_pass"] == "PENDING"
