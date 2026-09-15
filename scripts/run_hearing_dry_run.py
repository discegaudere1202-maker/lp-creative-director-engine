"""Generate the five-case Hearing planner dry-run package.

This is a research/test fixture. It describes missing fields from the existing
Safety dry-run and does not create customer-facing copy or production claims.
"""

from __future__ import annotations

import json
from pathlib import Path

from lp_engine.hearing import plan_hearing


CASES = {
    "P02": {
        "domain": "社労士・相談",
        "conversion_goal": "consultation",
        "primary_objections": ["O7_RISK", "O4_NEXT"],
        "missing": [("O7_RISK", ["RISK_POLICY"]), ("O4_NEXT", ["POST_CLICK_FLOW"])],
        "blocked": [{"claim_id": "NO_PRESSURE", "required_evidence_types": ["RISK_POLICY"]}],
    },
    "P09": {
        "domain": "看板・見積",
        "conversion_goal": "quote_request",
        "primary_objections": ["O6_COST", "O4_NEXT"],
        "missing": [("O6_COST", ["FEE_CONDITION"]), ("O4_NEXT", ["POST_CLICK_FLOW"])],
        "blocked": [{"claim_id": "FULLY_FREE", "required_evidence_types": ["PRICE", "FEE_CONDITION"]}],
    },
    "P10": {
        "domain": "キャリア相談・伴走",
        "conversion_goal": "consultation",
        "primary_objections": ["O7_RISK", "O8_CONTINUITY"],
        "missing": [("O7_RISK", ["RISK_POLICY"]), ("O8_CONTINUITY", ["CONTINUITY_POLICY"])],
        "blocked": [{"claim_id": "NO_OBLIGATION", "required_evidence_types": ["DECISION_BOUNDARY", "RISK_POLICY"]}],
    },
    "MORIBITO": {
        "domain": "店舗サービス",
        "conversion_goal": "visit",
        "primary_objections": ["O2_ACCOUNTABILITY", "O3_PROCESS"],
        "missing": [("O2_ACCOUNTABILITY", ["ACCOUNTABILITY_SCOPE"]), ("O3_PROCESS", ["SERVICE_PROCESS"])],
        "blocked": [],
    },
    "INDEPENDENT_KOKORO_SEITAI": {
        "domain": "整体・予約",
        "conversion_goal": "reservation",
        "primary_objections": ["O2_ACCOUNTABILITY", "O4_NEXT"],
        "missing": [("O2_ACCOUNTABILITY", ["OWNER_IDENTITY"]), ("O4_NEXT", ["POST_CLICK_FLOW"])],
        "blocked": [],
    },
}


def safety_gap(spec: dict) -> dict:
    return {
        "conversion_goal": spec["conversion_goal"],
        "primary_objections": spec["primary_objections"],
        "missing_evidence": [
            {"target_objection": objection, "preferred_evidence_types": types, "status": "MISSING"}
            for objection, types in spec["missing"]
        ],
        "blocked_claims": spec["blocked"],
        "hearing_required": [
            {"target_objection": objection, "missing_evidence_type": types, "status": "HEARING_REQUIRED"}
            for objection, types in spec["missing"]
        ],
        "eligible_evidence": [],
    }


def main() -> None:
    payload = {
        "schema": "hearing_requirements_schema_v2",
        "status": "RESEARCH_DRY_RUN_NOT_PRODUCTION_OUTPUT",
        "cases": {},
    }
    for case_id, spec in CASES.items():
        plan = plan_hearing(
            safety_gap(spec),
            conversion_goal=spec["conversion_goal"],
            primary_objections=spec["primary_objections"],
            domain=spec["domain"],
        )
        payload["cases"][case_id] = {
            "conversion_goal": spec["conversion_goal"],
            "domain": spec["domain"],
            "primary_objections": spec["primary_objections"],
            "missing_evidence_count": len(spec["missing"]),
            "plan": plan.to_dict(),
            "resulting_evidence_candidates": [],
            "notes": "Synthetic dry-run fixture; no customer answer or Production claim is created.",
        }
    output = Path(__file__).resolve().parents[1] / "data" / "hearing_dry_run_v1.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
