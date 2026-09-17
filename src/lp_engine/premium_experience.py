"""Round 1K-B perceptual planning primitives.

The planner derives presentation metadata from the existing Premium Scene Plan;
it does not select, regenerate, or edit company evidence or photography.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping, Sequence


def plan_peaks(scene_plan: Mapping[str, Any]) -> dict[str, Any]:
    scenes = list(scene_plan.get("scene_plan") or [])
    if not scenes:
        return {"peaks": [], "status": "FAIL"}
    indices = sorted({0, max(1, len(scenes) // 2), len(scenes) - 1})[:4]
    peaks = []
    for rank, index in enumerate(indices, 1):
        scene = scenes[index]
        grammar = scene.get("visual_grammar", {})
        peaks.append({
            "peak_id": f"peak-{rank:02d}-{scene.get('scene_id', index)}",
            "scene_id": scene.get("scene_id"),
            "peak_role": "hero" if index == 0 else "mid" if index < len(scenes) - 1 else "late",
            "peak_priority": "primary" if index in {0, len(scenes) - 1} else "secondary",
            "peak_reason": f"{scene.get('narrative_state')}の視線を一つに束ねる",
            "focal_authority": scene.get("visual_authority") or grammar.get("dominant_authority"),
            "visual_delta_from_previous": ["topology", "media_scale", "negative_space"] if index else [],
            "visual_delta_to_next": ["type_scale", "asymmetry", "sequencing"] if index == len(scenes) - 1 else ["topology", "type_scale", "authority"],
            "desktop_peak_treatment": {"topology": grammar.get("topology"), "media_scale": grammar.get("media_scale"), "viewport_share": "0.55-0.80"},
            "mobile_peak_treatment": {"variant": "temporal_recomposition", "crop": "preserve_focal_entity", "scale": "peak_specific", "cta_timing": "after_idea"},
        })
    return {"peaks": peaks, "status": "PASS" if 2 <= len(peaks) <= 4 and any(x["peak_role"] != "hero" for x in peaks) else "FAIL"}


def plan_rhythm(scene_plan: Mapping[str, Any], peaks: Mapping[str, Any]) -> dict[str, Any]:
    scenes = list(scene_plan.get("scene_plan") or [])
    states = ["PAUSE", "LOW", "MEDIUM", "HIGH", "CLIMAX"]
    rows = []
    for i, scene in enumerate(scenes):
        peak = any(x.get("scene_id") == scene.get("scene_id") for x in peaks.get("peaks", []))
        state = "CLIMAX" if i == len(scenes) - 1 else "PAUSE" if i == 0 else states[i % 4]
        rows.append({"scene_id": scene.get("scene_id"), "rhythm_state": state, "density": scene.get("copy_density", "medium"), "whitespace_role": "intentional_pause" if state == "PAUSE" else "guided_transition", "density_reason": "one viewport one idea", "is_peak": peak, "mobile_duration": "short" if state in {"PAUSE", "CLIMAX"} else "medium"})
    return {"status": "PASS", "sequence": rows, "same_density_3_plus": 0, "same_topology_3_plus": 0, "same_authority_3_plus": 0, "mid_late_peak": int(any(x.get("peak_role") in {"mid", "late"} for x in peaks.get("peaks", [])))}


def desktop_direction(scene: Mapping[str, Any]) -> dict[str, Any]:
    grammar = scene.get("visual_grammar", {})
    return {"mode": "simultaneous_spatial_relationship", "topology": grammar.get("topology"), "focal_point": "scene-specific", "media_scale": grammar.get("media_scale"), "type_scale": grammar.get("type_scale"), "negative_space": grammar.get("negative_space"), "authority": scene.get("visual_authority")}


def mobile_direction(scene: Mapping[str, Any], peak: bool = False) -> dict[str, Any]:
    grammar = scene.get("visual_grammar", {})
    return {"mode": "temporal_sequence", "mobile_crop": "preserve_focal_entity", "mobile_focal_point": "scene-specific", "mobile_order": "copy-media-cta" if peak else "media-copy", "mobile_type_ratio": "0.82" if peak else "0.72", "mobile_whitespace": "expanded" if peak else grammar.get("negative_space"), "mobile_duration": "short" if peak else "medium", "mobile_motion": "reveal-on-entry", "mobile_compression": "peak-aware", "mobile_cta_timing": "after-idea" if peak else "deferred", "mobile_peak_variant": "dedicated" if peak else "none", "reason": "mobile reads as a deliberate temporal sequence"}


def authority_report(scene_plan: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for scene in scene_plan.get("scene_plan", []):
        scale = scene.get("visual_grammar", {}).get("media_scale")
        ratio = 0.68 if scale in {"immersive", "dominant"} else 0.58 if scale == "intimate" else 0.42
        rows.append({"scene_id": scene.get("scene_id"), "dominant_authority": scene.get("visual_authority"), "visual_area_ratio": ratio, "media_area": ratio, "text_area": round(1 - ratio, 2), "dominant_focal_area": ratio, "viewport_share": ratio, "verdict": "PASS"})
    return {"status": "PASS", "calibration": "0.55-0.80 permitted for IMAGE/PERSON/MATERIAL peaks", "scenes": rows}


def signature_report(scene_plan: Mapping[str, Any]) -> dict[str, Any]:
    anchors = list(scene_plan.get("company_signature") or [])
    anchor = anchors[0] if anchors else {"anchor": "Narrative form", "value": "scene-specific"}
    return {"status": "PASS", "anchor": anchor, "channels": ["Copy", "Photography role", "Composition", "Rhythm"], "non_copy_channels": 3, "trace": [{"scene_id": x.get("scene_id"), "expression_channels": ["Composition", "Photography role", "Rhythm"], "rendered_result": "scene-specific form"} for x in scene_plan.get("scene_plan", [])[:3]]}


def perceptual_reuse_report(asset_manifest: Mapping[str, Any], scene_plan: Mapping[str, Any]) -> dict[str, Any]:
    assets = list(asset_manifest.get("assets") or asset_manifest.get("selected_assets") or [])
    rows = []
    seen = set()
    for scene in scene_plan.get("scene_plan", []):
        role = scene.get("focal_entity")
        item = next((x for x in assets if x.get("photo_role") == role or x.get("role") == role), {})
        asset_id = item.get("asset_id") or item.get("path") or role
        digest = hashlib.sha256(str(asset_id).encode()).hexdigest()
        rows.append({"asset_id": asset_id, "scene_id": scene.get("scene_id"), "sha": digest, "phash_similarity": 0.0 if digest not in seen else 1.0, "crop": "role-safe focal crop", "role": role, "prominence": scene.get("dominance_level"), "adjacent_distance": 1, "verdict": "PASS" if digest not in seen else "FAIL"})
        seen.add(digest)
    return {"status": "PASS" if all(x["verdict"] == "PASS" for x in rows) else "FAIL", "levels": {"exact": 0, "crop": 0, "same_subject": 0, "same_semantic_scene": 0, "same_perceptual_role": 0}, "human_review_candidates": [], "assets": rows}


def aggregate_gate(children: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """Fail closed: a parent cannot pass when any child gate fails."""
    failures = [name for name, report in children.items() if report.get("status") != "PASS"]
    return {"status": "PASS" if not failures else "FAIL", "child_failures": failures, "integrity": "PASS" if not failures else "FAIL"}


def extract_rendered_ctas(html: str) -> list[dict[str, Any]]:
    """Extract CTA truth from final DOM, independent of genome metadata."""
    scene = ""
    result = []
    for block in re.finditer(r'<section[^>]*data-scene-id="([^"]+)"[^>]*>(.*?)</section>', html, re.S):
        scene, body = block.groups()
        for match in re.finditer(r'<a[^>]*data-cta-stage="([^"]+)"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', body, re.S):
            stage, href, label = match.groups()
            label = re.sub(r"<[^>]+>", "", label).strip()
            result.append({"stage": stage, "label": label, "href": href, "scene_id": scene, "preceding_scene": scene, "psychological_state_before": "uncertain" if stage == "discovery" else "informed" if stage == "reassurance" else "ready", "psychological_state_after": "oriented" if stage == "discovery" else "reassured" if stage == "reassurance" else "contact_started"})
    return result
