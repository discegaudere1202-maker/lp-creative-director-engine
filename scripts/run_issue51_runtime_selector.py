"""Build the deterministic Issue #51 selector regression artifact."""
from __future__ import annotations

import json
from pathlib import Path

from lp_engine.production_architecture import FIT_DIMENSIONS, infer_creative_family

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts" / "issue49_riko"
OUT = ROOT / "artifacts" / "issue51_runtime_selector"


def main() -> int:
    labels = json.loads((SOURCE / "creative_fit_expected_labels.json").read_text(encoding="utf-8"))["records"]
    companies = json.loads((SOURCE / "validation_company_registry.json").read_text(encoding="utf-8"))["companies"]
    by_id = {row["case_id"]: row for row in companies}
    results = []
    for expected in labels:
        company = by_id[expected["case_id"]]
        fit = {
            "schema_version": "creative_fit_profile_v1",
            "profile_id": f"artifact-{expected['case_id']}",
            "dimensions": dict(zip(FIT_DIMENSIONS, expected["scores"])),
            "source_refs": ["issue49:creative_fit_expected_labels"],
        }
        result = infer_creative_family(
            company_truth={"verified": True, "company": company["company"], "facts": company["company_intelligence"]},
            customer_decision_state=company["customer_decision_state"],
            creative_fit=fit,
        )
        results.append({"case_id": expected["case_id"], "expected": expected["dominant"], "inferred": result["dominant_family"], "status": "PASS" if result["dominant_family"] == expected["dominant"] else "FAIL", "ambiguity_state": result["ambiguity_state"], "human_review_required": result["human_review_required"]})
    distribution = {family: sum(row["inferred"] == family for row in results) for family in [f"BW-F0{i}" for i in range(1, 9)]}
    payload = {"schema_version": "issue51_runtime_selector_artifact_v1", "status": "PASS" if all(row["status"] == "PASS" for row in results) and distribution == {family: 2 for family in distribution} else "FAIL", "source_issue": 49, "source_artifacts": ["creative_fit_expected_labels.json", "collision_ambiguity_report.json", "selector_rule_proposal.json", "rin_facing_selector_contract.json", "feasibility_invariance_checks.json"], "case_count": len(results), "distribution": distribution, "results": results, "layout_id_emitted": False, "feasibility_ignored_at_selection": True, "human_review_boundary": ["unresolved co-dominance", "unknown readiness", "unclear locality relevance", "novel context"]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "selector_validation.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "manifest.json").write_text(json.dumps({"files": ["selector_validation.json"], "source_issue": 49, "status": payload["status"]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
