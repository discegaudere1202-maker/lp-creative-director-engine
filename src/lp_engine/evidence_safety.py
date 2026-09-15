from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
import re
from typing import Any, Iterable, Mapping


SUPPORTED_GOALS = {
    "inquiry",
    "quote_request",
    "consultation",
    "reservation",
    "visit",
    "purchase",
    "application",
}
OBJECTION_IDS = {f"O{i}_{label}" for i, label in enumerate(
    ["ABILITY", "ACCOUNTABILITY", "PROCESS", "NEXT", "DECISION", "COST", "RISK", "CONTINUITY"],
    start=1,
)}
ACCEPTED_VERIFICATION = {"VERIFIED"}
ACCEPTED_RIGHTS = {"CLEARED", "NOT_APPLICABLE"}
REQUIRED_FIELDS = (
    "evidence_id",
    "company_id",
    "case_id",
    "evidence_type",
    "evidence_strength",
    "target_objections",
    "claim",
    "source",
    "source_type",
    "verification_status",
    "verification_date",
    "usage_status",
    "placement_candidates",
    "rights_status",
    "hearing_required",
    "blocking_status",
    "notes",
)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    company_id: str
    case_id: str
    evidence_type: str
    evidence_strength: str
    target_objections: tuple[str, ...]
    claim: str
    source: str
    source_type: str
    verification_status: str
    verification_date: str
    usage_status: str
    placement_candidates: tuple[str, ...]
    rights_status: str
    hearing_required: bool
    blocking_status: str
    notes: str = ""

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "EvidenceRecord":
        missing = [field for field in REQUIRED_FIELDS if field not in raw]
        if missing:
            raise ValueError("evidence record missing fields: " + ", ".join(missing))
        return cls(
            evidence_id=str(raw["evidence_id"]),
            company_id=str(raw["company_id"]),
            case_id=str(raw["case_id"]),
            evidence_type=str(raw["evidence_type"]),
            evidence_strength=str(raw["evidence_strength"]),
            target_objections=tuple(str(x) for x in raw["target_objections"]),
            claim=str(raw["claim"]),
            source=str(raw["source"]),
            source_type=str(raw["source_type"]),
            verification_status=str(raw["verification_status"]),
            verification_date=str(raw["verification_date"]),
            usage_status=str(raw["usage_status"]),
            placement_candidates=tuple(str(x) for x in raw["placement_candidates"]),
            rights_status=str(raw["rights_status"]),
            hearing_required=bool(raw["hearing_required"]),
            blocking_status=str(raw["blocking_status"]),
            notes=str(raw.get("notes", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "company_id": self.company_id,
            "case_id": self.case_id,
            "evidence_type": self.evidence_type,
            "evidence_strength": self.evidence_strength,
            "target_objections": list(self.target_objections),
            "claim": self.claim,
            "source": self.source,
            "source_type": self.source_type,
            "verification_status": self.verification_status,
            "verification_date": self.verification_date,
            "usage_status": self.usage_status,
            "placement_candidates": list(self.placement_candidates),
            "rights_status": self.rights_status,
            "hearing_required": self.hearing_required,
            "blocking_status": self.blocking_status,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class SafetyDecision:
    conversion_goal: str
    primary_objections: tuple[str, ...]
    eligible_evidence: list[dict[str, Any]] = field(default_factory=list)
    missing_evidence: list[dict[str, Any]] = field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = field(default_factory=list)
    hearing_required: list[dict[str, Any]] = field(default_factory=list)
    allowed_placements: list[str] = field(default_factory=list)
    safety_status: str = "INVALID_INPUT"
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversion_goal": self.conversion_goal,
            "primary_objections": list(self.primary_objections),
            "eligible_evidence": self.eligible_evidence,
            "missing_evidence": self.missing_evidence,
            "blocked_claims": self.blocked_claims,
            "hearing_required": self.hearing_required,
            "allowed_placements": self.allowed_placements,
            "safety_status": self.safety_status,
            "issues": self.issues,
        }


DEFAULT_OBJECTION_FIELDS: dict[str, dict[str, Any]] = {
    "O1_ABILITY": {"preferred": ["VERIFIED_METRIC", "QUALIFICATION", "EXPERIENCE", "RESULT_CASE"], "field": "ability_proof"},
    "O2_ACCOUNTABILITY": {"preferred": ["OWNER_IDENTITY", "TEAM_IDENTITY", "ACCOUNTABILITY_SCOPE"], "field": "responsible_person_or_team"},
    "O3_PROCESS": {"preferred": ["SERVICE_PROCESS", "CRAFT_ACTION", "PLACE_EXPERIENCE"], "field": "service_process"},
    "O4_NEXT": {"preferred": ["POST_CLICK_FLOW", "RESPONSE_EXPECTATION", "CTA_CHANNEL"], "field": "post_click_flow"},
    "O5_DECISION": {"preferred": ["DECISION_BOUNDARY", "SCOPE_BOUNDARY", "PRICE"], "field": "decision_boundary"},
    "O6_COST": {"preferred": ["PRICE", "FEE_CONDITION", "SCOPE_BOUNDARY"], "field": "fee_conditions"},
    "O7_RISK": {"preferred": ["RISK_POLICY", "PRIVACY_POLICY", "CANCELLATION_POLICY"], "field": "risk_and_privacy_policy"},
    "O8_CONTINUITY": {"preferred": ["CONTINUITY_POLICY", "AFTERCARE", "RESULT_CASE"], "field": "continuity_or_aftercare"},
}


DEFAULT_BLOCKED_CLAIMS = [
    {"claim_id": "NO_PRESSURE", "patterns": ["無理な勧誘はありません", "勧誘しません", "no pressure"], "target_objections": ["O7_RISK"], "required_evidence_types": ["RISK_POLICY"]},
    {"claim_id": "CONFIDENTIALITY", "patterns": ["秘密厳守", "守秘", "confidential"], "target_objections": ["O7_RISK"], "required_evidence_types": ["RISK_POLICY", "PRIVACY_POLICY"]},
    {"claim_id": "RESPONSE_TIME", "patterns": ["返信.*時間", "○時間以内返信", "within.*hour"], "target_objections": ["O4_NEXT"], "required_evidence_types": ["RESPONSE_EXPECTATION"]},
    {"claim_id": "ASSIGNED_PERSON", "patterns": ["必ず代表.*担当", "必ず.*が担当"], "target_objections": ["O2_ACCOUNTABILITY"], "required_evidence_types": ["ACCOUNTABILITY_SCOPE", "OWNER_IDENTITY"]},
    {"claim_id": "FULLY_FREE", "patterns": ["完全無料", "すべて無料", "fully free"], "target_objections": ["O6_COST"], "required_evidence_types": ["PRICE", "FEE_CONDITION"]},
    {"claim_id": "NO_OBLIGATION", "patterns": ["契約義務なし", "no obligation"], "target_objections": ["O5_DECISION", "O7_RISK"], "required_evidence_types": ["DECISION_BOUNDARY", "RISK_POLICY"]},
    {"claim_id": "FREE_CANCELLATION", "patterns": ["キャンセル無料", "無料キャンセル"], "target_objections": ["O7_RISK", "O6_COST"], "required_evidence_types": ["CANCELLATION_POLICY"]},
    {"claim_id": "NO_EXTRA_FEES", "patterns": ["追加料金なし", "no extra fees"], "target_objections": ["O6_COST"], "required_evidence_types": ["FEE_CONDITION"]},
    {"claim_id": "REFUND", "patterns": ["全額返金", "返金保証"], "target_objections": ["O7_RISK"], "required_evidence_types": ["REFUND_POLICY"]},
    {"claim_id": "GUARANTEE", "patterns": ["保証", "必ず結果が出る", "必ず○○できる"], "target_objections": ["O1_ABILITY", "O8_CONTINUITY"], "required_evidence_types": ["GUARANTEE_POLICY", "RESULT_CASE"]},
]


def _as_record(raw: EvidenceRecord | Mapping[str, Any]) -> EvidenceRecord:
    return raw if isinstance(raw, EvidenceRecord) else EvidenceRecord.from_mapping(raw)


def _claim_rule_matches(claim: str, rule: Mapping[str, Any]) -> bool:
    for pattern in rule.get("patterns", []):
        if re.search(str(pattern), claim, flags=re.IGNORECASE):
            return True
    return False


def _supports_claim(record: EvidenceRecord, rule: Mapping[str, Any]) -> bool:
    """Require semantic claim support for high-risk expansions.

    A fee condition such as "初回相談原則無料" is not evidence for the
    stronger customer-facing claim "完全無料". The selector therefore needs
    an exact-strength claim for that rule, not merely the same evidence type.
    """
    claim = record.claim
    if rule.get("claim_id") == "FULLY_FREE":
        return "完全無料" in claim and "条件" not in claim
    return True


def _hearing_item(objection: str, *, blocked_claims: Iterable[str] = ()) -> dict[str, Any]:
    spec = DEFAULT_OBJECTION_FIELDS[objection]
    blocked = list(blocked_claims)
    return {
        "target_objection": objection,
        "missing_evidence_type": spec["preferred"],
        "missing_field": spec["field"],
        "why_needed": f"Primary objection {objection} has no verified, production-eligible evidence.",
        "priority": "HIGH" if blocked else "MEDIUM",
        "blocked_claims": blocked,
        "suggested_hearing_field": spec["field"],
        "status": "HEARING_REQUIRED",
    }


def evaluate_evidence_selection(
    conversion_goal: str,
    primary_objections: Iterable[str],
    evidence_ledger: Iterable[EvidenceRecord | Mapping[str, Any]],
    *,
    requested_claims: Iterable[str] = (),
) -> SafetyDecision:
    """Evaluate evidence eligibility without generating customer-facing copy.

    This is deliberately a safety layer: it selects verified facts and routes gaps
    to hearing. It does not infer reassurance from a name, image, review, or a
    different objection's evidence.
    """
    goal = str(conversion_goal)
    objections = tuple(dict.fromkeys(str(x) for x in primary_objections))
    issues: list[str] = []
    if goal not in SUPPORTED_GOALS:
        issues.append(f"unsupported conversion goal: {goal}")
    invalid_objections = [x for x in objections if x not in OBJECTION_IDS]
    if invalid_objections:
        issues.append("unsupported objections: " + ", ".join(invalid_objections))
    if issues:
        return SafetyDecision(goal, objections, safety_status="INVALID_INPUT", issues=issues)

    records: list[EvidenceRecord] = []
    for raw in evidence_ledger:
        try:
            records.append(_as_record(raw))
        except (TypeError, ValueError) as exc:
            issues.append(str(exc))

    eligible: list[dict[str, Any]] = []
    eligible_by_objection: dict[str, list[EvidenceRecord]] = {x: [] for x in objections}
    for record in records:
        targets = set(record.target_objections)
        if not targets.intersection(objections):
            continue
        if (
            record.verification_status in ACCEPTED_VERIFICATION
            and record.source.strip()
            and record.verification_date.strip()
            and record.rights_status in ACCEPTED_RIGHTS
            and not record.hearing_required
            and record.usage_status not in {"BLOCKED", "REJECTED"}
        ):
            item = record.to_dict()
            eligible.append(item)
            for objection in targets.intersection(objections):
                eligible_by_objection[objection].append(record)

    requested = tuple(str(x) for x in requested_claims)
    blocked_claims: list[dict[str, Any]] = []
    hearing_claims_by_objection: dict[str, list[str]] = {x: [] for x in objections}
    for claim in requested:
        for rule in DEFAULT_BLOCKED_CLAIMS:
            if not _claim_rule_matches(claim, rule):
                continue
            supporting = [
                record for record in records
                if set(record.target_objections).intersection(rule["target_objections"])
                and record.evidence_type in set(rule["required_evidence_types"])
                and record.verification_status in ACCEPTED_VERIFICATION
                and record.source.strip()
                and record.verification_date.strip()
                and record.rights_status in ACCEPTED_RIGHTS
                and not record.hearing_required
                and record.usage_status not in {"BLOCKED", "REJECTED"}
                and _supports_claim(record, rule)
            ]
            if not supporting:
                blocked_claims.append({
                    "claim": claim,
                    "claim_id": rule["claim_id"],
                    "target_objections": rule["target_objections"],
                    "required_evidence_types": rule["required_evidence_types"],
                    "status": "BLOCKED",
                    "reason": "No verified, production-eligible policy/fact supports this claim.",
                })
                for objection in rule["target_objections"]:
                    if objection in hearing_claims_by_objection:
                        hearing_claims_by_objection[objection].append(claim)
            break

    missing: list[dict[str, Any]] = []
    hearing: list[dict[str, Any]] = []
    for objection in objections:
        if eligible_by_objection[objection]:
            continue
        item = _hearing_item(objection, blocked_claims=hearing_claims_by_objection[objection])
        missing.append({
            "target_objection": objection,
            "preferred_evidence_types": item["missing_evidence_type"],
            "status": "MISSING",
        })
        hearing.append(item)

    placements = sorted({
        placement
        for item in eligible
        for placement in item["placement_candidates"]
    })
    if blocked_claims:
        status = "BLOCKED"
    elif hearing:
        status = "HEARING_REQUIRED"
    elif issues:
        status = "INVALID_INPUT"
    else:
        status = "PASS"
    return SafetyDecision(
        goal,
        objections,
        eligible_evidence=eligible,
        missing_evidence=missing,
        blocked_claims=blocked_claims,
        hearing_required=hearing,
        allowed_placements=placements,
        safety_status=status,
        issues=issues,
    )


def production_approved(record: EvidenceRecord | Mapping[str, Any]) -> bool:
    """Return whether one record may be used as production evidence."""
    item = _as_record(record)
    return (
        item.verification_status in ACCEPTED_VERIFICATION
        and bool(item.source.strip() and item.verification_date.strip())
        and item.rights_status in ACCEPTED_RIGHTS
        and not item.hearing_required
        and item.usage_status not in {"BLOCKED", "REJECTED"}
    )
