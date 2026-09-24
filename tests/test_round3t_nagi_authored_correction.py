import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round3t_nagi_authored_correction"


def test_round3t_holds_human_gate_and_has_required_evidence():
    summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "HOLD — SARAH HUMAN VISUAL REVIEW PENDING"
    assert summary["human_review_ready"] == "YES"
    assert summary["formal_human_quality_pass"] is False
    assert summary["round3t"]["g5"] == "HUMAN_REVIEW_PENDING"
    for name in ("s3_s4_collision_metrics.json", "rendered_copy_snapshot.json", "round3t_regression_ledger.json", "manifest.json"):
        assert (OUT / name).is_file(), name


def test_round3t_browser_and_copy_gates_are_fail_closed():
    qa = json.loads((OUT / "browser_qa.json").read_text(encoding="utf-8"))
    assert qa["status"] == "PASS"
    assert qa["total"] == 9 and qa["pass"] == 9 and qa["fail"] == 0
    copy = json.loads((OUT / "rendered_copy_snapshot.json").read_text(encoding="utf-8"))
    assert copy["status"] == "PASS"
    assert copy["unauthorized_customer_copy"] == []
    collision = json.loads((OUT / "s3_s4_collision_metrics.json").read_text(encoding="utf-8"))
    assert collision["status"] == "PASS"
    assert all(not value[scene]["overlap"] for value in collision["measured"].values() for scene in ("S3", "S4"))


def test_round3t_preserves_architecture_and_s6():
    html = (OUT / "site" / "index.html").read_text(encoding="utf-8")
    assert all(f'id="s{i}"' in html for i in range(1, 9))
    assert 'class="scene trust"' in html
    assert "ここでは確認できていません。" in html
    assert "文面の例です" not in html
