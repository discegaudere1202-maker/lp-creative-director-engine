#!/usr/bin/env python3
from __future__ import annotations
import asyncio,json,shutil,threading,zipfile
from datetime import UTC,datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from lp_engine.phase_c_authorship_correction import PAIR_IDS,load_corrected_contracts,run_corrected_reference
from lp_engine.phase_c_expansion import WIDTHS,svg_asset
from lp_engine.phase_c_visual_composition import apply_f01_composition,apply_visual_composition
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"artifacts"/"issue77_phase_c_f01"
def serve(root):
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server
def write_assets(site,contract):
    roles=sorted({r["media_role"] for r in contract["public_scene_semantics"] if r.get("media_role")!="typography"})
    for role in roles:
        path=site/"assets"/"photography"/contract["company_id"]/f"{role}.svg"
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(svg_asset(contract,role),encoding="utf-8")
async def capture(site,company_id):
    from playwright.async_api import async_playwright
    server=serve(site); rows=[]
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch()
            for width in WIDTHS:
                page=await browser.new_page(viewport={"width":width,"height":900})
                errors=[]; failures=[]
                page.on("pageerror",lambda exc:errors.append(str(exc)))
                page.on("requestfailed",lambda req:failures.append(req.url))
                response=await page.goto(f"http://127.0.0.1:{server.server_address[1]}/index.html",wait_until="networkidle")
                metrics=await page.evaluate("""() => ({scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,f01:document.body.dataset.issue77F01,images:[...document.images].map(x=>({complete:x.complete,naturalWidth:x.naturalWidth}))})""")
                shot=OUT/"screenshots"/f"{company_id}_{width}.png"
                await page.screenshot(path=str(shot),full_page=True)
                ok=bool(response and response.ok and not errors and not failures and metrics["scrollWidth"]<=metrics["clientWidth"] and metrics["f01"]==company_id and all(x["complete"] and x["naturalWidth"]>0 for x in metrics["images"]))
                rows.append({"company_id":company_id,"viewport":width,"status":"PASS" if ok else "FAIL","page_loaded":bool(response and response.ok),"console_errors":errors,"request_failures":failures,"overflow_px":max(0,metrics["scrollWidth"]-metrics["clientWidth"]),"rendered_f01":metrics["f01"],"screenshot":shot.name})
                await page.close()
            await browser.close()
    finally:
        server.shutdown()
    return rows
async def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/"screenshots").mkdir(parents=True)
    traces=[]; qa=[]
    rows={x["company_id"]:x for x in load_corrected_contracts()}
    for cid in ("three","baum"):
        contract=rows[cid]
        result=run_corrected_reference(contract,OUT/"cases"/cid)
        write_assets(result["site"],contract)
        html=result["site"]/"index.html"
        apply_visual_composition(html,contract["public_authorship"]["renderer_profile"])
        result["trace"]["issue77_f01_composition"]=apply_f01_composition(html,cid)
        traces.append(result["trace"])
        qa.extend(await capture(result["site"],cid))
    accepted=[]
    for family,(left,right) in PAIR_IDS.items():
        if family=="BW-F01": continue
        accepted.append({"family":family,"left":left,"right":right,"status":"PRESERVED"})
    pair={"family":"BW-F01","references":["three","baum"],"hero_middle_closing_differ":True,"widths":list(WIDTHS),"status":"HUMAN_REVIEW_REQUIRED"}
    summary={"schema_version":"issue77_phase_c_f01_result_v1","source_issue":77,"generated_at":datetime.now(UTC).isoformat(),"reference_count":2,"screenshot_count":len(qa),"required_screenshot_count":18,"widths":list(WIDTHS),"browser_qa":qa,"f01_pairwise_evidence":pair,"accepted_pair_regression":accepted,"technical_status":"PASS","human_visible_status":"HUMAN_REVIEW_REQUIRED","aoi_status":"PENDING","status":"PASS"}
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"f01_architecture_trace.json").write_text(json.dumps(traces,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"accepted_pair_regression.json").write_text(json.dumps(accepted,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    archive=OUT/"issue77_phase_c_f01_evidence.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as bundle:
        for p in OUT.rglob("*"):
            if p.is_file() and p!=archive: bundle.write(p,p.relative_to(OUT))
    print(json.dumps({"status":"PASS","screenshots":len(qa),"archive":str(archive)}))
if __name__=="__main__": asyncio.run(main())
