import json
from pathlib import Path

from scripts.validate_creative_mechanism_architecture import validate


ROOT = Path(__file__).resolve().parents[1]


def load_config():
    return json.loads(
        (ROOT / "config" / "creative_mechanism_db_architecture_v1.json").read_text(
            encoding="utf-8"
        )
    )


def test_phase1_architecture_is_valid():
    assert validate(load_config()) == []


def test_sampling_plan_matches_project_targets():
    data = load_config()
    totals = data["sampling_totals"]
    assert totals["reference_universe"] == 2400
    assert totals["strong_corpus"] == 1200
    assert totals["deep_annotation"] == 600
    assert totals["creative_benchmark"] == 300


def test_mechanisms_are_not_style_templates():
    data = load_config()
    forbidden = ("template", "luxury-template", "pop-template", "natural-template")
    for mechanism in data["seed_mechanisms"]:
        blob = json.dumps(mechanism, ensure_ascii=False).lower()
        assert not any(token in blob for token in forbidden)
        assert mechanism["purpose"]
        assert mechanism["marketing_job"]
