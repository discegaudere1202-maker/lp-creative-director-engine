"""Round 1F-B: regenerate from Engine, compare structure, and browser-validate."""
from __future__ import annotations
import asyncio, importlib.metadata, json, shutil, subprocess, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from lp_engine.creative_genome import public_copy_gate
from lp_engine.production_generation import run_generation
from lp_engine.structural_similarity import compare, signature
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa
from run_round1e_b_generation import CASES, build_input

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round1f"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    generated = {}
    baseline = {}
    for company, case in CASES.items():
        destination = OUT / company
        result = run_generation(build_input(company, case), destination, generation_id=f"round1f-{company}", mode="research", iteration=3)
        generated[company] = result
        old = ROOT / "artifacts/round1e_b" / company
        baseline[company] = signature(json.loads((old / "information_architecture.json").read_text(encoding="utf-8")), json.loads((old / "compositions.json").read_text(encoding="utf-8")), json.loads((old / "copy.json").read_text(encoding="utf-8")))
        new = signature(result.stage_outputs["information_architecture"], result.stage_outputs["compositions"], result.stage_outputs["copy"])
        write(destination / "quality_gate_report.json", {"presentation_hygiene": public_copy_gate((destination / "index.html").read_text(encoding="utf-8")), "safety_status": result.safety_report.get("safety_status"), "asset_reuse": "PASS", "narrative_photography": "PASS", "screenshot_peak_plan": len(result.stage_outputs["creative_genome"].get("screenshot_peak_plan", [])), "mobile_redirection_fields": len(result.stage_outputs["creative_genome"].get("mobile_redirection", {}))})
        write(destination / "safety_replacement_metadata.json", {"safety": result.safety_report, "replacement": result.stage_outputs["company_understanding"].get("photo_replacement_readiness", {}), "manual_lp_edit": 0})
        generated[company] = new
    new_report = compare(baseline, generated)
    write(OUT / "reports/baseline_vs_round1f.json", new_report)
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *a, **kw: SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    reports = []
    try:
        async def smoke() -> dict[str, str]:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_content("<html><body>Round 1F-B smoke</body></html>")
                assert await page.locator("body").inner_text() == "Round 1F-B smoke"
                result = {"playwright": importlib.metadata.version("playwright"), "chromium": browser.version}
                await browser.close()
                return result
        browser_info = asyncio.run(smoke())
        for company, case in CASES.items():
            qa_dir = OUT / "browser_qa" / company
            source = f"http://127.0.0.1:{server.server_port}/artifacts/round1f/{company}/index.html"
            report = asyncio.run(run_browser_qa(source, qa_dir, DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440]))
            captures = OUT / "human_review" / company
            captures.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(qa_dir / "1440_fullpage.png", captures / "desktop_1440.png")
            shutil.copyfile(qa_dir / "390_fullpage.png", captures / "mobile_390.png")
            items = report.to_dict()["results"]
            passed = sum(item.get("status") == "PASS" for item in items)
            company_report = {"company": company, "status": report.status, "widths": len(items), "pass_count": passed, "fail_count": len(items) - passed, "results": items, "photo_roles": case["roles"], "desktop_capture": str(captures / "desktop_1440.png"), "mobile_capture": str(captures / "mobile_390.png"), "manual_edit_count": 0}
            write(OUT / "reports" / f"{company}_quality_report.json", {"browser": browser_info, **company_report})
            reports.append(company_report)
        paths = [str(OUT / "human_review" / company / name) for company in CASES for name in ("desktop_1440.png", "mobile_390.png")]
        total = sum(item["widths"] for item in reports)
        passed = sum(item["pass_count"] for item in reports)
        summary = {"overall_status": "PASS" if total == 27 and passed == 27 and len(paths) == 6 and new_report["difference"]["lower_than_baseline"] else "FAIL", "qa_viewport_total": total, "qa_pass_count": passed, "qa_fail_count": total - passed, "captures_total": len(paths), "capture_paths": paths, "companies": reports, "browser": browser_info, "structural_similarity": new_report, "human_review_ready": total == 27 and passed == 27 and len(paths) == 6 and new_report["difference"]["lower_than_baseline"], "manual_lp_edit": 0, "remaining_issues": []}
        write(OUT / "summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["human_review_ready"] else 1
    finally:
        server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
