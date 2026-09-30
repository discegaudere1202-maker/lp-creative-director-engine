"""Ordinary-browser durable-archive handoff package; Actions artifacts remain temporary."""
from __future__ import annotations
import argparse, hashlib, json, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
try:
    from .validate_phase2_2_1a_replacement import load_rows, validate
except ImportError:
    from validate_phase2_2_1a_replacement import load_rows, validate

VIEWPORTS={"DESKTOP":{"width":1440,"height":1000},"MOBILE":{"width":390,"height":844}}
CHALLENGE=re.compile(r"captcha|verify you are human|security challenge|access denied|checking your browser",re.I)
MAX_HEIGHT=30000

def now(): return datetime.now(timezone.utc).isoformat()
def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def facts(page):
    return page.evaluate("""() => { const norm=s=>(s||'').replace(/\\s+/g,' ').trim();
      const rect=e=>{const r=e.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y+scrollY),width:Math.round(r.width),height:Math.round(r.height)}};
      const nodes=[...document.querySelectorAll('h1,h2,h3,main section,main article,footer,nav,a,button')].slice(0,500).map((e,i)=>({i,tag:e.tagName.toLowerCase(),text:norm(e.innerText||e.getAttribute('aria-label')).slice(0,400),rect:rect(e)})).filter(x=>x.text);
      return {title:document.title,url:location.href,inner_width:innerWidth,scroll_width:document.documentElement.scrollWidth,scroll_height:document.documentElement.scrollHeight,visible_text:norm(document.body?.innerText).slice(0,3000),semantic_nodes:nodes,heading_count:document.querySelectorAll('h1,h2,h3').length,section_count:document.querySelectorAll('main section,main article,[data-section]').length,nav_count:document.querySelectorAll('nav').length,footer_present:!!document.querySelector('footer'),video_count:document.querySelectorAll('video').length}; }""")

def ordinary_settle(page):
    """Bounded wait and visible non-binding controls; never alter DOM/access controls."""
    actions=[]
    page.wait_for_timeout(3500)
    if classify(None,None,facts(page)) is not None:return actions
    for pattern in (r'^reject all$', r'^refuse all$', r'^decline$',
                    r'^allow technical cookies$', r'^no thanks$', r'^close(?: (?:dialog|form|popup|modal))?$',
                    r'^閉じる$', r'^必要なクッキーのみ許可$'):
        buttons=page.get_by_role('button',name=re.compile(pattern,re.I))
        for button in buttons.all()[:8]:
            if button.is_visible():
                button.click(timeout=1500)
                actions.append({'action':'VISIBLE_NON_BINDING_DISMISS','label_pattern':pattern})
                page.wait_for_timeout(300)
                break
    # Reviewed ordinary newsletter dismissal, scoped to the observed official host/frame.
    if re.match(r'^https://(?:www\.)?allbirds\.com/', page.url):
        frames=page.locator('iframe#attentive_creative[title="Sign Up via Text for Offers"]')
        if frames.count()==1:
            dismiss=page.frame_locator('iframe#attentive_creative[title="Sign Up via Text for Offers"]').get_by_role('button',name='Dismiss this popup',exact=True)
            if dismiss.is_visible():
                dismiss.click(timeout=1500)
                actions.append({'action':'VISIBLE_NON_BINDING_NEWSLETTER_DISMISS','host':'allbirds.com','frame':'attentive_creative','label':'Dismiss this popup'})
                page.wait_for_timeout(300)
    page.wait_for_timeout(1500)
    return actions

def traverse(page):
    sampled=[]; target=0; complete=False; stable_bottom=0; previous=None
    for _ in range(200):
        page.evaluate("y=>window.scrollTo(0,y)",target);page.wait_for_timeout(350)
        sample=page.evaluate("() => ({scroll_y:window.scrollY,document_height:document.documentElement.scrollHeight,viewport_height:innerHeight})")
        sampled.append(sample); height=sample['document_height']
        if height>MAX_HEIGHT:break
        at_bottom=sample['scroll_y']+sample['viewport_height']>=height-2
        stable_bottom=stable_bottom+1 if at_bottom and previous and height==previous['document_height'] else 0
        if stable_bottom>=2:complete=True;break
        if previous and not at_bottom and sample['scroll_y']==previous['scroll_y'] and target>sample['scroll_y']:break
        target=min(height,sample['scroll_y']+max(500,int(sample['viewport_height']*.78)))
        previous=sample
    final=page.evaluate("document.documentElement.scrollHeight")
    page.evaluate("window.scrollTo(0,0)");page.wait_for_timeout(500)
    return {"state":"OBSERVED" if complete else "NOT_OBSERVED","scroll_samples":sampled,"final_height":final,"max_height_limit":MAX_HEIGHT,"complete_to_bottom":complete,'position_measurement':'ACTUAL_WINDOW_SCROLLY','stable_bottom_samples':stable_bottom}

def save_screens(page,out:Path,rid:str,vp:str,stamp:str):
    facts0=facts(page); height=facts0["scroll_height"]
    files=[]
    view=out/f"{rid}__{vp.lower()}__viewport.png"
    page.screenshot(path=str(view),full_page=False,animations="disabled",timeout=30000)
    files.append({"screenshot_identifier":view.name,"kind":"VIEWPORT","content_sha256":digest(view)})
    if height<=MAX_HEIGHT:
        full=out/f"{rid}__{vp.lower()}__fullpage.png"
        try:
            page.screenshot(path=str(full),full_page=True,animations="disabled",timeout=60000)
            files.append({"screenshot_identifier":full.name,"kind":"FULL_PAGE","content_sha256":digest(full)})
        except Exception:
            if full.exists(): full.unlink()
    if not any(x["kind"]=="FULL_PAGE" for x in files):
        # Bounded tiled fallback: individually hashed visible segments, no browser or access-control evasion.
        tile_h=1200; count=min(25,max(1,(height+tile_h-1)//tile_h))
        for i in range(count):
            page.evaluate("y=>window.scrollTo(0,y)",i*tile_h);page.wait_for_timeout(80)
            tile=out/f"{rid}__{vp.lower()}__tile-{i+1:02d}.png"
            page.screenshot(path=str(tile),full_page=False,animations="disabled",timeout=30000)
            files.append({"screenshot_identifier":tile.name,"kind":"FULL_PAGE_TILE","tile_index":i+1,"scroll_y":i*tile_h,"content_sha256":digest(tile)})
        page.evaluate("window.scrollTo(0,0)")
    return files,facts0

def classify(status,error,fact=None):
    if status in (403,429): return f"HTTP_{status}"
    if status and status>=400: return f"HTTP_{status}"
    if fact and CHALLENGE.search(fact.get("title","")+" "+fact.get("visible_text","")[:1000]): return "SECURITY_CHALLENGE_OR_CAPTCHA_VISIBLE"
    if error:
        msg=error.lower()
        if "timeout" in msg: return "TIMEOUT"
        if "net::err_name_not_resolved" in msg: return "DNS_RESOLUTION"
        return "BROWSER_OR_RENDER_ERROR"
    if not fact or (not fact.get("visible_text") and not fact.get("heading_count")): return "HTTP_200_NO_VISIBLE_BODY"
    return None

def capture_one(browser,row,out,mode,run_id,artifact_name,retention):
    rid=row["replacement_reference_id"]; result={"replacement_reference_id":rid,"replaces_reference_id":row["replaces_reference_id"],"replacement_metadata":{k:row.get(k) for k in ("slot_id","business_archetype","industry","market_scope","discovery_source_class","original_official_url","evidence_source_roles","replacement_reason")},"record_kind":row.get("record_kind","PRODUCTION_CANDIDATE"),"production_eligible":row.get("production_eligible",True),"requested_url":row["original_official_url"],"captured_at":now(),"viewports":[],"capture_state":"CAPTURE_FAILED","failure_class":None,"error":None,"archive_ingestion_status":"TEMPORARY_ARTIFACT_PENDING_DURABLE_ARCHIVE","artifact":{"name":artifact_name,"run_id":str(run_id),"retention_days":retention,"classification":"TEMPORARY_GITHUB_ACTIONS_ARTIFACT_NOT_DURABLE_ARCHIVE_NOT_FINAL_ARCHIVE"}}
    failed=False
    for label,sz in VIEWPORTS.items():
        entry={"viewport_label":label,"viewport":sz,"capture_state":"CAPTURE_FAILED","screenshots":[],"traversal_facts":{"state":"NOT_OBSERVED"},"page_facts":None,"requested_url":row["original_official_url"],"final_url":None,"http_status":None,"captured_at":now()}
        ctx=browser.new_context(viewport=sz,device_scale_factor=1,locale="ja-JP",service_workers="block")
        page=ctx.new_page();page.set_default_navigation_timeout(30000);page.set_default_timeout(10000)
        try:
            response=None; error=None
            for attempt in range(2):
                try:
                    response=page.goto(row["original_official_url"],wait_until="domcontentloaded",timeout=30000)
                    page.wait_for_timeout(800)
                    break
                except Exception as exc:
                    error=f"{type(exc).__name__}: {str(exc)[:300]}"
                    if attempt==0 and "timeout" in str(exc).lower(): continue
                    break
            entry["final_url"]=page.url;entry["http_status"]=response.status if response else None
            pf=facts(page); entry["page_facts"]=pf
            fc=classify(entry["http_status"],error,pf)
            if fc:
                entry.update({"failure_class":fc,"error":error or fc});failed=True
            elif pf["inner_width"]!=sz["width"] or (not pf["visible_text"] and not pf["heading_count"]):
                entry.update({"failure_class":"VIEWPORT_OR_VISIBLE_BODY_INVALID","error":"Viewport mismatch or no visible page content"});failed=True
            else:
                entry['ordinary_ui_actions']=ordinary_settle(page)
                pf=facts(page);entry['page_facts']=pf
                fc=classify(entry['http_status'],None,pf)
                if fc:
                    entry.update({'failure_class':fc,'error':fc});failed=True
                    result['viewports'].append(entry)
                    continue
                entry["traversal_facts"]=traverse(page)
                if entry["traversal_facts"]["state"]!="OBSERVED" or not entry["traversal_facts"]["complete_to_bottom"]:
                    entry.update({"failure_class":"FULL_PAGE_TRAVERSAL_FAILED","error":"No semantic page traversal evidence"});failed=True
                else:
                    page.evaluate("window.scrollTo(0,0)");page.wait_for_timeout(100)
                    entry["screenshots"],entry["page_facts"]=save_screens(page,out,rid,label,entry["captured_at"])
                    entry["capture_state"]="CAPTURED_TEMPORARY"
                    if not any(x["kind"]=="VIEWPORT" for x in entry["screenshots"]) or not any(x["kind"] in ("FULL_PAGE","FULL_PAGE_TILE") for x in entry["screenshots"]):
                        entry["capture_state"]="CAPTURE_FAILED";entry["failure_class"]="SCREENSHOT_OR_HASH_MISSING";failed=True
        except Exception as exc:
            entry.update({"failure_class":classify(entry["http_status"],str(exc),entry.get("page_facts")),"error":f"{type(exc).__name__}: {str(exc)[:300]}"});failed=True
        finally: ctx.close()
        result["viewports"].append(entry)
    result["final_url"]=result["viewports"][-1].get("final_url") if result["viewports"] else None
    result["http_statuses"]={x["viewport_label"]:x["http_status"] for x in result["viewports"]}
    result["capture_state"]="CAPTURE_FAILED" if failed else "CAPTURED_TEMPORARY"
    if failed:
        result["failure_class"]=next((v.get("failure_class") for v in result["viewports"] if v.get("capture_state")!="CAPTURED_TEMPORARY"),"VIEWPORT_CAPTURE_FAILED")
        result["error"]=next((v.get("error") for v in result["viewports"] if v.get("capture_state")!="CAPTURED_TEMPORARY"),None)
    return result

def run(input_path:Path,out:Path,mode:str,run_id:str,artifact_name:str,retention:int):
    from playwright.sync_api import sync_playwright
    rows=validate(load_rows(input_path),mode) if input_path.suffix==".jsonl" else validate([json.loads(input_path.read_text(encoding="utf-8"))],mode)
    out.mkdir(parents=True,exist_ok=True)
    manifest={"schema_version":"PHASE2_2_1A_CAPTURE_MANIFEST_V1","mode":mode,"created_at":now(),"durability":"TEMPORARY_ACTIONS_ARTIFACT_ONLY_DURABLE_ARCHIVE_INGESTION_REQUIRED","phase2600_allowed":False,"records":[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            for row in rows:
                rec=capture_one(browser,row,out,mode,run_id,artifact_name,retention);manifest["records"].append(rec)
                print(f"{rec['replacement_reference_id']} {rec['capture_state']} {rec.get('failure_class') or ''}",flush=True)
        finally: browser.close()
    mp=out/"capture_manifest.json";mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    # Manifest itself is checksummed and listed outside itself to avoid recursive hashing.
    (out/"manifest.sha256").write_text(f"{digest(mp)}  capture_manifest.json\n",encoding="ascii")
    ok=all(r["capture_state"]=="CAPTURED_TEMPORARY" for r in manifest["records"])
    if ok: verify_package(manifest,out)
    if not ok: return 2
    return 0

def verify_package(manifest:dict,root:Path):
    """Hard gate: both required viewports and every declared image/hash must exist."""
    if manifest.get("phase2600_allowed") is not False: raise ValueError("phase2600_allowed must remain false")
    if not manifest.get("records"): raise ValueError("manifest has no records")
    for record in manifest["records"]:
        if record.get("capture_state")!="CAPTURED_TEMPORARY": raise ValueError("record capture failed")
        views={x.get("viewport_label"):x for x in record.get("viewports",[])}
        if set(views)!={"DESKTOP","MOBILE"}: raise ValueError("both Desktop and Mobile are required")
        for label, expected in VIEWPORTS.items():
            v=views[label]
            if v.get("viewport")!=expected or v.get("capture_state")!="CAPTURED_TEMPORARY": raise ValueError(f"invalid/missing viewport {label}")
            kinds={x.get("kind") for x in v.get("screenshots",[])}
            if "VIEWPORT" not in kinds or not kinds.intersection({"FULL_PAGE","FULL_PAGE_TILE"}): raise ValueError(f"missing screenshot coverage: {label}")
            for image in v["screenshots"]:
                path=root/image["screenshot_identifier"]
                if not path.is_file(): raise ValueError(f"missing screenshot file: {path.name}")
                if not image.get("content_sha256") or digest(path)!=image["content_sha256"]: raise ValueError(f"missing or mismatched screenshot hash: {path.name}")
            if v.get("traversal_facts",{}).get("state")!="OBSERVED" or not v["traversal_facts"].get("complete_to_bottom"):
                raise ValueError(f"full-page traversal not evidenced: {label}")
    return True

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--input",type=Path,required=True);ap.add_argument("--output",type=Path,required=True);ap.add_argument("--mode",choices=["approved_batch","smoke"],required=True);ap.add_argument("--run-id",default="LOCAL");ap.add_argument("--artifact-name",default="LOCAL-TEMPORARY-CAPTURE");ap.add_argument("--retention-days",type=int,default=30);args=ap.parse_args()
    sys.exit(run(args.input,args.output,args.mode,args.run_id,args.artifact_name,args.retention_days))
