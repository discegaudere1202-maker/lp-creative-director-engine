from __future__ import annotations

import asyncio
import json
from collections import Counter
from pathlib import Path

from playwright.async_api import async_playwright

from lp_engine.browser_qa import DEFAULT_WIDTHS, run_browser_qa_sync
from lp_engine.production_generation import run_generation


AUTHORITY_MAP = {
    "SERVICE": ["SENSORY", "PLACE", "TYPOGRAPHY", "WORLD"],
    "EXPERIENCE": ["SENSORY", "PLACE", "WORLD", "TYPOGRAPHY"],
    "TRUST": ["PLACE", "DOCUMENT", "TYPOGRAPHY", "SENSORY"],
    "CRAFT": ["MATERIAL", "PRODUCT", "PLACE", "TYPOGRAPHY"],
}


def load_targets(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload["targets"])


def build_input(target: dict) -> dict:
    company_id = target["id"]
    source = target["source"]
    service = target["service"]
    location = target["location"]
    evidence = []
    evidence_specs = [
        ("001", "SERVICE_SCOPE", f"{service}を案内している。", ["O3_PROCESS"], ["EARLY_PROOF", "MIDDLE"]),
        ("002", "PLACE_EXPERIENCE", f"{location}を拠点・対応エリアとして案内している。", ["O3_PROCESS"], ["HERO", "QUIET_CHAPTER"]),
        ("003", "CTA_CHANNEL", f"公式Instagramプロフィール: {source}", ["O4_NEXT"], ["BEFORE_CTA", "CTA_ZONE"]),
    ]
    for suffix, evidence_type, claim, objections, placements in evidence_specs:
        evidence.append(
            {
                "evidence_id": f"{company_id}-e-{suffix}",
                "company_id": company_id,
                "case_id": f"{company_id}-no-web-field-validation",
                "evidence_type": evidence_type,
                "evidence_strength": "E3_OPERATIONAL" if evidence_type != "CTA_CHANNEL" else "E5_DECISION_ENABLING",
                "target_objections": objections,
                "claim": claim,
                "source": source,
                "source_type": "official_social_profile",
                "verification_status": "VERIFIED",
                "verification_date": "2026-09-16",
                "usage_status": "PRODUCTION_ELIGIBLE",
                "placement_candidates": placements,
                "rights_status": "NOT_APPLICABLE",
                "hearing_required": False,
                "blocking_status": "NON_BLOCKING",
                "notes": "Text-only first-party public information. No client photo is represented as company evidence.",
            }
        )

    return {
        "schema_version": "production_generation_input_v1",
        "company_id": company_id,
        "company": {
            "company_name": target["name"],
            "industry": target["industry"],
            "service_category": service,
            "location": location,
            "business_model": "local_service",
            "company_truth": f"{location}で{service}の案内を公開している地域事業者。",
            "differentiators": [f"{service}を案内している。", f"{location}を拠点・対応エリアとしている。"],
            "visual_authority_candidates": AUTHORITY_MAP[target["authority"]],
            "contact_channels": {"instagram": source, "href": source},
        },
        "customer_state": {
            "before": target["barrier"],
            "after": "自分の状況を伝えて次の案内を確認してみようと思える",
            "barrier": target["barrier"],
        },
        "conversion_goal": "inquiry",
        "primary_objections": ["O3_PROCESS", "O4_NEXT"],
        "requested_claims": [],
        "unavailable_evidence": [
            "本人・実店舗・実施工・実商品の利用許諾済み写真",
            "公式一次情報で確認できない実績・受賞・顧客評価・保証",
            "公式一次情報で確認できない料金・返答時間・キャンセル方針",
        ],
        "evidence_ledger": evidence,
    }


async def capture_exact(html_path: Path, out_dir: Path) -> dict[str, str]:
    html = html_path.read_text(encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    captures = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        for name, width, height in [("mobile", 390, 844), ("desktop", 1440, 1000)]:
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.emulate_media(reduced_motion="reduce")
            await page.set_content(html, wait_until="load", timeout=45000)
            await page.evaluate("document.querySelectorAll('[data-reveal]').forEach(el => el.classList.add('is-visible'))")
            await page.wait_for_timeout(150)
            target = out_dir / f"{name}_{width}x{height}.png"
            await page.screenshot(path=str(target), full_page=False)
            captures[name] = str(target)
            await page.close()
        await browser.close()
    return captures


def structural_observations(case_dir: Path) -> dict:
    html = (case_dir / "index.html").read_text(encoding="utf-8")
    art = json.loads((case_dir / "art_direction.json").read_text(encoding="utf-8"))
    strategy = json.loads((case_dir / "creative_strategy.json").read_text(encoding="utf-8"))
    compositions = json.loads((case_dir / "compositions.json").read_text(encoding="utf-8"))
    return {
        "layout_profile": strategy.get("layout_profile"),
        "photography_logic": art.get("photography_logic"),
        "image_elements": html.lower().count("<img"),
        "hero_mark_count": html.count("hero-mark"),
        "section_count": html.count("<section"),
        "screenshot_peak_count": sum(1 for item in compositions if item.get("screenshot_peak")),
        "image_roles": sorted({item.get("image_role") for item in compositions}),
        "cta_points_to_social_profile": "instagram.com" in html,
        "manual_intervention": json.loads((case_dir / "generation_manifest.json").read_text(encoding="utf-8")).get("manual_intervention"),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", default="config/no_web_field_validation_targets_v1.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    targets = load_targets(Path(args.targets))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    case_results = []

    for index, target in enumerate(targets, 1):
        case_dir = out / f"{index:02d}_{target['id']}"
        input_payload = build_input(target)
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "field_input.json").write_text(json.dumps(input_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = run_generation(input_payload, case_dir, generation_id=f"field-{index:02d}-{target['id']}")
        qa_dir = case_dir / "browser_qa"
        qa = run_browser_qa_sync(str(case_dir / "index.html"), qa_dir, widths=DEFAULT_WIDTHS, height=1000, screenshot_widths=[390, 1440])
        exact = asyncio.run(capture_exact(case_dir / "index.html", case_dir / "exact_capture"))
        obs = structural_observations(case_dir)

        case_results.append(
            {
                "index": index,
                "company_id": target["id"],
                "company_name": target["name"],
                "industry": target["industry"],
                "service": target["service"],
                "location": target["location"],
                "source": target["source"],
                "safety_status": result.safety_report.get("safety_status"),
                "browser_qa_status": qa.status,
                "exact_capture": exact,
                "structural_observations": obs,
            }
        )

    profile_counts = Counter(row["structural_observations"]["layout_profile"] for row in case_results)
    photo_logic_counts = Counter(row["structural_observations"]["photography_logic"] for row in case_results)
    image_role_counts = Counter(tuple(row["structural_observations"]["image_roles"]) for row in case_results)
    summary = {
        "phase": "LP品質最終実地検証Phase",
        "scope": "NO_WEB only",
        "population": len(case_results),
        "engine_only": True,
        "manual_lp_edit": 0,
        "widths": DEFAULT_WIDTHS,
        "exact_viewports": ["390x844", "1440x1000"],
        "browser_pass": sum(1 for row in case_results if row["browser_qa_status"] == "PASS"),
        "safety_pass": sum(1 for row in case_results if row["safety_status"] == "PASS"),
        "layout_profile_counts": dict(profile_counts),
        "photography_logic_counts": dict(photo_logic_counts),
        "image_role_counts": {"|".join(k): v for k, v in image_role_counts.items()},
        "cases": case_results,
    }
    (out / "baseline_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
