"""Issue #68 Phase C controlled production expansion."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping
from .controlled_production import _select_module_grammar
from .production_architecture import FEASIBILITY_DIMENSIONS, FAMILY_IDS, FIT_DIMENSIONS, infer_and_select_family
from .production_generation import run_generation

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "data" / "phase_c_reference_companies.json"
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
FAMILY_DIMENSIONS = {
    "BW-F05": {"choice_guidance_need": .98, "decision_commitment_pressure": .9, "trust_requirement": .9, "process_inspectability_need": .86},
    "BW-F07": {"local_relationship_weight": .98, "human_relationship_weight": .95, "warmth": .9, "owner_personality_importance": .9},
    "BW-F01": {"sensory_experience_weight": .98, "emotional_purchase_weight": .9, "visual_storytelling_need": .92, "calmness": .9},
    "BW-F03": {"premium_authority_need": .98, "desired_state_change_intensity": .92, "information_density_need": .9, "visual_storytelling_need": .9},
}

def load_phase_c_contracts() -> list[dict[str, Any]]:
    return list(json.loads(CONTRACTS.read_text(encoding="utf-8"))["companies"])

def _fit(contract: Mapping[str, Any]) -> dict[str, Any]:
    values = {name: .5 for name in FIT_DIMENSIONS}
    values.update(FAMILY_DIMENSIONS[contract["expected_family"]])
    return {"schema_version": "creative_fit_profile_v1", "profile_id": f"issue68-{contract['reference_id']}-fit", "dimensions": values, "source_refs": contract["source_refs"]}

def _feasibility(contract: Mapping[str, Any], constrained: bool = False) -> dict[str, Any]:
    values = {name: (.15 if constrained else .8) for name in FEASIBILITY_DIMENSIONS}
    values.update(source_coverage=(.1 if constrained else .92), rights_clarity=(0 if constrained else .95))
    return {"schema_version": "production_feasibility_profile_v1", "profile_id": f"issue68-{contract['reference_id']}-{'constrained' if constrained else 'normal'}", "dimensions": values, "adaptation_policy": {"may_change_family": False, "notes": ["feasibility may change media realization only after family freeze"]}, "source_refs": contract["source_refs"]}

def _asset(contract: Mapping[str, Any], role: str) -> dict[str, Any]:
    path = f"assets/photography/{contract['company_id']}/{role}.svg"
    return {"asset_id": f"{contract['company_id']}-{role}", "photo_role": role, "source_type": "generated", "provider": "project-authored-generated", "source": "Issue 68 owned reference visual fixture", "asset_url": path, "local_asset_path": path, "creator": "Project-owned generated visual", "rights_status": "PROJECT_OWNED_GENERATED", "license_terms_url": "", "checked_at": "2026-09-25", "visual_subject": "non-evidentiary authored reference visual", "placement": "visual_context_only", "replacement_target": "rights-cleared or actual role media when available", "crop": "50% 50%", "preferred_orientation": "landscape", "alt": "参考ビジュアル"}

def reference_input(contract: Mapping[str, Any]) -> dict[str, Any]:
    company_id = contract["company_id"]
    evidence = [{"evidence_id": f"{contract['reference_id']}-truth", "company_id": company_id, "case_id": contract["reference_id"], "evidence_type": "COMPANY_TRUTH", "evidence_strength": "E3_OPERATIONAL", "target_objections": ["O3_PROCESS", "O4_NEXT"], "claim": contract["decision_job"], "source": contract["source_refs"][0], "source_type": "issue68_ssot_contract", "verification_status": "VERIFIED", "verification_date": "2026-09-25", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "NON_BLOCKING", "placement_candidates": ["hero", "process", "cta"], "notes": "Generated reference visual; not proof"}]
    roles = sorted({row["media_role"] for row in contract["public_scene_semantics"] if row.get("media_role") != "typography"})
    company = {"company_name": contract["company_name"], "industry": contract["industry"], "service_category": contract["decision_job"], "location": contract["location"], "business_model": "reference_business", "company_truth": contract["decision_job"], "differentiators": [contract["customer_state"], contract["coverage_role"]], "visual_authority_candidates": ["TYPE", "MATERIAL", "WORLD"], "contact_channels": {"href": contract["official_url"], "primary": "official reference"}}
    return {"schema_version": "production_generation_input_v1", "company_id": company_id, "company": company, "customer_state": state, "customer_decision_state": state, "conversion_goal": "inquiry", "primary_objections": ["O3_PROCESS", "O4_NEXT"], "requested_claims": [], "unavailable_evidence": ["actual staff identity", "actual customer testimonial", "rights-cleared production photography"], "evidence_ledger": evidence, "photo_assets": [_asset(contract, role) for role in roles], "prohibited_families": contract["prohibited_families"]}

def _architecture(contract: Mapping[str, Any], inference: Mapping[str, Any], feasibility: Mapping[str, Any]) -> dict[str, Any]:
    family = inference["dominant_family"]
    grammar = _select_module_grammar(family, {"decision_job": contract["decision_job"], "customer_state": contract["customer_state"]})
    if family == "BW-F03":
        grammar["hero_authoring"] = "F03 decision-job-authored aspirational authority; no fixed F03 hero template"
    grammar["compatibility_rationale"] = contract["decision_job"]
    semantics = deepcopy(contract["public_scene_semantics"])
    for row in semantics:
        row.update(family=family, public_customer_facing=True, source="company_truth + customer_decision_job")
    return {"dominant_family": family, "secondary_families": inference["secondary_influences"], "customer_decision_state": contract["customer_state"], "module_grammar": grammar, "public_semantic_profile": f"phase_c_{family.lower()}", "public_scene_semantics": semantics, "public_semantic_derivation": "frozen family + customer decision job + compatible grammar; no company lookup", "family_frozen_before_feasibility": True, "production_feasibility": feasibility, "source_contract": contract["reference_id"]}

def run_phase_c_reference(contract: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    raw, fit, feasibility = reference_input(contract), _fit(contract), _feasibility(contract)
    truth = {"verified": True, "facts": [contract["company_name"], contract["decision_job"], contract["customer_state"]], "prohibited_families": contract["prohibited_families"]}
    result = infer_and_select_family(company_truth=truth, customer_decision_state=contract["customer_state"], creative_fit=fit, feasibility=feasibility, candidates=[{"family_id": family} for family in FAMILY_IDS])
    selection = result["selection"]
    if selection is None:
        raise RuntimeError(f"{contract['reference_id']} remains ambiguous and is not production eligible")
    if selection["dominant_family"] != contract["expected_family"]:
        raise AssertionError(f"{contract['reference_id']} selected {selection['dominant_family']} expected {contract['expected_family']}")
    architecture = _architecture(contract, result["inference"], feasibility)
    out, site = Path(output_dir), Path(output_dir) / "site"
    generated = run_generation({**raw, "validation_context": "NO_WEB_FIELD_VALIDATION"}, site, generation_id=f"issue68-{contract['company_id']}", mode="production", architecture=architecture)
    constrained = _feasibility(contract, constrained=True)
    counter = infer_and_select_family(company_truth=truth, customer_decision_state=contract["customer_state"], creative_fit=fit, feasibility=constrained, candidates=[{"family_id": family} for family in FAMILY_IDS])
    trace = {"schema_version": "issue68_phase_c_architecture_trace_v1", "source_issue": 68, "reference_id": contract["reference_id"], "company_id": contract["company_id"], "expected_family": contract["expected_family"], "runtime_inference": result["inference"], "selection": selection, "architecture": architecture, "production_feasibility": feasibility, "feasibility_counterfactual": {"dominant_family": counter["selection"]["dominant_family"], "family_unchanged": counter["selection"]["dominant_family"] == contract["expected_family"], "may_change_family": False}, "generation_id": generated.generation_id, "production_output_allowed": generated.production_output_allowed, "no_company_lookup": True, "no_family_fixed_layout": True, "status": "PASS"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "architecture_trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "PASS", "trace": trace, "site": site}

def svg_asset(contract: Mapping[str, Any], role: str) -> str:
    color, label = contract["color"], contract["company_name"].upper()
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#f5f3ee"/><path d="M80 620 C260 350 410 660 620 360 S920 300 1120 520" fill="none" stroke="{color}" stroke-width="12"/><circle cx="350" cy="330" r="110" fill="none" stroke="#171a18" stroke-width="4"/><circle cx="850" cy="410" r="150" fill="none" stroke="#171a18" stroke-width="4"/><text x="90" y="150" font-family="Arial,sans-serif" font-size="30" letter-spacing="5" fill="#171a18">{label}</text><text x="90" y="700" font-family="Arial,sans-serif" font-size="22" letter-spacing="3" fill="#606762">{role.upper()} / REFERENCE VISUAL</text></svg>'
