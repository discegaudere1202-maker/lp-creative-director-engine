"""Run the final NO_WEB field validation cohort through the Engine only.

This runner deliberately uses the existing Sales Master snapshot as a
read-only, already-researched source. It creates no customer-facing claims
outside the source row, runs the structured production stages in research
mode, and records Browser QA/captures for human review. It is a validation
harness, not a manual page editor.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from lp_engine.browser_qa import run_browser_qa_sync
from lp_engine.production_generation import run_generation


WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
TARGET_SUBGENRES = [
    "鍼灸院",
    "ヨガスタジオ・ヨガ教室",
    "脱毛サロン",
    "ヘッドスパ専門店",
    "ハウスクリーニング",
    "エアコンクリーニング",
    "外壁塗装",
    "屋根修理・雨漏り修理",
    "造園・剪定・庭管理",
    "害虫・害獣駆除",
    "不用品回収・遺品整理",
    "カーコーティング・カー detailing",
    "バイク修理・バイクカスタム",
    "音楽教室",
    "ダンススクール・ダンス教室",
    "料理教室",
    "フォトグラファー・出張撮影・小規模写真スタジオ",
    "結婚相談所",
    "家事代行・生活支援サービス",
    "ドッグトレーニング・犬のしつけ教室",
]


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def select_cohort(master: dict[str, Any]) -> list[dict[str, Any]]:
    rows = master["candidates"]
    selected: list[dict[str, Any]] = []
    for subgenre in TARGET_SUBGENRES:
        matches = [
            row for row in rows
            if row.get("subgenre") == subgenre
            and row.get("web_gate_status") == "PASS_WEAK_WEB"
            and row.get("SALES_PRODUCTION_READY") == "YES"
            and row.get("公式本人性") in {"強", "確認済み"}
            and row.get("web_lookup_status") == "CHECKED"
        ]
        if not matches:
            raise RuntimeError(f"No eligible NO_WEB row for {subgenre}")
        selected.append(matches[0])
    return selected


def _goal(subgenre: str) -> str:
    return {
        "鍼灸院": "consultation",
        "ヨガスタジオ・ヨガ教室": "reservation",
        "脱毛サロン": "reservation",
        "ヘッドスパ専門店": "reservation",
        "ハウスクリーニング": "quote_request",
        "エアコンクリーニング": "quote_request",
        "外壁塗装": "quote_request",
        "屋根修理・雨漏り修理": "quote_request",
        "造園・剪定・庭管理": "quote_request",
        "害虫・害獣駆除": "quote_request",
        "不用品回収・遺品整理": "quote_request",
        "カーコーティング・カー detailing": "reservation",
        "バイク修理・バイクカスタム": "inquiry",
        "音楽教室": "application",
        "ダンススクール・ダンス教室": "application",
        "料理教室": "application",
        "フォトグラファー・出張撮影・小規模写真スタジオ": "inquiry",
        "結婚相談所": "consultation",
        "家事代行・生活支援サービス": "inquiry",
        "ドッグトレーニング・犬のしつけ教室": "consultation",
    }.get(subgenre, "inquiry")


def _customer_state(subgenre: str) -> dict[str, str]:
    return {
        "鍼灸院": {"before": "体の気になることを、どこまで相談してよいか迷っている", "after": "自分の状態を話す入口が分かる", "barrier": "症状や希望をうまく説明できるか不安"},
        "ヨガスタジオ・ヨガ教室": {"before": "運動を始めたいが、自分に合う過ごし方が分からない", "after": "無理なく試せる時間を選べる", "barrier": "雰囲気や続け方が見えない"},
        "脱毛サロン": {"before": "施術内容や相談の仕方を比較している", "after": "気になる部位から相談できる", "barrier": "何を聞けばよいか分からない"},
        "ヘッドスパ専門店": {"before": "疲れを整えたいが、どんな時間になるか想像しにくい", "after": "自分のための時間を相談できる", "barrier": "初めての店へ連絡するきっかけがない"},
        "ハウスクリーニング": {"before": "家の気になる場所を、どこまで頼めるか整理している", "after": "必要な清掃を見積相談できる", "barrier": "作業範囲と費用の聞き方が分からない"},
        "エアコンクリーニング": {"before": "エアコンの汚れや臭いが気になっている", "after": "洗浄について相談できる", "barrier": "機種や状態をどう伝えるか分からない"},
        "外壁塗装": {"before": "家の外壁を直したいが、最初に何を見ればよいか迷っている", "after": "現状を伝えて見積を相談できる", "barrier": "必要な工事と費用の順番が見えない"},
        "屋根修理・雨漏り修理": {"before": "雨漏りや屋根の不安を、急いで確認したい", "after": "状況を伝えて修理を相談できる", "barrier": "どの情報を先に送ればよいか分からない"},
        "造園・剪定・庭管理": {"before": "庭を整えたいが、希望をうまく形にできるか迷っている", "after": "庭の状態から相談できる", "barrier": "剪定や管理の範囲を決めにくい"},
        "害虫・害獣駆除": {"before": "気配や被害があり、どこへ頼むか探している", "after": "状況を伝えて対応を相談できる", "barrier": "被害の説明や相談の緊急度に迷う"},
        "不用品回収・遺品整理": {"before": "片付けたい物があるが、量や進め方を整理できていない", "after": "回収や買取を相談できる", "barrier": "何をどこまで頼めるか分からない"},
        "カーコーティング・カー detailing": {"before": "車の状態に合う仕上げを選びたい", "after": "車と希望を伝えて相談できる", "barrier": "メニューの違いを自分だけで判断しにくい"},
        "バイク修理・バイクカスタム": {"before": "バイクの不調や手を入れたい箇所を整理している", "after": "状態と希望から相談できる", "barrier": "症状をどう伝えればよいか分からない"},
        "音楽教室": {"before": "音楽を始めたいが、年齢や経験に合う教室を探している", "after": "やってみたいことから相談できる", "barrier": "通い方や雰囲気が見えない"},
        "ダンススクール・ダンス教室": {"before": "踊ってみたいが、初心者でも入れるか気になっている", "after": "自分に合うクラスを相談できる", "barrier": "レベルや教室の空気が分からない"},
        "料理教室": {"before": "料理を習いたいが、内容や参加の仕方を比べている", "after": "作りたいものから参加を相談できる", "barrier": "自分の経験で参加できるか不安"},
        "フォトグラファー・出張撮影・小規模写真スタジオ": {"before": "残したい場面はあるが、撮影場所や頼み方を決めきれていない", "after": "撮りたい時間から相談できる", "barrier": "希望を写真の言葉にしにくい"},
        "結婚相談所": {"before": "婚活を始めたいが、自分に合う進め方を整理したい", "after": "今の状況から相談を始められる", "barrier": "最初の相談で何を話すか迷う"},
        "家事代行・生活支援サービス": {"before": "暮らしの困りごとを抱えているが、どこまで頼めるか分からない", "after": "必要な支援を相談できる", "barrier": "自分の事情をどう伝えるか迷う"},
        "ドッグトレーニング・犬のしつけ教室": {"before": "愛犬との困りごとを、どう伝えて頼めばよいか整理している", "after": "犬との暮らしから相談できる", "barrier": "今の状態をうまく説明できるか不安"},
    }.get(subgenre, {"before": "サービスの違いや相談先が分かりにくい", "after": "自分に合う入口へ進める", "barrier": "何を伝えて相談すればよいか分からない"})


def _visual_authorities(subgenre: str) -> list[str]:
    if any(x in subgenre for x in ("塗装", "屋根", "造園", "害虫", "回収", "クリーニング")):
        return ["MATERIAL", "PLACE", "TYPOGRAPHY"]
    if any(x in subgenre for x in ("鍼灸", "脱毛", "ヘッドスパ", "ヨガ", "ピラティス")):
        return ["PERSON", "SENSORY", "PLACE"]
    if any(x in subgenre for x in ("音楽", "ダンス", "料理", "フラワー")):
        return ["PERSON", "WORLD", "PLACE"]
    if any(x in subgenre for x in ("カー", "バイク", "自動車")):
        return ["PRODUCT", "MATERIAL", "PLACE"]
    if any(x in subgenre for x in ("フォト", "写真")):
        return ["PERSON", "PLACE", "WORLD"]
    if any(x in subgenre for x in ("結婚相談", "相談所")):
        return ["PERSON", "TYPOGRAPHY", "PLACE"]
    return ["PLACE", "PERSON", "WORLD"]


def build_input(row: dict[str, Any]) -> dict[str, Any]:
    cid = row["lead_id"]
    source = row["Instagram URL"]
    name = row["事業者名"]
    scope = row["サービス内容"]
    location = row["エリア"]
    channel = row.get("primary_contact_channel") or "Instagram DM"
    ledger = [
        {
            "evidence_id": f"{cid}-identity",
            "company_id": cid,
            "case_id": cid,
            "evidence_type": "OWNER_IDENTITY",
            "evidence_strength": "E3_CONTEXTUAL",
            "target_objections": ["O2_ACCOUNTABILITY"],
            "claim": name + "の公式事業用アカウントであること",
            "source": source,
            "source_type": "official_sns",
            "verification_status": "VERIFIED",
            "verification_date": row["確認日"],
            "usage_status": "ELIGIBLE",
            "placement_candidates": ["hero", "truth"],
            "rights_status": "NOT_APPLICABLE",
            "hearing_required": False,
            "blocking_status": "NON_BLOCKING",
        },
        {
            "evidence_id": f"{cid}-scope",
            "company_id": cid,
            "case_id": cid,
            "evidence_type": "SERVICE_SCOPE",
            "evidence_strength": "E3_CONTEXTUAL",
            "target_objections": ["O1_ABILITY", "O3_PROCESS", "O5_DECISION"],
            "claim": scope,
            "source": source,
            "source_type": "official_sns",
            "verification_status": "VERIFIED",
            "verification_date": row["確認日"],
            "usage_status": "ELIGIBLE",
            "placement_candidates": ["hero", "truth", "service"],
            "rights_status": "NOT_APPLICABLE",
            "hearing_required": False,
            "blocking_status": "NON_BLOCKING",
        },
        {
            "evidence_id": f"{cid}-place",
            "company_id": cid,
            "case_id": cid,
            "evidence_type": "PLACE_WIDE",
            "evidence_strength": "E3_CONTEXTUAL",
            "target_objections": ["O6_COST", "O7_RISK"],
            "claim": location,
            "source": source,
            "source_type": "official_sns",
            "verification_status": "VERIFIED",
            "verification_date": row["確認日"],
            "usage_status": "ELIGIBLE",
            "placement_candidates": ["hero", "contact"],
            "rights_status": "NOT_APPLICABLE",
            "hearing_required": False,
            "blocking_status": "NON_BLOCKING",
        },
        {
            "evidence_id": f"{cid}-contact",
            "company_id": cid,
            "case_id": cid,
            "evidence_type": "CTA_CHANNEL",
            "evidence_strength": "E5_DECISION_ENABLING",
            "target_objections": ["O8_CONTINUITY"],
            "claim": "公開された" + channel + "から相談できること",
            "source": source,
            "source_type": "official_sns",
            "verification_status": "VERIFIED",
            "verification_date": row["確認日"],
            "usage_status": "ELIGIBLE",
            "placement_candidates": ["contact", "cta"],
            "rights_status": "NOT_APPLICABLE",
            "hearing_required": False,
            "blocking_status": "NON_BLOCKING",
        },
    ]
    return {
        "schema_version": "production_input_v1",
        "company_id": cid,
        "company_name": name,
        "industry": row["subgenre"],
        "location": location,
        "conversion_goal": _goal(row["subgenre"]),
        "primary_objections": ["O1_ABILITY", "O2_ACCOUNTABILITY", "O3_PROCESS", "O5_DECISION", "O7_RISK", "O8_CONTINUITY"],
        "company": {
            "company_id": cid,
            "company_name": name,
            "industry": row["subgenre"],
            "location": location,
            "service_category": row["subgenre"],
            "business_model": "地域の小規模事業者",
            "contact_channels": {
                "label": channel,
                "href": source,
            },
        },
        "company_truth": scope,
        "differentiators": [scope, location],
        "customer_state": _customer_state(row["subgenre"]),
        "evidence_density": "MEDIUM",
        "evidence_ledger": ledger,
        "requested_claims": [],
        "unavailable_evidence": ["実店舗・実施工・実商品・本人の実写真", "料金", "実績数", "保証", "資格・受賞歴"],
        "hearing_required": ["OWNER_QUOTE", "HERO_REALITY", "VERIFIED_METRIC", "PHOTO_RIGHTS"],
        "visual_authority_candidates": _visual_authorities(row["subgenre"]),
        "validation_context": "NO_WEB_FIELD_VALIDATION",
        "generation_iteration": 1,
        "input_file": f"master:{cid}",
    }


async def _exact_captures(html_path: Path, out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    captures = {"desktop": (1440, 1000), "mobile": (390, 844)}
    result: dict[str, str] = {}
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            executable_path="/usr/bin/chromium",
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        for name, (width, height) in captures.items():
            page = await browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            await page.emulate_media(reduced_motion="reduce")
            await page.goto(html_path.resolve().as_uri(), wait_until="load")
            await page.screenshot(path=str(out_dir / f"{name}_{width}x{height}.png"), full_page=False)
            result[name] = str(out_dir / f"{name}_{width}x{height}.png")
            await page.close()
        await browser.close()
    return result


def run(mode: str, input_path: Path, out_root: Path, *, skip_browser: bool = False) -> dict[str, Any]:
    master = json.loads(input_path.read_text(encoding="utf-8"))
    cohort = select_cohort(master)
    _write(out_root / "cohort_selection.json", {
        "schema_version": "final_field_validation_cohort_v1",
        "scope": "NO_WEB_ONLY",
        "selection_rule": "PASS_WEAK_WEB + official identity + CHECKED + SALES_PRODUCTION_READY",
        "source_file": str(input_path),
        "source_retrieved_at": master.get("retrieved_at"),
        "count": len(cohort),
        "candidates": cohort,
    })
    results = []
    for row in cohort:
        cid = row["lead_id"]
        out = out_root / cid
        raw = build_input(row)
        _write(out / "field_input.json", raw)
        result = run_generation(raw, out / "generation", generation_id=f"field_{cid}_{mode}", mode="research", iteration=1)
        if skip_browser:
            qa_summary = {
                "status": "NOT_RUN",
                "widths": WIDTHS,
                "line_issues": None,
                "overflow_px": None,
                "console_errors": None,
                "page_errors": None,
            }
            exact = {}
        else:
            qa = run_browser_qa_sync(str(Path(result.output_dir) / "index.html"), out / "browser", widths=WIDTHS, height=1000, screenshot_widths=[390, 1440], executable_path="/usr/bin/chromium")
            qa_summary = {
                "status": qa.status,
                "widths": WIDTHS,
                "line_issues": sum(len(x.line_issues) for x in qa.results),
                "overflow_px": max((x.horizontal_overflow_px for x in qa.results), default=0),
                "console_errors": sum(len(x.console_errors) for x in qa.results),
                "page_errors": sum(len(x.page_errors) for x in qa.results),
            }
            exact = asyncio.run(_exact_captures(Path(result.output_dir) / "index.html", out / "exact_captures"))
        summary = {
            "lead_id": cid,
            "company_name": row["事業者名"],
            "industry": row["subgenre"],
            "location": row["エリア"],
            "web_scope": "NO_WEB",
            "mode": "research",
            "manual_lp_edit": 0,
            "generation_id": result.generation_id,
            "safety_status": result.safety_report.get("safety_status"),
            "output_status": result.manifest.get("output_status"),
            "browser_qa": qa_summary,
            "exact_captures": exact,
            "evidence_ids": [x.get("evidence_id") for x in result.safety_report.get("eligible_evidence", [])],
            "layout_profile": result.stage_outputs.get("creative_strategy", {}).get("layout_profile"),
        }
        _write(out / "field_run_summary.json", summary)
        results.append(summary)
    payload = {
        "schema_version": "final_field_validation_run_v1",
        "status": "COMPLETED",
        "engine_only": True,
        "manual_lp_edit": 0,
        "mode": "research",
        "cohort_size": len(results),
        "results": results,
        "qa": {"widths": WIDTHS, "exact_captures": ["1440x1000", "390x844"]},
    }
    _write(out_root / "run_summary.json", payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", default="data/phase6_sales_master_snapshot_v1.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--skip-browser", action="store_true", help="Generate structured outputs without claiming Browser QA")
    args = parser.parse_args()
    payload = run(args.label, Path(args.master), Path(args.out), skip_browser=args.skip_browser)
    print(json.dumps({"status": payload["status"], "cohort_size": payload["cohort_size"], "out": args.out}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
