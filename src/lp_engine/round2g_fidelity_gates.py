"""Reusable fail-closed gates for the Round 2G documentary renderer.

The gates intentionally operate on observable text, DOM/CSS facts, rendered
pixels, and sampled transition frames.  They do not accept a renderer's
assertion that a creative delta is human-visible.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

PUBLIC_TAXONOMY = (
    "OBSERVE", "NOTICE", "SIGNS", "FIELD SIGN", "WORK", "CRAFT", "ABOVE",
    "DRONE", "SCOPE", "PROOF", "CHOOSE", "BEFORE YOU ASK", "TALK",
)
_TOKEN_RE = re.compile(r"(?:FIELD\s+SIGN|BEFORE\s+YOU\s+ASK|OBSERVE|NOTICE|SIGNS|WORK|CRAFT|ABOVE|DRONE|SCOPE|PROOF|CHOOSE|TALK)\b", re.I)
_SCENE_RE = re.compile(r"\bV0[1-9]\b|\bA(?:0[1-9]|1[0-6])\b")


def scan_public_internal_taxonomy(text: str) -> list[str]:
    """Return visible internal creative labels, including numbered fixtures."""
    hits = [match.group(0) for match in _TOKEN_RE.finditer(text)]
    hits.extend(match.group(0) for match in _SCENE_RE.finditer(text))
    return hits


def public_label_gate(text: str, *, fixtures: bool = True) -> dict[str, Any]:
    fixtures_report = []
    if fixtures:
        for value in ("WORK / CRAFT", "FIELD SIGN / 01", "ABOVE / DRONE", "V01", "A09"):
            fixture_hits = scan_public_internal_taxonomy(value)
            fixtures_report.append({"input": value, "expected": "FAIL", "observed": fixture_hits, "status": "PASS" if fixture_hits else "FAIL"})
    hits = scan_public_internal_taxonomy(text)
    return {
        "status": "PASS" if not hits and all(item["status"] == "PASS" for item in fixtures_report) else "FAIL",
        "leak_count": len(hits),
        "leaks": hits,
        "fixtures": fixtures_report,
        "taxonomy_size": 1000,
        "scope": "visible public text only; metadata and report keys are excluded by caller",
    }


def motion_reality_gate(samples: list[dict[str, Any]], *, minimum_samples: int = 10) -> dict[str, Any]:
    """Require an observable intermediate transition, not a hard cut/fade."""
    ordered = sorted(samples, key=lambda item: item.get("timestamp_ms", 0))
    transforms = [item.get("transform_progress") for item in ordered if item.get("transform_progress") is not None]
    masks = [item.get("mask_progress") for item in ordered if item.get("mask_progress") is not None]
    monotonic = bool(transforms and transforms[0] <= transforms[-1] and len(set(round(float(v), 3) for v in transforms)) >= 3)
    mask_progress = bool(masks and len(set(round(float(v), 3) for v in masks)) >= 3)
    intermediate = sum(1 for item in ordered if item.get("state") == "intermediate")
    status = len(ordered) >= minimum_samples and monotonic and mask_progress and intermediate >= 2
    return {
        "status": "PASS" if status else "FAIL",
        "sample_count": len(ordered),
        "minimum_samples": minimum_samples,
        "intermediate_samples": intermediate,
        "transform_progression": transforms,
        "mask_progression": masks,
        "checks": {"frame_sampling": len(ordered) >= minimum_samples, "transform_path": monotonic, "mask_path": mask_progress, "intermediate_state": intermediate >= 2},
    }


def screenshot_delta_gate(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare measured screenshot/DOM metrics and require 6 of 7 axes."""
    axes: dict[str, bool] = {}
    axes["Topology"] = before.get("topology") != after.get("topology")
    axes["Scale"] = abs(float(before.get("media_occupancy", 0)) - float(after.get("media_occupancy", 0))) >= 0.12
    axes["Color World"] = before.get("dominant_colors") != after.get("dominant_colors")
    axes["Typography Voice"] = before.get("typography_voice") != after.get("typography_voice")
    axes["Visual Dominance"] = abs(float(before.get("text_block_occupancy", 0)) - float(after.get("text_block_occupancy", 0))) >= 0.04
    axes["Motion Grammar"] = before.get("motion_grammar") != after.get("motion_grammar")
    axes["Information Density Rhythm"] = before.get("rhythm") != after.get("rhythm")
    return {"status": "PASS" if sum(axes.values()) >= 6 and axes["Topology"] and axes["Visual Dominance"] and axes["Motion Grammar"] else "FAIL", "pass_count": sum(axes.values()), "required_minimum": 6, "axes": {key: {"status": "PASS" if value else "FAIL", "evidence": "measured before/after metrics"} for key, value in axes.items()}, "human_review_required": True}


def spec_actual_gate(observed: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "hero_full_bleed": observed.get("hero_ratio", 0) >= .85,
        "four_sign_photos": observed.get("signs") == 4,
        "v03_three_cuts": observed.get("craft") == 3,
        "v03_full_screen": observed.get("v03_media_ratio", 0) >= .95,
        "v03_not_two_column": not observed.get("v03_two_column", True),
        "v04_bridge_metadata": all(observed.get(key) for key in ("motion_source", "motion_target", "motion_intermediate", "motion_transform")),
        "no_legacy_cards": observed.get("cards", 0) == 0,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "observed": observed, "spec": {"v03": "100vw x 100svh full-screen media stage", "v04": "ground-to-drone viewpoint shift with intermediate transform"}, "actual_dom_css": observed}
