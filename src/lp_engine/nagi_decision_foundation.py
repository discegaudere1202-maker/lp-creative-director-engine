"""Round 3I-A: file-first Nagi decision foundation (no page rendering)."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Iterable

from lp_engine.quality_invariants import (
    ApplicabilityResolver, InvariantArtifact, build_invariant_bundle,
    seeded_registry, to_jsonable,
)

CONTRACT_VERSION = "AAR-IPCF-3HF-v1.0"
CASE_ID = "nagi_no_mirai"
TRUTH_STATES = {"SUPPORTED", "PLAUSIBLE", "WEAK", "UNKNOWN", "CONTRADICTED"}
STRATEGY_GATES = {"READY", "READY_WITH_EXPLICIT_HYPOTHESES", "BLOCKED_MATERIAL_UNKNOWN"}
HYPOTHESIS_STATES = {"PROPOSED", "EXPLORING", "SELECTED", "REJECTED", "MERGED"}
TRANSLATION_STATES = {"TRANSLATABLE", "PARTIALLY_TRANSLATABLE", "NOT_TRANSLATABLE"}
ENTITY_TYPES = {
    "ProjectCase", "TruthSet", "InvariantBundle", "CustomerEvidenceBoard", "DecisionPersona",
    "CustomerHypothesis", "CustomerTension", "PersuasionArchitecture", "ConversionGoal",
    "ConversionPath", "CompanySpecificInsight", "CreativeProblem", "DesignIntelligenceResult",
    "LowEvidenceTranslationPlan", "CreativeHypothesis",
}
FORM_ONLY = re.compile(r"\b(hero|split hero|background|layout|grid|card|typography|css|gradient)\b", re.I)


def canonical_hash(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def envelope(entity_type: str, entity_id: str, payload: dict[str, Any], *, upstream_refs: Iterable[str] = (), dependencies: Iterable[str] = (), version: int = 1, status: str = "DRAFT") -> dict[str, Any]:
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"unknown canonical entity type: {entity_type}")
    now = datetime.now(timezone.utc).isoformat()
    result = {
        "entity_type": entity_type, "entity_id": entity_id, "case_id": CASE_ID,
        "schema_version": CONTRACT_VERSION, "entity_version": version, "status": status,
        "upstream_refs": sorted(set(upstream_refs)), "dependency_manifest": sorted(set(dependencies)),
        "created_at": now, "updated_at": now, "payload": payload,
    }
    validate_envelope(result)
    return result


def validate_envelope(value: dict[str, Any]) -> None:
    required = {"entity_type", "entity_id", "case_id", "schema_version", "entity_version", "status", "upstream_refs", "dependency_manifest", "created_at", "updated_at", "payload"}
    if not required <= value.keys():
        raise ValueError(f"missing envelope fields: {sorted(required - value.keys())}")
    if value["entity_type"] not in ENTITY_TYPES or value["case_id"] != CASE_ID:
        raise ValueError("entity type or case_id is outside this contract")
    if not isinstance(value["entity_version"], int) or value["entity_version"] < 1:
        raise ValueError("entity_version must be a positive integer")
    if not isinstance(value["upstream_refs"], list) or not isinstance(value["dependency_manifest"], list):
        raise ValueError("refs and dependencies must be lists")


def load_fixture(root: Path) -> dict[str, Any]:
    truth = json.loads((root / "frozen_truth.json").read_text(encoding="utf-8"))
    unknowns = json.loads((root / "frozen_unknowns.json").read_text(encoding="utf-8"))
    refs = json.loads((root / "frozen_evidence_refs.json").read_text(encoding="utf-8"))
    baseline = json.loads((root / "baseline_manifest.json").read_text(encoding="utf-8"))
    for item in (truth, unknowns, refs):
        if item["truth_boundary_version"] != CONTRACT_VERSION:
            raise ValueError("truth boundary version mismatch")
    canonical_inputs = {"truth": truth, "unknowns": unknowns, "evidence_refs": refs}
    return {"truth": truth, "unknowns": unknowns, "evidence_refs": refs, "baseline": baseline, "truth_hash": canonical_hash(canonical_inputs)}


def build_nagi_invariant_bundle() -> dict[str, Any]:
    registry = seeded_registry()
    artifact = InvariantArtifact("nagi-phase-a", CASE_ID, "page")
    bundle = build_invariant_bundle(
        registry=registry, resolver=ApplicabilityResolver(), artifact=artifact,
        target_decision_id="nagi-phase-a-decision-foundation",
        truth_constraints=("Frozen Nagi truth only", "Unknowns remain unknown"),
        preserve_decisions=("No public proof fabrication", "No unsupported efficacy", "No unverified business details"),
    )
    aliases = {"CONTACT_CTA_INTEGRITY": "CTA_INTEGRITY"}
    applied = []
    for invariant_id, version in bundle.quality_invariants:
        record = registry.get(invariant_id)
        applied.append({"invariant_id": invariant_id, "version": version, "family": aliases.get(record.defect_class, record.defect_class), "status": record.status.value})
    required = {"JAPANESE_LINE_COMPOSITION", "TRUST_INTEGRITY", "EVIDENCE_BOUNDARY", "PUBLIC_OUTPUT_SAFETY", "RESPONSIVE_FLOOR", "CTA_INTEGRITY", "MEDIA_INTEGRITY"}
    present = {item["family"] for item in applied}
    missing = sorted(required - present)
    if missing:
        raise ValueError(f"Round 3D registry lacks required invariant families: {missing}")
    return {
        "schema_version": CONTRACT_VERSION, "case_id": CASE_ID,
        "source_contract": "AAR-QI-3D-v1.0", "bundle_id": bundle.bundle_id,
        "bundle_hash": bundle.bundle_hash, "target_artifact_type": "page",
        "required_families": sorted(required), "invariants": applied, "missing_families": missing,
        "technical_release_floor": {"invariant_ids": [i for i, _ in bundle.quality_invariants if registry.get(i).defect_class == "TECHNICAL_RELEASE_FLOOR"], "source": "existing Round 3D seeded registry"},
        "result": "PASS",
    }


def hypothesis(ref: str, statement: str, *, status: str, evidence_refs: Iterable[str], ontology: str = "HYPOTHESIS", rationale: str = "") -> dict[str, Any]:
    if status not in TRUTH_STATES:
        raise ValueError(f"invalid customer hypothesis state: {status}")
    if status == "UNKNOWN" and ontology != "HYPOTHESIS":
        raise ValueError("UNKNOWN cannot be promoted by ontology relabeling")
    return {"hypothesis_id": ref, "statement": statement, "ontology": ontology, "status": status, "evidence_refs": list(evidence_refs), "rationale": rationale}


def strategy_gate(*, required_fields: dict[str, Any], material_unknowns: list[str], safe_hypothesis_refs: dict[str, str]) -> str:
    missing = [key for key, value in required_fields.items() if value in (None, "", [], {})]
    uncovered = [field for field in material_unknowns if not safe_hypothesis_refs.get(field)]
    if uncovered:
        return "BLOCKED_MATERIAL_UNKNOWN"
    if missing or material_unknowns:
        return "READY_WITH_EXPLICIT_HYPOTHESES"
    return "READY"


def build_customer_strategy(fixtures: dict[str, Any]) -> dict[str, Any]:
    truth = fixtures["truth"]
    services = truth["services"]
    refs = [row["evidence_id"] for row in fixtures["evidence_refs"]["evidence"]]
    hypotheses = [
        hypothesis("CH-NAGI-SERVICE-CHOICE", "来訪者は3つのサービスのうち、自分の目的に近い入口を見つけたい可能性がある。", status="PLAUSIBLE", evidence_refs=["nagi-truth-services"], rationale="複数の異なるサービス区分がFrozen Truthにある。個人の実際の迷いを測定した証拠ではない。"),
        hypothesis("CH-NAGI-CONTACT-CERTAINTY", "相談前に連絡先と相談対象を明確にしたい可能性がある。", status="WEAK", evidence_refs=["nagi-truth-contact", "nagi-truth-services"], rationale="公開連絡先と複数サービスは確認済みだが、予約者の行動・不安データはない。"),
    ]
    persona = {"persona_id": "DP-NAGI-INTENT-SEEKER", "state_before": "3つの提供サービスのうち関心の近いものが未確定、または詳細を確かめてから相談したい状態", "source_ontology": "INFERENCE", "evidence_refs": ["nagi-truth-services", "nagi-truth-contact"], "non_claim": "demographic, acquisition channel, and actual customer behavior are UNKNOWN"}
    tension = {"tension_id": "CT-NAGI-CHOICE-CLARITY", "main_customer_tension": "異なる3サービスのどれが自分の目的に近いかを選ぶ必要がある一方、未確認の詳細情報を断定できない。", "ontology": "INFERENCE", "evidence_refs": ["nagi-truth-services", "nagi-unknowns"]}
    material_unknowns = ["exact prices", "durations", "service process", "staff identity and qualifications", "healing efficacy"]
    safe_refs = {field: "HYP-NAGI-DETAILS-UNKNOWN" for field in material_unknowns}
    required = {"customer_decision_problem": tension["main_customer_tension"], "conversion_goal": "Instagram相談", "company_specific_insight": "3 services + 福岡市 + official SNS @happyfuture_02"}
    gate = strategy_gate(required_fields=required, material_unknowns=material_unknowns, safe_hypothesis_refs=safe_refs)
    strategy = {
        "schema_version": CONTRACT_VERSION, "ontology": ["FACT", "OBSERVATION", "INFERENCE", "HYPOTHESIS"],
        "decision_persona": persona, "customer_hypotheses": hypotheses, "customer_tension": tension,
        "trust_gap": {"statement": "人物・資格・経験・施術の詳細・料金・時間を裏付ける公開EvidenceがこのFreezeに含まれず、Human proofや数値で信頼を補えない。", "ontology": "FACT", "evidence_refs": ["nagi-unknowns"], "unknown_refs": material_unknowns},
        "explicit_unknown_hypothesis": {"hypothesis_id": "HYP-NAGI-DETAILS-UNKNOWN", "statement": "価格・時間・個別プロセス等はこのTruth Boundaryでは未確認であり、顧客向け事実として補わない。", "ontology": "FACT", "status": "UNKNOWN", "evidence_refs": ["nagi-unknowns"]},
        "main_objection": {"statement": "サービス内容や条件を十分に把握できないまま連絡することへのためらいが生じうる。", "status": "WEAK", "ontology": "HYPOTHESIS", "evidence_refs": ["nagi-truth-services", "nagi-unknowns"]},
        "required_belief": "3つのサービスは別々の選択肢であり、関心のあるサービスについて公開された事実の範囲で確認・相談できる。",
        "required_understanding": ["Dry Head Spa＝受ける", "Head Spa School＝学ぶ", "Healing Salon＝ヒーリングを知る", "公式連絡先は @happyfuture_02"],
        "required_feeling": "選択肢と確認済み情報が区別され、未確認事項は未確認のまま示される。",
        "conversion_goal": {"goal_id": "CG-NAGI-INSTAGRAM-CONSULT", "action": "Instagramで関心サービスについて相談する", "destination": truth["public_contact"]["handle"], "ontology": "FACT"},
        "conversion_path": {"path_id": "CP-NAGI-SELECT-TO-INSTAGRAM", "steps": ["3サービスの違いを理解する", "関心の対象を選ぶ", "確認済み情報と未確認範囲を把握する", "@happyfuture_02へ相談する"], "contact_route_refs": ["nagi-truth-contact"]},
        "persuasion_architecture": {"jobs": ["ORIENT", "DISTINGUISH_SERVICES", "STATE_KNOWN_AND_UNKNOWN", "REDUCE_UNSUPPORTED_EXPECTATION", "INVITE_CONTACT"], "evidence_refs": refs},
        "company_specific_insight": {"statement": "なぎのみらいは福岡市で、受ける・学ぶ・ヒーリングを知るという異なる3つのサービス入口を持ち、確認済みの公開連絡先は @happyfuture_02。", "evidence_refs": ["nagi-truth-name", "nagi-truth-location", "nagi-truth-services", "nagi-truth-contact"]},
        "material_unknowns": material_unknowns, "gate": gate,
    }
    if gate not in STRATEGY_GATES:
        raise ValueError("invalid Strategy Gate")
    return strategy


def build_creative_problems(strategy: dict[str, Any]) -> list[dict[str, Any]]:
    base = {
        "problem_id": "CPR-NAGI-SERVICE-DECISION", "case_id": CASE_ID,
        "customer_state_before": strategy["decision_persona"]["state_before"],
        "customer_decision_problem": strategy["customer_tension"]["main_customer_tension"],
        "strategy_refs": ["CT-NAGI-CHOICE-CLARITY", "CG-NAGI-INSTAGRAM-CONSULT"],
        "persuasion_job": "3つのサービスと確認済みの連絡経路を区別し、選択を助ける。",
        "conversion_relevance": "サービス対象が定まればInstagram相談先へ接続できる。行動率向上は未検証。",
        "trust_relevance": "未確認の人物・価格・時間・効果を作らず、事実と不明点を分ける。",
        "company_specific_context": "福岡市 / Dry Head Spa・Head Spa School・Healing Salon / @happyfuture_02",
        "screen_problem": "三つのサービスの相違と、選択後に何を確認・相談できるかが同じDecision Traceで判別可能である必要がある。",
        "why_creative_resolution_is_needed": "分類名だけを並べても、顧客が自分の意図と連絡先を結び付けられる保証がないため。",
        "evidence_constraints": ["Frozen Truth only", "no prices, duration, credentials, reviews, outcomes, or method claims"],
        "asset_constraints": ["staff and premises imagery are unknown; do not substitute stock/generated imagery as proof"],
        "quality_invariant_constraints": ["JAPANESE_LINE_COMPOSITION", "TRUST_INTEGRITY", "EVIDENCE_BOUNDARY", "PUBLIC_OUTPUT_SAFETY", "RESPONSIVE_FLOOR", "CTA_INTEGRITY", "MEDIA_INTEGRITY"],
        "state": "OPEN",
    }
    return [
        {**base, "candidate_decision_types": ["CHOICE_FIRST"], "resolution_logic": "訪問者の目的から3つの別サービスを識別し、その選択を確認済み連絡先へつなぐ。", "creative_problem_id": "CPR-NAGI-CHOICE-FIRST"},
        {**base, "candidate_decision_types": ["TRUST_FIRST"], "resolution_logic": "事実と未確認事項の境界を先に理解できるようにし、その後にサービス対象と相談先を選べるようにする。", "creative_problem_id": "CPR-NAGI-TRUST-FIRST"},
    ]


def load_design_intelligence_registry(registry_path: Path) -> dict[str, Any]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    required_top = {"registry_id", "source_contract", "freeze_contract", "schema_version", "created_for", "learning_records"}
    required_record = {"learning_id", "family", "observed_problem", "decision_principle", "human_visible_effect", "persuasion_effect", "required_conditions", "transferability", "asset_dependency", "low_evidence_translation", "failure_modes", "do_not_reuse_when", "representation_needed", "source_contract", "benchmark_provenance"}
    if not required_top <= registry.keys():
        raise ValueError("Design Intelligence registry metadata is incomplete")
    if registry["registry_id"] != "round3f_b_core_v1" or registry["source_contract"] != "AAR-PDI-3FB-v1.0" or registry["freeze_contract"] != CONTRACT_VERSION:
        raise ValueError("Design Intelligence registry source contract mismatch")
    ids: set[str] = set()
    for row in registry["learning_records"]:
        if not required_record <= row.keys() or row["source_contract"] != "AAR-PDI-3FB-v1.0":
            raise ValueError("Learning record is incomplete or has invalid provenance")
        if row["learning_id"] in ids:
            raise ValueError(f"duplicate Design Intelligence learning_id: {row['learning_id']}")
        if row["transferability"] not in {"PORTABLE", "CONDITIONAL", "CONTEXT_BOUND"}:
            raise ValueError("invalid learning transferability")
        ids.add(row["learning_id"])
    if not registry["learning_records"]:
        raise ValueError("Design Intelligence registry has no learning records")
    return registry


def retrieve_design_intelligence(registry_path: Path, problem: dict[str, Any]) -> dict[str, Any]:
    registry = load_design_intelligence_registry(registry_path)
    records = registry["learning_records"]
    mode = problem["candidate_decision_types"][0]
    families = {
        "CHOICE_FIRST": ["COMPANY_SPECIFICITY", "AUTHORITY", "COMPOSITION_RHYTHM", "MOBILE", "MEDIA"],
        "TRUST_FIRST": ["LOW_EVIDENCE", "AUTHORITY", "LATE_PAGE", "ENDING", "TYPOGRAPHY", "COMPANY_SPECIFICITY"],
    }[mode]
    selected_rows = [row for family in families for row in records if row["family"] == family][:5]
    selected = []
    for row in selected_rows:
        missing = [condition for condition in row["required_conditions"] if any(term in condition.lower() for term in ("proof", "evidence", "verified", "media")) and row["family"] in {"MEDIA", "LATE_PAGE", "BACKGROUND"}]
        selected.append({
            "learning_id": row["learning_id"], "family": row["family"],
            "learning": row["decision_principle"], "observed_problem": row["observed_problem"],
            "why_relevant": f"{mode} addresses Nagi's verified three-service choice and/or its explicit evidence boundary; this principle affects the customer's decision, not merely styling.",
            "human_visible_effect": row["human_visible_effect"], "persuasion_effect": row["persuasion_effect"],
            "required_conditions": row["required_conditions"],
            "conditions_met": ["Frozen Nagi service distinctions", "verified Instagram contact", "unknowns preserved as unknown"],
            "conditions_missing": missing + ["No verified staff, premises, price, duration, or review evidence in the frozen input"],
            "transferability": row["transferability"], "asset_dependency": row["asset_dependency"],
            "low_evidence_translation": row["low_evidence_translation"], "failure_modes": row["failure_modes"],
            "do_not_reuse_when": row["do_not_reuse_when"], "representation_needed": row["representation_needed"],
            "benchmark_provenance": row["benchmark_provenance"],
        })
    selected_ids = {row["learning_id"] for row in selected}
    rejected = [{"learning_id": row["learning_id"], "why_rejected": f"Family {row['family']} is outside the bounded retrieval set for {mode}; not judged universally irrelevant."} for row in records if row["learning_id"] not in selected_ids]
    return {
        "schema_version": CONTRACT_VERSION, "case_id": CASE_ID,
        "design_intelligence_source": registry["registry_id"], "source_contract": registry["source_contract"],
        "registry_version": registry["schema_version"], "problem_ref": problem["creative_problem_id"],
        "decision_logic": mode, "retrieved_learning_ids": [row["learning_id"] for row in selected],
        "results": selected, "why_relevant": [row["why_relevant"] for row in selected],
        "conditions_met": sorted({value for row in selected for value in row["conditions_met"]}),
        "conditions_missing": sorted({value for row in selected for value in row["conditions_missing"]}),
        "low_evidence_translation": [{"learning_id": row["learning_id"], "options": row["low_evidence_translation"]} for row in selected],
        "rejected_learning_ids": [row["learning_id"] for row in rejected], "why_rejected": rejected,
        "status": "PASS" if selected else "NO_MATCHING_REGISTERED_LEARNING", "benchmark_names_are_provenance_only": True,
    }


def route_low_evidence(*, desired_effect: str, required_dependency: str, available_dependencies: Iterable[str], unsafe_substitution: str, translation_options: list[str], selected_translation: str, learning_refs: Iterable[str] = ()) -> dict[str, Any]:
    available = set(available_dependencies)
    missing = [] if required_dependency in available else [required_dependency]
    blocked_terms = ("actual staff", "testimonial", "review", "qualification", "actual premises", "verified process", "factual workflow", "generated workflow", "achievement number", "performance metric", "efficacy")
    unsafe = unsafe_substitution if any(term in unsafe_substitution.lower() for term in blocked_terms) else ""
    if unsafe:
        status = "NOT_TRANSLATABLE"
        effect_preserved = False
        selected_translation = ""
    elif missing:
        status = "PARTIALLY_TRANSLATABLE" if translation_options else "NOT_TRANSLATABLE"
        effect_preserved = False
    else:
        status = "TRANSLATABLE"
        effect_preserved = True
    return {
        "desired_effect": desired_effect, "required_dependency": required_dependency, "design_intelligence_refs": list(learning_refs),
        "missing_dependency": missing, "unsafe_substitution": unsafe or None,
        "translation_options": translation_options, "selected_translation": selected_translation,
        "effect_preserved": effect_preserved, "effect_lost": not effect_preserved,
        "evidence_safety": "BLOCKED_UNSAFE_SUBSTITUTION" if unsafe else "PASS",
        "status": status,
    }


def build_hypotheses(strategy: dict[str, Any], problems: list[dict[str, Any]], intelligence: list[dict[str, Any]], translations: list[dict[str, Any]]) -> dict[str, Any]:
    hypotheses = []
    for index, problem in enumerate(problems):
        intel = intelligence[index]["results"]
        translation = translations[index]
        hypotheses.append({
            "hypothesis_id": f"HYP-NAGI-{problem['candidate_decision_types'][0]}", "case_id": CASE_ID,
            "creative_problem_id": problem["creative_problem_id"],
            "strategy_basis": ["CT-NAGI-CHOICE-CLARITY", "CP-NAGI-SELECT-TO-INSTAGRAM"],
            "customer_hypothesis_refs": [row["hypothesis_id"] for row in strategy["customer_hypotheses"]],
            "design_intelligence_refs": [row["learning_id"] for row in intel],
            "resolution_statement": problem["resolution_logic"],
            "human_visible_effect": "利用者が関心サービスと公開事実/未確認事項を区別できる。",
            "customer_effect": "選択前の混同または相談前の不確かさを減らせる可能性がある。",
            "persuasion_effect": "service orientation and expectation setting; not experimentally validated",
            "conversion_effect": "Instagram相談への経路理解を支援する仮説。成果向上は未測定。",
            "company_specific_reason": "3つの異なる提供サービス、福岡市、確認済み連絡先 @happyfuture_02 を同時に扱うため。",
            "asset_requirements": ["No staff/premises image is assumed; any later asset needs its own provenance."],
            "evidence_requirements": ["frozen_truth.json", "frozen_evidence_refs.json"],
            "low_evidence_translation": translation,
            "quality_invariant_constraints": problem["quality_invariant_constraints"],
            "failure_risks": ["inventing prices, duration, process, credentials, efficacy, reviews, or biography"],
            "anti_pattern_risks": ["layout-only hypothesis", "benchmark-style imitation", "three equal cards without decision rationale"],
            "representation_plan": ["Resolve service distinction", "retain evidence boundary", "carry verified contact route"],
            "state": "PROPOSED",
        })
    return {"schema_version": CONTRACT_VERSION, "case_id": CASE_ID, "hypotheses": hypotheses, "selection_status": "UNRESOLVED", "selection_argument": None}


def validate_hypothesis(item: dict[str, Any]) -> None:
    needed = {"hypothesis_id", "case_id", "creative_problem_id", "strategy_basis", "customer_hypothesis_refs", "design_intelligence_refs", "resolution_statement", "human_visible_effect", "customer_effect", "persuasion_effect", "conversion_effect", "company_specific_reason", "asset_requirements", "evidence_requirements", "low_evidence_translation", "quality_invariant_constraints", "failure_risks", "anti_pattern_risks", "representation_plan", "state"}
    if not needed <= item.keys():
        raise ValueError(f"creative hypothesis fields missing: {sorted(needed - item.keys())}")
    if item["state"] not in HYPOTHESIS_STATES:
        raise ValueError("invalid Creative Hypothesis state")
    if not item["strategy_basis"] or not item["company_specific_reason"]:
        raise ValueError("hypothesis must retain strategy refs and Nagi-specific reason")
    if FORM_ONLY.search(item["resolution_statement"]):
        raise ValueError("form-only layout/visual request is not a Creative Hypothesis")
    if item["state"] == "SELECTED" and not item.get("selection_argument"):
        raise ValueError("SELECTED requires a traceable selection argument")


def build_phase_a(root: Path, out: Path) -> dict[str, Any]:
    fixtures = load_fixture(root / "fixtures" / "nagi")
    strategy = build_customer_strategy(fixtures)
    problems = build_creative_problems(strategy)
    intelligence = [retrieve_design_intelligence(root / "registries" / "design_intelligence" / "round3f_b_core_v1.json", problem) for problem in problems]
    translations = []
    for problem in problems:
        translation = route_low_evidence(
            desired_effect=intelligence[len(translations)]["results"][0]["human_visible_effect"],
            required_dependency="specific staff/process/price evidence",
            available_dependencies=("verified service names", "Fukuoka city", "verified Instagram handle"),
            unsafe_substitution="",
            translation_options=["Use service category names and distinct intent verbs", "State only the verified location/contact and preserve unknown details as unknown"],
            selected_translation="事実であるサービス名・安全なサービス表現・福岡市・@happyfuture_02だけで判断経路を説明し、スタッフ/店舗/プロセス/価格の代替証拠は置かない。",
            learning_refs=intelligence[len(translations)]["retrieved_learning_ids"],
        )
        translations.append(translation)
    hypotheses = build_hypotheses(strategy, problems, intelligence, translations)
    for item in hypotheses["hypotheses"]:
        validate_hypothesis(item)

    invariant_bundle = build_nagi_invariant_bundle()
    truth_set = envelope("TruthSet", "TS-NAGI-FROZEN", {"truth_hash": fixtures["truth_hash"], "truth_boundary_version": CONTRACT_VERSION}, upstream_refs=["fixtures/nagi/frozen_truth.json", "fixtures/nagi/frozen_unknowns.json", "fixtures/nagi/frozen_evidence_refs.json"], dependencies=["truth", "unknowns", "evidence_refs"], status="FROZEN")
    canonical_entities = [
        envelope("ProjectCase", "PC-NAGI-PHASE-A", {"business": fixtures["truth"]["entity"], "location": fixtures["truth"]["location"], "phase": "DECISION_FOUNDATION"}, upstream_refs=["fixtures/nagi/frozen_truth.json"], dependencies=["truth_hash"], status="OPEN"),
        truth_set,
        envelope("InvariantBundle", "IB-NAGI-PHASE-A", invariant_bundle, upstream_refs=["TS-NAGI-FROZEN"], dependencies=["Round3D.registry"], status="APPLIED"),
        envelope("CustomerEvidenceBoard", "CEB-NAGI-PHASE-A", {"evidence_refs": fixtures["evidence_refs"]["evidence"], "frozen_unknowns": fixtures["unknowns"]["frozen_unknowns"]}, upstream_refs=["TS-NAGI-FROZEN"], dependencies=["truth", "evidence_refs"], status="FROZEN"),
        envelope("DecisionPersona", "DP-NAGI-INTENT-SEEKER", strategy["decision_persona"], upstream_refs=["CEB-NAGI-PHASE-A"], dependencies=["service_truth"], status="INFERRED"),
        *[envelope("CustomerHypothesis", row["hypothesis_id"], row, upstream_refs=["CEB-NAGI-PHASE-A"], dependencies=row["evidence_refs"], status=row["status"]) for row in strategy["customer_hypotheses"]],
        envelope("CustomerHypothesis", "HYP-NAGI-DETAILS-UNKNOWN", strategy["explicit_unknown_hypothesis"], upstream_refs=["CEB-NAGI-PHASE-A"], dependencies=["nagi-unknowns"], status="UNKNOWN"),
        envelope("CustomerTension", "CT-NAGI-CHOICE-CLARITY", strategy["customer_tension"], upstream_refs=["DP-NAGI-INTENT-SEEKER", "CEB-NAGI-PHASE-A"], dependencies=["services", "frozen_unknowns"], status="INFERRED"),
        envelope("PersuasionArchitecture", "PA-NAGI-PHASE-A", strategy["persuasion_architecture"], upstream_refs=["CT-NAGI-CHOICE-CLARITY"], dependencies=["strategy_gate"], status=strategy["gate"]),
        envelope("ConversionGoal", "CG-NAGI-INSTAGRAM-CONSULT", strategy["conversion_goal"], upstream_refs=["nagi-truth-contact"], dependencies=["verified_contact"], status="VERIFIED"),
        envelope("ConversionPath", "CP-NAGI-SELECT-TO-INSTAGRAM", strategy["conversion_path"], upstream_refs=["CG-NAGI-INSTAGRAM-CONSULT", "CT-NAGI-CHOICE-CLARITY"], dependencies=["services", "verified_contact"], status="PROPOSED"),
        envelope("CompanySpecificInsight", "CSI-NAGI-THREE-MODES", strategy["company_specific_insight"], upstream_refs=["CEB-NAGI-PHASE-A"], dependencies=["services", "location", "verified_contact"], status="SUPPORTED"),
        *[envelope("CreativeProblem", problem["creative_problem_id"], problem, upstream_refs=["PA-NAGI-PHASE-A", "CT-NAGI-CHOICE-CLARITY"], dependencies=["strategy"], status="OPEN") for problem in problems],
        *[envelope("DesignIntelligenceResult", f"DIR-{item['problem_ref']}", item, upstream_refs=[item["problem_ref"]], dependencies=[item["design_intelligence_source"]], status=item["status"]) for item in intelligence],
        *[envelope("LowEvidenceTranslationPlan", f"LETP-{problem['creative_problem_id']}", {"translation": translation}, upstream_refs=[problem["creative_problem_id"]], dependencies=["frozen_unknowns"], status=translation["status"]) for problem, translation in zip(problems, translations)],
        *[envelope("CreativeHypothesis", item["hypothesis_id"], item, upstream_refs=[item["creative_problem_id"], "PA-NAGI-PHASE-A"], dependencies=["strategy", "intelligence", "translation"], status=item["state"]) for item in hypotheses["hypotheses"]],
    ]
    typed = {
        "01_truth_set.json": truth_set,
        "02_invariant_bundle.json": envelope("InvariantBundle", "IB-NAGI-PHASE-A", invariant_bundle, upstream_refs=["TS-NAGI-FROZEN"], dependencies=["Round3D.registry"], status="APPLIED"),
        "03_customer_strategy.json": envelope("CustomerEvidenceBoard", "CEB-NAGI-PHASE-A", strategy, upstream_refs=["TS-NAGI-FROZEN"], dependencies=["truth", "evidence_refs"], status=strategy["gate"]),
        "04_creative_problem.json": envelope("CreativeProblem", "CP-NAGI-PHASE-A", {"problems": problems}, upstream_refs=["CEB-NAGI-PHASE-A"], dependencies=["strategy"], status="OPEN"),
        "05_design_intelligence.json": envelope("DesignIntelligenceResult", "DIR-NAGI-PHASE-A", {"design_intelligence_source": "round3f_b_core_v1", "source_contract": "AAR-PDI-3FB-v1.0", "results": intelligence}, upstream_refs=["CP-NAGI-PHASE-A"], dependencies=["registries/design_intelligence/round3f_b_core_v1.json"], status="RETRIEVED"),
        "06_low_evidence_translation.json": envelope("LowEvidenceTranslationPlan", "LETP-NAGI-PHASE-A", {"translations": translations}, upstream_refs=["DIR-NAGI-PHASE-A"], dependencies=["frozen_unknowns", "round3f_b_core_v1"], status="ROUTED"),
        "07_creative_hypothesis.json": envelope("CreativeHypothesis", "CHM-NAGI-PHASE-A", hypotheses, upstream_refs=["CEB-NAGI-PHASE-A", "CP-NAGI-PHASE-A", "DIR-NAGI-PHASE-A", "LETP-NAGI-PHASE-A"], dependencies=["strategy", "creative_problem", "design_intelligence", "translation"], status="PROPOSED"),
    }
    for filename, document in typed.items():
        write_json(out / filename, document)
    write_json(out / "canonical_entities.json", {"schema_version": CONTRACT_VERSION, "entity_count": len(canonical_entities), "entities": canonical_entities})
    write_json(out / "baseline_manifest.json", fixtures["baseline"])
    summary = make_summary(fixtures, strategy, problems, intelligence, translations, hypotheses)
    (out / "phase_a_summary.md").write_text(summary, encoding="utf-8")
    result = {
        "schema_version": CONTRACT_VERSION, "case_id": CASE_ID, "truth_hash": fixtures["truth_hash"],
        "baseline": fixtures["baseline"], "strategy_gate": strategy["gate"],
        "invariant_bundle": invariant_bundle, "creative_problem_count": len(problems),
        "retrieval_status": [item["status"] for item in intelligence],
        "translation_status": [item["status"] for item in translations],
        "hypothesis_count": len(hypotheses["hypotheses"]), "selection_status": hypotheses["selection_status"],
        "selection_argument": hypotheses["selection_argument"], "creative_rebuild": "NOT_STARTED",
        "design_intelligence_source": "round3f_b_core_v1",
        "retrieved_learning_ids": sorted({learning_id for item in intelligence for learning_id in item["retrieved_learning_ids"]}),
        "legacy_frame_registry_used": False,
        "phase_a_gate": "PASS" if strategy["gate"] == "READY_WITH_EXPLICIT_HYPOTHESES" and all(item["status"] == "PASS" for item in intelligence) and invariant_bundle["result"] == "PASS" and all(item["design_intelligence_refs"] for item in hypotheses["hypotheses"]) else "FAIL",
    }
    write_json(out / "phase_a_result.json", result)
    return result


def make_summary(fixtures: dict[str, Any], strategy: dict[str, Any], problems: list[dict[str, Any]], intelligence: list[dict[str, Any]], translations: list[dict[str, Any]], hypotheses: dict[str, Any]) -> str:
    services = ", ".join(f"{row['name']}＝{row['safe_framing']}" for row in fixtures["truth"]["services"])
    learning = [entry["learning_id"] for result in intelligence for entry in result["results"]]
    return "\n".join([
        "# Round 3I-A — Decision Foundation", "",
        "## Business Truth Boundary", f"{fixtures['truth']['entity']} / {fixtures['truth']['location']} / {services} / official SNS {fixtures['truth']['public_contact']['handle']}.",
        "Founder/staff, qualification, price, duration, process, premises, reviews, efficacy, and history remain UNKNOWN.", "",
        "## Customer Decision Problem", strategy["customer_tension"]["main_customer_tension"], "",
        "## Main Tension", strategy["main_objection"]["statement"], "",
        "## Conversion Goal", f"{strategy['conversion_goal']['action']} → {strategy['conversion_goal']['destination']}", "",
        "## Creative Problem", "Help a visitor distinguish three service intents and connect only verified facts to the verified contact route; do not invent missing evidence.", "",
        "## Relevant Intelligence", f"Registry: round3f_b_core_v1 (AAR-PDI-3FB-v1.0); {len(learning)} learning references across the candidate traces.",
        ", ".join(learning) if learning else "No matching registry records.",
        "Creative-facing principles only; benchmark names and URLs remain provenance.", "",
        "## Low-Evidence Translation", "\n".join(f"- {item['status']}: {item['selected_translation']}" for item in translations), "",
        "## Creative Hypothesis Candidates", "\n".join(f"- {item['hypothesis_id']} ({item['state']}): {item['resolution_statement']}" for item in hypotheses["hypotheses"]),
        "", "Selection remains unresolved (UNRESOLVED): both candidates remain PROPOSED because Phase A establishes decision logic and provenance but does not render or compare human-visible outcomes. No final design, layout, CSS, typography, or background is selected.",
        f"", f"Truth hash: `{fixtures['truth_hash']}`", f"Strategy Gate: `{strategy['gate']}`", "",
    ])


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(value), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_artifact_manifest(out: Path) -> dict[str, Any]:
    files = [{"path": path.relative_to(out).as_posix(), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in sorted(out.rglob("*")) if path.is_file() and path.name != "artifact_manifest.json"]
    manifest = {"schema_version": CONTRACT_VERSION, "file_count": len(files), "files": files}
    write_json(out / "artifact_manifest.json", manifest)
    return manifest
