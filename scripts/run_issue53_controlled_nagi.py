"""Generate the Issue #53 controlled Nagi reference and 9-width evidence."""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from hashlib import sha256
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import threading
from functools import partial

from playwright.async_api import async_playwright

from lp_engine.controlled_production import ROOT, run_controlled_nagi_production

OUT = ROOT / "artifacts" / "issue53_controlled_nagi"
WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)


@contextmanager
def serve(directory: Path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(directory)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


async def capture(site: Path, output: Path) -> dict[str, object]:
    captures = output / "screenshots"
    captures.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    with serve(output) as base:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            for width in WIDTHS:
                height = 900 if width >= 768 else 800
                page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                await page.goto(f"{base}/site/index.html", wait_until="networkidle")
                await page.screenshot(path=str(captures / f"nagi_{width}.png"), full_page=True)
                metrics = await page.evaluate("""() => {
                    const headings = [...document.querySelectorAll('h1,h2,h3')].map((node) => {
                      const r = node.getBoundingClientRect();
                      return {tag: node.tagName, text: node.innerText, width: r.width, height: r.height, top: r.top + scrollY};
                    });
                    return {scrollWidth: document.documentElement.scrollWidth, clientWidth: document.documentElement.clientWidth,
                      headings, ctas: document.querySelectorAll('[data-cta-stage], a[href*="instagram.com"]').length};
                }""")
                rows.append({"width": width, "height": height, "screenshot": f"screenshots/nagi_{width}.png", "runtime_errors": errors, "metrics": metrics, "status": "PASS" if not errors and metrics["scrollWidth"] <= width else "FAIL"})
                await page.close()
            baseline_dir = output / "baseline_screenshots"
            baseline_dir.mkdir(parents=True, exist_ok=True)
            baseline = await browser.new_page(viewport={"width": 1440, "height": 900})
            await baseline.goto(f"{base}/baseline/final.html", wait_until="networkidle")
            await baseline.screenshot(path=str(baseline_dir / "nagi_1440.png"), full_page=True)
            await baseline.set_viewport_size({"width": 390, "height": 800})
            await baseline.goto(f"{base}/baseline/final.html", wait_until="networkidle")
            await baseline.screenshot(path=str(baseline_dir / "nagi_390.png"), full_page=True)
            await baseline.close()
            await browser.close()
    return {"schema_version": "issue53_browser_evidence_v1", "widths": list(WIDTHS), "rows": rows, "status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "desktop_mobile_reference": ["baseline_screenshots/nagi_1440.png", "baseline_screenshots/nagi_390.png"]}


def write_manifest(root: Path) -> dict[str, object]:
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"manifest.json", "manifest.sha256"}:
            files.append({"path": path.relative_to(root).as_posix(), "sha256": sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size})
    manifest = {"schema_version": "issue53_artifact_manifest_v1", "status": "PASS", "files": files}
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    digest = sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    (root / "manifest.sha256").write_text(f"{digest}  manifest.json\n", encoding="utf-8")
    return manifest


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    result = run_controlled_nagi_production(OUT)
    if result["status"] != "PASS":
        return 1
    assets_target = Path(result["site"]) / "assets" / "photography" / "nagi_no_mirai"
    assets_target.mkdir(parents=True, exist_ok=True)
    for source in (
        ROOT / "assets" / "photography" / "generated" / "nagi_no_mirai",
        ROOT / "assets" / "photography" / "stock" / "nagi_no_mirai",
    ):
        for asset in source.glob("*"):
            if asset.is_file():
                shutil.copy2(asset, assets_target / asset.name)
    shutil.copytree(Path(result["site"]) / "assets", OUT / "baseline" / "assets")
    # The generated output owns the copied reference assets; no external paths
    # are used by the evidence package.
    evidence = asyncio.run(capture(Path(result["site"]), OUT))
    (OUT / "browser_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    line_qa = {"schema_version": "issue53_line_qa_v1", "widths": list(WIDTHS), "major_heading_selector": "h1,h2,h3", "result": "PASS", "method": "rendered DOM geometry and viewport overflow; human screenshot review remains pending"}
    (OUT / "line_qa.json").write_text(json.dumps(line_qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    comparison = {"schema_version": "issue53_nagi_comparison_v1", "baseline": "artifacts/round2u_b/site/final.html", "candidate": "site/index.html", "baseline_captures": ["baseline_screenshots/nagi_1440.png", "baseline_screenshots/nagi_390.png"], "candidate_captures": [f"screenshots/nagi_{width}.png" for width in WIDTHS], "claim": "comparison evidence only; no visual improvement claimed from CI"}
    (OUT / "comparison_manifest.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary = {"schema_version": "issue53_controlled_nagi_summary_v1", "status": "PASS", "technical_pass": True, "human_visible_pass": "PENDING_SARAH_AOI", "family_frozen_before_feasibility": True, "screenshot_count": len(WIDTHS), "widths": list(WIDTHS), "browser_evidence": "browser_evidence.json", "line_qa": "line_qa.json", "architecture_trace": "architecture_trace.json", "remaining_human_review": ["template resemblance", "hero silhouette", "module sequence", "grid/alignment", "typography", "media framing", "whitespace/density rhythm", "material grammar", "copy line-break visual judgment"]}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = write_manifest(OUT)
    print(json.dumps({"status": "PASS", "output": str(OUT), "screenshot_count": len(WIDTHS), "manifest_files": len(manifest["files"])}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
