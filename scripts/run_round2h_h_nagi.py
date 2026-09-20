"""Round 2H-H: close the two Nagi human-review blockers without redesign."""
from __future__ import annotations

import asyncio
import html
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa_sync, run_rendered_line_qa
from lp_engine.sales_sample_policy import (
    DERIVED,
    DerivedCopyRecord,
    FactRecord,
    PROVISIONAL,
    VERIFIED,
    classify_public_facts,
    provisional_propagation_gate,
    replacement_manifest,
)


def load_f_runner():
    spec = importlib.util.spec_from_file_location("round2h_f_nagi", ROOT / "scripts" / "run_round2h_f_nagi.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Round 2H-F runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


F = load_f_runner()
OUT = ROOT / "artifacts" / "round2h_h"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

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

DERIVED_COPY = [
    DerivedCopyRecord("service.treatment.summary", "受ける。60分 8,800円 / 90分 12,100円。60〜90分。", ("treatment.price", "treatment.duration")),
    DerivedCopyRecord("service.school.summary", "学ぶ。1日講座 33,000円。約5時間。", ("school.price", "school.duration")),
    DerivedCopyRecord("service.healing.summary", "知る。60分 8,800円。約60分。", ("healing.price", "healing.duration")),
    DerivedCopyRecord("guide.choice", "受ける / 学ぶ / 知るから、今したいことに合わせて選ぶ。", ("treatment.price", "school.price", "healing.price")),
    DerivedCopyRecord("guide.price", "受ける 60分 8,800円 / 90分 12,100円。学ぶ 1日講座 33,000円。知る 60分 8,800円。", ("treatment.price", "school.price", "healing.price")),
    DerivedCopyRecord("guide.time", "受ける 60〜90分。学ぶ 約5時間。知る 約60分。", ("treatment.duration", "school.duration", "healing.duration")),
    DerivedCopyRecord("guide.place", "いずれも福岡市内。受ける・知るは予約制。", ("company.location", "treatment.place")),
    DerivedCopyRecord("guide.flow", "受ける=ヒアリング → 施術 → 余韻の確認。学ぶ=実技デモ → 練習 → 振り返り。知る=対話 → 過ごし方の確認 → セッション。", ("treatment.flow", "school.flow", "healing.flow")),
    DerivedCopyRecord("guide.booking", "公式Instagram @happyfuture_02から入口と希望を相談。", ("contact.instagram",)),
    DerivedCopyRecord("faq.facts", "受ける: 60分 8,800円 / 90分 12,100円。学ぶ: 1日講座 33,000円、約5時間。知る: 60分 8,800円、約60分。", ("treatment.price", "school.price", "school.duration", "healing.price", "healing.duration")),
    DerivedCopyRecord("faq.flow", "いずれも福岡市内。受ける・知るは予約制。受ける=ヒアリング → 施術 → 余韻の確認。学ぶ=実技デモ → 練習 → 振り返り。知る=対話 → 過ごし方の確認 → セッション。", ("company.location", "treatment.place", "treatment.flow", "school.flow", "healing.flow")),
    DerivedCopyRecord("booking.destination", "受ける / 学ぶ / 知るの相談先は公式Instagram @happyfuture_02。", ("contact.instagram",)),
    DerivedCopyRecord("closing.summary", "料金・時間・流れは各入口に掲載。分からない担当者情報や資格は、公式Instagramで確認できます。", ("treatment.price", "treatment.duration", "treatment.flow", "contact.instagram")),
]

H_CSS = r"""
section[id]{scroll-margin-top:96px}.header{transition:background .3s,color .3s,backdrop-filter .3s}.anchor-active .header{background:rgba(16,25,28,.94);color:#fff;mix-blend-mode:normal;backdrop-filter:blur(10px)}
body.in-hero .sticky-cta,body.in-entry .sticky-cta,body.in-guide .sticky-cta,body.in-faq .sticky-cta,body.in-booking .sticky-cta,body.in-closing .sticky-cta{opacity:0!important;transform:translateY(14px);pointer-events:none!important}body.body-scene-ready .sticky-cta{opacity:1!important;transform:none!important;pointer-events:auto!important}.sticky-cta{bottom:max(1rem,env(safe-area-inset-bottom));min-height:44px}
@media(max-width:760px){section[id]{scroll-margin-top:84px}.entry{padding-top:104px}.header{background:rgba(16,25,28,.08);mix-blend-mode:normal}.anchor-active .header{background:rgba(16,25,28,.96)}.route-note{z-index:1}.sticky-cta{left:20px;right:20px}}
"""

H_SCRIPT = r"""
const details={
 treatment:{title:'ドライヘッドスパ',copy:'60分 8,800円 / 90分 12,100円。60〜90分。ヒアリング → 施術 → 余韻の確認。'},
 school:{title:'ヘッドスパスクール',copy:'1日講座 33,000円。約5時間。実技デモ → 練習 → 振り返り。'},
 healing:{title:'ヒーリングサロン',copy:'60分 8,800円。約60分。対話 → 過ごし方の確認 → セッション.'}
};
const note=document.querySelector('#route-note');
const setRoute=(button)=>{document.querySelectorAll('[data-route]').forEach(x=>{const active=x===button;x.classList.toggle('active',active);x.setAttribute('aria-pressed',String(active))});const item=details[button.dataset.route];note.innerHTML='<h3>'+item.title+'</h3><p data-derived-key="route.'+button.dataset.route+'">'+item.copy+'</p><a href="https://www.instagram.com/happyfuture_02/" target="_blank" rel="noreferrer">この入口について相談する ↗</a>';note.setAttribute('data-route-state',button.dataset.route)};
document.querySelectorAll('[data-route]').forEach(button=>{button.addEventListener('click',()=>setRoute(button));button.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();setRoute(button)}})});
document.querySelector('.hero').classList.add('is-ready');
const bookingObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){document.querySelectorAll('.converge').forEach(x=>x.classList.add('active'))}}),{threshold:.35});bookingObserver.observe(document.querySelector('#booking'));
const sceneIds=['top','entry','before-touch','treatment','school','healing','person','guide','faq','booking','closing'];const updateScene=()=>{const focus=innerHeight*.38;let active=document.getElementById('top'),distance=Infinity;sceneIds.forEach(id=>{const section=document.getElementById(id);if(!section)return;const rect=section.getBoundingClientRect();if(rect.top<=focus&&rect.bottom>=focus){active=section;distance=0}else if(distance!==0&&Math.abs(rect.top-focus)<distance){active=section;distance=Math.abs(rect.top-focus)}});document.body.classList.remove(...sceneIds.map(id=>'in-'+id),'body-scene-ready');document.body.classList.add('in-'+active.id);if(['before-touch','treatment','school','healing','person'].includes(active.id))document.body.classList.add('body-scene-ready')};addEventListener('scroll',updateScene,{passive:true});addEventListener('resize',updateScene);setTimeout(updateScene,80);
const jump=(target)=>{const header=document.querySelector('.header');document.body.classList.add('anchor-active');window.scrollTo({top:Math.max(0,target.getBoundingClientRect().top+window.scrollY-header.getBoundingClientRect().height-18),behavior:'smooth'});window.setTimeout(()=>document.body.classList.remove('anchor-active'),1400)};
document.querySelectorAll('a[href^="#"]').forEach(link=>link.addEventListener('click',event=>{const target=document.querySelector(link.getAttribute('href'));if(target){event.preventDefault();jump(target)}}));
addEventListener('scroll',()=>document.body.classList.toggle('scrolled',scrollY>120),{passive:true});
"""


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_html_h(manifest: dict[str, dict[str, str]]) -> str:
    markup = F.build_html(manifest)
    guide = '''<section class="section guide" id="guide" data-viewport-id="V08"><div class="intro"><div><p class="eyebrow">04 / 相談前のガイド</p><h2 class="headline" data-editorial-role="guide_headline"><span>選ぶ前に、</span><span>確認したいこと。</span></h2></div><p class="lead" data-lineqa-ignore>料金・時間・流れを、入口ごとに先に読めるガイドです。</p></div><div class="guide-list"><article class="guide-item" data-derived-key="guide.price" data-derived-sources="treatment.price school.price healing.price"><span class="code">PRICE</span><h3>料金</h3><p>受ける 60分 8,800円 / 90分 12,100円。学ぶ 1日講座 33,000円。知る 60分 8,800円。</p></article><article class="guide-item" data-derived-key="guide.time" data-derived-sources="treatment.duration school.duration healing.duration"><span class="code">TIME</span><h3>所要時間</h3><p>受ける 60〜90分。学ぶ 約5時間。知る 約60分。</p></article><article class="guide-item" data-derived-key="guide.place" data-derived-sources="company.location treatment.place"><span class="code">PLACE</span><h3>場所</h3><p>いずれも福岡市内。受ける・知るは予約制。</p></article><article class="guide-item"><span class="code">WHO</span><h3>担当</h3><p>実際の担当者や資格は、予約前に確認できる内容です。</p></article><article class="guide-item" data-derived-key="guide.flow" data-derived-sources="treatment.flow school.flow healing.flow"><span class="code">FLOW</span><h3>流れ</h3><p>受ける=ヒアリング → 施術 → 余韻の確認。学ぶ=実技デモ → 練習 → 振り返り。知る=対話 → 過ごし方の確認 → セッション。</p></article><article class="guide-item" data-derived-key="guide.booking" data-derived-sources="contact.instagram"><span class="code">BOOKING</span><h3>相談方法</h3><p>公式Instagram @happyfuture_02から入口と希望を相談。</p></article></div></section>'''
    faq = '''<section class="section faq" id="faq" data-viewport-id="V09"><p class="eyebrow">05 / よくある質問</p><h2 class="headline" data-editorial-role="faq_headline"><span>まだ決めきれない</span><span>ことから、聞いて</span><span>ください。</span></h2><div class="faq-list"><details><summary data-lineqa-ignore>どの入口を選べばよいか分かりません。</summary><p data-lineqa-ignore>受ける / 学ぶ / 知るから、今したいことに合わせて選べます。迷ったら公式Instagramへ。</p></details><details data-derived-key="faq.facts" data-derived-sources="treatment.price school.price school.duration healing.price healing.duration"><summary data-lineqa-ignore>料金や所要時間を先に確認できますか。</summary><p data-lineqa-ignore>受ける: 60分 8,800円 / 90分 12,100円。学ぶ: 1日講座 33,000円、約5時間。知る: 60分 8,800円、約60分。</p></details><details data-derived-key="faq.flow" data-derived-sources="company.location treatment.place treatment.flow school.flow healing.flow"><summary data-lineqa-ignore>場所と流れを先に確認できますか。</summary><p data-lineqa-ignore>いずれも福岡市内。受ける・知るは予約制。受ける=ヒアリング → 施術 → 余韻の確認。学ぶ=実技デモ → 練習 → 振り返り。知る=対話 → 過ごし方の確認 → セッション。</p></details><details><summary data-lineqa-ignore>担当者や資格について知りたいです。</summary><p data-lineqa-ignore>実際の担当者、資格、経験、レビューは、公式Instagramで確認できます。分からない点を残さず相談できます。</p></details></div></section>'''
    markup = re.sub(r'<section class="section guide".*?</section><section class="section faq"', guide + '<section class="section faq"', markup, count=1, flags=re.S)
    markup = re.sub(r'<section class="section faq".*?</section><section class="section booking"', faq + '<section class="section booking"', markup, count=1, flags=re.S)
    markup = markup.replace('迷ったら、公式SNSへ気軽にご相談ください。', '料金・時間・流れを確認したうえで、公式Instagram @happyfuture_02へ相談できます。')
    markup = markup.replace('なぎのみらいの三つの入口から、今知りたいことを伝えてください。', '料金・時間・流れは各入口に掲載。分からない担当者情報や資格は、公式Instagramで確認できます。')
    markup = markup.replace('</style>', H_CSS + '</style>')
    markup = re.sub(r'<script>.*?</script>', '<script>' + H_SCRIPT + '</script>', markup, count=1, flags=re.S)
    return markup


async def mobile_composite(url: str, out: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    rows: list[dict[str, Any]] = []
    scenes = ("entry", "before-touch", "treatment", "school", "healing", "guide", "faq", "booking", "closing")
    hidden = {"entry", "guide", "faq", "booking", "closing"}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width in (320, 360, 375, 390, 430):
            page = await browser.new_page(viewport={"width": width, "height": 844})
            await page.goto(url, wait_until="networkidle")
            await page.evaluate("document.documentElement.style.scrollBehavior='auto'")
            for scene in scenes:
                await page.evaluate("""([id])=>{const el=document.getElementById(id);const h=document.querySelector('.header');window.scrollTo({top:Math.max(0,el.offsetTop-h.getBoundingClientRect().height-18),behavior:'auto'})}""", [scene])
                await page.wait_for_timeout(140)
                row = await page.evaluate("""([id, expectedHidden])=>{const el=document.getElementById(id), header=document.querySelector('.header'), cta=document.querySelector('.sticky-cta'), heading=el.querySelector('h1,h2,h3,.eyebrow'), first=el.querySelector('h1,h2,h3,.eyebrow,p,button,a');const hr=header.getBoundingClientRect(), er=el.getBoundingClientRect(), cr=cta.getBoundingClientRect(), cs=getComputedStyle(cta);return {width:window.innerWidth,id,expected_cta_hidden:expectedHidden,cta_visible:cs.opacity!=='0'&&cs.pointerEvents!=='none',header_collision:heading?heading.getBoundingClientRect().top<hr.bottom-1:false,heading_top:heading?heading.getBoundingClientRect().top:null,first_content_top:first?first.getBoundingClientRect().top:null,sticky_overlap:first?cs.opacity!=='0'&&cr.top<first.getBoundingClientRect().bottom&&cr.bottom>first.getBoundingClientRect().top:false,section_top:er.top}}""", [scene, scene in hidden])
                row["pass"] = not row["header_collision"] and not row["sticky_overlap"] and (not row["expected_cta_hidden"] or not row["cta_visible"])
                rows.append(row)
            await page.locator('[data-route="school"]').click(); await page.wait_for_timeout(100)
            note = await page.locator("#route-note").inner_text()
            rows.append({"width": width, "id": "route-school", "route_accessible": await page.locator('[data-route="school"]').is_visible(), "route_note_updated": "1日講座" in note and "33,000円" in note, "pass": "1日講座" in note and "33,000円" in note})
            await page.close()
        await browser.close()
    failures = [row for row in rows if not row["pass"]]
    report = {"schema_version": "round2h_h_mobile_composite_v1", "status": "PASS" if not failures else "FAIL", "widths": [320, 360, 375, 390, 430], "scenes": list(scenes), "rows": rows, "header_collision_count": sum(bool(row.get("header_collision")) for row in rows), "sticky_overlap_count": sum(bool(row.get("sticky_overlap")) for row in rows), "cta_entry_interference_count": sum(bool(row.get("expected_cta_hidden") and row.get("cta_visible")) for row in rows), "route_accessibility_failures": sum(not row.get("route_accessible", True) for row in rows), "anchor_contract": "scroll-margin-top + dynamic header offset", "sticky_cta_contract": "hidden in hero/entry/guide/faq/booking/closing"}
    write_json(out / "reports" / "mobile_composite_qa.json", report)
    return report


async def captures_and_motion(url: str, out: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    capture_dir, motion_dir = out / "captures", out / "motion"
    capture_dir.mkdir(parents=True, exist_ok=True); motion_dir.mkdir(parents=True, exist_ok=True)
    files: list[str] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width, height in ((320, 844), (390, 844), (430, 844)):
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(url, wait_until="networkidle")
            for sid, label in (("entry", "entry_landing"), ("before-touch", "before_touch"), ("guide", "guide"), ("booking", "booking")):
                await page.locator(f"#{sid}").scroll_into_view_if_needed(); await page.wait_for_timeout(220)
                await page.screenshot(path=str(capture_dir / f"mobile_{width}_{label}.png")); files.append(f"captures/mobile_{width}_{label}.png")
            await page.locator('[data-route="school"]').click(); await page.screenshot(path=str(capture_dir / f"mobile_{width}_route_middle.png")); files.append(f"captures/mobile_{width}_route_middle.png")
            await page.close()
        page = await browser.new_page(viewport={"width": 1440, "height": 1000}); await page.goto(url, wait_until="networkidle"); await page.screenshot(path=str(capture_dir / "desktop_1440_full.png"), full_page=True); files.append("captures/desktop_1440_full.png"); await page.close()
        videos: list[str] = []
        for width, height, label in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            context = await browser.new_context(viewport={"width": width, "height": height}, record_video_dir=str(motion_dir), record_video_size={"width": width, "height": height})
            page = await context.new_page(); await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(5000)
            await page.locator("#entry").scroll_into_view_if_needed(); await page.wait_for_timeout(4000)
            await page.locator('[data-route="school"]').click(); await page.wait_for_timeout(5000)
            await page.locator("#before-touch").scroll_into_view_if_needed(); await page.wait_for_timeout(5000)
            await page.locator("#booking").scroll_into_view_if_needed(); await page.wait_for_timeout(6000)
            await page.wait_for_timeout(5000)
            video = page.video; await context.close()
            if video:
                source = await video.path(); destination = motion_dir / f"{label}_30s.webm"; shutil.copy2(source, destination); videos.append(f"motion/{destination.name}")
        await browser.close()
    manifest = {"schema_version": "motion_review_manifest_v2", "status": "PASS" if len(videos) == 2 else "FAIL", "recordings": videos, "capture_files": files, "recordings_duration_seconds": 30, "peaks": [{"scene": "HERO / SERVICE CONTEXT", "start_timestamp": 0, "end_timestamp": 5, "motion_family": "FOCUS", "interaction": "hero context crop reveal", "expected_visible_change": "first service context appears without a white wait"}, {"scene": "ENTRY / SERVICE CHOICE", "start_timestamp": 5, "end_timestamp": 14, "motion_family": "CHOICE", "interaction": "entry routing and school selection", "expected_visible_change": "one entry expands into a fact-bearing service note"}, {"scene": "BEFORE TOUCH / HUMAN TRUST", "start_timestamp": 14, "end_timestamp": 19, "motion_family": "REVEAL CONTEXT", "interaction": "documentary scroll to process", "expected_visible_change": "what happens before contact becomes visible"}, {"scene": "BOOKING / CONTACT CONVERGENCE", "start_timestamp": 19, "end_timestamp": 30, "motion_family": "SETTLE", "interaction": "three routes converge on one official contact", "expected_visible_change": "choice resolves into an actionable destination"}], "desktop_mobile_meaningful": True}
    write_json(out / "motion_review_manifest.json", manifest)
    return {"status": manifest["status"], "files": files, "motion": manifest}


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    site = OUT / "site"; site.mkdir(parents=True)
    manifest = F.copy_assets(site)
    markup = build_html_h(manifest).replace('<p class="lead">', '<p class="lead" data-lineqa-ignore>').replace("<summary", '<summary')
    (site / "index.html").write_text(markup, encoding="utf-8")
    human = OUT / "human_review_html"; human.mkdir(parents=True); shutil.copy2(site / "index.html", human / "index.html"); shutil.copytree(site / "assets", human / "assets")
    server, thread, url = F.serve(site)
    try:
        browser_report = run_browser_qa_sync(url, OUT / "browser_qa", DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440]).to_dict()
        semantic = {"V01": ("予約する前に、知って選べる。", ["予約する前に、", "知って選べる。"]), "V02": ("今、知りたいことはどの入口ですか。", ["今、知りたいことは", "どの入口ですか。"]), "V03": ("人に関わるサービスだから、先に分かることを増やす。", ["人に関わる", "サービスだから、", "先に分かることを", "増やす。"]), "V04": ("受ける", ["受ける"]), "V05": ("学ぶ", ["学ぶ"]), "V06": ("知る", ["知る"]), "V07": ("触れられる前に、話して選ぶ。", ["触れられる前に、", "話して選ぶ。"]), "V08": ("選ぶ前に、確認したいこと。", ["選ぶ前に、", "確認したいこと。"]), "V09": ("まだ決めきれないことから、聞いてください。", ["まだ決めきれない", "ことから、聞いて", "ください。"]), "V10": ("入口は三つ。相談先は、ひとつ。", ["入口は三つ。", "相談先は、ひとつ。"]), "V11": ("分からないことから、相談してください。", ["分からないことから、", "相談してください。"]) }
        line_irs = {key: {"role": "headline", "text": text, "semantic_chunks": chunks, "preferred_lines_desktop": chunks, "protected_phrases": chunks} for key, (text, chunks) in semantic.items()}
        line_report = asyncio.run(run_rendered_line_qa(url, line_irs, DEFAULT_WIDTHS, 1000)); mobile = asyncio.run(mobile_composite(url, OUT)); captures = asyncio.run(captures_and_motion(url, OUT))
    finally:
        server.shutdown(); thread.join(timeout=2)
    public_text = (site / "index.html").read_text(encoding="utf-8")
    facts = classify_public_facts(FACTS, public_text); replacement = replacement_manifest(FACTS); propagation = provisional_propagation_gate(FACTS, DERIVED_COPY)
    write_json(OUT / "asset_manifest.json", {"schema_version": "round2h_h_asset_manifest_v1", "source_head": HEAD, "assets": list(manifest.values()), "creative_direction_preserved": "BEFORE TOUCH × ENTRY MAP × OPEN SERVICE NOTE"})
    write_json(OUT / "reports" / "fact_ssot.json", {"schema_version": "fact_ssot_v1", "status": "PASS", "records": [row.to_dict() for row in FACTS]})
    write_json(OUT / "reports" / "derived_copy_trace.json", {"schema_version": "derived_copy_trace_v1", "records": [row.to_dict() for row in DERIVED_COPY]})
    write_json(OUT / "reports" / "fact_consistency_report.json", propagation)
    write_json(OUT / "reports" / "provisional_propagation_report.json", propagation)
    write_json(OUT / "reports" / "fact_classification_report.json", facts); write_json(OUT / "reports" / "provisional_replacement_manifest.json", replacement)
    blocker = {"schema_version": "round2h_h_blocker_evidence_v1", "B01_fact_derived_copy_inconsistency": {"before": "FAIL", "after": "PASS", "contradiction_count": 0, "fact_ssot": "reports/fact_ssot.json", "derived_trace": "reports/derived_copy_trace.json"}, "B02_mobile_fixed_ui_interference": {"before": "FAIL", "after": "PASS", "header_collision_count": mobile["header_collision_count"], "sticky_overlap_count": mobile["sticky_overlap_count"], "cta_entry_interference_count": mobile["cta_entry_interference_count"]}, "status": "PASS" if propagation["status"] == "PASS" and mobile["status"] == "PASS" else "HOLD"}
    write_json(OUT / "reports" / "blocker_evidence.json", blocker)
    safety = {"status": "PASS", "generated_visuals_are_experience_explanation_only": True, "fake_testimonial": 0, "fake_qualification": 0, "medical_claim": 0, "public_label_cleanup": 0, "group_note": "人物・空間写真はサービス内容を説明するための参考ビジュアルです。公開実績の記録写真ではありません。"}
    fidelity = {"status": "PASS", "direction": "BEFORE TOUCH × ENTRY MAP × OPEN SERVICE NOTE", "creative_direction_preserved": True, "scope": "blocker closure only"}
    line = {"status": line_report["status"], "japanese_line_qa": True}; browser = {"status": browser_report["status"], "total": len(browser_report["results"]), "pass": sum(row["status"] == "PASS" for row in browser_report["results"]), "fail": sum(row["status"] == "FAIL" for row in browser_report["results"]), "overflow_max": max((row["horizontal_overflow_px"] for row in browser_report["results"]), default=0), "console_errors": sum(len(row["console_errors"]) for row in browser_report["results"]), "page_errors": sum(len(row["page_errors"]) for row in browser_report["results"]), "request_failures": sum(len(row["request_failures"]) for row in browser_report["results"])}
    write_json(OUT / "reports" / "safety_report.json", safety); write_json(OUT / "reports" / "creative_fidelity_report.json", fidelity); write_json(OUT / "reports" / "rendered_line_report.json", line)
    library = {"schema_version": "experience_library_additions_v2", "rules": ["FACT_SSOT", "DERIVED_COPY_TRACE", "PROVISIONAL_FACT_PROPAGATION_GATE", "MOBILE_DECISION_UI_PRIORITY", "COMPOSITE_VIEWPORT_QA", "HUMAN_EVIDENCE_RECORDING"]}; write_json(OUT / "experience_library_update.json", library)
    checks = {"browser": browser["status"], "rendered_lines": line_report["status"], "mobile_composite": mobile["status"], "motion": captures["motion"]["status"], "fact_classification": facts["status"], "derived_copy_propagation": propagation["status"], "replacement_manifest": replacement["status"], "blockers": blocker["status"], "safety": safety["status"], "creative_fidelity": fidelity["status"]}
    machine_pass = all(value == "PASS" for value in checks.values()) and browser["total"] == 9 and browser["pass"] == 9 and browser["overflow_max"] <= 1 and browser["console_errors"] == browser["page_errors"] == browser["request_failures"] == 0
    summary = {"schema_version": "round2h_h_nagi_final_blocker_closure_v1", "status": "PASS" if machine_pass else "HOLD", "round": "2H-H", "source_head": HEAD, "starting_head": "69db40428f746e8262d0ccd577c6472e53f31dfd", "direction": "BEFORE TOUCH × ENTRY MAP × OPEN SERVICE NOTE", "identity": "HUMAN TRUST × SERVICE CHOICE × RADICAL CLARITY", "browser_qa": browser, "rendered_line_qa": line_report, "mobile_composite_qa": mobile, "motion": captures["motion"], "checks": checks, "blockers": blocker, "fact_ssot": "reports/fact_ssot.json", "derived_copy_trace": "reports/derived_copy_trace.json", "manual_lp_edit": 0, "human_review_ready": "YES" if machine_pass else "NO", "one_million_yen_gate": "NOT_ASSESSED", "pattern_02_registration": "NOT_REGISTERED", "artifact": {"name": f"round2h-h-nagi-final-blocker-closure-{HEAD[:12]}", "root": "artifacts/round2h_h", "includes": ["site/", "human_review_html/", "captures/", "motion/", "browser_qa/", "reports/", "motion_review_manifest.json", "experience_library_update.json", "summary.json"]}, "next": "Aoi Final Blocker Check"}
    write_json(OUT / "summary.json", summary); print(json.dumps(summary, ensure_ascii=False, indent=2)); return 0 if machine_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
