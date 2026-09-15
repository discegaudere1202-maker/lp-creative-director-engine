"""Run the generic Production QA Loop for multiple new fixtures.

Each generation is created by ``run_generation``.  This script only
orchestrates capture, diagnosis and report writing; it never edits generated
HTML, CSS or copy.  Browser capture is required in CI and may be disabled
locally with ``--static-only`` when Playwright is unavailable.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil
import sys

from lp_engine.production_generation import run_generation
from lp_engine.quality_diagnosis import build_structured_review, diagnose_quality
from run_production_qa import DEFAULT_WIDTHS, static_report


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["input_file"] = str(path)
    return data


def _browser_report(directory: Path, report: dict, static_only: bool) -> dict:
    if static_only:
        report["mode"] = "static_only"
        return report
    from lp_engine.browser_qa import run_browser_qa_sync
    browser = run_browser_qa_sync(
        str(directory / "index.html"),
        str(directory / "browser_qa"),
        DEFAULT_WIDTHS,
        1000,
        screenshot_widths=[390, 1440],
    )
    report["mode"] = "static_and_browser"
    report["browser"] = browser.to_dict()
    report["status"] = "PASS" if report["status"] == "PASS" and browser.status == "PASS" else "FAIL"
    report["exact_capture"] = {"desktop": "1440x1000", "mobile": "390x844"}
    return report


def _run_generation(fixture: Path, loop_dir: Path, iteration: int, static_only: bool) -> dict:
    destination = loop_dir / f"generation_{iteration}"
    if destination.exists():
        shutil.rmtree(destination)
    raw = _load(fixture)
    result = run_generation(raw, destination, generation_id=f"qa-{fixture.stem}-{iteration}", iteration=iteration)
    report = _browser_report(destination, static_report(destination), static_only)
    (destination / "qa_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review = build_structured_review(destination, report)
    (destination / "structured_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    diagnosis = diagnose_quality(destination, qa_report=report, review=review)
    (destination / "quality_diagnosis.json").write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "generation_id": result.generation_id,
        "generation_iteration": iteration,
        "path": str(destination),
        "safety_status": result.safety_report.get("safety_status"),
        "qa_status": report.get("status"),
        "qa_mode": report.get("mode"),
        "review_average": review.get("average_scores"),
        "sales_sample_gate": review.get("sales_sample_gate"),
        "diagnosis_status": diagnosis.get("status"),
        "issue_count": diagnosis.get("issue_count", 0),
        "manual_intervention": result.manifest.get("manual_intervention", []),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run multi-fixture Production QA Loop")
    parser.add_argument("fixtures", nargs="+", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    fixtures = [path.resolve() for path in args.fixtures]
    rows = []
    for fixture in fixtures:
        fixture_dir = args.out / fixture.stem.replace("_production_input_v1", "")
        if fixture_dir.exists():
            shutil.rmtree(fixture_dir)
        fixture_dir.mkdir(parents=True)
        gen1 = _run_generation(fixture, fixture_dir, 1, args.static_only)
        gen2 = _run_generation(fixture, fixture_dir, 2, args.static_only)
        rows.append({
            "company_id": _load(fixture).get("company_id"),
            "fixture": str(fixture),
            "gen1": gen1,
            "gen2": gen2,
            "improved": gen2["review_average"] != gen1["review_average"] or gen2["issue_count"] < gen1["issue_count"],
        })
    profiles = []
    for row in rows:
        for gen in (row["gen1"], row["gen2"]):
            strategy = json.loads((Path(gen["path"]) / "creative_strategy.json").read_text(encoding="utf-8"))
            art = json.loads((Path(gen["path"]) / "art_direction.json").read_text(encoding="utf-8"))
            profiles.append({"company_id": row["company_id"], "iteration": gen["generation_iteration"], "layout_profile": strategy.get("layout_profile"), "authorities": art.get("visual_authority_priority"), "palette": art.get("color_logic")})
    summary = {
        "schema_version": "production_qa_loop_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "fixtures": rows,
        "required_widths": DEFAULT_WIDTHS,
        "manual_intervention_total": sum(len(row["gen2"]["manual_intervention"]) for row in rows),
        "gen2_improved_fixture_count": sum(row["improved"] for row in rows),
        "diversity_profiles": profiles,
        "status": "PASS" if all(row["gen2"]["safety_status"] == "PASS" and row["gen2"]["qa_status"] == "PASS" and not row["gen2"]["manual_intervention"] for row in rows) else "HOLD",
    }
    (args.out / "phase2_qa_loop_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
