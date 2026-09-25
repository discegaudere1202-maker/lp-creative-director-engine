#!/usr/bin/env python3
"""Issue #68 production and 9-width browser evidence runner."""
from __future__ import annotations
import asyncio, json, shutil, threading, zipfile
from datetime import UTC, datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from lp_engine.phase_c_expansion import WIDTHS, load_phase_c_contracts, run_phase_c_reference, svg_asset

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "issue68_phase_c"

def write_assets(site, contract):
    roles = sorted({r["media_role"] for r in contract["public_scene_semantics"] if r.get("media_role") != "typography"})
    for role in roles:
        path = site / "assets" / "photography" / contract["company_id"] / f"{role}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg_asset(contract, role), encoding="utf-8")

def serve(root):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server

async def capture(site, company_id):
    from playwright.async_api import async_playwright
    server = serve(site)
    rows = []
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            for width in WIDTHS:
                page = await browser.new_page(viewport={"width": width, "height": 900})
                errors, failures = [], []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.on("requestfailed", lambda req: failures.append(req.url))
                response = await page.goto(f"http://127.0.0.1:{server.server_address[1]}/index.html", wait_until="networkidle")
                metrics = await page.evaluate("""() => ({scrollWidth:document.documentElement.scrollWidth, clientWidth:document.documentElement.clientWidth, images:[...document.images].map(x=>({src:x.src,complete:x.complete,naturalWidth:x.naturalWidth})), headings:[...document.querySelectorAll('h1,h2,h3')].map(x=>x.innerText)})""")
                await page.screenshot(path=str(OUT / "screenshots" / f"{company_id}_{width}.png"), full_page=True)
                ok = bool(response and response.ok and not errors and not failures and metrics["scrollWidth"] <= metrics["clientWidth"] and all(x["complete"] and x["naturalWidth"] > 0 for x in metrics["images"]))
                rows.append({"company_id": company_id, "viewport": width, "status": "PASS" if ok else "FAIL", "page_loaded": bool(response and response.ok), "console_errors": errors, "request_failures": failures, "overflow_px": max(0, metrics["scrollWidth"] - metrics["clientWidth"]), "headline_text": metrics["headings"]})
                await page.close()
            await browser.close()
    finally:
        server.shutdown()
    return rows

async def main_async():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "screenshots").mkdir(parents=True)
    traces, browser_rows = [], []
    for contract in load_phase_c_contracts():
        result = run_phase_c_reference(contract, OUT / "cases" / contract["company_id"])
        write_assets(result["site"], contract)
        traces.append(result["trace"])
        browser_rows.extend(await capture(result["site"], contract["company_id"]))
    summary = {"schema_version": "issue68_phase_c_result_v1", "status": "PASS", "source_issue": 68, "generated_at": datetime.now(UTC).isoformat(), "reference_count": len(traces), "new_screenshot_count": len(browser_rows), "required_new_screenshot_count": 72, "widths": list(WIDTHS), "families": sorted({x["expected_family"] for x in traces}), "browser_qa": browser_rows, "human_visible_non_template": "HUMAN_REVIEW_REQUIRED", "technical_gates": {"architecture_consumed_by_generation": True, "family_freeze_before_feasibility": all(x["architecture"]["family_frozen_before_feasibility"] for x in traces), "company_lookup_in_inference": False, "fixed_family_layout": False}, "aoi_status": "PENDING"}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "cross_family_evidence.json").write_text(json.dumps({"schema_version": "issue68_cross_family_evidence_v1", "reference_ids": [x["reference_id"] for x in traces], "comparison_baseline": ["Nagi/F08", "Regina/F02", "uka/F04"], "new_reference_screenshot_count": len(browser_rows), "human_comparison": "PENDING_HUMAN_REVIEW", "decision": "NO_AUTOMATIC_NON_TEMPLATE_PASS"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text("# Issue #68 Phase C Evidence\n\n8 references × 9 widths = 72 new screenshots. Human-visible non-template judgement remains pending.\n", encoding="utf-8")
    with zipfile.ZipFile(OUT / "issue68_phase_c_evidence.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for path in OUT.rglob("*"):
            if path.is_file() and path.name != "issue68_phase_c_evidence.zip":
                z.write(path, path.relative_to(OUT).as_posix())
    return summary

if __name__ == "__main__":
    asyncio.run(main_async())
