import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round4c_nagi_final_copy_visual_grammar"


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_round4c_browser_and_fixed_header_pass():
    browser = load("browser_qa.json")
    fixed = load("fixed_header_measurements.json")
    assert browser["status"] == "PASS"
    assert browser["total"] == 9
    assert browser["pass"] == 9
    assert fixed["status"] == "PASS"


def test_round4c_exact_copy_and_forbidden_language():
    snapshot = load("rendered_copy_snapshot.json")
    audit = load("visitor_production_language_audit.json")
    assert snapshot["S4"]["headline"] == "ヘッドスパを見ていて、|「どうやっているんだろう」が残ったら。"
    assert snapshot["S4"]["body"] == [
        "受けることに興味があったのに、気づけば、技術のほうを見ている。",
        "なぎのみらいの公式Instagramを見る ↗",
    ]
    assert snapshot["S5"]["headline"] == "ヒーリングは、|分かってから考えたい。"
    assert audit["status"] == "PASS"
    assert audit["forbidden_matches"] == []


def test_round4c_preserve_ledger_and_contract():
    ledger = load("preserve_intentional_incidental_regression_ledger.json")
    contract = load("round4c_contract_report.json")
    assert ledger["status"] == "PASS"
    assert ledger["regressions"] == []
    assert contract["status"] == "PASS"
    assert contract["HR-12"] == "HUMAN_PENDING"


def test_round4c_manifest_and_required_evidence():
    manifest = load("manifest.json")
    required = [
        "browser_qa.json",
        "fixed_header_measurements.json",
        "rendered_copy_snapshot.json",
        "visitor_production_language_audit.json",
        "scene_authority_motif_audit.json",
        "actual_geometry_measurements.json",
        "preserve_intentional_incidental_regression_ledger.json",
        "round4c_contract_report.json",
        "final_qa.json",
        "summary.json",
    ]
    paths = {entry["path"] for entry in manifest["files"]}
    assert all(item in paths for item in required)
    assert any(entry["path"] == "desktop/full_1440.png" for entry in manifest["files"])
    assert any(entry["path"] == "mobile/full_390.png" for entry in manifest["files"])
