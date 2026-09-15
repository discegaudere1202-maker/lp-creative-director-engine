from __future__ import annotations

import asyncio
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image, ImageFilter, ImageOps
from playwright.async_api import async_playwright
from .visual_metrics import analyze_vertical_rhythm, analyze_regions


@dataclass
class VisualArtifact:
    width: int
    fullpage: str
    grayscale: str
    blur: str
    logo_off: str
    sections: list[str] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    page_errors: list[str] = field(default_factory=list)
    rhythm_metrics: dict[str, Any] = field(default_factory=dict)
    section_pixel_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class VisualQAReport:
    source: str
    artifacts: list[VisualArtifact]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status,
            "artifacts": [asdict(a) for a in self.artifacts],
        }


def _prepare(source: str) -> dict[str, str]:
    if re.match(r"^https?://", source):
        return {"mode": "url", "value": source}
    path = Path(source).resolve()
    return {"mode": "html", "value": path.read_text(encoding="utf-8")}


async def _load(page, prepared: dict[str, str]) -> None:
    if prepared["mode"] == "url":
        await page.goto(prepared["value"], wait_until="networkidle", timeout=60000)
    else:
        await page.set_content(prepared["value"], wait_until="load", timeout=60000)
    await page.wait_for_timeout(2200)


async def _warm_scroll(page) -> None:
    metrics = await page.evaluate("""() => ({h: document.documentElement.scrollHeight, vh: window.innerHeight})""")
    total = int(metrics.get("h", 0))
    vh = max(300, int(metrics.get("vh", 800)))
    step = max(240, int(vh * 0.72))
    y = 0
    while y < total:
        await page.evaluate("(y)=>window.scrollTo(0,y)", y)
        await page.wait_for_timeout(70)
        y += step
    await page.evaluate("()=>window.scrollTo(0, document.documentElement.scrollHeight)")
    await page.wait_for_timeout(150)
    await page.evaluate("()=>window.scrollTo(0,0)")
    await page.wait_for_timeout(350)


def _make_variants(src: Path, gray: Path, blur: Path) -> None:
    with Image.open(src) as im:
        rgb = im.convert("RGB")
        ImageOps.grayscale(rgb).convert("RGB").save(gray, quality=88)
        rgb.filter(ImageFilter.GaussianBlur(radius=12)).save(blur, quality=84)


def _safe_name(value: str, fallback: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]+", "-", value).strip("-")
    return (value[:60] or fallback)


async def run_visual_qa(
    source: str,
    out_dir: str | Path,
    widths: list[int] | None = None,
    height: int = 1000,
    logo_selector: str = ".brand,.logo,[data-qa-brand]",
    section_selector: str = "[data-screenshot-peak]",
    fallback_section_selector: str = "section",
    max_sections: int = 12,
    executable_path: str | None = "/usr/bin/chromium",
) -> VisualQAReport:
    widths = widths or [390, 1440]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prepared = _prepare(source)
    artifacts: list[VisualArtifact] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            executable_path=executable_path if executable_path and Path(executable_path).exists() else None,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        for width in widths:
            console_errors: list[str] = []
            page_errors: list[str] = []
            page = await browser.new_page(viewport={"width": width, "height": height})

            def on_console(msg):
                if msg.type == "error":
                    console_errors.append(msg.text)

            def on_page_error(exc):
                page_errors.append(str(exc))

            page.on("console", on_console)
            page.on("pageerror", on_page_error)
            await _load(page, prepared)
            await _warm_scroll(page)

            region_bounds = await page.evaluate("""() => {
              const total = Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0) || 1;
              const els = [...document.querySelectorAll('section')].filter(el => {
                const r = el.getBoundingClientRect();
                const s = getComputedStyle(el);
                return r.height > 2 && s.display !== 'none' && s.visibility !== 'hidden';
              });
              return els.map((el, i) => {
                const r = el.getBoundingClientRect();
                const top = r.top + window.scrollY;
                const bottom = top + r.height;
                return {
                  id: el.id || el.getAttribute('data-section-id') || `section-${i+1}`,
                  y_start_ratio: Math.max(0, Math.min(1, top / total)),
                  y_end_ratio: Math.max(0, Math.min(1, bottom / total)),
                };
              });
            }""")

            full = out_dir / f"{width}_fullpage.png"
            gray = out_dir / f"{width}_grayscale.jpg"
            blur = out_dir / f"{width}_blur.jpg"
            logo_off = out_dir / f"{width}_logo_off.png"

            await page.screenshot(path=str(full), full_page=True)
            _make_variants(full, gray, blur)
            rhythm_metrics = analyze_vertical_rhythm(full)
            section_pixel_metrics = analyze_regions(full, region_bounds)

            style_id = await page.evaluate(
                """(selector) => {
                    const s = document.createElement('style');
                    s.id = 'lp-engine-logo-off';
                    s.textContent = `${selector}{visibility:hidden!important}`;
                    document.head.appendChild(s);
                    return s.id;
                }""",
                logo_selector,
            )
            await page.screenshot(path=str(logo_off), full_page=True)
            await page.evaluate("""(id)=>document.getElementById(id)?.remove()""", style_id)

            section_paths: list[str] = []
            if width == max(widths):
                count = await page.locator(section_selector).count()
                selector_used = section_selector
                if count == 0:
                    count = await page.locator(fallback_section_selector).count()
                    selector_used = fallback_section_selector
                count = min(count, max_sections)
                for i in range(count):
                    loc = page.locator(selector_used).nth(i)
                    try:
                        await loc.scroll_into_view_if_needed(timeout=3000)
                        meta = await loc.evaluate(
                            """(el)=>({id:el.id||'', cls:typeof el.className==='string'?el.className:''})"""
                        )
                        label = _safe_name(meta.get("id") or meta.get("cls") or "", f"section-{i+1:02d}")
                        path = out_dir / f"{width}_section_{i+1:02d}_{label}.png"
                        await loc.screenshot(path=str(path), timeout=10000)
                        section_paths.append(str(path))
                    except Exception:
                        continue

            artifacts.append(
                VisualArtifact(
                    width=width,
                    fullpage=str(full),
                    grayscale=str(gray),
                    blur=str(blur),
                    logo_off=str(logo_off),
                    sections=section_paths,
                    console_errors=console_errors,
                    page_errors=page_errors,
                    rhythm_metrics=rhythm_metrics,
                    section_pixel_metrics=section_pixel_metrics,
                )
            )
            await page.close()

        await browser.close()

    status = "PASS" if all(not a.console_errors and not a.page_errors for a in artifacts) else "HOLD"
    report = VisualQAReport(source=source, artifacts=artifacts, status=status)
    (out_dir / "visual_qa_report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def run_visual_qa_sync(*args, **kwargs) -> VisualQAReport:
    return asyncio.run(run_visual_qa(*args, **kwargs))
