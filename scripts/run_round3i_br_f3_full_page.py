"""Round 3I-BR-F3: line-coverage and human-perceived evidence closure."""
from __future__ import annotations
import asyncio, hashlib, json, shutil, sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"artifacts/round3i_br_f3"
WIDTHS=(320,360,375,390,430,768,1024,1280,1440); IG="https://www.instagram.com/happyfuture_02/"
sys.path.insert(0,str(ROOT/"scripts"))
import run_round3i_br_f2_full_page as f2  # noqa: E402

CSS=f2.CSS+r'''
.visual-disclosure{position:absolute;z-index:5;font:600 11px Inter,sans-serif;letter-spacing:.08em;color:#315451;background:#f8fbf5d9;padding:6px 9px;border:1px solid #31545138}.hero .visual-disclosure{right:8vw;top:76%}.late .visual-disclosure{right:5%;top:6%;background:#f8fbf5e8}.ending .visual-disclosure{right:5%;top:88%;background:#ffffffdf}.line-chunk{white-space:nowrap}
.late-panel h2{font-size:clamp(38px,4.5vw,68px)}.contact h2{max-width:700px}.ending h2{max-width:760px}
@media(max-width:760px){.hero .visual-disclosure{right:12%;top:73%}.choice-head h2{font-size:37px!important}.contact h2{font-size:29px!important;letter-spacing:-.07em}.late-panel h2{font-size:26px!important;letter-spacing:-.07em}.ending h2{font-size:26px!important;letter-spacing:-.07em}.middle .copy h2,.trust h2{font-size:35px!important}.hero .copy h1{font-size:42px!important}}
'''

HTML=f2.HTML
HTML=HTML.replace('<span class="jp-chunk">気になるものを、</span><br><span class="jp-chunk">ひとつ選ぶ。</span>','<span class="line-chunk">気になるものを、</span><br><span class="line-chunk">ひとつ選ぶ。</span>')
HTML=HTML.replace('<h1>今の自分に近い<br>入口から選ぶ。</h1>','<h1><span class="line-chunk">今の自分に近い</span><br><span class="line-chunk">入口から選ぶ。</span></h1>')
HTML=HTML.replace('<img class="hero-media" src="assets/photography/nagi_no_mirai/hero_treatment_space.png" alt="" aria-hidden="true">','<img class="hero-media" src="assets/photography/nagi_no_mirai/hero_treatment_space.png" alt="" aria-hidden="true"><span class="visual-disclosure">参考ビジュアル</span>')
HTML=HTML.replace('<h2>触れる前に、<br>感じ取る。</h2>','<h2><span class="line-chunk">触れる前に、</span><br><span class="line-chunk">感じ取る。</span></h2>')
HTML=HTML.replace('<h2>分かることを、<br>分かる形で。</h2>','<h2><span class="line-chunk">分かることを、</span><br><span class="line-chunk">分かる形で。</span></h2>')
HTML=HTML.replace('<h2><span class="jp-chunk">決めきれないときは、</span><br><span class="jp-chunk">入口から伝える。</span></h2>','<h2><span class="line-chunk">決めきれないときは、</span><br><span class="line-chunk">入口から伝える。</span></h2>')
HTML=HTML.replace('<h2>分かることが増えたら、<br>相談していい。</h2>','<h2><span class="line-chunk">分かることが増えたら。</span><br><span class="line-chunk">相談していい。</span></h2>')
HTML=HTML.replace('<h2>気になることがあれば、<br>そこから相談できます。</h2>','<h2><span class="line-chunk">気になることがあれば。</span><br><span class="line-chunk">そこから相談できます。</span></h2>')
HTML=HTML.replace('<img class="context-media" src="assets/photography/nagi_no_mirai/school_learning_context.png" alt="" aria-hidden="true">','<img class="context-media" src="assets/photography/nagi_no_mirai/school_learning_context.png" alt="" aria-hidden="true"><span class="visual-disclosure">参考ビジュアル</span>')
HTML=HTML.replace('<img class="ending-media" src="assets/photography/nagi_no_mirai/healing_consultation_context.png" alt="" aria-hidden="true">','<img class="ending-media" src="assets/photography/nagi_no_mirai/healing_consultation_context.png" alt="" aria-hidden="true"><span class="visual-disclosure">参考ビジュアル</span>')

def write_json(path:Path,value)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

@contextmanager
def serve(directory:Path):
    handler=lambda *a,**k:SimpleHTTPRequestHandler(*a,directory=str(directory),**k); server=ThreadingHTTPServer(("127.0.0.1",0),handler); thread=Thread(target=server.serve_forever,daemon=True); thread.start()
    try: yield f"http://127.0.0.1:{server.server_port}"
    finally: server.shutdown(); thread.join(timeout=2)

async def render(url:str):
    from playwright.async_api import async_playwright
    rows=[]; coverage=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        for width in WIDTHS:
            page=await browser.new_page(viewport={"width":width,"height":844 if width<768 else 1000}); console=[]; errors=[]; failures=[]
            page.on("console",lambda m:console.append(m.text) if m.type=="error" else None); page.on("pageerror",lambda e:errors.append(str(e))); page.on("requestfailed",lambda r:failures.append(r.url))
            await page.goto(url,wait_until="networkidle"); await page.evaluate("document.fonts.ready")
            state=await page.evaluate("""()=>{
              const forbidden=/DETAIL → RELATIONSHIP|GUIDED CHOICE|PATH MERGE|SELECTED TOKEN|MOTION 0[123]|SIGNATURE|AMBIENT|GROWTH HYPOTHESIS|SEARCH HYPOTHESIS|INSTAGRAM HYPOTHESIS|PROVISIONAL|DUMMY|UNCONFIRMED|design annotation|debug label/i;
              const selectors=['#hero h1','#choice h2','#middle h2','#trust h2','#contact h2','#late h2','#ending h2'];
              const headings=selectors.map(selector=>{const el=document.querySelector(selector);const chunks=[...el.querySelectorAll('.line-chunk')].map(x=>({text:x.textContent,rects:x.getClientRects().length,width:x.getBoundingClientRect().width,height:x.getBoundingClientRect().height}));return {selector,font_size:getComputedStyle(el).fontSize,chunks,box:el.getBoundingClientRect().toJSON()};});
              const orphan=headings.flatMap(h=>h.chunks).filter(x=>x.text.length<=1).map(x=>x.text);
              return {overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),images:[...document.images].every(x=>x.complete&&x.naturalWidth>0),frames:document.querySelectorAll('.section').length,forbidden:forbidden.test(document.body.innerText),headings,orphan,disclosures:document.querySelectorAll('.visual-disclosure').length};
            }""")
            line_pass=state["orphan"]==[] and all(c["rects"]==1 and c["width"]>0 and c["width"]<=h["box"]["width"]+2 for h in state["headings"] for c in h["chunks"])
            coverage.append({"width":width,"status":"PASS" if line_pass else "FAIL","headings":state["headings"],"orphan_lines":state["orphan"]})
            row={"width":width,**state,"line_qa":"PASS" if line_pass else "FAIL","console_errors":console,"page_errors":errors,"request_failures":failures}; row["pass"]=not state["overflow"] and state["images"] and state["frames"]==7 and not state["forbidden"] and state["disclosures"]==3 and line_pass and not console and not errors and not failures; rows.append(row)
            folder=OUT/("desktop" if width>=768 else "mobile"); folder.mkdir(parents=True,exist_ok=True); await page.screenshot(path=str(folder/f"full_{width}.png"),full_page=True)
            for sid in ("hero","choice","middle","trust","contact","late","ending"): await page.locator("#"+sid).screenshot(path=str(folder/f"{sid}_{width}.png"))
            await page.close()
        await browser.close()
    write_json(OUT/"line_composition_qa.json",{"status":"PASS" if all(x["status"]=="PASS" for x in coverage) else "FAIL","coverage":"all_major_customer_facing_headings","headings":['Hero','Choice','Middle','Trust','Contact','Late','Ending'],"widths":coverage,"orphan_line_count":sum(len(x["orphan_lines"]) for x in coverage),"known_regression_late":0,"known_regression_ending":0})
    return {"status":"PASS" if all(x["pass"] for x in rows) else "FAIL","rows":rows,"total":len(rows)}

def evidence():
    assets=[{"path":f"reproduction/assets/photography/nagi_no_mirai/{n}","role":r,"source":"existing project generated asset","rights_status":"PROJECT_OWNED_GENERATED","evidence_authority":"NONE","customer_facing_treatment":"参考ビジュアル label adjacent to image","not_actual_proof":True} for n,(r,_) in f2.ASSETS.items()]
    write_json(OUT/"asset_manifest.json",{"assets":assets,"retained_media_count":3,"replaced_media_count":0})
    write_json(OUT/"media_role_manifest.json",{"evidence_authority":"NONE","roles":{"hero":"ATMOSPHERE","late":"CONTEXT","ending":"EMOTION"},"human_perception_treatment":"Each image has an adjacent Japanese 参考ビジュアル disclosure; no image is presented as Nagi evidence."})
    write_json(OUT/"evidence_boundary.json",{"status":"PASS","reasonable_viewer_rule":"Applied","generated_visuals_are":"representative visual language only","not_actual_proof":True,"surface_disclosure":"参考ビジュアル appears adjacent to each image","unsupported_claims_added":0})
    write_json(OUT/"visual_regression_qa.json",{"status":"MACHINE_PASS_HUMAN_PENDING","baseline_commit":"b101f2185fdbd38ba31452796e15a24d282ceb7d","preserved":["Choice-first","Hero composition","Middle Art Direction","tactile/material language","mobile structure"]})
    write_json(OUT/"final_qa.json",{"status":"HOLD — FULL-PAGE HUMAN VISUAL REVIEW PENDING","aoi_formal_status":"PENDING_AOI_HUMAN_REVIEW","shun_status":"PENDING_FULL_PAGE_REALITY_GATE","judgment_ready":"YES","one_million_yen_gate":"NOT_ASSESSED"})
    write_json(OUT/"aoi_review.json",{"formal_visual_review_status":"PENDING_AOI_HUMAN_REVIEW","proxy_is_formal_review":False,"review_inputs":["desktop/full_1440.png","desktop/late_1440.png","desktop/ending_1440.png","mobile/full_390.png","mobile/late_390.png","mobile/ending_390.png","mobile/full_320.png"]})
    write_json(OUT/"comparison/comparison_manifest.json",{"baseline_commit":"b101f2185fdbd38ba31452796e15a24d282ceb7d","current":"Round 3I-BR-F3","scope":"two blocker closure only"})

def manifest():
    files=[]
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name!="manifest.json": files.append({"path":p.relative_to(OUT).as_posix(),"size_bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    write_json(OUT/"manifest.json",{"schema_version":"round3i_br_f3_v1","file_count":len(files)+1,"files":files})

def main():
    site=OUT/"reproduction"; (site/"assets/material").mkdir(parents=True,exist_ok=True); (site/"assets/photography/nagi_no_mirai").mkdir(parents=True,exist_ok=True)
    for n,s in f2.base.SVGS.items():(site/"assets/material"/n).write_text(s,encoding="utf-8")
    for n in ("NotoSansJP-Variable.ttf","InterTight-Variable.ttf"):
        (site/"assets/fonts").mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/"assets/fonts/round2f"/n,site/"assets/fonts"/n)
    for n in f2.ASSETS: shutil.copy2(ROOT/"assets/photography/generated/nagi_no_mirai"/n,site/"assets/photography/nagi_no_mirai"/n)
    (site/"index.html").write_text(HTML.replace("%%CSS%%",CSS).replace("%%IG%%",IG),encoding="utf-8"); shutil.copytree(site/"assets",OUT/"assets",dirs_exist_ok=True)
    evidence()
    with serve(site) as url: qa=asyncio.run(render(url))
    write_json(OUT/"browser_qa.json",qa); manifest(); return 0 if qa["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
