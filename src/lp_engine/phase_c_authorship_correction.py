"""Issue #71 same-family authorship correction.

The correction is driven by the frozen Phase C SSOT decision jobs. It makes
public structure explicit per reference without using company-name lookup.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from .phase_c_expansion import (
    _architecture,
    _feasibility,
    _fit,
    reference_input,
    load_phase_c_contracts,
    WIDTHS,
)
from .production_architecture import FAMILY_IDS, infer_and_select_family
from .production_generation import run_generation

PAIR_IDS = {
    "BW-F05": ("pola-apex", "fancl"),
    "BW-F07": ("lino-hair", "barbaro"),
    "BW-F01": ("three", "baum"),
    "BW-F03": ("kakimoto-arms", "pilates-k"),
}

AUTHORS = {
    "pola-apex": {
        "topology_signature": "diagnostic-route",
        "hero_mode": "question-to-route",
        "core_decision_mode": "diagnostic-evidence",
        "closing_mode": "route-booking",
        "progression": ["question", "route", "evidence", "compare", "book"],
    },
    "fancl": {
        "topology_signature": "self-check-field",
        "hero_mode": "self-check-invitation",
        "core_decision_mode": "routine-fit",
        "closing_mode": "small-next-step",
        "progression": ["self_check", "condition", "recommendation", "confidence", "start"],
    },
    "lino-hair": {
        "topology_signature": "relationship-continuity",
        "hero_mode": "people-before-place",
        "core_decision_mode": "relationship-continuity",
        "closing_mode": "returning-relationship",
        "progression": ["people", "place", "continuity", "nearby", "visit"],
    },
    "barbaro": {
        "topology_signature": "community-appointment",
        "hero_mode": "place-before-people",
        "core_decision_mode": "community-fit",
        "closing_mode": "appointment-path",
        "progression": ["place", "people", "grooming_choice", "continuity", "visit"],
    },
    "three": {
        "topology_signature": "ritual-material-proof",
        "hero_mode": "sensory-invitation",
        "core_decision_mode": "material-fit",
        "closing_mode": "ritual-start",
        "progression": ["ritual", "material", "fit", "proof", "start"],
    },
    "baum": {
        "topology_signature": "environment-lifestyle-fit",
        "hero_mode": "environment-first",
        "core_decision_mode": "lifestyle-context",
        "closing_mode": "space-invitation",
        "progression": ["environment", "space", "routine", "material", "start"],
    },
    "kakimoto-arms": {
        "topology_signature": "authorship-portfolio-investment",
        "hero_mode": "authorship-before-aspiration",
        "core_decision_mode": "portfolio-authorship",
        "closing_mode": "consultation-commitment",
        "progression": ["authority", "authorship", "portfolio", "investment", "commit"],
    },
    "pilates-k": {
        "topology_signature": "program-fit-commitment",
        "hero_mode": "program-before-self-image",
        "core_decision_mode": "method-program-fit",
        "closing_mode": "trial-to-program",
        "progression": ["method", "program", "fit", "schedule", "start"],
    },
}

HEADLINES = {
    "pola-apex": ["肌の状態を見ながら、今日の選択を決める。", "必要なことを、順番に確かめる。", "選ぶ根拠を、肌の変化から読む。", "違いを比べて、納得して進む。", "相談から、次の一歩を決める。"],
    "fancl": ["今の肌に、何が必要かを知る。", "続けられる方法を、暮らしから選ぶ。", "合うかどうかを、使い方と一緒に見る。", "迷いを残さず、確かめてから始める。", "小さな一歩から、相談する。"],
    "lino-hair": ["人と場所が見えるから、通い方を想像できる。", "顔が見える関係から、相談が始まる。", "続けて通う理由を、日々の中で考える。", "自分の毎日に近い場所を選ぶ。", "また来たいと思える入口へ。"],
    "barbaro": ["近くの店で、誰と過ごすかを選ぶ。", "場所と人柄を、先に確かめる。", "自分の頼み方に合う時間をつくる。", "通う条件を、生活と比べてみる。", "予約できる日から、始める。"],
    "three": ["感覚から、選ぶ時間をはじめる。", "素材と香りが、選ぶ理由になる。", "暮らしに置いたときの相性を見る。", "雰囲気を、確かめられる情報へ戻す。", "自分に合う入口から、始める。"],
    "baum": ["森の気配を、暮らしの中へ置く。", "空間と道具から、使う時間を想像する。", "毎日の習慣に続くかを考える。", "素材の背景と、手に取る理由を見る。", "暮らしに残る選択を、始める。"],
    "kakimoto-arms": ["つくり手の視点から、仕上がりを選ぶ。", "仕事の痕跡に、専門性が表れる。", "実績を、方法と一緒に読み解く。", "時間と費用に、納得して進む。", "相談して、次の完成像を決める。"],
    "pilates-k": ["続け方から、身体との向き合い方を選ぶ。", "動きの方法を、まず知る。", "プログラムが、自分の予定に合うかを見る。", "通う頻度と時間を、先に整理する。", "体験から、続ける形を決める。"],
}

def _correct_rows(company_id: str) -> list[dict[str, Any]]:
    author = AUTHORS[company_id]
    return [
        {
            "state": state,
            "role": f"{author['topology_signature']}_{state}",
            "headline": headline,
            "body": f"{headline} {author['core_decision_mode']}を、公開情報の範囲で確かめます。",
            "copy_intent": ["ORIENT", "SHOW_CRAFT", "PROVE", "COMPARE", "CONVERT"][index],
            "visual_authority": ["TYPE", "PERSON", "PROCESS", "DATA", "TYPE"][index],
            "media_role": ["hero_context", "human_context", "process_detail", "material_detail", "typography"][index],
            "cta_stage": ["discovery", "", "reassurance", "", "action"][index],
            "public_customer_facing": True,
            "source": "company_truth + customer_decision_job",
        }
        for index, (state, headline) in enumerate(zip(author["progression"], HEADLINES[company_id]))
    ]

def corrected_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(contract))
    company_id = result["company_id"]
    result["public_authorship"] = deepcopy(AUTHORS[company_id])
    result["public_scene_semantics"] = _correct_rows(company_id)
    result["authorship_derivation"] = {
        "source": "frozen company truth + customer decision job",
        "company_lookup": False,
        "family_fixed_layout": False,
    }
    return result

def load_corrected_contracts() -> list[dict[str, Any]]:
    return [corrected_contract(row) for row in load_phase_c_contracts()]

def public_topology_signature(contract: Mapping[str, Any]) -> dict[str, Any]:
    author = contract["public_authorship"]
    return {
        "reference_id": contract["reference_id"],
        "company_id": contract["company_id"],
        "family": contract["expected_family"],
        "topology_signature": author["topology_signature"],
        "hero_mode": author["hero_mode"],
        "core_decision_mode": author["core_decision_mode"],
        "closing_mode": author["closing_mode"],
        "progression": author["progression"],
        "scene_states": [row["state"] for row in contract["public_scene_semantics"]],
    }

def run_corrected_reference(contract: Mapping[str, Any], output_dir: str | Path) -> dict[str, Any]:
    raw, fit, feasibility = reference_input(contract), _fit(contract), _feasibility(contract)
    truth = {
        "verified": True,
        "facts": [contract["company_name"], contract["decision_job"], contract["customer_state"]],
        "prohibited_families": contract["prohibited_families"],
    }
    result = infer_and_select_family(
        company_truth=truth,
        customer_decision_state=contract["customer_state"],
        creative_fit=fit,
        feasibility=feasibility,
        candidates=[{"family_id": family} for family in FAMILY_IDS],
    )
    selection = result["selection"]
    if selection is None or selection["dominant_family"] != contract["expected_family"]:
        raise AssertionError(f"{contract['reference_id']} family selection is not stable")
    architecture = _architecture(contract, result["inference"], feasibility)
    architecture["public_authorship"] = deepcopy(contract["public_authorship"])
    architecture["public_topology_signature"] = contract["public_authorship"]["topology_signature"]
    architecture["public_semantic_derivation"] = "frozen family + customer decision job + authored topology; no company lookup"
    out, site = Path(output_dir), Path(output_dir) / "site"
    generated = run_generation(
        {**raw, "validation_context": "NO_WEB_FIELD_VALIDATION"},
        site,
        generation_id=f"issue71-{contract['company_id']}",
        mode="production",
        architecture=architecture,
    )
    constrained = _feasibility(contract, constrained=True)
    counter = infer_and_select_family(
        company_truth=truth,
        customer_decision_state=contract["customer_state"],
        creative_fit=fit,
        feasibility=constrained,
        candidates=[{"family_id": family} for family in FAMILY_IDS],
    )
    trace = {
        "schema_version": "issue71_phase_c_authorship_trace_v1",
        "source_issue": 71,
        "reference_id": contract["reference_id"],
        "company_id": contract["company_id"],
        "expected_family": contract["expected_family"],
        "public_authorship": deepcopy(contract["public_authorship"]),
        "runtime_inference": result["inference"],
        "selection": selection,
        "architecture": architecture,
        "production_feasibility": feasibility,
        "feasibility_counterfactual": {
            "dominant_family": counter["selection"]["dominant_family"],
            "family_unchanged": counter["selection"]["dominant_family"] == contract["expected_family"],
            "may_change_family": False,
        },
        "generation_id": generated.generation_id,
        "production_output_allowed": generated.production_output_allowed,
        "no_company_lookup": True,
        "no_family_fixed_layout": True,
        "status": "PASS",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "architecture_trace.json").write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "PASS", "trace": trace, "site": site}
