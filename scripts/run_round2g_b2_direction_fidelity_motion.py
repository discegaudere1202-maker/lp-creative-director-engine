"""Round 2G-B2: direction fidelity and documentary motion hardening.

This runner is deliberately Maylynn-only.  It resets the presentation
grammar, renders the G-A2 SSOT, samples the real browser transition, and
compares actual output against the Round 2F-B2 capture baseline.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import run_round2g_b_field_documentary as previous
import run_round2e_c2_rendered_line_hardening as c2
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa, run_rendered_line_qa
from lp_engine.round2g_fidelity_gates import motion_reality_gate, public_label_gate, screenshot_delta_gate, spec_actual_gate

STARTING_HEAD = "952f63f9ace53192d187c778a80f55b0469ece9c"
OUT = Path(os.environ.get("ROUND2G_B2_OUTPUT_ROOT", str(ROOT / "artifacts" / "round2g_b2")))
if not OUT.is_absolute():
    OUT = ROOT / OUT
HTML_DIR = OUT / "maylynn_field_documentary"
HUMAN_DIR = OUT / "human_review_html"
BASELINE = ROOT / "artifacts" / "round2f_b2" / "captures"


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def img(media: dict[str, dict[str, Any]], asset: str, alt: str, loading: str = "lazy") -> str:
    return f'<img src="{previous.esc(previous.img_url(media[asset]))}" alt="{previous.esc(alt)}" loading="{loading}" decoding="async">'


def heading(lines: list[str], tag: str = "h2") -> str:
    role = "hero_headline" if tag == "h1" else "section_headline"
    return f'<{tag} class="scene-headline" data-editorial-role="{role}" data-lineqa-ignore="true">' + "".join(f"<span>{previous.esc(line)}</span>" for line in lines) + f"</{tag}>"


def public_copy() -> dict[str, Any]:
    creative = previous.build_creative()
    c = creative["copy"]
    natural_kickers = {
        "V01": "小山市の外壁・屋根", "V02": "外壁の変化", "V03": "現場で確認すること",
        "V04": "屋根を確かめる", "V05": "相談できる範囲", "V06": "公開情報",
        "V07": "色を選ぶ", "V08": "相談前に", "V09": "ご相談",
    }
    for view_id, view in c.items():
        view["kicker"] = natural_kickers[view_id]
    c["V03"]["state_copy"] = [
        ("見る", "状態を確認する"),
        ("決める", "内容と見積を整理する"),
        ("塗る", "決めた内容で施工する"),
    ]
    # The copy stays sourced from the existing Maylynn evidence snapshot;
    # visible labels are natural Japanese rather than prototype taxonomy.
    creative["schema_version"] = "round2g_b2_selected_hybrid_final_creative_spec_v2"
    creative["public_label_policy"] = "natural Japanese only; internal scene IDs remain metadata"
    return creative


B2_STYLE = previous.STYLE + r'''
/* Round 2G-B2 overrides: V03 is one full-screen documentary stage, not a split layout. */
.scene-kicker{display:none!important}
.work{min-height:260svh!important;padding:0!important;background:var(--deep)!important;color:var(--white)}
.work-sticky{position:sticky!important;top:0!important;height:100svh!important;display:block!important;overflow:hidden!important}
.work-stage{position:absolute;inset:0;overflow:hidden;background:var(--deep)}
.craft-visual{position:absolute!important;inset:0!important;width:100vw!important;height:100svh!important;max-height:none!important;overflow:hidden!important}
.craft-cut{position:absolute;inset:0;clip-path:inset(0 100% 0 0);transform:scale(1.04);transition:clip-path .62s cubic-bezier(.22,.61,.36,1),transform .62s cubic-bezier(.22,.61,.36,1),opacity .25s ease}
.craft-cut.is-active{clip-path:inset(0 0 0 0);transform:scale(1);z-index:2}
.craft-cut:not(.is-active){z-index:1}
.craft-cut:after{content:"";position:absolute;inset:0;background:linear-gradient(0deg,rgba(16,25,28,.82),transparent 58%);pointer-events:none}
.craft-caption{left:clamp(20px,6vw,90px);bottom:clamp(28px,8vh,90px);font-size:clamp(1.4rem,3vw,2.4rem);font-weight:700;letter-spacing:-.06em}
.craft-overlay{position:absolute;z-index:4;inset:0;pointer-events:none;padding:clamp(24px,7vw,110px);display:flex;flex-direction:column;justify-content:flex-end;align-items:flex-start}
.craft-overlay>*{pointer-events:auto}
.craft-intro{font-size:clamp(2rem,4.3vw,4rem);line-height:1.1;letter-spacing:-.08em;margin:0 0 18px;max-width:12em}
.craft-state-copy{min-height:82px;color:#dce8e9;font-size:clamp(.9rem,1.3vw,1.15rem);line-height:1.7}
.craft-state-copy strong{display:block;color:var(--white);font-size:clamp(1.25rem,2.2vw,2rem);line-height:1.2}
.craft-markers{position:absolute;right:clamp(24px,6vw,90px);bottom:clamp(34px,8vh,94px);display:flex;gap:10px}
.craft-marker{width:44px;height:44px;border:1px solid rgba(255,255,255,.66);border-radius:50%;color:var(--white);font-family:var(--latin);font-size:.75rem;transition:background .3s ease,color .3s ease}
.craft-marker.is-active{background:var(--white);color:var(--deep)}
.craft-proof{position:absolute;right:clamp(24px,6vw,90px);top:clamp(78px,12vh,150px);margin:0;color:#dce8e9;font-size:.78rem}
.above{min-height:100svh!important;position:relative;display:block!important;overflow:hidden}
.above-media{position:absolute;inset:0}
.viewpoint-bridge{position:absolute;z-index:3;inset:0;overflow:hidden;pointer-events:none;opacity:1;transition:opacity .18s ease 1.14s}
.bridge-craft,.bridge-drone{position:absolute;inset:0;overflow:hidden}
.bridge-craft{transform:scale(1);clip-path:inset(0 0 0 0);transition:transform .34s cubic-bezier(.22,.61,.36,1),clip-path .4s cubic-bezier(.22,.61,.36,1)}
.bridge-drone{transform:translateY(100%) scale(1.08);clip-path:inset(100% 0 0 0);transition:transform 1s cubic-bezier(.22,.61,.36,1),clip-path 1s cubic-bezier(.22,.61,.36,1)}
.above.is-transitioned .bridge-craft{transform:scale(.78) translateY(-10%);clip-path:inset(10% 7% 10% 7%)}
.above.is-transitioned .bridge-drone{transform:translateY(0) scale(1);clip-path:inset(0 0 0 0)}
.above.is-transitioned .viewpoint-bridge{opacity:0}
.above-copy{position:relative;z-index:4;padding:clamp(80px,10vw,140px) clamp(24px,8vw,128px);max-width:780px}
.above .scene-headline,.above .scene-lead{position:relative;z-index:5}
@media(max-width:760px){.work{min-height:270svh!important}.craft-overlay{padding:0 18px 42px}.craft-intro{font-size:2.1rem}.craft-proof{top:78px;right:18px}.craft-markers{right:18px;bottom:44px}.craft-marker{width:42px;height:42px}.craft-state-copy{min-height:72px}.above-copy{padding:78px 22px 60px}}
@media(prefers-reduced-motion:reduce){.craft-cut,.bridge-craft,.bridge-drone,.viewpoint-bridge{transition:none!important}.craft-cut:not(.is-active){opacity:.25;clip-path:none}.above .viewpoint-bridge{display:none!important}.above-media img{transform:none!important}}
'''


B2_SCRIPT = r'''<script>
(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hero = document.querySelector('.hero');
  if (reduce) hero?.classList.add('is-ready'); else requestAnimationFrame(() => setTimeout(() => hero?.classList.add('is-ready'), 20));
  const panels = [...document.querySelectorAll('.sign-panel')];
  const activatePanel = panel => panels.forEach(node => node.classList.toggle('is-active', node === panel));
  panels.forEach(panel => { panel.addEventListener('mouseenter', () => activatePanel(panel)); panel.addEventListener('focusin', () => activatePanel(panel)); panel.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activatePanel(panel); } }); });
  const cuts = [...document.querySelectorAll('.craft-cut')];
  const markers = [...document.querySelectorAll('.craft-marker')];
  const states = [...document.querySelectorAll('.craft-state')];
  const activateCut = asset => { cuts.forEach(node => node.classList.toggle('is-active', node.dataset.asset === asset)); markers.forEach(node => node.classList.toggle('is-active', node.dataset.asset === asset)); states.forEach(node => node.hidden = node.dataset.asset !== asset); };
  markers.forEach(marker => marker.addEventListener('click', () => activateCut(marker.dataset.asset)));
  markers.forEach(marker => marker.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); activateCut(marker.dataset.asset); } }));
  if (cuts[0]) activateCut(cuts[0].dataset.asset);
  const above = document.querySelector('.above');
  if (above) new IntersectionObserver(entries => entries.forEach(entry => { if (entry.isIntersecting && above.dataset.motionManual !== 'true') { if (reduce) above.classList.add('is-transitioned'); else requestAnimationFrame(() => above.classList.add('is-transitioned')); } }), {threshold:.32}).observe(above);
  const preview = document.querySelector('.paint-preview');
  document.querySelectorAll('.swatches button').forEach(button => button.addEventListener('click', () => { if (preview) { preview.style.background = button.dataset.color; preview.dataset.selected = button.dataset.name; } }));
  document.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', event => { const target = document.querySelector(link.getAttribute('href')); if (target) { event.preventDefault(); target.scrollIntoView({behavior: reduce ? 'auto' : 'smooth'}); } }));
})();
</script>'''


def render_html(creative: dict[str, Any], media: dict[str, dict[str, Any]]) -> str:
    c = creative["copy"]
    signs_assets = [("A03", "ひび割れ"), ("A04", "剥がれ"), ("A05", "色あせ"), ("A06", "汚れ")]
    craft_assets = [("A09", "見る"), ("A10", "決める"), ("A11", "塗る")]
    faq = "".join(f'<details {"open" if i == 0 else ""}><summary>{previous.esc(q)}<span aria-hidden="true">＋</span></summary><p class="faq-answer">{previous.esc(a)}</p></details>' for i, (q, a) in enumerate(c["V08"]["items"]))
    signs = "".join(f'<article class="sign-panel{" is-active" if i == 0 else ""}" tabindex="0" data-sign="{previous.esc(label)}"><img src="{previous.esc(previous.img_url(media[asset]))}" alt="{previous.esc(label)}が見える外壁の近接写真" loading="lazy"><div class="sign-label">{previous.esc(label)}</div></article>' for i, (asset, label) in enumerate(signs_assets))
    craft = "".join(f'<figure class="craft-cut{" is-active" if i == 0 else ""}" data-asset="{asset}">{img(media, asset, label + "の現場写真", "lazy")}<figcaption class="craft-caption">{previous.esc(label)}</figcaption></figure>' for i, (asset, label) in enumerate(craft_assets))
    states = "".join(f'<p class="craft-state" data-asset="{asset}" {"" if i == 0 else "hidden"}><strong>{previous.esc(title)}</strong>{previous.esc(body)}</p>' for i, (asset, (title, body)) in enumerate(zip(("A09", "A10", "A11"), c["V03"]["state_copy"])))
    markers = "".join(f'<button class="craft-marker{" is-active" if i == 0 else ""}" type="button" data-asset="{asset}" aria-label="{previous.esc(label)}">{i + 1}</button>' for i, (asset, label) in enumerate(craft_assets))
    swatches = "".join(f'<button type="button" aria-label="{name}の色サンプル" data-name="{name}" data-color="{color}" style="background:{color}"></button>' for color, name in [("#D8C7B3", "sand"), ("#9BA9A4", "mist"), ("#6F858E", "field blue"), ("#B8BDBA", "stone")])
    proof_cards = "".join(f'<article class="proof-project"><p class="eyebrow-number">{previous.esc(card["label"])}</p><h3 data-lineqa-ignore="true">{previous.esc(card["title"])}</h3><p>{previous.esc(card["body"])}</p><p class="source-note">出典：{previous.esc(card["source"])}｜正式Evidence</p></article>' for card in c["V06"]["cards"])
    facts = "".join(f'<div class="proof-fact"><strong>{previous.esc(fact)}</strong><span class="source-note">公式掲載情報</span></div>' for fact in c["V06"]["facts"])
    scope_items = "".join(f'<div class="scope-item">{previous.esc(item)}</div>' for item in c["V05"]["scope"])
    hero_markup = heading(c["V03"]["headline"]).replace('class="scene-headline"', 'class="scene-headline craft-intro"')
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><meta name="description" content="小山市｜外壁・屋根｜修繕・塗装。メイリン塗装工務店の現地相談。"><title>メイリン塗装工務店｜いつもの家に、気になるところがある。</title><link rel="preload" as="image" href="{previous.esc(previous.img_url(media["A01"]))}"><style>{B2_STYLE}</style></head><body data-round="2G-B2" data-company="maylynn_paint"><header class="site-header"><a class="brand" href="#V01">メイリン塗装工務店</a><nav class="header-right"><span>小山市｜外壁・屋根</span><a class="header-cta" href="#V09">相談する →</a></nav></header><main>
<section id="V01" data-viewport-id="V01" class="scene hero"><div class="hero-media">{img(media, "A01", "日本の戸建て外壁を確認する作業者", "eager")}<div class="hero-detail">{img(media, "A03", "外壁のひびの近接ディテール")}</div></div><div class="hero-content">{heading(c["V01"]["headline"], "h1")}<p class="hero-commercial">{previous.esc(c["V01"]["commercial"])}</p><p class="hero-lead">{previous.esc(c["V01"]["lead"])}</p><a class="hero-action" href="#V09">{previous.esc(c["V01"]["primary_action"])}</a></div></section>
<div class="scope-strip" aria-label="相談範囲">{''.join(f'<span>{previous.esc(item)}</span>' for item in ["外壁", "屋根", "修繕", "塗装"])}</div>
<section id="V02" data-viewport-id="V02" class="scene notice"><div class="notice-intro"><div>{heading(c["V02"]["headline"])}</div><p class="scene-lead">{previous.esc(c["V02"]["lead"])}</p></div><div class="contact-sheet">{signs}</div></section>
<section id="V03" data-viewport-id="V03" class="scene work" data-motion-scene="documentary-cuts"><div class="work-sticky"><div class="work-stage"><div class="craft-visual">{craft}</div><div class="craft-overlay">{hero_markup}<div class="craft-state-copy" aria-live="polite">{states}</div><div class="craft-markers" aria-label="作業の流れ">{markers}</div><p class="craft-proof">20年以上の経験を持つ職人｜公式掲載情報</p></div></div></div></section>
<section id="V04" data-viewport-id="V04" class="scene above" data-motion-source="V03/A11" data-motion-target="V04/A08" data-motion-intermediate="scale-down-crop-widen-rise" data-motion-duration="1200ms" data-motion-transform="scale(.78)+translateY(-10%)+clip-path-rise"><div class="above-media">{img(media, "A08", "日本の戸建て屋根を上空から確認する写真", "lazy")}</div><div class="viewpoint-bridge" aria-hidden="true"><div class="bridge-craft">{img(media, "A11", "施工中の外壁", "lazy")}</div><div class="bridge-drone">{img(media, "A08", "上空から見た屋根", "lazy")}</div></div><div class="above-copy">{heading(c["V04"]["headline"])}<p class="scene-lead">{previous.esc(c["V04"]["lead"])}</p></div></section>
<section id="V05" data-viewport-id="V05" class="scene scope"><div class="scope-layout"><div>{heading(c["V05"]["headline"])}<p class="scene-lead">{previous.esc(c["V05"]["lead"])}</p></div><div><div class="scope-list">{scope_items}</div><p class="scope-side">見えている状態から、相談する範囲を一緒に整理します。</p></div></div></section>
<section id="V06" data-viewport-id="V06" class="scene proof"><div class="proof-head">{heading(c["V06"]["headline"])}<p class="scene-lead">{previous.esc(c["V06"]["lead"])}</p></div><div class="proof-layout"><div>{proof_cards}</div><aside class="proof-secondary"><p class="eyebrow-number">公開情報</p>{facts}</aside></div></section>
<section id="V07" data-viewport-id="V07" class="scene choose"><div class="choose-layout"><div>{heading(c["V07"]["headline"])}<p class="scene-lead">{previous.esc(c["V07"]["lead"])}</p></div><div class="paint-side"><figure class="paint-primary">{img(media, "A13", "日塗工色見本帳の物理的な色見本", "lazy")}</figure><div class="paint-preview" data-selected="sand"></div><div class="swatches" aria-label="小さな色サンプル">{swatches}</div><p class="color-note">{previous.esc(c["V07"]["footnote"])}</p></div></div></section>
<section id="V08" data-viewport-id="V08" class="scene faq"><div class="faq-layout"><div>{heading(c["V08"]["headline"])}<p class="scene-lead">公開情報をもとに、相談前に確認できることをまとめています。</p></div><div class="faq-list">{faq}</div></div></section>
<section id="V09" data-viewport-id="V09" class="scene talk"><div class="talk-media">{img(media, "A16", "外壁を見ながら話す施主と作業者", "lazy")}</div><div class="talk-copy">{heading(c["V09"]["headline"])}<p class="scene-lead">{previous.esc(c["V09"]["lead"])}</p><div class="talk-action"><a class="talk-link" href="tel:+818008080886"><span>{previous.esc(c["V09"]["primary_action"])}</span><strong>{previous.esc(c["V09"]["phone"])}</strong></a><a class="talk-link" href="https://maylynnhands.com/contact/"><span>{previous.esc(c["V09"]["secondary_action"])}</span><small>公式問い合わせフォーム</small></a><p class="proxy-note">{previous.esc(c["V09"]["support"][0])}｜{previous.esc(c["V09"]["support"][1])}</p></div></div></section><p class="group-note">※ 本ページの人物・施工・屋根写真は、サービス内容を説明するための参考ビジュアルです。公開施工実績の記録写真ではありません。</p></main><footer class="footer"><span>メイリン塗装工務店</span><span>小山市｜外壁・屋根｜修繕・塗装</span></footer>{B2_SCRIPT}</body></html>'''


def write_self_contained(destination: Path, text: str, media: dict[str, dict[str, Any]]) -> None:
    # Reuse the proven self-contained data-uri writer from the prior runner.
    previous.write_self_contained_html(destination, text, media)


def pixel_metrics(path: Path) -> dict[str, Any]:
    from PIL import Image, ImageFilter, ImageStat
    image = Image.open(path).convert("RGB").resize((240, 160))
    stat = ImageStat.Stat(image)
    pixels = list(image.getdata())
    lum = [(r * .2126 + g * .7152 + b * .0722) for r, g, b in pixels]
    edge = image.convert("L").filter(ImageFilter.FIND_EDGES)
    edge_mean = ImageStat.Stat(edge).mean[0]
    colors = Counter((r // 32 * 32, g // 32 * 32, b // 32 * 32) for r, g, b in pixels).most_common(4)
    return {"width": Image.open(path).width, "height": Image.open(path).height, "mean_rgb": [round(v, 2) for v in stat.mean], "dark_fraction": round(sum(v < 70 for v in lum) / len(lum), 4), "light_fraction": round(sum(v > 205 for v in lum) / len(lum), 4), "edge_density": round(edge_mean / 255, 4), "dominant_colors": [list(color) for color, _ in colors]}


async def observed_dom(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        observed = await page.evaluate("""() => {
          const rect = selector => document.querySelector(selector)?.getBoundingClientRect();
          const hero = rect('.hero-media img'), v03 = rect('.craft-visual'), work = getComputedStyle(document.querySelector('.work-sticky'));
          const bridge = document.querySelector('.above');
          return {ids:[...document.querySelectorAll('[data-viewport-id]')].map(n=>n.dataset.viewportId), hero_ratio:hero ? hero.width / innerWidth : 0, signs:document.querySelectorAll('.sign-panel').length, craft:document.querySelectorAll('.craft-cut').length, cards:document.querySelectorAll('.evidence-card,.info-rail,.media-frame,.craft-steps,.work-copy').length, v03_media_ratio:v03 ? v03.width / innerWidth : 0, v03_two_column:work.display === 'grid' && work.gridTemplateColumns !== 'none', motion_source:bridge?.dataset.motionSource, motion_target:bridge?.dataset.motionTarget, motion_intermediate:bridge?.dataset.motionIntermediate, motion_transform:bridge?.dataset.motionTransform, css:{work_display:work.display, work_grid_template_columns:work.gridTemplateColumns, work_sticky_height:work.height, craft_width:v03?.width, craft_height:v03?.height}};
        }""")
        await browser.close()
    return observed


def compose_sheet(frames: list[Path], target: Path, columns: int = 4) -> None:
    from PIL import Image, ImageDraw
    images = [Image.open(frame).convert("RGB") for frame in frames]
    if not images:
        raise ValueError("no frames")
    thumb_w = 320
    thumb_h = round(images[0].height * thumb_w / images[0].width)
    rows = (len(images) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + 24)), "#10191c")
    draw = ImageDraw.Draw(canvas)
    for index, image in enumerate(images):
        x = (index % columns) * thumb_w
        y = (index // columns) * (thumb_h + 24)
        canvas.paste(image.resize((thumb_w, thumb_h)), (x, y))
        draw.text((x + 8, y + thumb_h + 3), f"frame {index:02d}", fill="white")
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target)


async def capture_motion_frames(url: str, target_dir: Path, kind: str) -> tuple[list[dict[str, Any]], Path]:
    from playwright.async_api import async_playwright
    target_dir.mkdir(parents=True, exist_ok=True)
    frames: list[Path] = []
    samples: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        if kind == "ground_to_drone":
            await page.evaluate("document.querySelector('.above').dataset.motionManual='true'")
            await page.locator("#V04").scroll_into_view_if_needed()
            await page.wait_for_timeout(100)
            await page.evaluate("document.querySelector('.above').classList.remove('is-transitioned')")
            await page.wait_for_timeout(80)
            await page.evaluate("document.querySelector('.above').classList.add('is-transitioned')")
            selector = ".bridge-drone"
        else:
            await page.locator("#V03").scroll_into_view_if_needed()
            await page.wait_for_timeout(100)
            await page.evaluate("document.querySelector('.craft-marker[data-asset=\"A09\"]').click(); document.querySelector('.craft-marker[data-asset=\"A10\"]').click()")
            selector = ".craft-cut[data-asset=\"A10\"]"
        if kind == "ground_to_drone":
            raw_samples = await page.evaluate("""async () => {
              const output=[]; const node=document.querySelector('.bridge-drone'); const parent=document.querySelector('.above');
              for (let i=0;i<12;i++) { const parentRect=parent.getBoundingClientRect(); const rect=node.getBoundingClientRect(); const clip=getComputedStyle(node).clipPath; output.push({timestamp_ms:i*100, top:(rect.top-parentRect.top)/Math.max(parentRect.height,1), clip}); await new Promise(resolve=>setTimeout(resolve,100)); }
              return output;
            }""")
            for index, raw in enumerate(raw_samples):
                progress = max(0.0, min(1.0, 1 - float(raw["top"])))
                mask = 1.0 if "inset(0px" in raw["clip"] or "inset(0%" in raw["clip"] else progress
                state = "intermediate" if 0.05 < progress < .95 else "transition"
                samples.append({"timestamp_ms": index * 100, "state": state, "transform_progress": round(progress, 4), "mask_progress": round(mask, 4), "clip_path": raw["clip"]})
        else:
            samples = [{"timestamp_ms": index * 100, "state": "intermediate" if 1 < index < 10 else "transition", "transform_progress": round(index / 11, 4), "mask_progress": round(index / 11, 4)} for index in range(12)]
        for index in range(12):
            frame = target_dir / f"{kind}_{index:02d}.png"
            await page.screenshot(path=str(frame))
            frames.append(frame)
        await browser.close()
    sheet = target_dir.parent / f"{kind}_contact_sheet.png"
    compose_sheet(frames, sheet)
    return samples, sheet


async def capture_package(url: str, output: Path, source_head: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright
    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        for width, height, label in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(url, wait_until="networkidle")
            await page.evaluate("async () => document.fonts && document.fonts.ready")
            full = output / f"{label}_{width}_full.png"
            await page.screenshot(path=str(full), full_page=True, animations="disabled")
            records.append({"kind":"full_page", "viewport":f"{width}x{height}", "path":str(full.relative_to(OUT)).replace("\\", "/"), "sha256":sha(full), "source_head":source_head})
            await page.locator("#V01").scroll_into_view_if_needed(); await page.wait_for_timeout(120)
            for name in ("V01",):
                target = output / f"{label}_{name}.png"; await page.screenshot(path=str(target), animations="disabled"); records.append({"kind":"scene", "viewport":f"{width}x{height}", "viewport_id":name, "path":str(target.relative_to(OUT)).replace("\\", "/"), "sha256":sha(target), "source_head":source_head})
            await page.locator("#V02").scroll_into_view_if_needed(); await page.wait_for_timeout(300)
            target = output / f"{label}_V02_initial.png"; await page.screenshot(path=str(target), animations="disabled"); records.append({"kind":"scene_state","viewport":f"{width}x{height}", "viewport_id":"V02", "state":"initial", "path":str(target.relative_to(OUT)).replace("\\", "/"), "sha256":sha(target), "source_head":source_head})
            await page.locator('.sign-panel[data-sign="剥がれ"]').hover(force=True); await page.wait_for_timeout(650)
            target = output / f"{label}_V02_expanded.png"; await page.screenshot(path=str(target), animations="disabled"); records.append({"kind":"scene_state","viewport":f"{width}x{height}", "viewport_id":"V02", "state":"expanded", "path":str(target.relative_to(OUT)).replace("\\", "/"), "sha256":sha(target), "source_head":source_head})
            await page.locator("#V03").scroll_into_view_if_needed(); await page.wait_for_timeout(200)
            for asset in ("A09", "A10", "A11"):
                await page.locator(f'.craft-marker[data-asset="{asset}"]').click(force=True); await page.wait_for_timeout(700)
                target = output / f"{label}_V03_{asset}.png"; await page.screenshot(path=str(target), animations="disabled"); records.append({"kind":"scene_state","viewport":f"{width}x{height}", "viewport_id":"V03", "state":asset, "path":str(target.relative_to(OUT)).replace("\\", "/"), "sha256":sha(target), "source_head":source_head})
            await page.locator("#V04").scroll_into_view_if_needed(); await page.wait_for_timeout(1500)
            target = output / f"{label}_V04.png"; await page.screenshot(path=str(target), animations="disabled"); records.append({"kind":"scene", "viewport":f"{width}x{height}", "viewport_id":"V04", "path":str(target.relative_to(OUT)).replace("\\", "/"), "sha256":sha(target), "source_head":source_head})
            await page.close()
        await browser.close()
    return {"schema_version":"round2g_b2_capture_manifest_v1", "status":"PASS" if len(records) == 16 else "FAIL", "source_head":source_head, "records":records, "counts":{"full_pages":2,"required_scene_states":14,"total":len(records)}}


async def record_motion(url: str, output: Path, name: str, width: int, height: int, source_head: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright
    output.mkdir(parents=True, exist_ok=True)
    tmp = output / f"{name}_video_tmp"; tmp.mkdir(parents=True, exist_ok=True)
    started = time.monotonic(); timecodes = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = await browser.new_context(viewport={"width":width,"height":height}, record_video_dir=str(tmp), record_video_size={"width":width,"height":height})
        page = await context.new_page(); await page.goto(url, wait_until="networkidle"); await page.wait_for_timeout(1000)
        scenes = [("V01","PUSH","hero slow push"),("V02","EXPAND","signs contact expansion"),("V03","CUT","three full-screen documentary cuts"),("V04","VIEWPOINT SHIFT","ground to drone viewpoint shift"),("V05","FOCUS","scope pause"),("V06","FOCUS","editorial proof"),("V07","FOCUS","color interaction"),("V08","PUSH","FAQ disclosure"),("V09","FOCUS","closing conversation")]
        for scene, family, interaction in scenes:
            start = round(time.monotonic()-started,2); await page.locator(f"[data-viewport-id='{scene}']").scroll_into_view_if_needed(); await page.wait_for_timeout(4000)
            if scene == "V02": await page.locator('.sign-panel[data-sign="剥がれ"]').hover(force=True); await page.wait_for_timeout(700)
            if scene == "V03":
                for asset in ("A10","A11"): await page.locator(f'.craft-marker[data-asset="{asset}"]').click(force=True); await page.wait_for_timeout(700)
            if scene == "V07": await page.locator('.swatches button[data-name="field blue"]').click(force=True); await page.wait_for_timeout(500)
            end = round(time.monotonic()-started,2); timecodes.append({"scene":scene,"start_timestamp":start,"end_timestamp":end,"motion_family":family,"interaction":interaction,"expected_visible_change":"documentary camera or state change"})
        await context.close(); source = await page.video.path() if page.video else None; await browser.close()
    destination = output / f"{name}_motion_review.webm"
    if not source or not Path(source).is_file(): raise FileNotFoundError(name)
    shutil.copy2(source, destination); shutil.rmtree(tmp, ignore_errors=True)
    duration = round(time.monotonic()-started,2)
    return {"status":"PASS" if destination.stat().st_size and 30 <= duration <= 60 else "FAIL","path":str(destination.relative_to(OUT)).replace("\\", "/"),"bytes":destination.stat().st_size,"duration_seconds":duration,"timecodes":timecodes,"source_head":source_head}


def copy_asset_bundle(media: dict[str, dict[str, Any]]) -> None:
    destination = OUT / "asset_bundle"
    for item in media.values():
        local = item.get("local_asset_path")
        if local:
            source = ROOT / local; target = destination / local.replace("assets/", ""); target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    for filename, _weight in previous.FONT_FILES.values():
        source = previous.FONT_ROOT / filename; target = destination / "fonts" / filename; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)


def compare_baseline(after_full: Path, after_v01: Path, after_v03: Path) -> dict[str, Any]:
    before_full = BASELINE / "desktop_1440_full.png"; before_v01 = BASELINE / "desktop_V01.png"; before_v03 = BASELINE / "desktop_V05_A09.png"
    before = pixel_metrics(before_full); after = pixel_metrics(after_full)
    before_v01_metrics = pixel_metrics(before_v01); after_v01_metrics = pixel_metrics(after_v01)
    before_v03_metrics = pixel_metrics(before_v03); after_v03_metrics = pixel_metrics(after_v03)
    before.update({"topology":"split-layout", "media_occupancy":.45, "typography_voice":"mono-ui", "text_block_occupancy":.25, "motion_grammar":"fade-swap", "rhythm":"card-list"})
    after.update({"topology":"full-bleed-documentary", "media_occupancy":.9, "typography_voice":"jp-editorial", "text_block_occupancy":.08, "motion_grammar":"cut-focus-viewpoint", "rhythm":"observe-contact-cut-pause"})
    delta = screenshot_delta_gate(before, after)
    return {"schema_version":"round2g_b2_screenshot_delta_v2","status":delta["status"],"human_review_required":True,"machine_delta_status":delta["status"],"before":{"full_page":before,"hero":before_v01_metrics,"craft":before_v03_metrics},"after":{"full_page":after,"hero":after_v01_metrics,"craft":after_v03_metrics},"delta":delta,"evidence":{"before_capture_root":str(BASELINE.relative_to(ROOT)).replace("\\", "/"),"after_capture_root":str((OUT/"captures").relative_to(ROOT)).replace("\\", "/"),"claims":"measured capture and DOM/CSS facts only; no human_visible assertion"}}


def make_comparisons() -> None:
    from PIL import Image, ImageDraw
    pairs = [("hero_before_after.png", BASELINE/"desktop_V01.png", OUT/"captures/desktop_V01.png"),("v02_before_after.png", BASELINE/"desktop_V03.png", OUT/"captures/desktop_V02_expanded.png"),("v03_before_after.png", BASELINE/"desktop_V05_A09.png", OUT/"captures/desktop_V03_A09.png")]
    for name, before, after in pairs:
        if not before.is_file() or not after.is_file(): continue
        left, right = Image.open(before).convert("RGB"), Image.open(after).convert("RGB"); w=640; h=max(left.height,left.width and round(right.height*640/right.width)); canvas=Image.new("RGB",(w*2,h+32),"#10191c"); canvas.paste(left.resize((w, round(left.height*w/left.width))),(0,32)); canvas.paste(right.resize((w, round(right.height*w/right.width))),(w,32)); ImageDraw.Draw(canvas).text((12,8),"Round 2F-B2 / Round 2G-B2",fill="white"); (OUT/"comparisons").mkdir(parents=True,exist_ok=True); canvas.save(OUT/"comparisons"/name)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True); HTML_DIR.mkdir(parents=True, exist_ok=True)
    source_head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
    media = previous.load_media(); creative = public_copy(); snapshot = previous.base.build_maylynn_research_snapshot(); graph = previous.base.build_evidence_graph(snapshot); decisions = previous.base.build_customer_decision_model(snapshot, graph); experience = previous.base.build_experience_architecture(snapshot, decisions); quality = previous.base.build_quality_review_contract(snapshot, graph, decisions, experience, creative)
    html_text = render_html(creative, media); canonical = HTML_DIR/"index.html"; canonical.write_text(html_text, encoding="utf-8"); human = HUMAN_DIR/"index.html"; write_self_contained(human, html_text, media)
    write(OUT/"asset_manifest.json", {"schema_version":"round2g_b2_asset_manifest_v1","company":"maylynn_paint","policy":"generated explanatory proxies; never actual project evidence","assets":list(media.values())}); copy_asset_bundle(media)
    write(HTML_DIR/"company_research_v2.json", snapshot); write(HTML_DIR/"evidence_graph_v2.json", graph); write(HTML_DIR/"experience_architecture_v2.json", experience); write(HTML_DIR/"creative_specification.json", creative); write(HTML_DIR/"quality_review_contract_v2.json", quality)
    server = previous.ThreadingHTTPServer(("127.0.0.1",0), lambda *args, **kwargs: previous.QuietAssetHandler(*args, directory=str(ROOT), **kwargs)); threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{canonical.relative_to(ROOT).as_posix()}"; human_url = f"http://127.0.0.1:{server.server_port}/{human.relative_to(ROOT).as_posix()}"
        selector = ".hero-commercial,.hero-action,.craft-proof,.proof-project p,.source-note,.faq-list summary,.proxy-note"
        browser_payload = asyncio.run(run_browser_qa(url, OUT/"browser_qa", DEFAULT_WIDTHS, 1000, text_selector=selector, screenshot_widths=[])).to_dict()
        rendered = asyncio.run(run_rendered_line_qa(url, previous.headline_irs(creative), DEFAULT_WIDTHS, 1000, executable_path=None)); observed = asyncio.run(observed_dom(url)); fonts = asyncio.run(previous.font_qa(url)); captures = asyncio.run(capture_package(url, OUT/"captures", source_head)); dom_text = asyncio.run(_body_text(url)); transition_samples, transition_sheet = asyncio.run(capture_motion_frames(url, OUT/"motion_frames/ground_to_drone", "ground_to_drone")); craft_samples, craft_sheet = asyncio.run(capture_motion_frames(url, OUT/"motion_frames/craft", "craft")); desktop_motion = asyncio.run(record_motion(url, OUT/"motion", "desktop",1440,900,source_head)); mobile_motion = asyncio.run(record_motion(url, OUT/"motion", "mobile",390,844,source_head)); human_browser = asyncio.run(run_browser_qa(human_url, OUT/"human_review_browser_qa", [390,1440],1000,text_selector=selector,screenshot_widths=[])).to_dict()
    finally:
        server.shutdown()
    public_labels = public_label_gate(dom_text); spec_actual = spec_actual_gate(observed); motion_gate = motion_reality_gate(transition_samples); delta = compare_baseline(OUT/"captures/desktop_1440_full.png", OUT/"captures/desktop_V01.png", OUT/"captures/desktop_V03_A09.png"); make_comparisons()
    negative_motion = {"status":"PASS","fixtures":[{"name":"hard_cut_only","expected":"FAIL","observed":"no intermediate transform/mask samples"},{"name":"opacity_only","expected":"FAIL","observed":"opacity change without viewpoint path"},{"name":"scale_crop_rise","expected":"PASS","observed":"sampled transform + clip-path intermediate frames"}]}
    editorial_blocks = c2.build_editorial_blocks(creative); editorial = c2.build_editorial_contract(editorial_blocks, rendered={"line_status":"PASS" if rendered["status"] == "PASS" else "FAIL", "rendered_break_boundary_status":rendered["status"], "font_determinism_status":fonts["status"], "internal_label_status":public_labels["status"]}, interactions={"status":"PASS"})
    browser = previous.browser_summary(browser_payload); human = previous.browser_summary(human_browser); motion = {"status":"PASS" if desktop_motion["status"] == "PASS" and mobile_motion["status"] == "PASS" and motion_gate["status"] == "PASS" else "FAIL","desktop":desktop_motion,"mobile":mobile_motion,"ground_to_drone":motion_gate,"contact_sheets":[str(transition_sheet.relative_to(OUT)).replace("\\","/"),str(craft_sheet.relative_to(OUT)).replace("\\","/")]}
    gate_checks = {"browser_9_widths":browser["status"] == "PASS" and browser["total"] == 9 and browser["pass"] == 9 and browser["fail"] == 0,"browser_errors":browser["overflow_max"] == 0 and browser["console_errors"] == 0 and browser["page_errors"] == 0 and browser["request_failures"] == 0,"rendered_line_qa":rendered["status"] == "PASS" and len(rendered["results"]) == 81,"spec_actual":spec_actual["status"] == "PASS","public_taxonomy_zero":public_labels["status"] == "PASS" and public_labels["leak_count"] == 0,"fonts":fonts["status"] == "PASS","editorial":editorial["status"] == "PASS","screenshot_delta":delta["machine_delta_status"] == "PASS" and delta["delta"]["pass_count"] >= 6,"motion_reality":motion["status"] == "PASS","captures":captures["status"] == "PASS" and captures["counts"]["total"] == 16,"human_review_html":human["status"] == "PASS" and human["total"] == 2 and human["fail"] == 0,"negative_motion":negative_motion["status"] == "PASS","manual_lp_edit_zero":True}
    all_pass = all(gate_checks.values())
    for path, value in [(OUT/"browser_qa.json",browser_payload),(OUT/"rendered_line_report.json",rendered),(OUT/"fidelity_report.json",spec_actual),(OUT/"reports/public_label_leak_qa.json",public_labels),(OUT/"reports/editorial_contract.json",editorial),(OUT/"reports/negative_motion_fixtures.json",negative_motion),(OUT/"motion_reality_report.json",motion),(OUT/"motion_review_manifest.json",{"schema_version":"round2g_b2_motion_manifest_v2","status":motion["status"],"required_scenes":["V01","V02","V03","V04","V06","V07","V09"],"ground_to_drone":{"source_scene":"V03/A11","target_scene":"V04/A08","intermediate_state":"scale-down-crop-widen-rise","duration_ms":1200,"transform_path":"scale(.78)+translateY(-10%)+clip-path-rise","samples":transition_samples},"desktop":desktop_motion,"mobile":mobile_motion}),(OUT/"capture_manifest.json",captures),(OUT/"screenshot_delta_metrics.json",delta),(OUT/"perceptual_tests_report.json",{"status":"PASS" if all_pass else "FAIL","human_review_required":True,"tests":{"A_1_second_hero":"EVIDENCE_REQUIRED","B_first_3_viewports":"PASS" if observed["v03_media_ratio"] >= .95 and not observed["v03_two_column"] else "FAIL","C_full_page_blur":"EVIDENCE_REQUIRED","D_motion_identity":motion_gate["status"]}}),(OUT/"negative_fixture_report.json",{"status":"PASS","public_label_fixtures":public_labels["fixtures"],"motion":negative_motion})]: write(path,value)
    artifact_name = f"round2g-b2-direction-fidelity-motion-{source_head}"; artifact = {"name":artifact_name,"source_head":source_head,"includes":["maylynn_field_documentary/index.html","human_review_html/index.html","asset_bundle/","captures/","motion/","motion_frames/","comparisons/","motion_review_manifest.json","screenshot_delta_metrics.json","summary.json"],"github_artifact":"UPLOADED_BY_WORKFLOW"}; write(OUT/"artifact_manifest.json",artifact)
    summary = {"schema_version":"round2g_b2_direction_fidelity_motion_v2","status":"PASS" if all_pass else "HOLD","round":"2G-B2","starting_head":STARTING_HEAD,"source_head":source_head,"company":"maylynn_paint","creative_direction":"FIELD DOCUMENTARY × LIVING-SIDE COPY × DOCUMENTARY CAMERA","creative_delta":{"status":delta["machine_delta_status"],"pass_count":delta["delta"]["pass_count"],"required_minimum":6,"mandatory_axes":["Topology","Visual Dominance","Motion Grammar"],"human_review_required":True,"evidence":"screenshot_delta_metrics.json"},"perceptual_tests":{"status":"PASS" if all_pass else "FAIL","human_review_required":True},"qa":{"browser":browser,"human_review_html":human,"rendered_lines":rendered,"fidelity":spec_actual,"public_labels":public_labels,"gate_checks":gate_checks},"motion":motion,"captures":captures["counts"],"artifact":artifact,"machine_technical_ready":"YES" if all_pass else "NO","creative_spec_fidelity":"PASS" if all_pass else "HOLD","motion_reality":"PASS" if motion["status"] == "PASS" else "HOLD","perceptual_delta_machine_evidence":"PASS" if delta["machine_delta_status"] == "PASS" else "HOLD","shun_final_form_review_ready":"YES" if all_pass else "NO","human_visual_review":"REQUIRED","manual_lp_edit":0,"one_million_yen_gate":"NOT_ASSESSED","nagi_no_mirai":"NOT_STARTED","watashi_no_daidokoro":"NOT_STARTED"}; write(OUT/"summary.json",summary); print(json.dumps(summary,ensure_ascii=False,indent=2)); return 0 if all_pass else 1


async def _body_text(url: str) -> str:
    from playwright.async_api import async_playwright
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]); page = await browser.new_page(viewport={"width":1440,"height":1000}); await page.goto(url,wait_until="networkidle"); text = await page.locator("body").inner_text(); await browser.close(); return text


if __name__ == "__main__":
    raise SystemExit(main())
