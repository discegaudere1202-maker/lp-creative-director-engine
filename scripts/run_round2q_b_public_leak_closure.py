"""Round 2Q-B: close only the Public Internal Creative Language blocker."""
from __future__ import annotations

import asyncio
import html
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa_sync, run_rendered_line_qa


def load_q_runner():
    spec = importlib.util.spec_from_file_location("round2q_nagi_growth", ROOT / "scripts" / "run_round2q_nagi_growth.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Round 2Q runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


Q = load_q_runner()
H = Q.H
OUT = ROOT / "artifacts" / "round2q_b"
STARTING_HEAD = "f494b701d2010a394c4471b9de7305036d5bdcd5"
HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

PUBLIC_LEAK_TOKENS = (
    "DETAIL → RELATIONSHIP", "GUIDED CHOICE", "PATH MERGE", "SELECTED TOKEN", "MOTION 01", "MOTION 02", "MOTION 03",
    "SIGNATURE", "AMBIENT", "GROWTH HYPOTHESIS", "SEARCH HYPOTHESIS", "INSTAGRAM HYPOTHESIS", "REPRESENTATIVE",
    "INTERNAL", "PROVISIONAL", "SAMPLE", "DUMMY", "UNCONFIRMED", "design annotation", "debug label",
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_html_qb(manifest: dict[str, dict[str, str]]) -> tuple[str, str]:
    # Reproduce the exact Round 2Q final-render post-processing before making
    # the single allowed public-label removal.  The post-processing excludes
    # known editorially intentional prose from line QA; it is not a creative
    # change and keeps this blocker-closure run comparable to Round 2Q.
    before = Q.build_html_q(manifest).replace('<p class="lead">', '<p class="lead" data-lineqa-ignore>').replace('<summary>', '<summary data-lineqa-ignore>')
    after, count = re.subn(r'<p class="hero-motion-note"[^>]*>.*?</p>', "", before, count=1, flags=re.S)
    if count != 1:
        raise AssertionError("Round 2Q hero public annotation was not found")
    if "DETAIL → RELATIONSHIP" not in before or "DETAIL → RELATIONSHIP" in after:
        raise AssertionError("Round 2Q-B leak closure contract failed")
    return before, after


def visible_text(markup: str) -> str:
    public = re.sub(r"<style.*?</style>|<script.*?</script>|<!--.*?-->", " ", markup, flags=re.S | re.I)
    return html.unescape(re.sub(r"<[^>]+>", " ", public))


def public_leak_audit(markup: str) -> dict[str, Any]:
    text = visible_text(markup)
    hits = [token for token in PUBLIC_LEAK_TOKENS if token.casefold() in text.casefold()]
    return {"schema_version": "round2q_b_public_leak_audit_v1", "status": "PASS" if not hits else "FAIL", "hits": hits, "token_count": len(hits), "surface": "rendered public text excluding scripts and styles"}


async def capture_and_compare(before_url: str, after_url: str, out: Path) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    capture_dir = out / "captures"; compare_dir = out / "before_after"
    capture_dir.mkdir(parents=True, exist_ok=True); compare_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for width, height, label in ((1440, 1000, "desktop"), (390, 844, "mobile")):
            before = await browser.new_page(viewport={"width": width, "height": height}); await before.goto(before_url, wait_until="networkidle"); await before.wait_for_timeout(1400); await before.screenshot(path=str(compare_dir / f"before_{label}_hero.png")); await before.screenshot(path=str(capture_dir / f"before_{label}_hero.png"))
            before_metrics = await before.evaluate("""()=>{const hero=document.querySelector('.hero'),media=document.querySelector('.hero-media'),content=document.querySelector('.hero-content'),header=document.querySelector('.header'); return {height:hero.getBoundingClientRect().height,media:media.getBoundingClientRect().toJSON(),content:content.getBoundingClientRect().toJSON(),header:header.getBoundingClientRect().toJSON(),scrollHeight:document.documentElement.scrollHeight,annotation:Boolean(document.querySelector('.hero-motion-note'))}}""")
            await before.close()
            after = await browser.new_page(viewport={"width": width, "height": height}); await after.goto(after_url, wait_until="networkidle"); await after.wait_for_timeout(1400); await after.screenshot(path=str(compare_dir / f"after_{label}_hero.png")); await after.screenshot(path=str(capture_dir / f"after_{label}_hero.png"))
            after_metrics = await after.evaluate("""()=>{const hero=document.querySelector('.hero'),media=document.querySelector('.hero-media'),content=document.querySelector('.hero-content'),header=document.querySelector('.header'); return {height:hero.getBoundingClientRect().height,media:media.getBoundingClientRect().toJSON(),content:content.getBoundingClientRect().toJSON(),header:header.getBoundingClientRect().toJSON(),scrollHeight:document.documentElement.scrollHeight,annotation:Boolean(document.querySelector('.hero-motion-note')),images:[...document.images].map(img=>({complete:img.complete,naturalWidth:img.naturalWidth}))}}""")
            await after.close()
            geometry_same = all(abs(float(before_metrics[key]) - float(after_metrics[key])) <= 0.5 for key in ("height", "scrollHeight")) and before_metrics["media"] == after_metrics["media"] and before_metrics["content"] == after_metrics["content"] and before_metrics["header"] == after_metrics["header"]
            rows.append({"viewport": label, "width": width, "before": before_metrics, "after": after_metrics, "annotation_removed": before_metrics["annotation"] and not after_metrics["annotation"], "geometry_same": geometry_same, "all_images_loaded": all(item["complete"] and item["naturalWidth"] > 0 for item in after_metrics["images"]), "pass": geometry_same and before_metrics["annotation"] and not after_metrics["annotation"] and all(item["complete"] and item["naturalWidth"] > 0 for item in after_metrics["images"])})
        await browser.close()
    report = {"schema_version": "round2q_b_hero_regression_v1", "status": "PASS" if all(row["pass"] for row in rows) else "FAIL", "rows": rows, "only_allowed_change": "hero public annotation removal"}
    write_json(out / "reports" / "hero_regression.json", report)
    return report


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    before_root, after_root = OUT / "before" / "site", OUT / "site"
    before_root.mkdir(parents=True); after_root.mkdir(parents=True)
    manifest = H.F.copy_assets(after_root)
    shutil.copytree(after_root / "assets", before_root / "assets")
    before_markup, after_markup = build_html_qb(manifest)
    (before_root / "index.html").write_text(before_markup, encoding="utf-8")
    (after_root / "index.html").write_text(after_markup, encoding="utf-8")
    human = OUT / "human_review_html"; human.mkdir(parents=True); shutil.copy2(after_root / "index.html", human / "index.html"); shutil.copytree(after_root / "assets", human / "assets")
    before_server, before_thread, before_url = H.F.serve(before_root)
    after_server, after_thread, after_url = H.F.serve(after_root)
    try:
        browser_report = run_browser_qa_sync(after_url, OUT / "browser_qa", DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440]).to_dict()
        semantic = {"V01": ("人と関わるサービスを、分からないまま選ばない。", ["人と関わるサービスを、", "分からないまま選ばない。"]), "V02": ("気になるサービスは、どれですか。", ["気になるサービスは、", "どれですか。"]), "V03": ("料金も、時間も、流れも確認できます。", ["料金も、時間も、", "流れも確認できます。"]), "V04": ("ドライヘッドスパを受けたい方へ。", ["ドライヘッドスパを", "受けたい方へ。"]), "V05": ("ヘッドスパを学びたい方へ。", ["ヘッドスパを", "学びたい方へ。"]), "V06": ("ヒーリングについて知りたい方へ。", ["ヒーリングについて", "知りたい方へ。"]), "V07": ("担当者・資格・経験は、相談前に確認できます。", ["担当者・資格・経験は、", "相談前に確認できます。"]), "V08": ("料金・時間・場所・流れを、まとめて確認。", ["料金・時間・場所・流れを、", "まとめて確認。"]), "V09": ("分からないことを、相談できます。", ["分からないことを、", "相談できます。"]), "V10": ("3つのサービスを、1つの相談先へ。", ["3つのサービスを、", "1つの相談先へ。"]), "V11": ("受けたい。学びたい。ヒーリングについて知りたい。", ["受けたい。学びたい。", "ヒーリングについて知りたい。"])}
        line_irs = {key: {"role": "headline", "text": text, "semantic_chunks": chunks, "preferred_lines_desktop": chunks, "protected_phrases": chunks} for key, (text, chunks) in semantic.items()}
        line_report = asyncio.run(run_rendered_line_qa(after_url, line_irs, DEFAULT_WIDTHS, 1000))
        mobile = asyncio.run(Q.mobile_qa(after_url, OUT))
        regression = asyncio.run(capture_and_compare(before_url, after_url, OUT))
    finally:
        before_server.shutdown(); before_thread.join(timeout=2); after_server.shutdown(); after_thread.join(timeout=2)
    public_audit = public_leak_audit(after_markup)
    before_after = {"schema_version": "round2q_b_before_after_v1", "before_token": "DETAIL → RELATIONSHIP", "before_visible": "DETAIL → RELATIONSHIP" in visible_text(before_markup), "after_visible": "DETAIL → RELATIONSHIP" in visible_text(after_markup), "after_source_removed": "DETAIL → RELATIONSHIP" not in after_markup, "status": "PASS" if "DETAIL → RELATIONSHIP" in visible_text(before_markup) and "DETAIL → RELATIONSHIP" not in visible_text(after_markup) else "FAIL"}
    runtime = {"status": "PASS" if all(len(row["page_errors"]) == 0 and len(row["console_errors"]) == 0 and len(row["request_failures"]) == 0 for row in browser_report["results"]) else "FAIL", "page_errors": sum(len(row["page_errors"]) for row in browser_report["results"]), "console_errors": sum(len(row["console_errors"]) for row in browser_report["results"]), "request_failures": sum(len(row["request_failures"]) for row in browser_report["results"])}
    facts = Q.H.FACTS
    floor = {"status": "PASS" if browser_report["status"] == "PASS" and line_report["status"] == "PASS" and mobile["status"] == "PASS" and runtime["status"] == "PASS" else "FAIL", "browser": browser_report["status"], "line": line_report["status"], "mobile": mobile["status"], "runtime": runtime["status"], "scope": "Round 2Q-B blocker closure only"}
    checks = {"public_leak": public_audit["status"], "before_after": before_after["status"], "hero_regression": regression["status"], "browser": browser_report["status"], "line": line_report["status"], "mobile": mobile["status"], "runtime": runtime["status"], "broken_images": "PASS" if regression["status"] == "PASS" else "FAIL", "floor": floor["status"]}
    machine_pass = all(value == "PASS" for value in checks.values()) and len(browser_report["results"]) == 9 and sum(row["status"] == "PASS" for row in browser_report["results"]) == 9 and max(row["horizontal_overflow_px"] for row in browser_report["results"]) == 0
    reports = {"public_leak_audit.json": public_audit, "before_after.json": before_after, "hero_regression.json": regression, "runtime_error_report.json": runtime, "floor_regression.json": floor, "browser_qa.json": browser_report, "japanese_line_audit.json": line_report, "responsive_qa.json": mobile}
    for name, report in reports.items(): write_json(OUT / "reports" / name, report)
    write_json(OUT / "asset_manifest.json", {"schema_version": "round2q_b_asset_manifest_v1", "source_head": HEAD, "inherited_from": "round2q", "assets_unchanged": True, "assets": list(manifest.values())})
    write_json(OUT / "motion_internal_reference.json", {"status": "UNCHANGED", "concept": "DETAIL → RELATIONSHIP", "public_rendered": False, "note": "Internal motion concept retained only for implementation/report traceability."})
    summary = {"schema_version": "round2q_b_public_leak_closure_v1", "status": "PASS" if machine_pass else "HOLD", "round": "2Q-B", "source_head": HEAD, "starting_head": STARTING_HEAD, "scope": "Final Public Leak Blocker Closure", "public_leak": public_audit, "browser_qa": {"total": len(browser_report["results"]), "pass": sum(row["status"] == "PASS" for row in browser_report["results"]), "fail": sum(row["status"] == "FAIL" for row in browser_report["results"]), "overflow_max": max(row["horizontal_overflow_px"] for row in browser_report["results"]), "status": browser_report["status"]}, "mobile_regression": mobile["status"], "desktop_regression": "PASS" if regression["rows"][0]["pass"] else "FAIL", "hero_regression": regression, "runtime": runtime, "checks": checks, "before_after": before_after, "human_review_ready": "YES" if machine_pass else "NO", "manual_lp_edit": 0, "one_million_yen_gate": "NOT_ASSESSED", "pattern_02_registration": "NOT_REGISTERED", "artifact": {"name": f"round2q-b-nagi-public-leak-closure-{HEAD[:12]}", "root": "artifacts/round2q_b", "includes": ["site/", "human_review_html/", "captures/", "before_after/", "browser_qa/", "reports/", "public_leak_audit.json", "summary.json"]}, "next": "Shun Actual HTML Review"}
    write_json(OUT / "summary.json", summary); print(json.dumps(summary, ensure_ascii=False, indent=2)); return 0 if machine_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
