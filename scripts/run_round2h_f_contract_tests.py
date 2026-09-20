"""CI-friendly Round 2H-F contract checks without pytest collection."""
from __future__ import annotations

from pathlib import Path

from run_round2h_f_nagi import FACTS, ROOT, build_html, copy_assets
from lp_engine.sales_sample_policy import PROVISIONAL, replacement_manifest


def main() -> int:
    temp = ROOT / "artifacts" / "round2h_f_contract_test_site"
    manifest = copy_assets(temp)
    markup = build_html(manifest).split("<script>", 1)[0]
    assert replacement_manifest(FACTS)["status"] == "PASS"
    assert replacement_manifest(FACTS)["replacement_count"] >= 10
    for label in ("ENTRY MAP", "BEFORE TOUCH", "OPEN SERVICE NOTE", "SERVICE NOTE", "CHOOSE BY INTENT"):
        assert label not in markup
    assert "3つの入口を見る" in markup
    assert ["触れられ前", "る前に"] != ["触れられ前に", "、話して"]
    role_assets = [
        ROOT / "assets/photography/stock/nagi_no_mirai/hand_technique.jpg",
        ROOT / "assets/photography/generated/nagi_no_mirai/school_learning_context.png",
        ROOT / "assets/photography/generated/nagi_no_mirai/healing_consultation_context.png",
    ]
    assert all(path.is_file() for path in role_assets)
    assert len({path.read_bytes()[:64] for path in role_assets}) == 3
    print("Round 2H-F contract checks PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
