"""Issue #129 Premium Perception Recovery exact Stage A evidence.

The runner reuses the accepted Issue #124/#121/#116/#111 chain, then proves the
new owner-delivery surface independently against the exact Shun-rejected Issue
#124 artifact.  Automated gates establish integrity and mechanism execution;
they never self-declare HUMAN_VISIBLE_PASS or premium value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps
from playwright.sync_api import sync_playwright

import run_issue124_whole_page_art_direction as issue124
from lp_engine.premium_perception_recovery import (
    MEDIA_BEAT_FIELDS,
    SPINE_V2_FIELDS,
    validate_owner_delivery_integrity,
)

SAMPLES = ("SK1", "SK2", "SK3", "HS1", "HS2", "BR1", "BR2", "PI1", "PI2")
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
CONTACT_WIDTHS = (390, 1440)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_issue124(baseline: Path, out: Path) -> int:
    original = list(sys.argv)
    try:
        sys.argv = [
            sys.argv[0],
            "--baseline", str(baseline.resolve()),
            "--out", str((out / "issue124_base").resolve()),
        ]
        return int(issue124.main())
    finally:
        sys.argv = original


def _find_case_root(root: Path, *, prefer_owner: bool = True) -> Path:
    candidates = []
    pattern = "owner_html_bundle/cases/SK1/index.html" if prefer_owner else "cases/SK1/index.html"
    for hit in root.rglob("index.html"):
        normalized = hit.as_posix()
        if normalized.endswith(pattern):
            candidates.append(hit.parent.parent)
    if not candidates and prefer_owner:
        return _find_case_root(root, prefer_owner=False)
    if not candidates:
        raise RuntimeError(f"CASE_ROOT_NOT_FOUND:{root}")
    candidates.sort(key=lambda p: (len(p.parts), p.as_posix()))
    return candidates[0]


def _find_screenshot_root(root: Path) -> Path:
    candidates = []
    for hit in root.rglob("390.png"):
        if hit.parent.name == "SK1" and hit.parent.parent.name == "screenshots":
            candidates.append(hit.parent.parent)
    if not candidates:
        raise RuntimeError(f"SCREENSHOT_ROOT_NOT_FOUND:{root}")
    candidates.sort(key=lambda p: (len(p.parts), p.as_posix()))
    return candidates[0]


def _capture_exact_owner_html(case_root: Path, out: Path) -> tuple[dict[str, Any], dict[str, str], dict[str, dict[str, str]]]:
    rows: list[dict[str, Any]] = []
    current_html_sha: dict[str, str] = {}
    screenshot_source: dict[str, dict[str, str]] = {}
    screenshot_root = out / "screenshots"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id in SAMPLES:
            html_path = case_root / case_id / "index.html"
            if not html_path.is_file():
                raise RuntimeError(f"CURRENT_OWNER_HTML_MISSING:{case_id}")
            html_sha = _sha_file(html_path)
            current_html_sha[case_id] = html_sha
            screenshot_source[case_id] = {}
            uri = html_path.resolve().as_uri()
            for width in WIDTHS:
                context = browser.new_context(viewport={"width": width, "height": 900})
                page = context.new_page()
                page.goto(uri, wait_until="load")
                page.wait_for_load_state("networkidle")
                metrics = page.evaluate(
                    """
                    () => {
                      const root=document.documentElement;
                      const all=[...document.images];
                      const ppr=[...document.querySelectorAll('.ppr-media img')];
                      const rect=n=>{const r=n.getBoundingClientRect();return {w:r.width,h:r.height,top:r.top,left:r.left};};
                      const pageArea=Math.max(1,root.scrollHeight*root.clientWidth);
                      const pprArea=ppr.reduce((sum,n)=>{const r=n.getBoundingClientRect();return sum+Math.max(0,r.width)*Math.max(0,r.height);},0);
                      return {
                        recovery:document.body.dataset.premiumPerceptionRecovery||null,
                        media_narrative:document.body.dataset.mediaNarrative||null,
                        spine_v2:document.body.dataset.spineV2||null,
                        all_image_count:all.length,
                        ppr_image_count:ppr.length,
                        ppr_scene_count:document.querySelectorAll('[data-premium-authored-scene="true"]').length,
                        dominant_count:document.querySelectorAll('.ppr-media--dominant').length,
                        codominant_count:document.querySelectorAll('.ppr-media--co-dominant').length,
                        loaded:all.length>0&&all.every(i=>i.complete&&i.naturalWidth>0&&i.naturalHeight>0),
                        overflow:root.scrollWidth>root.clientWidth,
                        ppr_area_ratio:Number((pprArea/pageArea).toFixed(4)),
                        ppr_rects:ppr.map(rect),
                        mobile_reauthored:document.querySelectorAll('[data-mobile-re-art-directed="true"]').length>0,
                      };
                    }
                    """
                )
                target = screenshot_root / case_id / f"{width}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(target), full_page=True)
                screenshot_source[case_id][str(width)] = html_sha
                row = {"case_id": case_id, "width": width, "html_sha256": html_sha, "screenshot_sha256": _sha_file(target), **metrics}
                row["pass"] = bool(
                    metrics["recovery"] == "issue129"
                    and metrics["media_narrative"] == "true"
                    and metrics["spine_v2"] == "true"
                    and metrics["ppr_scene_count"] >= 1
                    and metrics["ppr_image_count"] >= 1
                    and metrics["dominant_count"] + metrics["codominant_count"] >= 1
                    and metrics["loaded"]
                    and not metrics["overflow"]
                    and (width > 430 or metrics["mobile_reauthored"])
                )
                rows.append(row)
                context.close()
        browser.close()
    failures = [row for row in rows if not row["pass"]]
    return {
        "schema_version": "issue129_browser_media_reality_execution_v1",
        "checks": len(rows),
        "failures": failures,
        "rows": rows,
        "pass": len(rows) == 81 and not failures,
        "note": "Area ratio is descriptive evidence only; no invented numeric premium threshold is used.",
    }, current_html_sha, screenshot_source


def _collect_runtime_contract(case_root: Path) -> dict[str, Any]:
    pages: dict[str, Any] = {}
    for case_id in SAMPLES:
        manifest_path = case_root / case_id / "production_manifest.json"
        if not manifest_path.is_file():
            raise RuntimeError(f"PRODUCTION_MANIFEST_MISSING:{case_id}")
        manifest = _json(manifest_path)
        media = manifest.get("media_narrative_plan") or {}
        spine = manifest.get("page_art_direction_spine_v2") or {}
        trace = manifest.get("perceptual_variant_trace") or {}
        beats = media.get("beats") or []
        beat_fields_complete = bool(beats) and all(set(MEDIA_BEAT_FIELDS).issubset(beat) for beat in beats)
        pages[case_id] = {
            "media_narrative_plan": media,
            "page_art_direction_spine_v2": spine,
            "perceptual_variant_trace": trace,
            "media_beat_fields_complete": beat_fields_complete,
            "spine_v2_fields_complete": set(SPINE_V2_FIELDS).issubset(spine),
            "family_frozen": bool(media.get("family_frozen") and spine.get("family_frozen")),
            "no_identity_category_random_routing": bool(
                media.get("identity_routing_used") is False
                and media.get("category_layout_routing_used") is False
                and media.get("randomness_used") is False
                and trace.get("identity_routing_used") is False
                and trace.get("category_layout_routing_used") is False
                and trace.get("randomness_used") is False
            ),
            "evidence_boundary_preserved": bool(
                media.get("illustrative_media_promoted_to_proof") is False
                and trace.get("illustrative_media_promoted_to_proof") is False
            ),
            "human_premium_not_self_declared": trace.get("human_visible_premium_declared") is False,
            "aoi_v2_required": trace.get("aoi_v2_required") is True,
        }
    return {"schema_version":"issue129_runtime_contract_trace_v1","pages":pages}


def _rejected_hashes(rejected_case_root: Path) -> dict[str, str]:
    result = {}
    for case_id in SAMPLES:
        path = rejected_case_root / case_id / "index.html"
        if not path.is_file():
            raise RuntimeError(f"REJECTED_BASELINE_HTML_MISSING:{case_id}")
        result[case_id] = _sha_file(path)
    return result


def _baseline_delta(
    current_screenshots: Path,
    rejected_screenshots: Path,
    current_html: dict[str, str],
    rejected_html: dict[str, str],
) -> dict[str, Any]:
    rows = []
    for case_id in SAMPLES:
        row = {
            "case_id": case_id,
            "html_distinct": current_html[case_id] != rejected_html[case_id],
            "screenshots": {},
        }
        for width in CONTACT_WIDTHS:
            cur = current_screenshots / case_id / f"{width}.png"
            old = rejected_screenshots / case_id / f"{width}.png"
            if not old.is_file():
                raise RuntimeError(f"REJECTED_SCREENSHOT_MISSING:{case_id}@{width}")
            row["screenshots"][str(width)] = {
                "current_sha256": _sha_file(cur),
                "rejected_sha256": _sha_file(old),
                "binary_distinct": _sha_file(cur) != _sha_file(old),
            }
        row["pass"] = row["html_distinct"] and all(value["binary_distinct"] for value in row["screenshots"].values())
        rows.append(row)
    return {
        "schema_version":"issue129_rejected_baseline_delta_v1",
        "rows":rows,
        "pass":all(row["pass"] for row in rows),
        "human_first_glance_delta":"PENDING_AOI_V2_BLIND_REVIEW",
        "numeric_similarity_threshold_used":False,
    }


def _pair_sheet(current: Path, rejected: Path, case_id: str, width: int, output: Path) -> None:
    old = Image.open(rejected / case_id / f"{width}.png").convert("RGB")
    new = Image.open(current / case_id / f"{width}.png").convert("RGB")
    target_w = 500 if width >= 768 else 300
    target_h = 1250
    old_preview = ImageOps.contain(old, (target_w, target_h))
    new_preview = ImageOps.contain(new, (target_w, target_h))
    canvas = Image.new("RGB", (target_w * 2 + 30, max(old_preview.height, new_preview.height) + 50), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text((6, 8), "REJECTED", fill="black")
    draw.text((target_w + 24, 8), "CURRENT", fill="black")
    canvas.paste(old_preview, (0, 42))
    canvas.paste(new_preview, (target_w + 30, 42))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, quality=91)


def _batch_contact_sheet(screenshot_root: Path, width: int, output: Path) -> None:
    tile_w, tile_h, cols = 340, 510, 3
    sheet = Image.new("RGB", (cols * tile_w, 52 + 3 * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((14, 16), f"Issue129 exact owner HTML — {width}px", fill="black")
    for i, case_id in enumerate(SAMPLES):
        image = Image.open(screenshot_root / case_id / f"{width}.png").convert("RGB")
        preview = ImageOps.contain(image, (tile_w - 12, tile_h - 52))
        x = (i % cols) * tile_w
        y = 52 + (i // cols) * tile_h
        tile = Image.new("RGB", (tile_w, tile_h - 42), "#eeeeee")
        tile.paste(preview, ((tile_w - preview.width) // 2, 0))
        sheet.paste(tile, (x, y))
        draw.text((x + 10, y + tile_h - 32), case_id, fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=91)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline111", required=True)
    parser.add_argument("--rejected124", required=True)
    parser.add_argument("--out", default="artifacts/issue129_premium_perception_recovery")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)

    if _run_issue124(Path(args.baseline111), out) != 0:
        return 1

    current_root = out / "issue124_base" / "issue121_base" / "stage_a" / "premium"
    current_cases = current_root / "cases"
    if not (current_cases / "SK1" / "index.html").is_file():
        raise RuntimeError("CURRENT_STAGE_A_ROOT_MISSING")

    rejected_root = Path(args.rejected124).resolve()
    rejected_cases = _find_case_root(rejected_root, prefer_owner=True)
    rejected_screenshots = _find_screenshot_root(rejected_root)

    browser, current_html, screenshot_source = _capture_exact_owner_html(current_cases, out)
    rejected_html = _rejected_hashes(rejected_cases)
    integrity = validate_owner_delivery_integrity(current_html, rejected_html, screenshot_source)
    runtime = _collect_runtime_contract(current_cases)
    delta = _baseline_delta(out / "screenshots", rejected_screenshots, current_html, rejected_html)

    for width in CONTACT_WIDTHS:
        _batch_contact_sheet(out / "screenshots", width, out / "contact_sheets" / f"current_{width}.jpg")
        for case_id in SAMPLES:
            _pair_sheet(out / "screenshots", rejected_screenshots, case_id, width, out / "rejected_baseline_delta" / str(width) / f"{case_id}.jpg")

    owner_bundle = out / "owner_html_bundle"
    shutil.copytree(current_cases, owner_bundle / "cases")
    asset_cache = current_root / "asset_cache"
    if asset_cache.exists():
        shutil.copytree(asset_cache, owner_bundle / "asset_cache")

    nested_manifest = _json(out / "issue124_base" / "issue124_manifest.json")
    nested_gates = nested_manifest.get("gates") or {}
    pages = runtime["pages"]
    runtime_contract_pass = all(
        row["media_beat_fields_complete"]
        and row["spine_v2_fields_complete"]
        and row["family_frozen"]
        and row["no_identity_category_random_routing"]
        and row["evidence_boundary_preserved"]
        and row["human_premium_not_self_declared"]
        and row["aoi_v2_required"]
        for row in pages.values()
    )
    media_execution_pass = browser["pass"] and all(
        any(r["case_id"] == case_id and r["ppr_image_count"] == int(pages[case_id]["media_narrative_plan"].get("beat_count") or 0) for r in browser["rows"])
        for case_id in SAMPLES
    )

    aoi_bundle = {
        "schema_version":"issue129_aoi_v2_review_bundle_v1",
        "status":"READY_FOR_AOI_V2_NOT_REVIEWED",
        "review_order":[
            "Delivery Integrity Gate",
            "Blind Single-page Premium Gate",
            "Media Reality Gate",
            "Benchmark Perceptual Fidelity Gate",
            "Rejected Baseline Delta Gate",
            "Mobile Independent Art-direction Gate",
            "Cross-sample Template Risk Gate",
            "Trace / Technical Corroboration",
        ],
        "blind_inputs":{
            "current_1440":"screenshots/<CASE>/1440.png",
            "current_390":"screenshots/<CASE>/390.png",
            "rejected_delta_1440":"rejected_baseline_delta/1440/<CASE>.jpg",
            "rejected_delta_390":"rejected_baseline_delta/390/<CASE>.jpg",
        },
        "prohibited_pass_reasons":["not a clone","variant IDs differ","81 screenshots rendered","no overflow","assets exist","automated QA Green"],
        "human_visible_pass":None,
        "premium_quality":None,
        "owner_approval":None,
    }

    gates = {
        "issue124_121_116_111_regression_chain_all_green": bool(nested_gates) and all(nested_gates.values()),
        "81_81_exact_owner_html_screenshots_render": browser["pass"] and browser["checks"] == 81,
        "owner_html_screenshot_rejected_baseline_integrity": integrity["pass"],
        "media_narrative_plan_executes_exact_mechanism_beats": media_execution_pass,
        "spine_v2_and_perceptual_runtime_contract_all_9": runtime_contract_pass,
        "rejected_baseline_current_html_and_390_1440_binary_distinct": delta["pass"],
        "aoi_v2_blind_review_bundle_prepared": aoi_bundle["status"] == "READY_FOR_AOI_V2_NOT_REVIEWED",
        "human_premium_not_self_declared": all(row["human_premium_not_self_declared"] for row in pages.values()),
    }

    integrity_manifest = {
        **integrity,
        "current_html_sha256": current_html,
        "rejected_html_sha256": rejected_html,
        "screenshot_source_html_sha256": screenshot_source,
        "current_owner_bundle":"owner_html_bundle/cases",
        "rejected_source":"independent Issue #124 Shun-rejected artifact",
    }
    manifest = {
        "schema_version":"issue129_premium_perception_recovery_evidence_v1",
        "issue":129,
        "samples":list(SAMPLES),
        "widths":list(WIDTHS),
        "screenshot_count":browser["checks"],
        "gates":gates,
        "human_boundary":{
            "HUMAN_VISIBLE_PASS":"NOT_SELF_DECLARED_PENDING_AOI_V2",
            "final_premium_quality":"NOT_SELF_DECLARED",
            "million_yen_value":"NOT_SELF_DECLARED",
            "Shun_actual_HTML_approval":"PENDING_AOI_V2_PASS",
        },
        "recovery_scope":"minimal delta over merged Issue #127 architecture + accepted Issue #124/#106 runtime",
        "remaining_limitations":[
            "Stage A still uses generic illustrative stock; it cannot substitute for client-owned staff/store/results/testimonials/credentials/pricing evidence.",
            "Automated media execution proves visible narrative responsibility and integrity, not human premium perception.",
            "Aoi v2 blind review must judge absolute single-page quality and Media Reality before clone/template risk.",
            "Shun must review the exact owner HTML only after Aoi v2 PASS.",
        ],
    }

    # Durable runtime/evidence artifacts required by Issue #127 handoff.
    _write(out / "media_narrative_plan.json", {case_id: pages[case_id]["media_narrative_plan"] for case_id in SAMPLES})
    _write(out / "page_art_direction_spine_v2.json", {case_id: pages[case_id]["page_art_direction_spine_v2"] for case_id in SAMPLES})
    _write(out / "perceptual_variant_trace.json", {case_id: pages[case_id]["perceptual_variant_trace"] for case_id in SAMPLES})
    _write(out / "owner_delivery_integrity_manifest.json", integrity_manifest)
    _write(out / "rejected_baseline_delta_manifest.json", delta)
    _write(out / "browser_media_reality_execution.json", browser)
    _write(out / "rights_evidence_regression.json", {"issue124_gates": nested_gates, "pass": bool(nested_gates) and all(nested_gates.values())})
    _write(out / "aoi_v2_review_bundle.json", aoi_bundle)
    _write(out / "issue129_manifest.json", manifest)

    print(json.dumps({
        "issue":129,
        "screenshots":browser["checks"],
        "owner_integrity":integrity["pass"],
        "rejected_baseline_delta":delta["pass"],
        "gates":gates,
        "human_boundary":manifest["human_boundary"],
    }, ensure_ascii=False, indent=2))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
