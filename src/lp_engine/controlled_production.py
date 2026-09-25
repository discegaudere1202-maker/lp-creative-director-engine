"""Controlled Production integration for Issue #53.

This is an intentionally narrow adapter: it runs the accepted runtime family
inference before the existing production generator, freezes the family, then
selects compatible composition grammar.  It does not turn a family into a
fixed layout and it stops before rendering when inference is ambiguous.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from .production_architecture import (
    FEASIBILITY_DIMENSIONS,
    FIT_DIMENSIONS,
    FAMILY_IDS,
    infer_and_select_family,
    load_json,
)
from .production_generation import run_generation

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data" / "production_architecture" / "module_composition_registry_v1.json"
NAGI_ASSET_ROOT = ROOT / "artifacts" / "round2u_b" / "site" / "assets"


def nagi_reference_input() -> dict[str, Any]:
    """Return the frozen, verified Nagi reference input used by Issue #53."""
    company_id = "nagi-no-mirai"
    return {
        "schema_version": "production_generation_input_v1",
        "company_id": company_id,
        "company": {
            "company_name": "なぎのみらい",
            "industry": "美容・健康",
            "service_category": "ヘッドスパ・スクール・ヒーリング",
            "location": "福岡市",
            "business_model": "local_service",
            "company_truth": "ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロンを案内する福岡市の事業者。",
            "differentiators": ["受ける・学ぶ・知るという3つの入口がある。", "公式Instagramから相談できる。"],
            "visual_authority_candidates": ["PERSON", "SENSORY", "TYPOGRAPHY"],
            "contact_channels": {"href": "https://www.instagram.com/happyfuture_02/", "instagram": "@happyfuture_02"},
        },
        "customer_state": {
            "before": "3つのサービスの違いが分からず、どこから相談すればよいか迷っている",
            "after": "自分の目的に近い入口から内容を確認できる",
            "barrier": "施術・スクール・ヒーリングの違いと最初の相談先が分からない",
        },
        "customer_decision_state": {
            "intent": "first-timer needs category education before choosing a service",
            "decision_job": "understand the category and compare the three service modes",
            "signal": "category education",
        },
        "conversion_goal": "consultation",
        "primary_objections": ["O3_PROCESS", "O4_NEXT"],
        "requested_claims": [],
        "unavailable_evidence": ["verified price", "duration", "qualifications", "testimonials", "actual venue photography"],
        "evidence_ledger": [
            {
                "evidence_id": "nagi-e-001", "company_id": company_id, "case_id": "nagi-reference-53",
                "evidence_type": "SERVICE_SCOPE", "evidence_strength": "E3_OPERATIONAL",
                "target_objections": ["O3_PROCESS"],
                "claim": "ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロンを案内しています。",
                "source": "https://www.instagram.com/happyfuture_02/", "source_type": "official_social_profile",
                "verification_status": "VERIFIED", "verification_date": "2026-09-15",
                "usage_status": "PRODUCTION_ELIGIBLE", "placement_candidates": ["HERO", "MIDDLE"],
                "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "NON_BLOCKING",
            },
            {
                "evidence_id": "nagi-e-002", "company_id": company_id, "case_id": "nagi-reference-53",
                "evidence_type": "PLACE_EXPERIENCE", "evidence_strength": "E2_SPECIFIC",
                "target_objections": ["O3_PROCESS"],
                "claim": "福岡市でサービスを案内しています。",
                "source": "https://www.instagram.com/happyfuture_02/", "source_type": "official_social_profile",
                "verification_status": "VERIFIED", "verification_date": "2026-09-15",
                "usage_status": "PRODUCTION_ELIGIBLE", "placement_candidates": ["HERO", "EARLY_PROOF"],
                "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "NON_BLOCKING",
            },
            {
                "evidence_id": "nagi-e-003", "company_id": company_id, "case_id": "nagi-reference-53",
                "evidence_type": "CTA_CHANNEL", "evidence_strength": "E5_DECISION_ENABLING",
                "target_objections": ["O4_NEXT"],
                "claim": "公式Instagram @happyfuture_02 から相談できます。",
                "source": "https://www.instagram.com/happyfuture_02/", "source_type": "official_social_profile",
                "verification_status": "VERIFIED", "verification_date": "2026-09-15",
                "usage_status": "PRODUCTION_ELIGIBLE", "placement_candidates": ["BEFORE_CTA", "CTA_ZONE"],
                "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "NON_BLOCKING",
            },
        ],
        "photo_assets": [
            _asset("hero_treatment_space", "hero_treatment_space.png", "landscape"),
            _asset("hand_technique", "hand_technique.jpg", "portrait"),
            _asset("sensory_detail", "sensory_detail.png", "square"),
            _asset("welcome_human", "welcome_human.png", "landscape"),
        ],
    }


def _asset(role: str, filename: str, orientation: str) -> dict[str, Any]:
    relative = f"assets/photography/nagi_no_mirai/{filename}"
    return {
        "asset_id": f"nagi-{role}", "photo_role": role, "source_type": "generated",
        "provider": "project-owned-generated", "source": f"data/photography/nagi_no_mirai_{role}_generation_v1.json",
        "asset_url": relative, "local_asset_path": relative, "creator": "OpenAI generated project asset",
        "rights_status": "RESEARCH_APPROVED_GENERATED_VISUAL", "license_terms_url": "",
        "checked_at": "2026-09-15", "visual_subject": role, "placement": "visual_context_only",
        "replacement_target": "actual Nagi visual when available", "crop": "50% 50%",
        "preferred_orientation": orientation, "alt": f"{role}の参考ビジュアル",
    }


def _creative_fit() -> dict[str, Any]:
    return {
        "schema_version": "creative_fit_profile_v1",
        "profile_id": "issue53-nagi-creative-fit",
        "dimensions": {name: 0.5 for name in FIT_DIMENSIONS},
        "source_refs": ["issue53:controlled-nagi-reference", "issue49:accepted-fit-contract"],
    }


def _feasibility() -> dict[str, Any]:
    return {
        "schema_version": "production_feasibility_profile_v1",
        "profile_id": "issue53-nagi-production-feasibility",
        "dimensions": {name: 0.5 for name in FEASIBILITY_DIMENSIONS},
        "adaptation_policy": {"may_change_family": False, "notes": ["select safe realization after family freeze"]},
        "source_refs": ["issue53:feasibility-separate-from-fit"],
    }


def _select_module_grammar(family: str, state: Mapping[str, Any]) -> dict[str, Any]:
    registry = load_json(REGISTRY)
    compatible = [row for row in registry["patterns"] if family in row.get("compatible_families", [])]
    desired = ("hero", "problem", "service", "cta")
    selected: list[dict[str, Any]] = []
    for role in desired:
        matches = [row for row in compatible if role in row["pattern_id"].lower() or role in row["name"].lower()]
        if matches:
            selected.append(matches[0])
    # The registry is a grammar, not a family->layout map. Fill missing roles
    # from compatible patterns in registry order, preserving provenance.
    for row in compatible:
        if row not in selected and len(selected) < 4:
            selected.append(row)
    return {
        "schema_version": "controlled_module_grammar_selection_v1",
        "family": family,
        "customer_decision_state": dict(state),
        "candidate_pattern_ids": [row["pattern_id"] for row in compatible],
        "selected_patterns": [{"pattern_id": row["pattern_id"], "name": row["name"], "mobile_principle": row["mobile_principle"]} for row in selected],
        "selection_basis": "dominant_family + customer_decision_state + compatible grammar; not fixed layout",
    }


def run_controlled_nagi_production(output_dir: str | Path) -> dict[str, Any]:
    raw = nagi_reference_input()
    company_truth = {"verified": True, "company": raw["company"]["company_name"], "facts": [raw["company"]["company_truth"], *raw["company"]["differentiators"]]}
    inference = infer_and_select_family(
        company_truth=company_truth,
        customer_decision_state=raw["customer_decision_state"],
        creative_fit=_creative_fit(),
        feasibility=_feasibility(),
        candidates=[{"family_id": family} for family in FAMILY_IDS],
    )
    trace = {
        "schema_version": "issue53_controlled_production_trace_v1",
        "integration_contract_version": "issue53-controlled-production-v1",
        "source_issue": 53,
        "company": raw["company"]["company_name"],
        "company_truth": company_truth,
        "customer_decision_state": raw["customer_decision_state"],
        "creative_fit": _creative_fit(),
        "runtime_inference": inference["inference"],
        "selection": inference["selection"],
        "production_feasibility": _feasibility(),
        "architecture_order": ["Company Truth", "Customer Decision State", "Creative Fit", "Runtime Family Inference", "Family frozen", "Production Feasibility", "Module Grammar", "Generation"],
    }
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "architecture_trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if inference["selection"] is None:
        trace["status"] = "HUMAN_REVIEW_REQUIRED"
        (out / "architecture_trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return {"status": "HUMAN_REVIEW_REQUIRED", "trace": trace, "output_dir": str(out)}

    family = inference["selection"]["dominant_family"]
    grammar = _select_module_grammar(family, raw["customer_decision_state"])
    architecture = {"dominant_family": family, "secondary_families": inference["inference"]["secondary_influences"], "customer_decision_state": raw["customer_decision_state"], "module_grammar": grammar}
    raw_for_generation = deepcopy(raw)
    raw_for_generation["validation_context"] = "NO_WEB_FIELD_VALIDATION"
    site = out / "site"
    result = run_generation(raw_for_generation, site, generation_id="issue53-nagi-controlled-reference", mode="production", architecture=architecture)
    # Preserve the pre-integration generator output as a local comparison
    # reference. The package labels it as evidence, never as a visual PASS.
    (out / "baseline").mkdir(parents=True, exist_ok=True)
    baseline_html = site / "index.html"
    (out / "baseline" / "final.html").write_text(baseline_html.read_text(encoding="utf-8"), encoding="utf-8")
    html_path = site / "index.html"
    html = html_path.read_text(encoding="utf-8")
    html = html.replace("<head>", f'<head><meta name="creative-family" content="{family}"><meta name="module-grammar" content="{",".join(row["pattern_id"] for row in grammar["selected_patterns"])}">', 1)
    html = html.replace('<body class="', f'<body data-creative-family="{family}" data-module-grammar="{",".join(row["pattern_id"] for row in grammar["selected_patterns"])}" class="', 1)
    html_path.write_text(html, encoding="utf-8")
    render_spec_path = site / "render_spec.json"
    render_spec = json.loads(render_spec_path.read_text(encoding="utf-8"))
    render_spec["controlled_architecture"] = architecture
    render_spec_path.write_text(json.dumps(render_spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    trace.update({"status": "PASS", "module_grammar": grammar, "architecture_decision": architecture, "generation_id": result.generation_id, "production_output_allowed": result.production_output_allowed})
    (out / "architecture_trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "PASS", "trace": trace, "result": result, "output_dir": str(out), "site": str(site)}
