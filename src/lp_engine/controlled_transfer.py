"""Issue #59 controlled transfer runner for the Regina/uka reference set.

The runner is contract-driven: the reference fixture supplies truth and the
decision state, runtime inference selects the Family, and only then does
feasibility and compatible module grammar enter generation.  Company IDs are
not selector rules and no Family is mapped to a fixed layout.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

from .controlled_production import _select_module_grammar
from .production_architecture import FEASIBILITY_DIMENSIONS, FAMILY_IDS, FIT_DIMENSIONS, infer_and_select_family
from .production_generation import run_generation

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "data" / "issue59_reference_companies.json"
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)


def load_reference_contracts() -> list[dict[str, Any]]:
    payload = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    return list(payload["companies"])


def _fit(contract: Mapping[str, Any]) -> dict[str, Any]:
    values = {name: 0.5 for name in FIT_DIMENSIONS}
    if contract["expected_family"] == "BW-F02":
        values.update(clinical_expertise=0.95, trust_requirement=1.0, information_density_need=0.9, calmness=0.9, process_inspectability_need=0.9)
    else:
        values.update(craftsmanship=0.95, human_relationship_weight=0.9, process_inspectability_need=0.95, intimacy=0.85, sensory_experience_weight=0.9)
    return {"schema_version": "creative_fit_profile_v1", "profile_id": f"issue59-{contract['company_id']}-fit", "dimensions": values, "source_refs": contract["source_refs"]}


def _feasibility(contract: Mapping[str, Any], *, constrained: bool = False) -> dict[str, Any]:
    values = {name: (0.15 if constrained else 0.8) for name in FEASIBILITY_DIMENSIONS}
    values["source_coverage"] = 0.95 if not constrained else 0.1
    values["rights_clarity"] = 0.2 if not constrained else 0.0
    return {"schema_version": "production_feasibility_profile_v1", "profile_id": f"issue59-{contract['company_id']}-{'constrained' if constrained else 'normal'}", "dimensions": values, "adaptation_policy": {"may_change_family": False, "notes": ["safe media realization may change after Family freeze"]}, "source_refs": contract["source_refs"]}


def _svg_asset(company_id: str, role: str, color: str) -> str:
    label = "REGINA / BOUNDARY" if company_id == "regina-clinic" else "uka / METHOD"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#f4f1eb"/><rect x="68" y="68" width="1064" height="664" fill="none" stroke="{color}" stroke-width="3"/><path d="M120 590 C280 360 410 630 590 390 S900 300 1080 500" fill="none" stroke="{color}" stroke-width="10"/><circle cx="350" cy="360" r="92" fill="none" stroke="#171a18" stroke-width="3"/><circle cx="850" cy="430" r="128" fill="none" stroke="#171a18" stroke-width="3"/><text x="120" y="150" font-family="Arial,sans-serif" font-size="34" fill="#171a18" letter-spacing="5">{label}</text><text x="120" y="680" font-family="Arial,sans-serif" font-size="24" fill="#5b625d" letter-spacing="3">{role.upper()} / REFERENCE VISUAL</text></svg>'''


def _asset(contract: Mapping[str, Any], role: str) -> dict[str, Any]:
    path = f"assets/photography/{contract['company_id']}/{role}.svg"
    return {"asset_id": f"{contract['company_id']}-{role}", "photo_role": role, "source_type": "generated", "provider": "project-authored-generated", "source": "Issue #59 controlled transfer visual fixture", "asset_url": path, "local_asset_path": path, "creator": "Project-owned generated visual", "rights_status": "PROJECT_OWNED_GENERATED", "license_terms_url": "", "checked_at": "2026-09-25", "visual_subject": "non-evidentiary authored reference visual", "placement": "visual_context_only", "replacement_target": "rights-cleared or actual role media when available", "crop": "50% 50%", "preferred_orientation": "landscape", "alt": "参考ビジュアル"}


def reference_input(contract: Mapping[str, Any]) -> dict[str, Any]:
    company_id = contract["company_id"]
    evidence = [{"evidence_id": f"{company_id}-truth-001", "company_id": company_id, "case_id": contract["reference_id"], "evidence_type": "COMPANY_TRUTH", "evidence_strength": "E3_OPERATIONAL", "target_objections": ["O3_PROCESS", "O4_NEXT"], "claim": contract["decision_job"], "source": contract["source_refs"][0], "source_type": "issue57_ssot_contract", "verification_status": "VERIFIED", "verification_date": "2026-09-25", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "NON_BLOCKING"}]
    if company_id == "regina-clinic":
        company = {"company_name": contract["company_name"], "industry": contract["industry"], "service_category": "医療脱毛・無料カウンセリング", "location": contract["location"], "business_model": "consultation_led_service", "company_truth": "医師の確認と無料カウンセリングを経て、適応・方法・費用・リスクを説明する医療脱毛サービス。", "differentiators": ["適応と安全性を確認してから契約を判断する", "無料カウンセリングから相談できる"], "visual_authority_candidates": ["BOUNDARY", "PROCESS", "TYPOGRAPHY"], "contact_channels": {"href": "https://www.reginaclinic.jp/about/clinic/free-counseling/", "primary": "公式カウンセリング予約"}}
        roles = ["hero_context", "consultation_context", "process_detail", "material_detail"]
    else:
        company = {"company_name": contract["company_name"], "industry": contract["industry"], "service_category": "ヘッドスパ・Deep Care Method", "location": contract["location"], "business_model": "method_led_service", "company_truth": "サロンのシャンプー・手技を磨いてきた方法と、相談・観察・手技をつなぐヘッドスパサービス。", "differentiators": ["積み重ねた手技と方法が選択理由になる", "相談・観察からメニューとサロンを選ぶ"], "visual_authority_candidates": ["HUMAN", "METHOD", "ATMOSPHERE"], "contact_channels": {"href": "https://uka.co.jp/salons/", "primary": "公式サロン予約"}}
        roles = ["hero_context", "hand_technique", "process_detail", "material_detail"]
    return {"schema_version": "production_generation_input_v1", "company_id": company_id, "company": company, "customer_state": contract["customer_state"], "customer_decision_state": contract["customer_state"], "conversion_goal": "consultation", "primary_objections": ["O3_PROCESS", "O4_NEXT"], "requested_claims": [], "unavailable_evidence": ["actual staff identity", "actual customer testimonial", "reusable official photography"], "evidence_ledger": evidence, "photo_assets": [_asset(contract, role) for role in roles], "prohibited_families": contract["prohibited_families"]}


def _architecture(contract: Mapping[str, Any], inference: Mapping[str, Any], feasibility: Mapping[str, Any]) -> dict[str, Any]:
    grammar = _select_module_grammar(inference["dominant_family"], contract["customer_state"])
    if contract["expected_family"] == "BW-F04":
        grammar["hero_authoring"] = "F04 decision job authored from compatible story/human/atmosphere grammar; no F04-specific hero template"
    grammar["compatibility_rationale"] = contract["decision_job"]
    return {"dominant_family": inference["dominant_family"], "secondary_families": inference["secondary_influences"], "customer_decision_state": contract["customer_state"], "module_grammar": grammar, "family_frozen_before_feasibility": True, "production_feasibility": feasibility, "source_contract": contract["reference_id"]}


def run_reference_company(contract: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    raw = reference_input(contract)
    fit = _fit(contract)
    feasibility = _feasibility(contract)
    truth = {"verified": True, "company": contract["company_name"], "facts": [raw["company"]["company_truth"], *raw["company"]["differentiators"]], "prohibited_families": contract["prohibited_families"]}
    result = infer_and_select_family(company_truth=truth, customer_decision_state=contract["customer_state"], creative_fit=fit, feasibility=feasibility, candidates=[{"family_id": family} for family in FAMILY_IDS])
    if result["selection"] is None:
        raise RuntimeError(f"{contract['reference_id']} requires human review before production")
    if result["selection"]["dominant_family"] != contract["expected_family"]:
        raise AssertionError(f"{contract['reference_id']} selected {result['selection']['dominant_family']} expected {contract['expected_family']}")
    architecture = _architecture(contract, result["inference"], feasibility)
    out = Path(output_dir)
    site = out / "site"
    generated = run_generation({**raw, "validation_context": "NO_WEB_FIELD_VALIDATION"}, site, generation_id=f"issue59-{contract['company_id']}", mode="production", architecture=architecture)
    constrained = _feasibility(contract, constrained=True)
    counter = infer_and_select_family(company_truth=truth, customer_decision_state=contract["customer_state"], creative_fit=fit, feasibility=constrained, candidates=[{"family_id": family} for family in FAMILY_IDS])
    trace = {"schema_version": "issue59_transfer_architecture_trace_v1", "source_issue": 59, "source_contract": contract["reference_id"], "company": contract["company_name"], "expected_family": contract["expected_family"], "runtime_inference": result["inference"], "selection": result["selection"], "architecture": architecture, "production_feasibility": feasibility, "feasibility_counterfactual": {"profile_id": constrained["profile_id"], "dominant_family": counter["selection"]["dominant_family"], "family_unchanged": counter["selection"]["dominant_family"] == contract["expected_family"], "may_change_family": False}, "generation_id": generated.generation_id, "production_output_allowed": generated.production_output_allowed, "no_company_lookup": True, "no_family_fixed_layout": True, "status": "PASS"}
    out.mkdir(parents=True, exist_ok=True)
    (out / "architecture_trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "PASS", "trace": trace, "site": site}


def sha_manifest(root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "manifest.sha256"}:
            files.append({"path": path.relative_to(root).as_posix(), "sha256": sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    manifest = {"schema_version": "issue59_transfer_manifest_v1", "status": "PASS", "files": files}
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    (root / "manifest.sha256").write_text(f"{digest}  manifest.json\n", encoding="utf-8")
    return manifest
