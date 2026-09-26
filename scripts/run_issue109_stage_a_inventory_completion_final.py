"""Issue #109 final runner applying acquisition-time candidate corrections."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import run_issue109_stage_a_inventory_completion as issue109

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = ROOT / "data/visual_asset_library/providers/pexels_stage_a_issue109_corrections_v1.json"


def main() -> int:
    completion = issue109.ORIGINAL_LOAD_JSON(issue109.COMPLETION_SEED)
    corrections = issue109.ORIGINAL_LOAD_JSON(CORRECTIONS)
    blocked = {row["asset_id"] for row in corrections["blocked_asset_ids"]}
    assets = [copy.deepcopy(row) for row in completion["assets"] if row["asset_id"] not in blocked]
    assets.extend(copy.deepcopy(corrections["replacement_assets"]))
    ids = [row["asset_id"] for row in assets]
    if len(ids) != 49 or len(ids) != len(set(ids)):
        raise RuntimeError(f"Issue109 corrected completion set must contain 49 distinct assets, got {len(ids)}")

    runtime_seed = ROOT / "artifacts/issue109_runtime_completion_seed.json"
    runtime_seed.parent.mkdir(parents=True, exist_ok=True)
    corrected = copy.deepcopy(completion)
    corrected["schema_version"] = "issue109_pexels_stage_a_completion_candidate_corrected_v1"
    corrected["assets"] = assets
    corrected["candidate_corrections"] = {
        "contract": str(CORRECTIONS.relative_to(ROOT)),
        "blocked_asset_ids": sorted(blocked),
        "replacement_asset_ids": sorted(row["asset_id"] for row in corrections["replacement_assets"]),
    }
    runtime_seed.write_text(json.dumps(corrected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    issue109.COMPLETION_SEED = runtime_seed
    return issue109.main()


if __name__ == "__main__":
    raise SystemExit(main())
