import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts/round3i_br_f2"

def test_f2_artifact_and_known_line_regressions():
    qa=json.loads((OUT/"browser_qa.json").read_text(encoding="utf-8"))
    lines=json.loads((OUT/"line_composition_qa.json").read_text(encoding="utf-8"))
    assert qa["status"]=="PASS"
    assert lines["status"]=="PASS"
    assert [x["width"] for x in lines["widths"]]==[320,360,375,390,430,768,1024,1280,1440]
    assert lines["orphan_character_count"]==0
    assert all(x["known_regressions_absent"] for x in lines["widths"])
    html=(OUT/"reproduction/index.html").read_text(encoding="utf-8")
    assert "DETAIL → RELATIONSHIP" not in html
    assert all(f"assets/photography/nagi_no_mirai/{x}" in html for x in ("hero_treatment_space.png","school_learning_context.png","healing_consultation_context.png"))
    assert all((OUT/"assets/photography/nagi_no_mirai"/x).exists() for x in ("hero_treatment_space.png","school_learning_context.png","healing_consultation_context.png"))
    assert json.loads((OUT/"final_qa.json").read_text(encoding="utf-8"))["status"].startswith("HOLD")
