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


def _evidence_safety_gate(spec: Mapping) -> GateResult:
    decision = evaluate_evidence_selection(
        spec.get("conversion_goal", ""),
        spec.get("primary_objections", []),
        spec.get("evidence_ledger", []),
        requested_claims=spec.get("requested_claims", []),
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
    evidence_safety=None,
):
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
    if evidence_safety is not None:
        if not isinstance(evidence_safety, Mapping):
            results.append(GateResult(
                gate="EvidenceSafetyGate",
                status="FAIL",
                message="Safety input must be a JSON object.",
                details={"safety_status": "INVALID_INPUT"},
            ))
        else:
            results.append(_evidence_safety_gate(evidence_safety))
    return PipelineReport(
        company_name=profile.company_name,
        primary_authority=primary,
        results=results,
    )
