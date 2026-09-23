import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OUT = ROOT / "artifacts" / "round3n_nagi_visual_continuity"


def test_visual_continuity_ledger_contract():
    ledger = json.loads((OUT / "visual_continuity_ledger.json").read_text(encoding="utf-8"))
    assert ledger["status"] == "PASS"
    assert ledger["composition_family_count"] >= 3
    assert ledger["non_flat_environmental_background_count"] >= 2
    assert ledger["strong_dark_anchor_count"] >= 1
    assert ledger["standalone_photo_card_only"] is False
    assert ledger["old_selector_architecture"] is False
    assert ledger["unsafe_evidence_imagery"] is False


def test_copy_safety_and_visual_qa_remain_explicit():
    final_qa = json.loads((OUT / "final_qa.json").read_text(encoding="utf-8"))
    copy = json.loads((OUT / "copy_ssot.json").read_text(encoding="utf-8"))
    evidence = json.loads((OUT / "evidence_boundary.json").read_text(encoding="utf-8"))
    assert final_qa["copy_persuasion_safety"] == "PRESERVED_FROM_ROUND_3K_R2"
    assert copy["status"] == "COPY_READY"
    assert evidence["status"] == "PASS"
    assert final_qa["status"].startswith("HOLD")
