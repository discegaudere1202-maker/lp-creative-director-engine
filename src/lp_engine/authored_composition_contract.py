"""Generalized authored-composition contract.

This module is a planning boundary for Issue #89. It derives an authored plan
from normalized truth and decision inputs, never from company identity or
reference names. Rendering integration remains a separate migration step.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping, Sequence


RESPONSIVE_WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
REQUIRED_INPUT_KEYS = (
    "company_truth",
    "customer_decision_state",
    "creative_family",
    "evidence",
    "media_roles",
)
DECISION_JOBS = {"choose", "understand", "trust", "compare", "prepare", "act"}
CONFIDENCE_VALUES = {"verified", "provisional", "unknown", "contradictory"}
MEDIA_ROLES = {
    "person",
    "touch",
    "space",
    "process",
    "learning",
    "material",
    "choice",
    "after",
}


class ContractError(ValueError):
    """Raised when the normalized authored-composition input is invalid."""


def _text(value: Any) -> str:
    return str(value or "").strip()


def _sorted_unique(values: Sequence[Any]) -> list[str]:
    return sorted({_text(value) for value in values if _text(value)})


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _truth_value(value: Any, *, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError(f"{field} must be a truth value object")
    confidence = _text(value.get("confidence"))
    if confidence not in CONFIDENCE_VALUES:
        raise ContractError(f"{field}.confidence is invalid")
    sources = value.get("sources", [])
    if not isinstance(sources, list):
        raise ContractError(f"{field}.sources must be a list")
    return {
        "value": deepcopy(value.get("value")),
        "confidence": confidence,
        "sources": deepcopy(sources),
        "notes": list(value.get("notes") or []),
    }


def _normalize_company_truth(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("company_truth must be an object")
    required = ("category", "name", "offers")
    for field in required:
        if field not in value:
            raise ContractError(f"company_truth.{field} is required")
    offers = value.get("offers")
    if not isinstance(offers, list):
        raise ContractError("company_truth.offers must be a list")
    normalized = {
        "category": _truth_value(value["category"], field="company_truth.category"),
        "name": _truth_value(value["name"], field="company_truth.name"),
        "offers": [],
    }
    for index, offer in enumerate(offers):
        if not isinstance(offer, Mapping):
            raise ContractError(f"company_truth.offers[{index}] must be an object")
        if not _text(offer.get("id")) or not _text(offer.get("job")):
            raise ContractError(f"company_truth.offers[{index}] requires id and job")
        normalized["offers"].append(deepcopy(dict(offer)))
    for field in ("location", "contact", "hours", "philosophy", "qualifications", "reviews"):
        if field in value and value[field] is not None:
            normalized[field] = _truth_value(value[field], field=f"company_truth.{field}")
    normalized["unknowns"] = _sorted_unique(value.get("unknowns") or [])
    return normalized


def _normalize_decision(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("customer_decision_state must be an object")
    job = _text(value.get("primary_job"))
    stage = _text(value.get("decision_stage"))
    risk = _text(value.get("risk_sensitivity"))
    if job not in DECISION_JOBS:
        raise ContractError("customer_decision_state.primary_job is invalid")
    if stage not in {"discover", "consider", "validate", "ready"}:
        raise ContractError("customer_decision_state.decision_stage is invalid")
    if risk not in {"low", "medium", "high"}:
        raise ContractError("customer_decision_state.risk_sensitivity is invalid")
    return {
        "primary_job": job,
        "tensions": _sorted_unique(value.get("tensions") or []),
        "questions": _sorted_unique(value.get("questions") or []),
        "risk_sensitivity": risk,
        "decision_stage": stage,
    }


def _normalize_family(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("creative_family must be an object")
    family_id = _text(value.get("family_id"))
    version = _text(value.get("version"))
    if not family_id or not version or value.get("frozen") is not True:
        raise ContractError("creative_family requires family_id, version, and frozen=true")
    rationale = _sorted_unique(value.get("rationale") or [])
    if not rationale:
        raise ContractError("creative_family.rationale is required")
    return {
        "family_id": family_id,
        "version": version,
        "rationale": rationale,
        "frozen": True,
    }


def _normalize_evidence(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("evidence must be an object")
    facts = value.get("facts", [])
    if not isinstance(facts, list):
        raise ContractError("evidence.facts must be a list")
    normalized_facts = []
    for index, fact in enumerate(facts):
        if not isinstance(fact, Mapping):
            raise ContractError(f"evidence.facts[{index}] must be an object")
        if not _text(fact.get("id")) or not _text(fact.get("claim")):
            raise ContractError(f"evidence.facts[{index}] requires id and claim")
        confidence = _text(fact.get("confidence", "unknown"))
        if confidence not in CONFIDENCE_VALUES:
            raise ContractError(f"evidence.facts[{index}].confidence is invalid")
        normalized_facts.append({
            "id": _text(fact["id"]),
            "claim": _text(fact["claim"]),
            "scope": _text(fact.get("scope", "company")),
            "sources": _sorted_unique(fact.get("sources") or []),
            "confidence": confidence,
            "usable_for_persuasion": bool(fact.get("usable_for_persuasion", False)),
        })
    return {
        "facts": normalized_facts,
        "proof_gaps": _sorted_unique(value.get("proof_gaps") or []),
        "contradictions": _sorted_unique(value.get("contradictions") or []),
    }


def _normalize_media_roles(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ContractError("media_roles must be a list")
    result = []
    for index, role in enumerate(value):
        if not isinstance(role, Mapping):
            raise ContractError(f"media_roles[{index}] must be an object")
        role_name = _text(role.get("role"))
        if role_name not in MEDIA_ROLES:
            raise ContractError(f"media_roles[{index}].role is invalid")
        rights = _text(role.get("rights", "unknown"))
        if rights not in {"owned", "licensed", "generated", "unknown"}:
            raise ContractError(f"media_roles[{index}].rights is invalid")
        result.append({
            "role_id": _text(role.get("role_id")) or f"role-{index + 1}",
            "role": role_name,
            "required_content_class": _text(role.get("required_content_class")),
            "actual_proof": False,
            "rights": rights,
        })
    return result


def normalize_authorship_input(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ContractError("authorship input must be an object")
    missing = [key for key in REQUIRED_INPUT_KEYS if key not in raw]
    if missing:
        raise ContractError("missing required input: " + ", ".join(missing))
    return {
        "company_truth": _normalize_company_truth(raw["company_truth"]),
        "customer_decision_state": _normalize_decision(raw["customer_decision_state"]),
        "creative_family": _normalize_family(raw["creative_family"]),
        "evidence": _normalize_evidence(raw["evidence"]),
        "media_roles": _normalize_media_roles(raw["media_roles"]),
        "offer_conditions": deepcopy(dict(raw.get("offer_conditions") or {})),
        "renderer_capabilities": _sorted_unique(raw.get("renderer_capabilities") or []),
    }


def _usable_facts(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        fact for fact in evidence["facts"]
        if fact["usable_for_persuasion"] and fact["confidence"] == "verified"
    ]


def _has_role(roles: Sequence[Mapping[str, Any]], *names: str) -> bool:
    return any(_text(role.get("role")) in names for role in roles)


def _scene_intents(inp: Mapping[str, Any]) -> list[dict[str, Any]]:
    decision = inp["customer_decision_state"]
    offers = inp["company_truth"]["offers"]
    job = decision["primary_job"]
    intents = [{"id": "recognize", "intent": "recognize", "required_facts": []}]
    if job in {"choose", "compare"} or len(offers) > 1:
        intents.append({"id": "choose", "intent": "choose", "required_facts": []})
    if job in {"understand", "prepare"}:
        intents.append({"id": "understand", "intent": "understand", "required_facts": []})
    if decision["risk_sensitivity"] in {"medium", "high"}:
        intents.append({"id": "trust", "intent": "trust", "required_facts": [fact["id"] for fact in _usable_facts(inp["evidence"])[:3]]})
    if job in {"compare", "trust", "understand"} and len(offers) > 1:
        intents.append({"id": "compare", "intent": "compare", "required_facts": []})
    intents.append({"id": "act", "intent": "act", "required_facts": []})
    seen = set()
    result = []
    for item in intents:
        if item["id"] not in seen:
            result.append({**item, "source_decision": job})
            seen.add(item["id"])
    return result


def _topology(inp: Mapping[str, Any], scene_ids: Sequence[str]) -> dict[str, str]:
    decision = inp["customer_decision_state"]
    evidence = inp["evidence"]
    roles = inp["media_roles"]
    offer_count = len(inp["company_truth"]["offers"])
    proof_count = len(_usable_facts(evidence))
    job = decision["primary_job"]
    hero = "text_led_field"
    if _has_role(roles, "space", "person") and proof_count:
        hero = "relationship_media"
    elif offer_count > 1 or job in {"choose", "compare"}:
        hero = "guided_choice"
    core = "comparison_rail" if offer_count > 1 else "single_offer_sequence"
    if proof_count >= 3 and _has_role(roles, "process", "material"):
        core = "evidence_process_spread"
    trust = "fact_ledger" if proof_count else "transparent_unknowns"
    if _has_role(roles, "person", "process"):
        trust = "human_process"
    closing = "direct_action" if decision["decision_stage"] == "ready" else "guided_action"
    if decision["primary_job"] == "trust":
        closing = "reassurance_then_action"
    return {
        "hero": hero,
        "core_decision": core,
        "trust_proof": trust,
        "closing": closing,
        "scene_order": ",".join(scene_ids),
    }


def _variation(inp: Mapping[str, Any], topology: Mapping[str, str]) -> dict[str, str]:
    decision = inp["customer_decision_state"]
    roles = inp["media_roles"]
    evidence_count = len(_usable_facts(inp["evidence"]))
    return {
        "hero_topology": topology["hero"],
        "visual_authority": "media" if _has_role(roles, "person", "space", "process") else "copy",
        "type_voice": "direct_commercial" if decision["primary_job"] in {"choose", "act"} else "human_editorial",
        "density_rhythm": "dense_proof" if evidence_count >= 3 else "open_transparency",
        "media_cadence": "continuous" if len(roles) >= 3 else "interstitial",
        "interaction_mode": "guided_choice" if decision["primary_job"] in {"choose", "compare"} else "progressive_disclosure",
        "closing_choreography": topology["closing"],
        "mobile_composition": "stacked_chapters" if decision["risk_sensitivity"] == "high" else "decision_first_stack",
    }


def _review_reasons(inp: Mapping[str, Any], topology: Mapping[str, str]) -> list[str]:
    reasons = []
    truth = inp["company_truth"]
    evidence = inp["evidence"]
    if truth["name"]["confidence"] != "verified" or truth["category"]["confidence"] != "verified":
        reasons.append("insufficient_verified_company_truth")
    if evidence["contradictions"]:
        reasons.append("contradictory_evidence")
    if any(fact["confidence"] != "verified" for fact in evidence["facts"] if fact["usable_for_persuasion"]):
        reasons.append("unsupported_persuasion_claim")
    if not inp["company_truth"].get("contact") or inp["company_truth"]["contact"]["confidence"] != "verified":
        reasons.append("unverified_cta_destination")
    if topology["hero"] == "relationship_media" and not _has_role(inp["media_roles"], "person", "space"):
        reasons.append("ambiguous_media_authority")
    for role in inp["media_roles"]:
        if role["rights"] == "unknown":
            reasons.append("media_rights_unknown")
            break
    return sorted(set(reasons))


def _feasibility(inp: Mapping[str, Any], topology: Mapping[str, str]) -> dict[str, Any]:
    missing = []
    downgraded = []
    for role in inp["media_roles"]:
        if not role["required_content_class"] or role["rights"] == "unknown":
            missing.append(role["role_id"])
            downgraded.append(role["role"])
    return {
        "family_id": inp["creative_family"]["family_id"],
        "missing_media_roles": missing,
        "downgraded_roles": sorted(set(downgraded)),
        "preserved_scene_intents": [item["id"] for item in _scene_intents(inp)],
        "blocked_claims": [
            fact["id"] for fact in inp["evidence"]["facts"]
            if fact["confidence"] != "verified" or not fact["usable_for_persuasion"]
        ],
        "responsive_widths": list(RESPONSIVE_WIDTHS),
        "topology_preserved": True,
    }


def infer_authored_composition(raw: Mapping[str, Any]) -> dict[str, Any]:
    inp = normalize_authorship_input(raw)
    scenes = _scene_intents(inp)
    topology = _topology(inp, [item["id"] for item in scenes])
    plan = {
        "contract_version": "authored_composition_contract_v1",
        "input": inp,
        "family_id": inp["creative_family"]["family_id"],
        "family_version": inp["creative_family"]["version"],
        "family_frozen": True,
        "scene_intents": scenes,
        "topology": topology,
        "variation_vector": _variation(inp, topology),
        "media_cadence": {
            "roles": [role["role"] for role in inp["media_roles"]],
            "required_content_classes": [role["required_content_class"] for role in inp["media_roles"] if role["required_content_class"]],
        },
        "responsive_authorship": {
            "widths": list(RESPONSIVE_WIDTHS),
            "rules": {
                "narrow": "preserve_decision_job_and_reflow_interaction",
                "tablet": "preserve_primary_authority_and_reduce_density",
                "desktop": "preserve_scene_order_and_expand_context",
            },
        },
    }
    plan["fit_trace"] = {
        "inputs": ["customer_decision_state", "company_truth.offers", "evidence", "media_roles"],
        "family_selection": "frozen_input_only",
        "identity_used": False,
        "reference_lookup_used": False,
    }
    plan["feasibility"] = _feasibility(inp, topology)
    reasons = _review_reasons(inp, topology)
    plan["review_gate"] = {
        "status": "HUMAN_REVIEW_REQUIRED" if reasons else "AUTO_ELIGIBLE",
        "reasons": reasons,
    }
    return plan


def plan_digest(plan: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(plan).encode("utf-8")).hexdigest()


def assert_identity_invariance(base: Mapping[str, Any], changed: Mapping[str, Any]) -> None:
    left = deepcopy(dict(base))
    right = deepcopy(dict(changed))
    left["company_truth"]["name"] = deepcopy(left["company_truth"]["name"])
    right["company_truth"]["name"] = deepcopy(right["company_truth"]["name"])
    left["company_truth"]["name"]["value"] = "identity-a"
    right["company_truth"]["name"]["value"] = "identity-b"
    left["company_truth"]["name"]["sources"] = ["identity-a-source"]
    right["company_truth"]["name"]["sources"] = ["identity-b-source"]
    plan_left = infer_authored_composition(left)
    plan_right = infer_authored_composition(right)
    if plan_left["family_id"] != plan_right["family_id"] or plan_left["variation_vector"] != plan_right["variation_vector"]:
        raise AssertionError("composition changed because company identity changed")


def assert_decision_sensitivity(base: Mapping[str, Any], changed: Mapping[str, Any]) -> None:
    first = infer_authored_composition(base)
    second = infer_authored_composition(changed)
    if first["variation_vector"] == second["variation_vector"] and first["topology"] == second["topology"]:
        raise AssertionError("composition did not respond to decision-state mutation")


def assert_no_identity_routing(plan: Mapping[str, Any]) -> None:
    trace = plan.get("fit_trace") or {}
    if trace.get("identity_used") or trace.get("reference_lookup_used"):
        raise AssertionError("identity/reference routing is prohibited")
    if plan.get("family_id") in str(trace.get("selection_expression", "")):
        raise AssertionError("family selection may not be company-keyed")


__all__ = [
    "ContractError",
    "RESPONSIVE_WIDTHS",
    "assert_decision_sensitivity",
    "assert_identity_invariance",
    "assert_no_identity_routing",
    "infer_authored_composition",
    "normalize_authorship_input",
    "plan_digest",
]
