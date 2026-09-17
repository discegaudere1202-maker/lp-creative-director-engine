"""Deterministic cross-LP structural signatures and comparison reports."""
from __future__ import annotations
from itertools import combinations
from typing import Any, Mapping, Sequence


def signature(ia: Sequence[Mapping[str, Any]], compositions: Sequence[Mapping[str, Any]], copy: Mapping[str, Any] | None = None, architecture: Mapping[str, Any] | None = None) -> dict[str, Any]:
    by_id = {str(item.get("section_id")): item for item in compositions}
    ordered = sorted(ia, key=lambda item: item.get("order", 0))
    architecture = architecture or {}
    return {
        "section_sequence": [item.get("section_role") for item in ordered],
        "composition_sequence": [by_id.get(item.get("section_id"), {}).get("layout_type") or by_id.get(item.get("section_id"), {}).get("composition_grammar") for item in ordered],
        "cta_sequence": [item.get("cta_role") for item in ordered],
        "photo_sequence": [by_id.get(item.get("section_id"), {}).get("image_role") for item in ordered],
        "rhythm_signature": [item.get("quiet_or_peak") for item in ordered],
        "card_group_pattern": [item.get("composition_grammar", "") for item in ordered],
        "narrative_family": architecture.get("narrative_family", ""),
        "narrative_state_sequence": architecture.get("narrative_states", []),
        "section_purpose_sequence": architecture.get("section_purposes", []),
        "section_heading_signature": architecture.get("section_naming", []),
        "visual_grammar_sequence": architecture.get("visual_progression", []),
        "cta_delta": [(item.get("stage"), item.get("action_reason")) for item in architecture.get("cta_progression_mapping", [])],
        "mobile_delta": sorted((architecture.get("mobile_redirection") or {}).keys()),
        "screenshot_peak_placement": [item.get("section_role") for item in (architecture.get("narrative_arc") or []) if item.get("section_purpose") in {"CREATE_DESIRE", "SHOW_TRANSFORMATION", "SHOW_EXPERIENCE", "ENABLE_ACTION"}],
    }


def similarity(left: Mapping[str, Any], right: Mapping[str, Any], keys: Sequence[str] | None = None) -> float:
    keys = keys or ("section_sequence", "composition_sequence", "cta_sequence", "photo_sequence", "rhythm_signature", "card_group_pattern", "narrative_family", "narrative_state_sequence", "section_purpose_sequence", "section_heading_signature", "visual_grammar_sequence", "cta_delta", "mobile_delta", "screenshot_peak_placement")
    scores = []
    for key in keys:
        raw_a, raw_b = left.get(key), right.get(key)
        a = list(raw_a) if isinstance(raw_a, (list, tuple)) else [raw_a] if raw_a not in (None, "") else []
        b = list(raw_b) if isinstance(raw_b, (list, tuple)) else [raw_b] if raw_b not in (None, "") else []
        size = max(len(a), len(b), 1)
        scores.append(sum(x == y for x, y in zip(a, b)) / size)
    return round(sum(scores) / len(scores), 4)


def pairwise(signatures: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    return {f"{a}__{b}": similarity(signatures[a], signatures[b]) for a, b in combinations(sorted(signatures), 2)}


def compare(baseline: Mapping[str, Mapping[str, Any]], new: Mapping[str, Mapping[str, Any]], *, label: str = "round1f") -> dict[str, Any]:
    structural_keys = ("section_sequence", "composition_sequence", "cta_sequence", "photo_sequence", "rhythm_signature", "card_group_pattern")
    narrative_keys = ("narrative_family", "narrative_state_sequence", "section_purpose_sequence", "section_heading_signature", "visual_grammar_sequence", "cta_delta", "mobile_delta", "screenshot_peak_placement")
    def pairs(items, keys):
        from itertools import combinations
        return {f"{a}__{b}": similarity(items[a], items[b], keys) for a, b in combinations(sorted(items), 2)}
    old_pairs, new_pairs = pairs(baseline, structural_keys), pairs(new, structural_keys)
    old_narrative, new_narrative = pairs(baseline, narrative_keys), pairs(new, narrative_keys)
    old_avg = round(sum(old_pairs.values()) / len(old_pairs), 4) if old_pairs else 0.0
    new_avg = round(sum(new_pairs.values()) / len(new_pairs), 4) if new_pairs else 0.0
    old_narrative_avg = round(sum(old_narrative.values()) / len(old_narrative), 4) if old_narrative else 0.0
    new_narrative_avg = round(sum(new_narrative.values()) / len(new_narrative), 4) if new_narrative else 0.0
    return {"schema_version": f"baseline_vs_{label}_v1", "baseline": {"signatures": baseline, "pairwise": old_pairs, "average": old_avg, "narrative_pairwise": old_narrative, "narrative_average": old_narrative_avg}, "new": {"signatures": new, "pairwise": new_pairs, "average": new_avg, "narrative_pairwise": new_narrative, "narrative_average": new_narrative_avg}, "difference": {"average": round(new_avg - old_avg, 4), "narrative_average": round(new_narrative_avg - old_narrative_avg, 4), "lower_than_baseline": new_avg < old_avg, "narrative_distinctness_checked": True}}
