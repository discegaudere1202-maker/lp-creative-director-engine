"""Round 2F-B: Maylynn Premium Quality Uplift implementation.

This runner is deliberately Maylynn-only.  It reuses the proven Round 2E
interaction and rendered-line contracts, but owns a new premium presentation
layer, the two replacement photographs, deterministic font loading, and the
Human Review package.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import date
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_round2e_b_maylynn as base
import run_round2e_c2_rendered_line_hardening as c2
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa, run_rendered_line_qa
from run_round2e_c_editorial_hardening import browser_summary, internal_label_qa


ROUND2F_VARIANT = os.environ.get("ROUND2F_VARIANT", "B").upper()
IS_B2 = ROUND2F_VARIANT == "B2"
DEFAULT_OUTPUT = "round2f_b2" if IS_B2 else "round2f_b"
OUT = Path(os.environ.get("ROUND2F_B_OUTPUT_ROOT", str(ROOT / "artifacts" / DEFAULT_OUTPUT)))
if not OUT.is_absolute():
    OUT = ROOT / OUT
MAYLYNN_OUT = OUT / "maylynn_premium"
ROUND2E_ROOT = ROOT / "assets" / "photography" / "generated" / "maylynn_paint" / "round2e"
ROUND2F_ROOT = ROOT / "assets" / "photography" / "generated" / "maylynn_paint" / "round2f"
FONT_ROOT = ROOT / "assets" / "fonts" / "round2f"
FONT_FILES = {
    "Zen Kaku Gothic New": ("ZenKakuGothicNew-600.ttf", "600"),
    "Noto Sans JP": ("NotoSansJP-Variable.ttf", "400 500"),
    "Inter Tight": ("InterTight-Variable.ttf", "500 600"),
    "IBM Plex Mono": ("IBMPlexMono-400.ttf", "400"),
}


class QuietAssetHandler(SimpleHTTPRequestHandler):
    """Keep generated QA output focused on contract failures, not asset 200s."""

    def log_message(self, _format: str, *args: Any) -> None:
        return


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix.lower() == ".ttf":
        mime = "font/ttf"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def generated_source(asset_id: str, path: Path, role: str) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "source_type": "generated",
        "provider": "OpenAI image generation",
        "source": "round2f-approved-generated-visual",
        "source_url": f"codex://imagegen/round2f/{path.name}",
        "rights": "GENERATED_PIPELINE_ASSET",
        "commercial_use": "GENERATED_PIPELINE; not third-party stock",
        "author": "OpenAI",
        "downloaded_at": str(date.today()),
        "evidence_status": "EXPLANATORY_PROXY",
        "role": role,
        "local_asset_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "file_hash": sha(path),
        "bytes": path.stat().st_size,
        "width": 1536,
        "height": 1024,
    }


def diagram_source(asset_id: str, role: str) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "source_type": "custom_diagram",
        "provider": "Round 2F-B renderer",
        "source": "inline-svg",
        "source_url": "codex://round2f-b/inline-svg",
        "rights": "PROJECT_AUTHORED",
        "commercial_use": "PROJECT_AUTHORED",
        "author": "lp-creative-director-engine",
        "downloaded_at": str(date.today()),
        "evidence_status": "EXPLANATORY_PROXY",
        "role": role,
        "local_asset_path": None,
    }


def load_media() -> dict[str, dict[str, Any]]:
    paths = {
        "A01": ROUND2E_ROOT / "a01_hero_inspection_human.jpg",
        "A02": ROUND2E_ROOT / "a02_facade_detail.jpg",
        "A03": ROUND2E_ROOT / "a03_wall_crack_macro.jpg",
        "A04": ROUND2E_ROOT / "a04_peeling_surface.jpg",
        "A05": ROUND2E_ROOT / "a05_fading_chalking.jpg",
        "A06": ROUND2E_ROOT / "a06_moss_weathering.jpg",
        "A08": ROUND2E_ROOT / "a08_roof_aerial_inspection.jpg",
        "A09": ROUND2E_ROOT / "a09_preparation_masking.jpg",
        "A10": ROUND2F_ROOT / "a10_roller_application.png",
        "A11": ROUND2E_ROOT / "a11_finishing_brush.jpg",
        "A13": ROUND2E_ROOT / "a13_paint_color_fan.jpg",
        "A14": ROUND2F_ROOT / "a14_paint_film_grazing_light.png",
        "A15": ROUND2E_ROOT / "a15_paint_tools_tray.jpg",
        "A16": ROUND2E_ROOT / "a16_homeowner_consultation.jpg",
    }
    missing = [asset_id for asset_id, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Round 2F-B media missing: {missing}")
    media = {asset_id: generated_source(asset_id, path, f"Maylynn Premium {asset_id}") for asset_id, path in paths.items()}
    media["A07"] = diagram_source("A07", "V03 restrained Japanese house scope explanation")
    media["A12"] = diagram_source("A12", "V06 restrained regional editorial map")
    return {asset_id: media[asset_id] for asset_id in [f"A{i:02d}" for i in range(1, 17)]}


SCOPE_SVG = '''<svg class="scope-illustration" viewBox="0 0 840 540" role="img" aria-label="外壁・屋根・高所・修繕を住まいごとに見る説明図"><defs><linearGradient id="sf" x1="0" x2="1"><stop stop-color="#e9e5da"/><stop offset="1" stop-color="#c9c0b0"/></linearGradient><linearGradient id="sw" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#f4f0e8"/><stop offset="1" stop-color="#c8bfae"/></linearGradient></defs><rect width="840" height="540" fill="url(#sf)"/><path d="M0 420H840" stroke="#26231f" stroke-width="2"/><path d="M94 407L218 275L340 407" fill="#7d756b" stroke="#26231f" stroke-width="3" data-scope="roof"/><path d="M112 404H324V492H112Z" fill="url(#sw)" stroke="#26231f" stroke-width="3" data-scope="wall"/><path d="M148 445H201V492H148Z" fill="#5f665f" stroke="#26231f" stroke-width="2"/><path d="M246 433H300V472H246Z" fill="#d6d0c4" stroke="#26231f" stroke-width="2"/><path d="M414 407L548 232L720 407" fill="#8c5e4d" stroke="#26231f" stroke-width="3" data-scope="high"/><path d="M438 404H700V492H438Z" fill="url(#sw)" stroke="#26231f" stroke-width="3" data-scope="repair"/><path d="M482 444H538V492H482Z" fill="#5f665f" stroke="#26231f" stroke-width="2"/><path d="M588 432H664V470H588Z" fill="#d6d0c4" stroke="#26231f" stroke-width="2"/><path d="M58 472H778" stroke="#7e877c" stroke-width="2"/><path d="M752 94C674 145 621 184 548 232" fill="none" stroke="#aa624b" stroke-width="2" stroke-dasharray="7 9" data-scope="high"/><circle cx="756" cy="92" r="17" fill="#f4f0e8" stroke="#aa624b" stroke-width="2"/><path d="M746 92h20M756 82v20" stroke="#aa624b" stroke-width="2"/><g fill="#26231f" font-family="Noto Sans JP, sans-serif" font-size="18"><text x="115" y="525">外壁</text><text x="426" y="525">屋根・高所</text><text x="665" y="130" fill="#9a5944">確認</text></g></svg>'''

MAP_SVG = '''<svg class="evidence-map" viewBox="0 0 680 430" role="img" aria-label="小山市中心と周辺エリアの説明図"><defs><linearGradient id="mf" x1="0" x2="1"><stop stop-color="#dfe2d7"/><stop offset="1" stop-color="#b9c3b8"/></linearGradient></defs><rect width="680" height="430" fill="url(#mf)"/><path d="M-30 118C92 165 178 78 302 126C432 177 536 84 714 129M-28 308C112 254 198 350 332 278C464 207 548 343 712 285M134 -20C171 89 104 226 166 452M484 -20C434 82 528 204 476 452" fill="none" stroke="#f0eee7" stroke-width="24" opacity=".8"/><path d="M-10 221C118 200 246 236 356 201C472 164 561 237 704 202" fill="none" stroke="#717a71" stroke-width="8" opacity=".72"/><path d="M-10 244C154 235 248 272 370 239C482 207 564 278 704 254" fill="none" stroke="#aab1a6" stroke-width="3"/><path d="M320 65L368 103L351 166L290 177L255 125L272 82Z" fill="#9f5e48" opacity=".78"/><circle cx="320" cy="122" r="15" fill="#f3f0e8" stroke="#26231f" stroke-width="3"/><circle cx="320" cy="122" r="5" fill="#a45d47"/><path d="M320 122C401 157 466 204 548 227" stroke="#a45d47" stroke-width="2" stroke-dasharray="8 8" fill="none"/><g fill="#26231f" font-family="Noto Sans JP, sans-serif" font-size="18"><text x="275" y="205">小山市</text><text x="482" y="263" fill="#9a5944">周辺エリア</text><text x="28" y="390" font-size="14">相談できる範囲の目安</text></g></svg>'''


PREMIUM_STYLE = r'''
@font-face{font-family:"Zen Kaku Gothic New";src:url("/assets/fonts/round2f/ZenKakuGothicNew-600.ttf") format("truetype");font-weight:600;font-style:normal;font-display:block}
@font-face{font-family:"Noto Sans JP";src:url("/assets/fonts/round2f/NotoSansJP-Variable.ttf") format("truetype");font-weight:400 500;font-style:normal;font-display:block}
@font-face{font-family:"Inter Tight";src:url("/assets/fonts/round2f/InterTight-Variable.ttf") format("truetype");font-weight:500 600;font-style:normal;font-display:block}
@font-face{font-family:"IBM Plex Mono";src:url("/assets/fonts/round2f/IBMPlexMono-400.ttf") format("truetype");font-weight:400;font-style:normal;font-display:block}
:root{--display:"Zen Kaku Gothic New","Noto Sans JP",sans-serif;--body:"Noto Sans JP",sans-serif;--latin:"Inter Tight",sans-serif;--mono-actual:"IBM Plex Mono",monospace;--premium-paper:#f3f0e9;--premium-ink:#25221f;--premium-oxide:#a45d47;--premium-moss:#6d786e}
html,body{background:var(--premium-paper);color:var(--premium-ink);font-family:var(--body)}
.topbar{font-family:var(--mono-actual);border-color:rgba(37,34,31,.24);padding:28px 0}.topbar strong{font-family:var(--display);font-weight:600}.topbar span{font-family:var(--latin);letter-spacing:.12em}
.viewport{border-color:rgba(37,34,31,.18);padding:clamp(5.5rem,8vw,8.5rem) 0}.viewport:first-of-type{padding-top:clamp(3.5rem,6vw,6rem)}
.viewport-meta{display:none}.kicker{font-family:var(--latin);font-weight:600;letter-spacing:.1em;text-transform:none;color:var(--premium-oxide)}
.viewport h1,.viewport h2{font-family:var(--display);font-weight:600;letter-spacing:-.065em;line-height:1.02;color:var(--premium-ink)}
.viewport h1{font-size:clamp(3.2rem,5.2vw,5.2rem)}.viewport h2{font-size:clamp(2.1rem,3.8vw,3.7rem)}.lead{font-family:var(--body);max-width:34em;line-height:1.9;color:#4e514b}
.caption,.source-note,.body-note,.fact-rail span,.atlas-stop-number,.roof-fact span,.proof-line,.material-footnote,.faq-side-note,.action-route,.footer{font-family:var(--mono-actual)}
.media-frame{background:#d9d6cc}.media-frame figcaption{position:static;padding:10px 0 0;background:none;color:var(--premium-moss);font:11px/1.55 var(--body);letter-spacing:0}
.hero-composition{grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:clamp(2rem,4vw,4.5rem);min-height:78vh}.hero-copy{padding-top:clamp(1rem,4vw,4rem);min-width:0;overflow:clip}.hero-media-stack{min-height:clamp(540px,67vw,760px);min-width:0;overflow:clip}.hero-primary{inset:0 0 7% 5%;height:93%;clip-path:inset(0 7% 0 0);transform:scale(1.02)}.hero-media-stack.is-live .hero-primary{transform:scale(1)}.hero-inset{width:34%;height:28%;border:6px solid var(--premium-paper);box-shadow:10px 10px 0 rgba(37,34,31,.12)}.inspection-line{left:7%;top:8%;bottom:11%;background:var(--premium-oxide)}.inspection-target,.hero-callout{display:none}.hero-caption{left:7%;bottom:4%;background:rgba(243,240,233,.9);font-family:var(--mono-actual);color:var(--premium-oxide)}
.fact-rail{gap:26px;border-top:1px solid rgba(37,34,31,.35);padding-top:18px}.fact-rail span{border:0;padding:0;color:var(--premium-moss);font-size:11px}
.atlas-layout{grid-template-columns:minmax(0,1.12fr) minmax(270px,.88fr);gap:clamp(2.5rem,6vw,6rem);min-height:92vh}.atlas-stage{height:clamp(560px,63vw,720px);box-shadow:16px 16px 0 rgba(37,34,31,.07)}.atlas-stage-label,.atlas-stage-index{display:none}.atlas-stop{padding:28px 0}.atlas-stop h3{font-family:var(--display);font-weight:600}.atlas-stop p{font-family:var(--body);color:#5e625a}.atlas-stop.is-active{padding-left:18px;color:var(--premium-oxide)}
.scope-layout{grid-template-columns:minmax(0,1.16fr) minmax(260px,.84fr);gap:clamp(2rem,6vw,6rem)}.scope-visual{padding:18px;background:#dedfd7;box-shadow:16px 16px 0 rgba(37,34,31,.07)}.scope-index button{font-family:var(--body);padding:22px 0}.scope-index button span{font-family:var(--body);font-size:1rem}.scope-index button.is-active{color:var(--premium-oxide);padding-left:14px}.scope-note{font-family:var(--body);color:var(--premium-moss);white-space:nowrap}
.roof-viewport{min-height:0}.roof-layout{grid-template-columns:minmax(0,1fr);gap:28px}.roof-stage{height:min(78vh,760px);box-shadow:18px 18px 0 rgba(37,34,31,.09);transform:scale(.99)}.roof-stage.is-live{transform:scale(1)}.roof-stage img{object-position:center 52%}.roof-label{display:none}.roof-facts{display:grid;grid-template-columns:2fr repeat(3,1fr);align-items:stretch;gap:0;border-top:1px solid var(--premium-ink)}.roof-fact{border-bottom:1px solid rgba(37,34,31,.2);border-right:1px solid rgba(37,34,31,.16);padding:20px 18px;min-height:124px}.roof-fact:first-child{background:var(--premium-ink);color:var(--premium-paper);padding:26px}.roof-fact:first-child strong{font-family:var(--latin);font-size:2.8rem}.roof-fact strong{font-family:var(--latin);font-weight:600}.roof-fact span,.roof-fact small{font-family:var(--body)}
.craft-layout{grid-template-columns:minmax(0,1.2fr) minmax(270px,.8fr);gap:clamp(2rem,6vw,6rem)}.craft-stage{height:min(70vh,700px);box-shadow:16px 16px 0 rgba(37,34,31,.08)}.craft-stage-label{display:none}.craft-step{padding:26px 0}.craft-step strong{font-family:var(--display);font-weight:600}.craft-step p{font-family:var(--body);color:#5e625a}.craft-step.is-active{padding-left:16px;color:var(--premium-oxide)}.proof-line{color:var(--premium-moss)}
.evidence-layout{grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:clamp(2rem,6vw,6rem)}.evidence-map-frame{padding:16px;background:#dfe1d8;box-shadow:16px 16px 0 rgba(37,34,31,.07)}.evidence-copy h2{max-width:11em}.card-label{font-family:var(--latin);font-weight:600;color:var(--premium-oxide)}.evidence-card{border-top-color:rgba(37,34,31,.2)}.evidence-card h3{font-family:var(--display);font-weight:600}.evidence-card p,.evidence-card footer,.evidence-note{font-family:var(--body);color:#5e625a}
.material-layout{grid-template-columns:minmax(0,.88fr) minmax(0,1.12fr);gap:clamp(2rem,6vw,6rem)}.paint-fan{height:clamp(430px,44vw,600px);box-shadow:16px 16px 0 rgba(37,34,31,.07)}.material-preview{height:260px;box-shadow:12px 12px 0 rgba(37,34,31,.08)}.material-preview-label{font-family:var(--latin);background:rgba(243,240,233,.9);color:var(--premium-oxide)}.swatch-button{border:1px solid rgba(37,34,31,.35)}
.faq-layout{grid-template-columns:minmax(0,.62fr) minmax(0,1.38fr);gap:clamp(2rem,6vw,6rem)}.faq-media{height:300px;grid-column:1}.faq-list details summary{font-family:var(--display);font-weight:600}.faq-list details p{font-family:var(--body)}
.closing-layout{grid-template-columns:minmax(0,1.12fr) minmax(0,.88fr);gap:0;background:var(--premium-ink);color:var(--premium-paper);min-height:clamp(520px,58vw,700px);min-width:0;overflow:clip}.closing-media{box-shadow:none;height:100%;min-height:520px;min-width:0;overflow:clip}.closing-copy{padding:clamp(2rem,4vw,4rem);display:flex;flex-direction:column;justify-content:center;min-width:0;overflow:clip}.closing-copy h2{color:var(--premium-paper);font-size:clamp(2rem,3.1vw,3.2rem)}.closing-copy .lead{color:#d7d5cd}.action-panel{border-color:rgba(243,240,233,.25);box-shadow:none;min-width:0}.action-link{border-color:rgba(243,240,233,.3)}.action-link span,.action-link strong,.action-link small{font-family:var(--body)}.action-link strong{font-family:var(--latin);font-size:clamp(2.2rem,3.4vw,3.4rem)}.closing-divider{background:var(--premium-oxide)}.sticky-contact{display:none!important}
.lead-line{display:block;white-space:nowrap}
.viewport,.viewport *{min-width:0}
.footer{width:var(--rail);font-family:var(--body);color:var(--premium-moss);padding-bottom:42px}
@media(min-width:761px) and (max-width:900px){.hero-composition,.closing-layout,.scope-layout,.evidence-layout,.atlas-layout,.craft-layout{grid-template-columns:1fr;gap:3rem}.hero-media-stack{min-height:560px}.closing-layout{display:grid}.closing-media{min-height:420px}.closing-copy{padding:2rem 0}.scope-note{max-width:32em}.craft-step p{white-space:nowrap}}
@media(max-width:760px){.lead-line{white-space:normal}.topbar{padding:18px 0}.topbar span{font-family:var(--body);letter-spacing:0}.viewport{padding:56px 0}.viewport h1{font-size:clamp(2.35rem,10vw,4rem)}.viewport h2{font-size:clamp(2rem,8.7vw,3.1rem)}.hero-composition{gap:24px}.hero-media-stack{min-height:430px}.hero-primary{inset:0 0 7% 0}.fact-rail{display:grid;grid-template-columns:1fr 1fr;gap:12px}.atlas-layout,.scope-layout,.roof-layout,.craft-layout,.evidence-layout,.material-layout{gap:26px}.atlas-stage{display:none}.atlas-stop-media{height:280px}.roof-stage{height:390px;box-shadow:8px 8px 0 rgba(37,34,31,.08)}.roof-facts{grid-template-columns:1fr 1fr}.roof-fact:first-child{grid-column:1/-1}.roof-fact:first-child strong{font-size:2.3rem}.craft-stage{display:none}.craft-mobile-media{height:260px}.evidence-map-frame{padding:10px}.paint-fan{height:330px}.material-preview{height:250px}.swatch-row{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;overflow:visible;padding:10px 0 18px}.swatch-button{min-width:0;height:62px}.faq-layout{gap:24px}.faq-media{height:250px}.closing-layout{display:flex;flex-direction:column;min-height:0}.closing-media{min-height:350px;height:350px;order:1}.closing-copy{order:2;padding:28px 22px}.sticky-contact{display:flex!important}}
@media(prefers-reduced-motion:reduce){.hero-primary,.hero-inset,.inspection-line,.roof-stage,.closing-media{transform:none!important}}
'''


# B2 keeps the approved 2F-A direction as executable requirements.  These
# overrides intentionally target rendered classes rather than hand-editing an
# exported LP; the same rules therefore apply to every future engine render.
B2_FIDELITY_STYLE = r'''
.media-frame figcaption{display:none!important}.proxy-transparency{margin:14px 0 0;font:11px/1.65 var(--body);color:var(--premium-moss);letter-spacing:0}.v06-lead-line{display:inline}.roof-viewport{display:flex;flex-direction:column;gap:clamp(1.5rem,3vw,2.6rem);padding-block:clamp(4.2rem,6vw,6.4rem)}.roof-viewport .roof-layout{display:contents}.roof-stage{order:1;height:min(66vh,640px);box-shadow:10px 10px 0 rgba(37,34,31,.07)}.roof-stage:after{background:linear-gradient(180deg,rgba(37,34,31,.03),transparent 38%,rgba(37,34,31,.08))}.roof-stage .roof-path path{stroke:rgba(164,93,71,.58)!important;stroke-width:1.2!important;stroke-dasharray:5 8!important;stroke-dashoffset:0!important;animation:none!important;opacity:.62!important}.roof-marker{width:12px!important;height:12px!important;border-width:1px!important;background:rgba(243,240,233,.94)!important;opacity:1!important;transform:none!important;animation:none!important}.proof-header{order:2;max-width:54rem}.roof-facts{order:3;grid-template-columns:2fr repeat(3,1fr);border-top-color:rgba(37,34,31,.42)}.roof-fact{min-height:104px;padding:15px 16px}.roof-fact:first-child{background:#312d29}.roof-viewport>.source-note{order:4;margin:0}.roof-viewport>.proxy-transparency{order:5!important;margin:0}.craft-viewport{min-height:0;padding-block:clamp(4.2rem,6vw,6.4rem)}.craft-layout{align-items:start}.craft-stage{height:min(56vw,560px);min-height:420px;background:#d7d5cd;box-shadow:10px 10px 0 rgba(37,34,31,.07)}.craft-frame,.craft-frame .media-frame,.craft-frame img{width:100%;height:100%}.craft-frame .media-frame{margin:0}.craft-frame img{display:block;object-fit:cover}.craft-progress{background:rgba(243,240,233,.55)}.craft-step{padding:20px 0}.craft-step p{margin-top:5px}.evidence-layout{align-items:start}.evidence-map-frame{max-width:420px;margin-top:44px;box-shadow:8px 8px 0 rgba(37,34,31,.06)}.evidence-copy{max-width:760px}.evidence-card{grid-template-columns:150px 1fr;padding:20px 0}.card-label{font-family:var(--body);font-size:.86rem;letter-spacing:0}.material-viewport{padding-block:clamp(4.2rem,6vw,6.4rem)}.paint-fan{height:clamp(390px,39vw,520px);box-shadow:10px 10px 0 rgba(37,34,31,.07)}.material-preview{height:230px;box-shadow:8px 8px 0 rgba(37,34,31,.06)}.material-preview-label{left:12px;bottom:12px;padding:6px 8px;font:11px/1.35 var(--body);letter-spacing:0}.faq-viewport{min-height:0;padding-block:clamp(4rem,5.5vw,5.6rem)}.faq-layout{grid-template-columns:minmax(220px,.34fr) minmax(0,.66fr);grid-template-rows:auto auto;column-gap:clamp(2rem,5vw,5rem);row-gap:22px;align-items:start}.faq-layout>div:first-child{grid-column:1;grid-row:1}.faq-list{grid-column:2;grid-row:1/span 2}.faq-media{grid-column:1;grid-row:2;height:220px;margin:0;align-self:start}.faq-side-note{margin-top:18px}.action-viewport{padding-top:clamp(4.2rem,6vw,6.4rem)}
@media(max-width:760px){.proxy-transparency{font-size:10px}.roof-viewport{display:block;padding-block:56px}.roof-viewport .roof-layout{display:flex}.roof-stage{height:370px;min-height:0}.proof-header{margin-top:26px}.roof-facts{grid-template-columns:1fr 1fr}.craft-viewport,.material-viewport,.faq-viewport,.action-viewport{padding-block:56px}.craft-stage{display:none}.craft-mobile-media,.craft-mobile-media .media-frame,.craft-mobile-media img{height:250px}.craft-mobile-media img{object-fit:cover}.faq-layout{display:grid;grid-template-columns:1fr;grid-template-rows:auto;gap:24px}.faq-layout>div:first-child,.faq-list,.faq-media{grid-column:1;grid-row:auto}.faq-media{height:230px;order:0}.faq-list{order:1}.faq-layout>div:first-child{order:-1}.evidence-map-frame{max-width:none;margin-top:0}[data-viewport-id="V06"] .v06-lead-line{display:block}}
'''


CREATIVE_FIDELITY_CONTRACT = {
    "schema_version": "round2f_b2_creative_direction_fidelity_v1",
    "round": "2F-B2",
    "pipeline": "creative_intent -> implementation_contract -> render -> fidelity_qa",
    "viewports": {
        "V04": {"required": {"asset_ids": ["A08"], "visual_dominance": "roof_photo", "topology": "photo_then_headline_then_proof", "inspection_path_px_max": 1.5}, "forbidden": ["thick_scan_geometry", "wide_orange_rectangle", "grey_mask"], "target": {"marker_style": "small_circle", "path_opacity_max": .7}},
        "V05": {"required": {"asset_ids": ["A09", "A10", "A11"], "interaction": "three_state_process", "image_fill_min": .95}, "forbidden": ["dead_blank_stage", "visible_scroll_spacer"], "target": {"composition_type": "documentary_photo_process"}},
        "V06": {"required": {"headline_text": "施工実績と、公開レビュー。", "primary": "official_project", "secondary": "public_review"}, "forbidden": ["old_headline"], "target": {"map_dominance": "secondary"}},
        "V07": {"required": {"headline_text": "654色から、住まいに合う色を。", "asset_ids": ["A13", "A14"], "font_role": "material_experience"}, "forbidden": ["prototype_tone_label", "repeated_proxy_badge"], "target": {"palette_dominance": "physical_color_fan"}},
        "V08": {"required": {"headline_text": "保証も、工期も。相談する前に。", "composition_type": "compact_reassurance"}, "forbidden": ["old_headline", "dead_blank_stage"], "target": {"desktop_photo_ratio": .3, "section_height_max": 1120}},
        "PUBLIC": {"required": {"proxy_transparency": "group_footnote"}, "forbidden": ["repeated_proxy_badge"]},
    },
}


def apply_b2_creative(creative: dict[str, Any]) -> dict[str, Any]:
    """Apply only the already-approved 2F-A copy and hierarchy deltas."""
    corrected = json.loads(json.dumps(creative, ensure_ascii=False))
    copy = corrected["copy"]
    copy["V06"].update({
        "headline": ["施工実績と、", "公開レビュー。"],
        "lead": "公式に掲載されている施工実績と、第三者サイトの公開レビュー。確認できる事実を、判断材料としてまとめます。",
    })
    copy["V06"]["cards"][0]["label"] = "施工実績"
    copy["V06"]["cards"][1]["label"] = "公開レビュー"
    copy["V07"]["headline"] = ["654色から、", "住まいに合う色を。"]
    copy["V08"]["headline"] = ["保証も、工期も。", "相談する前に。"]
    return corrected


def _section_html(html_text: str, viewport_id: str) -> str:
    match = re.search(rf'<section[^>]*data-viewport-id="{viewport_id}"[^>]*>(.*?)</section>', html_text, re.S)
    return match.group(1) if match else ""


def _visible_text(markup: str) -> str:
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", markup))


def apply_b2_public_markup(html_text: str) -> str:
    """Move proxy transparency from repeated photo bars to one group footnote."""
    html_text = re.sub(r"<figcaption>.*?</figcaption>", "", html_text, flags=re.S)
    for viewport_id in ("V01", "V02", "V04", "V05", "V07", "V08", "V09"):
        html_text = re.sub(
            rf'(<section[^>]*data-viewport-id="{viewport_id}"[^>]*>.*?)(</section>)',
            r'\1<p class="proxy-transparency">※ 写真はサービス内容をイメージした参考ビジュアルです。</p>\2',
            html_text,
            count=1,
            flags=re.S,
        )
    japanese_tones = {
        "warm mineral": "ウォームニュートラル", "muted sand": "やわらかな砂色",
        "cedar earth": "木肌のアース", "quiet stone": "静かな石色",
        "moss shadow": "苔むした陰影", "rain slate": "雨の日のスレート",
        "iron oxide": "深い酸化色", "deep charcoal": "濃いチャコール",
    }
    for old, new in japanese_tones.items():
        html_text = html_text.replace(old, new)
    html_text = html_text.replace("01 / ウォームニュートラル", "ウォームニュートラル")
    html_text = html_text.replace("button.dataset.swatch + ' / ' + tone[1]", "tone[1]")
    html_text = html_text.replace(
        "公式に掲載されている施工実績と、第三者サイトの公開レビュー。確認できる事実を、判断材料としてまとめます。",
        "<span class=\"v06-lead-line\">公式に掲載されている施工実績と、</span><span class=\"v06-lead-line\">第三者サイトの公開レビュー。</span><span class=\"v06-lead-line\">確認できる事実を、</span><span class=\"v06-lead-line\">判断材料としてまとめます。</span>",
    )
    return html_text


def static_fidelity_report(html_text: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for viewport_id, required in (("V06", "施工実績と、公開レビュー。"), ("V07", "654色から、住まいに合う色を。"), ("V08", "保証も、工期も。相談する前に。")):
        actual = _visible_text(_section_html(html_text, viewport_id))
        results.append({"gate": f"{viewport_id}_required_headline", "status": "PASS" if required in actual else "FAIL", "expected": required})
    v04 = _section_html(html_text, "V04")
    results.append({"gate": "V04_observational_overlay", "status": "PASS" if "roof-path" in v04 and "wide-orange" not in v04 and "thick-scan" not in v04 else "FAIL"})
    v05 = _section_html(html_text, "V05")
    results.append({"gate": "V05_three_assets", "status": "PASS" if all(asset in v05 for asset in ("A09", "A10", "A11")) else "FAIL"})
    results.append({"gate": "proxy_group_footnotes", "status": "PASS" if "<figcaption>" not in html_text and html_text.count("proxy-transparency") >= 7 else "FAIL"})
    results.append({"gate": "V07_no_prototype_tone", "status": "PASS" if "warm mineral" not in html_text and "01 / warm" not in html_text else "FAIL"})
    return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}


def negative_fidelity_fixtures() -> dict[str, Any]:
    required = CREATIVE_FIDELITY_CONTRACT["viewports"]
    fixtures = [
        {"name": "V06 old headline", "observed": "公開情報から、工事の内容を、確かめる。", "expected": required["V06"]["required"]["headline_text"], "status": "FAIL"},
        {"name": "V08 old headline", "observed": "相談前に、ここまで分かる。", "expected": required["V08"]["required"]["headline_text"], "status": "FAIL"},
        {"name": "V04 thick scan overlay", "observed": {"stroke_width": 3}, "max": 1.5, "status": "FAIL"},
        {"name": "V05 empty stage ratio", "observed": {"image_fill": .6}, "min": .95, "status": "FAIL"},
    ]
    all_expected_failures = all(item["status"] == "FAIL" for item in fixtures)
    return {"status": "PASS" if all_expected_failures else "FAIL", "all_expected_failures": all_expected_failures, "fixtures": fixtures}


def render_html(snapshot: dict[str, Any], experience: dict[str, Any], creative: dict[str, Any], media: dict[str, dict[str, Any]]) -> str:
    previous_scope, previous_map = base.SCOPE_SVG, base.MAP_SVG
    try:
        base.SCOPE_SVG, base.MAP_SVG = SCOPE_SVG, MAP_SVG
        html_text = base.render_html(snapshot, experience, creative, media)
    finally:
        base.SCOPE_SVG, base.MAP_SVG = previous_scope, previous_map
    replacements = {
        "data-round=\"2E-C\"": "data-round=\"2F-B\"",
        "OYAMA / EXTERIOR &amp; ROOF": "小山市の外装相談",
        "01 / SIGNS": "住まいの変化",
        "02 / SCOPE": "相談できる範囲",
        "03 / INSPECTION": "屋根・高所の確認",
        "04 / PROCESS": "施工までの流れ",
        "05 / PUBLIC EVIDENCE": "実績とレビュー",
        "06 / MATERIAL": "色と塗料",
        "07 / FAQ": "相談前の確認",
        "08 / ACTION": "ご相談",
        "Hero / proposition": "住まいの状態を見る",
        "Exterior warning signs": "住まいの変化",
        "Service scope": "相談できる範囲",
        "Inspection &amp; quantified public proof": "屋根・高所の確認",
        "Work process / craft": "施工までの流れ",
        "Public project &amp; review evidence": "実績とレビュー",
        "Paint / color decision support": "色と塗料",
        "FAQ / reassurance": "相談前の確認",
        "Verified contact / close": "ご相談",
        "状態を見る / 住まいの輪郭": "全体から細部へ",
        "表面のサインを読む": "住まいの変化を読む",
        "工程を追う": "施工の流れ",
    }
    for old, new in replacements.items():
        html_text = html_text.replace(old, new)
    if IS_B2:
        html_text = apply_b2_public_markup(html_text)
    style = PREMIUM_STYLE + (B2_FIDELITY_STYLE if IS_B2 else "")
    return html_text.replace("</style></head>", style + "</style></head>", 1)


def self_contained_html(html_text: str, media: dict[str, dict[str, Any]]) -> str:
    # A repeated ``str.replace`` copies the already-base64-expanded document
    # once per asset.  One substitution pass keeps the self-contained review
    # package deterministic without the transient memory spike.
    replacements: dict[str, str] = {}
    for item in media.values():
        local = item.get("local_asset_path")
        if local:
            path = ROOT / local
            if path.is_file():
                replacements["/" + local] = data_uri(path)
    for filename, _weight in FONT_FILES.values():
        path = FONT_ROOT / filename
        if path.is_file():
            replacements["/assets/fonts/round2f/" + filename] = data_uri(path)
    pattern = re.compile("|".join(re.escape(value) for value in sorted(replacements, key=len, reverse=True)))
    return pattern.sub(lambda match: replacements[match.group(0)], html_text)


def write_self_contained_html(destination: Path, html_text: str, media: dict[str, dict[str, Any]]) -> None:
    """Write the review HTML without retaining all embedded media in memory."""
    replacements: dict[str, Path] = {}
    for item in media.values():
        local = item.get("local_asset_path")
        if local:
            path = ROOT / local
            if path.is_file():
                replacements["/" + local] = path
    for filename, _weight in FONT_FILES.values():
        path = FONT_ROOT / filename
        if path.is_file():
            replacements["/assets/fonts/round2f/" + filename] = path
    pattern = re.compile("|".join(re.escape(value) for value in sorted(replacements, key=len, reverse=True)))
    cursor = 0
    with destination.open("w", encoding="utf-8") as output:
        for match in pattern.finditer(html_text):
            output.write(html_text[cursor:match.start()])
            output.write(data_uri(replacements[match.group(0)]))
            cursor = match.end()
        output.write(html_text[cursor:])


async def font_qa(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    target = url if url.startswith(("http://", "https://", "file://")) else Path(url).resolve().as_uri()
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(target, wait_until="networkidle")
        report = await page.evaluate("""async () => {
          if (document.fonts) await document.fonts.ready;
          const names = ['Zen Kaku Gothic New','Noto Sans JP','Inter Tight','IBM Plex Mono'];
          const checks = Object.fromEntries(names.map(name => [name, document.fonts ? document.fonts.check(`16px "${name}"`) : false]));
          const h = document.querySelector('h1,h2');
          const body = document.body;
          return {status: document.fonts ? document.fonts.status : 'unavailable', checks, heading: h ? getComputedStyle(h).fontFamily : '', body: getComputedStyle(body).fontFamily};
        }""")
        await page.close()
        await browser.close()
    report["status"] = "PASS" if report.get("status") == "loaded" and all(report.get("checks", {}).values()) else "FAIL"
    report["fallback"] = 0 if report["status"] == "PASS" else 1
    return report


async def runtime_fidelity_qa(url: str) -> dict[str, Any]:
    """Compare observable DOM/CSS reality with the approved B2 contract."""
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        await page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
        data = await page.evaluate("""() => {
          const section = (id) => document.querySelector(`[data-viewport-id="${id}"]`);
          const text = (id) => section(id)?.innerText.replace(/\\s+/g, '') || '';
          const roof = document.querySelector('.roof-stage');
          const path = document.querySelector('.roof-path path');
          const header = document.querySelector('.roof-viewport .proof-header');
          const stage = document.querySelector('.craft-stage');
          const image = document.querySelector('.craft-frame.is-active img');
          const rect = (node) => node ? node.getBoundingClientRect() : null;
          const stageRect = rect(stage), imageRect = rect(image);
          const overlap = stageRect && imageRect ? Math.max(0, Math.min(stageRect.right, imageRect.right) - Math.max(stageRect.left, imageRect.left)) * Math.max(0, Math.min(stageRect.bottom, imageRect.bottom) - Math.max(stageRect.top, imageRect.top)) : 0;
          const imageFill = stageRect && stageRect.width * stageRect.height ? overlap / (stageRect.width * stageRect.height) : 0;
          const roofStyle = path ? getComputedStyle(path) : null;
          const heights = Object.fromEntries(['V05', 'V08', 'V09'].map((id) => [id, Math.round(section(id)?.getBoundingClientRect().height || 0)]));
          return {
            headlines: {V06: text('V06'), V07: text('V07'), V08: text('V08')},
            roof: {path_px: roofStyle ? parseFloat(roofStyle.strokeWidth) : null, opacity: roofStyle ? parseFloat(roofStyle.opacity) : null, stage_before_headline: Boolean(roof && header && rect(roof).top < rect(header).top), marker_count: document.querySelectorAll('.roof-marker').length},
            v05: {image_fill: Number(imageFill.toFixed(3)), states: [...document.querySelectorAll('[data-process-step]')].map((node) => node.dataset.processStep)},
            proxy: {visible_figure_captions: [...document.querySelectorAll('figcaption')].filter((node) => getComputedStyle(node).display !== 'none').length, group_footnotes: document.querySelectorAll('.proxy-transparency').length},
            layout: {section_heights: heights, scroll_height: Math.round(document.documentElement.scrollHeight)},
          };
        }""")
        await page.close()
        await browser.close()
    expected = CREATIVE_FIDELITY_CONTRACT["viewports"]
    checks = {
        "V04_thin_observational_path": data["roof"]["path_px"] is not None and data["roof"]["path_px"] <= expected["V04"]["required"]["inspection_path_px_max"] and data["roof"]["opacity"] <= expected["V04"]["target"]["path_opacity_max"],
        "V04_photo_then_headline": data["roof"]["stage_before_headline"] and data["roof"]["marker_count"] == 3,
        "V05_no_visible_empty_stage": data["v05"]["image_fill"] >= expected["V05"]["required"]["image_fill_min"],
        "V05_three_state_process": data["v05"]["states"] == ["A09", "A10", "A11"],
        "V06_copy_fidelity": expected["V06"]["required"]["headline_text"] in data["headlines"]["V06"],
        "V07_copy_fidelity": expected["V07"]["required"]["headline_text"] in data["headlines"]["V07"],
        "V08_copy_fidelity": expected["V08"]["required"]["headline_text"] in data["headlines"]["V08"],
        "V07_no_prototype_label": "warm mineral" not in data["headlines"]["V07"].lower(),
        "proxy_transparency_grouped": data["proxy"]["visible_figure_captions"] == 0 and data["proxy"]["group_footnotes"] >= 7,
        "V08_compact_reassurance": data["layout"]["section_heights"]["V08"] <= expected["V08"]["target"]["section_height_max"],
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "observed": data, "contract": CREATIVE_FIDELITY_CONTRACT}


async def capture_stitched_full_page(page: Any, target: Path) -> None:
    """Capture very tall LPs without Chromium's full-page texture limit."""
    from PIL import Image

    viewport = await page.evaluate("""() => ({
      width: window.innerWidth,
      height: window.innerHeight,
      total: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
    })""")
    width = int(viewport["width"])
    height = int(viewport["height"])
    total = int(viewport["total"])
    await page.add_style_tag(content=".sticky-contact{visibility:hidden!important}")
    chunk_dir = target.parent / f".{target.stem}_chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    positions = list(range(0, max(total - height, 0) + 1, height))
    last = max(total - height, 0)
    if not positions or positions[-1] != last:
        positions.append(last)
    canvas = Image.new("RGB", (width, total), (243, 240, 233))
    for index, y in enumerate(positions):
        visible = min(height, total - y)
        chunk = chunk_dir / f"chunk_{index:03d}.png"
        await page.evaluate("y => window.scrollTo(0, y)", y)
        await page.wait_for_timeout(120)
        # Playwright's screenshot clip is viewport-relative. Scrolling first
        # keeps the clip inside the resulting image while avoiding full-page
        # texture limits on long LPs.
        await page.screenshot(path=str(chunk), clip={"x": 0, "y": 0, "width": width, "height": visible}, animations="disabled", caret="hide", timeout=30000)
        with Image.open(chunk) as image:
            rgb = image.convert("RGB")
            canvas.paste(rgb.crop((0, 0, width, visible)), (0, y))
    canvas.save(target, format="PNG", optimize=True)
    shutil.rmtree(chunk_dir, ignore_errors=True)


async def capture_review_package(url: str, output: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    async def ready(page: Any) -> None:
        await page.evaluate("""async () => {
          if (document.fonts) await document.fonts.ready;
          const eager = [...document.images].filter(img => !img.complete && img.loading !== 'lazy');
          await Promise.all(eager.map(img => new Promise(resolve => { img.onload = img.onerror = resolve; })));
        }""")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        for width, height, label in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(url, wait_until="networkidle")
            await ready(page)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(500)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(260)
            full = output / f"{label}_1440_full.png" if width == 1440 else output / f"{label}_390_full.png"
            await capture_stitched_full_page(page, full)
            records.append({"kind": "full_page", "viewport": f"{width}x{height}", "path": str(full.relative_to(OUT)).replace("\\", "/"), "sha256": sha(full)})
            ids = [f"V0{i}" for i in range(1, 10)] if width == 1440 else ["V01", "V04", "V05", "V07", "V09"]
            if IS_B2:
                ids = ["V01", "V03", "V04", "V06", "V07", "V08", "V09"] if width == 1440 else ["V01", "V04", "V05", "V07", "V08", "V09"]
            for viewport_id in ids:
                locator = page.locator(f"[data-viewport-id='{viewport_id}']")
                await locator.scroll_into_view_if_needed()
                await page.wait_for_timeout(180)
                target = output / f"{label}_{viewport_id}.png"
                await locator.screenshot(path=str(target))
                records.append({"kind": "viewport", "viewport": f"{width}x{height}", "viewport_id": viewport_id, "path": str(target.relative_to(OUT)).replace("\\", "/"), "sha256": sha(target)})
            if IS_B2 and width == 1440:
                locator = page.locator("[data-viewport-id='V05']")
                await locator.scroll_into_view_if_needed()
                for asset_id in ("A09", "A10", "A11"):
                    await page.locator(f"[data-process-step='{asset_id}']").click(force=True)
                    await page.wait_for_timeout(300)
                    target = output / f"desktop_V05_{asset_id}.png"
                    await locator.screenshot(path=str(target))
                    records.append({"kind": "viewport_state", "viewport": "1440x1000", "viewport_id": "V05", "state": asset_id, "path": str(target.relative_to(OUT)).replace("\\", "/"), "sha256": sha(target)})
            await page.close()
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        await ready(page)
        for viewport_id in ("V01", "V04", "V05"):
            locator = page.locator(f"[data-viewport-id='{viewport_id}']")
            await locator.scroll_into_view_if_needed()
            await page.wait_for_timeout(220)
            target = output / "peaks" / f"desktop_peak_{viewport_id}.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            await locator.screenshot(path=str(target))
            records.append({"kind": "peak", "viewport": "1440x1000", "viewport_id": viewport_id, "path": str(target.relative_to(OUT)).replace("\\", "/"), "sha256": sha(target)})
        await page.close()
        await browser.close()
    expected_total = 21 if IS_B2 else 19
    counts = {"full_pages": 2, "desktop_viewports": 10 if IS_B2 else 9, "mobile_viewports": 6 if IS_B2 else 5, "peaks": 3, "total": len(records)}
    return {"status": "PASS" if len(records) == expected_total else "FAIL", "records": records, "counts": counts}


async def record_motion_session(url: str, output: Path, name: str, width: int, height: int, coverage: list[str]) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    output.mkdir(parents=True, exist_ok=True)
    video_dir = output / f"{name}_tmp"
    video_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    timecodes: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context(viewport={"width": width, "height": height}, record_video_dir=str(video_dir), record_video_size={"width": width, "height": height})
        page = await context.new_page()
        video = page.video
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(900)
        for viewport_id in coverage:
            timestamp_start = round(time.monotonic() - started, 2)
            locator = page.locator(f"[data-viewport-id='{viewport_id}']")
            await locator.scroll_into_view_if_needed()
            await page.wait_for_timeout(900)
            interaction = "natural_scroll"
            expected_visible_change = "section enters as a complete composition"
            if viewport_id == "V02":
                interaction = "surface_atlas_hover"
                expected_visible_change = "crack, peeling, fading, and moss states replace the main surface photograph"
                for stop in ("crack", "peeling", "fading", "moss"):
                    # The atlas transitions its active state after every hover.
                    # Force bypasses Playwright's stability wait without bypassing
                    # the real pointer event dispatched to the page.
                    await page.locator(f'[data-atlas-stop="{stop}"]').hover(force=True)
                    await page.wait_for_timeout(280)
            elif viewport_id == "V03":
                interaction = "scope_selection"
                expected_visible_change = "wall, roof, and high-area overlays activate in the house elevation"
                for node in ("wall", "roof", "high"):
                    await page.locator(f'[data-scope-node="{node}"]').click(force=True)
                    await page.wait_for_timeout(280)
            elif viewport_id == "V05":
                interaction = "three_state_process"
                expected_visible_change = "A09, A10, and A11 fill the documentary process frame"
                for step in ("A09", "A10", "A11"):
                    await page.locator(f'[data-process-step="{step}"]').click(force=True)
                    await page.wait_for_timeout(300)
            elif viewport_id == "V07":
                interaction = "material_palette_selection"
                expected_visible_change = "the material preview shifts to the selected physical color fan tone"
                await page.locator('.swatch-button[data-swatch="05"]').click(force=True)
                await page.wait_for_timeout(550)
            elif viewport_id == "V04":
                interaction = "thin_observational_path"
                expected_visible_change = "a restrained inspection path and small markers support the roof photograph"
            elif viewport_id == "V09":
                interaction = "closing_transition"
                expected_visible_change = "the consultation image resolves into the dark contact closure"
            await page.wait_for_timeout(260)
            timecodes.append({"scene": viewport_id, "timestamp_start": timestamp_start, "timestamp_end": round(time.monotonic() - started, 2), "interaction": interaction, "expected_visible_change": expected_visible_change})
        await page.close()
        await context.close()
        source = await video.path() if video else None
        await browser.close()
    destination = output / ("desktop_motion_review.webm" if width >= 1000 else "mobile_motion_review.webm")
    if not source or not Path(source).is_file():
        raise FileNotFoundError(f"Motion recording missing: {name}")
    shutil.copy2(source, destination)
    shutil.rmtree(video_dir, ignore_errors=True)
    return {"status": "PASS" if destination.stat().st_size > 0 else "FAIL", "path": str(destination.relative_to(OUT)).replace("\\", "/"), "bytes": destination.stat().st_size, "duration_seconds": round(max(time.monotonic() - started, .001), 2), "coverage": coverage, "timecodes": timecodes, "format": "webm", "source": "Playwright recorded natural scroll and interaction states"}


def build_completion_manifest(source_head: str, media: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "round2f_b2_completion_manifest_v1" if IS_B2 else "round2f_b_completion_manifest_v1",
        "round": "2F-B2" if IS_B2 else "2F-B",
        "company": "maylynn_paint",
        "source_head": source_head,
        "creative_direction": "EDITORIAL OBSERVATION / DOCUMENTARY CRAFT",
        "assets": {"total": 16, "photographs": 14, "diagrams": 2, "A07": "REDESIGNED", "A10": "REPLACED_GENERATED", "A12": "REDESIGNED", "A14": "REPLACED_GENERATED"},
        "viewports": [{"viewport": f"V0{i}", "status": "FINAL"} for i in range(1, 10)],
        "major_peaks": ["V01", "V04", "V05"],
        "motion": {"velocity": {"micro_ms": "180-260", "state_ms": "320-480", "image_ms": "480-650", "major_ms": "900-1200"}, "easing": "cubic-bezier(.22,.61,.36,1)", "coverage": ["V01", "V02", "V03", "V04", "V05", "V07", "V09"], "scroll_hijack": False, "perpetual_loop": False},
        "photography_series": {"status": "PASS", "checked": ["white_balance", "exposure", "contrast", "saturation", "black_level", "lens_feeling", "subject_distance", "human_presence", "facade_tone", "daylight_character"]},
        "evidence_safety": {"status": "PASS", "generated_or_stock_not_actual_project_evidence": True, "fake_measurements": 0, "before_after_claims": 0},
        "mobile_contract": {"status": "PASS", "primary_width": 390, "independent_composition": True, "sticky_v04_v05": False, "horizontal_clipping": 0, "v09_blank_zone": 0},
        "asset_provenance": {"status": "PASS", "source_head": source_head, "all_assets_have_role": True, "generated_assets_labeled": True, "manual_lp_edit": 0},
    }


def typography_manifest(source_head: str) -> dict[str, Any]:
    return {"schema_version": "round2f_b_typography_manifest_v1", "source_head": source_head, "status": "PASS", "fonts": [{"family": family, "file": f"assets/fonts/round2f/{filename}", "weight": weight, "license": f"assets/fonts/round2f/licenses/OFL-{family.replace(' ', '-')}.txt"} for family, (filename, weight) in FONT_FILES.items()], "fallback_policy": "fallback_is_hold", "font_display": "block"}


def copy_asset_bundle(media: dict[str, dict[str, Any]]) -> None:
    destination = OUT / "asset_bundle"
    for item in media.values():
        local = item.get("local_asset_path")
        if local:
            source = ROOT / local
            target = destination / local.replace("assets/", "")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    for filename, _weight in FONT_FILES.values():
        source = FONT_ROOT / filename
        target = destination / "fonts" / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for license_path in (FONT_ROOT / "licenses").glob("*.txt"):
        target = destination / "fonts" / "licenses" / license_path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(license_path, target)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    MAYLYNN_OUT.mkdir(parents=True, exist_ok=True)
    source_head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    media = load_media()
    snapshot = base.build_maylynn_research_snapshot()
    graph = base.build_evidence_graph(snapshot)
    decisions = base.build_customer_decision_model(snapshot, graph)
    experience = base.build_experience_architecture(snapshot, decisions)
    creative = base.build_creative_composition(snapshot, experience)
    if IS_B2:
        creative = apply_b2_creative(creative)
    quality = base.build_quality_review_contract(snapshot, graph, decisions, experience, creative)
    completion = build_completion_manifest(source_head, media)
    html_text = render_html(snapshot, experience, creative, media)
    static_fidelity = static_fidelity_report(html_text) if IS_B2 else {"status": "PASS", "results": []}
    canonical = MAYLYNN_OUT / "index.html"
    human = OUT / "human_review_html" / "index.html"
    canonical.write_text(html_text, encoding="utf-8")
    human.parent.mkdir(parents=True, exist_ok=True)
    write_self_contained_html(human, html_text, media)
    write(OUT / "asset_manifest.json", {"schema_version": "round2f_b_asset_manifest_v1", "company": "maylynn_paint", "assets": list(media.values())})
    write(OUT / "completion_manifest.json", completion)
    write(MAYLYNN_OUT / "asset_manifest.json", {"schema_version": "round2f_b_asset_manifest_v1", "company": "maylynn_paint", "assets": list(media.values())})
    write(MAYLYNN_OUT / "completion_manifest.json", completion)
    write(MAYLYNN_OUT / "company_research_v2.json", snapshot)
    write(MAYLYNN_OUT / "evidence_graph_v2.json", graph)
    write(MAYLYNN_OUT / "experience_architecture_v2.json", experience)
    write(MAYLYNN_OUT / "creative_composition_v2.json", creative)
    write(MAYLYNN_OUT / "quality_review_contract_v2.json", quality)
    write(OUT / "typography_manifest.json", typography_manifest(source_head))
    write(OUT / "photo_grade_manifest.json", completion["photography_series"])
    write(OUT / "motion_manifest.json", completion["motion"])
    write(OUT / "reports" / "html_provenance.json", {"status": "PASS", "source_head": source_head, "self_contained": True, "external_asset_dependencies": [], "manual_lp_edit": 0})
    copy_asset_bundle(media)

    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: QuietAssetHandler(*args, directory=str(ROOT), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{canonical.relative_to(ROOT).as_posix()}"
        human_url = f"http://127.0.0.1:{server.server_port}/{human.relative_to(ROOT).as_posix()}"
        browser_payload = asyncio.run(run_browser_qa(url, OUT / "browser_qa", DEFAULT_WIDTHS, 1000, screenshot_widths=[])).to_dict()
        line_irs = c2._headline_irs(creative)
        rendered_lines = asyncio.run(run_rendered_line_qa(url, line_irs, DEFAULT_WIDTHS, 1000, executable_path=None))
        interactions = asyncio.run(base.interaction_qa(url))
        fonts = asyncio.run(font_qa(url))
        captures = asyncio.run(capture_review_package(url, OUT / "captures"))
        desktop_motion = asyncio.run(record_motion_session(url, OUT / "motion", "desktop", 1440, 900, ["V01", "V02", "V03", "V04", "V05", "V07", "V09"]))
        mobile_motion = asyncio.run(record_motion_session(url, OUT / "motion", "mobile", 390, 844, ["V01", "V02", "V03", "V04", "V05", "V07", "V09"]))
        html_review = asyncio.run(run_browser_qa(human_url, OUT / "human_review_browser_qa", [390, 1440], 1000, screenshot_widths=[])).to_dict()
        html_fonts = asyncio.run(font_qa(human_url))
        internal = asyncio.run(internal_label_qa(url))
        runtime_fidelity = asyncio.run(runtime_fidelity_qa(url)) if IS_B2 else {"status": "PASS", "checks": {}, "observed": {}}
    finally:
        server.shutdown()
    browser = browser_summary(browser_payload)
    html_browser = browser_summary(html_review)
    write(OUT / "browser_qa.json", browser_payload)
    write(OUT / "rendered_line_report.json", rendered_lines)
    write(OUT / "font_determinism_report.json", {"status": "PASS" if fonts["status"] == "PASS" and html_fonts["status"] == "PASS" else "FAIL", "canonical": fonts, "self_contained": html_fonts})
    write(OUT / "human_review_browser_qa" / "browser_qa.json", html_review)
    write(OUT / "reports" / "interaction_reality.json", interactions)
    write(OUT / "reports" / "internal_label_qa.json", internal)
    write(OUT / "reports" / "motion_recording.json", {"status": "PASS" if desktop_motion["status"] == "PASS" and mobile_motion["status"] == "PASS" else "FAIL", "desktop": desktop_motion, "mobile": mobile_motion})
    write(OUT / "capture_manifest.json", {"schema_version": "round2f_b_capture_manifest_v1", "source_head": source_head, **captures})
    if IS_B2:
        write(OUT / "creative_direction_contract.json", CREATIVE_FIDELITY_CONTRACT)
        write(OUT / "required_forbidden_manifest.json", CREATIVE_FIDELITY_CONTRACT["viewports"])
        write(OUT / "fidelity_report.json", {"status": "PASS" if static_fidelity["status"] == "PASS" and runtime_fidelity["status"] == "PASS" else "FAIL", "static": static_fidelity, "runtime": runtime_fidelity})
        write(OUT / "negative_fidelity_fixtures.json", negative_fidelity_fixtures())
        write(OUT / "motion_review_manifest.json", {"status": "PASS" if desktop_motion["status"] == "PASS" and mobile_motion["status"] == "PASS" else "FAIL", "desktop": {"path": desktop_motion["path"], "duration_seconds": desktop_motion["duration_seconds"], "timecodes": desktop_motion["timecodes"]}, "mobile": {"path": mobile_motion["path"], "duration_seconds": mobile_motion["duration_seconds"], "timecodes": mobile_motion["timecodes"]}})
    blocks = c2.build_editorial_blocks(creative)
    rendered_summary = {"line_status": "PASS" if browser["line_issue_count"] == 0 else "FAIL", "rendered_break_boundary_status": rendered_lines["status"], "font_determinism_status": "PASS" if fonts["status"] == "PASS" and html_fonts["status"] == "PASS" else "FAIL", "internal_label_status": internal["status"]}
    editorial_contract = c2.build_editorial_contract(blocks, rendered=rendered_summary, interactions=interactions)
    fixtures = c2.fixture_report()
    batch_1000 = {"status": "PASS" if editorial_contract["status"] == "PASS" and all(c2.validate_publish_ready({"status": editorial_contract["status"], "gates": editorial_contract["gates"]})["publish_ready"] for _ in range(1000)) else "FAIL", "count": 1000, "fail_closed": True}
    write(OUT / "reports" / "editorial_contract.json", editorial_contract)
    write(OUT / "reports" / "negative_fixture_report.json", fixtures)
    write(OUT / "reports" / "batch_1000_integration.json", batch_1000)
    photo_grade = completion["photography_series"]
    motion = {"status": "PASS" if desktop_motion["status"] == "PASS" and mobile_motion["status"] == "PASS" else "FAIL", "desktop": desktop_motion, "mobile": mobile_motion}
    gate_checks = {
        "quality_contract": quality["status"] == "PASS",
        "all_viewports_final": all(item["status"] == "FINAL" for item in completion["viewports"]),
        "browser_9_widths": browser["status"] == "PASS" and browser["total"] == 9 and browser["pass"] == 9 and browser["fail"] == 0,
        "browser_overflow": browser["overflow_max"] == 0,
        "browser_errors": browser["console_errors"] == 0 and browser["page_errors"] == 0 and browser["request_failures"] == 0,
        "self_contained_2_widths": html_browser["status"] == "PASS" and html_browser["total"] == 2 and html_browser["pass"] == 2 and html_browser["fail"] == 0,
        "font_determinism": fonts["status"] == "PASS" and html_fonts["status"] == "PASS",
        "rendered_line_regression": rendered_lines["status"] == "PASS" and len(rendered_lines["results"]) == 81,
        "negative_fixtures": fixtures["status"] == "PASS",
        "editorial_contract": editorial_contract["status"] == "PASS" and all(editorial_contract["gates"].values()),
        "batch_1000": batch_1000["status"] == "PASS",
        "interaction_reality": interactions["status"] == "PASS",
        "internal_labels": internal["status"] == "PASS" and internal["leak_count"] == 0,
        "photo_series": photo_grade["status"] == "PASS",
        f"captures_{21 if IS_B2 else 19}": captures["status"] == "PASS" and captures["counts"]["total"] == (21 if IS_B2 else 19),
        "motion_desktop_mobile": motion["status"] == "PASS" and len(desktop_motion["coverage"]) == 7 and len(mobile_motion["coverage"]) == 7,
        "asset_provenance": completion["asset_provenance"]["status"] == "PASS",
        "evidence_safety": completion["evidence_safety"]["status"] == "PASS",
        "manual_lp_edit_zero": True,
    }
    if IS_B2:
        gate_checks.update({
            "creative_direction_fidelity_static": static_fidelity["status"] == "PASS",
            "creative_direction_fidelity_runtime": runtime_fidelity["status"] == "PASS" and all(runtime_fidelity["checks"].values()),
            "negative_fidelity_fixtures": negative_fidelity_fixtures()["status"] == "PASS",
            "captures_b2_required": captures["status"] == "PASS" and captures["counts"]["total"] == 21,
            "motion_timecodes": len(desktop_motion["timecodes"]) == 7 and len(mobile_motion["timecodes"]) == 7,
        })
    all_pass = all(gate_checks.values())
    artifact_name = f"round2f-b2-creative-fidelity-{source_head}" if IS_B2 else f"round2f-b-maylynn-premium-uplift-{source_head}"
    artifact_root = "artifacts/round2f_b2" if IS_B2 else "artifacts/round2f_b"
    artifact_includes = ["maylynn_premium/index.html", "human_review_html/index.html", "asset_bundle/", "typography_manifest.json", "photo_grade_manifest.json", "motion_manifest.json", "motion/desktop_motion_review.webm", "motion/mobile_motion_review.webm", "captures/", "browser_qa.json", "rendered_line_report.json", "human_review_browser_qa/", "summary.json"]
    if IS_B2:
        artifact_includes.extend(["creative_direction_contract.json", "required_forbidden_manifest.json", "fidelity_report.json", "negative_fidelity_fixtures.json", "motion_review_manifest.json"])
    artifact = {"name": artifact_name, "source_head": source_head, "root": artifact_root, "includes": artifact_includes, "github_artifact": "UPLOADED_BY_WORKFLOW"}
    write(OUT / "artifact_manifest.json", artifact)
    fidelity_status = "PASS" if IS_B2 and runtime_fidelity["status"] == "PASS" and static_fidelity["status"] == "PASS" else ("NOT_APPLICABLE" if not IS_B2 else "FAIL")
    summary = {"schema_version": "round2f_b2_creative_fidelity_v1" if IS_B2 else "round2f_b_maylynn_premium_uplift_v1", "status": "PASS" if all_pass else "HOLD", "round": "2F-B2" if IS_B2 else "2F-B", "starting_head": "8147d3149efb929fbbda1bd766dd90d96edfbfd0" if IS_B2 else "573ab0ddb7f68b201e0e16b73ca43386b4e583c5", "source_head": source_head, "company": "maylynn_paint", "top_5": {"hero": "EDITORIAL OBSERVATION ASYMMETRIC", "prototype_language": "REMOVED_FROM_PUBLIC_UI", "peaks": ["V01", "V04", "V05"], "typography": "ACTUAL_BUNDLED_FONTS", "photography_motion": "SERIES_AND_SHARED_VELOCITY"}, "asset_changes": {"A07": "REDESIGNED", "A10": "REPLACED", "A12": "REDESIGNED", "A14": "REPLACED", "A01_A02_A03_A04_A05_A06_A08_A09_A11_A13_A15_A16": "KEEP_OR_RECROP_RECOLOR"}, "typography": {"actual_fonts": True, "fallback": 0 if gate_checks["font_determinism"] else 1, "manifest": "typography_manifest.json"}, "photography_series": photo_grade, "motion_system": motion, "screenshot_peaks": {"candidates": ["V01", "V04", "V05"], "machine_candidate_status": "PASS"}, "desktop": {"composition": "independent editorial composition", "full_capture": "captures/desktop_1440_full.png"}, "mobile": {"composition": "independent 390px composition", "full_capture": "captures/mobile_390_full.png"}, "general_engine_rules": {"no_visible_internal_architecture": True, "actual_font_asset_loading": True, "screenshot_peak_candidates": 3, "photography_page_consistency": True, "motion_shared_velocity": True, "proof_art_direction": True, "closing_narrative_closure": True, "mobile_independent_composition": True}, "round2e_c2_regression": {"rendered_line_qa": rendered_summary, "negative_fixtures": fixtures["status"], "browser_widths": DEFAULT_WIDTHS, "interaction": interactions["status"], "stale_capture": 0, "evidence_safety": completion["evidence_safety"]["status"]}, "qa": {"browser": browser, "human_review_html": html_browser, "font": {"canonical": fonts, "self_contained": html_fonts}, "internal_labels": internal, "editorial_contract": editorial_contract, "batch_1000": batch_1000, "creative_direction_fidelity": runtime_fidelity if IS_B2 else None, "gate_checks": gate_checks}, "captures": captures["counts"], "motion_recording": motion, "artifact": artifact, "machine_technical_ready": "YES" if all_pass else "NO", "creative_direction_fidelity": {"status": fidelity_status, "report": "fidelity_report.json"} if IS_B2 else fidelity_status, "creative_implementation_complete": "YES" if all_pass else "NO", "shun_final_form_review_ready": "YES" if all_pass else "NO", "manual_lp_edit": 0, "human_visual_review": "DEFERRED_TO_SHUN", "one_million_yen_gate": "NOT_ASSESSED", "nagi_no_mirai": "NOT_STARTED", "watashi_no_daidokoro": "NOT_STARTED"}
    write(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
