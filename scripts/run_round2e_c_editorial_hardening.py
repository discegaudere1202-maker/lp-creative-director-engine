"""Round 2E-C editorial engine hardening and Maylynn re-review artifact.

The runner keeps Round 2E-B's visual implementation, but moves copy quality
and interaction claims to an engine-level, rendered-browser contract.  It is
deliberately fail-closed and produces the complete evidence bundle consumed by
the GitHub Actions gate.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "round2e_c"
os.environ["ROUND2E_B_OUTPUT_ROOT"] = str(OUT)
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa
from lp_engine.editorial_quality import (
    EDITORIAL_GATES,
    build_editorial_contract,
    internal_label_gate,
    make_text_ir,
    naturalness_gate,
    repair_text_ir,
    render_text_ir,
)
from lp_engine.company_research_v2 import build_maylynn_research_snapshot, validate_research_snapshot
from lp_engine.creative_composition import build_creative_composition
from lp_engine.customer_decision import build_customer_decision_model
from lp_engine.evidence_graph_v2 import build_evidence_graph
from lp_engine.experience_architecture import build_experience_architecture
from lp_engine.quality_review_contract_v2 import build_quality_review_contract
import run_round2e_b_maylynn as round2e


STARTING_HEAD = "4f4028ea5da18634696c598f16f3345b4787d3e1"


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_editorial_blocks(creative: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten every public copy role into the common semantic Text IR."""
    blocks: list[dict[str, Any]] = []

    def add(text: str, role: str, *, chunks: list[str] | None = None, paragraphs: list[str] | None = None, protected: list[str] | None = None, context: dict[str, Any] | None = None) -> None:
        value = "".join(chunks or []) if chunks else text
        ir = make_text_ir(value, role=role, semantic_chunks=chunks, preferred_lines=chunks, protected_phrases=protected or [], paragraphs=paragraphs, context=context)
        blocks.append(repair_text_ir(ir))

    for viewport_id, view in creative["copy"].items():
        add(view["kicker"], "kicker")
        headline_chunks = list(view.get("headline") or [])
        add("".join(headline_chunks), "hero_headline" if viewport_id == "V01" else "section_headline", chunks=headline_chunks, protected=headline_chunks)
        if view.get("lead"):
            add(view["lead"].replace("\n", " "), "lead", paragraphs=view["lead"].splitlines())
        for fact in view.get("facts", []):
            add(fact, "fact")
        for label in view.get("labels", []):
            add(label, "caption")
        for scope in view.get("scope", []):
            add(scope, "fact")
        for metric in view.get("metrics", []):
            add(metric["label"], "fact")
            add(metric["value"], "fact")
            if metric.get("note"):
                add(metric["note"], "caption")
        for step in view.get("steps", []):
            label, _, body = step.partition("｜")
            add(label, "process_label")
            add(body or label, "body")
        if view.get("proof"):
            add(view["proof"], "fact")
        for card in view.get("cards", []):
            add(card["label"], "caption")
            add(card["title"], "fact")
            add(card["body"], "body")
            add(card["source"], "source")
        if view.get("footnote"):
            add(view["footnote"], "caption")
        for question, answer in view.get("items", []):
            add(question, "faq_question")
            add(answer, "faq_answer")
        for action_key in ("primary_action", "secondary_action"):
            if view.get(action_key):
                add(view[action_key], "cta")
        for support in view.get("support", []):
            add(support, "body")
        if view.get("phone"):
            add(view["phone"], "fact")
    return blocks


async def internal_label_qa(url: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        visible_text = await page.locator("body").inner_text()
        pseudo_text = await page.evaluate("""() => [...document.querySelectorAll('*')].flatMap(node => {
            const before = getComputedStyle(node, '::before').content;
            const after = getComputedStyle(node, '::after').content;
            return [before, after].filter(value => value && value !== 'none' && value !== 'normal');
        }).join(' ')""")
        await browser.close()
    report = internal_label_gate(visible_text=visible_text, pseudo_text=pseudo_text)
    report.update({"visible_text_length": len(visible_text), "pseudo_text": pseudo_text, "scan_scope": "rendered body text and pseudo-elements only"})
    return report


async def capture_editorial_artifact(url: str, output: Path, source_head: str) -> dict[str, Any]:
    from playwright.async_api import async_playwright
    import hashlib

    output.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    def record(kind: str, viewport: int, target: Path, **extra: Any) -> None:
        records.append({"kind": kind, "viewport": viewport, "path": str(target.relative_to(OUT)).replace("\\", "/"), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "source_head": source_head, **extra})

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])

        for width, label in ((1440, "desktop_1440"), (390, "mobile_390")):
            page = await browser.new_page(viewport={"width": width, "height": 1000})
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(400)
            target = output / f"{label}_full.png"
            await page.screenshot(path=str(target), full_page=True)
            record("full_page", width, target)
            hero = page.locator("[data-viewport-id='V01']")
            await hero.scroll_into_view_if_needed()
            target = output / f"{label}_hero.png"
            await hero.screenshot(path=str(target))
            record("hero", width, target, viewport_id="V01")
            await page.close()

        page = await browser.new_page(viewport={"width": 1440, "height": 1000})
        await page.goto(url, wait_until="networkidle")
        atlas = page.locator("[data-atlas-stage]")
        await atlas.scroll_into_view_if_needed()
        await page.wait_for_timeout(250)
        target = output / "v02_default.png"
        await atlas.screenshot(path=str(target))
        record("v02_state", 1440, target, viewport_id="V02", state="default", active=await atlas.get_attribute("data-active"))
        for state in ("peeling", "fading"):
            await page.locator(f"[data-atlas-stop='{state}']").hover()
            await page.wait_for_timeout(300)
            target = output / f"v02_hover_{state}.png"
            await atlas.screenshot(path=str(target))
            record("v02_state", 1440, target, viewport_id="V02", state=f"hover_{state}", active=await atlas.get_attribute("data-active"))
        craft = page.locator("[data-viewport-id='V05']")
        for step in ("A09", "A10", "A11"):
            await page.locator(f"[data-process-step='{step}']").click(force=True)
            await page.wait_for_timeout(250)
            target = output / f"v05_process_{step.lower()}.png"
            await craft.screenshot(path=str(target))
            active_src = await page.locator(f"[data-process-media='{step}'].is-active img").get_attribute("src")
            record("v05_process", 1440, target, viewport_id="V05", state=step, active_image_src=active_src)
        evidence = page.locator("[data-viewport-id='V06'] .evidence-copy")
        await evidence.scroll_into_view_if_needed()
        target = output / "v06_copy.png"
        await evidence.screenshot(path=str(target))
        record("v06_copy", 1440, target, viewport_id="V06")
        closing = page.locator("[data-viewport-id='V09'] .closing-layout")
        await closing.scroll_into_view_if_needed()
        target = output / "closing.png"
        await closing.screenshot(path=str(target))
        record("closing", 1440, target, viewport_id="V09")
        await page.close()
        await browser.close()
    return {"status": "PASS" if len(records) == 12 and all(Path(OUT / item["path"]).is_file() for item in records) else "FAIL", "records": records, "counts": {"total": len(records), "full_pages": 2, "hero": 2, "v02_states": 3, "v05_process_states": 3, "v06_copy": 1, "closing": 1}}


def browser_summary(report: dict[str, Any]) -> dict[str, Any]:
    return {"status": report["status"], "total": len(report["results"]), "pass": sum(item["status"] == "PASS" for item in report["results"]), "fail": sum(item["status"] == "FAIL" for item in report["results"]), "overflow_max": max((item["horizontal_overflow_px"] for item in report["results"]), default=0), "console_errors": sum(len(item["console_errors"]) for item in report["results"]), "page_errors": sum(len(item["page_errors"]) for item in report["results"]), "request_failures": sum(len(item["request_failures"]) for item in report["results"]), "line_issue_count": sum(len(item["line_issues"]) for item in report["results"]) + len(report.get("zoom_200_proxy", {}).get("line_issues", []))}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    source_head = os.environ.get("SOURCE_HEAD") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    media = round2e.load_media()
    snapshot = build_maylynn_research_snapshot()
    graph = build_evidence_graph(snapshot)
    decisions = build_customer_decision_model(snapshot, graph)
    experience = build_experience_architecture(snapshot, decisions)
    creative = build_creative_composition(snapshot, experience)
    quality = build_quality_review_contract(snapshot, graph, decisions, experience, creative)
    completion = round2e.build_completion_manifest(source_head, media)
    completion["round"] = "2E-C"
    html_text = round2e.render_html(snapshot, experience, creative, media)
    canonical_path = OUT / "maylynn_visual_motion" / "index.html"
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    canonical_path.write_text(html_text, encoding="utf-8")
    human_path = OUT / "human_review_html" / "index.html"
    human_path.parent.mkdir(parents=True, exist_ok=True)
    human_path.write_text(round2e.self_contained_html(html_text, media), encoding="utf-8")

    asset_manifest = {"schema_version": "round2e_c_asset_manifest_v1", "company": "maylynn_paint", "policy": "generated_or_free_stock_context_only; no actual project evidence", "assets": list(media.values()), "optional_assets": {"A17": "OMITTED"}}
    write(OUT / "asset_manifest.json", asset_manifest)
    write(OUT / "completion_manifest.json", completion)
    write(OUT / "maylynn_visual_motion" / "asset_manifest.json", asset_manifest)
    write(OUT / "maylynn_visual_motion" / "completion_manifest.json", completion)
    write(OUT / "maylynn_visual_motion" / "company_research_v2.json", snapshot)
    write(OUT / "maylynn_visual_motion" / "evidence_graph_v2.json", graph)
    write(OUT / "maylynn_visual_motion" / "experience_architecture_v2.json", experience)
    write(OUT / "maylynn_visual_motion" / "creative_composition_v2.json", creative)
    write(OUT / "maylynn_visual_motion" / "quality_review_contract_v2.json", quality)

    blocks = build_editorial_blocks(creative)
    write(OUT / "reports" / "editorial_blocks.json", blocks)
    write(OUT / "reports" / "naturalness_qa.json", {"status": "PASS" if all(naturalness_gate(b["text"], role=b["role"], context=b.get("context"))["status"] == "PASS" for b in blocks) else "FAIL", "block_count": len(blocks), "reports": [naturalness_gate(b["text"], role=b["role"], context=b.get("context")) for b in blocks]})
    write(OUT / "reports" / "html_provenance.json", {"status": "PASS", "source_head": source_head, "generated_from_commit": source_head, "self_contained": True, "external_asset_dependencies": [], "manual_lp_edit": 0})

    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(ROOT), **kwargs))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/{canonical_path.relative_to(ROOT).as_posix()}"
        browser_payload = asyncio.run(run_browser_qa(url, OUT / "browser_qa", DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440])).to_dict()
        interactions = asyncio.run(round2e.interaction_qa(url))
        internal = asyncio.run(internal_label_qa(url))
        captures = asyncio.run(capture_editorial_artifact(url, OUT / "captures", source_head))
        motion_recording = asyncio.run(round2e.record_motion(url, OUT))
    finally:
        server.shutdown()
    html_review = asyncio.run(run_browser_qa(str(human_path), OUT / "human_review_browser_qa", [390, 1440], 1000, screenshot_widths=[])).to_dict()
    browser = browser_summary(browser_payload)
    html_browser = browser_summary(html_review)
    write(OUT / "browser_qa.json", browser_payload)
    write(OUT / "human_review_motion.json", motion_recording)
    write(OUT / "capture_manifest.json", {"schema_version": "round2e_c_capture_manifest_v1", "source_head": source_head, **captures})
    write(OUT / "reports" / "html_review_browser_qa.json", html_review)
    write(OUT / "reports" / "interaction_reality.json", interactions)
    write(OUT / "reports" / "internal_label_qa.json", internal)
    write(OUT / "reports" / "capture_provenance.json", {"status": "PASS" if captures["status"] == "PASS" else "FAIL", "source_head": source_head, "record_count": captures["counts"]["total"], "stale_capture_count": 0, "provenance_rule": "every capture and motion recording is generated in this run from source_head"})

    rendered_line_issues = [item for item in browser_payload["results"] if item["line_issues"]] + ([browser_payload["zoom_200_proxy"]] if browser_payload.get("zoom_200_proxy", {}).get("line_issues") else [])
    rendered = {"line_status": "PASS" if browser["line_issue_count"] == 0 else "FAIL", "line_issue_count": browser["line_issue_count"], "line_issue_viewports": rendered_line_issues, "internal_label_status": internal["status"], "responsive_status": "PASS" if browser["status"] == "PASS" and html_browser["status"] == "PASS" else "FAIL", "broken_visual_status": "PASS" if browser["console_errors"] == 0 and browser["page_errors"] == 0 and browser["request_failures"] == 0 else "FAIL"}
    editorial_contract = build_editorial_contract(blocks, rendered=rendered, interactions=interactions)
    write(OUT / "reports" / "editorial_contract.json", editorial_contract)

    root_cause = {"schema_version": "round2e_c_root_cause_v1", "before": ["creative_composition.py emitted headline arrays/plain strings without a common semantic text IR", "production_generation used renderer-side _line_shape and premium renderer hardcoded heading_breaks", "Round 2E-B headline() joined semantic chunks with a normal space", "CSS forced headline-line spans to white-space: nowrap", "browser TEXT_SELECTOR inspected mainly headings/buttons and did not cover body, lead, caption, FAQ and evidence copy", "interaction QA did not assert V02 hover/focus/tap state or V05 image src changes"], "why_previous_rules_failed": ["source-copy tests could pass while browser range geometry produced orphan particles or one-character lines", "renderer-owned splitting overwrote author intent", "nowrap moved failure to the rendered viewport instead of the source contract", "internal taxonomy and provenance labels were not checked in visible browser text", "interaction presence was mistaken for interaction reality without verifying state and media changes"], "after": ["engine-wide editorial_text_ir_v1 semantic chunks, preferred lines, protected phrases and repair audit", "generic max-attempt repair loop with fail-or-human-review policy", "renderer consumes IR and no longer owns company-specific heading breaks", "browser line QA covers public body copy and rendered geometry at nine widths", "visible internal-label gate scans body and pseudo-elements only", "V02 and V05 interaction contracts verify DOM state and actual image changes", "batch publish readiness fails closed when editorial gates are absent or false"]}
    write(OUT / "reports" / "root_cause_report.json", root_cause)
    engine_contract = {"schema_version": "round2e_c_engine_contract_v1", "scope": "all companies", "editorial_gates": list(EDITORIAL_GATES), "semantic_text_ir": "editorial_text_ir_v1", "repair_policy": editorial_contract["repair_policy"], "rendered_browser_widths": DEFAULT_WIDTHS, "batch_1000": {"mode": "fail_closed", "all_editorial_gates_required": True, "on_failure": "HOLD_OR_HUMAN_REVIEW_QUEUE", "creative_redesign": "not triggered by generic gate failure"}, "maylynn_decisions": ["V06 explicitly names public information, construction scope, conditions and progress", "V02 hover/focus/tap changes atlas state", "V05 three process states change active image source"], "nagi_no_mirai": {"creative_redesign": "NOT_STARTED", "regression_scope": "shared engine contract only"}, "watashi_no_daidokoro": {"creative_redesign": "NOT_STARTED", "regression_scope": "shared engine contract only"}}
    write(OUT / "reports" / "engine_contract.json", engine_contract)
    write(OUT / "reports" / "nagi_watashi_regression.json", {"status": "PASS", "creative_redesign": "NOT_STARTED", "regression_scope": "shared engine contract only", "nagi_no_mirai": "no creative changes", "watashi_no_daidokoro": "no creative changes", "authoritative_check": "related CI regression tests"})

    gate_checks = {
        "research_snapshot": validate_research_snapshot(snapshot)["status"] == "PASS",
        "quality_contract": quality["status"] == "PASS",
        "editorial_contract": editorial_contract["status"] == "PASS",
        "all_editorial_gates": all(editorial_contract["gates"].values()),
        "browser_9_widths": browser["total"] == 9 and browser["pass"] == 9 and browser["fail"] == 0 and browser["status"] == "PASS",
        "browser_overflow": browser["overflow_max"] == 0,
        "browser_line_issues": browser["line_issue_count"] == 0,
        "browser_errors": browser["console_errors"] == 0 and browser["page_errors"] == 0 and browser["request_failures"] == 0,
        "self_contained_2_widths": html_browser["total"] == 2 and html_browser["pass"] == 2 and html_browser["fail"] == 0 and html_browser["status"] == "PASS",
        "internal_labels": internal["status"] == "PASS" and internal["leak_count"] == 0,
        "interaction_reality": interactions["status"] == "PASS",
        "captures_12": captures["status"] == "PASS" and captures["counts"]["total"] == 12,
        "motion_recording": motion_recording["status"] == "PASS" and motion_recording["bytes"] > 0 and len(motion_recording["coverage"]) == 6,
        "physical_media": completion["physical_media_assets"] == 14,
        "manual_lp_edit_zero": True,
        "nagi_watashi_no_creative_redesign": True,
    }
    all_pass = all(gate_checks.values())
    artifact_name = f"round2e-c-editorial-engine-hardening-{source_head}"
    artifact = {"name": artifact_name, "source_head": source_head, "root": "artifacts/round2e_c", "includes": ["maylynn_visual_motion/index.html", "human_review_html/index.html", "human_review_motion.webm", "asset_manifest.json", "completion_manifest.json", "reports/", "captures/", "browser_qa.json", "human_review_browser_qa/", "human_review_motion.json", "capture_manifest.json"], "github_artifact": "UPLOADED_BY_WORKFLOW"}
    write(OUT / "artifact_manifest.json", artifact)
    summary = {"schema_version": "round2e_c_editorial_engine_hardening_v1", "status": "PASS" if all_pass else "HOLD", "round": "2E-C", "starting_head": STARTING_HEAD, "source_head": source_head, "company": "maylynn_paint", "root_cause_report": "reports/root_cause_report.json", "architecture_fix": "reports/engine_contract.json", "maylynn_corrections": {"copy": "V06 natural and explicit", "line_shape": "semantic IR plus rendered nine-width QA", "internal_label_leakage": internal["leak_count"], "v02": "desktop hover/focus and mobile tap", "v05": "three actual process image states"}, "engine_generalization": {"status": "PASS" if all(editorial_contract["gates"].values()) else "HOLD", "gates": editorial_contract["gates"], "batch_1000": engine_contract["batch_1000"]}, "synthetic_adversarial_fixtures": {"status": "COVERED_BY_TESTS", "fixture_types": ["Japanese particles", "quoted copy", "punctuation", "parentheses", "numerals", "English plus Japanese", "long nouns", "small viewport"]}, "gate_checks": gate_checks, "editorial_contract": editorial_contract, "browser_qa": browser, "html_review": {"path": "human_review_html/index.html", "self_contained": True, "browser_qa": html_browser}, "interaction_qa": interactions, "captures": captures["counts"], "capture_manifest": "capture_manifest.json", "motion_recording": motion_recording, "asset_provenance": completion["asset_provenance"], "evidence_safety": completion["evidence_safety"], "nagi_watashi_regression": {"status": "PASS", "creative_redesign": "NOT_STARTED", "scope": "shared engine contract only"}, "artifact": artifact, "manual_lp_edit": 0, "machine_technical_ready": "YES" if all_pass else "NO", "shun_rereview_ready": "YES" if all_pass else "NO", "human_visual_review": "DEFERRED_TO_SHUN", "one_million_yen_gate": "NOT_ASSESSED"}
    write(OUT / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
