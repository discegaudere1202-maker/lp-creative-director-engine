import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_refs():
    with (ROOT / "data/creative_mechanism_phase2_pilot_references.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_pilot_has_100_references_and_matrix_coverage():
    refs = load_refs()
    with (ROOT / "data/creative_mechanism_phase1_2_pilot_coverage_matrix.csv").open(encoding="utf-8", newline="") as handle:
        matrix = list(csv.DictReader(handle))
    assert len(refs) == 100
    assert len(matrix) == 20
    cells = {(r["slot_id"], r["pool_type"], r["business_archetype"], r["industry"], r["market_scope"], r["discovery_source_class"]) for r in refs}
    assert len(cells) == 20
    matrix_cells = {(r["slot_id"], r["pool_type"], r["business_archetype"], r["industry"], r["market_scope"], r["discovery_source_class"]) for r in matrix}
    assert cells == matrix_cells
    counts = {cell: 0 for cell in cells}
    for ref in refs:
        cell = (ref["slot_id"], ref["pool_type"], ref["business_archetype"], ref["industry"], ref["market_scope"], ref["discovery_source_class"])
        counts[cell] += 1
    assert set(counts.values()) == {5}


def test_reference_trace_and_decision_fields_are_complete():
    refs = load_refs()
    required = {"reference_id", "brand", "company", "url", "canonical_url", "industry", "business_archetype", "pool_type", "discovery_source_class", "evidence_source_roles", "original_evidence_status", "evidence_grade", "live_page_status", "live_page_url", "desktop_observation_status", "mobile_observation_status", "strong_hold_reject", "decision_reason", "source_trace"}
    assert all(required.issubset(row) for row in refs)
    assert len({row["reference_id"] for row in refs}) == 100
    assert len({row["canonical_url"] for row in refs}) == 100
    assert all("ORIGINAL_LIVE" in json.loads(row["evidence_source_roles"]) for row in refs)
    assert {row["strong_hold_reject"] for row in refs} <= {"STRONG", "HOLD", "REJECT"}
    assert sum(row["strong_hold_reject"] == "STRONG" for row in refs) + sum(row["strong_hold_reject"] == "HOLD" for row in refs) + sum(row["strong_hold_reject"] == "REJECT" for row in refs) == 100


def test_quality_uses_only_v122_levels_and_motion_missingness_is_explicit():
    refs = load_refs()
    assert {r["relevance_level"] for r in refs} <= {"DIRECT", "SUPPORTING", "CONTEXTUAL", "WEAK", "IRRELEVANT"}
    assert {r["directness_level"] for r in refs} <= {"EXPLICIT_OFFICIAL", "EXPLICIT_THIRD_PARTY", "SPECIFIC_IMPLICIT", "VISUAL_ONLY", "ABSENT"}
    assert {r["confidence_level"] for r in refs} <= {"E4", "E3", "E2", "E1", "E0"}
    assert all(r["evidence_grade"] == r["confidence_level"] for r in refs)
    assert any(r["motion_quality_score"] == "NOT_APPLICABLE" for r in refs)
    assert any(r["mobile_observation_status"] == "NOT_OBSERVED" for r in refs)


def test_scene_evidence_covers_every_reference_and_snapshot_fields():
    refs = load_refs()
    ref_ids = {r["reference_id"] for r in refs}
    scenes = [json.loads(line) for line in (ROOT / "data/creative_mechanism_phase2_scene_evidence.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(scenes) == 400
    assert {s["reference_id"] for s in scenes} == ref_ids
    required = {"captured_at", "viewport", "original_url", "evidence_locator", "screenshot_identifier", "content_hash"}
    assert all(required.issubset(scene) for scene in scenes)
    assert {s["scene"] for s in scenes} == {"HERO", "PROOF", "CONVERSION", "MOBILE"}


def test_candidate_mechanisms_have_required_schema_and_are_not_canonical():
    required = {"mechanism_id", "mechanism_name", "category", "subcategory", "purpose", "marketing_job", "user_effect", "best_for", "avoid_when", "best_scene", "compatible_archetypes", "evidence_authority", "expression_driver", "visual_impact", "conversion_utility", "automation_difficulty", "html_implementation_difficulty", "motion_dependency", "responsive_risk", "performance_risk", "accessibility_risk", "required_media", "reference_lps", "implementation_notes", "combination_notes", "anti_pattern", "confidence", "evidence_count"}
    mechanisms = [json.loads(line) for line in (ROOT / "data/creative_mechanism_phase2_mechanism_candidates.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(mechanisms) == 25
    assert all(required.issubset(m) for m in mechanisms)
    assert {m["promotion_state"] for m in mechanisms} == {"CANDIDATE"}


def test_architecture_issues_and_v122_gate_are_present():
    issues = [json.loads(line) for line in (ROOT / "data/creative_mechanism_phase2_architecture_issues.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(issues) >= 1
    config = json.loads((ROOT / "config/creative_mechanism_db_architecture_v1_2_2.json").read_text(encoding="utf-8"))
    assert config["schema_version"] == "1.2.2"
    assert config["phase2_gate"]["collection_started"] is False
    assert config["phase2_gate"]["pilot_allowed_only_after"] == "Phase 1.2.2 PM Approval"
