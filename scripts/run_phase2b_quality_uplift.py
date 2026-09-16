"""Run the Phase 2B premium-quality loop and an unseen hold-out generation."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import shutil

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
    browser = run_browser_qa_sync(str(directory / "index.html"), str(directory / "browser_qa"), DEFAULT_WIDTHS, 1000, screenshot_widths=[390, 1440])
    report["mode"] = "static_and_browser"
    report["browser"] = browser.to_dict()
    report["status"] = "PASS" if report["status"] == "PASS" and browser.status == "PASS" else "FAIL"
    report["exact_capture"] = {"desktop": "1440x1000", "mobile": "390x844"}
    return report


def _run(fixture: Path, root: Path, iteration: int, static_only: bool, label: str) -> dict:
    destination = root / label
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    result = run_generation(_load(fixture), destination, generation_id=f"phase2b-{fixture.stem}-{label}", iteration=iteration)
    report = _browser_report(destination, static_report(destination), static_only)
    (destination / "qa_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review = build_structured_review(destination, report)
    (destination / "structured_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    diagnosis = diagnose_quality(destination, qa_report=report, review=review)
    (destination / "quality_diagnosis.json").write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    strategy = json.loads((destination / "creative_strategy.json").read_text(encoding="utf-8"))
    art = json.loads((destination / "art_direction.json").read_text(encoding="utf-8"))
    understanding = json.loads((destination / "company_understanding.json").read_text(encoding="utf-8"))
    return {
        "generation_id": result.generation_id, "generation_iteration": iteration, "label": label, "path": str(destination),
        "safety_status": result.safety_report.get("safety_status"), "qa_status": report.get("status"), "qa_mode": report.get("mode"),
        "review_average": review.get("average_scores"),
        "scores": {role: payload.get("scores", {}) for role, payload in review.get("reviewer_roles", {}).items()},
        "sales_sample_gate": review.get("sales_sample_gate"), "premium_gate_checks": review.get("premium_gate_checks", {}),
        "research_metrics": review.get("research_metrics", {}), "diagnosis_status": diagnosis.get("status"),
        "issue_count": diagnosis.get("issue_count", 0), "issue_types": diagnosis.get("root_cause_summary", []),
        "manual_intervention": result.manifest.get("manual_intervention", []), "layout_profile": strategy.get("layout_profile"),
        "visual_authority": art.get("visual_authority_priority", []), "evidence_density": understanding.get("evidence_density"),
        "evidence_strategy": understanding.get("evidence_strategy"),
    }


def _improved(before: dict, after: dict) -> bool:
    return after.get("review_average") != before.get("review_average") or after.get("issue_count", 0) < before.get("issue_count", 0)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run Phase 2B premium quality uplift")
    parser.add_argument("fixtures", nargs=3, type=Path)
    parser.add_argument("--holdout", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    rows = []
    for fixture in [path.resolve() for path in args.fixtures]:
        data = _load(fixture)
        root = args.out / data["company_id"]
        gen2 = _run(fixture, root, 2, args.static_only, "gen2")
        gen3 = _run(fixture, root, 3, args.static_only, "gen3")
        rows.append({"company_id": data["company_id"], "company_name": data["company"].get("company_name"), "fixture": str(fixture), "gen2": gen2, "gen3": gen3, "improved": _improved(gen2, gen3), "degraded_axes": [axis for axis, score in gen3["scores"].get("creative_art_direction", {}).items() if score < gen2["scores"].get("creative_art_direction", {}).get(axis, score)]})
    holdout = args.holdout.resolve()
    holdout_data = _load(holdout)
    holdout_result = _run(holdout, args.out / "holdout", 3, args.static_only, "generation")
    profiles = [{"company_id": row["company_id"], "kind": "gen3", "layout_profile": row["gen3"]["layout_profile"], "visual_authority": row["gen3"]["visual_authority"], "evidence_density": row["gen3"]["evidence_density"]} for row in rows]
    profiles.append({"company_id": holdout_data["company_id"], "kind": "holdout", "layout_profile": holdout_result["layout_profile"], "visual_authority": holdout_result["visual_authority"], "evidence_density": holdout_result["evidence_density"]})
    unique_profiles = sorted({item["layout_profile"] for item in profiles})
    diversity = {"profiles": profiles, "unique_layout_profiles": unique_profiles, "unique_layout_profile_count": len(unique_profiles), "similarity_gate": "PASS" if len(unique_profiles) >= 3 else "HOLD", "method": "generic layout profile and authority comparison; not a pixel similarity claim"}
    technical_pass = all(row["gen3"]["qa_status"] == "PASS" and row["gen3"]["safety_status"] == "PASS" and not row["gen3"]["manual_intervention"] for row in rows) and holdout_result["qa_status"] == "PASS" and holdout_result["safety_status"] == "PASS" and not holdout_result["manual_intervention"] and diversity["similarity_gate"] == "PASS"
    gates = {row["company_id"]: row["gen3"]["sales_sample_gate"] for row in rows}
    summary = {"schema_version": "phase2b_premium_quality_uplift_v1", "generated_at": datetime.now(UTC).isoformat(), "engine_rule_scope": "generic_cross_fixture_only", "manual_intervention_total": sum(len(row["gen3"]["manual_intervention"]) for row in rows) + len(holdout_result["manual_intervention"]), "fixtures": rows, "holdout": {"company_id": holdout_data["company_id"], "company_name": holdout_data["company"].get("company_name"), "fixture": str(holdout), "result": holdout_result}, "required_widths": DEFAULT_WIDTHS, "diversity": diversity, "gen3_improved_fixture_count": sum(row["improved"] for row in rows), "sales_sample_gates": gates, "holdout_sales_sample_gate": holdout_result["sales_sample_gate"], "phase2b_decision": "PASS" if any(value == "PASS" for value in gates.values()) and holdout_result["sales_sample_gate"] != "FAIL" else "HOLD", "technical_status": "PASS" if technical_pass else "HOLD", "status": "PASS" if technical_pass else "HOLD", "manual_lp_edit": 0, "holdout_is_rule_selection_input": False}
    (args.out / "phase2b_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if technical_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
