from __future__ import annotations

import pytest

from lp_engine.adaptive_authored_resolution import (
    AoiHumanRealityReview, ArtifactState, CritiqueAction, CritiqueIssue,
    DecisionMode, DecisionState, DependencyManifest, FinalCraftResult,
    FloorQAResult, MobileResolution, RenderPreflightResult, RepresentationArtifact,
    ReviewState, SelectionArgument, build_revision_brief,
    aoi_direct_prompt_allowed, invalidate_artifacts, mobile_is_complete,
    open_decision, route_critique_to_designer, sales_readiness_blockers,
    select_candidate, update_aoi_after_fix,
)


def test_01_resolved_cta_is_direct_and_not_rebranched_by_hero() -> None:
    cta = open_decision("CTA", "Where can the customer contact?", [{"id": "verified-instagram", "proposition": "Instagram @happyfuture_02"}], ["truth.contact"])
    assert cta.mode == DecisionMode.DIRECT
    assert cta.state == DecisionState.RESOLVED
    assert cta.selected_candidate_id is not None


def test_02_thesis_change_stales_only_dependent_artifacts() -> None:
    manifest = DependencyManifest()
    manifest.register("hero", ["thesis", "hero-layout"])
    manifest.register("faq", ["faq-copy"])
    artifacts = {key: RepresentationArtifact(key) for key in ("hero", "faq")}
    stale, preserved = invalidate_artifacts(manifest, artifacts, ["thesis"])
    assert stale == ["hero"] and preserved == ["faq"]
    assert artifacts["hero"].state == ArtifactState.STALE
    assert artifacts["faq"].state == ArtifactState.CURRENT


def test_03_motion_without_a_creative_question_is_not_opened() -> None:
    motion = open_decision("MOTION", "", [])
    assert motion.mode == DecisionMode.NONE and motion.state == DecisionState.NONE


def test_04_visual_variations_of_same_hypothesis_are_not_a_branch() -> None:
    with pytest.raises(ValueError, match="different hypotheses"):
        open_decision("HERO", "How should services be understood?", [
            {"id": "service-choice", "proposition": "image left"},
            {"id": "service-choice", "proposition": "image right"},
        ])


def test_05_selected_decision_requires_selection_argument() -> None:
    decision = open_decision("THESIS", "What does the first screen resolve?", [
        {"id": "experience-first", "proposition": "Experience first"},
        {"id": "choice-first", "proposition": "Choose before contact"},
    ])
    with pytest.raises(ValueError, match="SelectionArgument"):
        select_candidate(decision, decision.candidate_ids[1], None)
    argument = SelectionArgument("arg:thesis", chosen_candidate_id=decision.candidate_ids[1], decisive_reason="Nagi has three distinct service modes.")
    select_candidate(decision, decision.candidate_ids[1], argument)
    assert decision.state == DecisionState.SELECTED
    assert decision.selection_argument_id == argument.entity_id


def test_06_critique_cannot_return_directly_to_designer() -> None:
    issue = CritiqueIssue("issue:1", action=CritiqueAction.RETHINK, root_decision="INFORMATION", why="Service intent is not visible early.", return_target="INFORMATION", required_representation="SCENE_MAP")
    with pytest.raises(ValueError, match="Revision Planner"):
        route_critique_to_designer(issue, None)
    brief = build_revision_brief(issue)
    route_critique_to_designer(issue, brief)
    assert brief.return_target == "INFORMATION"


def test_07_aoi_target_hint_allowed_but_authorial_instruction_rejected() -> None:
    assert aoi_direct_prompt_allowed("In the first viewport, service modes are difficult to distinguish.")
    assert not aoi_direct_prompt_allowed("Make it more premium and rewrite the thesis.")


def test_08_technical_responsive_only_does_not_complete_mobile_direction() -> None:
    mobile = MobileResolution("mobile", representative_scenes=["entry"], mobile_artifact_ids=["m1"], technical_responsive_only=True)
    assert not mobile_is_complete(mobile)
    mobile.technical_responsive_only = False
    mobile.authored_complete = True
    assert mobile_is_complete(mobile)


def test_09_aoi_sales_ready_alone_does_not_release() -> None:
    review = AoiHumanRealityReview("aoi", candidate_version="v1", state=ReviewState.SALES_READY)
    blockers = sales_readiness_blockers(craft=None, preflight=None, review=review, floor=None, decisions_current=True, stale_required_artifacts=[], active_escalation=False, dependencies_valid=True, public_candidate_version="v1")
    assert {"final_craft_not_current", "render_preflight_not_current_pass", "floor_qa_not_current_pass"} <= set(blockers)


def test_10_floor_pass_alone_does_not_release() -> None:
    floor = FloorQAResult("floor", candidate_version="v1", passed=True)
    blockers = sales_readiness_blockers(craft=None, preflight=None, review=None, floor=floor, decisions_current=True, stale_required_artifacts=[], active_escalation=False, dependencies_valid=True, public_candidate_version="v1")
    assert "aoi_review_not_current_sales_ready" in blockers
    assert "final_craft_not_current" in blockers


def test_11_stale_required_artifact_blocks_release_even_when_other_gates_pass() -> None:
    craft = FinalCraftResult("craft", candidate_version="v1")
    preflight = RenderPreflightResult("preflight", candidate_version="v1", passed=True)
    review = AoiHumanRealityReview("aoi", candidate_version="v1", state=ReviewState.SALES_READY)
    floor = FloorQAResult("floor", candidate_version="v1", passed=True)
    blockers = sales_readiness_blockers(craft=craft, preflight=preflight, review=review, floor=floor, decisions_current=True, stale_required_artifacts=["hero"], active_escalation=False, dependencies_valid=True, public_candidate_version="v1")
    assert blockers == ["stale_required_artifact"]


def test_12_floor_visual_fix_stales_aoi_review() -> None:
    review = AoiHumanRealityReview("aoi", visual_dependency_keys=["hero.crop", "mobile.layout"])
    assert update_aoi_after_fix(review, ["hero.crop"])
    assert review.state == ReviewState.STALE


def test_13_nonvisual_fix_preserves_aoi_review() -> None:
    review = AoiHumanRealityReview("aoi", state=ReviewState.SALES_READY, visual_dependency_keys=["hero.crop", "copy.visible"])
    assert not update_aoi_after_fix(review, ["event.logging"])
    assert review.state == ReviewState.SALES_READY


def test_14_controlled_return_preserves_unaffected_artifacts() -> None:
    manifest = DependencyManifest()
    manifest.register("hero-composition", ["thesis", "hero.crop"])
    manifest.register("school-scene", ["school-flow"])
    manifest.register("healing-scene", ["healing-copy"])
    artifacts = {key: RepresentationArtifact(key) for key in manifest.artifacts}
    stale, preserved = invalidate_artifacts(manifest, artifacts, ["hero.crop"])
    assert stale == ["hero-composition"]
    assert preserved == ["healing-scene", "school-scene"]
    assert all(artifacts[key].state == ArtifactState.CURRENT for key in preserved)
