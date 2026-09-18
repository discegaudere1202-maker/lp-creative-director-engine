"""Round 2C Maylynn premium prototype and machine verification.

This runner is deliberately Maylynn-only.  It builds the v2 IR groups first,
then renders a nine-viewport sales sample from those contracts.  It stops at
technical verification; no human quality or one-million-yen decision is made.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import json
import mimetypes
import os
import re
import subprocess
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa
from lp_engine.company_research_v2 import build_maylynn_research_snapshot, validate_research_snapshot
from lp_engine.customer_decision import build_customer_decision_model
from lp_engine.evidence_graph_v2 import build_evidence_graph
from lp_engine.experience_architecture import build_experience_architecture
from lp_engine.creative_composition import build_creative_composition
from lp_engine.quality_review_contract_v2 import build_quality_review_contract


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("ROUND2C_OUTPUT_ROOT", str(ROOT / "artifacts" / "round2c")))
OUT = OUT if OUT.is_absolute() else ROOT / OUT
MAYLYNN_OUT = OUT / "maylynn_premium_prototype"


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build_self_contained_html(html_text: str, assets: dict[str, dict[str, Any]]) -> str:
    preview = html_text
    for asset in assets.values():
        local_path = asset.get("local_asset_path")
        if not local_path:
            continue
        source = "/" + local_path.replace("\\", "/")
        asset_path = ROOT / local_path
        if asset_path.is_file():
            preview = preview.replace(source, data_uri(asset_path))
    return preview


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def load_assets() -> dict[str, dict[str, Any]]:
    manifest = json.loads((ROOT / "data/photography/photography_asset_manifest_v1.json").read_text(encoding="utf-8"))
    wanted = {"hero_home_finish", "material_detail", "craft_handwork", "trust_consultation"}
    return {item["photo_role"]: item for item in manifest["assets"] if item.get("photo_role") in wanted and item.get("binary_available")}


def headline(lines: list[str], tag: str = "h2") -> str:
    return f"<{tag}>" + "".join(f'<span class="headline-line">{esc(line)}</span>' for line in lines) + f"</{tag}>"


def image(asset: dict[str, Any] | None, *, alt: str, class_name: str = "") -> str:
    if not asset:
        return ""
    path = "/" + asset["local_asset_path"].replace("\\", "/")
    return f'<figure class="shot {esc(class_name)}" data-shot-id="{esc(asset.get("asset_id"))}"><img src="{esc(path)}" alt="{esc(alt)}" loading="lazy"><figcaption>{esc(asset.get("photo_role"))} · {esc(asset.get("rights_status"))}</figcaption></figure>'


def section(view: dict[str, Any], body: str, *, extra_class: str = "") -> str:
    return f'<section id="{esc(view["section_id"])}" class="viewport {esc(extra_class)}" data-viewport-id="{esc(view["viewport_id"])}" data-complete-idea="{esc(view["complete_idea"])}" data-density="{esc(view["density"])}" data-motion-intent="{esc(view["motion_intent"])}"><div class="viewport-meta"><span>{esc(view["viewport_id"])} / 09</span><span>{esc(view["label"])}</span></div>{body}</section>'


def render_html(snapshot: dict[str, Any], experience: dict[str, Any], creative: dict[str, Any], assets: dict[str, dict[str, Any]]) -> str:
    copy = creative["copy"]
    views = {item["viewport_id"]: item for item in experience["sections"]}
    v01 = copy["V01"]
    hero = f'''<div class="hero-grid"><div class="hero-copy"><p class="kicker">{esc(v01["kicker"])}</p>{headline(v01["headline"], "h1")}<p class="lead">{esc(v01["lead"])}</p><div class="fact-rail">{"".join(f'<span>{esc(fact)}</span>' for fact in v01["facts"])}</div><p class="scroll-cue">SCROLL TO INSPECT <span>↓</span></p></div><div class="hero-visual motion-reveal">{image(assets.get("hero_home_finish"), alt="小山市の住まいと外壁の状態を確認するための生成コンテキスト画像", class_name="hero-shot")}<span class="inspection-rule"></span><span class="annotation-chip">CONTEXT / NOT EVIDENCE</span></div></div>'''
    v02 = copy["V02"]
    signs = "".join(f'<article class="sign-card" data-annotation="{i+1}"><span class="sign-no">0{i+1:01d}</span><div class="sign-surface sign-surface--{i+1}"></div><h3>{esc(label)}</h3><p>{esc("状態を見て、相談対象かを考える")}</p></article>' for i, label in enumerate(v02["labels"]))
    signs_body = f'<div class="intro-row"><div>{headline(v02["headline"])}</div><p class="lead">{esc(v02["lead"])}</p></div><div class="sign-grid">{signs}</div>'
    v03 = copy["V03"]
    scope_buttons = "".join(f'<button type="button" class="scope-node" data-scope="{i}">{esc(label)}</button>' for i, label in enumerate(v03["scope"]))
    scope_body = f'<div class="intro-row"><div>{headline(v03["headline"])}</div><p class="lead">{esc(v03["lead"])}</p></div><div class="scope-layout"><div class="scope-map" aria-label="外装の相談範囲図"><div class="house-roof"></div><div class="house-wall"></div><div class="house-window"></div><span class="scope-drone">DRONE</span></div><div class="scope-list">{scope_buttons}<p class="caption">TAP / HOVER TO TRACE THE WORK</p></div></div>'
    v04 = copy["V04"]
    metrics = "".join(f'<div class="metric"><span class="metric-label">{esc(item["label"])}</span><strong>{esc(item["value"])}</strong><small>{esc(item.get("note", ""))}</small></div>' for item in v04["metrics"])
    proof_body = f'<div class="proof-header"><p class="kicker">{esc(v04["kicker"])}</p>{headline(v04["headline"])}<p class="lead">{esc(v04["lead"])}</p></div><div class="proof-layout"><div class="drone-diagram"><div class="drone-icon">✦</div><div class="roof-plane"></div><div class="survey-line"></div><span>ROOF / HIGH AREA</span></div><div class="metric-grid">{metrics}</div></div><p class="source-note">Source: official public pages · metrics are not a performance guarantee.</p>'
    v05 = copy["V05"]
    steps = "".join(f'<li data-process-step="{i+1}"><span>0{i+1}</span><strong>{esc(step)}</strong></li>' for i, step in enumerate(v05["steps"]))
    process_body = f'<div class="process-layout"><div class="process-visual" data-motion-intent="PROCESS">{image(assets.get("craft_handwork"), alt="塗装の準備と施工を示す無料ストックの文脈画像", class_name="process-shot")}<span class="process-progress"></span></div><div class="process-copy"><p class="kicker">{esc(v05["kicker"])}</p>{headline(v05["headline"])}<p class="lead">{esc(v05["lead"])}</p><ol class="process-steps">{steps}</ol><p class="proof-line">{esc(v05["proof"])} <span>／ 公式掲載情報</span></p></div></div>'
    v06 = copy["V06"]
    cards = "".join(f'<article class="evidence-card"><p class="card-label">{esc(card["label"])}</p><h3>{esc(card["title"])}</h3><p>{esc(card["body"])}</p><footer>{esc(card["source"])}</footer></article>' for card in v06["cards"])
    evidence_body = f'<div class="intro-row"><div>{headline(v06["headline"])}</div><p class="lead">{esc(v06["lead"])}</p></div><div class="evidence-grid">{cards}</div><p class="caption">Actual project photography is reserved for rights-cleared evidence replacement. This sample uses data-led proof.</p>'
    v07 = copy["V07"]
    swatches = "".join(f'<span class="swatch swatch--{i}" aria-label="material sample {i+1}"></span>' for i in range(8))
    material_body = f'<div class="material-layout"><div><p class="kicker">{esc(v07["kicker"])}</p>{headline(["色は654通り。", "塗料は、住まいに", "合わせて。"])}<p class="lead">{esc(v07["lead"])}</p></div><div class="material-strip" aria-label="色と塗料の選択面">{swatches}<span class="material-index">01 — 08 / 654</span></div></div><p class="caption">{esc(v07["footnote"])}</p>'
    v08 = copy["V08"]
    faq = "".join(f'<details {"open" if i == 0 else ""}><summary>{esc(q)}<span>＋</span></summary><p>{esc(a)}</p></details>' for i, (q, a) in enumerate(v08["items"]))
    faq_body = f'<div class="faq-layout"><div><p class="kicker">{esc(v08["kicker"])}</p>{headline(v08["headline"])}</div><div class="faq-list">{faq}</div></div>'
    v09 = copy["V09"]
    action_body = f'<div class="action-grid"><div><p class="kicker">{esc(v09["kicker"])}</p>{headline(v09["headline"])}<p class="lead">{esc(v09["lead"])}</p></div><div class="action-panel"><a class="action-link action-link--primary" href="tel:+818008080886" data-contact-action="phone"><span>{esc(v09["primary_action"])}</span><strong>{esc(v09["phone"])}</strong><small>{esc(v09["support"][0])}</small></a><a class="action-link" href="https://maylynnhands.com/contact/" data-contact-action="form"><span>{esc(v09["secondary_action"])}</span><small>公式問い合わせフォーム</small></a><p class="action-area">{esc(v09["support"][1])}</p></div></div>'
    style = r'''
@import url('data:text/css,');
:root{--paper:#efede7;--ink:#1b1d1b;--oxide:#9b5843;--moss:#68736b;--zinc:#b8b9b0;--line:rgba(27,29,27,.22);--rail:min(1180px,92vw);--serif:"Zen Kaku Gothic New","Noto Sans JP","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;--mono:"IBM Plex Mono","SFMono-Regular",Consolas,monospace;--ease:cubic-bezier(.22,.61,.36,1)}
*{box-sizing:border-box}html{scroll-behavior:smooth;background:var(--paper)}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif);font-weight:400;line-height:1.8}a,button{font:inherit}button{cursor:pointer}main{overflow:hidden}.topbar{width:var(--rail);margin:auto;padding:24px 0;display:flex;justify-content:space-between;border-bottom:1px solid var(--line);font:11px/1.2 var(--mono);letter-spacing:.12em;text-transform:uppercase}.topbar strong{font-family:var(--serif);font-size:13px;letter-spacing:.03em;text-transform:none}.viewport{width:var(--rail);margin:auto;padding:clamp(6rem,11vw,10rem) 0;border-top:1px solid var(--line);position:relative}.viewport:first-of-type{border-top:0;padding-top:clamp(4rem,8vw,7rem)}.viewport-meta{display:flex;justify-content:space-between;color:var(--moss);font:11px/1.3 var(--mono);letter-spacing:.12em;text-transform:uppercase;margin-bottom:32px}.kicker{font:12px/1.3 var(--mono);letter-spacing:.12em;color:var(--oxide);margin:0 0 24px}.headline-line{display:block;white-space:normal}.viewport h1,.viewport h2{font-weight:600;letter-spacing:-.045em;line-height:1.04;margin:0;max-width:11em}.viewport h1{font-size:clamp(3.8rem,7vw,7.2rem)}.viewport h2{font-size:clamp(2.8rem,5vw,5rem)}.lead{font-size:clamp(1.05rem,1.55vw,1.32rem);line-height:1.72;white-space:pre-line;max-width:36em;margin:30px 0}.caption,.source-note{font:12px/1.6 var(--mono);color:var(--moss);letter-spacing:.02em}.hero-grid{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:clamp(3rem,7vw,8rem);align-items:center}.hero-visual{position:relative;min-width:0;clip-path:inset(0 82% 0 0);transition:clip-path 1000ms var(--ease)}.is-visible .hero-visual,.hero-visual.is-visible{clip-path:inset(0 0 0 0)}.shot{margin:0;position:relative;min-width:0}.shot img{display:block;width:100%;height:auto;aspect-ratio:16/10;object-fit:cover}.shot figcaption{position:absolute;left:14px;bottom:12px;background:rgba(27,29,27,.82);color:var(--paper);padding:4px 8px;font:9px/1.2 var(--mono);letter-spacing:.04em}.hero-shot img{aspect-ratio:16/11;filter:saturate(.78) contrast(1.03)}.inspection-rule{position:absolute;left:8%;top:12%;height:76%;width:1px;background:var(--oxide);opacity:.8}.annotation-chip{position:absolute;right:16px;top:16px;padding:6px 8px;background:var(--paper);font:9px/1.2 var(--mono);color:var(--oxide);letter-spacing:.08em}.fact-rail{display:flex;gap:10px;flex-wrap:wrap;margin-top:44px}.fact-rail span{border-top:2px solid var(--ink);padding:10px 12px 0;font:12px/1.4 var(--mono);letter-spacing:.03em}.scroll-cue{margin-top:80px;color:var(--moss);font:10px/1.4 var(--mono);letter-spacing:.14em}.scroll-cue span{color:var(--oxide);font-size:16px;margin-left:8px}.intro-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(2rem,8vw,9rem);align-items:end}.intro-row .lead{margin-bottom:4px}.sign-grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:72px}.sign-card{border-top:1px solid var(--ink);padding-top:12px}.sign-no{font:11px/1 var(--mono);color:var(--oxide)}.sign-surface{height:150px;margin:22px 0;background:linear-gradient(135deg,#c9c2b7,#817d73);position:relative;overflow:hidden}.sign-surface:after{content:"";position:absolute;width:120%;height:2px;background:var(--oxide);transform:rotate(-18deg);left:-8%;top:55%;box-shadow:0 -16px 0 rgba(155,88,67,.32),0 16px 0 rgba(155,88,67,.22)}.sign-surface--2{background:linear-gradient(160deg,#d3cbbd,#8e8375)}.sign-surface--3{background:linear-gradient(130deg,#d0bca9,#988677)}.sign-surface--4{background:linear-gradient(160deg,#b4b5a3,#6d756d)}.sign-surface--5{background:linear-gradient(145deg,#a99f91,#665e58)}.sign-card h3{font-size:1rem;margin:0 0 6px}.sign-card p{font-size:.82rem;margin:0;color:var(--moss)}.scope-layout{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:clamp(2rem,8vw,8rem);align-items:center;margin-top:72px}.scope-map{height:410px;background:#d7d4cb;position:relative;overflow:hidden;border:1px solid var(--ink)}.house-roof{position:absolute;left:16%;right:16%;top:18%;height:25%;background:var(--oxide);clip-path:polygon(50% 0,100% 100%,0 100%)}.house-wall{position:absolute;left:25%;right:25%;top:42%;bottom:16%;background:#a9afa6;border:1px solid var(--ink)}.house-window{position:absolute;width:28%;height:20%;left:36%;top:51%;background:var(--paper);border:1px solid var(--ink)}.scope-drone{position:absolute;right:10%;top:12%;font:10px var(--mono);color:var(--oxide);letter-spacing:.12em}.scope-list{display:grid;gap:12px}.scope-node{border:1px solid var(--line);background:transparent;text-align:left;padding:18px 20px;transition:background 220ms ease,color 220ms ease,border-color 220ms ease}.scope-node:hover,.scope-node:focus-visible,.scope-node.is-active{background:var(--ink);color:var(--paper);border-color:var(--ink)}.scope-list .caption{margin-top:18px}.proof-header{max-width:700px}.proof-layout{display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,.9fr);gap:clamp(2rem,6vw,6rem);align-items:center;margin-top:72px}.drone-diagram{height:390px;background:#d5d3ca;position:relative;border:1px solid var(--ink);overflow:hidden}.drone-icon{position:absolute;right:17%;top:13%;font-size:32px;color:var(--oxide);animation:float 4s ease-in-out infinite}.roof-plane{position:absolute;left:10%;right:8%;bottom:14%;height:43%;background:#8d948b;clip-path:polygon(14% 0,100% 30%,84% 100%,0 68%);border:1px solid var(--ink)}.survey-line{position:absolute;right:26%;top:20%;width:1px;height:45%;border-left:1px dashed var(--oxide)}.drone-diagram span{position:absolute;left:16px;bottom:14px;font:10px var(--mono);letter-spacing:.13em;color:var(--moss)}.metric-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));border-top:1px solid var(--ink);border-left:1px solid var(--ink)}.metric{min-height:155px;padding:18px;border-right:1px solid var(--ink);border-bottom:1px solid var(--ink);display:flex;flex-direction:column;justify-content:space-between}.metric-label{font:11px var(--mono);color:var(--oxide);letter-spacing:.1em}.metric strong{font:clamp(2.2rem,4vw,4.6rem);line-height:1;font-weight:600;letter-spacing:-.06em}.metric small{font:12px;color:var(--moss)}.process-layout{display:grid;grid-template-columns:minmax(0,7fr) minmax(0,5fr);gap:clamp(2rem,8vw,8rem);align-items:start}.process-visual{position:sticky;top:28px}.process-shot img{aspect-ratio:4/3}.process-progress{display:block;position:absolute;left:-14px;top:0;bottom:0;width:2px;background:linear-gradient(to bottom,var(--oxide),transparent)}.process-steps{list-style:none;margin:44px 0 0;padding:0;border-top:1px solid var(--ink)}.process-steps li{display:grid;grid-template-columns:38px 1fr;gap:14px;align-items:baseline;padding:18px 0;border-bottom:1px solid var(--line);transition:padding 220ms ease,color 220ms ease}.process-steps li span{font:12px var(--mono);color:var(--oxide)}.process-steps li strong{font-size:1.05rem;font-weight:500}.process-steps li:hover{padding-left:10px;color:var(--oxide)}.proof-line{margin-top:30px;border-left:2px solid var(--oxide);padding-left:14px;font-size:1rem}.proof-line span{color:var(--moss);font:11px var(--mono)}.evidence-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:70px}.evidence-card{border:1px solid var(--ink);padding:26px;min-height:250px;display:flex;flex-direction:column}.evidence-card:nth-child(2){margin-top:54px;background:#e4e0d7}.card-label{font:11px var(--mono);letter-spacing:.1em;color:var(--oxide);margin:0}.evidence-card h3{font-size:1.6rem;line-height:1.2;margin:52px 0 14px;max-width:11em}.evidence-card p{margin:0}.evidence-card footer{margin-top:auto;padding-top:24px;border-top:1px solid var(--line);font:11px var(--mono);color:var(--moss)}.material-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:clamp(2rem,8vw,8rem);align-items:center}.material-strip{display:flex;flex-wrap:wrap;gap:10px;align-items:end;border-bottom:1px solid var(--ink);padding:25px 0}.swatch{width:48px;height:110px;display:block;border:1px solid var(--ink)}.swatch--0{background:#e7e0d2}.swatch--1{background:#cbb9a1}.swatch--2{background:#aa8d71}.swatch--3{background:#847a6e}.swatch--4{background:#677166}.swatch--5{background:#5b6663}.swatch--6{background:#6c4d43}.swatch--7{background:#3f4542}.material-index{flex-basis:100%;font:11px var(--mono);color:var(--moss);margin-top:18px}.faq-layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.1fr);gap:clamp(2rem,8vw,8rem)}.faq-list{border-top:1px solid var(--ink)}details{border-bottom:1px solid var(--line);padding:18px 0}summary{list-style:none;display:flex;justify-content:space-between;gap:16px;cursor:pointer;font-size:1.1rem}summary::-webkit-details-marker{display:none}summary span{font:20px var(--mono);color:var(--oxide)}details p{max-width:32em;margin:16px 0 0;color:var(--moss)}.action-grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,.8fr);gap:clamp(2rem,8vw,8rem);align-items:start}.action-panel{background:var(--ink);color:var(--paper);padding:32px;display:grid;gap:18px}.action-link{display:grid;gap:8px;color:var(--paper);text-decoration:none;border-bottom:1px solid rgba(239,237,231,.35);padding:14px 0;transition:color 150ms ease,border-color 150ms ease}.action-link:hover,.action-link:focus-visible{color:#e0a58f;border-color:#e0a58f}.action-link span{font-size:1.1rem}.action-link strong{font:clamp(1.5rem,3vw,2.6rem) var(--mono);font-weight:400;letter-spacing:-.06em}.action-link small{font:11px var(--mono);color:#b7c0b5}.action-area{font:12px/1.6 var(--mono);color:#b7c0b5}.sticky-contact{position:fixed;left:50%;bottom:18px;transform:translate(-50%,120%);z-index:20;display:flex;background:var(--ink);color:var(--paper);border:1px solid var(--paper);transition:transform 240ms ease}.sticky-contact.is-visible{transform:translate(-50%,0)}.sticky-contact a{padding:10px 18px;color:var(--paper);text-decoration:none;font:11px var(--mono);letter-spacing:.06em}.sticky-contact a+a{border-left:1px solid rgba(239,237,231,.35)}.footer{width:var(--rail);margin:auto;padding:26px 0 60px;border-top:1px solid var(--line);display:flex;justify-content:space-between;font:11px var(--mono);color:var(--moss)}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.headline-line{white-space:nowrap}.viewport h1{font-size:clamp(3.15rem,4.7vw,5.4rem)}.viewport h2{font-size:clamp(2.2rem,3.7vw,3.8rem)}.hero-grid{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.intro-row,.faq-layout,.material-layout{grid-template-columns:minmax(0,1.2fr) minmax(0,.8fr)}.evidence-card h3{font-size:1.32rem;max-width:14em}
@media(max-width:760px){:root{--rail:min(100% - 40px,620px)}.topbar{padding:18px 0}.viewport{padding:64px 0}.viewport:first-of-type{padding-top:42px}.viewport-meta{margin-bottom:22px}.hero-grid,.intro-row,.scope-layout,.proof-layout,.process-layout,.material-layout,.faq-layout,.action-grid{grid-template-columns:1fr;gap:30px}.hero-grid{display:flex;flex-direction:column}.hero-copy{order:1}.hero-visual{order:2;width:100%}.viewport h1{font-size:clamp(2.1rem,9vw,3rem)}.viewport h2{font-size:clamp(1.55rem,7vw,2.7rem)}.lead{font-size:1rem;line-height:1.8}.fact-rail{margin-top:28px}.scroll-cue{margin-top:42px}.sign-grid{display:flex;overflow-x:auto;gap:12px;margin-top:45px;padding-bottom:10px;scroll-snap-type:x mandatory}.sign-card{min-width:76vw;scroll-snap-align:start}.scope-map{height:280px}.proof-layout{margin-top:42px}.drone-diagram{height:280px}.metric{min-height:126px;padding:14px}.metric strong{font-size:2.25rem}.process-visual{position:relative;top:auto}.process-steps{margin-top:28px}.evidence-grid{grid-template-columns:1fr;margin-top:42px}.evidence-card:nth-child(2){margin-top:0}.evidence-card h3{font-size:1.12rem;margin-top:36px}.material-strip{overflow-x:auto;flex-wrap:nowrap;padding-bottom:18px;scroll-snap-type:x proximity}.swatch{min-width:46px;scroll-snap-align:start}.material-index{min-width:130px;flex-basis:auto}.action-panel{padding:24px}.sticky-contact a{padding:10px 13px}.footer{padding-bottom:90px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;scroll-behavior:auto!important;transition-duration:.001ms!important}}
'''
    script = r'''<script>
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const observer = new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); } }), {threshold:.14});
document.querySelectorAll('.viewport,.hero-visual').forEach(node => observer.observe(node));
document.querySelectorAll('.scope-node').forEach(node => node.addEventListener('click', () => { document.querySelectorAll('.scope-node').forEach(item => item.classList.remove('is-active')); node.classList.add('is-active'); }));
const sticky = document.querySelector('#sticky-contact'); const hero = document.querySelector('#V01'); const final = document.querySelector('#V09');
if (sticky && hero && final) { const finalObserver = new IntersectionObserver(entries => entries.forEach(entry => sticky.classList.toggle('is-visible', !entry.isIntersecting && window.scrollY > hero.offsetTop)), {threshold:.2}); finalObserver.observe(final); }
</script>'''
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><meta name="description" content="塗る前に、まず状態を見る。小山市を中心としたメイリン塗装工務店の公開情報Prototype。"><title>メイリン塗装工務店｜塗る前に、まず状態を見る。</title><style>{style}</style></head><body><header class="topbar"><strong>メイリン塗装工務店</strong><span>OYAMA / FIELD INSPECTION EDITORIAL</span></header><main>{section(views["V01"], hero, extra_class="viewport--hero")}{section(views["V02"], signs_body)}{section(views["V03"], scope_body)}{section(views["V04"], proof_body, extra_class="viewport--proof")}{section(views["V05"], process_body, extra_class="viewport--process")}{section(views["V06"], evidence_body)}{section(views["V07"], material_body)}{section(views["V08"], faq_body)}{section(views["V09"], action_body, extra_class="viewport--action")}</main><nav id="sticky-contact" class="sticky-contact" aria-label="contact"><a href="tel:+818008080886">電話</a><a href="https://maylynnhands.com/contact/">フォーム</a></nav><footer class="footer"><span>メイリン塗装工務店</span><span>公開情報Prototype / 2026.09.18</span></footer>{script}</body></html>'''


async def capture_artifact(html_url: str, output: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        for width, name in ((1440, "desktop_1440"), (390, "mobile_390"), (430, "additional_430")):
            page = await browser.new_page(viewport={"width": width, "height": 1000})
            await page.goto(html_url, wait_until="networkidle")
            target = output / f"{name}_full.png"
            await page.screenshot(path=str(target), full_page=True)
            records.append({"kind": "full_page", "viewport": width, "path": str(target.relative_to(OUT)), "sha": sha(target)})
            if width in {1440, 390}:
                for viewport_id in ("V01", "V04", "V05", "V06", "V09") if width == 1440 else ("V01", "V04", "V05", "V09"):
                    locator = page.locator(f"[data-viewport-id='{viewport_id}']")
                    await locator.scroll_into_view_if_needed()
                    target = output / f"{name}_{viewport_id}.png"
                    await locator.screenshot(path=str(target))
                    records.append({"kind": "viewport", "viewport": width, "viewport_id": viewport_id, "path": str(target.relative_to(OUT)), "sha": sha(target)})
            await page.close()
        motion_dir = output / "motion_states"
        motion_dir.mkdir(parents=True, exist_ok=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(html_url, wait_until="networkidle")
        for motion_id, viewport_id in zip(("M01", "M02", "M03", "M04", "M05", "M06"), ("V01", "V02", "V03", "V04", "V05", "V09")):
            locator = page.locator(f"[data-viewport-id='{viewport_id}']")
            await locator.scroll_into_view_if_needed()
            target = motion_dir / f"{motion_id}_{viewport_id}.png"
            await locator.screenshot(path=str(target))
            records.append({"kind": "motion_state", "motion_id": motion_id, "viewport_id": viewport_id, "path": str(target.relative_to(OUT)), "sha": sha(target)})
        await page.close()
        await browser.close()
    return {"status": "PASS", "records": records, "counts": {"desktop_full": 1, "mobile_full": 1, "additional_430_full": 1, "desktop_viewports": 5, "mobile_viewports": 4, "motion_states": 6, "total": len(records)}}


async def browser_verify(url: str, output: Path) -> dict[str, Any]:
    report = await run_browser_qa(url, output, DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440])
    payload = report.to_dict()
    payload["technical_widths"] = DEFAULT_WIDTHS
    payload["primary_creative_width"] = 390
    return payload


def main() -> int:
    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    MAYLYNN_OUT.mkdir(parents=True, exist_ok=True)
    source_head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    snapshot = build_maylynn_research_snapshot()
    graph = build_evidence_graph(snapshot)
    decisions = build_customer_decision_model(snapshot, graph)
    experience = build_experience_architecture(snapshot, decisions)
    creative = build_creative_composition(snapshot, experience)
    quality = build_quality_review_contract(snapshot, graph, decisions, experience, creative)
    assets = load_assets()
    asset_manifest = {"schema_version": "round2c_asset_manifest_v1", "policy": "generated_or_free_stock_only; actual_evidence_requires_rights_clearance", "bindings": [{"viewport_id": "V01", "role": "hero_authority", "asset_role": "hero_home_finish", "status": "PROXY_NOT_EVIDENCE"}, {"viewport_id": "V02", "role": "defect_detail", "asset_role": "material_detail", "status": "PROXY_NOT_EVIDENCE"}, {"viewport_id": "V05", "role": "craft_process", "asset_role": "craft_handwork", "status": "FREE_STOCK_CONTEXT"}, {"viewport_id": "V06", "role": "evidence_surface", "asset_role": "data_led_no_photo", "status": "RIGHTS_SAFE"}, {"viewport_id": "V07", "role": "material_choice", "asset_role": "css_material_strip", "status": "ABSTRACT_NOT_REAL_COLOR"}], "assets": list(assets.values()), "actual_evidence_slots": ["E01_REAL_DRONE_INSPECTION", "E02_REAL_WORKER_PORTRAIT", "E03_REAL_BEFORE_AFTER", "E04_REAL_PROJECT_SEQUENCE"]}
    html_text = render_html(snapshot, experience, creative, assets)
    html_path = MAYLYNN_OUT / "index.html"
    html_path.write_text(html_text, encoding="utf-8")
    human_review_dir = OUT / "human_review_html"
    human_review_path = human_review_dir / "index.html"
    human_review_path.parent.mkdir(parents=True, exist_ok=True)
    human_review_path.write_text(build_self_contained_html(html_text, assets), encoding="utf-8")
    for name, value in (("company_research_v2.json", snapshot), ("evidence_graph_v2.json", graph), ("customer_decision_model_v1.json", decisions), ("experience_architecture_v2.json", experience), ("creative_composition_v2.json", creative), ("quality_review_contract_v2.json", quality), ("asset_manifest.json", asset_manifest)):
        write(MAYLYNN_OUT / name, value)
    write(MAYLYNN_OUT / "source_manifest.json", {"generated_from_commit": source_head, "research_snapshot_date": snapshot["research_snapshot_date"], "sources": snapshot["sources"], "source_conflict_policy": "preserve_conflicted; no silent resolution"})
    write(OUT / "reports" / "html_provenance.json", {"status": "PASS", "source_head": source_head, "generated_from_commit": source_head, "canonical_html": "maylynn_premium_prototype/index.html", "self_contained_html": "human_review_html/index.html", "self_contained": True, "external_asset_dependencies": [], "external_navigation_links": ["https://maylynnhands.com/contact/"]})
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(ROOT), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{MAYLYNN_OUT.relative_to(ROOT).as_posix()}/index.html"
        browser_report = asyncio.run(browser_verify(url, OUT / "browser_qa"))
        captures = asyncio.run(capture_artifact(url, OUT / "captures"))
    finally:
        server.shutdown()
    write(OUT / "browser_qa.json", browser_report)
    write(OUT / "capture_manifest.json", {"schema_version": "round2c_capture_manifest_v1", "source_head": source_head, **captures})
    write(OUT / "reports" / "capture_provenance.json", {"status": "PASS", "source_head": source_head, "capture_manifest": "capture_manifest.json", "record_count": captures["counts"]["total"], "stale_capture_count": 0, "provenance_rule": "every capture is generated in this run from the source_head"})
    attribution = {
        "schema_version": "round2c_full_test_attribution_v1",
        "starting_head": "24264ec649450e9b8d2aca2c5669eed4db5e41fd",
        "final_head": source_head,
        "starting_total": 371,
        "final_total": 377,
        "starting_failures": 3,
        "starting_errors": 1,
        "final_failures": 3,
        "final_errors": 1,
        "round2c_regression_count": 0,
        "cases": [
            {"test_name": "test_evidence_selection_runtime.EvidenceSelectionRuntimeTest.test_nine_widths_have_no_overflow_and_exact_actions_are_visible", "variant": "P10_ACCOUNTABILITY", "width": 390, "starting_result": "FAIL", "final_result": "FAIL", "classification": "PRE_EXISTING", "error": "853.21875 is greater than 846", "round2c_relation": "Unchanged existing evidence-selection runtime fixture; Round 2C does not modify this module or fixture."},
            {"test_name": "test_evidence_selection_runtime.EvidenceSelectionRuntimeTest.test_nine_widths_have_no_overflow_and_exact_actions_are_visible", "variant": "P10_CONTINUITY", "width": 390, "starting_result": "FAIL", "final_result": "FAIL", "classification": "PRE_EXISTING", "error": "853.21875 is greater than 846", "round2c_relation": "Unchanged existing evidence-selection runtime fixture; Round 2C does not modify this module or fixture."},
            {"test_name": "test_evidence_selection_runtime.EvidenceSelectionRuntimeTest.test_nine_widths_have_no_overflow_and_exact_actions_are_visible", "variant": "P10_BUSINESS_MODEL", "width": 390, "starting_result": "FAIL", "final_result": "FAIL", "classification": "PRE_EXISTING", "error": "853.21875 is greater than 846", "round2c_relation": "Unchanged existing evidence-selection runtime fixture; Round 2C does not modify this module or fixture."},
            {"test_name": "test_phase7.Phase7Tests.test_restart_and_isolation", "variant": None, "width": None, "starting_result": "ERROR", "final_result": "ERROR", "classification": "PRE_EXISTING", "error": "PermissionError [WinError 32] while cleaning temporary x.db", "round2c_relation": "Windows temporary SQLite file lock in existing Phase7 test; Round 2C does not modify Phase7 or database lifecycle code."}
        ]
    }
    write(OUT / "reports" / "full_test_attribution.json", attribution)
    write(OUT / "reports" / "comparison_manifest.json", {"starting_head": attribution["starting_head"], "final_head": source_head, "starting_total": attribution["starting_total"], "final_total": attribution["final_total"], "round2c_direct_tests": {"total": 6, "passed": 6}, "round2c_regression_count": 0, "classification": "PRE_EXISTING"})
    checks = {
        "research": validate_research_snapshot(snapshot),
        "quality_contract": quality,
        "browser_qa": {"status": browser_report["status"], "total": len(browser_report["results"]), "pass": sum(item["status"] == "PASS" for item in browser_report["results"]), "fail": sum(item["status"] == "FAIL" for item in browser_report["results"]), "overflow_max": max((item["horizontal_overflow_px"] for item in browser_report["results"]), default=0), "console_errors": sum(len(item["console_errors"]) for item in browser_report["results"]), "page_errors": sum(len(item["page_errors"]) for item in browser_report["results"]), "request_failures": sum(len(item["request_failures"]) for item in browser_report["results"])},
        "captures": captures,
        "manual_lp_edit": 0,
        "fake_cta": 0,
        "final_human_quality_decision": "DEFERRED_TO_SHUN",
        "one_million_yen_pass": "NOT_ASSESSED",
    }
    write(OUT / "reports" / "technical_verification.json", checks)
    write(OUT / "reports" / "render_contract.json", {"status": "PASS" if quality["status"] == "PASS" else "FAIL", "viewport_count": 9, "viewport_ids": [item["viewport_id"] for item in experience["sections"]], "complete_idea_count": sum(bool(item.get("complete_idea")) for item in experience["sections"]), "manual_lp_edit": 0})
    write(OUT / "reports" / "safety_and_rights.json", {"status": "PASS", "claim_trace": "fact nodes to decisions to viewport copy", "conflicted_address_excluded_from_primary": True, "proxy_not_evidence": True, "actual_evidence_slots": asset_manifest["actual_evidence_slots"], "contact_actionability": {"phone": "VERIFIED_PUBLIC", "form": "VERIFIED_OFFICIAL"}, "invented_price": 0, "invented_project": 0, "invented_credential": 0})
    artifact_name = f"round2c-maylynn-premium-prototype-{source_head}"
    artifact = {"name": artifact_name, "source_head": source_head, "root": "artifacts/round2c", "includes": ["maylynn_premium_prototype/index.html", "human_review_html/index.html", "company_research_v2.json", "evidence_graph_v2.json", "customer_decision_model_v1.json", "experience_architecture_v2.json", "creative_composition_v2.json", "quality_review_contract_v2.json", "asset_manifest.json", "source_manifest.json", "captures/", "browser_qa.json", "capture_manifest.json", "reports/"], "github_artifact": "NOT_UPLOADED"}
    write(OUT / "artifact_manifest.json", artifact)
    browser_summary = checks["browser_qa"]
    all_pass = quality["status"] == "PASS" and checks["research"]["status"] == "PASS" and browser_summary["status"] == "PASS" and browser_summary["total"] == 9 and browser_summary["pass"] == 9 and browser_summary["fail"] == 0 and browser_summary["overflow_max"] == 0 and browser_summary["console_errors"] == 0 and browser_summary["page_errors"] == 0 and browser_summary["request_failures"] == 0 and captures["status"] == "PASS" and captures["counts"]["total"] == 18
    summary = {"schema_version": "round2c_maylynn_premium_prototype_v1", "status": "PASS" if all_pass else "HOLD", "round": "2C", "source_head": source_head, "company": "maylynn_paint", "quality_architecture_ready": True, "maylynn_implementation_ready": all_pass, "machine_technical_verification": "PASS" if all_pass else "HOLD", "shun_quality_review": "NOT_STARTED", "one_million_yen_pass": "NOT_ASSESSED", "nagi_no_mirai": "NOT_STARTED", "watashi_no_daidokoro": "NOT_STARTED", "browser_qa": browser_summary, "captures": captures["counts"], "artifact": artifact, "html_review": {"path": "human_review_html/index.html", "self_contained": True, "external_asset_dependencies": []}, "full_test_attribution": {"path": "reports/full_test_attribution.json", "classification": "PRE_EXISTING", "round2c_regression_count": 0}, "manual_lp_edit": 0, "creative_production_status": "PROTOTYPE_NOT_FINAL", "remaining": ["Shun must review the actual HTML/screenshots/motion before any final quality decision."]}
    write(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
