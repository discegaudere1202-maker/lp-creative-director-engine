from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.evidence_safety import evaluate_evidence_selection


def main() -> int:
    target_path = ROOT / "config/evidence_safety_dry_run_targets_v1.json"
    output_path = ROOT / "data/evidence_safety_dry_run_v1.json"
    payload = json.loads(target_path.read_text(encoding="utf-8"))
    results = []
    for target in payload["targets"]:
        decision = evaluate_evidence_selection(
            target["conversion_goal"],
            target["primary_objections"],
            target["ledger"],
            requested_claims=target.get("requested_claims", []),
            require_production_clearance=False,
        )
        results.append({
            "case_id": target["case_id"],
            "company_id": target["company_id"],
            "conversion_goal": target["conversion_goal"],
            "primary_objections": target["primary_objections"],
            "decision": decision.to_dict(),
            "research_note": "Programmatic safety dry run; not a live conversion or causal experiment.",
        })
    output = {
        "schema_version": 1,
        "run_id": payload["run_id"],
        "research_only": True,
        "cases": results,
        "summary": {
            "case_count": len(results),
            "all_have_decisions": all("decision" in item for item in results),
            "customer_facing_approved_blocked_claims": sum(
                len(item["decision"]["blocked_claims"]) for item in results
            ),
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], ensure_ascii=False))
    for item in results:
        decision = item["decision"]
        print(item["case_id"], decision["safety_status"], len(decision["eligible_evidence"]), len(decision["hearing_required"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
