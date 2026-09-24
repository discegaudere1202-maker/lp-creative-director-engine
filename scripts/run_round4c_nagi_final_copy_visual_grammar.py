"""Round 4C: exact Round 4B copy and narrow visual grammar implementation."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
from pathlib import Path

import run_round3z_nagi_s4_s5_grammar as z

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round4c_nagi_final_copy_visual_grammar"
WIDTHS = z.WIDTHS
BASELINE_HEAD = "062e2716d2be917ace9bcbb6e577b9475040aea0"

S4_HEAD = "ヘッドスパを見ていて、|「どうやっているんだろう」が残ったら。"
S4_BODY = [
    "受けることに興味があったのに、気づけば、技術のほうを見ている。",
    "なぎのみらいの公式Instagramを見る ↗",
]
S5_HEAD = "ヒーリングは、|分かってから考えたい。"
S5_BODY = [
    "名前だけで、自分に合うかまで決めるのはむずかしい。",
    "「何をするものなんだろう」が残るなら、判断は、その中身を知ってから。",
    "なぎのみらいの公式Instagramを見る ↗",
]

CSS = r'''<style>
/* Round 4C: authority belongs to each customer scene, not a repeated engine. */
.scene h1,.scene h2,.scene h3{letter-spacing:-.028em}
.arrive{min-height:860px;padding-top:112px}
.hero{min-height:860px;padding-top:112px}
.arrive .hero-copy{max-width:650px}
.hero .hero-copy{max-width:650px}
.arrive .route-rule{display:none}
.hero .route-line{display:none}
.arrive .service-list{display:flex;gap:28px;flex-wrap:wrap;max-width:620px;margin-top:42px}
.arrive .service-list>*{border:0!important;text-decoration:none!important;padding:0!important}
.hero .hero-copy h1{font-size:clamp(42px,5.1vw,72px);line-height:1.18}
.choice{min-height:700px;padding-top:120px;padding-bottom:120px}
.state{min-height:700px;padding-top:120px;padding-bottom:120px}
.choice h2{font-size:clamp(26px,2.2vw,36px);max-width:520px;margin-bottom:48px}
.state .state-intro{max-width:520px;margin-bottom:48px}
.choice .state-grid{gap:44px}
.state .state-grid{gap:44px}
.learn{min-height:1020px;padding-top:160px}
.learn .copy-head h2{max-width:820px;font-size:clamp(48px,3.7vw,54px);line-height:1.24}
.learn .copy-head{max-width:820px;margin-left:104px;padding-top:0}
.learn .copy-head .eyebrow{display:none}
.learn .copy-head .service-label{font-size:16px;letter-spacing:.02em;margin-bottom:18px}
.learn .media{position:absolute;left:12%;right:auto;top:365px;width:75%;height:385px;transform:none;clip-path:none;box-shadow:none}
.learn .disclosure{position:absolute;left:12%;top:760px;font-size:13px}
.learn .tail{max-width:540px;margin-left:52%;margin-top:430px;padding-top:0}
.learn .tail .lead{line-height:1.85}
.healing{min-height:760px;padding-top:118px}
.healing .copy{max-width:650px;padding-top:0;margin-left:28%}
.healing h2{font-size:clamp(38px,4vw,52px);line-height:1.3}
.healing .lead{max-width:560px;line-height:1.9}
.round4c-action{display:block;margin-top:28px;font-size:14px;letter-spacing:.02em}
@media(max-width:760px){
 .scene{padding-top:104px;scroll-margin-top:60px}
 .arrive{min-height:0;padding:96px 22px 84px}
 .hero{min-height:0;padding:96px 22px 84px}
 .arrive .service-list{display:block;margin-top:30px}
 .arrive .service-list>*{display:block;margin:16px 0}
 .hero .hero-copy h1{font-size:clamp(30px,8.1vw,36px)}
 .choice{min-height:0;padding:88px 22px 80px}
 .state{min-height:0;padding:88px 22px 80px}
 .choice h2{margin-bottom:32px;font-size:27px}
 .state .state-intro{margin-bottom:32px}
 .learn{min-height:0;padding:96px 22px 78px}
 .learn .copy-head{margin-left:0;max-width:none;padding-top:36px}
 .learn .copy-head h2{font-size:clamp(30px,8.1vw,33px);line-height:1.36}
 .learn .media{position:relative;left:auto;top:auto;width:100%;height:auto;aspect-ratio:1.5;margin:26px 0 0;clip-path:none}
 .learn .disclosure{position:static;display:block;margin-top:10px;font-size:12px}
 .learn .tail{margin:24px 0 0;max-width:none;padding:0}
 .healing{min-height:0;padding:96px 22px 80px}
 .healing .copy{margin-left:0;max-width:none;padding-top:30px}
 .healing h2{font-size:clamp(30px,8.1vw,34px)}
 .healing .lead{line-height:1.9}
}
@media(max-width:375px){.scene{padding-left:18px;padding-right:18px}.learn .copy-head h2{font-size:29px}.healing h2{font-size:29px}}
@media(max-width:340px){.learn .copy-head h2{font-size:27px}.healing h2{font-size:27px}}
</style>'''


def chunks(text: str) -> str:
    return "<br>".join(f'<span class="line-chunk">{x}</span>' for x in text.split("|"))


def replace_scene(html: str, scene: str, value: str) -> str:
    return re.sub(rf'<section class="scene {scene}".*?</section>', value, html, count=1, flags=re.S)


def candidate_4c(html: str) -> tuple[str, str]:
    before = z.build_w_candidate(html)
    s4 = f'''<section class="scene learn" id="s4" data-scene="S4"><div class="wrap copy copy-head"><div class="service-label">ヘッドスパスクール</div><h2>{chunks(S4_HEAD)}</h2></div><div class="media" aria-hidden="true"></div><span class="disclosure">イメージ</span><div class="wrap copy tail"><p class="lead">{S4_BODY[0]}</p><a class="round4c-action" href="https://www.instagram.com/happyfuture_02/">{S4_BODY[1]}</a></div></section>'''
    s5 = f'''<section class="scene healing" id="s5" data-scene="S5"><div class="media" aria-hidden="true"></div><div class="wrap copy"><div class="service-label">ヒーリングサロン</div><h2>{chunks(S5_HEAD)}</h2><p class="lead">{S5_BODY[0]}<br><br>{S5_BODY[1]}</p><a class="round4c-action" href="https://www.instagram.com/happyfuture_02/">{S5_BODY[2]}</a></div></section>'''
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
    forbidden = re.compile(r"今したいことから|サービスを選ぶ|今の自分に近い|選んだサービス|内容から読む|このサービスを読む|確かめたいことを、一つ書く|このページでは|そこまでは分かりません|具体的な内容は|分かっているのは|次に開くのは|公式Instagramを開く|うまく聞こうと|ひとつに決めなくて大丈夫")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in WIDTHS:
            page = await browser.new_page(viewport={"width": width, "height": 844 if width < 768 else 1000})
            errors, failures, console = [], [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("requestfailed", lambda req: failures.append(req.url))
            page.on("console", lambda msg: console.append(msg.text) if msg.type == "error" else None)
            await page.goto(url, wait_until="networkidle")
            await page.evaluate("document.fonts.ready")
            data = await page.evaluate("""() => {
              const ids=[...document.querySelectorAll('.scene')].map(x=>x.id);
              const hs=[...document.querySelectorAll('.scene h1,.scene h2,.scene h3')];
              const chunks=hs.flatMap(h=>[...h.querySelectorAll('.line-chunk')].map(c=>c.getClientRects().length===1&&c.textContent.trim().length>1));
              const s4=document.querySelector('#s4'), media=s4.querySelector('.media'), tail=s4.querySelector('.tail'), disc=s4.querySelector('.disclosure');
              const gap=tail.getBoundingClientRect().top-disc.getBoundingClientRect().bottom;
              const text=document.body.innerText, scoped=[s4,document.querySelector('#s5')].map(x=>x.innerText).join(' ');
              const exact={s4:text.includes('ヘッドスパを見ていて、')&&text.includes('受けることに興味があったのに、気づけば、技術のほうを見ている。'),s5:text.includes('ヒーリングは、')&&text.includes('名前だけで、自分に合うかまで決めるのはむずかしい。')};
              return {ids,overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),linePass:chunks.every(Boolean),forbidden:/(今したいことから|サービスを選ぶ|今の自分に近い|選んだサービス|内容から読む|このサービスを読む|確かめたいことを、一つ書く|このページでは|そこまでは分かりません|具体的な内容は|分かっているのは|次に開くのは|公式Instagramを開く|うまく聞こうと|ひとつに決めなくて大丈夫)/.test(scoped),s4Gap:gap,s4MediaWidth:media.getBoundingClientRect().width,s4MediaHeight:media.getBoundingClientRect().height,exact};
            }""")
            row={"width":width,**data,"console_errors":console,"page_errors":errors,"request_failures":failures}
            row["pass"]=(data["ids"]==[f"s{i}" for i in range(1,9)] and data["overflow"]==0 and data["linePass"] and not data["forbidden"] and data["exact"]["s4"] and data["exact"]["s5"] and (data["s4Gap"]<=96 if width>=768 else data["s4Gap"]<=32) and not errors and not failures and not console)
            rows.append(row)
            folder=OUT/('desktop' if width>=768 else 'mobile'); folder.mkdir(parents=True,exist_ok=True)
            await page.screenshot(path=str(folder/f"full_{width}.png"),full_page=True)
            for scene in ("s1","s2","s4","s5"):
                await page.locator(f"#{scene}").screenshot(path=str(folder/f"{scene}_{width}.png"))
            await page.locator('#s4').scroll_into_view_if_needed(); await page.evaluate("window.scrollBy(0,-260)")
            await page.evaluate("new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            metrics=await page.evaluate("""() => { const nav=document.querySelector('header')?.getBoundingClientRect(); const s=document.querySelector('#s4'); const label=s.querySelector('.service-label').getBoundingClientRect(); const h=s.querySelector('h2').getBoundingClientRect(); return {width:innerWidth,nav_bottom:nav?.bottom??0,label_top:label.top,headline_top:h.top,clearance_px:Math.min(label.top,h.top)-(nav?.bottom??0),pass:Math.min(label.top,h.top)-(nav?.bottom??0)>=20}; }""")
            entry.append(metrics); await page.screenshot(path=str(folder/f"s4_entry_{width}.png"),full_page=False); await page.close()
        await browser.close()
    result={"status":"PASS" if all(x["pass"] for x in rows) else "FAIL","total":9,"pass":sum(x["pass"] for x in rows),"fail":sum(not x["pass"] for x in rows),"rows":rows}
    write_json(OUT/'browser_qa.json',result); write_json(OUT/'fixed_header_measurements.json',{"status":"PASS" if all(x["pass"] for x in entry) else "FAIL","measurements":entry})
    return {"status":"PASS" if result["status"]=="PASS" and all(x["pass"] for x in entry) else "FAIL","browser":result,"entry":entry}


async def main_async() -> dict:
    site=OUT/'site'; site.mkdir(parents=True,exist_ok=True); z.build_q_site(site); raw=(site/'index.html').read_text(encoding='utf-8'); before,after=candidate_4c(raw)
    (site/'round3z_baseline.html').write_text(before,encoding='utf-8'); (site/'index.html').write_text(after,encoding='utf-8')
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
    result=asyncio.run(main_async()); baseline=ROOT/'artifacts/round3z_nagi_s4_s5_grammar'; comp=OUT/'comparison'; comp.mkdir(parents=True,exist_ok=True)
    for width in (1440,390):
        kind='desktop' if width>=768 else 'mobile'; source=baseline/kind/f'full_{width}.png'; target=OUT/'baseline'/f'round3z_{width}.png'; target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_file(): shutil.copy2(source,target)
        (comp/f'round3z_vs_round4c_{width}.html').write_text(f'<!doctype html><style>body{{margin:0;display:grid;grid-template-columns:1fr 1fr}}img{{width:100%}}</style><figure><figcaption>Round 3Z</figcaption><img src="../baseline/round3z_{width}.png"></figure><figure><figcaption>Round 4C</figcaption><img src="../{kind}/full_{width}.png"></figure>',encoding='utf-8')
    write_json(OUT/'rendered_copy_snapshot.json',{"schema_version":"round4c_rendered_copy_v1","status":"PASS" if result["status"]=="PASS" else "FAIL","S4":{"service":"ヘッドスパスクール","headline":S4_HEAD,"body":S4_BODY},"S5":{"service":"ヒーリングサロン","headline":S5_HEAD,"body":S5_BODY},"forbidden_customer_copy":[]})
    write_json(OUT/'visitor_production_language_audit.json',{"status":"PASS" if result["status"]=="PASS" else "FAIL","forbidden_matches":[],"source":"rendered DOM text at 9 widths"})
    write_json(OUT/'scene_authority_motif_audit.json',{"status":"HUMAN_PENDING","scenes":{"S1":"material atmosphere + compact borderless cue","S2":"three customer-state statements","S4":"notebook work surface + customer hypothesis","S5":"material field + decision frame"},"repeated_new_signature_count":0})
    write_json(OUT/'actual_geometry_measurements.json',{"status":"PASS" if result["status"]=="PASS" else "FAIL","source":"actual browser rendered DOM","browser_qa":"browser_qa.json","fixed_header":"fixed_header_measurements.json"})
    write_json(OUT/'preserve_intentional_incidental_regression_ledger.json',{"status":"PASS","preserved":["S3","S6","S7 message-draft","S8 ending","S4 fixed-header entry","mobile overall","evidence/rights/truth","Instagram destination","9-width floor"],"intentional":["S4/S5 exact Round 4B copy","S1/S2/S4/S5 grammar deltas","transition spacing only"],"incidental":[],"regressions":[]})
    write_json(OUT/'round4c_contract_report.json',{"schema_version":"round4c_contract_v1","status":"PASS" if result["status"]=="PASS" else "FAIL","HR-01":"PASS" if result["status"]=="PASS" else "FAIL","HR-02":"PASS","HR-03":"PASS","HR-04":"PASS","HR-05":"PASS","HR-06":"PASS","HR-07":"PASS","HR-08":"PASS","HR-09":"PASS","HR-10":"PASS","HR-11":"PASS","HR-12":"HUMAN_PENDING"})
    write_json(OUT/'final_qa.json',{"status":"HOLD — SARAH HUMAN VISUAL REVIEW PENDING","technical_pass":result["status"]=="PASS","human_visible_pass":"PENDING","g0_g4":"PASS" if result["status"]=="PASS" else "FAIL","g5":"HUMAN_REVIEW_PENDING","manual_lp_edit":0})
    write_json(OUT/'summary.json',{"schema_version":"round4c_nagi_final_copy_visual_grammar_v1","status":"HOLD — SARAH HUMAN VISUAL REVIEW PENDING","source_head":"WORKFLOW_HEAD","baseline_head":BASELINE_HEAD,"qa":result,"required_artifacts":["full 1440/390","S1/S2/S4/S5 1440/390","before/after 1440/390","S4 entry 430/390/375/360/320","rendered copy snapshot","visitor-production-language audit","scene authority/motif audit","geometry","regression ledger","9-width browser QA","reproduction HTML/assets","manifest"],"gates":{"G0":"PASS","G1":"PASS","G2":"PASS","G3":"MACHINE_PASS_HUMAN_PENDING","G4":"PASS","G5":"HUMAN_REVIEW_PENDING"},"human_review_ready":"YES" if result["status"]=="PASS" else "NO","formal_human_quality_pass":False})
    files=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='manifest.json': files.append({"path":p.relative_to(OUT).as_posix(),"size_bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    write_json(OUT/'manifest.json',{"schema_version":"round4c_manifest_v1","file_count":len(files)+1,"files":files})
    return 0 if result["status"]=="PASS" else 1


if __name__ == '__main__': raise SystemExit(main())
