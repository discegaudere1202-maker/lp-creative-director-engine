from __future__ import annotations

import json
from pathlib import Path

import pytest

from lp_engine.nagi_decision_foundation import (
    CASE_ID, CONTRACT_VERSION, build_creative_problems, build_customer_strategy,
    build_nagi_invariant_bundle, build_phase_a, envelope, hypothesis, load_design_intelligence_registry,
    load_fixture, retrieve_design_intelligence, route_low_evidence, strategy_gate,
    validate_envelope, validate_hypothesis,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return load_fixture(ROOT / "fixtures" / "nagi")


def test_envelope_version_refs_and_dependency_manifest_are_canonical():
    item = envelope("TruthSet", "truth-1", {"x": 1}, upstream_refs=["b", "a", "a"], dependencies=["z", "a"])
    validate_envelope(item)
    assert item["schema_version"] == CONTRACT_VERSION
    assert item["case_id"] == CASE_ID
    assert item["upstream_refs"] == ["a", "b"]
    assert item["dependency_manifest"] == ["a", "z"]
    invalid = {**item, "entity_version": 0}
    with pytest.raises(ValueError):
        validate_envelope(invalid)


def test_frozen_truth_hash_is_deterministic_and_baseline_is_fixed():
    loaded = fixture()
    assert loaded["truth_hash"] == fixture()["truth_hash"]
    assert loaded["baseline"]["baseline_type"] == "ROUND_2U_B_CLEAN"
    assert loaded["baseline"]["baseline_head"] == "a4873e9421f5ddce3d84d84fbf27f40b54a84223"
    assert loaded["baseline"]["excluded_candidate"]["promoted"] is False


def test_round3d_invariant_engine_is_reused_with_required_families():
    bundle = build_nagi_invariant_bundle()
    assert bundle["source_contract"] == "AAR-QI-3D-v1.0"
    assert set(bundle["required_families"]) <= {item["family"] for item in bundle["invariants"]}
    assert bundle["technical_release_floor"]["invariant_ids"]


def test_strategy_gate_strong_evidence_can_be_ready():
    assert strategy_gate(required_fields={"persona": "p", "goal": "g"}, material_unknowns=[], safe_hypothesis_refs={}) == "READY"


def test_strategy_gate_explicit_safe_hypotheses_and_uncovered_unknown_block():
    assert strategy_gate(required_fields={"persona": "p", "goal": "g"}, material_unknowns=["price"], safe_hypothesis_refs={"price": "HYP-1"}) == "READY_WITH_EXPLICIT_HYPOTHESES"
    assert strategy_gate(required_fields={"persona": "p", "goal": "g"}, material_unknowns=["process"], safe_hypothesis_refs={}) == "BLOCKED_MATERIAL_UNKNOWN"


def test_unknown_hypothesis_is_not_promoted_and_strategy_trace_exists():
    with pytest.raises(ValueError):
        hypothesis("h", "unknown", status="UNKNOWN", evidence_refs=[], ontology="FACT")
    strategy = build_customer_strategy(fixture())
    assert strategy["gate"] == "READY_WITH_EXPLICIT_HYPOTHESES"
    assert all(item["evidence_refs"] for item in strategy["customer_hypotheses"])
    assert strategy["customer_hypotheses"][0]["status"] == "PLAUSIBLE"
    assert strategy["customer_hypotheses"][1]["status"] == "WEAK"
    assert strategy["conversion_goal"]["destination"] == "@happyfuture_02"


def test_creative_problem_requires_customer_decision_consequence():
    problems = build_creative_problems(build_customer_strategy(fixture()))
    assert len(problems) == 2
    assert all(problem["customer_decision_problem"] and problem["why_creative_resolution_is_needed"] for problem in problems)
    assert {tuple(problem["candidate_decision_types"]) for problem in problems} == {("CHOICE_FIRST",), ("TRUST_FIRST",)}


@pytest.mark.parametrize("unsafe", [
    "use stock person as actual staff", "invent testimonial", "generate factual workflow",
    "add performance metric", "use representative photo as actual premises",
])
def test_low_evidence_fabrication_routes_block(unsafe):
    result = route_low_evidence(desired_effect="trust", required_dependency="proof", available_dependencies=[], unsafe_substitution=unsafe, translation_options=["safe structure"], selected_translation="safe structure")
    assert result["status"] == "NOT_TRANSLATABLE"
    assert result["evidence_safety"] == "BLOCKED_UNSAFE_SUBSTITUTION"
    assert result["selected_translation"] == ""


def test_missing_asset_uses_safe_partial_translation():
    result = route_low_evidence(desired_effect="choose service", required_dependency="staff photo", available_dependencies=["service names"], unsafe_substitution="", translation_options=["service-name comparison"], selected_translation="service-name comparison")
    assert result["status"] == "PARTIALLY_TRANSLATABLE"
    assert result["effect_lost"] is True


def test_creative_hypothesis_rejects_layout_only_and_selected_requires_argument():
    base = {"hypothesis_id":"h", "case_id":CASE_ID, "creative_problem_id":"p", "strategy_basis":["s"], "customer_hypothesis_refs":["c"], "design_intelligence_refs":["d"], "resolution_statement":"Split Hero with a new background", "human_visible_effect":"e", "customer_effect":"c", "persuasion_effect":"p", "conversion_effect":"x", "company_specific_reason":"Nagi has three distinct services", "asset_requirements":[], "evidence_requirements":[], "low_evidence_translation":{}, "quality_invariant_constraints":[], "failure_risks":[], "anti_pattern_risks":[], "representation_plan":[], "state":"PROPOSED"}
    with pytest.raises(ValueError, match="form-only"):
        validate_hypothesis(base)
    selected = {**base, "resolution_statement":"Visitors identify one of three service intents before contacting the verified channel.", "state":"SELECTED"}
    with pytest.raises(ValueError, match="selection argument"):
        validate_hypothesis(selected)


def test_phase_a_emits_machine_artifacts_without_rendering(tmp_path):
    result = build_phase_a(ROOT, tmp_path)
    assert result["phase_a_gate"] == "PASS"
    assert result["creative_rebuild"] == "NOT_STARTED"
    for name in ("01_truth_set.json", "02_invariant_bundle.json", "03_customer_strategy.json", "04_creative_problem.json", "05_design_intelligence.json", "06_low_evidence_translation.json", "07_creative_hypothesis.json", "phase_a_summary.md", "phase_a_result.json", "baseline_manifest.json"):
        assert (tmp_path / name).is_file()
    entities = json.loads((tmp_path / "canonical_entities.json").read_text(encoding="utf-8"))
    assert entities["entity_count"] >= 15
    assert len({item["entity_id"] for item in entities["entities"]}) == entities["entity_count"]
    assert {item["entity_type"] for item in entities["entities"]} >= {"ProjectCase", "TruthSet", "InvariantBundle", "CustomerEvidenceBoard", "DecisionPersona", "CustomerHypothesis", "CustomerTension", "PersuasionArchitecture", "ConversionGoal", "ConversionPath", "CompanySpecificInsight", "CreativeProblem", "DesignIntelligenceResult", "LowEvidenceTranslationPlan", "CreativeHypothesis"}
    hypotheses = json.loads((tmp_path / "07_creative_hypothesis.json").read_text(encoding="utf-8"))["payload"]["hypotheses"]
    assert len(hypotheses) >= 2 and all(item["state"] == "PROPOSED" for item in hypotheses)
    assert json.loads((tmp_path / "03_customer_strategy.json").read_text(encoding="utf-8"))["payload"]["gate"] == "READY_WITH_EXPLICIT_HYPOTHESES"


def test_t1_nagi_retrieval_uses_round3f_b_registry():
    registry = load_design_intelligence_registry(ROOT / "registries/design_intelligence/round3f_b_core_v1.json")
    assert registry["registry_id"] == "round3f_b_core_v1"
    assert registry["source_contract"] == "AAR-PDI-3FB-v1.0"
    assert registry["freeze_contract"] == CONTRACT_VERSION


def test_t2_retrieved_learning_ids_resolve_to_registry_records():
    path = ROOT / "registries/design_intelligence/round3f_b_core_v1.json"
    registry = load_design_intelligence_registry(path)
    problem = build_creative_problems(build_customer_strategy(fixture()))[0]
    result = retrieve_design_intelligence(path, problem)
    known = {row["learning_id"] for row in registry["learning_records"]}
    assert result["retrieved_learning_ids"]
    assert set(result["retrieved_learning_ids"]) <= known
    assert all(row["learning_id"] in known for row in result["results"])


def test_t3_benchmark_names_are_not_creative_resolution_answers():
    path = ROOT / "registries/design_intelligence/round3f_b_core_v1.json"
    problem = build_creative_problems(build_customer_strategy(fixture()))[0]
    result = retrieve_design_intelligence(path, problem)
    assert result["benchmark_names_are_provenance_only"] is True
    assert all(row["learning"] and row["learning_id"] for row in result["results"])
    assert not any("風" in row["learning"] or "っぽく" in row["learning"] for row in result["results"])


def test_t4_legacy_frame_registry_cannot_satisfy_phase_a_retrieval():
    problem = build_creative_problems(build_customer_strategy(fixture()))[0]
    with pytest.raises(ValueError, match="metadata is incomplete|source contract mismatch"):
        retrieve_design_intelligence(ROOT / "config/frame_registry_v1.json", problem)


def test_t5_creative_hypotheses_trace_to_round3f_learning_records(tmp_path):
    result = build_phase_a(ROOT, tmp_path)
    design = json.loads((tmp_path / "05_design_intelligence.json").read_text(encoding="utf-8"))["payload"]
    hypotheses = json.loads((tmp_path / "07_creative_hypothesis.json").read_text(encoding="utf-8"))["payload"]["hypotheses"]
    known = {item["learning_id"] for group in design["results"] for item in group["results"]}
    assert result["phase_a_gate"] == "PASS"
    assert design["design_intelligence_source"] == "round3f_b_core_v1"
    assert all(item["design_intelligence_refs"] for item in hypotheses)
    assert all(set(item["design_intelligence_refs"]) <= known for item in hypotheses)


def test_t6_low_evidence_translation_is_linked_to_retrieved_learning(tmp_path):
    build_phase_a(ROOT, tmp_path)
    design = json.loads((tmp_path / "05_design_intelligence.json").read_text(encoding="utf-8"))["payload"]["results"]
    translations = json.loads((tmp_path / "06_low_evidence_translation.json").read_text(encoding="utf-8"))["payload"]["translations"]
    for translation, retrieved in zip(translations, design):
        assert translation["design_intelligence_refs"] == retrieved["retrieved_learning_ids"]
        assert translation["desired_effect"] == retrieved["results"][0]["human_visible_effect"]
