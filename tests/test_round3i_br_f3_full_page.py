import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"artifacts/round3i_br_f3"
def test_all_major_headings_have_nine_width_coverage():
    qa=json.loads((OUT/"browser_qa.json").read_text(encoding="utf-8")); line=json.loads((OUT/"line_composition_qa.json").read_text(encoding="utf-8"))
    assert qa["status"]=="PASS" and qa["total"]==9
    assert line["status"]=="PASS" and line["coverage"]=="all_major_customer_facing_headings"
    assert [x["width"] for x in line["widths"]]==[320,360,375,390,430,768,1024,1280,1440]
    assert line["orphan_line_count"]==0 and line["known_regression_late"]==0 and line["known_regression_ending"]==0
def test_media_surface_boundary_and_hold_status():
    asset=json.loads((OUT/"asset_manifest.json").read_text(encoding="utf-8")); boundary=json.loads((OUT/"evidence_boundary.json").read_text(encoding="utf-8")); final=json.loads((OUT/"final_qa.json").read_text(encoding="utf-8"))
    assert len(asset["assets"])==3 and all(x["rights_status"]=="PROJECT_OWNED_GENERATED" for x in asset["assets"])
    assert boundary["status"]=="PASS" and boundary["surface_disclosure"]
    assert final["status"].startswith("HOLD") and final["judgment_ready"]=="YES"
