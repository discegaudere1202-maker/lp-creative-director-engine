from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ExistingSiteBaseline:
    has_site: bool
    visual_design: int = 0
    brand_specificity: int = 0
    authentic_assets: int = 0
    message_clarity: int = 0
    trust_evidence: int = 0
    mobile_ux: int = 0
    conversion_path: int = 0

    @property
    def total(self) -> int:
        return sum([
            self.visual_design,
            self.brand_specificity,
            self.authentic_assets,
            self.message_clarity,
            self.trust_evidence,
            self.mobile_ux,
            self.conversion_path,
        ])


@dataclass
class AssetReality:
    business_asset_strength: int
    accessible_asset_strength: int

    @property
    def classification(self) -> str:
        if self.business_asset_strength >= 7 and self.accessible_asset_strength <= 3:
            return "ACCESS_CONSTRAINT_NOT_ASSET_POOR"
        if self.business_asset_strength <= 3:
            return "ASSET_POOR"
        return "ASSET_AVAILABLE_OR_MODERATE"


@dataclass
class SalesEligibilityResult:
    status: str
    reason: str
    baseline_total: int
    asset_classification: str
    improvement_gaps: list[str]
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_sales_eligibility(
    baseline: ExistingSiteBaseline,
    asset_reality: AssetReality,
    *,
    improvement_gaps: list[str] | None = None,
    explicit_redesign_challenge: bool = False,
) -> SalesEligibilityResult:
    """Pre-creative eligibility gate.

    This gate answers a different question from Creative QA:
    "Should we build a sales sample for this company at all?"

    It deliberately separates:
    - BENCHMARK_ONLY: strong existing site; study it, do not pitch a weaker redesign.
    - SALES_CANDIDATE: no site or clear, specific improvement opportunity.
    - REDESIGN_CHALLENGE: intentionally redesigning a strong site for R&D only.
    - REVIEW: opportunity is not proven enough to spend production effort.
    """
    gaps = [g.strip() for g in (improvement_gaps or []) if g.strip()]
    total = baseline.total
    asset_class = asset_reality.classification

    if not baseline.has_site:
        return SalesEligibilityResult(
            status="SALES_CANDIDATE",
            reason="No existing website baseline. A sales sample can create net-new value.",
            baseline_total=0,
            asset_classification=asset_class,
            improvement_gaps=gaps,
            details={"existing_site_band": "NONE"},
        )

    strong_identity = baseline.brand_specificity >= 7 and baseline.authentic_assets >= 7
    strong_baseline = total >= 49 or (total >= 42 and strong_identity)

    if strong_baseline:
        if explicit_redesign_challenge:
            return SalesEligibilityResult(
                status="REDESIGN_CHALLENGE",
                reason=(
                    "Existing site is already strong. Redesign is allowed only as an explicit R&D "
                    "challenge with a defined baseline, never as an automatic sales prospect."
                ),
                baseline_total=total,
                asset_classification=asset_class,
                improvement_gaps=gaps,
                details={"existing_site_band": "STRONG", "strong_identity": strong_identity},
            )
        return SalesEligibilityResult(
            status="BENCHMARK_ONLY",
            reason=(
                "Existing site already has strong design/brand/authenticity. Study it as a benchmark; "
                "do not generate a sales sample unless a materially better hypothesis is first proven."
            ),
            baseline_total=total,
            asset_classification=asset_class,
            improvement_gaps=gaps,
            details={"existing_site_band": "STRONG", "strong_identity": strong_identity},
        )

    # Existing sites require concrete, named gaps before production starts.
    if len(gaps) >= 2:
        return SalesEligibilityResult(
            status="SALES_CANDIDATE",
            reason="Existing site has at least two concrete improvement gaps and is eligible for a sales sample.",
            baseline_total=total,
            asset_classification=asset_class,
            improvement_gaps=gaps,
            details={"existing_site_band": "WEAK_OR_MODERATE"},
        )

    return SalesEligibilityResult(
        status="REVIEW",
        reason=(
            "An existing site is present, but the value of redesign has not been proven. "
            "Identify at least two concrete customer/business gaps before production."
        ),
        baseline_total=total,
        asset_classification=asset_class,
        improvement_gaps=gaps,
        details={"existing_site_band": "WEAK_OR_MODERATE"},
    )
