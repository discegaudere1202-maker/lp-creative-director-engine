from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "creative_mechanism_db_architecture_v1_2.json"
PILOT_MATRIX = ROOT / "data" / "creative_mechanism_phase1_2_pilot_coverage_matrix.csv"


def validate_v1_1_compat(data: dict) -> list[str]:
    """Keep the historical v1.1 validator path usable for preserved fixtures."""
    issues: list[str] = []
    required = {"business_archetypes", "reference_pool_types", "scoring", "retrieval", "source_model", "creative_profile", "evidence_grade", "evidence_snapshot_schema", "pilot_coverage_matrix"}
    issues.extend(f"missing historical v1.1 field: {key}" for key in sorted(required - data.keys()))
    if "CREATIVE_BENCHMARK" in data.get("business_archetypes", []):
        issues.append("CREATIVE_BENCHMARK must not be a business archetype")
    totals = data.get("sampling_totals", {})
    if totals.get("reference_universe_discovery_candidates") != 2600 or totals.get("strong_corpus") != 1200 or totals.get("deep_annotation") != 600:
        issues.append("historical v1.1 sampling totals mismatch")
    expected_targets = {"design":40,"conversion_architecture":30,"motion":15,"implementation_feasibility":15}
    for name, target in expected_targets.items():
        block = data.get("scoring", {}).get("dimensions", {}).get(name, {})
        if sum(block.get("weights", {}).values()) != target or block.get("target_max") != target:
            issues.append(f"historical v1.1 rubric mismatch: {name}")
    if round(sum(data.get("retrieval", {}).get("weights", {}).values()), 5) != 1:
        issues.append("historical v1.1 retrieval weights mismatch")
    if len(data.get("creative_profile", {}).get("axes", [])) != 16:
        issues.append("historical v1.1 profile axis count mismatch")
    if data.get("evidence_grade", {}).get("allowed_values") != ["E0","E1","E2","E3","E4"]:
        issues.append("historical v1.1 evidence grades mismatch")
    if data.get("pilot_coverage_matrix", {}).get("planned_records") != 100:
        issues.append("historical v1.1 pilot count mismatch")
    return issues


def validate(data: dict) -> list[str]:
    if data.get("schema_version") == "1.1.0":
        return validate_v1_1_compat(data)
    issues: list[str] = []
    required = {
        "schema_version", "business_archetypes", "reference_pool_types", "industry_taxonomy",
        "evidence_authority_taxonomy", "expression_driver_taxonomy", "mechanism_categories",
        "mechanism_record_required_fields", "mechanism_promotion_policy", "scoring", "retrieval",
        "source_model", "conversion_architecture_policy", "observed_performance_evidence_schema",
        "creative_profile", "evidence_grade", "evidence_snapshot_schema", "storage_policy",
        "pilot_coverage_matrix", "phase2_gate", "archetype_sampling_allocation",
        "promotion_rules_by_pool_type",
    }
    issues.extend(f"missing top-level field: {key}" for key in sorted(required - data.keys()))

    pools = {row.get("pool_type"): row for row in data.get("reference_pool_types", [])}
    if "CONVERSION_INDUSTRY" not in pools or "CREATIVE_BENCHMARK" not in pools:
        issues.append("CONVERSION_INDUSTRY and CREATIVE_BENCHMARK pool types are required")
    if "CREATIVE_BENCHMARK" in data.get("business_archetypes", []):
        issues.append("CREATIVE_BENCHMARK must not be a business archetype")
    for pool_id, pool in pools.items():
        if int(pool.get("strong_target", 0)) >= int(pool.get("discovery_candidate_target", 0)):
            issues.append(f"{pool_id}: strong must be less than discovery candidates")
    totals = data.get("sampling_totals", {})
    if totals.get("reference_universe_discovery_candidates") != 2600:
        issues.append("reference universe discovery candidates must be 2600")
    if totals.get("strong_corpus") != 1200 or totals.get("deep_annotation") != 600:
        issues.append("strong/deep totals must be 1200/600")

    allocation = data.get("archetype_sampling_allocation", [])
    if len(allocation) != 16:
        issues.append(f"archetype allocation must contain 16 rows, found {len(allocation)}")
    if {row.get("archetype_id") for row in allocation} != set(data.get("business_archetypes", [])):
        issues.append("archetype allocation IDs must exactly match business archetypes")
    allocation_totals = {field: sum(int(row.get(field, 0)) for row in allocation) for field in ("discovery_target", "strong_target", "deep_target")}
    if allocation_totals != {"discovery_target":2100, "strong_target":900, "deep_target":480}:
        issues.append(f"archetype allocation totals mismatch: {allocation_totals}")
    for row in allocation:
        for field in ("archetype_id", "discovery_target", "strong_target", "deep_target", "lower_bound", "upper_bound", "rationale", "saturation_stop_rule"):
            if field not in row or row[field] in (None, ""):
                issues.append(f"archetype allocation missing {field}: {row.get('archetype_id')}")
        if row.get("lower_bound", 0) > row.get("discovery_target", 0) or row.get("upper_bound", 0) < row.get("discovery_target", 0):
            issues.append(f"archetype bounds do not contain target: {row.get('archetype_id')}")

    rubric = data.get("scoring", {})
    dimensions = rubric.get("dimensions", {})
    expected_targets = {"design":40,"conversion_architecture":30,"motion":15,"implementation_feasibility":15}
    for name, target in expected_targets.items():
        block = dimensions.get(name, {})
        weight_sum = sum(block.get("weights", {}).values())
        if weight_sum != target or block.get("target_max") != target:
            issues.append(f"rubric {name} weights/target mismatch: {weight_sum}/{block.get('target_max')} != {target}")
    if sum(expected_targets.values()) != 100:
        issues.append("rubric category totals must equal 100")
    if rubric.get("score_direction") != "HIGHER_IS_BETTER":
        issues.append("all rubric scores must use HIGHER_IS_BETTER direction")
    if "strong_threshold" in rubric or rubric.get("global_promotion_gate_removed") is not True:
        issues.append("v1.2 must remove the global Strong threshold gate")
    applicability = rubric.get("dimension_applicability", {})
    if applicability.get("allowed_values") != ["REQUIRED", "OPTIONAL", "NOT_APPLICABLE"]:
        issues.append("dimension applicability values are not locked")
    if set(applicability.get("observation_state", {}).get("allowed_values", [])) != {"OBSERVED", "MISSING", "NOT_OBSERVED", "NOT_APPLICABLE"}:
        issues.append("observation states must distinguish OBSERVED/MISSING/NOT_OBSERVED/NOT_APPLICABLE")
    if "motion" not in applicability.get("motion_policy", "").lower():
        issues.append("motion optionality policy is missing")

    weight_total = round(sum(data.get("retrieval", {}).get("weights", {}).values()), 5)
    if weight_total != 1:
        issues.append(f"retrieval weights sum to {weight_total}, expected 1.0")
    required_pipeline = [
        "ELIGIBILITY_EVIDENCE_HARD_GATE",
        "MECHANISM_CANDIDATE_SCORING",
        "COMPATIBILITY_SOLVER",
        "RECIPE_ASSEMBLY",
        "DIVERSITY_NOVELTY_RERANKING",
        "FINAL_THREE_RECIPE_OUTPUT",
    ]
    if data.get("retrieval", {}).get("pipeline_order") != required_pipeline:
        issues.append("retrieval pipeline order is not locked")
    novelty = data.get("retrieval", {}).get("novelty_policy", {})
    if novelty.get("cannot_override_hard_gate") is not True or novelty.get("cannot_override_evidence_safety") is not True:
        issues.append("novelty must not override hard gates or evidence safety")

    promotion = data.get("promotion_rules_by_pool_type", {})
    if set(promotion) != {"CONVERSION_INDUSTRY", "CREATIVE_BENCHMARK"}:
        issues.append("pool-specific promotion rules must exist for both pools")
    conversion_rule = promotion.get("CONVERSION_INDUSTRY", {})
    creative_rule = promotion.get("CREATIVE_BENCHMARK", {})
    if conversion_rule.get("conversion_architecture_is_required") is not True:
        issues.append("CONVERSION_INDUSTRY must require Conversion Architecture")
    if creative_rule.get("conversion_architecture_is_required") is not False:
        issues.append("CREATIVE_BENCHMARK must not require Conversion Architecture")
    for rule_id, rule in promotion.items():
        motion_rule = rule.get("motion_rule", {})
        if motion_rule.get("default_applicability") != "OPTIONAL":
            issues.append(f"{rule_id} motion must default to OPTIONAL")
        if motion_rule.get("motion_threshold_applies_only_when") != "reference_is_promoted_as_motion_mechanism_evidence":
            issues.append(f"{rule_id} motion threshold must be conditional")
        if not rule.get("hard_gate_dimensions"):
            issues.append(f"{rule_id} must explicitly list hard-gate dimensions")

    source_model = data.get("source_model", {})
    discovery_mix = source_model.get("discovery_source_mix_targets", {})
    if round(sum(discovery_mix.values()), 5) != 1:
        issues.append("discovery source mix targets must sum to 1.0")
    if not source_model.get("discovery_source_class") or not source_model.get("evidence_source_roles"):
        issues.append("discovery sources and evidence roles must both be defined")
    if source_model.get("source_mix_applies_to") != "DISCOVERY_BIAS_ONLY":
        issues.append("source mix must be explicitly limited to discovery bias")
    if source_model.get("strong_evidence_requirement", {}).get("official_or_original_evidence_required") is not True:
        issues.append("strong promotion must require original or official evidence")

    if data.get("conversion_architecture_policy", {}).get("display_name") != "Conversion Architecture Quality":
        issues.append("conversion category must be named Conversion Architecture Quality")
    if "observed_performance_evidence" not in data.get("entity_types", []):
        issues.append("observed_performance_evidence entity is required")

    profile = data.get("creative_profile", {})
    axes = profile.get("axes", [])
    for axis in axes:
        for field in ("axis", "evidence_candidates", "derivation_rule", "confidence_rule", "unknown_policy", "numeric_derivation_policy"):
            if not axis.get(field):
                issues.append(f"creative profile axis missing {field}: {axis.get('axis')}")
    if len(axes) != 16:
        issues.append(f"creative profile must have 16 axes, found {len(axes)}")

    independence = data.get("mechanism_promotion_policy", {})
    for stage in ("candidate_to_supported", "supported_to_canonical"):
        block = independence.get(stage, {})
        for field in ("independent_lp_min", "unique_brand_min", "unique_agency_min", "unique_campaign_min"):
            if field not in block:
                issues.append(f"mechanism independence missing {stage}.{field}")
    for field in ("unique_lp_count", "unique_brand_count", "unique_agency_count", "unique_campaign_count"):
        if field not in data.get("mechanism_record_required_fields", []):
            issues.append(f"mechanism schema missing {field}")

    grades = data.get("evidence_grade", {})
    if grades.get("allowed_values") != ["E0","E1","E2","E3","E4"]:
        issues.append("evidence grades must be exactly E0-E4")
    if any(alias.startswith("M") for alias in grades.get("forbidden_aliases", [])) is not True:
        issues.append("M-series evidence aliases must be explicitly forbidden")
    for field in ("captured_at", "viewport", "original_url", "evidence_locator", "screenshot_identifier", "content_hash"):
        if field not in data.get("evidence_snapshot_schema", {}).get("required_fields", []):
            issues.append(f"snapshot schema missing {field}")
    if data.get("pilot_coverage_matrix", {}).get("planned_records") != 100:
        issues.append("pilot coverage plan must contain 100 records")
    if data.get("pilot_coverage_matrix", {}).get("collection_started") is not False:
        issues.append("phase 2 collection_started must be false")

    storage = data.get("storage_policy", {})
    for field in ("storage_backend", "retention", "archive_uri_format", "expiration_policy", "re_capture_policy"):
        if not storage.get(field):
            issues.append(f"evidence archive policy missing {field}")
    if "S3" not in storage.get("storage_backend", "") and "s3" not in storage.get("archive_uri_format", ""):
        issues.append("evidence archive backend/URI must be concrete")

    phase2_gate = data.get("phase2_gate", {})
    if phase2_gate.get("collection_started") is not False:
        issues.append("phase2_gate.collection_started must be false")
    try:
        with PILOT_MATRIX.open(newline="", encoding="utf-8") as handle:
            pilot_rows = list(csv.DictReader(handle))
        pilot_total = sum(int(row["planned_count"]) for row in pilot_rows)
        if pilot_total != 100:
            issues.append(f"pilot CSV planned count must be 100, found {pilot_total}")
        required_risk_cells = {
            ("PROFESSIONAL_ADVICE", "FINANCE_INSURANCE"),
            ("MEDICAL_WELLNESS", "MEDICAL_DENTAL_CLINIC"),
            ("BEAUTY_PERSONAL", "BEAUTY_SALON_BODYCARE"),
            ("PUBLIC_SOCIAL", "PUBLIC_NONPROFIT"),
        }
        observed_risk_cells = {(row.get("business_archetype"), row.get("industry")) for row in pilot_rows}
        missing_risk_cells = required_risk_cells - observed_risk_cells
        if missing_risk_cells:
            issues.append(f"pilot risk cells missing: {sorted(missing_risk_cells)}")
    except Exception as exc:
        issues.append(f"pilot coverage matrix read error: {exc}")
    return issues


def main() -> int:
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover
        print(f"CONFIG_READ_ERROR: {exc}")
        return 1
    issues = validate(data)
    if issues:
        print("FAIL")
        print("\n".join(f"- {issue}" for issue in issues))
        return 1
    print("PASS: Creative Mechanism DB Phase 1 architecture is internally consistent")
    print(f"business_archetypes={len(data['business_archetypes'])}")
    print(f"reference_universe={data['sampling_totals']['reference_universe_discovery_candidates']}")
    print(f"strong_corpus={data['sampling_totals']['strong_corpus']}")
    print(f"deep_annotation={data['sampling_totals']['deep_annotation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
