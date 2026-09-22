from __future__ import annotations

import pytest

from lp_engine.quality_invariants import (
    AoiInvariantCandidate, ApplicabilityResolver, ArtifactValidity, BackgroundStrategy,
    BackgroundStrategyDecision, CaseApprovedDecision, CaseDecisionReopenRequest,
    DecisionStatus, EnforcementRouter, InvariantArtifact, InvariantOverride,
    InvariantStatus, JapaneseLineValidator, Observability, RegressionTestRunner, RenderMeasurement,
    ReturnTarget, build_invariant_bundle, change_approved_decision, nagi_failure_memory,
    preserve_constraints, seeded_registry, selective_revalidation,
)


def measurements(*, bad: bool = False) -> list[RenderMeasurement]:
    return [RenderMeasurement(width, ("気になるサービスを", "確認できます。"), overflow=1 if bad and width == 390 else 0) for width in (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)]


def bundle_for(artifact: InvariantArtifact):
    registry = seeded_registry()
    return registry, build_invariant_bundle(registry=registry, resolver=ApplicabilityResolver(), artifact=artifact, target_decision_id="copy")


def test_d01_creative_thesis_change_preserves_japanese_invariants() -> None:
    artifact = InvariantArtifact("hero", "nagi", "page", dependency_keys={"thesis"})
    registry, bundle = bundle_for(artifact)
    assert "QI-JP-LINE-02" in dict(bundle.quality_invariants)
    assert "QI-JP-LINE-02" in dict(build_invariant_bundle(registry=registry, resolver=ApplicabilityResolver(), artifact=artifact, target_decision_id="revised-thesis").quality_invariants)


def test_d02_regenerated_headline_is_not_valid_without_validation() -> None:
    assert InvariantArtifact("headline", "nagi", "page").state == ArtifactValidity.GENERATED


def test_d03_particle_orphan_cannot_flow_downstream() -> None:
    artifact = InvariantArtifact("headline", "nagi", "page")
    registry, bundle = bundle_for(artifact)
    result = JapaneseLineValidator().validate("相談する\nに", measurements(), registry)
    targets = EnforcementRouter().route(artifact, result, bundle)
    assert ReturnTarget.TYPOGRAPHY in targets
    assert artifact.state == ArtifactValidity.INVALID_INVARIANT
    assert not EnforcementRouter.aoi_input_allowed(artifact)


def test_d04_case_approved_mobile_hierarchy_survives_unrelated_hero_revision() -> None:
    decision = CaseApprovedDecision("a1", "nagi", "mobile-hierarchy", "1", "selector before ledger", ("selector-before-ledger",), "Shun", "mobile priority")
    assert preserve_constraints([decision]) == ["selector-before-ledger"]


def test_d05_approved_decision_requires_explicit_reopen() -> None:
    decision = CaseApprovedDecision("a1", "nagi", "mobile", "1", "a", ("a",), "Shun", "reason")
    with pytest.raises(ValueError, match="explicit authorized reopen"):
        change_approved_decision(decision, "b", None)
    change_approved_decision(decision, "b", CaseDecisionReopenRequest("a1", "new evidence", "Shun"))
    assert decision.status == DecisionStatus.REOPENED and decision.approved_resolution == "b"


def test_d06_global_update_stales_only_applicable_artifact() -> None:
    registry = seeded_registry()
    resolver = ApplicabilityResolver()
    page = InvariantArtifact("page", "nagi", "page", state=ArtifactValidity.VALID)
    media = InvariantArtifact("media", "nagi", "media-only", state=ArtifactValidity.VALID)
    stale, preserved = selective_revalidation([page, media], ["QI-JP-LINE-02"], registry, resolver)
    assert stale == ["page"] and preserved == ["media"] and page.state == ArtifactValidity.NEEDS_REVALIDATION


def test_d07_unrelated_media_is_not_regenerated_for_invariant_update() -> None:
    registry = seeded_registry(); resolver = ApplicabilityResolver()
    media = InvariantArtifact("media", "nagi", "media-only", state=ArtifactValidity.VALID)
    stale, _ = selective_revalidation([media], ["QI-JP-LINE-02"], registry, resolver)
    assert stale == [] and media.state == ArtifactValidity.VALID


def test_d08_aoi_schema_can_store_candidate() -> None:
    candidate = AoiInvariantCandidate(True, "touch context missing", "repeats", "CATEGORY", ("capture.png",), "negative:1")
    assert candidate.candidate_exists and candidate.related_negative_example == "negative:1"


def test_d09_aoi_candidate_does_not_activate_registry_rule() -> None:
    registry = seeded_registry()
    assert registry.get("QI-JP-LINE-04").status == InvariantStatus.SHADOW


def test_d10_hard_invariant_cannot_be_bypassed_without_approved_override() -> None:
    artifact = InvariantArtifact("headline", "nagi", "page")
    registry, bundle = bundle_for(artifact)
    result = JapaneseLineValidator().validate("相談する\nに", measurements(), registry)
    router = EnforcementRouter()
    router.route(artifact, result, bundle, override=InvariantOverride("QI-JP-LINE-02", "no authority"))
    assert artifact.state == ArtifactValidity.INVALID_INVARIANT
    router.route(artifact, result, bundle, override=InvariantOverride("QI-JP-LINE-02", "documented exception", "Shun"))
    assert artifact.state == ArtifactValidity.VALID


def test_d11_nagi_known_failure_is_detected_as_failure_class_not_literal() -> None:
    registry = seeded_registry()
    result = JapaneseLineValidator().validate("受ける。学ぶ。知る。\nその前に、内容から。", measurements(), registry)
    assert not result.violations and [item.invariant_id for item in result.shadow_findings] == ["QI-JP-LINE-04"]
    fixture = RegressionTestRunner().run_known_failure("nagi-line-001", "RHETORICAL_SEMANTIC_LINE_COMPOSITION_REGRESSION", result)
    assert fixture.status == "FAIL" and fixture.findings == ("QI-JP-LINE-04",)
    memory = nagi_failure_memory()
    assert memory.defect_class == "RHETORICAL_SEMANTIC_LINE_COMPOSITION_REGRESSION"


def test_d12_corrected_fixture_passes_all_nine_viewports_before_release() -> None:
    artifact = InvariantArtifact("corrected", "nagi", "page")
    registry, bundle = bundle_for(artifact)
    result = JapaneseLineValidator().validate("受ける。学ぶ。知りたいことを、\n相談する前に確認できます。", measurements(), registry)
    EnforcementRouter().route(artifact, result, bundle)
    assert result.passed and artifact.state == ArtifactValidity.VALID and len(result.measurements) == 9


def test_d13_background_schema_cannot_bypass_evidence_or_rights() -> None:
    strategy = BackgroundStrategyDecision("context", "understand", "support", "pace", "support", "legible", "cut", (BackgroundStrategy.NONE, BackgroundStrategy.PHOTOGRAPHIC), BackgroundStrategy.PHOTOGRAPHIC, "pending", "fit", "clarity", "required", "mobile crop", "none", "fast", "fast", "rights required")
    assert strategy.representation_type == "BACKGROUND_SCENE_MAP"
    assert not strategy.validate_truth_boundary(evidence_ok=False, rights_ok=True)
    assert not strategy.validate_truth_boundary(evidence_ok=True, rights_ok=False)


def test_d14_known_defect_cannot_reach_aoi() -> None:
    artifact = InvariantArtifact("bad", "nagi", "page")
    registry, bundle = bundle_for(artifact)
    result = JapaneseLineValidator().validate("見積\nを", measurements(), registry)
    EnforcementRouter().route(artifact, result, bundle)
    assert not EnforcementRouter.aoi_input_allowed(artifact)


def test_d15_recurring_reminder_is_caught_before_shun() -> None:
    registry = seeded_registry()
    result = JapaneseLineValidator().validate("確認\nを", measurements(), registry)
    metrics = Observability(); metrics.record(result)
    assert metrics.violations_by_invariant["QI-JP-LINE-02"] == 1


def test_d16_local_line_repair_does_not_stale_unrelated_section() -> None:
    registry = seeded_registry(); resolver = ApplicabilityResolver()
    local = InvariantArtifact("selector", "nagi", "page", dependency_keys={"selector.copy"}, state=ArtifactValidity.VALID)
    unrelated = InvariantArtifact("faq", "nagi", "media-only", dependency_keys={"faq.copy"}, state=ArtifactValidity.VALID)
    stale, preserved = selective_revalidation([local, unrelated], ["QI-JP-LINE-02"], registry, resolver)
    assert stale == ["selector"] and preserved == ["faq"]


def test_d17_bad_copy_cannot_pass_as_css_reflow() -> None:
    registry = seeded_registry()
    result = JapaneseLineValidator().validate("受ける。学ぶ。知る。\nその前に、内容から。", measurements(), registry)
    assert result.shadow_findings[0].return_target == ReturnTarget.COPY


def test_observability_known_defect_escape_rate_is_zero() -> None:
    metrics = Observability()
    assert metrics.known_defect_escape_rate == 0.0
