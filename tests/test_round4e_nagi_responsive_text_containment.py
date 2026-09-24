import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round4e_nagi_responsive_text_containment"


def load(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def test_nine_width_and_text_containment_pass():
    qa = load("browser_qa.json")
    diagnostics = load("text_containment_diagnostics.json")
    assert qa["status"] == "PASS"
    assert qa["pass"] == 9
    assert diagnostics["status"] == "PASS"
    assert all(d["pass"] for row in diagnostics["rows"] for d in row["diagnostics"])


def test_exact_copy_preserved():
    snapshot = load("rendered_copy_snapshot.json")
    assert snapshot["S4"]["headline"] == "ヘッドスパを見ていて、|「どうやっているんだろう」が残ったら。"
    assert snapshot["S5"]["headline"] == "ヒーリングは、|分かってから考えたい。"
    assert snapshot["S4"]["body"][0] == "受けることに興味があったのに、気づけば、技術のほうを見ている。"
    assert snapshot["S5"]["body"][0] == "名前だけで、自分に合うかまで決めるのはむずかしい。"


def test_required_capture_manifest_and_human_gate():
    manifest = load("manifest.json")
    paths = {item["path"] for item in manifest["files"]}
    assert "desktop/s2_1440.png" in paths
    assert "mobile/s7_320.png" in paths
    assert "mobile/s4_entry_320.png" in paths
    assert "text_containment_diagnostics.json" in paths
    assert load("final_qa.json")["human_visible_pass"] == "PENDING"
