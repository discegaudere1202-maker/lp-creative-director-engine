from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "creative_mechanism_db_architecture_v1_1.json"
PILOT_MATRIX = ROOT / "data" / "creative_mechanism_phase1_1_pilot_coverage_matrix.csv"


def validate(data: dict) -> list[str]:
    issues: list[str] = []
    required = {
        "schema_version", "business_archetypes", "reference_pool_types", "industry_taxonomy",
        "evidence_authority_taxonomy", "expression_driver_taxonomy", "mechanism_categories",
        "mechanism_record_required_fields", "mechanism_promotion_policy", "scoring", "retrieval",
        "source_model", "conversion_architecture_policy", "observed_performance_evidence_schema",
        "creative_profile", "evidence_grade", "evidence_snapshot_schema", "storage_policy",
        "pilot_coverage_matrix", "phase2_gate",
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
        for field in ("axis", "evidence_candidates", "derivation_rule", "confidence_rule", "unknown_policy"):
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
