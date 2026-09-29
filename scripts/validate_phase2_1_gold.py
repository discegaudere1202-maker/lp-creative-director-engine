"""Validate the Phase 2.1 evidence ledger without treating absence as a pass."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]

def validate(root=ROOT, artifact=None):
    d = root / "data"
    refs = list(csv.DictReader((d / "creative_mechanism_phase2_1_gold_references.csv").open()))
    scenes = lines(d / "creative_mechanism_phase2_1_gold_scene_evidence.jsonl")
    snaps = lines(d / "creative_mechanism_phase2_1_gold_snapshots.jsonl")
    mechs = lines(d / "creative_mechanism_phase2_1_gold_mechanisms.jsonl")
    claims = lines(d / "creative_mechanism_phase2_1_claim_evidence.jsonl")
    access = lines(d / "creative_mechanism_phase2_1_accessibility.jsonl")
    legacy = lines(d / "creative_mechanism_phase2_1_legacy_candidate_review.jsonl")
    old = list(csv.DictReader((d / "creative_mechanism_phase2_pilot_references.csv").open()))
    cfg = json.loads((root / "config/creative_mechanism_db_architecture_v1_3.json").read_text())
    assert len(old) == 100 and len(refs) == 20 and len({r["slot_id"] for r in refs}) == 20
    assert {r["reference_id"] for r in refs} <= {r["reference_id"] for r in old}
    assert len(scenes) == 80 and len({s["scene_evidence_id"] for s in scenes}) == 80
    assert len(snaps) == 118 and len(legacy) == 25
    assert all(x["status"] == "PROVISIONAL_FROM_PHASE2" for x in legacy)
    by_scene = {s["scene_evidence_id"]: s for s in scenes}
    by_ref = {r["reference_id"]: r for r in refs}
    for r in refs:
        assert r["desktop_observation_status"] == r["mobile_observation_status"] == "OBSERVED"
        assert r["strong_hold_reject"] == "HOLD"
        assert r["evidence_status"] == "TEMPORARY_CAPTURE"
        assert r["score_audit_status"] == "EVIDENCE_CAPTURED_RESCORING_REQUIRED"
        assert r["final_url"].startswith("https://")
        assert len(json.loads(r["scene_evidence_ids"])) == 4
    for s in scenes:
        assert s["reference_id"] in by_ref
        assert s["observation_state"] in {"OBSERVED","MISSING","NOT_OBSERVED","NOT_APPLICABLE"}
        assert s["concrete_locator"] and s["source_artifact"].startswith("https://github.com/")
        if s["observation_state"] == "OBSERVED":
            assert s["screenshot_identifier"] and s["content_hash"]
            assert s["scene_crop_identifier"] and s["visible_structure"] and s["observed_facts"]
            assert "Observed when capture exists" not in str(s)
            assert "Scene structure recorded from official page candidate" not in str(s)
        else:
            assert not s["mechanism_subject_visible"]
    for m in mechs:
        src = m["source_scene_evidence_ids"]
        assert src and len(src) == len(set(src)) == m["evidence_count"]
        assert m["status"] == "CANDIDATE"
        assert all(by_scene[s]["observation_state"] == "OBSERVED" and by_scene[s]["mechanism_subject_visible"] for s in src)
        refs_m = {by_scene[s]["reference_id"] for s in src}
        assert m["reference_count"] == len(refs_m) and m["reference_lps"] == sorted(refs_m)
        assert m["unique_brand_count"] == len({by_ref[r]["brand"] for r in refs_m})
        for key in ("unique_agency_count","unique_campaign_count"):
            assert m[key] == "UNKNOWN"
    for s in snaps:
        assert s["screenshot_identifier"] and len(s["content_hash"]) == 64
        assert s["archive_locator"] == "TEMPORARY_CAPTURE:" + s["screenshot_identifier"]
        if artifact:
            assert hashlib.sha256((artifact / s["screenshot_identifier"]).read_bytes()).hexdigest() == s["content_hash"]
    for r in ("P05-R04","P06-R02","P17-R01"):
        assert any(c["reference_id"] == r for c in claims)
    for c in claims:
        assert c["scene_evidence_id"] in by_scene and c["source_locator"] and c["risk_flag"]
    assert {x["reference_id"] for x in access} == {"P06-R02","P18-R01"}
    assert all(x["assessment"] != "PASS" and x["keyboard_navigation"] == "NOT_OBSERVED" for x in access)
    assert not cfg["phase2_gate"]["remaining_80_allowed"] and not cfg["phase2_gate"]["bulk_collection_allowed"]
    assert cfg["evidence_grounding_contract"]["scene_source_state"] == "OBSERVED"
    return {"references":len(refs),"scenes":len(scenes),"snapshots":len(snaps),"candidates":len(mechs),
            "claims":len(claims),"accessibility":len(access),"archive":"TEMPORARY_CAPTURE","final_scored":0}

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--artifact-root",type=Path)
    print("PASS",json.dumps(validate(artifact=p.parse_args().artifact_root)))
