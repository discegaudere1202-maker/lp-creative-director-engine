"""Issue #111 — Stage A Real-image Sales Sample QA Production Evidence Gate.

Runs nine representative Stage A samples through the normal Production path using
only the merged Issue #109 62/62 rights-approved Visual Asset Library inventory.
The runner preserves frozen CompositionPlan authority, deterministic selection,
full binding provenance, generic-illustrative semantics, batch anti-repetition,
and 9-width browser evidence for independent Aoi review.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps
from playwright.sync_api import sync_playwright

import run_issue106_visual_asset_library as issue106
import run_issue109_stage_a_inventory_completion as issue109
import run_issue109_stage_a_inventory_completion_final as issue109_final

from lp_engine.authored_composition_contract import plan_digest
from lp_engine.production_cutover import WIDTHS, plan_current_industry_production
from lp_engine.visual_asset_library import (
    PASS_STATES,
    append_usage_entry,
    evaluate_visual_asset_rights,
    make_asset_binding,
    query_asset_candidates,
    select_visual_asset,
    verify_asset_binary,
)
from lp_engine.visual_asset_production import run_asset_bound_generation

ROOT = Path(__file__).resolve().parents[1]
BASELINE_MAIN_SHA = "116fb0d7e19e16cbcf97343d7f96566f07d044c6"
BATCH_ID = "issue111-stage-a-real-image-sales-sample"
EXPECTED_FLOOR = {
    "skincare_cosmetics_product": 10,
    "hair_salon": 18,
    "barber": 18,
    "pilates_studio": 16,
}
HERO_CLASSES = {
    "skincare_cosmetics_product": ["product_packshot_generic", "product_texture_generic"],
    "hair_salon": ["salon_interior_generic", "cutting_process_generic", "stylist_consultation_generic"],
    "barber": ["barber_interior_generic", "cutting_process_generic", "barber_consultation_generic"],
    "pilates_studio": ["studio_interior_generic", "reformer_training_generic", "mat_training_generic"],
}
ROLE_PREFERENCES = {
    "choose": ["tools_material_detail", "lifestyle_context", "interior_environment", "process", "consultation"],
    "understand": ["process", "tools_material_detail", "interior_environment", "consultation"],
    "trust": ["interior_environment", "consultation", "lifestyle_context", "person_staff", "tools_material_detail"],
    "compare": ["tools_material_detail", "lifestyle_context", "process", "interior_environment"],
    "prepare": ["process", "interior_environment", "tools_material_detail", "consultation"],
    "act": ["lifestyle_context", "interior_environment", "tools_material_detail", "process"],
}


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(value: Any) -> str:
    payload = value if isinstance(value, bytes) else _canonical(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def truth(value: Any, confidence: str = "verified") -> dict[str, Any]:
    return {"value": value, "confidence": confidence, "sources": ["issue111-synthetic-qa-fixture"]}


def fixture(
    case_id: str,
    *,
    industry: str,
    name: str,
    primary_job: str,
    family: str,
    offer_count: int,
) -> dict[str, Any]:
    """Synthetic QA input; never represented as actual-company evidence."""
    return {
        "audit_fixture_id": case_id,
        "company_id": f"issue111-company-{case_id.lower()}",
        "reference_id": f"issue111-reference-{case_id.lower()}",
        "fixture_semantics": "SYNTHETIC_QA_ONLY_NOT_COMPANY_EVIDENCE",
        "company_truth": {
            "category": truth(industry),
            "name": truth(name),
            "offers": [
                {"id": f"{case_id}-offer-{index}", "name": f"QAメニュー{index}", "job": "choose"}
                for index in range(1, offer_count + 1)
            ],
            "contact": truth({"channel": "form"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": primary_job,
            "tensions": [f"{case_id} decision tension"],
            "questions": ["price", "process", f"{case_id}-specific-question"],
            "risk_sensitivity": "high" if primary_job == "trust" else "medium",
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": family,
            "version": "1",
            "rationale": ["Issue111 QA family is frozen before media selection"],
            "frozen": True,
        },
        "evidence": {
            "facts": [
                {
                    "id": f"{case_id}-qa-process",
                    "claim": f"{case_id} synthetic QA process fact",
                    "scope": "process",
                    "sources": ["issue111-synthetic-fixture"],
                    "confidence": "verified",
                    "usable_for_persuasion": False,
                }
            ],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [
            {
                "role_id": f"{case_id}-primary",
                "role": "process",
                "required_content_class": "generic",
                "rights": "visual_asset_library",
            }
        ],
        "renderer_capabilities": ["responsive"],
    }


def sample_matrix() -> dict[str, dict[str, Any]]:
    specs = {
        "SK1": ("beauty_cosmetics", "skincare_cosmetics_product", "QAスキンケアA", "choose", "family-alpha", 3),
        "SK2": ("beauty_cosmetics", "skincare_cosmetics_product", "QAスキンケアB", "trust", "family-alpha", 1),
        "SK3": ("beauty_cosmetics", "skincare_cosmetics_product", "QAスキンケアC", "compare", "family-alpha", 2),
        "HS1": ("hair_salon_barber", "hair_salon", "QAヘアサロンA", "choose", "family-beta", 3),
        "HS2": ("hair_salon_barber", "hair_salon", "QAヘアサロンB", "trust", "family-beta", 1),
        "BR1": ("hair_salon_barber", "barber", "QAバーバーA", "prepare", "family-beta", 1),
        "BR2": ("hair_salon_barber", "barber", "QAバーバーB", "compare", "family-beta", 2),
        "PI1": ("pilates_fitness", "pilates_studio", "QAピラティスA", "act", "family-gamma", 2),
        "PI2": ("pilates_fitness", "pilates_studio", "QAピラティスB", "trust", "family-gamma", 1),
    }
    result: dict[str, dict[str, Any]] = {}
    for case_id, (industry, category, name, job, family, offer_count) in specs.items():
        result[case_id] = {
            "industry": industry,
            "business_category": category,
            "fixture": fixture(
                case_id,
                industry=industry,
                name=name,
                primary_job=job,
                family=family,
                offer_count=offer_count,
            ),
        }
    return result


def build_effective_stage_a_seed() -> dict[str, Any]:
    """Rebuild the exact merged Issue109 effective 62-asset seed, fail closed."""
    corrected_completion_path = issue109_final._build_corrected_completion_seed()
    base_seed = issue109.ORIGINAL_LOAD_JSON(issue109.BASE_SEED)
    sarah = issue109.ORIGINAL_LOAD_JSON(issue109.SARAH_CORRECTIONS)
    completion = issue109.ORIGINAL_LOAD_JSON(corrected_completion_path)

    blocked = {row["asset_id"] for row in sarah["blocked_asset_ids"]}
    assets = [copy.deepcopy(row) for row in base_seed["assets"] if row["asset_id"] not in blocked]
    assets.extend(copy.deepcopy(row) for row in sarah["replacement_assets"])
    assets.extend(copy.deepcopy(row) for row in completion["assets"])

    ids = [row["asset_id"] for row in assets]
    if len(ids) != 62 or len(ids) != len(set(ids)):
        raise RuntimeError(f"Issue111 requires 62 distinct merged Stage A assets, got {len(ids)}")
    if blocked.intersection(ids):
        raise RuntimeError(f"Sarah-blocked asset survived merged Stage A seed: {sorted(blocked.intersection(ids))}")

    category_counts = {
        category: len({row["asset_id"] for row in assets if category in row["business_category_tags"]})
        for category in EXPECTED_FLOOR
    }
    if category_counts != EXPECTED_FLOOR:
        raise RuntimeError(f"Stage A category floor mismatch: {category_counts}")

    seed = copy.deepcopy(base_seed)
    seed["schema_version"] = "issue111_stage_a_62_rights_approved_effective_seed_v1"
    seed["policy"] = (
        "Exact merged Issue109 62/62 inventory only; prior Sarah and Issue109 exact-binary corrections preserved; "
        "all runtime bytes are reacquired, hashed, and rights-gated again before binding."
    )
    seed["assets"] = assets
    seed["issue111_provenance"] = {
        "baseline_main_sha": BASELINE_MAIN_SHA,
        "base_seed": str(issue109.BASE_SEED.relative_to(ROOT)),
        "sarah_correction_contract": str(issue109.SARAH_CORRECTIONS.relative_to(ROOT)),
        "issue109_completion_seed": str(issue109.COMPLETION_SEED.relative_to(ROOT)),
        "issue109_candidate_corrections": str(issue109_final.CORRECTIONS.relative_to(ROOT)),
        "issue109_sarah_return_corrections": str(issue109_final.SARAH_RETURN_CORRECTIONS.relative_to(ROOT)),
        "category_counts": category_counts,
    }
    return seed


def acquire_effective_catalog(out: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    seed = build_effective_stage_a_seed()
    original_loader = issue106._load_json

    def issue111_loader(path: Path) -> Any:
        if path.name == issue109.BASE_SEED.name:
            return copy.deepcopy(seed)
        return original_loader(path)

    issue106._load_json = issue111_loader
    try:
        catalog, acquisition = issue106.acquire_seed_catalog(out)
    finally:
        issue106._load_json = original_loader

    if len(catalog) != 62:
        raise RuntimeError(f"Issue111 acquired catalog must contain 62 assets, got {len(catalog)}")
    return catalog, acquisition, seed


def catalog_version(catalog: list[dict[str, Any]]) -> str:
    stripped = [{key: value for key, value in row.items() if key != "runtime_cache_path"} for row in catalog]
    return _sha(stripped)


def rights_decisions(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in candidates:
        rights = evaluate_visual_asset_rights(
            item,
            {
                "crop_required": True,
                "can_render_attribution": True,
                "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK",
                "current_binary_sha256": item["binary_sha256"],
            },
        )
        rows.append({
            "asset_id": item["asset_id"],
            "binary_sha256": item["binary_sha256"],
            "source_url": item["source_url"],
            "rights_state": rights["state"],
            "rights_conditions": rights["conditions"],
        })
    return rows


def _bind_asset(
    *,
    generation_id: str,
    industry: str,
    category: str,
    plan: dict[str, Any],
    scene: dict[str, Any],
    media_role: str,
    required_classes: list[str],
    catalog: list[dict[str, Any]],
    version: str,
    usage_ledger: list[dict[str, Any]],
    batch_used_asset_ids: set[str],
    case_dir: Path,
    out: Path,
    placement_prominence: str,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    raw_candidates = query_asset_candidates(
        catalog,
        industry=industry,
        business_category=category,
        scene_intent=str(scene["intent"]),
        media_role=media_role,
        required_content_classes=required_classes,
        evidence_boundary="GENERIC_ILLUSTRATIVE_STOCK",
    )
    decisions = rights_decisions(raw_candidates)
    available = [row for row in raw_candidates if row["asset_id"] not in batch_used_asset_ids]
    selection_context = {
        "candidate_asset_ids": [row["asset_id"] for row in raw_candidates],
        "candidate_rights_decisions": decisions,
        "batch_reuse_excluded_asset_ids": sorted(
            row["asset_id"] for row in raw_candidates if row["asset_id"] in batch_used_asset_ids
        ),
        "available_candidate_asset_ids": [row["asset_id"] for row in available],
    }
    if not available:
        return None, {**selection_context, "state": "MEDIA_ROLE_UNSATISFIED_AFTER_BATCH_UNIQUENESS"}

    crop_variant_id = f"{media_role}-center-safe-v1"
    selection = select_visual_asset(
        available,
        frozen_composition_plan=plan,
        scene=scene,
        media_role=media_role,
        target_placement={
            "required_content_classes": required_classes,
            "orientation": "flexible",
            "business_category": category,
            "crop_fingerprint": crop_variant_id,
            "batch_id": BATCH_ID,
            "can_render_attribution": True,
            "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK",
            "people_type": "any",
            "visual_tone_tags": [],
            "material_quality_tags": [],
        },
        usage_ledger_snapshot=usage_ledger,
    )
    if selection["state"] != "SELECTED":
        return None, {**selection_context, "state": selection["state"], "selector": selection}

    selected = selection["selected"]
    cache_path = Path(selected["runtime_cache_path"]).resolve()
    relative_path = os.path.relpath(cache_path, case_dir.resolve()).replace(os.sep, "/")
    binding = make_asset_binding(
        generation_id=generation_id,
        plan=plan,
        scene=scene,
        media_role=media_role,
        business_category=category,
        selection=selection,
        catalog_version=version,
        usage_ledger=usage_ledger,
        crop_variant_id=crop_variant_id,
        focal_point=[0.5, 0.5],
        local_asset_path=relative_path,
        source_path=(
            str(cache_path.relative_to(out.resolve()))
            if cache_path.is_relative_to(out.resolve())
            else str(cache_path)
        ),
    )
    # Issue111 strengthens the durable per-binding trace with the complete queried
    # candidate set and every candidate's rights decision, not only rejected rows.
    binding["trace"]["candidate_asset_ids"] = selection_context["candidate_asset_ids"]
    binding["trace"]["candidate_rights_decisions"] = decisions
    binding["trace"]["batch_reuse_excluded_asset_ids"] = selection_context["batch_reuse_excluded_asset_ids"]
    binding["trace"]["available_candidate_asset_ids"] = selection_context["available_candidate_asset_ids"]
    binding["trace"]["selection_deterministic"] = True
    binding["trace"]["company_reference_identity_used_for_routing"] = False
    binding["trace"]["source_dimensions"] = selected.get("source_dimensions")

    verify_asset_binary(cache_path, binding["binary_sha256"])
    append_usage_entry(
        usage_ledger,
        binding=binding,
        generation_id=generation_id,
        batch_id=BATCH_ID,
        business_category=category,
        placement_prominence=placement_prominence,
        crop_fingerprint=crop_variant_id,
    )
    batch_used_asset_ids.add(binding["asset_id"])
    return binding, {**selection_context, "state": "SELECTED", "selected_asset_id": binding["asset_id"]}


def _select_support_binding(
    *,
    case_id: str,
    industry: str,
    category: str,
    plan: dict[str, Any],
    catalog: list[dict[str, Any]],
    version: str,
    usage_ledger: list[dict[str, Any]],
    batch_used_asset_ids: set[str],
    case_dir: Path,
    out: Path,
) -> tuple[str | None, dict[str, Any] | None, list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    for scene in plan["scene_intents"]:
        if str(scene.get("id")) == "recognize":
            continue
        for role in ROLE_PREFERENCES.get(str(scene.get("intent")), ROLE_PREFERENCES["understand"]):
            binding, context = _bind_asset(
                generation_id=case_id,
                industry=industry,
                category=category,
                plan=plan,
                scene=scene,
                media_role=role,
                required_classes=[],
                catalog=catalog,
                version=version,
                usage_ledger=usage_ledger,
                batch_used_asset_ids=batch_used_asset_ids,
                case_dir=case_dir,
                out=out,
                placement_prominence="support",
            )
            attempts.append({"scene_id": scene["id"], "scene_intent": scene["intent"], "media_role": role, **context})
            if binding is not None:
                return str(scene["id"]), binding, attempts
    return None, None, attempts


def _contact_sheet(paths: list[tuple[str, Path]], output: Path, *, title: str) -> None:
    tile_w, tile_h = 320, 300
    image_h = 252
    cols = 3
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, 52 + rows * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 16), title, fill="black")
    for index, (label, path) in enumerate(paths):
        image = Image.open(path).convert("RGB")
        top = image.crop((0, 0, image.width, min(image.height, max(900, image.width))))
        fitted = ImageOps.contain(top, (tile_w - 12, image_h - 12))
        tile = Image.new("RGB", (tile_w, image_h), "#ededed")
        tile.paste(fitted, ((tile_w - fitted.width) // 2, (image_h - fitted.height) // 2))
        x = (index % cols) * tile_w
        y = 52 + (index // cols) * tile_h
        sheet.paste(tile, (x, y))
        draw.text((x + 8, y + image_h + 10), label, fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)


def _browser_metrics(page) -> dict[str, Any]:
    return page.evaluate(
        """
        () => {
          const figures = [...document.querySelectorAll('.production-asset')];
          const images = figures.map(fig => fig.querySelector('img')).filter(Boolean);
          const semantic = [...document.querySelectorAll('.semantic-headline-unit,.semantic-body-unit')];
          const cropFractions = images.map(img => {
            const box = img.getBoundingClientRect();
            if (!img.naturalWidth || !img.naturalHeight || !box.width || !box.height) return 0;
            const sourceAspect = img.naturalWidth / img.naturalHeight;
            const boxAspect = box.width / box.height;
            return Math.min(1, sourceAspect / boxAspect, boxAspect / sourceAspect);
          });
          return {
            overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
            images_loaded: images.length > 0 && images.every(img => img.complete && img.naturalWidth > 0 && img.naturalHeight > 0),
            image_count: images.length,
            asset_count: figures.length,
            illustrative_caption_count: [...document.querySelectorAll('.production-asset figcaption')]
              .filter(node => node.textContent.includes('イメージ写真')).length,
            generic_asset_count: figures.filter(fig => fig.dataset.evidenceStatus === 'GENERIC_ILLUSTRATIVE_STOCK').length,
            semantic_atomic: semantic.every(node => node.getClientRects().length === 1),
            min_crop_visible_fraction: cropFractions.length ? Math.min(...cropFractions) : 0,
            bound_assets: figures.map(fig => ({
              asset_id: fig.dataset.assetId || null,
              binary_sha256: fig.dataset.binarySha || null,
              evidence_status: fig.dataset.evidenceStatus || null,
            })),
          };
        }
        """
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts/issue111_stage_a_sales_sample_qa")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    catalog, acquisition, effective_seed = acquire_effective_catalog(out)
    version = catalog_version(catalog)
    (out / "normalized_asset_catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "issue111_acquisition_report.json").write_text(
        json.dumps(acquisition, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    matrix = sample_matrix()
    usage_ledger: list[dict[str, Any]] = []
    batch_used_asset_ids: set[str] = set()
    sample_results: dict[str, Any] = {}
    screenshots: list[dict[str, Any]] = []

    for case_id, spec in matrix.items():
        industry = spec["industry"]
        category = spec["business_category"]
        raw = spec["fixture"]
        case_dir = out / "cases" / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        pre_plan = plan_current_industry_production(raw)
        if pre_plan.get("input", {}).get("creative_family", {}).get("frozen") is not True:
            raise RuntimeError(f"Family not frozen before asset selection: {case_id}")
        recognize = next(scene for scene in pre_plan["scene_intents"] if scene["id"] == "recognize")

        hero_binding, hero_context = _bind_asset(
            generation_id=case_id,
            industry=industry,
            category=category,
            plan=pre_plan,
            scene=recognize,
            media_role="hero",
            required_classes=HERO_CLASSES[category],
            catalog=catalog,
            version=version,
            usage_ledger=usage_ledger,
            batch_used_asset_ids=batch_used_asset_ids,
            case_dir=case_dir,
            out=out,
            placement_prominence="dominant",
        )
        if hero_binding is None:
            raise RuntimeError(f"No unique rights-pass hero for {case_id}: {hero_context}")

        bindings: dict[str, dict[str, Any]] = {"hero": hero_binding}
        support_scene_id, support_binding, support_attempts = _select_support_binding(
            case_id=case_id,
            industry=industry,
            category=category,
            plan=pre_plan,
            catalog=catalog,
            version=version,
            usage_ledger=usage_ledger,
            batch_used_asset_ids=batch_used_asset_ids,
            case_dir=case_dir,
            out=out,
        )
        if support_scene_id and support_binding:
            bindings[support_scene_id] = support_binding

        result = run_asset_bound_generation(raw, case_dir, asset_bindings=bindings)
        post_plan = result["plan"]
        architecture_preserved = (
            pre_plan["family_id"] == post_plan["family_id"]
            and pre_plan["topology"] == post_plan["topology"]
            and pre_plan["scene_intents"] == post_plan["scene_intents"]
        )
        if not architecture_preserved:
            raise RuntimeError(f"Asset binding changed frozen authorship for {case_id}")

        html_path = case_dir / "index.html"
        html_sha = hashlib.sha256(html_path.read_bytes()).hexdigest()
        sample_results[case_id] = {
            "company_id": raw["company_id"],
            "reference_id": raw["reference_id"],
            "fixture_semantics": raw["fixture_semantics"],
            "industry": industry,
            "business_category": category,
            "family_id": pre_plan["family_id"],
            "family_frozen": True,
            "topology": pre_plan["topology"],
            "scene_order": [row["id"] for row in pre_plan["scene_intents"]],
            "plan_digest": plan_digest(pre_plan),
            "rendered_html_sha256": html_sha,
            "hero_candidate_pool": hero_context["candidate_asset_ids"],
            "hero_selection_context": hero_context,
            "support_selection_attempts": support_attempts,
            "selected_bindings": {
                key: {
                    "asset_id": value["asset_id"],
                    "binary_sha256": value["binary_sha256"],
                    "media_role": value["media_role"],
                    "scene_id": value["scene_id"],
                    "evidence_status": value["evidence_status"],
                    "rights_gate": value["rights_gate"],
                    "trace": copy.deepcopy(value["trace"]),
                }
                for key, value in bindings.items()
            },
            "bundle_asset_ids": sorted(value["asset_id"] for value in bindings.values()),
            "bundle_signature": _sha(sorted(value["asset_id"] for value in bindings.values())),
            "architecture_preserved": architecture_preserved,
        }

    category_groups: dict[str, list[str]] = defaultdict(list)
    for case_id, row in sample_results.items():
        category_groups[row["business_category"]].append(case_id)

    candidate_pool_invariance: dict[str, Any] = {}
    authored_divergence: dict[str, Any] = {}
    for category, case_ids in category_groups.items():
        pools = {_canonical(sample_results[case_id]["hero_candidate_pool"]) for case_id in case_ids}
        digests = {sample_results[case_id]["plan_digest"] for case_id in case_ids}
        html_hashes = {sample_results[case_id]["rendered_html_sha256"] for case_id in case_ids}
        candidate_pool_invariance[category] = {
            "sample_ids": case_ids,
            "same_unfiltered_hero_candidate_pool": len(pools) == 1,
        }
        authored_divergence[category] = {
            "sample_ids": case_ids,
            "distinct_plan_digests": len(digests),
            "distinct_rendered_html_hashes": len(html_hashes),
            "company_specific_divergence": len(digests) == len(case_ids) and len(html_hashes) == len(case_ids),
        }

    hero_ids = [row["selected_bindings"]["hero"]["asset_id"] for row in sample_results.values()]
    bundle_signatures = [row["bundle_signature"] for row in sample_results.values()]
    all_binding_ids = [
        binding["asset_id"]
        for row in sample_results.values()
        for binding in row["selected_bindings"].values()
    ]
    reuse_report = {
        "schema_version": "issue111_stage_a_batch_reuse_uniqueness_v1",
        "batch_id": BATCH_ID,
        "sample_count": len(sample_results),
        "hero_asset_ids": hero_ids,
        "hero_unique": len(hero_ids) == len(set(hero_ids)),
        "all_binding_asset_ids": all_binding_ids,
        "all_binding_assets_unique_in_batch": len(all_binding_ids) == len(set(all_binding_ids)),
        "asset_usage_counts": dict(sorted(Counter(all_binding_ids).items())),
        "bundle_signatures": bundle_signatures,
        "bundle_signatures_unique": len(bundle_signatures) == len(set(bundle_signatures)),
        "same_category_candidate_pool_invariance": candidate_pool_invariance,
        "company_specific_authored_divergence": authored_divergence,
        "company_reference_identity_routing": False,
        "random_selection": False,
    }
    if not reuse_report["hero_unique"]:
        raise RuntimeError(f"Repeated dominant Hero detected: {hero_ids}")
    if not reuse_report["all_binding_assets_unique_in_batch"]:
        raise RuntimeError(f"Repeated asset binding detected across sample batch: {reuse_report['asset_usage_counts']}")
    if not reuse_report["bundle_signatures_unique"]:
        raise RuntimeError("Repeated media-role bundle signature detected")
    if not all(row["same_unfiltered_hero_candidate_pool"] for row in candidate_pool_invariance.values()):
        raise RuntimeError(f"Company identity affected candidate pool: {candidate_pool_invariance}")
    if not all(row["company_specific_divergence"] for row in authored_divergence.values()):
        raise RuntimeError(f"Company-specific authored divergence missing: {authored_divergence}")

    (out / "usage_ledger.json").write_text(
        json.dumps(usage_ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "issue111_batch_reuse_uniqueness_report.json").write_text(
        json.dumps(reuse_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "issue111_sample_matrix.json").write_text(
        json.dumps(sample_results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    screenshot_index: dict[int, list[tuple[str, Path]]] = {width: [] for width in WIDTHS}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id, row in sample_results.items():
            page = browser.new_page()
            html_path = (out / "cases" / case_id / "index.html").resolve()
            expected_bindings = row["selected_bindings"]
            expected_pairs = {
                (binding["asset_id"], binding["binary_sha256"])
                for binding in expected_bindings.values()
            }
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(html_path.as_uri(), wait_until="load")
                page.wait_for_load_state("networkidle")
                metrics = _browser_metrics(page)
                actual_pairs = {
                    (item["asset_id"], item["binary_sha256"])
                    for item in metrics["bound_assets"]
                }
                trace_joinable = actual_pairs == expected_pairs
                generic_boundary_visible = (
                    metrics["generic_asset_count"] == len(expected_bindings)
                    and metrics["illustrative_caption_count"] == len(expected_bindings)
                )
                if metrics["overflow"]:
                    raise RuntimeError(f"Overflow {case_id}@{width}: {metrics}")
                if not metrics["images_loaded"]:
                    raise RuntimeError(f"Broken image {case_id}@{width}: {metrics}")
                if width == 320 and not metrics["semantic_atomic"]:
                    raise RuntimeError(f"320px semantic Hard Gate failed {case_id}: {metrics}")
                if metrics["asset_count"] != len(expected_bindings):
                    raise RuntimeError(f"Rendered asset count mismatch {case_id}@{width}: {metrics}")
                if not trace_joinable:
                    raise RuntimeError(f"Binding trace/hash mismatch {case_id}@{width}: {metrics}")
                if not generic_boundary_visible:
                    raise RuntimeError(f"Generic illustrative boundary not visible {case_id}@{width}: {metrics}")
                if metrics["min_crop_visible_fraction"] < 0.42:
                    raise RuntimeError(f"Destructive crop heuristic failed {case_id}@{width}: {metrics}")

                shot_dir = out / "screenshots" / case_id
                shot_dir.mkdir(parents=True, exist_ok=True)
                shot = shot_dir / f"{width}.png"
                page.screenshot(path=str(shot), full_page=True)
                screenshot_index[width].append((case_id, shot))
                screenshots.append({
                    "case_id": case_id,
                    "industry": row["industry"],
                    "business_category": row["business_category"],
                    "width": width,
                    "path": str(shot.relative_to(out)),
                    **metrics,
                    "trace_hash_joinable": trace_joinable,
                    "generic_boundary_visible": generic_boundary_visible,
                    "expected_bindings": [
                        {"asset_id": asset_id, "binary_sha256": binary_sha}
                        for asset_id, binary_sha in sorted(expected_pairs)
                    ],
                })
            page.close()
        browser.close()

    for width, paths in screenshot_index.items():
        _contact_sheet(
            paths,
            out / "human_review_contact_sheets" / f"stage_a_{width}.jpg",
            title=f"Issue111 Stage A real-image sales samples — {width}px",
        )

    category_counts = effective_seed["issue111_provenance"]["category_counts"]
    all_binding_traces_complete = all(
        binding["trace"].get("candidate_asset_ids")
        and binding["trace"].get("candidate_rights_decisions")
        and binding["trace"].get("selected_asset_id")
        and binding["trace"].get("binary_sha256")
        and binding["trace"].get("crop_variant_id")
        and binding["trace"].get("renderer_binding_id")
        for row in sample_results.values()
        for binding in row["selected_bindings"].values()
    )
    manifest = {
        "schema_version": "issue111_stage_a_real_image_sales_sample_qa_evidence_v1",
        "baseline_main_sha": BASELINE_MAIN_SHA,
        "scope": sorted(EXPECTED_FLOOR),
        "stage_a_inventory": {
            "distinct_assets": len(catalog),
            "category_counts": category_counts,
            "floor_complete": category_counts == EXPECTED_FLOOR,
            "all_acquired_again_for_issue111": len(acquisition) == 62,
        },
        "catalog_version": version,
        "sample_count": len(sample_results),
        "sample_ids": list(sample_results),
        "sample_results": sample_results,
        "usage_ledger": usage_ledger,
        "batch_reuse_uniqueness": reuse_report,
        "widths": list(WIDTHS),
        "screenshots": screenshots,
        "screenshot_count": len(screenshots),
        "all_family_topology_scene_order_preserved": all(row["architecture_preserved"] for row in sample_results.values()),
        "all_selected_rights_pass": all(
            binding["rights_gate"] in PASS_STATES
            for row in sample_results.values()
            for binding in row["selected_bindings"].values()
        ),
        "all_generic_illustrative_boundary_preserved": all(
            binding["evidence_status"] == "GENERIC_ILLUSTRATIVE_STOCK"
            for row in sample_results.values()
            for binding in row["selected_bindings"].values()
        ),
        "all_binding_traces_complete": all_binding_traces_complete,
        "all_images_loaded": all(row["images_loaded"] for row in screenshots),
        "all_overflow_free": all(not row["overflow"] for row in screenshots),
        "semantic_320_hard_gate": all(row["semantic_atomic"] for row in screenshots if row["width"] == 320),
        "all_render_trace_hash_joinable": all(row["trace_hash_joinable"] for row in screenshots),
        "all_generic_boundaries_visible": all(row["generic_boundary_visible"] for row in screenshots),
        "all_crop_heuristics_pass": all(row["min_crop_visible_fraction"] >= 0.42 for row in screenshots),
        "batch_hero_unique": reuse_report["hero_unique"],
        "batch_bundle_unique": reuse_report["bundle_signatures_unique"],
        "same_category_candidate_pool_identity_invariant": all(
            row["same_unfiltered_hero_candidate_pool"] for row in candidate_pool_invariance.values()
        ),
        "company_specific_authored_divergence": all(
            row["company_specific_divergence"] for row in authored_divergence.values()
        ),
        "asset_scarcity_family_switch": False,
        "company_reference_identity_routing": False,
        "random_selection": False,
        "human_visible_status": "PENDING_AOI_NOT_SELF_DECLARED",
        "real_image_sales_sample_readiness": "NOT_SELF_DECLARED_PENDING_SARAH_AND_AOI",
        "million_yen_quality": "NOT_SELF_DECLARED",
    }
    (out / "issue111_stage_a_sales_sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "issue111_binding_trace_report.json").write_text(
        json.dumps(
            {
                case_id: row["selected_bindings"]
                for case_id, row in sample_results.items()
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    required_gates = [
        len(catalog) == 62,
        category_counts == EXPECTED_FLOOR,
        len(sample_results) == 9,
        len(screenshots) == 81,
        manifest["all_family_topology_scene_order_preserved"],
        manifest["all_selected_rights_pass"],
        manifest["all_generic_illustrative_boundary_preserved"],
        manifest["all_binding_traces_complete"],
        manifest["all_images_loaded"],
        manifest["all_overflow_free"],
        manifest["semantic_320_hard_gate"],
        manifest["all_render_trace_hash_joinable"],
        manifest["all_generic_boundaries_visible"],
        manifest["all_crop_heuristics_pass"],
        manifest["batch_hero_unique"],
        manifest["batch_bundle_unique"],
        manifest["same_category_candidate_pool_identity_invariant"],
        manifest["company_specific_authored_divergence"],
    ]
    print(json.dumps({
        "catalog_version": version,
        "stage_a_inventory": manifest["stage_a_inventory"],
        "samples": {
            case_id: {
                "category": row["business_category"],
                "family": row["family_id"],
                "bindings": {
                    key: value["asset_id"] for key, value in row["selected_bindings"].items()
                },
            }
            for case_id, row in sample_results.items()
        },
        "screenshot_count": len(screenshots),
        "batch_reuse_uniqueness": reuse_report,
        "gates": {
            "all_family_topology_scene_order_preserved": manifest["all_family_topology_scene_order_preserved"],
            "all_selected_rights_pass": manifest["all_selected_rights_pass"],
            "all_binding_traces_complete": manifest["all_binding_traces_complete"],
            "semantic_320_hard_gate": manifest["semantic_320_hard_gate"],
            "all_render_trace_hash_joinable": manifest["all_render_trace_hash_joinable"],
            "all_crop_heuristics_pass": manifest["all_crop_heuristics_pass"],
        },
    }, ensure_ascii=False, indent=2))
    return 0 if all(required_gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
