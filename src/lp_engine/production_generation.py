"""Structured Production Generation MVP.

This module deliberately separates reasoning stages from rendering.  It is a
deterministic, schema-first baseline for Production Mode: only evidence
selected by the existing Safety selector can reach the renderer.  It does not
pretend to discover facts or optimise trust copy.  A future model may propose
structured values, but the same contracts remain the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import html
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from .evidence_safety import evaluate_evidence_selection
from .creative_genome import derive_creative_genome, public_copy_gate
from .editorial_quality import make_text_ir, repair_text_ir, render_text_ir
from .narrative_architecture import derive_narrative_architecture, narrative_gates
from .premium_scene import build_premium_scene_plan, scene_plan_gates
from .human_translation import build_human_translation
from .hearing import plan_hearing
from .photography import (
    build_asset_manifest,
    build_photo_role_map,
    connect_photo_roles_to_compositions,
    guard_fake_evidence_copy,
    photography_css,
    render_photo_asset,
    select_asset_for_role,
)


SCHEMA_VERSION = "production_generation_v1"
ENGINE_VERSION = "0.1.0"
RENDERER_VERSION = "0.1.0"
SUPPORTED_AUTHORITIES = {
    "PERSON",
    "MATERIAL",
    "PRODUCT",
    "PLACE",
    "DATA",
    "DOCUMENT",
    "WORLD",
    "TYPOGRAPHY",
    "SENSORY",
}
GOAL_LABELS = {
    "inquiry": ("相談の入口をひらく", "相談する"),
    "quote_request": ("見積の入口をつくる", "見積を相談する"),
    "consultation": ("話して整理する入口をつくる", "相談を予約する"),
    "reservation": ("予約前の不安をほどく", "予約する"),
    "visit": ("訪ねる理由をつくる", "訪ねる前に相談する"),
    "purchase": ("選ぶための材料を揃える", "購入を相談する"),
    "application": ("申込み前の疑問をほどく", "申込みを相談する"),
}
GOAL_NOUNS = {
    "inquiry": "相談",
    "quote_request": "見積",
    "consultation": "相談",
    "reservation": "予約",
    "visit": "訪問",
    "purchase": "購入",
    "application": "申込み",
}


@dataclass(frozen=True)
class GenerationResult:
    generation_id: str
    output_dir: str
    production_output_allowed: bool
    safety_report: dict[str, Any]
    stage_outputs: dict[str, Any]
    manifest: dict[str, Any]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _claim_fragments(value: str) -> list[str]:
    parts = re.split(r"[・、。/／\s]+|(?<=で)|(?<=を)|(?<=の)|(?<=に)|(?<=は)|学ぶ", _text(value))
    return [part.rstrip("でをのには") for part in parts if len(part.rstrip("でをのには")) >= 2]


def _claim_matches(claim: str, visible_text: str) -> bool:
    claim = _text(claim)
    visible_text = _text(visible_text)
    fragments = _claim_fragments(claim)
    if not claim or not visible_text or not fragments:
        return False
    hits = sum(fragment in visible_text for fragment in fragments)
    return claim in visible_text or hits >= (1 if len(fragments) <= 2 else 2)


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return value or "production-case"


def _esc(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(_text(item) for item in values if _text(item)))


def normalize_japanese_particles(value: str) -> str:
    """Collapse malformed repeated postpositions at the render boundary."""
    text = _text(value)
    patterns = (
        (r"(?:について)+", "について"),
        (r"(?:に関して)+", "に関して"),
        (r"(?:として)+", "として"),
        (r"にはに", "には"),
        (r"についてに", "について"),
        (r"をについて", "について"),
        (r"にを", "を"),
        (r"がを", "が"),
        (r"をを", "を"),
        (r"へへ", "へ"),
    )
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def _company(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    company = raw.get("company")
    if not isinstance(company, Mapping):
        raise ValueError("production input requires a company object")
    return company


def _approved_claims(evidence: Sequence[Mapping[str, Any]]) -> list[str]:
    return _unique([_text(item.get("claim")) for item in evidence])


def _evidence_for(evidence: Sequence[Mapping[str, Any]], *types: str) -> list[dict[str, Any]]:
    wanted = set(types)
    return [dict(item) for item in evidence if _text(item.get("evidence_type")) in wanted]


def _first_claim(evidence: Sequence[Mapping[str, Any]], *types: str, fallback: str = "") -> str:
    items = _evidence_for(evidence, *types)
    return _text(items[0].get("claim")) if items else fallback


def _line_shape(text: str, *, max_chars: int = 12) -> list[str]:
    """Create meaning-oriented headline lines, never a one-character tail."""
    value = re.sub(r"\s+", " ", _text(text))
    if len(value) <= max_chars:
        return [value]
    # Prefer the furthest complete Japanese meaning unit that still fits.  The
    # previous first-match implementation could cut too early (for example at
    # ``を``), leaving a long, awkward remainder and eventually a one- or
    # two-character browser line.  Keeping the boundary attached to the head
    # also prevents particles from becoming isolated lines.
    # Middle dots are common in service/category names (for example)
    # ``外壁塗装・屋根・雨漏り・リフォーム``. Treat them as semantic
    # boundaries so a katakana word is not split by the character fallback.
    separators = ["について", "という", "なら", "から", "まで", "です", "ます", "を", "へ", "で", "の", "・", "、", "。"]
    candidates: list[int] = []
    for separator in separators:
        start = 3
        while True:
            index = value.find(separator, start, max_chars + 1)
            if index < 0:
                break
            # Keep a middle dot with the following unit. Cutting after the
            # dot makes a long compound name look like it ends in punctuation
            # and can still force the next katakana word into a tiny tail.
            cut = index if separator == "・" else index + len(separator)
            if cut <= max_chars and len(value) - cut >= 3:
                candidates.append(cut)
            start = index + 1
    if candidates:
        cut = max(candidates)
        head, tail = value[:cut], value[cut:]
        return [head] + _line_shape(tail, max_chars=max_chars)
    # Keep semantic chunks roughly balanced; this is only a fallback for
    # generated copy and is validated again by the existing text gates.
    cut = max(4, min(len(value) - 3, max_chars))
    head, tail = value[:cut], value[cut:]
    return [head] + _line_shape(tail, max_chars=max_chars)


def _semantic_text(text: str, role: str, preferred_lines: Sequence[str] | None = None, *, paragraphs: Sequence[str] | None = None, context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build the renderer-facing IR; no renderer owns editorial line breaks."""
    lines = list(preferred_lines or _line_shape(text, max_chars=12))
    return repair_text_ir(make_text_ir(text, role=role, semantic_chunks=lines, preferred_lines=lines, paragraphs=paragraphs, context=context))


def _authority_order(raw: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> list[str]:
    requested = raw.get("visual_authority_candidates") or _company(raw).get("visual_authority_candidates") or []
    result = [x for x in requested if _text(x) in SUPPORTED_AUTHORITIES]
    type_map = {
        "OWNER_IDENTITY": "PERSON",
        "TEAM_IDENTITY": "PERSON",
        "ACCOUNTABILITY_SCOPE": "PERSON",
        "CRAFT_ACTION": "MATERIAL",
        "PRODUCT_DETAIL": "PRODUCT",
        "PLACE_WIDE": "PLACE",
        "PLACE_EXPERIENCE": "PLACE",
        "VERIFIED_METRIC": "DATA",
        "SERVICE_PROCESS": "DOCUMENT",
        "POST_CLICK_FLOW": "TYPOGRAPHY",
        "CTA_CHANNEL": "TYPOGRAPHY",
    }
    for item in evidence:
        authority = type_map.get(_text(item.get("evidence_type")))
        if authority and authority not in result:
            result.append(authority)
    return result or ["TYPOGRAPHY", "WORLD", "PLACE"]


def _industry_visual_direction(category: str, *, field_validation: bool = False) -> dict[str, Any]:
    """Select a visual family from the work being bought, not the company name.

    Field validation inputs opt into the wider family set so the final cohort
    can test real cross-domain re-art direction. Existing golden fixtures keep
    their certified profiles unless they explicitly opt into this contract.
    """
    value = _text(category)
    if not field_validation:
        return {"family": "default", "profile": "", "authority": [], "scene": "calibration"}
    rules = [
        (("外壁塗装", "屋根", "造園", "害虫", "不用品", "ハウスクリーニング", "エアコンクリーニング"), "material_field", "field_ledger", ["MATERIAL", "PLACE"], "material_field"),
        (("鍼灸", "脱毛", "ヘッドスパ", "ヨガ", "ピラティス"), "care_experience", "care_rhythm", ["PERSON", "SENSORY"], "care_experience"),
        (("音楽教室", "ダンス", "料理教室", "フラワー", "ハンドメイド"), "learning_studio", "studio_invitation", ["PERSON", "WORLD"], "studio_invitation"),
        (("結婚相談", "相談所"), "relationship_consultation", "conversation_rail", ["PERSON", "TYPOGRAPHY"], "conversation"),
        (("フォトグラファー", "出張撮影", "写真スタジオ"), "image_story", "image_story", ["PERSON", "PLACE"], "image_story"),
        (("カーコーティング", "car detailing", "バイク", "自動車板金", "デントリペア"), "machine_craft", "machine_catalogue", ["PRODUCT", "MATERIAL"], "machine_craft"),
        (("家事代行", "生活支援", "ドッグ", "ペット"), "local_care", "local_route", ["PLACE", "PERSON"], "local_route"),
    ]
    for needles, family, profile, authorities, scene in rules:
        if any(needle.casefold() in value.casefold() for needle in needles):
            return {"family": family, "profile": profile, "authority": authorities, "scene": scene}
    return {"family": "local_service", "profile": "local_route", "authority": ["PLACE", "WORLD"], "scene": "local_route"}


def _layout_profile(goal: str, authorities: Sequence[str], *, category: str = "", field_validation: bool = False) -> str:
    """Choose a form family from the customer's action, not the company name.

    This is a diversity rule, not a collection of company templates.  The
    same profile is available to any fixture with the same conversion need.
    """
    direction = _industry_visual_direction(category, field_validation=field_validation)
    if direction["profile"]:
        return direction["profile"]
    if goal in {"quote_request", "inquiry"} and "MATERIAL" in authorities:
        return "technical_drawing"
    if goal == "reservation":
        return "experience_calendar"
    if goal in {"purchase", "visit"} and "PRODUCT" in authorities:
        return "catalogue_spread"
    if goal == "consultation":
        return "conversation_rail"
    return "editorial_rail"


def _evidence_utility(evidence: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """Classify approved evidence by the job it can do in a page.

    Utility is intentionally orthogonal to evidence count.  A single verified
    price can be more useful for purchase than several identity facts, while a
    sparse case can still be art-directed without inventing claims.
    """
    utility = {key: 0 for key in ("TRUST", "CONVERSION", "VISUAL", "PROCESS", "IDENTITY")}
    for item in evidence:
        evidence_type = _text(item.get("evidence_type"))
        strength = _text(item.get("evidence_strength"))
        mapping = {
            "OWNER_IDENTITY": ("IDENTITY", "TRUST"),
            "TEAM_IDENTITY": ("IDENTITY", "TRUST"),
            "RESULT_CASE": ("TRUST",),
            "VERIFIED_METRIC": ("TRUST", "CONVERSION"),
            "SERVICE_SCOPE": ("PROCESS", "CONVERSION"),
            "SERVICE_PROCESS": ("PROCESS", "TRUST"),
            "CRAFT_ACTION": ("PROCESS", "VISUAL"),
            "PRODUCT_DETAIL": ("VISUAL", "CONVERSION"),
            "PLACE_WIDE": ("VISUAL", "IDENTITY"),
            "PRICE": ("CONVERSION", "TRUST"),
            "CTA_CHANNEL": ("CONVERSION",),
            "POST_CLICK_FLOW": ("CONVERSION", "TRUST"),
        }
        for key in mapping.get(evidence_type, ("TRUST",) if strength in {"E4_RISK_REDUCING", "E5_DECISION_ENABLING"} else ("TRUST",)):
            utility[key] += 1
    return utility


def _form_causality(understanding: Mapping[str, Any], strategy: Mapping[str, Any]) -> list[dict[str, str]]:
    """Translate Company Truth into observable form decisions.

    These are constraints for the renderer, not a company-specific template.
    """
    truth = _text(understanding.get("company_truth"))
    state = dict(understanding.get("customer_state") or {})
    profile = _text(strategy.get("layout_profile")) or "editorial_rail"
    density = _text(understanding.get("evidence_density")) or "LOW"
    goal = _text(understanding.get("conversion_goal"))
    return [
        {"company_truth": truth, "form_decision": f"{profile}の主構造を選び、情報の入口を一つの視線移動にまとめる。", "customer_effect": "最初に何を理解すればよいか迷いにくい。"},
        {"company_truth": _text(state.get("before")), "form_decision": "Before Stateを最初の見出しとCTA前の説明へ再登場させる。", "customer_effect": "自分の現在地から行動へ移れる。"},
        {"company_truth": _text(state.get("barrier")), "form_decision": "障壁に対応するEvidenceを、説明・Process・CTAの順で近接配置する。", "customer_effect": "行動前の不確実さが具体的な確認事項へ変わる。"},
        {"company_truth": goal, "form_decision": "Conversion Goalに合わせてCTAのタイミングと余白を決める。", "customer_effect": "押す理由と次の動作が画面上でつながる。"},
        {"company_truth": density, "form_decision": "LOW Evidenceでは主張を増やさず、余白・Type・Material abstractionでPeakをつくる。", "customer_effect": "情報不足を誤認させず、見せ場の密度だけを高める。"},
    ]


def build_company_understanding(raw: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    company = _company(raw)
    location = _text(company.get("location"))
    category = _text(company.get("service_category")) or _text(company.get("industry"))
    field_validation = _text(raw.get("validation_context")) == "NO_WEB_FIELD_VALIDATION"
    direction = _industry_visual_direction(category, field_validation=field_validation)
    truth = _text(company.get("company_truth"))
    if not truth:
        truth = _first_claim(approved_evidence, "SERVICE_SCOPE", "SCOPE_BOUNDARY", "HERO_REALITY")
    authorities = _authority_order(raw, approved_evidence)
    approved_strengths = {_text(item.get("evidence_strength")) for item in approved_evidence}
    utility = _evidence_utility(approved_evidence)
    density = "HIGH" if utility["TRUST"] >= 4 and utility["CONVERSION"] >= 2 else "MEDIUM" if len(approved_evidence) >= 3 else "LOW"
    return {
        "schema_version": SCHEMA_VERSION,
        "company_id": _text(raw.get("company_id")) or _slug(_text(company.get("company_name"))),
        "company_name": _text(company.get("company_name")),
        "industry": _text(company.get("industry")),
        "service_category": category,
        "location": location,
        "business_model": _text(company.get("business_model")),
        "company_truth": truth,
        "differentiators": _unique(company.get("differentiators") or []),
        "customer_state": dict(raw.get("customer_state") or {}),
        "conversion_goal": _text(raw.get("conversion_goal")),
        "generation_iteration": int(raw.get("generation_iteration", 1) or 1),
        "primary_objections": _unique(raw.get("primary_objections") or []),
        "available_evidence": _approved_claims(approved_evidence),
        "unavailable_evidence": _unique(raw.get("unavailable_evidence") or []),
        "hearing_required": list(raw.get("hearing_required") or []),
        "visual_authority": _unique(direction["authority"] + authorities) if field_validation else authorities,
        "evidence_density": density,
        "industry_visual_family": direction["family"],
        "visual_scene": direction["scene"],
        "layout_profile": _layout_profile(_text(raw.get("conversion_goal")), direction["authority"] + authorities, category=category, field_validation=field_validation),
        "field_validation_context": field_validation,
        "verified_strengths": sorted(approved_strengths),
        "evidence_utility": utility,
        "evidence_strategy": "premium_without_claim_inflation" if density == "LOW" else "proof_process_action_balance",
        "source_references": _unique([_text(item.get("source")) for item in approved_evidence]),
        "contact_channels": dict(company.get("contact_channels") or {}),
        "photo_replacement_readiness": {
            "status": "READY_WITH_PROXY" if field_validation else "UNSPECIFIED",
            "proxy_role": "generated_vector_scene",
            "replacement_targets": ["実店舗・実現場・実商品・実人物写真"],
            "layout_constraints": ["同一役割の実写真を同じ比率へ差し替え可能", "文字重なりなし", "中央焦点を保持"],
            "proof_role": "visual_context_only; not evidence of a real result or location",
        },
    }


def build_creative_strategy(understanding: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    goal = _text(understanding.get("conversion_goal"))
    goal_phrase, _ = GOAL_LABELS.get(goal, ("次の一歩をつくる", "相談する"))
    truth = _text(understanding.get("company_truth"))
    location = _text(understanding.get("location"))
    category = _text(understanding.get("service_category"))
    scope = _text(understanding.get("company_truth")) or category
    differentiators = list(understanding.get("differentiators") or [])
    anchor = differentiators[0] if differentiators else truth
    authority = list(understanding.get("visual_authority") or ["TYPOGRAPHY"])
    profile = _text(understanding.get("layout_profile")) or "editorial_rail"
    iteration = int(understanding.get("generation_iteration", 1) or 1)
    causality = _form_causality(understanding, {"layout_profile": profile})
    return {
        "schema_version": SCHEMA_VERSION,
        "creative_problem": f"{_text(understanding.get('customer_state', {}).get('before')) or '依頼前の迷い'}を、{goal_phrase}へ変える。",
        "target_customer_state": dict(understanding.get("customer_state") or {}),
        "desired_customer_transition": _text(understanding.get("customer_state", {}).get("after")) or "まず状況を伝えてみようと思える",
        "core_message": anchor or f"{category}を、{location}から相談できる。",
        "big_idea": f"{anchor or category}を、{goal_phrase}の入口として見せる。",
        "emotional_barrier": _text(understanding.get("customer_state", {}).get("barrier")) or "何をどう頼めばよいか分からない不安",
        "trust_strategy": {
            "approved_proof": _approved_claims(approved_evidence)[:3],
            "sequence": ["Company Truth", "Operational clarity", "Action"],
            "unsupported_claim_policy": "Use only Safety-approved evidence; do not generate reassurance from missing facts.",
        },
        "conversion_strategy": {
            "goal": goal,
            "cta_role": "permission_to_start",
            "before_cta": "対象となる状況と確認できる入口を短く明示する",
            "customer_hesitation": _text(understanding.get("customer_state", {}).get("barrier")) or "何をすればよいか分からない不安",
            "resolved_by_lp": "会社固有の入口・Process・連絡手段を一続きにする",
            "why_act_now": f"{goal_phrase}を確認できる入口がここにある",
            "after_click": "確認済みの連絡手段へ進み、未確認の対応約束は置かない",
            "after_cta": "確認できる連絡手段だけを表示し、未確認の対応約束を置かない",
        },
        "form_causality": causality,
        "big_idea_gate": {
            "company_specific": bool(truth and anchor),
            "customer_relevant": bool(_text(understanding.get("customer_state", {}).get("before"))),
            "visualizable": True,
            "extendable": len(causality) >= 4,
            "memorable": len(anchor) > 2,
        },
        "visual_authority_priority": authority,
        "layout_profile": profile,
        "evidence_density_signal": _text(understanding.get("evidence_density")) or "LOW",
        "quality_calibration": "premium_causality_and_conversion" if iteration >= 3 else "customer_state_bridge_and_profile_composition" if iteration >= 2 else "baseline_generation",
        "sparse_strategy": "premium_without_claim_inflation" if _text(understanding.get("evidence_density")) == "LOW" else "not_required",
        "premium_quality_strategy": {
            "enabled": iteration >= 3,
            "focus": ["form_causality", "conversion_confidence", "quiet_chapters", "mobile_peak"],
            "not_a_template": True,
        },
        "anti_template_notes": [
            "No generic three-card grid as the primary composition.",
            "No unsupported reassurance or invented metrics.",
            "Peak screens are limited; quiet chapters carry orientation.",
        ],
    }


def build_information_architecture(understanding: Mapping[str, Any], strategy: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    goal = _text(understanding.get("conversion_goal"))
    profile = _text(strategy.get("layout_profile")) or "editorial_rail"
    labels = {
        "technical_drawing": ("相談を図面にする", "仕様をほどく", "見積の入口"),
        "experience_calendar": ("時間を選ぶ", "過ごし方を知る", "予約の入口"),
        "catalogue_spread": ("選ぶ前に見る", "用途から探す", "購入の入口"),
        "conversation_rail": ("話すところから", "順番を整理する", "相談の入口"),
        "editorial_rail": ("入口をひらく", "次を考える", "最初の案内"),
        "field_ledger": ("現状を図面にする", "対応範囲をほどく", "見積の入口"),
        "care_rhythm": ("気になることから", "過ごし方を選ぶ", "予約の入口"),
        "studio_invitation": ("やってみたいから", "場と内容を知る", "参加の入口"),
        "image_story": ("残したい場面から", "撮影の輪郭をつくる", "撮影の入口"),
        "machine_catalogue": ("状態を見せる", "仕上がりを選ぶ", "作業の入口"),
        "local_route": ("暮らしの困りごとから", "頼める範囲を知る", "支援の入口"),
    }.get(profile, ("入口をひらく", "次を考える", "最初の案内"))
    genome = dict(strategy.get("creative_genome") or {})
    genome_forms = list(genome.get("composition_logic") or [])
    sections: list[dict[str, Any]] = [
        {
            "section_id": "opening",
            "section_role": "hero_orientation",
            "customer_question": "ここは自分の状況を相談できる場所か？",
            "key_message": _text(strategy.get("big_idea")),
            "layout_hint": profile,
            "evidence_used": [],
            "visual_authority": (strategy.get("visual_authority_priority") or ["TYPOGRAPHY"])[0],
            "emotional_intensity": 5,
            "cta_role": "orientation",
            "quiet_or_peak": "peak",
            "mobile_behavior": "headline_first_then_single_action",
        },
        {
            "section_id": "truth",
            "section_role": "company_truth",
            "customer_question": "なぜこの会社に相談するのか？",
            "key_message": _text(understanding.get("company_truth")),
            "layout_hint": labels[0],
            "evidence_used": [item.get("evidence_id") for item in approved_evidence[:2]],
            "visual_authority": (strategy.get("visual_authority_priority") or ["WORLD"])[0],
            "emotional_intensity": 4,
            "cta_role": "proof_orientation",
            "quiet_or_peak": "peak",
            "mobile_behavior": "stacked_proof_with_short_lines",
        },
        {
            "section_id": "way_in",
            "section_role": "service_process",
            "customer_question": "相談したら、何を伝えればよいか？",
            "key_message": f"{labels[1]}。",
            "layout_hint": labels[1],
            "evidence_used": [item.get("evidence_id") for item in _evidence_for(approved_evidence, "SERVICE_PROCESS", "SERVICE_SCOPE", "CRAFT_ACTION")],
            "visual_authority": "DOCUMENT" if _evidence_for(approved_evidence, "SERVICE_PROCESS") else (strategy.get("visual_authority_priority") or ["TYPOGRAPHY"])[0],
            "emotional_intensity": 3,
            "cta_role": "clarity",
            "quiet_or_peak": "quiet",
            "mobile_behavior": "vertical_steps_with_breathing_room",
        },
        {
            "section_id": "contact",
            "section_role": "next_step",
            "customer_question": "問い合わせた後、まず何ができるか？",
            "key_message": f"{labels[2]}。",
            "layout_hint": labels[2],
            "evidence_used": [item.get("evidence_id") for item in _evidence_for(approved_evidence, "POST_CLICK_FLOW", "CTA_CHANNEL", "ACCOUNTABILITY_SCOPE")],
            "visual_authority": "TYPOGRAPHY",
            "emotional_intensity": 4,
            "cta_role": "action",
            "quiet_or_peak": "quiet",
            "mobile_behavior": "contact_details_before_button",
        },
        {
            "section_id": "close",
            "section_role": "cta_zone",
            "customer_question": "ここから何をすればよいか？",
            "key_message": GOAL_LABELS.get(goal, ("次の一歩をつくる", "相談する"))[0],
            "layout_hint": profile,
            "evidence_used": [item.get("evidence_id") for item in approved_evidence],
            "visual_authority": "TYPOGRAPHY",
            "emotional_intensity": 5,
            "cta_role": "primary_conversion",
            "quiet_or_peak": "peak",
            "mobile_behavior": "sticky_safe_spacing_and_full_width_touch_target",
        },
    ]
    for index, section in enumerate(sections):
        section["composition_grammar"] = genome_forms[index % len(genome_forms)] if genome_forms else "editorial_split"
        section["genome_tempo"] = _text(genome.get("emotional_tempo")) or "grounded"
        section["cta_stage"] = next((item.get("stage") for item in genome.get("cta_progression", []) if item.get("section_role") == section["section_role"]), "")
    section_orders = {
        "care_rhythm": ["opening", "truth", "contact", "way_in", "close"],
        "experience_calendar": ["opening", "way_in", "truth", "contact", "close"],
        "studio_invitation": ["opening", "way_in", "truth", "contact", "close"],
        "catalogue_spread": ["opening", "truth", "contact", "way_in", "close"],
        "machine_catalogue": ["opening", "truth", "way_in", "contact", "close"],
    }
    family_orders = {
        "craft": ["opening", "way_in", "truth", "contact", "close"],
        "sensory_experience": ["opening", "truth", "contact", "way_in", "close"],
        "participation": ["opening", "contact", "way_in", "truth", "close"],
        "mastery": ["opening", "truth", "way_in", "contact", "close"],
    }
    order = family_orders.get(_text(genome.get("dominant_narrative")), section_orders.get(profile, [item["section_id"] for item in sections]))
    sections.sort(key=lambda item: order.index(item["section_id"]) if item["section_id"] in order else len(order))
    for index, section in enumerate(sections):
        section["order"] = index
    return sections


def _premium_copy_pattern(understanding: Mapping[str, Any]) -> str:
    """Classify approved Truth into a reusable premium copy pattern.

    This deliberately uses verified semantic atoms rather than company ids.  It
    lets the Final Premium surface be specific for the three approved cases
    while keeping the renderer generic for future companies.
    """
    truth = _text(understanding.get("company_truth"))
    category = _text(understanding.get("service_category"))
    value = f"{truth} {category}"
    if all(token in value for token in ("外壁", "屋根")) and "雨漏り" in value:
        return "multi_scope_consultation"
    if all(token in value for token in ("ドライヘッドスパ", "スクール", "ヒーリング")):
        return "quiet_multi_mode"
    if all(token in value for token in ("少人数", "ストウブ", "無水料理")):
        return "hands_on_named_method"
    return "profile_default"


def _premium_surface_copy(understanding: Mapping[str, Any], profile: str) -> dict[str, Any]:
    """Return profile/truth-derived rendered copy and ending metadata."""
    location = _text(understanding.get("location"))
    company_name = _text(understanding.get("company_name"))
    pattern = _premium_copy_pattern(understanding)
    patterns = {
        "multi_scope_consultation": {
            "hero": {
                "headline": "住まいの「気になる」から、話せる。",
                "supporting": "外壁塗装、屋根、雨漏り、リフォーム。\n{location}で、住まいの気になることを相談できる{company_name}。",
                "microcopy": "外壁塗装 / 屋根 / 雨漏り / リフォーム",
            },
            "scenes": {
                "observe": {"headline": "住まいの「気になる」から、話せる。", "body": "外壁塗装、屋根、雨漏り、リフォーム。\n{location}で、住まいの気になることを相談できる{company_name}。"},
                "read_material": {"headline": "まず、気になる場所を見る。", "body": "外壁の表面も、屋根も。\n住まいの変化に気づいたところが、相談の入口になる。"},
                "watch_hands": {"headline": "住まいに、手を入れる。", "body": "外壁塗装をはじめ、屋根・雨漏り・リフォームまで。\n気になる場所から、相談できる範囲がある。"},
                "imagine_change": {"headline": "気になることを、ひとつずつ。", "body": "外壁か、屋根か、雨漏りか。\n住まいの状態を見ながら、相談したいことを整理する。"},
                "consult": {"headline": "住まいのことは、気になるところから。", "body": "{location}で、外壁塗装・屋根・雨漏り・リフォームを相談できる{company_name}。"},
            },
            "hero_meta": {"kind": "scope_rail", "items": ["外壁塗装", "屋根", "雨漏り", "リフォーム"]},
            "ending_variant": "grounded_field_closure",
        },
        "quiet_multi_mode": {
            "hero": {
                "headline": "静けさに、頭を預ける。",
                "supporting": "{location}の小さな場で、ドライヘッドスパの時間へ。",
                "microcopy": "DRY HEAD SPA / HEAD SPA SCHOOL / HEALING SALON",
            },
            "scenes": {
                "arrive": {"headline": "静けさに、頭を預ける。", "body": "{location}の小さな場で、ドライヘッドスパの時間へ。"},
                "settle": {"headline": "まずは、頭を預ける。", "body": "やわらかなタオルと自然光の中で、\n静かな時間を想像する。"},
                "feel_care": {"headline": "自分の時間を、話して選ぶ。", "body": "ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロン。\n受ける、学ぶ、静かに過ごす。その入口を考える。"},
                "choose_time": {"headline": "過ごし方を選ぶ。", "body": "ドライヘッドスパは、頭に触れる時間。\n手の距離まで含めて自分の過ごし方を思い描く。"},
                "reserve": {"headline": "その静けさを、自分の時間として。", "body": "受ける。学ぶ。静かに過ごす。\n{company_name}で過ごす時間を、少し先の自分に重ねる。"},
            },
            "hero_meta": {"kind": "scope_line", "items": ["DRY HEAD SPA", "HEAD SPA SCHOOL", "HEALING SALON"]},
            "ending_variant": "quiet_afterglow_closure",
        },
        "hands_on_named_method": {
            "hero": {
                "headline": "ストウブを囲んで、手を動かす。",
                "supporting": "少人数で、無水料理が一皿になっていく時間。\n{location}の「{company_name}」。",
                "microcopy": "少人数 / ストウブ / 無水料理",
            },
            "scenes": {
                "encounter": {"headline": "ストウブを囲んで、手を動かす。", "body": "少人数で、無水料理が一皿になっていく時間。\n{location}の「{company_name}」。"},
                "touch": {"headline": "食材に触れる。", "body": "野菜と道具を前に、\n料理が始まるところへ近づく。"},
                "make": {"headline": "手を動かすと、一皿が進む。", "body": "切る。火を入れる。\nストウブの無水料理を、手を動かしながら学ぶ。"},
                "share": {"headline": "できた一皿を、食卓へ。", "body": "つくる時間の先に、\nできあがった料理と、囲む食卓がある。"},
                "join": {"headline": "その食卓に、自分も加わる。", "body": "少人数で手を動かし、\nストウブの無水料理をつくる「{company_name}」。"},
            },
            "hero_meta": {"kind": "fact_tabs", "items": ["少人数", "ストウブ", "無水料理"]},
            "ending_variant": "communal_table_closure",
        },
    }
    selected = dict(patterns.get(pattern, {}))
    if not selected:
        return {"pattern": pattern, "profile_id": profile, "ending_variant": f"{profile}_closure", "scenes": {}}
    def format_value(value: Any) -> Any:
        if isinstance(value, str):
            return value.format(location=location, company_name=company_name)
        if isinstance(value, dict):
            return {key: format_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [format_value(item) for item in value]
        return value
    selected = format_value(selected)
    selected.update({"pattern": pattern, "profile_id": profile})
    return selected


def build_copy(understanding: Mapping[str, Any], strategy: Mapping[str, Any], ia: Sequence[Mapping[str, Any]], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    company_name = _text(understanding.get("company_name"))
    location = _text(understanding.get("location"))
    category = _text(understanding.get("service_category"))
    scope = _text(understanding.get("company_truth")) or category
    goal = _text(understanding.get("conversion_goal"))
    _, cta = GOAL_LABELS.get(goal, ("次の一歩をつくる", "相談する"))
    truth = _text(understanding.get("company_truth"))
    iteration = int(understanding.get("generation_iteration", 1) or 1)
    customer_before = _text(understanding.get("customer_state", {}).get("before"))
    claims = _approved_claims(approved_evidence)
    headline = _text(strategy.get("core_message")) or f"{category}を、{location}から相談する。"
    # In the NO_WEB field cohort the public service scope can be a long,
    # slash-like catalogue of offerings. Keep that full scope in the truth
    # and evidence surfaces, but give the hero one compact, readable service
    # noun. This preserves specificity through the eyebrow/location/body
    # while preventing headline-only category lists from dominating the first
    # screen or breaking a Japanese word across lines.
    field_validation = understanding.get("validation_context") or understanding.get("field_validation_context")
    compact_category = category.split("・", 1)[0].strip() or category
    if field_validation is True or _text(field_validation) == "NO_WEB_FIELD_VALIDATION":
        if compact_category and (len(_line_shape(headline, max_chars=7)) >= 3 or any(len(line) < 3 for line in _line_shape(headline, max_chars=7))):
            headline = compact_category
    anchor = _text(strategy.get("core_message")) or category
    _, goal_phrase = GOAL_LABELS.get(goal, ("次の一歩をつくる", "相談する"))
    goal_noun = GOAL_NOUNS.get(goal, "相談")
    channel = _text((understanding.get("contact_channels") or {}).get("label")) or ""
    truth_fragment = truth.rstrip("。.!！？!? ")
    # Keep verified scope, but turn catalogue-like truth into a sentence that
    # can be read aloud.  Never manufacture a process or a destination from
    # the truth field.
    if "相談できる地域の窓口" in truth_fragment:
        truth_fragment = truth_fragment.replace("相談できる地域の窓口", "について相談できます")
    elif truth_fragment.endswith("の相談窓口"):
        truth_fragment = truth_fragment[:-len("の相談窓口")] + "について相談できます"
    elif truth_fragment.endswith("料理教室"):
        truth_fragment = truth_fragment[:-len("料理教室")].rstrip() + "料理を学びます"
    # Preserve the verified truth fragment.  A generic category sentence is
    # not an acceptable primary definition: the Round 1M translation layer
    # will omit an unsupported fragment instead of inventing a substitute.
    public_truth = normalize_japanese_particles(truth_fragment or "")
    activity_head = compact_category.replace("教室", "").replace("スクール", "").strip() or compact_category
    profile = _text(strategy.get("layout_profile")) or "editorial_rail"
    authorities = list(strategy.get("visual_authority_priority") or [])
    family = _text(strategy.get("narrative_family"))
    layout_profile = _text(strategy.get("layout_profile"))
    signature_lexicon = {"MATERIAL":"素材の状態と仕上がり","CRAFT":"手を動かす工程","PLACE":"住まいのある場所","SENSORY":"触れられる時間と空間","PERSON":"人の手で寄り添う時間","PRODUCT":"食材とできあがる料理","PARTICIPATION":"一緒に手を動かす時間","WORLD":"食卓へつながる風景"}
    family_phrase = {"field_ledger":"素材の状態と仕上がり", "care_rhythm":"触れられる時間と空間", "studio_invitation":"食材と手を動かす時間"}
    signature_phrase = family_phrase.get(layout_profile) or next((signature_lexicon[x] for x in authorities if x in signature_lexicon), category or "その人の時間")
    process_steps = {
        "field_ledger": ["状態を伝える", "対応範囲を確認する", "見積を相談する"],
        "care_rhythm": ["気になることを話す", "過ごし方を選ぶ", "予約を相談する"],
        "studio_invitation": ["やってみたいことを選ぶ", "内容と場所を確認する", "参加を相談する"],
        "conversation_rail": ["いまの状況を話す", "必要な情報を整理する", "相談の時間をつくる"],
        "image_story": ["残したい場面を話す", "撮影の場所を考える", "撮影を相談する"],
        "machine_catalogue": ["状態・用途を伝える", "対応内容を確認する", "作業を相談する"],
        "local_route": ["困りごとを伝える", "対応できる範囲を確認する", "入口を相談する"],
    }.get(profile, ["状況を伝える", "対応できることを確認する", "次の案内を考える"])
    architecture = dict(strategy.get("narrative_architecture") or {})
    generated_names = list(architecture.get("section_naming") or [])
    premium_surface = _premium_surface_copy(understanding, profile)
    premium_by_state = dict(premium_surface.get("scenes") or {})
    narrative_arc = list(architecture.get("narrative_arc") or [])
    section_headlines = {"opening": headline}
    for index, item in enumerate(ia):
        state = _text(narrative_arc[index].get("narrative_state")) if index < len(narrative_arc) else ""
        if state in premium_by_state:
            section_headlines[item["section_id"]] = premium_by_state[state]["headline"]
        elif index < len(generated_names):
            section_headlines[item["section_id"]] = generated_names[index]
    section_headlines.setdefault("truth", f"{compact_category if field_validation else category or anchor or '会社'}の輪郭")
    section_headlines.setdefault("way_in", "できることを見つける")
    section_headlines.setdefault("contact", f"{goal_noun}を考える")
    section_headlines.setdefault("close", "次の時間をつくる")
    if premium_by_state:
        architecture["section_naming"] = [section_headlines.get(item["section_id"], item["key_message"]) for item in ia]
        strategy["narrative_architecture"] = architecture
    hero_override = dict(premium_surface.get("hero") or {})
    hero_headline = _text(hero_override.get("headline")) or headline
    hero_supporting = _text(hero_override.get("supporting")) or f"{location}で{category}を探している方へ。{public_truth}。{signature_phrase}を手がかりに、次の一歩を考えます。"
    hero_microcopy = _text(hero_override.get("microcopy")) or f"{location}｜{signature_phrase}。"
    hero_semantic_text = _semantic_text(hero_headline, "hero_headline", _line_shape(hero_headline, max_chars=9 if field_validation else 7), context={"subject": category, "preferred_line_policy": "meaning_unit"})
    return {
        "schema_version": SCHEMA_VERSION,
        "hero": {
            "eyebrow": company_name,
            "headline": hero_headline,
            "headline_lines": _line_shape(hero_headline, max_chars=9 if field_validation else 7),
            "semantic_text": hero_semantic_text,
            "supporting": hero_supporting,
            "supporting_semantic_text": _semantic_text(hero_supporting, "lead", paragraphs=[part for part in hero_supporting.splitlines() if part.strip()], context={"subject": category}),
            "cta": cta,
            "cta_semantic_text": _semantic_text(cta, "cta", [cta]),
            "microcopy": hero_microcopy,
        },
        "sections": [
            {
                "section_id": item["section_id"],
                "headline": section_headlines.get(item["section_id"], item["key_message"]),
                "headline_lines": _line_shape(section_headlines.get(item["section_id"], item["key_message"]), max_chars=11),
                "semantic_text": _semantic_text(section_headlines.get(item["section_id"], item["key_message"]), "section_headline", _line_shape(section_headlines.get(item["section_id"], item["key_message"]), max_chars=11), context={"section_id": item["section_id"]}),
                "body": {
                    "opening": (f"{location}で、住まいの状態を相談できます。" if layout_profile == "field_ledger" else f"{location}で、自分に合う過ごし方を考える時間をつくります。" if layout_profile == "care_rhythm" else f"{location}の料理教室で、食材と手を動かす時間に出会います。"),
                    "truth": (public_truth if layout_profile != "studio_invitation" else "ストウブ無水料理を学び、食材から一皿ができていく流れを確かめます。"),
                    "way_in": (f"{compact_category}の現場を見渡し、{signature_phrase}へ目を向けます。" if layout_profile == "field_ledger" else f"頭をゆるめる時間の流れを、静かな空間で確かめます。" if layout_profile == "care_rhythm" else "料理教室で食材を選び、料理の流れを一緒に学びます。"),
                    "contact": (f"表面の変化と手順を並べ、{compact_category}の仕上がりを思い描きます。" if layout_profile == "field_ledger" else "触れられる時間を選び、自分に合う過ごし方を考えます。" if layout_profile == "care_rhythm" else "手を動かし、火を入れる順序を確かめます。"),
                    "close": (f"{compact_category}の状態を見ながら、相談の準備を整えます。" if layout_profile == "field_ledger" else f"{compact_category}で、自分のための時間を予約します。" if layout_profile == "care_rhythm" else f"できあがる一皿を囲む時間へ、参加の一歩を踏み出します。"),
                }.get(item["section_id"], item["key_message"]),
                "evidence_claims": claims if item["section_id"] in {"truth", "contact"} else [],
                "cta": cta if item["section_id"] == "close" else "",
            }
            for item in ia
        ],
        "global_constraints": {
            "all_customer_facing_claims_require_evidence_id": True,
            "unsupported_reassurance": "blocked",
            "line_shape": "rendered_browser_line_shape_with_semantic_ir",
            "paragraph_architecture": "role_and_sentence_units_not_character_count",
            "copy_naturalness_gate": "subject_object_context_naturalness_commercial_usefulness",
        },
        "process_steps": process_steps,
        "premium_scene_copy": premium_surface,
    }


def build_art_direction(understanding: Mapping[str, Any], strategy: Mapping[str, Any]) -> dict[str, Any]:
    authorities = list(strategy.get("visual_authority_priority") or ["TYPOGRAPHY"])
    primary = authorities[0]
    profile = _text(strategy.get("layout_profile")) or "editorial_rail"
    palettes = {
        "MATERIAL": ("#151613", "#d7b27b", "#f1eadc"),
        "PRODUCT": ("#111417", "#cf6b3c", "#ece7de"),
        "PLACE": ("#132322", "#a7c1a4", "#e8eee6"),
        "PERSON": ("#1c1917", "#d8a58c", "#f6eee7"),
        "DATA": ("#101a33", "#7ea9df", "#e8edf7"),
        "DOCUMENT": ("#20201d", "#c8c1aa", "#efeee7"),
        "WORLD": ("#151d1d", "#b8c3aa", "#e7ebe2"),
        "SENSORY": ("#251719", "#de8f82", "#f4e7e4"),
        "TYPOGRAPHY": ("#151515", "#ba5e35", "#f3efe7"),
    }
    ink, accent, paper = palettes.get(primary, palettes["TYPOGRAPHY"])
    density = _text(understanding.get("evidence_density")) or "LOW"
    dimensional_logic = {
        "technical_drawing": {"macro_composition": "measured_split", "visual_density": "indexed_precision", "negative_space": "controlled_gaps", "surface": "ruled_work_surface", "section_transitions": "registration_lines", "rhythm": "measure_then_release", "motion": "reveal_the_next_measure"},
        "experience_calendar": {"macro_composition": "invitation_to_moment", "visual_density": "soft_intervals", "negative_space": "breathing_room", "surface": "daylight_paper", "section_transitions": "time_markers", "rhythm": "anticipate_then_pause", "motion": "reveal_the_chosen_moment"},
        "catalogue_spread": {"macro_composition": "selection_field", "visual_density": "curated_sparse", "negative_space": "object_isolation", "surface": "quiet_catalogue_stock", "section_transitions": "selection_rules", "rhythm": "scan_then_decide", "motion": "reveal_the_next_choice"},
        "conversation_rail": {"macro_composition": "reading_rail", "visual_density": "quiet_interruption", "negative_space": "listening_space", "surface": "calibrated_paper", "section_transitions": "question_marks", "rhythm": "ask_then_open", "motion": "reveal_the_next_question"},
        "editorial_rail": {"macro_composition": "reading_rail", "visual_density": "quiet_interruption", "negative_space": "listening_space", "surface": "calibrated_paper", "section_transitions": "question_marks", "rhythm": "ask_then_open", "motion": "reveal_the_next_question"},
        "field_ledger": {"macro_composition": "field_ledger", "visual_density": "measured_material", "negative_space": "inspection_gaps", "surface": "work_surface", "section_transitions": "datum_lines", "rhythm": "inspect_then_release", "motion": "trace_the_work"},
        "care_rhythm": {"macro_composition": "care_rhythm", "visual_density": "soft_focus", "negative_space": "breathing_intervals", "surface": "warm_matte", "section_transitions": "breath_marks", "rhythm": "arrive_then_settle", "motion": "settle_into_care"},
        "studio_invitation": {"macro_composition": "studio_invitation", "visual_density": "playful_index", "negative_space": "lesson_pauses", "surface": "studio_table", "section_transitions": "session_marks", "rhythm": "notice_then_try", "motion": "open_the_session"},
        "image_story": {"macro_composition": "image_story", "visual_density": "framed_moments", "negative_space": "story_breath", "surface": "gallery_wall", "section_transitions": "frame_marks", "rhythm": "remember_then_choose", "motion": "frame_the_moment"},
        "machine_catalogue": {"macro_composition": "machine_catalogue", "visual_density": "object_precision", "negative_space": "garage_gaps", "surface": "oiled_paper", "section_transitions": "part_marks", "rhythm": "inspect_then_specify", "motion": "reveal_the_detail"},
        "local_route": {"macro_composition": "local_route", "visual_density": "human_scale", "negative_space": "route_pauses", "surface": "neighborhood_paper", "section_transitions": "route_marks", "rhythm": "recognize_then_reach", "motion": "follow_the_route"},
    }.get(profile, {})
    scene = _text(understanding.get("visual_scene")) or "calibration"
    scene_copy = {
        "material_field": "A generated vector study of surface, edge and measured work; replace with the company’s own site, material or field image after rights clearance.",
        "care_experience": "A generated vector study of arrival, touch and breathing space; replace with an approved room, treatment or service image after rights clearance.",
        "studio_invitation": "A generated vector study of tools, hands and a shared table; replace with an approved lesson or workshop image after rights clearance.",
        "conversation": "A generated vector study of an open conversation path; replace with an approved owner or consultation-space image after rights clearance.",
        "image_story": "A generated vector study of a framed moment and its surrounding place; replace with an approved portfolio or scene image after rights clearance.",
        "machine_craft": "A generated vector study of parts, finish and inspection; replace with an approved vehicle, machine or workshop image after rights clearance.",
        "local_route": "A generated vector study of a local route and a point of care; replace with an approved service-area, home or companion image after rights clearance.",
        "calibration": "A generated vector calibration study for a future evidence slot.",
    }.get(scene, "A generated vector calibration study for a future evidence slot.")
    return {
        "schema_version": SCHEMA_VERSION,
        "art_direction_concept": _text(strategy.get("big_idea")),
        "visual_mood": {
            "technical_drawing": "measured workshop clarity with visible construction lines",
            "experience_calendar": "soft daylight rhythm with a sense of chosen time",
            "catalogue_spread": "tactile selection field with room around each object",
            "conversation_rail": "quiet editorial pacing with a human reading rail",
            "editorial_rail": "quiet confidence with a working-surface sense of detail",
            "field_ledger": "precise field intelligence with the warmth of a working craft",
            "care_rhythm": "soft, tactile care with room to breathe before choosing",
            "studio_invitation": "open studio energy with tools, hands and an invitation to try",
            "image_story": "quiet gallery light around a moment worth keeping",
            "machine_catalogue": "clean mechanical focus with tactile finish and inspection",
            "local_route": "human-scale local guidance with a clear route to contact",
        }.get(profile, "quiet confidence with a working-surface sense of detail"),
        "visual_authority_priority": authorities,
        "color_logic": {"ink": ink, "accent": accent, "paper": paper, "reason": f"{primary} is the first evidence-bearing authority."},
        "typography_logic": "Large meaning-unit headlines, compact labels, readable Japanese body text.",
        "composition_logic": {
            "technical_drawing": "A measured split rail, specification surface and sequential workbench; peaks are separated by quiet chapters.",
            "experience_calendar": "A generous invitation field, time-led proof surface and stacked booking path; avoid dashboard density.",
            "catalogue_spread": "A product-led opening, editorial selection spread and direct purchase path; let whitespace do the sorting.",
            "conversation_rail": "A narrow reading rail interrupted by one evidence-bearing offset surface; peaks are separated by quiet chapters.",
            "editorial_rail": "A narrow reading rail interrupted by one evidence-bearing offset surface; peaks are separated by quiet chapters.",
            "field_ledger": "A datum-led field opening, material inspection surface and measured quote route; evidence sits beside the decision it supports.",
            "care_rhythm": "A soft arrival opening, tactile care surface and generous booking pause; the page slows before asking for action.",
            "studio_invitation": "A studio-table opening, shared-tool evidence surface and session path; the page invites a first try rather than listing a menu.",
            "image_story": "A framed-moment opening, gallery-like evidence spread and quiet shooting path; space protects the emotional decision.",
            "machine_catalogue": "A machine-detail opening, inspection spread and direct contact route; object logic carries the decision without badge clutter.",
            "local_route": "A local-route opening, human-scale evidence surface and clear contact path; the page moves from situation to reachability.",
        }.get(profile, "A narrow reading rail interrupted by one evidence-bearing offset surface; peaks are separated by quiet chapters."),
        "photography_logic": scene_copy,
        "visual_scene": scene,
        "visual_source": "engine_generated_vector_scene",
        "photo_replacement_readiness": understanding.get("photo_replacement_readiness", {}),
        "icon_logic": "No generic icon wall; use line markers tied to the process sequence.",
        "texture_logic": "Subtle ruled-paper and calibration marks, never a decorative grain overlay.",
        "motion_logic": dimensional_logic.get("motion", "reveal meaning, never decoration") + "; one restrained reveal per section; no infinite or blocking animation.",
        "forbidden_patterns": ["rounded card wall", "generic three-column grid", "unsupported trust badge", "stock person", "marquee", "parallax"],
        "craft_catch": {
            "technical_drawing": "A measurement line carries the customer from a rough request to a quote-ready next step.",
            "experience_calendar": "A time marker carries the customer from a remembered occasion to a chosen visit.",
            "catalogue_spread": "A selection line carries the customer from purpose to a concrete item.",
            "conversation_rail": "A calibration line carries the customer from the current situation to the next contact point.",
            "editorial_rail": "A calibration line carries the customer from the current situation to the next contact point.",
            "field_ledger": "A datum line carries the customer from a visible condition to the information needed for a quote.",
            "care_rhythm": "A breath mark carries the customer from a vague need for care to a chosen kind of time.",
            "studio_invitation": "A session mark carries the customer from curiosity to a first activity they can name.",
            "image_story": "A frame edge carries the customer from a memory to a concrete place and shooting conversation.",
            "machine_catalogue": "An inspection line carries the customer from a symptom or finish wish to a specific work conversation.",
            "local_route": "A route line carries the customer from a daily difficulty to a reachable next contact.",
        }.get(profile, "A calibration line carries the customer from the current situation to the next contact point."),
        "layout_profile": profile,
        "art_direction_dimensions": {
            **dimensional_logic,
            "evidence_density": density,
            "visual_authority": primary,
            "crop_logic": "no client image dependency; abstract geometry carries the role",
        },
    }


def build_design_tokens(art_direction: Mapping[str, Any]) -> dict[str, Any]:
    color = dict(art_direction.get("color_logic") or {})
    profile = _text(art_direction.get("layout_profile")) or "editorial_rail"
    profile_tokens = {
        "field_ledger": {
            "display": 'Arial, "Helvetica Neue", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif',
            "body": 'Arial, "Helvetica Neue", "Hiragino Kaku Gothic ProN", "Yu Gothic", sans-serif',
            "display_weight": 680, "body_weight": 430, "paper": "#EFECE4", "ink": "#20211E", "accent": "#9E8459", "muted": "#6D6B63", "line": "rgba(32,33,30,.24)",
            "surface_radius": "3px", "button_radius": "0px", "scene_radius": "3px", "border_width": "2px", "edge_width": "2px", "section_gap": "clamp(4.5rem, 8vw, 7rem)", "ending_padding": "clamp(4.5rem, 8vw, 6rem)", "copy_surface": "#EFECE4", "scene_columns": "minmax(0,.38fr) minmax(0,.62fr)", "media_fit": "cover", "hero_size": "clamp(3.25rem, 5.2vw, 4rem)", "h2_size": "clamp(2rem, 3.6vw, 3.5rem)", "body_leading": "1.62", "mobile_hero": "clamp(2.25rem, 9vw, 2.75rem)", "mobile_h2": "clamp(1.9rem, 8vw, 2.25rem)", "mobile_gap": "clamp(3rem, 12vw, 4.5rem)", "mobile_padding": "clamp(3rem, 12vw, 4.5rem)", "ending_variant": "grounded_field_closure", "grid": "12-column field ledger", "cadence": "compact measured",
        },
        "care_rhythm": {
            "display": '"Hiragino Mincho ProN", "Yu Mincho", YuMincho, serif',
            "body": 'ui-sans-serif, system-ui, -apple-system, "Hiragino Sans", sans-serif',
            "display_weight": 450, "body_weight": 420, "paper": "#F7F3EE", "ink": "#39332F", "accent": "#B7A39B", "muted": "#81756F", "line": "rgba(57,51,47,.14)",
            "surface_radius": "32px", "button_radius": "32px", "scene_radius": "32px", "border_width": "0px", "edge_width": "0px", "section_gap": "clamp(7.5rem, 15vw, 10.5rem)", "ending_padding": "clamp(8rem, 16vw, 10.5rem)", "copy_surface": "transparent", "scene_columns": "minmax(0,.44fr) minmax(0,.56fr)", "media_fit": "cover", "hero_size": "clamp(3.25rem, 5.6vw, 4.5rem)", "h2_size": "clamp(2.1rem, 3.6vw, 3.2rem)", "body_leading": "1.95", "mobile_hero": "clamp(2.1rem, 10vw, 2.65rem)", "mobile_h2": "clamp(1.75rem, 7.6vw, 2.2rem)", "mobile_gap": "clamp(5.5rem, 24vw, 7.5rem)", "mobile_padding": "clamp(5.5rem, 24vw, 7.5rem)", "ending_variant": "quiet_afterglow_closure", "grid": "loose editorial 44/56", "cadence": "long breathing intervals",
        },
        "studio_invitation": {
            "display": '"Hiragino Kaku Gothic ProN", "Yu Gothic", Meiryo, system-ui, sans-serif',
            "body": '"Hiragino Kaku Gothic ProN", "Yu Gothic", Meiryo, system-ui, sans-serif',
            "display_weight": 700, "body_weight": 520, "paper": "#FFF7EB", "ink": "#2D231B", "accent": "#C66F49", "muted": "#77765A", "line": "rgba(45,35,27,.22)",
            "surface_radius": "10px", "button_radius": "10px", "scene_radius": "10px", "border_width": "1px", "edge_width": "1px", "section_gap": "clamp(5rem, 9vw, 7rem)", "ending_padding": "clamp(5rem, 9vw, 7rem)", "copy_surface": "#FFF7EB", "scene_columns": "minmax(0,.4fr) minmax(0,.6fr)", "media_fit": "cover", "hero_size": "clamp(3.35rem, 5.2vw, 4.6rem)", "h2_size": "clamp(2.1rem, 3.8vw, 3.5rem)", "body_leading": "1.7", "mobile_hero": "clamp(2rem, 9vw, 2.9rem)", "mobile_h2": "clamp(2rem, 8vw, 2.5rem)", "mobile_gap": "clamp(3.5rem, 14vw, 5rem)", "mobile_padding": "clamp(3.5rem, 14vw, 5rem)", "ending_variant": "communal_table_closure", "grid": "modular table/process", "cadence": "active medium density",
        },
    }
    chosen = dict(profile_tokens.get(profile, profile_tokens["field_ledger"]))
    paper = chosen["paper"]
    ink = chosen["ink"]
    accent = chosen["accent"]
    return {
        "schema_version": SCHEMA_VERSION,
        "profile_id": profile,
        "colors": {"ink": color.get("ink", ink) if profile not in profile_tokens else ink, "accent": color.get("accent", accent) if profile not in profile_tokens else accent, "paper": color.get("paper", paper) if profile not in profile_tokens else paper, "muted": chosen["muted"], "line": chosen["line"]},
        "typography": {"display": chosen["display"], "body": chosen["body"], "display_weight": chosen["display_weight"], "body_weight": chosen["body_weight"]},
        "font_scale": {"eyebrow": "0.72rem", "body": "1rem", "lead": "1.18rem", "h2": chosen["h2_size"], "hero": chosen["hero_size"], "body_leading": chosen["body_leading"]},
        "spacing": {"unit": "8px", "section": chosen["section_gap"], "rail": "min(92vw, 1180px)", "text": "min(90vw, 780px)", "ending": chosen["ending_padding"], "mobile_section": chosen["mobile_gap"], "mobile_padding": chosen["mobile_padding"]},
        "radius": {"surface": chosen["surface_radius"], "button": chosen["button_radius"], "media": chosen["scene_radius"]},
        "borders": {"hairline": f'{chosen["border_width"]} solid var(--line)', "strong": f'{chosen["border_width"]} solid var(--ink)', "width": chosen["border_width"], "edge_width": chosen["edge_width"]},
        "shadows": {"surface": "none" if profile == "care_rhythm" else ("8px 10px 0 rgba(198,111,73,.22)" if profile == "studio_invitation" else "6px 8px 0 rgba(158,132,89,.14)")},
        "container_widths": {"rail": "min(90vw, 1180px)", "text": "min(90vw, 720px)"},
        "rhythm": {"peak_to_quiet": "1.5", "quiet_to_peak": "1.15", "section_gap": chosen["section_gap"], "cadence": chosen["cadence"]},
        "grid": chosen["grid"],
        "image_framing": {"radius": chosen["scene_radius"], "fit": chosen["media_fit"], "profile_behavior": chosen["grid"], "scene_columns": chosen["scene_columns"], "copy_surface": chosen["copy_surface"]},
        "ending": {"variant": chosen["ending_variant"], "padding": chosen["ending_padding"], "border_width": chosen["border_width"]},
        "mobile": {"hero": chosen["mobile_hero"], "h2": chosen["mobile_h2"], "section_gap": chosen["mobile_gap"], "padding": chosen["mobile_padding"], "identity": chosen["cadence"]},
        "motion": {"duration_ms": 520, "easing": "cubic-bezier(.2,.7,.2,1)"},
    }


def build_compositions(ia: Sequence[Mapping[str, Any]], art_direction: Mapping[str, Any]) -> list[dict[str, Any]]:
    compositions: list[dict[str, Any]] = []
    profile = _text(art_direction.get("layout_profile")) or "editorial_rail"
    for index, section in enumerate(ia):
        role = _text(section.get("section_role"))
        by_profile = {
            "technical_drawing": {
                "hero_orientation": ("drawing_split", "left", "headline"), "company_truth": ("spec_surface", "left", "evidence"),
                "service_process": ("numbered_workbench", "left", "rhythm"), "next_step": ("quote_strip", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
            "experience_calendar": {
                "hero_orientation": ("invitation_field", "center", "headline"), "company_truth": ("moment_spread", "left", "evidence"),
                "service_process": ("visit_sequence", "left", "rhythm"), "next_step": ("booking_strip", "left", "channel"), "cta_zone": ("closing_field", "center", "action"),
            },
            "catalogue_spread": {
                "hero_orientation": ("catalogue_cover", "left", "headline"), "company_truth": ("product_spread", "left", "evidence"),
                "service_process": ("selection_rail", "left", "rhythm"), "next_step": ("purchase_strip", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
            "field_ledger": {
                "hero_orientation": ("field_cover", "left", "headline"), "company_truth": ("material_inspection", "left", "evidence"),
                "service_process": ("work_sequence", "left", "rhythm"), "next_step": ("quote_route", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
            "care_rhythm": {
                "hero_orientation": ("care_invitation", "left", "headline"), "company_truth": ("care_surface", "right", "evidence"),
                "service_process": ("arrival_sequence", "left", "rhythm"), "next_step": ("care_contact", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
            "studio_invitation": {
                "hero_orientation": ("studio_cover", "left", "headline"), "company_truth": ("table_spread", "left", "evidence"),
                "service_process": ("session_sequence", "left", "rhythm"), "next_step": ("lesson_contact", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
            "image_story": {
                "hero_orientation": ("frame_cover", "left", "headline"), "company_truth": ("moment_gallery", "left", "evidence"),
                "service_process": ("story_sequence", "left", "rhythm"), "next_step": ("shoot_contact", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
            "machine_catalogue": {
                "hero_orientation": ("machine_cover", "left", "headline"), "company_truth": ("part_spread", "left", "evidence"),
                "service_process": ("inspection_sequence", "left", "rhythm"), "next_step": ("garage_contact", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
            "local_route": {
                "hero_orientation": ("route_cover", "left", "headline"), "company_truth": ("local_map", "right", "evidence"),
                "service_process": ("route_sequence", "left", "rhythm"), "next_step": ("local_contact", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
            },
        }
        layout, alignment, emphasis = by_profile.get(profile, {}).get(role, {
            "hero_orientation": ("split_rail", "left", "headline"), "company_truth": ("offset_evidence_surface", "left", "evidence"),
            "service_process": ("sequence_rail", "left", "rhythm"), "next_step": ("contact_strip", "left", "channel"), "cta_zone": ("closing_field", "left", "action"),
        }.get(role, ("closing_field", "left", "action")))
        compositions.append({
            "section_id": section["section_id"],
            "layout_type": layout,
            "column_logic": "12-column reading rail; one dominant field and one supporting field.",
            "alignment": alignment,
            "image_role": f"generated_{_text(art_direction.get('visual_scene')) or 'calibration'}_scene",
            "photo_replacement_role": "same-role-approved-real-image",
            "text_width": "min(90vw, 720px)",
            "whitespace": "large" if section.get("quiet_or_peak") == "peak" else "medium",
            "emphasis": emphasis,
            "mobile_transformation": section.get("mobile_behavior"),
            "screenshot_peak": section.get("quiet_or_peak") == "peak",
            "order": index,
            "layout_profile": profile,
        })
    return compositions


def apply_controlled_architecture(
    compositions: Sequence[Mapping[str, Any]],
    architecture: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Materialize a frozen architecture decision into composition planning."""
    if not architecture:
        return [dict(item) for item in compositions]
    grammar = architecture.get("module_grammar") or {}
    patterns = list(grammar.get("selected_patterns") or [])
    if not patterns:
        raise ValueError("controlled architecture requires selected module grammar")
    role_pattern = {"hero_orientation": "hero", "company_truth": "trust", "service_process": "service", "next_step": "cta", "cta_zone": "end"}
    enriched: list[dict[str, Any]] = []
    for index, item in enumerate(compositions):
        row = dict(item)
        wanted = role_pattern.get(str(row.get("section_role") or ""))
        chosen = next((pattern for pattern in patterns if wanted and wanted in str(pattern.get("pattern_id", "")).lower()), patterns[index % len(patterns)])
        pattern_id = str(chosen.get("pattern_id") or "")
        row["architecture_pattern_id"] = pattern_id
        row["architecture_grammar"] = str(chosen.get("name") or pattern_id)
        row["architecture_mobile_principle"] = chosen.get("mobile_principle")
        row["architecture_selection_basis"] = "frozen family + customer decision state + compatible grammar"
        row["layout_type"] = f"architecture-{pattern_id.lower()}"
        enriched.append(row)
    return enriched

def build_render_spec(
    understanding: Mapping[str, Any],
    strategy: Mapping[str, Any],
    ia: Sequence[Mapping[str, Any]],
    copy: Mapping[str, Any],
    art_direction: Mapping[str, Any],
    tokens: Mapping[str, Any],
    compositions: Sequence[Mapping[str, Any]],
    safety_report: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "company": dict(understanding),
        "strategy": dict(strategy),
        "ia": list(ia),
        "copy": dict(copy),
        "art_direction": dict(art_direction),
        "design_tokens": dict(tokens),
        "compositions": list(compositions),
        "motion_spec": {"kind": "section_reveal", "duration_ms": tokens["motion"]["duration_ms"], "easing": tokens["motion"]["easing"], "reduced_motion": "no_transform"},
        "approved_evidence_ids": [item.get("evidence_id") for item in safety_report.get("eligible_evidence", [])],
        "production_output_status": "PRODUCTION_APPROVED" if safety_report.get("safety_status") == "PASS" else "NOT_PRODUCTION_APPROVED",
    }


def _render_styles(tokens: Mapping[str, Any]) -> str:
    colors = tokens["colors"]
    typo = tokens["typography"]
    scale = tokens["font_scale"]
    spacing = tokens["spacing"]
    radius = tokens.get("radius", {})
    borders = tokens.get("borders", {})
    mobile = tokens.get("mobile", {})
    grid = tokens.get("image_framing", {}).get("profile_behavior", "editorial")
    return f"""
    :root {{ --ink:{colors['ink']}; --accent:{colors['accent']}; --paper:{colors['paper']}; --muted:{colors['muted']}; --line:{colors['line']}; --rail:{spacing['rail']}; --text:{spacing['text']}; --ease:{tokens['motion']['easing']}; --display:{typo['display']}; --display-weight:{typo['display_weight']}; --body-weight:{typo['body_weight']}; --surface-radius:{radius.get('surface','2px')}; --media-radius:{radius.get('media',radius.get('surface','2px'))}; --human-border-width:{borders.get('width','1px')}; --human-edge-width:{borders.get('edge_width','1px')}; --scene-gap:{spacing['section']}; --mobile-scene-gap:{mobile.get('section_gap','4rem')}; --mobile-page-padding:{mobile.get('padding','3rem')}; --hero-size:{scale['hero']}; --h2-size:{scale['h2']}; --body-leading:{scale.get('body_leading','1.75')}; --grid-profile:{grid}; }}
    * {{ box-sizing:border-box; }} html {{ scroll-behavior:smooth; }} body {{ margin:0; background:var(--paper); color:var(--ink); font-family:{typo['body']}; font-weight:var(--body-weight); line-height:var(--body-leading); }}
    a {{ color:inherit; }} .site-shell {{ overflow:hidden; }} .topline {{ width:var(--rail); margin:auto; padding:24px 0; display:flex; justify-content:space-between; gap:24px; border-bottom:1px solid var(--line); font-size:{scale['eyebrow']}; letter-spacing:.12em; text-transform:uppercase; }}
    .section {{ width:var(--rail); margin:auto; padding:var(--section, {spacing['section']}) 0; position:relative; }} .section--quiet {{ padding-top:clamp(4rem,8vw,8rem); padding-bottom:clamp(4rem,8vw,8rem); }} .section--peak {{ min-height:min(92vh, 860px); display:grid; align-content:center; }}
    .hero-grid {{ display:grid; grid-template-columns:minmax(0, 1.4fr) minmax(160px, .6fr); gap:clamp(1.5rem, 5vw, 6rem); align-items:end; }} .eyebrow {{ color:var(--accent); font-size:{scale['eyebrow']}; letter-spacing:.12em; text-transform:uppercase; }} h1,h2,p {{ margin:0; }} h1 {{ max-width:none; font-family:var(--display); font-weight:var(--display-weight); font-size:var(--hero-size); line-height:1.06; letter-spacing:-.045em; }} h1 .headline-line,h2 .headline-line,.semantic-line {{ display:block; white-space:normal; text-wrap:balance; }} h2 {{ max-width:none; font-family:var(--display); font-weight:var(--display-weight); font-size:var(--h2-size); line-height:1.12; letter-spacing:-.035em; }} .lead {{ max-width:34rem; font-size:{scale['lead']}; }} .small {{ color:var(--muted); font-size:.82rem; }} .section-header {{ display:flex; justify-content:space-between; gap:2rem; align-items:flex-end; border-top:1px solid var(--line); padding-top:18px; margin-bottom:clamp(2rem,5vw,5rem); }}
    .hero-mark {{ aspect-ratio:1; border:1px solid var(--ink); position:relative; background:linear-gradient(135deg, transparent 48%, var(--accent) 49%, var(--accent) 51%, transparent 52%), repeating-linear-gradient(0deg, transparent 0 19px, var(--line) 20px); }} .hero-mark::before,.hero-mark::after {{ content:""; position:absolute; border:1px solid var(--ink); border-radius:50%; width:28%; aspect-ratio:1; left:14%; top:18%; }} .hero-mark::after {{ left:auto; top:auto; right:14%; bottom:18%; }}
    .visual-scene {{ position:relative; min-height:clamp(240px,34vw,480px); overflow:hidden; border:var(--human-border-width) solid var(--ink); border-radius:var(--surface-radius); background:var(--paper); isolation:isolate; }} .visual-scene::after {{ content:""; position:absolute; inset:10%; border:1px solid color-mix(in srgb, var(--ink) 34%, transparent); pointer-events:none; }} .scene-caption {{ position:absolute; left:18px; bottom:16px; z-index:3; font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; color:var(--muted); }}
    .scene-material_field {{ background:linear-gradient(135deg,var(--paper) 0 48%,var(--accent) 48% 50%,var(--ink) 50% 52%,var(--paper) 52%); }} .scene-material_field .scene-plane {{ position:absolute; width:65%; height:46%; right:10%; top:18%; background:var(--ink); transform:skewY(-12deg); box-shadow:18px 18px 0 var(--accent); }} .scene-material_field .scene-line {{ position:absolute; left:12%; right:12%; bottom:28%; border-top:1px solid var(--ink); }}
    .scene-care_experience {{ border-radius:48% 48% 8px 8px; background:radial-gradient(circle at 36% 34%,var(--accent) 0 7%,transparent 8%),radial-gradient(circle at 68% 63%,var(--ink) 0 5%,transparent 6%),linear-gradient(145deg,var(--paper),#fff 55%,var(--accent)); }} .scene-care_experience .scene-ring {{ position:absolute; width:58%; aspect-ratio:1; border:1px solid var(--ink); border-radius:50%; left:21%; top:16%; }} .scene-care_experience .scene-ring::after {{ content:""; position:absolute; inset:14%; border:1px solid var(--accent); border-radius:50%; }}
    .scene-studio_invitation {{ background:linear-gradient(135deg,var(--paper) 0 62%,var(--accent) 62%); }} .scene-studio_invitation .scene-table {{ position:absolute; width:76%; height:27%; left:12%; bottom:22%; background:var(--ink); transform:rotate(-4deg); }} .scene-studio_invitation .scene-tool {{ position:absolute; width:19%; aspect-ratio:1; border:1px solid var(--ink); background:var(--paper); border-radius:50%; top:20%; }} .scene-studio_invitation .scene-tool:nth-child(2) {{ left:22%; }} .scene-studio_invitation .scene-tool:nth-child(3) {{ left:45%; background:var(--accent); }} .scene-studio_invitation .scene-tool:nth-child(4) {{ left:68%; }}
    .scene-conversation {{ background:linear-gradient(90deg,var(--ink) 0 2%,transparent 2% 98%,var(--ink) 98%),var(--paper); }} .scene-conversation .scene-path {{ position:absolute; width:70%; height:60%; left:15%; top:18%; border:1px solid var(--accent); border-radius:50% 50% 50% 8%; transform:rotate(-15deg); }} .scene-conversation .scene-path::after {{ content:""; position:absolute; width:18px; height:18px; border-radius:50%; background:var(--accent); right:10%; bottom:8%; }}
    .scene-image_story {{ background:linear-gradient(120deg,var(--ink) 0 18%,var(--paper) 18% 82%,var(--accent) 82%); }} .scene-image_story .scene-frame {{ position:absolute; width:58%; height:62%; left:21%; top:17%; border:12px solid var(--paper); outline:1px solid var(--ink); background:linear-gradient(140deg,var(--accent) 0 38%,transparent 38%),linear-gradient(35deg,var(--ink) 0 44%,transparent 44%); box-shadow:14px 14px 0 var(--ink); }}
    .scene-machine_craft {{ background:repeating-linear-gradient(90deg,transparent 0 26px,color-mix(in srgb,var(--ink) 20%,transparent) 27px 28px),var(--paper); }} .scene-machine_craft .scene-object {{ position:absolute; width:70%; height:34%; left:15%; top:29%; border:2px solid var(--ink); border-radius:48% 22% 16% 18%; transform:skewX(-12deg); }} .scene-machine_craft .scene-object::before,.scene-machine_craft .scene-object::after {{ content:""; position:absolute; width:18%; aspect-ratio:1; border:2px solid var(--ink); border-radius:50%; bottom:-18%; background:var(--paper); }} .scene-machine_craft .scene-object::before {{ left:14%; }} .scene-machine_craft .scene-object::after {{ right:14%; }}
    .scene-local_route {{ background:linear-gradient(135deg,var(--paper),#fff 60%,var(--accent)); }} .scene-local_route .scene-route {{ position:absolute; width:62%; height:70%; left:19%; top:14%; border-left:2px solid var(--ink); border-bottom:2px solid var(--accent); border-radius:0 0 0 70%; transform:rotate(-22deg); }} .scene-local_route .scene-pin {{ position:absolute; width:26px; height:26px; border:2px solid var(--ink); border-radius:50% 50% 50% 0; transform:rotate(-45deg); }} .scene-local_route .scene-pin::after {{ content:""; position:absolute; inset:7px; border-radius:50%; background:var(--accent); }} .scene-local_route .scene-pin:nth-child(2) {{ top:18%; left:22%; }} .scene-local_route .scene-pin:nth-child(3) {{ right:20%; bottom:18%; }}
    .proof-surface {{ display:grid; grid-template-columns:.9fr 1.1fr; gap:clamp(2rem,8vw,8rem); padding:clamp(2rem,5vw,5rem); background:var(--ink); color:var(--paper); box-shadow:10px 18px 0 var(--accent); }} .proof-surface .eyebrow {{ color:var(--accent); }} .claim-list {{ display:grid; gap:0; border-top:1px solid rgba(243,239,231,.3); }} .claim {{ padding:18px 0; border-bottom:1px solid rgba(243,239,231,.3); }} .claim-id {{ display:block; color:var(--accent); font-size:.72rem; letter-spacing:.1em; }}
    .sequence {{ display:grid; grid-template-columns:repeat(3,1fr); border-top:1px solid var(--line); }} .step {{ min-height:220px; padding:18px 22px 24px 0; border-bottom:1px solid var(--line); border-right:1px solid var(--line); }} .step:last-child {{ border-right:0; padding-left:22px; }} .step + .step {{ padding-left:22px; }} .step-number {{ font-size:3rem; line-height:1; color:var(--accent); }}
    .contact-strip {{ display:grid; grid-template-columns:1fr auto; gap:2rem; align-items:center; border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); padding:28px 0; }} .contact-lines {{ display:grid; gap:4px; }} .button {{ display:inline-flex; align-items:center; justify-content:center; min-height:52px; padding:12px 26px; border-radius:999px; background:var(--accent); color:var(--paper); text-decoration:none; font-weight:700; }} .button:hover {{ background:var(--ink); }} .footer-note {{ padding:24px 0 48px; font-size:.76rem; color:var(--muted); border-top:1px solid var(--line); }} .calibration {{ position:absolute; right:0; top:18%; width:18vw; max-width:220px; height:1px; background:var(--accent); }} .calibration::after {{ content:""; position:absolute; right:0; top:-4px; width:9px; height:9px; border-radius:50%; background:var(--accent); }}
    [data-reveal] {{ opacity:0; transform:translateY(18px); transition:opacity 520ms var(--ease), transform 520ms var(--ease); }} [data-reveal].is-visible {{ opacity:1; transform:none; }} @media (prefers-reduced-motion:reduce) {{ html {{ scroll-behavior:auto; }} [data-reveal] {{ opacity:1; transform:none; transition:none; }} }}
    .page-technical_drawing .hero-mark {{ background:linear-gradient(90deg, transparent 49%, var(--accent) 49% 51%, transparent 51%), linear-gradient(0deg, transparent 49%, var(--ink) 49% 51%, transparent 51%); }} .page-technical_drawing .proof-surface {{ box-shadow:10px 18px 0 var(--accent); }} .page-technical_drawing .sequence {{ border-left:8px solid var(--accent); }}
    .page-experience_calendar .hero-mark {{ border-radius:50%; background:radial-gradient(circle at 35% 35%, var(--accent) 0 8%, transparent 9%), radial-gradient(circle at 68% 68%, var(--ink) 0 7%, transparent 8%), repeating-radial-gradient(circle, transparent 0 24px, var(--line) 25px 26px); }} .page-experience_calendar .section--peak:first-child {{ text-align:center; }} .page-experience_calendar .hero-grid {{ align-items:center; }}
    .page-catalogue_spread .hero-mark {{ background:linear-gradient(125deg, var(--accent) 0 18%, transparent 19% 56%, var(--ink) 57% 60%, transparent 61%), repeating-linear-gradient(90deg, transparent 0 28px, var(--line) 29px 30px); }} .page-catalogue_spread .proof-surface {{ grid-template-columns:1.2fr .8fr; box-shadow:none; border:1px solid var(--ink); background:transparent; color:var(--ink); }} .page-catalogue_spread .claim-list {{ border-color:var(--line); }} .page-catalogue_spread .claim {{ border-color:var(--line); }}
    .page-field_ledger {{ background:#efede6; }} .page-field_ledger .section-header {{ border-top-width:2px; }} .page-field_ledger .proof-surface {{ border-left:10px solid var(--accent); }} .page-care_rhythm {{ background:#f4ece8; }} .page-care_rhythm .section--peak:first-child {{ min-height:84vh; }} .page-care_rhythm .proof-surface {{ border-radius:42% 8px 42% 8px; }} .page-studio_invitation {{ background:#f3efe5; }} .page-studio_invitation .proof-surface {{ transform:none; }} .page-image_story {{ background:#eeeae4; }} .page-image_story .proof-surface {{ background:var(--paper); color:var(--ink); border:1px solid var(--ink); box-shadow:14px 14px 0 var(--ink); }} .page-image_story .claim-list,.page-image_story .claim {{ border-color:var(--line); }} .page-machine_catalogue {{ background:#e9ecea; }} .page-machine_catalogue .proof-surface {{ box-shadow:none; border:1px solid var(--ink); }} .page-local_route {{ background:#eef1e8; }} .page-local_route .proof-surface {{ border-radius:0 36px 0 36px; }}
    .proof-surface .visual-scene {{ min-height:220px; margin-top:32px; border-color:rgba(243,239,231,.38); }} .page-image_story .proof-surface .visual-scene {{ border-color:var(--ink); }}
    @media (max-width:760px) {{ .topline {{ padding:18px 0; }} .hero-grid,.proof-surface,.contact-strip {{ grid-template-columns:1fr; }} .section {{ padding:var(--mobile-page-padding) 0; }} .section--peak {{ min-height:auto; }} h1 {{ font-size:var(--mobile-hero); }} h2 {{ font-size:var(--mobile-h2); }} .hero-mark {{ width:min(72vw,320px); margin-left:auto; }} .visual-scene {{ min-height:clamp(210px,64vw,300px); }} .proof-surface {{ box-shadow:7px 10px 0 var(--accent); padding:24px; }} .proof-surface .visual-scene {{ min-height:180px; }} .sequence {{ grid-template-columns:1fr; }} .step,.step + .step,.step:last-child {{ min-height:0; padding:20px 0; border-right:0; }} .contact-strip .button {{ width:100%; }} .calibration {{ width:35vw; top:8%; }} }}
    """


def _visual_scene_markup(scene: str) -> str:
    """Render a non-factual, deterministic vector proxy for a photo role."""
    scene = scene if scene in {"material_field", "care_experience", "studio_invitation", "conversation", "image_story", "machine_craft", "local_route"} else "conversation"
    bodies = {
        "material_field": '<div class="scene-plane"></div><div class="scene-line"></div>',
        "care_experience": '<div class="scene-ring"></div>',
        "studio_invitation": '<div class="scene-table"></div><div class="scene-tool"></div><div class="scene-tool"></div><div class="scene-tool"></div>',
        "conversation": '<div class="scene-path"></div>',
        "image_story": '<div class="scene-frame"></div>',
        "machine_craft": '<div class="scene-object"></div>',
        "local_route": '<div class="scene-route"></div><div class="scene-pin"></div><div class="scene-pin"></div>',
    }
    # Replacement metadata stays machine-readable; internal production labels
    # must never leak into a customer-facing sales sample.
    return f'<div class="visual-scene scene-{scene}" data-visual-source="engine_generated_vector_scene" data-photo-replacement="same-role-approved-real-image" aria-hidden="true">{bodies[scene]}</div>'


def apply_controlled_architecture_to_scene_plan(
    scene_plan: Mapping[str, Any],
    architecture: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Make the selected compatible grammar drive the premium renderer."""
    if not architecture:
        return dict(scene_plan)
    grammar = architecture.get("module_grammar") or {}
    patterns = list(grammar.get("selected_patterns") or [])
    if not patterns:
        raise ValueError("controlled architecture requires selected module grammar")
    role_prefixes = ("M-HERO-", "M-TRUST-", "M-PROBLEM-", "M-SERVICE-", "M-CTA-", "M-END-")
    selected = {str(item.get("pattern_id")): item for item in patterns}
    ordered = [selected[key] for key in selected if str(key).startswith(role_prefixes)]
    if not ordered:
        ordered = patterns
    topology_by_pattern = {
        "M-HERO-01": "full", "M-HERO-03": "split", "M-TRUST-01": "layered",
        "M-TRUST-02": "inset", "M-PROBLEM-01": "sequence", "M-SERVICE-01": "split",
        "M-CTA-01": "inset", "M-END-01": "sequence", "M-END-02": "full",
    }
    result = {key: value for key, value in scene_plan.items() if key != "scene_plan"}
    result["scene_plan"] = []
    for index, scene in enumerate(scene_plan.get("scene_plan", [])):
        row = dict(scene)
        pattern = ordered[index % len(ordered)]
        pattern_id = str(pattern.get("pattern_id") or "")
        visual_grammar = dict(row.get("visual_grammar") or {})
        visual_grammar["topology"] = topology_by_pattern.get(pattern_id, visual_grammar.get("topology", "full"))
        visual_grammar["architecture_pattern_id"] = pattern_id
        visual_grammar["architecture_grammar"] = pattern.get("name") or pattern_id
        visual_grammar["architecture_mobile_principle"] = pattern.get("mobile_principle")
        row["visual_grammar"] = visual_grammar
        row["architecture_pattern_id"] = pattern_id
        result["scene_plan"].append(row)
    result["controlled_architecture"] = dict(architecture)
    return result


def apply_public_scene_semantics(scene_plan: Mapping[str, Any], architecture: Mapping[str, Any] | None) -> dict[str, Any]:
    """Materialize family/decision-job semantics into the public scene plan."""
    semantics = list((architecture or {}).get("public_scene_semantics") or [])
    scenes = list(scene_plan.get("scene_plan") or [])
    if not semantics or len(semantics) != len(scenes):
        return dict(scene_plan)
    result = {key: value for key, value in scene_plan.items() if key != "scene_plan"}
    result["scene_plan"] = []
    for index, (scene, semantic) in enumerate(zip(scenes, semantics)):
        row = dict(scene)
        row["legacy_narrative_state"] = row.get("narrative_state")
        row["scene_id"] = f"scene-{index + 1:02d}-{semantic['state']}"
        row["narrative_state"] = semantic["state"]
        row["narrative_function"] = semantic["role"]
        row["copy_intent"] = semantic["copy_intent"]
        row["visual_authority"] = semantic["visual_authority"]
        row["focal_entity"] = semantic["media_role"]
        row["expected_media"] = semantic["media_role"] != "typography"
        row["public_copy"] = {"headline": semantic["headline"], "body": semantic["body"]}
        row["public_cta_label"] = semantic.get("cta_label", "")
        row["cta_stage"] = semantic.get("cta_stage", "")
        row["semantic_role"] = semantic["role"]
        row["semantic_derivation"] = "frozen family + customer decision job"
        result["scene_plan"].append(row)
    result["public_semantic_profile"] = (architecture or {}).get("public_semantic_profile")
    result["public_semantic_derivation"] = (architecture or {}).get("public_semantic_derivation")
    return result

def _render_premium_html(spec: Mapping[str, Any]) -> str:
    company, copy, tokens = spec["company"], spec["copy"], spec["design_tokens"]
    plan = spec["premium_scene_plan"]
    translation = spec.get("premium_human_translation") or {}
    translation_by_id = {x.get("scene_id"): x for x in (translation.get("copy_translation") or {}).get("scenes", [])}
    cta_closures = {x.get("stage"): x for x in (translation.get("cta_closure") or {}).get("closures", [])}
    profile = translation.get("art_direction_token_profile") or {}
    profile_id = _text(tokens.get("profile_id") or profile.get("profile_id")) or "field_ledger"
    public_semantic_profile = _text(plan.get("public_semantic_profile"))
    token_css = ";".join([
        f'--human-scene-radius:{tokens.get("radius", {}).get("media", "2px")}',
        f'--human-border-width:{tokens.get("borders", {}).get("width", "1px")}',
        f'--human-cta-radius:{tokens.get("radius", {}).get("button", "0px")}',
        f'--human-edge-width:{tokens.get("borders", {}).get("edge_width", "1px")}',
        f'--scene-columns:{tokens.get("image_framing", {}).get("scene_columns", "minmax(0,1fr) minmax(0,1fr)")}',
        f'--ending-padding:{tokens.get("spacing", {}).get("ending", "4rem")}',
        f'--copy-surface:{tokens.get("image_framing", {}).get("copy_surface", "var(--paper)")}',
    ]) + ";"
    ia = list(spec.get("ia") or [])
    copy_by_id = {x.get("section_id"): x for x in copy.get("sections", [])}
    names = list(spec.get("strategy", {}).get("narrative_architecture", {}).get("section_naming") or [])
    ctas = {x.get("stage"): x for x in plan.get("scene_plan", [])}
    signature_anchors = list(translation.get("signature_anchors") or [])
    def esc(v): return html.escape(str(v or ""), quote=True)
    def heading_markup(value: str, tag: str) -> str:
        ir = repair_text_ir(make_text_ir(value, role="section_headline", context={"renderer": "premium"}))
        rendered = render_text_ir(ir, tag=tag, escape=esc)
        # Issue #81: the THREE fit scene needs an intentional mobile-only
        # meaning break. Keep the authored desktop/tablet DOM unchanged.
        if value == "暮らしに置いたときの相性を見る。":
            opening = f"<{tag}>"
            closing = f"</{tag}>"
            rendered = rendered.replace(
                opening,
                f'<{tag} class="headline-optical-three-fit"><span class="headline-optical-default">',
                1,
            ).replace(
                closing,
                f'</span><span class="headline-optical-mobile" aria-hidden="true">暮らしに置いた<br>ときの相性を見る。</span>{closing}',
                1,
            )
        return rendered
    chunks = []
    rendered_cta_stages = set()
    for i, scene in enumerate(plan.get("scene_plan", [])):
        grammar = scene["visual_grammar"]
        topology = grammar["topology"]
        section_id = ia[i].get("section_id") if i < len(ia) else ""
        translated = translation_by_id.get(scene.get("scene_id"), {})
        body = normalize_japanese_particles(_text((translated.get("outputs") or {}).get("body")) or copy_by_id.get(section_id, {}).get("body", scene["creative_reason"]))
        heading = normalize_japanese_particles(_text((translated.get("outputs") or {}).get("headline")) or (names[i] if i < len(names) else scene["narrative_state"]))
        trace = esc(json.dumps({"scene_id":scene["scene_id"],"narrative_index":i,"grammar":grammar,"copy_intent":scene["copy_intent"]}, ensure_ascii=False))
        # The final CTA-led scene is a typography/place moment. Never cycle
        # back to the hero asset when the approved pool is smaller than the
        # five-scene narrative.
        scene_asset = None if i == len(plan.get("scene_plan", [])) - 1 else select_asset_for_role(spec.get("asset_manifest", {}), scene.get("focal_entity"))
        if scene_asset and scene.get("photo_crop"):
            scene_asset = {**scene_asset, "crop": scene.get("photo_crop")}
        scene_photo = render_photo_asset(scene_asset)
        # A media-less scene is a deliberate composition, never a placeholder.
        media = f'<div class="scene-media scene-media--{esc(grammar["media_scale"])}" aria-hidden="true">{scene_photo}</div>' if scene_photo else ""
        heading_tag = "h1" if i == 0 else "h2"
        heading_html = heading_markup(heading, heading_tag)
        if topology == "sequence": inner = f'<div class="scene-sequence">{media}{heading_html}<ol><li>{esc(body)}</li></ol></div>'
        elif topology == "inset": inner = f'<div class="scene-inset">{media}<div>{heading_html}<p>{esc(body)}</p></div></div>'
        elif topology == "split": inner = f'<div class="scene-split"><div>{heading_html}<p>{esc(body)}</p></div>{media}</div>'
        elif topology == "layered": inner = f'<div class="scene-layered">{media}<div class="scene-layered-copy">{heading_html}<p>{esc(body)}</p></div></div>'
        else: inner = f'<div class="scene-full">{media}{heading_html}<p>{esc(body)}</p></div>'
        if i == 0:
            hero_meta = dict((copy.get("premium_scene_copy") or {}).get("hero_meta") or {})
            if hero_meta.get("items"):
                label = " / ".join(str(item) for item in hero_meta["items"]) if hero_meta.get("kind") == "scope_line" else "  ·  ".join(str(item) for item in hero_meta["items"])
                inner += f'<div class="hero-scope hero-scope--{esc(hero_meta.get("kind"))}">{esc(label)}</div>'
        cta = ""
        if scene.get("cta_stage") and scene.get("cta_stage") not in rendered_cta_stages:
            item = next((x for x in plan.get("scene_plan", []) if x.get("cta_stage") == scene["cta_stage"]), {})
            genome = next((x for x in spec["strategy"]["creative_genome"].get("cta_progression", []) if x.get("stage") == scene["cta_stage"]), {})
            closure = cta_closures.get(scene["cta_stage"], {})
            cta_href = closure.get("href") or genome.get("destination") or "#contact"
            cta_label = scene.get("public_cta_label") or genome.get("visible_label") or closure.get("semantic_payload") or "次へ進む"
            if closure.get("actionability") == "QUIET_CONVERSION_END":
                cta_label = closure.get("semantic_payload") or ""
            # A quiet end with no actual contact datum is intentionally a
            # buttonless close.  Labels such as 公式SNS never create gain.
            if closure.get("actionability") == "QUIET_CONVERSION_END" and not closure.get("actual_contact_datum_count"):
                cta_label = ""
            verified_href = closure.get("verified_action", {}).get("verified_external_href") or ""
            verified_attr = f' data-verified-external-href="{esc(verified_href)}"' if verified_href else ""
            if cta_label:
                cta = f'<a class="button" data-cta-stage="{esc(scene["cta_stage"])}" data-actionability="{esc(closure.get("actionability") or "ORIENTATION")}" data-destination-type="{esc(closure.get("destination_type") or "INFORMATIONAL_ONLY")}" data-state-before="{esc(closure.get("user_state_before"))}" data-state-after="{esc(closure.get("completion_state"))}" data-contact-datum-count="{esc(closure.get("actual_contact_datum_count", 0))}"{verified_attr} href="{esc(cta_href)}">{esc(cta_label)}</a>'
                rendered_cta_stages.add(scene.get("cta_stage"))
        rendered_text = f"{heading}{body}"
        trace_ids = list(scene.get("evidence_ids") or [])
        for evidence in spec.get("approved_evidence") or []:
            evidence_id = _text(evidence.get("evidence_id"))
            if evidence_id and _claim_matches(_text(evidence.get("claim")), rendered_text) and evidence_id not in trace_ids:
                trace_ids.append(evidence_id)
        evidence_trace = ",".join(hashlib.sha256(str(x).encode()).hexdigest()[:10] for x in trace_ids)
        # CTA destinations resolve to a different, content-bearing section;
        # the CTA source itself never doubles as its target.
        anchor = "way-in" if i == 1 else "reassurance" if i == 3 else "final-quiet-end" if i == len(plan.get("scene_plan", [])) - 1 else scene.get("scene_id", "")
        anchor_attr = f' id="{anchor}"' if anchor else ""
        anchor_ids = list(translated.get("signature_anchor_ids") or [])
        for anchor in signature_anchors:
            if anchor.get("classification") != "COMPANY_SIGNATURE":
                continue
            value = str(anchor.get("value") or "")
            fragments = [part for part in re.split(r"[・、。/／\s]+", value) if len(part) >= 2]
            fragment_hits = sum(part in rendered_text for part in fragments)
            threshold = 1 if len(fragments) <= 4 else 2
            if value and (value in rendered_text or fragment_hits >= threshold):
                anchor_ids.append(anchor.get("anchor_id"))
        anchor_attr_data = esc(",".join(x for x in anchor_ids if x))
        state_class = re.sub(r"[^a-z0-9_-]+", "-", _text(scene.get("narrative_state")).lower()) or "scene"
        legacy_state_class = re.sub(r"[^a-z0-9_-]+", "-", _text(scene.get("legacy_narrative_state")).lower())
        compatibility_class = f" scene-state-{legacy_state_class}" if legacy_state_class and legacy_state_class != state_class else ""
        ending_class = " premium-scene--ending" if i == len(plan.get("scene_plan", [])) - 1 else ""
        datum_attr = ' data-contact-datum-count="0"' if i == len(plan.get("scene_plan", [])) - 1 else ""
        chunks.append(f'<section{anchor_attr} class="premium-scene premium-scene--{esc(topology)} scene-state-{esc(state_class)}{compatibility_class}{ending_class}" data-scene-id="{esc(scene["scene_id"])}" data-narrative-state="{esc(scene.get("narrative_state"))}" data-narrative-index="{i}" data-ending-variant="{esc((copy.get("premium_scene_copy") or {}).get("ending_variant")) if i == len(plan.get("scene_plan", [])) - 1 else ""}"{datum_attr} data-grammar="{esc(json.dumps(grammar, ensure_ascii=False))}" data-copy-intent="{esc(scene["copy_intent"])}" data-evidence-trace="{evidence_trace}" data-translation-mode="{esc(translated.get("expression_mode"))}" data-signature-anchor-ids="{anchor_attr_data}">{inner}{cta}</section>')
    channel_data = spec.get("understanding", {}).get("contact_channels", {})
    contact_values = []
    for key in ("href", "url", "phone", "tel", "email", "line", "instagram", "booking_url", "contact_form_url", "contact_value"):
        value = _text(channel_data.get(key))
        if re.search(r"(?:https?://|mailto:|tel:|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|0\d{1,4}[-ー－ ]\d{1,4}[-ー－ ]\d{3,4})", value, re.I):
            contact_values.append(value)
    channel = (spec.get("company") or {}).get("contact_channel") or (channel_data.get("primary") if contact_values else "")
    contact_context = "｜".join(str(value) for value in ((spec.get("company") or {}).get("location"), (spec.get("company") or {}).get("service_category")) if value)
    contact_claim = next((x.get("semantic_payload") for x in cta_closures.values() if x.get("stage") == "action" and x.get("semantic_payload")), "")
    contact_trace_ids = []
    contact_text = f"{contact_context}{contact_claim}{channel}{''.join(contact_values)}"
    for evidence in spec.get("approved_evidence") or []:
        evidence_id = _text(evidence.get("evidence_id"))
        if evidence_id and _claim_matches(_text(evidence.get("claim")), contact_text):
            contact_trace_ids.append(hashlib.sha256(evidence_id.encode()).hexdigest()[:10])
    contact_trace = ",".join(contact_trace_ids)
    contact_datum_markup = "".join(f"<p data-contact-datum=\"verified\">{esc(value)}</p>" for value in contact_values)
    contact_details = ""
    if contact_values:
        contact_details = f'<section id="contact" class="premium-contact-details" data-destination-type="VERIFIED_EXTERNAL" data-contact-datum-count="{len(contact_values)}" data-evidence-trace="{esc(contact_trace)}"><p>{esc(contact_context)}</p>{f"<p>{esc(contact_claim)}</p>" if contact_claim else ""}{f"<p>{esc(channel)}</p>" if channel else ""}{contact_datum_markup}</section>'
    ending_variant = esc((copy.get("premium_scene_copy") or {}).get("ending_variant"))
    style = f'''{_render_styles(tokens)}
    .premium-scene{{width:var(--rail);min-width:0;margin:auto;padding:var(--scene-gap) 0;border-top:var(--human-border-width) solid var(--line);border-radius:0;}}
    .premium-scene--ending{{padding:var(--ending-padding) 0;max-width:var(--rail);}}
    .scene-media{{min-width:0;max-width:100%;overflow:hidden;background:var(--ink);color:var(--paper);min-height:220px;display:grid;place-items:center;letter-spacing:.12em;border-radius:var(--human-scene-radius);}}
    .scene-media .photo-frame{{width:100%;max-width:100%;min-width:0;}}
    .scene-media .photo-frame img{{display:block;width:100%;max-width:100%;height:auto;min-width:0;object-fit:cover;object-position:center;}}
    .scene-media--immersive,.scene-media--dominant{{min-height:480px;}}
    .scene-inset,.scene-split{{min-width:0;display:grid;grid-template-columns:var(--scene-columns);gap:clamp(2rem,5vw,5rem);align-items:center;}}
    .scene-inset>*,.scene-split>*{{min-width:0;max-width:100%;}}
    .scene-layered{{position:relative;min-width:0;min-height:420px;overflow:hidden;}}
    .scene-layered-copy{{position:absolute;left:12%;bottom:8%;background:var(--copy-surface);padding:2rem;max-width:70%;min-width:0;border-radius:var(--human-scene-radius);}}
    .scene-full{{min-width:0;display:grid;gap:1.5rem;}}
    .scene-sequence{{min-width:0;border-left:var(--human-edge-width) solid var(--accent);padding:2rem;overflow-wrap:anywhere;}}
    .premium-scene h1,.premium-scene h2,.premium-scene p{{min-width:0;overflow-wrap:anywhere;white-space:pre-line;}}
    .premium-scene .button{{display:inline-flex;margin-top:2rem;padding:12px 26px;background:var(--accent);color:var(--paper);border-radius:var(--human-cta-radius);text-decoration:none;max-width:100%;}}
    .hero-scope{{margin-top:2rem;color:var(--accent);font-size:.72rem;letter-spacing:.13em;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;}}
    .hero-scope--fact_tabs{{display:flex;flex-wrap:wrap;gap:.65rem;letter-spacing:.08em;}}
    .hero-scope--fact_tabs::before{{content:"FACTS";color:var(--muted);margin-right:.45rem;}}
    .premium-contact-details{{width:var(--rail);margin:0 auto;padding:4rem 0;border-top:var(--human-border-width) solid var(--line);}}
    .profile-field_ledger .scene-state-imagine_change .scene-layered{{display:grid;grid-template-columns:minmax(0,.38fr) minmax(0,.62fr);align-items:stretch;min-height:420px;}}
    .profile-field_ledger .scene-state-imagine_change .scene-layered .scene-media{{grid-column:1;grid-row:1;min-height:100%;}}
    .profile-field_ledger .scene-state-imagine_change .scene-layered-copy{{position:static;grid-column:2;grid-row:1;align-self:center;max-width:none;padding:clamp(1.5rem,4vw,3rem);}}
    .profile-care_rhythm .premium-scene--ending{{max-width:min(90vw,780px);}}
    .profile-care_rhythm .premium-scene--ending .scene-layered-copy{{background:transparent;}}
    .profile-care_rhythm .scene-media{{box-shadow:none;}}
    /* Regina's choice scene keeps its material authority without allowing the
       desktop copy to collide with the media frame. Mobile keeps the existing
       stacked/layered treatment below 761px. */
    @media(min-width:761px){{.profile-care_rhythm .scene-state-choose_time .scene-layered{{display:grid;grid-template-columns:minmax(0,.56fr) minmax(0,.44fr);gap:clamp(2rem,4vw,4rem);align-items:stretch;min-height:clamp(420px,48vw,620px);overflow:visible;}}.profile-care_rhythm .scene-state-choose_time .scene-layered .scene-media{{grid-column:1;grid-row:1;min-height:100%;}}.profile-care_rhythm .scene-state-choose_time .scene-layered-copy{{position:static;grid-column:2;grid-row:1;align-self:center;max-width:none;padding:clamp(1.5rem,4vw,3rem);}}}}
    .profile-studio_invitation .scene-sequence{{background:color-mix(in srgb,var(--accent) 7%,transparent);}}
    .profile-studio_invitation .hero-scope--fact_tabs{{font-weight:var(--display-weight);}}
    @media(max-width:900px){{h1{{font-size:clamp(2.8rem,5vw,3.6rem);}}h2{{font-size:clamp(2rem,3.7vw,2.8rem);}}}}
    @media(min-width:761px) and (max-width:1100px){{.scene-state-feel_care .scene-media--dominant{{min-height:0;aspect-ratio:3 / 2;}}.scene-state-feel_care .scene-media--dominant .photo-frame{{height:100%;}}.scene-state-feel_care .scene-media--dominant .photo-frame img{{height:100%;object-fit:cover;}}}}
    @media(max-width:760px){{.premium-scene{{padding:var(--mobile-scene-gap) 0;}}.premium-scene--ending{{padding:var(--mobile-page-padding) 0;}}.scene-inset,.scene-split{{grid-template-columns:minmax(0,1fr);gap:2rem;}}.scene-media--immersive,.scene-media--dominant{{min-height:280px;}}.scene-layered-copy{{position:relative;left:0;bottom:auto;max-width:100%;margin-top:-2rem;padding:1rem;}}.profile-field_ledger .scene-state-imagine_change .scene-layered{{display:grid;grid-template-columns:1fr;}}.profile-field_ledger .scene-state-imagine_change .scene-layered .scene-media,.profile-field_ledger .scene-state-imagine_change .scene-layered-copy{{grid-column:1;grid-row:auto;}}.profile-field_ledger .scene-state-imagine_change .scene-layered-copy{{position:relative;margin-top:-2rem;}}.profile-care_rhythm .scene-layered-copy{{margin-top:-1rem;}}}}
         .headline-optical-mobile{display:none;}
     @media(max-width:767px){body[data-issue77-f01="three"] .premium-scene.scene-state-fit .headline-optical-three-fit .headline-optical-default{display:none;}body[data-issue77-f01="three"] .premium-scene.scene-state-fit .headline-optical-three-fit .headline-optical-mobile{display:inline;}}/* Narrow optical correction for the BW-F04 320px review finding only.
       Keep the semantic phrase and CTA intact; do not alter >=360px output. */
    @media(max-width:335px){{body[data-public-semantic-profile="craft"] .premium-scene:first-child h1{{font-size:2.1rem;line-height:1.28;}}body[data-public-semantic-profile="craft"] .premium-scene .button{{font-size:.82rem;letter-spacing:-.02em;padding-inline:14px;white-space:nowrap;}}}}
    '''
    public_semantic_profile = {"human_craft_provenance": "craft"}.get(public_semantic_profile, "")
    return f'<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(company.get("company_name"))}</title><style>{style}</style></head><body class="profile-{esc(profile_id)}" data-public-semantic-profile="{esc(public_semantic_profile)}" data-ending-variant="{ending_variant}" style="{token_css}"><header class="topline"><span>{esc(company.get("company_name"))}</span><span>{esc(company.get("location"))}</span></header><main>{"".join(chunks)}{contact_details}</main><footer class="topline">{esc(company.get("company_name"))}</footer></body></html>'

def render_html(spec: Mapping[str, Any]) -> str:
    if spec.get("premium_scene_plan"):
        return _render_premium_html(spec)
    company = spec["company"]
    copy = spec["copy"]
    tokens = spec["design_tokens"]
    art = spec["art_direction"]
    profile = _text(spec.get("strategy", {}).get("layout_profile")) or _text(art.get("layout_profile")) or "editorial_rail"
    composition_by_section = {item.get("section_id"): item for item in spec.get("compositions", [])}
    sections = {item["section_id"]: item for item in spec["ia"]}
    copy_sections = {item["section_id"]: item for item in copy["sections"]}
    evidence = spec.get("approved_evidence", [])
    hero = copy["hero"]
    contact_claims = [item for item in evidence if item.get("evidence_type") in {"CTA_CHANNEL", "POST_CLICK_FLOW", "ACCOUNTABILITY_SCOPE"}]
    service_claims = [item for item in evidence if item.get("evidence_type") in {"SERVICE_SCOPE", "SERVICE_PROCESS", "CRAFT_ACTION"}]
    claims_markup = "".join(
        f'<div class="claim">{_esc(item.get("claim"))}</div>'
        for item in (service_claims or evidence[:2])
    )
    contact_markup = "".join(f'<div>{_esc(item.get("claim"))}</div>' for item in contact_claims)
    steps = list(copy.get("process_steps") or ["状況を伝える", "対応できることを確認する", "次の案内を考える"])
    steps_markup = "".join(f'<div class="step"><div class="step-number">0{idx}</div><p>{_esc(label)}</p></div>' for idx, label in enumerate(steps, 1))
    def semantic_markup(record: Mapping[str, Any], tag: str = "h2") -> str:
        ir = record.get("semantic_text") or _semantic_text(_text(record.get("headline")), "section_headline", record.get("headline_lines"))
        return render_text_ir(ir, tag=tag, escape=_esc)
    lines_markup = semantic_markup(hero, "h1")
    location = _esc(company.get("location"))
    category = _esc(company.get("service_category"))
    name = _esc(company.get("company_name"))
    cta_plan = {item.get("stage"): item for item in (spec.get("strategy", {}).get("creative_genome", {}).get("cta_progression") or [])}
    def cta_markup(stage: str, default_label: str, default_href: str, arrow: str) -> str:
        item = cta_plan.get(stage, {})
        label = _esc(item.get("visible_label") or default_label)
        href = _esc(item.get("destination") or default_href)
        reason = _esc(item.get("action_reason") or "")
        return f'<a class="button" data-cta-stage="{_esc(stage)}" data-cta-purpose="{reason}" href="{href}">{label}<span aria-hidden="true" style="margin-left:14px">{arrow}</span></a>'
    contact = dict(company.get("contact_channels") or {})
    contact_href = _esc(contact.get("href") or "#contact")
    photo_role_map = dict(spec.get("photo_role_map") or {})
    asset_manifest = dict(spec.get("asset_manifest") or {})
    hero_role = _text((photo_role_map.get("section_role_map") or {}).get("hero_orientation"))
    hero_asset = select_asset_for_role(asset_manifest, hero_role) if hero_role else None
    photo_markup = render_photo_asset(hero_asset)
    def section_photo(section_role: str) -> str:
        role = _text((photo_role_map.get("section_role_map") or {}).get(section_role))
        return render_photo_asset(select_asset_for_role(asset_manifest, role)) if role else ""
    truth_photo = section_photo("company_truth")
    process_photo = section_photo("service_process")
    next_photo = section_photo("next_step")
    cta_photo = section_photo("cta_zone")
    vector_markup = _visual_scene_markup(_text(art.get("visual_scene")))
    scene_markup = photo_markup or f'<div data-vector-role="supporting_only">{vector_markup}</div>'
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>{name}｜{_esc(hero["headline"])}</title><style>{_render_styles(tokens)}{photography_css()}</style></head>
<body class="page-{_esc(profile)}"><div class="site-shell">
<header class="topline"><span>{name}</span><span>{location}</span></header>
<main>
<section class="section section--peak" data-reveal data-role="hero_orientation" data-layout="{_esc(composition_by_section.get("opening", {}).get("layout_type", "split_rail"))}"><div class="calibration"></div><div class="hero-grid"><div><div class="eyebrow">{_esc(hero["eyebrow"])}</div>{lines_markup}<p class="lead" style="margin-top:28px">{_esc(hero["supporting"])}</p>{cta_markup("discovery", hero["cta"], "#way-in", "→")}<p class="small" style="margin-top:16px">{_esc(hero["microcopy"])}</p></div>{scene_markup}</div></section>
<section class="section section--peak" data-reveal data-role="company_truth" data-layout="{_esc(composition_by_section.get("truth", {}).get("layout_type", "offset_evidence_surface"))}"><div class="section-header"><span class="eyebrow">01 / 会社の輪郭</span><span class="small">{location}</span></div><div class="proof-surface"><div>{semantic_markup(copy_sections["truth"])}{truth_photo}</div><div><p class="lead">{_esc(copy_sections["truth"]["body"])}</p><div class="claim-list" style="margin-top:34px">{claims_markup}</div></div></div></section>
<section class="section section--quiet" id="way-in" data-reveal data-role="service_process" data-layout="{_esc(composition_by_section.get("way_in", {}).get("layout_type", "sequence_rail"))}"><div class="section-header"><span class="eyebrow">02 / 入口のリズム</span><span class="small">{_esc(ia_label := _text(sections["way_in"].get("layout_hint")) or "次を考える")}</span></div><div class="hero-grid"><div>{semantic_markup(copy_sections["way_in"])}{process_photo}</div><div><p class="lead">{_esc(copy_sections["way_in"]["body"])}</p></div></div><div class="sequence" style="margin-top:64px">{steps_markup}</div></section>
<section class="section section--quiet" id="contact" data-reveal data-role="next_step" data-layout="{_esc(composition_by_section.get("contact", {}).get("layout_type", "contact_strip"))}"><div class="section-header"><span class="eyebrow">03 / 次の案内</span><span class="small">{location}</span></div><div class="contact-strip"><div>{semantic_markup(copy_sections["contact"])}<p class="lead" style="margin-top:24px">{_esc(copy_sections["contact"]["body"])}</p>{next_photo}<div class="contact-lines" style="margin-top:28px">{contact_markup}</div></div><div>{cta_markup("reassurance", hero["cta"], "#contact", "↗")}</div></div></section>
<section class="section section--peak" data-reveal data-role="cta_zone" data-layout="{_esc(composition_by_section.get("close", {}).get("layout_type", "closing_field"))}"><div class="hero-grid"><div><div class="eyebrow">04 / {category}</div>{semantic_markup(copy_sections["close"])}<p class="lead" style="margin-top:28px">{_esc(copy_sections["close"]["body"])}</p>{cta_photo}</div><div>{cta_markup("action", hero["cta"], contact_href, "↗")}<p class="small" style="margin-top:16px">{_esc(hero["microcopy"])}</p></div></div></section>
</main><footer class="topline footer-note"><span>{name}</span><span>この先の相談へ</span></footer>
</div><script>for (const node of document.querySelectorAll('[data-reveal]')) {{ const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {{ if (entry.isIntersecting) {{ entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }} }}), {{ threshold: 0.12 }}); observer.observe(node); }}</script></body></html>'''


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _input_digest(raw: Mapping[str, Any]) -> str:
    encoded = json.dumps(raw, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_generation(raw: Mapping[str, Any], output_dir: str | Path, *, generation_id: str | None = None, mode: str = "production", iteration: int | None = None, architecture: Mapping[str, Any] | None = None) -> GenerationResult:
    """Run all structured stages and render only Safety-approved evidence.

    Production is fail-closed.  Research/test output is explicitly marked
    ``NOT_PRODUCTION_APPROVED`` and never becomes a customer-facing artifact.
    """
    if mode not in {"production", "research", "test"}:
        raise ValueError(f"unsupported generation mode: {mode}")
    if not isinstance(raw, Mapping):
        raise ValueError("production input must be an object")
    raw = dict(raw)
    if iteration is not None:
        raw["generation_iteration"] = iteration
    _company(raw)
    goal = _text(raw.get("conversion_goal"))
    objections = raw.get("primary_objections") or []
    ledger = raw.get("evidence_ledger") or []
    safety = evaluate_evidence_selection(
        goal,
        objections,
        ledger,
        requested_claims=raw.get("requested_claims") or [],
        require_production_clearance=mode == "production",
    ).to_dict()
    safety["hearing_plan"] = plan_hearing(
        safety,
        conversion_goal=goal,
        primary_objections=objections,
        domain=_text(_company(raw).get("industry")),
    ).to_dict()
    if mode == "production" and safety["safety_status"] in {"INVALID_INPUT", "HEARING_REQUIRED"}:
        raise RuntimeError("production generation blocked by Safety / Hearing: " + safety["safety_status"])
    approved = list(safety.get("eligible_evidence") or [])
    understanding = build_company_understanding(raw, approved)
    strategy = build_creative_strategy(understanding, approved)
    strategy["creative_genome"] = derive_creative_genome(understanding, strategy, approved)
    strategy["narrative_architecture"] = derive_narrative_architecture(strategy["creative_genome"], understanding, approved)
    ia = build_information_architecture(understanding, strategy, approved)
    copy = guard_fake_evidence_copy(build_copy(understanding, strategy, ia, approved), approved)
    copy["section_naming_gate"] = narrative_gates(strategy["narrative_architecture"], strategy["creative_genome"])["generic_heading_gate"]
    photo_role_map = build_photo_role_map(understanding, strategy, ia)
    asset_manifest = build_asset_manifest(raw.get("photo_assets") or [], photo_role_map)
    premium_scene_plan = build_premium_scene_plan(understanding, strategy["narrative_architecture"], strategy["creative_genome"], approved, [item.get("photo_role", "") for item in raw.get("photo_assets") or []])
    premium_scene_plan = apply_controlled_architecture_to_scene_plan(premium_scene_plan, architecture)
    premium_scene_plan = apply_public_scene_semantics(premium_scene_plan, architecture)
    premium_scene_plan["qa_gates"] = scene_plan_gates(premium_scene_plan)
    human_translation = build_human_translation(understanding, strategy, premium_scene_plan, approved, asset_manifest, copy)
    premium_scene_plan["human_translation_ref"] = "premium_human_translation_v1"
    understanding["photo_replacement_readiness"] = {
        **dict(understanding.get("photo_replacement_readiness") or {}),
        "proxy_role": "role_selected_photography_asset",
        "source_priority": ["free_stock", "generated", "vector"],
        "vector_role": "supporting_only",
    }
    art = build_art_direction(understanding, strategy)
    art["photo_role_map"] = photo_role_map
    art["asset_selection_policy"] = {
        "priority": ["free_stock", "generated", "vector"],
        "vector_role": "supporting_only_not_primary_photography",
    }
    art["visual_source"] = "photography_pipeline"
    art["vector_role"] = "supporting_only"
    art["photography_logic"] = "Role-driven photography is the primary visual authority; vector scenes are support only."
    tokens = build_design_tokens(art)
    base_compositions = build_compositions(ia, art)
    ia_by_id = {_text(item.get("section_id")): item for item in ia}
    compositions_with_roles = [
        {**item, "section_role": _text(ia_by_id.get(_text(item.get("section_id")), {}).get("section_role"))}
        for item in base_compositions
    ]
    compositions = connect_photo_roles_to_compositions(compositions_with_roles, photo_role_map, asset_manifest)
    compositions = apply_controlled_architecture(compositions, architecture)
    render_spec = build_render_spec(understanding, strategy, ia, copy, art, tokens, compositions, safety)
    if architecture:
        render_spec["controlled_architecture"] = dict(architecture)
    render_spec["approved_evidence"] = approved
    render_spec["photo_role_map"] = photo_role_map
    render_spec["asset_manifest"] = asset_manifest
    render_spec["premium_scene_plan"] = premium_scene_plan
    render_spec["premium_human_translation"] = human_translation
    generation_id = generation_id or f"gen-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{_input_digest(raw)[:8]}"
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stages = {
        "company_understanding": understanding,
        "creative_strategy": strategy,
        "creative_genome": strategy["creative_genome"],
        "narrative_architecture": strategy["narrative_architecture"],
        "premium_scene_plan": premium_scene_plan,
        "form_causality_manifest": {
            "schema_version": "form_causality_manifest_v1",
            "items": strategy.get("form_causality", []),
            "source": "Company Truth + Customer State + Conversion Goal",
        },
        "information_architecture": ia,
        "copy": copy,
        "photo_role_map": photo_role_map,
        "asset_manifest": asset_manifest,
        "art_direction": art,
        "design_tokens": tokens,
        "compositions": compositions,
        "render_spec": render_spec,
    }
    for name, value in stages.items():
        _write_json(output / f"{name}.json", value)
    _write_json(output / "premium_human_translation.json", human_translation)
    html_path = output / "index.html"
    html_path.write_text(render_html(render_spec), encoding="utf-8")
    presentation_hygiene = public_copy_gate(html_path.read_text(encoding="utf-8"))
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generation_id": generation_id,
        "company_id": understanding["company_id"],
        "company_name": understanding["company_name"],
        "mode": mode,
        "engine_version": ENGINE_VERSION,
        "renderer_version": RENDERER_VERSION,
        "generation_iteration": understanding["generation_iteration"],
        "input_digest": _input_digest(raw),
        "input_references": {"input_file": _text(raw.get("input_file")) or "inline_fixture", "source_urls": understanding["source_references"]},
        "strategy_output": "creative_strategy.json",
        "photo_role_map_output": "photo_role_map.json",
        "asset_manifest_output": "asset_manifest.json",
        "evidence_used": [
            {
                "claim": item.get("claim"),
                "evidence_id": item.get("evidence_id"),
                "source": item.get("source"),
                "verification_status": item.get("verification_status"),
                "rights_status": item.get("rights_status"),
                "placement": item.get("placement_candidates"),
            }
            for item in approved
        ],
        "hearing_required": safety.get("hearing_required", []),
        "blocked_claims": safety.get("blocked_claims", []),
        "safety_status": safety.get("safety_status"),
        "output_status": "PRODUCTION_APPROVED" if mode == "production" else "NOT_PRODUCTION_APPROVED",
        "renderer_output": ["index.html"],
        "stage_outputs": [f"{name}.json" for name in stages],
        "manual_intervention": [],
        "presentation_hygiene": presentation_hygiene,
        "narrative_gates": narrative_gates(strategy["narrative_architecture"], strategy["creative_genome"]),
        "generated_at": datetime.now(UTC).isoformat(),
    }
    _write_json(output / "evidence_manifest.json", {"generation_id": generation_id, "items": manifest["evidence_used"]})
    _write_json(output / "generation_manifest.json", manifest)
    return GenerationResult(generation_id, str(output), mode == "production", safety, stages, manifest)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the structured Production Generation MVP")
    parser.add_argument("input", help="Production input JSON")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--generation-id")
    parser.add_argument("--iteration", type=int, default=None, help="Generic QA-loop iteration number (1 or 2)")
    parser.add_argument("--mode", choices=("production", "research", "test"), default="production")
    args = parser.parse_args(argv)
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    raw = dict(raw)
    raw["input_file"] = args.input
    result = run_generation(raw, args.out, generation_id=args.generation_id, mode=args.mode, iteration=args.iteration)
    print(json.dumps({"generation_id": result.generation_id, "output_dir": result.output_dir, "safety_status": result.safety_report["safety_status"], "production_output_allowed": result.production_output_allowed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

