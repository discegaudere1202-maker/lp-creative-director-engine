"""Auditable raw-dimension scores limited to captured Gold scenes.

Each vector is a reviewer judgement tied to the actual 1440/390 screenshots; these
are not performance estimates. Unseen dimensions remain NOT_OBSERVED and are
excluded under the v1.2.2 normalization formula.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Order is explicit below. Scores are reviewer judgements, not automatically
# inferred from the DOM or inherited from provisional Phase 2 scores.
# Design: hero, type, layout, media, hierarchy, brand, screenshot, distinctiveness.
# Conversion: CTA, navigation, clarity, decision size, customer state.
# Feasibility: mobile quality, responsive recomposition.
RAW = {
 "P01-R01": ([4,4,4,5,4,4,5,4],[3,3,3,3,3],[4,4]),
 "P02-R01": ([4,4,4,4,4,4,4,4],[2,3,2,2,3],[4,4]),
 "P03-R04": ([3,3,3,4,3,3,3,3],[4,4,4,4,4],[3,3]),
 "P04-R01": ([2,3,3,1,3,3,2,2],[3,4,3,3,3],[3,3]),
 "P05-R04": ([2,3,3,2,4,3,2,2],[4,4,4,3,4],[4,4]),
 "P06-R02": ([4,4,4,4,4,4,4,4],[4,4,4,4,5],[4,4]),
 "P07-R01": ([3,3,3,4,3,4,3,3],[3,3,3,2,3],[2,3]),
 "P08-R02": ([4,4,4,4,4,5,4,4],[3,3,3,3,4],[4,4]),
 "P09-R01": ([4,3,4,4,4,4,4,4],[4,5,4,5,5],[4,4]),
 "P10-R02": ([4,4,5,5,4,4,4,4],[3,4,3,3,4],[4,5]),
 "P11-R01": ([3,3,3,4,4,3,3,3],[5,4,5,5,5],[4,4]),
 "P12-R01": ([5,4,4,4,4,5,5,5],[5,4,5,5,5],[4,4]),
 "P13-R04": ([4,4,4,5,4,4,5,4],[4,4,4,4,4],[3,3]),
 "P14-R01": ([5,5,4,5,5,5,5,5],[5,4,5,5,5],[5,5]),
 "P15-R04": ([4,3,4,5,4,5,4,4],[4,4,4,4,4],[4,4]),
 "P16-R03": ([4,5,4,5,4,5,5,5],[4,4,4,4,4],[4,4]),
 "P17-R01": ([4,4,4,5,4,5,5,4],[3,4,3,3,3],[4,4]),
 "P18-R01": ([3,3,3,4,4,4,3,3],[3,5,4,4,5],[4,4]),
 "P19-R01": ([2,3,3,0,3,4,2,3],[3,4,3,3,4],[3,4]),
 "P20-R01": ([5,4,4,5,5,5,5,5],[3,4,3,3,4],[5,5]),
}
DESIGN = ["hero_originality","typography","layout_composition","image_treatment","visual_hierarchy","brand_distinctiveness","screenshot_worthy_quality","design_distinctiveness"]
CONVERSION = ["cta_clarity","navigation_utility","conversion_clarity","decision_size","customer_state_fit"]
FEASIBILITY = ["mobile_quality","responsive_recomposition"]

def main():
    data = ROOT / "data"
    scenes = {x["scene_evidence_id"]:x for x in map(json.loads,(data/"creative_mechanism_phase2_1_gold_scene_evidence.jsonl").read_text().splitlines())}
    with (data/"creative_mechanism_phase2_1_gold_references.csv").open(newline="",encoding="utf-8") as fh:
        refs = list(csv.DictReader(fh))
    cfg = json.loads((ROOT/"config/creative_mechanism_db_architecture_v1_3.json").read_text())
    assert set(RAW) == {r["reference_id"] for r in refs}
    dimension = cfg["scoring"]["dimensions"]
    scores = []
    for r in refs:
        ref = r["reference_id"]
        ds,cs,fs = RAW[ref]
        desktop = scenes[f"GOLD-{ref}-DESKTOP-HERO"]
        mobile = scenes[f"GOLD-{ref}-MOBILE-HERO"]
        section = scenes[f"GOLD-{ref}-DESKTOP-SECTION"]
        anchors = [desktop["scene_evidence_id"],mobile["scene_evidence_id"]]
        if section["observation_state"] == "OBSERVED": anchors.append(section["scene_evidence_id"])
        raw = {"design":dict(zip(DESIGN,ds)), "conversion_architecture":dict(zip(CONVERSION,cs)),
               "implementation_feasibility":dict(zip(FEASIBILITY,fs)), "motion":{}}
        category = {}; missing = {}; rationale = {}
        for cat,block in dimension.items():
            weights=block["weights"]
            observed=raw[cat]
            missing[cat]={name:"NOT_OBSERVED" for name in weights if name not in observed}
            if observed:
                category[cat]=round(sum((v/5)*weights[k] for k,v in observed.items()) /
                                    sum(weights[k] for k in observed)*block["target_max"],4)
                rationale[cat] = {"source_scene_evidence_ids":anchors,
                    "concrete_visual_note": desktop["observed_facts"][0] + " / " + mobile["observed_facts"][0],
                    "score_scope": "Entry viewport and first scrolled section only; judgement from attached screenshots"}
            else: category[cat]=None
        denominator=sum(dimension[cat]["target_max"] for cat,value in category.items() if value is not None)
        overall=round(sum(v for v in category.values() if v is not None)/denominator*100,4)
        scores.append({"reference_id":ref,"score_audit_status":"EVIDENCE_BACKED_FINAL",
            "score_scope":"CAPTURED_ENTRY_AND_FIRST_SCROLL_ONLY",
            "reviewer":"MIO_MANUAL_VISUAL_2026-09-29",
            "source_scene_evidence_ids":anchors,"raw_dimension_scores":raw,"missingness":missing,
            "category_scores":category,"overall_normalized_score":overall,"normalization_denominator":denominator,
            "dimension_rationale":rationale,"promotion_allowed":False,
            "promotion_blockers":["TEMPORARY_CAPTURE","UNOBSERVED_MOTION_RUNTIME_AND_DEEP_CONVERSION"],
            "measured_cvr":"NOT_MEASURED"})
        r["score_audit_status"]="EVIDENCE_BACKED_FINAL"
        r["score_scope"]="CAPTURED_ENTRY_AND_FIRST_SCROLL_ONLY"
        r["overall_normalized_score"]=str(overall)
        r["decision_reason"]="TEMPORARY_CAPTURE; scoped score excludes unobserved dimensions; no Strong promotion"
    with (data/"creative_mechanism_phase2_1_gold_references.csv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(refs[0]));w.writeheader();w.writerows(refs)
    with (data/"creative_mechanism_phase2_1_gold_scores.jsonl").open("w",encoding="utf-8") as fh:
        for s in scores: fh.write(json.dumps(s,ensure_ascii=False,separators=(",",":"))+"\n")
    print(f"EVIDENCE_BACKED_FINAL {len(scores)} scoped scores; range {min(x['overall_normalized_score'] for x in scores)}-{max(x['overall_normalized_score'] for x in scores)}; promotion blocked")

if __name__ == "__main__": main()
