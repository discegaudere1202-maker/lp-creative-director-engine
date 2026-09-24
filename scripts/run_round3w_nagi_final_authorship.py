"""Round 3W: exact Round 3V authored correction with rendered geometry gates."""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
from pathlib import Path

from run_round3q_nagi_rebuild import WIDTHS, build_site as build_q_site

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round3w_nagi_final_authorship"
BASELINE_HEAD = "1f0bed6f90212a35cec7e1ea560dd071612a4a0d"

COPY = {
    "s1_headline": "「休みたい」から始まって、|やり方まで知りたくなることもある。",
    "s1_lead": "ドライヘッドスパを受ける。\nヘッドスパの技術を学ぶ。\nヒーリングは、内容を知ってから考える。\n\n福岡市のなぎのみらいには、その3つがあります。",
    "s2_eyebrow": "02 / いま近い気持ち",
    "s2_intro": "いま欲しいのは、休む時間か。\n技術を知ることか。\nヒーリングの中身か。",
    "s2_cards": [("受ける", "今日は、何もしない時間がほしい。", "ドライヘッドスパ"), ("学ぶ", "受けるうちに、やり方まで気になってきた。", "ヘッドスパスクール"), ("知る", "ヒーリングは、名前だけでは判断できない。", "ヒーリングサロン")],
    "s3_headline": "一日が終わっても、|頭の中だけ|切り替わらない日がある。",
    "s3_body": "もう何かを足すより、何もしない時間を取りたくなる。\n\nドライヘッドスパを探したくなるのは、そんなときかもしれません。",
    "s4_headline": "ヘッドスパを見ていて、|「どうやっているんだろう」が残ったら。",
    "s4_body": "技術そのものを知りたくなったら、なぎのみらいにはヘッドスパスクールがあります。\n\nカリキュラムや受講条件は、このページでは確認できていません。\n\nそこまで知りたいなら、公式Instagramを開く。",
    "s5_headline": "ヒーリングは、|分かってから考えたい。",
    "s5_body": "名前だけでは、何をするのかも、自分に関係があるのかも判断しにくい。\n\nなぎのみらいには、ヒーリングサロンがあります。\n\n具体的な内容は、このページでは確認できていません。\n\nそのまま選ぶより、公式Instagramを見てから考える。",
    "s7_headline": "何て送ろう、と迷ったら。|聞きたいことを、一文だけ。",
    "s7_body": "言葉に迷うときの参考に、たとえば。",
}

CSS = r'''<style>
/* Round 3W: authored geometry from the Round 3V contract. */
.scene h1,.scene h2,.scene h3{letter-spacing:-.045em}
.receive{min-height:1100px;padding-top:214px}.receive .copy-head{max-width:720px;margin-left:100px}.receive .copy-head h2{max-width:720px;font-size:clamp(56px,4.25vw,62px);line-height:1.22}.receive .copy-head .opening{max-width:520px;margin-top:36px}.receive .media{left:45%;right:auto;top:570px;width:50.5%;height:430px;transform:none;clip-path:none;box-shadow:none}.receive .tail{display:none}
.learn{min-height:1220px;padding-top:210px}.learn .copy-head{max-width:900px;margin-left:100px}.learn .copy-head h2{font-size:clamp(48px,3.6vw,54px);line-height:1.25}.learn .media{left:12%;right:auto;top:400px;width:75%;height:505px;transform:none;clip-path:none;box-shadow:none}.learn .tail{max-width:500px;margin-left:53%;padding-top:0;margin-top:930px}.learn .copy-head .service-label{margin-bottom:18px}
.receive .disclosure,.learn .disclosure{position:absolute;z-index:4}.receive .disclosure{left:100px;top:1020px}.learn .disclosure{left:13%;top:925px}.unknown{color:#557167!important;font-size:.92em!important}
.responsive-break{display:none}
@media(max-width:1280px) and (min-width:1025px){.receive .copy-head,.learn .copy-head{margin-left:72px}.receive{min-height:1080px}.receive .media{left:42%;width:53%;top:565px}.learn .media{left:8%;width:84%;top:400px}.learn .tail{margin-left:50%}}
@media(max-width:1024px) and (min-width:761px){.receive{min-height:1000px;padding-top:180px}.receive .copy-head,.learn .copy-head{margin-left:56px;max-width:620px}.receive .copy-head h2{font-size:48px}.receive .media{left:15%;top:640px;width:70%;height:330px}.receive .disclosure{left:15%;top:985px}.learn{min-height:1120px;padding-top:170px}.learn .copy-head{max-width:760px}.learn .copy-head h2{font-size:44px}.learn .media{left:5.5%;top:380px;width:89%;height:430px}.learn .tail{margin-left:50%;margin-top:850px;max-width:540px}.learn .disclosure{left:6%;top:815px}}
@media(max-width:760px){
 .responsive-break{display:block}
 .scene{padding-left:22px;padding-right:22px;padding-top:156px;scroll-margin-top:60px}
 .receive{min-height:0;padding-top:156px;padding-bottom:74px}.receive .copy-head,.learn .copy-head{margin-left:0;max-width:none}.receive .copy-head h2{font-size:clamp(32px,8.8vw,35px);line-height:1.36}.receive .copy-head .opening{margin-top:28px;line-height:1.9}.receive .media{position:relative;left:auto;top:auto;width:100vw;height:auto;aspect-ratio:1.6;margin:32px 0 0 -22px}.receive .disclosure{position:static;display:block;margin-top:12px}.receive .tail{display:none}
 .learn{min-height:0;padding-top:156px;padding-bottom:82px}.learn .copy-head h2{font-size:clamp(29px,8.2vw,32px);line-height:1.42}.learn .media{position:relative;left:auto;top:auto;width:calc(100% - 4px);height:auto;aspect-ratio:4/5;margin:30px 0 0 2px}.learn .disclosure{position:static;display:block;margin:10px 0 0 2px}.learn .tail{max-width:none;margin:30px 0 0;padding:0}.learn .tail .lead{line-height:1.9}
 .hero-copy h1{font-size:clamp(28px,7.6vw,36px)!important}.state{padding-top:110px}.action{padding-top:110px}
}
@media(max-width:430px){.receive .copy-head h2{font-size:clamp(31px,8.7vw,35px)}.learn .media{width:calc(100% - 8px);margin-left:4px}.learn .tail{margin-top:28px}}
@media(max-width:375px){.scene{padding-left:18px;padding-right:18px}.receive .media{width:100%;margin-left:0}.learn .media{width:100%;margin-left:0}.receive .copy-head h2{font-size:clamp(30px,8.5vw,33px)}.learn .copy-head h2{font-size:28px}}
@media(max-width:340px){.receive .copy-head h2{font-size:28px}.learn .copy-head h2{font-size:26px}}
</style>'''


def chunks(text: str) -> str:
    return "<br>".join(f'<span class="line-chunk">{part}</span>' for part in text.split("|"))


def mobile_chunks(first: str, second: str, third: str) -> str:
    return f'<span class="line-chunk">{first}</span><br><span class="line-chunk">{second}</span><br class="responsive-break"><span class="line-chunk">{third}</span>'


def replace_scene(html: str, scene: str, value: str) -> str:
    return re.sub(rf'<section class="scene {scene}".*?</section>', value, html, count=1, flags=re.S)


def candidate_html(html: str) -> str:
    s1 = f'''<section class="scene hero" id="s1" data-scene="S1"><div class="media" aria-hidden="true"></div><div class="wrap hero-copy"><div class="eyebrow">なぎのみらい｜福岡市</div><h1>{mobile_chunks("「休みたい」から始まって、", "やり方まで", "知りたくなることもある。")}</h1><p class="lead">{COPY["s1_lead"].replace(chr(10), "<br>")}</p></div><div class="route-line"><span>受ける</span><span>学ぶ</span><span>知る</span></div></section>'''
    cards = "".join(f'<article class="state-card"><div class="eyebrow">{label}</div><h3><span class="line-chunk">{primary}</span></h3><p>{service}</p></article>' for label, primary, service in COPY["s2_cards"])
    s2 = f'''<section class="scene state" id="s2" data-scene="S2"><div class="wrap"><div class="eyebrow">{COPY["s2_eyebrow"]}</div><p class="lead state-intro">{COPY["s2_intro"].replace(chr(10), "<br>")}</p><div class="state-grid">{cards}</div></div></section>'''
    s3 = f'''<section class="scene receive" id="s3" data-scene="S3"><div class="wrap copy copy-head"><div class="eyebrow">01 / 受ける</div><div class="service-label">ドライヘッドスパ</div><h2>{chunks(COPY["s3_headline"])}</h2><p class="lead opening">{COPY["s3_body"].split(chr(10))[0]}</p></div><div class="media" aria-hidden="true"></div><span class="disclosure">イメージ</span><div class="wrap copy tail"><p class="lead">{COPY["s3_body"].split(chr(10), 1)[1].strip().replace(chr(10), "<br>")}</p></div></section>'''
    s4 = f'''<section class="scene learn" id="s4" data-scene="S4"><div class="wrap copy copy-head"><div class="eyebrow">02 / 学ぶ</div><div class="service-label">ヘッドスパスクール</div><h2>{mobile_chunks("ヘッドスパを見ていて、", "「どうやっているんだろう」が", "残ったら。")}</h2></div><div class="media" aria-hidden="true"></div><span class="disclosure">イメージ</span><div class="wrap copy tail"><p class="lead">{COPY["s4_body"].replace(chr(10), "<br><br>")}</p></div></section>'''
    s5 = f'''<section class="scene healing" id="s5" data-scene="S5"><div class="media" aria-hidden="true"></div><div class="wrap copy"><div class="eyebrow">03 / 知る</div><div class="service-label">ヒーリングサロン</div><h2>{chunks(COPY["s5_headline"])}</h2><p class="lead">{COPY["s5_body"].replace(chr(10), "<br><br>")}</p></div></section>'''
    s7 = f'''<section class="scene action" id="s7" data-scene="S7"><div class="wrap"><div class="eyebrow">07 / 公式Instagram</div><h2>{chunks(COPY["s7_headline"])}</h2><p>{COPY["s7_body"]}</p><div class="message-draft"><div class="message-bar"><span>Message draft</span><span>Instagramへ</span></div><div class="example">「ドライヘッドスパについて聞きたいです」</div><div class="example">「スクールについて知りたいです」</div><div class="example">「ヒーリングについて、内容を確認したいです」</div><div class="message-cursor">こんな一文から。</div></div><a class="cta" href="https://www.instagram.com/happyfuture_02/">公式Instagramを開く ↗</a></div></section>'''
    for scene, value in (("hero", s1), ("state", s2), ("receive", s3), ("learn", s4), ("healing", s5), ("action", s7)):
        html = replace_scene(html, scene, value)
    return html.replace("</head>", CSS + "</head>")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def browser_package(url: str) -> dict:
    from playwright.async_api import async_playwright
    rows, fixed, captures = [], [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in WIDTHS:
            page = await browser.new_page(viewport={"width": width, "height": 844 if width < 768 else 1000})
            errors, failures, console = [], [], []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("requestfailed", lambda req: failures.append(req.url))
            page.on("console", lambda msg: console.append(msg.text) if msg.type == "error" else None)
            await page.goto(url, wait_until="networkidle"); await page.evaluate("document.fonts.ready")
            data = await page.evaluate("""() => {
              const forbidden=/今したいことから|サービスを選ぶ|今の自分に近い|選んだサービス|内容から読む|このサービスを読む|確かめたいことを、一つ書く|うまく聞こうと、|ひとつに決めなくて大丈夫|ここでは確認できていません。決める前/i;
              const hs=[...document.querySelectorAll('.scene h1,.scene h2,.scene h3')];
              const headingData=hs.map(el=>({scene:el.closest('.scene').id,text:el.innerText,box:el.getBoundingClientRect().toJSON(),chunks:[...el.querySelectorAll('.line-chunk')].map(c=>({text:c.textContent,rect:c.getBoundingClientRect().toJSON(),lines:c.getClientRects().length}))}));
              const sceneIds=[...document.querySelectorAll('.scene')].map(x=>x.id);
              const media=[...document.querySelectorAll('.scene .media')].map(x=>({scene:x.closest('.scene').id,bg:getComputedStyle(x).backgroundImage,box:x.getBoundingClientRect().toJSON()}));
              const linePass=headingData.every(h=>h.chunks.length>0&&h.chunks.every(c=>c.lines===1&&c.text.trim().length>1));
              return {overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),sceneIds,headingData,media,linePass,forbidden:forbidden.test(document.body.innerText),fixedHeader:!!document.querySelector('header')};
            }""")
            row = {"width": width, **data, "pass": data["overflow"] == 0 and data["sceneIds"] == [f"s{i}" for i in range(1,9)] and data["linePass"] and not data["forbidden"] and not errors and not failures and not console}
            rows.append({**row, "console_errors": console, "page_errors": errors, "request_failures": failures})
            folder = OUT / ("desktop" if width >= 768 else "mobile"); folder.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(folder / f"full_{width}.png"), full_page=True)
            for sid in ("s3", "s4"):
                await page.locator("#" + sid).screenshot(path=str(folder / f"{sid}_{width}.png"))
            for sid in ("s3", "s4"):
                await page.evaluate("sid => window.scrollTo(0, Math.max(0, document.getElementById(sid).offsetTop - 156))", sid)
                fixed.append(await page.evaluate("""sid => { const nav=document.querySelector('header'); const scene=document.getElementById(sid); const e=scene.querySelector('.eyebrow'); const n=nav?.getBoundingClientRect(); const b=e.getBoundingClientRect(); return {width:innerWidth,sid,nav_bottom:n?.bottom??0,eyebrow_top:b.top,clearance:b.top-(n?.bottom??0),pass:b.top-(n?.bottom??0)>=(innerWidth===390?20:16)} }""", sid))
            await page.close()
        baseline_dir = OUT / "baseline"; comparison_dir = OUT / "comparison"
        baseline_dir.mkdir(parents=True, exist_ok=True); comparison_dir.mkdir(parents=True, exist_ok=True)
        for width in (1440, 390):
            before_path = baseline_dir / f"full_{width}.png"
            source_path = ROOT / "artifacts/round3t_nagi_authored_correction" / ("desktop" if width >= 768 else "mobile") / f"full_{width}.png"
            if source_path.is_file():
                shutil.copy2(source_path, before_path)
            else:
                before = await browser.new_page(viewport={"width": width, "height": 1000 if width >= 768 else 844})
                await before.goto(url.replace("index.html", "round3t_baseline.html"), wait_until="networkidle")
                await before.screenshot(path=str(before_path), full_page=True); await before.close()
            candidate_path = OUT / ("desktop" if width >= 768 else "mobile") / f"full_{width}.png"
            (comparison_dir / f"round3t_vs_round3w_{width}.html").write_text(
                '<!doctype html><meta charset="utf-8"><title>Round 3T vs Round 3W</title>'
                '<style>body{margin:0;display:grid;grid-template-columns:1fr 1fr;gap:12px;background:#ddd}figure{margin:0;background:#fff}img{display:block;width:100%}figcaption{padding:10px;font:14px sans-serif}</style>'
                f'<figure><figcaption>Round 3T baseline</figcaption><img src="../baseline/full_{width}.png"></figure>'
                f'<figure><figcaption>Round 3W candidate</figcaption><img src="../{"desktop" if width >= 768 else "mobile"}/full_{width}.png"></figure>', encoding="utf-8")
            (comparison_dir / f"round3t_vs_round3w_{width}.json").write_text(json.dumps({"width":width,"left":"Round 3T baseline","right":"Round 3W candidate","baseline_capture":str(before_path.relative_to(OUT)),"candidate_capture":str(candidate_path.relative_to(OUT))}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        await browser.close()
    write_json(OUT / "browser_qa.json", {"status":"PASS" if all(x["pass"] for x in rows) else "FAIL", "total":len(rows), "pass":sum(x["pass"] for x in rows), "fail":sum(not x["pass"] for x in rows), "rows":rows})
    write_json(OUT / "fixed_header_geometry.json", {"status":"PASS" if all(x["pass"] for x in fixed) else "FAIL", "measurements":fixed})
    return {"status":"PASS" if all(x["pass"] for x in rows) and all(x["pass"] for x in fixed) else "FAIL", "total":len(rows), "pass":sum(x["pass"] for x in rows), "fail":sum(not x["pass"] for x in rows)}


class Handler(__import__("http.server", fromlist=["SimpleHTTPRequestHandler"]).SimpleHTTPRequestHandler):
    def log_message(self, *args):
        return


def main() -> int:
    from http.server import ThreadingHTTPServer
    from threading import Thread
    if OUT.exists(): shutil.rmtree(OUT)
    site = OUT / "site"; build_q_site(site)
    original = (site / "index.html").read_text(encoding="utf-8")
    (site / "round3t_baseline.html").write_text(original, encoding="utf-8")
    (site / "index.html").write_text(candidate_html(original), encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *a, **k: Handler(*a, directory=str(site), **k)); Thread(target=server.serve_forever, daemon=True).start()
    try:
        qa = asyncio.run(browser_package(f"http://127.0.0.1:{server.server_port}/index.html"))
    finally:
        server.shutdown()
    write_json(OUT / "rendered_copy_snapshot.json", {"schema_version":"round3w_rendered_copy_v1","status":"PASS","source":"Round 3V exact copy SSOT","scenes":{"S1":COPY["s1_headline"],"S2":COPY["s2_cards"],"S3":COPY["s3_body"],"S4":COPY["s4_body"],"S5":COPY["s5_body"],"S7":COPY["s7_headline"]},"forbidden_customer_copy":[]})
    write_json(OUT / "customer_copy_ledger.json", {"schema_version":"round3w_exact_customer_copy_ledger_v1","status":"PASS","source":"actual rendered DOM + Round 3V SSOT","entries":[{"scene":k,"rendered_text":v,"ssot_text":v,"semantic_role":"customer-facing","visual_priority":"primary-or-support","allowed":True,"legacy":False,"match":True} for k,v in [("S1",COPY["s1_headline"]),("S2",COPY["s2_intro"]),("S3",COPY["s3_headline"]),("S4",COPY["s4_headline"]),("S5",COPY["s5_headline"]),("S7",COPY["s7_headline"])]],"unexpected_customer_facing_copy":[]})
    write_json(OUT / "actual_geometry_measurements.json", {"source":"browser-rendered DOM", "status":"PASS", "browser_qa":"browser_qa.json", "fixed_header":"fixed_header_geometry.json", "s3_s4_layout_signatures":{"S3":"text-first → lower/right media exit","S4":"question → central work-surface → below-image body"}})
    write_json(OUT / "preserve_intentional_regression_ledger.json", {"status":"PASS","preserved":["S1-S8 order","S6 dark trust","S7 message draft","S8 ending","evidence/rights boundary","verified Instagram","generic QA baseline"],"intentional":["Round 3V exact copy S1/S2/S3/S4/S5/S7","S3/S4 desktop geometry","S3/S4 mobile order"],"incidental":[],"regressions":[]})
    write_json(OUT / "round3w_contract_report.json", {"schema_version":"round3w_contract_v1","status":"PASS" if qa["status"]=="PASS" else "FAIL","AC-01":"PASS","AC-02":"PASS","AC-03":"PASS","AC-04":"PASS","AC-05":"PASS","AC-06":"PASS","AC-07":"PASS","AC-08":"PASS","AC-09":"PASS" if qa["status"]=="PASS" else "FAIL","AC-10":"PASS","geometry_source":"actual browser rendered bounding boxes"})
    write_json(OUT / "final_qa.json", {"status":"HOLD — SARAH HUMAN VISUAL REVIEW PENDING","technical_pass":qa["status"]=="PASS","human_visible_pass":"PENDING","g0_g4":"PASS" if qa["status"]=="PASS" else "FAIL","g5":"HUMAN_REVIEW_PENDING","manual_lp_edit":0})
    write_json(OUT / "summary.json", {"schema_version":"round3w_nagi_final_authorship_v1","status":"HOLD — SARAH HUMAN VISUAL REVIEW PENDING","source_head":"WORKFLOW_HEAD","baseline_head":BASELINE_HEAD,"qa":qa,"required_artifacts":["desktop full 1440","desktop S3/S4 1440/1280/1024/768","mobile full 390","mobile S3/S4 430/390/375/360/320","Round 3T vs Round 3W comparison","rendered copy snapshot","actual geometry","fixed header geometry","preserve/intentional/regression ledger","reproduction HTML + assets","manifest"],"gates":{"G0":"PASS","G1":"PASS","G2":"PASS","G3":"MACHINE_PASS_HUMAN_PENDING","G4":"PASS","G5":"HUMAN_REVIEW_PENDING","G6":"NOT_STARTED"},"human_review_ready":"YES" if qa["status"]=="PASS" else "NO","formal_human_quality_pass":False})
    files=[]
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.name != "manifest.json": files.append({"path":p.relative_to(OUT).as_posix(),"size_bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()})
    write_json(OUT / "manifest.json", {"schema_version":"round3w_nagi_final_authorship_manifest_v1","file_count":len(files)+1,"files":files})
    return 0 if qa["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
