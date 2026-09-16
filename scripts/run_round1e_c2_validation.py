"""GitHub Actions orchestration for Round 1E-C2 browser validation."""
from __future__ import annotations
import asyncio
import importlib.metadata
import json
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.async_api import async_playwright
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/round1e_c"
CASES = {"maylynn_paint": ["hero_home_finish", "craft_handwork", "material_detail", "trust_consultation"], "nagi_no_mirai": ["hero_treatment_space", "hand_technique", "sensory_detail", "welcome_human"], "watashi_no_daidokoro": ["hero_shared_cooking", "ingredient_story", "hands_in_action", "finished_table"]}

def write_failure(stage: str, exc: BaseException) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {"overall_status": "FAIL", "stage": stage, "exception_type": type(exc).__name__, "exception_message": str(exc), "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "human_review_ready": False}
    (OUT / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

async def smoke() -> dict[str, str]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content("<html><body>Round 1E-C2 smoke</body></html>")
        assert await page.locator("body").inner_text() == "Round 1E-C2 smoke"
        version = browser.version
        await browser.close()
        return {"playwright": importlib.metadata.version("playwright"), "chromium": version}

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *a, **kw: SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        try:
            browser = asyncio.run(smoke())
        except Exception as exc:
            write_failure("browser_smoke", exc)
            return 1
        reports = []
        for company, roles in CASES.items():
            artifact = ROOT / "artifacts/round1e_b" / company
            out = OUT / "browser_qa" / company
            try:
                report = asyncio.run(run_browser_qa(f"http://127.0.0.1:{server.server_port}/artifacts/round1e_b/{company}/index.html", out, DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440]))
                captures = OUT / "human_review" / company
                captures.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(out / "1440_fullpage.png", captures / "desktop_1440.png")
                shutil.copyfile(out / "390_fullpage.png", captures / "mobile_390.png")
                reports.append({"company": company, "status": report.status, "widths": len(report.results), "desktop_capture": str(captures / "desktop_1440.png"), "mobile_capture": str(captures / "mobile_390.png")})
            except Exception as exc:
                (OUT / "reports").mkdir(parents=True, exist_ok=True)
                (OUT / "reports" / f"{company}_browser_qa_failure.json").write_text(json.dumps({"company": company, "status": "FAIL", "exception_type": type(exc).__name__, "exception_message": str(exc)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                reports.append({"company": company, "status": "FAIL", "widths": 0, "error": str(exc)})
        summary = {"overall_status": "PASS" if all(x["status"] == "PASS" for x in reports) else "FAIL", "qa_viewport_total": sum(x["widths"] for x in reports), "qa_pass_count": sum(x["widths"] for x in reports if x["status"] == "PASS"), "qa_fail_count": sum(x["widths"] for x in reports if x["status"] != "PASS"), "captures_total": sum(2 for x in reports if x["status"] == "PASS"), "companies": reports, "browser": browser, "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "human_review_ready": all(x["status"] == "PASS" for x in reports), "remaining_issues": [] if all(x["status"] == "PASS" for x in reports) else ["one or more browser QA runs failed"]}
        (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["overall_status"] == "PASS" else 1
    finally:
        server.shutdown()

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        write_failure("orchestration", exc)
        raise
