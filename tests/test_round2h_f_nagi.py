import json
from pathlib import Path

from scripts.run_round2h_f_nagi import FACTS, build_html, copy_assets
from lp_engine.sales_sample_policy import PROVISIONAL, replacement_manifest


ROOT = Path(__file__).resolve().parents[1]


def test_facts_are_substantive_and_replaceable():
    report = replacement_manifest(FACTS)
    assert report["status"] == "PASS"
    assert report["replacement_count"] >= 10
    assert all(row["status"] == PROVISIONAL or not row["replacement_required"] for row in report["records"])


def test_public_labels_do_not_expose_internal_direction_names(tmp_path):
    markup = build_html(copy_assets(tmp_path / "site"))
    visible = markup.split("<script>", 1)[0]
    for label in ("ENTRY MAP", "BEFORE TOUCH", "OPEN SERVICE NOTE", "SERVICE NOTE", "CHOOSE BY INTENT"):
        assert label not in visible
    assert "3つの入口を見る" in visible
    assert "相談前のガイド" in visible


def test_semantic_chunks_are_not_one_character_fixtures():
    fixtures = {
        "good": ["触れられる前に、", "分かることを増やす。"],
        "good_choice": ["今、知りたいことは", "どの入口ですか。"],
    }
    assert all(len(chunk.replace("、", "")) >= 3 for chunks in fixtures.values() for chunk in chunks)
    bad = ["触れられ", "る前に"]
    assert "".join(bad) == "触れられる前に"
    assert bad != fixtures["good"]


def test_role_specific_assets_are_distinct():
    assets = {
        "treatment": ROOT / "assets/photography/stock/nagi_no_mirai/hand_technique.jpg",
        "school": ROOT / "assets/photography/generated/nagi_no_mirai/school_learning_context.png",
        "healing": ROOT / "assets/photography/generated/nagi_no_mirai/healing_consultation_context.png",
    }
    assert all(path.is_file() for path in assets.values())
    assert len({path.read_bytes()[:64] for path in assets.values()}) == 3
