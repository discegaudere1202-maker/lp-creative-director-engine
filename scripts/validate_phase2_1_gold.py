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
    with (d / "creative_mechanism_phase2_1_gold_references.csv").open(newline="", encoding="utf-8") as fh:
        refs = list(csv.DictReader(fh))
    scenes = lines(d / "creative_mechanism_phase2_1_gold_scene_evidence.jsonl")
    snaps = lines(d / "creative_mechanism_phase2_1_gold_snapshots.jsonl")
    mechs = lines(d / "creative_mechanism_phase2_1_gold_mechanisms.jsonl")
    scores = lines(d / "creative_mechanism_phase2_1_gold_scores.jsonl")
    claims = lines(d / "creative_mechanism_phase2_1_claim_evidence.jsonl")
    access = lines(d / "creative_mechanism_phase2_1_accessibility.jsonl")
    legacy = lines(d / "creative_mechanism_phase2_1_legacy_candidate_review.jsonl")
    with (d / "creative_mechanism_phase2_pilot_references.csv").open(newline="", encoding="utf-8") as fh:
        old = list(csv.DictReader(fh))
    cfg = json.loads((root / "config/creative_mechanism_db_architecture_v1_3.json").read_text())
    assert len(old) == 100 and len(refs) == 20 and len({r["slot_id"] for r in refs}) == 20
    assert {r["reference_id"] for r in refs} <= {r["reference_id"] for r in old}
    assert len(scenes) == 80 and len({s["scene_evidence_id"] for s in scenes}) == 80
    assert len(snaps) == 118 and len(legacy) == 25 and len(scores) == 20
    assert all(x["status"] == "PROVISIONAL_FROM_PHASE2" for x in legacy)
    by_scene = {s["scene_evidence_id"]: s for s in scenes}
    by_ref = {r["reference_id"]: r for r in refs}
    for r in refs:
        assert r["desktop_observation_status"] == r["mobile_observation_status"] == "OBSERVED"
        assert r["strong_hold_reject"] == "HOLD"
        assert r["evidence_status"] == "DURABLE_VERIFIED"
        assert r["score_audit_status"] == "EVIDENCE_BACKED_FINAL"
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
        assert s["archive_status"] == "DURABLE_VERIFIED" and s["archive_entry"] == "capture/" + s["screenshot_identifier"]
        if artifact:
            assert hashlib.sha256((artifact / s["screenshot_identifier"]).read_bytes()).hexdigest() == s["content_hash"]
    dims = cfg["scoring"]["dimensions"]
    for score in scores:
        assert score["reference_id"] in by_ref and score["score_audit_status"] == "EVIDENCE_BACKED_FINAL"
        assert score["source_scene_evidence_ids"] and not score["promotion_allowed"]
        assert all(by_scene[k]["observation_state"] == "OBSERVED" for k in score["source_scene_evidence_ids"])
        assert by_ref[score["reference_id"]]["overall_normalized_score"] == str(score["overall_normalized_score"])
        category_sum = 0
        denominator = 0
        for cat, block in dims.items():
            raw = score["raw_dimension_scores"][cat]
            assert all(k in block["weights"] and type(v) in (int,float) and 0 <= v <= 5 for k,v in raw.items())
            assert set(raw).isdisjoint(score["missingness"][cat])
            assert set(raw) | set(score["missingness"][cat]) == set(block["weights"])
            if raw:
                v = round(sum((rating/5)*block["weights"][key] for key,rating in raw.items()) /
                          sum(block["weights"][key] for key in raw)*block["target_max"],4)
                assert abs(v-score["category_scores"][cat]) < 0.00001
                category_sum += v
                denominator += block["target_max"]
            else: assert score["category_scores"][cat] is None
        assert denominator == score["normalization_denominator"]
        assert abs(round(category_sum/denominator*100,4)-score["overall_normalized_score"]) < 0.00001
    for r in ("P05-R04","P06-R02","P17-R01"):
        assert any(c["reference_id"] == r for c in claims)
    for c in claims:
        assert c["scene_evidence_id"] in by_scene and c["source_locator"] and c["risk_flag"]
    assert {x["reference_id"] for x in access} == {"P06-R02","P18-R01"}
    assert all(x["assessment"] != "PASS" and x["keyboard_navigation"] == "NOT_OBSERVED" for x in access)
    assert not cfg["phase2_gate"]["remaining_80_allowed"] and not cfg["phase2_gate"]["bulk_collection_allowed"]
    assert cfg["evidence_grounding_contract"]["scene_source_state"] == "OBSERVED"
    return {"references":len(refs),"scenes":len(scenes),"snapshots":len(snaps),"candidates":len(mechs),
            "claims":len(claims),"accessibility":len(access),"archive":"DURABLE_VERIFIED","final_scored":len(scores)}

if __name__ == "__main__":
    p=argparse.ArgumentParser(); p.add_argument("--artifact-root",type=Path)
    print("PASS",json.dumps(validate(artifact=p.parse_args().artifact_root)))
