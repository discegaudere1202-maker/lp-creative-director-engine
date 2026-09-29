from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "creative_mechanism_db_architecture_v1.json"


def validate(data: dict) -> list[str]:
    issues: list[str] = []
    required = {
        "schema_version", "entity_types", "archetypes", "industry_taxonomy",
        "creative_authority_taxonomy", "mechanism_categories", "mechanism_field_order",
        "seed_mechanisms", "compatibility_relations", "compatibility_seed_edges",
        "scoring", "creative_profile_axes", "retrieval_weights", "retrieval_hard_gates",
        "source_mix_limits", "sampling_totals", "phase2_passes",
    }
    issues.extend(f"missing top-level field: {key}" for key in sorted(required - data.keys()))

    archetypes = data.get("archetypes", [])
    for field in ("universe", "strong", "deep"):
        total = sum(int(row.get(field, 0)) for row in archetypes)
        expected = data.get("sampling_totals", {}).get(
            {"universe": "reference_universe", "strong": "strong_corpus", "deep": "deep_annotation"}[field]
        )
        if total != expected:
            issues.append(f"{field} allocation total {total} != expected {expected}")

    limits = data.get("source_mix_limits", {})
    if round(sum(limits.values()), 5) != 1:
        issues.append("source_mix_limits must sum to 1.0")

    ids = [row.get("mechanism_id") for row in data.get("seed_mechanisms", [])]
    if len(ids) != len(set(ids)):
        issues.append("duplicate seed mechanism IDs")
    valid_categories = {row.get("id") for row in data.get("mechanism_categories", [])}
    for row in data.get("seed_mechanisms", []):
        if row.get("category") not in valid_categories:
            issues.append(f"unknown mechanism category: {row.get('category')}")
        for field in ("mechanism_id", "mechanism_name", "purpose", "marketing_job", "confidence", "evidence_requirement"):
            if not row.get(field):
                issues.append(f"{row.get('mechanism_id')}: missing {field}")

    weight_total = round(sum(data.get("retrieval_weights", {}).values()), 5)
    if weight_total != 1:
        issues.append(f"retrieval weights sum to {weight_total}, expected 1.0")

    for edge in data.get("compatibility_seed_edges", []):
        if edge.get("relation") not in data.get("compatibility_relations", []):
            issues.append(f"invalid compatibility relation: {edge.get('relation')}")
        for field in ("source", "target", "relation", "role_rule", "reason"):
            if not edge.get(field):
                issues.append(f"compatibility edge missing {field}")
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
    print(f"seed_mechanisms={len(data['seed_mechanisms'])}")
    print(f"archetypes={len(data['archetypes'])}")
    print(f"reference_universe={data['sampling_totals']['reference_universe']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
