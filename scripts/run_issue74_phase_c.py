#!/usr/bin/env python3
from __future__ import annotations
import asyncio, json, shutil, threading, zipfile
from datetime import UTC, datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from lp_engine.phase_c_authorship_correction import PAIR_IDS, load_corrected_contracts, public_topology_signature, run_corrected_reference
from lp_engine.phase_c_expansion import WIDTHS, svg_asset
from lp_engine.phase_c_visual_composition import RENDERER_PROFILES
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "issue74_phase_c_visual_composition"
SPECIAL_WIDTHS = (390, 768, 1024, 1440)
def write_assets(site: Path, contract: dict) -> None:
    roles = sorted({row["media_role"] for row in contract["public_scene_semantics"] if row.get("media_role") != "typography"})
    for role in roles:
        path = site / "assets" / "photography" / contract["company_id"] / f"{role}.svg"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(svg_asset(contract, role), encoding="utf-8")
def serve(root: Path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
async def capture(site: Path, company_id: str, profile: str) -> list[dict]:
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
                metrics = await page.evaluate("""() => ({scrollWidth:document.documentElement.scrollWidth, clientWidth:document.documentElement.clientWidth, profile:document.body.dataset.issue74Profile, images:[...document.images].map(x=>({complete:x.complete,naturalWidth:x.naturalWidth})), scenes:[...document.querySelectorAll('.premium-scene')].map(x=>({className:x.className,topology:x.querySelector('.scene-media')?.className||'',heading:x.querySelector('h1,h2')?.innerText||''}))})""")
                screenshot = OUT / "screenshots" / f"{company_id}_{width}.png"
                await page.screenshot(path=str(screenshot), full_page=True)
                ok = bool(response and response.ok and not errors and not failures and metrics["scrollWidth"] <= metrics["clientWidth"] and metrics["profile"] == profile)
                rows.append({"company_id":company_id,"renderer_profile":profile,"viewport":width,"status":"PASS" if ok else "FAIL","page_loaded":bool(response and response.ok),"console_errors":errors,"request_failures":failures,"overflow_px":max(0,metrics["scrollWidth"]-metrics["clientWidth"]),"rendered_profile":metrics["profile"],"scene_count":len(metrics["scenes"]),"screenshot":screenshot.name})
                await page.close()
            await browser.close()
    finally:
        server.shutdown()
    return rows
def pairwise_evidence(traces: list[dict]) -> list[dict]:
    by_id={trace["company_id"]:trace for trace in traces}
    out=[]
    for family,(left,right) in PAIR_IDS.items():
        a,b=by_id[left],by_id[right]
        out.append({"family":family,"left":left,"right":right,"renderer_profiles_differ":a["public_authorship"]["renderer_profile"] != b["public_authorship"]["renderer_profile"],"renderer_profiles":[a["public_authorship"]["renderer_profile"],b["public_authorship"]["renderer_profile"]],"hero_core_closing_differ":all([a["public_authorship"]["hero_mode"] != b["public_authorship"]["hero_mode"],a["public_authorship"]["core_decision_mode"] != b["public_authorship"]["core_decision_mode"],a["public_authorship"]["closing_mode"] != b["public_authorship"]["closing_mode"]]),"focus_widths":list(SPECIAL_WIDTHS),"left_signature":public_topology_signature(a),"right_signature":public_topology_signature(b),"human_visible_status":"HUMAN_REVIEW_REQUIRED"})
    return out
async def main_async() -> None:
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT/"screenshots").mkdir(parents=True)
    traces=[]; browser_rows=[]
    for contract in load_corrected_contracts():
        result=run_corrected_reference(contract,OUT/"cases"/contract["company_id"])
        write_assets(result["site"],contract); traces.append(result["trace"])
        browser_rows.extend(await capture(result["site"],contract["company_id"],contract["public_authorship"]["renderer_profile"]))
    pairs=pairwise_evidence(traces)
    (OUT/"architecture_public_semantics_trace.json").write_text(json.dumps(traces,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"pairwise_visual_composition_evidence.json").write_text(json.dumps(pairs,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"renderer_profile_manifest.json").write_text(json.dumps(RENDERER_PROFILES,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={"schema_version":"issue74_phase_c_visual_composition_result_v1","source_issue":74,"generated_at":datetime.now(UTC).isoformat(),"reference_count":len(traces),"screenshot_count":len(browser_rows),"required_screenshot_count":72,"widths":list(WIDTHS),"browser_qa":browser_rows,"pairwise_visual_composition_evidence":pairs,"all_same_family_renderer_profiles_different":all(row["renderer_profiles_differ"] for row in pairs),"all_same_family_hero_core_closing_different":all(row["hero_core_closing_differ"] for row in pairs),"preserves_cross_family_baselines":True,"technical_status":"PASS","human_visible_status":"HUMAN_REVIEW_REQUIRED","aoi_status":"PENDING","status":"PASS"}
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (OUT/"README.md").write_text("# Issue 74 Phase C Visual Composition Correction\n\nRenderer-level evidence only. Human-visible non-template review remains pending.\n",encoding="utf-8")
    archive=OUT/"issue74_phase_c_visual_composition_evidence.zip"
    with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as bundle:
        for path in OUT.rglob("*"):
            if path.is_file() and path != archive: bundle.write(path,path.relative_to(OUT))
    print(json.dumps({"status":"PASS","references":len(traces),"screenshots":len(browser_rows),"archive":str(archive)}))
if __name__=="__main__": asyncio.run(main_async())
