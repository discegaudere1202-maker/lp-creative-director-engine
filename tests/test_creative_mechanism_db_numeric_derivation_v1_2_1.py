import csv
import json
from pathlib import Path

from scripts.validate_creative_mechanism_architecture import validate


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "creative_mechanism_db_architecture_v1_2_1.json"
MATRIX_PATH = ROOT / "data" / "creative_mechanism_phase1_2_pilot_coverage_matrix.csv"


def config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_v1_2_1_architecture_is_valid():
    assert validate(config()) == []


def test_rubric_is_normalized_to_100_and_motion_is_optional():
    data = config()
    dimensions = data["scoring"]["dimensions"]
    assert [dimensions[name]["target_max"] for name in ("design", "conversion_architecture", "motion", "implementation_feasibility")] == [40, 30, 15, 15]
    assert sum(block["target_max"] for block in dimensions.values()) == 100
    assert sum(data["retrieval"]["weights"].values()) == 1.0
    assert data["scoring"]["global_promotion_gate_removed"] is True
    assert data["scoring"]["dimension_applicability"]["allowed_values"] == ["REQUIRED", "OPTIONAL", "NOT_APPLICABLE"]
    assert set(data["scoring"]["dimension_applicability"]["observation_state"]["allowed_values"]) == {"OBSERVED", "MISSING", "NOT_OBSERVED", "NOT_APPLICABLE"}
    assert data["promotion_rules_by_pool_type"]["CONVERSION_INDUSTRY"]["motion_rule"]["default_applicability"] == "OPTIONAL"


def test_static_motion_na_can_remain_strong_candidate():
    data = config()
    for rule in data["promotion_rules_by_pool_type"].values():
        assert "motion" not in rule["required_category_thresholds"]
        assert rule["motion_rule"]["default_applicability"] == "OPTIONAL"
        assert not any("motion" in dimension for dimension in rule["hard_gate_dimensions"])


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
        assert axis["numeric_derivation_policy"] == "PROFILE_AXIS_NUMERIC_V2"
    numeric = data["creative_profile"]["numeric_derivation_policy"]
    assert numeric["allowed_values"] == ["UNKNOWN", 0, 0.25, 0.5, 0.75, 1.0]
    assert numeric["policy_id"] == "PROFILE_AXIS_NUMERIC_V2"
    assert "axis_signal_value" in numeric["evidence_item_required_fields"]
    assert numeric["evidence_weight_formula"] == "evidence_weight = relevance * directness * confidence"
    assert numeric["axis_score_raw_formula"] == "axis_score_raw = SUM(axis_signal_value * evidence_weight) / SUM(evidence_weight)"
    assert {"axis_score_raw", "axis_score", "conflict_flag", "conflict_resolved", "confidence"}.issubset(numeric["axis_output_fields"])
    assert "conflict_rule" in numeric
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
    risk_cells = {(row["business_archetype"], row["industry"]) for row in rows}
    assert {("PROFESSIONAL_ADVICE", "FINANCE_INSURANCE"), ("MEDICAL_WELLNESS", "MEDICAL_DENTAL_CLINIC"), ("BEAUTY_PERSONAL", "BEAUTY_SALON_BODYCARE"), ("PUBLIC_SOCIAL", "PUBLIC_NONPROFIT")}.issubset(risk_cells)


def test_archetype_sampling_allocation_is_machine_readable_and_totals_match():
    data = config()
    rows = data["archetype_sampling_allocation"]
    assert len(rows) == 16
    assert {row["archetype_id"] for row in rows} == set(data["business_archetypes"])
    assert sum(row["discovery_target"] for row in rows) == 2100
    assert sum(row["strong_target"] for row in rows) == 900
    assert sum(row["deep_target"] for row in rows) == 480
    for row in rows:
        assert row["lower_bound"] <= row["discovery_target"] <= row["upper_bound"]
        assert row["saturation_stop_rule"]


def test_pool_specific_promotion_rules_do_not_apply_conversion_to_creative_benchmark():
    data = config()
    conversion = data["promotion_rules_by_pool_type"]["CONVERSION_INDUSTRY"]
    creative = data["promotion_rules_by_pool_type"]["CREATIVE_BENCHMARK"]
    assert conversion["conversion_architecture_is_required"] is True
    assert creative["conversion_architecture_is_required"] is False
    assert creative["optional_category_thresholds"]["conversion_architecture"] is None
    assert creative["motion_rule"]["motion_threshold_applies_only_when"] == "reference_is_promoted_as_motion_mechanism_evidence"


def test_evidence_archive_preflight_is_concrete_and_collection_is_not_started():
    data = config()
    storage = data["storage_policy"]
    for field in ("storage_backend", "retention", "archive_uri_format", "expiration_policy", "re_capture_policy"):
        assert storage[field]
    assert "s3://" in storage["archive_uri_format"]
    assert data["phase2_gate"]["collection_started"] is False


def derive_axis_score(items):
    """Reference implementation of PROFILE_AXIS_NUMERIC_V2 for deterministic unit tests."""
    weighted = [(item["axis_signal_value"], item["relevance"] * item["directness"] * item["confidence"]) for item in items]
    denominator = sum(weight for _, weight in weighted)
    if denominator == 0:
        return "UNKNOWN", False, "UNKNOWN"
    raw = sum(signal * weight for signal, weight in weighted) / denominator
    allowed = [0, 0.25, 0.5, 0.75, 1.0]
    distances = [(abs(value - raw), value) for value in allowed]
    minimum_distance = min(distance for distance, _ in distances)
    # On an exact midpoint, choose the lower allowed value.
    score = min(value for distance, value in distances if distance == minimum_distance)
    conflict = any(signal <= 0.25 and weight >= 0.25 for signal, weight in weighted) and any(signal >= 0.75 and weight >= 0.25 for signal, weight in weighted)
    return score, conflict, "LOW" if conflict else "HIGH"


def test_axis_signal_quality_is_separate_and_deterministic():
    data = config()
    policy = data["creative_profile"]["numeric_derivation_policy"]
    assert "axis_signal_value" in policy["evidence_item_required_fields"]
    assert {"relevance", "directness", "confidence"}.issubset(policy["evidence_item_required_fields"])
    assert policy["axis_signal_value_definition"] != policy["evidence_quality_field_definition"]
    assert len(policy["signal_mappings"]) == 16
    for mapping in policy["signal_mappings"]:
        assert set(mapping) >= {"axis", "positive", "neutral", "negative"}
        assert mapping["positive"][0]["axis_signal_value"] >= 0.75
        assert mapping["neutral"][0]["axis_signal_value"] == 0.5
        assert mapping["negative"][0]["axis_signal_value"] <= 0.25


def test_premium_case_a_high_price_limited_premium_positioning_scores_high():
    items = [
        {"axis_signal_value":1.0,"relevance":1.0,"directness":1.0,"confidence":1.0},
        {"axis_signal_value":1.0,"relevance":1.0,"directness":1.0,"confidence":1.0},
        {"axis_signal_value":1.0,"relevance":1.0,"directness":1.0,"confidence":0.9},
    ]
    assert derive_axis_score(items) == (1.0, False, "HIGH")


def test_premium_case_b_low_price_mass_positioning_scores_low():
    items = [
        {"axis_signal_value":0.0,"relevance":1.0,"directness":1.0,"confidence":1.0},
        {"axis_signal_value":0.0,"relevance":1.0,"directness":1.0,"confidence":1.0},
    ]
    assert derive_axis_score(items) == (0, False, "HIGH")


def test_premium_case_c_premium_positioning_mass_price_is_midpoint_conflict_low_confidence():
    items = [
        {"axis_signal_value":1.0,"relevance":1.0,"directness":1.0,"confidence":1.0},
        {"axis_signal_value":0.0,"relevance":1.0,"directness":1.0,"confidence":1.0},
    ]
    assert derive_axis_score(items) == (0.5, True, "LOW")


def test_high_quality_negative_evidence_lowers_axis_and_no_evidence_is_unknown():
    negative = [{"axis_signal_value":0.0,"relevance":1.0,"directness":1.0,"confidence":1.0}]
    assert derive_axis_score(negative)[0] == 0
    assert derive_axis_score([])[0] == "UNKNOWN"
    assert derive_axis_score([{"axis_signal_value":0.0,"relevance":0.0,"directness":1.0,"confidence":1.0}])[0] == "UNKNOWN"
