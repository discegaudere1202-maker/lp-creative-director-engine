"""Deterministic cross-LP structural signatures and comparison reports."""
from __future__ import annotations
from itertools import combinations
from typing import Any, Mapping, Sequence


def signature(ia: Sequence[Mapping[str, Any]], compositions: Sequence[Mapping[str, Any]], copy: Mapping[str, Any] | None = None) -> dict[str, Any]:
    by_id = {str(item.get("section_id")): item for item in compositions}
    ordered = sorted(ia, key=lambda item: item.get("order", 0))
    return {
        "section_sequence": [item.get("section_role") for item in ordered],
        "composition_sequence": [by_id.get(item.get("section_id"), {}).get("layout_type") or by_id.get(item.get("section_id"), {}).get("composition_grammar") for item in ordered],
        "cta_sequence": [item.get("cta_role") for item in ordered],
        "photo_sequence": [by_id.get(item.get("section_id"), {}).get("image_role") for item in ordered],
        "rhythm_signature": [item.get("quiet_or_peak") for item in ordered],
        "card_group_pattern": [item.get("composition_grammar", "") for item in ordered],
    }


def similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    keys = ("section_sequence", "composition_sequence", "cta_sequence", "photo_sequence", "rhythm_signature", "card_group_pattern")
    scores = []
    for key in keys:
        a, b = list(left.get(key) or []), list(right.get(key) or [])
        size = max(len(a), len(b), 1)
        scores.append(sum(x == y for x, y in zip(a, b)) / size)
    return round(sum(scores) / len(scores), 4)


def pairwise(signatures: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    return {f"{a}__{b}": similarity(signatures[a], signatures[b]) for a, b in combinations(sorted(signatures), 2)}


def compare(baseline: Mapping[str, Mapping[str, Any]], new: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    old_pairs, new_pairs = pairwise(baseline), pairwise(new)
    old_avg = round(sum(old_pairs.values()) / len(old_pairs), 4) if old_pairs else 0.0
    new_avg = round(sum(new_pairs.values()) / len(new_pairs), 4) if new_pairs else 0.0
    return {"schema_version": "baseline_vs_round1f_v1", "baseline": {"signatures": baseline, "pairwise": old_pairs, "average": old_avg}, "new": {"signatures": new, "pairwise": new_pairs, "average": new_avg}, "difference": {"average": round(new_avg - old_avg, 4), "lower_than_baseline": new_avg < old_avg}}
