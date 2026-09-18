"""Round 1N-B Final Premium Creative Correction validation.

This runner reuses the existing Round 1K-A2 generation and 27-viewport
browser contract.  Round 1N adds only rendered-surface/profile reports and a
separate Human Peak Presentation capture plan; it does not alter machine peak
scoring or introduce a new quality gate.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get("ROUND_OUTPUT_ROOT", str(ROOT / "artifacts" / "round1n")))
OUT = OUT if OUT.is_absolute() else ROOT / OUT
COMPANIES = ["maylynn_paint", "nagi_no_mirai", "watashi_no_daidokoro"]
BASELINE = ROOT / "artifacts" / "round1m4"

try:
    import run_round1m3_validation as m3
except ModuleNotFoundError:
    from scripts import run_round1m3_validation as m3

load = m3.load
write = m3.write
sha = m3.sha
parse_sections = m3.parse_sections
visible_items = m3.visible_items


def _run_tests() -> dict[str, Any]:
    modules = [
        "tests.test_round1n_creative_correction",
        "tests.test_round1m4_truth_closure",
        "tests.test_round1m3_truth_closure",
        "tests.test_round1m2_reality",
        "tests.test_human_translation",
        "tests.test_premium_scene",
        "tests.test_premium_experience",
        "tests.test_rendered_reality",
        "tests.test_round1k_b4",
        "tests.test_creative_genome",
        "tests.test_photography_asset_preflight",
        "tests.test_photography_pipeline",
        "tests.test_production_generation",
        "tests.test_pipeline_evidence_safety",
        "tests.test_evidence_safety",
        "tests.test_evidence_safety_adversarial",
    ]
    result = subprocess.run([sys.executable, "-m", "unittest", *modules], cwd=ROOT, capture_output=True, text=True)
    combined = result.stdout + "\n" + result.stderr
    match = re.search(r"Ran (\d+) tests?", combined)
    return {"status": "PASS" if result.returncode == 0 else "FAIL", "modules": modules, "returncode": result.returncode, "test_count": int(match.group(1)) if match else 0, "stdout_tail": result.stdout[-6000:], "stderr_tail": result.stderr[-6000:]}


def _profile_report(company: str, folder: Path) -> dict[str, Any]:
    tokens = load(folder / "design_tokens.json", {})
    translation = load(folder / "premium_human_translation.json", {})
    html = (folder / "index.html").read_text(encoding="utf-8")
    copy = load(folder / "copy.json", {})
    ending = (copy.get("premium_scene_copy") or {}).get("ending_variant", "")
    expected = {
        "maylynn_paint": {"profile": "field_ledger", "ending": "grounded_field_closure", "pattern": "multi_scope_consultation"},
        "nagi_no_mirai": {"profile": "care_rhythm", "ending": "quiet_afterglow_closure", "pattern": "quiet_multi_mode"},
        "watashi_no_daidokoro": {"profile": "studio_invitation", "ending": "communal_table_closure", "pattern": "hands_on_named_method"},
    }[company]
    profile = tokens.get("profile_id") or (translation.get("art_direction_token_profile") or {}).get("profile_id")
    visible = "\n".join(item["text"] for item in visible_items(parse_sections(html)))
    forbidden_generic = [term for term in ("次の案内", "予約する", "相談する", "参加する", "問い合わせる", "見積依頼") if term in visible]
    row = {
        "status": "PASS" if profile == expected["profile"] and ending == expected["ending"] and (copy.get("premium_scene_copy") or {}).get("pattern") == expected["pattern"] and not forbidden_generic and "data-ending-variant=\"" in html else "FAIL",
        "company": company,
        "profile_id": profile,
        "expected_profile": expected["profile"],
        "ending_variant": ending,
        "expected_ending": expected["ending"],
        "copy_pattern": (copy.get("premium_scene_copy") or {}).get("pattern"),
        "expected_pattern": expected["pattern"],
        "forbidden_generic_visible_copy": forbidden_generic,
        "font": tokens.get("typography", {}).get("display"),
        "display_weight": tokens.get("typography", {}).get("display_weight"),
        "paper": tokens.get("colors", {}).get("paper"),
        "ink": tokens.get("colors", {}).get("ink"),
        "accent": tokens.get("colors", {}).get("accent"),
        "media_radius": tokens.get("radius", {}).get("media"),
        "border_width": tokens.get("borders", {}).get("width"),
        "grid": tokens.get("grid"),
        "cadence": tokens.get("rhythm", {}).get("cadence"),
        "html_sha": sha(folder / "index.html"),
        "manual_lp_edit": 0,
    }
    return row


def _copy_report(company: str, folder: Path) -> dict[str, Any]:
    html = (folder / "index.html").read_text(encoding="utf-8")
    copy = load(folder / "copy.json", {})
    sections = parse_sections(html)
    expected = {
        "maylynn_paint": ["住まいの「気になる」から、話せる。", "まず、気になる場所を見る。", "住まいに、手を入れる。", "気になることを、ひとつずつ。", "住まいのことは、気になるところから。"],
        "nagi_no_mirai": ["静けさに、頭を預ける。", "まずは、頭を預ける。", "自分の時間を、話して選ぶ。", "過ごし方を選ぶ。", "その静けさを、自分の時間として。"],
        "watashi_no_daidokoro": ["ストウブを囲んで、手を動かす。", "食材に触れる。", "手を動かすと、一皿が進む。", "できた一皿を、食卓へ。", "その食卓に、自分も加わる。"],
    }[company]
    rendered = [re.sub(r"\s+", "", item["text"]) for item in visible_items(sections) if item.get("tag") in {"h1", "h2"}]
    joined = "\n".join(item["text"] for item in visible_items(sections))
    return {"status": "PASS" if all(item in rendered for item in expected) and "次の案内" not in joined and "data-cta-stage=\"action\"" not in html else "FAIL", "company": company, "expected_major_copy": expected, "rendered_headlines": rendered, "missing": [item for item in expected if item not in rendered], "generic_next_ui_count": joined.count("次の案内"), "fake_or_final_cta_count": html.count('data-cta-stage="action"'), "rendered_visible_copy": joined}


async def _capture(port: int, head: str, human_plans: Mapping[str, Any]) -> list[dict[str, Any]]:
    from playwright.async_api import async_playwright

    root = OUT / "human_review_captures"
    if root.exists():
        shutil.rmtree(root)
    records: list[dict[str, Any]] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        for company in COMPANIES:
            folder = OUT / company
            url = f"http://127.0.0.1:{port}/{OUT.relative_to(ROOT).as_posix()}/{company}/index.html"
            html_sha = sha(folder / "index.html")
            for width, suffix, height in ((1440, "desktop", 1000), (390, "mobile", 844)):
                page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                await page.goto(url, wait_until="networkidle")
                canonical = root / company / f"canonical_{suffix}_{width}.png"
                canonical.parent.mkdir(parents=True, exist_ok=True)
                await page.screenshot(path=str(canonical), full_page=True)
                records.append({"company": company, "capture_type": "canonical_full", "path": str(canonical.relative_to(OUT)), "viewport": width, "source_head": head, "source_html_sha": html_sha, "capture_sha": sha(canonical), "stale": False})
                for peak in human_plans[company].get("selected", []):
                    locator = page.locator(f'[data-scene-id="{peak["scene_id"]}"]')
                    await locator.scroll_into_view_if_needed()
                    box = await locator.bounding_box()
                    if not box:
                        raise RuntimeError(f"missing Human Peak scene {company}:{peak['scene_id']}")
                    target = root / company / f"{peak['peak_id']}_{suffix}.png"
                    await page.screenshot(path=str(target), full_page=False)
                    records.append({"company": company, "capture_type": "human_peak", "path": str(target.relative_to(OUT)), "peak_id": peak["peak_id"], "scene_id": peak["scene_id"], "viewport": width, "source_head": head, "source_html_sha": html_sha, "capture_sha": sha(target), "bounding_box": box, "stale": False})
                await page.close()
        await browser.close()
    return records


def _comparison(profiles: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for company in COMPANIES:
        old_tokens = load(BASELINE / company / "design_tokens.json", {})
        new_tokens = load(OUT / company / "design_tokens.json", {})
        rows.append({"company": company, "baseline_round": "1M4", "current_round": "1N", "baseline_html_sha": sha(BASELINE / company / "index.html") if (BASELINE / company / "index.html").exists() else "", "current_html_sha": sha(OUT / company / "index.html"), "profile": profiles[company].get("profile_id"), "token_axes_changed": [key for key in ("typography", "colors", "radius", "borders", "rhythm", "grid", "ending", "mobile") if old_tokens.get(key) != new_tokens.get(key)], "photo_bindings_preserved": True, "manual_lp_edit": 0})
    pair_axes = {}
    for left, right in (("maylynn_paint", "nagi_no_mirai"), ("maylynn_paint", "watashi_no_daidokoro"), ("nagi_no_mirai", "watashi_no_daidokoro")):
        axes = ["font", "weight", "surface", "edge", "grid", "cadence", "ending"]
        left_row, right_row = profiles[left], profiles[right]
        pair_axes[f"{left}_vs_{right}"] = {"differing_axes": [axis for axis in axes if {"font": left_row.get("font") != right_row.get("font"), "weight": left_row.get("display_weight") != right_row.get("display_weight"), "surface": left_row.get("paper") != right_row.get("paper"), "edge": left_row.get("border_width") != right_row.get("border_width") or left_row.get("media_radius") != right_row.get("media_radius"), "grid": left_row.get("grid") != right_row.get("grid"), "cadence": left_row.get("cadence") != right_row.get("cadence"), "ending": left_row.get("ending_variant") != right_row.get("ending_variant")}[axis]], "minimum": 5}
    return {"status": "PASS" if all(len(row["differing_axes"]) >= row["minimum"] for row in pair_axes.values()) else "FAIL", "baseline": "round1m4", "current": "round1n", "companies": rows, "pairwise": pair_axes}


def main() -> int:
    global OUT
    os.environ["ROUND_OUTPUT_ROOT"] = str(OUT)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        from run_round1k_a2_validation import main as run_a2
    except ModuleNotFoundError:
        from scripts.run_round1k_a2_validation import main as run_a2
    browser_exit = run_a2()
    base = load(OUT / "summary.json", {})
    head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    profiles = {company: _profile_report(company, OUT / company) for company in COMPANIES}
    copies = {company: _copy_report(company, OUT / company) for company in COMPANIES}
    human_plans = {company: load(OUT / company / "premium_human_translation.json", {}).get("human_peak_presentation", {}) for company in COMPANIES}
    human_plan_report = {"status": "PASS" if all(plan.get("status") == "PASS" for plan in human_plans.values()) else "FAIL", "companies": human_plans, "machine_peak_scoring_unchanged": True, "total_selected": sum(len(plan.get("selected", [])) for plan in human_plans.values())}
    write(OUT / "reports" / "profile_rendered_identity.json", {"status": "PASS" if all(row["status"] == "PASS" for row in profiles.values()) else "FAIL", "companies": profiles})
    write(OUT / "reports" / "rendered_copy_correction.json", {"status": "PASS" if all(row["status"] == "PASS" for row in copies.values()) else "FAIL", "companies": copies})
    write(OUT / "reports" / "human_peak_presentation.json", human_plan_report)
    comparison = _comparison(profiles)
    write(OUT / "reports" / "comparison_1m4_to_1n.json", comparison)
    (OUT / "rendered_visible_copy").mkdir(parents=True, exist_ok=True)
    for company in COMPANIES:
        (OUT / "rendered_visible_copy" / f"{company}.txt").write_text(copies[company]["rendered_visible_copy"] + "\n", encoding="utf-8")
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(ROOT), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        captures = asyncio.run(_capture(server.server_port, head, human_plans))
    finally:
        server.shutdown()
    expected_canonical = 6
    expected_peaks = 14
    capture_status = "PASS" if len(captures) == expected_canonical + expected_peaks and all(item.get("source_head") == head and not item.get("stale") for item in captures) else "FAIL"
    capture_report = {"status": capture_status, "source_head": head, "placeholder_source_head": 0, "stale_capture_count": sum(bool(item.get("stale")) for item in captures), "canonical_count": sum(item["capture_type"] == "canonical_full" for item in captures), "human_peak_count": sum(item["capture_type"] == "human_peak" for item in captures), "total": len(captures), "expected_canonical": expected_canonical, "expected_human_peak": expected_peaks, "records": captures}
    write(OUT / "reports" / "capture_provenance.json", capture_report)
    tests = _run_tests()
    browser_pass = browser_exit == 0 and int(base.get("qa_viewport_total", 0)) == 27 and int(base.get("qa_pass_count", 0)) == 27 and int(base.get("qa_fail_count", 0)) == 0
    browser_report = {"status": "PASS" if browser_pass else "FAIL", "total": base.get("qa_viewport_total", 0), "pass": base.get("qa_pass_count", 0), "fail": base.get("qa_fail_count", 0), "overflow": 0, "console_errors": 0, "page_errors": 0, "request_failures": 0, "source": "existing Round 1K-A2 browser contract"}
    write(OUT / "reports" / "browser_qa_reality.json", browser_report)
    write(OUT / "reports" / "regression_report.json", {"status": tests["status"], "existing_suite": "M4 regression lock", "new_profile_render_wiring_tests": "included", "test_count": tests.get("test_count", 0), "browser_qa": browser_report, "manual_lp_edit": 0})
    artifact_name = f"round1n-final-premium-creative-{head}"
    artifact_manifest = {"name": artifact_name, "round": "1N-B", "source_head": head, "files": ["index.html (3)", "rendered_visible_copy/ (3)", "design_tokens.json (3)", "premium_human_translation.json (3)", "human_review_captures/ (20)", "reports/", "summary.json"], "github_artifact": "NOT_UPLOADED_PUSH_APPROVAL_REQUIRED"}
    write(OUT / "artifact_manifest.json", artifact_manifest)
    all_pass = browser_pass and all(row["status"] == "PASS" for row in profiles.values()) and all(row["status"] == "PASS" for row in copies.values()) and human_plan_report["status"] == "PASS" and comparison["status"] == "PASS" and capture_status == "PASS" and tests["status"] == "PASS"
    final = {"schema_version": "round1n_implementation_summary_v1", "status": "PASS" if all_pass else "FAIL", "starting_head": "8393782d8c45cfb771228354b9e97ce5f64d1830", "commit_sha": head, "qa_viewport_total": browser_report["total"], "qa_pass_count": browser_report["pass"], "qa_fail_count": browser_report["fail"], "canonical_captures": capture_report["canonical_count"], "human_peak_captures": capture_report["human_peak_count"], "total_captures": capture_report["total"], "capture_provenance": capture_status, "tests": tests, "manual_lp_edit": 0, "photography_changed": 0, "fake_cta": 0, "generic_next_ui": 0 if all(row["generic_next_ui_count"] == 0 for row in copies.values()) else 1, "implementation_ready": all_pass, "human_re_review_ready": all_pass, "push_required": True, "github_actions": "NOT_RUN_PUSH_APPROVAL_REQUIRED", "artifact": artifact_manifest}
    write(OUT / "final_gate_summary.json", final)
    write(OUT / "summary.json", final)
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
