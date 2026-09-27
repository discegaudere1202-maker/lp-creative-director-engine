"""Issue #129 premium perception recovery runtime.

This layer is downstream of the accepted Issue #121/#124 renderer chain.  It
turns the Page Art Direction Spine into pixel-authoritative v2 instructions and
turns existing rights-gated asset bindings into a page-level Media Narrative
Plan.  It never reopens Creative Family, mutates CompositionPlan, promotes
illustrative media to evidence, or routes from company/reference identity.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import html
import json
from typing import Any, Mapping, Sequence

from .visual_asset_library import render_asset_binding


class PremiumPerceptionRecoveryError(RuntimeError):
    pass


def _text(value: Any) -> str:
    return str(value or "").strip()


def _esc(value: Any) -> str:
    return html.escape(_text(value), quote=True)


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


SPINE_V2_FIELDS = (
    "primary_visual_thesis",
    "macro_silhouette",
    "hero_authority",
    "typography_relationship",
    "media_narrative_arc",
    "focal_scene_sequence",
    "density_arc",
    "whitespace_cadence",
    "contrast_arc",
    "material_surface_language",
    "section_transition_grammar",
    "proof_rhythm",
    "cta_cadence",
    "ending_resolution",
    "motion_intent",
    "desktop_composition",
    "mobile_re_art_direction",
)

MEDIA_BEAT_FIELDS = (
    "scene_id",
    "narrative_role",
    "compositional_role",
    "prominence_intent",
    "evidence_status",
    "source_rights_identity",
    "crop_geometry",
    "layering_behavior",
    "copy_interaction",
    "transition_role",
    "desktop_behavior",
    "mobile_re_art_direction",
    "fallback_restriction",
)

# Counts intentionally differ by mechanism.  They are narrative beats, not a
# universal image-count floor.  A beat can reuse a rights-gated source with a
# materially different crop/geometry when no truthful additional source exists.
MEDIA_NARRATIVE_TEMPLATES: dict[str, tuple[dict[str, str], ...]] = {
    "route": (
        {"narrative_role":"orientation_context","compositional_role":"opening panorama","prominence_intent":"dominant","crop_geometry":"landscape_immersive","layering_behavior":"bleed_under_route_index","copy_interaction":"copy floats beside, never over focal subject","transition_role":"hero_to_choice","desktop_behavior":"wide 12-column field","mobile_re_art_direction":"tall foreground context before route labels"},
        {"narrative_role":"route_context","compositional_role":"asymmetric route companion","prominence_intent":"co-dominant","crop_geometry":"portrait_offset","layering_behavior":"overlap_route_edge","copy_interaction":"media and route label share one focal scene","transition_role":"choice_deepening","desktop_behavior":"offset portrait/wide pair","mobile_re_art_direction":"media interrupts route stack as authored beat"},
        {"narrative_role":"decision_detail","compositional_role":"material/detail interruption","prominence_intent":"supporting","crop_geometry":"detail_strip","layering_behavior":"edge_to_edge_strip","copy_interaction":"detail follows decision cue","transition_role":"choice_to_reassurance","desktop_behavior":"horizontal material band","mobile_re_art_direction":"short full-width detail band"},
        {"narrative_role":"closing_echo","compositional_role":"visual route resolution","prominence_intent":"supporting","crop_geometry":"wide_quiet_crop","layering_behavior":"inset_horizon","copy_interaction":"closing copy remains separate","transition_role":"cta_to_ending","desktop_behavior":"wide quiet horizon","mobile_re_art_direction":"shallow closing image above final action"},
    ),
    "evidence": (
        {"narrative_role":"context_anchor","compositional_role":"environment/specimen authority","prominence_intent":"dominant","crop_geometry":"large_context_crop","layering_behavior":"full_bleed_with_fact_margin","copy_interaction":"facts sit adjacent, not printed on image","transition_role":"promise_to_context","desktop_behavior":"large image field plus narrow fact margin","mobile_re_art_direction":"image first, compact fact margin second"},
        {"narrative_role":"verification_context","compositional_role":"evidence-adjacent context","prominence_intent":"co-dominant","crop_geometry":"portrait_or_square_anchor","layering_behavior":"inset_against_ledger","copy_interaction":"illustrative context cannot become proof","transition_role":"context_to_known_unknown","desktop_behavior":"asymmetric image/ledger pair","mobile_re_art_direction":"image window followed by static verification"},
        {"narrative_role":"material_detail","compositional_role":"sensory detail","prominence_intent":"supporting","crop_geometry":"macro_detail_strip","layering_behavior":"cropped_material_band","copy_interaction":"detail carries atmosphere only","transition_role":"verification_to_service","desktop_behavior":"compressed detail band","mobile_re_art_direction":"edge-to-edge detail interruption"},
        {"narrative_role":"trust_transition","compositional_role":"spatial trust bridge","prominence_intent":"supporting","crop_geometry":"wide_environment","layering_behavior":"offset_against_whitespace","copy_interaction":"no factual claim overlay","transition_role":"proof_to_action","desktop_behavior":"wide spatial pause","mobile_re_art_direction":"full-width spatial pause"},
        {"narrative_role":"closing_context","compositional_role":"quiet contextual release","prominence_intent":"supporting","crop_geometry":"wide_quiet_crop","layering_behavior":"under_closing_frame","copy_interaction":"ending remains legible and separate","transition_role":"cta_to_ending","desktop_behavior":"low, wide closing image","mobile_re_art_direction":"short closing image after CTA"},
    ),
    "compare": (
        {"narrative_role":"comparison_a","compositional_role":"paired visual A","prominence_intent":"co-dominant","crop_geometry":"paired_equal_a","layering_behavior":"left_or_top_panel","copy_interaction":"A label outside image","transition_role":"comparison_open","desktop_behavior":"left half of diptych","mobile_re_art_direction":"first full-width comparison panel"},
        {"narrative_role":"comparison_b","compositional_role":"paired visual B","prominence_intent":"co-dominant","crop_geometry":"paired_equal_b","layering_behavior":"right_or_bottom_panel","copy_interaction":"B label outside image","transition_role":"comparison_open","desktop_behavior":"right half of diptych","mobile_re_art_direction":"second full-width comparison panel with contrast divider"},
        {"narrative_role":"criteria_detail","compositional_role":"comparison detail cut","prominence_intent":"supporting","crop_geometry":"detail_matrix_cut","layering_behavior":"cross_axis_inset","copy_interaction":"criteria remain text, image remains illustrative","transition_role":"compare_to_decision","desktop_behavior":"narrow detail crossing comparison axis","mobile_re_art_direction":"detail band between criteria and resolution"},
        {"narrative_role":"resolution_context","compositional_role":"single visual resolution","prominence_intent":"supporting","crop_geometry":"wide_resolution","layering_behavior":"single_field_after_pair","copy_interaction":"resolution copy adjacent","transition_role":"decision_to_cta","desktop_behavior":"one wide field resolves the pair","mobile_re_art_direction":"single closing context before CTA"},
    ),
    "prepare": (
        {"narrative_role":"before_context","compositional_role":"pre-action context","prominence_intent":"dominant","crop_geometry":"wide_before_scene","layering_behavior":"scene_entry_bleed","copy_interaction":"copy names uncertainty beside image","transition_role":"recognition_to_process","desktop_behavior":"large contextual opening","mobile_re_art_direction":"tall context scene before process"},
        {"narrative_role":"process_context","compositional_role":"process sequence carrier","prominence_intent":"co-dominant","crop_geometry":"process_landscape","layering_behavior":"integrated_with_steps","copy_interaction":"steps remain truthful; media carries atmosphere","transition_role":"process_progression","desktop_behavior":"wide media threaded through steps","mobile_re_art_direction":"media appears between process checkpoints"},
        {"narrative_role":"process_detail","compositional_role":"material/process detail","prominence_intent":"supporting","crop_geometry":"macro_process_detail","layering_behavior":"detail_inset","copy_interaction":"detail does not imply unverified equipment/process","transition_role":"process_to_reassurance","desktop_behavior":"small detail next to final checkpoint","mobile_re_art_direction":"full-width short detail"},
        {"narrative_role":"next_step_context","compositional_role":"prepared-state release","prominence_intent":"supporting","crop_geometry":"quiet_wide","layering_behavior":"breathing_space_before_cta","copy_interaction":"next step text outside image","transition_role":"prepare_to_action","desktop_behavior":"wide calm field","mobile_re_art_direction":"calm media pause before CTA"},
    ),
    "act": (
        {"narrative_role":"recognition_context","compositional_role":"action-opening field","prominence_intent":"dominant","crop_geometry":"immersive_context","layering_behavior":"full_bleed_entry","copy_interaction":"short action copy overlays safe region only","transition_role":"recognition_to_action","desktop_behavior":"immersive wide field","mobile_re_art_direction":"tall immersive field with copy below focal point"},
        {"narrative_role":"transition_field","compositional_role":"momentum bridge","prominence_intent":"co-dominant","crop_geometry":"asymmetric_transition","layering_behavior":"offset_overlap","copy_interaction":"media leads into CTA","transition_role":"body_to_action","desktop_behavior":"large offset image beside action field","mobile_re_art_direction":"image/action interlock, not generic stack"},
        {"narrative_role":"action_context","compositional_role":"closing reassurance image","prominence_intent":"supporting","crop_geometry":"quiet_close","layering_behavior":"inset_under_action","copy_interaction":"verified destination remains separate","transition_role":"cta_to_release","desktop_behavior":"low wide release","mobile_re_art_direction":"short final context after action"},
    ),
    "recognition": (
        {"narrative_role":"opening_context","compositional_role":"editorial opening world","prominence_intent":"dominant","crop_geometry":"editorial_immersive","layering_behavior":"full_bleed_or_large_inset","copy_interaction":"large type occupies deliberate negative space","transition_role":"emotion_to_recognition","desktop_behavior":"large editorial spread","mobile_re_art_direction":"tall image then oversized semantic headline"},
        {"narrative_role":"editorial_spread","compositional_role":"asymmetric story spread","prominence_intent":"co-dominant","crop_geometry":"portrait_landscape_dialogue","layering_behavior":"offset_overlap_pair","copy_interaction":"short prose sits in negative space","transition_role":"recognition_to_understanding","desktop_behavior":"asymmetric editorial two-up","mobile_re_art_direction":"alternating image/text beats"},
        {"narrative_role":"detail_echo","compositional_role":"sensory detail punctuation","prominence_intent":"supporting","crop_geometry":"detail_close","layering_behavior":"small_high_contrast_inset","copy_interaction":"no evidence claim","transition_role":"story_to_decision","desktop_behavior":"small detail against large whitespace","mobile_re_art_direction":"edge detail interruption"},
        {"narrative_role":"closing_breath","compositional_role":"visual emotional resolution","prominence_intent":"supporting","crop_geometry":"wide_breath","layering_behavior":"quiet_closing_field","copy_interaction":"ending copy remains sparse","transition_role":"cta_to_ending","desktop_behavior":"wide low-density close","mobile_re_art_direction":"quiet image close with inset CTA"},
    ),
}

WHITESPACE_CADENCE = {
    "route": "open orientation -> compressed route cluster -> material pause -> open route closure",
    "evidence": "large contextual field -> dense verification -> sensory pause -> calm factual close",
    "compare": "paired density -> criteria compression -> single-field resolution",
    "prepare": "open before-state -> sequenced compression -> reassurance pause -> prepared close",
    "act": "immersive recognition -> rapid narrowing -> oversized action release",
    "recognition": "immersive opening -> editorial breath -> focused detail -> spacious resolution",
}

TRANSITION_GRAMMAR = {
    "route": "field edge / index / band transitions",
    "evidence": "context field / factual inset / quiet spatial bridge",
    "compare": "paired axis / contrast cut / single-field resolution",
    "prepare": "checkpoint continuity / process-media interruption / calm release",
    "act": "overlap / momentum bridge / action field",
    "recognition": "editorial spread / alternating scale / whitespace handoff",
}


def _body_binding(asset_bindings: Mapping[str, Mapping[str, Any]]) -> tuple[str, Mapping[str, Any]] | tuple[None, None]:
    for key, value in asset_bindings.items():
        if key != "hero" and value:
            return key, value
    return None, None


def _binding_identity(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "asset_id": _text(binding.get("asset_id")),
        "binary_sha256": _text(binding.get("binary_sha256")),
        "source_provider": _text(binding.get("source_provider") or (binding.get("trace") or {}).get("source_provider")),
        "source_url": _text(binding.get("source_url") or (binding.get("trace") or {}).get("source_url")),
        "rights_gate": _text(binding.get("rights_gate") or (binding.get("trace") or {}).get("rights_gate_state")),
    }


def compile_media_narrative_plan(
    plan: Mapping[str, Any],
    ensemble: Mapping[str, Any],
    whole_trace: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Compile page-level media responsibility after Family freeze.

    Existing rights-gated bindings may be deliberately reused with different
    crops/geometry.  Reuse is recorded; it never manufactures new evidence.
    """
    family = plan.get("input", {}).get("creative_family", {})
    if family.get("frozen") is not True:
        raise PremiumPerceptionRecoveryError("FAMILY_NOT_FROZEN")
    continuation_family = _text(whole_trace.get("continuation_family"))
    template = MEDIA_NARRATIVE_TEMPLATES.get(continuation_family)
    if not template:
        raise PremiumPerceptionRecoveryError(f"MEDIA_NARRATIVE_TEMPLATE_MISSING:{continuation_family}")
    hero = asset_bindings.get("hero")
    body_key, body = _body_binding(asset_bindings)
    sources: list[tuple[str, Mapping[str, Any]]] = []
    if hero:
        sources.append(("hero", hero))
    if body:
        sources.append((_text(body_key), body))
    if not sources:
        raise PremiumPerceptionRecoveryError("MEDIA_NARRATIVE_SOURCE_BINDING_MISSING")

    beats: list[dict[str, Any]] = []
    for index, spec in enumerate(template):
        source_key, binding = sources[index % len(sources)]
        evidence_status = _text(binding.get("evidence_status")) or "UNKNOWN"
        beat = {
            "scene_id": f"media-narrative-{index + 1:02d}",
            "narrative_role": spec["narrative_role"],
            "compositional_role": spec["compositional_role"],
            "prominence_intent": spec["prominence_intent"],
            "evidence_status": evidence_status,
            "source_rights_identity": _binding_identity(binding),
            "crop_geometry": spec["crop_geometry"],
            "layering_behavior": spec["layering_behavior"],
            "copy_interaction": spec["copy_interaction"],
            "transition_role": spec["transition_role"],
            "desktop_behavior": spec["desktop_behavior"],
            "mobile_re_art_direction": spec["mobile_re_art_direction"],
            "fallback_restriction": "fail_closed_if_source_missing; never promote illustrative media to company evidence",
            "source_binding_key": source_key,
            "source_asset_id": _text(binding.get("asset_id")),
            "source_reused_for_composition": sum(1 for prior in beats if prior.get("source_asset_id") == _text(binding.get("asset_id"))) > 0,
        }
        missing = [field for field in MEDIA_BEAT_FIELDS if not beat.get(field)]
        if missing:
            raise PremiumPerceptionRecoveryError("MEDIA_BEAT_FIELDS_MISSING:" + ",".join(missing))
        beats.append(beat)

    return {
        "schema_version": "issue129_media_narrative_plan_v1",
        "continuation_family": continuation_family,
        "continuation_variant_id": _text(whole_trace.get("continuation_variant_id")),
        "decision_job": _text((ensemble.get("decision_signature") or {}).get("primary_job")),
        "family_frozen": True,
        "beat_count": len(beats),
        "beats": beats,
        "source_binding_count": len(sources),
        "source_asset_ids": sorted({_text(binding.get("asset_id")) for _, binding in sources}),
        "arbitrary_global_image_floor_used": False,
        "illustrative_media_promoted_to_proof": False,
        "identity_routing_used": False,
        "category_layout_routing_used": False,
        "randomness_used": False,
        "plan_digest": _sha({"family": plan.get("family_id"), "topology": plan.get("topology"), "scenes": plan.get("scene_intents")}),
    }


def compile_page_art_direction_spine_v2(
    ensemble: Mapping[str, Any],
    whole_trace: Mapping[str, Any],
    media_plan: Mapping[str, Any],
) -> dict[str, Any]:
    old = ensemble.get("page_art_direction_spine") or {}
    continuation_family = _text(whole_trace.get("continuation_family"))
    hero = ensemble.get("hero") or {}
    signature = ensemble.get("decision_signature") or {}
    if not continuation_family:
        raise PremiumPerceptionRecoveryError("CONTINUATION_FAMILY_MISSING")
    spine = {
        "primary_visual_thesis": _text(old.get("primary_visual_thesis")),
        "macro_silhouette": _text(old.get("silhouette_strategy")),
        "hero_authority": _text(hero.get("selected_production_variant_id")),
        "typography_relationship": _text(old.get("type_authority_strategy")),
        "media_narrative_arc": [beat["narrative_role"] for beat in media_plan["beats"]],
        "focal_scene_sequence": [beat["scene_id"] for beat in media_plan["beats"]],
        "density_arc": deepcopy(old.get("density_arc")),
        "whitespace_cadence": WHITESPACE_CADENCE[continuation_family],
        "contrast_arc": _text(old.get("contrast_strategy")),
        "material_surface_language": _text(old.get("material_language")),
        "section_transition_grammar": TRANSITION_GRAMMAR[continuation_family],
        "proof_rhythm": "verified facts remain static/local; illustrative media supplies context only" if signature.get("proof_available") else "known/unknown boundaries remain explicit; media cannot fill proof gaps",
        "cta_cadence": _text((whole_trace.get("propagation") or {}).get("cta")),
        "ending_resolution": _text(old.get("closing_resolution")),
        "motion_intent": f"{continuation_family} choreography: anticipation -> focal reveal -> stillness -> resolution; reduced-motion safe",
        "desktop_composition": f"1440 authored {continuation_family} composition with media carrying page-level rhythm",
        "mobile_re_art_direction": _text((whole_trace.get("propagation") or {}).get("mobile")),
    }
    missing = [field for field in SPINE_V2_FIELDS if spine.get(field) in (None, "", [])]
    if missing:
        raise PremiumPerceptionRecoveryError("SPINE_V2_FIELDS_MISSING:" + ",".join(missing))
    spine.update({
        "schema_version": "issue129_page_art_direction_spine_v2",
        "source_spine_digest": _text(old.get("spine_digest")),
        "family_frozen": True,
        "composition_plan_mutated": False,
        "identity_routing_used": False,
        "category_fixed_template_lookup_used": False,
        "random_diversity_used": False,
    })
    spine["spine_v2_digest"] = _sha(spine)
    return spine


def _narrative_figure(binding: Mapping[str, Any], beat: Mapping[str, Any], index: int) -> str:
    rendered = render_asset_binding(binding)
    return (
        f'<div class="ppr-media ppr-media--{_esc(beat["prominence_intent"])} ppr-crop--{_esc(beat["crop_geometry"])}" '
        f'data-media-role="{_esc(beat["narrative_role"])}" data-media-beat="{index:02d}" '
        f'data-evidence-status="{_esc(beat["evidence_status"])}">{rendered}</div>'
    )


def _media_scene(
    beats: Sequence[Mapping[str, Any]],
    asset_bindings: Mapping[str, Mapping[str, Any]],
    *,
    scene_index: int,
    family: str,
) -> str:
    figures = []
    for index, beat in enumerate(beats, 1):
        binding = asset_bindings.get(_text(beat.get("source_binding_key")))
        if not binding:
            raise PremiumPerceptionRecoveryError("MEDIA_NARRATIVE_RENDER_BINDING_MISSING")
        figures.append(_narrative_figure(binding, beat, index))
    role = " / ".join(_text(beat.get("narrative_role")).replace("_", " ").upper() for beat in beats)
    return (
        f'<section class="ppr-scene ppr-scene--{scene_index} ppr-family--{_esc(family)}" '
        f'data-premium-authored-scene="true" data-mobile-re-art-directed="true">'
        f'<div class="ppr-scene__label" aria-hidden="true">{_esc(role)}</div>'
        f'<div class="ppr-scene__media">{"".join(figures)}</div>'
        f'</section>'
    )


def _insert_after_hero(rendered: str, fragment: str) -> str:
    start = rendered.find('<section class="variant-hero')
    if start < 0:
        raise PremiumPerceptionRecoveryError("HERO_SECTION_ANCHOR_MISSING")
    end = rendered.find("</section>", start)
    if end < 0:
        raise PremiumPerceptionRecoveryError("HERO_SECTION_END_MISSING")
    end += len("</section>")
    return rendered[:end] + fragment + rendered[end:]


def _insert_before_closing(rendered: str, fragment: str) -> str:
    candidates = [
        rendered.find('<section class="variant-scene action-event'),
        rendered.find('<section class="variant-cta'),
        rendered.find('<section class="variant-ending'),
    ]
    candidates = [index for index in candidates if index >= 0]
    if not candidates:
        marker = rendered.rfind("</main>")
        if marker < 0:
            raise PremiumPerceptionRecoveryError("CLOSING_ANCHOR_MISSING")
        return rendered[:marker] + fragment + rendered[marker:]
    marker = min(candidates)
    return rendered[:marker] + fragment + rendered[marker:]


def _css() -> str:
    return r'''
/* Issue #129 — Premium Perception Recovery: media narrative + pixel-authoritative Spine v2 */
body[data-premium-perception-recovery="issue129"] .ppr-scene{position:relative;margin:0;padding:clamp(72px,9vw,150px) max(22px,5vw);overflow:hidden;isolation:isolate}
.ppr-scene__label{font:700 10px/1.2 ui-monospace,monospace;letter-spacing:.16em;opacity:.58;margin:0 0 26px}
.ppr-scene__media{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:clamp(12px,2vw,30px);align-items:center}
.ppr-media{min-width:0;position:relative}.ppr-media .production-asset{margin:0}.ppr-media .production-asset img{width:100%;height:100%;min-height:260px;object-fit:cover;border-radius:0}.ppr-media figcaption,.ppr-media .asset-attribution{position:absolute;left:10px;bottom:8px;margin:0;padding:4px 7px;background:rgba(255,255,255,.78);backdrop-filter:blur(6px);z-index:3}
.ppr-media--dominant{grid-column:1/13}.ppr-media--dominant .production-asset img{height:clamp(520px,68vw,880px)}
.ppr-media--co-dominant{grid-column:span 6}.ppr-media--co-dominant .production-asset img{height:clamp(430px,48vw,680px)}
.ppr-media--supporting{grid-column:span 4}.ppr-media--supporting .production-asset img{height:clamp(260px,31vw,430px)}
.ppr-scene--2 .ppr-media:first-child{grid-column:2/9}.ppr-scene--2 .ppr-media:nth-child(2){grid-column:8/13;margin-top:11vw;z-index:2}.ppr-scene--2 .ppr-media:nth-child(3){grid-column:1/6;margin-top:-5vw}
.ppr-family--route{background:linear-gradient(180deg,#f4f1ea 0%,#ece8de 100%)}.ppr-family--route .ppr-scene__media{transform:skewY(-1deg)}.ppr-family--route .ppr-media>*{transform:skewY(1deg)}
.ppr-family--evidence{background:#161918;color:#f4f2eb}.ppr-family--evidence .ppr-media--supporting{border-left:1px solid rgba(255,255,255,.35);padding-left:18px}.ppr-family--evidence .ppr-scene__label{border-bottom:1px solid rgba(255,255,255,.35);padding-bottom:12px}
.ppr-family--compare{background:#edece7}.ppr-family--compare .ppr-scene__media{gap:2px}.ppr-family--compare .ppr-media--co-dominant{grid-column:span 6}.ppr-family--compare .ppr-media--co-dominant:first-child{transform:translateY(-28px)}.ppr-family--compare .ppr-media--co-dominant:nth-child(2){transform:translateY(28px)}
.ppr-family--prepare{background:#f0eee7}.ppr-family--prepare .ppr-scene__media{border-top:1px solid #8f8d85;padding-top:34px}.ppr-family--prepare .ppr-media:nth-child(even){transform:translateY(54px)}
.ppr-family--act{background:#101614;color:#f8f4ea}.ppr-family--act .ppr-media--dominant{grid-column:2/13}.ppr-family--act .ppr-scene__label{writing-mode:vertical-rl;position:absolute;left:2vw;top:12vw}
.ppr-family--recognition{background:#f7f4ed}.ppr-family--recognition .ppr-media--dominant{grid-column:1/10}.ppr-family--recognition .ppr-media--co-dominant{grid-column:7/13;margin-top:-13vw;z-index:2}.ppr-family--recognition .ppr-media--supporting{grid-column:2/6;margin-top:5vw}
.ppr-crop--detail_strip .production-asset img,.ppr-crop--macro_detail_strip .production-asset img,.ppr-crop--detail_matrix_cut .production-asset img,.ppr-crop--macro_process_detail .production-asset img{height:220px;min-height:220px;object-position:center 52%}
.ppr-crop--portrait_offset .production-asset img,.ppr-crop--portrait_or_square_anchor .production-asset img{aspect-ratio:3/4}
.ppr-crop--paired_equal_a .production-asset img{object-position:35% 50%}.ppr-crop--paired_equal_b .production-asset img{object-position:65% 50%}
body[data-premium-perception-recovery="issue129"] .wp-cta{position:relative;z-index:4}body[data-premium-perception-recovery="issue129"] .wp-ending{position:relative;z-index:3}
@media(max-width:700px){
  body[data-premium-perception-recovery="issue129"] .ppr-scene{padding:64px 18px 76px}
  .ppr-scene__media{display:flex;flex-direction:column;gap:18px}.ppr-media,.ppr-media--dominant,.ppr-media--co-dominant,.ppr-media--supporting,.ppr-scene--2 .ppr-media:first-child,.ppr-scene--2 .ppr-media:nth-child(2),.ppr-scene--2 .ppr-media:nth-child(3){width:100%;margin:0;transform:none;display:block}
  .ppr-media--dominant .production-asset img{height:min(126vw,560px);min-height:380px;aspect-ratio:auto}.ppr-media--co-dominant .production-asset img{height:min(104vw,470px);min-height:330px;aspect-ratio:auto}.ppr-media--supporting .production-asset img{height:min(68vw,300px);min-height:220px;aspect-ratio:auto}
  .ppr-family--route .ppr-scene__media{transform:none}.ppr-family--route .ppr-media>*{transform:none}.ppr-family--compare .ppr-media--co-dominant:first-child,.ppr-family--compare .ppr-media--co-dominant:nth-child(2),.ppr-family--prepare .ppr-media:nth-child(even){transform:none}
  .ppr-family--act .ppr-scene__label{writing-mode:horizontal-tb;position:static}.ppr-family--recognition .ppr-media--co-dominant{margin-top:0}
  .ppr-scene--1 .ppr-media:nth-child(2){width:84%;align-self:flex-end}.ppr-scene--2 .ppr-media:nth-child(2){width:82%;align-self:flex-start}.ppr-scene--2 .ppr-media:nth-child(3){width:70%;align-self:flex-end}
}
@media(prefers-reduced-motion:reduce){.ppr-scene,.ppr-media{scroll-behavior:auto!important;animation:none!important;transition:none!important;transform:none!important}}
'''


def apply_premium_perception_recovery(
    rendered: str,
    plan: Mapping[str, Any],
    ensemble: Mapping[str, Any],
    whole_trace: Mapping[str, Any],
    asset_bindings: Mapping[str, Mapping[str, Any]],
) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Apply the Issue #129 final pixel layer without changing semantic authority."""
    before_architecture = _sha({"family": plan.get("family_id"), "topology": plan.get("topology"), "scenes": plan.get("scene_intents")})
    media_plan = compile_media_narrative_plan(plan, ensemble, whole_trace, asset_bindings)
    spine_v2 = compile_page_art_direction_spine_v2(ensemble, whole_trace, media_plan)
    family = _text(whole_trace.get("continuation_family"))
    beats = list(media_plan["beats"])
    split = max(1, (len(beats) + 1) // 2)
    first = _media_scene(beats[:split], asset_bindings, scene_index=1, family=family)
    second = _media_scene(beats[split:], asset_bindings, scene_index=2, family=family) if beats[split:] else ""

    rendered = _insert_after_hero(rendered, first)
    if second:
        rendered = _insert_before_closing(rendered, second)
    rendered = rendered.replace(
        "<body ",
        '<body data-premium-perception-recovery="issue129" data-media-narrative="true" data-spine-v2="true" ',
        1,
    )
    if "</style>" not in rendered:
        raise PremiumPerceptionRecoveryError("STYLE_ANCHOR_MISSING")
    rendered = rendered.replace("</style>", _css() + "</style>", 1)

    after_architecture = _sha({"family": plan.get("family_id"), "topology": plan.get("topology"), "scenes": plan.get("scene_intents")})
    if before_architecture != after_architecture:
        raise PremiumPerceptionRecoveryError("RECOVERY_MUTATED_COMPOSITION_AUTHORITY")
    trace = {
        "schema_version": "issue129_perceptual_variant_trace_v1",
        "continuation_family": family,
        "continuation_variant_id": _text(whole_trace.get("continuation_variant_id")),
        "spine_v2_digest": spine_v2["spine_v2_digest"],
        "media_plan_digest": _sha(media_plan),
        "media_beat_count": len(beats),
        "authored_media_scene_count": 1 + int(bool(second)),
        "dominant_or_codominant_beat_count": sum(beat["prominence_intent"] in {"dominant", "co-dominant"} for beat in beats),
        "pixel_authority": "page_art_direction_spine_v2_plus_media_narrative_plan",
        "identity_routing_used": False,
        "category_layout_routing_used": False,
        "randomness_used": False,
        "family_reopened": False,
        "composition_plan_mutated": False,
        "illustrative_media_promoted_to_proof": False,
        "human_visible_premium_declared": False,
        "aoi_v2_required": True,
        "shun_owner_html_review_required_after_aoi": True,
    }
    return rendered, media_plan, spine_v2, trace


def validate_owner_delivery_integrity(
    current_html_sha256: Mapping[str, str],
    rejected_html_sha256: Mapping[str, str],
    screenshot_source_html_sha256: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    """Fail closed when owner HTML, screenshot input or rejected baseline collides."""
    cases = sorted(current_html_sha256)
    failures: list[dict[str, str]] = []
    for case_id in cases:
        current = _text(current_html_sha256.get(case_id))
        rejected = _text(rejected_html_sha256.get(case_id))
        if not current or not rejected:
            failures.append({"case_id": case_id, "reason": "HTML_PROVENANCE_MISSING"})
            continue
        if current == rejected:
            failures.append({"case_id": case_id, "reason": "CURRENT_REJECTED_BASELINE_COLLISION"})
        widths = screenshot_source_html_sha256.get(case_id) or {}
        if not widths:
            failures.append({"case_id": case_id, "reason": "SCREENSHOT_SOURCE_HASHES_MISSING"})
        for width, source_hash in widths.items():
            if _text(source_hash) != current:
                failures.append({"case_id": case_id, "reason": f"SCREENSHOT_HTML_MISMATCH:{width}"})
    return {
        "schema_version": "issue129_owner_delivery_integrity_v1",
        "cases": cases,
        "failures": failures,
        "pass": not failures,
        "owner_html_equals_screenshot_input": not any("SCREENSHOT_HTML_MISMATCH" in row["reason"] for row in failures),
        "rejected_baseline_independently_distinct": not any(row["reason"] == "CURRENT_REJECTED_BASELINE_COLLISION" for row in failures),
    }


__all__ = [
    "MEDIA_BEAT_FIELDS",
    "MEDIA_NARRATIVE_TEMPLATES",
    "SPINE_V2_FIELDS",
    "PremiumPerceptionRecoveryError",
    "apply_premium_perception_recovery",
    "compile_media_narrative_plan",
    "compile_page_art_direction_spine_v2",
    "validate_owner_delivery_integrity",
]
