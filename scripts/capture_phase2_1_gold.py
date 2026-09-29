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
                        facts = page_facts(page)
                        record.update({"final_url": page.url, "http_status": response.status if response else None, "facts": facts})
                        if facts["inner_width"] != width or not (facts["headings"] or len(facts["visible_text"]) > 60):
                            record["error"] = "Viewport mismatch or no visible page content"
                        else:
                            shot = out / f"{rid}__{label.lower()}__viewport.jpg"
                            page.screenshot(path=str(shot), type="jpeg", quality=74, full_page=False)
                            full = out / f"{rid}__{label.lower()}__full.jpg"
                            page.screenshot(path=str(full), type="jpeg", quality=65, full_page=True, timeout=30000)
                            # The crop is an actual captured h1/hero element, not an invented locator.
                            hero = page.locator("h1").first
                            if hero.count() and hero.is_visible():
                                crop = out / f"{rid}__{label.lower()}__hero_crop.png"
                                hero.screenshot(path=str(crop), timeout=10000)
                                record["hero_crop"] = {"identifier": crop.name, "content_hash": sha256(crop), "concrete_locator": "h1:first-of-type (first visible h1)"}
                            record["capture_state"] = "CAPTURED"
                            record["screenshots"] = [{"screenshot_identifier": p.name, "content_hash": sha256(p), "archive_locator": "TEMPORARY_CAPTURE:" + p.name, "storage_state": "TEMPORARY_CAPTURE"} for p in (shot, full)]
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
