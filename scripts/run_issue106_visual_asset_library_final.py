"""Final Issue #106 evidence runner with Sarah visual-risk corrections.

The underlying runtime/evidence logic remains the Issue #106 runner. This wrapper
only patches the candidate seed before acquisition so exact binaries that failed
Sarah's human visual-risk audit cannot enter the normalized catalog.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import run_issue106_visual_asset_library as base

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS_PATH = ROOT / "data/visual_asset_library/providers/pexels_stage_a_sarah_corrections_v1.json"
ORIGINAL_LOAD_JSON = base._load_json


def _corrected_load_json(path: Path):
    data = ORIGINAL_LOAD_JSON(path)
    if path.name != "pexels_stage_a_seed_v1.json":
        return data
    corrections = ORIGINAL_LOAD_JSON(CORRECTIONS_PATH)
    blocked = {row["asset_id"] for row in corrections["blocked_asset_ids"]}
    assets = [copy.deepcopy(row) for row in data["assets"] if row["asset_id"] not in blocked]
    assets.extend(copy.deepcopy(corrections["replacement_assets"]))
    ids = [row["asset_id"] for row in assets]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Sarah correction produced duplicate asset ids")
    if blocked.intersection(ids):
        raise RuntimeError("Sarah-blocked visual-risk asset survived corrected seed")
    replacement_ids = {row["asset_id"] for row in corrections["replacement_assets"]}
    if not replacement_ids.issubset(ids):
        raise RuntimeError("Sarah replacement asset missing from corrected seed")
    corrected = copy.deepcopy(data)
    corrected["schema_version"] = "issue106_pexels_stage_a_seed_sarah_corrected_v1"
    corrected["policy"] += "; Sarah exact-binary visual-risk corrections applied before ingestion"
    corrected["assets"] = assets
    corrected["sarah_visual_risk_corrections"] = {
        "blocked_asset_ids": sorted(blocked),
        "replacement_asset_ids": sorted(replacement_ids),
        "contract": str(CORRECTIONS_PATH.relative_to(ROOT)),
    }
    return corrected


def _out_dir_from_argv() -> Path:
    if "--out" in sys.argv:
        index = sys.argv.index("--out")
        if index + 1 < len(sys.argv):
            return Path(sys.argv[index + 1])
    return Path("artifacts/issue106_visual_asset_library")


def main() -> int:
    base._load_json = _corrected_load_json
    code = base.main()
    if code != 0:
        return code
    out = _out_dir_from_argv()
    manifest_path = out / "issue106_visual_asset_library_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    corrections = ORIGINAL_LOAD_JSON(CORRECTIONS_PATH)
    manifest["sarah_technical_evidence_audit"] = {
        "state": "CORRECTED_AND_REGENERATED_PENDING_AOI",
        "blocked_asset_ids": [row["asset_id"] for row in corrections["blocked_asset_ids"]],
        "replacement_asset_ids": [row["asset_id"] for row in corrections["replacement_assets"]],
        "reason_codes": [row["reason"] for row in corrections["blocked_asset_ids"]],
        "correction_contract": str(CORRECTIONS_PATH.relative_to(ROOT)),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "sarah_visual_risk_corrections.json").write_text(
        json.dumps(corrections, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
