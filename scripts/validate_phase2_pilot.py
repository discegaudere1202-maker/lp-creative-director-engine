from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)


def main() -> int:
    issues: list[str] = []
    refs_path = ROOT / "data/creative_mechanism_phase2_pilot_references.csv"
    matrix_path = ROOT / "data/creative_mechanism_phase1_2_pilot_coverage_matrix.csv"
    with refs_path.open(encoding="utf-8", newline="") as handle:
        refs = list(csv.DictReader(handle))
    with matrix_path.open(encoding="utf-8", newline="") as handle:
        matrix = list(csv.DictReader(handle))
    if len(refs) != 100:
        fail(f"reference count={len(refs)}", issues)
    if len(matrix) != 20:
        fail(f"matrix cell count={len(matrix)}", issues)
    if len({r["reference_id"] for r in refs}) != len(refs):
        fail("duplicate reference_id", issues)
    if len({r["canonical_url"] for r in refs}) != len(refs):
        fail("duplicate canonical_url", issues)
    cell = lambda r: (r["slot_id"], r["pool_type"], r["business_archetype"], r["industry"], r["market_scope"], r["discovery_source_class"])
    counts = Counter(cell(r) for r in refs)
    matrix_cells = {cell(r) for r in matrix}
    if set(counts) != matrix_cells:
        fail("reference cells do not equal Coverage Matrix cells", issues)
    if set(counts.values()) != {5}:
        fail(f"cell counts={sorted(counts.values())}", issues)
    required = {"reference_id", "brand", "company", "url", "canonical_url", "industry", "business_archetype", "pool_type", "discovery_source_class", "evidence_source_roles", "original_evidence_status", "evidence_grade", "desktop_observation_status", "mobile_observation_status", "strong_hold_reject", "decision_reason", "source_trace"}
    for r in refs:
        if not required.issubset(r):
            fail(f"missing reference field: {r.get('reference_id')}", issues)
        if "ORIGINAL_LIVE" not in json.loads(r["evidence_source_roles"]):
            fail(f"no Original evidence role: {r['reference_id']}", issues)
    scene_path = ROOT / "data/creative_mechanism_phase2_scene_evidence.jsonl"
    scenes = [json.loads(line) for line in scene_path.read_text(encoding="utf-8").splitlines()]
    if len(scenes) != 400:
        fail(f"scene evidence count={len(scenes)}", issues)
    if {s["reference_id"] for s in scenes} != {r["reference_id"] for r in refs}:
        fail("scene evidence reference coverage mismatch", issues)
    snapshot_fields = {"captured_at", "viewport", "original_url", "evidence_locator", "screenshot_identifier", "content_hash"}
    if any(not snapshot_fields.issubset(s) for s in scenes):
        fail("scene snapshot field missing", issues)
    mechanisms = [json.loads(line) for line in (ROOT / "data/creative_mechanism_phase2_mechanism_candidates.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(mechanisms) < 20:
        fail(f"mechanism candidate count={len(mechanisms)}", issues)
    if any(m.get("promotion_state") != "CANDIDATE" for m in mechanisms):
        fail("non-candidate mechanism found", issues)
    issues_path = ROOT / "data/creative_mechanism_phase2_architecture_issues.jsonl"
    if not issues_path.read_text(encoding="utf-8").strip():
        fail("architecture issue ledger is empty", issues)
    config = json.loads((ROOT / "config/creative_mechanism_db_architecture_v1_2_2.json").read_text(encoding="utf-8"))
    if config["schema_version"] != "1.2.2":
        fail("not using v1.2.2 config", issues)
    if config["phase2_gate"]["collection_started"] is not False:
        fail("collection_started is not false", issues)
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1
    print("PASS: Phase 2 100-reference Pilot is internally consistent")
    print(f"references={len(refs)} scenes={len(scenes)} mechanisms={len(mechanisms)}")
    print(f"status={Counter(r['strong_hold_reject'] for r in refs)}")
    print("collection_started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
