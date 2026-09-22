"""Executable, deliberately small AAR-PC-3A contract slice for Round 3B."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Iterable
import uuid

CONTRACT_VERSION = "AAR-PC-3A-v1.0+3B"


class DecisionMode(StrEnum):
    DIRECT = "R0_DIRECT"
    SELECTIVE_PARALLEL = "R2_SELECTIVE_PARALLEL"
    NONE = "NONE"


class DecisionState(StrEnum):
    OPEN = "OPEN"
    BRANCHED = "BRANCHED"
    SELECTED = "SELECTED"
    RESOLVED = "RESOLVED"
    NONE = "NONE"


class ArtifactState(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"


class ReviewState(StrEnum):
    SALES_READY = "SALES_READY"
    RETURN_REQUIRED = "RETURN_REQUIRED"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"
    STALE = "STALE"


class CritiqueAction(StrEnum):
    PRESERVE = "PRESERVE"
    STRENGTHEN = "STRENGTHEN"
    REMOVE = "REMOVE"
    RETHINK = "RETHINK"
    DO_NOT_TOUCH = "DO_NOT_TOUCH"


@dataclass
class VersionedEntity:
    entity_id: str
    version: int = 1
    status: str = "CURRENT"


@dataclass
class ProjectCase(VersionedEntity):
    company: str = "なぎのみらい"
    case_state: str = "INTAKE"
    evidence_boundary_id: str = "round2u-b-frozen"


@dataclass
class TruthSet(VersionedEntity):
    facts: dict[str, Any] = field(default_factory=dict)
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class InterpretiveFrame(VersionedEntity):
    customer_tension: str = ""
    commercial_priority: str = ""


@dataclass
class CreativeProblem(VersionedEntity):
    statement: str = ""


@dataclass
class CreativeThesis(VersionedEntity):
    statement: str = ""
    hypothesis_id: str = ""


@dataclass
class Candidate(VersionedEntity):
    hypothesis_id: str = ""
    proposition: str = ""
    representation_ids: list[str] = field(default_factory=list)


@dataclass
class SelectionArgument(VersionedEntity):
    chosen_candidate_id: str = ""
    decisive_reason: str = ""
    company_specific_reason: str = ""
    customer_consequence: str = ""
    commercial_consequence: str = ""
    perceptual_consequence: str = ""
    evidence_reason: str = ""
    accepted_tradeoff: str = ""
    rejected_candidates: list[dict[str, str]] = field(default_factory=list)
    remaining_risk: str = ""


@dataclass
class CreativeDecision(VersionedEntity):
    decision_type: str = ""
    question: str = ""
    mode: DecisionMode = DecisionMode.DIRECT
    state: DecisionState = DecisionState.OPEN
    candidate_ids: list[str] = field(default_factory=list)
    selected_candidate_id: str | None = None
    selection_argument_id: str | None = None
    dependency_keys: list[str] = field(default_factory=list)


@dataclass
class RepresentationArtifact(VersionedEntity):
    representation_type: str = ""
    decision_id: str = ""
    dependency_keys: list[str] = field(default_factory=list)
    state: ArtifactState = ArtifactState.CURRENT
    path: str = ""


@dataclass
class IntegratedRough(VersionedEntity):
    decision_ids: list[str] = field(default_factory=list)
    representation_ids: list[str] = field(default_factory=list)
    critiquable: bool = True
    rebuildable: bool = True


@dataclass
class CritiqueIssue(VersionedEntity):
    action: CritiqueAction = CritiqueAction.RETHINK
    root_decision: str = ""
    why: str = ""
    screen_consequence: str = ""
    return_target: str = ""
    required_representation: str = ""
    preserve_constraint: str = ""


@dataclass
class CritiqueReport(VersionedEntity):
    issue_ids: list[str] = field(default_factory=list)
    context_manifest: list[str] = field(default_factory=list)
    withheld_context: list[str] = field(default_factory=list)


@dataclass
class RevisionBrief(VersionedEntity):
    objective: str = ""
    root_problem: str = ""
    preserve: list[str] = field(default_factory=list)
    strengthen: list[str] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)
    rethink: list[str] = field(default_factory=list)
    do_not_touch: list[str] = field(default_factory=list)
    return_target: str = ""
    affected_decisions: list[str] = field(default_factory=list)
    affected_scenes: list[str] = field(default_factory=list)
    required_representation: str = ""
    success_condition: str = ""
    do_not_solve_by: list[str] = field(default_factory=list)


@dataclass
class RevisionResult(VersionedEntity):
    brief_id: str = ""
    changed_dependency_keys: list[str] = field(default_factory=list)
    preserved_artifact_ids: list[str] = field(default_factory=list)
    regenerated_artifact_ids: list[str] = field(default_factory=list)


@dataclass
class MobileResolution(VersionedEntity):
    representative_scenes: list[str] = field(default_factory=list)
    critical_flow: list[str] = field(default_factory=list)
    mobile_artifact_ids: list[str] = field(default_factory=list)
    authored_complete: bool = False
    technical_responsive_only: bool = False


@dataclass
class FinalCraftResult(VersionedEntity):
    candidate_version: str = ""
    artifact_ids: list[str] = field(default_factory=list)
    decisions_current: bool = True


@dataclass
class RenderPreflightResult(VersionedEntity):
    candidate_version: str = ""
    passed: bool = False
    checks: dict[str, Any] = field(default_factory=dict)


@dataclass
class AoiHumanRealityReview(VersionedEntity):
    candidate_version: str = ""
    state: ReviewState = ReviewState.RETURN_REQUIRED
    pass_a: dict[str, Any] = field(default_factory=dict)
    pass_b: dict[str, Any] = field(default_factory=dict)
    visual_dependency_keys: list[str] = field(default_factory=list)
    reviewer_type: str = "automated_visual_review"


@dataclass
class FloorQAResult(VersionedEntity):
    candidate_version: str = ""
    passed: bool = False
    checks: dict[str, Any] = field(default_factory=dict)


@dataclass
class SalesReleaseRecord(VersionedEntity):
    eligible: bool = False
    candidate_version: str = ""
    blockers: list[str] = field(default_factory=list)
    claim: str = "ELIGIBLE_FOR_SALES_PRODUCTION"


@dataclass
class DecisionTrace(VersionedEntity):
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ProductionRun(VersionedEntity):
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: str | None = None
    stage_durations_ms: dict[str, int] = field(default_factory=dict)
    model_calls: int = 0
    token_estimate: int = 0
    artifact_generation_count: int = 0
    artifact_reuse_count: int = 0
    branch_count: int = 0
    representation_upgrades: int = 0
    decision_reopen_count: int = 0
    critique_count: int = 0
    revision_count: int = 0
    aoi_reviews: int = 0
    aoi_returns: int = 0
    regenerated_artifacts: int = 0
    preserved_artifacts: int = 0
    full_page_regeneration_count: int = 0


@dataclass
class DependencyManifest:
    artifacts: dict[str, set[str]] = field(default_factory=dict)

    def register(self, artifact_id: str, dependency_keys: Iterable[str]) -> None:
        self.artifacts[artifact_id] = set(dependency_keys)

    def affected_by(self, changed_keys: Iterable[str]) -> set[str]:
        changed = set(changed_keys)
        return {artifact_id for artifact_id, keys in self.artifacts.items() if keys & changed}


@dataclass
class EventLog:
    case_id: str
    events: list[dict[str, Any]] = field(default_factory=list)

    def append(self, event_type: str, **payload: Any) -> dict[str, Any]:
        event = {"event_id": str(uuid.uuid4()), "timestamp": datetime.now(timezone.utc).isoformat(), "case_id": self.case_id, "event_type": event_type, **payload}
        self.events.append(event)
        return event


def open_decision(decision_type: str, question: str, hypotheses: list[dict[str, str]], dependency_keys: Iterable[str] = ()) -> CreativeDecision:
    """One solution stays direct; parallel candidates require distinct hypotheses."""
    decision_id = f"decision:{decision_type.lower()}"
    if not hypotheses:
        return CreativeDecision(decision_id, decision_type=decision_type, question=question, mode=DecisionMode.NONE, state=DecisionState.NONE, dependency_keys=list(dependency_keys))
    if len(hypotheses) == 1:
        candidate = Candidate(f"candidate:{hypotheses[0]['id']}", hypothesis_id=hypotheses[0]["id"], proposition=hypotheses[0]["proposition"])
        return CreativeDecision(decision_id, decision_type=decision_type, question=question, mode=DecisionMode.DIRECT, state=DecisionState.RESOLVED, candidate_ids=[candidate.entity_id], selected_candidate_id=candidate.entity_id, dependency_keys=list(dependency_keys))
    ids = [hypothesis["id"] for hypothesis in hypotheses]
    if len(set(ids)) != len(ids):
        raise ValueError("parallel candidates must encode different hypotheses")
    return CreativeDecision(decision_id, decision_type=decision_type, question=question, mode=DecisionMode.SELECTIVE_PARALLEL, state=DecisionState.BRANCHED, candidate_ids=[f"candidate:{item}" for item in ids], dependency_keys=list(dependency_keys))


def select_candidate(decision: CreativeDecision, candidate_id: str, argument: SelectionArgument | None) -> None:
    if decision.mode != DecisionMode.SELECTIVE_PARALLEL or candidate_id not in decision.candidate_ids:
        raise ValueError("selection must target a candidate in an open parallel decision")
    if argument is None or argument.chosen_candidate_id != candidate_id or not argument.decisive_reason:
        raise ValueError("SelectionArgument with a decisive reason is required")
    decision.selected_candidate_id = candidate_id
    decision.selection_argument_id = argument.entity_id
    decision.state = DecisionState.SELECTED


def build_revision_brief(issue: CritiqueIssue) -> RevisionBrief:
    if not issue.root_decision or not issue.return_target:
        raise ValueError("critique issue needs a causal root and return target")
    return RevisionBrief(
        f"revision-brief:{issue.entity_id}", objective=f"Resolve {issue.root_decision} at {issue.return_target}",
        root_problem=issue.why, preserve=[issue.preserve_constraint] if issue.preserve_constraint else [],
        rethink=[issue.why] if issue.action == CritiqueAction.RETHINK else [],
        do_not_touch=[issue.preserve_constraint] if issue.preserve_constraint else [],
        return_target=issue.return_target, affected_decisions=[issue.root_decision],
        required_representation=issue.required_representation, success_condition=issue.screen_consequence,
    )


def route_critique_to_designer(issue: CritiqueIssue, revision_brief: RevisionBrief | None) -> None:
    if revision_brief is None or revision_brief.return_target != issue.return_target:
        raise ValueError("critique cannot return directly to designer; Revision Planner is required")


def aoi_direct_prompt_allowed(prompt: str) -> bool:
    forbidden = ("make it more premium", "rewrite the thesis", "choose the direction", "certify ¥1m")
    return not any(term in prompt.casefold() for term in forbidden)


def mobile_is_complete(resolution: MobileResolution) -> bool:
    return bool(resolution.authored_complete and not resolution.technical_responsive_only and resolution.representative_scenes and resolution.mobile_artifact_ids)


def invalidate_artifacts(manifest: DependencyManifest, artifacts: dict[str, RepresentationArtifact], changed_keys: Iterable[str]) -> tuple[list[str], list[str]]:
    affected = manifest.affected_by(changed_keys)
    stale, preserved = [], []
    for artifact_id, artifact in artifacts.items():
        if artifact_id in affected:
            artifact.state = ArtifactState.STALE
            stale.append(artifact_id)
        else:
            preserved.append(artifact_id)
    return sorted(stale), sorted(preserved)


def update_aoi_after_fix(review: AoiHumanRealityReview, changed_keys: Iterable[str]) -> bool:
    if set(changed_keys) & set(review.visual_dependency_keys):
        review.state = ReviewState.STALE
        return True
    return False


def sales_readiness_blockers(*, craft: FinalCraftResult | None, preflight: RenderPreflightResult | None,
    review: AoiHumanRealityReview | None, floor: FloorQAResult | None, decisions_current: bool,
    stale_required_artifacts: Iterable[str], active_escalation: bool, dependencies_valid: bool,
    public_candidate_version: str, required_artifact_states: Iterable[ArtifactState] = ()) -> list[str]:
    blockers: list[str] = []
    version = craft.candidate_version if craft else ""
    if craft is None or not craft.decisions_current: blockers.append("final_craft_not_current")
    if preflight is None or not preflight.passed or preflight.candidate_version != version: blockers.append("render_preflight_not_current_pass")
    if review is None or review.state != ReviewState.SALES_READY or review.candidate_version != version: blockers.append("aoi_review_not_current_sales_ready")
    if floor is None or not floor.passed or floor.candidate_version != version: blockers.append("floor_qa_not_current_pass")
    if not decisions_current: blockers.append("blocking_decision_unresolved")
    if list(stale_required_artifacts) or any(state == ArtifactState.STALE for state in required_artifact_states): blockers.append("stale_required_artifact")
    if active_escalation: blockers.append("active_escalation")
    if not dependencies_valid: blockers.append("dependency_invalid")
    if not version or public_candidate_version != version: blockers.append("public_candidate_version_mismatch")
    return blockers


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_jsonable(asdict(value))
    if isinstance(value, dict): return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)): return [to_jsonable(item) for item in value]
    if isinstance(value, StrEnum): return value.value
    return value
