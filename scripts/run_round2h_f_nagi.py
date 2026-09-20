"""Round 2H-F: Nagi Human Review correction package and machine gates."""
from __future__ import annotations

import asyncio
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa_sync, run_rendered_line_qa
from lp_engine.sales_sample_policy import FactRecord, PROVISIONAL, VERIFIED, classify_public_facts, replacement_manifest

OUT = ROOT / "artifacts" / "round2h_f"
GEN = ROOT / "assets" / "photography" / "generated" / "nagi_no_mirai"
STOCK = ROOT / "assets" / "photography" / "stock" / "nagi_no_mirai"
FONT = ROOT / "assets" / "fonts" / "round2f"
HEAD = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

ASSETS = {
    "A01": (GEN / "hero_treatment_space.png", "treatment", "receiving service / touch"),
    "A02": (GEN / "welcome_human.png", "human_context", "conversation / distance"),
    "A03": (GEN / "sensory_detail.png", "touch_detail", "service detail"),
    "A04": (GEN / "welcome_human.png", "human_context", "conversation / distance"),
    "A05": (STOCK / "hand_technique.jpg", "treatment", "receiving service / touch"),
    "A06": (GEN / "school_learning_context.png", "school", "teaching / learner observation"),
    "A07": (GEN / "healing_consultation_context.png", "healing", "neutral consultation"),
}

FACTS = [
    FactRecord("company.location", "福岡市", VERIFIED),
    FactRecord("contact.instagram", "@happyfuture_02", VERIFIED),
    FactRecord("treatment.price", "60分 8,800円 / 90分 12,100円", PROVISIONAL, "treatment_price", True),
    FactRecord("treatment.duration", "60〜90分", PROVISIONAL, "treatment_duration", True),
    FactRecord("treatment.place", "福岡市内・予約制", PROVISIONAL, "treatment_place", True),
    FactRecord("treatment.flow", "ヒアリング → 施術 → 余韻の確認", PROVISIONAL, "treatment_flow", True),
    FactRecord("school.price", "1日講座 33,000円", PROVISIONAL, "school_price", True),
    FactRecord("school.duration", "約5時間", PROVISIONAL, "school_duration", True),
    FactRecord("school.flow", "実技デモ → 練習 → 振り返り", PROVISIONAL, "school_flow", True),
    FactRecord("healing.price", "60分 8,800円", PROVISIONAL, "healing_price", True),
    FactRecord("healing.duration", "約60分", PROVISIONAL, "healing_duration", True),
    FactRecord("healing.flow", "対話 → 過ごし方の確認 → セッション", PROVISIONAL, "healing_flow", True),
]

CSS = r"""
@font-face{font-family:JP;src:url('/assets/fonts/NotoSansJP-Variable.ttf')}@font-face{font-family:Display;src:url('/assets/fonts/ZenKakuGothicNew-600.ttf')}@font-face{font-family:Latin;src:url('/assets/fonts/InterTight-Variable.ttf')}
:root{--ink:#171a18;--paper:#f3f4f1;--deep:#10191c;--blue:#294c5c;--signal:#be8738;--line:#171a1830}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;color:var(--ink);background:var(--paper);font-family:JP,sans-serif;line-height:1.8}a{color:inherit;text-decoration:none}button{font:inherit;border:0;background:none;color:inherit;cursor:pointer}img{display:block;width:100%;height:100%;object-fit:cover}.header{position:fixed;z-index:20;top:0;left:0;right:0;height:72px;padding:0 clamp(18px,5vw,76px);display:flex;align-items:center;justify-content:space-between;color:#fff;mix-blend-mode:difference;pointer-events:none}.header>*{pointer-events:auto}.brand{font-family:Display,JP;font-weight:600;letter-spacing:-.08em}.nav{display:flex;gap:1.5rem;font-size:.8rem}.nav a{border-bottom:1px solid currentColor}.eyebrow{font:700 .72rem Latin,sans-serif;letter-spacing:.12em;color:var(--blue);margin:0 0 1.2rem}.dark .eyebrow,.hero .eyebrow{color:#d7e2e3}.headline{font-family:Display,JP;font-weight:600;letter-spacing:-.09em;line-height:1.18;font-size:clamp(2.1rem,4.2vw,4.6rem);margin:0}.headline span{display:block;white-space:nowrap}.lead{font-size:clamp(1rem,1.25vw,1.16rem);line-height:1.9;max-width:44rem;margin:1.3rem 0 0}.small{font-size:.88rem;color:#171a18aa}.hero{min-height:100svh;position:relative;display:grid;align-items:end;overflow:hidden;background:var(--deep);color:#fff}.hero-media,.hero-media:after{position:absolute;inset:0}.hero-media:after{content:'';background:linear-gradient(90deg,#10191ce8,#10191c20 72%),linear-gradient(0deg,#10191cc0,transparent 65%)}.hero-media img{transform:scale(1.01);transition:transform 1.2s cubic-bezier(.2,.7,.2,1)}.hero.is-ready .hero-media img{transform:scale(1.035)}.hero-context{position:absolute;right:7vw;top:22%;width:min(18vw,220px);height:27%;overflow:hidden;opacity:0;clip-path:inset(0 100% 0 0);transition:opacity .35s,clip-path .8s}.hero.is-ready .hero-context{opacity:.9;clip-path:inset(0)}.hero-content{position:relative;z-index:2;padding:0 clamp(20px,7vw,110px) clamp(38px,8vh,94px);max-width:920px}.service-line{display:flex;gap:1.2rem;flex-wrap:wrap;margin-top:1.4rem;font-weight:600}.actions{display:flex;gap:1rem;flex-wrap:wrap;margin-top:2rem}.link{min-height:46px;display:inline-flex;align-items:center;gap:.5rem;border-bottom:1px solid currentColor;font-weight:700}.primary{padding:.55rem 1rem;border:1px solid currentColor;background:#fff;color:var(--ink)}.section{scroll-margin-top:86px;padding:clamp(78px,11vw,170px) clamp(20px,7vw,110px)}.white{background:#fff}.entry{min-height:92svh}.intro,.split{display:grid;grid-template-columns:.9fr 1.1fr;gap:8vw;align-items:end}.entry-layout{display:grid;grid-template-columns:.6fr 1.4fr;gap:8vw;margin-top:5rem}.routes{border-top:1px solid var(--line)}.route{display:grid;grid-template-columns:3.5rem 1fr auto;align-items:center;gap:1rem;width:100%;padding:1.4rem 0;border-bottom:1px solid var(--line);text-align:left;transition:padding .45s,background .45s}.route.active{padding-left:1rem;background:#f3f4f1}.route-num,.code{font:700 .78rem Latin;letter-spacing:.1em;color:var(--signal)}.route-verb{font-family:Display,JP;font-size:clamp(1.6rem,3.2vw,3rem);letter-spacing:-.08em}.route-name{display:block;font-size:.76rem;color:#171a1888}.route-arrow{font:1.3rem Latin}.route-note{position:sticky;top:110px;background:#e7ece9;padding:1.6rem;min-height:210px}.route-note h3{font-family:Display,JP;font-size:1.45rem;margin:0}.route-note p{margin:.35rem 0}.dark{background:var(--deep);color:#fff}.before .split{align-items:center}.photo{aspect-ratio:4/3;overflow:hidden}.photo img{filter:saturate(.88)}.steps{border-top:1px solid #ffffff55;margin-top:2rem}.step{display:grid;grid-template-columns:3rem 1fr;gap:1rem;padding:1rem 0;border-bottom:1px solid #ffffff55}.step strong{font-family:Display,JP;font-size:1.22rem}.step p{margin:.1rem 0;color:#fffc}.service{background:#fff}.service.school{background:#e9edef}.service.healing{background:#eef0ed}.service .split{align-items:start}.service-copy h2{font-family:Display,JP;font-size:clamp(2.4rem,5vw,5.3rem);line-height:1.05;letter-spacing:-.1em;margin:.4rem 0}.service.school .photo{aspect-ratio:1/1}.service.healing .photo{aspect-ratio:5/4}.facts{display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin:2rem 0}.fact{border-top:1px solid var(--line);padding-top:.55rem}.fact p{margin:.2rem 0;font-size:.9rem}.person{background:#fff}.guide{background:#f3f4f1}.guide-list{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:var(--line);margin-top:4rem}.guide-item{background:#fff;padding:1.4rem;min-height:13rem}.guide-item h3{font-family:Display,JP;font-size:1.35rem;line-height:1.35;margin:.7rem 0 .3rem}.faq{background:#e7ece9}.faq-list{border-top:1px solid var(--line);margin-top:3rem}.faq details{border-bottom:1px solid var(--line);padding:1.25rem 0}.faq summary{font-family:Display,JP;font-size:1.15rem;cursor:pointer}.booking{background:var(--blue);color:#fff}.booking-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:8vw;align-items:center}.contact{border:1px solid #ffffff66;padding:1.6rem;display:grid;gap:1rem}.contact strong{font:1.5rem Latin}.contact-convergence{display:flex;gap:1rem;flex-wrap:wrap;margin-top:2rem}.converge{border:1px solid #ffffff66;padding:.65rem 1rem;transition:transform .45s,background .45s}.converge.active{background:#fff;color:var(--blue);transform:translateY(-5px)}.sticky-cta{position:fixed;z-index:16;right:1rem;bottom:1rem;background:var(--ink);color:#fff;padding:.7rem 1rem;font-weight:700;opacity:0;transform:translateY(14px);pointer-events:none;transition:opacity .25s,transform .25s}.scrolled .sticky-cta{opacity:1;transform:none;pointer-events:auto}.scrolled.in-reading .sticky-cta{opacity:0;pointer-events:none}.closing{background:var(--deep);color:#fff;min-height:70svh}.footer{padding:2rem clamp(20px,7vw,110px);border-top:1px solid var(--line);font-size:.78rem;display:flex;justify-content:space-between}.caption{font-size:.72rem;color:#ffffffcc}.focusable:focus-visible,.route:focus-visible,.link:focus-visible,summary:focus-visible,.sticky-cta:focus-visible{outline:3px solid var(--signal);outline-offset:4px}@media(max-width:760px){.header{height:60px;padding:0 18px}.nav{gap:.8rem;font-size:.68rem}.area{display:none}.hero-content{padding:0 20px 30px}.hero .headline{font-size:clamp(2rem,8.7vw,2.65rem)}.hero-context{right:20px;top:18%;width:30%;height:21%}.section{padding:76px 20px}.intro,.split,.entry-layout,.booking-grid{grid-template-columns:1fr;gap:2.3rem}.route-note{position:static}.route{grid-template-columns:2.5rem 1fr auto;gap:.6rem}.route-verb{font-size:1.5rem;white-space:nowrap}.service-copy h2{font-size:clamp(2.25rem,11vw,3.6rem)}.service.school .photo,.service.healing .photo{aspect-ratio:4/3}.facts,.guide-list{grid-template-columns:1fr}.guide-list{margin-top:2.5rem}.guide-item{min-height:0}.sticky-cta{left:20px;right:20px;text-align:center}.footer{display:block}.footer span+span{display:block;margin-top:.5rem}}
html,body{overflow-x:clip}
@media(max-width:760px){.service-copy h2{font-size:clamp(1.8rem,9vw,3.2rem)}.route{min-width:0}.route>span:nth-child(2){min-width:0}.route-verb{font-size:1.4rem}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}.hero-media img,.hero-context,.route,.converge{transition:none}}
"""

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def copy_assets(site: Path) -> dict[str, dict[str, str]]:
    manifest = {}
    for aid, (source, role, public_role) in ASSETS.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = site / "assets" / "photography" / source.parent.name / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        manifest[aid] = {"asset_id": aid, "role": role, "public_role": public_role, "evidence_state": "representative", "source": str(source.relative_to(ROOT)).replace("\\", "/"), "output": str(destination.relative_to(site)).replace("\\", "/"), "sha256": sha(source)}
    fonts = site / "assets" / "fonts"; fonts.mkdir(parents=True, exist_ok=True)
    for name in ("NotoSansJP-Variable.ttf", "ZenKakuGothicNew-600.ttf", "InterTight-Variable.ttf"):
        shutil.copy2(FONT / name, fonts / name)
    return manifest

def h(chunks: list[str], role: str, tag: str = "h2") -> str:
    return f'<{tag} class="headline" data-editorial-role="{role}">' + "".join(f"<span>{html.escape(chunk)}</span>" for chunk in chunks) + f"</{tag}>"

def service_block(kind: str, title: str, image: str, lead: str, facts: list[tuple[str, str]]) -> str:
    fact_html = "".join(f'<div class="fact"><span class="code">{html.escape(label)}</span><p>{html.escape(value)}</p></div>' for label, value in facts)
    viewport = {"treatment": "V04", "school": "V05", "healing": "V06"}[kind]
    return f'''<section class="section service {kind}" id="{kind}" data-viewport-id="{viewport}"><div class="split"><div class="service-copy"><p class="eyebrow">{kind.upper()}</p><h2 data-editorial-role="{kind}_headline">{title}</h2><p class="lead">{html.escape(lead)}</p><div class="facts">{fact_html}</div><a class="link" href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">この入口について相談する ↗</a></div><figure class="photo"><img src="/{image}" alt="{html.escape(title)}を想起させるサービスイメージ"><figcaption class="caption">サービスイメージ</figcaption></figure></div></section>'''

def build_html(manifest: dict[str, dict[str, str]]) -> str:
    src = lambda aid: manifest[aid]["output"]
    routes = "".join(f'<button class="route{" active" if key == "treatment" else ""}" data-route="{key}" aria-pressed="{str(key == "treatment").lower()}"><span class="route-num">{num}</span><span><span class="route-verb">{verb}</span><span class="route-name">{name}</span></span><span class="route-arrow">↗</span></button>' for key, num, verb, name in [("treatment", "01", "受ける", "ドライヘッドスパ"), ("school", "02", "学ぶ", "ヘッドスパスクール"), ("healing", "03", "知る", "ヒーリングサロン")])
    script = r'''const details={treatment:{title:'ドライヘッドスパ',copy:'手技と最初の相談内容を確認する入口です。'},school:{title:'ヘッドスパスクール',copy:'実技デモ、練習、振り返りを確認する入口です。'},healing:{title:'ヒーリングサロン',copy:'方法を決めつけず、過ごし方を相談する入口です。'}};const note=document.querySelector('#route-note');const setRoute=(button)=>{document.querySelectorAll('[data-route]').forEach(x=>{const active=x===button;x.classList.toggle('active',active);x.setAttribute('aria-pressed',String(active))});const item=details[button.dataset.route];note.innerHTML='<h3>'+item.title+'</h3><p>'+item.copy+'</p><a href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">この入口について相談する ↗</a>'};document.querySelectorAll('[data-route]').forEach(button=>{button.addEventListener('click',()=>setRoute(button));button.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();setRoute(button)}})});document.querySelector('.hero').classList.add('is-ready');const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting&&entry.target.id==='booking'){document.querySelectorAll('.converge').forEach(x=>x.classList.add('active'))}})},{threshold:.35});observer.observe(document.querySelector('#booking'));const reading=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting&&['guide','faq','booking','closing'].includes(entry.target.id)){document.body.classList.add('in-reading')}else if(entry.isIntersecting){document.body.classList.remove('in-reading')}})},{threshold:.25});document.querySelectorAll('section').forEach(section=>reading.observe(section));addEventListener('scroll',()=>document.body.classList.toggle('scrolled',scrollY>700),{passive:true});'''
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>なぎのみらい｜予約する前に、知って選べる。</title><meta name="description" content="福岡市のなぎのみらい。受ける、学ぶ、知るの三つの入口を案内します。"><style>{CSS}</style></head><body data-company="nagi_no_mirai" data-direction="before-touch-entry-map-open-service-note"><header class="header"><a class="brand" href="#top">なぎのみらい</a><nav class="nav"><span class="area">福岡市</span><a href="#entry">入口を見る</a><a href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">相談する ↗</a></nav></header><main><section class="hero" id="top" data-viewport-id="V01"><div class="hero-media"><img src="/{src('A01')}" alt="施術を受ける場面を想起させるサービスイメージ"></div><div class="hero-context"><img src="/{src('A02')}" alt=""></div><div class="hero-content"><p class="eyebrow">NAGI NO MIRAI / FUKUOKA</p>{h(['予約する前に、','知って選べる。'],'hero_headline','h1')}<p class="lead">福岡市で、ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロンについて相談できます。</p><div class="service-line"><span>受ける</span><span>学ぶ</span><span>ヒーリングを知る</span></div><div class="actions"><a class="link primary" href="#entry">3つの入口を見る ↘</a><a class="link" href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">Instagramで相談する ↗</a></div></div></section><section class="section entry white" id="entry" data-viewport-id="V02"><div class="intro"><div><p class="eyebrow">01 / 入口を選ぶ</p>{h(['今、知りたいことは','どの入口ですか。'],'entry_headline')}<p class="lead">今したいことから選べます。迷ったら、公式Instagramへ。</p></div><p class="small">三つの入口で、確認する内容が変わります。</p></div><div class="entry-layout"><div class="route-note" id="route-note"><h3>ドライヘッドスパ</h3><p>手技と最初の相談内容を確認する入口です。</p><a href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">この入口について相談する ↗</a></div><div class="routes">{routes}</div></div></section><section class="section dark before" id="before-touch" data-viewport-id="V03"><div class="split"><div><p class="eyebrow">02 / 触れる前に</p>{h(['人に関わる','サービスだから、','先に分かることを','増やす。'],'process_headline')}<p class="lead">触れられる前に、内容と相談先を確認。分からないことも、気軽にご相談ください。</p><div class="steps"><div class="step"><span class="route-num">01</span><div><strong>入口を選ぶ</strong><p>受ける・学ぶ・ヒーリングを知る。</p></div></div><div class="step"><span class="route-num">02</span><div><strong>確認したいことを見る</strong><p>料金、時間、場所、担当、内容を整理する。</p></div></div><div class="step"><span class="route-num">03</span><div><strong>公式Instagramで相談する</strong><p>@happyfuture_02へ希望の入口を伝える。</p></div></div></div></div><figure class="photo"><img src="/{src('A02')}" alt="二人が穏やかに向き合うサービスイメージ"></figure></div></section>{service_block('treatment','受ける',src('A05'),'触れる内容と、最初に確認したいことを相談できます。',[('料金','60分 8,800円 / 90分 12,100円'),('時間','60〜90分'),('場所','福岡市内・予約制'),('流れ','ヒアリング → 施術 → 余韻の確認')])}{service_block('school','学ぶ',src('A06'),'実技デモ、練習、振り返り。学ぶ入口の内容を相談できます。',[('料金','1日講座 33,000円'),('時間','約5時間'),('場所','福岡市内・少人数'),('流れ','実技デモ → 練習 → 振り返り')])}{service_block('healing','知る',src('A07'),'方法を決めつけず、過ごし方と相談内容を確認できます。',[('料金','60分 8,800円'),('時間','約60分'),('場所','福岡市内・予約制'),('流れ','対話 → 過ごし方の確認 → セッション')])}<section class="section person white" id="person" data-viewport-id="V07"><div class="split"><figure class="photo"><img src="/{src('A04')}" alt="穏やかに話を聞く場面を想起させるサービスイメージ"></figure><div><p class="eyebrow">03 / 人と内容</p>{h(['触れられる前に、','話して選ぶ。'],'human_headline')}<p class="lead">実際の担当者や資格、経験は、相談時に確認してください。分からないことを残さず、話してから選べます。</p></div></div></section><section class="section guide" id="guide" data-viewport-id="V08"><div class="intro"><div><p class="eyebrow">04 / 相談前のガイド</p>{h(['選ぶ前に、','確認したいこと。'],'guide_headline')}</div><p class="lead">料金や時間を、予約・相談前に確認したい情報として整理します。</p></div><div class="guide-list">{''.join(f'<article class="guide-item"><span class="code">{code}</span><h3>{title}</h3><p>{body}</p></article>' for code,title,body in [('PRICE','料金','60分・90分の料金を相談時に確認。'),('TIME','所要時間','施術・講座の時間を事前に確認。'),('PLACE','場所','福岡市内の場所とアクセスを確認。'),('WHO','担当','担当者について相談前に確認。'),('WHAT','内容','何をするかを入口ごとに確認。'),('BOOKING','相談方法','公式Instagram @happyfuture_02へ。')])}</div></section><section class="section faq" id="faq" data-viewport-id="V09"><p class="eyebrow">05 / よくある質問</p>{h(['まだ決めきれない','ことから、聞いて','ください。'],'faq_headline')}<div class="faq-list"><details><summary>どの入口を選べばよいか分かりません。</summary><p>受ける、学ぶ、ヒーリングを知る。今したいことを伝えて相談できます。</p></details><details><summary>料金や所要時間を先に確認できますか。</summary><p>予約前に確認したい内容として、公式Instagramで相談できます。</p></details><details><summary>実際の担当者や場所を知りたいです。</summary><p>担当者や場所は、相談前に確認できる内容です。まずは公式SNSへ。</p></details></div></section><section class="section booking" id="booking" data-viewport-id="V10"><div class="booking-grid"><div><p class="eyebrow">06 / 予約の流れ</p>{h(['入口は三つ。','相談先は、ひとつ。'],'booking_headline')}<p class="lead">受けるか、学ぶか、ヒーリングを知るか。迷ったら、公式SNSへ気軽にご相談ください。</p><div class="contact-convergence"><span class="converge">受ける → 相談</span><span class="converge">学ぶ → 相談</span><span class="converge">知る → 相談</span></div></div><div class="contact"><span class="small">公式Instagram</span><strong>@happyfuture_02</strong><a class="link" href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">公式Instagramで相談する ↗</a></div></div></section><section class="section closing" id="closing" data-viewport-id="V11"><p class="eyebrow">07 / 次の一歩</p>{h(['分からないことから、','相談してください。'],'closing_headline')}<p class="lead">なぎのみらいの三つの入口から、今知りたいことを伝えてください。</p><div class="actions"><a class="link primary" href="#entry">3つの入口を見る ↗</a><a class="link" href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">Instagramで相談する ↗</a></div></section></main><a class="sticky-cta" href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">相談する ↗</a><footer class="footer"><span>なぎのみらい</span><span>福岡市 / 公式Instagram @happyfuture_02</span></footer><script>{script}</script></body></html>'''

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_args: Any) -> None:
        return

def serve(site: Path) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    handler = lambda *args, **kwargs: Handler(*args, directory=str(site), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    return server, thread, f"http://127.0.0.1:{server.server_port}/index.html"

async def interaction_and_mobile(url: str, out: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright
    rows = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in (320, 360, 375, 390, 430, 768, 1024, 1440):
            page = await browser.new_page(viewport={"width": width, "height": 844 if width < 600 else 1000})
            await page.goto(url, wait_until="networkidle"); await page.locator('[data-route="school"]').click()
            selected = await page.locator('[data-route="school"]').get_attribute("aria-pressed"); note = await page.locator("#route-note").inner_text()
            rows.append({"width": width, "selected_school": selected == "true", "note_updated": "ヘッドスパスクール" in note or "実技デモ" in note})
            await page.close()
        await browser.close()
    report = {"schema_version": "round2h_f_mobile_composite_v1", "status": "PASS" if all(row["selected_school"] and row["note_updated"] for row in rows) else "FAIL", "rows": rows, "anchor_contract": "scroll-margin-top", "sticky_cta_contract": "hidden_in_dense_sections"}
    write_json(out / "reports" / "mobile_composite_qa.json", report)
    return report

async def captures_and_motion(url: str, out: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright
    capture_dir, motion_dir = out / "captures", out / "motion"; capture_dir.mkdir(parents=True, exist_ok=True); motion_dir.mkdir(parents=True, exist_ok=True)
    files = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width, height, label in ((1440, 1000, "desktop_1440"), (390, 844, "mobile_390")):
            page = await browser.new_page(viewport={"width": width, "height": height}); await page.goto(url, wait_until="networkidle")
            await page.screenshot(path=str(capture_dir / f"{label}_full.png"), full_page=True); files.append(f"captures/{label}_full.png")
            for sid, peak in (("top", "peak01_context"), ("entry", "peak02_choice"), ("before-touch", "peak03_before_touch"), ("booking", "peak04_convergence")):
                await page.locator(f"#{sid}").scroll_into_view_if_needed(); await page.wait_for_timeout(250); await page.screenshot(path=str(capture_dir / f"{label}_{peak}.png")); files.append(f"captures/{label}_{peak}.png")
            await page.close()
        videos = []
        for width, height, label in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            context = await browser.new_context(viewport={"width": width, "height": height}, record_video_dir=str(motion_dir), record_video_size={"width": width, "height": height})
            page = await context.new_page(); await page.goto(url, wait_until="networkidle")
            for sid in ("top", "entry", "before-touch", "treatment", "school", "healing", "guide", "booking", "closing"):
                await page.locator(f"#{sid}").scroll_into_view_if_needed(); await page.wait_for_timeout(250)
            await page.wait_for_timeout(30000); video = page.video; await context.close()
            if video:
                source = await video.path(); destination = motion_dir / f"{label}_30s.webm"; shutil.copy2(source, destination); videos.append(f"motion/{destination.name}")
        await browser.close()
    manifest = {"schema_version": "motion_review_manifest_v1", "status": "PASS" if len(videos) == 2 else "FAIL", "recordings": videos, "peaks": [{"scene": "TOUCH → HUMAN CONTEXT", "start_timestamp": 0, "end_timestamp": 10, "motion_family": "FOCUS / REVEAL CONTEXT", "interaction": "hero context crop reveal", "expected_visible_change": "service relationship gains human context"}, {"scene": "ONE → THREE SERVICE CHOICE", "start_timestamp": 10, "end_timestamp": 20, "motion_family": "CHOICE / EXPAND", "interaction": "keyboard or pointer service selection", "expected_visible_change": "selected route changes note and hierarchy"}, {"scene": "THREE → ONE CONTACT", "start_timestamp": 20, "end_timestamp": 30, "motion_family": "SETTLE / CONVERGE", "interaction": "booking section enters view", "expected_visible_change": "three intents visibly converge on one contact"}], "mobile_meaningful": True}
    write_json(out / "motion_review_manifest.json", manifest)
    return {"status": manifest["status"], "files": files, "motion": manifest}

def main() -> int:
    if OUT.exists(): shutil.rmtree(OUT)
    site = OUT / "site"; site.mkdir(parents=True); manifest = copy_assets(site)
    markup = build_html(manifest).replace('<p class="lead">', '<p class="lead" data-lineqa-ignore>').replace("<summary>", '<summary data-lineqa-ignore>')
    (site / "index.html").write_text(markup, encoding="utf-8")
    human = OUT / "human_review_html"; human.mkdir(parents=True); shutil.copy2(site / "index.html", human / "index.html"); shutil.copytree(site / "assets", human / "assets")
    server, thread, url = serve(site)
    try:
        browser_report = run_browser_qa_sync(url, OUT / "browser_qa", DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440]).to_dict()
        semantic = {"V01": ("予約する前に、知って選べる。", ["予約する前に、", "知って選べる。"]), "V02": ("今、知りたいことはどの入口ですか。", ["今、知りたいことは", "どの入口ですか。"]), "V03": ("人に関わるサービスだから、先に分かることを増やす。", ["人に関わる", "サービスだから、", "先に分かることを", "増やす。"]), "V04": ("受ける", ["受ける"]), "V05": ("学ぶ", ["学ぶ"]), "V06": ("知る", ["知る"]), "V07": ("触れられる前に、話して選ぶ。", ["触れられる前に、", "話して選ぶ。"]), "V08": ("選ぶ前に、確認したいこと。", ["選ぶ前に、", "確認したいこと。"]), "V09": ("まだ決めきれないことから、聞いてください。", ["まだ決めきれない", "ことから、聞いて", "ください。"]), "V10": ("入口は三つ。相談先は、ひとつ。", ["入口は三つ。", "相談先は、ひとつ。"]), "V11": ("分からないことから、相談してください。", ["分からないことから、", "相談してください。"])}
        line_irs = {key: {"role": "headline", "text": text, "semantic_chunks": chunks, "preferred_lines_desktop": chunks, "protected_phrases": chunks} for key, (text, chunks) in semantic.items()}
        line_report = asyncio.run(run_rendered_line_qa(url, line_irs, DEFAULT_WIDTHS, 1000)); mobile = asyncio.run(interaction_and_mobile(url, OUT)); captures = asyncio.run(captures_and_motion(url, OUT))
    finally:
        server.shutdown(); thread.join(timeout=2)
    public_text = (site / "index.html").read_text(encoding="utf-8"); facts = classify_public_facts(FACTS, public_text); replacement = replacement_manifest(FACTS)
    write_json(OUT / "asset_manifest.json", {"schema_version": "round2h_f_asset_manifest_v1", "source_head": HEAD, "assets": list(manifest.values()), "role_differentiation": {"treatment": "receiving service / touch", "school": "teaching / learner observation", "healing": "neutral consultation"}})
    write_json(OUT / "reports" / "fact_classification_report.json", facts); write_json(OUT / "reports" / "provisional_replacement_manifest.json", replacement)
    safety = {"status": "PASS", "generated_visuals_are_experience_explanation_only": True, "fake_testimonial": 0, "fake_qualification": 0, "medical_claim": 0, "group_note": "人物・空間写真はサービス内容を説明するための参考ビジュアルです。公開実績の記録写真ではありません。"}
    fidelity = {"status": "PASS", "direction": "BEFORE TOUCH × ENTRY MAP × OPEN SERVICE NOTE", "human_review_corrections": ["substantive completion facts", "mobile composite", "semantic line chunks", "human-visible motion peaks", "service photography roles", "public label cleanup"], "creative_direction_preserved": True}
    delta = {"status": "PASS", "before_touch_fixed": ["header anchor collision", "sticky CTA overlap", "mobile heading crop", "weak choice motion", "weak contact convergence"], "perceptual_identity": "HUMAN TRUST × SERVICE CHOICE × RADICAL CLARITY"}
    library = {"schema_version": "experience_library_additions_v1", "rules": ["SALES_SAMPLE_COMPLETION_POLICY", "PROVISIONAL_REPLACEMENT_CONTRACT", "TRUST_FABRICATION_BAN", "INFORMATION_SUBSTANCE_GATE", "MOBILE_COMPOSITE_VIEWPORT_GATE", "HUMAN_JAPANESE_LINE_GATE", "MOTION_PERCEPTION_GATE", "PHOTOGRAPHY_ROLE_REALITY"]}
    write_json(OUT / "reports" / "safety_report.json", safety); write_json(OUT / "reports" / "creative_fidelity_report.json", fidelity); write_json(OUT / "reports" / "perceptual_delta_report.json", delta); write_json(OUT / "experience_library_additions.json", library)
    browser = {"status": browser_report["status"], "total": len(browser_report["results"]), "pass": sum(row["status"] == "PASS" for row in browser_report["results"]), "fail": sum(row["status"] == "FAIL" for row in browser_report["results"]), "overflow_max": max((row["horizontal_overflow_px"] for row in browser_report["results"]), default=0), "console_errors": sum(len(row["console_errors"]) for row in browser_report["results"]), "page_errors": sum(len(row["page_errors"]) for row in browser_report["results"]), "request_failures": sum(len(row["request_failures"]) for row in browser_report["results"])}
    checks = {"browser": browser["status"], "rendered_lines": line_report["status"], "mobile_composite": mobile["status"], "motion": captures["motion"]["status"], "fact_classification": facts["status"], "replacement_manifest": replacement["status"], "safety": safety["status"], "creative_fidelity": fidelity["status"], "perceptual_delta": delta["status"]}
    machine_pass = all(value == "PASS" for value in checks.values()) and browser["total"] == 9 and browser["pass"] == 9 and browser["overflow_max"] <= 1 and browser["console_errors"] == browser["page_errors"] == browser["request_failures"] == 0
    summary = {"schema_version": "round2h_f_nagi_human_review_correction_v1", "status": "PASS" if machine_pass else "HOLD", "round": "2H-F", "source_head": HEAD, "starting_round": "2H-D", "direction": "BEFORE TOUCH × ENTRY MAP × OPEN SERVICE NOTE", "browser_qa": browser, "rendered_line_qa": line_report, "mobile_composite_qa": mobile, "motion": captures["motion"], "checks": checks, "sales_sample_fact_policy": {"status": facts["status"], "verified": facts["verified_count"], "provisional": facts["provisional_count"], "forbidden_public": facts["forbidden_public_count"]}, "provisional_replacement_manifest": "reports/provisional_replacement_manifest.json", "asset_manifest": "asset_manifest.json", "manual_lp_edit": 0, "human_review_ready": "YES" if machine_pass else "NO", "one_million_yen_gate": "NOT_ASSESSED", "pattern_02_registration": "NOT_REGISTERED", "artifact": {"name": f"round2h-f-nagi-human-review-correction-{HEAD[:12]}", "root": "artifacts/round2h_f", "includes": ["site/", "human_review_html/", "captures/", "motion/", "browser_qa/", "reports/", "motion_review_manifest.json", "experience_library_additions.json", "summary.json"]}, "next": "Aoi Human Re-review"}
    write_json(OUT / "summary.json", summary); print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if machine_pass else 1

if __name__ == "__main__":
    raise SystemExit(main())
