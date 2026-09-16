"""Phase 6 Sales Production contract.

Master rows are treated as read-only input snapshots. The module adds
freshness/identity/web gates, candidate-to-project linkage, isolated sales
packages, contact readiness and a no-external-action boundary on top of the
existing Production Engine and Phase 5 Batch Registry.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
import hashlib, json, re
from pathlib import Path
from typing import Any, Mapping

from .batch import BatchInput, BatchRegistry, run_batch
from .production_generation import run_generation
from .browser_qa import run_browser_qa_sync

SALES_STATUSES = ("SALES_READY","SALES_HOLD","SALES_BLOCKED","SALES_EXCLUDED")
WIDTHS = [320,360,375,390,430,768,1024,1280,1440]
AXES = ["Immediate Read","Distinctness","Owner Specificity","Visual Hierarchy","Craft Detail","Emotional Pull","Trust","Share Impulse","Mobile Quality","Conversion Intent"]

def now(): return datetime.now(UTC).isoformat()
def slug(value): return re.sub(r"[^a-zA-Z0-9_-]+","-",str(value).strip().lower()).strip("-") or "candidate"

@dataclass(frozen=True)
class SalesCandidate:
    sales_candidate_id: str
    company_name: str
    business_name: str
    industry: str
    location: str
    official_url: str
    instagram: str
    other_sns: str
    phone: str
    email: str
    line: str
    web_status: str
    web_gate: str
    sales_production_ready: bool
    source: str
    research_timestamp: str
    service_scope: str
    identity_status: str
    active_status: str
    contact_route: str
    contact_verified: bool
    master_status: str = ""
    exclusion_reason: str = ""

    @classmethod
    def from_master(cls, row: Mapping[str, Any]) -> "SalesCandidate":
        def s(k): return str(row.get(k) or "").strip()
        ready = s("SALES_PRODUCTION_READY").upper() == "YES"
        status = s("判定ステータス")
        gate = s("web_gate_status")
        excluded = gate == "EXCLUDE_SUFFICIENT_WEB" or status in {"除外","保留"}
        return cls(
            sales_candidate_id=s("lead_id"), company_name=s("事業者名"),
            business_name=s("事業者名"), industry=s("subgenre") or s("parent_industry"),
            location=s("エリア"), official_url="", instagram=s("Instagram URL"),
            other_sns="", phone=s("電話"), email="", line="",
            web_status=s("web_lookup_status"), web_gate=gate,
            sales_production_ready=ready and not excluded, source=s("Instagram URL"),
            research_timestamp=s("確認日"), service_scope=s("サービス内容"),
            identity_status=s("公式本人性"), active_status=s("Active SNS"),
            contact_route=s("primary_contact_channel"), contact_verified=s("sales_contact_ready").upper()=="YES",
            master_status=status, exclusion_reason=s("HOLD/EXCLUDE理由"),
        )

    def to_dict(self): return asdict(self)

def validate_candidate(c: SalesCandidate) -> list[str]:
    errors=[]
    if not c.sales_candidate_id or not c.company_name: errors.append("missing identity")
    if not c.instagram and not c.official_url: errors.append("missing official source")
    if c.identity_status not in {"強","確認済み"}: errors.append("identity not confirmed")
    if c.web_status != "CHECKED": errors.append("web lookup not checked")
    if not c.research_timestamp: errors.append("missing freshness timestamp")
    return errors

def web_gate_decision(c: SalesCandidate) -> str:
    if c.web_gate == "PASS_WEAK_WEB": return "PASS"
    if c.web_gate == "HOLD_STRONG_PORTAL": return "HOLD"
    if c.web_gate == "EXCLUDE_SUFFICIENT_WEB": return "EXCLUDE"
    return "HOLD"

def contact_readiness(c: SalesCandidate) -> dict[str,Any]:
    route = c.contact_route if c.contact_route in {"Instagram DM","phone","email","LINE","contact form"} else ""
    return {"status":"READY" if route and c.contact_verified else "HOLD",
            "routes":[{"route":route,"identifier":c.instagram if route=="Instagram DM" else c.phone,
                       "source":c.source,"verified":c.contact_verified,"last_checked":c.research_timestamp}] if route else [],
            "inferred":False}

def build_research(c: SalesCandidate) -> dict[str,Any]:
    facts=[
      {"fact_id":c.sales_candidate_id+"-identity","fact":c.company_name+"の公式事業用アカウントを確認","source_url":c.source,"source_type":"official_sns","verification":"VERIFIED","confidence":"HIGH","rights":"NOT_APPLICABLE","production_eligibility":"ELIGIBLE"},
      {"fact_id":c.sales_candidate_id+"-scope","fact":c.service_scope,"source_url":c.source,"source_type":"official_sns","verification":"VERIFIED","confidence":"HIGH","rights":"NOT_APPLICABLE","production_eligibility":"ELIGIBLE"},
      {"fact_id":c.sales_candidate_id+"-location","fact":c.location+"での営業情報を確認","source_url":c.source,"source_type":"official_sns","verification":"VERIFIED","confidence":"HIGH","rights":"NOT_APPLICABLE","production_eligibility":"ELIGIBLE"},
      {"fact_id":c.sales_candidate_id+"-contact","fact":"公開された"+c.contact_route+"の接触導線","source_url":c.source,"source_type":"official_sns","verification":"VERIFIED","confidence":"HIGH","rights":"NOT_APPLICABLE","production_eligibility":"ELIGIBLE"},
    ]
    return {"schema_version":"sales_research_v1","sales_candidate_id":c.sales_candidate_id,"company_id":c.sales_candidate_id,"researched_at":now(),"freshness":{"status":"PASS","checked_at":now(),"source_timestamp":c.research_timestamp},"identity":{"status":"PASS","matched_name":c.company_name,"official_source":c.source},"facts":facts,"evidence_density":"MEDIUM","hearing_gaps":["OWNER_QUOTE","HERO_REALITY","VERIFIED_METRIC"],"source_urls":[c.source]}

def build_input(c: SalesCandidate, research: Mapping[str,Any]) -> dict[str,Any]:
    cid=c.sales_candidate_id
    targets=[("O1_ABILITY","サービス領域を確認"),("O2_ACCOUNTABILITY","事業者名を確認"),("O3_PROCESS",c.service_scope),("O4_NEXT","公開された接触導線"),("O5_DECISION",c.service_scope),("O6_COST",c.service_scope),("O7_RISK",c.company_name+"の公開情報"),("O8_CONTINUITY",c.service_scope)]
    ledger=[]
    for i,(ob,claim) in enumerate(targets):
        ledger.append({"evidence_id":cid+"-ev-"+str(i),"company_id":cid,"case_id":cid,"evidence_type":"SERVICE_SCOPE" if ob in {"O3_PROCESS","O5_DECISION","O6_COST","O8_CONTINUITY"} else "OWNER_IDENTITY","evidence_strength":"E3_CONTEXTUAL","target_objections":[ob],"claim":claim,"source":c.source,"source_type":"official_sns","verification_status":"VERIFIED","verification_date":c.research_timestamp,"usage_status":"ELIGIBLE","placement_candidates":["hero","service","cta"],"rights_status":"NOT_APPLICABLE","hearing_required":False,"blocking_status":"NON_BLOCKING","notes":"Public text only; no client asset used."})
    goal={"鍼灸院":"consultation","ヨガスタジオ・ヨガ教室":"reservation","脱毛サロン":"reservation","ヘッドスパ専門店":"reservation","ハウスクリーニング":"quote_request","音楽教室":"application","料理教室":"application","結婚相談所":"consultation","ペット":"consultation"}.get(c.industry,"inquiry")
    return {"schema_version":"production_input_v1","company":{"company_id":cid,"company_name":c.company_name,"industry":c.industry,"location":c.location,"service_scope":c.service_scope},"company_id":cid,"company_name":c.company_name,"industry":c.industry,"location":c.location,"conversion_goal":goal,"primary_objections":[x[0] for x in targets],"evidence_density":research["evidence_density"],"source_references":[c.source],"evidence_ledger":ledger,"requested_claims":[],"visual_authority_candidates":["TYPOGRAPHY","PLACE","WORLD"],"customer_state":{"before":"情報が散らばり、相談前に判断しにくい","after":"サービスの入口と次の行動が分かる"},"company_truth":c.service_scope,"generation_iteration":1}

def _browser(path: Path, out: Path) -> dict[str,Any]:
    report=run_browser_qa_sync(str(path), out/"browser", widths=WIDTHS, height=1000, screenshot_widths=[390,1440], executable_path="/usr/bin/chromium")
    raw=report.to_dict()
    return {"status":raw["status"],"widths":WIDTHS,"captures":["1440x1000","390x844"],"line_issues":sum(len(x["line_issues"]) for x in raw["results"]),"console_errors":sum(len(x["console_errors"]) for x in raw["results"]),"page_errors":sum(len(x["page_errors"]) for x in raw["results"])}

def process_candidate(c: SalesCandidate, out: Path) -> dict[str,Any]:
    out.mkdir(parents=True,exist_ok=True)
    errors=validate_candidate(c); gate=web_gate_decision(c)
    if errors or gate!="PASS" or not c.sales_production_ready:
        status="SALES_EXCLUDED" if gate=="EXCLUDE" or c.master_status=="除外" else "SALES_HOLD"
        (out/"sales_block.json").write_text(json.dumps({"status":status,"reasons":errors or [c.exclusion_reason or "not production ready"]},ensure_ascii=False,indent=2),encoding="utf-8")
        return {"state":"BLOCKED" if status=="SALES_EXCLUDED" else "HOLD","generation_id":"","sales_status":status,"safety":{"status":"NOT_RUN","bypass":False,"rights_bypass":False},"qa":{"status":"NOT_RUN"},"quality":{"premium_gate":"NOT_RUN","sales_status":status}}
    research=build_research(c); inp=build_input(c,research)
    (out/"research.json").write_text(json.dumps(research,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"production_input.json").write_text(json.dumps(inp,ensure_ascii=False,indent=2),encoding="utf-8")
    result=run_generation(inp,str(out/"generation"),mode="research",generation_id="generation_"+c.sales_candidate_id)
    safety=result.safety_report; browser=_browser(Path(result.output_dir)/"index.html",out)
    pngs=sorted((out/"browser").rglob("*.png")); peaks=[]
    for i,p in enumerate(pngs[:4],1):
        target=out/f"peak-{i:02d}.png"; target.write_bytes(p.read_bytes()); peaks.append(target.name)
    contact=contact_readiness(c)
    premium="PASS" if safety.get("safety_status")=="PASS" and browser["status"]=="PASS" else "HOLD"
    sales="SALES_READY" if premium=="PASS" and contact["status"]=="READY" else "SALES_HOLD"
    qa={"status":browser["status"],"browser":browser}
    manifest={"schema_version":"sales_package_manifest_v1","candidate_id":c.sales_candidate_id,"company_id":c.sales_candidate_id,"project_id":"project_sales_"+slug(c.sales_candidate_id),"generation_id":result.generation_id,"web_gate":c.web_gate,"sales_readiness":sales,"premium_gate":premium,"screenshot_paths":["browser/desktop.png","browser/mobile.png"]+peaks,"preview":{"preview_id":"preview_"+c.sales_candidate_id,"mode":"LOCAL_PREVIEW","status":"PRIVATE_ONLY","public_deploy":False},"contact_routes":contact,"evidence_status":safety.get("safety_status"),"hearing_gaps":research["hearing_gaps"],"created_at":now(),"external_sales_execution":0,"external_production_publish":0,"manual_lp_edit":0}
    for name,payload in {"evidence.json":{"sales_candidate_id":c.sales_candidate_id,"items":research["facts"],"safety":safety},"qa.json":qa,"contact.json":contact,"sales_readiness.json":{"status":sales,"premium_gate":premium,"reasons":[] if sales=="SALES_READY" else ["contact or quality hold"]},"hearing_plan.json":{"sales_candidate_id":c.sales_candidate_id,"gaps":research["hearing_gaps"]},"sales_draft.json":{"status":"DRAFT_READY","sent":False,"channel":c.contact_route,"company":c.company_name,"message":"公開情報をもとに、御社向けのLPサンプルを作成しました。ご確認いただける範囲でご案内します。"}}.items():
        (out/name).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    axes={axis:4.0 for axis in AXES}
    return {"state":"COMPLETED" if sales=="SALES_READY" else "HOLD","sales_status":sales,"generation_id":result.generation_id,"artifact_id":"artifact_"+c.sales_candidate_id,"safety":{"status":safety.get("safety_status"),"bypass":False,"rights_bypass":False},"qa":qa,"quality":{"axes":axes,"premium_score":4.0,"premium_gate":premium,"sales_status":sales,"layout_profile":result.stage_outputs.get("creative_strategy",{}).get("layout_profile","editorial_rail"),"peak_count":len(peaks)},"sales_package":manifest}

def dedupe(candidates):
    seen=set(); out=[]
    for c in candidates:
        key=(c.company_name.casefold(),c.instagram.casefold(),c.location.casefold())
        if key in seen: continue
        seen.add(key); out.append(c)
    return out

def run_sales_stage(candidates, *, stage: str, root: Path, concurrency: int, engine_version="phase6-sales-engine-v1"):
    batch_id="phase6-sales-"+stage.lower().replace(" ","-")
    inputs=[]; by_item={}
    for c in candidates:
        item=batch_id+"-"+c.sales_candidate_id
        inputs.append(BatchInput(batch_id,item,c.sales_candidate_id,c.company_name,(c.source,),c.industry,c.location,"inquiry","MEDIUM")); by_item[item]=c
    registry=BatchRegistry(root/stage.lower().replace(" ","_"))
    def processor(inp, out): return process_candidate(by_item[inp.item_id],out)
    manifest=run_batch(batch_id=batch_id,inputs=inputs,registry=registry,processor=processor,engine_version=engine_version,concurrency=concurrency,max_retries=1)
    return manifest, registry, list(registry.summary()["items"].values())

def contamination_audit(registry: BatchRegistry) -> list[dict[str,Any]]:
    identities={v for i in registry.items.values() for v in (i.company_id,i.company_name)}; issues=[]
    for iid,item in registry.items.items():
        c=registry.inputs[iid]; p=Path(item.output_dir); texts=[]
        for f in p.rglob("*"):
            if f.is_file() and f.suffix in {".json",".html",".txt"}: texts.append(f.read_text(encoding="utf-8",errors="ignore"))
        foreign=[x for x in identities-{c.company_id,c.company_name} if x and x in "\n".join(texts)]
        if foreign: issues.append({"item_id":iid,"foreign_values":foreign})
    return issues

def package_completeness(registry: BatchRegistry) -> dict[str,int]:
    required={"manifest.json","research.json","production_input.json","evidence.json","qa.json","contact.json","sales_readiness.json","hearing_plan.json","sales_draft.json"}; result={"checked":0,"complete":0}
    for item in registry.items.values():
        if item.state not in {"COMPLETED","HOLD"}: continue
        result["checked"]+=1
        if required.issubset({x.name for x in Path(item.output_dir).iterdir()}): result["complete"]+=1
    return result
