"""Premium authored-surface layer for the current-industry Production path.

Issue #116 implements PU1-PU8 after CompositionPlan is frozen.  This module
never selects Creative Family, never changes scene order/topology, and never
promotes illustrative media into company evidence.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
from typing import Any, Mapping, Sequence

from .authored_composition_contract import plan_digest
from .visual_asset_library import asset_binding_css, render_asset_binding

MOBILE_WIDTHS = (320, 360, 375, 390, 430)
INTERNAL_INTENT_TOKENS = {"recognize", "choose", "understand", "trust", "compare", "prepare", "act"}
BANNED_VALIDATION_COPY = (
    "CompositionPlanの意図から、確認すべき情報を順に案内します。",
    "決めるための情報を整理します。",
)

CATEGORY_LABELS = {
    "beauty_cosmetics": "SKINCARE / BEAUTY",
    "hair_salon_barber": "HAIR / GROOMING",
    "pilates_fitness": "PILATES / MOVEMENT",
}

HERO_HEADLINES = {
    "choose": ("違いが見えると、", "選びやすくなる。"),
    "understand": ("はじめる前に、", "流れをわかりやすく。"),
    "trust": ("任せる前に、", "安心できる理由を。"),
    "compare": ("比べるほど、", "自分の基準が見えてくる。"),
    "prepare": ("迷いを減らして、", "気持ちよくはじめる。"),
    "act": ("考えすぎる前に、", "次の一歩を軽く。"),
}

SCENE_HEADLINES = {
    "recognize": "まず、選ぶ基準を整える",
    "choose": "選択肢を、違いで見る",
    "understand": "体験の流れを、順番に",
    "trust": "安心につながる情報を、近くに",
    "compare": "比べるポイントを、ひと目で",
    "prepare": "はじめる前の不安を、小さくする",
    "act": "次の一歩は、ここから",
}

SCENE_SUPPORT = {
    "recognize": "気になることを先にほどき、必要な情報へ迷わず進める入口をつくります。",
    "choose": "選択肢を並べるだけでなく、違いが伝わる順番で見比べられるようにしています。",
    "understand": "体験の前後を想像しやすいよう、流れと確認ポイントを近くにまとめています。",
    "trust": "判断を急がせず、確認できる情報と、まだ確認できていないことを分けて伝えます。",
    "compare": "同じ目線で見比べられるよう、迷いやすいポイントを整理して並べます。",
    "prepare": "はじめる前に気になりやすいことを、行動の直前で確かめられるようにします。",
    "act": "ここまで確認した内容を踏まえて、無理のない次の行動へつなげます。",
}


class PremiumAuthorshipError(RuntimeError):
    """Raised when the premium authored surface cannot be produced honestly."""


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


def _usable_facts(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    facts = plan.get("input", {}).get("evidence", {}).get("facts", [])
    return [
        deepcopy(dict(fact))
        for fact in facts
        if fact.get("usable_for_persuasion") is True and fact.get("confidence") == "verified"
    ]


def _question_labels(questions: Sequence[Any]) -> list[str]:
    mapping = {
        "price": "料金",
        "process": "流れ",
        "duration": "所要時間",
        "access": "アクセス",
        "difference": "違い",
        "fit": "自分に合うか",
    }
    labels = []
    for question in questions:
        token = _text(question)
        if token in mapping:
            labels.append(mapping[token])
    return labels


def build_public_copy(plan: Mapping[str, Any]) -> dict[str, Any]:
    """PU1: transform frozen planning semantics into customer-facing copy."""
    inp = plan["input"]
    decision = inp["customer_decision_state"]
    company = inp["company_truth"]
    job = _text(decision["primary_job"])
    if job not in HERO_HEADLINES:
        raise PremiumAuthorshipError("PUBLIC_COPY_UNSUPPORTED_DECISION_JOB")

    company_name = _text(_truth_value(company.get("name")))
    if not company_name:
        raise PremiumAuthorshipError("PUBLIC_COPY_COMPANY_NAME_MISSING")

    category = _text(_truth_value(company.get("category")))
    eyebrow = CATEGORY_LABELS.get(category, "SERVICE / GUIDE")
    offers = list(company.get("offers") or [])
    question_labels = _question_labels(decision.get("questions") or [])
    if question_labels:
        hero_support = "・".join(question_labels[:3]) + "など、選ぶ前に知りたいことから確認できます。"
    elif len(offers) > 1:
        hero_support = "複数の選択肢を、違いがわかる順番で確認できます。"
    else:
        hero_support = "気になることを先に確かめてから、次の一歩を選べます。"

    hero_units = list(HERO_HEADLINES[job])
    scenes: dict[str, Any] = {}
    usable = {fact["id"]: fact for fact in _usable_facts(plan)}
    for scene in plan.get("scene_intents", []):
        scene_id = _text(scene.get("id"))
        intent = _text(scene.get("intent"))
        required = [fact_id for fact_id in scene.get("required_facts", []) if fact_id in usable]
        proof_rows = [
            {
                "fact_id": fact_id,
                "copy": usable[fact_id]["claim"],
                "sources": deepcopy(usable[fact_id].get("sources") or []),
            }
            for fact_id in required
        ]
        scenes[scene_id] = {
            "scene_id": scene_id,
            "headline": SCENE_HEADLINES.get(intent, "必要な情報を、わかりやすく"),
            "support_copy": SCENE_SUPPORT.get(intent, "必要な情報を、判断しやすい順番でまとめています。"),
            "proof_copy": proof_rows,
            "evidence_refs": required,
            "source_intent": intent,
        }

    trace = {
        "inputs": {
            "company_truth_name": company.get("name"),
            "company_truth_category": company.get("category"),
            "decision_job": job,
            "questions": list(decision.get("questions") or []),
            "offer_ids": [_text(row.get("id")) for row in offers],
            "verified_fact_ids": sorted(usable),
        },
        "factual_claims": [
            {"fact_id": row["fact_id"], "copy": row["copy"], "sources": row["sources"]}
            for scene in scenes.values()
            for row in scene["proof_copy"]
        ],
        "validation_copy_removed": True,
        "internal_intent_tokens_are_private": True,
    }
    result = {
        "company_name": company_name,
        "eyebrow": eyebrow,
        "hero_headline_units": hero_units,
        "hero_support": hero_support,
        "scenes": scenes,
        "trace": trace,
    }
    visible = " ".join(
        hero_units
        + [hero_support]
        + [row["headline"] for row in scenes.values()]
        + [row["support_copy"] for row in scenes.values()]
    )
    if any(phrase in visible for phrase in BANNED_VALIDATION_COPY):
        raise PremiumAuthorshipError("BANNED_VALIDATION_COPY_VISIBLE")
    if any(token == text.strip().lower() for text in [row["headline"] for row in scenes.values()] for token in INTERNAL_INTENT_TOKENS):
        raise PremiumAuthorshipError("INTERNAL_INTENT_TOKEN_VISIBLE")
    return result


def compose_hero_authority(plan: Mapping[str, Any], public_copy: Mapping[str, Any]) -> dict[str, Any]:
    """PU2: derive Hero authority without Family->Hero lookup."""
    decision = plan["input"]["customer_decision_state"]
    offers = plan["input"]["company_truth"]["offers"]
    proof_count = len(_usable_facts(plan))
    job = _text(decision["primary_job"])
    risk = _text(decision["risk_sensitivity"])

    if proof_count and risk == "high":
        variant = "proof_led"
        geometry = "anchored_portrait"
    elif len(offers) >= 3:
        variant = "choice_led"
        geometry = "wide_editorial"
    elif job in {"trust", "understand"}:
        variant = "quiet_authority"
        geometry = "calm_frame"
    elif job == "act":
        variant = "action_led"
        geometry = "immersive_panel"
    else:
        variant = "editorial_split"
        geometry = "split_frame"

    return {
        "hero_composition_intent": variant,
        "authority_statement": "".join(public_copy["hero_headline_units"]),
        "media_geometry": geometry,
        "proof_or_context_adjacency": "verified_proof" if proof_count else "illustrative_context",
        "selection_trace": {
            "family_frozen": bool(plan.get("family_frozen")),
            "family_id": plan.get("family_id"),
            "decision_job": job,
            "risk_sensitivity": risk,
            "offer_count": len(offers),
            "verified_proof_count": proof_count,
            "company_identity_used": False,
            "category_template_lookup_used": False,
        },
    }


def plan_scene_dramaturgy(plan: Mapping[str, Any]) -> dict[str, Any]:
    """PU3: author density, width and media/text relationships per scene."""
    scenes = list(plan.get("scene_intents") or [])
    offers = plan["input"]["company_truth"]["offers"]
    proof_count = len(_usable_facts(plan))
    rows: dict[str, Any] = {}
    for index, scene in enumerate(scenes):
        scene_id = _text(scene["id"])
        intent = _text(scene["intent"])
        if intent == "recognize":
            weight = "dominant"
            width = "wide"
            relationship = "media_anchor"
            transition = "open_field"
        elif intent == "trust":
            weight = "proof"
            width = "contained"
            relationship = "proof_adjacent"
            transition = "soft_rule"
        elif intent in {"choose", "compare"}:
            weight = "decision"
            width = "wide"
            relationship = "split_compare"
            transition = "numbered_chapter"
        elif intent == "act":
            weight = "closing"
            width = "contained"
            relationship = "text_action"
            transition = "deep_space"
        else:
            weight = "support"
            width = "contained"
            relationship = "media_support"
            transition = "numbered_chapter"

        if intent in {"choose", "compare"} and len(offers) >= 3:
            density = "structured_dense"
        elif intent == "trust" and proof_count:
            density = "proof_dense"
        elif index % 2:
            density = "compact"
        else:
            density = "open"

        rows[scene_id] = {
            "scene_weight": weight,
            "density_mode": density,
            "canvas_width_mode": width,
            "media_text_relationship": relationship,
            "chapter_transition": transition,
            "proof_adjacency": bool(scene.get("required_facts")),
            "mobile_recomposition": {
                "media_priority": "first" if intent in {"recognize", "trust"} else "after_copy",
                "proof_proximity": "immediate" if intent == "trust" else "contextual",
                "chapter_pacing": "compact" if intent == "act" else "breathing",
            },
            "index": index,
        }

    signatures = {
        (row["scene_weight"], row["density_mode"], row["canvas_width_mode"], row["media_text_relationship"])
        for row in rows.values()
    }
    if len(rows) > 1 and len(signatures) < 2:
        raise PremiumAuthorshipError("SCENE_DRAMATURGY_UNIFORM_STACK")
    return {
        "scenes": rows,
        "same_family_divergence_inputs": {
            "decision_job": plan["input"]["customer_decision_state"]["primary_job"],
            "offer_count": len(offers),
            "scene_count": len(scenes),
            "verified_proof_count": proof_count,
        },
    }


def bind_media_story(
    plan: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
    dramaturgy: Mapping[str, Any],
) -> dict[str, Any]:
    """PU4: connect rights-safe media to narrative function, never fake proof."""
    rows: dict[str, Any] = {}
    scene_map = {row["id"]: row for row in plan.get("scene_intents", [])}
    for key, binding in asset_bindings.items():
        scene_id = _text(binding.get("scene_id"))
        scene = scene_map.get(scene_id, {"id": scene_id, "intent": "recognize", "required_facts": []})
        illustrative = _text(binding.get("evidence_status")) == "GENERIC_ILLUSTRATIVE_STOCK"
        intent = _text(scene.get("intent"))
        story_function = {
            "recognize": "authority_context",
            "choose": "choice_context",
            "understand": "process_context",
            "trust": "trust_context",
            "compare": "comparison_context",
            "prepare": "preparation_context",
            "act": "closing_context",
        }.get(intent, "context")
        rows[key] = {
            "asset_id": binding.get("asset_id"),
            "scene_id": scene_id,
            "story_function": story_function,
            "claim_adjacency": [] if illustrative else list(scene.get("required_facts") or []),
            "crop_intent": "subject_safe_cover",
            "caption_mode": "illustrative_explicit" if illustrative else "evidence_caption",
            "sequence_role": "hero_authority" if key == "hero" else f"chapter_{dramaturgy['scenes'].get(scene_id, {}).get('index', 0) + 1}",
            "mobile_priority": dramaturgy["scenes"].get(scene_id, {}).get("mobile_recomposition", {}).get("media_priority", "after_copy"),
            "evidence_status": binding.get("evidence_status"),
            "binary_sha256": binding.get("binary_sha256"),
            "rights_gate": binding.get("rights_gate"),
            "generic_stock_promoted_to_evidence": False,
        }
    return {"bindings": rows, "illustrative_boundary_preserved": all(not row["generic_stock_promoted_to_evidence"] for row in rows.values())}


def choreograph_proof_cta(plan: Mapping[str, Any], public_copy: Mapping[str, Any]) -> dict[str, Any]:
    """PU5: stage verified proof and only render a positive CTA with a verified destination."""
    decision = plan["input"]["customer_decision_state"]
    contact = plan["input"]["company_truth"].get("contact")
    destination = None
    contact_verified = isinstance(contact, Mapping) and contact.get("confidence") == "verified"
    if contact_verified:
        value = _truth_value(contact)
        if isinstance(value, Mapping):
            destination = _text(value.get("destination"))

    usable = _usable_facts(plan)
    proof_rows = [
        {
            "fact_id": fact["id"],
            "claim": fact["claim"],
            "sources": deepcopy(fact.get("sources") or []),
            "placement": "objection_adjacent",
        }
        for fact in usable
    ]
    job = _text(decision["primary_job"])
    label = {
        "trust": "安心して相談する",
        "choose": "相談して選び方を確認する",
        "compare": "違いを相談して確認する",
        "prepare": "はじめる前に相談する",
        "act": "次の一歩を相談する",
    }.get(job, "相談する")

    actionable = bool(destination and (destination.startswith("https://") or destination.startswith("http://") or destination.startswith("mailto:") or destination.startswith("tel:")))
    return {
        "proof": {
            "state": "VERIFIED_PROOF_AVAILABLE" if proof_rows else "CLIENT_EVIDENCE_DEPENDENT",
            "objection_to_proof_map": proof_rows,
            "no_fabricated_proof": True,
        },
        "cta": {
            "state": "ACTIONABLE_VERIFIED_DESTINATION" if actionable else "NON_ACTION_NO_VERIFIED_DESTINATION",
            "verified_destination": destination if actionable else None,
            "primary_label": label if actionable else "お問い合わせ方法は確認中です",
            "secondary_label": "内容をもう一度見る",
            "secondary_destination": "#details",
            "pre_cta_reassurance": "確認できていない実績や条件を、事実のようには掲載しません。",
            "reentry_scene_ids": [
                scene_id
                for scene_id in public_copy["scenes"]
                if scene_id in {"choose", "trust", "compare"}
            ][:2],
            "actionable": actionable,
        },
    }


def derive_visual_voice(plan: Mapping[str, Any], dramaturgy: Mapping[str, Any]) -> dict[str, Any]:
    """PU6: derive visible primitives from semantic inputs, not identity/category templates."""
    decision = plan["input"]["customer_decision_state"]
    offers = plan["input"]["company_truth"]["offers"]
    job = _text(decision["primary_job"])
    risk = _text(decision["risk_sensitivity"])
    scene_count = len(plan.get("scene_intents") or [])

    if risk == "high":
        energy = "calm"
    elif len(offers) >= 3:
        energy = "structured"
    elif job == "act":
        energy = "forward"
    else:
        energy = "editorial"

    primitives = {
        "calm": {
            "type_relationship": "serif_display_sans_body",
            "measure": "34rem",
            "spacing_cadence": "long_breath",
            "rule_treatment": "hairline",
            "image_geometry": "soft_portrait",
            "surface_depth": "tonal_layer",
            "accent": "#5f6f69",
        },
        "structured": {
            "type_relationship": "compact_sans_display",
            "measure": "38rem",
            "spacing_cadence": "modular",
            "rule_treatment": "indexed",
            "image_geometry": "wide_crop",
            "surface_depth": "card_plane",
            "accent": "#544e46",
        },
        "forward": {
            "type_relationship": "large_sans_display",
            "measure": "32rem",
            "spacing_cadence": "compressed_then_open",
            "rule_treatment": "bold_rule",
            "image_geometry": "immersive",
            "surface_depth": "contrast_panel",
            "accent": "#3d4c46",
        },
        "editorial": {
            "type_relationship": "serif_display_sans_body",
            "measure": "36rem",
            "spacing_cadence": "editorial",
            "rule_treatment": "quiet_rule",
            "image_geometry": "editorial_split",
            "surface_depth": "paper_layer",
            "accent": "#665b50",
        },
    }[energy]
    result = deepcopy(primitives)
    result.update({
        "voice_mode": energy,
        "trace": {
            "family_id": plan.get("family_id"),
            "family_frozen": plan.get("family_frozen"),
            "decision_job": job,
            "risk_sensitivity": risk,
            "offer_count": len(offers),
            "scene_count": scene_count,
            "scene_density_signature": [row["density_mode"] for row in dramaturgy["scenes"].values()],
            "company_identity_used": False,
            "category_direct_template_lookup_used": False,
        },
    })
    return result


def plan_motion(plan: Mapping[str, Any], dramaturgy: Mapping[str, Any]) -> dict[str, Any]:
    """PU7: purposeful hierarchy/sequence motion with reduced-motion fallback."""
    items = [
        {
            "id": "hero-reveal",
            "purpose": "hierarchy",
            "trigger": "initial_render",
            "affected_element": ".premium-hero__copy,.premium-hero__media",
            "reduced_motion_fallback": "visible_without_transform_or_animation",
        }
    ]
    for scene_id, row in dramaturgy["scenes"].items():
        if scene_id == "recognize":
            continue
        items.append({
            "id": f"{scene_id}-reveal",
            "purpose": "sequence",
            "trigger": "initial_render",
            "affected_element": f'[data-premium-scene="{scene_id}"]',
            "reduced_motion_fallback": "visible_without_transform_or_animation",
            "chapter_index": row["index"],
        })
    return {
        "motion_optional": False,
        "intents": items,
        "random_motion_uniqueness": False,
        "reduced_motion_css_required": True,
    }


def plan_mobile_recomposition(
    plan: Mapping[str, Any],
    dramaturgy: Mapping[str, Any],
    proof_cta: Mapping[str, Any],
) -> dict[str, Any]:
    """PU8: explicit authored mobile behavior for every narrow validation width."""
    decision = plan["input"]["customer_decision_state"]
    job = _text(decision["primary_job"])
    risk = _text(decision["risk_sensitivity"])
    hero_media_first = risk == "high" or job in {"trust", "understand"}
    width_rows = {}
    for width in MOBILE_WIDTHS:
        width_rows[str(width)] = {
            "hero_media_order": "first" if hero_media_first else "after_copy",
            "media_priority": "scene_authored",
            "proof_proximity": "immediate" if risk == "high" else "contextual",
            "cta_mode": "full_width_inline" if proof_cta["cta"]["actionable"] else "transparent_non_action",
            "text_measure": "29ch" if width <= 360 else "32ch",
            "chapter_pacing": "compressed" if width <= 360 else "breathing",
        }
    return {
        "widths": width_rows,
        "hero_media_first": hero_media_first,
        "scene_mobile_directives": {
            scene_id: deepcopy(row["mobile_recomposition"])
            for scene_id, row in dramaturgy["scenes"].items()
        },
        "desktop_dom_stack_only": False,
    }


def build_premium_uplift(
    plan: Mapping[str, Any],
    directives: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Build PU1-PU8 without mutating the frozen CompositionPlan."""
    before_digest = plan_digest(plan)
    original_topology = deepcopy(plan.get("topology"))
    original_scenes = deepcopy(plan.get("scene_intents"))

    public_copy = build_public_copy(plan)
    hero = compose_hero_authority(plan, public_copy)
    dramaturgy = plan_scene_dramaturgy(plan)
    media_story = bind_media_story(plan, asset_bindings, dramaturgy)
    proof_cta = choreograph_proof_cta(plan, public_copy)
    visual_voice = derive_visual_voice(plan, dramaturgy)
    motion = plan_motion(plan, dramaturgy)
    mobile = plan_mobile_recomposition(plan, dramaturgy, proof_cta)

    if plan_digest(plan) != before_digest or plan.get("topology") != original_topology or plan.get("scene_intents") != original_scenes:
        raise PremiumAuthorshipError("PREMIUM_LAYER_MUTATED_COMPOSITION_PLAN")

    return {
        "schema_version": "issue116_premium_authorship_v1",
        "composition_plan_digest": before_digest,
        "family_id": plan.get("family_id"),
        "family_frozen": plan.get("family_frozen") is True,
        "topology_preserved": True,
        "scene_order_preserved": True,
        "review_gate_preserved": deepcopy(plan.get("review_gate")),
        "PU1_public_copy": public_copy,
        "PU2_hero_authority": hero,
        "PU3_scene_dramaturgy": dramaturgy,
        "PU4_media_story": media_story,
        "PU5_proof_cta": proof_cta,
        "PU6_visual_voice": visual_voice,
        "PU7_motion": motion,
        "PU8_mobile": mobile,
        "identity_routing": False,
        "category_direct_visual_template_lookup": False,
        "asset_scarcity_family_switch": False,
    }


def _headline_markup(units: Sequence[str]) -> str:
    return "".join(f'<span class="premium-headline-unit">{_esc(unit)}</span>' for unit in units)


def _binding_markup(binding: Mapping[str, Any] | None, story: Mapping[str, Any] | None) -> str:
    if not binding:
        return ""
    rendered = render_asset_binding(binding)
    story = story or {}
    return (
        f'<div class="premium-media" data-story-function="{_esc(story.get("story_function"))}" '
        f'data-caption-mode="{_esc(story.get("caption_mode"))}">{rendered}</div>'
    )


def _offer_markup(offers: Sequence[Mapping[str, Any]]) -> str:
    rows = []
    for index, offer in enumerate(offers, 1):
        name = _text(offer.get("name")) or f"選択肢 {index:02d}"
        rows.append(
            f'<li><span class="offer-index">{index:02d}</span>'
            f'<strong>{_esc(name)}</strong><span class="offer-note">選ぶ前に違いを確認</span></li>'
        )
    return "".join(rows)


def _proof_markup(proof_cta: Mapping[str, Any]) -> str:
    rows = proof_cta["proof"]["objection_to_proof_map"]
    if not rows:
        return (
            '<div class="proof-boundary"><span>FACT CHECK</span>'
            '<p>確認できていない実績や評価は、事実のようには掲載していません。</p></div>'
        )
    return "".join(
        f'<article class="proof-card" data-fact-id="{_esc(row["fact_id"])}">'
        f'<span>VERIFIED</span><p>{_esc(row["claim"])}</p></article>'
        for row in rows
    )


def _cta_markup(proof_cta: Mapping[str, Any], *, compact: bool = False) -> str:
    cta = proof_cta["cta"]
    cls = "cta-row cta-row--compact" if compact else "cta-row"
    if cta["actionable"]:
        primary = (
            f'<a class="cta-primary" href="{_esc(cta["verified_destination"])}">'
            f'{_esc(cta["primary_label"])}<span aria-hidden="true">↗</span></a>'
        )
    else:
        primary = f'<span class="cta-primary cta-primary--disabled" aria-disabled="true">{_esc(cta["primary_label"])}</span>'
    secondary = f'<a class="cta-secondary" href="{_esc(cta["secondary_destination"])}">{_esc(cta["secondary_label"])}</a>'
    return f'<div class="{cls}">{primary}{secondary}</div>'


def render_premium_asset_bound_html(
    plan: Mapping[str, Any],
    directives: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
    premium: Mapping[str, Any] | None = None,
) -> str:
    """Render the premium authored sales surface while preserving plan authority."""
    premium = deepcopy(dict(premium or build_premium_uplift(plan, directives, asset_bindings)))
    copy = premium["PU1_public_copy"]
    hero = premium["PU2_hero_authority"]
    dramaturgy = premium["PU3_scene_dramaturgy"]
    media_story = premium["PU4_media_story"]["bindings"]
    proof_cta = premium["PU5_proof_cta"]
    voice = premium["PU6_visual_voice"]
    mobile = premium["PU8_mobile"]
    offers = plan["input"]["company_truth"]["offers"]
    scenes = list(directives.get("scene_intents") or [])

    hero_media = _binding_markup(asset_bindings.get("hero"), media_story.get("hero"))
    hero_mobile_class = " mobile-media-first" if mobile["hero_media_first"] else ""
    scene_markup: list[str] = []
    for index, scene in enumerate(scenes, 1):
        scene_id = _text(scene["id"])
        if scene_id == "recognize":
            continue
        authored = copy["scenes"][scene_id]
        drama = dramaturgy["scenes"][scene_id]
        story = media_story.get(scene_id)
        media = _binding_markup(asset_bindings.get(scene_id), story)
        proof = _proof_markup(proof_cta) if scene_id == "trust" else ""
        reentry = _cta_markup(proof_cta, compact=True) if scene_id in proof_cta["cta"]["reentry_scene_ids"] else ""
        media_first = drama["mobile_recomposition"]["media_priority"] == "first"
        scene_markup.append(
            f'<section class="premium-scene scene--{_esc(drama["scene_weight"])} '
            f'density--{_esc(drama["density_mode"])} width--{_esc(drama["canvas_width_mode"])}" '
            f'data-premium-scene="{_esc(scene_id)}" data-intent="{_esc(scene.get("intent"))}" '
            f'data-mobile-media-first="{str(media_first).lower()}" style="--chapter-index:{index}">'
            f'<div class="scene-index">{index:02d}</div>'
            f'<div class="scene-copy"><p class="scene-kicker">CHAPTER {index:02d}</p>'
            f'<h2>{_esc(authored["headline"])}</h2>'
            f'<p>{_esc(authored["support_copy"])}</p>{proof}{reentry}</div>'
            f'<div class="scene-media">{media}</div>'
            f'</section>'
        )

    accent = _esc(voice["accent"])
    font_display = (
        '"Yu Mincho","Hiragino Mincho ProN",serif'
        if voice["type_relationship"] == "serif_display_sans_body"
        else 'system-ui,-apple-system,"Hiragino Kaku Gothic ProN",sans-serif'
    )
    header_note = "選ぶ前に、必要なことを。"
    html_text = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(copy["company_name"])}</title>
<style>
:root{{--ink:#161916;--paper:#f4f2ed;--surface:#fff;--muted:#6f746f;--line:#c9cec7;--accent:{accent};
--display:{font_display};--body:system-ui,-apple-system,"Hiragino Kaku Gothic ProN",sans-serif;--measure:{_esc(voice["measure"])};}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);letter-spacing:.01em}}
a{{color:inherit}}.premium-shell{{max-width:1440px;margin:auto;padding:0 clamp(20px,5.5vw,88px);overflow-x:clip}}
.premium-header{{min-height:78px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);gap:20px}}
.brand-mark{{font-weight:760;letter-spacing:.08em}}.header-note{{font-size:12px;color:var(--muted);letter-spacing:.12em}}
.premium-hero{{min-height:82svh;display:grid;grid-template-columns:minmax(0,.92fr) minmax(320px,1.08fr);gap:clamp(32px,7vw,104px);align-items:center;padding:clamp(56px,8vw,118px) 0}}
.hero--choice_led{{grid-template-columns:minmax(0,.82fr) minmax(360px,1.18fr)}}.hero--quiet_authority{{grid-template-columns:minmax(0,1.06fr) minmax(320px,.94fr)}}
.hero--action_led{{min-height:76svh}}.hero--proof_led{{grid-template-columns:minmax(0,.86fr) minmax(360px,1.14fr)}}
.eyebrow,.scene-kicker,.proof-card span,.proof-boundary span{{font-size:11px;letter-spacing:.18em;color:var(--muted);text-transform:uppercase}}
.premium-hero h1{{font-family:var(--display);font-weight:500;font-size:clamp(46px,7.2vw,108px);line-height:.98;letter-spacing:-.045em;margin:18px 0 26px;max-width:10.5em}}
.premium-headline-unit{{display:block}}.hero-lead{{max-width:var(--measure);font-size:clamp(16px,1.45vw,20px);line-height:1.9;color:#3b403c}}
.hero-authority{{display:flex;gap:12px;align-items:center;margin-top:30px;font-size:12px;color:var(--muted)}}.hero-authority:before{{content:"";width:40px;border-top:1px solid var(--accent)}}
.premium-media{{min-width:0}}.production-asset{{margin:0!important}}.premium-hero__media .production-asset img{{aspect-ratio:4/5;border-radius:clamp(8px,1.6vw,24px)}}
.offer-guide{{padding:clamp(52px,8vw,110px) 0;border-top:1px solid var(--line)}}.offer-guide__head{{max-width:760px;margin-bottom:34px}}
.offer-guide h2{{font-family:var(--display);font-size:clamp(32px,4vw,56px);font-weight:500;line-height:1.15;margin:10px 0}}
.premium-offers{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}}
.premium-offers li{{min-height:170px;padding:22px;border:1px solid var(--line);background:rgba(255,255,255,.52);display:flex;flex-direction:column;justify-content:space-between}}
.offer-index{{font-size:11px;color:var(--muted)}}.premium-offers strong{{font-size:clamp(20px,2vw,28px);font-weight:600}}.offer-note{{font-size:12px;color:var(--muted)}}
.premium-scene{{position:relative;min-height:52svh;border-top:1px solid var(--line);display:grid;grid-template-columns:54px minmax(0,.88fr) minmax(280px,1.12fr);gap:clamp(20px,4.5vw,70px);align-items:center;padding:clamp(60px,9vw,132px) 0}}
.premium-scene.width--contained{{grid-template-columns:54px minmax(0,1.05fr) minmax(260px,.95fr);max-width:1180px}}
.premium-scene.scene--closing{{min-height:38svh}}.scene-index{{align-self:start;font-size:12px;color:var(--muted);padding-top:10px}}
.scene-copy{{max-width:var(--measure)}}.scene-copy h2{{font-family:var(--display);font-weight:500;font-size:clamp(34px,5vw,70px);line-height:1.08;letter-spacing:-.035em;margin:10px 0 22px}}
.scene-copy>p{{font-size:clamp(15px,1.35vw,19px);line-height:1.9;color:#404640}}
.scene-media{{min-width:0}}.scene-media .production-asset img{{aspect-ratio:16/11;border-radius:clamp(5px,1.2vw,18px)}}
.density--compact{{padding-top:clamp(44px,6vw,88px);padding-bottom:clamp(44px,6vw,88px)}}.density--structured_dense .scene-copy{{max-width:31rem}}
.proof-boundary,.proof-card{{margin-top:28px;padding:18px 20px;border-left:2px solid var(--accent);background:rgba(255,255,255,.58)}}.proof-boundary p,.proof-card p{{margin:7px 0 0;line-height:1.65}}
.cta-row{{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:30px}}.cta-row--compact{{margin-top:22px}}
.cta-primary,.cta-secondary{{display:inline-flex;align-items:center;justify-content:space-between;gap:24px;text-decoration:none;border-radius:999px;min-height:52px;padding:0 22px;font-size:14px}}
.cta-primary{{background:var(--ink);color:white;min-width:230px}}.cta-secondary{{border:1px solid var(--line);background:rgba(255,255,255,.45)}}.cta-primary--disabled{{opacity:.58}}
.premium-closing{{margin:0 calc(-1 * clamp(20px,5.5vw,88px));padding:clamp(70px,10vw,150px) clamp(20px,5.5vw,88px);background:#1c211e;color:#f8f7f3;display:grid;grid-template-columns:minmax(0,1fr) minmax(280px,.75fr);gap:clamp(30px,7vw,100px);align-items:end}}
.premium-closing h2{{font-family:var(--display);font-weight:500;font-size:clamp(40px,6vw,82px);line-height:1.03;margin:14px 0 22px;max-width:9em}}.premium-closing p{{color:#c7cec9;line-height:1.8;max-width:34rem}}
.premium-closing .cta-primary{{background:#f5f4ef;color:#171a18}}.premium-closing .cta-secondary{{border-color:#59615c;color:#f5f4ef}}
.premium-footer{{min-height:84px;display:flex;align-items:center;justify-content:space-between;gap:18px;font-size:11px;color:var(--muted)}}
@keyframes premium-reveal{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:none}}}}
.premium-hero__copy,.premium-hero__media{{animation:premium-reveal .68s cubic-bezier(.2,.72,.2,1) both}}.premium-hero__media{{animation-delay:.12s}}
.premium-scene{{animation:premium-reveal .58s ease-out both;animation-delay:calc(min(var(--chapter-index),6) * 55ms)}}
@media(max-width:900px){{.premium-hero,.hero--choice_led,.hero--quiet_authority,.hero--proof_led{{grid-template-columns:1fr 1fr;gap:30px}}.premium-scene,.premium-scene.width--contained{{grid-template-columns:42px minmax(0,1fr);gap:22px}}.scene-media{{grid-column:2}}.premium-closing{{grid-template-columns:1fr}}}}
@media(max-width:430px){{.premium-shell{{padding:0 20px}}.premium-header{{min-height:68px}}.header-note{{display:none}}
.premium-hero,.hero--choice_led,.hero--quiet_authority,.hero--proof_led,.hero--action_led{{grid-template-columns:1fr;min-height:auto;padding:54px 0 64px;gap:28px}}
.premium-hero__copy{{max-width:100%}}.premium-hero__media{{order:2}}.premium-hero.mobile-media-first .premium-hero__media{{order:-1}}.premium-hero.mobile-media-first .premium-hero__copy{{order:1}}
.premium-hero h1{{font-size:clamp(42px,14vw,58px);max-width:9em;margin:14px 0 20px}}.hero-lead{{max-width:32ch;line-height:1.8}}
.premium-offers{{grid-template-columns:1fr}}.premium-offers li{{min-height:132px}}
.premium-scene,.premium-scene.width--contained{{display:flex;flex-direction:column;align-items:stretch;min-height:auto;padding:64px 0;gap:18px}}.scene-index{{padding:0}}.scene-copy{{max-width:32ch}}.scene-copy h2{{font-size:clamp(34px,11vw,46px)}}
.scene-media{{order:2}}.premium-scene[data-mobile-media-first="true"] .scene-media{{order:1}}.premium-scene[data-mobile-media-first="true"] .scene-copy{{order:2}}.premium-scene .scene-index{{order:0}}
.scene-media .production-asset img,.premium-hero__media .production-asset img{{aspect-ratio:4/3}}.cta-row{{align-items:stretch}}.cta-primary,.cta-secondary{{width:100%;min-width:0}}
.premium-closing{{margin:0 -20px;padding:72px 20px}}.premium-closing h2{{font-size:clamp(40px,13vw,54px)}}.premium-footer{{flex-direction:column;align-items:flex-start;padding:24px 0}}
}}
@media(max-width:360px){{.hero-lead,.scene-copy{{max-width:29ch}}.premium-scene{{padding:56px 0}}}}
@media(max-width:340px){{.premium-headline-unit{{display:block;white-space:nowrap}}}}
@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}*,*::before,*::after{{animation:none!important;transition:none!important;transform:none!important}}}}
{asset_binding_css()}
</style></head>
<body data-production-authority="composition_plan" data-plan-digest="{_esc(plan_digest(plan))}" data-premium-authorship="issue116">
<main class="premium-shell" data-voice="{_esc(voice["voice_mode"])}">
<header class="premium-header"><strong class="brand-mark">{_esc(copy["company_name"])}</strong><span class="header-note">{_esc(header_note)}</span></header>
<section class="premium-hero hero--{_esc(hero["hero_composition_intent"])}{hero_mobile_class}">
<div class="premium-hero__copy"><p class="eyebrow">{_esc(copy["eyebrow"])}</p>
<h1>{_headline_markup(copy["hero_headline_units"])}</h1><p class="hero-lead">{_esc(copy["hero_support"])}</p>
<p class="hero-authority">確認できる情報だけで、判断しやすい順番をつくる。</p>{_cta_markup(proof_cta, compact=True)}</div>
<div class="premium-hero__media">{hero_media}</div></section>
<section class="offer-guide" id="details"><div class="offer-guide__head"><p class="eyebrow">YOUR OPTIONS</p><h2>選ぶ前に、違いを見渡す。</h2><p>必要な情報を、迷いが少ない順番で確かめられます。</p></div>
<ul class="premium-offers">{_offer_markup(offers)}</ul></section>
{''.join(scene_markup)}
<section class="premium-closing" id="contact"><div><p class="eyebrow">NEXT STEP</p><h2>納得してから、次へ。</h2><p>{_esc(proof_cta["cta"]["pre_cta_reassurance"])}</p></div>
<div>{_cta_markup(proof_cta)}</div></section>
<footer class="premium-footer"><span>{_esc(copy["company_name"])}</span><span>確認済み情報を優先して構成しています。</span></footer>
</main></body></html>"""

    visible_text = html_text.replace('data-intent="recognize"', 'data-intent-private="recognize"')
    for phrase in BANNED_VALIDATION_COPY:
        if phrase in visible_text:
            raise PremiumAuthorshipError("BANNED_VALIDATION_COPY_VISIBLE")
    return html_text


__all__ = [
    "MOBILE_WIDTHS",
    "INTERNAL_INTENT_TOKENS",
    "BANNED_VALIDATION_COPY",
    "PremiumAuthorshipError",
    "build_public_copy",
    "compose_hero_authority",
    "plan_scene_dramaturgy",
    "bind_media_story",
    "choreograph_proof_cta",
    "derive_visual_voice",
    "plan_motion",
    "plan_mobile_recomposition",
    "build_premium_uplift",
    "render_premium_asset_bound_html",
]
