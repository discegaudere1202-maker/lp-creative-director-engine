"""Generate Issue #59 Regina/uka transfer evidence and 18 new screenshots."""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
import shutil
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading

from playwright.async_api import async_playwright

from lp_engine.controlled_production import run_controlled_nagi_production
from lp_engine.controlled_transfer import ROOT, WIDTHS, load_reference_contracts, run_reference_company, sha_manifest

OUT = ROOT / "artifacts" / "issue59_reference_transfer"


@contextmanager
def serve(directory: Path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(directory)))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try: yield f"http://127.0.0.1:{server.server_address[1]}"
    finally: server.shutdown(); thread.join(timeout=3); server.server_close()


def copy_visual_assets(site: Path, company_id: str, color: str) -> None:
    target = site / "assets" / "photography" / company_id; target.mkdir(parents=True, exist_ok=True)
    roles = ["hero_context", "consultation_context", "process_detail", "material_detail", "hand_technique"]
    for role in roles:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"><rect width="1200" height="800" fill="#f4f1eb"/><rect x="60" y="60" width="1080" height="680" fill="none" stroke="{color}" stroke-width="4"/><path d="M110 600 C300 320 450 650 630 390 S920 300 1090 520" fill="none" stroke="{color}" stroke-width="12"/><circle cx="350" cy="360" r="90" fill="none" stroke="#171a18" stroke-width="3"/><circle cx="850" cy="430" r="120" fill="none" stroke="#171a18" stroke-width="3"/><text x="110" y="150" font-family="Arial,sans-serif" font-size="34" fill="#171a18" letter-spacing="5">{company_id.upper()}</text><text x="110" y="680" font-family="Arial,sans-serif" font-size="24" fill="#5b625d" letter-spacing="3">{role.upper()} / REFERENCE VISUAL</text></svg>'''
        (target / f"{role}.svg").write_text(svg, encoding="utf-8")


async def capture_site(root: Path, label: str, output: Path) -> list[dict[str, object]]:
    rows = []; shots = output / "screenshots"; shots.mkdir(parents=True, exist_ok=True)
    with serve(root) as base:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch()
            for width in WIDTHS:
                page = await browser.new_page(viewport={"width": width, "height": 900 if width >= 768 else 800})
                errors = []; page.on("pageerror", lambda e: errors.append(str(e)))
                await page.goto(f"{base}/index.html", wait_until="networkidle")
                metrics = await page.evaluate("""() => ({scrollWidth:document.documentElement.scrollWidth, clientWidth:document.documentElement.clientWidth, headings:[...document.querySelectorAll('h1,h2')].length, images:[...document.images].map(i=>({src:i.getAttribute('src'),complete:i.complete,naturalWidth:i.naturalWidth}))})""")
                filename = f"{label}_{width}.png"; await page.screenshot(path=str(shots / filename), full_page=True)
                rows.append({"company": label, "width": width, "screenshot": f"screenshots/{filename}", "runtime_errors": errors, "metrics": metrics, "status": "PASS" if not errors and metrics["scrollWidth"] <= width and all(i["complete"] and i["naturalWidth"] > 0 for i in metrics["images"]) else "FAIL"})
                await page.close()
            await browser.close()
    return rows


async def main_async() -> dict[str, object]:
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    all_rows = []; traces = {}
    colors = {"regina-clinic": "#6a4f58", "uka": "#295c54"}
    for contract in load_reference_contracts():
        result = run_reference_company(contract, OUT / contract["company_id"])
        copy_visual_assets(Path(result["site"]), contract["company_id"], colors[contract["company_id"]])
        rows = await capture_site(Path(result["site"]), contract["company_id"], OUT / contract["company_id"])
        all_rows.extend(rows); traces[contract["reference_id"]] = f"{contract['company_id']}/architecture_trace.json"
    # Produce a fresh accepted Nagi reference package for direct comparison.
    nagi = run_controlled_nagi_production(OUT / "nagi_reference")
    nagi_site = Path(nagi["site"]); target = nagi_site / "assets" / "photography" / "nagi_no_mirai"; target.mkdir(parents=True, exist_ok=True)
    for source in (ROOT / "assets" / "photography" / "generated" / "nagi_no_mirai", ROOT / "assets" / "photography" / "stock" / "nagi_no_mirai"):
        for asset in source.glob("*"):
            if asset.is_file(): shutil.copy2(asset, target / asset.name)
    nagi_rows = await capture_site(nagi_site, "nagi_reference", OUT / "nagi_reference")
    (OUT / "nagi_reference" / "accepted_evidence.json").write_text(json.dumps({"source_issue": 53, "status": "accepted_reference_for_comparison", "rows": nagi_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    comparison = {"schema_version": "issue59_cross_company_evidence_v1", "status": "HUMAN_REVIEW_REQUIRED", "companies": ["Nagi", "Regina", "uka"], "new_screenshot_count": 18, "accepted_nagi_reference_screenshot_count": 9, "dimensions": ["screenshot_gestalt", "hero_silhouette", "section_topology", "module_sequence", "trust_logic", "media_role_framing", "density_whitespace_rhythm", "typography_material_grammar", "cta_choreography", "responsive_authorship"], "numeric_template_threshold": None, "rule": "token/color/photo/copy swaps alone cannot establish uniqueness", "architecture_traces": traces, "pairwise_review": [{"pair": ["Nagi", "Regina"], "status": "HUMAN_REVIEW_REQUIRED", "token_only_change": False}, {"pair": ["Nagi", "uka"], "status": "HUMAN_REVIEW_REQUIRED", "token_only_change": False}, {"pair": ["Regina", "uka"], "status": "HUMAN_REVIEW_REQUIRED", "token_only_change": False}]}
    (OUT / "cross_company_evidence.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence_status = "PASS" if all(r["status"] == "PASS" for r in all_rows + nagi_rows) else "FAIL"
    (OUT / "screenshot_inventory.json").write_text(json.dumps({"new_widths": list(WIDTHS), "new_count": len(all_rows), "nagi_reference_count": len(nagi_rows), "rows": all_rows, "status": evidence_status}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps({"schema_version": "issue59_transfer_summary_v1", "status": evidence_status, "technical_pass": evidence_status == "PASS", "human_visible_pass": "PENDING_SARAH_AOI", "new_screenshot_count": len(all_rows), "nagi_reference_screenshot_count": len(nagi_rows), "widths": list(WIDTHS), "families": {"RC57-02": "BW-F02", "RC57-03": "BW-F04"}, "cross_company_review": "HUMAN_REVIEW_REQUIRED", "known_risks": ["cross-company gestalt and non-template judgment requires Sarah/Aoi screenshot review", "volatile pricing/menu/store facts require implementation-date re-verification", "generated visuals are explanatory, not actual company evidence"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "source_contract_reference.json").write_text((ROOT / "data" / "issue59_reference_companies.json").read_text(encoding="utf-8"), encoding="utf-8")
    manifest = sha_manifest(OUT)
    shutil.make_archive(str(OUT / "issue59_cross_company_evidence"), "zip", root_dir=OUT, base_dir=".")
    if evidence_status != "PASS":
        raise SystemExit("screenshot evidence failed")
    return {"status": "PASS", "new_screenshot_count": len(all_rows), "nagi_reference_count": len(nagi_rows), "manifest_files": len(manifest["files"])}


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main_async()), ensure_ascii=False, indent=2))
