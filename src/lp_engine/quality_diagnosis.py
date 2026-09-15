"""Structured quality diagnosis for the Production QA Loop.

The diagnosis layer is deliberately deterministic and role-based.  It does
not edit a generated page or pretend to be a human reviewer.  It converts
observable generation, Safety and QA signals into Engine-layer hypotheses so
the next iteration can be regenerated from the input fixture.
"""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Mapping


AXES = (
    "Immediate Read", "Distinctness", "Owner Specificity", "Visual Hierarchy",
    "Craft Detail", "Emotional Pull", "Trust", "Share Impulse",
    "Mobile Quality", "Conversion Intent",
)
ROOT_CAUSES = {
    "STRATEGY", "COMPANY_TRUTH", "IA", "COPY", "EVIDENCE", "ART_DIRECTION",
    "TYPOGRAPHY", "COMPOSITION", "RHYTHM", "MOTION", "MOBILE", "CTA",
    "RENDERER", "SAFETY",
}
SEVERITIES = {"S0", "S1", "S2", "S3"}


def _read(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _issue(issue_id: str, issue_type: str, severity: str, axis: str, viewport: str, section: str, problem: str, root: str, layer: str, priority: str) -> dict[str, Any]:
    if issue_type not in ROOT_CAUSES or root not in ROOT_CAUSES or severity not in SEVERITIES:
        raise ValueError("invalid diagnosis classification")
    return {
        "issue_id": issue_id,
        "issue_type": issue_type,
        "severity": severity,
        "affected_axis": axis,
        "viewport": viewport,
        "affected_section": section,
        "observed_problem": problem,
        "likely_root_cause": root,
        "recommended_engine_layer": layer,
        "fix_priority": priority,
    }


def build_structured_review(output_dir: str | Path, qa_report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create comparable Creative and Business structured review roles."""
    directory = Path(output_dir)
    manifest = _read(directory / "generation_manifest.json", {})
    strategy = _read(directory / "creative_strategy.json", {})
    art = _read(directory / "art_direction.json", {})
    copy = _read(directory / "copy.json", {})
    understanding = _read(directory / "company_understanding.json", {})
    qa = dict(qa_report or _read(directory / "qa_report.json", {}))
    evidence_count = len(manifest.get("evidence_used", []))
    profile = strategy.get("layout_profile")
    iteration = int(manifest.get("generation_iteration", 1) or 1)
    calibrated = strategy.get("quality_calibration") == "customer_state_bridge_and_profile_composition"
    browser_pass = qa.get("status") == "PASS" and qa.get("mode") == "static_and_browser"
    base = {
        "Immediate Read": 4 if copy.get("hero", {}).get("headline") else 2,
        "Distinctness": 4 if profile and profile != "editorial_rail" else 3,
        "Owner Specificity": 4 if understanding.get("company_truth") and understanding.get("differentiators") else 3,
        "Visual Hierarchy": 4 if len(art.get("forbidden_patterns", [])) >= 5 else 3,
        "Craft Detail": 4 if art.get("craft_catch") else 2,
        "Emotional Pull": 4 if calibrated and understanding.get("customer_state", {}).get("before") else 3,
        "Trust": min(5, 2 + evidence_count // 2),
        "Share Impulse": 4 if profile in {"experience_calendar", "catalogue_spread", "technical_drawing"} else 3,
        "Mobile Quality": 4 if browser_pass else 2,
        "Conversion Intent": 4 if understanding.get("conversion_goal") and manifest.get("output_status") == "PRODUCTION_APPROVED" else 3,
    }
    creative = dict(base)
    business = dict(base)
    business["Distinctness"] = max(2, business["Distinctness"] - 1)
    business["Craft Detail"] = max(2, business["Craft Detail"] - 1)
    business["Trust"] = min(5, business["Trust"] + (1 if evidence_count >= 5 else 0))
    business["Conversion Intent"] = min(5, business["Conversion Intent"] + (1 if calibrated else 0))
    return {
        "review_type": "structured_review_roles",
        "iteration": iteration,
        "reviewer_roles": {
            "creative_art_direction": {"label": "Creative / Art Direction", "scores": creative},
            "business_owner_conversion": {"label": "Business Owner / Conversion", "scores": business},
        },
        "axes": list(AXES),
        "method": "deterministic role rubric from manifest, stage outputs and QA signals; not an independent human review",
        "average_scores": {
            "creative_art_direction": round(sum(creative.values()) / len(creative), 2),
            "business_owner_conversion": round(sum(business.values()) / len(business), 2),
        },
        "sales_sample_gate": "PASS" if min(sum(creative.values()), sum(business.values())) / len(AXES) >= 4 else "HOLD",
        "decision": "ENGINE_IMPROVEMENT_REQUIRED" if iteration == 1 else "SALES_SAMPLE_MVP_HOLD",
    }


def diagnose_quality(output_dir: str | Path, *, qa_report: Mapping[str, Any] | None = None, review: Mapping[str, Any] | None = None) -> dict[str, Any]:
    directory = Path(output_dir)
    manifest = _read(directory / "generation_manifest.json", {})
    strategy = _read(directory / "creative_strategy.json", {})
    understanding = _read(directory / "company_understanding.json", {})
    qa = dict(qa_report or _read(directory / "qa_report.json", {}))
    review = dict(review or _read(directory / "structured_review.json", {}))
    issues: list[dict[str, Any]] = []
    if manifest.get("output_status") != "PRODUCTION_APPROVED" or manifest.get("safety_status") != "PASS":
        issues.append(_issue("safety-output", "SAFETY", "S0", "Trust", "all", "production", "Production status is not Safety-approved.", "SAFETY", "evidence_safety", "P0"))
    if qa.get("status") == "FAIL":
        issues.append(_issue("qa-integrity", "RENDERER", "S0", "Mobile Quality", "all", "rendered output", "Browser or static QA reported a hard failure.", "RENDERER", "browser_qa_and_renderer", "P0"))
    if not understanding.get("company_truth"):
        issues.append(_issue("company-truth", "COMPANY_TRUTH", "S1", "Owner Specificity", "all", "hero", "No company-specific truth reached the understanding stage.", "COMPANY_TRUTH", "company_understanding", "P1"))
    if not strategy.get("layout_profile") or strategy.get("layout_profile") == "editorial_rail":
        issues.append(_issue("form-profile", "ART_DIRECTION", "S1", "Distinctness", "all", "hero", "No conversion- or authority-specific form profile was selected.", "ART_DIRECTION", "art_direction_and_composition", "P1"))
    if int(manifest.get("generation_iteration", 1) or 1) == 1 and understanding.get("customer_state", {}).get("before"):
        issues.append(_issue("state-bridge", "COPY", "S1", "Immediate Read", "all", "hero", "First pass does not explicitly bridge the customer's starting state to the service entrance.", "COPY", "copy_generation", "P1"))
    if len(manifest.get("evidence_used", [])) < 3:
        issues.append(_issue("sparse-evidence", "EVIDENCE", "S2", "Trust", "all", "proof", "Evidence density is low; creative richness must not be filled with invented facts.", "EVIDENCE", "evidence_selection_and_art_direction", "P2"))
    if len(review) == 0:
        issues.append(_issue("missing-review", "STRATEGY", "S1", "Immediate Read", "all", "page", "Structured review output is missing.", "STRATEGY", "quality_diagnosis", "P1"))
    return {
        "diagnosis_type": "production_quality_diagnosis",
        "generation_id": manifest.get("generation_id"),
        "generation_iteration": manifest.get("generation_iteration", 1),
        "status": "PASS" if not issues else "IMPROVEMENT_REQUIRED",
        "issue_count": len(issues),
        "issues": issues,
        "root_cause_summary": sorted({item["likely_root_cause"] for item in issues}),
        "manual_intervention": manifest.get("manual_intervention", []),
        "structured_review_method": review.get("method", ""),
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Diagnose a generated Production LP")
    parser.add_argument("output_dir")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    directory = Path(args.output_dir)
    review = build_structured_review(directory)
    diagnosis = diagnose_quality(directory, review=review)
    (directory / "structured_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.out).write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(diagnosis, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
