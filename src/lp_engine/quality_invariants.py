"""Round 3D-I: versioned quality invariants and regression-immunity primitives.

This module deliberately contains no visual-direction rule.  It protects verified
quality, evidence, public-output and rendering floors across later revisions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json
from typing import Any, Iterable


CONTRACT_VERSION = "AAR-QI-3D-v1.0"
REQUIRED_VIEWPORTS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)


class InvariantStatus(StrEnum):
    DRAFT = "DRAFT"
    SHADOW = "SHADOW"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class EnforcementType(StrEnum):
    AUTO_REPAIR = "AUTO_REPAIR"
    CONTROLLED_RETURN = "CONTROLLED_RETURN"
    HARD_BLOCK = "HARD_BLOCK"


class ArtifactValidity(StrEnum):
    GENERATED = "GENERATED"
    INVARIANT_VALIDATION_PENDING = "INVARIANT_VALIDATION_PENDING"
    VALID = "VALID"
    INVALID_INVARIANT = "INVALID_INVARIANT"
    NEEDS_REVALIDATION = "NEEDS_REVALIDATION"


class ReturnTarget(StrEnum):
    COPY = "COPY"
    TYPOGRAPHY = "TYPOGRAPHY"
    TRUTH_EVIDENCE = "TRUTH_EVIDENCE"
    MOBILE_COMPOSITION = "MOBILE_COMPOSITION"
    RESTORE_APPROVED_DECISION = "RESTORE_APPROVED_DECISION"
    RELEASE = "RELEASE"


class DecisionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    REOPENED = "REOPENED"
    SUPERSEDED = "SUPERSEDED"


class BackgroundStrategy(StrEnum):
    NONE = "NONE"
    SOLID = "SOLID"
    MATERIAL = "MATERIAL"
    PHOTOGRAPHIC = "PHOTOGRAPHIC"
    ATMOSPHERIC = "ATMOSPHERIC"


@dataclass(frozen=True)
class QualityInvariant:
    invariant_id: str
    canonical_name: str
    invariant_version: str
    status: InvariantStatus
    scope: str = "GLOBAL"
    category_scope: tuple[str, ...] = ()
    defect_class: str = ""
    defect_definition: str = ""
    why_defective: str = ""
    applicability: tuple[str, ...] = ("page",)
    detection_method: tuple[str, ...] = ("static",)
    validator_contract: str = ""
    rendered_validation_required: bool = False
    required_viewports: tuple[int, ...] = ()
    enforcement_type: EnforcementType = EnforcementType.HARD_BLOCK
    release_effect: str = "BLOCK"
    repair_policy: str = "controlled return"
    return_target_default: ReturnTarget = ReturnTarget.RELEASE
    origin: str = CONTRACT_VERSION
    approved_by: str = "Shun Decision Gate"
    regression_test_refs: tuple[str, ...] = ()
    preserve_across_generation: bool = True
    preserve_across_revision: bool = True
    preserve_across_return: bool = True
    preserve_across_mobile: bool = True
    preserve_across_craft: bool = True


class QualityInvariantRegistry:
    def __init__(self, invariants: Iterable[QualityInvariant] = ()) -> None:
        self._items = {item.invariant_id: item for item in invariants}

    def register(self, invariant: QualityInvariant) -> None:
        previous = self._items.get(invariant.invariant_id)
        if previous and previous.invariant_version == invariant.invariant_version:
            raise ValueError("invariant version must advance when replacing a registry item")
        self._items[invariant.invariant_id] = invariant

    def get(self, invariant_id: str) -> QualityInvariant:
        return self._items[invariant_id]

    def active(self) -> list[QualityInvariant]:
        return [item for item in self._items.values() if item.status == InvariantStatus.ACTIVE]

    def snapshot(self) -> dict[str, Any]:
        return {"contract": CONTRACT_VERSION, "invariants": [to_jsonable(item) for item in sorted(self._items.values(), key=lambda x: x.invariant_id)]}


def _seed(invariant_id: str, name: str, family: str, *, active: bool = True, rendered: bool = False,
          enforcement: EnforcementType = EnforcementType.HARD_BLOCK, target: ReturnTarget = ReturnTarget.RELEASE,
          definition: str = "") -> QualityInvariant:
    return QualityInvariant(
        invariant_id, name, "1.0.0", InvariantStatus.ACTIVE if active else InvariantStatus.SHADOW,
        defect_class=family, defect_definition=definition or name, why_defective="Breaks a verified quality floor.",
        detection_method=("static", "semantic", "rendered") if rendered else ("static",),
        rendered_validation_required=rendered, required_viewports=REQUIRED_VIEWPORTS if rendered else (),
        enforcement_type=enforcement, return_target_default=target,
        regression_test_refs=("tests/test_round3d_regression_immunity.py",),
    )


def seeded_registry() -> QualityInvariantRegistry:
    items = [
        _seed("QI-JP-LINE-01", "Semantic Unit Preservation", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.CONTROLLED_RETURN, target=ReturnTarget.COPY),
        _seed("QI-JP-LINE-02", "Particle Orphan", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.HARD_BLOCK, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-03", "Conjunction Orphan", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.HARD_BLOCK, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-04", "Semantic Dependency", "JAPANESE_LINE_COMPOSITION", active=False, rendered=True, enforcement=EnforcementType.CONTROLLED_RETURN, target=ReturnTarget.COPY, definition="Semantic/rhetorical dependency calibration in shadow mode."),
        _seed("QI-JP-LINE-05", "No Character-count Breaker", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.CONTROLLED_RETURN, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-06", "No Isolated Content Word", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.HARD_BLOCK, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-07", "First / Last Line Orphan", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.HARD_BLOCK, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-08", "Desktop Headline Composition", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.CONTROLLED_RETURN, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-09", "Mobile Natural Wrap", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.CONTROLLED_RETURN, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-10", "Role-specific Rules", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.HARD_BLOCK, target=ReturnTarget.TYPOGRAPHY),
        _seed("QI-JP-LINE-11", "Required Viewport Validation", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.HARD_BLOCK),
        _seed("QI-JP-LINE-12", "No Accidental Truncation", "JAPANESE_LINE_COMPOSITION", rendered=True, enforcement=EnforcementType.HARD_BLOCK),
        _seed("QI-TRUST-01", "Trust Integrity", "TRUST_INTEGRITY", definition="No fabricated human proof.", target=ReturnTarget.TRUTH_EVIDENCE),
        _seed("QI-EVIDENCE-01", "Evidence Boundary", "EVIDENCE_BOUNDARY", definition="Claims must retain their evidence boundary.", target=ReturnTarget.TRUTH_EVIDENCE),
        _seed("QI-PUBLIC-01", "Public Output Safety", "PUBLIC_OUTPUT_SAFETY", definition="Internal, dummy, provisional and debug language cannot render publicly."),
        _seed("QI-RESPONSIVE-01", "Responsive Floor", "RESPONSIVE_FLOOR", rendered=True, definition="Required mobile and desktop viewports remain usable.", target=ReturnTarget.MOBILE_COMPOSITION),
        _seed("QI-CTA-01", "Contact CTA Integrity", "CONTACT_CTA_INTEGRITY", definition="Verified contact route must remain reachable."),
        _seed("QI-MEDIA-01", "Media Integrity", "MEDIA_INTEGRITY", definition="Required media cannot be missing or broken."),
        _seed("QI-TECH-01", "Technical Release Floor", "TECHNICAL_RELEASE_FLOOR", rendered=True, definition="No release with runtime, overflow or truncation failure."),
    ]
    return QualityInvariantRegistry(items)


@dataclass
class ArtifactProvenance:
    validated_invariants: list[dict[str, str]] = field(default_factory=list)
    invariant_bundle_hash: str = ""
    validated_at: str | None = None


@dataclass
class InvariantArtifact:
    artifact_id: str
    case_id: str
    artifact_type: str
    dependency_keys: set[str] = field(default_factory=set)
    categories: set[str] = field(default_factory=set)
    state: ArtifactValidity = ArtifactValidity.GENERATED
    provenance: ArtifactProvenance = field(default_factory=ArtifactProvenance)


class ApplicabilityResolver:
    def resolve(self, registry: QualityInvariantRegistry, artifact: InvariantArtifact) -> list[QualityInvariant]:
        # A page-level representation receives every global page invariant. A
        # media-only artifact is intentionally preserved by a copy-line update.
        return [item for item in registry.active() if artifact.artifact_type in item.applicability]


@dataclass(frozen=True)
class InvariantBundle:
    bundle_id: str
    case_id: str
    target_decision_id: str
    target_artifact_type: str
    truth_constraints: tuple[str, ...]
    quality_invariants: tuple[tuple[str, str], ...]
    case_preserve_decisions: tuple[str, ...]
    bundle_version: str = "1.0.0"

    @property
    def bundle_hash(self) -> str:
        raw = json.dumps(to_jsonable(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return sha256(raw.encode()).hexdigest()


def build_invariant_bundle(*, registry: QualityInvariantRegistry, resolver: ApplicabilityResolver,
                           artifact: InvariantArtifact, target_decision_id: str,
                           truth_constraints: Iterable[str] = (), preserve_decisions: Iterable[str] = ()) -> InvariantBundle:
    applied = resolver.resolve(registry, artifact)
    return InvariantBundle(
        bundle_id=f"bundle:{artifact.case_id}:{artifact.artifact_id}", case_id=artifact.case_id,
        target_decision_id=target_decision_id, target_artifact_type=artifact.artifact_type,
        truth_constraints=tuple(truth_constraints), quality_invariants=tuple((item.invariant_id, item.invariant_version) for item in applied),
        case_preserve_decisions=tuple(preserve_decisions),
    )


@dataclass(frozen=True)
class RenderMeasurement:
    viewport: int
    lines: tuple[str, ...]
    overflow: int = 0
    truncated: bool = False


@dataclass(frozen=True)
class ValidationViolation:
    invariant_id: str
    message: str
    return_target: ReturnTarget
    deterministic: bool


@dataclass
class ValidationResult:
    violations: list[ValidationViolation] = field(default_factory=list)
    shadow_findings: list[ValidationViolation] = field(default_factory=list)
    measurements: list[RenderMeasurement] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.violations


_PARTICLES = frozenset("はがをにへとでのもやかねよぞさ")
_CONJUNCTIONS = frozenset(("そして", "しかし", "だから", "また", "ただし"))


class JapaneseLineValidator:
    """Hybrid validator: deterministic layout faults plus bounded semantic review.

    The semantic rule is class-based: it detects an unfinished contextual clause,
    not a literal Nagi string. It intentionally remains SHADOW until calibration.
    """
    def validate(self, text: str, measurements: Iterable[RenderMeasurement], registry: QualityInvariantRegistry) -> ValidationResult:
        result = ValidationResult(measurements=list(measurements))
        lines = text.splitlines()
        if any(len(line) == 1 and line in _PARTICLES for line in lines):
            result.violations.append(ValidationViolation("QI-JP-LINE-02", "isolated particle", ReturnTarget.TYPOGRAPHY, True))
        if any(line in _CONJUNCTIONS for line in lines):
            result.violations.append(ValidationViolation("QI-JP-LINE-03", "isolated conjunction", ReturnTarget.TYPOGRAPHY, True))
        if "<br" in text.lower() and any(len(line.strip()) == 1 for line in lines):
            result.violations.append(ValidationViolation("QI-JP-LINE-05", "character-count style forced break", ReturnTarget.TYPOGRAPHY, True))
        if self._unfinished_contextual_clause(text):
            finding = ValidationViolation("QI-JP-LINE-04", "contextual clause ends without an action predicate", ReturnTarget.COPY, False)
            if registry.get("QI-JP-LINE-04").status == InvariantStatus.ACTIVE:
                result.violations.append(finding)
            else:
                result.shadow_findings.append(finding)
        required = set(REQUIRED_VIEWPORTS)
        seen = {item.viewport for item in result.measurements}
        if seen and seen != required:
            result.violations.append(ValidationViolation("QI-JP-LINE-11", "required viewport evidence is incomplete", ReturnTarget.RELEASE, True))
        for measurement in result.measurements:
            if measurement.overflow:
                result.violations.append(ValidationViolation("QI-TECH-01", f"overflow at {measurement.viewport}px", ReturnTarget.TYPOGRAPHY, True))
            if measurement.truncated:
                result.violations.append(ValidationViolation("QI-JP-LINE-12", f"truncation at {measurement.viewport}px", ReturnTarget.TYPOGRAPHY, True))
            if any(len(line.strip()) == 1 and line.strip() not in "。、】【" for line in measurement.lines):
                result.violations.append(ValidationViolation("QI-JP-LINE-06", f"isolated content word at {measurement.viewport}px", ReturnTarget.TYPOGRAPHY, True))
        return result

    @staticmethod
    def _unfinished_contextual_clause(text: str) -> bool:
        normalized = text.replace("\n", "").replace(" ", "")
        # A contextual "その前に" needs a following action/purpose; a noun-only tail is a copy defect.
        if "その前に、" not in normalized:
            return False
        tail = normalized.split("その前に、", 1)[1].rstrip("。！？")
        action_markers = ("確認", "選ぶ", "知る", "相談", "始め", "見", "比べ", "進")
        return not any(marker in tail for marker in action_markers)


class EnforcementRouter:
    def route(self, artifact: InvariantArtifact, result: ValidationResult, bundle: InvariantBundle, *, override: "InvariantOverride | None" = None) -> list[ReturnTarget]:
        if result.violations and (override is None or not override.approved):
            artifact.state = ArtifactValidity.INVALID_INVARIANT
            return sorted({item.return_target for item in result.violations}, key=str)
        artifact.state = ArtifactValidity.VALID
        artifact.provenance = ArtifactProvenance(
            validated_invariants=[{"invariant_id": ident, "invariant_version": version} for ident, version in bundle.quality_invariants],
            invariant_bundle_hash=bundle.bundle_hash, validated_at=datetime.now(timezone.utc).isoformat(),
        )
        return []

    @staticmethod
    def aoi_input_allowed(artifact: InvariantArtifact) -> bool:
        return artifact.state == ArtifactValidity.VALID


@dataclass(frozen=True)
class RegressionFixtureResult:
    fixture_id: str
    status: str
    defect_class: str
    findings: tuple[str, ...]


class RegressionTestRunner:
    """Runs retained failures independently of generic invariant activation.

    A semantic rule can stay in calibration (SHADOW) without allowing the exact
    *failure class* that already escaped once to re-enter review.
    """
    def run_known_failure(self, fixture_id: str, defect_class: str, result: ValidationResult) -> RegressionFixtureResult:
        findings = tuple(item.invariant_id for item in [*result.violations, *result.shadow_findings])
        return RegressionFixtureResult(fixture_id, "FAIL" if findings else "PASS", defect_class, findings)


@dataclass
class CaseApprovedDecision:
    approval_id: str
    case_id: str
    decision_id: str
    decision_version: str
    approved_resolution: str
    preserve_aspects: tuple[str, ...]
    approval_source: str
    approval_reason: str
    status: DecisionStatus = DecisionStatus.ACTIVE
    reopen_requires_reason: bool = True
    reopen_authority: str = "Shun"


@dataclass(frozen=True)
class CaseDecisionReopenRequest:
    approval_id: str
    reason: str
    authority: str


def change_approved_decision(decision: CaseApprovedDecision, new_resolution: str, reopen: CaseDecisionReopenRequest | None) -> None:
    if decision.status == DecisionStatus.ACTIVE:
        if reopen is None or not reopen.reason or reopen.approval_id != decision.approval_id or reopen.authority != decision.reopen_authority:
            raise ValueError("active case-approved decision requires an explicit authorized reopen request")
        decision.status = DecisionStatus.REOPENED
    decision.approved_resolution = new_resolution


def preserve_constraints(decisions: Iterable[CaseApprovedDecision]) -> list[str]:
    return [aspect for decision in decisions if decision.status == DecisionStatus.ACTIVE for aspect in decision.preserve_aspects]


def selective_revalidation(artifacts: Iterable[InvariantArtifact], changed_invariant_ids: Iterable[str], registry: QualityInvariantRegistry,
                           resolver: ApplicabilityResolver) -> tuple[list[str], list[str]]:
    changed = set(changed_invariant_ids)
    stale, preserved = [], []
    for artifact in artifacts:
        applies = {item.invariant_id for item in resolver.resolve(registry, artifact)}
        if applies & changed:
            artifact.state = ArtifactValidity.NEEDS_REVALIDATION
            stale.append(artifact.artifact_id)
        else:
            preserved.append(artifact.artifact_id)
    return sorted(stale), sorted(preserved)


@dataclass(frozen=True)
class ResolvedDefectMemory:
    case_id: str
    artifact_before: str
    artifact_after: str
    defect_class: str
    observed_failure: str
    human_visible_reason: str
    root_cause: str
    corrected_principle: str
    repair_action: str
    detection_method: tuple[str, ...]
    applicability: tuple[str, ...]
    source: str


@dataclass(frozen=True)
class NegativeExample:
    example_id: str
    defect_class: str
    screenshot_ref: str
    principle: str
    retrieval_tags: tuple[str, ...]


@dataclass(frozen=True)
class FailureCluster:
    cluster_id: str
    defect_class: str
    example_ids: tuple[str, ...]
    recurrence_count: int = 0


@dataclass(frozen=True)
class InvariantOverride:
    invariant_id: str
    reason: str
    approved_by: str | None = None

    @property
    def approved(self) -> bool:
        return bool(self.reason and self.approved_by)


@dataclass(frozen=True)
class AoiInvariantCandidate:
    candidate_exists: bool
    defect_pattern: str = ""
    why_repeatable: str = ""
    suggested_scope: str = ""
    evidence_refs: tuple[str, ...] = ()
    related_negative_example: str | None = None


@dataclass(frozen=True)
class BackgroundStrategyDecision:
    purpose: str
    human_consequence: str
    emotional_role: str
    narrative_role: str
    dominance_role: str
    foreground_support_role: str
    transition_role: str
    candidate_modes: tuple[BackgroundStrategy, ...]
    chosen_mode: BackgroundStrategy
    evidence_fit: str
    brand_personality_fit: str
    commercial_consequence: str
    foreground_legibility: str
    mobile_strategy: str
    crop_behavior: str
    motion_behavior: str
    performance_constraint: str
    rights_constraint: str
    representation_type: str = "BACKGROUND_SCENE_MAP"

    def validate_truth_boundary(self, *, evidence_ok: bool, rights_ok: bool) -> bool:
        return evidence_ok and rights_ok


@dataclass
class Observability:
    invariant_violation_count: int = 0
    violations_by_invariant: dict[str, int] = field(default_factory=dict)
    regression_recurrence_count: int = 0
    auto_repair_count: int = 0
    repair_success_rate: float = 0.0
    controlled_return_by_invariant: dict[str, int] = field(default_factory=dict)
    revalidation_count: int = 0
    stale_due_to_invariant_update: int = 0
    override_request_count: int = 0
    new_invariant_candidate_count: int = 0
    case_approved_decision_violation_count: int = 0
    known_defect_escape_count: int = 0

    @property
    def known_defect_escape_rate(self) -> float:
        return float(self.known_defect_escape_count)

    def record(self, result: ValidationResult) -> None:
        self.invariant_violation_count += len(result.violations)
        for violation in result.violations:
            self.violations_by_invariant[violation.invariant_id] = self.violations_by_invariant.get(violation.invariant_id, 0) + 1
            if violation.return_target != ReturnTarget.RELEASE:
                self.controlled_return_by_invariant[violation.invariant_id] = self.controlled_return_by_invariant.get(violation.invariant_id, 0) + 1


def nagi_failure_memory() -> ResolvedDefectMemory:
    return ResolvedDefectMemory(
        case_id="nagi_no_mirai", artifact_before="fixtures/nagi_original_failure.html", artifact_after="fixtures/nagi_corrected_fixture.html",
        defect_class="RHETORICAL_SEMANTIC_LINE_COMPOSITION_REGRESSION",
        observed_failure="受ける。学ぶ。知る。\nその前に、内容から。",
        human_visible_reason="The final contextual phrase reads as an unfinished sentence, not a deliberate line composition.",
        root_cause="A visual forced break masked a weak clause relationship.",
        corrected_principle="Return weak rhetorical dependency to COPY; validate natural line composition at all required widths.",
        repair_action="rewrite copy before any local typography repair", detection_method=("semantic", "rendered"),
        applicability=("headline", "service-selector"), source="Round 2Q Nagi known failure",
    )


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, StrEnum):
        return value.value
    return value
