"""Package and validate the Round 2S-B lab as one self-contained HTML file."""
from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts" / "round2s_b" / "site" / "motion-lab.html"
OUT = ROOT / "artifacts" / "round2s_b_review" / "Nagi_Round2S-B_Motion_Lab_SelfContained.html"
REPORT = ROOT / "artifacts" / "round2s_b_review" / "self_contained_validation.json"
ASSET_ROOT = ROOT / "artifacts" / "round2s_b" / "site"


def data_uri(path: Path, mime: str | None = None) -> str:
    kind = mime or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{kind};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def package() -> tuple[Path, dict[str, Any]]:
    markup = SOURCE.read_text(encoding="utf-8")
    assets = {
        "assets/photography/nagi_no_mirai/welcome_human.png": ASSET_ROOT / "assets/photography/nagi_no_mirai/welcome_human.png",
        "assets/photography/nagi_no_mirai/sensory_detail.png": ASSET_ROOT / "assets/photography/nagi_no_mirai/sensory_detail.png",
        "assets/photography/nagi_no_mirai/school_learning_context.png": ASSET_ROOT / "assets/photography/nagi_no_mirai/school_learning_context.png",
        "assets/photography/nagi_no_mirai/hero_treatment_space.png": ASSET_ROOT / "assets/photography/nagi_no_mirai/hero_treatment_space.png",
        "assets/photography/nagi_no_mirai/healing_consultation_context.png": ASSET_ROOT / "assets/photography/nagi_no_mirai/healing_consultation_context.png",
        "assets/photography/nagi_no_mirai/hand_technique.jpg": ASSET_ROOT / "assets/photography/nagi_no_mirai/hand_technique.jpg",
    }
    fonts = {
        "Noto Sans JP": ASSET_ROOT / "assets/fonts/NotoSansJP-Variable.ttf",
        "Inter Tight": ASSET_ROOT / "assets/fonts/InterTight-Variable.ttf",
        "Zen Kaku Gothic New": ASSET_ROOT / "assets/fonts/ZenKakuGothicNew-600.ttf",
    }
    for rel, path in assets.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        markup = markup.replace("/" + rel, data_uri(path))
    font_css = "".join(f"@font-face{{font-family:'{name}';src:url({data_uri(path)}) format('truetype');font-style:normal;font-weight:100 900;font-display:swap;}}" for name, path in fonts.items())
    markup = re.sub(r"<style>", f"<style>{font_css}", markup, count=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(markup, encoding="utf-8")
    report = {"schema_version": "round2s_b_self_contained_package_v1", "source": str(SOURCE), "output": OUT.name, "single_file": True, "embedded_images": len(assets), "embedded_fonts": len(fonts), "external_asset_references": bool(re.search(r"(?:src|href)=[\"'](?:/|assets/|https?://)", markup)), "production_integration": "NOT_INTEGRATED"}
    return OUT, report


async def validate(path: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    rows = []
    uri = path.resolve().as_uri()
    async with async_playwright() as p:
        for width, height, device in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(viewport={"width": width, "height": height})
            console_errors: list[str] = []; page_errors: list[str] = []; request_failures: list[str] = []
            page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
            page.on("pageerror", lambda error: page_errors.append(str(error)))
            page.on("requestfailed", lambda request: request_failures.append(request.url))
            await page.goto(uri, wait_until="load")
            await page.evaluate("window.__labSet('hero','B','mid'); window.__labSet('merge','D','end')")
            await page.locator('[data-exp="selector"] [data-choice="school"]').click()
            await page.locator('[data-exp="ambient"] .ambient-button').first.focus()
            state = await page.evaluate("""()=>({
                labSet:typeof window.__labSet==='function',
                images:[...document.images].map(x=>x.src.startsWith('data:')&&x.complete&&x.naturalWidth>0),
                external:[...document.querySelectorAll('img,source,link,script')].map(x=>x.src||x.href||'').filter(x=>x&& !x.startsWith('data:') && !x.startsWith('file:')),
                overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),
                selected:document.querySelector('[data-exp="selector"] [data-choice="school"]').getAttribute('aria-pressed')==='true',
                hero:document.querySelector('[data-exp="hero"]').dataset.phase,
                merge:document.querySelector('[data-exp="merge"]').dataset.phase
            })""")
            row = {"device": device, "width": width, **state, "console_errors": console_errors, "page_errors": page_errors, "request_failures": request_failures}
            row["pass"] = state["labSet"] and all(state["images"]) and not state["external"] and state["overflow"] == 0 and state["selected"] and state["hero"] == "mid" and state["merge"] == "end" and not console_errors and not page_errors and not request_failures
            rows.append(row); await page.close(); await browser.close()
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"]); page = await browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce"); await page.goto(uri, wait_until="load"); reduced = await page.evaluate("matchMedia('(prefers-reduced-motion: reduce)').matches && typeof window.__labSet==='function'"); await page.close(); await browser.close()
    report = {"schema_version": "round2s_b_self_contained_validation_v1", "status": "PASS" if all(row["pass"] for row in rows) and reduced else "FAIL", "rows": rows, "reduced_motion": "PASS" if reduced else "FAIL", "motion_integrity": "PASS" if all(row["pass"] for row in rows) and reduced else "FAIL"}
    return report


async def main() -> int:
    output, package_report = package()
    validation = await validate(output)
    report = {**package_report, "status": validation["status"], "motion_integrity": validation["motion_integrity"], "validation": validation}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" and not report["external_asset_references"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
