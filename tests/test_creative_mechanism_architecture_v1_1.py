import csv
import json
from pathlib import Path

from scripts.validate_creative_mechanism_architecture import validate


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "creative_mechanism_db_architecture_v1_1.json"
MATRIX_PATH = ROOT / "data" / "creative_mechanism_phase1_1_pilot_coverage_matrix.csv"


def config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_v1_1_architecture_is_valid():
    assert validate(config()) == []


def test_rubric_is_normalized_to_100():
    data = config()
    dimensions = data["scoring"]["dimensions"]
    assert [dimensions[name]["target_max"] for name in ("design", "conversion_architecture", "motion", "implementation_feasibility")] == [40, 30, 15, 15]
    assert sum(block["target_max"] for block in dimensions.values()) == 100
    assert sum(data["retrieval"]["weights"].values()) == 1.0


def test_creative_pool_is_not_an_archetype_and_not_auto_strong():
    data = config()
    assert "CREATIVE_BENCHMARK" not in data["business_archetypes"]
    pool = next(row for row in data["reference_pool_types"] if row["pool_type"] == "CREATIVE_BENCHMARK")
    assert pool["discovery_candidate_target"] == 500
    assert pool["strong_target"] == 300
    assert pool["deep_target"] == 120
    assert pool["strong_target"] < pool["discovery_candidate_target"]


def test_source_roles_profile_derivation_independence_and_snapshot_are_present():
    data = config()
    source_model = data["source_model"]
    assert source_model["discovery_source_class"]
    assert source_model["evidence_source_roles"]
    assert source_model["source_mix_applies_to"] == "DISCOVERY_BIAS_ONLY"
    assert len(data["creative_profile"]["axes"]) == 16
    for axis in data["creative_profile"]["axes"]:
        assert axis["derivation_rule"]
        assert axis["unknown_policy"]
    required = data["mechanism_record_required_fields"]
    assert {"unique_lp_count", "unique_brand_count", "unique_agency_count", "unique_campaign_count"}.issubset(required)
    assert data["evidence_grade"]["allowed_values"] == ["E0", "E1", "E2", "E3", "E4"]
    assert set(data["evidence_snapshot_schema"]["required_fields"]) >= {"captured_at", "viewport", "original_url", "evidence_locator", "screenshot_identifier", "content_hash"}


def test_pilot_matrix_has_100_planned_records():
    with MATRIX_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert sum(int(row["planned_count"]) for row in rows) == 100
    assert {"JP", "GLOBAL"}.issubset({row["market_scope"] for row in rows})
    assert {"CONVERSION_INDUSTRY", "CREATIVE_BENCHMARK"}.issubset({row["pool_type"] for row in rows})
