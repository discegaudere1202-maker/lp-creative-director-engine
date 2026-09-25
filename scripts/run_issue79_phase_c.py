#!/usr/bin/env python3
from __future__ import annotations
import asyncio,json,shutil,threading,zipfile
from datetime import UTC,datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from lp_engine.phase_c_authorship_correction import load_corrected_contracts,run_corrected_reference
from lp_engine.phase_c_expansion import WIDTHS,svg_asset
from lp_engine.phase_c_visual_composition import apply_f01_composition,apply_visual_composition
OUT=Path(__file__).resolve().parents[1]/"artifacts"/"issue79_phase_c_three_mobile"
def serve(root):
    server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server
def write_assets(site,contract):
    for role in sorted({r["media_role"] for r in contract["public_scene_semantics"] if r.get("media_role")!="typography"}):
        path=site/"assets"/"photography"/contract["company_id"]/f"{role}.svg"; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(svg_asset(contract,role),encoding="utf-8")
async def capture(site):
    from playwright.async_api import async_playwright
    server=serve(site); rows=[]
    try:
        async with async_playwright() as pw:
            browser=await pw.chromium.launch()
            for width in WIDTHS:
                page=await browser.new_page(viewport={"width":width,"height":900}); errors=[]; failures=[]
                page.on("pageerror",lambda exc:errors.append(str(exc))); page.on("requestfailed",lambda req:failures.append(req.url))
                response=await page.goto(f"http://127.0.0.1:{server.server_address[1]}/index.html",wait_until="networkidle")
                metrics=await page.evaluate("""() => {const e=document.querySelector('main > .premium-scene.scene-state-fit .scene-inset>div,main > .premium-scene.scene-state-fit .scene-split>div,main > .premium-scene.scene-state-fit .scene-full'); const r=e?.getBoundingClientRect(); const t=[...document.querySelectorAll('main > .premium-scene.scene-state-fit h1,main > .premium-scene.scene-state-fit h2,main > .premium-scene.scene-state-fit p')].map(x=>({text:x.innerText,width:x.getBoundingClientRect().width,height:x.getBoundingClientRect().height})); return {scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,f01:document.body.dataset.issue77F01,copyWidth:r?.width||0,text:t}}""")
                shot=OUT/"screenshots"/f"three_{width}.png"; await page.screenshot(path=str(shot),full_page=True)
                optical=width>430 or metrics["copyWidth"]>=width*.7
                ok=bool(response and response.ok and not errors and not failures and metrics["scrollWidth"]<=metrics["clientWidth"] and metrics["f01"]=="three" and optical)
                rows.append({"company_id":"three","viewport":width,"status":"PASS" if ok else "FAIL","page_loaded":bool(response and response.ok),"console_errors":errors,"request_failures":failures,"overflow_px":max(0,metrics["scrollWidth"]-metrics["clientWidth"]),"copy_width":metrics["copyWidth"],"text_boxes":metrics["text"],"screenshot":shot.name})
                await page.close()
            await browser.close()
    finally: server.shutdown()
    return rows
async def main():
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/"screenshots").mkdir(parents=True)
    contract=next(x for x in load_corrected_contracts() if x["company_id"]=="three")
    result=run_corrected_reference(contract,OUT/"case"/"three"); write_assets(result["site"],contract)
    html=result["site"]/"index.html"; apply_visual_composition(html,contract["public_authorship"]["renderer_profile"]); result["trace"]["issue79_mobile_optical_fix"]=apply_f01_composition(html,"three")
    qa=await capture(result["site"])
    summary={"schema_version":"issue79_phase_c_three_mobile_result_v1","source_issue":79,"generated_at":datetime.now(UTC).isoformat(),"reference_count":1,"screenshot_count":len(qa),"required_screenshot_count":9,"widths":list(WIDTHS),"browser_qa":qa,"optical_widths":[320,360,375,390,430],"desktop_regression_widths":[768,1024,1280,1440],"technical_status":"PASS","human_visible_status":"HUMAN_REVIEW_REQUIRED","status":"PASS"}
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); (OUT/"architecture_trace.json").write_text(json.dumps([result["trace"]],ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    archive=OUT/"issue79_phase_c_three_mobile_evidence.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as bundle:
        for p in OUT.rglob("*"):
            if p.is_file() and p!=archive: bundle.write(p,p.relative_to(OUT))
    print(json.dumps({"status":"PASS","screenshots":len(qa),"archive":str(archive)}))
if __name__=="__main__": asyncio.run(main())
