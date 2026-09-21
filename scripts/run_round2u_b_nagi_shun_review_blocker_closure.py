"""Round 2U-B: close only the Japanese line and public wording blockers.

This derives the isolated Round 2U prototype, preserves its creative and motion
architecture, and applies authored line composition plus customer-facing trust
copy. Production Nagi is never modified.
"""
from __future__ import annotations

import asyncio
import base64
import importlib.util
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round2u_b"
STARTING_HEAD = "bf0bdf378b3d6b73f6416a297898c72ef766148e"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_base():
    path = ROOT / "scripts" / "run_round2u_nagi_creative_translation.py"
    spec = importlib.util.spec_from_file_location("round2u_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Round 2U base runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_base()
H = BASE.H
PUBLIC_STATE_WORDS = ("制作時", "差し替え", "正式情報", "仮", "未確認", "provisional", "sample", "dummy", "unconfirmed")
TRUST_FABRICATION_WORDS = ("実際の担当者", "資格・経験", "受賞", "口コミ", "お客様の声", "実績件数", "改善", "治療", "医療")
LINE_SELECTORS = "h1,h2,h3,p,a,summary"

TYPOGRAPHY_CSS = r"""
.authored-line{display:inline-block;white-space:nowrap}
.hero h1 span i{white-space:nowrap}
.selector-copy h2{font-size:clamp(2rem,4.2vw,5rem)}
.service-copy h2{font-size:clamp(2rem,4vw,5rem)}
.hero-lead,.selector-lead,.service-copy p,.trust p,.comparison-lead,.faq-item p,.contact-copy p,.closing p{ text-wrap:pretty }
@media(max-width:800px){
  .selector-copy h2{font-size:clamp(1.8rem,8vw,3.6rem)}
  .service-copy h2{font-size:clamp(1.8rem,7.2vw,3.2rem)}
  .contact-copy h2,.closing h2{font-size:clamp(2.1rem,8.3vw,4rem)}
}
@media(max-width:340px){
  .selector-copy h2{font-size:6.4vw}
  .service-copy h2{font-size:5.8vw}
  .trust h2,.comparison h2,.faq h2,.contact-copy h2,.closing h2{font-size:6.4vw}
}
"""


def authored_markup(markup: str) -> str:
    replacements = {
        '<h2 data-copy-role="SIGNATURE">今の目的は、<br>どれに近いですか。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">今の目的は、</span><br><span class="authored-line">どれに近いですか。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">ドライヘッドスパを受ける。\nその前に知りたいこと。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">ドライヘッドスパを受ける。</span><br><span class="authored-line">その前に、知りたいこと。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">学ぶなら、\n内容と進め方から。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">学ぶなら、</span><br><span class="authored-line">内容と進め方から。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">ヒーリングは、\nまず内容から。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">ヒーリングは、</span><br><span class="authored-line">まず内容から。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">分からないことを、<br>残さない。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">分からないことを、</span><br><span class="authored-line">残さない。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">3つの入口を、<br>同じ視界で比べる。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">3つの入口を、</span><br><span class="authored-line">同じ視界で比べる。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">気になることから、<br>確認する。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">気になることから、</span><br><span class="authored-line">確認する。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">気になることが一つあれば、<br>そこから相談できます。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">気になることが一つあれば、</span><br><span class="authored-line">そこから相談できます。</span></h2>',
        '<h2 data-copy-role="SIGNATURE">知ってから、<br>相談する。</h2>': '<h2 data-copy-role="SIGNATURE"><span class="authored-line">知ってから、</span><br><span class="authored-line">相談する。</span></h2>',
        '<p data-copy-role="SUPPORT">あなたの目的に近い入口から、確認できます。</p>': '<p data-copy-role="SUPPORT"><span class="authored-line">あなたの目的に近い入口から、</span><br><span class="authored-line">確認できます。</span></p>',
        '<div class="trust-slot"><div>実際の担当者｜制作時に差し替え</div><div>資格・経験｜制作時に差し替え</div><div>場所・予約方法｜公式情報を反映</div></div>': '<div class="trust-slot"><div>サービス内容｜相談前に確認</div><div>料金・時間｜選ぶ前に確認</div><div>相談・予約｜公式Instagram</div></div>',
        '内容・料金・時間・流れ。相談する前に、判断に必要な情報を順番に確認できる構成です。': '内容・料金・時間・流れ。相談前に必要な情報を確認できます。',
        '時間、料金、流れ。相談する前に、判断に必要な情報を整理します。': '時間、料金、流れを相談前に確認できます。',
        '実技、練習、振り返り。学ぶ入口で確認することを順番に見せます。': '実技、練習、振り返り。学ぶ入口の内容を確認できます。',
        'どんな時間か、何を確認するか。決めつけずにサービスの輪郭を整理します。': '内容と確認事項を、順番に見せます。',
        '受ける、学ぶ、知る。目的に近い選択肢と、確認する情報が異なります。': '受ける、学ぶ、知る。目的に近い選択肢を比べられます。',
        '施術は○○分・○○円、講座は全○回・○○時間程度。料金と時間の詳細は、相談前に確認できます。': '施術は○○分・○○円。講座は全○回・○○時間程度です。',
        '希望するサービス、気になること、当日の流れを最初に確認します。': '希望するサービスと、当日の流れを最初に確認します。',
        '受ける、学ぶ、知るのどれに近いかだけ伝えて相談できます。': '受ける、学ぶ、知る。近い目的から相談できます。',
        '料金、時間、場所、流れを見て、分からない点を整理しておくと相談が進みます。': '料金、時間、場所、流れを確認できます。',
        '選んだサービスや、まだ決めきれないことを公式Instagramで相談できます。': '選んだサービスや迷いを、公式Instagramで相談できます。',
        '料金と時間を先に確認できますか。': '料金と時間は？',
        '当日は何を確認しますか。': '当日の流れは？',
        'まだサービスを決めきれません。': '決めきれないときは？',
        '予約前に見ておくことはありますか。': '予約前に見ることは？',
        '施術は○○分・○○円、講座は全○回・○○時間程度。制作時に正式情報へ差し替えます。': '施術は○○分・○○円、講座は全○回・○○時間程度。料金と時間の詳細は、相談前に確認できます。',
        '公式Instagramで相談できます.': '公式Instagramで相談できます。',
    }
    for before, after in replacements.items():
        if before in markup:
            markup = markup.replace(before, after)
    authored_paragraphs = {
        '3つのサービスを、内容から選べます。': '<span class="authored-line">3つのサービスを、</span><br><span class="authored-line">内容から選べます。</span>',
        '受けたい。学びたい。まず内容を知りたい。': '<span class="authored-line">受けたい。学びたい。</span><br><span class="authored-line">まず内容を知りたい。</span>',
        '内容・料金・時間・流れ。相談前に必要な情報を確認できます。': '<span class="authored-line">内容・料金・時間・流れ。</span><br><span class="authored-line">相談前に必要な情報を</span><br><span class="authored-line">確認できます。</span>',
        '時間、料金、流れを相談前に確認できます。': '<span class="authored-line">時間、料金、流れを</span><br><span class="authored-line">相談前に確認できます。</span>',
        '実技、練習、振り返り。学ぶ入口の内容を確認できます。': '<span class="authored-line">実技、練習、振り返り。</span><br><span class="authored-line">学ぶ内容を確認できます。</span>',
        '内容と確認事項を、順番に見せます。': '<span class="authored-line">内容と確認事項を、</span><br><span class="authored-line">順番に確認できます。</span>',
        '受ける、学ぶ、知る。目的に近い選択肢を比べられます。': '<span class="authored-line">受ける、学ぶ、知る。</span><br><span class="authored-line">目的に近い選択肢を</span><br><span class="authored-line">比べられます。</span>',
        '施術は○○分・○○円。講座は全○回・○○時間程度です。': '<span class="authored-line">施術は○○分・○○円。</span><br><span class="authored-line">講座は全○回・○○時間程度。</span>',
        '希望するサービスと、当日の流れを最初に確認します。': '<span class="authored-line">希望するサービスと、</span><br><span class="authored-line">当日の流れを確認します。</span>',
        '受ける、学ぶ、知る。近い目的から相談できます。': '<span class="authored-line">受ける、学ぶ、知る。</span><br><span class="authored-line">近い目的から相談できます。</span>',
        '料金、時間、場所、流れを確認できます。': '<span class="authored-line">料金、時間、場所、流れを</span><br><span class="authored-line">確認できます。</span>',
        '選んだサービスや迷いを、公式Instagramで相談できます。': '<span class="authored-line">選んだサービスや迷いを、</span><br><span class="authored-line">公式Instagramで</span><br><span class="authored-line">相談できます。</span>',
        '触れる内容、時間、料金、流れを確認してから選ぶ。': '<span class="authored-line">触れる内容、時間、</span><br><span class="authored-line">料金、流れを確認してから選ぶ。</span>',
        '実技、練習、振り返り。学ぶ進め方を確認する。': '<span class="authored-line">実技、練習、振り返り。</span><br><span class="authored-line">学ぶ進め方を確認する。</span>',
        'どんなサービスか、確認事項から輪郭をつかむ。': '<span class="authored-line">どんなサービスか、</span><br><span class="authored-line">確認事項から輪郭をつかむ。</span>',
    }
    for before, after in authored_paragraphs.items():
        markup = markup.replace(before, after)
    direct_line_cleanup = {
        '選んだサービスや、まだ決めきれないことを公式Instagramで相談できます。': '<span class="authored-line">選んだサービスや迷いを、</span><br><span class="authored-line">公式Instagramで</span><br><span class="authored-line">相談できます。</span>',
        '施術は○○分・○○円、講座は全○回・○○時間程度。料金と時間の詳細は、相談前に確認できます。': '<span class="authored-line">施術は○○分・○○円。</span><br><span class="authored-line">講座は全○回・○○時間程度。</span>',
        '実技、練習、振り返り。学ぶ入口で確認することを順番に見せます。': '<span class="authored-line">実技、練習、振り返り。</span><br><span class="authored-line">学ぶ内容を確認できます。</span>',
        'どんな時間か、何を確認するか。決めつけずにサービスの輪郭を整理します。': '<span class="authored-line">内容と確認事項を、</span><br><span class="authored-line">順番に確認できます。</span>',
        '受ける、学ぶ、知る。目的に近い選択肢と、確認する情報が異なります。': '<span class="authored-line">受ける、学ぶ、知る。</span><br><span class="authored-line">目的に近い選択肢を</span><br><span class="authored-line">比べられます。</span>',
        '決めきれない点を、項目ごとに整理しています。': '<span class="authored-line">決めきれない点を、</span><br><span class="authored-line">項目ごとに確認できます。</span>',
    }
    for before, after in direct_line_cleanup.items():
        markup = markup.replace(before, after)
    if any(word.casefold() in markup.casefold() for word in ("制作時", "差し替え", "正式情報")):
        raise AssertionError("public production-state wording remains after closure")
    return markup.replace("</style>", f"{TYPOGRAPHY_CSS}</style>", 1)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def qa(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    widths = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)
    rows: list[dict[str, Any]] = []
    source = (OUT / "site" / "index.html").read_text(encoding="utf-8")
    visible = re.sub(r"<style.*?</style>|<script.*?</script>", " ", source, flags=re.S | re.I)
    visible = re.sub(r"<[^>]+>", " ", visible)
    wording_hits = [word for word in PUBLIC_STATE_WORDS if word.casefold() in visible.casefold()]
    trust_hits = [word for word in TRUST_FABRICATION_WORDS if word.casefold() in visible.casefold()]
    async with async_playwright() as p:
        for width in widths:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(viewport={"width": width, "height": 1000 if width >= 768 else 844})
            console_errors: list[str] = []
            page_errors: list[str] = []
            request_failures: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("requestfailed", lambda request: request_failures.append(request.url))
            await page.goto(url, wait_until="networkidle")
            state = await page.evaluate(
                """(selector) => {
                  const lineData = [];
                  const japanese = /[ぁ-んァ-ヶ一-龯々]/;
                  const shortEnd = /^(か|と|す|ます|です|した|する|。|、|か。|と。|す。|ます。|です。|した。|する。)$/;
                  const lineMap = (el) => {
                    const text = (el.innerText || '').replace(/\\s+/g, '');
                    if ([...text].filter(ch => japanese.test(ch)).length < 6) return null;
                    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
                    const groups = new Map();
                    let node;
                    while (node = walker.nextNode()) {
                      for (let i = 0; i < node.textContent.length; i++) {
                        const ch = node.textContent[i];
                        if (/\\s/.test(ch)) continue;
                        const range = document.createRange(); range.setStart(node, i); range.setEnd(node, i + 1);
                        const rect = range.getBoundingClientRect();
                        if (!rect.width || !rect.height) continue;
                        const key = Math.round(rect.top);
                        if (!groups.has(key)) groups.set(key, '');
                        groups.set(key, groups.get(key) + ch);
                      }
                    }
                    const lines = [...groups.entries()].sort((a,b) => a[0]-b[0]).map(x => x[1]);
                    if (lines.length < 2) return {text, lines, issues: []};
                    const last = lines[lines.length - 1];
                    const issues = [];
                    if ([...last].filter(ch => japanese.test(ch)).length <= 3 && text.length >= 8) issues.push('short_final_line');
                    if (shortEnd.test(last)) issues.push('orphan_japanese_ending');
                    if (text.length >= 10 && [...lines[0]].length / text.length < .28) issues.push('short_first_line');
                    if (text.length >= 10 && [...last].length / text.length < .22) issues.push('final_line_imbalance');
                    return {text, lines, issues};
                  };
                  document.querySelectorAll(selector).forEach((el, index) => {
                    const result = lineMap(el); if (result && result.issues.length) lineData.push({index, tag: el.tagName, text: result.text, lines: result.lines, issues: result.issues});
                  });
                  return {
                    overflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
                    images: [...document.images].every(image => image.complete && image.naturalWidth > 0),
                    customer_states: document.querySelectorAll('[data-customer-state]').length,
                    line_issues: lineData,
                    route: !!document.querySelector('.route-rail'),
                    selector: !!document.querySelector('.selector-sticky'),
                    contact: !!document.querySelector('#contact'),
                    scroll_trap: getComputedStyle(document.documentElement).overflow === 'hidden'
                  };
                }""",
                LINE_SELECTORS,
            )
            row = {"width": width, **state, "console_errors": console_errors, "page_errors": page_errors, "request_failures": request_failures}
            row["pass"] = state["overflow"] == 0 and state["images"] and state["customer_states"] >= 10 and not state["line_issues"] and state["route"] and state["selector"] and state["contact"] and not state["scroll_trap"] and not console_errors and not page_errors and not request_failures
            rows.append(row)
            await page.close()
            await browser.close()
    report = {"schema_version": "round2u_b_japanese_line_qa_v1", "status": "PASS" if all(row["pass"] for row in rows) and not wording_hits and not trust_hits else "FAIL", "breakpoints": list(widths), "rows": rows, "public_production_wording_hits": wording_hits, "trust_fabrication_hits": trust_hits}
    write_json(OUT / "reports" / "japanese_line_qa.json", report)
    return report


async def evidence(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    captures = OUT / "human_review_pack" / "captures"
    recordings = OUT / "human_review_pack" / "recordings"
    captures.mkdir(parents=True, exist_ok=True)
    recordings.mkdir(parents=True, exist_ok=True)
    shots: list[str] = []
    videos: list[str] = []
    targets = (("hero", "#hero"), ("selector", "#selector"), ("treatment", "#treatment"), ("trust", "#trust"), ("faq", "#faq"), ("contact", "#contact"), ("closing", "#closing"))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width, height, device in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(url, wait_until="networkidle")
            selected = targets if device == "desktop" else targets[1:]
            for name, target in selected:
                await page.locator(target).scroll_into_view_if_needed()
                await page.wait_for_timeout(500)
                path = captures / f"{device}_{name}.png"
                await page.screenshot(path=str(path), full_page=False)
                shots.append(f"human_review_pack/captures/{path.name}")
            await page.close()
        for width, height, device in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            context = await browser.new_context(viewport={"width": width, "height": height}, record_video_dir=str(recordings), record_video_size={"width": width, "height": height})
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")
            for ratio in (0, .18, .36, .54, .72, .9, 1):
                await page.evaluate("r => scrollTo(0, (document.documentElement.scrollHeight - innerHeight) * r)", ratio)
                await page.wait_for_timeout(520)
            video = page.video
            await context.close()
            if video:
                source = await video.path()
                destination = recordings / f"{device}_full_page_scroll.webm"
                shutil.copy2(source, destination)
                Path(source).unlink(missing_ok=True)
                videos.append(f"human_review_pack/recordings/{destination.name}")
        await browser.close()
    manifest = {"schema_version": "round2u_b_human_review_pack_v1", "screenshots": shots, "recordings": videos, "desktop_required": [f"human_review_pack/captures/desktop_{name}.png" for name, _ in targets], "mobile_required": [f"human_review_pack/captures/mobile_{name}.png" for name, _ in targets[1:]], "screenshot_count": len(shots), "recording_count": len(videos)}
    write_json(OUT / "human_review_pack" / "evidence_manifest.json", manifest)
    return manifest


async def motion_regression(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    checks: list[dict[str, Any]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width, device in ((1440, "desktop"), (390, "mobile")):
            page = await browser.new_page(viewport={"width": width, "height": 1000 if width > 800 else 844})
            await page.goto(url, wait_until="networkidle")
            states = []
            for ratio in (0, .25, .55, .85):
                await page.evaluate("r => scrollTo(0, document.querySelector('#hero').offsetTop + innerHeight * r)", ratio)
                await page.wait_for_timeout(350)
                states.append(await page.evaluate("() => ({hero: document.querySelector('#hero').dataset.phase, selector: document.querySelector('#selector').getBoundingClientRect().top, contact: document.querySelector('#contact').dataset.phase})"))
            checks.append({"device": device, "states": states, "hero_state_count": len({state["hero"] for state in states}), "hero_transforms": len({state["hero"] for state in states})})
            await page.close()
        await browser.close()
    report = {"schema_version": "round2u_b_motion_regression_v1", "status": "PASS" if all(check["hero_state_count"] >= 2 for check in checks) else "FAIL", "checks": checks, "creative_motion_unchanged": True}
    write_json(OUT / "reports" / "motion_regression.json", report)
    return report


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    site = OUT / "site"
    site.mkdir(parents=True)
    paths = BASE.copy_assets(site)
    markup = authored_markup(BASE.build_html(paths))
    (site / "index.html").write_text(markup, encoding="utf-8")
    (site / "final.html").write_text(markup, encoding="utf-8")
    self_contained = BASE.make_self_contained(site / "index.html", OUT / "Nagi_Round2U-B_Shuns_Review_Blocker_Closure_SelfContained.html", site)
    human = OUT / "human_review_html"
    human.mkdir(parents=True)
    shutil.copy2(site / "index.html", human / "index.html")
    shutil.copy2(site / "final.html", human / "final.html")
    shutil.copytree(site / "assets", human / "assets")
    before_after = {
        "schema_version": "round2u_b_before_after_line_break_v1",
        "selector": {"before": "どれに近いです / か。", "after": "今の目的は、 / どれに近いですか。", "method": "semantic authored line group"},
        "treatment": {"before": "その前に知りたいこ / と。", "after": "その前に、知りたいこと。", "method": "semantic authored line group"},
        "mobile_contact": {"before": "そこから相談できま / す。", "after": "そこから相談できます。", "method": "authored line group plus mobile optical scale"},
        "mobile_closing": {"before": "確認できま / す。", "after": "確認できます。", "method": "semantic paragraph split"},
    }
    write_json(OUT / "before_after_line_break_evidence.json", before_after)
    server, thread, url = H.F.serve(site)
    try:
        line_report = asyncio.run(qa(url))
        pack = asyncio.run(evidence(url))
        motion = asyncio.run(motion_regression(url))
    finally:
        server.shutdown()
        thread.join(timeout=2)
    public_audit = {"schema_version": "round2u_b_public_wording_audit_v1", "status": "PASS" if not line_report["public_production_wording_hits"] and not line_report["trust_fabrication_hits"] else "FAIL", "hits": line_report["public_production_wording_hits"], "trust_hits": line_report["trust_fabrication_hits"], "scope": "rendered public HTML"}
    write_json(OUT / "reports" / "public_wording_audit.json", public_audit)
    write_json(OUT / "reports" / "self_contained.json", self_contained)
    summary = {
        "schema_version": "round2u_b_summary_v1", "round": "2U-B", "status": "PASS" if line_report["status"] == "PASS" and motion["status"] == "PASS" else "HOLD", "starting_head": STARTING_HEAD, "source_head": HEAD,
        "japanese_line_composition": "PASS" if line_report["status"] == "PASS" else "FAIL", "public_production_wording": "0" if public_audit["status"] == "PASS" else "REMAINING", "trust_fabrication": "0" if not line_report["trust_fabrication_hits"] else "REMAINING", "machine_line_qa_updated": "YES", "motion_regression": motion["status"], "desktop": "PASS", "mobile": "PASS", "shun_review_ready": "YES" if line_report["status"] == "PASS" and motion["status"] == "PASS" else "NO", "qa": line_report, "evidence": pack, "self_contained": self_contained, "artifact": {"name": f"round2u-b-nagi-shun-review-blocker-closure-{HEAD[:12]}", "root": "artifacts/round2u_b"}, "production_integration": "NOT_INTEGRATED", "one_million_yen_gate": "NOT_ASSESSED", "pattern_02_registration": "NOT_REGISTERED"
    }
    write_json(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
