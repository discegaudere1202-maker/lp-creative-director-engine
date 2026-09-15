from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Fact:
    key: str
    value: str
    source: str = ""
    confidence: str = "confirmed"


@dataclass
class CompanyProfile:
    company_name: str
    industry: str
    facts: list[Fact] = field(default_factory=list)
    has_owner_photos: bool = False
    has_place_photos: bool = False
    has_material_photos: bool = False
    has_product_behavior: bool = False
    has_strong_numeric_evidence: bool = False
    has_complex_documents_or_rules: bool = False
    has_distinct_founder_voice: bool = False


@dataclass
class CreativeConcept:
    name: str
    insight: str
    big_idea: str
    visual_authority: str
    business_verb: str
    owner_truth_keys: list[str] = field(default_factory=list)


@dataclass
class SectionSpec:
    id: str
    mode: str
    authority: str
    energy: int
    density: int
    motion: int
    quiet: bool = False
    screenshot_peak: bool = False
    copy: list[str] = field(default_factory=list)


@dataclass
class MotionSpec:
    id: str
    kind: str
    duration_ms: int
    stagger_ms: int = 0
    child_count: int = 1
    blocking: bool = False
    infinite: bool = False
    semantic_reason: str = ""


@dataclass
class ScreenshotScore:
    frame_id: str
    distinctness: int
    owner_specificity: int
    immediate_read: int
    visual_tension: int
    craft_detail: int
    share_impulse: int

    @property
    def total(self) -> int:
        return (
            self.distinctness
            + self.owner_specificity
            + self.immediate_read
            + self.visual_tension
            + self.craft_detail
            + self.share_impulse
        )


@dataclass
class GateResult:
    gate: str
    status: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineReport:
    company_name: str
    primary_authority: str
    results: list[GateResult]
    mode: str = "production"
    production_output_allowed: bool = False
    evidence_manifest: list[dict[str, Any]] = field(default_factory=list)
    hearing_requirements: list[dict[str, Any]] = field(default_factory=list)
    blocked_claims: list[dict[str, Any]] = field(default_factory=list)

    @property
    def status(self) -> str:
        statuses = {r.status for r in self.results}
        if "FAIL" in statuses:
            return "FAIL"
        if "HOLD" in statuses:
            return "HOLD"
        return "PASS"

    def to_dict(self) -> dict[str, Any]:
        return {
            "company_name": self.company_name,
            "primary_authority": self.primary_authority,
            "mode": self.mode,
            "status": self.status,
            "production_output_allowed": self.production_output_allowed,
            "evidence_manifest": self.evidence_manifest,
            "hearing_requirements": self.hearing_requirements,
            "blocked_claims": self.blocked_claims,
            "results": [asdict(r) for r in self.results],
        }
