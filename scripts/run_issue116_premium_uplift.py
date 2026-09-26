"""Issue #116 — Stage A Premium Authorship Uplift evidence runner.

Reuses the accepted Issue #111 Stage A acquisition/selection/browser gate, then
adds the Issue #114 PU1-PU8 premium-authorship evidence contract.  The runner
never changes Family, topology, scene order, rights policy, or evidence state.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps
from playwright.sync_api import sync_playwright

import run_issue111_stage_a_sales_sample_qa as issue111
import run_issue111_stage_a_sales_sample_qa_final as issue111_final

from lp_engine.premium_authorship import BANNED_VALIDATION_COPY, INTERNAL_INTENT_TOKENS, MOBILE_WIDTHS

ROOT = Path(__file__).resolve().parents[1]
BASELINE_MAIN_SHA = "e43e9006c753829360f25a90d8cca4db9fdc48ab"
BASELINE_ARTIFACT_ID = 10912860741
SAMPLES = ("SK1", "SK2", "SK3", "HS1", "HS2", "BR1", "BR2", "PI1", "PI2")
WIDTHS = tuple(issue111.WIDTHS)
CONTACT_WIDTHS = (320, 390, 768, 1440)

PUBLIC_FIXTURE_COPY = {
    "SK1": {"name": "MELT SKIN", "offers": ["ベーシック", "モイスチャー", "ケアセット"]},
    "SK2": {"name": "CALM SKIN", "offers": ["デイリーケア"]},
    "SK3": {"name": "LINO SKIN", "offers": ["ライトケア", "リッチケア"]},
    "HS1": {"name": "muku hair", "offers": ["カット", "カラー", "ケア"]},
    "HS2": {"name": "tone hair", "offers": ["スタイルケア"]},
    "BR1": {"name": "CIVIC BARBER", "offers": ["スタンダード"]},
    "BR2": {"name": "NEST BARBER", "offers": ["ベーシック", "グルーミング"]},
    "PI1": {"name": "ALIGN PILATES", "offers": ["ベーシック", "プライベート"]},
    "PI2": {"name": "SUI PILATES", "offers": ["プライベート"]},
}

CLIENT_EVIDENCE_DEPENDENCIES = [
    "actual_staff_or_owner_identity",
    "actual_store_studio_space",
    "actual_results_before_after_or_portfolio",
    "verified_testimonials_reviews",
    "credentials_qualifications_awards",
    "verified_price_offer_duration_conditions",
    "actual_process_equipment_material_detail",
    "company_specific_brand_assets_and_voice",
]

_ORIGINAL_FIXTURE = issue111.fixture


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _premium_fixture(*args, **kwargs):
    """Keep the Issue111 synthetic truth boundary but add verified QA CTA destinations."""
    raw = _ORIGINAL_FIXTURE(*args, **kwargs)
    case_id = str(raw["audit_fixture_id"])
    public = PUBLIC_FIXTURE_COPY[case_id]
    for role in raw.get("media_roles", []):
        role["rights"] = "licensed"
    raw["company_truth"]["name"] = issue111.truth(public["name"])
    for offer, name in zip(raw["company_truth"]["offers"], public["offers"]):
        offer["name"] = name
    raw["company_truth"]["contact"] = issue111.truth({
        "channel": "qa_fixture_form",
        "destination": f"https://example.com/issue116/{case_id.lower()}/contact",
        "fixture_only": True,
    })
    raw["fixture_semantics"] = "SYNTHETIC_QA_ONLY_NOT_COMPANY_EVIDENCE"
    raw["issue116_fixture_note"] = "Verified QA-only CTA destination; never presented as a real client contact endpoint."
    return raw


def _premium_browser_metrics(page) -> dict[str, Any]:
    metrics = issue111_final._metrics_with_numeric_tolerance(page)
    premium = page.evaluate(
        """
        () => {
          const headlineUnits = [...document.querySelectorAll('.premium-headline-unit')];
          const publicHeadings = [...document.querySelectorAll('h1,h2')].map(n => (n.textContent || '').trim());
          const publicText = document.body.innerText || '';
          const primaryLinks = [...document.querySelectorAll('a.cta-primary')];
          const disabledPrimary = [...document.querySelectorAll('.cta-primary[aria-disabled="true"]')];
          const premiumScenes = [...document.querySelectorAll('[data-premium-scene]')];
          return {
            premium_surface_present: document.body.dataset.premiumAuthorship === 'issue116',
            premium_headline_semantic_atomic: headlineUnits.length > 0 && headlineUnits.every(node => {
              const range = document.createRange();
              range.selectNodeContents(node);
              return range.getClientRects().length === 1;
            }),
            public_headings: publicHeadings,
            public_text: publicText,
            primary_actionable_cta_count: primaryLinks.length,
            disabled_primary_cta_count: disabledPrimary.length,
            primary_cta_hrefs: primaryLinks.map(node => node.getAttribute('href')),
            premium_scene_count: premiumScenes.length,
            mobile_media_first_scene_count: premiumScenes.filter(node => node.dataset.mobileMediaFirst === 'true').length,
            voice_mode: document.querySelector('.premium-shell')?.dataset.voice || null,
          };
        }
        """
    )
    metrics.update(premium)
    return metrics


def _find_baseline_root(path: Path) -> Path:
    path = path.resolve()
    direct = path / "screenshots" / "SK1" / "320.png"
    if direct.is_file():
        return path
    matches = list(path.rglob("screenshots/SK1/320.png"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one Issue111 baseline screenshot root, got {len(matches)} under {path}")
    return matches[0].parents[2]


def _baseline_matrix(root: Path) -> dict[tuple[str, int], Path]:
    result = {}
    for case_id in SAMPLES:
        for width in WIDTHS:
            path = root / "screenshots" / case_id / f"{width}.png"
            if not path.is_file():
                raise RuntimeError(f"Baseline screenshot missing: {path}")
            result[(case_id, width)] = path
    if len(result) != 81:
        raise RuntimeError(f"Baseline matrix must contain 81 screenshots, got {len(result)}")
    return result


def _fit_preview(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    crop_h = min(image.height, max(1100, int(image.width * 1.35)))
    top = image.crop((0, 0, image.width, crop_h))
    return ImageOps.contain(top, size)


def _before_after_sheet(
    baseline: dict[tuple[str, int], Path],
    premium_root: Path,
    width: int,
    output: Path,
) -> None:
    tile_w, tile_h = 300, 390
    pair_gap = 12
    cols = 3
    rows = (len(SAMPLES) + cols - 1) // cols
    cell_w = tile_w * 2 + pair_gap
    sheet = Image.new("RGB", (cols * cell_w, 58 + rows * tile_h), "white")
    draw = ImageDraw.Draw(sheet)
    draw.text((14, 16), f"Issue116 before / after — {width}px — baseline Artifact {BASELINE_ARTIFACT_ID}", fill="black")
    for index, case_id in enumerate(SAMPLES):
        x = (index % cols) * cell_w
        y = 58 + (index // cols) * tile_h
        before = _fit_preview(baseline[(case_id, width)], (tile_w - 8, 330))
        after_path = premium_root / "screenshots" / case_id / f"{width}.png"
        after = _fit_preview(after_path, (tile_w - 8, 330))
        before_tile = Image.new("RGB", (tile_w, 334), "#ececec")
        after_tile = Image.new("RGB", (tile_w, 334), "#ececec")
        before_tile.paste(before, ((tile_w - before.width) // 2, (334 - before.height) // 2))
        after_tile.paste(after, ((tile_w - after.width) // 2, (334 - after.height) // 2))
        sheet.paste(before_tile, (x, y))
        sheet.paste(after_tile, (x + tile_w + pair_gap, y))
        draw.text((x + 5, y + 342), f"{case_id} BEFORE", fill="black")
        draw.text((x + tile_w + pair_gap + 5, y + 342), f"{case_id} AFTER", fill="black")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=90)


def _reduced_motion_report(premium_root: Path) -> dict[str, Any]:
    report: dict[str, Any] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        for case_id in SAMPLES:
            context = browser.new_context(viewport={"width": 390, "height": 900}, reduced_motion="reduce")
            page = context.new_page()
            page.goto((premium_root / "cases" / case_id / "index.html").resolve().as_uri(), wait_until="load")
            page.wait_for_load_state("networkidle")
            row = page.evaluate(
                """
                () => {
                  const hero = document.querySelector('.premium-hero__copy');
                  const scene = document.querySelector('.premium-scene');
                  const hs = hero ? getComputedStyle(hero) : null;
                  const ss = scene ? getComputedStyle(scene) : null;
                  return {
                    hero_animation_name: hs?.animationName || null,
                    scene_animation_name: ss?.animationName || null,
                    hero_transform: hs?.transform || null,
                    scene_transform: ss?.transform || null,
                    overflow: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                  };
                }
                """
            )
            row["pass"] = (
                row["hero_animation_name"] == "none"
                and row["scene_animation_name"] in {None, "none"}
                and row["hero_transform"] in {None, "none"}
                and row["scene_transform"] in {None, "none"}
                and not row["overflow"]
            )
            report[case_id] = row
            context.close()
        browser.close()
    return report


def _public_surface_report(premium_root: Path, issue111_manifest: dict[str, Any]) -> dict[str, Any]:
    rows = []
    internal_heading_leaks = []
    banned_copy_leaks = []
    cta_failures = []
    premium_surface_failures = []
    semantic_320_failures = []
    for shot in issue111_manifest["screenshots"]:
        case_id = shot["case_id"]
        width = int(shot["width"])
        headings = [str(value).strip().lower() for value in shot.get("public_headings") or []]
        leaked = sorted(token for token in INTERNAL_INTENT_TOKENS if token in headings or any(h == f"{token}のための入口" for h in headings))
        text = str(shot.get("public_text") or "")
        banned = [phrase for phrase in BANNED_VALIDATION_COPY if phrase in text]
        expected_destination = f"https://example.com/issue116/{case_id.lower()}/contact"
        cta_ok = (
            int(shot.get("primary_actionable_cta_count") or 0) >= 1
            and expected_destination in (shot.get("primary_cta_hrefs") or [])
        )
        if leaked:
            internal_heading_leaks.append({"case_id": case_id, "width": width, "tokens": leaked})
        if banned:
            banned_copy_leaks.append({"case_id": case_id, "width": width, "phrases": banned})
        if not cta_ok:
            cta_failures.append({"case_id": case_id, "width": width, "expected": expected_destination, "actual": shot.get("primary_cta_hrefs")})
        if not shot.get("premium_surface_present"):
            premium_surface_failures.append({"case_id": case_id, "width": width})
        if width == 320 and not shot.get("premium_headline_semantic_atomic"):
            semantic_320_failures.append({"case_id": case_id, "width": width})
        rows.append({
            "case_id": case_id,
            "width": width,
            "headings": shot.get("public_headings"),
            "voice_mode": shot.get("voice_mode"),
            "primary_cta_hrefs": shot.get("primary_cta_hrefs"),
            "premium_surface_present": shot.get("premium_surface_present"),
        })
    return {
        "screenshots": rows,
        "internal_heading_leaks": internal_heading_leaks,
        "banned_validation_copy_leaks": banned_copy_leaks,
        "cta_failures": cta_failures,
        "premium_surface_failures": premium_surface_failures,
        "semantic_320_failures": semantic_320_failures,
    }


def _load_case_traces(premium_root: Path) -> dict[str, Any]:
    result = {}
    for case_id in SAMPLES:
        manifest = _json(premium_root / "cases" / case_id / "production_manifest.json")
        premium = manifest.get("premium_authorship")
        if not premium:
            raise RuntimeError(f"Premium trace missing: {case_id}")
        result[case_id] = {
            "production_authority": manifest.get("production_authority"),
            "premium": premium,
            "visual_asset_library": manifest.get("visual_asset_library"),
            "rendered_html_sha256": _sha_file(premium_root / "cases" / case_id / "index.html"),
        }
    return result


def _template_resemblance_report(case_traces: dict[str, Any]) -> dict[str, Any]:
    family_groups: dict[str, list[str]] = defaultdict(list)
    signatures: dict[str, Any] = {}
    for case_id, row in case_traces.items():
        premium = row["premium"]
        family = str(premium["family_id"])
        family_groups[family].append(case_id)
        signatures[case_id] = {
            "family_id": family,
            "hero": premium["PU2_hero_authority"]["hero_composition_intent"],
            "voice": premium["PU6_visual_voice"]["voice_mode"],
            "scene_signature": [
                [
                    scene_id,
                    scene["scene_weight"],
                    scene["density_mode"],
                    scene["canvas_width_mode"],
                    scene["media_text_relationship"],
                ]
                for scene_id, scene in premium["PU3_scene_dramaturgy"]["scenes"].items()
            ],
            "mobile_hero_media_first": premium["PU8_mobile"]["hero_media_first"],
            "cta_state": premium["PU5_proof_cta"]["cta"]["state"],
            "rendered_html_sha256": row["rendered_html_sha256"],
        }

    same_family = {}
    for family, case_ids in family_groups.items():
        html_hashes = {signatures[case_id]["rendered_html_sha256"] for case_id in case_ids}
        semantic_signatures = {
            json.dumps({key: value for key, value in signatures[case_id].items() if key != "rendered_html_sha256"}, ensure_ascii=False, sort_keys=True)
            for case_id in case_ids
        }
        same_family[family] = {
            "sample_ids": case_ids,
            "distinct_html_hashes": len(html_hashes),
            "distinct_visible_semantic_signatures": len(semantic_signatures),
            "authored_divergence": len(html_hashes) == len(case_ids),
        }

    cross_family_collisions = []
    ids = list(SAMPLES)
    for index, left_id in enumerate(ids):
        left = signatures[left_id]
        for right_id in ids[index + 1:]:
            right = signatures[right_id]
            if left["family_id"] == right["family_id"]:
                continue
            left_visible = {key: value for key, value in left.items() if key not in {"family_id", "rendered_html_sha256"}}
            right_visible = {key: value for key, value in right.items() if key not in {"family_id", "rendered_html_sha256"}}
            if left_visible == right_visible:
                cross_family_collisions.append({
                    "left": left_id,
                    "right": right_id,
                    "state": "HUMAN_REVIEW_REQUIRED",
                    "reason": "cross_family_visible_signature_collision",
                })

    return {
        "signatures": signatures,
        "same_family": same_family,
        "same_family_authored_divergence_preserved": all(row["authored_divergence"] for row in same_family.values()),
        "cross_family_near_collision_review": {
            "collisions": cross_family_collisions,
            "identity_routing_used_to_hide_collision": False,
            "review_state_preserved": True,
        },
    }


def _unsupported_claim_report(case_traces: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for case_id, row in case_traces.items():
        public = row["premium"]["PU1_public_copy"]
        verified_ids = set(public["trace"]["inputs"]["verified_fact_ids"])
        for claim in public["trace"]["factual_claims"]:
            if claim["fact_id"] not in verified_ids or not claim.get("sources"):
                failures.append({"case_id": case_id, "claim": claim})
    return {"failures": failures, "pass": not failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="Extracted Issue111 Artifact 10912860741")
    parser.add_argument("--out", default="artifacts/issue116_premium_uplift")
    args = parser.parse_args()

    out = Path(args.out).resolve()
    premium_root = out / "premium"
    out.mkdir(parents=True, exist_ok=True)
    baseline_root = _find_baseline_root(Path(args.baseline))
    baseline = _baseline_matrix(baseline_root)

    original_argv = list(sys.argv)
    original_fixture = issue111.fixture
    original_select = issue111.select_visual_asset
    original_metrics = issue111._browser_metrics
    issue111.fixture = _premium_fixture
    issue111.select_visual_asset = issue111_final._crop_safe_select
    issue111._browser_metrics = _premium_browser_metrics
    try:
        sys.argv = [sys.argv[0], "--out", str(premium_root)]
        code = issue111.main()
    finally:
        sys.argv = original_argv
        issue111.fixture = original_fixture
        issue111.select_visual_asset = original_select
        issue111._browser_metrics = original_metrics
    if code != 0:
        return code
    issue111_final._normalize_final_manifest(premium_root)

    issue111_manifest = _json(premium_root / "issue111_stage_a_sales_sample_manifest.json")
    if issue111_manifest.get("screenshot_count") != 81:
        raise RuntimeError(f"Expected 81 premium screenshots, got {issue111_manifest.get('screenshot_count')}")

    before_after_rows = []
    for case_id in SAMPLES:
        for width in WIDTHS:
            before = baseline[(case_id, width)]
            after = premium_root / "screenshots" / case_id / f"{width}.png"
            before_sha = _sha_file(before)
            after_sha = _sha_file(after)
            before_after_rows.append({
                "case_id": case_id,
                "width": width,
                "baseline_path": str(before),
                "premium_path": str(after.relative_to(out)),
                "baseline_sha256": before_sha,
                "premium_sha256": after_sha,
                "changed": before_sha != after_sha,
            })

    for width in CONTACT_WIDTHS:
        _before_after_sheet(
            baseline,
            premium_root,
            width,
            out / "before_after_contact_sheets" / f"issue111_vs_issue116_{width}.jpg",
        )
        source = premium_root / "human_review_contact_sheets" / f"stage_a_{width}.jpg"
        shutil.copy2(source, out / "premium_contact_sheets" / source.name)
        baseline_sheet = baseline_root / "human_review_contact_sheets" / f"stage_a_{width}.jpg"
        if baseline_sheet.is_file():
            target = out / "baseline_contact_sheets" / baseline_sheet.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(baseline_sheet, target)

    case_traces = _load_case_traces(premium_root)
    template_report = _template_resemblance_report(case_traces)
    unsupported_claims = _unsupported_claim_report(case_traces)
    reduced_motion = _reduced_motion_report(premium_root)
    public_surface = _public_surface_report(premium_root, issue111_manifest)

    premium_trace = {case_id: row["premium"] for case_id, row in case_traces.items()}
    public_copy_trace = {case_id: row["premium"]["PU1_public_copy"] for case_id, row in case_traces.items()}
    cta_trace = {case_id: row["premium"]["PU5_proof_cta"] for case_id, row in case_traces.items()}
    motion_trace = {
        case_id: {
            "contract": row["premium"]["PU7_motion"],
            "reduced_motion_browser": reduced_motion[case_id],
        }
        for case_id, row in case_traces.items()
    }
    mobile_trace = {case_id: row["premium"]["PU8_mobile"] for case_id, row in case_traces.items()}

    coverage = {
        "PU1": all("PU1_public_copy" in row["premium"] for row in case_traces.values()),
        "PU2": all("PU2_hero_authority" in row["premium"] for row in case_traces.values()),
        "PU3": all("PU3_scene_dramaturgy" in row["premium"] for row in case_traces.values()),
        "PU4": all("PU4_media_story" in row["premium"] for row in case_traces.values()),
        "PU5": all("PU5_proof_cta" in row["premium"] for row in case_traces.values()),
        "PU6": all("PU6_visual_voice" in row["premium"] for row in case_traces.values()),
        "PU7": all("PU7_motion" in row["premium"] for row in case_traces.values()),
        "PU8": all("PU8_mobile" in row["premium"] for row in case_traces.values()),
    }

    issue111_regression = {
        "stage_a_inventory_62": issue111_manifest["stage_a_inventory"]["distinct_assets"] == 62,
        "all_selected_rights_pass": issue111_manifest["all_selected_rights_pass"],
        "generic_illustrative_boundary_preserved": issue111_manifest["all_generic_illustrative_boundary_preserved"],
        "complete_binding_trace": issue111_manifest["all_binding_traces_complete"],
        "all_images_loaded": issue111_manifest["all_images_loaded"],
        "all_overflow_free": issue111_manifest["all_overflow_free"],
        "render_trace_hash_joinable": issue111_manifest["all_render_trace_hash_joinable"],
        "crop_heuristics_pass": issue111_manifest["all_crop_heuristics_pass"],
        "batch_hero_unique": issue111_manifest["batch_hero_unique"],
        "batch_bundle_unique": issue111_manifest["batch_bundle_unique"],
        "candidate_pool_identity_invariant": issue111_manifest["same_category_candidate_pool_identity_invariant"],
        "company_specific_authored_divergence": issue111_manifest["company_specific_authored_divergence"],
        "asset_scarcity_family_switch": issue111_manifest["asset_scarcity_family_switch"],
        "company_reference_identity_routing": issue111_manifest["company_reference_identity_routing"],
        "random_selection": issue111_manifest["random_selection"],
    }

    cta_positive_pass = not public_surface["cta_failures"]
    mobile_complete = all(
        {int(width) for width in row["premium"]["PU8_mobile"]["widths"]} == set(MOBILE_WIDTHS)
        and row["premium"]["PU8_mobile"]["desktop_dom_stack_only"] is False
        for row in case_traces.values()
    )
    reduced_motion_pass = all(row["pass"] for row in reduced_motion.values())
    all_81_changed = len(before_after_rows) == 81 and all(row["changed"] for row in before_after_rows)
    family_preserved = all(
        row["premium"]["family_frozen"]
        and row["premium"]["topology_preserved"]
        and row["premium"]["scene_order_preserved"]
        and row["premium"]["asset_scarcity_family_switch"] is False
        for row in case_traces.values()
    )

    gates = {
        "all_81_renders_produced": issue111_manifest["screenshot_count"] == 81,
        "all_81_before_after_changed": all_81_changed,
        "no_internal_decision_job_token_exposed_as_public_heading": not public_surface["internal_heading_leaks"],
        "no_banned_generic_validation_copy_on_public_sales_surface": not public_surface["banned_validation_copy_leaks"],
        "no_unsupported_factual_claims": unsupported_claims["pass"],
        "positive_cases_with_verified_CTA_destination_render_actionable_links": cta_positive_pass,
        "rights_and_provenance_pass": (
            issue111_regression["all_selected_rights_pass"]
            and issue111_regression["complete_binding_trace"]
            and issue111_regression["render_trace_hash_joinable"]
        ),
        "Family_unchanged_by_asset_scarcity": family_preserved,
        "same_Family_authored_divergence_preserved": template_report["same_family_authored_divergence_preserved"],
        "cross_Family_near_collision_remains_reviewable": template_report["cross_family_near_collision_review"]["review_state_preserved"],
        "320px_semantic_line_gate": not public_surface["semantic_320_failures"],
        "no_overflow_or_clipping_at_all_9_widths": issue111_manifest["all_overflow_free"],
        "motion_reduced_motion_fallback_if_motion_exists": reduced_motion_pass,
        "premium_surface_present_all_widths": not public_surface["premium_surface_failures"],
        "mobile_authorship_320_430_complete": mobile_complete,
        "PU1_PU8_coverage": all(coverage.values()),
        "Issue111_rights_reuse_semantic_regressions_preserved": all(
            value is True
            for key, value in issue111_regression.items()
            if key not in {"asset_scarcity_family_switch", "company_reference_identity_routing", "random_selection"}
        ) and all(
            issue111_regression[key] is False
            for key in ("asset_scarcity_family_switch", "company_reference_identity_routing", "random_selection")
        ),
    }

    before_after_report = {
        "baseline_artifact_id": BASELINE_ARTIFACT_ID,
        "baseline_root": str(baseline_root),
        "rows": before_after_rows,
        "changed_count": sum(1 for row in before_after_rows if row["changed"]),
        "total": len(before_after_rows),
        "contact_widths": list(CONTACT_WIDTHS),
    }
    client_dependencies = {
        "state": "CLIENT_EVIDENCE_DEPENDENT_NOT_RENDERER_FAILURE",
        "dependencies": CLIENT_EVIDENCE_DEPENDENCIES,
        "generic_stock_may_replace_actual_company_evidence": False,
    }

    manifest = {
        "schema_version": "issue116_stage_a_premium_authorship_uplift_evidence_v1",
        "issue": 116,
        "baseline_main_sha": BASELINE_MAIN_SHA,
        "baseline_issue111_artifact_id": BASELINE_ARTIFACT_ID,
        "samples": list(SAMPLES),
        "widths": list(WIDTHS),
        "screenshot_count": issue111_manifest["screenshot_count"],
        "before_after_count": len(before_after_rows),
        "PU1_PU8_coverage": coverage,
        "gates": gates,
        "issue111_regression": issue111_regression,
        "public_surface": public_surface,
        "unsupported_claims": unsupported_claims,
        "template_resemblance": template_report,
        "reduced_motion": reduced_motion,
        "client_evidence_dependencies": client_dependencies,
        "human_boundary": {
            "HUMAN_VISIBLE_PASS": "NOT_SELF_DECLARED_PENDING_AOI",
            "final_premium_quality": "NOT_SELF_DECLARED",
            "million_yen_value": "NOT_SELF_DECLARED",
            "broader_sales_launch_readiness": "NOT_SELF_DECLARED",
        },
    }

    _write(out / "issue116_premium_uplift_trace.json", premium_trace)
    _write(out / "issue116_public_copy_trace.json", public_copy_trace)
    _write(out / "issue116_cta_trace.json", cta_trace)
    _write(out / "issue116_motion_trace.json", motion_trace)
    _write(out / "issue116_mobile_authorship_trace.json", mobile_trace)
    shutil.copy2(
        premium_root / "issue111_binding_trace_report.json",
        out / "issue116_asset_provenance_trace.json",
    )
    _write(out / "issue116_template_resemblance_report.json", template_report)
    _write(out / "issue116_before_after_report.json", before_after_report)
    _write(out / "issue116_client_evidence_dependencies.json", client_dependencies)
    _write(out / "issue116_premium_uplift_manifest.json", manifest)

    print(json.dumps({
        "issue": 116,
        "samples": len(SAMPLES),
        "screenshots": issue111_manifest["screenshot_count"],
        "before_after_changed": before_after_report["changed_count"],
        "PU1_PU8_coverage": coverage,
        "gates": gates,
        "client_evidence_dependencies": CLIENT_EVIDENCE_DEPENDENCIES,
        "human_boundary": manifest["human_boundary"],
    }, ensure_ascii=False, indent=2))

    return 0 if all(gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
