"""Schema-first hearing planning and evidence completion helpers.

This module plans the smallest useful set of customer questions. It never
turns a customer answer directly into a production claim: answers start as
unverified candidates and must be completed, then re-evaluated by the Safety
selector before they can be used in Production.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


REQUIREMENT_CLASSES = {
    "UNIVERSAL_REQUIRED",
    "DOMAIN_REQUIRED",
    "CONDITIONAL_REQUIRED",
    "HIGH_VALUE",
    "OPTIONAL",
}
BLOCKING_LEVELS = {"CLAIM_BLOCKING", "SECTION_BLOCKING", "PAGE_BLOCKING", "NON_BLOCKING"}
ANSWER_TYPES = {
    "boolean", "short_text", "long_text", "number", "currency", "duration",
    "select", "multi_select", "URL", "file_reference", "date", "structured_steps",
}
VERIFICATION_CLASSES = {
    "SELF_DECLARABLE",
    "DOCUMENT_REQUIRED",
    "THIRD_PARTY_EVIDENCE_REQUIRED",
    "RIGHTS_REQUIRED",
}
PRODUCTION_RIGHTS = {"CLEARED", "NOT_APPLICABLE"}
PRODUCTION_USAGE = {"ELIGIBLE", "PRODUCTION_ELIGIBLE"}
VAGUE_MARKERS = ("多分", "たぶん", "おそらく", "だいたい", "と思います", "かもしれません")


@dataclass(frozen=True)
class HearingField:
    field_id: str
    label: str
    description: str
    requirement_class: str
    target_objections: tuple[str, ...]
    target_evidence_types: tuple[str, ...]
    trigger_condition: dict[str, Any]
    blocking_level: str
    question_template: str
    answer_type: str
    verification_requirement: str
    provenance_requirement: str
    rights_requirement: str
    fallback: str
    priority: str
    answer_group: str
    verification_class: str

    def __post_init__(self):
        if self.requirement_class not in REQUIREMENT_CLASSES:
            raise ValueError(f"unsupported requirement class: {self.requirement_class}")
        if self.blocking_level not in BLOCKING_LEVELS:
            raise ValueError(f"unsupported blocking level: {self.blocking_level}")
        if self.answer_type not in ANSWER_TYPES:
            raise ValueError(f"unsupported answer type: {self.answer_type}")
        if self.verification_class not in VERIFICATION_CLASSES:
            raise ValueError(f"unsupported verification class: {self.verification_class}")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["target_objections"] = list(self.target_objections)
        data["target_evidence_types"] = list(self.target_evidence_types)
        return data


@dataclass(frozen=True)
class HearingPlan:
    conversion_goal: str
    domain: str
    required_hearing_fields: list[dict[str, Any]] = field(default_factory=list)
    minimum_question_set: list[dict[str, Any]] = field(default_factory=list)
    blocking_questions: list[str] = field(default_factory=list)
    optional_questions: list[str] = field(default_factory=list)
    redundant_questions: list[str] = field(default_factory=list)
    resulting_evidence_candidates: list[dict[str, Any]] = field(default_factory=list)
    completion_status: str = "PLANNED"

    def to_dict(self) -> dict[str, Any]:
        questions = self.minimum_question_set
        return {
            "conversion_goal": self.conversion_goal,
            "domain": self.domain,
            "required_hearing_fields": self.required_hearing_fields,
            "minimum_question_set": questions,
            "blocking_questions": self.blocking_questions,
            "optional_questions": self.optional_questions,
            "redundant_questions": self.redundant_questions,
            "resulting_evidence_candidates": self.resulting_evidence_candidates,
            "completion_status": self.completion_status,
            "question_count": len(questions),
            "hearing_burden": {
                "p0_questions": sum(x["priority"] == "P0" for x in questions),
                "p1_questions": sum(x["priority"] == "P1" for x in questions),
                "optional_questions": len(self.optional_questions),
                "total_questions": len(questions),
                "evidence_filled_per_question": round(
                    sum(len(x["target_evidence_types"]) for x in questions) / len(questions), 2
                ) if questions else 0,
            },
        }


def _field(
    field_id: str,
    label: str,
    description: str,
    requirement_class: str,
    objections: Sequence[str],
    evidence_types: Sequence[str],
    question: str,
    answer_type: str,
    blocking_level: str,
    priority: str,
    answer_group: str,
    verification_class: str = "SELF_DECLARABLE",
    *,
    trigger: str = "NEED_AND_MISSING_AND_RELEVANT",
    verification: str = "Confirm against an official company source or dated client-approved statement.",
    provenance: str = "source, source_type and verification_date are required",
    rights: str = "NOT_APPLICABLE unless the answer references an image, logo or file",
) -> HearingField:
    return HearingField(
        field_id=field_id,
        label=label,
        description=description,
        requirement_class=requirement_class,
        target_objections=tuple(objections),
        target_evidence_types=tuple(evidence_types),
        trigger_condition={"expression": trigger},
        blocking_level=blocking_level,
        question_template=question,
        answer_type=answer_type,
        verification_requirement=verification,
        provenance_requirement=provenance,
        rights_requirement=rights,
        fallback="HEARING_REQUIRED",
        priority=priority,
        answer_group=answer_group,
        verification_class=verification_class,
    )


DEFAULT_HEARING_FIELDS: tuple[HearingField, ...] = (
    _field("responsible_person_or_team", "担当主体", "問い合わせ後に責任を持って対応する人またはチーム", "UNIVERSAL_REQUIRED", ["O2_ACCOUNTABILITY"], ["OWNER_IDENTITY", "TEAM_IDENTITY", "ACCOUNTABILITY_SCOPE"], "お問い合わせ後は、どなた、またはどのチームが主に対応されますか？", "short_text", "SECTION_BLOCKING", "P1", "responsible_party"),
    _field("service_scope", "対応範囲", "何を依頼でき、何が対象外か", "UNIVERSAL_REQUIRED", ["O3_PROCESS", "O5_DECISION"], ["SCOPE_BOUNDARY"], "対応できることと、対応の対象外になることを教えてください。", "long_text", "SECTION_BLOCKING", "P1", "scope"),
    _field("service_process", "提供工程", "相談・制作・施術などの実際の進み方", "UNIVERSAL_REQUIRED", ["O3_PROCESS"], ["SERVICE_PROCESS", "CRAFT_ACTION", "PLACE_EXPERIENCE"], "お問い合わせから提供完了まで、主な流れを教えてください。", "structured_steps", "SECTION_BLOCKING", "P1", "process"),
    _field("post_click_flow", "問い合わせ後の流れ", "クリック後に起きることと次の連絡", "UNIVERSAL_REQUIRED", ["O4_NEXT"], ["POST_CLICK_FLOW", "RESPONSE_EXPECTATION", "CTA_CHANNEL"], "お問い合わせ・予約をした後、最初に何が起きますか？", "structured_steps", "SECTION_BLOCKING", "P1", "next"),
    _field("primary_evidence_source", "主要Evidenceの出典", "公開または確認可能な会社固有事実の出典", "UNIVERSAL_REQUIRED", ["O1_ABILITY", "O2_ACCOUNTABILITY", "O3_PROCESS", "O4_NEXT"], ["VERIFIED_METRIC", "EXPERIENCE", "QUALIFICATION", "RESULT_CASE"], "この内容を確認できる公式ページ、資料、または記録はありますか？", "URL", "CLAIM_BLOCKING", "P1", "evidence_source", "DOCUMENT_REQUIRED", verification="Provide a source or document that can be checked.", rights="Source permission must be confirmed if a file or image is supplied."),
    _field("ability_proof", "能力の根拠", "資格・許認可・経験・実績などの検証可能な根拠", "DOMAIN_REQUIRED", ["O1_ABILITY"], ["VERIFIED_METRIC", "QUALIFICATION", "EXPERIENCE", "RESULT_CASE"], "資格、経験、実績など、確認できる根拠を教えてください。", "long_text", "CLAIM_BLOCKING", "P1", "ability", "DOCUMENT_REQUIRED"),
    _field("fee_conditions", "費用条件", "料金、無料範囲、費用発生のタイミング", "DOMAIN_REQUIRED", ["O6_COST"], ["PRICE", "FEE_CONDITION", "SCOPE_BOUNDARY"], "料金はいくらで、どの時点から費用が発生しますか？条件があれば教えてください。", "currency", "SECTION_BLOCKING", "P1", "cost"),
    _field("continuity_or_aftercare", "継続・アフター対応", "購入・相談・提供後の支援や保守", "DOMAIN_REQUIRED", ["O8_CONTINUITY"], ["CONTINUITY_POLICY", "AFTERCARE", "RESULT_CASE"], "提供後や相談後に、継続する支援・保守・フォローはありますか？", "long_text", "SECTION_BLOCKING", "P1", "continuity"),
    _field("decision_boundary", "判断のタイミング", "契約・購入・申込を判断する時点", "CONDITIONAL_REQUIRED", ["O5_DECISION"], ["DECISION_BOUNDARY", "SCOPE_BOUNDARY", "PRICE"], "契約・購入・申込みを判断するのは、どの段階ですか？", "short_text", "CLAIM_BLOCKING", "P1", "decision"),
    _field("risk_and_privacy_policy", "不利益・個人情報の扱い", "勧誘、守秘、個人情報、キャンセル等の実際の方針", "CONDITIONAL_REQUIRED", ["O7_RISK"], ["RISK_POLICY", "PRIVACY_POLICY", "CANCELLATION_POLICY"], "相談後に契約しない場合や、個人情報・キャンセルについて、実際にはどのような対応になりますか？", "long_text", "CLAIM_BLOCKING", "P1", "risk", "SELF_DECLARABLE"),
    _field("response_expectation", "返信・対応目安", "返信方法と対応の目安。時間を約束する場合の根拠", "CONDITIONAL_REQUIRED", ["O4_NEXT"], ["RESPONSE_EXPECTATION"], "お問い合わせ後の連絡方法と、案内できる対応目安があれば教えてください。", "short_text", "CLAIM_BLOCKING", "P1", "next"),
    _field("visual_rights", "素材利用権", "人物写真、現場写真、ロゴ等の利用許諾", "CONDITIONAL_REQUIRED", [], ["OWNER_PORTRAIT", "PLACE_WIDE", "PRODUCT_DETAIL", "CRAFT_ACTION"], "掲載する写真・ロゴ・資料について、LPで利用してよい範囲を確認できますか？", "file_reference", "CLAIM_BLOCKING", "P1", "rights", "RIGHTS_REQUIRED", rights="Explicit client permission or a documented production license is required."),
    _field("customer_state", "顧客の現在の状況", "誰のどの状態をLPで扱うか", "HIGH_VALUE", [], ["HERO_REALITY"], "今回のLPを見てほしいお客様は、どのような状況で相談・予約・購入を検討されますか？", "long_text", "NON_BLOCKING", "P2", "customer_state"),
)

FIELD_BY_ID = {item.field_id: item for item in DEFAULT_HEARING_FIELDS}
FIELD_BY_EVIDENCE = {
    evidence_type: item
    for item in DEFAULT_HEARING_FIELDS
    for evidence_type in item.target_evidence_types
}


def _as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _missing_types(safety: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for item in safety.get("missing_evidence", []):
        result.update(str(x) for x in item.get("preferred_evidence_types", []))
        result.update(str(x) for x in item.get("missing_evidence_type", []))
    for item in safety.get("hearing_required", []):
        result.update(str(x) for x in item.get("missing_evidence_type", []))
    for item in safety.get("blocked_claims", []):
        result.update(str(x) for x in item.get("required_evidence_types", []))
    return result


def plan_hearing(
    safety_report: Any,
    *,
    conversion_goal: str = "",
    primary_objections: Sequence[str] = (),
    domain: str = "",
    current_ledger: Sequence[Mapping[str, Any]] = (),
) -> HearingPlan:
    """Create a deduplicated minimum question set from Safety gaps."""
    safety = _as_dict(safety_report)
    goal = conversion_goal or str(safety.get("conversion_goal", ""))
    objections = set(primary_objections or safety.get("primary_objections", []))
    missing_types = _missing_types(safety)
    missing_by_objection = {
        str(item.get("target_objection"))
        for item in safety.get("missing_evidence", [])
        if item.get("target_objection")
    }
    relevant_objections = objections | missing_by_objection
    eligible_types = {
        str(item.get("evidence_type"))
        for item in safety.get("eligible_evidence", [])
    }
    eligible_types.update(
        str(item.get("evidence_type"))
        for item in current_ledger
        if str(item.get("verification_status", "")) == "VERIFIED"
    )

    selected: dict[str, HearingField] = {}
    for evidence_type in missing_types:
        field_spec = FIELD_BY_EVIDENCE.get(evidence_type)
        if not field_spec:
            continue
        if set(field_spec.target_objections) and not (set(field_spec.target_objections) & relevant_objections):
            continue
        if set(field_spec.target_evidence_types) & eligible_types:
            continue
        selected[field_spec.field_id] = field_spec

    # If Safety only returned an objection but no type, use that objection's
    # canonical field. This keeps the planner useful for older reports.
    for field_spec in DEFAULT_HEARING_FIELDS:
        if field_spec.field_id in selected:
            continue
        if set(field_spec.target_objections) & relevant_objections and any(
            field_type in missing_types for field_type in field_spec.target_evidence_types
        ) and not (set(field_spec.target_evidence_types) & eligible_types):
            selected[field_spec.field_id] = field_spec

    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    fields = sorted(selected.values(), key=lambda item: (priority_rank.get(item.priority, 9), item.field_id))
    questions = []
    seen_groups: set[str] = set()
    redundant: list[str] = []
    for spec in fields:
        if spec.answer_group in seen_groups:
            redundant.append(spec.field_id)
            continue
        seen_groups.add(spec.answer_group)
        questions.append({
            "field_id": spec.field_id,
            "question": spec.question_template,
            "reason": spec.description,
            "priority": spec.priority,
            "requirement_class": spec.requirement_class,
            "blocking_level": spec.blocking_level,
            "answer_type": spec.answer_type,
            "target_objections": list(spec.target_objections),
            "target_evidence_types": list(spec.target_evidence_types),
            "verification_class": spec.verification_class,
            "verification_requirement": spec.verification_requirement,
            "provenance_requirement": spec.provenance_requirement,
            "rights_requirement": spec.rights_requirement,
            "evidence_target": spec.target_evidence_types[0],
            "status": "QUESTION_REQUIRED",
        })
    blocking = [item["field_id"] for item in questions if item["blocking_level"] in {"PAGE_BLOCKING", "SECTION_BLOCKING", "CLAIM_BLOCKING"}]
    optional = [item["field_id"] for item in questions if item["blocking_level"] == "NON_BLOCKING"]
    return HearingPlan(
        conversion_goal=goal,
        domain=domain,
        required_hearing_fields=[FIELD_BY_ID[item["field_id"]].to_dict() for item in questions],
        minimum_question_set=questions,
        blocking_questions=blocking,
        optional_questions=optional,
        redundant_questions=redundant,
    )


def _field_spec(field: HearingField | str | Mapping[str, Any]) -> HearingField:
    if isinstance(field, HearingField):
        return field
    if isinstance(field, str) and field in FIELD_BY_ID:
        return FIELD_BY_ID[field]
    if isinstance(field, Mapping):
        data = dict(field)
        data["target_objections"] = tuple(data.get("target_objections", []))
        data["target_evidence_types"] = tuple(data.get("target_evidence_types", []))
        return HearingField(**data)
    raise ValueError("unknown hearing field")


def answer_to_evidence_candidate(
    field: HearingField | str | Mapping[str, Any],
    answer: Any,
    *,
    company_id: str = "",
    case_id: str = "",
) -> dict[str, Any]:
    """Convert an answer to an unverified candidate, never production evidence."""
    spec = _field_spec(field)
    if isinstance(answer, Mapping):
        if answer.get("conflict") or str(answer.get("status", "")).upper() == "CONFLICT":
            return {"field_id": spec.field_id, "completion_status": "CONFLICT", "next_action": "HOLD", "safety_recheck_required": True}
        value = answer.get("value", answer.get("answer", ""))
    else:
        value = answer
    text = "" if value is None else str(value).strip()
    if not text:
        return {"field_id": spec.field_id, "completion_status": "HEARING_REQUIRED", "next_action": "ASK_AGAIN", "safety_recheck_required": True}
    vague = any(marker in text for marker in VAGUE_MARKERS)
    status = "UNVERIFIED_CUSTOMER_INPUT"
    next_action = "NEEDS_VERIFICATION"
    completion = "NEEDS_VERIFICATION"
    if spec.verification_class == "DOCUMENT_REQUIRED":
        next_action = "NEEDS_DOCUMENT"
        completion = "NEEDS_DOCUMENT"
    if spec.verification_class == "THIRD_PARTY_EVIDENCE_REQUIRED":
        next_action = "NEEDS_DOCUMENT"
        completion = "NEEDS_DOCUMENT"
    if spec.verification_class == "RIGHTS_REQUIRED":
        next_action = "NEEDS_RIGHTS"
        completion = "NEEDS_RIGHTS"
    if vague:
        next_action = "NEEDS_VERIFICATION"
        completion = "NEEDS_VERIFICATION"
    return {
        "evidence_id": f"HEARING-CANDIDATE-{spec.field_id}",
        "company_id": company_id,
        "case_id": case_id,
        "field_id": spec.field_id,
        "evidence_type": spec.target_evidence_types[0],
        "evidence_strength": "E2_SPECIFIC",
        "target_objections": list(spec.target_objections),
        "claim": text,
        "source": "",
        "source_type": "customer_statement",
        "verification_status": status,
        "verification_date": "",
        "usage_status": "UNKNOWN",
        "placement_candidates": ["MIDDLE", "BEFORE_CTA"],
        "rights_status": "UNKNOWN" if spec.verification_class == "RIGHTS_REQUIRED" else "NOT_APPLICABLE",
        "hearing_required": True,
        "blocking_status": spec.blocking_level,
        "notes": "Customer answer is a candidate only; Safety recheck is mandatory.",
        "completion_status": completion,
        "next_action": next_action,
        "safety_recheck_required": True,
    }


def complete_evidence_candidate(
    candidate: Mapping[str, Any],
    *,
    source: str,
    source_type: str,
    verification_status: str,
    verification_date: str,
    rights_status: str,
    usage_status: str,
    verification_class: str = "SELF_DECLARABLE",
    conflict: bool = False,
) -> dict[str, Any]:
    """Attach verification/provenance/rights metadata without bypassing Safety."""
    item = dict(candidate)
    if conflict:
        item.update({"completion_status": "CONFLICT", "next_action": "HOLD", "safety_recheck_required": True})
        return item
    item.update({
        "source": source,
        "source_type": source_type,
        "verification_status": verification_status,
        "verification_date": verification_date,
        "rights_status": rights_status,
        "usage_status": usage_status,
        "verification_class": verification_class,
    })
    if verification_class in {"DOCUMENT_REQUIRED", "THIRD_PARTY_EVIDENCE_REQUIRED"} and source_type in {"customer_statement", "self_reported"}:
        item.update({"completion_status": "NEEDS_DOCUMENT", "next_action": "PROVIDE_DOCUMENT", "safety_recheck_required": True})
        return item
    if verification_status != "VERIFIED" or not source.strip() or not verification_date.strip():
        item.update({"completion_status": "NEEDS_VERIFICATION", "next_action": "VERIFY_SOURCE", "safety_recheck_required": True})
        return item
    if rights_status not in PRODUCTION_RIGHTS:
        item.update({"completion_status": "NEEDS_RIGHTS", "next_action": "CONFIRM_RIGHTS", "safety_recheck_required": True})
        return item
    if usage_status not in PRODUCTION_USAGE:
        item.update({"completion_status": "NEEDS_VERIFICATION", "next_action": "MARK_PRODUCTION_ELIGIBLE_AFTER_REVIEW", "safety_recheck_required": True})
        return item
    item.update({"completion_status": "COMPLETE", "next_action": "SAFETY_RECHECK_REQUIRED", "safety_recheck_required": True, "hearing_required": False, "blocking_status": "NON_BLOCKING"})
    return item


def verify_evidence_candidate(candidate: Mapping[str, Any], **metadata: Any) -> dict[str, Any]:
    return complete_evidence_candidate(candidate, **metadata)
