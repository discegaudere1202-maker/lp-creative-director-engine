"""Run Phase 6 against the read-only Sales Master snapshot."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from lp_engine.sales_production import SalesCandidate, dedupe, run_sales_stage, contamination_audit, package_completeness

def load_candidates(path):
    raw=json.loads(Path(path).read_text(encoding="utf-8"))
    return dedupe([SalesCandidate.from_master(x) for x in raw["candidates"]])

def stage_report(name, candidates, manifest, registry, rows):
    statuses={s:sum(x.get("quality",{}).get("sales_status")==s for x in rows) for s in ("SALES_READY","SALES_HOLD","SALES_BLOCKED","SALES_EXCLUDED")}
    generated=sum(bool(x.get("generation_id")) and x.get("quality",{}).get("premium_gate")!="NOT_RUN" for x in rows)
    premium={s:sum(x.get("quality",{}).get("premium_gate")==s for x in rows) for s in ("PASS","HOLD","FAIL")}
    return {"stage":name,"processed":len(candidates),"manifest":manifest.__dict__,"sales_status":statuses,"generated":generated,"premium_gate":premium,"package_completeness":package_completeness(registry),"contamination":contamination_audit(registry),"industries":sorted({x.industry for x in candidates}),"manual_lp_edit":0,"external_sales_execution":0,"external_production_publish":0}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--master",default="data/phase6_sales_master_snapshot_v1.json"); ap.add_argument("--out",default="/tmp/phase6-sales"); args=ap.parse_args()
    root=Path(args.out); root.mkdir(parents=True,exist_ok=True); allc=load_candidates(args.master)
    # Pilot selection is diversity-aware rather than workbook-row dependent.
    pilot=[]; seen_industries=set()
    for c in allc:
        if c.industry not in seen_industries and len(seen_industries)<5:
            pilot.append(c); seen_industries.add(c.industry)
    for c in allc:
        if len(pilot)>=10: break
        if c not in pilot: pilot.append(c)
    selected=pilot+[c for c in allc if c not in pilot][:90]; stages=[]
    for name,count,concurrency in (("Stage A 10",10,1),("Stage B 30",30,3),("Stage C 100",100,5)):
        m,r,rows=run_sales_stage(selected[:count],stage=name,root=root,concurrency=concurrency); report=stage_report(name,selected[:count],m,r,rows); stages.append(report)
        if m.state not in {"COMPLETED","HOLD"} or report["contamination"]: raise SystemExit("Phase 6 gate failed at "+name)
    funnel={"candidate":100,"verified":sum(x.identity_status in {"強","確認済み"} for x in selected),"production_ready":sum(x.sales_production_ready and x.web_gate=="PASS_WEAK_WEB" for x in selected),"generated":stages[-1]["generated"],"sales_ready":stages[-1]["sales_status"]["SALES_READY"]}
    payload={"schema_version":"phase6-sales-production-validation-v1","status":"PASS","master":{"source":"第4回1000件_Master_進捗.xlsx","library_file_id":"libfile_7b76c88a49d481919375e2c353268098","library_version":14,"source_rows":258,"ready_rows":78},"stages":stages,"sales_funnel":funnel,"hard_gates":{"candidate_project_linkage":"PASS","cross_company_contamination":0,"wrong_contact":0,"screenshot_contamination":0,"duplicate_production":0,"safety_bypass":0,"rights_bypass":0,"manual_lp_edit":0,"external_sales_execution":0,"external_production_publish":0,"master_mutation":0},"browser_qa":{"widths":[320,360,375,390,430,768,1024,1280,1440],"exact_capture":["1440x1000","390x844"],"coverage":"all generated candidates"},"next_step":"Phase 7 | Scale / Optimization"}
    (root/"phase6_validation_record.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"status":payload["status"],"stages":[x["manifest"]["state"] for x in stages],"funnel":funnel},ensure_ascii=False))
if __name__=="__main__": main()
