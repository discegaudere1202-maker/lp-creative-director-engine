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


def aggregate_viewports(results: list[dict]) -> tuple[int, int, int]:
    total = len(results)
    passed = sum(item.get("status") == "PASS" for item in results)
    failed = sum(item.get("status") == "FAIL" for item in results)
    assert passed + failed == total
    return total, passed, failed


def capture_paths(company: str) -> list[str]:
    base = OUT / "human_review" / company
    return [str(base / name) for name in ("desktop_1440.png", "mobile_390.png") if (base / name).is_file()]


def build_summary(reports: list[dict], browser: dict[str, str], commit_sha: str) -> dict:
    total = sum(item["widths"] for item in reports)
    passed = sum(item["pass_count"] for item in reports)
    failed = sum(item["fail_count"] for item in reports)
    assert passed + failed == total
    paths = [path for company in CASES for path in capture_paths(company)]
    critical = any(
        detail.get("console_errors") or detail.get("page_errors") or detail.get("request_failures") or detail.get("horizontal_overflow_px", 0) > 1
        for company in reports for detail in company.get("results", [])
    )
    ready = total == 27 and passed == 27 and failed == 0 and len(paths) == 6 and len(reports) == 3 and all(len(item.get("photo_roles", [])) == 4 for item in reports) and not critical
    return {"overall_status": "PASS" if ready else "FAIL", "qa_viewport_total": total, "qa_pass_count": passed, "qa_fail_count": failed, "captures_total": len(paths), "capture_paths": paths, "companies": reports, "browser": browser, "commit_sha": commit_sha, "human_review_ready": ready, "remaining_issues": [] if ready else ["one or more browser QA, capture, or technical gates failed"]}

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
                result_items = report.to_dict()["results"]
                total, passed, failed = aggregate_viewports(result_items)
                company_report = {"company": company, "status": report.status, "widths": total, "pass_count": passed, "fail_count": failed, "results": result_items, "photo_roles": roles, "desktop_capture": str(captures / "desktop_1440.png"), "mobile_capture": str(captures / "mobile_390.png"), "manual_edit_count": 0}
                (OUT / "reports").mkdir(parents=True, exist_ok=True)
                (OUT / "reports" / f"{company}_browser_qa.json").write_text(json.dumps({"browser": browser, **company_report}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                reports.append(company_report)
            except Exception as exc:
                (OUT / "reports").mkdir(parents=True, exist_ok=True)
                (OUT / "reports" / f"{company}_browser_qa_failure.json").write_text(json.dumps({"company": company, "status": "FAIL", "exception_type": type(exc).__name__, "exception_message": str(exc)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                reports.append({"company": company, "status": "FAIL", "widths": 0, "pass_count": 0, "fail_count": 0, "results": [], "error": str(exc)})
        summary = build_summary(reports, browser, subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip())
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
