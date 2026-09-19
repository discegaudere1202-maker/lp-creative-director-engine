import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("round2g_b", ROOT / "scripts" / "run_round2g_b_field_documentary.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_round2g_direction_and_sequence_are_explicit():
    creative = MODULE.build_creative()
    assert creative["direction"] == "FIELD DOCUMENTARY × LIVING-SIDE COPY × DOCUMENTARY CAMERA"
    assert creative["sequence"] == ["OBSERVE", "NOTICE", "WORK", "ABOVE", "SCOPE", "PROOF", "CHOOSE", "BEFORE YOU ASK", "TALK"]
    assert MODULE.CREATIVE_SPEC["palette"]["base"] == "#F3F4F1"
    assert MODULE.CREATIVE_SPEC["palette"]["deep_field"] == "#10191C"


def test_round2g_copy_contract_is_exact_for_required_public_copy():
    copy = MODULE.build_creative()["copy"]
    assert copy["V01"]["headline"] == ["いつもの家に、", "気になるところがある。"]
    assert copy["V01"]["commercial"] == "小山市｜外壁・屋根｜修繕・塗装"
    assert copy["V02"]["headline"] == ["いつもの外壁に、", "変化がある。"]
    assert copy["V04"]["headline"] == ["下から見えない屋根は、", "上から確かめる。"]
    assert copy["V07"]["footnote"] == "画面上の色は実色再現ではありません。"
    assert copy["V09"]["headline"] == ["気になるところから、", "ご相談ください。"]


def test_round2g_media_manifest_has_regenerated_assets():
    media = MODULE.load_media()
    for asset_id in ("A01", "A03", "A04", "A05", "A06", "A09", "A10", "A16"):
        assert media[asset_id]["source_type"] == "generated"
        assert media[asset_id]["evidence_status"] == "EXPLANATORY_PROXY"
        assert Path(ROOT / media[asset_id]["local_asset_path"]).is_file()


def test_round2g_creative_delta_is_7_of_7_and_perceptual_tests_remain_human_reviewable():
    delta = MODULE.delta_report()
    perceptual = MODULE.perceptual_report()
    assert delta["status"] == "PASS"
    assert delta["pass_count"] == 7
    assert perceptual["status"] == "PASS"
    assert perceptual["human_review_required"] is True


def test_round2g_negative_fixtures_fail_closed_against_legacy_presentation():
    report = MODULE.negative_fixtures()
    assert report["status"] == "PASS"
    assert all(item["expected"] == "FAIL" for item in report["fixtures"])


def test_round2g_renderer_does_not_contain_legacy_public_markers():
    creative = MODULE.build_creative()
    media = {key: {"local_asset_path": "assets/placeholder.png"} for key in [f"A{i:02d}" for i in range(1, 17)]}
    html = MODULE.render_html(creative, media)
    assert "塗る前に、" not in html
    assert "evidence-card" not in html
    assert "info-rail" not in html
    assert "roof-path" not in html
    assert "data-round=\"2G-B\"" in html


def test_round2g_starting_head_is_fixed():
    assert MODULE.STARTING_HEAD == "491dfc78509e987fc62eab148b77c2f0bd608aed"
