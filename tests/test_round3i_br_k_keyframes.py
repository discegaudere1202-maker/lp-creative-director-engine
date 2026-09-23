from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round3i_br_k"


def test_keyframe_contract_and_qa() -> None:
    assert (OUT / "04_keyframe_a_1440.png").exists()
    assert (OUT / "05_keyframe_b_1440.png").exists()
    assert (OUT / "06_keyframe_c_1440.png").exists()
    qa = json.loads((OUT / "12_technical_qa.json").read_text(encoding="utf-8"))
    assert qa["status"] == "PASS"
    assert qa["internal_wording_leak"] == 0
    assert qa["evidence_boundary_violation"] == 0
    assert {row["width"] for row in qa["browser"]["rows"]} == {1440, 390, 320}


def test_manifest_has_reproduction_and_specs() -> None:
    manifest = json.loads((OUT / "artifact_manifest.json").read_text(encoding="utf-8"))
    paths = {row["path"] for row in manifest["files"]}
    for required in (
        "01_art_direction_spec.json",
        "02_safe_visual_authority.json",
        "07_background_resolution.json",
        "08_typography_role_spec.json",
        "09_composition_spec.json",
        "10_renderer_preserve_manifest.json",
        "11_keyframe_review_manifest.md",
        "12_technical_qa.json",
        "reproduction/index.html",
    ):
        assert required in paths
