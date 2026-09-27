'''Issue #121 research-pattern -> Production Variant bridge.

This layer sits after CompositionPlan/Family freeze. It converts accepted
Issue #119 research patterns into deterministic Production Variants, compiles a
page Art Direction Spine, and dispatches to variant-owned renderers. It never
re-opens Family selection, never routes by company/reference identity, and
never promotes illustrative media into evidence.
'''
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
from typing import Any, Mapping, Sequence

from .authored_composition_contract import plan_digest
from .visual_asset_library import asset_binding_css, render_asset_binding

WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
MOBILE_WIDTHS = (320, 360, 375, 390, 430)

class ProductionVariantBridgeError(RuntimeError):
    '''Fail-closed bridge error.'''


def _text(value: Any) -> str:
    return str(value or "").strip()


def _esc(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _truth_value(truth: Mapping[str, Any] | None) -> Any:
    if not isinstance(truth, Mapping):
        return None
    return deepcopy(truth.get("value"))


def _company(plan: Mapping[str, Any]) -> Mapping[str, Any]:
    return plan["input"]["company_truth"]


def _decision(plan: Mapping[str, Any]) -> Mapping[str, Any]:
    return plan["input"]["customer_decision_state"]


def _verified_facts(plan: Mapping[str, Any], *, persuasive_only: bool = False) -> list[dict[str, Any]]:
    facts = plan.get("input", {}).get("evidence", {}).get("facts", [])
    rows: list[dict[str, Any]] = []
    for fact in facts:
        if fact.get("confidence") != "verified":
            continue
        if persuasive_only and fact.get("usable_for_persuasion") is not True:
            continue
        rows.append(deepcopy(dict(fact)))
    return rows


def _offers(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [deepcopy(dict(row)) for row in (_company(plan).get("offers") or [])]


def _company_name(plan: Mapping[str, Any]) -> str:
    value = _text(_truth_value(_company(plan).get("name")))
    if not value:
        raise ProductionVariantBridgeError("COMPANY_NAME_MISSING")
    return value


def _contact_state(plan: Mapping[str, Any]) -> dict[str, Any]:
    contact = _company(plan).get("contact")
    verified = isinstance(contact, Mapping) and contact.get("confidence") == "verified"
    value = _truth_value(contact) if verified else None
    destination = ""
    if isinstance(value, Mapping):
        destination = _text(value.get("destination"))
    actionable = bool(
        destination
        and destination.startswith(("https://", "http://", "mailto:", "tel:"))
    )
    return {
        "verified": verified,
        "destination": destination if actionable else None,
        "actionable": actionable,
    }


VARIANT_REGISTRY: dict[str, dict[str, Any]] = {
    "PV-HERO-RECOGNITION-FIELD-v1": {
        "module_type": "hero",
        "source_pattern_ids": ["M-HERO-01"],
        "renderer_implementation_identity": "issue121.hero.recognition_field.v1",
        "mechanism_intent": "recognition before explanation",
        "mobile_transform": "recognition_focal_media_then_copy_field",
        "motion_intent": "hierarchy_focus_reveal",
    },
    "PV-HERO-EVIDENCE-ANCHOR-v1": {
        "module_type": "hero",
        "source_pattern_ids": ["M-HERO-02"],
        "renderer_implementation_identity": "issue121.hero.evidence_anchor.v1",
        "mechanism_intent": "credible evidence before aspiration",
        "mobile_transform": "claim_then_adjacent_verification_rail",
        "motion_intent": "evidence_sequence_reveal",
    },
    "PV-HERO-GUIDED-ROUTE-CANVAS-v1": {
        "module_type": "hero",
        "source_pattern_ids": ["M-HERO-03"],
        "renderer_implementation_identity": "issue121.hero.guided_route_canvas.v1",
        "mechanism_intent": "route user among meaningful choices",
        "mobile_transform": "route_by_route_priority_sequence",
        "motion_intent": "route_focus_feedback",
    },
    "PV-TRUST-BOUNDARY-LEDGER-v1": {
        "module_type": "trust",
        "source_pattern_ids": ["M-TRUST-01"],
        "renderer_implementation_identity": "issue121.trust.boundary_ledger.v1",
        "mechanism_intent": "make known/unknown boundary reassuring",
        "mobile_transform": "claim_and_boundary_remain_adjacent",
        "motion_intent": "none",
    },
    "PV-TRUST-DISTRIBUTED-PROOF-THREAD-v1": {
        "module_type": "trust",
        "source_pattern_ids": ["M-TRUST-02"],
        "renderer_implementation_identity": "issue121.trust.distributed_proof_thread.v1",
        "mechanism_intent": "thread proof through objections",
        "mobile_transform": "proof_immediately_after_triggering_claim",
        "motion_intent": "progressive_disclosure",
    },
    "PV-PROBLEM-SCENE-TENSION-v1": {
        "module_type": "problem",
        "source_pattern_ids": ["M-PROBLEM-01"],
        "renderer_implementation_identity": "issue121.problem.scene_tension.v1",
        "mechanism_intent": "name tension through a concrete scene",
        "mobile_transform": "short_scene_before_explanation",
        "motion_intent": "tension_then_resolution_reveal",
    },
    "PV-STORY-CAUSAL-CHAIN-v1": {
        "module_type": "story",
        "source_pattern_ids": ["M-STORY-01"],
        "renderer_implementation_identity": "issue121.story.causal_chain.v1",
        "mechanism_intent": "show causal business/provenance chain",
        "mobile_transform": "one_causal_beat_per_view",
        "motion_intent": "causal_sequence_reveal",
    },
    "PV-SERVICE-INTENT-ROUTED-FIELD-v1": {
        "module_type": "service",
        "source_pattern_ids": ["M-SERVICE-01"],
        "renderer_implementation_identity": "issue121.service.intent_routed_field.v1",
        "mechanism_intent": "route by customer intent",
        "mobile_transform": "intent_first_vertical_routes",
        "motion_intent": "route_focus_feedback",
    },
    "PV-PROCESS-PROOF-SEQUENCE-v1": {
        "module_type": "process",
        "source_pattern_ids": ["M-PROCESS-01"],
        "renderer_implementation_identity": "issue121.process.proof_sequence.v1",
        "mechanism_intent": "use verified process as proof",
        "mobile_transform": "one_process_unit_with_adjacent_boundary",
        "motion_intent": "sequence_reveal",
    },
    "PV-HUMAN-RELATIONSHIP-EVIDENCE-v1": {
        "module_type": "human",
        "source_pattern_ids": ["M-HUMAN-01"],
        "renderer_implementation_identity": "issue121.human.relationship_evidence.v1",
        "mechanism_intent": "make verified human relationship part of trust",
        "mobile_transform": "context_before_identity_detail",
        "motion_intent": "minimal",
    },
    "PV-GALLERY-ATMOSPHERE-DECISION-v1": {
        "module_type": "gallery",
        "source_pattern_ids": ["M-GALLERY-01"],
        "renderer_implementation_identity": "issue121.gallery.atmosphere_decision.v1",
        "mechanism_intent": "make atmosphere decision-relevant",
        "mobile_transform": "dominant_frame_then_supporting_detail",
        "motion_intent": "slow_media_reveal",
    },
    "PV-OFFER-COMMITMENT-LADDER-v1": {
        "module_type": "offer",
        "source_pattern_ids": ["M-OFFER-01"],
        "renderer_implementation_identity": "issue121.offer.commitment_ladder.v1",
        "mechanism_intent": "show increasing commitment transparently",
        "mobile_transform": "one_commitment_step_at_a_time",
        "motion_intent": "focus_progression",
    },
    "PV-CTA-STATE-SPECIFIC-EVENT-v1": {
        "module_type": "cta",
        "source_pattern_ids": ["M-CTA-01"],
        "renderer_implementation_identity": "issue121.cta.state_specific_event.v1",
        "mechanism_intent": "offer the next event appropriate to current decision state",
        "mobile_transform": "state_appropriate_full_width_action",
        "motion_intent": "interaction_feedback",
    },
    "PV-END-UTILITY-CLOSURE-v1": {
        "module_type": "ending",
        "source_pattern_ids": ["M-END-01"],
        "renderer_implementation_identity": "issue121.ending.utility_closure.v1",
        "mechanism_intent": "close with practical certainty",
        "mobile_transform": "action_then_utility_stack",
        "motion_intent": "none",
    },
    "PV-END-EMOTIONAL-RESOLUTION-v1": {
        "module_type": "ending",
        "source_pattern_ids": ["M-END-02"],
        "renderer_implementation_identity": "issue121.ending.emotional_resolution.v1",
        "mechanism_intent": "resolve emotional arc without unsupported promise",
        "mobile_transform": "single_focal_resolution_then_action",
        "motion_intent": "gentle_resolution_reveal",
    },
}

PATTERN_TO_VARIANT = {
    meta["source_pattern_ids"][0]: variant_id for variant_id, meta in VARIANT_REGISTRY.items()
}

_EXPECTED_PATTERNS = {
    "M-HERO-01", "M-HERO-02", "M-HERO-03", "M-TRUST-01", "M-TRUST-02",
    "M-PROBLEM-01", "M-STORY-01", "M-SERVICE-01", "M-PROCESS-01",
    "M-HUMAN-01", "M-GALLERY-01", "M-OFFER-01", "M-CTA-01", "M-END-01",
    "M-END-02",
}
if set(PATTERN_TO_VARIANT) != _EXPECTED_PATTERNS:
    raise RuntimeError("Issue121 registry must cover the accepted 15-pattern blueprint set exactly")


SCENE_COPY = {
    "recognize": (("まず、", "選ぶ基準を", "整える"), "最初に見るべきことを絞り、判断の入口をつくります。"),
    "choose": (("選択肢を、", "違いで", "見る"), "同じ並びではなく、選ぶ理由が見える順番で確認します。"),
    "understand": (("体験の流れを、", "順番に"), "確認できる範囲だけを、前後関係がわかる形で整理します。"),
    "trust": (("安心につながる", "情報を、", "近くに"), "確認済みと未確認を分け、判断材料の境界を見えるようにします。"),
    "compare": (("比べる", "ポイントを、", "ひと目で"), "違いを見つけやすい比較軸に沿って、選択肢を並べます。"),
    "prepare": (("はじめる前の", "不安を、", "小さくする"), "行動の直前に気になることを、先に確認できる場をつくります。"),
    "act": (("次の一歩は、", "ここから"), "ここまでの確認内容を踏まえ、無理のない次の行動につなげます。"),
}

HERO_COPY = {
    "recognition": {
        "default": (("気になる理由を、", "最初の一画面に。"), "説明より先に、選ぶ感覚をつくる。"),
        "prepare": (("不安をほどいて、", "はじめる準備を。"), "先に確かめることで、行動のハードルを下げる。"),
        "act": (("考えすぎる前に、", "次の一歩を軽く。"), "必要なことだけを見て、その先へ。"),
    },
    "evidence": {"default": (("確かめられる", "情報から、", "安心の理由を。"), "わかっていることと、まだ確認中のことを近くに置く。")},
    "route": {"default": (("違いを見ながら、", "自分に合う", "入口へ。"), "選択肢を同じ大きさにせず、判断の優先度で案内する。")},
}


def build_decision_signature(plan: Mapping[str, Any]) -> dict[str, Any]:
    decision = _decision(plan)
    offers = _offers(plan)
    evidence = plan.get("input", {}).get("evidence", {})
    facts = _verified_facts(plan)
    persuasive = _verified_facts(plan, persuasive_only=True)
    questions = [_text(row) for row in (decision.get("questions") or []) if _text(row)]
    tensions = [_text(row) for row in (decision.get("tensions") or []) if _text(row)]
    contact = _contact_state(plan)
    return {
        "primary_job": _text(decision.get("primary_job")),
        "decision_stage": _text(decision.get("decision_stage")),
        "risk_sensitivity": _text(decision.get("risk_sensitivity")),
        "tensions": tensions,
        "questions": questions,
        "offer_structure": {"count": len(offers), "ids": [_text(row.get("id")) for row in offers], "names_present": [bool(_text(row.get("name"))) for row in offers]},
        "proof_available": bool(persuasive),
        "verified_fact_count": len(facts),
        "persuasive_fact_count": len(persuasive),
        "proof_gaps": deepcopy(list(evidence.get("proof_gaps") or [])),
        "human_relationship_relevance": False,
        "local_relationship_relevance": False,
        "sensory_experience_weight": "medium" if len(offers) else "low",
        "craftsmanship_weight": "unknown",
        "category_education_need": "process" in questions,
        "choice_guidance_need": len(offers) > 1 or "difference" in questions,
        "process_inspectability_need": "process" in questions,
        "commitment_shape": "UNVERIFIED",
        "verified_cta_state": "ACTIONABLE" if contact["actionable"] else "NON_ACTION",
    }


def _variant_trace(*, scene_id: str, decision_job: str, family_id: str, candidates: Sequence[str], selected: str, reason: str, company_inputs: Sequence[str], decision_inputs: Sequence[str], asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    if selected not in VARIANT_REGISTRY:
        raise ProductionVariantBridgeError(f"UNKNOWN_VARIANT:{selected}")
    meta = VARIANT_REGISTRY[selected]
    implementation = _text(meta.get("renderer_implementation_identity"))
    if not implementation or implementation == "UNIMPLEMENTED_REQUIRED":
        raise ProductionVariantBridgeError(f"MISSING_RENDERER_IMPLEMENTATION_IDENTITY:{selected}")
    rejected = [{"production_variant_id": value, "reason": "lower precedence for normalized semantic inputs"} for value in candidates if value != selected]
    media_binding = asset_bindings.get("hero" if scene_id == "hero" else scene_id)
    responsive = {str(width): meta["mobile_transform"] if width in MOBILE_WIDTHS else "desktop_mechanism_preserved" for width in WIDTHS}
    return {
        "scene_id": scene_id,
        "decision_job": decision_job,
        "family_id": family_id,
        "source_research_refs": [{"source": "Issue #44 accepted pattern registry via Issue #119", "artifact_path": "data/production_architecture/module_composition_registry_v1.json", "pattern_id": pattern_id, "mechanism_excerpt": meta["mechanism_intent"]} for pattern_id in meta["source_pattern_ids"]],
        "source_pattern_ids": list(meta["source_pattern_ids"]),
        "candidate_production_variant_ids": list(candidates),
        "selected_production_variant_id": selected,
        "selection_reason": reason,
        "rejected_alternatives": rejected,
        "company_inputs_used": list(company_inputs),
        "decision_inputs_used": list(decision_inputs),
        "evidence_requirements": "verified_or_explicitly_bounded_only",
        "media_requirements": "rights-gated; illustrative media never proof",
        "evidence_bindings": [],
        "media_bindings": ([{"asset_id": media_binding.get("asset_id"), "binary_sha256": media_binding.get("binary_sha256"), "evidence_status": media_binding.get("evidence_status"), "rights_gate": media_binding.get("rights_gate")}] if media_binding else []),
        "feasibility_adaptation": "inside_selected_variant_only",
        "responsive_variant_transform": responsive,
        "renderer_implementation_identity": implementation,
        "rendered_dom_identity": f'data-production-variant="{selected}"',
        "rendered_style_identity": f"variant::{selected}",
        "screenshot_verification": [{"width": width, "artifact_path": None, "mechanism_fidelity": "NOT_REVIEWED", "whole_page_coherence": "NOT_REVIEWED", "reviewer": None, "notes": "Populated by Issue #121 evidence runner."} for width in WIDTHS],
    }


def _select_hero(plan: Mapping[str, Any], signature: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    job = signature["primary_job"]
    offers = int(signature["offer_structure"]["count"])
    candidates = ["PV-HERO-RECOGNITION-FIELD-v1", "PV-HERO-EVIDENCE-ANCHOR-v1", "PV-HERO-GUIDED-ROUTE-CANVAS-v1"]
    if job == "trust":
        selected = "PV-HERO-EVIDENCE-ANCHOR-v1"
        reason = "trust-sensitive decision state requires known/unknown verification boundary in the Hero"
    elif job in {"choose", "compare"} and offers >= 2:
        selected = "PV-HERO-GUIDED-ROUTE-CANVAS-v1"
        reason = "multiple verified offer names plus choice/comparison job require unequal route hierarchy"
    else:
        selected = "PV-HERO-RECOGNITION-FIELD-v1"
        reason = "decision state is best served by recognition before explanation"
    return _variant_trace(scene_id="hero", decision_job=job, family_id=_text(plan.get("family_id")), candidates=candidates, selected=selected, reason=reason, company_inputs=["company_truth.name", "company_truth.offers", "company_truth.contact"], decision_inputs=["primary_job", "risk_sensitivity", "offer_structure", "proof_available"], asset_bindings=asset_bindings)


def _select_scene(plan: Mapping[str, Any], scene: Mapping[str, Any], signature: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    intent = _text(scene.get("intent"))
    scene_id = _text(scene.get("id")) or intent
    proof = bool(signature["proof_available"])
    offers = int(signature["offer_structure"]["count"])
    mapping: dict[str, tuple[list[str], str, str]] = {
        "recognize": (["PV-PROBLEM-SCENE-TENSION-v1", "PV-STORY-CAUSAL-CHAIN-v1"], "PV-PROBLEM-SCENE-TENSION-v1", "opening body beat names the current decision tension before explanation"),
        "choose": (["PV-SERVICE-INTENT-ROUTED-FIELD-v1", "PV-OFFER-COMMITMENT-LADDER-v1"], "PV-SERVICE-INTENT-ROUTED-FIELD-v1", "choice job is routed by intent using verified offer names rather than equal cards"),
        "understand": (["PV-PROCESS-PROOF-SEQUENCE-v1", "PV-STORY-CAUSAL-CHAIN-v1"], "PV-PROCESS-PROOF-SEQUENCE-v1", "understanding job needs a process-shaped sequence without inventing extra steps"),
        "trust": (["PV-TRUST-BOUNDARY-LEDGER-v1", "PV-TRUST-DISTRIBUTED-PROOF-THREAD-v1"], "PV-TRUST-DISTRIBUTED-PROOF-THREAD-v1" if proof else "PV-TRUST-BOUNDARY-LEDGER-v1", "verified persuasive proof is distributed locally" if proof else "missing proof stays explicit through a known/unknown boundary ledger"),
        "compare": (["PV-SERVICE-INTENT-ROUTED-FIELD-v1", "PV-OFFER-COMMITMENT-LADDER-v1"], "PV-SERVICE-INTENT-ROUTED-FIELD-v1", "offer names are verified but commitment/pricing terms are not, so comparison uses intent routing rather than an invented ladder"),
        "prepare": (["PV-PROBLEM-SCENE-TENSION-v1", "PV-PROCESS-PROOF-SEQUENCE-v1"], "PV-PROBLEM-SCENE-TENSION-v1", "pre-action uncertainty is staged as a concrete tension scene"),
        "act": (["PV-CTA-STATE-SPECIFIC-EVENT-v1", "PV-END-UTILITY-CLOSURE-v1"], "PV-CTA-STATE-SPECIFIC-EVENT-v1", "act scene resolves into the verified next event rather than another content chapter"),
    }
    if intent not in mapping:
        raise ProductionVariantBridgeError(f"UNMAPPED_SCENE_INTENT:{intent}")
    candidates, selected, reason = mapping[intent]
    if selected == "PV-OFFER-COMMITMENT-LADDER-v1" and signature["commitment_shape"] == "UNVERIFIED":
        raise ProductionVariantBridgeError("COMMITMENT_LADDER_REQUIRES_VERIFIED_COMMITMENT_SHAPE")
    if selected == "PV-SERVICE-INTENT-ROUTED-FIELD-v1" and offers < 1:
        raise ProductionVariantBridgeError("SERVICE_ROUTE_REQUIRES_VERIFIED_OFFER_NAME")
    return _variant_trace(scene_id=scene_id, decision_job=intent, family_id=_text(plan.get("family_id")), candidates=candidates, selected=selected, reason=reason, company_inputs=["company_truth.offers", "company_truth.contact", "evidence.facts"], decision_inputs=["primary_job", "questions", "risk_sensitivity", "proof_available"], asset_bindings=asset_bindings)


def _select_cta(plan: Mapping[str, Any], signature: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return _variant_trace(scene_id="cta", decision_job=signature["primary_job"], family_id=_text(plan.get("family_id")), candidates=["PV-CTA-STATE-SPECIFIC-EVENT-v1"], selected="PV-CTA-STATE-SPECIFIC-EVENT-v1", reason="CTA mechanism is state-specific and may only become actionable with a verified destination", company_inputs=["company_truth.contact"], decision_inputs=["primary_job", "verified_cta_state"], asset_bindings=asset_bindings)


def _select_ending(plan: Mapping[str, Any], signature: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    candidates = ["PV-END-UTILITY-CLOSURE-v1", "PV-END-EMOTIONAL-RESOLUTION-v1"]
    job = signature["primary_job"]
    if job in {"trust", "prepare", "understand"}:
        selected = "PV-END-UTILITY-CLOSURE-v1"
        reason = "risk/uncertainty remains operational, so the page closes with practical certainty"
    else:
        selected = "PV-END-EMOTIONAL-RESOLUTION-v1"
        reason = "decision arc can resolve with a spacious emotional close without adding unsupported promises"
    return _variant_trace(scene_id="ending", decision_job=job, family_id=_text(plan.get("family_id")), candidates=candidates, selected=selected, reason=reason, company_inputs=["company_truth.contact", "company_truth.offers"], decision_inputs=["primary_job", "risk_sensitivity", "verified_cta_state"], asset_bindings=asset_bindings)


def compile_page_art_direction_spine(plan: Mapping[str, Any], hero_trace: Mapping[str, Any], scene_traces: Sequence[Mapping[str, Any]], ending_trace: Mapping[str, Any]) -> dict[str, Any]:
    hero = hero_trace["selected_production_variant_id"]
    job = _text(_decision(plan).get("primary_job"))
    hero_strategy = {
        "PV-HERO-RECOGNITION-FIELD-v1": {"primary_visual_thesis": "open contextual field: recognition precedes explanation", "silhouette_strategy": "asymmetric media field with a single high-authority copy focal zone", "type_authority_strategy": "large editorial display + quiet utility sans", "material_language": "paper/atmosphere with sparse rules", "contrast_strategy": "scale and negative space"},
        "PV-HERO-EVIDENCE-ANCHOR-v1": {"primary_visual_thesis": "verification rail anchors the promise", "silhouette_strategy": "claim field locked to an evidence/boundary rail", "type_authority_strategy": "disciplined sans display + ledger microtype", "material_language": "ledger/rule/inset evidence surfaces", "contrast_strategy": "information density against calm surrounding air"},
        "PV-HERO-GUIDED-ROUTE-CANVAS-v1": {"primary_visual_thesis": "unequal routes express decision priority", "silhouette_strategy": "route canvas with dominant first path and secondary paths", "type_authority_strategy": "orientation statement + route labels with stepped scale", "material_language": "navigation rails, route indices and open field", "contrast_strategy": "route footprint and hierarchy"},
    }[hero]
    density_arc = ["opening_breath", *[{"PV-SERVICE-INTENT-ROUTED-FIELD-v1": "decision_cluster", "PV-TRUST-BOUNDARY-LEDGER-v1": "calm_information_pause", "PV-TRUST-DISTRIBUTED-PROOF-THREAD-v1": "proof_interruptions", "PV-PROBLEM-SCENE-TENSION-v1": "focused_tension_beat", "PV-PROCESS-PROOF-SEQUENCE-v1": "sequenced_rhythm", "PV-CTA-STATE-SPECIFIC-EVENT-v1": "action_resolution"}.get(row["selected_production_variant_id"], "authored_beat") for row in scene_traces], "terminal_breath" if ending_trace["selected_production_variant_id"].endswith("EMOTIONAL-RESOLUTION-v1") else "utility_certainty"]
    media_arc = ["hero_dominant_context", *["local_media_if_bound" if row.get("media_bindings") else "copy_evidence_only" for row in scene_traces]]
    spine = {**hero_strategy, "density_arc": density_arc, "media_arc": media_arc, "closing_resolution": ending_trace["selected_production_variant_id"], "decision_job": job, "family_id": _text(plan.get("family_id")), "family_frozen": plan.get("input", {}).get("creative_family", {}).get("frozen") is True, "company_identity_used_for_routing": False, "category_fixed_template_lookup_used": False, "random_diversity_used": False}
    spine["spine_digest"] = _sha(spine)
    return spine


def select_variant_ensemble(plan: Mapping[str, Any], directives: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    if plan.get("production_authority") != "composition_plan":
        raise ProductionVariantBridgeError("COMPOSITION_PLAN_NOT_AUTHORITATIVE")
    if plan.get("input", {}).get("creative_family", {}).get("frozen") is not True:
        raise ProductionVariantBridgeError("FAMILY_NOT_FROZEN")
    before = plan_digest(plan)
    signature = build_decision_signature(plan)
    hero = _select_hero(plan, signature, asset_bindings)
    scene_traces = [_select_scene(plan, scene, signature, asset_bindings) for scene in (directives.get("scene_intents") or []) if _text(scene.get("id")) != "recognize"]
    cta = _select_cta(plan, signature, asset_bindings)
    ending = _select_ending(plan, signature, asset_bindings)
    spine = compile_page_art_direction_spine(plan, hero, scene_traces, ending)
    selected_ids = [hero["selected_production_variant_id"], *[row["selected_production_variant_id"] for row in scene_traces], cta["selected_production_variant_id"], ending["selected_production_variant_id"]]
    for variant_id in selected_ids:
        if variant_id not in VARIANT_REGISTRY:
            raise ProductionVariantBridgeError(f"UNKNOWN_VARIANT:{variant_id}")
    if plan_digest(plan) != before:
        raise ProductionVariantBridgeError("VARIANT_SELECTION_MUTATED_COMPOSITION_PLAN")
    return {"schema_version": "issue121_research_to_production_bridge_v1", "composition_plan_digest": before, "decision_signature": signature, "decision_signature_digest": _sha(signature), "creative_family_id": _text(plan.get("family_id")), "family_frozen": True, "hero": hero, "scenes": scene_traces, "cta": cta, "ending": ending, "page_art_direction_spine": spine, "selected_production_variant_ids": selected_ids, "production_variant_set_digest": _sha(selected_ids), "registry_pattern_coverage": sorted(PATTERN_TO_VARIANT), "registry_variant_coverage": sorted(VARIANT_REGISTRY), "renderer_cutover": {"legacy_generic_renderer_is_final_authority": False, "variant_dispatch_is_final_authority": True, "silent_generic_fallback": False}}


def _heading(chunks: Sequence[str], *, level: int = 2, class_name: str = "") -> str:
    cls = f' class="{_esc(class_name)}"' if class_name else ""
    pieces: list[str] = []
    for index, chunk in enumerate(chunks):
        pieces.append(f'<span class="semantic-headline-unit premium-display-unit">{_esc(chunk)}</span>')
        if index < len(chunks) - 1:
            pieces.append("<wbr>")
    return f"<h{level}{cls} data-semantic-heading=\"authored\">{''.join(pieces)}</h{level}>"


def _hero_heading(chunks: Sequence[str]) -> str:
    pieces = "".join(f'<span class="premium-headline-unit semantic-headline-unit">{_esc(chunk)}</span>' for chunk in chunks)
    return f"<h1>{pieces}</h1>"


def _media(binding: Mapping[str, Any] | None, *, class_name: str) -> str:
    if not binding:
        return f'<div class="{_esc(class_name)} media-empty" aria-hidden="true"></div>'
    return f'<div class="{_esc(class_name)}">{render_asset_binding(binding)}</div>'


def _offer_name(offer: Mapping[str, Any], index: int) -> str:
    return _text(offer.get("name")) or f"選択肢 {index:02d}"


def _cta_markup(plan: Mapping[str, Any], *, context: str = "body") -> str:
    state = _contact_state(plan)
    job = _text(_decision(plan).get("primary_job"))
    label = {"trust": "確認したうえで相談する", "choose": "選び方を相談する", "compare": "違いを相談する", "prepare": "始める前に相談する", "act": "次の一歩へ進む"}.get(job, "相談する")
    if state["actionable"]:
        primary = f'<a class="cta-primary variant-action" href="{_esc(state["destination"])}">{_esc(label)}<span aria-hidden="true">↗</span></a>'
    else:
        primary = '<span class="cta-primary variant-action variant-action--disabled" aria-disabled="true">お問い合わせ方法は確認中です</span>'
    return f'<div class="variant-action-group" data-cta-context="{_esc(context)}">{primary}<a class="cta-secondary variant-action-secondary" href="#details">内容を見直す</a></div>'


def _hero_copy_for(variant_id: str, job: str) -> tuple[tuple[str, ...], str]:
    if variant_id == "PV-HERO-EVIDENCE-ANCHOR-v1":
        return HERO_COPY["evidence"]["default"]
    if variant_id == "PV-HERO-GUIDED-ROUTE-CANVAS-v1":
        return HERO_COPY["route"]["default"]
    return HERO_COPY["recognition"].get(job, HERO_COPY["recognition"]["default"])


def _trace_attrs(trace: Mapping[str, Any]) -> str:
    variant = trace["selected_production_variant_id"]
    pattern = ",".join(trace["source_pattern_ids"])
    renderer = trace["renderer_implementation_identity"]
    return f'data-research-pattern="{_esc(pattern)}" data-production-variant="{_esc(variant)}" data-renderer-id="{_esc(renderer)}" data-responsive-transform="{_esc(VARIANT_REGISTRY[variant]["mobile_transform"])}"'


def _render_hero_recognition(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _hero_copy_for(trace["selected_production_variant_id"], _text(_decision(plan).get("primary_job")))
    return f'''<section class="variant-hero hero-recognition premium-hero" {_trace_attrs(trace)}><div class="hero-recognition__media">{_media(asset_bindings.get("hero"), class_name="hero-media-field")}</div><div class="hero-recognition__copy premium-hero__copy"><p class="variant-kicker">RECOGNITION FIELD</p>{_hero_heading(chunks)}<p class="hero-lead">{_esc(support)}</p>{_cta_markup(plan, context="hero")}</div><p class="hero-recognition__side-note">説明より先に、判断の焦点を。</p></section>'''


def _verification_rows(plan: Mapping[str, Any]) -> str:
    persuasive = _verified_facts(plan, persuasive_only=True)
    contact = _contact_state(plan)
    offers = _offers(plan)
    rows: list[tuple[str, str, str]] = [("SERVICE", "確認済み", f"{len(offers)}件の名称を表示"), ("CONTACT", "確認済み" if contact["verified"] else "未確認", "遷移先あり" if contact["actionable"] else "方法確認中")]
    if persuasive:
        for fact in persuasive[:2]:
            rows.append(("EVIDENCE", "確認済み", _text(fact.get("claim"))))
    else:
        rows.append(("PROOF", "境界表示", "実績・評価は確認済み情報のみ掲載"))
    return "".join(f'<li><span>{_esc(label)}</span><strong>{_esc(state)}</strong><p>{_esc(value)}</p></li>' for label, state, value in rows)


def _render_hero_evidence(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _hero_copy_for(trace["selected_production_variant_id"], _text(_decision(plan).get("primary_job")))
    return f'''<section class="variant-hero hero-evidence premium-hero" {_trace_attrs(trace)}><div class="hero-evidence__claim premium-hero__copy"><p class="variant-kicker">EVIDENCE ANCHOR</p>{_hero_heading(chunks)}<p class="hero-lead">{_esc(support)}</p>{_cta_markup(plan, context="hero")}</div><aside class="hero-evidence__ledger"><p class="ledger-title">WHAT IS VERIFIED</p><ul>{_verification_rows(plan)}</ul>{_media(asset_bindings.get("hero"), class_name="hero-evidence__media")}</aside></section>'''


def _render_hero_route(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _hero_copy_for(trace["selected_production_variant_id"], _text(_decision(plan).get("primary_job")))
    routes: list[str] = []
    for index, offer in enumerate(_offers(plan), 1):
        routes.append(f'<li class="route-item route-item--{index}"><span class="route-index">{index:02d}</span><div><strong>{_esc(_offer_name(offer, index))}</strong><p>{"最初に見るルート" if index == 1 else "比較しながら確認"}</p></div><span aria-hidden="true">↘</span></li>')
    return f'''<section class="variant-hero hero-route premium-hero" {_trace_attrs(trace)}><div class="hero-route__orientation premium-hero__copy"><p class="variant-kicker">GUIDED ROUTE CANVAS</p>{_hero_heading(chunks)}<p class="hero-lead">{_esc(support)}</p></div><ol class="hero-route__routes">{''.join(routes)}</ol><div class="hero-route__media">{_media(asset_bindings.get("hero"), class_name="route-media-band")}</div><div class="hero-route__action">{_cta_markup(plan, context="hero")}</div></section>'''


def _scene_text(intent: str) -> tuple[tuple[str, ...], str]:
    return SCENE_COPY.get(intent, (("必要な", "情報を、", "わかりやすく"), "判断に必要なことだけを整理します。"))


def _scene_binding(asset_bindings: Mapping[str, Mapping[str, Any]], scene_id: str) -> Mapping[str, Any] | None:
    return asset_bindings.get(scene_id)


def _render_service_field(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _scene_text(trace["decision_job"])
    rows = [f'<article class="service-route service-route--{index}"><span>{index:02d}</span><h3>{_esc(_offer_name(offer, index))}</h3><p>{"基準になる入口" if index == 1 else "違いを見ながら確認"}</p></article>' for index, offer in enumerate(_offers(plan), 1)]
    return f'''<section id="details" class="variant-scene service-field premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}><header class="service-field__intro"><p class="variant-kicker">INTENT ROUTES</p>{_heading(chunks)}<p>{_esc(support)}</p></header><div class="service-field__routes">{''.join(rows)}</div>{_media(_scene_binding(asset_bindings, trace["scene_id"]), class_name="service-field__media")}</section>'''


def _render_trust_ledger(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _scene_text("trust")
    contact = _contact_state(plan)
    proof = _verified_facts(plan, persuasive_only=True)
    proof_state = "確認済み" if proof else "確認中"
    return f'''<section class="variant-scene trust-ledger premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}><div class="trust-ledger__copy"><p class="variant-kicker">BOUNDARY LEDGER</p>{_heading(chunks)}<p>{_esc(support)}</p></div><dl class="trust-ledger__table"><div><dt>サービス名称</dt><dd>確認済み</dd></div><div><dt>問い合わせ先</dt><dd>{"確認済み" if contact["verified"] else "確認中"}</dd></div><div><dt>実績・評価</dt><dd>{proof_state}</dd></div></dl>{_media(_scene_binding(asset_bindings, trace["scene_id"]), class_name="trust-ledger__media")}</section>'''


def _render_proof_thread(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _scene_text("trust")
    facts = _verified_facts(plan, persuasive_only=True)
    if not facts:
        raise ProductionVariantBridgeError("DISTRIBUTED_PROOF_THREAD_REQUIRES_PERSUASIVE_VERIFIED_FACT")
    nodes = "".join(f'<article class="proof-thread__node"><span>VERIFIED {index:02d}</span><p>{_esc(fact.get("claim"))}</p></article>' for index, fact in enumerate(facts, 1))
    return f'''<section class="variant-scene proof-thread premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}><header><p class="variant-kicker">DISTRIBUTED PROOF</p>{_heading(chunks)}<p>{_esc(support)}</p></header><div class="proof-thread__rail">{nodes}</div>{_media(_scene_binding(asset_bindings, trace["scene_id"]), class_name="proof-thread__media")}</section>'''


def _render_tension_scene(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _scene_text(trace["decision_job"])
    tensions = [_text(row) for row in (_decision(plan).get("tensions") or []) if _text(row)]
    tension = tensions[0] if tensions else "選ぶ前の迷いを、具体的な確認へ変える。"
    return f'''<section class="variant-scene tension-scene premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}><div class="tension-scene__statement"><p class="variant-kicker">DECISION TENSION</p><blockquote>{_esc(tension)}</blockquote></div><div class="tension-scene__resolution">{_heading(chunks)}<p>{_esc(support)}</p></div>{_media(_scene_binding(asset_bindings, trace["scene_id"]), class_name="tension-scene__media")}</section>'''


def _render_causal_story(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _scene_text(trace["decision_job"])
    return f'''<section class="variant-scene causal-story premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}><header><p class="variant-kicker">CAUSAL CHAIN</p>{_heading(chunks)}<p>{_esc(support)}</p></header><ol class="causal-story__rail"><li>確認する</li><li>違いを理解する</li><li>次の判断へ</li></ol></section>'''


def _render_process_sequence(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _scene_text("understand")
    facts = _verified_facts(plan, persuasive_only=True)
    if facts:
        steps = "".join(f'<li><span>{index:02d}</span><div><strong>確認済み</strong><p>{_esc(fact.get("claim"))}</p></div></li>' for index, fact in enumerate(facts, 1))
    else:
        steps = '<li><span>01</span><div><strong>確認できる流れだけ</strong><p>具体的な工程数や内容は、確認できた情報だけを掲載します。</p></div></li>'
    return f'''<section class="variant-scene process-sequence premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}><header><p class="variant-kicker">PROCESS AS PROOF</p>{_heading(chunks)}<p>{_esc(support)}</p></header><ol class="process-sequence__steps">{steps}</ol>{_media(_scene_binding(asset_bindings, trace["scene_id"]), class_name="process-sequence__media")}</section>'''


def _render_human_evidence(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    binding = _scene_binding(asset_bindings, trace["scene_id"])
    if not binding or _text(binding.get("evidence_status")) != "ACTUAL_COMPANY_EVIDENCE":
        raise ProductionVariantBridgeError("HUMAN_RELATIONSHIP_VARIANT_REQUIRES_ACTUAL_COMPANY_EVIDENCE")
    chunks, support = _scene_text("trust")
    return f'''<section class="variant-scene human-evidence premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}>{_media(binding, class_name="human-evidence__portrait")}<div><p class="variant-kicker">RELATIONSHIP EVIDENCE</p>{_heading(chunks)}<p>{_esc(support)}</p></div></section>'''


def _render_gallery(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    binding = _scene_binding(asset_bindings, trace["scene_id"])
    if not binding:
        raise ProductionVariantBridgeError("GALLERY_VARIANT_REQUIRES_MEDIA")
    chunks, support = _scene_text(trace["decision_job"])
    return f'''<section class="variant-scene atmosphere-gallery premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}>{_media(binding, class_name="atmosphere-gallery__dominant")}<div class="atmosphere-gallery__caption"><p class="variant-kicker">ATMOSPHERE / DECISION</p>{_heading(chunks)}<p>{_esc(support)}</p></div></section>'''


def _render_offer_ladder(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    raise ProductionVariantBridgeError("OFFER_COMMITMENT_LADDER_NOT_SELECTABLE_WITHOUT_VERIFIED_COMMITMENT_TERMS")


def _render_act_scene(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    chunks, support = _scene_text("act")
    return f'''<section class="variant-scene action-event premium-scene" data-premium-scene="{_esc(trace["scene_id"])}" {_trace_attrs(trace)}><div><p class="variant-kicker">NEXT EVENT</p>{_heading(chunks)}<p>{_esc(support)}</p></div>{_cta_markup(plan, context="scene")}</section>'''


def _render_cta_variant(plan: Mapping[str, Any], trace: Mapping[str, Any]) -> str:
    return f'''<section class="variant-cta state-event-cta" {_trace_attrs(trace)}><div><p class="variant-kicker">DECISION EVENT</p>{_heading(("納得して", "から、", "次へ。"))}<p>確認できていない条件を、事実のように補わずに次の行動へつなげます。</p></div>{_cta_markup(plan, context="final")}</section>'''


def _render_ending_utility(plan: Mapping[str, Any], trace: Mapping[str, Any]) -> str:
    contact = _contact_state(plan)
    return f'''<section class="variant-ending ending-utility" {_trace_attrs(trace)}><div><p class="variant-kicker">UTILITY CLOSURE</p>{_heading(("最後に、", "確認できること。"))}</div><dl><div><dt>問い合わせ</dt><dd>{"遷移先確認済み" if contact["actionable"] else "方法確認中"}</dd></div><div><dt>掲載情報</dt><dd>確認済み情報を優先</dd></div></dl></section>'''


def _render_ending_emotional(plan: Mapping[str, Any], trace: Mapping[str, Any]) -> str:
    return f'''<section class="variant-ending ending-emotional" {_trace_attrs(trace)}><p class="variant-kicker">EMOTIONAL RESOLUTION</p>{_heading(("選ぶ時間まで、", "心地よく。"))}<p>急がせず、必要な情報を確かめた先に次の行動を置きます。</p></section>'''


_RENDERERS = {
    "PV-HERO-RECOGNITION-FIELD-v1": _render_hero_recognition,
    "PV-HERO-EVIDENCE-ANCHOR-v1": _render_hero_evidence,
    "PV-HERO-GUIDED-ROUTE-CANVAS-v1": _render_hero_route,
    "PV-TRUST-BOUNDARY-LEDGER-v1": _render_trust_ledger,
    "PV-TRUST-DISTRIBUTED-PROOF-THREAD-v1": _render_proof_thread,
    "PV-PROBLEM-SCENE-TENSION-v1": _render_tension_scene,
    "PV-STORY-CAUSAL-CHAIN-v1": _render_causal_story,
    "PV-SERVICE-INTENT-ROUTED-FIELD-v1": _render_service_field,
    "PV-PROCESS-PROOF-SEQUENCE-v1": _render_process_sequence,
    "PV-HUMAN-RELATIONSHIP-EVIDENCE-v1": _render_human_evidence,
    "PV-GALLERY-ATMOSPHERE-DECISION-v1": _render_gallery,
    "PV-OFFER-COMMITMENT-LADDER-v1": _render_offer_ladder,
    "PV-CTA-STATE-SPECIFIC-EVENT-v1": _render_act_scene,
}

if set(_RENDERERS) != set(VARIANT_REGISTRY) - {"PV-END-UTILITY-CLOSURE-v1", "PV-END-EMOTIONAL-RESOLUTION-v1"}:
    raise RuntimeError("Issue121 renderer dispatch must cover every non-ending Production Variant")


def _render_variant(plan: Mapping[str, Any], trace: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]]) -> str:
    variant_id = trace["selected_production_variant_id"]
    renderer = _RENDERERS.get(variant_id)
    if renderer is None:
        raise ProductionVariantBridgeError(f"NO_VARIANT_RENDERER:{variant_id}")
    return renderer(plan, trace, asset_bindings)


def _css(spine: Mapping[str, Any]) -> str:
    accent = {"asymmetric media field with a single high-authority copy focal zone": "#6c4f3d", "claim field locked to an evidence/boundary rail": "#34564f", "route canvas with dominant first path and secondary paths": "#514a70"}.get(spine["silhouette_strategy"], "#4c514d")
    return f'''
:root{{--ink:#161916;--paper:#f1efe9;--surface:#fbfaf6;--muted:#69706b;--line:#c8ccc5;--accent:{accent};--sans:system-ui,-apple-system,"Hiragino Kaku Gothic ProN",sans-serif;--serif:"Yu Mincho","Hiragino Mincho ProN",serif}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans)}}a{{color:inherit}}
.variant-page{{max-width:1440px;margin:auto;padding:0 clamp(20px,5vw,80px);overflow-x:clip}}.premium-shell{{max-width:1440px}}
.variant-header{{min-height:76px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:20px}}.variant-header strong{{letter-spacing:.08em}}.variant-header span{{font-size:11px;color:var(--muted);letter-spacing:.12em}}
.variant-kicker{{font-size:11px;letter-spacing:.18em;color:var(--muted);text-transform:uppercase;margin:0 0 18px}}
.semantic-headline-unit,.premium-display-unit,.premium-headline-unit{{white-space:nowrap}}.premium-headline-unit{{display:block}}.premium-display-unit{{display:inline-block}}
h1,h2,h3,p{{overflow-wrap:normal;word-break:normal}}.hero-lead{{font-size:clamp(16px,1.45vw,20px);line-height:1.85;max-width:36rem;color:#3d443f}}
.production-asset{{margin:0!important}}.production-asset img{{border-radius:0!important}}
.variant-action-group{{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-top:30px}}.variant-action,.variant-action-secondary{{min-height:52px;padding:0 20px;display:inline-flex;align-items:center;justify-content:space-between;gap:24px;text-decoration:none;border:1px solid var(--ink);font-size:14px}}.variant-action{{background:var(--ink);color:white;min-width:220px}}.variant-action-secondary{{background:transparent}}.variant-action--disabled{{opacity:.55}}
.hero-recognition{{position:relative;min-height:86svh;padding:clamp(60px,8vw,120px) 0;display:grid;grid-template-columns:repeat(12,1fr);align-items:center}}
.hero-recognition__media{{grid-column:5/13;grid-row:1;align-self:stretch;min-height:620px}}.hero-recognition__media .production-asset,.hero-recognition__media img{{height:100%}}.hero-recognition__media img{{object-fit:cover;aspect-ratio:auto!important}}
.hero-recognition__copy{{grid-column:1/8;grid-row:1;z-index:2;background:rgba(241,239,233,.92);padding:clamp(32px,5vw,74px) clamp(24px,4vw,58px) clamp(32px,5vw,74px) 0}}
.hero-recognition h1{{font-family:var(--serif);font-weight:500;font-size:clamp(52px,7.4vw,108px);line-height:.98;letter-spacing:-.05em;margin:0 0 28px}}.hero-recognition__side-note{{position:absolute;right:0;bottom:28px;writing-mode:vertical-rl;font-size:11px;letter-spacing:.12em;color:var(--muted)}}
.hero-evidence{{min-height:82svh;padding:clamp(58px,8vw,112px) 0;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(330px,.85fr);gap:clamp(34px,7vw,100px);align-items:center}}
.hero-evidence__claim h1{{font-family:var(--sans);font-size:clamp(48px,6.5vw,92px);font-weight:650;line-height:1.02;letter-spacing:-.045em;margin:0 0 28px;max-width:9em}}
.hero-evidence__ledger{{border-left:2px solid var(--accent);padding-left:26px}}.hero-evidence__ledger .ledger-title{{font-size:10px;letter-spacing:.18em;color:var(--muted)}}.hero-evidence__ledger ul{{list-style:none;margin:16px 0 24px;padding:0}}.hero-evidence__ledger li{{display:grid;grid-template-columns:90px 90px 1fr;gap:12px;padding:14px 0;border-top:1px solid var(--line);font-size:12px}}.hero-evidence__ledger li span{{color:var(--muted)}}.hero-evidence__ledger li p{{margin:0;line-height:1.55}}.hero-evidence__media img{{aspect-ratio:16/10!important;object-fit:cover}}
.hero-route{{min-height:86svh;padding:clamp(56px,7vw,100px) 0;display:grid;grid-template-columns:minmax(0,.8fr) minmax(340px,1.2fr);grid-template-areas:"orientation routes" "media routes" "action routes";gap:28px clamp(30px,6vw,84px);align-items:start}}
.hero-route__orientation{{grid-area:orientation}}.hero-route__orientation h1{{font-size:clamp(46px,6vw,86px);line-height:1.02;letter-spacing:-.045em;margin:0 0 24px;font-weight:680;max-width:9em}}.hero-route__routes{{grid-area:routes;list-style:none;margin:0;padding:0;border-top:1px solid var(--ink)}}.route-item{{display:grid;grid-template-columns:48px 1fr 32px;gap:14px;align-items:center;padding:24px 0;border-bottom:1px solid var(--line);min-height:112px}}.route-item--1{{min-height:190px;background:rgba(255,255,255,.45);padding-left:20px;padding-right:14px}}.route-item strong{{font-size:clamp(22px,2.6vw,38px);font-weight:560}}.route-item p{{margin:8px 0 0;color:var(--muted);font-size:12px}}.route-index{{font-size:11px;color:var(--muted)}}.hero-route__media{{grid-area:media;max-width:74%}}.hero-route__media img{{aspect-ratio:16/7!important;object-fit:cover}}.hero-route__action{{grid-area:action}}
.variant-scene{{border-top:1px solid var(--line);position:relative}}.premium-scene{{animation:none}}
.service-field{{padding:clamp(70px,10vw,150px) 0;display:grid;grid-template-columns:minmax(0,.7fr) minmax(0,1.3fr);gap:clamp(32px,7vw,100px)}}.service-field__intro h2{{font-family:var(--serif);font-weight:500;font-size:clamp(38px,5vw,68px);line-height:1.04;margin:0 0 24px}}.service-field__intro>p:last-child{{line-height:1.85;color:#424944}}.service-field__routes{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0;border-top:1px solid var(--ink)}}.service-route{{min-height:180px;padding:22px;border-bottom:1px solid var(--line);border-right:1px solid var(--line);display:flex;flex-direction:column;justify-content:space-between}}.service-route--1{{grid-row:span 2;min-height:360px;background:rgba(255,255,255,.48)}}.service-route h3{{font-size:clamp(22px,2.4vw,34px);font-weight:600}}.service-route span,.service-route p{{font-size:11px;color:var(--muted)}}.service-field__media{{grid-column:2;margin-top:24px;max-width:70%;justify-self:end}}.service-field__media img{{aspect-ratio:3/2!important}}
.trust-ledger{{padding:clamp(64px,9vw,130px) 0;display:grid;grid-template-columns:minmax(0,.9fr) minmax(360px,1.1fr);gap:clamp(34px,7vw,90px)}}.trust-ledger h2{{font-size:clamp(36px,4.7vw,66px);font-weight:560;line-height:1.06;margin:0 0 24px}}.trust-ledger__table{{margin:0;border-top:2px solid var(--accent)}}.trust-ledger__table div{{display:grid;grid-template-columns:1fr auto;gap:20px;padding:20px 0;border-bottom:1px solid var(--line)}}.trust-ledger dt{{color:var(--muted)}}.trust-ledger dd{{margin:0;font-weight:650}}.trust-ledger__media{{grid-column:2;max-width:62%;justify-self:end}}.trust-ledger__media img{{aspect-ratio:1/1!important}}
.proof-thread{{padding:clamp(70px,10vw,148px) 0;display:grid;grid-template-columns:minmax(0,.75fr) minmax(0,1.25fr);gap:clamp(40px,8vw,110px)}}.proof-thread h2{{font-family:var(--serif);font-size:clamp(38px,5vw,68px);font-weight:500;line-height:1.05;margin:0 0 24px}}.proof-thread__rail{{border-left:1px solid var(--accent);padding-left:30px}}.proof-thread__node{{padding:0 0 34px;position:relative}}.proof-thread__node:before{{content:"";position:absolute;width:9px;height:9px;background:var(--accent);border-radius:50%;left:-35px;top:4px}}.proof-thread__node span{{font-size:10px;color:var(--muted);letter-spacing:.15em}}.proof-thread__node p{{font-size:20px;line-height:1.6}}.proof-thread__media{{grid-column:2;max-width:72%}}
.tension-scene{{padding:clamp(70px,10vw,154px) 0;display:grid;grid-template-columns:minmax(0,1.15fr) minmax(320px,.85fr);gap:clamp(36px,7vw,96px);align-items:end}}.tension-scene blockquote{{font-family:var(--serif);font-size:clamp(38px,5.4vw,76px);line-height:1.08;margin:0;letter-spacing:-.035em}}.tension-scene__resolution h2{{font-size:clamp(30px,3.5vw,48px);line-height:1.12;margin:0 0 20px}}.tension-scene__media{{grid-column:1/3;margin-top:26px;max-width:70%}}.tension-scene__media img{{aspect-ratio:16/8!important}}
.causal-story{{padding:clamp(68px,9vw,130px) 0}}.causal-story h2{{font-size:clamp(36px,4.5vw,62px);line-height:1.08;margin:0 0 22px}}.causal-story__rail{{display:flex;list-style:none;padding:40px 0 0;margin:0;border-top:1px solid var(--ink)}}.causal-story__rail li{{flex:1;padding:20px;border-right:1px solid var(--line);font-size:18px}}
.process-sequence{{padding:clamp(70px,9vw,138px) 0;display:grid;grid-template-columns:minmax(0,.72fr) minmax(0,1.28fr);gap:clamp(36px,7vw,100px)}}.process-sequence h2{{font-family:var(--serif);font-size:clamp(36px,4.8vw,66px);font-weight:500;line-height:1.06;margin:0 0 22px}}.process-sequence__steps{{list-style:none;margin:0;padding:0;border-top:1px solid var(--ink)}}.process-sequence__steps li{{display:grid;grid-template-columns:54px 1fr;gap:18px;padding:24px 0;border-bottom:1px solid var(--line)}}.process-sequence__steps span{{font-size:11px;color:var(--muted)}}.process-sequence__steps p{{margin:8px 0 0;line-height:1.7;color:#48504a}}.process-sequence__media{{grid-column:2;max-width:76%;justify-self:end}}
.human-evidence{{padding:clamp(70px,9vw,140px) 0;display:grid;grid-template-columns:minmax(320px,.9fr) minmax(0,1.1fr);gap:clamp(36px,7vw,90px);align-items:center}}.human-evidence__portrait img{{aspect-ratio:3/4!important}}
.atmosphere-gallery{{padding:clamp(60px,7vw,108px) 0;display:grid;grid-template-columns:repeat(12,1fr)}}.atmosphere-gallery__dominant{{grid-column:1/11}}.atmosphere-gallery__dominant img{{aspect-ratio:16/8!important}}.atmosphere-gallery__caption{{grid-column:8/13;margin-top:-90px;background:var(--paper);padding:34px;z-index:2}}
.action-event{{padding:clamp(62px,8vw,118px) 0;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:36px;align-items:end}}.action-event h2{{font-size:clamp(38px,4.6vw,64px);line-height:1.05;margin:0 0 20px}}
.variant-cta{{margin:0 calc(-1 * clamp(20px,5vw,80px));padding:clamp(72px,9vw,136px) clamp(20px,5vw,80px);background:#e6e1d7;display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,.7fr);gap:clamp(34px,7vw,90px);align-items:end}}.variant-cta h2{{font-family:var(--serif);font-size:clamp(42px,5.5vw,78px);line-height:1.02;font-weight:500;margin:0 0 22px}}
.ending-utility{{padding:60px 0 40px;display:grid;grid-template-columns:1fr 1fr;gap:40px;border-top:1px solid var(--ink)}}.ending-utility h2{{font-size:clamp(28px,3.5vw,48px);margin:0}}.ending-utility dl{{margin:0}}.ending-utility dl div{{display:flex;justify-content:space-between;padding:14px 0;border-bottom:1px solid var(--line)}}.ending-utility dd{{margin:0}}
.ending-emotional{{min-height:50svh;margin:0 calc(-1 * clamp(20px,5vw,80px));padding:clamp(90px,12vw,170px) clamp(20px,5vw,80px);display:flex;flex-direction:column;justify-content:center;align-items:flex-start;background:#1b1e1c;color:#f5f2ea}}.ending-emotional h2{{font-family:var(--serif);font-weight:500;font-size:clamp(48px,7vw,100px);line-height:.98;margin:0 0 28px;max-width:9em}}.ending-emotional p:last-child{{max-width:34rem;line-height:1.8;color:#c9d0cb}}
.variant-footer{{min-height:78px;display:flex;align-items:center;justify-content:space-between;gap:18px;font-size:11px;color:var(--muted)}}
@keyframes recognition-focus{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}@keyframes ledger-reveal{{from{{opacity:0;transform:translateX(10px)}}to{{opacity:1;transform:none}}}}@keyframes route-reveal{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
.hero-recognition__copy{{animation:recognition-focus .55s ease-out both}}.hero-evidence__ledger{{animation:ledger-reveal .48s ease-out both}}.hero-route__routes{{animation:route-reveal .48s ease-out both}}
@media(max-width:900px){{.hero-recognition{{min-height:auto;grid-template-columns:1fr;padding:46px 0 64px}}.hero-recognition__media,.hero-recognition__copy{{grid-column:1;grid-row:auto}}.hero-recognition__media{{min-height:360px;order:0}}.hero-recognition__copy{{padding:30px 0;background:none;order:1}}.hero-recognition__side-note{{display:none}}.hero-evidence{{grid-template-columns:1fr;gap:34px;min-height:auto}}.hero-route{{grid-template-columns:1fr;grid-template-areas:"orientation" "routes" "media" "action";min-height:auto}}.hero-route__media{{max-width:100%}}.service-field,.trust-ledger,.proof-thread,.tension-scene,.process-sequence,.human-evidence,.action-event,.variant-cta,.ending-utility{{grid-template-columns:1fr}}.service-field__media,.trust-ledger__media,.proof-thread__media,.tension-scene__media,.process-sequence__media{{grid-column:1;justify-self:auto;max-width:100%}}.atmosphere-gallery__dominant{{grid-column:1/13}}.atmosphere-gallery__caption{{grid-column:2/13;margin-top:-44px}}}}
@media(max-width:430px){{.variant-page{{padding:0 20px}}.variant-header{{min-height:66px}}.variant-header span{{display:none}}.hero-recognition h1,.hero-evidence h1,.hero-route h1{{font-size:clamp(40px,13vw,54px)}}.hero-evidence__ledger li{{grid-template-columns:70px 70px 1fr;gap:8px}}.route-item{{grid-template-columns:38px 1fr 22px;padding:18px 0;min-height:92px}}.route-item--1{{min-height:146px;padding-left:12px}}.service-field__routes{{grid-template-columns:1fr}}.service-route--1{{grid-row:auto;min-height:180px}}.service-route{{border-right:0}}.variant-scene{{padding-top:64px;padding-bottom:64px}}.variant-scene h2,.variant-cta h2{{font-size:clamp(34px,10.5vw,46px)}}.tension-scene blockquote{{font-size:clamp(34px,10.5vw,48px)}}.causal-story__rail{{flex-direction:column}}.causal-story__rail li{{border-right:0;border-bottom:1px solid var(--line)}}.variant-cta{{margin:0 -20px;padding:72px 20px}}.variant-action-group{{align-items:stretch}}.variant-action,.variant-action-secondary{{width:100%;min-width:0}}.ending-emotional{{margin:0 -20px;padding:90px 20px}}.ending-emotional h2{{font-size:clamp(42px,13vw,58px)}}.variant-footer{{flex-direction:column;align-items:flex-start;padding:24px 0}}}}
@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}*,*::before,*::after{{animation:none!important;transition:none!important;transform:none!important}}}}
{asset_binding_css()}
'''


def render_variant_faithful_page(plan: Mapping[str, Any], directives: Mapping[str, Any], asset_bindings: Mapping[str, Mapping[str, Any]], ensemble: Mapping[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    before = plan_digest(plan)
    ensemble = deepcopy(dict(ensemble or select_variant_ensemble(plan, directives, asset_bindings)))
    hero_trace = ensemble["hero"]
    hero_variant = hero_trace["selected_production_variant_id"]
    hero_renderer = _RENDERERS.get(hero_variant)
    if hero_renderer is None:
        raise ProductionVariantBridgeError(f"NO_HERO_RENDERER:{hero_variant}")
    hero_html = hero_renderer(plan, hero_trace, asset_bindings)
    scene_html = [_render_variant(plan, trace, asset_bindings) for trace in ensemble["scenes"]]
    cta_html = _render_cta_variant(plan, ensemble["cta"])
    ending_variant = ensemble["ending"]["selected_production_variant_id"]
    if ending_variant == "PV-END-UTILITY-CLOSURE-v1":
        ending_html = _render_ending_utility(plan, ensemble["ending"])
    elif ending_variant == "PV-END-EMOTIONAL-RESOLUTION-v1":
        ending_html = _render_ending_emotional(plan, ensemble["ending"])
    else:
        raise ProductionVariantBridgeError(f"NO_ENDING_RENDERER:{ending_variant}")
    company_name = _company_name(plan)
    spine = ensemble["page_art_direction_spine"]
    css = _css(spine)
    html_text = f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_esc(company_name)}</title><style>{css}</style></head><body data-production-authority="composition_plan" data-premium-authorship="issue116" data-production-variant-bridge="issue121"><main class="variant-page premium-shell" data-voice="{_esc(spine["type_authority_strategy"])}" data-spine-digest="{_esc(spine["spine_digest"])}"><header class="variant-header"><strong>{_esc(company_name)}</strong><span>RESEARCH-DERIVED PRODUCTION VARIANTS</span></header>{hero_html}{''.join(scene_html)}{cta_html}{ending_html}<footer class="variant-footer"><span>{_esc(company_name)}</span><span>確認済み情報と権利条件を優先して構成しています。</span></footer></main></body></html>'''
    if plan_digest(plan) != before:
        raise ProductionVariantBridgeError("VARIANT_RENDERER_MUTATED_COMPOSITION_PLAN")
    trace = deepcopy(ensemble)
    trace["renderer"] = {"schema_version": "issue121_variant_renderer_trace_v1", "final_visual_authority": "production_variant_dispatch", "legacy_generic_premium_scene_final_authority": False, "silent_generic_fallback": False, "shared_primitives_scope": ["reset", "accessibility", "asset safety/provenance", "focus behavior", "responsive safety", "semantic line-break safety"], "html_sha256": hashlib.sha256(html_text.encode("utf-8")).hexdigest()}
    return html_text, trace


def registry_manifest() -> dict[str, Any]:
    return {"schema_version": "issue121_production_variant_registry_v1", "patterns": sorted(PATTERN_TO_VARIANT), "variants": deepcopy(VARIANT_REGISTRY), "all_renderer_identities_implemented": all(_text(row.get("renderer_implementation_identity")) and row.get("renderer_implementation_identity") != "UNIMPLEMENTED_REQUIRED" for row in VARIANT_REGISTRY.values()), "unknown_variant_policy": "FAIL_CLOSED", "identity_routing": False, "random_diversity": False}


__all__ = ["WIDTHS", "MOBILE_WIDTHS", "VARIANT_REGISTRY", "PATTERN_TO_VARIANT", "ProductionVariantBridgeError", "build_decision_signature", "select_variant_ensemble", "compile_page_art_direction_spine", "render_variant_faithful_page", "registry_manifest"]
