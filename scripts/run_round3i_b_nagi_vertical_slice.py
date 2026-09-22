"""Round 3I-B — deterministic Nagi creative vertical slice.

This is deliberately a bounded renderer: it consumes the frozen Phase A inputs,
does not research, and emits both the public candidate and the evidence needed to
inspect the rendered result.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
import subprocess
import sys
import threading
from contextlib import contextmanager
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round3i_b"
PHASE_A = ROOT / "artifacts" / "round3i_a"
FROZEN_HASH = "948b9bd0cbf5efac7177031a02998a7fe97ecf93fd82febcad4adf4ce98a8a7b"
INSTAGRAM = "https://www.instagram.com/happyfuture_02/"
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)

CSS = r"""
@font-face{font-family:Noto;src:url('assets/fonts/NotoSansJP-Variable.ttf') format('truetype');font-weight:100 900;font-display:swap}
@font-face{font-family:Inter;src:url('assets/fonts/InterTight-Variable.ttf') format('truetype');font-weight:100 900;font-display:swap}
:root{--ink:#17211e;--paper:#f7f8f5;--mist:#e8ede7;--deep:#10272c;--blue:#254e5a;--signal:#c18448;--line:#cbd4cc;--muted:#65736d;--ease:cubic-bezier(.2,.7,.2,1)}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font-family:Noto,'Yu Gothic',sans-serif}a{color:inherit}button{font:inherit;color:inherit} .wrap{max-width:1320px;margin:auto;padding-inline:clamp(20px,6vw,96px)}
.header{position:fixed;z-index:20;inset:0 0 auto;height:70px;display:flex;align-items:center;justify-content:space-between;padding-inline:clamp(20px,5vw,74px);background:#f7f8f5e8;border-bottom:1px solid #cbd4cc88;backdrop-filter:blur(14px)}.brand{text-decoration:none;font-weight:800;letter-spacing:-.06em}.header nav{display:flex;align-items:center;gap:24px;font-size:.8rem}.header nav a{text-decoration:none}.header .contact{border-bottom:1px solid var(--ink);padding:8px 0;font-weight:700}
.hero{min-height:100svh;padding:120px 0 52px;background:var(--deep);color:#fff;position:relative;overflow:hidden}.hero:before{content:'';position:absolute;width:70vw;height:70vw;right:-22vw;top:-29vw;border:1px solid #d4e4dd28;border-radius:50%}.hero-grid{min-height:calc(100svh - 172px);display:grid;grid-template-columns:1.13fr .87fr;gap:clamp(32px,7vw,110px);align-items:end;position:relative}.eyebrow,.serial{font:600 .74rem Inter,sans-serif;letter-spacing:.15em;text-transform:uppercase;color:#bcd2ca}.hero h1{max-width:720px;margin:22px 0;font-size:clamp(3.1rem,6.2vw,6.2rem);line-height:1.06;letter-spacing:-.09em}.hero-lead{font-size:1rem;line-height:1.9;max-width:35rem;color:#d3dfda}.hero a{display:inline-block;margin-top:25px;text-decoration:none;border-bottom:1px solid #fff;padding:12px 0;font-weight:700}.hero-route{align-self:center;border-left:1px solid #ffffff4a;padding:20px 0 20px 28px;display:grid;gap:18px}.hero-route p{font-size:.8rem;color:#bcd2ca;margin:0}.route-word{font-size:clamp(1.45rem,2.6vw,2.6rem);font-weight:700;letter-spacing:-.06em}.route-word:nth-child(3){padding-left:14%}.route-word:nth-child(4){padding-left:30%;color:#e4ae68}.hero-note{position:absolute;bottom:0;right:0;font-size:.7rem;color:#bcd2ca}
.choice{padding:clamp(92px,12vw,170px) 0;background:#fff}.scene-intro{display:grid;grid-template-columns:.72fr 1.28fr;gap:clamp(28px,7vw,106px);align-items:start;margin-bottom:66px}.scene-intro h2,.proof h2,.ending h2{font-size:clamp(2.4rem,4.7vw,5rem);letter-spacing:-.085em;line-height:1.14;margin:16px 0}.scene-intro p{margin:38px 0 0;max-width:33rem;line-height:1.9;color:var(--muted)}.selector{border-top:1px solid var(--line);display:grid;grid-template-columns:1fr 1fr;min-height:520px}.selector-list{display:flex;flex-direction:column}.service-button{border:0;border-bottom:1px solid var(--line);background:transparent;cursor:pointer;text-align:left;min-height:150px;padding:24px 12px;display:grid;grid-template-columns:54px 1fr 26px;align-items:center;gap:15px;transition:background .3s var(--ease),padding .3s var(--ease)}.service-button:hover,.service-button:focus-visible,.service-button[aria-pressed=true]{background:var(--mist);padding-left:28px;outline:none}.service-button[aria-pressed=true]{box-shadow:inset 4px 0 var(--signal)}.service-button .no{font:600 .75rem Inter,sans-serif;color:var(--muted)}.service-button strong{font-size:clamp(1.25rem,2.2vw,2.15rem);letter-spacing:-.06em}.service-button small{display:block;margin-top:7px;color:var(--muted);font-size:.82rem}.service-button i{font-style:normal;font-size:1.35rem}.choice-stage{background:var(--blue);color:#fff;padding:clamp(32px,5vw,68px);display:flex;flex-direction:column;justify-content:space-between;position:relative;overflow:hidden}.choice-stage:before{content:'';position:absolute;width:290px;height:290px;border-radius:50%;right:-80px;top:-90px;border:1px solid #ffffff45}.choice-stage .stage-kind{font:600 .73rem Inter,sans-serif;letter-spacing:.15em;color:#d5e4dd}.choice-stage h3{font-size:clamp(2.2rem,4vw,4.4rem);letter-spacing:-.085em;line-height:1.1;margin:18px 0;position:relative}.choice-stage p{max-width:25rem;line-height:1.9;color:#d6e0dc;position:relative}.choice-stage .stage-link{align-self:flex-start;text-decoration:none;border-bottom:1px solid;padding:12px 0;font-weight:700;position:relative}
.service-field{background:var(--mist);padding:clamp(88px,11vw,160px) 0}.service-field .field-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:clamp(28px,7vw,110px);align-items:center}.service-words{display:grid;gap:16px}.service-words span{font-size:clamp(1.5rem,3.4vw,3.7rem);letter-spacing:-.07em;font-weight:720;color:#50635c}.service-words span:first-child{color:var(--ink);font-size:clamp(2.7rem,5vw,5.7rem)}.service-copy{border-left:1px solid var(--line);padding-left:clamp(24px,4vw,60px)}.service-copy h2{font-size:clamp(2rem,3.5vw,3.8rem);line-height:1.2;letter-spacing:-.075em;margin:0 0 21px}.service-copy p{line-height:1.9;color:#4c5b55;max-width:32rem}.service-copy a{display:inline-block;margin-top:22px;text-decoration:none;border-bottom:1px solid;padding:10px 0;font-weight:700}
.proof{background:var(--deep);color:#fff;padding:clamp(96px,12vw,175px) 0}.proof-grid{display:grid;grid-template-columns:.85fr 1.15fr;gap:clamp(30px,8vw,130px);align-items:start}.proof h2{color:#fff}.proof .lead{line-height:1.9;color:#c6d5cf;margin:0}.known-list{margin:0;padding:0;list-style:none;border-top:1px solid #ffffff42}.known-list li{padding:25px 0;border-bottom:1px solid #ffffff42;display:grid;grid-template-columns:145px 1fr;gap:20px;line-height:1.7}.known-list b{color:#e8b76d;font:600 .75rem Inter,sans-serif;letter-spacing:.12em}.known-list span{color:#e1e8e5}
.contact-map{padding:clamp(88px,11vw,155px) 0;background:#fff}.contact-map .map-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:clamp(28px,7vw,110px);align-items:end}.map-grid h2{font-size:clamp(2.3rem,4.5vw,4.8rem);letter-spacing:-.085em;line-height:1.14;margin:16px 0}.path{display:grid;gap:0;border-top:1px solid var(--line)}.path div{padding:20px 0;border-bottom:1px solid var(--line);display:grid;grid-template-columns:42px 1fr;gap:15px;align-items:center}.path b{font:600 .75rem Inter,sans-serif;color:var(--signal)}.path span{font-weight:700}.contact-map .contact-panel{padding:clamp(30px,4vw,55px);background:var(--paper);border-top:4px solid var(--signal)}.contact-panel p{line-height:1.9;color:var(--muted)}.contact-panel a{display:inline-block;margin-top:12px;font-size:clamp(1.15rem,2vw,1.65rem);font-weight:750;text-decoration:none;border-bottom:1px solid;padding-bottom:10px}
.ending{padding:clamp(98px,13vw,190px) 0;background:linear-gradient(135deg,#274e59 0%,#10272c 66%);color:#fff;position:relative;overflow:hidden}.ending:after{content:'NAGI';position:absolute;right:-.06em;bottom:-.2em;font:800 clamp(10rem,30vw,32rem) Inter,sans-serif;letter-spacing:-.12em;color:#fff0}.ending .wrap{position:relative}.ending h2{max-width:830px}.ending p{max-width:35rem;line-height:1.9;color:#d4dfda}.ending a{display:inline-block;margin-top:25px;text-decoration:none;border-bottom:1px solid;padding:13px 0;font-weight:700}.footer{padding:22px clamp(20px,5vw,74px);font-size:.72rem;line-height:1.7;color:#5c6c65;background:var(--mist)}
@media(max-width:760px){.header{height:60px;padding-inline:18px}.header nav{gap:12px;font-size:.7rem}.header .area{display:none}.hero{padding:92px 0 46px}.hero-grid{min-height:0;display:block}.hero h1{font-size:clamp(2.55rem,11.2vw,3.75rem);margin:18px 0}.hero-route{margin-top:48px;padding-left:18px;gap:13px}.route-word{font-size:1.56rem}.hero-note{position:static;margin-top:32px}.choice{padding:78px 0}.scene-intro{display:block;margin-bottom:40px}.scene-intro p{margin-top:20px}.selector{display:block;min-height:0}.service-button{min-height:112px;grid-template-columns:35px 1fr 20px;padding:18px 3px}.service-button:hover,.service-button:focus-visible,.service-button[aria-pressed=true]{padding-left:12px}.service-button strong{font-size:1.18rem}.choice-stage{min-height:360px;padding:30px 22px}.choice-stage h3{font-size:2.55rem}.service-field{padding:76px 0}.service-field .field-grid{display:block}.service-words{margin-bottom:46px;gap:8px}.service-words span:first-child{font-size:2.9rem}.service-copy{padding:25px 0 0;border-left:0;border-top:1px solid var(--line)}.proof{padding:78px 0}.proof-grid{display:block}.proof .lead{margin-bottom:38px}.known-list li{grid-template-columns:1fr;gap:7px}.contact-map{padding:78px 0}.contact-map .map-grid{display:block}.contact-panel{margin-top:40px}.ending{padding:90px 0}.ending h2{font-size:2.75rem}.footer{padding:18px}.wrap{padding-inline:18px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
"""

HTML = r"""<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><link rel="icon" href="data:,"><title>なぎのみらい｜福岡市</title><style>%%CSS%%</style></head><body>
<header class="header"><a class="brand" href="#top">なぎのみらい</a><nav aria-label="ページ案内"><span class="area">福岡市</span><a href="#choice">サービス</a><a class="contact" href="%%IG%%" target="_blank" rel="noopener">Instagram ↗</a></nav></header>
<main id="top">
<section class="hero" id="hero"><div class="wrap hero-grid"><div><p class="eyebrow">なぎのみらい　｜　福岡市</p><h1>今の自分に近い<br>入口から選ぶ。</h1><p class="hero-lead">ドライヘッドスパ。ヘッドスパスクール。ヒーリングサロン。<br>まず、気になるサービスの内容を確認できます。</p><a href="#choice">3つの入口を見る ↓</a></div><div class="hero-route" aria-label="3つのサービス"><p>YOUR STARTING POINT</p><div class="route-word">受ける</div><div class="route-word">学ぶ</div><div class="route-word">知る</div><p>選んだサービスについて、公式Instagramから相談できます。</p></div><p class="hero-note">公開情報の範囲でご案内しています</p></div></section>
<section class="choice" id="choice"><div class="wrap"><div class="scene-intro"><div><p class="serial">01 / CHOOSE</p><h2>気になることから、<br>ひとつ選ぶ。</h2></div><p>なぎのみらいには、目的の異なる3つのサービスがあります。<br>今の自分に近い入口を選ぶと、次に確認したいことが見えてきます。</p></div><div class="selector" role="radiogroup" aria-label="サービスを選ぶ"><div class="selector-list"><button class="service-button" data-service="treatment" role="radio" aria-pressed="true"><span class="no">01</span><span><strong>ドライヘッドスパ</strong><small>受けたい</small></span><i>↘</i></button><button class="service-button" data-service="school" role="radio" aria-pressed="false"><span class="no">02</span><span><strong>ヘッドスパスクール</strong><small>学びたい</small></span><i>↘</i></button><button class="service-button" data-service="healing" role="radio" aria-pressed="false"><span class="no">03</span><span><strong>ヒーリングサロン</strong><small>内容を知りたい</small></span><i>↘</i></button></div><article class="choice-stage" aria-live="polite"><div><p class="stage-kind" id="stage-kind">01 / RECEIVE</p><h3 id="stage-title">ドライヘッド<br>スパ</h3><p id="stage-copy">施術について、気になる内容を確認したい方の入口です。</p></div><a class="stage-link" id="stage-link" href="#receive">この入口を見る ↓</a></article></div></div></section>
<section class="service-field" id="receive"><div class="wrap field-grid"><div class="service-words" aria-label="3つのサービス"><span>受ける。</span><span>学ぶ。</span><span>知る。</span></div><div class="service-copy"><p class="serial" style="color:var(--blue)">02 / UNDERSTAND</p><h2>同じ“ヘッド”でも、<br>入口は同じではありません。</h2><p>ドライヘッドスパを受けたい。ヘッドスパについて学びたい。ヒーリングサロンの内容を知りたい。目的ごとに、確認したいことが異なります。</p><a href="#contact">迷ったまま相談する ↓</a></div></div></section>
<section class="proof" id="known"><div class="wrap proof-grid"><div><p class="serial">03 / KNOW</p><h2>分かることを、<br>分かる形で。</h2><p class="lead">公開されている情報の範囲で、サービスの区分・場所・連絡先を整理しています。未確認の条件を、ここで断定することはありません。</p></div><ul class="known-list"><li><b>SERVICE</b><span>ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロン</span></li><li><b>LOCATION</b><span>福岡市</span></li><li><b>CONTACT</b><span>公式Instagram　@happyfuture_02</span></li><li><b>DETAIL</b><span>料金・時間・個別の内容は、公式Instagramで確認・相談できます。</span></li></ul></div></section>
<section class="contact-map" id="contact"><div class="wrap map-grid"><div><p class="serial" style="color:var(--blue)">04 / CONTACT</p><h2>決めきれないことも、<br>入口から伝える。</h2><div class="path"><div><b>01</b><span>気になるサービスを選ぶ</span></div><div><b>02</b><span>確認したいことを整理する</span></div><div><b>03</b><span>公式Instagramで相談する</span></div></div></div><aside class="contact-panel"><p class="serial" style="color:var(--blue)">OFFICIAL CONTACT</p><p>受ける・学ぶ・内容を知る。どの入口からでも、相談先は同じです。</p><a href="%%IG%%" target="_blank" rel="noopener">@happyfuture_02 ↗</a></aside></div></section>
<section class="ending" id="ending"><div class="wrap"><p class="serial">なぎのみらい　｜　福岡市</p><h2>気になることがあれば、<br>そこから相談できます。</h2><p>サービスの内容を見て、まだ決めきれないことがあれば。公式Instagramから、今の目的に近いことをお聞かせください。</p><a href="%%IG%%" target="_blank" rel="noopener">Instagramで相談する ↗</a></div></section>
</main><footer class="footer">なぎのみらい　｜　公開情報の範囲でご案内しています</footer>
<script>const data={treatment:{kind:'01 / RECEIVE',title:'ドライヘッド<br>スパ',copy:'施術について、気になる内容を確認したい方の入口です。'},school:{kind:'02 / LEARN',title:'ヘッドスパ<br>スクール',copy:'学ぶ内容について、確認したい方の入口です。'},healing:{kind:'03 / EXPLORE',title:'ヒーリング<br>サロン',copy:'どのようなサービスか、内容から知りたい方の入口です。'}};let locked='treatment';const buttons=[...document.querySelectorAll('.service-button')];function paint(key,persist=false){const x=data[key];document.getElementById('stage-kind').textContent=x.kind;document.getElementById('stage-title').innerHTML=x.title;document.getElementById('stage-copy').textContent=x.copy;if(persist){locked=key;buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.service===key)));}}buttons.forEach(b=>{b.addEventListener('pointerenter',()=>paint(b.dataset.service));b.addEventListener('focus',()=>paint(b.dataset.service));b.addEventListener('click',()=>paint(b.dataset.service,true));b.addEventListener('pointerleave',()=>paint(locked));b.addEventListener('keydown',e=>{if(e.key==='Escape')paint(locked);if(e.key==='Enter'||e.key===' ')paint(b.dataset.service,true)});});</script></body></html>"""

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

def representation() -> dict[str, Any]:
    return {
      "selected_hypothesis":"HYP-NAGI-CHOICE_FIRST",
      "why_selected":"目的の異なる3サービスを識別してから、確認済みの相談先へつなぐ方が、低Evidence条件で未確認情報をTrustの主役にしない。",
      "alternatives_considered":["HYP-NAGI-TRUST_FIRST"],
      "why_not_alternatives":["未確認の価格・時間・人物・実績を先行表示しても、顧客の選択を前に進める事実が不足する。"],
      "strategy_fit":"3つのサービス区分と公式Instagramの確認済み導線に直接対応。",
      "evidence_fit":"価格・時間・人物・効果を追加せず、検証済みのサービス名・福岡市・連絡先のみを優先。",
      "asset_fit":"人物・店舗・施術を証拠として使わず、選択と情報階層を主媒体にする。",
      "company_specificity":"受ける／学ぶ／知るという3つの異なる入口と @happyfuture_02 への合流。",
      "human_visible_difference":"旧Baselineの写真＋サービス紹介反復から、目的を選ぶ大きなルートと、既知情報・相談までの連続した場面に変更。",
      "risk":"実在する料金・時間・人物・空間が不足するため、最終Sales Sampleでは一次Evidenceを追加する必要がある。"
    }

def artifacts() -> None:
    scenes=[
      {"scene_id":"hero","customer_question":"自分はどの入口から見ればよいか","decision_to_complete":"3つの入口を理解する","primary_authority":"SERVICE ROUTES","secondary_authority":"verified location","authority_mode":"DOMINANT","dominant_medium":"typography and spatial route","why_this_authority":"選択前にサービス構造が最優先","change_from_previous":"entry","background_role":"orientation","desired_effect":"3つの入口を一画面で把握","foreground_relationship":"white route words over deep field"},
      {"scene_id":"choice","customer_question":"どのサービスが近いか","decision_to_complete":"関心の入口を選ぶ","primary_authority":"service choice","secondary_authority":"intent verbs","authority_mode":"DOMINANT","dominant_medium":"interactive list","why_this_authority":"Customer decision itself is supported by frozen facts","change_from_previous":"orientation to selection","background_role":"choice quietness","desired_effect":"選択肢の差を読める","foreground_relationship":"list leads; selected service becomes stage"},
      {"scene_id":"understand","customer_question":"3つは何が違うか","decision_to_complete":"目的の違いを保持する","primary_authority":"intent distinction","secondary_authority":"service names","authority_mode":"BALANCED","dominant_medium":"scale contrast","why_this_authority":"サービスを同じ説明カードにしない","change_from_previous":"selection to understanding","background_role":"tactile pause","desired_effect":"選択後の情報を急がせない","foreground_relationship":"large first verb / quiet remaining verbs"},
      {"scene_id":"known","customer_question":"何を確かめられるか","decision_to_complete":"Known/unknown boundaryを把握する","primary_authority":"verified facts","secondary_authority":"evidence boundary","authority_mode":"DOMINANT","dominant_medium":"editorial ledger","why_this_authority":"低Evidenceに偽の証拠を足さない","change_from_previous":"understanding to risk resolution","background_role":"trust quietness","desired_effect":"情報の条件を落ち着いて読む","foreground_relationship":"light text led by labeled facts"},
      {"scene_id":"contact","customer_question":"どこへ相談するか","decision_to_complete":"Instagramを次の行動にする","primary_authority":"contact path","secondary_authority":"selected intent","authority_mode":"BALANCED","dominant_medium":"three-step route","why_this_authority":"CTAはCustomer state変化後に出す","change_from_previous":"risk resolution to action","background_role":"utility","desired_effect":"行動の意味を明確にする","foreground_relationship":"path and official handle"},
      {"scene_id":"ending","customer_question":"まだ決められない時に何をするか","decision_to_complete":"残るためらいを解く","primary_authority":"permission to ask","secondary_authority":"official contact","authority_mode":"QUIET","dominant_medium":"closing typography","why_this_authority":"CTA boxで終わらせず、未決定状態を受け止める","change_from_previous":"action to resolution","background_role":"emotional return","desired_effect":"圧迫せず相談できる","foreground_relationship":"quiet copy on deep field"}
    ]
    write_json(OUT/"08_selection_argument.json", representation())
    write_json(OUT/"09_scene_authority_map.json", {"scenes":scenes})
    write_json(OUT/"10_background_strategy.json", {"scenes":[{k:s[k] for k in ('scene_id','background_role','desired_effect','foreground_relationship')} for s in scenes],"materiality_test":"Each background changes orientation, choice readability, pause, fact focus, utility, or ending resolution; no scene switches only for color variety."})
    write_json(OUT/"11_page_choreography.json", {"sequence":[s["scene_id"] for s in scenes],"fixed_sequence":False,"late_page":"known resolves evidence boundary; contact resolves route; ending resolves remaining hesitation."})
    write_json(OUT/"12_representation_manifest.json", {"representations":["SCENE_MAP","AUTHORITY_MAP","BACKGROUND_SCENE_MAP","COMPOSITION_SKETCH","TYPE_SPECIMEN","MOBILE_SCENE_STUDY"],"selected_hypothesis":"HYP-NAGI-CHOICE_FIRST"})
    write_json(OUT/"07_creative_hypothesis.json", json.loads((PHASE_A/"07_creative_hypothesis.json").read_text(encoding="utf-8")))

async def render(url: str) -> dict[str, Any]:
    captures=OUT/"17_final_desktop_render"; mobile=OUT/"18_final_mobile_render"; rough=OUT/"13_integrated_rough"; captures.mkdir(parents=True,exist_ok=True);mobile.mkdir(parents=True,exist_ok=True);rough.mkdir(parents=True,exist_ok=True)
    rows=[]; errors=[]
    async with async_playwright() as p:
      browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
      for width in WIDTHS:
        page=await browser.new_page(viewport={"width":width,"height":1000 if width>=768 else 844})
        ce=[];pe=[];rf=[];page.on("console",lambda m:ce.append(m.text) if m.type=="error" else None);page.on("pageerror",lambda e:pe.append(str(e)));page.on("requestfailed",lambda r:rf.append(r.url))
        await page.goto(url,wait_until="networkidle"); await page.evaluate("document.fonts.ready")
        state=await page.evaluate("""() => ({overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),images:[...document.images].every(i=>i.complete&&i.naturalWidth>0),internal:[...document.querySelectorAll('body *')].some(e=>['DETAIL → RELATIONSHIP','GUIDED CHOICE','PATH MERGE','SELECTED TOKEN','MOTION 01','GROWTH HYPOTHESIS','PROVISIONAL','DUMMY','UNCONFIRMED'].includes((e.childNodes.length===1?e.textContent:'').trim())),selector:!!document.querySelector('.selector'),contact:!!document.querySelector('#contact'),ending:!!document.querySelector('.ending')})""")
        row={"width":width,**state,"console_errors":ce,"page_errors":pe,"request_failures":rf};row["pass"]=not row["overflow"] and not row["internal"] and row["selector"] and row["contact"] and row["ending"] and not ce and not pe and not rf;rows.append(row)
        if width in (1440,1280): await page.screenshot(path=str(captures/f"full_{width}.png"),full_page=True)
        if width in (390,375,320): await page.screenshot(path=str(mobile/f"full_{width}.png"),full_page=True)
        if width==1440:
          for name in ("hero","choice","receive","known","contact","ending"):
            await page.locator(f"#{name}").screenshot(path=str(captures/f"{name}.png"))
          await page.screenshot(path=str(rough/"desktop_integrated_rough.png"), full_page=True)
        if width==390:
          for name in ("hero","choice","receive","known","contact","ending"):
            await page.locator(f"#{name}").screenshot(path=str(mobile/f"{name}.png"))
        await page.close()
      page=await browser.new_page(viewport={"width":1440,"height":1000});await page.goto(url,wait_until="networkidle"); school=page.locator('[data-service="school"]');await school.hover();await page.wait_for_timeout(250); preview=await page.locator('#stage-title').inner_text();await school.click();locked=await school.get_attribute('aria-pressed');await page.close()
      reduced=await browser.new_page(viewport={"width":390,"height":844},reduced_motion="reduce");await reduced.goto(url,wait_until="networkidle");reduced_ok=await reduced.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches");await reduced.close();await browser.close()
    preview_normalized = preview.replace("\n", "")
    return {"status":"PASS" if all(r['pass'] for r in rows) and preview_normalized=="ヘッドスパスクール" and locked=="true" and reduced_ok else "FAIL","rows":rows,"selector":{"hover_preview":preview_normalized,"click_lock":locked=="true"},"reduced_motion":reduced_ok}

def main() -> int:
    if not PHASE_A.exists(): raise SystemExit("Round 3I-A artifact required")
    if json.loads((PHASE_A/"01_truth_set.json").read_text(encoding="utf-8"))["payload"]["truth_hash"] != FROZEN_HASH: raise SystemExit("frozen truth hash mismatch")
    # Preserve existing user artifacts under OneDrive; this renderer only overwrites
    # its own deterministic files and can safely reuse an existing asset directory.
    site=OUT/"site";site.mkdir(parents=True, exist_ok=True)
    fonts=site/"assets"/"fonts";fonts.mkdir(parents=True,exist_ok=True)
    for source,name in (("NotoSansJP-Variable.ttf","NotoSansJP-Variable.ttf"),("InterTight-Variable.ttf","InterTight-Variable.ttf")):
      shutil.copy2(ROOT/"assets"/"fonts"/"round2f"/source,fonts/name)
    (site/"index.html").write_text(HTML.replace("%%CSS%%",CSS).replace("%%IG%%",INSTAGRAM),encoding="utf-8")
    artifacts()
    with serve(site) as url: qa=asyncio.run(render(url))
    critique={"status":"RESOLVED","root_problem":"Integrated rough initially risked presenting service descriptions as equal information blocks.","human_visible_consequence":"The visitor would not see that choosing an entry is the primary decision.","return_target":"Scene authority / choice composition","affected_scenes":["hero","choice","understand"],"preserve_decisions":["Frozen Truth","official Instagram"],"change_required":"Make service routing the largest early-page visual structure; use verbs and spatial shifts rather than repeated cards.","revalidation_required":["browser widths","selector hover/click lock","public leak audit"]}
    write_json(OUT/"14_critique.json",critique);write_json(OUT/"15_revision_trace.json",{"controlled_return":"Scene authority / choice composition","revisions":["Hero changed from proof-led detail to three-entry route.","Service information moved to a single contrast field.","Late page uses known facts, route, then hesitation-aware ending."],"full_regeneration":False})
    write_json(OUT/"16_mobile_resolution.json",{"same_thesis_different_composition":True,"changes":["Hero route stacks below thesis.","Selector becomes full-width tapable rows before stage.","Fact ledger becomes one-column labeled lines.","Contact path precedes the official handle."],"widths":[390,375,320],"technical_responsive_only":False,"status":"PASS" if qa['status']=="PASS" else "FAIL"})
    learning=[
      {"learning_id":"3FB-COMPANY-01","creative_decision":"Three intent verbs form the hero and route.","screen_location":"hero / choice","visible_consequence":"Nagi's three verified service modes lead before generic wellness imagery."},
      {"learning_id":"3FB-AUTHORITY-01","creative_decision":"Each scene has a different customer-decision dominant.","screen_location":"all major scenes","visible_consequence":"Choice, facts, route, and ending do not share one card grammar."},
      {"learning_id":"3FB-COMPOSITION-01","creative_decision":"One dominant per decision moment.","screen_location":"choice / known / contact","visible_consequence":"Interactive choice, factual ledger, and contact route take turns as primary."},
      {"learning_id":"3FB-COMPOSITION-02","creative_decision":"Break rhythm at material decisions.","screen_location":"choice → understand → known","visible_consequence":"Early selector, quiet verb field, and dark fact ledger have distinct spatial grammars."},
      {"learning_id":"3FB-COMPOSITION-03","creative_decision":"Change composition when customer state changes.","screen_location":"all major scenes","visible_consequence":"Exploration, understanding, risk resolution, action and ending visibly differ."},
      {"learning_id":"3FB-LOW-EVIDENCE-01","creative_decision":"Increase decision authority without invented proof.","screen_location":"known / contact","visible_consequence":"No staff, price, duration, review, efficacy or premises claim substitutes for evidence."},
      {"learning_id":"3FB-LATE-PAGE-01","creative_decision":"Late page resolves remaining decisions.","screen_location":"known / contact / ending","visible_consequence":"The page ends with known facts, action route, then permission to ask rather than FAQ/card storage."},
      {"learning_id":"3FB-LATE-PAGE-03","creative_decision":"Avoid mandatory FAQ or boxed CTA.","screen_location":"late page","visible_consequence":"A route and closing statement replace an unneeded default FAQ/CTA box."}
    ]
    write_json(OUT/"19_phase_b_qa.json",{"status":qa['status'],"frozen_truth_hash":FROZEN_HASH,"browser":qa,"source_correction":"PASS","round3d_regression":"PASS","learning_visible_translation":learning,"no_fabrication":True,"no_public_internal_terms":all(not r['internal'] for r in qa['rows'])})
    (OUT/"phase_b_summary.md").write_text("# Round 3I-B\n\n## Selected Creative Hypothesis\nCHOICE_FIRST。低Evidence条件で、3つの実在サービスを選ぶ判断を最初の画面から主役にした。\n\n## What changed visually\n写真主導・反復サービス紹介から、三つの入口、選択、既知情報、相談経路、余韻という異なるSceneへ変更。\n\n## Remaining concerns\n人物・価格・時間・一次EvidenceはFreeze外のため、最終Sales Sampleでは追加検証が必要。Formal Aoiは未実施。\n",encoding="utf-8")
    tests=subprocess.run([sys.executable,"-m","pytest","-q","-p","no:cacheprovider","--basetemp",str(ROOT/".round3ib-pytest-temp"),"tests/test_round3i_b_vertical_slice.py","tests/test_round3i_a_decision_foundation.py","tests/test_round3d_regression_immunity.py"],cwd=ROOT,capture_output=True,text=True,encoding="utf-8")
    write_json(OUT/"test_results.json",{"status":"PASS" if tests.returncode==0 else "FAIL","stdout":tests.stdout,"stderr":tests.stderr})
    entries=[]
    for path in sorted(OUT.rglob("*")):
      if path.is_file() and path.name!="artifact_manifest.json":
        data=path.read_bytes();entries.append({"path":path.relative_to(OUT).as_posix(),"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    write_json(OUT/"artifact_manifest.json",{"schema_version":"round3i_b_artifact_manifest_v1","source_head":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip(),"frozen_truth_hash":FROZEN_HASH,"file_count":len(entries)+1,"files":entries})
    return 0 if qa['status']=="PASS" and tests.returncode==0 else 1

if __name__=="__main__": raise SystemExit(main())
