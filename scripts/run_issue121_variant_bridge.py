"""Issue #121 Stage A research-pattern -> Production Variant evidence runner.

The accepted Issue #116 runner remains the rights/provenance/81-screen
regression harness.  This runner executes it through the Issue #121 renderer
cutover, then verifies the direct research pattern -> selected Production
Variant -> renderer implementation -> screenshot chain without claiming human
visible approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps
from playwright.sync_api import sync_playwright

import run_issue116_premium_uplift as issue116
from lp_engine.production_variant_bridge import VARIANT_REGISTRY, registry_manifest

ROOT = Path(__file__).resolve().parents[1]
STARTING_MAIN = "1fdede758bb7f4710b2f4aee51df7e9309968ca0"
SAMPLES = ("SK1", "SK2", "SK3", "HS1", "HS2", "BR1", "BR2", "PI1", "PI2")
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
CONTACT_WIDTHS = (390, 1440)
EXPECTED_HERO_VARIANTS = {
    "PV-HERO-RECOGNITION-FIELD-v1",
    "PV-HERO-EVIDENCE-ANCHOR-v1",
    "PV-HERO-GUIDED-ROUTE-CANVAS-v1",
}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_issue116(baseline: Path, out: Path) -> int:
    original = list(sys.argv)
    try:
        sys.argv = [
            sys.argv[0],
            "--baseline", str(baseline.resolve()),
            "--out", str((out / "stage_a").resolve()),
        ]
        return int(issue116.main())
    finally:
        sys.argv = original


def _top_preview(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    crop_h = min(image.height, max(1200, int(image.width * 1.45)))
    return ImageOps.contain(image.crop((0, 0, image.width, crop_h)), size)


def _contact_sheet(screenshot_root: Path, width: int, output: Path) -> None:
    tile_w, tile_h = 340, 400
    cols = 3
    rows = 3
    sheet = Image.new("RGB", (cols * tile_w, 54 + rows * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((14, 17), f"Issue121 Stage A variant-faithful pages — {width}px", fill="black")
    for index, case_id in enumerate(SAMPLES):
        source = screenshot_root / case_id / f"{width}.png"
        preview = _top_preview(source, (tile_w - 12, tile_h - 58))
        x = (index % cols) * tile_w
        y = 54 + (index // cols) * tile_h
        tile = Image.new("RGB", (tile_w, tile_h - 44), "#efefef")
        tile.paste(preview, ((tile_w - preview.width) // 2, ((tile_h - 44) - preview.height) // 2))
        sheet.paste(tile, (x, y))
        draw.text((x + 10, y + tile_h - 34), case_id, fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=91)


def _manifest_rows(premium_root: Path, screenshot_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pages: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for case_id in SAMPLES:
        manifest = _json(premium_root / "cases" / case_id / "production_manifest.json")
        bridge = manifest.get("research_to_production_bridge")
        if not bridge:
            raise RuntimeError(f"Issue121 bridge trace missing: {case_id}")
        if manifest.get("final_visual_authority") != "production_variant_dispatch":
            raise RuntimeError(f"Variant dispatch is not final authority: {case_id}")
        if manifest.get("silent_generic_variant_fallback") is not False:
            raise RuntimeError(f"Silent generic fallback not closed: {case_id}")
        scene_rows = [bridge["hero"], *bridge["scenes"], bridge["cta"], bridge["ending"]]
        for scene in scene_rows:
            selected = scene["selected_production_variant_id"]
            if selected not in VARIANT_REGISTRY:
                raise RuntimeError(f"Unknown selected Production Variant: {case_id}:{selected}")
            if scene["renderer_implementation_identity"] != VARIANT_REGISTRY[selected]["renderer_implementation_identity"]:
                raise RuntimeError(f"Renderer identity mismatch: {case_id}:{selected}")
            if not scene["source_pattern_ids"]:
                raise RuntimeError(f"Research pattern trace missing: {case_id}:{selected}")
            responsive = scene.get("responsive_variant_transform") or {}
            if {int(width) for width in responsive} != set(WIDTHS):
                raise RuntimeError(f"Responsive transform incomplete: {case_id}:{selected}")
            screenshot_verification = []
            for width in WIDTHS:
                screenshot = screenshot_root / case_id / f"{width}.png"
                screenshot_verification.append({
                    "width": width,
                    "artifact_path": f"stage_a/premium/screenshots/{case_id}/{width}.png",
                    "screenshot_sha256": _sha_file(screenshot),
                    "mechanism_fidelity": "AUTOMATED_STRUCTURE_VERIFIED_PENDING_AOI",
                    "whole_page_coherence": "NOT_REVIEWED_PENDING_AOI",
                    "reviewer": "Rin automated prerequisite",
                })
            row = dict(scene)
            row["sample_id"] = case_id
            row["screenshot_verification"] = screenshot_verification
            rows.append(row)
        pages[case_id] = {
            "sample_id": case_id,
            "company_truth_digest": hashlib.sha256(json.dumps(manifest.get("input_digest", manifest.get("company_truth", {})), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
            "decision_signature_digest": bridge["decision_signature_digest"],
            "creative_family_id": bridge["creative_family_id"],
            "family_frozen": bridge["family_frozen"],
            "page_art_direction_spine": bridge["page_art_direction_spine"],
            "composition_plan_digest": bridge["composition_plan_digest"],
            "production_variant_set_digest": bridge["production_variant_set_digest"],
            "selected_production_variant_ids": bridge["selected_production_variant_ids"],
            "renderer_final_authority": bridge["renderer"]["final_visual_authority"],
            "html_path": f"stage_a/premium/cases/{case_id}/index.html",
            "html_sha256": _sha_file(premium_root / "cases" / case_id / "index.html"),
        }
    return pages, rows


def _browser_verify(premium_root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    hero_mechanisms: dict[str, dict[str, Any]] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id in SAMPLES:
            uri = (premium_root / "cases" / case_id / "index.html").resolve().as_uri()
            for width in WIDTHS:
                context = browser.new_context(viewport={"width": width, "height": 900})
                page = context.new_page()
                page.goto(uri, wait_until="load")
                page.wait_for_load_state("networkidle")
                metrics = page.evaluate(
                    """
                    () => {
                      const root = document.documentElement;
                      const hero = document.querySelector('.variant-hero');
                      const heroVariant = hero?.dataset.productionVariant || null;
                      const routeCount = document.querySelectorAll('.hero-route__routes .route-item').length;
                      const ledgerCount = document.querySelectorAll('.hero-evidence__ledger li').length;
                      const recognitionNoteCount = document.querySelectorAll('.hero-recognition__side-note').length;
                      const variantNodes = [...document.querySelectorAll('[data-production-variant]')];
                      const semantic = [...document.querySelectorAll('.premium-headline-unit,.premium-display-unit')];
                      const semanticRows = semantic.map(node => {
                        const range = document.createRange();
                        range.selectNodeContents(node);
                        const rect = node.getBoundingClientRect();
                        return {
                          text: (node.textContent || '').trim(),
                          lines: range.getClientRects().length,
                          left: rect.left,
                          right: rect.right,
                        };
                      });
                      const images = [...document.querySelectorAll('.production-asset img')];
                      const heroRect = hero?.getBoundingClientRect();
                      const h1Rect = document.querySelector('.variant-hero h1')?.getBoundingClientRect();
                      return {
                        bridge: document.body.dataset.productionVariantBridge || null,
                        overflow: root.scrollWidth > root.clientWidth,
                        hero_variant: heroVariant,
                        hero_class: hero?.className || null,
                        route_count: routeCount,
                        ledger_count: ledgerCount,
                        recognition_note_count: recognitionNoteCount,
                        production_variant_count: variantNodes.length,
                        all_variant_renderer_ids_present: variantNodes.length > 0 && variantNodes.every(n => Boolean(n.dataset.rendererId)),
                        all_variant_pattern_ids_present: variantNodes.length > 0 && variantNodes.every(n => Boolean(n.dataset.researchPattern)),
                        all_variant_responsive_transforms_present: variantNodes.length > 0 && variantNodes.every(n => Boolean(n.dataset.responsiveTransform)),
                        semantic_rows: semanticRows,
                        semantic_atomic_and_visible: semanticRows.length > 0 && semanticRows.every(row => row.lines === 1 && row.left >= -0.75 && row.right <= root.clientWidth + 0.75),
                        images_loaded: images.length > 0 && images.every(img => img.complete && img.naturalWidth > 0 && img.naturalHeight > 0),
                        hero_geometry: heroRect ? {left:heroRect.left,right:heroRect.right,width:heroRect.width,height:heroRect.height} : null,
                        h1_geometry: h1Rect ? {left:h1Rect.left,right:h1Rect.right,width:h1Rect.width,height:h1Rect.height} : null,
                        legacy_shared_final_authority_marker: document.body.dataset.premiumAuthorship === 'issue116' && document.body.dataset.productionVariantBridge !== 'issue121',
                      };
                    }
                    """
                )
                row = {"case_id": case_id, "width": width, **metrics}
                row["pass"] = bool(
                    metrics.get("bridge") == "issue121"
                    and not metrics.get("overflow")
                    and metrics.get("hero_variant")
                    and metrics.get("production_variant_count", 0) >= 4
                    and metrics.get("all_variant_renderer_ids_present")
                    and metrics.get("all_variant_pattern_ids_present")
                    and metrics.get("all_variant_responsive_transforms_present")
                    and metrics.get("semantic_atomic_and_visible")
                    and metrics.get("images_loaded")
                    and not metrics.get("legacy_shared_final_authority_marker")
                )
                rows.append(row)
                if not row["pass"]:
                    failures.append(row)
                if width in CONTACT_WIDTHS and metrics.get("hero_variant"):
                    hero_mechanisms[f"{case_id}@{width}"] = {
                        "hero_variant": metrics["hero_variant"],
                        "hero_class": metrics["hero_class"],
                        "route_count": metrics["route_count"],
                        "ledger_count": metrics["ledger_count"],
                        "recognition_note_count": metrics["recognition_note_count"],
                        "hero_geometry": metrics["hero_geometry"],
                        "h1_geometry": metrics["h1_geometry"],
                    }
                context.close()
        browser.close()
    return {
        "schema_version": "issue121_browser_variant_gate_v1",
        "checks": len(rows),
        "failures": failures,
        "pass": not failures,
        "rows": rows,
        "hero_mechanism_geometry": hero_mechanisms,
    }


def _hero_mechanism_gate(browser_report: dict[str, Any], pages: dict[str, Any]) -> dict[str, Any]:
    by_width: dict[str, dict[str, set[str]]] = {}
    for width in CONTACT_WIDTHS:
        structures: dict[str, set[str]] = defaultdict(set)
        for case_id in SAMPLES:
            key = f"{case_id}@{width}"
            row = browser_report["hero_mechanism_geometry"].get(key)
            if not row:
                continue
            signature = json.dumps({
                "hero_class": row["hero_class"],
                "route_count_positive": row["route_count"] > 0,
                "ledger_count_positive": row["ledger_count"] > 0,
                "recognition_note_positive": row["recognition_note_count"] > 0,
            }, sort_keys=True)
            structures[row["hero_variant"]].add(signature)
        by_width[str(width)] = {variant: values for variant, values in structures.items()}
    selected = {
        pages[case_id]["selected_production_variant_ids"][0]
        for case_id in SAMPLES
    }
    width_results = {}
    for width, structures in by_width.items():
        signatures = {
            variant: sorted(values)
            for variant, values in structures.items()
        }
        representative = {
            variant: values[0] for variant, values in signatures.items() if values
        }
        width_results[width] = {
            "variants_present": sorted(structures),
            "representative_structure_signatures": representative,
            "three_hero_variants_present": set(structures) == EXPECTED_HERO_VARIANTS,
            "mechanism_structures_distinct": len(set(representative.values())) == 3,
        }
    return {
        "selected_hero_variants": sorted(selected),
        "expected_hero_variants": sorted(EXPECTED_HERO_VARIANTS),
        "width_results": width_results,
        "pass": selected == EXPECTED_HERO_VARIANTS and all(
            row["three_hero_variants_present"] and row["mechanism_structures_distinct"]
            for row in width_results.values()
        ),
        "human_visible_fidelity": "PENDING_AOI_AND_SHUN",
    }


def _comparison_evidence(pages: dict[str, Any]) -> dict[str, Any]:
    families: dict[str, list[str]] = defaultdict(list)
    for case_id, row in pages.items():
        families[row["creative_family_id"]].append(case_id)
    same_family = {}
    for family, ids in families.items():
        variant_sequences = [pages[case_id]["selected_production_variant_ids"] for case_id in ids]
        spines = [pages[case_id]["page_art_direction_spine"]["spine_digest"] for case_id in ids]
        same_family[family] = {
            "sample_ids": ids,
            "variant_sequences": variant_sequences,
            "distinct_variant_sequences": len({json.dumps(row) for row in variant_sequences}),
            "distinct_spine_digests": len(set(spines)),
            "all_html_distinct": len({pages[case_id]["html_sha256"] for case_id in ids}) == len(ids),
        }
    cross = []
    ids = list(SAMPLES)
    for index, left in enumerate(ids):
        for right in ids[index + 1:]:
            if pages[left]["creative_family_id"] == pages[right]["creative_family_id"]:
                continue
            cross.append({
                "left": left,
                "right": right,
                "same_variant_sequence": pages[left]["selected_production_variant_ids"] == pages[right]["selected_production_variant_ids"],
                "same_spine": pages[left]["page_art_direction_spine"]["spine_digest"] == pages[right]["page_art_direction_spine"]["spine_digest"],
                "human_template_resemblance": "PENDING_AOI",
            })
    return {
        "same_family": same_family,
        "cross_family": cross,
        "identity_routing_used": False,
        "random_diversity_used": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--out", default="artifacts/issue121_variant_bridge")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    code = _run_issue116(Path(args.baseline), out)
    if code != 0:
        return code

    stage_a = out / "stage_a"
    premium_root = stage_a / "premium"
    screenshot_root = premium_root / "screenshots"
    issue116_manifest = _json(stage_a / "issue116_premium_uplift_manifest.json")
    issue111_manifest = _json(premium_root / "issue111_stage_a_sales_sample_manifest.json")

    pages, scene_rows = _manifest_rows(premium_root, screenshot_root)
    browser = _browser_verify(premium_root)
    hero_gate = _hero_mechanism_gate(browser, pages)
    comparison = _comparison_evidence(pages)

    for width in CONTACT_WIDTHS:
        _contact_sheet(
            screenshot_root,
            width,
            out / "contact_sheets" / f"stage_a_variant_bridge_{width}.jpg",
        )

    selected_variants = sorted({
        variant
        for page in pages.values()
        for variant in page["selected_production_variant_ids"]
    })
    selected_patterns = sorted({
        pattern
        for row in scene_rows
        for pattern in row["source_pattern_ids"]
    })

    rights_regression = {
        "issue116_gates": issue116_manifest["gates"],
        "issue111_all_selected_rights_pass": issue111_manifest["all_selected_rights_pass"],
        "issue111_generic_illustrative_boundary_preserved": issue111_manifest["all_generic_illustrative_boundary_preserved"],
        "issue111_all_binding_traces_complete": issue111_manifest["all_binding_traces_complete"],
        "issue111_all_images_loaded": issue111_manifest["all_images_loaded"],
        "issue111_all_overflow_free": issue111_manifest["all_overflow_free"],
        "issue111_batch_hero_unique": issue111_manifest["batch_hero_unique"],
        "issue111_batch_bundle_unique": issue111_manifest["batch_bundle_unique"],
        "asset_scarcity_family_switch": issue111_manifest["asset_scarcity_family_switch"],
        "company_reference_identity_routing": issue111_manifest["company_reference_identity_routing"],
        "random_selection": issue111_manifest["random_selection"],
    }

    gates = {
        "registry_15_patterns_15_variants": len(registry_manifest()["patterns"]) == 15 and len(registry_manifest()["variants"]) == 15,
        "all_renderer_implementation_identities_present": registry_manifest()["all_renderer_identities_implemented"],
        "final_visual_authority_is_variant_dispatch_all_samples": all(row["renderer_final_authority"] == "production_variant_dispatch" for row in pages.values()),
        "no_silent_generic_fallback": all(_json(premium_root / "cases" / case_id / "production_manifest.json")["silent_generic_variant_fallback"] is False for case_id in SAMPLES),
        "trace_complete": all(row["source_pattern_ids"] and row["selected_production_variant_id"] and row["renderer_implementation_identity"] and row["selection_reason"] for row in scene_rows),
        "81_81_screenshots": issue111_manifest["screenshot_count"] == 81,
        "browser_81_81_variant_chain_and_semantic_gate": browser["pass"] and browser["checks"] == 81,
        "three_hero_mechanisms_distinct_1440_and_390_prerequisite": hero_gate["pass"],
        "rights_provenance_regressions": (
            rights_regression["issue111_all_selected_rights_pass"]
            and rights_regression["issue111_generic_illustrative_boundary_preserved"]
            and rights_regression["issue111_all_binding_traces_complete"]
            and rights_regression["issue111_all_images_loaded"]
            and rights_regression["issue111_all_overflow_free"]
            and rights_regression["issue111_batch_hero_unique"]
            and rights_regression["issue111_batch_bundle_unique"]
            and rights_regression["asset_scarcity_family_switch"] is False
            and rights_regression["company_reference_identity_routing"] is False
            and rights_regression["random_selection"] is False
        ),
        "issue116_full_regression_gates": all(issue116_manifest["gates"].values()),
    }

    direct_chain = {
        "schema_version": "issue121_pattern_variant_renderer_screenshot_trace_v1",
        "starting_main": STARTING_MAIN,
        "pages": pages,
        "scene_traces": scene_rows,
        "selected_research_patterns": selected_patterns,
        "selected_production_variants": selected_variants,
        "registry": registry_manifest(),
        "screenshot_verification_boundary": "Rin verifies technical/rendered mechanism structure; Aoi/Shun human-visible fidelity remains pending.",
    }
    manifest = {
        "schema_version": "issue121_stage_a_variant_bridge_evidence_v1",
        "issue": 121,
        "starting_main": STARTING_MAIN,
        "samples": list(SAMPLES),
        "widths": list(WIDTHS),
        "screenshot_count": issue111_manifest["screenshot_count"],
        "selected_research_patterns": selected_patterns,
        "selected_production_variants": selected_variants,
        "hero_variants_present": hero_gate["selected_hero_variants"],
        "renderer_cutover": {
            "legacy_render_premium_asset_bound_html_final_visual_authority": False,
            "production_variant_dispatch_final_visual_authority": True,
            "silent_generic_fallback": False,
        },
        "gates": gates,
        "human_boundary": {
            "HUMAN_VISIBLE_PASS": "NOT_SELF_DECLARED_PENDING_AOI",
            "final_premium_quality": "NOT_SELF_DECLARED",
            "million_yen_value": "NOT_SELF_DECLARED",
            "Shun_approval": "NOT_SELF_DECLARED_PENDING_ACTUAL_HTML_REVIEW",
        },
        "remaining_limitations": [
            "Human relationship variant requires actual-company human evidence and is fail-closed in Stage A synthetic fixtures.",
            "Gallery atmosphere variant requires a scene media binding and is fail-closed when absent.",
            "Commitment ladder is not selected without verified commitment/pricing terms; Stage A does not fabricate them.",
            "Aoi whole-page mechanism fidelity and Shun value/design judgment remain mandatory after Rin technical completion.",
        ],
    }

    _write(out / "production_variant_registry.json", registry_manifest())
    _write(out / "pattern_variant_renderer_screenshot_manifest.json", direct_chain)
    _write(out / "hero_mechanism_geometry_report.json", hero_gate)
    _write(out / "browser_81_variant_gate.json", browser)
    _write(out / "same_cross_family_comparison.json", comparison)
    _write(out / "rights_evidence_regression.json", rights_regression)
    _write(out / "issue121_manifest.json", manifest)

    # Durable owner-review HTML bundle while preserving all relative asset refs.
    html_bundle = out / "owner_html_bundle"
    if html_bundle.exists():
        shutil.rmtree(html_bundle)
    shutil.copytree(premium_root / "cases", html_bundle / "cases")
    cache = premium_root / "asset_cache"
    if cache.exists():
        shutil.copytree(cache, html_bundle / "asset_cache")

    print(json.dumps({
        "issue": 121,
        "screenshots": manifest["screenshot_count"],
        "selected_patterns": selected_patterns,
        "selected_variants": selected_variants,
        "hero_gate": hero_gate,
        "gates": gates,
        "human_boundary": manifest["human_boundary"],
    }, ensure_ascii=False, indent=2))
    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
