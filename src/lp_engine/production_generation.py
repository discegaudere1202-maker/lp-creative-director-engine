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
from .hearing import plan_hearing


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


def _slug(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return value or "production-case"


def _esc(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _unique(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(_text(item) for item in values if _text(item)))


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


def _line_shape(text: str, *, max_chars: int = 16) -> list[str]:
    """Create meaning-oriented headline lines, never a one-character tail."""
    value = re.sub(r"\s+", " ", _text(text))
    if len(value) <= max_chars:
        return [value]
    # Prefer complete Japanese meaning units. The ordering matters: a later
    # phrase boundary such as ``なら`` is safer than breaking a lexical unit
    # at an earlier one-character particle.
    separators = ["について", "という", "なら", "から", "まで", "です", "ます", "を", "へ", "で", "の"]
    for separator in separators:
        index = value.find(separator, 3, max_chars + 1)
        if index >= 3 and len(value) - index - len(separator) >= 3:
            cut = index + len(separator)
            return [value[:cut], value[cut:]]
    # Keep semantic chunks roughly balanced; this is only a fallback for
    # generated copy and is validated again by the existing text gates.
    cut = max(4, min(len(value) - 3, len(value) // 2))
    return [value[:cut], value[cut:]]


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


def build_company_understanding(raw: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    company = _company(raw)
    location = _text(company.get("location"))
    category = _text(company.get("service_category")) or _text(company.get("industry"))
    truth = _text(company.get("company_truth"))
    if not truth:
        truth = _first_claim(approved_evidence, "SERVICE_SCOPE", "SCOPE_BOUNDARY", "HERO_REALITY")
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
        "primary_objections": _unique(raw.get("primary_objections") or []),
        "available_evidence": _approved_claims(approved_evidence),
        "unavailable_evidence": _unique(raw.get("unavailable_evidence") or []),
        "hearing_required": list(raw.get("hearing_required") or []),
        "visual_authority": _authority_order(raw, approved_evidence),
        "source_references": _unique([_text(item.get("source")) for item in approved_evidence]),
        "contact_channels": dict(company.get("contact_channels") or {}),
    }


def build_creative_strategy(understanding: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    goal = _text(understanding.get("conversion_goal"))
    goal_phrase, _ = GOAL_LABELS.get(goal, ("次の一歩をつくる", "相談する"))
    truth = _text(understanding.get("company_truth"))
    location = _text(understanding.get("location"))
    category = _text(understanding.get("service_category"))
    differentiators = list(understanding.get("differentiators") or [])
    anchor = differentiators[0] if differentiators else truth
    authority = list(understanding.get("visual_authority") or ["TYPOGRAPHY"])
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
            "after_cta": "確認できる連絡手段だけを表示し、未確認の対応約束を置かない",
        },
        "form_causality": [
            {
                "company_truth": truth,
                "form_decision": f"{authority[0]}を主役にし、{category or 'サービス'}の入口を一枚の流れとして見せる。",
            },
            {
                "company_truth": anchor,
                "form_decision": "Evidenceをカードの壁ではなく、見出し・工程・CTAの同じリズムへ接続する。",
            },
        ],
        "visual_authority_priority": authority,
        "anti_template_notes": [
            "No generic three-card grid as the primary composition.",
            "No unsupported reassurance or invented metrics.",
            "Peak screens are limited; quiet chapters carry orientation.",
        ],
    }


def build_information_architecture(understanding: Mapping[str, Any], strategy: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    goal = _text(understanding.get("conversion_goal"))
    sections: list[dict[str, Any]] = [
        {
            "section_id": "opening",
            "section_role": "hero_orientation",
            "customer_question": "ここは自分の状況を相談できる場所か？",
            "key_message": _text(strategy.get("big_idea")),
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
            "key_message": "状況を伝えるところから、次の案内を考える。",
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
            "key_message": "決めきっていなくても、いまの状況から伝えられる。",
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
            "evidence_used": [item.get("evidence_id") for item in approved_evidence],
            "visual_authority": "TYPOGRAPHY",
            "emotional_intensity": 5,
            "cta_role": "primary_conversion",
            "quiet_or_peak": "peak",
            "mobile_behavior": "sticky_safe_spacing_and_full_width_touch_target",
        },
    ]
    return sections


def build_copy(understanding: Mapping[str, Any], strategy: Mapping[str, Any], ia: Sequence[Mapping[str, Any]], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    company_name = _text(understanding.get("company_name"))
    location = _text(understanding.get("location"))
    category = _text(understanding.get("service_category"))
    goal = _text(understanding.get("conversion_goal"))
    _, cta = GOAL_LABELS.get(goal, ("次の一歩をつくる", "相談する"))
    truth = _text(understanding.get("company_truth"))
    claims = _approved_claims(approved_evidence)
    headline = _text(strategy.get("core_message")) or f"{category}を、{location}から相談する。"
    return {
        "schema_version": SCHEMA_VERSION,
        "hero": {
            "eyebrow": company_name,
            "headline": headline,
            "headline_lines": _line_shape(headline),
            "supporting": f"{location}で{category}を探している方へ。{truth}",
            "cta": cta,
            "microcopy": "連絡手段と所在地を確認できます。",
        },
        "sections": [
            {
                "section_id": item["section_id"],
                "headline": {
                    "opening": headline,
                    "truth": "この場所で、相談の入口をひらく",
                    "way_in": "伝えるところから、次を考える",
                    "contact": "まずは、いまの状況を",
                    "close": "次の一歩は、ここから",
                }.get(item["section_id"], item["key_message"]),
                "body": {
                    "opening": f"{location}の{category}。{truth}",
                    "truth": truth,
                    "way_in": "依頼前に、相談の入口と確認できる連絡手段を整理します。",
                    "contact": "連絡先を選び、確認したい内容を知らせるための入口を用意します。",
                    "close": "相談内容を伝えるための連絡先を、ここで確認できます。",
                }.get(item["section_id"], item["key_message"]),
                "evidence_claims": claims if item["section_id"] in {"truth", "contact"} else [],
                "cta": cta if item["section_id"] == "close" else "",
            }
            for item in ia
        ],
        "global_constraints": {
            "all_customer_facing_claims_require_evidence_id": True,
            "unsupported_reassurance": "blocked",
            "line_shape": "meaning_units_not_character_count",
        },
    }


def build_art_direction(understanding: Mapping[str, Any], strategy: Mapping[str, Any]) -> dict[str, Any]:
    authorities = list(strategy.get("visual_authority_priority") or ["TYPOGRAPHY"])
    primary = authorities[0]
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
    return {
        "schema_version": SCHEMA_VERSION,
        "art_direction_concept": _text(strategy.get("big_idea")),
        "visual_mood": "quiet confidence with a working-surface sense of detail",
        "visual_authority_priority": authorities,
        "color_logic": {"ink": ink, "accent": accent, "paper": paper, "reason": f"{primary} is the first evidence-bearing authority."},
        "typography_logic": "Large meaning-unit headlines, compact labels, readable Japanese body text.",
        "composition_logic": "A narrow reading rail interrupted by one evidence-bearing offset surface; peaks are separated by quiet chapters.",
        "photography_logic": "No client image is required for the sample; use generated SVG/CSS geometry until rights are cleared.",
        "icon_logic": "No generic icon wall; use line markers tied to the process sequence.",
        "texture_logic": "Subtle ruled-paper and calibration marks, never a decorative grain overlay.",
        "motion_logic": "One restrained reveal for section entry; no infinite or blocking animation.",
        "forbidden_patterns": ["rounded card wall", "generic three-column grid", "unsupported trust badge", "stock person", "marquee", "parallax"],
        "craft_catch": "A calibration line carries the customer from the current situation to the next contact point.",
    }


def build_design_tokens(art_direction: Mapping[str, Any]) -> dict[str, Any]:
    color = dict(art_direction.get("color_logic") or {})
    return {
        "schema_version": SCHEMA_VERSION,
        "colors": {"ink": color.get("ink", "#151515"), "accent": color.get("accent", "#ba5e35"), "paper": color.get("paper", "#f3efe7"), "muted": "#77736b", "line": "rgba(21,21,21,.18)"},
        "typography": {"display": "ui-sans-serif, system-ui, -apple-system, 'Hiragino Sans', sans-serif", "body": "ui-sans-serif, system-ui, -apple-system, 'Hiragino Sans', sans-serif", "display_weight": 800, "body_weight": 450},
        "font_scale": {"eyebrow": "0.72rem", "body": "1rem", "lead": "1.18rem", "h2": "clamp(2rem, 5vw, 5rem)", "hero": "clamp(3rem, 10vw, 9rem)"},
        "spacing": {"unit": "8px", "section": "clamp(5rem, 12vw, 12rem)", "rail": "min(90vw, 1180px)", "text": "min(90vw, 720px)"},
        "radius": {"surface": "2px", "button": "999px"},
        "borders": {"hairline": "1px solid var(--line)", "strong": "1px solid var(--ink)"},
        "shadows": {"surface": "10px 18px 0 rgba(21,21,21,.08)"},
        "container_widths": {"rail": "min(90vw, 1180px)", "text": "min(90vw, 720px)"},
        "rhythm": {"peak_to_quiet": "1.5", "quiet_to_peak": "1.15"},
        "motion": {"duration_ms": 520, "easing": "cubic-bezier(.2,.7,.2,1)"},
    }


def build_compositions(ia: Sequence[Mapping[str, Any]], art_direction: Mapping[str, Any]) -> list[dict[str, Any]]:
    compositions: list[dict[str, Any]] = []
    for index, section in enumerate(ia):
        role = _text(section.get("section_role"))
        if role == "hero_orientation":
            layout, alignment, emphasis = "split_rail", "left", "headline"
        elif role == "company_truth":
            layout, alignment, emphasis = "offset_evidence_surface", "left", "evidence"
        elif role == "service_process":
            layout, alignment, emphasis = "sequence_rail", "left", "rhythm"
        elif role == "next_step":
            layout, alignment, emphasis = "contact_strip", "left", "channel"
        else:
            layout, alignment, emphasis = "closing_field", "left", "action"
        compositions.append({
            "section_id": section["section_id"],
            "layout_type": layout,
            "column_logic": "12-column reading rail; one dominant field and one supporting field.",
            "alignment": alignment,
            "image_role": "generated_abstract_geometry",
            "text_width": "min(90vw, 720px)",
            "whitespace": "large" if section.get("quiet_or_peak") == "peak" else "medium",
            "emphasis": emphasis,
            "mobile_transformation": section.get("mobile_behavior"),
            "screenshot_peak": section.get("quiet_or_peak") == "peak",
            "order": index,
        })
    return compositions


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
    return f"""
    :root {{ --ink:{colors['ink']}; --accent:{colors['accent']}; --paper:{colors['paper']}; --muted:{colors['muted']}; --line:{colors['line']}; --rail:{spacing['rail']}; --text:{spacing['text']}; --ease:{tokens['motion']['easing']}; }}
    * {{ box-sizing:border-box; }} html {{ scroll-behavior:smooth; }} body {{ margin:0; background:var(--paper); color:var(--ink); font-family:{typo['body']}; font-weight:{typo['body_weight']}; line-height:1.75; }}
    a {{ color:inherit; }} .site-shell {{ overflow:hidden; }} .topline {{ width:var(--rail); margin:auto; padding:24px 0; display:flex; justify-content:space-between; gap:24px; border-bottom:1px solid var(--line); font-size:{scale['eyebrow']}; letter-spacing:.12em; text-transform:uppercase; }}
    .section {{ width:var(--rail); margin:auto; padding:var(--section, {spacing['section']}) 0; position:relative; }} .section--quiet {{ padding-top:clamp(4rem,8vw,8rem); padding-bottom:clamp(4rem,8vw,8rem); }} .section--peak {{ min-height:min(92vh, 860px); display:grid; align-content:center; }}
    .hero-grid {{ display:grid; grid-template-columns:minmax(0, 1.25fr) minmax(180px, .75fr); gap:clamp(2rem, 8vw, 9rem); align-items:end; }} .eyebrow {{ color:var(--accent); font-size:{scale['eyebrow']}; letter-spacing:.12em; text-transform:uppercase; }} h1,h2,p {{ margin:0; }} h1 {{ max-width:11ch; font-size:{scale['hero']}; line-height:.95; letter-spacing:-.07em; }} h2 {{ max-width:12ch; font-size:{scale['h2']}; line-height:1; letter-spacing:-.06em; }} .lead {{ max-width:34rem; font-size:{scale['lead']}; }} .small {{ color:var(--muted); font-size:.82rem; }} .section-header {{ display:flex; justify-content:space-between; gap:2rem; align-items:flex-end; border-top:1px solid var(--line); padding-top:18px; margin-bottom:clamp(2rem,5vw,5rem); }}
    .hero-mark {{ aspect-ratio:1; border:1px solid var(--ink); position:relative; background:linear-gradient(135deg, transparent 48%, var(--accent) 49%, var(--accent) 51%, transparent 52%), repeating-linear-gradient(0deg, transparent 0 19px, var(--line) 20px); }} .hero-mark::before,.hero-mark::after {{ content:""; position:absolute; border:1px solid var(--ink); border-radius:50%; width:28%; aspect-ratio:1; left:14%; top:18%; }} .hero-mark::after {{ left:auto; top:auto; right:14%; bottom:18%; }}
    .proof-surface {{ display:grid; grid-template-columns:.9fr 1.1fr; gap:clamp(2rem,8vw,8rem); padding:clamp(2rem,5vw,5rem); background:var(--ink); color:var(--paper); box-shadow:10px 18px 0 var(--accent); }} .proof-surface .eyebrow {{ color:var(--accent); }} .claim-list {{ display:grid; gap:0; border-top:1px solid rgba(243,239,231,.3); }} .claim {{ padding:18px 0; border-bottom:1px solid rgba(243,239,231,.3); }} .claim-id {{ display:block; color:var(--accent); font-size:.72rem; letter-spacing:.1em; }}
    .sequence {{ display:grid; grid-template-columns:repeat(3,1fr); border-top:1px solid var(--line); }} .step {{ min-height:220px; padding:18px 22px 24px 0; border-bottom:1px solid var(--line); border-right:1px solid var(--line); }} .step:last-child {{ border-right:0; padding-left:22px; }} .step + .step {{ padding-left:22px; }} .step-number {{ font-size:3rem; line-height:1; color:var(--accent); }}
    .contact-strip {{ display:grid; grid-template-columns:1fr auto; gap:2rem; align-items:center; border-top:1px solid var(--ink); border-bottom:1px solid var(--ink); padding:28px 0; }} .contact-lines {{ display:grid; gap:4px; }} .button {{ display:inline-flex; align-items:center; justify-content:center; min-height:52px; padding:12px 26px; border-radius:999px; background:var(--accent); color:var(--paper); text-decoration:none; font-weight:700; }} .button:hover {{ background:var(--ink); }} .footer-note {{ padding:24px 0 48px; font-size:.76rem; color:var(--muted); border-top:1px solid var(--line); }} .calibration {{ position:absolute; right:0; top:18%; width:18vw; max-width:220px; height:1px; background:var(--accent); }} .calibration::after {{ content:""; position:absolute; right:0; top:-4px; width:9px; height:9px; border-radius:50%; background:var(--accent); }}
    [data-reveal] {{ opacity:0; transform:translateY(18px); transition:opacity 520ms var(--ease), transform 520ms var(--ease); }} [data-reveal].is-visible {{ opacity:1; transform:none; }} @media (prefers-reduced-motion:reduce) {{ html {{ scroll-behavior:auto; }} [data-reveal] {{ opacity:1; transform:none; transition:none; }} }}
    @media (max-width:760px) {{ .topline {{ padding:18px 0; }} .hero-grid,.proof-surface,.contact-strip {{ grid-template-columns:1fr; }} .section {{ padding:clamp(4rem,16vw,7rem) 0; }} .section--peak {{ min-height:auto; }} h1 {{ max-width:9ch; }} .hero-mark {{ width:min(72vw,320px); margin-left:auto; }} .proof-surface {{ box-shadow:7px 10px 0 var(--accent); padding:24px; }} .sequence {{ grid-template-columns:1fr; }} .step,.step + .step,.step:last-child {{ min-height:0; padding:20px 0; border-right:0; }} .contact-strip .button {{ width:100%; }} .calibration {{ width:35vw; top:8%; }} }}
    """


def render_html(spec: Mapping[str, Any]) -> str:
    company = spec["company"]
    copy = spec["copy"]
    tokens = spec["design_tokens"]
    art = spec["art_direction"]
    sections = {item["section_id"]: item for item in spec["ia"]}
    copy_sections = {item["section_id"]: item for item in copy["sections"]}
    evidence = spec.get("approved_evidence", [])
    hero = copy["hero"]
    contact_claims = [item for item in evidence if item.get("evidence_type") in {"CTA_CHANNEL", "POST_CLICK_FLOW", "ACCOUNTABILITY_SCOPE"}]
    service_claims = [item for item in evidence if item.get("evidence_type") in {"SERVICE_SCOPE", "SERVICE_PROCESS", "CRAFT_ACTION"}]
    claims_markup = "".join(
        f'<div class="claim"><span class="claim-id">{_esc(item.get("evidence_id"))}</span>{_esc(item.get("claim"))}</div>'
        for item in (service_claims or evidence[:2])
    )
    contact_markup = "".join(f'<div>{_esc(item.get("claim"))}</div>' for item in contact_claims)
    steps = ["状況を伝える", "対応できることを確認する", "次の案内を考える"]
    steps_markup = "".join(f'<div class="step"><div class="step-number">0{idx}</div><p>{_esc(label)}</p></div>' for idx, label in enumerate(steps, 1))
    lines_markup = "<br>".join(_esc(line) for line in hero["headline_lines"])
    location = _esc(company.get("location"))
    category = _esc(company.get("service_category"))
    name = _esc(company.get("company_name"))
    cta = _esc(hero["cta"])
    contact = dict(company.get("contact_channels") or {})
    contact_href = _esc(contact.get("href") or "#contact")
    return f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><title>{name}｜{_esc(hero["headline"])}</title><style>{_render_styles(tokens)}</style></head>
<body><div class="site-shell">
<header class="topline"><span>{name}</span><span>{location}</span></header>
<main>
<section class="section section--peak" data-reveal data-role="hero_orientation"><div class="calibration"></div><div class="hero-grid"><div><div class="eyebrow">{_esc(hero["eyebrow"])}</div><h1>{lines_markup}</h1><p class="lead" style="margin-top:28px">{_esc(hero["supporting"])}</p><a class="button" href="#contact" style="margin-top:34px">{cta}<span aria-hidden="true" style="margin-left:14px">→</span></a><p class="small" style="margin-top:16px">{_esc(hero["microcopy"])}</p></div><div class="hero-mark" aria-hidden="true"></div></div></section>
<section class="section section--peak" data-reveal data-role="company_truth"><div class="section-header"><span class="eyebrow">01 / 会社の輪郭</span><span class="small">{location}</span></div><div class="proof-surface"><div><h2>{_esc(copy_sections["truth"]["headline"])}</h2></div><div><p class="lead">{_esc(copy_sections["truth"]["body"])}</p><div class="claim-list" style="margin-top:34px">{claims_markup}</div></div></div></section>
<section class="section section--quiet" data-reveal data-role="service_process"><div class="section-header"><span class="eyebrow">02 / 入口のリズム</span><span class="small">相談の前に、入口を確認する</span></div><div class="hero-grid"><div><h2>{_esc(copy_sections["way_in"]["headline"])}</h2></div><div><p class="lead">{_esc(copy_sections["way_in"]["body"])}</p></div></div><div class="sequence" style="margin-top:64px">{steps_markup}</div></section>
<section class="section section--quiet" id="contact" data-reveal data-role="next_step"><div class="section-header"><span class="eyebrow">03 / 次の案内</span><span class="small">{location}</span></div><div class="contact-strip"><div><h2>{_esc(copy_sections["contact"]["headline"])}</h2><p class="lead" style="margin-top:24px">{_esc(copy_sections["contact"]["body"])}</p><div class="contact-lines" style="margin-top:28px">{contact_markup}</div></div><div><a class="button" href="{contact_href}">{cta}<span aria-hidden="true" style="margin-left:14px">↗</span></a></div></div></section>
<section class="section section--peak" data-reveal data-role="cta_zone"><div class="hero-grid"><div><div class="eyebrow">04 / {category}</div><h2>{_esc(copy_sections["close"]["headline"])}</h2><p class="lead" style="margin-top:28px">{_esc(copy_sections["close"]["body"])}</p></div><div><a class="button" href="{contact_href}">{cta}<span aria-hidden="true" style="margin-left:14px">↗</span></a><p class="small" style="margin-top:16px">{_esc(hero["microcopy"])}</p></div></div></section>
</main><footer class="topline footer-note"><span>{name}</span><span>事実確認済みの内容のみで構成</span></footer>
</div><script>for (const node of document.querySelectorAll('[data-reveal]')) {{ const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {{ if (entry.isIntersecting) {{ entry.target.classList.add('is-visible'); observer.unobserve(entry.target); }} }}), {{ threshold: 0.12 }}); observer.observe(node); }}</script></body></html>'''


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _input_digest(raw: Mapping[str, Any]) -> str:
    encoded = json.dumps(raw, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_generation(raw: Mapping[str, Any], output_dir: str | Path, *, generation_id: str | None = None, mode: str = "production") -> GenerationResult:
    """Run all structured stages and render only Safety-approved evidence.

    Production is fail-closed.  Research/test output is explicitly marked
    ``NOT_PRODUCTION_APPROVED`` and never becomes a customer-facing artifact.
    """
    if mode not in {"production", "research", "test"}:
        raise ValueError(f"unsupported generation mode: {mode}")
    if not isinstance(raw, Mapping):
        raise ValueError("production input must be an object")
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
    ia = build_information_architecture(understanding, strategy, approved)
    copy = build_copy(understanding, strategy, ia, approved)
    art = build_art_direction(understanding, strategy)
    tokens = build_design_tokens(art)
    compositions = build_compositions(ia, art)
    render_spec = build_render_spec(understanding, strategy, ia, copy, art, tokens, compositions, safety)
    render_spec["approved_evidence"] = approved
    generation_id = generation_id or f"gen-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{_input_digest(raw)[:8]}"
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    stages = {
        "company_understanding": understanding,
        "creative_strategy": strategy,
        "information_architecture": ia,
        "copy": copy,
        "art_direction": art,
        "design_tokens": tokens,
        "compositions": compositions,
        "render_spec": render_spec,
    }
    for name, value in stages.items():
        _write_json(output / f"{name}.json", value)
    html_path = output / "index.html"
    html_path.write_text(render_html(render_spec), encoding="utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "generation_id": generation_id,
        "company_id": understanding["company_id"],
        "company_name": understanding["company_name"],
        "mode": mode,
        "engine_version": ENGINE_VERSION,
        "renderer_version": RENDERER_VERSION,
        "input_digest": _input_digest(raw),
        "input_references": {"input_file": _text(raw.get("input_file")) or "inline_fixture", "source_urls": understanding["source_references"]},
        "strategy_output": "creative_strategy.json",
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
    parser.add_argument("--mode", choices=("production", "research", "test"), default="production")
    args = parser.parse_args(argv)
    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    raw = dict(raw)
    raw["input_file"] = args.input
    result = run_generation(raw, args.out, generation_id=args.generation_id, mode=args.mode)
    print(json.dumps({"generation_id": result.generation_id, "output_dir": result.output_dir, "safety_status": result.safety_report["safety_status"], "production_output_allowed": result.production_output_allowed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
