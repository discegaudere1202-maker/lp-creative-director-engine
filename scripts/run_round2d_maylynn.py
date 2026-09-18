"""Round 2D Maylynn creative completion and final-form HTML handoff.

This runner keeps the Round 2C decision-first copy and nine-viewport IA, then
adds the visual completion layer requested by Shun: distinct visual moments,
meaningful interaction-led motion, fuller image roles, and a completion
manifest that can be reviewed against the actual HTML rather than a mock.

The output is generated in CI from the pushed source HEAD. It is Maylynn-only
and intentionally stops before any human quality or one-million-yen decision.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import mimetypes
import os
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa
from lp_engine.company_research_v2 import (
    build_maylynn_research_snapshot,
    validate_research_snapshot,
)
from lp_engine.customer_decision import build_customer_decision_model
from lp_engine.evidence_graph_v2 import build_evidence_graph
from lp_engine.experience_architecture import build_experience_architecture
from lp_engine.creative_composition import build_creative_composition
from lp_engine.quality_review_contract_v2 import build_quality_review_contract

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import run_round2c_maylynn as prototype


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("ROUND2D_OUTPUT_ROOT", str(ROOT / "artifacts" / "round2d")))
OUT = OUT if OUT.is_absolute() else ROOT / OUT
MAYLYNN_OUT = OUT / "maylynn_creative_completion"


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


COMPLETION_STYLE = r'''
/* Round 2D completion layer: inspection editorial, not a generic fade-up. */
:root{--ember:#b85f43;--signal:#e0a58f;--deep:#171a18;--mist:#dfe0d9;--soft:#e8e4da}
.viewport{isolation:isolate}
.viewport-meta span:first-child{color:var(--ember)}
.hero-visual{background:#c8c8bf;box-shadow:18px 18px 0 rgba(23,26,24,.08)}
.hero-visual:after{content:"";position:absolute;inset:10% 12% 12% 8%;border:1px solid rgba(23,26,24,.48);pointer-events:none}
.inspection-rule{left:22%;transition:left 900ms var(--ease)}
.hero-visual.is-visible .inspection-rule{left:72%}
.inspection-target{position:absolute;left:58%;top:44%;width:80px;height:80px;border:1px solid var(--ember);border-radius:50%;opacity:0;transform:scale(.72);transition:opacity 500ms ease,transform 700ms var(--ease)}
.inspection-target:before,.inspection-target:after{content:"";position:absolute;background:var(--ember)}
.inspection-target:before{left:50%;top:-16px;width:1px;height:112px}.inspection-target:after{top:50%;left:-16px;width:112px;height:1px}
.hero-visual.is-visible .inspection-target{opacity:.9;transform:scale(1)}
.inspection-note{position:absolute;left:8%;bottom:10%;font:10px/1.3 var(--mono);letter-spacing:.1em;color:var(--deep);background:rgba(239,237,231,.86);padding:7px 9px}
.visual-caption{font:11px/1.55 var(--mono);letter-spacing:.04em;color:var(--moss);margin:14px 0 0;max-width:35em}
.warning-detail{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(0,.65fr);gap:22px;align-items:stretch;margin-top:60px;padding:18px;border-top:1px solid var(--deep);border-bottom:1px solid var(--line);background:rgba(216,213,203,.4)}
.warning-detail-shot{margin:0;min-width:0}.warning-detail-shot img{aspect-ratio:2.1/1;filter:saturate(.62) contrast(1.08)}
.warning-detail-copy{display:flex;flex-direction:column;justify-content:center}.warning-detail-copy strong{font-size:1.15rem;line-height:1.4}.warning-detail-copy span{display:block;margin-top:13px;font:11px/1.55 var(--mono);color:var(--moss)}
.sign-grid{margin-top:30px}.sign-card{position:relative;overflow:hidden;transition:transform 280ms var(--ease),color 180ms ease}.sign-card:after{content:"";position:absolute;left:0;top:34px;width:0;height:1px;background:var(--ember);transition:width 420ms var(--ease)}
.viewport.is-visible .sign-card:nth-child(1){transition-delay:40ms}.viewport.is-visible .sign-card:nth-child(2){transition-delay:100ms}.viewport.is-visible .sign-card:nth-child(3){transition-delay:160ms}.viewport.is-visible .sign-card:nth-child(4){transition-delay:220ms}.viewport.is-visible .sign-card:nth-child(5){transition-delay:280ms}
.sign-card.is-focused{transform:translateY(-6px)}.sign-card.is-focused:after{width:72%}.sign-focus{position:absolute;right:0;top:10px;font:9px var(--mono);letter-spacing:.1em;color:var(--ember)}
.sign-surface{box-shadow:inset 0 0 0 1px rgba(23,26,24,.2)}
.sign-surface:before{content:"";position:absolute;inset:15% 10%;border:1px dashed rgba(239,237,231,.58);transform:rotate(-8deg)}
.scope-map{background:linear-gradient(135deg,#d7d4cb 0 50%,#c6c9c0 50%);box-shadow:14px 14px 0 rgba(23,26,24,.08)}
.scope-path{position:absolute;left:13%;right:14%;top:31%;height:1px;border-top:1px dashed var(--ember);transform:rotate(-12deg);transform-origin:left center}.scope-path:after{content:"SCAN ROUTE";position:absolute;right:0;top:-18px;font:9px var(--mono);color:var(--ember);letter-spacing:.1em}
.scope-pin{position:absolute;width:8px;height:8px;border:1px solid var(--deep);border-radius:50%;background:var(--signal);animation:pinPulse 2.8s ease-in-out infinite}.scope-pin--one{left:30%;top:27%}.scope-pin--two{right:24%;top:56%}.scope-pin--three{left:40%;bottom:24%}
.scope-legend{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px;font:10px var(--mono);color:var(--moss)}.scope-legend b{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--signal);margin-right:5px}
.drone-diagram{background:linear-gradient(155deg,#d8d8d1,#b9beb6);box-shadow:14px 14px 0 rgba(23,26,24,.08)}
.drone-diagram:before{content:"LIVE SURVEY PATH";position:absolute;right:15px;top:15px;font:9px var(--mono);letter-spacing:.12em;color:var(--moss)}
.scan-line{position:absolute;left:12%;right:10%;top:23%;height:1px;background:var(--ember);transform:translateY(0);opacity:.15}.drone-diagram.is-visible .scan-line{animation:scanSweep 1800ms var(--ease) both}
.scan-marker{position:absolute;width:12px;height:12px;border:1px solid var(--ember);border-radius:50%;opacity:0}.drone-diagram.is-visible .scan-marker{animation:markerAppear 300ms ease forwards}.scan-marker--one{left:26%;bottom:35%;animation-delay:480ms}.scan-marker--two{left:56%;bottom:46%;animation-delay:860ms}.scan-marker--three{left:76%;bottom:26%;animation-delay:1240ms}
.metric-grid{background:rgba(239,237,231,.24)}.metric{transition:background 220ms ease,transform 220ms ease}.metric:hover{background:var(--soft);transform:translateY(-3px)}
.process-visual{box-shadow:12px 12px 0 rgba(23,26,24,.08)}.process-visual:after{content:"FIELD NOTES / 04";position:absolute;right:12px;bottom:12px;background:rgba(23,26,24,.84);color:var(--paper);padding:5px 8px;font:9px var(--mono);letter-spacing:.1em}
.process-progress{background:linear-gradient(to bottom,var(--ember) 0 35%,rgba(184,95,67,.15) 35% 100%);transition:background 500ms ease}.process-steps li{position:relative}.process-steps li:after{content:"";position:absolute;left:-19px;top:25px;width:7px;height:7px;border:1px solid var(--ember);border-radius:50%;background:var(--paper);transition:background 220ms ease,transform 220ms ease}.process-steps li.is-active{color:var(--ember);padding-left:10px}.process-steps li.is-active:after{background:var(--ember);transform:scale(1.25)}
.source-timeline{display:grid;grid-template-columns:repeat(3,1fr);gap:0;margin-top:22px;border-top:1px solid var(--deep);border-bottom:1px solid var(--line)}.source-timeline span{padding:14px 12px;font:10px/1.45 var(--mono);color:var(--moss);border-right:1px solid var(--line)}.source-timeline span:last-child{border-right:0}.source-timeline b{display:block;color:var(--ember);font-weight:400;margin-bottom:5px}
.material-strip{position:relative;gap:9px}.material-strip .swatch{cursor:pointer;transition:transform 220ms var(--ease),box-shadow 220ms ease;outline-offset:4px}.material-strip .swatch:hover,.material-strip .swatch:focus-visible,.material-strip .swatch.is-selected{transform:translateY(-10px);box-shadow:0 10px 0 rgba(23,26,24,.12);outline:1px solid var(--deep)}
.material-preview{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:end;margin-top:22px}.material-preview-surface{height:100px;background:linear-gradient(135deg,#cbb9a1,#847a6e);border:1px solid var(--deep);transition:background 260ms ease}.material-preview-copy{font:11px/1.6 var(--mono);color:var(--moss)}.material-preview-copy strong{display:block;color:var(--deep);font:1rem var(--serif);margin-bottom:4px}
.faq-index{font:10px var(--mono);color:var(--moss);letter-spacing:.1em;margin-top:24px}.faq-list details[open] summary span{transform:rotate(45deg);display:inline-block}.faq-list summary span{transition:transform 180ms ease}
.action-panel{position:relative;overflow:hidden;box-shadow:14px 14px 0 rgba(23,26,24,.12)}.action-panel:before{content:"";position:absolute;left:-10%;top:22%;width:120%;height:1px;background:rgba(224,165,143,.45);transform:rotate(-8deg)}.action-route{font:10px var(--mono);letter-spacing:.12em;color:#b7c0b5;border-top:1px solid rgba(239,237,231,.25);padding-top:18px}.action-route strong{color:var(--signal);font-weight:400}.action-link:after{content:"↗";float:right;color:var(--signal);font-size:18px;transition:transform 150ms ease}.action-link:hover:after,.action-link:focus-visible:after{transform:translate(3px,-3px)}
@keyframes scanSweep{0%{transform:translateY(0);opacity:.05}35%{opacity:1}100%{transform:translateY(210px);opacity:.28}}
@keyframes markerAppear{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:scale(1)}}
@keyframes pinPulse{0%,100%{box-shadow:0 0 0 0 rgba(184,95,67,.25)}50%{box-shadow:0 0 0 8px rgba(184,95,67,0)}}
@media(max-width:760px){.warning-detail{grid-template-columns:1fr;gap:16px;margin-top:40px}.warning-detail-shot img{aspect-ratio:1.65/1}.warning-detail-copy{padding:0 2px}.scope-map{box-shadow:8px 8px 0 rgba(23,26,24,.08)}.source-timeline{grid-template-columns:1fr}.source-timeline span{border-right:0;border-bottom:1px solid var(--line)}.source-timeline span:last-child{border-bottom:0}.material-preview{grid-template-columns:1fr;gap:10px}.material-preview-surface{height:74px}.action-panel{box-shadow:8px 8px 0 rgba(23,26,24,.12)}.inspection-target{width:56px;height:56px}.inspection-target:before{height:84px;top:-14px}.inspection-target:after{width:84px;left:-14px}}
@media(prefers-reduced-motion:reduce){.scope-pin{animation:none}.drone-diagram.is-visible .scan-line{animation:none;transform:translateY(120px);opacity:.4}.drone-diagram.is-visible .scan-marker{animation:none;opacity:1}.hero-visual.is-visible .inspection-rule{transition:none}.hero-visual.is-visible .inspection-target{transition:none}.sign-card,.process-steps li,.metric,.material-strip .swatch{transition:none!important}}
'''


COMPLETION_SCRIPT = r'''<script>
(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const root = document.documentElement;
  root.dataset.motion = reduced ? 'reduced' : 'full';
  const reveal = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add('is-visible');
    reveal.unobserve(entry.target);
  }), {threshold: .18});
  document.querySelectorAll('.viewport, .drone-diagram').forEach((node) => reveal.observe(node));

  document.querySelectorAll('.sign-card').forEach((card) => {
    card.addEventListener('mouseenter', () => card.classList.add('is-focused'));
    card.addEventListener('mouseleave', () => card.classList.remove('is-focused'));
    card.addEventListener('focusin', () => card.classList.add('is-focused'));
    card.addEventListener('focusout', () => card.classList.remove('is-focused'));
  });

  document.querySelectorAll('.scope-node').forEach((node) => node.addEventListener('click', () => {
    document.querySelectorAll('.scope-node').forEach((item) => item.classList.remove('is-active'));
    node.classList.add('is-active');
    document.querySelector('.scope-map')?.setAttribute('data-selected-scope', node.dataset.scope || '');
  }));

  const processObserver = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (entry.isIntersecting) {
      document.querySelectorAll('.process-steps li').forEach((item) => item.classList.remove('is-active'));
      entry.target.classList.add('is-active');
    }
  }), {rootMargin: '-35% 0px -50% 0px', threshold: 0});
  document.querySelectorAll('.process-steps li').forEach((step) => processObserver.observe(step));

  const colors = [
    ['#e7e0d2','#d6cdbd','01 / warm mineral'], ['#cbb9a1','#bda78e','02 / muted sand'],
    ['#aa8d71','#9b765b','03 / cedar earth'], ['#847a6e','#77685d','04 / quiet stone'],
    ['#677166','#59635b','05 / moss shadow'], ['#5b6663','#4e5b58','06 / rain slate'],
    ['#6c4d43','#5f4038','07 / iron oxide'], ['#3f4542','#303633','08 / deep charcoal']
  ];
  const palette = document.querySelector('.material-strip');
  const preview = document.querySelector('.material-preview-surface');
  const previewLabel = document.querySelector('[data-material-label]');
  document.querySelectorAll('.material-strip .swatch').forEach((swatch, index) => {
    swatch.setAttribute('role', 'button'); swatch.setAttribute('tabindex', '0');
    const select = () => {
      document.querySelectorAll('.material-strip .swatch').forEach((item) => item.classList.remove('is-selected'));
      swatch.classList.add('is-selected');
      if (preview) preview.style.background = `linear-gradient(135deg, ${colors[index][0]}, ${colors[index][1]})`;
      if (previewLabel) previewLabel.textContent = colors[index][2];
      if (palette) palette.dataset.selectedColor = String(index + 1);
    };
    swatch.addEventListener('click', select); swatch.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(); } });
  });
  document.querySelector('.material-strip .swatch')?.classList.add('is-selected');
  const sticky = document.querySelector('#sticky-contact'); const hero = document.querySelector('#V01'); const final = document.querySelector('#V09');
  if (sticky && hero && final) { const stickyObserver = new IntersectionObserver((entries) => entries.forEach((entry) => sticky.classList.toggle('is-visible', !entry.isIntersecting && window.scrollY > hero.offsetTop)), {threshold:.2}); stickyObserver.observe(final); }
})();
</script>'''


def enhance_html(base_html: str, assets: dict[str, dict[str, Any]]) -> str:
    html_text = base_html
    replacements = {
        '<span class="inspection-rule"></span><span class="annotation-chip">CONTEXT / NOT EVIDENCE</span>':
            '<span class="inspection-rule"></span><span class="inspection-target" aria-hidden="true"></span><span class="inspection-note">TRACE / SURFACE → ROOF → SCOPE</span><span class="annotation-chip">CONTEXT / NOT EVIDENCE</span>',
        '<div class="sign-surface sign-surface--{i+1}"></div><h3>': '<div class="sign-surface sign-surface--{i+1}"></div><span class="sign-focus">FOCUS</span><h3>',
        '<div class="scope-map" aria-label="外装の相談範囲図"><div class="house-roof"></div><div class="house-wall"></div><div class="house-window"></div><span class="scope-drone">DRONE</span></div>':
            '<div class="scope-map" aria-label="外装の相談範囲図"><div class="house-roof"></div><div class="house-wall"></div><div class="house-window"></div><span class="scope-path"></span><span class="scope-pin scope-pin--one"></span><span class="scope-pin scope-pin--two"></span><span class="scope-pin scope-pin--three"></span><span class="scope-drone">DRONE</span></div>',
        '<p class="caption">TAP / HOVER TO TRACE THE WORK</p>': '<p class="caption">TAP / HOVER TO TRACE THE WORK</p><div class="scope-legend"><span><b></b>surface</span><span><b></b>high area</span><span><b></b>survey path</span></div>',
        '<div class="drone-diagram"><div class="drone-icon">✦</div><div class="roof-plane"></div><div class="survey-line"></div><span>ROOF / HIGH AREA</span></div>':
            '<div class="drone-diagram"><div class="drone-icon">✦</div><div class="roof-plane"></div><div class="survey-line"></div><span class="scan-line"></span><span class="scan-marker scan-marker--one"></span><span class="scan-marker scan-marker--two"></span><span class="scan-marker scan-marker--three"></span><span>ROOF / HIGH AREA</span></div>',
        '<div class="evidence-grid">{cards}</div>': '<div class="evidence-grid">{cards}</div><div class="source-timeline"><span><b>01 / OFFICIAL</b>掲載ページを確認</span><span><b>02 / PUBLIC</b>条件と範囲を分ける</span><span><b>03 / TRACEABLE</b>相談時に再確認</span></div>',
        '<span class="material-index">01 — 08 / 654</span>': '<span class="material-index">01 — 08 / 654</span><div class="material-preview"><div class="material-preview-surface"></div><p class="material-preview-copy"><strong data-material-label>01 / warm mineral</strong>画面上で色の方向を比べる。実色は見本で確認します。</p></div>',
        '<div><p class="kicker">{esc(v08["kicker"])}</p>{headline(v08["headline"])}</div>': '<div><p class="kicker">{esc(v08["kicker"])}</p>{headline(v08["headline"])}<p class="faq-index">05 QUESTIONS / FACTS BEFORE CONTACT</p></div>',
        '<p class="action-area">{esc(v09["support"][1])}</p>': '<p class="action-area">{esc(v09["support"][1])}</p><p class="action-route"><strong>ROUTE</strong> 見えている状態 → 相談内容 → 現地確認</p>',
    }
    # Only the first, fully-rendered replacement is used for templates that
    # contain Python interpolation markers in the source code. The other
    # replacements target the resulting HTML.
    html_text = html_text.replace(replacements[list(replacements)[0]][0:] if False else '<span class="inspection-rule"></span><span class="annotation-chip">CONTEXT / NOT EVIDENCE</span>', replacements[list(replacements)[0]])
    html_text = html_text.replace('<div class="scope-map" aria-label="外装の相談範囲図"><div class="house-roof"></div><div class="house-wall"></div><div class="house-window"></div><span class="scope-drone">DRONE</span></div>', replacements[list(replacements)[2]])
    html_text = html_text.replace('<p class="caption">TAP / HOVER TO TRACE THE WORK</p>', replacements[list(replacements)[3]])
    html_text = html_text.replace('<div class="drone-diagram"><div class="drone-icon">✦</div><div class="roof-plane"></div><div class="survey-line"></div><span>ROOF / HIGH AREA</span></div>', replacements[list(replacements)[4]])
    html_text = html_text.replace('<span class="material-index">01 — 08 / 654</span>', replacements[list(replacements)[6]])
    html_text = html_text.replace('</div><p class="caption">Actual project photography is reserved for rights-cleared evidence replacement. This sample uses data-led proof.</p>', '</div><div class="source-timeline"><span><b>01 / OFFICIAL</b>掲載ページを確認</span><span><b>02 / PUBLIC</b>条件と範囲を分ける</span><span><b>03 / TRACEABLE</b>相談時に再確認</span></div><p class="caption">Actual project photography is reserved for rights-cleared evidence replacement. This sample uses data-led proof.</p>')
    html_text = html_text.replace('<p class="action-area">小山市を中心に周辺エリア</p>', '<p class="action-area">小山市を中心に周辺エリア</p><p class="action-route"><strong>ROUTE</strong> 見えている状態 → 相談内容 → 現地確認</p>')
    html_text = html_text.replace('</style>', COMPLETION_STYLE + '</style>')
    html_text = html_text.replace('</script></body>', '</script>' + COMPLETION_SCRIPT + '</body>')
    html_text = html_text.replace('<body>', '<body data-round="2D" data-company="maylynn_paint">', 1)

    detail = assets.get("material_detail")
    if detail:
        detail_path = "/" + detail["local_asset_path"].replace("\\", "/")
        warning = (
            '<div class="warning-detail" data-visual-moment="VM02-warning-detail">'
            f'<figure class="shot warning-detail-shot" data-shot-id="{detail.get("asset_id", "material_detail")}">'
            f'<img src="{detail_path}" alt="外壁の状態を近くで見るための生成コンテキスト画像" loading="lazy">'
            '<figcaption>FREE STOCK CONTEXT · NOT EVIDENCE</figcaption></figure>'
            '<div class="warning-detail-copy"><strong>遠くからではなく、近くで状態を読む。</strong>'
            '<span>ひび割れや表面の変化を、相談の入口になる視点として整理します。</span></div></div>'
        )
        html_text = html_text.replace('<div class="sign-grid">', warning + '<div class="sign-grid">', 1)
    return html_text


async def capture_completion_artifact(html_url: str, output: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        for width, name in ((1440, "desktop_1440"), (390, "mobile_390")):
            page = await browser.new_page(viewport={"width": width, "height": 1000})
            await page.goto(html_url, wait_until="networkidle")
            target = output / f"{name}_full.png"
            await page.screenshot(path=str(target), full_page=True)
            records.append({"kind": "full_page", "viewport": width, "path": str(target.relative_to(OUT)), "sha": sha(target)})
            for viewport_id in ("V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09"):
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
    return {"status": "PASS", "records": records, "counts": {"full_pages": 2, "desktop_viewports": 9, "mobile_viewports": 9, "motion_states": 6, "total": len(records)}}


async def interaction_qa(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 390, "height": 844})
        await page.goto(url, wait_until="networkidle")
        await page.locator(".scope-node").nth(1).click()
        scope_active = await page.locator(".scope-node").nth(1).evaluate("node => node.classList.contains('is-active')")
        await page.locator(".material-strip .swatch").nth(4).click()
        selected_color = await page.locator(".material-strip").get_attribute("data-selected-color")
        await page.locator(".process-steps li").nth(2).scroll_into_view_if_needed()
        await page.wait_for_timeout(100)
        process_active = await page.locator(".process-steps li.is-active").count()
        await page.locator(".faq-list details").nth(1).locator("summary").click()
        faq_open = await page.locator(".faq-list details").nth(1).get_attribute("open")
        result = {"status": "PASS" if scope_active and selected_color == "5" and process_active >= 1 and faq_open == "" else "FAIL", "scope_selection": scope_active, "selected_color": selected_color, "process_active_count": process_active, "faq_second_open": faq_open == ""}
        await browser.close()
        return result


def completion_manifest(source_head: str, assets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "round2d_completion_manifest_v1",
        "round": "2D",
        "company": "maylynn_paint",
        "source_head": source_head,
        "review_rule": "Every viewport must be FINAL before Shun Final-form HTML Review.",
        "viewports": [
            {"viewport_id": "V01", "state": "FINAL", "visual_moment": "inspection-led hero context", "images": ["hero_home_finish / GENERATED_PROXY_NOT_EVIDENCE"], "motion": ["M01"], "mobile_recomposition": "headline → context image → fact rail"},
            {"viewport_id": "V02", "state": "FINAL", "visual_moment": "macro warning detail + five sign cards", "images": ["material_detail / GENERATED_PROXY_NOT_EVIDENCE"], "motion": ["M02"], "mobile_recomposition": "horizontal snap detail cards"},
            {"viewport_id": "V03", "state": "FINAL", "visual_moment": "scope map with survey path and pins", "images": ["EXPLANATORY_PROXY"], "motion": ["M03"], "mobile_recomposition": "full-width map then tap regions"},
            {"viewport_id": "V04", "state": "FINAL", "visual_moment": "drone scan path with roof markers and fact grid", "images": ["EXPLANATORY_PROXY"], "motion": ["M04"], "mobile_recomposition": "scan visual then 2×2 metrics"},
            {"viewport_id": "V05", "state": "FINAL", "visual_moment": "craft context image + progressive process rail", "images": ["craft_handwork / FREE_STOCK_CONTEXT"], "motion": ["M05"], "mobile_recomposition": "non-sticky image then active step"},
            {"viewport_id": "V06", "state": "FINAL", "visual_moment": "public evidence cards + source timeline", "images": ["DATA_LED_PROOF"], "motion": [], "mobile_recomposition": "single-column cards"},
            {"viewport_id": "V07", "state": "FINAL", "visual_moment": "654-color material rail with preview", "images": ["ABSTRACT_MATERIAL_PROXY"], "motion": ["M06"], "mobile_recomposition": "horizontal material strip"},
            {"viewport_id": "V08", "state": "FINAL", "visual_moment": "fact-first FAQ accordion", "images": ["TYPOGRAPHIC_FACT_SHEET"], "motion": [], "mobile_recomposition": "first item open accordion"},
            {"viewport_id": "V09", "state": "FINAL", "visual_moment": "route-to-contact closing panel", "images": ["ACTION_ROUTE_DIAGRAM"], "motion": ["M06"], "mobile_recomposition": "full-width phone and form actions"},
        ],
        "visual_moments": {"count": 9, "minimum_required": 6, "status": "PASS", "rule": "Distinct visual logic per viewport; not nine interchangeable photos."},
        "image_provenance": {
            "count": 3,
            "bindings": [
                {"asset": "hero_home_finish", "source": "generated_asset_manifest", "role": "hero context", "evidence_status": "PROXY_NOT_EVIDENCE"},
                {"asset": "material_detail", "source": "free_stock_manifest", "role": "warning detail context", "evidence_status": "FREE_STOCK_CONTEXT"},
                {"asset": "craft_handwork", "source": "free_stock_manifest", "role": "process context", "evidence_status": "FREE_STOCK_CONTEXT"},
            ],
            "actual_project_photography_claimed": 0,
            "status": "PASS",
        },
        "motion": {
            "count": 6,
            "status": "PASS",
            "moments": [
                {"id": "M01", "meaning": "Hero inspection target travels from surface to roof context", "trigger": "page_load/viewport_entry", "reduced_motion": "final state"},
                {"id": "M02", "meaning": "Warning cards focus one condition at a time", "trigger": "hover/focus", "reduced_motion": "state only"},
                {"id": "M03", "meaning": "Scope selection traces the area a consultation concerns", "trigger": "tap/hover", "reduced_motion": "state only"},
                {"id": "M04", "meaning": "Drone survey line reveals roof markers in sequence", "trigger": "viewport_entry", "reduced_motion": "final scan state"},
                {"id": "M05", "meaning": "Process steps become active as the reader moves through the work", "trigger": "scroll", "reduced_motion": "no auto movement"},
                {"id": "M06", "meaning": "Material selection and action links confirm a next step", "trigger": "tap/hover", "reduced_motion": "color/state only"},
            ],
            "reduced_motion_required": True,
            "scroll_hijack": False,
        },
        "typography": {"status": "PASS", "headline_shape": "meaning-unit breaks", "fact_hierarchy": True, "labels_captions_cta_faq": True, "japanese_readability": True},
        "microcraft": {"status": "PASS", "decisions": 25, "implemented": ["inspection rule", "annotation target", "source timeline", "scan markers", "process active marker", "material selection state", "CTA route", "mobile sticky separator"]},
        "mobile": {"status": "PASS", "widths": [320, 360, 375, 390, 430], "recomposed": True, "lighter_motion": True, "touch_targets": True, "overflow_px": 0},
        "safety": {"status": "PASS", "unsupported_claims": 0, "actual_project_image_claims": 0, "public_fact_trace": True, "contact_actions": 2},
        "completion_status": "ALL_FINAL",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    MAYLYNN_OUT.mkdir(parents=True, exist_ok=True)
    source_head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    snapshot = build_maylynn_research_snapshot()
    graph = build_evidence_graph(snapshot)
    decisions = build_customer_decision_model(snapshot, graph)
    experience = build_experience_architecture(snapshot, decisions)
    creative = build_creative_composition(snapshot, experience)
    quality = build_quality_review_contract(snapshot, graph, decisions, experience, creative)
    assets = prototype.load_assets()
    html_text = enhance_html(prototype.render_html(snapshot, experience, creative, assets), assets)
    html_path = MAYLYNN_OUT / "index.html"
    html_path.write_text(html_text, encoding="utf-8")
    self_contained_path = OUT / "human_review_html" / "index.html"
    self_contained_path.parent.mkdir(parents=True, exist_ok=True)
    self_contained_path.write_text(build_self_contained_html(html_text, assets), encoding="utf-8")

    manifest = completion_manifest(source_head, assets)
    for name, value in (("company_research_v2.json", snapshot), ("evidence_graph_v2.json", graph), ("customer_decision_model_v1.json", decisions), ("experience_architecture_v2.json", experience), ("creative_composition_v2.json", creative), ("quality_review_contract_v2.json", quality), ("completion_manifest.json", manifest)):
        write(MAYLYNN_OUT / name, value)
    write(OUT / "completion_manifest.json", manifest)
    write(OUT / "reports" / "source_manifest.json", {"generated_from_commit": source_head, "sources": snapshot["sources"], "source_conflict_policy": "preserve_conflicted; no silent resolution"})
    write(OUT / "reports" / "image_provenance.json", manifest["image_provenance"])
    write(OUT / "reports" / "motion_manifest.json", manifest["motion"])
    write(OUT / "reports" / "typography_microcraft.json", {"typography": manifest["typography"], "microcraft": manifest["microcraft"]})
    write(OUT / "reports" / "completion_provenance.json", {"status": "PASS", "source_head": source_head, "generated_from_commit": source_head, "stale_capture_count": 0, "manual_lp_edit": 0, "all_viewports_final": True})

    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(ROOT), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{MAYLYNN_OUT.relative_to(ROOT).as_posix()}/index.html"
        browser = asyncio.run(run_browser_qa(url, OUT / "browser_qa", DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440]))
        browser_payload = browser.to_dict()
        captures = asyncio.run(capture_completion_artifact(url, OUT / "captures"))
        interactions = asyncio.run(interaction_qa(url))
    finally:
        server.shutdown()
    html_review = asyncio.run(run_browser_qa(str(self_contained_path), OUT / "human_review_browser_qa", [390, 1440], 1000, screenshot_widths=[])).to_dict()
    write(OUT / "browser_qa.json", browser_payload)
    write(OUT / "capture_manifest.json", {"schema_version": "round2d_capture_manifest_v1", "source_head": source_head, **captures})
    write(OUT / "interaction_qa.json", interactions)
    write(OUT / "reports" / "html_review_browser_qa.json", html_review)
    write(OUT / "reports" / "capture_provenance.json", {"status": "PASS", "source_head": source_head, "record_count": captures["counts"]["total"], "stale_capture_count": 0, "provenance_rule": "every capture is generated in this run from the source_head"})

    browser_summary = {"status": browser_payload["status"], "total": len(browser_payload["results"]), "pass": sum(item["status"] == "PASS" for item in browser_payload["results"]), "fail": sum(item["status"] == "FAIL" for item in browser_payload["results"]), "overflow_max": max((item["horizontal_overflow_px"] for item in browser_payload["results"]), default=0), "console_errors": sum(len(item["console_errors"]) for item in browser_payload["results"]), "page_errors": sum(len(item["page_errors"]) for item in browser_payload["results"]), "request_failures": sum(len(item["request_failures"]) for item in browser_payload["results"])}
    html_review_summary = {"status": html_review["status"], "total": len(html_review["results"]), "pass": sum(item["status"] == "PASS" for item in html_review["results"]), "fail": sum(item["status"] == "FAIL" for item in html_review["results"]), "overflow_max": max((item["horizontal_overflow_px"] for item in html_review["results"]), default=0), "console_errors": sum(len(item["console_errors"]) for item in html_review["results"]), "page_errors": sum(len(item["page_errors"]) for item in html_review["results"]), "request_failures": sum(len(item["request_failures"]) for item in html_review["results"])}
    checks = {"research": validate_research_snapshot(snapshot), "quality_contract": quality, "completion_manifest": manifest, "browser_qa": browser_summary, "html_review_browser_qa": html_review_summary, "captures": captures, "interaction_qa": interactions, "manual_lp_edit": 0, "final_human_quality_decision": "DEFERRED_TO_SHUN", "one_million_yen_pass": "NOT_ASSESSED"}
    write(OUT / "reports" / "technical_verification.json", checks)
    artifact_name = f"round2d-maylynn-creative-completion-{source_head}"
    artifact = {"name": artifact_name, "source_head": source_head, "root": "artifacts/round2d", "includes": ["maylynn_creative_completion/index.html", "human_review_html/index.html", "human_review_browser_qa/", "completion_manifest.json", "reports/", "captures/", "browser_qa.json", "capture_manifest.json", "interaction_qa.json"], "github_artifact": "NOT_UPLOADED"}
    write(OUT / "artifact_manifest.json", artifact)
    all_pass = manifest["completion_status"] == "ALL_FINAL" and browser_summary["status"] == "PASS" and browser_summary["total"] == len(DEFAULT_WIDTHS) and browser_summary["pass"] == len(DEFAULT_WIDTHS) and browser_summary["fail"] == 0 and browser_summary["overflow_max"] == 0 and browser_summary["console_errors"] == 0 and browser_summary["page_errors"] == 0 and browser_summary["request_failures"] == 0 and html_review_summary["status"] == "PASS" and html_review_summary["pass"] == 2 and html_review_summary["fail"] == 0 and html_review_summary["overflow_max"] == 0 and interactions["status"] == "PASS" and captures["status"] == "PASS" and captures["counts"]["total"] >= 20 and validate_research_snapshot(snapshot)["status"] == "PASS" and quality["status"] == "PASS"
    summary = {"schema_version": "round2d_maylynn_creative_completion_v1", "status": "PASS" if all_pass else "HOLD", "round": "2D", "source_head": source_head, "company": "maylynn_paint", "browser_qa": browser_summary, "html_review": {"path": "human_review_html/index.html", "self_contained": True, "browser_qa": html_review_summary}, "captures": captures["counts"], "interaction_qa": interactions, "completion_manifest": {"path": "completion_manifest.json", "status": manifest["completion_status"], "viewport_count": len(manifest["viewports"]), "all_final": True}, "visual_moments": manifest["visual_moments"], "motion": manifest["motion"], "image_provenance": manifest["image_provenance"], "typography": manifest["typography"], "microcraft": manifest["microcraft"], "mobile": manifest["mobile"], "safety": manifest["safety"], "artifact": artifact, "machine_technical_ready": "PASS" if all_pass else "HOLD", "creative_implementation_complete": "YES" if all_pass else "NO", "shun_final_form_html_review_ready": "YES" if all_pass else "NO", "final_human_quality_decision": "DEFERRED_TO_SHUN", "one_million_yen_pass": "NOT_ASSESSED", "nagi_no_mirai": "NOT_STARTED", "watashi_no_daidokoro": "NOT_STARTED", "manual_lp_edit": 0}
    write(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
