"""Issue #106 real-candidate acquisition + asset-bound Production evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image
from playwright.sync_api import sync_playwright

from lp_engine.authored_composition_contract import plan_digest
from lp_engine.production_cutover import WIDTHS, plan_current_industry_production
from lp_engine.visual_asset_library import (
    PASS_STATES,
    acquire_remote_binary,
    append_usage_entry,
    evaluate_visual_asset_rights,
    ingest_provider_asset,
    make_asset_binding,
    query_asset_candidates,
    select_visual_asset,
    verify_asset_binary,
)
from lp_engine.visual_asset_production import run_asset_bound_generation

BASELINE_MAIN_SHA = "2eaf82a55292911bf6383feb0ff90291b386663c"
BATCH_ID = "issue106-current-industry-asset-evidence"
STAGE_A_MINIMUM = {
    "skincare_cosmetics_product": 10,
    "hair_salon": 18,
    "barber": 18,
    "pilates_studio": 16,
}
CASE_CATEGORY = {
    "B1": ("beauty_cosmetics", "skincare_cosmetics_product"),
    "B2": ("beauty_cosmetics", "skincare_cosmetics_product"),
    "B3": ("beauty_cosmetics", "skincare_cosmetics_product"),
    "H1": ("hair_salon_barber", "hair_salon"),
    "H2": ("hair_salon_barber", "hair_salon"),
    "H3": ("hair_salon_barber", "barber"),
    "P1": ("pilates_fitness", "pilates_studio"),
    "P2": ("pilates_fitness", "pilates_studio"),
    "P3": ("pilates_fitness", "pilates_studio"),
}


def truth(value: Any, confidence: str = "verified") -> dict[str, Any]:
    return {"value": value, "confidence": confidence, "sources": ["issue106-fixture"]}


def fixture(case_id: str, category: str, job: str, family: str, offer_count: int = 2) -> dict[str, Any]:
    return {
        "audit_fixture_id": case_id,
        "company_truth": {
            "category": truth(category), "name": truth("Fixture business"),
            "offers": [{"id": f"{case_id}-offer-{i}", "name": f"Offer {i}", "job": "choose"} for i in range(offer_count)],
            "contact": truth({"channel": "form"}), "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": job, "tensions": ["verified decision tension"], "questions": ["price", "process"],
            "risk_sensitivity": "high" if job == "trust" else "medium", "decision_stage": "consider",
        },
        "creative_family": {"family_id": family, "version": "1", "rationale": ["verified grammar"], "frozen": True},
        "evidence": {
            "facts": [
                {"id": f"{case_id}-price", "claim": "verified price", "scope": "offer", "sources": ["fixture"], "confidence": "verified", "usable_for_persuasion": True},
                {"id": f"{case_id}-process", "claim": "verified process", "scope": "process", "sources": ["fixture"], "confidence": "verified", "usable_for_persuasion": True},
            ],
            "proof_gaps": [], "contradictions": [],
        },
        "media_roles": [{"role_id": f"{case_id}-primary", "role": "process", "required_content_class": "human_scale_detail", "rights": "generated"}],
        "renderer_capabilities": ["responsive"],
    }


def positive_cases() -> dict[str, dict[str, Any]]:
    return {
        "B1": fixture("B1", "beauty_cosmetics", "choose", "family-alpha", 3),
        "B2": fixture("B2", "beauty_cosmetics", "trust", "family-alpha", 1),
        "B3": fixture("B3", "beauty_cosmetics", "compare", "family-alpha", 2),
        "H1": fixture("H1", "hair_salon_barber", "choose", "family-beta", 3),
        "H2": fixture("H2", "hair_salon_barber", "trust", "family-beta", 1),
        "H3": fixture("H3", "hair_salon_barber", "prepare", "family-beta", 1),
        "P1": fixture("P1", "pilates_fitness", "act", "family-gamma", 2),
        "P2": fixture("P2", "pilates_fitness", "trust", "family-gamma", 1),
        "P3": fixture("P3", "pilates_fitness", "compare", "family-gamma", 2),
    }


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def acquire_seed_catalog(out: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seed = _load_json(_root() / "data/visual_asset_library/providers/pexels_stage_a_seed_v1.json")
    catalog: list[dict[str, Any]] = []
    acquisition: list[dict[str, Any]] = []
    for raw in seed["assets"]:
        asset_id = raw["asset_id"]
        download_path = out / "acquisition" / f"{asset_id}.jpg"
        fetched = acquire_remote_binary(raw["binary_url"], download_path)
        with Image.open(download_path) as image:
            image.verify()
        with Image.open(download_path) as image:
            width, height = image.size
        if width < 500 or height < 350:
            raise RuntimeError(f"candidate too small for Production evidence: {asset_id} {width}x{height}")
        metadata = copy.deepcopy(seed["metadata_defaults"])
        metadata.update({key: copy.deepcopy(value) for key, value in raw.items() if key != "binary_url"})
        metadata["source_provider"] = seed["provider"]
        metadata["license_terms_url"] = seed["license_terms_url"]
        metadata["license_terms_checked_at"] = seed["license_terms_checked_at"]
        provider_record = {
            "metadata": metadata,
            "raw_provenance": {
                "provider": seed["provider"], "source_url": raw["source_url"], "binary_url": raw["binary_url"],
                "license_terms_url": seed["license_terms_url"], "seed_schema": seed["schema_version"],
            },
        }
        item = ingest_provider_asset(provider_record, download_path.read_bytes(), acquired_at="2026-09-26")
        rights = evaluate_visual_asset_rights(item, {
            "crop_required": True, "can_render_attribution": True,
            "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK", "current_binary_sha256": item["binary_sha256"],
        })
        if rights["state"] not in PASS_STATES:
            raise RuntimeError(f"seed candidate failed rights gate: {asset_id}: {rights['state']}")
        cache = out / "cache" / item["source_provider"].lower() / item["source_id"] / f"{item['binary_sha256']}.jpg"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(download_path.read_bytes())
        verify_asset_binary(cache, item["binary_sha256"])
        item["runtime_cache_path"] = str(cache)
        item["source_dimensions"] = [width, height]
        catalog.append(item)
        acquisition.append({
            "asset_id": asset_id, "source_url": item["source_url"], "binary_url": raw["binary_url"],
            "binary_sha256": item["binary_sha256"], "bytes": fetched["size"], "content_type": fetched["content_type"],
            "dimensions": [width, height], "rights_gate": rights,
        })
    return catalog, acquisition


def inventory_report(catalog: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    actual_total = 0
    for category, required in STAGE_A_MINIMUM.items():
        ids = sorted({item["asset_id"] for item in catalog if category in item["business_category_tags"]})
        actual = len(ids); actual_total += actual
        rows.append({
            "business_category": category, "minimum_distinct_assets": required,
            "actual_distinct_rights_pass_assets": actual, "remaining_gap": max(0, required - actual),
            "minimum_complete": actual >= required, "asset_ids": ids,
        })
    minimum_total = sum(STAGE_A_MINIMUM.values())
    return {
        "stage": "A_CORE", "actual_distinct_assets": len({item["asset_id"] for item in catalog}),
        "stage_a_minimum_distinct_assets": minimum_total, "remaining_stage_a_gap": max(0, minimum_total - actual_total),
        "categories": rows, "real_image_sales_sample_qa_start_gate": False,
        "gate_reason": "Stage A seed intentionally exercises runtime without fabricating the Issue #104 minimum inventory.",
    }


def catalog_version(catalog: list[dict[str, Any]]) -> str:
    stripped = [{key: value for key, value in item.items() if key != "runtime_cache_path"} for item in catalog]
    payload = json.dumps(stripped, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts/issue106_visual_asset_library")
    args = parser.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    catalog, acquisition = acquire_seed_catalog(out)
    version = catalog_version(catalog)
    inventory = inventory_report(catalog)
    (out / "normalized_asset_catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cases = positive_cases()
    usage_ledger: list[dict[str, Any]] = []
    case_results: dict[str, Any] = {}
    screenshots: list[dict[str, Any]] = []
    hero_classes = {
        "skincare_cosmetics_product": ["product_packshot_generic", "product_texture_generic"],
        "hair_salon": ["salon_interior_generic", "cutting_process_generic", "stylist_consultation_generic"],
        "barber": ["barber_interior_generic", "cutting_process_generic", "barber_consultation_generic"],
        "pilates_studio": ["studio_interior_generic", "reformer_training_generic", "mat_training_generic"],
    }

    for case_id, raw in cases.items():
        industry, category = CASE_CATEGORY[case_id]
        pre_plan = plan_current_industry_production(raw)
        recognize = next(scene for scene in pre_plan["scene_intents"] if scene["id"] == "recognize")
        required_classes = hero_classes[category]
        candidates = query_asset_candidates(
            catalog, industry=industry, business_category=category, scene_intent="recognize", media_role="hero",
            required_content_classes=required_classes, evidence_boundary="GENERIC_ILLUSTRATIVE_STOCK",
        )
        placement = {
            "required_content_classes": required_classes, "orientation": "flexible", "business_category": category,
            "crop_fingerprint": "hero-center-safe-v1", "batch_id": BATCH_ID, "can_render_attribution": True,
            "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK", "people_type": "none",
            "visual_tone_tags": [], "material_quality_tags": [],
        }
        selection = select_visual_asset(
            candidates, frozen_composition_plan=pre_plan, scene=recognize, media_role="hero",
            target_placement=placement, usage_ledger_snapshot=usage_ledger,
        )
        if selection["state"] != "SELECTED":
            raise RuntimeError(f"no selectable hero for {case_id}: {selection}")
        selected = selection["selected"]
        case_dir = out / "cases" / case_id; case_dir.mkdir(parents=True, exist_ok=True)
        cache_path = Path(selected["runtime_cache_path"]).resolve()
        relative_path = os.path.relpath(cache_path, case_dir.resolve()).replace(os.sep, "/")
        binding = make_asset_binding(
            generation_id=case_id, plan=pre_plan, scene=recognize, media_role="hero", business_category=category,
            selection=selection, catalog_version=version, usage_ledger=usage_ledger,
            crop_variant_id="hero-center-safe-v1", focal_point=[0.5, 0.5], local_asset_path=relative_path,
            source_path=str(cache_path.relative_to(out.resolve())) if cache_path.is_relative_to(out.resolve()) else str(cache_path),
        )
        verify_asset_binary(cache_path, binding["binary_sha256"])
        append_usage_entry(
            usage_ledger, binding=binding, generation_id=case_id, batch_id=BATCH_ID,
            business_category=category, placement_prominence="dominant", crop_fingerprint="hero-center-safe-v1",
        )
        result = run_asset_bound_generation(raw, case_dir, asset_bindings={"hero": binding})
        post_plan = result["plan"]
        architecture_same = (
            pre_plan["family_id"] == post_plan["family_id"]
            and pre_plan["topology"] == post_plan["topology"]
            and pre_plan["scene_intents"] == post_plan["scene_intents"]
        )
        if not architecture_same:
            raise RuntimeError(f"asset binding changed authored structure for {case_id}")
        case_results[case_id] = {
            "industry": industry, "business_category": category, "plan_digest": plan_digest(pre_plan),
            "family_id": pre_plan["family_id"], "family_frozen": True, "topology": pre_plan["topology"],
            "scene_media_role": {"scene_id": "recognize", "scene_intent": "recognize", "media_role": "hero"},
            "candidate_asset_ids": [item["asset_id"] for item in candidates], "candidate_rejections": selection["candidate_rejections"],
            "selected_asset_id": binding["asset_id"], "selected_binary_sha256": binding["binary_sha256"],
            "rights_gate": binding["rights_gate"], "evidence_status": binding["evidence_status"],
            "crop_variant_id": binding["crop_variant_id"], "renderer_binding_id": binding["trace"]["renderer_binding_id"],
            "provenance_trace": binding["trace"], "architecture_preserved": architecture_same,
        }

    (out / "usage_ledger.json").write_text(json.dumps(usage_ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id in cases:
            page = browser.new_page()
            html_path = (out / "cases" / case_id / "index.html").resolve()
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(html_path.as_uri(), wait_until="load")
                page.wait_for_load_state("networkidle")
                metrics = page.evaluate("""
                    () => {
                      const images = [...document.images];
                      const semantic = [...document.querySelectorAll('.semantic-headline-unit,.semantic-body-unit')];
                      const asset = document.querySelector('.production-asset');
                      return {
                        overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                        images_loaded: images.length > 0 && images.every(img => img.complete && img.naturalWidth > 0 && img.naturalHeight > 0),
                        image_count: images.length,
                        illustrative_caption: document.body.innerText.includes('イメージ写真'),
                        semantic_atomic: semantic.every(node => node.getClientRects().length === 1),
                        bound_asset_id: asset?.dataset.assetId || null,
                        bound_binary_sha: asset?.dataset.binarySha || null,
                      };
                    }
                """)
                if metrics["overflow"] or not metrics["images_loaded"] or not metrics["illustrative_caption"]:
                    raise RuntimeError(f"browser asset gate failed {case_id}@{width}: {metrics}")
                if width == 320 and not metrics["semantic_atomic"]:
                    raise RuntimeError(f"320 semantic regression {case_id}: {metrics}")
                if metrics["bound_asset_id"] != case_results[case_id]["selected_asset_id"] or metrics["bound_binary_sha"] != case_results[case_id]["selected_binary_sha256"]:
                    raise RuntimeError(f"render trace mismatch {case_id}@{width}: {metrics}")
                shot_dir = out / "screenshots" / case_id; shot_dir.mkdir(parents=True, exist_ok=True)
                shot = shot_dir / f"{width}.png"; page.screenshot(path=str(shot), full_page=True)
                screenshots.append({
                    "case_id": case_id, "width": width, "path": str(shot.relative_to(out)), **metrics,
                    "selected_asset_id": case_results[case_id]["selected_asset_id"],
                    "selected_binary_sha256": case_results[case_id]["selected_binary_sha256"],
                })
            page.close()
        browser.close()

    manifest = {
        "schema_version": "issue106_current_industry_visual_asset_library_evidence_v1",
        "baseline_main_sha": BASELINE_MAIN_SHA,
        "contracts": [
            "docs/ISSUE104_RIKO_CURRENT_INDUSTRY_VISUAL_ASSET_LIBRARY_SPEC.md",
            "artifacts/issue104_riko/asset_metadata_contract_v1.json",
            "artifacts/issue104_riko/rights_gate_contract_v1.json",
            "artifacts/issue104_riko/selection_reuse_contract_v1.json",
            "artifacts/issue104_riko/asset_provenance_trace_contract_v1.json",
            "artifacts/issue104_riko/minimum_current_industry_asset_inventory_matrix_v1.json",
        ],
        "catalog_version": version, "real_candidate_inventory": inventory, "acquisition": acquisition,
        "case_results": case_results, "usage_ledger": usage_ledger, "widths": list(WIDTHS),
        "screenshots": screenshots, "screenshot_count": len(screenshots),
        "composition_plan_authoritative": all(item["architecture_preserved"] for item in case_results.values()),
        "family_topology_scene_order_preserved": all(item["architecture_preserved"] for item in case_results.values()),
        "all_selected_rights_pass": all(item["rights_gate"] in PASS_STATES for item in case_results.values()),
        "generic_illustrative_boundary_preserved": all(item["evidence_status"] == "GENERIC_ILLUSTRATIVE_STOCK" for item in case_results.values()),
        "all_images_loaded": all(item["images_loaded"] for item in screenshots),
        "all_overflow_free": all(not item["overflow"] for item in screenshots),
        "semantic_320_regression_lock": all(item["semantic_atomic"] for item in screenshots if item["width"] == 320),
        "render_trace_hash_joinable": all(
            item["bound_asset_id"] == item["selected_asset_id"] and item["bound_binary_sha"] == item["selected_binary_sha256"]
            for item in screenshots
        ),
        "identity_routing": False, "reference_lookup": False, "random_selection": False,
        "human_visible_status": "PENDING_AOI_NOT_SELF_DECLARED",
        "real_image_sales_sample_readiness": "NOT_DECLARED_INVENTORY_GAPS_REMAIN",
    }
    (out / "issue106_visual_asset_library_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "catalog_version": version, "inventory": inventory, "screenshot_count": manifest["screenshot_count"],
        "selected_assets": {case_id: row["selected_asset_id"] for case_id, row in case_results.items()},
        "gates": {key: manifest[key] for key in (
            "composition_plan_authoritative", "family_topology_scene_order_preserved", "all_selected_rights_pass",
            "generic_illustrative_boundary_preserved", "all_images_loaded", "all_overflow_free",
            "semantic_320_regression_lock", "render_trace_hash_joinable",
        )},
    }, ensure_ascii=False, indent=2))
    gates = [
        manifest["screenshot_count"] == 81, manifest["composition_plan_authoritative"], manifest["all_selected_rights_pass"],
        manifest["generic_illustrative_boundary_preserved"], manifest["all_images_loaded"], manifest["all_overflow_free"],
        manifest["semantic_320_regression_lock"], manifest["render_trace_hash_joinable"],
    ]
    return 0 if all(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
