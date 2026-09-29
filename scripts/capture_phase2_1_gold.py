"""Evidence-only Playwright capture for the selected existing pilot references.

Does not score or mint mechanisms. Every observation and screenshot is emitted with
its actual URL/viewport/hash; failures remain failures. This is not a crawler.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = {"DESKTOP": (1440, 1000), "MOBILE": (390, 844)}
CONSENT_ACTIONS = {
    "P04-R01": ("必要なCookieのみ",),
    "P09-R01": ("全て拒否",),
    "P10-R02": ("Decline all",),
    "P16-R03": ("Accept All Cookies",),
    "P19-R01": ("Reject All",),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_facts(page):
    return page.evaluate("""() => {
      const clean = s => (s || '').replace(/\\s+/g, ' ').trim().slice(0, 500);
      const rect = e => { const r=e.getBoundingClientRect(); return {
        x:Math.round(r.x),y:Math.round(r.y+scrollY),w:Math.round(r.width),h:Math.round(r.height)
      }};
      const items = sel => [...document.querySelectorAll(sel)].slice(0,40).map((e,i)=>({
        index:i,tag:e.tagName.toLowerCase(),text:clean(e.innerText || e.getAttribute('aria-label')),
        href:e.href || null,alt:e.getAttribute('alt'),src:e.currentSrc || null,
        rect:rect(e),font:getComputedStyle(e).fontFamily,
        font_size:getComputedStyle(e).fontSize
      })).filter(e=>e.text || e.alt || e.src);
      return {title:document.title,document_url:location.href,inner_width:innerWidth,
        inner_height:innerHeight,scroll_width:document.documentElement.scrollWidth,
        scroll_height:document.documentElement.scrollHeight,
        headings:items('h1,h2,h3'),sections:items('main section,main article,section,article'),
        actions:items('a,button'),images:items('main img,img'),
        visible_text:clean(document.body?.innerText).slice(0,500),
        main_actions:items('main a,main button'),
        has_main:!!document.querySelector('main'),
        video_count:document.querySelectorAll('video').length,
        prefers_reduced_motion:matchMedia('(prefers-reduced-motion: reduce)').matches};
    }""")


def capture(out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    selection = json.loads((ROOT / "config/creative_mechanism_phase2_1_gold_selection.json").read_text())
    rows = {r["reference_id"]: r for r in csv.DictReader((ROOT / "data/creative_mechanism_phase2_pilot_references.csv").open(newline="", encoding="utf-8"))}
    report = {"schema_version": "phase2.1-capture-v1", "created_at": datetime.now(timezone.utc).isoformat(), "selection": selection["reference_ids"], "records": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for rid in selection["reference_ids"]:
                r = rows[rid]
                for label, (width, height) in VIEWPORTS.items():
                    context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1, locale="ja-JP", reduced_motion="reduce")
                    page = context.new_page()
                    record = {"reference_id": rid, "viewport_label": label, "viewport": {"width": width, "height": height}, "original_url": r["url"], "capture_state": "MISSING", "captured_at": datetime.now(timezone.utc).isoformat(), "evidence_source_role": "ORIGINAL_LIVE"}
                    try:
                        response = page.goto(r["url"], wait_until="domcontentloaded", timeout=40000)
                        page.wait_for_timeout(1800)
                        for consent_label in CONSENT_ACTIONS.get(rid, ()):
                            button = page.get_by_text(consent_label, exact=True).first
                            if button.count() and button.is_visible():
                                button.click(timeout=5000)
                                record["consent_action"] = consent_label
                                page.wait_for_timeout(400)
                                break
                        try:
                            facts = page_facts(page)
                        except Exception as first_error:
                            # Locale redirects can replace the document immediately after DOMContentLoaded.
                            # One ordinary re-observation only; do not retry access-denied pages.
                            if "Execution context was destroyed" not in str(first_error):
                                raise
                            page.wait_for_load_state("domcontentloaded", timeout=15000)
                            facts = page_facts(page)
                        record.update({"final_url": page.url, "http_status": response.status if response else None, "facts": facts})
                        blocked = (response and response.status >= 400) or any(x in facts["title"].lower() for x in ("access denied", "forbidden", "error 403"))
                        if blocked or facts["inner_width"] != width or not (facts["headings"] or len(facts["visible_text"]) > 60):
                            record["error"] = "HTTP error / denied page, viewport mismatch, or no visible page content"
                        else:
                            shot = out / f"{rid}__{label.lower()}__viewport.jpg"
                            page.screenshot(path=str(shot), type="jpeg", quality=74, full_page=False)
                            full = out / f"{rid}__{label.lower()}__full.jpg"
                            page.screenshot(path=str(full), type="jpeg", quality=65, full_page=True, timeout=30000)
                            # The crop is an actual captured h1-containing scene, not an invented locator.
                            hero = page.locator("h1").first
                            if hero.count() and hero.is_visible():
                                crop = out / f"{rid}__{label.lower()}__hero_crop.png"
                                scene = hero.locator("xpath=parent::*")
                                scene.screenshot(path=str(crop), timeout=10000)
                                record["hero_crop"] = {"identifier": crop.name, "content_hash": sha256(crop), "concrete_locator": "parent of first visible h1"}
                            else:
                                crop = out / f"{rid}__{label.lower()}__hero_crop.png"
                                page.screenshot(path=str(crop), type="png", full_page=False)
                                record["hero_crop"] = {"identifier": crop.name, "content_hash": sha256(crop), "concrete_locator": "initial viewport (no visible h1)"}
                            record["capture_state"] = "CAPTURED"
                            record["screenshots"] = [{"screenshot_identifier": p.name, "content_hash": sha256(p), "archive_locator": "TEMPORARY_CAPTURE:" + p.name, "storage_state": "TEMPORARY_CAPTURE"} for p in (shot, full)]
                            # Observe a second, actual in-browser scene after scrolling.
                            # Full-page stitching alone does not validate lazy media/UI.
                            page.evaluate("""() => window.scrollTo(0, Math.min(document.documentElement.scrollHeight - innerHeight, innerHeight))""")
                            page.wait_for_timeout(700)
                            scroll_y = page.evaluate("window.scrollY")
                            if scroll_y > 0:
                                section = out / f"{rid}__{label.lower()}__section.jpg"
                                page.screenshot(path=str(section), type="jpeg", quality=75, full_page=False)
                                record["section_capture"] = {
                                    "observation_state": "OBSERVED", "scroll_y": scroll_y,
                                    "captured_at": datetime.now(timezone.utc).isoformat(),
                                    "facts": page_facts(page), "scene_crop_identifier": section.name,
                                    "screenshot_identifier": section.name, "content_hash": sha256(section),
                                    "archive_locator": "TEMPORARY_CAPTURE:" + section.name,
                                }
                            else:
                                record["section_capture"] = {"observation_state": "NOT_APPLICABLE", "reason": "No vertical scroll range in captured page"}
                    except Exception as exc:
                        record.update({"final_url": page.url, "error": f"{type(exc).__name__}: {str(exc)[:350]}"})
                    finally:
                        report["records"].append(record)
                        print(f"{rid} {label} {record['capture_state']} {record.get('final_url','')}", flush=True)
                        context.close()
        finally:
            browser.close()
    (out / "capture_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/phase2_1_gold_capture"))
    args = parser.parse_args()
    result = capture(args.output)
    print(f"CAPTURED {sum(r['capture_state']=='CAPTURED' for r in result['records'])}/{len(result['records'])}")
