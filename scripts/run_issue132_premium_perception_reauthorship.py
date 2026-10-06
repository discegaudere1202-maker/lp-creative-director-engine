"""Issue #132 exact Stage A evidence for six Aoi-RETURN sample re-authorship.

This runner regenerates the same 9 Stage A samples at 9 widths through the
accepted Issue #129 pipeline plus Issue #132. It freezes SK2/HS2/PI2 against the
accepted Issue #129 artifact, proves structural delta for the six RETURN samples,
and preserves the human boundary: technical evidence never self-declares
HUMAN_VISIBLE_PASS or premium value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from PIL import Image

import run_issue129_premium_perception_recovery as issue129
import run_issue129_premium_perception_recovery_ci as issue129_ci

SAMPLES = ("SK1", "SK2", "SK3", "HS1", "HS2", "BR1", "BR2", "PI1", "PI2")
RETURN_SAMPLES = ("SK1", "SK3", "HS1", "BR1", "BR2", "PI1")
FROZEN_PASS_SAMPLES = ("SK2", "HS2", "PI2")
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
CONTACT_WIDTHS = (390, 1440)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_current_issue129(baseline111: Path, rejected124: Path, out: Path) -> int:
    original = list(sys.argv)
    try:
        sys.argv = [
            sys.argv[0],
            "--baseline111", str(baseline111.resolve()),
            "--rejected124", str(rejected124.resolve()),
            "--out", str(out.resolve()),
        ]
        return int(issue129_ci.target.main())
    finally:
        sys.argv = original


def _pair_no_overlay(left: Path, right: Path, output: Path) -> None:
    a = Image.open(left).convert("RGB")
    b = Image.open(right).convert("RGB")
    target_w = 500 if max(a.width, b.width) >= 768 else 300
    target_h = 1400
    a.thumbnail((target_w, target_h))
    b.thumbnail((target_w, target_h))
    gap = 24
    canvas = Image.new("RGB", (target_w * 2 + gap, max(a.height, b.height)), "white")
    canvas.paste(a, ((target_w - a.width) // 2, 0))
    canvas.paste(b, (target_w + gap + (target_w - b.width) // 2, 0))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=92)


def _collect_runtime(current_cases: Path) -> dict[str, Any]:
    pages: dict[str, Any] = {}
    for case_id in SAMPLES:
        manifest = _json(current_cases / case_id / "production_manifest.json")
        trace = manifest.get("perceptual_variant_trace") or {}
        r2 = trace.get("issue132_reauthorship") or {}
        media = manifest.get("media_narrative_plan") or {}
        bindings = (manifest.get("visual_asset_library") or {}).get("bindings") or {}
        pages[case_id] = {
            "continuation_variant_id": r2.get("continuation_variant_id"),
            "issue132_reauthorship": r2,
            "media_narrative_plan": media,
            "bindings": bindings,
            "pixel_visual_authority": manifest.get("pixel_visual_authority"),
            "final_visual_authority": manifest.get("final_visual_authority"),
        }
    return {"schema_version": "issue132_runtime_trace_v1", "pages": pages}


def _freeze_proof(
    current_cases: Path,
    current_screens: Path,
    accepted_cases: Path,
    accepted_screens: Path,
) -> dict[str, Any]:
    rows = []
    for case_id in FROZEN_PASS_SAMPLES:
        current_html = current_cases / case_id / "index.html"
        accepted_html = accepted_cases / case_id / "index.html"
        screenshots = {}
        for width in WIDTHS:
            cur = current_screens / case_id / f"{width}.png"
            old = accepted_screens / case_id / f"{width}.png"
            screenshots[str(width)] = {
                "current_sha256": _sha(cur),
                "accepted_issue129_sha256": _sha(old),
                "binary_identical": _sha(cur) == _sha(old),
            }
        row = {
            "case_id": case_id,
            "current_html_sha256": _sha(current_html),
            "accepted_issue129_html_sha256": _sha(accepted_html),
            "html_byte_identical": current_html.read_bytes() == accepted_html.read_bytes(),
            "screenshots": screenshots,
        }
        row["pass"] = row["html_byte_identical"] and all(v["binary_identical"] for v in screenshots.values())
        rows.append(row)
    return {
        "schema_version": "issue132_pass_sample_freeze_v1",
        "rows": rows,
        "pass": len(rows) == 3 and all(row["pass"] for row in rows),
    }


def _issue129_delta(
    current_cases: Path,
    current_screens: Path,
    accepted_cases: Path,
    accepted_screens: Path,
    out: Path,
) -> dict[str, Any]:
    rows = []
    for case_id in RETURN_SAMPLES:
        current_html = current_cases / case_id / "index.html"
        accepted_html = accepted_cases / case_id / "index.html"
        row = {
            "case_id": case_id,
            "current_html_sha256": _sha(current_html),
            "accepted_issue129_html_sha256": _sha(accepted_html),
            "html_distinct": _sha(current_html) != _sha(accepted_html),
            "screenshots": {},
        }
        for width in CONTACT_WIDTHS:
            cur = current_screens / case_id / f"{width}.png"
            old = accepted_screens / case_id / f"{width}.png"
            row["screenshots"][str(width)] = {
                "current_sha256": _sha(cur),
                "accepted_issue129_sha256": _sha(old),
                "binary_distinct": _sha(cur) != _sha(old),
            }
            _pair_no_overlay(
                old,
                cur,
                out / "issue129_vs_r2" / str(width) / f"{case_id}.jpg",
            )
        row["pass"] = row["html_distinct"] and all(v["binary_distinct"] for v in row["screenshots"].values())
        rows.append(row)
    return {
        "schema_version": "issue132_issue129_delta_v1",
        "rows": rows,
        "pass": len(rows) == 6 and all(row["pass"] for row in rows),
        "human_first_glance_delta": "PENDING_AOI_V2_REREVIEW",
        "numeric_similarity_threshold_used": False,
    }


def _runtime_gates(runtime: dict[str, Any]) -> dict[str, Any]:
    pages = runtime["pages"]
    rows = []
    for case_id in SAMPLES:
        r2 = pages[case_id]["issue132_reauthorship"]
        if case_id in RETURN_SAMPLES:
            passed = bool(
                r2.get("applied") is True
                and r2.get("macro_silhouette_reauthored") is True
                and r2.get("typography_media_material_coauthored") is True
                and r2.get("cta_ending_reauthored") is True
                and r2.get("mobile_390_independent_recomposition") is True
                and r2.get("media_is_layout_authority") is True
                and r2.get("html_byte_mutated") is True
                and r2.get("family_reopened") is False
                and r2.get("composition_plan_mutated") is False
                and r2.get("identity_routing_used") is False
                and r2.get("category_layout_routing_used") is False
                and r2.get("randomness_used") is False
                and r2.get("arbitrary_image_count_inflation_used") is False
                and r2.get("illustrative_media_promoted_to_proof") is False
                and r2.get("human_visible_pass_declared") is False
                and r2.get("aoi_rereview_required") is True
            )
        else:
            passed = bool(
                r2.get("applied") is False
                and r2.get("pass_sample_freeze_variant") is True
                and r2.get("html_byte_mutated") is False
                and r2.get("family_reopened") is False
                and r2.get("composition_plan_mutated") is False
                and r2.get("identity_routing_used") is False
                and r2.get("category_layout_routing_used") is False
                and r2.get("randomness_used") is False
                and r2.get("human_visible_pass_declared") is False
            )
        rows.append({"case_id": case_id, "pass": passed, "trace": r2})
    return {
        "schema_version": "issue132_runtime_gate_v1",
        "rows": rows,
        "pass": len(rows) == 9 and all(row["pass"] for row in rows),
    }


def _pi1_media_relevance(runtime: dict[str, Any]) -> dict[str, Any]:
    page = runtime["pages"]["PI1"]
    r2 = page["issue132_reauthorship"]
    reselection = r2.get("media_reselection") or {}
    hero = (page.get("bindings") or {}).get("hero") or {}
    trace = hero.get("trace") or {}
    conditions = trace.get("required_content_conditions") or {}
    source_url = str(trace.get("source_url") or "").lower()
    rights = str((reselection.get("selected_source_rights_identity") or {}).get("rights_gate") or "")
    checks = {
        "reselection_applied": reselection.get("applied") is True,
        "rebound_media_beats_positive": int(reselection.get("rebound_media_beats") or 0) > 0,
        "legacy_source_binding_preserved": reselection.get("legacy_source_binding_preserved") is True,
        "decorative_legacy_slot_hidden": reselection.get("decorative_legacy_slot_hidden_by_profile") is True,
        "client_evidence_not_promoted": reselection.get("client_evidence_promoted") is False,
        "selected_rights_gate_pass": rights.startswith("RIGHTS_PASS"),
        "selected_media_is_illustrative": reselection.get("selected_evidence_status") == "GENERIC_ILLUSTRATIVE_STOCK",
        "hero_content_is_studio_context": conditions.get("content_class") == "studio_interior_generic",
        "industry_is_pilates": trace.get("industry") == "pilates_fitness",
        "category_is_pilates_studio": trace.get("business_category") == "pilates_studio",
        "source_url_reads_as_pilates": "pilates" in source_url,
    }
    return {
        "schema_version": "issue132_pi1_media_relevance_v1",
        "checks": checks,
        "selected_asset_id": reselection.get("selected_asset_id"),
        "selected_source_url": trace.get("source_url"),
        "selected_content_class": conditions.get("content_class"),
        "pass": all(checks.values()),
        "note": "This proves rights-safe Pilates/studio relevance metadata and reselection behavior; Aoi must still judge perceptual relevance in pixels.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline111", required=True)
    parser.add_argument("--rejected124", required=True)
    parser.add_argument("--accepted129", required=True)
    parser.add_argument("--out", default="artifacts/issue132_premium_perception_reauthorship")
    args = parser.parse_args()

    out = Path(args.out).resolve()
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)

    nested = out / "issue129_current"
    if _run_current_issue129(Path(args.baseline111), Path(args.rejected124), nested) != 0:
        return 1

    current_cases = nested / "issue124_base" / "issue121_base" / "stage_a" / "premium" / "cases"
    current_screens = nested / "screenshots"
    accepted_root = Path(args.accepted129).resolve()
    accepted_cases = issue129._find_case_root(accepted_root, prefer_owner=True)
    accepted_screens = issue129._find_screenshot_root(accepted_root)

    runtime = _collect_runtime(current_cases)
    runtime_gate = _runtime_gates(runtime)
    freeze = _freeze_proof(current_cases, current_screens, accepted_cases, accepted_screens)
    issue129_delta = _issue129_delta(current_cases, current_screens, accepted_cases, accepted_screens, out)
    pi1 = _pi1_media_relevance(runtime)

    nested_manifest = _json(nested / "issue129_manifest.json")
    nested_gates = nested_manifest.get("gates") or {}
    nested_integrity = _json(nested / "owner_delivery_integrity_manifest.json")
    nested_rights = _json(nested / "rights_evidence_regression.json")
    browser = _json(nested / "browser_media_reality_execution.json")

    mobile_rows = []
    for case_id in RETURN_SAMPLES:
        page_rows = [row for row in browser.get("rows", []) if row.get("case_id") == case_id and int(row.get("width") or 0) <= 430]
        r2 = runtime["pages"][case_id]["issue132_reauthorship"]
        mobile_rows.append({
            "case_id": case_id,
            "widths": [row.get("width") for row in page_rows],
            "all_loaded": bool(page_rows) and all(row.get("loaded") and not row.get("overflow") for row in page_rows),
            "r2_390_independent_recomposition": r2.get("mobile_390_independent_recomposition") is True,
            "screenshots_present": all((current_screens / case_id / f"{width}.png").is_file() for width in (320, 360, 375, 390, 430)),
        })
    mobile = {
        "schema_version": "issue132_mobile_authored_evidence_v1",
        "rows": mobile_rows,
        "pass": len(mobile_rows) == 6 and all(row["all_loaded"] and row["r2_390_independent_recomposition"] and row["screenshots_present"] for row in mobile_rows),
    }

    aoi_bundle = {
        "schema_version": "issue132_aoi_v2_rereview_bundle_v1",
        "status": "READY_FOR_AOI_V2_REREVIEW_NOT_REVIEWED",
        "review_scope": {
            "frozen_pass": list(FROZEN_PASS_SAMPLES),
            "corrected_return": list(RETURN_SAMPLES),
        },
        "mandatory_review_order": [
            "Delivery Integrity",
            "Blind Single-page Premium",
            "Media Reality",
            "Benchmark Perceptual Fidelity",
            "Latest Shun-rejected Baseline Delta",
            "Issue129-to-R2 Delta for six RETURN samples",
            "Mobile Independent Art-direction",
            "Cross-sample Template Risk",
            "Trace / Technical Corroboration",
        ],
        "blind_inputs": {
            "current_1440": "issue129_current/screenshots/<CASE>/1440.png",
            "current_390": "issue129_current/screenshots/<CASE>/390.png",
            "shun_rejected_delta_1440": "issue129_current/rejected_baseline_delta/1440/<CASE>.jpg",
            "shun_rejected_delta_390": "issue129_current/rejected_baseline_delta/390/<CASE>.jpg",
            "issue129_vs_r2_return_1440": "issue129_vs_r2/1440/<RETURN_CASE>.jpg",
            "issue129_vs_r2_return_390": "issue129_vs_r2/390/<RETURN_CASE>.jpg",
        },
        "prohibited_pass_reasons": [
            "not a clone", "variant IDs differ", "81 screenshots exist", "no overflow",
            "images increased", "automated QA Green", "binary delta alone",
        ],
        "human_visible_pass": None,
        "premium_quality": None,
        "million_yen_value": None,
        "owner_approval": None,
    }

    gates = {
        "issue129_and_legacy_regression_chain_green": bool(nested_gates) and all(nested_gates.values()),
        "81_81_exact_owner_html_screenshots_render": browser.get("pass") is True and browser.get("checks") == 81,
        "owner_html_screenshot_integrity": nested_integrity.get("pass") is True,
        "six_return_variants_structurally_reauthored": runtime_gate["pass"],
        "three_pass_samples_issue129_byte_and_pixel_frozen": freeze["pass"],
        "six_return_samples_distinct_from_accepted_issue129_at_1440_390": issue129_delta["pass"],
        "latest_shun_rejected_baseline_delta_preserved": (_json(nested / "rejected_baseline_delta_manifest.json")).get("pass") is True,
        "pi1_rights_safe_pilates_media_relevance_proof": pi1["pass"],
        "mobile_320_430_authored_evidence": mobile["pass"],
        "rights_evidence_regression": nested_rights.get("pass") is True,
        "aoi_v2_rereview_bundle_prepared": aoi_bundle["status"] == "READY_FOR_AOI_V2_REREVIEW_NOT_REVIEWED",
        "human_premium_not_self_declared": all((runtime["pages"][case_id]["issue132_reauthorship"] or {}).get("human_visible_pass_declared") is False for case_id in SAMPLES),
    }

    manifest = {
        "schema_version": "issue132_premium_perception_reauthorship_evidence_v1",
        "issue": 132,
        "source_human_review": "Issue #131 Aoi Premium Perception Blind Human Reality Review v2",
        "samples": list(SAMPLES),
        "return_samples": list(RETURN_SAMPLES),
        "frozen_pass_samples": list(FROZEN_PASS_SAMPLES),
        "widths": list(WIDTHS),
        "screenshot_count": browser.get("checks"),
        "gates": gates,
        "human_boundary": {
            "HUMAN_VISIBLE_PASS": "NOT_SELF_DECLARED_PENDING_AOI_V2_REREVIEW",
            "final_premium_quality": "NOT_SELF_DECLARED",
            "million_yen_value": "NOT_SELF_DECLARED",
            "Shun_actual_HTML_approval": "PENDING_9_OF_9_AOI_BATCH_PASS",
        },
    }

    _write(out / "issue132_runtime_trace.json", runtime)
    _write(out / "issue132_runtime_gate.json", runtime_gate)
    _write(out / "pass_sample_freeze_manifest.json", freeze)
    _write(out / "issue129_vs_r2_delta_manifest.json", issue129_delta)
    _write(out / "pi1_media_relevance_proof.json", pi1)
    _write(out / "mobile_authored_evidence.json", mobile)
    _write(out / "rights_evidence_regression.json", nested_rights)
    _write(out / "owner_delivery_integrity_manifest.json", nested_integrity)
    _write(out / "aoi_v2_rereview_bundle.json", aoi_bundle)
    _write(out / "issue132_manifest.json", manifest)

    print(json.dumps({"issue": 132, "screenshots": browser.get("checks"), "gates": gates, "human_boundary": manifest["human_boundary"]}, ensure_ascii=False, indent=2))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
