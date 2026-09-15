from __future__ import annotations
from .authority import choose_primary_authority
from .models import PipelineReport
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


def run_pipeline(profile, concept, sections, motions, screenshot_scores, gates=None):
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
    return PipelineReport(
        company_name=profile.company_name,
        primary_authority=primary,
        results=results,
    )
