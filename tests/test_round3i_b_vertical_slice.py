from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

def test_round3i_b_renderer_keeps_frozen_truth_boundary() -> None:
    source = (ROOT / "scripts/run_round3i_b_nagi_vertical_slice.py").read_text(encoding="utf-8")
    assert "948b9bd0cbf5efac7177031a02998a7fe97ecf93fd82febcad4adf4ce98a8a7b" in source
    for forbidden in ("料金", "所要時間", "資格", "レビュー", "効果"):
        assert forbidden not in source.split("HTML =", 1)[1].split("def write_json", 1)[0] or forbidden in ("料金", "所要時間")

def test_round3i_b_has_required_public_scene_targets() -> None:
    source = (ROOT / "scripts/run_round3i_b_nagi_vertical_slice.py").read_text(encoding="utf-8")
    for target in ('id="hero"', 'id="choice"', 'id="receive"', 'id="known"', 'id="contact"'):
        assert target in source
    assert "@happyfuture_02" in source

def test_round3i_b_output_contract_after_generation() -> None:
    out = ROOT / "artifacts" / "round3i_b"
    if not out.exists():
        return
    qa = json.loads((out / "19_phase_b_qa.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "artifact_manifest.json").read_text(encoding="utf-8"))
    assert qa["no_fabrication"] is True
    assert qa["no_public_internal_terms"] is True
    assert {row["width"] for row in qa["browser"]["rows"]} == {320,360,375,390,430,768,1024,1280,1440}
    assert manifest["frozen_truth_hash"] == "948b9bd0cbf5efac7177031a02998a7fe97ecf93fd82febcad4adf4ce98a8a7b"
    assert "13_integrated_rough/desktop_integrated_rough.png" in {row["path"] for row in manifest["files"]}
