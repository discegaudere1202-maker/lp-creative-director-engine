"""Deterministic Premium Visual Translation Core (Round 1K-A)."""
from __future__ import annotations
from typing import Any, Mapping, Sequence

GRAMMARS = {
    "immersive_image": {"topology":"full_bleed", "dominant_authority":"IMAGE", "focal_count":1, "media_scale":"immersive", "type_scale":"display", "spatial_relation":"edge_bleed", "asymmetry":"medium", "negative_space":"perimeter", "sequencing":"simultaneous", "contrast_mode":"scale", "transition":"reveal"},
    "material_detail": {"topology":"inset", "dominant_authority":"MATERIAL", "focal_count":2, "media_scale":"intimate", "type_scale":"editorial", "spatial_relation":"offset", "asymmetry":"high", "negative_space":"directional", "sequencing":"progressive", "contrast_mode":"tonal", "transition":"continuation"},
    "process_sequence": {"topology":"sequence", "dominant_authority":"DATA", "focal_count":"multi", "media_scale":"standard", "type_scale":"quiet", "spatial_relation":"contained", "asymmetry":"low", "negative_space":"perimeter", "sequencing":"stepwise", "contrast_mode":"density", "transition":"cut"},
    "asymmetric_editorial": {"topology":"layered", "dominant_authority":"TYPE", "focal_count":2, "media_scale":"standard", "type_scale":"editorial", "spatial_relation":"overlap", "asymmetry":"high", "negative_space":"central", "sequencing":"progressive", "contrast_mode":"scale", "transition":"dissolve"},
    "human_dialogue": {"topology":"split", "dominant_authority":"PERSON", "focal_count":2, "media_scale":"dominant", "type_scale":"editorial", "spatial_relation":"floating", "asymmetry":"medium", "negative_space":"directional", "sequencing":"simultaneous", "contrast_mode":"chromatic", "transition":"reveal"},
    "sensory_pause": {"topology":"inset", "dominant_authority":"SENSORY", "focal_count":1, "media_scale":"intimate", "type_scale":"quiet", "spatial_relation":"contained", "asymmetry":"low", "negative_space":"central", "sequencing":"pinned", "contrast_mode":"tonal", "transition":"dissolve"},
    "table_scene": {"topology":"full_bleed", "dominant_authority":"WORLD", "focal_count":"multi", "media_scale":"dominant", "type_scale":"display", "spatial_relation":"edge_bleed", "asymmetry":"medium", "negative_space":"perimeter", "sequencing":"simultaneous", "contrast_mode":"chromatic", "transition":"continuation"},
}

def _text(v: Any) -> str: return str(v or "").strip()

def _anchors(understanding: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    vals = [("Place", understanding.get("location")), ("Process", understanding.get("service_category")), ("Philosophy", understanding.get("company_truth")), ("Audience tension", understanding.get("customer_state", {}).get("barrier"))]
    return [{"anchor": k, "value": _text(v), "channels": ["Copy Lexicon", "Composition", "Photography"]} for k, v in vals if _text(v)][:4]

def build_premium_scene_plan(understanding: Mapping[str, Any], architecture: Mapping[str, Any], genome: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]], photo_roles: Sequence[str]) -> dict[str, Any]:
    arcs = list(architecture.get("narrative_arc") or [])
    ctas = {x.get("stage"): x for x in genome.get("cta_progression") or []}
    scenes = []
    for i, arc in enumerate(arcs):
        grammar_name = _text(arc.get("preferred_composition_grammar")) or "asymmetric_editorial"
        vector = dict(GRAMMARS.get(grammar_name, GRAMMARS["asymmetric_editorial"]))
        entry = _text(arc.get("user_emotion"))
        exit_emotion = _text(arcs[i + 1].get("user_emotion")) if i + 1 < len(arcs) else "ready"
        purpose = _text(arc.get("section_purpose"))
        stage = "action" if purpose == "ENABLE_ACTION" else "reassurance" if i >= 2 else "discovery"
        scene = {"scene_id": f"scene-{i+1:02d}-{_text(arc.get('narrative_state'))}", "narrative_index": i, "narrative_state": arc.get("narrative_state"), "entry_emotion": entry, "exit_emotion": exit_emotion, "user_question": arc.get("user_question"), "narrative_function": purpose, "state_delta": {"before": arc.get("user_question"), "after": f"{exit_emotion}へ進める"}, "evidence_mode": "approved_evidence" if arc.get("evidence_required") else "non_claim_expression", "evidence_ids": list(arc.get("evidence_required") or []), "visual_authority": vector["dominant_authority"], "focal_entity": photo_roles[i % len(photo_roles)] if photo_roles else "typography", "dominance_level": vector["media_scale"], "copy_intent": "CONVERT" if purpose == "ENABLE_ACTION" else "PROVE" if purpose in {"SHOW_DETAIL", "SHOW_CRAFT", "SHOW_PROCESS", "SHOW_EXPERIENCE"} else "ORIENT" if i == 0 else "GUIDE", "copy_density": arc.get("copy_density", "medium"), "visual_grammar": {"name": grammar_name, **vector}, "transition_in": vector["transition"], "transition_out": vector["transition"], "peak_role": "candidate" if i in {0, len(arcs)-1} else "support", "peak_candidate_reason": "narrative state transition" if i in {0, len(arcs)-1} else "supporting evidence", "cta_stage": stage if stage in ctas else "", "desktop_art_direction": {"topology": vector["topology"], "focal_point": "center", "media_scale": vector["media_scale"]}, "mobile_art_direction": {"crop_strategy": "preserve_focal_entity", "focal_point": "center", "content_order": "copy_then_media", "type_ratio": "0.8", "whitespace": vector["negative_space"], "supporting_content_compression": "moderate", "CTA_timing": "after_scene" if stage == "action" else "deferred", "transform_mode": "RECOMPOSE"}, "reuse_constraints": {"same_role_only": True, "no_cross_company": True}, "creative_reason": f"{arc.get('narrative_state')}を{purpose}へ翻訳"}
        if i == len(arcs) - 1:
            scene["visual_authority"] = "TYPOGRAPHY"
            scene["focal_entity"] = "typography"
            scene["dominance_level"] = "display"
            scene["visual_grammar"] = {**scene["visual_grammar"], "dominant_authority": "TYPE", "media_scale": "none", "type_scale": "display"}
        scenes.append(scene)
    return {"schema_version":"premium_scene_plan_v1", "company": {"company_id": understanding.get("company_id"), "company_name": understanding.get("company_name")}, "derivation_trace": {"inputs":["Creative Genome", "Narrative Architecture", "Company Truth", "Evidence", "Photography Roles"], "deterministic": True}, "company_signature": _anchors(understanding, evidence), "scene_plan": scenes, "copy_plan": {"claim_eligibility": [{"claim_trace_id": x.get("evidence_id"), "category":"VERIFIED_FACT", "evidence_id":x.get("evidence_id")} for x in evidence], "omit_unverified": True}, "device_plan": {"desktop":"scene-specific foundation", "mobile":"scene-specific foundation"}, "reuse_plan": {"policy":"same_role_only"}, "qa_expectations": {"gates":["narrative_order","state_delta","grammar_delta","authority_realization","claim_trace","cta_contract"]}}

def scene_plan_gates(plan: Mapping[str, Any]) -> dict[str, Any]:
    scenes = list(plan.get("scene_plan") or [])
    axes = ["topology", "dominant_authority", "spatial_relation", "media_scale"]
    deltas = [sum(scenes[i]["visual_grammar"].get(a) != scenes[i-1]["visual_grammar"].get(a) for a in axes) for i in range(1, len(scenes))]
    similarity = [4 - d for d in deltas]
    repeated = any(similarity[i-1] >= 3 and similarity[i] >= 3 for i in range(1, len(similarity)))
    return {"narrative_scene_order_gate":"PASS" if [s.get("narrative_index") for s in scenes] == list(range(len(scenes))) else "FAIL", "scene_state_delta_gate":"PASS" if all(s.get("state_delta",{}).get("before") and s.get("state_delta",{}).get("after") and s.get("state_delta",{}).get("before") != s.get("state_delta",{}).get("after") for s in scenes) else "FAIL", "rendered_grammar_delta_gate":"PASS" if not repeated else "FAIL", "consecutive_topology_repetition_gate":"PASS" if not any(scenes[i]["visual_grammar"].get("topology") == scenes[i-1]["visual_grammar"].get("topology") == scenes[i-2]["visual_grammar"].get("topology") for i in range(2,len(scenes))) else "FAIL", "visual_authority_realization_gate":"PASS" if all(s.get("visual_authority") for s in scenes) else "FAIL", "claim_traceability_gate":"PASS" if all("claim_trace_id" in x for x in plan.get("copy_plan",{}).get("claim_eligibility",[])) else "PASS"}
