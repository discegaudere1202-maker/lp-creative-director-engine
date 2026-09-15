from __future__ import annotations
from collections.abc import Mapping
from .authority import choose_primary_authority
from .models import GateResult, PipelineReport
from .evidence_safety import evaluate_evidence_selection
from .gates.owner import OwnerSpecificityGate
from .gates.screenshot import ScreenshotPeakGate
from .gates.rhythm import RhythmGate
from .gates.motion import MotionGate
from .gates.text import StaticTextGate
from .gates.authority import AuthorityConsistencyGate


DEFAULT_GATES = [
    AuthorityConsistencyGate(),
    OwnerSpecificityGate(),
    ScreenshotPeakGate(),
    RhythmGate(),
    MotionGate(),
    StaticTextGate(),
]

PIPELINE_MODES = {"production", "research", "test"}


def _evidence_safety_gate(spec: Mapping) -> GateResult:
    decision = evaluate_evidence_selection(
        spec.get("conversion_goal", ""),
        spec.get("primary_objections") or [],
        spec.get("evidence_ledger") or [],
        requested_claims=spec.get("requested_claims") or [],
        require_production_clearance=True,
    )
    status_map = {
        "PASS": "PASS",
        "HEARING_REQUIRED": "HOLD",
        "BLOCKED": "FAIL",
        "INVALID_INPUT": "FAIL",
    }
    return GateResult(
        gate="EvidenceSafetyGate",
        status=status_map.get(decision.safety_status, "FAIL"),
        message=(
            "Verified evidence is eligible."
            if decision.safety_status == "PASS"
            else "Safety evidence selection requires hearing or blocks a requested claim."
        ),
        details=decision.to_dict(),
    )


def run_pipeline(
    profile,
    concept,
    sections,
    motions,
    screenshot_scores,
    gates=None,
    *,
    mode="production",
    evidence_safety=None,
):
    if mode not in PIPELINE_MODES:
        raise ValueError(f"unsupported pipeline mode: {mode}")
    primary, authority_scores = choose_primary_authority(profile)
    ctx = {
        "profile": profile,
        "concept": concept,
        "sections": sections,
        "motions": motions,
        "screenshot_scores": screenshot_scores,
        "primary_authority": primary,
        "authority_scores": authority_scores,
    }
    results = [gate.evaluate(ctx) for gate in (gates or DEFAULT_GATES)]
    safety_decision = None
    if mode == "production" and evidence_safety is None:
        results.append(GateResult(
            gate="EvidenceSafetyGate",
            status="FAIL",
            message="Production mode requires a Safety-layer input.",
            details={
                "safety_status": "INVALID_INPUT",
                "blocked_claims": [],
                "hearing_required": [{
                    "status": "HEARING_REQUIRED",
                    "missing_field": "evidence_safety_input",
                    "priority": "HIGH",
                }],
            },
        ))
    elif evidence_safety is not None:
        if not isinstance(evidence_safety, Mapping):
            results.append(GateResult(
                gate="EvidenceSafetyGate",
                status="FAIL",
                message="Safety input must be a JSON object.",
                details={"safety_status": "INVALID_INPUT"},
            ))
        else:
            safety_result = _evidence_safety_gate(evidence_safety)
            results.append(safety_result)
            safety_decision = safety_result.details
    evidence_manifest = []
    hearing_requirements = []
    blocked_claims = []
    if safety_decision:
        evidence_manifest = [
            {
                "claim": item["claim"],
                "evidence_id": item["evidence_id"],
                "source": item["source"],
                "verification_status": item["verification_status"],
                "rights_status": item["rights_status"],
                "placement_candidates": item["placement_candidates"],
            }
            for item in safety_decision.get("eligible_evidence", [])
        ]
        hearing_requirements = safety_decision.get("hearing_required", [])
        blocked_claims = safety_decision.get("blocked_claims", [])
    safety_pass = bool(safety_decision and safety_decision.get("safety_status") == "PASS")
    production_output_allowed = mode == "production" and safety_pass
    return PipelineReport(
        company_name=profile.company_name,
        primary_authority=primary,
        results=results,
        mode=mode,
        production_output_allowed=production_output_allowed,
        evidence_manifest=evidence_manifest,
        hearing_requirements=hearing_requirements,
        blocked_claims=blocked_claims,
    )


def run_production_pipeline(profile, concept, sections, motions, screenshot_scores, **kwargs):
    """Explicit Production entry point; Safety input cannot be omitted."""
    return run_pipeline(
        profile,
        concept,
        sections,
        motions,
        screenshot_scores,
        mode="production",
        **kwargs,
    )
