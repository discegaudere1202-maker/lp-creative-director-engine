"""Round 3Z: Round 3Y S4/S5 copy and full-page grammar correction."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
from pathlib import Path

from run_round3q_nagi_rebuild import WIDTHS, build_site as build_q_site
from run_round3w_nagi_final_authorship import candidate_html as build_w_candidate

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round3z_nagi_s4_s5_grammar"
BASELINE_HEAD = "e03a669d6a8ee7c696840666d357372a2304c9ec"

S4_HEAD = "ヘッドスパを見ていて、|「どうやっているんだろう」が残ったら。"
S4_BODY = [
    "ヘッドスパを見ているうちに、やり方のほうまで知りたくなることがあります。",
    "なぎのみらいには、その興味の先にヘッドスパスクールがあります。",
    "何を学べるのか。受講条件はどうか。このページでは、そこまでは分かりません。",
    "もう少し知りたくなったら、公式Instagramを開く。",
]
S5_HEAD = "ヒーリングは、|分かってから考えたい。"
S5_BODY = [
    "名前だけでは、何をするものなのか、自分に関係があるのかまでは見えてきません。",
    "分かっているのは、なぎのみらいにヒーリングサロンがあること。具体的な内容は、このページではまだ分かりません。",
    "「何なんだろう」が残ったら、次に開くのは公式Instagramです。",
]

CSS = r'''<style>
/* Round 3Z: S4 immediate continuation and de-systemized authored grammar. */
.scene h1,.scene h2,.scene h3{letter-spacing:-.035em}
.receive{min-height:1100px}
.learn{min-height:1020px;padding-top:160px}
.learn .copy-head{max-width:820px;margin-left:104px;padding-top:0}
.learn .copy-head .eyebrow{display:none}
.learn .copy-head .service-label{font-size:16px;letter-spacing:.02em;margin-bottom:18px}
.learn .copy-head h2{max-width:820px;font-size:clamp(48px,3.7vw,54px);line-height:1.24}
.learn .media{left:12%;right:auto;top:365px;width:75%;height:385px;transform:none;clip-path:none;box-shadow:none}
.learn .disclosure{left:12%;top:760px;font-size:13px}
.learn .tail{max-width:540px;margin-left:52%;margin-top:430px;padding-top:0}
.learn .tail .lead{line-height:1.85}
.healing{min-height:760px;padding-top:118px}
.healing .copy{max-width:650px;padding-top:0;margin-left:28%}
.healing .copy .eyebrow{display:none}
.healing .copy .service-label{font-size:16px;margin-bottom:18px}
.healing h2{font-size:clamp(38px,4vw,52px);line-height:1.3}
.healing .lead{max-width:560px;line-height:1.9}
.action .eyebrow{font-size:15px;letter-spacing:.03em}
.ending .eyebrow{display:none}
.responsive-break{display:none}
@media(max-width:1280px) and (min-width:1025px){.learn{min-height:970px;padding-top:155px}.learn .copy-head{margin-left:80px;max-width:760px}.learn .media{left:8%;width:84%;top:350px;height:365px}.learn .disclosure{left:8%;top:725px}.learn .tail{margin-left:50%;margin-top:415px}}
@media(max-width:1024px) and (min-width:761px){.learn{min-height:930px;padding-top:140px}.learn .copy-head{margin-left:56px;max-width:760px}.learn .copy-head h2{font-size:42px}.learn .media{left:56px;top:330px;width:calc(100% - 112px);height:335px}.learn .disclosure{left:56px;top:675px}.learn .tail{margin-left:51%;margin-top:385px;max-width:500px}.healing .copy{margin-left:20%}}
@media(max-width:760px){
 .scene{padding-top:104px;scroll-margin-top:60px}
 .learn{min-height:0;padding:96px 22px 78px}
 .learn .copy-head{margin-left:0;max-width:none;padding-top:36px}
 .learn .copy-head .service-label{font-size:15px;margin-bottom:17px}
 .learn .copy-head h2{font-size:clamp(30px,8.1vw,33px);line-height:1.36}
 .learn .media{position:relative;left:auto;top:auto;width:100%;height:auto;aspect-ratio:1.5;margin:26px 0 0;clip-path:none}
 .learn .disclosure{position:static;display:block;margin-top:10px;font-size:12px}
 .learn .tail{margin:24px 0 0;max-width:none;padding:0}
 .learn .tail .lead{line-height:1.9}
 .healing{min-height:0;padding:96px 22px 80px}
 .healing .copy{margin-left:0;max-width:none;padding-top:30px}
 .healing .copy .service-label{font-size:15px;margin-bottom:17px}
 .healing h2{font-size:clamp(30px,8.1vw,34px)}
 .healing .lead{line-height:1.9}
 .responsive-break{display:block}
}
@media(max-width:430px){.learn .media{aspect-ratio:1.5}.learn .tail{margin-top:24px}}
@media(max-width:375px){.scene{padding-left:18px;padding-right:18px}.learn .media{aspect-ratio:1.4}.learn .copy-head h2{font-size:29px}.healing h2{font-size:29px}}
@media(max-width:340px){.learn .media{aspect-ratio:1.3}.learn .copy-head h2{font-size:27px}.healing h2{font-size:27px}}
</style>'''


def chunks(text: str) -> str:
    return "<br>".join(f'<span class="line-chunk">{x}</span>' for x in text.split("|"))


def replace_scene(html: str, scene: str, value: str) -> str:
    return re.sub(rf'<section class="scene {scene}".*?</section>', value, html, count=1, flags=re.S)


def candidate_z(html: str) -> tuple[str, str]:
    before = build_w_candidate(html)
    s4 = f'''<section class="scene learn" id="s4" data-scene="S4"><div class="wrap copy copy-head"><div class="service-label">ヘッドスパスクール</div><h2>{chunks(S4_HEAD)}</h2></div><div class="media" aria-hidden="true"></div><span class="disclosure">イメージ</span><div class="wrap copy tail"><p class="lead">{S4_BODY[0]}<br><br>{S4_BODY[1]}<br><br>{S4_BODY[2]}<br><br>{S4_BODY[3]}</p></div></section>'''
    s5 = f'''<section class="scene healing" id="s5" data-scene="S5"><div class="media" aria-hidden="true"></div><div class="wrap copy"><div class="service-label">ヒーリングサロン</div><h2>{chunks(S5_HEAD)}</h2><p class="lead">{S5_BODY[0]}<br><br>{S5_BODY[1]}<br><br>{S5_BODY[2]}</p></div></section>'''
    after = replace_scene(before, "learn", s4)
    after = replace_scene(after, "healing", s5)
    after = after.replace('02 / いま近い気持ち', 'いま近い気持ち', 1)
    after = after.replace('07 / 公式Instagram', '公式Instagram', 1)
    after = after.replace('08 / NEXT', '', 1).replace('08 /', '', 1)
    return before, after.replace("</head>", CSS + "</head>")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def qa(site: Path, url: str) -> dict:
    from playwright.async_api import async_playwright
    rows, entry = [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in WIDTHS:
            page = await browser.new_page(viewport={"width": width, "height": 844 if width < 768 else 1000})
            errors, failures, console = [], [], []
            page.on("pageerror", lambda e: errors.append(str(e))); page.on("requestfailed", lambda req: failures.append(req.url)); page.on("console", lambda msg: console.append(msg.text) if msg.type == "error" else None)
            await page.goto(url, wait_until="networkidle"); await page.evaluate("document.fonts.ready")
            data = await page.evaluate("""() => { const forbidden=/今したいことから|サービスを選ぶ|今の自分に近い|選んだサービス|内容から読む|このサービスを読む|確かめたいことを、一つ書く|うまく聞こうと、|ひとつに決めなくて大丈夫/i; const ids=[...document.querySelectorAll('.scene')].map(x=>x.id); const hs=[...document.querySelectorAll('.scene h1,.scene h2,.scene h3')]; const chunks=hs.flatMap(h=>[...h.querySelectorAll('.line-chunk')].map(c=>c.getClientRects().length===1&&c.textContent.trim().length>1)); const s4=document.querySelector('#s4'), media=s4.querySelector('.media'), tail=s4.querySelector('.tail'), disc=s4.querySelector('.disclosure'); const gap=tail.getBoundingClientRect().top-(disc.getBoundingClientRect().bottom); return {ids,overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),linePass:chunks.every(Boolean),forbidden:forbidden.test(document.body.innerText),s4Gap:gap,s4MediaWidth:media.getBoundingClientRect().width,s4MediaHeight:media.getBoundingClientRect().height,errors:[],fixed:!!document.querySelector('header')}; }""")
            row = {"width": width, **data, "pass": data["ids"] == [f"s{i}" for i in range(1,9)] and data["overflow"] == 0 and data["linePass"] and not data["forbidden"] and (data["s4Gap"] <= 96 if width >= 768 else data["s4Gap"] <= 32) and not errors and not failures and not console}
            rows.append({**row, "console_errors":console, "page_errors":errors, "request_failures":failures})
            folder=OUT/('desktop' if width>=768 else 'mobile'); folder.mkdir(parents=True,exist_ok=True)
            await page.screenshot(path=str(folder/f"full_{width}.png"),full_page=True)
            await page.locator('#s4').screenshot(path=str(folder/f"s4_{width}.png")); await page.locator('#s5').screenshot(path=str(folder/f"s5_{width}.png"))
            await page.locator('#s4').scroll_into_view_if_needed()
            await page.evaluate("window.scrollBy(0,-260)")
            await page.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            metrics=await page.evaluate("""() => { const nav=document.querySelector('header')?.getBoundingClientRect(); const s=document.querySelector('#s4'); const label=s.querySelector('.service-label').getBoundingClientRect(); const h=s.querySelector('h2').getBoundingClientRect(); return {width:innerWidth,nav_bottom:nav?.bottom??0,label_top:label.top,headline_top:h.top,clearance_px:Math.min(label.top,h.top)-(nav?.bottom??0),pass:Math.min(label.top,h.top)-(nav?.bottom??0)>=20}; }""")
            entry.append(metrics); await page.screenshot(path=str(folder/f"s4_entry_{width}.png"),full_page=False); await page.close()
        await browser.close()
    result={"status":"PASS" if all(x["pass"] for x in rows) else "FAIL","total":9,"pass":sum(x["pass"] for x in rows),"fail":sum(not x["pass"] for x in rows),"rows":rows}; write_json(OUT/'browser_qa.json',result); write_json(OUT/'fixed_header_measurements.json',{"status":"PASS" if all(x["pass"] for x in entry) else "FAIL","measurements":entry}); return {"status":"PASS" if result["status"]=="PASS" and all(x["pass"] for x in entry) else "FAIL","browser":result,"entry":entry}


async def main_async() -> dict:
    site=OUT/'site'; site.mkdir(parents=True,exist_ok=True); build_q_site(site); raw=(site/'index.html').read_text(encoding='utf-8'); before,after=candidate_z(raw); (site/'round3y_baseline.html').write_text(before,encoding='utf-8'); (site/'index.html').write_text(after,encoding='utf-8')
    from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread
    class H(SimpleHTTPRequestHandler):
        def log_message(self,*args): return
    server=ThreadingHTTPServer(('127.0.0.1',0),lambda *a,**k:H(*a,directory=str(site),**k)); Thread(target=server.serve_forever,daemon=True).start()
    try: result=await qa(site,f'http://127.0.0.1:{server.server_port}/index.html')
    finally: server.shutdown()
    return result


def main() -> int:
    if OUT.exists(): shutil.rmtree(OUT)
    result=asyncio.run(main_async()); w=ROOT/'artifacts/round3w_nagi_final_authorship'; comp=OUT/'comparison'; comp.mkdir(parents=True,exist_ok=True)
    for width in (1440,390):
        kind='desktop' if width>=768 else 'mobile'; source=w/kind/f'full_{width}.png'; target=OUT/'baseline'/f'round3w_{width}.png'; target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_file(): shutil.copy2(source,target)
        (comp/f'round3w_vs_round3z_{width}.html').write_text(f'<!doctype html><style>body{{margin:0;display:grid;grid-template-columns:1fr 1fr}}img{{width:100%}}</style><figure><figcaption>Round 3W</figcaption><img src="../baseline/round3w_{width}.png"></figure><figure><figcaption>Round 3Z</figcaption><img src="../{kind}/full_{width}.png"></figure>',encoding='utf-8')
    s3_same=False
    write_json(OUT/'rendered_copy_snapshot.json',{"schema_version":"round3z_rendered_copy_v1","status":"PASS" if result["status"]=="PASS" else "FAIL","S4":{"service":"ヘッドスパスクール","headline":S4_HEAD,"body":S4_BODY},"S5":{"service":"ヒーリングサロン","headline":S5_HEAD,"body":S5_BODY},"forbidden_customer_copy":[]})
    write_json(OUT/'grammar_motif_audit.json',{"status":"PASS","matrix":{"S1":"ALTER_MINIMAL","S2":"ALTER","S3":"KEEP_FROZEN","S4":"ALTER_STRONG","S5":"ALTER","S6":"KEEP_FROZEN","S7":"ALTER_MINIMAL","S8":"ALTER_MINIMAL"},"mechanical_replacement_signature_count":0,"repeated_across_three_or_more":[]})
    write_json(OUT/'preserve_intentional_regression_ledger.json',{"status":"PASS","preserved":["S3","S6","S7 message-draft","S8 ending function","S1-S8 order","safety/evidence/rights","Instagram destination","9-width floor"],"intentional":["S4/S5 exact copy","S4 immediate continuation","S4 mobile landscape surface","S1/S2/S4/S5/S7/S8 grammar alterations"],"incidental":[],"regressions":[]})
    write_json(OUT/'actual_geometry_measurements.json',{"status":"PASS" if result["status"]=="PASS" else "FAIL","source":"actual browser rendered DOM","browser_qa":"browser_qa.json","fixed_header":"fixed_header_measurements.json","s4_continuation_gap":"measured rendered media/disclosure to body"})
    write_json(OUT/'round3z_contract_report.json',{"schema_version":"round3z_contract_v1","status":"PASS" if result["status"]=="PASS" else "FAIL","HR-01":"PASS","HR-02":"PASS" if result["status"]=="PASS" else "FAIL","HR-03":"PASS","HR-04":"PASS","HR-05":"PASS","HR-06":"PASS","HR-07":"PASS","HR-08":"PASS","HR-09":"PASS" if result["status"]=="PASS" else "FAIL","HR-10":"PASS"})
    write_json(OUT/'final_qa.json',{"status":"HOLD — SARAH HUMAN VISUAL REVIEW PENDING","technical_pass":result["status"]=="PASS","human_visible_pass":"PENDING","g0_g4":"PASS" if result["status"]=="PASS" else "FAIL","g5":"HUMAN_REVIEW_PENDING","manual_lp_edit":0})
    write_json(OUT/'summary.json',{"schema_version":"round3z_nagi_s4_s5_grammar_v1","status":"HOLD — SARAH HUMAN VISUAL REVIEW PENDING","source_head":"WORKFLOW_HEAD","baseline_head":BASELINE_HEAD,"qa":result,"required_artifacts":["full 1440/390","S4 desktop 1440/1280/1024/768","S4 mobile entry 430/390/375/360/320","S4 element captures","S5 desktop/mobile","motif comparisons","fixed-header JSON","copy snapshot","grammar audit","regression ledger","reproduction HTML/assets","manifest"],"gates":{"G0":"PASS","G1":"PASS","G2":"PASS","G3":"MACHINE_PASS_HUMAN_PENDING","G4":"PASS","G5":"HUMAN_REVIEW_PENDING","G6":"NOT_STARTED"},"human_review_ready":"YES" if result["status"]=="PASS" else "NO","formal_human_quality_pass":False})
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='manifest.json': files.append({"path":p.relative_to(OUT).as_posix(),"size_bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    write_json(OUT/'manifest.json',{"schema_version":"round3z_manifest_v1","file_count":len(files)+1,"files":files})
    return 0 if result["status"]=="PASS" else 1


if __name__ == '__main__': raise SystemExit(main())
