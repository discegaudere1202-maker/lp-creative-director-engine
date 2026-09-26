"""Issue #109 final runner applying exact-binary human-audit and Sarah RETURN corrections."""
from __future__ import annotations

from collections import Counter
import copy
import json
from pathlib import Path

import run_issue109_stage_a_inventory_completion as issue109

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = ROOT / "data/visual_asset_library/providers/pexels_stage_a_issue109_corrections_v1.json"
SARAH_RETURN_CORRECTIONS = ROOT / "data/visual_asset_library/providers/pexels_stage_a_issue109_sarah_return_v1.json"


def _dedupe_rows(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for row in rows:
        asset_id = str(row.get("asset_id") or "")
        if not asset_id or asset_id in seen:
            continue
        seen.add(asset_id)
        result.append(copy.deepcopy(row))
    return result


def _build_corrected_completion_seed() -> Path:
    completion = issue109.ORIGINAL_LOAD_JSON(issue109.COMPLETION_SEED)
    corrections = issue109.ORIGINAL_LOAD_JSON(CORRECTIONS)
    sarah_return = issue109.ORIGINAL_LOAD_JSON(SARAH_RETURN_CORRECTIONS)

    correction_blocked = {row["asset_id"] for row in corrections["blocked_asset_ids"]}
    return_blocked = {row["asset_id"] for row in sarah_return["blocked_asset_ids"]}
    blocked = correction_blocked | return_blocked

    assets = [copy.deepcopy(row) for row in completion["assets"] if row["asset_id"] not in blocked]
    # Sarah RETURN can block an asset that was introduced by the prior Issue109
    # replacement set, so fail closed there too instead of filtering only the
    # original completion seed.
    assets.extend(
        copy.deepcopy(row)
        for row in corrections["replacement_assets"]
        if row["asset_id"] not in return_blocked
    )
    assets.extend(copy.deepcopy(sarah_return["replacement_assets"]))

    ids = [row["asset_id"] for row in assets]
    if len(ids) != 49 or len(ids) != len(set(ids)):
        raise RuntimeError(f"Issue109 corrected completion set must contain 49 distinct assets, got {len(ids)}")
    if blocked.intersection(ids):
        raise RuntimeError(f"Issue109 blocked asset survived corrected completion set: {sorted(blocked.intersection(ids))}")

    runtime_seed = ROOT / "artifacts/issue109_runtime_completion_seed.json"
    runtime_seed.parent.mkdir(parents=True, exist_ok=True)
    corrected = copy.deepcopy(completion)
    corrected["schema_version"] = "issue109_pexels_stage_a_completion_candidate_corrected_v3"
    corrected["assets"] = assets
    corrected["candidate_corrections"] = {
        "contracts": [
            str(CORRECTIONS.relative_to(ROOT)),
            str(SARAH_RETURN_CORRECTIONS.relative_to(ROOT)),
        ],
        "blocked_asset_ids": sorted(blocked),
        "replacement_asset_ids": sorted(
            row["asset_id"]
            for row in assets
            if row["asset_id"] not in {item["asset_id"] for item in completion["assets"]}
        ),
        "sarah_return_blocked_asset_ids": sorted(return_blocked),
        "sarah_return_replacement_asset_ids": sorted(row["asset_id"] for row in sarah_return["replacement_assets"]),
    }
    runtime_seed.write_text(json.dumps(corrected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return runtime_seed


def _postprocess_reports(out: Path) -> None:
    prior_sarah = issue109.ORIGINAL_LOAD_JSON(issue109.SARAH_CORRECTIONS)
    corrections = issue109.ORIGINAL_LOAD_JSON(CORRECTIONS)
    sarah_return = issue109.ORIGINAL_LOAD_JSON(SARAH_RETURN_CORRECTIONS)

    issue109_holds = _dedupe_rows(
        [copy.deepcopy(row) for row in corrections["blocked_asset_ids"]]
        + [copy.deepcopy(row) for row in sarah_return["blocked_asset_ids"]]
    )
    rejected_report = {
        "schema_version": "issue109_rejected_held_candidates_v2",
        "blocked_from_prior_sarah_audit": prior_sarah["blocked_asset_ids"],
        "issue109_new_holds": issue109_holds,
        "sarah_return_holds": sarah_return["blocked_asset_ids"],
        "issue109_new_hold_count": len(issue109_holds),
        "note": "All listed held/rejected assets are excluded from the final 62 rights-pass inventory. Sarah RETURN replacement is re-acquired and re-hashed by this workflow.",
    }
    (out / "issue109_rejected_held_candidates.json").write_text(
        json.dumps(rejected_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    catalog = json.loads((out / "normalized_asset_catalog.json").read_text(encoding="utf-8"))
    categories: dict[str, dict] = {}
    for category in issue109.EXPECTED:
        rows = [item for item in catalog if category in item["business_category_tags"]]
        creators = Counter(item["creator"] for item in rows)
        content_classes = Counter(item["content_class"] for item in rows)
        media_roles = Counter(role for item in rows for role in item["eligible_media_roles"])
        categories[category] = {
            "asset_count": len(rows),
            "distinct_asset_ids": len({item["asset_id"] for item in rows}),
            "distinct_creators": len(creators),
            "creator_distribution": dict(sorted(creators.items())),
            "content_class_distribution": dict(sorted(content_classes.items())),
            "eligible_media_role_distribution": dict(sorted(media_roles.items())),
            "max_single_creator_asset_count": max(creators.values(), default=0),
        }

    near_duplicate_blocks = [
        row for row in issue109_holds if row.get("reason") == "ANTI_REPETITION_NEAR_DUPLICATE"
    ]
    diversity_report = {
        "schema_version": "issue109_diversity_anti_repetition_report_v1",
        "distinct_catalog_assets": len({item["asset_id"] for item in catalog}),
        "categories": categories,
        "known_near_duplicate_blocks": near_duplicate_blocks,
        "known_near_duplicate_block_count": len(near_duplicate_blocks),
        "sarah_return_replacement": {
            "removed_asset_id": "pexels-13809242",
            "replacement_asset_id": "pexels-30807437",
            "replacement_creator": "James Collington",
            "replacement_visual_cluster": "generic_barber_pole_closeup",
            "same_photoshoot_as_removed_asset": False,
        },
        "anti_repetition_status": "PASS_KNOWN_HUMAN_REVIEWED_CLUSTERS",
        "note": "Known same-photoshoot/near-duplicate candidates were excluded from count padding; exact-binary human review remains authoritative over metadata-only similarity checks.",
    }
    (out / "issue109_diversity_anti_repetition_report.json").write_text(
        json.dumps(diversity_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    runtime_seed = _build_corrected_completion_seed()
    issue109.COMPLETION_SEED = runtime_seed

    # Make the effective combined seed explicit instead of depending on import-time globals.
    def corrected_loader(path: Path):
        data = issue109.ORIGINAL_LOAD_JSON(path)
        if path.name != issue109.BASE_SEED.name:
            return data
        sarah = issue109.ORIGINAL_LOAD_JSON(issue109.SARAH_CORRECTIONS)
        completion = issue109.ORIGINAL_LOAD_JSON(runtime_seed)
        blocked = {row["asset_id"] for row in sarah["blocked_asset_ids"]}
        assets = [copy.deepcopy(row) for row in data["assets"] if row["asset_id"] not in blocked]
        assets.extend(copy.deepcopy(sarah["replacement_assets"]))
        assets.extend(copy.deepcopy(completion["assets"]))
        ids = [row["asset_id"] for row in assets]
        if len(ids) != 62 or len(ids) != len(set(ids)):
            raise RuntimeError(f"Issue109 effective Stage A seed must contain 62 distinct assets, got {len(ids)}")
        corrected = copy.deepcopy(data)
        corrected["schema_version"] = "issue109_stage_a_completion_effective_seed_v3"
        corrected["policy"] = data.get("policy", "") + "; Sarah corrections + Issue109 exact-binary corrections + Sarah RETURN correction applied"
        corrected["assets"] = assets
        corrected["issue109_provenance"] = {
            "baseline_seed": str(issue109.BASE_SEED.relative_to(ROOT)),
            "sarah_correction_contract": str(issue109.SARAH_CORRECTIONS.relative_to(ROOT)),
            "completion_seed": str(runtime_seed.relative_to(ROOT)),
            "issue109_candidate_corrections": str(CORRECTIONS.relative_to(ROOT)),
            "issue109_sarah_return_corrections": str(SARAH_RETURN_CORRECTIONS.relative_to(ROOT)),
            "sarah_blocked_asset_ids": sorted(blocked),
        }
        return corrected

    issue109._issue109_load_json = corrected_loader
    code = issue109.main()
    if code != 0:
        return code
    _postprocess_reports(issue109._out_dir())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
