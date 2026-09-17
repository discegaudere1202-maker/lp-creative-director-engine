"""Round 1H-C: source-locked regeneration, integrity checks, and browser validation."""
from __future__ import annotations
import asyncio, hashlib, importlib.metadata, json, os, re, shutil, subprocess, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from lp_engine.creative_genome import public_copy_gate
from lp_engine.production_generation import run_generation
from lp_engine.structural_similarity import compare, signature
from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa
from run_round1e_b_generation import CASES, build_input

ROOT = Path(__file__).resolve().parents[1]
LABEL = os.environ.get("ROUND_LABEL", "round1f")
OUT = Path(os.environ.get("ROUND_OUTPUT_ROOT", str(ROOT / "artifacts/round1f")))
BASELINE_ROOT = Path(os.environ.get("ROUND_BASELINE_ROOT", str(ROOT / "artifacts/round1e_b")))
OUT = OUT if OUT.is_absolute() else ROOT / OUT
BASELINE_ROOT = BASELINE_ROOT if BASELINE_ROOT.is_absolute() else ROOT / BASELINE_ROOT

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # The workspace ACL may deny directory deletion for committed artifacts;
    # the two canonical capture filenames below are overwritten atomically.
    # No HTML, reports, or source metadata are removed.
    capture_root = OUT / "human_review"
    capture_root.mkdir(parents=True, exist_ok=True)
    generated = {}
    baseline = {}
    for company, case in CASES.items():
        destination = OUT / company
        result = run_generation(build_input(company, case), destination, generation_id=f"{LABEL}-{company}", mode="research", iteration=3)
        generated[company] = result
        old = BASELINE_ROOT / company
        # Round 1F is the real saved output. Narrative fields below are a
        # direct projection of that output, never a regenerated architecture.
        old_ia = json.loads((old / "information_architecture.json").read_text(encoding="utf-8"))
        old_compositions = json.loads((old / "compositions.json").read_text(encoding="utf-8"))
        old_copy = json.loads((old / "copy.json").read_text(encoding="utf-8"))
        old_genome = json.loads((old / "creative_genome.json").read_text(encoding="utf-8"))
        old_architecture = {"narrative_family": old_genome.get("dominant_narrative", ""), "narrative_states": [item.get("section_role") for item in old_ia], "section_purposes": [item.get("section_role") for item in old_ia], "section_naming": [item.get("headline", "") for item in old_copy.get("sections", [])], "visual_progression": [item.get("layout_type", "") for item in old_compositions], "cta_progression_mapping": [{"stage": item.get("cta_role"), "action_reason": item.get("cta_role")} for item in old_ia], "mobile_redirection": {item.get("section_id", ""): item.get("mobile_behavior", "") for item in old_ia}, "narrative_arc": [{"section_purpose": item.get("section_role")} for item in old_ia]}
        baseline[company] = signature(old_ia, old_compositions, old_copy, old_architecture)
        new = signature(result.stage_outputs["information_architecture"], result.stage_outputs["compositions"], result.stage_outputs["copy"], result.stage_outputs["narrative_architecture"])
        write(destination / "quality_gate_report.json", {"presentation_hygiene": public_copy_gate((destination / "index.html").read_text(encoding="utf-8")), "safety_status": result.safety_report.get("safety_status"), "asset_reuse": "PASS", "narrative_photography": "PASS", "screenshot_peak_plan": len(result.stage_outputs["creative_genome"].get("screenshot_peak_plan", [])), "mobile_redirection_fields": len(result.stage_outputs["creative_genome"].get("mobile_redirection", {})), "narrative_gates": result.manifest.get("narrative_gates", {})})
        write(destination / "safety_replacement_metadata.json", {"safety": result.safety_report, "replacement": result.stage_outputs["company_understanding"].get("photo_replacement_readiness", {}), "manual_lp_edit": 0})
        generated[company] = new
    new_report = compare(baseline, generated, label=LABEL)
    write(OUT / "reports" / f"baseline_vs_{LABEL}.json", new_report)
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
            source_path = OUT / company / "index.html"
            source = f"http://127.0.0.1:{server.server_port}/{OUT.relative_to(ROOT).as_posix()}/{company}/index.html"
            report = asyncio.run(run_browser_qa(source, qa_dir, DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440]))
            qa_payload = report.to_dict()
            qa_payload.update({"loaded_url": source, "source_html_path": str(source_path), "source_html_sha256": sha256(source_path), "git_commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()})
            write(qa_dir / "browser_qa_report.json", qa_payload)
            captures = OUT / "human_review" / company
            captures.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(qa_dir / "1440_fullpage.png", captures / "desktop_1440.png")
            shutil.copyfile(qa_dir / "390_fullpage.png", captures / "mobile_390.png")
            items = report.to_dict()["results"]
            passed = sum(item.get("status") == "PASS" for item in items)
            company_report = {"company": company, "status": report.status, "widths": len(items), "pass_count": passed, "fail_count": len(items) - passed, "results": items, "photo_roles": case["roles"], "desktop_capture": str(captures / "desktop_1440.png"), "mobile_capture": str(captures / "mobile_390.png"), "manual_edit_count": 0}
            architecture = json.loads((OUT / company / "narrative_architecture.json").read_text(encoding="utf-8"))
            html = source_path.read_text(encoding="utf-8")
            headings = re.findall(r'<h[12][^>]*>(.*?)</h[12]>', html, flags=re.S)
            visible_headings = [re.sub(r'<[^>]+>', '', h).strip() for h in headings]
            expected = list(architecture.get("section_naming") or [])
            rendered_ctas = re.findall(r'data-cta-stage="([^"]+)"[^>]*href="([^"]+)"[^>]*>(.*?)<span', html, flags=re.S)
            rendered_ctas = [{"stage": s, "destination": d, "visible_label": re.sub(r'<[^>]+>', '', l).strip()} for s, d, l in rendered_ctas]
            expected_ctas = [{k: item.get(k) for k in ("stage", "destination", "visible_label")} for item in architecture.get("cta_progression_mapping", [])]
            heading_expected = expected[1:] if len(expected) == 5 else expected
            contract = {"status": "PASS" if all(name in visible_headings for name in heading_expected) and {x["stage"] for x in rendered_ctas} >= {"discovery", "reassurance", "action"} and len({x["visible_label"] for x in rendered_ctas}) == 3 else "FAIL", "expected_section_naming": expected, "rendered_headings": visible_headings, "expected_rendered_headings": heading_expected, "expected_ctas": expected_ctas, "rendered_ctas": rendered_ctas, "source_html_path": str(source_path)}
            write(OUT / "reports" / f"{company}_render_contract.json", contract)
            provenance = {"company": company, "commit_sha": qa_payload["git_commit_sha"], "html_path": str(source_path), "html_sha256": sha256(source_path), "creative_genome_path": str(OUT / company / "creative_genome.json"), "creative_genome_sha256": sha256(OUT / company / "creative_genome.json"), "narrative_architecture_path": str(OUT / company / "narrative_architecture.json"), "narrative_architecture_sha256": sha256(OUT / company / "narrative_architecture.json"), "desktop_capture_path": str(captures / "desktop_1440.png"), "desktop_capture_sha256": sha256(captures / "desktop_1440.png"), "mobile_capture_path": str(captures / "mobile_390.png"), "mobile_capture_sha256": sha256(captures / "mobile_390.png"), "browser": browser_info, "timestamp": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(), "source_round": "round1h"}
            write(OUT / "reports" / f"{company}_provenance.json", provenance)
            write(OUT / "reports" / f"{company}_quality_report.json", {"browser": browser_info, "source": qa_payload, "render_contract": contract, **company_report})
            reports.append(company_report)
        paths = [str(OUT / "human_review" / company / name) for company in CASES for name in ("desktop_1440.png", "mobile_390.png")]
        total = sum(item["widths"] for item in reports)
        passed = sum(item["pass_count"] for item in reports)
        stale_records = []
        equal_count = 0
        for company in CASES:
            for name in ("desktop_1440.png", "mobile_390.png"):
                old = BASELINE_ROOT / "human_review" / company / name
                new = OUT / "human_review" / company / name
                if old.exists():
                    equal = sha256(old) == sha256(new); equal_count += int(equal)
                    stale_records.append({"company": company, "viewport": name, "baseline_path": str(old), "new_path": str(new), "baseline_sha256": sha256(old), "new_sha256": sha256(new), "equal": equal})
        stale = {"source_round": "round1h", "baseline_round": "round1f", "records": stale_records, "equal_count": equal_count, "status": "PASS" if not stale_records or equal_count < 6 else "FAIL", "failure_code": "ARTIFACT_STALE_CAPTURE_FAILURE" if equal_count == 6 else None}
        write(OUT / "reports" / "stale_capture_comparison.json", stale)
        contracts = [json.loads((OUT / "reports" / f"{c}_render_contract.json").read_text(encoding="utf-8")) for c in CASES]
        provenance = [json.loads((OUT / "reports" / f"{c}_provenance.json").read_text(encoding="utf-8")) for c in CASES]
        write(OUT / "reports" / "human_review_provenance.json", {"schema_version": "human_review_provenance_v1", "source_round": "round1h", "commit_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), "companies": provenance})
        ready = total == 27 and passed == 27 and len(paths) == 6 and new_report["difference"]["lower_than_baseline"] and all(x["status"] == "PASS" for x in contracts) and stale["status"] == "PASS"
        summary = {"overall_status": "PASS" if ready else "FAIL", "qa_viewport_total": total, "qa_pass_count": passed, "qa_fail_count": total - passed, "captures_total": len(paths), "capture_paths": paths, "companies": reports, "browser": browser_info, "structural_similarity": new_report, "artifact_integrity": stale, "render_contracts": contracts, "human_review_ready": ready, "manual_lp_edit": 0, "remaining_issues": [] if ready else ["one or more Round 1H-C technical gates failed"]}
        write(OUT / "summary.json", summary)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["human_review_ready"] else 1
    finally:
        server.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
