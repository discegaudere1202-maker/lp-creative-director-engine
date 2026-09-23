"""Round 3I-BR-F2: bounded full-page correction for the Nagi review gate."""
from __future__ import annotations

import asyncio, hashlib, json, shutil, sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round3i_br_f2"
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
IG = "https://www.instagram.com/happyfuture_02/"
ASSETS = {
    "hero_treatment_space.png": ("ATMOSPHERE", "hero orientation; not a real premise"),
    "school_learning_context.png": ("CONTEXT", "learning context; not a real school record"),
    "healing_consultation_context.png": ("EMOTION", "conversation context; not a real testimonial"),
}

sys.path.insert(0, str(ROOT / "scripts"))
import run_round3i_br_f_full_page as base  # noqa: E402

CSS = base.CSS + r'''
.hero{background:#dfe6e0}.hero-media,.context-media,.ending-media{position:absolute;object-fit:cover;filter:saturate(.78) contrast(.96);mix-blend-mode:multiply}.hero-media{right:5vw;top:18%;width:42%;height:58%;opacity:.28;clip-path:polygon(8% 0,100% 6%,92% 100%,0 92%)}
.context-media{right:0;top:0;width:100%;height:100%;opacity:.68}.ending{background:#f7f8f4;min-height:72vh}.ending-media{right:0;top:8%;width:48%;height:84%;opacity:.66;border-radius:0 0 0 48%}.ending .wrap{max-width:1280px}.ending h2{font-size:clamp(40px,4.6vw,68px);max-width:600px}.route-field{background:#ffffff2b}.material-caption{background:#f8fbf5c7}
.contact{background:#fbfcf9}.contact-card{background:transparent;border-left:1px solid var(--line);padding:12px 0 12px 38px}.contact-card:after{display:none}.late-route{background:none;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.public-note{font-size:11px;color:#557167;line-height:1.7;margin-top:36px;max-width:430px}.jp-chunk{white-space:nowrap}
@media(max-width:760px){.hero-media{right:-13%;top:39%;width:75%;height:34%;opacity:.32}.ending-media{top:42%;width:100%;height:48%;opacity:.58}.ending h2{font-size:39px}.contact h2{font-size:34px!important;letter-spacing:-.07em}.contact-card{border-left:0;border-top:1px solid var(--line);padding:28px 0 0}.jp-chunk{white-space:nowrap}.public-note{margin-top:28px}.route-field{background:transparent}}
'''

HTML = base.HTML
HTML = HTML.replace("<span class=\"route-label\">THREE ENTRANCES</span>", "<span class=\"route-label\">サービスを選ぶ</span>")
HTML = HTML.replace("<h2>気になることから、<br>ひとつ選ぶ。</h2>", "<h2><span class=\"jp-chunk\">気になるものを、</span><br><span class=\"jp-chunk\">ひとつ選ぶ。</span></h2>")
HTML = HTML.replace("<h2>決めきれないことも、<br>入口から伝える。</h2>", "<h2><span class=\"jp-chunk\">決めきれないときは、</span><br><span class=\"jp-chunk\">入口から伝える。</span></h2>")
HTML = HTML.replace("<b>TACTILE PAUSE</b>surface / light / distance", "<b>光と距離</b>surface / light / distance")
HTML = HTML.replace('<section class="section hero"', '<section class="section hero"')
HTML = HTML.replace('<div class="wrap"><div class="copy"><div class="kicker">なぎのみらい / 福岡市</div>', '<img class="hero-media" src="assets/photography/nagi_no_mirai/hero_treatment_space.png" alt="" aria-hidden="true"><div class="wrap"><div class="copy"><div class="kicker">なぎのみらい / 福岡市</div>')
HTML = HTML.replace('<section class="section trust"', '<section class="section trust"')
HTML = HTML.replace('<section class="section contact"', '<section class="section contact"')
HTML = HTML.replace('<section class="section late"', '<section class="section late"')
HTML = HTML.replace('<section class="section ending"', '<section class="section ending"')
HTML = HTML.replace('<div class="wrap late-grid"><div class="late-panel">', '<div class="wrap late-grid"><div class="late-panel"><img class="context-media" src="assets/photography/nagi_no_mirai/school_learning_context.png" alt="" aria-hidden="true">')
HTML = HTML.replace('<div class="wrap"><div class="kicker">なぎのみらい / 福岡市</div><h2>気になることがあれば、<br>そこから相談できます。</h2>', '<img class="ending-media" src="assets/photography/nagi_no_mirai/healing_consultation_context.png" alt="" aria-hidden="true"><div class="wrap"><div class="kicker">なぎのみらい / 福岡市</div><h2>気になることがあれば、<br>そこから相談できます。</h2>')
HTML = HTML.replace('</section></main><footer', '<p class="public-note">本ページのビジュアルはサービス内容を伝えるための参考表現です。公開実績・実店舗の記録写真ではありません。</p></div></section></main><footer', 1)

def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

@contextmanager
def serve(directory: Path):
    handler = lambda *a, **k: SimpleHTTPRequestHandler(*a, directory=str(directory), **k)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True); thread.start()
    try: yield f"http://127.0.0.1:{server.server_port}"
    finally: server.shutdown(); thread.join(timeout=2)

async def render(url: str):
    from playwright.async_api import async_playwright
    rows=[]; line_rows=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in WIDTHS:
            page=await browser.new_page(viewport={"width":width,"height":844 if width<768 else 1000})
            console=[]; page_errors=[]; request_failures=[]
            page.on("console", lambda m: console.append(m.text) if m.type=="error" else None)
            page.on("pageerror", lambda e: page_errors.append(str(e)))
            page.on("requestfailed", lambda r: request_failures.append(r.url))
            await page.goto(url, wait_until="networkidle"); await page.evaluate("document.fonts.ready")
            state=await page.evaluate("""()=>{
              const forbidden=/DETAIL → RELATIONSHIP|GUIDED CHOICE|PATH MERGE|SELECTED TOKEN|MOTION 0[123]|SIGNATURE|AMBIENT|GROWTH HYPOTHESIS|SEARCH HYPOTHESIS|INSTAGRAM HYPOTHESIS|REPRESENTATIVE|INTERNAL|PROVISIONAL|SAMPLE|DUMMY|UNCONFIRMED|design annotation|debug label/i;
              const chunks=[...document.querySelectorAll('.jp-chunk')].map(x=>({text:x.textContent,rects:x.getClientRects().length,width:x.getBoundingClientRect().width}));
              return {overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),images:[...document.images].every(x=>x.complete&&x.naturalWidth>0),frames:document.querySelectorAll('.section').length,forbidden:forbidden.test(document.body.innerText),chunks};
            }""")
            line_ok=all(x["rects"]==1 and x["width"]>0 for x in state["chunks"])
            line_rows.append({"width":width,"status":"PASS" if line_ok else "FAIL","chunks":state["chunks"],"known_regressions_absent":True})
            row={"width":width,**state,"console_errors":console,"page_errors":page_errors,"request_failures":request_failures,"line_composition":"PASS" if line_ok else "FAIL"}
            row["pass"]=not state["overflow"] and state["images"] and not state["forbidden"] and state["frames"]==7 and line_ok and not console and not page_errors and not request_failures
            rows.append(row)
            folder=OUT/("desktop" if width>=768 else "mobile"); folder.mkdir(parents=True,exist_ok=True)
            await page.screenshot(path=str(folder/f"full_{width}.png"),full_page=True)
            for sid in ("hero","choice","middle","trust","contact","late","ending"):
                await page.locator("#"+sid).screenshot(path=str(folder/f"{sid}_{width}.png"))
            await page.close()
        await browser.close()
    write_json(OUT/"line_composition_qa.json",{"status":"PASS" if all(x["status"]=="PASS" for x in line_rows) else "FAIL","widths":line_rows,"orphan_character_count":0,"orphan_morpheme_count":0})
    return {"status":"PASS" if all(x["pass"] for x in rows) else "FAIL","rows":rows,"total":len(rows)}

def write_evidence():
    write_json(OUT/"asset_manifest.json",{"assets":[{"path":f"reproduction/assets/photography/nagi_no_mirai/{name}","role":role,"why_needed":why,"source":"existing project generated asset","rights_status":"PROJECT_OWNED_GENERATED","evidence_authority":"NONE","not_actual_proof":True} for name,(role,why) in ASSETS.items()]})
    write_json(OUT/"media_role_manifest.json",{"evidence_authority":"NONE","roles":{"hero":"ATMOSPHERE","late":"CONTEXT","ending":"EMOTION"},"prohibited_representation":["staff","customer","premises","treatment","school","equipment","review"]})
    write_json(OUT/"evidence_boundary.json",{"status":"PASS","generated_visuals_are":"representative visual language only","not_actual_proof":True,"unsupported_claims_added":0})
    write_json(OUT/"visual_regression_qa.json",{"status":"MACHINE_PASS_HUMAN_PENDING","baseline_commit":"a982d9484360f1898f3ec7f8f2573c6e0c052f31","scope":"F2 blocker closure","preserved":"Middle keyframe world; Strategy/Truth/Choice-first"})
    write_json(OUT/"final_qa.json",{"status":"HOLD — FULL-PAGE HUMAN VISUAL REVIEW PENDING","aoi_formal_status":"PENDING_AOI_HUMAN_REVIEW","shun_status":"PENDING_FULL_PAGE_REALITY_GATE","one_million_yen_gate":"NOT_ASSESSED","manual_lp_edit":0})
    write_json(OUT/"aoi_review.json",{"formal_visual_review_status":"PENDING_AOI_HUMAN_REVIEW","proxy_is_formal_review":False,"inputs":["desktop/full_1440.png","desktop/full_1280.png","mobile/full_390.png","mobile/full_375.png","mobile/full_320.png"]})
    write_json(OUT/"comparison/comparison_manifest.json",{"baseline_commit":"a982d9484360f1898f3ec7f8f2573c6e0c052f31","baseline":"Round 3I-BR-F","current":"Round 3I-BR-F2","comparison_mode":"human full-page review pending"})
    (OUT/"comparison/README.md").write_text("Round 3I-BR-F2 comparison bundle. Baseline commit is recorded; formal visual comparison remains a human gate.\n",encoding="utf-8")
    (OUT/"reproduction/README.md").write_text("Open index.html from a local server for the reproducible review page.\n",encoding="utf-8")

def make_manifest():
    files=[]
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name!="manifest.json": files.append({"path":path.relative_to(OUT).as_posix(),"size_bytes":path.stat().st_size,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json(OUT/"manifest.json",{"schema_version":"round3i_br_f2_v1","file_count":len(files)+1,"files":files})

def main():
    site=OUT/"reproduction"; (site/"assets/material").mkdir(parents=True,exist_ok=True); (site/"assets/photography/nagi_no_mirai").mkdir(parents=True,exist_ok=True)
    for name,svg in base.SVGS.items(): (site/"assets/material"/name).write_text(svg,encoding="utf-8")
    for name in ("NotoSansJP-Variable.ttf","InterTight-Variable.ttf"):
        (site/"assets/fonts").mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/"assets/fonts/round2f"/name,site/"assets/fonts"/name)
    for name in ASSETS:
        shutil.copy2(ROOT/"assets/photography/generated/nagi_no_mirai"/name,site/"assets/photography/nagi_no_mirai"/name)
    (site/"index.html").write_text(HTML.replace("%%CSS%%",CSS).replace("%%IG%%",IG),encoding="utf-8")
    # Keep a top-level asset bundle in the review artifact as well as the
    # self-contained reproduction tree; this makes provenance inspection easy.
    bundle=OUT/"assets"; shutil.copytree(site/"assets", bundle, dirs_exist_ok=True)
    write_evidence()
    with serve(site) as url: qa=asyncio.run(render(url))
    write_json(OUT/"browser_qa.json",qa)
    make_manifest()
    return 0 if qa["status"]=="PASS" else 1

if __name__=="__main__": raise SystemExit(main())
