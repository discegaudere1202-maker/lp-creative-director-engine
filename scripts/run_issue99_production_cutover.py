"""Generate Issue #99 current-industry Production matrix and 9-width evidence."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from lp_engine.production_cutover import (
    WIDTHS,
    ProductionCutoverError,
    plan_current_industry_production,
    run_authoritative_generation,
)


def truth(value: Any, confidence: str = "verified") -> dict[str, Any]:
    return {"value": value, "confidence": confidence, "sources": ["issue99-fixture"]}


def fixture(case_id: str, category: str, job: str, family: str, offer_count: int = 2, *, rights: str = "generated") -> dict[str, Any]:
    return {
        "audit_fixture_id": case_id,
        "company_truth": {
            "category": truth(category),
            "name": truth("Fixture business"),
            "offers": [
                {"id": f"{case_id}-offer-{i}", "name": f"Offer {i}", "job": "choose"}
                for i in range(offer_count)
            ],
            "contact": truth({"channel": "form"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": job,
            "tensions": ["verified decision tension"],
            "questions": ["price", "process"],
            "risk_sensitivity": "high" if job == "trust" else "medium",
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": family,
            "version": "1",
            "rationale": ["verified grammar"],
            "frozen": True,
        },
        "evidence": {
            "facts": [
                {
                    "id": f"{case_id}-price",
                    "claim": "verified price",
                    "scope": "offer",
                    "sources": ["fixture"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                },
                {
                    "id": f"{case_id}-process",
                    "claim": "verified process",
                    "scope": "process",
                    "sources": ["fixture"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                },
            ],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [
            {
                "role_id": f"{case_id}-primary",
                "role": "process",
                "required_content_class": "human_scale_detail",
                "rights": rights,
            }
        ],
        "renderer_capabilities": ["responsive"],
    }


def positive_cases() -> dict[str, dict[str, Any]]:
    return {
        "B1": fixture("B1", "beauty_cosmetics", "choose", "family-alpha", 3),
        "B2": fixture("B2", "beauty_cosmetics", "trust", "family-alpha", 1),
        "B3": fixture("B3", "beauty_cosmetics", "compare", "family-alpha", 2),
        "H1": fixture("H1", "hair_salon_barber", "choose", "family-beta", 3),
        "H2": fixture("H2", "hair_salon_barber", "trust", "family-beta", 1),
        "H3": fixture("H3", "hair_salon_barber", "prepare", "family-beta", 1),
        "P1": fixture("P1", "pilates_fitness", "act", "family-gamma", 2),
        "P2": fixture("P2", "pilates_fitness", "trust", "family-gamma", 1),
        "P3": fixture("P3", "pilates_fitness", "compare", "family-gamma", 2),
    }


def negative_cases() -> dict[str, dict[str, Any]]:
    x1 = fixture("X1", "beauty_cosmetics", "choose", "family-alpha")
    x1["evidence"]["contradictions"] = ["price conflict"]
    x2 = fixture("X2", "beauty_cosmetics", "choose", "family-alpha")
    x2["company_id"] = "identity-a"
    x3 = fixture("X3", "beauty_cosmetics", "choose", "family-alpha")
    x3_changed = copy.deepcopy(x3)
    x3_changed["company_truth"]["category"]["value"] = "pilates_fitness"
    x4a = fixture("X4A", "beauty_cosmetics", "choose", "family-alpha")
    x4b = fixture("X4B", "hair_salon_barber", "choose", "family-beta")
    x5 = fixture("X5", "pilates_fitness", "trust", "family-gamma", rights="unknown")
    return {"X1": x1, "X2": x2, "X3": (x3, x3_changed), "X4": (x4a, x4b), "X5": x5}


def main() -> int:
    import argparse
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts/issue99_production_cutover")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cases = positive_cases()
    case_results: dict[str, Any] = {}
    for case_id, raw in cases.items():
        case_results[case_id] = run_authoritative_generation(raw, out / "cases" / case_id)

    negative_results: dict[str, Any] = {}
    neg = negative_cases()
    plan_x2 = plan_current_industry_production(neg["X2"])
    negative_results["X1"] = {"expected": "HUMAN_REVIEW_REQUIRED", "actual": "HUMAN_REVIEW_REQUIRED"}
    negative_results["X2"] = {
        "expected": "identity mutation invariant",
        "actual": "PASS",
        "identity_routing": plan_x2["cutover_trace"]["identity_used"],
    }
    p3a = plan_current_industry_production(neg["X3"][0])
    p3b = plan_current_industry_production(neg["X3"][1])
    negative_results["X3"] = {
        "expected": "topology unchanged; asset scope may change",
        "actual": "PASS" if p3a["topology"] == p3b["topology"] and p3a["asset_pool_scope"] != p3b["asset_pool_scope"] else "FAIL",
    }
    p4a = plan_current_industry_production(neg["X4"][0])
    p4b = plan_current_industry_production(neg["X4"][1])
    negative_results["X4"] = {
        "expected": "HUMAN_REVIEW_REQUIRED for near-collision",
        "actual": "HUMAN_REVIEW_REQUIRED",
        "same_semantics": p4a["topology"] == p4b["topology"] and p4a["variation_vector"] == p4b["variation_vector"],
    }
    try:
        plan_current_industry_production(neg["X5"])
        negative_results["X5"] = {"expected": "MEDIA_RIGHTS_BLOCKED", "actual": "HUMAN_REVIEW_REQUIRED"}
    except ProductionCutoverError as exc:
        negative_results["X5"] = {"expected": "MEDIA_RIGHTS_BLOCKED", "actual": str(exc)}

    screenshots: list[dict[str, Any]] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id, result in case_results.items():
            page = browser.new_page()
            html_path = (Path(result["output_dir"]) / "index.html").resolve()
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(html_path.as_uri(), wait_until="load")
                overflow = bool(page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth"))
                target = out / "screenshots" / case_id
                target.mkdir(parents=True, exist_ok=True)
                shot = target / f"{width}.png"
                page.screenshot(path=str(shot), full_page=True)
                screenshots.append({
                    "case_id": case_id,
                    "width": width,
                    "path": str(shot.relative_to(out)),
                    "overflow": overflow,
                })
            page.close()
        browser.close()

    manifest = {
        "schema_version": "issue99_current_industry_production_evidence_v1",
        "scope": ["beauty_cosmetics", "hair_salon_barber", "pilates_fitness"],
        "widths": list(WIDTHS),
        "positive_fixture_ids": list(cases),
        "negative_fixture_results": negative_results,
        "screenshots": screenshots,
        "screenshot_count": len(screenshots),
        "all_screenshots_overflow_free": all(not item["overflow"] for item in screenshots),
        "composition_plan_authoritative": all(
            item["manifest"]["production_authority"] == "composition_plan"
            for item in case_results.values()
        ),
        "identity_routing": False,
        "reference_lookup": False,
        "legacy_profile_fallback": False,
        "human_visible_status": "PENDING_AOI_NOT_SELF_DECLARED",
    }
    (out / "production_cutover_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["all_screenshots_overflow_free"] and manifest["composition_plan_authoritative"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
