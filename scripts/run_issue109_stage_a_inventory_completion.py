"""Issue #109 — complete Stage A current-industry visual inventory to the accepted floor.

This runner reuses the Issue #106 acquisition/normalization/rights/runtime path. It only
extends the corrected Pexels candidate seed, emits durable inventory/provenance evidence,
and generates human-review contact sheets from the exact downloaded binaries.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
from typing import Any

from PIL import Image, ImageDraw, ImageOps

import run_issue106_visual_asset_library as base
from lp_engine.visual_asset_library import PASS_STATES, evaluate_visual_asset_rights

ROOT = Path(__file__).resolve().parents[1]
BASE_SEED = ROOT / "data/visual_asset_library/providers/pexels_stage_a_seed_v1.json"
SARAH_CORRECTIONS = ROOT / "data/visual_asset_library/providers/pexels_stage_a_sarah_corrections_v1.json"
COMPLETION_SEED = ROOT / "data/visual_asset_library/providers/pexels_stage_a_completion_issue109_v1.json"
ORIGINAL_LOAD_JSON = base._load_json

EXPECTED = {
    "skincare_cosmetics_product": 10,
    "hair_salon": 18,
    "barber": 18,
    "pilates_studio": 16,
}


def _issue109_load_json(path: Path) -> Any:
    data = ORIGINAL_LOAD_JSON(path)
    if path.name != BASE_SEED.name:
        return data

    corrections = ORIGINAL_LOAD_JSON(SARAH_CORRECTIONS)
    completion = ORIGINAL_LOAD_JSON(COMPLETION_SEED)
    blocked = {row["asset_id"] for row in corrections["blocked_asset_ids"]}

    assets = [copy.deepcopy(row) for row in data["assets"] if row["asset_id"] not in blocked]
    assets.extend(copy.deepcopy(corrections["replacement_assets"]))
    assets.extend(copy.deepcopy(completion["assets"]))

    ids = [row["asset_id"] for row in assets]
    if len(ids) != len(set(ids)):
        duplicates = sorted({asset_id for asset_id in ids if ids.count(asset_id) > 1})
        raise RuntimeError(f"Issue109 candidate inventory contains duplicate asset IDs: {duplicates}")
    if blocked.intersection(ids):
        raise RuntimeError("Sarah-blocked asset survived Issue109 combined seed")

    corrected = copy.deepcopy(data)
    corrected["schema_version"] = "issue109_stage_a_completion_combined_seed_v1"
    corrected["policy"] = (
        data.get("policy", "")
        + "; Sarah exact-binary corrections preserved; Issue109 completion candidates appended"
    )
    corrected["assets"] = assets
    corrected["issue109_provenance"] = {
        "baseline_seed": str(BASE_SEED.relative_to(ROOT)),
        "sarah_correction_contract": str(SARAH_CORRECTIONS.relative_to(ROOT)),
        "completion_seed": str(COMPLETION_SEED.relative_to(ROOT)),
        "blocked_asset_ids": sorted(blocked),
    }
    return corrected


def _out_dir() -> Path:
    if "--out" in sys.argv:
        idx = sys.argv.index("--out")
        if idx + 1 < len(sys.argv):
            return Path(sys.argv[idx + 1])
    return Path("artifacts/issue109_stage_a_inventory")


def _contact_sheet(image_paths: list[Path], output: Path, *, title: str) -> None:
    thumb_w, thumb_h = 320, 230
    label_h = 42
    cols = 4
    rows = (len(image_paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, 48 + rows * (thumb_h + label_h)), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 14), title, fill="black")
    for index, path in enumerate(image_paths):
        image = Image.open(path).convert("RGB")
        fitted = ImageOps.contain(image, (thumb_w - 12, thumb_h - 12))
        tile = Image.new("RGB", (thumb_w, thumb_h), "#efefef")
        tile.paste(fitted, ((thumb_w - fitted.width) // 2, (thumb_h - fitted.height) // 2))
        x = (index % cols) * thumb_w
        y = 48 + (index // cols) * (thumb_h + label_h)
        sheet.paste(tile, (x, y))
        draw.text((x + 8, y + thumb_h + 8), path.stem, fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def _emit_issue109_reports(out: Path) -> None:
    catalog = json.loads((out / "normalized_asset_catalog.json").read_text(encoding="utf-8"))
    completion = ORIGINAL_LOAD_JSON(COMPLETION_SEED)
    corrections = ORIGINAL_LOAD_JSON(SARAH_CORRECTIONS)

    category_rows = []
    all_ids = {item["asset_id"] for item in catalog}
    exact_total = 0
    for category, required in EXPECTED.items():
        ids = sorted({item["asset_id"] for item in catalog if category in item["business_category_tags"]})
        exact_total += len(ids)
        category_rows.append({
            "business_category": category,
            "required": required,
            "actual": len(ids),
            "gap": max(0, required - len(ids)),
            "complete": len(ids) >= required,
            "asset_ids": ids,
        })

    rights_rows = []
    rights_failures = []
    provenance_failures = []
    for item in catalog:
        rights = evaluate_visual_asset_rights(item, {
            "crop_required": True,
            "can_render_attribution": True,
            "evidence_boundary": "GENERIC_ILLUSTRATIVE_STOCK",
            "current_binary_sha256": item["binary_sha256"],
        })
        row = {
            "asset_id": item["asset_id"],
            "source_provider": item["source_provider"],
            "source_id": item["source_id"],
            "source_url": item["source_url"],
            "creator": item["creator"],
            "binary_sha256": item["binary_sha256"],
            "checked_at": item["checked_at"],
            "license_terms_checked_at": item["license_terms_checked_at"],
            "rights_state": rights["state"],
            "rights_conditions": rights["conditions"],
            "evidence_status": item["evidence_status"],
            "trademark_logo_risk": item["trademark_logo_risk"],
        }
        rights_rows.append(row)
        if rights["state"] not in PASS_STATES:
            rights_failures.append(row)
        if not item.get("raw_provenance") or not item.get("binary_sha256"):
            provenance_failures.append(item["asset_id"])

    completion_ids = {row["asset_id"] for row in completion["assets"]}
    missing_completion = sorted(completion_ids - all_ids)
    report = {
        "schema_version": "issue109_stage_a_inventory_completion_report_v1",
        "stage": "A_CORE",
        "total_required": 62,
        "total_actual_category_sum": exact_total,
        "distinct_catalog_assets": len(all_ids),
        "stage_a_floor_complete": all(row["complete"] for row in category_rows) and exact_total >= 62,
        "categories": category_rows,
        "completion_candidate_count": len(completion_ids),
        "completion_candidates_missing_after_ingestion": missing_completion,
        "all_asset_rights_pass": not rights_failures,
        "rights_failures": rights_failures,
        "all_provenance_present": not provenance_failures,
        "provenance_failures": provenance_failures,
        "sarah_rights_evidence_audit_required": True,
        "real_image_sales_sample_qa_start_gate": False,
        "gate_reason": "Exact 62/62 inventory is necessary but Sarah rights/evidence audit remains the next gate.",
    }
    (out / "issue109_inventory_completion_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "issue109_provenance_rights_report.json").write_text(
        json.dumps({"assets": rights_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (out / "issue109_rejected_held_candidates.json").write_text(
        json.dumps({
            "blocked_from_prior_sarah_audit": corrections["blocked_asset_ids"],
            "issue109_new_holds": [],
            "note": "Populate issue109_new_holds if exact-binary human review rejects any completion candidate before final acceptance.",
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    acquisition_dir = out / "acquisition"
    categories: dict[str, list[Path]] = {key: [] for key in EXPECTED}
    item_by_id = {item["asset_id"]: item for item in catalog}
    for path in sorted(acquisition_dir.glob("*.jpg")):
        item = item_by_id.get(path.stem)
        if not item:
            continue
        for category in EXPECTED:
            if category in item["business_category_tags"]:
                categories[category].append(path)
    for category, paths in categories.items():
        _contact_sheet(paths, out / "human_review_contact_sheets" / f"{category}.jpg", title=f"Issue109 exact binaries — {category}")

    if not report["stage_a_floor_complete"]:
        raise RuntimeError(f"Stage A inventory floor incomplete: {category_rows}")
    if rights_failures:
        raise RuntimeError(f"Asset-level rights failures remain: {[row['asset_id'] for row in rights_failures]}")
    if provenance_failures:
        raise RuntimeError(f"Provenance failures remain: {provenance_failures}")
    if missing_completion:
        raise RuntimeError(f"Completion candidates missing after ingestion: {missing_completion}")


def main() -> int:
    base._load_json = _issue109_load_json
    code = base.main()
    if code != 0:
        return code
    _emit_issue109_reports(_out_dir())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
