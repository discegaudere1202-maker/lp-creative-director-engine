"""Phase 3 Hearing-to-Finalization completion loop.

The module keeps four responsibilities separate:

* identify evidence gaps that matter to a Production requirement;
* plan the smallest natural Hearing question set;
* turn an answer into an unverified candidate and route it through
  verification/provenance/rights checks; and
* re-run the existing Safety selector before a simulated final regeneration.

It deliberately never turns a customer answer directly into customer-facing
copy.  ``simulation_mode`` is required for synthetic answer packets and all
outputs created from them remain ``TEST_ONLY`` / ``NOT_PRODUCTION_APPROVED``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Mapping, Sequence

from .evidence_safety import evaluate_evidence_selection
from .hearing import (
    FIELD_BY_ID,
    answer_to_evidence_candidate,
    complete_evidence_candidate,
)


QUESTION_PRIORITIES = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
BLOCKING_LEVELS = {"PAGE_BLOCKING", "SECTION_BLOCKING", "CLAIM_BLOCKING"}
VALID_ANSWER_STATES = {
    "UNVERIFIED_CUSTOMER_INPUT",
    "VERIFIED_CUSTOMER_STATEMENT",
    "DOCUMENT_SUPPORTED",
    "PRODUCTION_ELIGIBLE",
    "REJECTED",
    "CONFLICT",
    "HEARING_REQUIRED",
}


def _as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return dict(value) if isinstance(value, Mapping) else {}


def _eligible_types(safety_report: Any, ledger: Iterable[Mapping[str, Any]]) -> set[str]:
    safety = _as_dict(safety_report)
    result = {str(item.get("evidence_type")) for item in safety.get("eligible_evidence", [])}
    for item in ledger:
        if (
            str(item.get("verification_status", "")) == "VERIFIED"
            and str(item.get("source", "")).strip()
            and str(item.get("verification_date", "")).strip()
            and str(item.get("rights_status", "UNKNOWN")) in {"CLEARED", "NOT_APPLICABLE"}
            and str(item.get("usage_status", "")) in {"ELIGIBLE", "PRODUCTION_ELIGIBLE"}
            and not item.get("hearing_required", False)
        ):
            result.add(str(item.get("evidence_type")))
    return result


def analyze_evidence_gaps(
    safety_report: Any,
    requirements: Sequence[Mapping[str, Any]],
    *,
    current_ledger: Iterable[Mapping[str, Any]] = (),
    affected_section_by_field: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Map Production requirements to missing, actionable evidence gaps.

    Requirements are intentionally explicit.  This prevents the analyzer from
    guessing that a vaguely related public fact satisfies a richer finalization
    need (for example, a generic ``SERVICE_PROCESS`` fact satisfying a request
    for a store's delivery conditions).
    """
    safety = _as_dict(safety_report)
    ledger = list(current_ledger)
    eligible_types = _eligible_types(safety, ledger)
    gaps: list[dict[str, Any]] = []
    for requirement in requirements:
        types = [str(x) for x in requirement.get("required_evidence_types", requirement.get("evidence_types", []))]
        if not types:
            continue
        satisfied = bool(set(types) & eligible_types)
        if requirement.get("force_gap", False):
            satisfied = False
        if satisfied:
            continue
        field_id = str(requirement.get("required_field", requirement.get("field_id", "")))
        gaps.append({
            "gap_id": str(requirement.get("gap_id", field_id or types[0])),
            "missing_evidence": types,
            "target_objection": list(requirement.get("target_objections", [])),
            "blocked_claim": requirement.get("blocked_claim", ""),
            "affected_section": str(
                requirement.get("affected_section")
                or (affected_section_by_field or {}).get(field_id, "")
            ),
            "required_field": field_id,
            "verification_class": str(requirement.get("verification_class", "SELF_DECLARABLE")),
            "rights_requirement": str(requirement.get("rights_requirement", "NOT_APPLICABLE")),
            "blocking_level": str(requirement.get("blocking_level", "CLAIM_BLOCKING")),
            "hearing_priority": str(requirement.get("priority", "P1")),
            "question_id": str(requirement.get("question_id", f"Q-{field_id or types[0]}")),
            "requested_asset": requirement.get("requested_asset"),
            "reason": str(requirement.get("reason", "Production finalization needs a verified company fact.")),
        })

    # Preserve Safety's own gaps, but do not duplicate an explicit requirement.
    explicit_keys = {(g["required_field"], tuple(g["missing_evidence"])) for g in gaps}
    explicit_fields = {g["required_field"] for g in gaps if g.get("required_field")}
    for item in safety.get("hearing_required", []):
        field_id = str(item.get("suggested_hearing_field", item.get("missing_field", "")))
        types = [str(x) for x in item.get("missing_evidence_type", [])]
        key = (field_id, tuple(types))
        if key in explicit_keys or field_id in explicit_fields or not field_id:
            continue
        gaps.append({
            "gap_id": f"safety-{field_id}",
            "missing_evidence": types,
            "target_objection": [str(item.get("target_objection", ""))] if item.get("target_objection") else [],
            "blocked_claim": ", ".join(item.get("blocked_claims", [])),
            "affected_section": "",
            "required_field": field_id,
            "verification_class": "SELF_DECLARABLE",
            "rights_requirement": "NOT_APPLICABLE",
            "blocking_level": "CLAIM_BLOCKING",
            "hearing_priority": "P1",
            "question_id": f"Q-{field_id}",
            "requested_asset": None,
            "reason": str(item.get("why_needed", "Safety evidence is missing.")),
        })
    gaps.sort(key=lambda item: (QUESTION_PRIORITIES.get(item["hearing_priority"], 9), item["gap_id"]))
    blocking = [g["gap_id"] for g in gaps if g["blocking_level"] in BLOCKING_LEVELS]
    return {
        "status": "GAPS_FOUND" if gaps else "COMPLETE",
        "missing_evidence": gaps,
        "blocking_gaps": blocking,
        "missing_evidence_count": len(gaps),
        "source": "Production Requirement + Safety Report + Evidence Ledger",
    }


def _question_for_gap(gap: Mapping[str, Any]) -> dict[str, Any]:
    field_id = str(gap.get("required_field", ""))
    field = FIELD_BY_ID.get(field_id)
    question = field.question_template if field else str(gap.get("question_template", "正式版LPに掲載できる内容を確認させてください。"))
    answer_type = field.answer_type if field else str(gap.get("answer_type", "short_text"))
    verification_class = field.verification_class if field else str(gap.get("verification_class", "SELF_DECLARABLE"))
    answer_group = field.answer_group if field else str(gap.get("answer_group", field_id or gap["gap_id"]))
    blocking = str(gap.get("blocking_level", "CLAIM_BLOCKING"))
    priority = str(gap.get("hearing_priority", "P1"))
    info_gain = {"P0": 1.0, "P1": 0.85, "P2": 0.55, "P3": 0.25}.get(priority, 0.25)
    if len(gap.get("missing_evidence", [])) > 1:
        info_gain = min(1.0, info_gain + 0.05)
    return {
        "question_id": str(gap.get("question_id", f"Q-{field_id or gap['gap_id']}")),
        "field_id": field_id,
        "question": question,
        "reason": str(gap.get("reason", "この情報が正式版の判断材料になるためです。")),
        "priority": priority,
        "blocking_level": blocking,
        "answer_type": answer_type,
        "answer_group": answer_group,
        "verification_class": verification_class,
        "verification_requirement": field.verification_requirement if field else "会社の公式情報または確認可能な資料が必要です。",
        "provenance_requirement": field.provenance_requirement if field else "source, source_type and verification_date are required",
        "rights_requirement": str(gap.get("rights_requirement", field.rights_requirement if field else "NOT_APPLICABLE")),
        "target_objections": list(gap.get("target_objection", [])),
        "evidence_target": list(gap.get("missing_evidence", [])),
        "affected_section": str(gap.get("affected_section", "")),
        "requested_asset": gap.get("requested_asset"),
        "question_cost": "IMAGE_UPLOAD" if gap.get("requested_asset") else ("DOCUMENT_UPLOAD" if verification_class in {"DOCUMENT_REQUIRED", "THIRD_PARTY_EVIDENCE_REQUIRED"} else "SHORT_TEXT"),
        "expected_information_gain": round(info_gain, 2),
        "status": "QUESTION_REQUIRED",
    }


def build_hearing_plan(gap_report: Mapping[str, Any]) -> dict[str, Any]:
    """Create a deduplicated, value-ranked question plan from evidence gaps."""
    questions: list[dict[str, Any]] = []
    by_group: dict[str, dict[str, Any]] = {}
    redundant: list[str] = []
    for gap in gap_report.get("missing_evidence", []):
        question = _question_for_gap(gap)
        group = question["answer_group"]
        if group in by_group:
            existing = by_group[group]
            existing["evidence_target"] = list(dict.fromkeys(existing["evidence_target"] + question["evidence_target"]))
            redundant.append(question["field_id"] or question["question_id"])
            continue
        by_group[group] = question
        questions.append(question)
    questions.sort(key=lambda item: (QUESTION_PRIORITIES.get(item["priority"], 9), -item["expected_information_gain"], item["question_id"]))
    blocking = [q["question_id"] for q in questions if q["blocking_level"] in BLOCKING_LEVELS]
    optional = [q["question_id"] for q in questions if q["blocking_level"] == "NON_BLOCKING"]
    return {
        "schema_version": "hearing_completion_plan_v1",
        "status": "PLANNED" if questions else "NO_HEARING_REQUIRED",
        "minimum_question_set": questions,
        "required_hearing_fields": [q["field_id"] for q in questions if q["field_id"]],
        "blocking_questions": blocking,
        "optional_questions": optional,
        "redundant_questions": redundant,
        "question_count": len(questions),
        "hearing_burden": {
            "p0_questions": sum(q["priority"] == "P0" for q in questions),
            "p1_questions": sum(q["priority"] == "P1" for q in questions),
            "optional_questions": len(optional),
            "total_questions": len(questions),
            "evidence_targets": sum(len(q["evidence_target"]) for q in questions),
            "evidence_filled_per_question": round(
                sum(len(q["evidence_target"]) for q in questions) / len(questions), 2
            ) if questions else 0,
        },
    }


def ingest_hearing_answers(
    plan: Mapping[str, Any],
    answers: Sequence[Mapping[str, Any]],
    *,
    company_id: str,
    case_id: str,
    mode: str = "production",
) -> list[dict[str, Any]]:
    """Create candidates from answers; synthetic answers are TEST_ONLY only."""
    if mode not in {"production", "test", "simulation"}:
        raise ValueError(f"unsupported hearing intake mode: {mode}")
    questions = {str(q["question_id"]): q for q in plan.get("minimum_question_set", [])}
    fields = {str(q.get("field_id")): q for q in plan.get("minimum_question_set", []) if q.get("field_id")}
    result: list[dict[str, Any]] = []
    for packet in answers:
        question_id = str(packet.get("question_id", ""))
        question = questions.get(question_id) or fields.get(str(packet.get("field_id", "")))
        if not question:
            raise ValueError(f"answer has no matching hearing question: {question_id}")
        simulated = bool(packet.get("simulation_mode", False)) or mode in {"test", "simulation"}
        if simulated and mode == "production":
            raise ValueError("synthetic Hearing answer cannot enter Production mode")
        field_id = str(question.get("field_id", ""))
        answer = packet.get("answer", packet.get("value", ""))
        if field_id in FIELD_BY_ID:
            candidate = answer_to_evidence_candidate(field_id, answer, company_id=company_id, case_id=case_id)
            # A Hearing field can be reused for several domain-specific
            # evidence types.  The requirement, not the generic field
            # default, is authoritative for the candidate target.
            if question.get("evidence_target"):
                candidate["evidence_type"] = str(question["evidence_target"][0])
            if question.get("target_objections"):
                candidate["target_objections"] = list(question["target_objections"])
        else:
            text = "" if answer is None else str(answer).strip()
            candidate = {
                "evidence_id": f"HEARING-CANDIDATE-{field_id or question_id}",
                "company_id": company_id,
                "case_id": case_id,
                "field_id": field_id,
                "evidence_type": str(question.get("evidence_target", [""])[0]),
                "evidence_strength": "E2_SPECIFIC",
                "target_objections": list(question.get("target_objections", [])),
                "claim": text,
                "source": "",
                "source_type": "synthetic_customer_statement" if simulated else "customer_statement",
                "verification_status": "UNVERIFIED_CUSTOMER_INPUT",
                "verification_date": "",
                "usage_status": "TEST_ONLY" if simulated else "UNKNOWN",
                "placement_candidates": ["MIDDLE", "BEFORE_CTA"],
                "rights_status": "UNKNOWN" if question.get("requested_asset") else "NOT_APPLICABLE",
                "hearing_required": True,
                "blocking_status": question.get("blocking_level", "CLAIM_BLOCKING"),
                "notes": "Answer is a candidate only; Safety recheck is mandatory.",
                "completion_status": "NEEDS_VERIFICATION" if text else "HEARING_REQUIRED",
                "next_action": "NEEDS_VERIFICATION" if text else "ASK_AGAIN",
                "safety_recheck_required": True,
            }
        candidate.update({
            "answer_id": str(packet.get("answer_id", f"answer-{question_id}")),
            "question_id": question["question_id"],
            "answered_at": str(packet.get("answered_at", datetime.now(UTC).isoformat())),
            "answer_source": "SIMULATED_TEST_FIXTURE" if simulated else str(packet.get("answer_source", "CLIENT_RESPONSE")),
            "simulation_mode": simulated,
            "customer_answer_status": "UNVERIFIED_CUSTOMER_INPUT",
        })
        result.append(candidate)
    return result


def promote_answer_candidate(
    candidate: Mapping[str, Any],
    *,
    source: str,
    source_type: str,
    verification_status: str,
    verification_date: str,
    rights_status: str,
    usage_status: str,
    verification_class: str,
    supporting_document: str = "",
    reviewer_status: str = "REVIEWED",
    conflict: bool = False,
) -> dict[str, Any]:
    """Attach completion metadata; never skips the existing completion checks."""
    item = complete_evidence_candidate(
        candidate,
        source=source,
        source_type=source_type,
        verification_status=verification_status,
        verification_date=verification_date,
        rights_status=rights_status,
        usage_status=usage_status,
        verification_class=verification_class,
        conflict=conflict,
    )
    # A completed metadata envelope still cannot promote an answer containing
    # a high-risk claim unless the canonical Safety selector can support that
    # exact claim.  This closes the Hearing-to-Production shortcut for claims
    # such as guarantees, No.1, confidentiality, or fully-free promises.
    if item.get("completion_status") == "COMPLETE" and str(item.get("claim", "")).strip():
        claim_check = evaluate_evidence_selection(
            "inquiry",
            item.get("target_objections", []),
            [item],
            requested_claims=[item["claim"]],
            require_production_clearance=True,
        )
        if claim_check.blocked_claims:
            item.update({
                "completion_status": "REJECTED",
                "next_action": "HOLD",
                "safety_recheck_required": True,
                "blocked_claims": claim_check.blocked_claims,
            })
    item.update({
        "customer_answer_status": "PRODUCTION_ELIGIBLE" if item.get("completion_status") == "COMPLETE" else candidate.get("customer_answer_status", "UNVERIFIED_CUSTOMER_INPUT"),
        "supporting_document": supporting_document,
        "reviewer_status": reviewer_status,
        "promoted_at": datetime.now(UTC).isoformat(),
    })
    if candidate.get("simulation_mode"):
        item["simulation_mode"] = True
        item["usage_status"] = "TEST_ONLY" if item.get("completion_status") != "COMPLETE" else item.get("usage_status")
        item["production_status"] = "NOT_PRODUCTION_APPROVED"
    return item


def detect_answer_conflicts(
    answers: Sequence[Mapping[str, Any]],
    existing_ledger: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Flag conflicting claims instead of silently choosing a newer answer."""
    conflicts: list[dict[str, Any]] = []
    by_type = {str(item.get("evidence_type")): item for item in existing_ledger}
    for answer in answers:
        record = by_type.get(str(answer.get("evidence_type")))
        if record and str(record.get("claim", "")).strip() and str(answer.get("claim", "")).strip() and record["claim"].strip() != answer["claim"].strip():
            conflicts.append({
                "answer_id": answer.get("answer_id"),
                "evidence_type": answer.get("evidence_type"),
                "existing_claim": record.get("claim"),
                "answer_claim": answer.get("claim"),
                "status": "CONFLICT",
                "next_action": "HOLD",
            })
    return conflicts


def recheck_safety(
    production_input: Mapping[str, Any],
    completed_evidence: Sequence[Mapping[str, Any]],
    *,
    mode: str = "test",
) -> dict[str, Any]:
    """Re-run the canonical selector after completion, never approve locally."""
    decision = evaluate_evidence_selection(
        str(production_input.get("conversion_goal", "")),
        production_input.get("primary_objections", []),
        completed_evidence,
        requested_claims=production_input.get("requested_claims", []),
        require_production_clearance=mode == "production",
    )
    result = decision.to_dict()
    result["mode"] = mode
    result["safety_recheck"] = True
    if mode in {"test", "simulation"}:
        result["output_status"] = "NOT_PRODUCTION_APPROVED"
    return result


def build_finalization_spec(
    baseline_safety: Mapping[str, Any],
    final_safety: Mapping[str, Any],
    gap_report: Mapping[str, Any],
    *,
    completed_candidates: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    baseline_ids = {str(x.get("evidence_id")) for x in baseline_safety.get("eligible_evidence", [])}
    final_items = list(final_safety.get("eligible_evidence", []))
    newly_approved = [x for x in final_items if str(x.get("evidence_id")) not in baseline_ids]
    unresolved = list(final_safety.get("hearing_required", [])) + list(final_safety.get("blocked_claims", []))
    completed_fields = {str(x.get("field_id")) for x in completed_candidates}
    unresolved_gap_ids = {
        str(gap.get("gap_id"))
        for gap in gap_report.get("missing_evidence", [])
        if str(gap.get("required_field")) not in completed_fields
    }
    blocking_gaps = [gap_id for gap_id in gap_report.get("blocking_gaps", []) if gap_id in unresolved_gap_ids]
    ready = final_safety.get("safety_status") == "PASS" and not unresolved and not blocking_gaps
    unlocked_sections = sorted({
        str(gap.get("affected_section"))
        for gap in gap_report.get("missing_evidence", [])
        if gap.get("affected_section") and str(gap.get("required_field")) in completed_fields
    })
    return {
        "schema_version": "finalization_spec_v1",
        "status": "READY_FOR_FINALIZATION" if ready else "FINALIZATION_BLOCKED",
        "newly_approved_evidence": [x.get("evidence_id") for x in newly_approved],
        "unlocked_claims": [x.get("claim") for x in newly_approved],
        "unlocked_sections": unlocked_sections,
        "upgraded_trust_elements": [x.get("evidence_type") for x in newly_approved],
        "upgraded_assets": [x.get("requested_asset") for x in gap_report.get("missing_evidence", []) if x.get("requested_asset")],
        "cta_changes": ["Re-evaluate CTA Zone after Safety PASS."] if ready else [],
        "proof_changes": [x.get("evidence_id") for x in newly_approved],
        "remaining_blockers": unresolved + blocking_gaps,
        "completed_candidate_count": len(completed_candidates),
        "creative_direction_preserved": True,
        "manual_intervention": [],
    }
