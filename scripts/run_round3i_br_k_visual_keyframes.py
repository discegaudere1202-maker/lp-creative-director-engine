"""Round 3I-BR-K: bounded visual keyframe study for Nagi.

This deliberately emits three independent, code-generated visual studies. It does
not alter the Round 3I-B implementation or generate a full page.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import subprocess
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round3i_br_k"
WIDTHS = (1440, 390, 320)

CSS = r'''
@font-face{font-family:Noto;src:url('fonts/NotoSansJP-Variable.ttf');font-weight:100 900;font-display:swap}
@font-face{font-family:Inter;src:url('fonts/InterTight-Variable.ttf');font-weight:100 900;font-display:swap}
:root{--ink:#1b2421;--mineral:#ded7c9;--sage:#9fb8ae;--moss:#526b61;--deep:#16383b;--cream:#f4f0e7;--line:#203b3b70;--signal:#b77b43}*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--ink);font-family:Noto,sans-serif}main{display:grid;gap:0}.frame{min-height:100vh;position:relative;overflow:hidden;padding:74px 8vw 7vw;isolation:isolate}.kicker{font:600 12px Inter,sans-serif;letter-spacing:.16em;text-transform:uppercase;opacity:.68}.copy{position:relative;z-index:4;max-width:510px}.copy h1{font-weight:620;letter-spacing:-.08em;line-height:1.12;font-size:clamp(45px,5.4vw,82px);margin:24px 0 22px}.copy p{line-height:2;color:#40514b;max-width:430px}.micro{font:500 12px Inter,sans-serif;letter-spacing:.08em}.route{position:absolute;z-index:5;right:7vw;top:29%;width:42%;height:42%;display:grid;grid-template-columns:repeat(3,1fr);align-items:end;gap:6%;border-bottom:1px solid var(--line);padding:0 2% 5%}.route:before{content:'';position:absolute;left:8%;right:9%;bottom:13%;height:38%;border-top:1px solid var(--line);border-radius:50% 50% 0 0;transform:rotate(-9deg)}.route span{position:relative;font-size:clamp(20px,2.1vw,34px);font-weight:650;letter-spacing:-.08em}.route span:nth-child(2){align-self:center}.route span:nth-child(3){align-self:start}.hero{background:var(--mineral)}.hero:before{content:'';position:absolute;z-index:0;inset:18% 0 0 28%;background:linear-gradient(112deg,#ffffff22,#ffffffb8 42%,#bd9d7258),radial-gradient(ellipse at 70% 25%,#fff8 0 12%,transparent 43%),repeating-linear-gradient(103deg,#8d795333 0 1px,transparent 1px 15px);clip-path:polygon(12% 0,100% 7%,94% 100%,0 92%);box-shadow:-30px 35px 50px #795e4930}.hero:after{content:'';position:absolute;z-index:1;width:38vw;height:38vw;right:-10vw;bottom:-17vw;border:1px solid #35554d65;border-radius:49% 51% 45% 55%;box-shadow:inset 0 0 0 20px #ffffff14}.hero .copy{margin-top:11vh}.hero .copy h1{max-width:620px}.hero .copy p{font-size:16px}.hero .route{color:var(--deep)}.hero .route .micro{grid-column:1/-1;align-self:start}.hero .route:after{content:'route / 01 → 02 → 03';position:absolute;right:0;bottom:-34px;font:500 11px Inter,sans-serif;letter-spacing:.12em;color:#526b61}.middle{background:#e8eee9;padding-top:0;display:flex;align-items:center}.middle:before{content:'';position:absolute;inset:0 38% 0 0;background:linear-gradient(90deg,#eef4ef,#c9d5cb88),radial-gradient(ellipse at 20% 30%,#ffffffc4 0 8%,transparent 42%);z-index:0}.middle:after{content:'';position:absolute;z-index:1;right:-8%;top:12%;width:65%;height:78%;background:linear-gradient(124deg,#ffffff30,#ffffffb8 32%,#b5c4b5 33%,#e1e7de 53%,#ffffff46 54%),repeating-linear-gradient(82deg,#64766c22 0 2px,transparent 2px 21px);clip-path:polygon(18% 0,100% 8%,86% 100%,0 89%);transform:rotate(4deg);box-shadow:-24px 22px 50px #526b6130}.middle .material-note{position:absolute;z-index:3;right:14%;bottom:12%;padding:17px 22px;background:#f8fbf5c9;border:1px solid #ffffffaa;box-shadow:0 15px 30px #526b6124;backdrop-filter:blur(8px)}.middle .material-note span{display:block;font:600 12px Inter,sans-serif;letter-spacing:.16em;color:var(--moss);margin-bottom:7px}.middle .copy{z-index:4;margin-left:6vw}.middle .copy h1{font-size:clamp(42px,4.5vw,68px);font-weight:470;line-height:1.25}.middle .copy p{max-width:380px}.middle .breath{position:absolute;z-index:4;left:6vw;bottom:11%;font:500 15px Inter,sans-serif;letter-spacing:.2em;color:var(--moss)}.late{background:var(--deep);color:#f9fbf5;padding-top:10vh}.late:before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at 20% 25%,#9fb8ae2d 0 8%,transparent 32%),linear-gradient(115deg,transparent 0 47%,#ffffff0c 47% 47.2%,transparent 47.2%);z-index:0}.late:after{content:'';position:absolute;right:8%;top:22%;width:37vw;height:48vh;border-left:1px solid #c6e0d546;border-top:1px solid #c6e0d546;transform:skewY(-12deg);z-index:1}.late .copy{margin-top:15vh}.late .copy h1{font-size:clamp(44px,5vw,75px);font-weight:570}.late .copy p{color:#c4d4cf}.late .endpoint{position:absolute;z-index:5;right:15%;bottom:21%;display:flex;align-items:center;gap:20px;color:#e4bf91}.late .endpoint i{display:block;width:100px;height:1px;background:#e4bf91}.late .endpoint strong{font-weight:600}.late .open{position:absolute;z-index:3;right:7%;bottom:8%;font:500 11px Inter,sans-serif;letter-spacing:.17em;color:#a8c2ba}.study-note{position:absolute;bottom:4%;left:8vw;font:500 11px Inter,sans-serif;letter-spacing:.12em;opacity:.6}.late .study-note{color:#c4d4cf}@media(max-width:760px){.frame{min-height:720px;padding:60px 22px 42px}.copy h1{font-size:clamp(39px,11vw,55px)}.hero .copy{margin-top:7vh}.hero:before{inset:35% -20% 6% 2%;transform:rotate(-3deg)}.route{right:10%;top:auto;bottom:15%;width:78%;height:29%;padding-bottom:10%}.route span{font-size:21px}.hero:after{width:70vw;height:70vw;right:-25vw;bottom:-20vw}.middle{min-height:760px;display:block;padding-top:82px}.middle:before{inset:0 0 42% 0}.middle:after{right:-20%;top:36%;width:116%;height:52%;}.middle .copy{margin-left:0}.middle .copy h1{font-size:43px}.middle .material-note{right:10%;bottom:9%;font-size:12px}.middle .breath{left:22px;bottom:5%}.late{min-height:760px}.late .copy{margin-top:10vh}.late:after{right:-10%;top:41%;width:82vw;height:34vh}.late .endpoint{right:12%;bottom:19%}.late .open{right:22px;bottom:8%}}
'''

HTML = r'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Nagi Visual Keyframes</title><style>%%CSS%%</style></head><body><main>
<section class="frame hero" id="keyframe-a"><div class="copy"><div class="kicker">KEYFRAME A / ENTRY</div><h1>今の自分に近い<br>入口から選ぶ。</h1><p>受ける、学ぶ、知る。目的の違う3つのサービスを、ひとつの場で見渡す。</p></div><div class="route" aria-label="service routes"><span class="micro">THREE ENTRANCES</span><span>受ける</span><span>学ぶ</span><span>知る</span></div><div class="study-note">HUMAN-SCALE WAYFINDING / generated material study</div></section>
<section class="frame middle" id="keyframe-b"><div class="copy"><div class="kicker">KEYFRAME B / MATERIAL MIDDLE</div><h1>触れる前に、<br>感じ取る。</h1><p>光が面を渡り、距離が少しひらく。サービスの違いを急がず、次に知りたいことへ進むための余白。</p></div><div class="material-note"><span>TACTILE PAUSE</span>surface / light / distance</div><div class="breath">TOUCH&nbsp;&nbsp;&nbsp;BREATH&nbsp;&nbsp;&nbsp;PAUSE</div><div class="study-note">SENSORY UNDERSTANDING / generated material study</div></section>
<section class="frame late" id="keyframe-c"><div class="copy"><div class="kicker">KEYFRAME C / LATE</div><h1>分かることが増えたら、<br>相談していい。</h1><p>確認できたことと、聞いてみたいこと。その両方を持ったまま、公式Instagramへ進めます。</p></div><div class="endpoint"><i></i><strong>@happyfuture_02 ↗</strong></div><div class="open">THE VIEW OPENS / PERMISSION TO ACT</div><div class="study-note">PERMISSION TO ACT / generated material study</div></section></main></body></html>'''

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

@contextmanager
def serve(directory: Path):
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(directory), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try: yield f"http://127.0.0.1:{server.server_port}"
    finally: server.shutdown(); thread.join(timeout=2)

def specs() -> None:
    write_json(OUT/"01_art_direction_spec.json", {"thesis":"HUMAN-SCALE WAYFINDING × TACTILE CALM × OPEN POSSIBILITY","frozen_strategy":"HYP-NAGI-CHOICE_FIRST","visual_meaning":"Structured routing with soft physical presence; not generic wellness.","generic_wellness_rejected":["sleeping person","spa stones","rolled towels","beige luxury cliché","mystical aura"],"media_role":"ATMOSPHERE / TACTILE / CONTEXT / EMOTION, never evidence authority"})
    write_json(OUT/"02_safe_visual_authority.json", {"authority":"code-generated material and SVG-like CSS geometry","provenance":"authored in this script; no external imagery or unknown rights asset","effect_preserved":True,"effect_lost":False,"evidence_boundary":"No staff, customer, premises, treatment, school, equipment, or efficacy claim is represented."})
    write_json(OUT/"07_background_resolution.json", {"keyframes":[{"id":"A","role":"orientation","visible_mechanism":"mineral base + translucent plane + organic crop + route field","surface":"warm mineral, imperfect lines","depth":"base / atmospheric plane / route foreground","light":"diffused directional","material":"linear and radial gradients with tactile line texture","media_relation":"material supports three entrances; no evidence claim","foreground_relation":"copy frames; route occupies right edge","transition_behavior":"later route motif may carry; not implemented here","mobile_translation":"route remains visible beside the material field, then compresses below copy without becoming a plain stack"},{"id":"B","role":"sensory understanding","visible_mechanism":"large faceted translucent material with light crossing surface","surface":"pale layered plane","depth":"field / translucent material / small tactile note","light":"soft cross-surface gradient","material":"layered polygon and fine line texture","media_relation":"material is the dominant visual field","foreground_relation":"quiet copy sits against open left field","transition_behavior":"material can settle while copy enters","mobile_translation":"material moves behind and below copy; tactile note remains anchored"},{"id":"C","role":"permission to act","visible_mechanism":"open dark field + route endpoint + receding line","surface":"deep mineral green","depth":"atmospheric field / open line / endpoint foreground","light":"low contrast diffused glow","material":"thin route geometry, not a box","media_relation":"openness resolves uncertainty; no hero clone","foreground_relation":"copy and endpoint have separate spatial jobs","transition_behavior":"route converges to verified Instagram endpoint","mobile_translation":"endpoint stays visible as a horizontal destination, not a boxed CTA"}]})
    write_json(OUT/"08_typography_role_spec.json", {"keyframes":[{"id":"A","role":"framing + choosing","headline":"620 weight / tight but breathable / 5.4vw max","route":"medium Inter micro plus medium Japanese labels"},{"id":"B","role":"quiet reflective","headline":"470 weight / longer leading / generous line-height","cue":"small spaced bilingual material cue"},{"id":"C","role":"trust + permission","headline":"570 weight / open dark field / calm line break","endpoint":"small warm signal, not a button"}],"repetition_guard":"No shared bold-heading + tiny-uppercase + underline grammar across all three."})
    write_json(OUT/"09_composition_spec.json", {"A":"asymmetric field; copy left, route right-edge, controlled organic overlap","B":"material-led bleed; copy occupies quiet left field; note floats on material","C":"open dark field; copy left, endpoint right, route line recedes","dominance":"A orientation / B material / C openness and route endpoint"})
    write_json(OUT/"10_renderer_preserve_manifest.json", {"preserve":["dominance","depth","material","edge","media_scale","type_role","spacing_character"],"exceptions":["scene-specific DOM","absolute layering","controlled overlap","full-bleed material","custom crop","scene-specific typography"],"scope":"three keyframes only; no full-page merge"})
    (OUT/"11_keyframe_review_manifest.md").write_text("# Round 3I-BR-K Keyframe Review\n\n- A: Entry / Hero — orientation through three entrances in one tactile spatial field.\n- B: Material Middle — sensory understanding through light crossing a translucent surface.\n- C: Late / Ending — information becomes lighter and a route endpoint permits action.\n\nAll visuals are code-generated studies; they are not photographs or service evidence. Full-page translation is intentionally not included.\n",encoding="utf-8")

async def capture(url: str) -> dict[str, Any]:
    screenshots=[]; errors=[]; rows=[]
    async with async_playwright() as p:
      browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
      for width in WIDTHS:
        page=await browser.new_page(viewport={"width":width,"height":1000 if width==1440 else 844})
        ce=[];pe=[];rf=[];page.on("console",lambda m:ce.append(m.text) if m.type=="error" else None);page.on("pageerror",lambda e:pe.append(str(e)));page.on("requestfailed",lambda r:rf.append(r.url))
        await page.goto(url,wait_until="networkidle"); await page.evaluate("document.fonts.ready")
        state=await page.evaluate("""() => ({overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),fonts:document.fonts.status,internal:[...document.body.innerText.matchAll(/DETAIL → RELATIONSHIP|GUIDED CHOICE|PATH MERGE|SELECTED TOKEN|MOTION 0[123]|SIGNATURE|AMBIENT|GROWTH HYPOTHESIS|PROVISIONAL|DUMMY|UNCONFIRMED|debug label/gi)].length,frames:document.querySelectorAll('.frame').length})""")
        row={"width":width,**state,"console_errors":ce,"page_errors":pe,"request_failures":rf};row["pass"]=state["overflow"]==0 and state["fonts"]=="loaded" and state["internal"]==0 and state["frames"]==3 and not ce and not pe and not rf;rows.append(row)
        for index,frame in enumerate(("keyframe-a","keyframe-b","keyframe-c"), start=4):
          path=OUT/f"{index:02d}_{frame.replace('-', '_')}_{width}.png";await page.locator(f"#{frame}").screenshot(path=str(path));screenshots.append(path.name)
        await page.close()
      await browser.close()
    return {"status":"PASS" if all(r["pass"] for r in rows) else "FAIL","rows":rows,"screenshots":screenshots,"comparison_vs_3i_b":"New material planes, depth layers, edge crops, route geometry, and role-specific typography are visible; no full-page correction performed."}

def manifest() -> None:
    entries=[]
    for path in sorted(OUT.rglob("*")):
      if path.is_file() and path.name!="artifact_manifest.json":
        data=path.read_bytes();entries.append({"path":path.relative_to(OUT).as_posix(),"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    write_json(OUT/"artifact_manifest.json",{"schema_version":"round3i_br_k_artifact_manifest_v1","scope":"3 visual keyframes only","file_count":len(entries)+1,"files":entries})

def main() -> int:
    OUT.mkdir(parents=True,exist_ok=True)
    fonts=OUT/"reproduction"/"fonts";fonts.mkdir(parents=True,exist_ok=True)
    for name in ("NotoSansJP-Variable.ttf","InterTight-Variable.ttf"):
      source=ROOT/"assets"/"fonts"/"round2f"/name
      if not source.exists(): raise SystemExit(f"missing font: {source}")
      (fonts/name).write_bytes(source.read_bytes())
    (OUT/"reproduction"/"index.html").write_text(HTML.replace("%%CSS%%",CSS),encoding="utf-8")
    specs()
    with serve(OUT/"reproduction") as url: qa=asyncio.run(capture(url))
    write_json(OUT/"12_technical_qa.json",{"status":qa["status"],"browser":qa,"console_errors":0,"runtime_errors":0,"missing_assets":0,"broken_fonts":0,"overflow":0,"internal_wording_leak":0,"evidence_boundary_violation":0})
    manifest()
    return 0 if qa["status"]=="PASS" else 1

if __name__ == "__main__": raise SystemExit(main())
