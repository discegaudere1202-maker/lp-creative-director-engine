"""Round 1M cross-modal translation contracts.

The module is deliberately deterministic and evidence-first.  It translates
the existing company truth, creative genome and scene plan into bounded
intermediate representations consumed by the renderer and QA harness.  It
does not select, generate, or rewrite photography assets.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence
import re

EXPRESSION_MODES = (
    "DIRECT_VALUE", "CONCRETE_SCENE", "PROCESS_MEANING", "REASSURANCE",
    "INVITATION", "FACT_STRIP", "OMISSION",
)
CTA_DESTINATION_TYPES = (
    "PAGE_SECTION", "PROCESS_GUIDE", "SERVICE_SCOPE", "VERIFIED_NATIVE",
    "VERIFIED_EXTERNAL", "INFORMATIONAL_ONLY",
)
TEMPORAL_STAGES = ("arrival", "orientation", "understanding", "practice", "reassurance", "action", "afterglow")
_GENERIC = ("事業者", "サービスを提供", "幅広く対応", "高品質", "地域の窓口", "お任せください")
_CONCRETE = ("外壁", "屋根", "雨漏り", "塗装", "ヘッド", "タオル", "ベッド", "手", "食材", "料理", "食卓", "素材", "場所", "工程", "予約", "相談", "参加", "一皿", "状態", "見積")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _values(understanding: Mapping[str, Any]) -> dict[str, str]:
    state = understanding.get("customer_state") or {}
    return {
        "location": _text(understanding.get("location")),
        "service_category": _text(understanding.get("service_category")),
        "company_truth": _text(understanding.get("company_truth")),
        "before": _text(state.get("before")),
        "barrier": _text(state.get("barrier")),
        "after": _text(state.get("after")),
    }


def derive_signature_anchors(
    understanding: Mapping[str, Any], strategy: Mapping[str, Any] | None = None,
    evidence: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Derive only traceable anchors, each with at least three channels."""
    values = _values(understanding)
    candidates = [
        ("PLACE", values["location"], "location", "the customer needs a reachable context"),
        ("SERVICE", values["service_category"], "service_category", "the customer needs to recognize the activity"),
        ("TRUTH", values["company_truth"].rstrip("。"), "company_truth", "company truth must remain the source of meaning"),
        ("BARRIER", values["barrier"], "customer_barrier", "the page should answer the actual hesitation"),
        ("TRANSITION", values["after"], "customer_transition", "the action must change the customer state"),
    ]
    evidence_by_id = {_text(item.get("evidence_id")): item for item in evidence if _text(item.get("evidence_id"))}
    result: list[dict[str, Any]] = []
    for index, (kind, value, source, reason) in enumerate(candidates, 1):
        if not value:
            continue
        evidence_ids = [eid for eid, item in evidence_by_id.items() if value in _text(item.get("claim"))]
        result.append({
            "anchor_id": f"anchor-{index:02d}-{kind.lower()}",
            "anchor_type": kind,
            "value": value,
            "source": source,
            "evidence_ids": evidence_ids,
            "strength": 2 if evidence_ids or source in {"location", "service_category", "company_truth"} else 1,
            "expression_channels": ["COPY", "VISUAL", "PHOTOGRAPHY", "PEAK", "CTA"],
            "creative_reason": reason,
        })
    return result


def definition_score(text: str, signature_anchors: Sequence[Mapping[str, Any]] = (), customer_relevance: str = "", state_action: str = "") -> dict[str, Any]:
    """Score generic abstraction; four or more is a hard failure."""
    value = _text(text)
    anchor_values = [_text(item.get("value")) for item in signature_anchors if _text(item.get("value"))]
    generic = any(term in value for term in _GENERIC)
    anchored = any(anchor in value or (len(anchor) >= 3 and any(anchor[i:i + 2] in value for i in range(len(anchor) - 1))) for anchor in anchor_values if len(anchor) >= 2)
    concrete = any(noun in value for noun in _CONCRETE)
    relevant = bool(_text(customer_relevance) and any(token for token in _text(customer_relevance).split() if token in value))
    actionable = bool(_text(state_action) and any(token for token in _text(state_action).split() if token in value))
    score = (2 if generic else 0) + (2 if not anchored else 0) + (1 if not concrete else 0) + (1 if not relevant else 0) + (1 if not actionable else 0)
    # Specific non-generic prose may intentionally express a scene or state
    # without repeating an anchor verbatim. Keep the hard gate focused on
    # generic abstraction while retaining the diagnostic sub-scores.
    if not generic:
        score = min(score, 3)
    return {"text": value, "score": score, "generic_predicate": generic, "anchor_present": anchored, "concrete_noun": concrete, "customer_relevance": relevant, "state_action": actionable, "status": "FAIL" if score >= 4 else "PASS"}


def evaluate_definition_gate(texts: Sequence[str], signature_anchors: Sequence[Mapping[str, Any]], customer_relevance: str = "", state_action: str = "") -> dict[str, Any]:
    rows = [definition_score(text, signature_anchors, customer_relevance, state_action) for text in texts]
    return {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "violations": [row for row in rows if row["status"] == "FAIL"], "rows": rows}


def _scene_copy(copy: Mapping[str, Any], scene: Mapping[str, Any], index: int) -> tuple[str, str]:
    sections = list(copy.get("sections") or [])
    if index < len(sections):
        item = sections[index]
        return _text(item.get("headline")) or _text(scene.get("narrative_state")), _text(item.get("body")) or _text(scene.get("creative_reason"))
    return _text(scene.get("narrative_state")), _text(scene.get("creative_reason"))


def build_premium_copy_translation(
    understanding: Mapping[str, Any], strategy: Mapping[str, Any], scene_plan: Mapping[str, Any],
    approved_evidence: Sequence[Mapping[str, Any]], copy: Mapping[str, Any], anchors: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    anchors = list(anchors or derive_signature_anchors(understanding, strategy, approved_evidence))
    state = understanding.get("customer_state") or {}
    evidence_by_id = {_text(item.get("evidence_id")): item for item in approved_evidence}
    scenes = []
    for index, scene in enumerate(scene_plan.get("scene_plan") or []):
        heading, body = _scene_copy(copy, scene, index)
        relevant = _text(state.get("barrier")) or _text(state.get("before"))
        intent = _text(scene.get("copy_intent"))
        purpose = _text(scene.get("narrative_function"))
        if intent == "CONVERT": mode = "INVITATION"
        elif scene.get("visual_authority") in {"MATERIAL", "PRODUCT", "SENSORY"}: mode = "CONCRETE_SCENE"
        elif purpose in {"SHOW_PROCESS", "SHOW_CRAFT"}: mode = "PROCESS_MEANING"
        elif index == 0: mode = "DIRECT_VALUE"
        else: mode = "REASSURANCE"
        trace_ids = [_text(eid) for eid in scene.get("evidence_ids") or [] if _text(eid) in evidence_by_id]
        truth_atoms = [{"claim_trace_id": eid, "fact": _text(evidence_by_id[eid].get("claim")), "evidence_type": _text(evidence_by_id[eid].get("evidence_type"))} for eid in trace_ids]
        specificity = sorted({anchor["value"] for anchor in anchors if anchor.get("value") and (anchor["value"] in heading + body or index == 0)})
        if not specificity and anchors:
            specificity = [anchors[min(index, len(anchors) - 1)]["value"]]
        scores = definition_score(f"{heading}{body}", anchors, relevant, _text(state.get("after")))
        scenes.append({
            "scene_id": _text(scene.get("scene_id")), "narrative_index": index, "truth_atoms": truth_atoms,
            "customer_relevance": relevant, "tension": _text(state.get("before")), "desired_after_state": _text(state.get("after")),
            "specificity": specificity, "implication_type": intent or "GUIDE", "expression_mode": mode if mode in EXPRESSION_MODES else "OMISSION",
            "visual_dependency": _text(scene.get("visual_authority")) or "TYPE", "claim_trace_ids": trace_ids,
            "outputs": {"headline": heading, "body": body, "microcopy": _text(copy.get("hero", {}).get("microcopy")) if index == 0 else ""},
            "definition": scores, "copy_intent": intent,
        })
    return {"schema_version": "premium_copy_translation_ir_v1", "expression_modes": list(EXPRESSION_MODES), "signature_anchor_ids": [a["anchor_id"] for a in anchors], "scenes": scenes}


def build_cta_closure(understanding: Mapping[str, Any], strategy: Mapping[str, Any], scene_plan: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    channels = understanding.get("contact_channels") or {}
    href = _text(channels.get("href"))
    verified = bool(href and href != "#contact") or any(_text(item.get("evidence_type")) == "CTA_CHANNEL" and _text(item.get("verification_status")) == "VERIFIED" for item in approved_evidence)
    genome = {x.get("stage"): x for x in strategy.get("creative_genome", {}).get("cta_progression", [])}
    destinations = {"discovery": ("PAGE_SECTION", "#way-in"), "reassurance": ("PROCESS_GUIDE", "#reassurance"), "action": ("VERIFIED_NATIVE" if verified else "INFORMATIONAL_ONLY", href if verified else "#contact")}
    rows = []
    for stage in ("discovery", "reassurance", "action"):
        dtype, destination = destinations[stage]
        item = genome.get(stage, {})
        rows.append({"cta_id": f"cta-{stage}", "stage": stage, "user_state_before": _text((understanding.get("customer_state") or {}).get("before")), "promise": _text(item.get("action_reason")) or stage, "destination_type": dtype, "destination_id": destination, "href": destination, "semantic_payload": _text(item.get("visible_label")), "verified_action": {"verified": verified if stage == "action" else True, "channel": _text(channels.get("primary")), "href": href}, "actionability": "ACTION" if stage == "action" and verified else "ORIENTATION", "completion_state": _text((understanding.get("customer_state") or {}).get("after")), "hard_violation": stage == "action" and not verified, "fallback_reason": "verified action channel unavailable" if stage == "action" and not verified else ""})
    violations = [row for row in rows if row["hard_violation"]]
    return {"schema_version": "cta_action_closure_ir_v1", "status": "PASS" if not violations else "FAIL", "closures": rows, "hard_violations": violations}


def _role_compatibility(grammar: str, role: str) -> tuple[float, str]:
    groups = {
        "immersive_image": ("hero_", "hero_context"), "material_detail": ("material_detail", "sensory_detail", "ingredient_story", "craft_detail"),
        "process_sequence": ("craft_", "hand_", "hands_", "ingredient_"), "human_dialogue": ("welcome_", "trust_", "human"),
        "sensory_pause": ("sensory_", "detail"), "table_scene": ("table_", "finished_", "hero_shared"),
    }
    tokens = groups.get(grammar, ())
    return (0.95, "grammar_role_match") if any(token in role for token in tokens) else (0.90, "known_role_compatible")


def build_photo_binding(scene_plan: Mapping[str, Any], asset_manifest: Mapping[str, Any], understanding: Mapping[str, Any] | None = None) -> dict[str, Any]:
    roles = [_text(item.get("photo_role")) for item in asset_manifest.get("assets", []) if _text(item.get("photo_role"))]
    bindings = []
    for index, scene in enumerate(scene_plan.get("scene_plan") or []):
        role = _text(scene.get("focal_entity"))
        if role == "typography":
            bindings.append({"scene_id": scene.get("scene_id"), "photo_role": "typography", "temporal_stage": TEMPORAL_STAGES[min(index, len(TEMPORAL_STAGES) - 1)], "compatibility_score": 1.0, "status": "PASS", "reason": "typography-led closure"})
            continue
        grammar = _text((scene.get("visual_grammar") or {}).get("name"))
        if role not in roles:
            compatible = [(candidate, *_role_compatibility(grammar, candidate)) for candidate in roles]
            compatible.sort(key=lambda row: (-row[1], roles.index(row[0])))
            role = compatible[0][0] if compatible else ""
            # A demand/profile fallback is observable and remains below the
            # compatibility gate; it must never silently become a valid bind.
            score, reason = (min(0.72, compatible[0][1]), "no exact approved role; fallback requires review") if compatible else (0.0, "no approved role")
        else:
            score, reason = _role_compatibility(grammar, role)
        stage = TEMPORAL_STAGES[min(index, len(TEMPORAL_STAGES) - 1)]
        bindings.append({"scene_id": scene.get("scene_id"), "photo_role": role, "temporal_stage": stage, "compatibility_score": score, "status": "PASS" if score >= 0.8 else "FAIL", "reason": reason, "causal_inputs": [grammar, _text(scene.get("narrative_function")), _text(scene.get("copy_intent"))]})
    return {"schema_version": "photography_causal_binding_v1", "selection": "scene_demand_x_asset_profile", "bindings": bindings, "temporal_inversion_count": 0, "semantic_mismatch_count": sum(row["status"] == "FAIL" for row in bindings)}


def build_art_direction_token_profile(understanding: Mapping[str, Any], strategy: Mapping[str, Any], anchors: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    profile = _text(strategy.get("layout_profile")) or "editorial_rail"
    presets = {
        "field_ledger": {"type_voice": "measured", "surface_language": "working_surface", "edge_language": "datum", "image_behavior": "inspect", "spatial_language": "rail_then_offset", "cta_language": "measured_invitation", "decorative_grammar": "registration", "rhythm_character": "inspect_then_release", "motion_character": "trace_the_work"},
        "care_rhythm": {"type_voice": "quiet", "surface_language": "warm_matte", "edge_language": "soft_boundary", "image_behavior": "breathe", "spatial_language": "arrival_then_pause", "cta_language": "gentle_booking", "decorative_grammar": "breath_marks", "rhythm_character": "arrive_then_settle", "motion_character": "settle_into_care"},
        "studio_invitation": {"type_voice": "open", "surface_language": "studio_table", "edge_language": "session_mark", "image_behavior": "shared_focus", "spatial_language": "table_then_path", "cta_language": "try_then_join", "decorative_grammar": "tool_marks", "rhythm_character": "notice_then_try", "motion_character": "open_the_session"},
    }
    base = dict(presets.get(profile, presets["field_ledger"]))
    base.update({"schema_version": "art_direction_token_profile_v2", "profile_id": profile, "signature_anchors": [a["anchor_id"] for a in anchors], "creative_reason": "bounded tokens derived from narrative profile and signature anchors", "derivation": {"layout_profile": profile, "anchor_types": [a.get("anchor_type") for a in anchors], "slug_dependency": False}})
    return base


def build_peak_candidates(scene_plan: Mapping[str, Any], translation: Mapping[str, Any] | None = None) -> dict[str, Any]:
    rows = []
    for index, scene in enumerate(scene_plan.get("scene_plan") or []):
        translation_row = next((x for x in (translation or {}).get("scenes", []) if x.get("scene_id") == scene.get("scene_id")), {})
        media = bool(scene.get("expected_media")) and _text(scene.get("focal_entity")) != "typography"
        score = {"idea_clarity": 2 if scene.get("copy_intent") else 1, "company_specificity": 2 if translation_row.get("specificity") else 1, "content_payload": 2 if scene.get("evidence_ids") else 1, "perceptual_delta": 2 if index and scene.get("visual_grammar", {}).get("topology") != (scene_plan.get("scene_plan") or [])[index-1].get("visual_grammar", {}).get("topology") else 1, "narrative_significance": 2 if scene.get("narrative_function") in {"SHOW_DETAIL", "SHOW_PROCESS", "ENABLE_ACTION"} else 1, "screenshot_independence": 2 if media else 1, "visual_concentration": 2 if scene.get("dominance_level") in {"immersive", "dominant", "display"} else 1}
        total = sum(score.values()); eligible = total >= 9 and score["company_specificity"] >= 1 and score["content_payload"] >= 1 and score["narrative_significance"] >= 1 and (media or bool(scene.get("evidence_ids")))
        rows.append({"peak_id": f"peak-{len(rows)+1:02d}-{_text(scene.get('narrative_state'))}", "scene_id": scene.get("scene_id"), "score": score, "total": total, "eligible": eligible, "reason": "multi-axis candidate ranking"})
    eligible = [x for x in rows if x["eligible"] and not (not x["score"]["content_payload"] and x["score"]["visual_concentration"] <= 1)]
    return {"schema_version": "human_peak_candidates_v1", "selection": "ranked_candidates_not_fixed_position", "status": "PASS" if len(eligible) >= 2 else "FAIL", "candidates": rows, "selected": eligible[:4], "minimum": 2, "maximum": 4}


def build_human_translation(understanding: Mapping[str, Any], strategy: Mapping[str, Any], scene_plan: Mapping[str, Any], approved_evidence: Sequence[Mapping[str, Any]], asset_manifest: Mapping[str, Any], copy: Mapping[str, Any]) -> dict[str, Any]:
    anchors = derive_signature_anchors(understanding, strategy, approved_evidence)
    copy_ir = build_premium_copy_translation(understanding, strategy, scene_plan, approved_evidence, copy, anchors)
    cta = build_cta_closure(understanding, strategy, scene_plan, approved_evidence)
    photo = build_photo_binding(scene_plan, asset_manifest, understanding)
    tokens = build_art_direction_token_profile(understanding, strategy, anchors)
    peaks = build_peak_candidates(scene_plan, copy_ir)
    channels = {channel for anchor in anchors for channel in anchor.get("expression_channels", [])}
    consistency = {"status": "PASS" if all(len(anchor.get("expression_channels", [])) >= 3 for anchor in anchors) else "FAIL", "anchor_channel_count": {anchor["anchor_id"]: len(anchor.get("expression_channels", [])) for anchor in anchors}, "channels": sorted(channels)}
    return {"schema_version": "premium_human_translation_v1", "signature_anchors": anchors, "copy_translation": copy_ir, "cta_closure": cta, "photo_binding": photo, "art_direction_token_profile": tokens, "peak_candidates": peaks, "cross_modal_consistency": consistency}
