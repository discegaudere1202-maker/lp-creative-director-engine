"""Generate controlled current-domain HTML and 9-width browser evidence."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from lp_engine.authored_composition_contract import (
    assert_decision_sensitivity,
    assert_identity_invariance,
    infer_authored_composition,
)
from lp_engine.controlled_render import write_controlled_case


WIDTHS = (320, 360, 375, 390, 430, 768, 1024, 1280, 1440)


def truth(value: Any) -> dict[str, Any]:
    return {"value": value, "confidence": "verified", "sources": ["synthetic-verified-fixture"]}


def fixture(
    fixture_id: str,
    *,
    family_id: str,
    category: str,
    primary_job: str,
    offer_count: int,
    media_role: str,
    risk: str = "medium",
) -> dict[str, Any]:
    offers = [
        {"id": f"{fixture_id}-offer-{i}", "name": f"Offer {i}", "job": "receive"}
        for i in range(offer_count)
    ]
    if offer_count > 1:
        offers[-1]["job"] = "learn"
    return {
        "audit_fixture_id": fixture_id,
        "company_truth": {
            "category": truth(category),
            "name": truth("Synthetic current-domain business"),
            "offers": offers,
            "contact": truth({"channel": "form"}),
            "unknowns": [],
        },
        "customer_decision_state": {
            "primary_job": primary_job,
            "tensions": ["verified decision tension"],
            "questions": ["price", "process"],
            "risk_sensitivity": risk,
            "decision_stage": "consider",
        },
        "creative_family": {
            "family_id": family_id,
            "version": "1",
            "rationale": ["verified decision shape"],
            "frozen": True,
        },
        "evidence": {
            "facts": [
                {
                    "id": f"{fixture_id}-price",
                    "claim": "verified price",
                    "scope": "offer",
                    "sources": ["synthetic-verified-fixture"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                },
                {
                    "id": f"{fixture_id}-process",
                    "claim": "verified process",
                    "scope": "process",
                    "sources": ["synthetic-verified-fixture"],
                    "confidence": "verified",
                    "usable_for_persuasion": True,
                },
            ],
            "proof_gaps": [],
            "contradictions": [],
        },
        "media_roles": [{
            "role_id": f"{fixture_id}-media",
            "role": media_role,
            "required_content_class": "non_identifying_context",
            "rights": "generated",
        }],
        "renderer_capabilities": ["responsive"],
    }


def cases() -> dict[str, dict[str, Any]]:
    return {
        "beauty-choice-same-family": fixture(
            "beauty-choice-same-family",
            family_id="family-alpha",
            category="beauty",
            primary_job="choose",
            offer_count=3,
            media_role="person",
        ),
        "pilates-trust-same-family": fixture(
            "pilates-trust-same-family",
            family_id="family-alpha",
            category="pilates-fitness",
            primary_job="trust",
            offer_count=1,
            media_role="process",
            risk="high",
        ),
        "cosmetics-cross-family": fixture(
            "cosmetics-cross-family",
            family_id="family-beta",
            category="cosmetics",
            primary_job="compare",
            offer_count=2,
            media_role="material",
        ),
        "hair-cross-family": fixture(
            "hair-cross-family",
            family_id="family-gamma",
            category="hair_salon",
            primary_job="compare",
            offer_count=2,
            media_role="material",
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="artifacts/issue92_controlled_render")
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    inputs = cases()
    plans = {key: infer_authored_composition(value) for key, value in inputs.items()}

    identity_mutation = copy.deepcopy(inputs["beauty-choice-same-family"])
    identity_mutation["company_truth"]["name"]["value"] = "Different identity"
    identity_mutation["company_truth"]["name"]["sources"] = ["different-source"]
    assert_identity_invariance(inputs["beauty-choice-same-family"], identity_mutation)

    decision_mutation = copy.deepcopy(inputs["beauty-choice-same-family"])
    decision_mutation["customer_decision_state"]["primary_job"] = "trust"
    decision_mutation["customer_decision_state"]["risk_sensitivity"] = "high"
    assert_decision_sensitivity(inputs["beauty-choice-same-family"], decision_mutation)

    same_family_material_difference = (
        plans["beauty-choice-same-family"]["variation_vector"]
        != plans["pilates-trust-same-family"]["variation_vector"]
        and plans["beauty-choice-same-family"]["topology"]
        != plans["pilates-trust-same-family"]["topology"]
    )
    cross_family_collision = (
        plans["cosmetics-cross-family"]["topology"]
        == plans["hair-cross-family"]["topology"]
        and plans["cosmetics-cross-family"]["variation_vector"]
        == plans["hair-cross-family"]["variation_vector"]
    )

    render_cases = {}
    for case_id, raw in inputs.items():
        case_dir = output / "cases" / case_id
        manifest = write_controlled_case(raw, case_dir)
        render_cases[case_id] = {
            "audit_fixture_id": case_id,
            "plan_digest": manifest["plan_digest"],
            "topology": manifest["topology"],
            "variation_vector": manifest["variation_vector"],
            "html": str((case_dir / "index.html").relative_to(output)),
            "screenshots": [],
        }

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id in inputs:
            page = browser.new_page()
            html_path = (output / render_cases[case_id]["html"]).resolve()
            for width in WIDTHS:
                page.set_viewport_size({"width": width, "height": 900})
                page.goto(html_path.as_uri(), wait_until="load")
                overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
                shot = output / "screenshots" / case_id
                shot.mkdir(parents=True, exist_ok=True)
                shot_path = shot / f"{width}.png"
                page.screenshot(path=str(shot_path), full_page=True)
                render_cases[case_id]["screenshots"].append({
                    "width": width,
                    "path": str(shot_path.relative_to(output)),
                    "overflow": bool(overflow),
                })
            page.close()
        browser.close()

    manifest = {
        "schema_version": "issue92_controlled_render_v1",
        "renderer_mode": "controlled_shadow_consumer",
        "domains": ["beauty", "cosmetics", "hair_salon", "pilates_fitness"],
        "widths": list(WIDTHS),
        "cases": render_cases,
        "same_family_material_difference": same_family_material_difference,
        "cross_family_near_collision": {
            "same_semantics": cross_family_collision,
            "status": "HUMAN_REVIEW_REQUIRED" if cross_family_collision else "DISTINGUISHABLE",
        },
        "identity_mutation_invariance": "PASS",
        "decision_mutation_sensitivity": "PASS",
        "identity_routing": False,
        "reference_lookup": False,
        "fit_freezes_before_feasibility": True,
        "human_visible_template_resemblance": "PENDING_AOI_NOT_SELF_DECLARED",
        "screenshot_count": sum(len(item["screenshots"]) for item in render_cases.values()),
        "all_screenshots_overflow_free": all(
            not shot["overflow"]
            for item in render_cases.values()
            for shot in item["screenshots"]
        ),
    }
    (output / "controlled_render_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["all_screenshots_overflow_free"] and same_family_material_difference else 1


if __name__ == "__main__":
    raise SystemExit(main())
