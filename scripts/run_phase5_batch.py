"""Run the Phase 5 10 -> 30 -> 100 batch rehearsal.

All generated fixtures in this rehearsal are explicitly TEST_ONLY.  They are
useful for exercising isolation, persistence, QA and scaling contracts without
inventing real customer facts or treating synthetic data as a deliverable.
The existing real fixtures remain regression controls in CI.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any

from lp_engine.batch import (
    BATCH_ENGINE_CONTRACT_VERSION,
    BatchItem,
    BatchOrchestrator,
    BatchProcessingError,
    BatchRegistry,
)
from lp_engine.operations import OperationsStore
from lp_engine.production_generation import ENGINE_VERSION, run_generation
from lp_engine.quality_diagnosis import build_structured_review, diagnose_quality
from run_production_qa import static_report


ROOT = Path(__file__).resolve().parents[1]
WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]
GOALS = ("inquiry", "reservation", "quote_request", "purchase", "application", "consultation", "visit")
INDUSTRIES = ("工房", "予約サービス", "地域小売", "教室", "専門相談", "設計サービス", "飲食")
PROFILES = ("MATERIAL", "PLACE", "PRODUCT", "DOCUMENT", "PERSON", "TYPOGRAPHY")


def _evidence(item_id: str, company_id: str, *, density: str, target: str, kind: str, claim: str) -> dict[str, Any]:
    return {
        "evidence_id": f"{company_id}-e-{kind.lower()}",
        "company_id": company_id,
        "case_id": f"{company_id}-test-only",
        "evidence_type": kind,
        "evidence_strength": "E5_DECISION_ENABLING" if kind == "CTA_CHANNEL" else "E3_OPERATIONAL",
        "target_objections": [target],
        "claim": claim,
        "source": f"synthetic://phase5/{item_id}/{kind.lower()}",
        "source_type": "synthetic_test_fixture",
        "verification_status": "VERIFIED",
        "verification_date": "2026-09-16",
        "usage_status": "PRODUCTION_ELIGIBLE",
        "placement_candidates": ["EARLY_PROOF", "BEFORE_CTA", "CTA_ZONE"],
        "rights_status": "NOT_APPLICABLE",
        "hearing_required": False,
        "blocking_status": "NON_BLOCKING",
        "notes": "TEST_ONLY synthetic evidence; never a customer-facing proof record.",
    }


def build_input(index: int) -> dict[str, Any]:
    item_id = f"item-{index:03d}"
    company_id = f"p5-test-company-{index:03d}"
    industry = INDUSTRIES[(index - 1) % len(INDUSTRIES)]
    goal = GOALS[(index - 1) % len(GOALS)]
    location = f"福岡市テスト区{index}"
    company_name = f"TEST_ONLY｜Phase 5 {industry} {index:03d}"
    density = ("LOW", "MEDIUM", "HIGH")[(index - 1) % 3]
    truth = f"{location}で{industry}の入口をひらく、{company_name}。"
    if goal in {"inquiry", "quote_request"}:
        visual_authority = "MATERIAL"
    elif goal == "reservation":
        visual_authority = "PLACE"
    elif goal in {"purchase", "visit"}:
        visual_authority = "PRODUCT"
    elif goal == "consultation":
        visual_authority = "PERSON"
    else:
        visual_authority = "DOCUMENT"
    evidence = [_evidence(item_id, company_id, density=density, target="O3_PROCESS", kind="SERVICE_SCOPE", claim=f"{company_name}は{location}で{industry}の相談入口を案内する。")]
    if density in {"MEDIUM", "HIGH"}:
        evidence.append(_evidence(item_id, company_id, density=density, target="O4_NEXT", kind="CTA_CHANNEL", claim="相談内容をフォームから送る入口を用意している。"))
    if density == "HIGH":
        evidence.extend([
            _evidence(item_id, company_id, density=density, target="O3_PROCESS", kind="SERVICE_PROCESS", claim="相談内容を確認して、次に必要な情報を整理する。"),
            _evidence(item_id, company_id, density=density, target="O4_NEXT", kind="POST_CLICK_FLOW", claim="フォーム送信後は相談内容の確認から始める。"),
        ])
    return {
        "schema_version": "production_generation_input_v1",
        "company_id": company_id,
        "company": {
            "company_name": company_name,
            "industry": industry,
            "service_category": f"{industry}の相談窓口",
            "location": location,
            "business_model": "test_only_local_service",
            "company_truth": truth,
            "differentiators": [f"{location}を起点にする", f"{industry}の入口を一つにまとめる"],
            "visual_authority_candidates": [visual_authority, "TYPOGRAPHY"],
            "contact_channels": {"href": "#test-only-contact"},
        },
        "customer_state": {
            "before": f"{industry}について、どこから相談すればよいか分からない",
            "after": "状況を整理して最初の一歩を選べる",
            "barrier": "何を伝えれば話が進むか分からない",
        },
        "conversion_goal": goal,
        "primary_objections": ["O3_PROCESS", "O4_NEXT"],
        "requested_claims": [],
        "unavailable_evidence": ["料金・資格・実績・画像利用許諾は未確認"],
        "evidence_ledger": evidence,
        "test_only": True,
        "simulation_mode": True,
    }


def make_items(batch_id: str, count: int) -> list[BatchItem]:
    result = []
    for index in range(1, count + 1):
        raw = build_input(index)
        company = raw["company"]
        result.append(BatchItem(
            batch_id=batch_id,
            item_id=f"item-{index:03d}",
            company_id=raw["company_id"],
            company_name=company["company_name"],
            source_urls=[f"synthetic://phase5/{index:03d}"],
            industry=company["industry"],
            location=company["location"],
            conversion_goal=raw["conversion_goal"],
            evidence_density=("LOW", "MEDIUM", "HIGH")[(index - 1) % 3],
            input_version="phase5-test-input-v1",
            input_payload=raw,
            test_only=True,
        ))
    return result


def stage_gate(report: dict[str, Any], *, stage: str, expected: int, browser_required: bool) -> dict[str, Any]:
    items = report["items"][:expected]
    processed = sum(item["status"] in {"COMPLETED", "HOLD", "BLOCKED"} for item in items)
    browser_ok = sum(item.get("browser_qa_status") == "PASS" for item in items)
    safety_bypass = [item["item_id"] for item in items if item.get("safety_status") not in {"PASS", "HEARING_REQUIRED"}]
    manual_edits = [item["item_id"] for item in items if item.get("metrics", {}).get("manual_intervention")]
    checks = {
        "processed": processed == expected,
        "catastrophic_failure_zero": not any(item["status"] == "FAILED" for item in items),
        "isolation": report["isolation"]["status"] == "PASS",
        "safety_bypass_zero": not safety_bypass,
        "manual_edit_zero": not manual_edits,
        "browser_qa": browser_ok == expected if browser_required else False,
        "traceable": all(item.get("generation_id") and item.get("project_id") and item.get("output_dir") for item in items),
    }
    return {
        "stage": stage,
        "expected": expected,
        "processed": processed,
        "browser_qa_pass": browser_ok,
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "HOLD",
        "quality_distribution": report["quality"],
        "failure_taxonomy": report["failure_taxonomy"],
    }


def run_item_factory(browser_items: set[str], operations: dict[str, dict[str, Any]]):
    def process(item: BatchItem, output_dir: Path, attempt: int) -> dict[str, Any]:
        raw = deepcopy(item.input_payload)
        generation_id = f"{item.batch_id}-{item.item_id}-generation-{attempt}"
        result = run_generation(raw, output_dir, generation_id=generation_id, mode="test")
        qa = static_report(output_dir, allow_non_production=True)
        browser_mode = "static_only"
        browser_status = None
        if item.item_id in browser_items:
            from lp_engine.browser_qa import run_browser_qa_sync
            browser = run_browser_qa_sync(str(output_dir / "index.html"), str(output_dir / "browser_qa"), WIDTHS, 1000, screenshot_widths=[390, 1440])
            qa["mode"] = "static_and_browser"
            qa["browser"] = browser.to_dict()
            qa["status"] = "PASS" if qa["status"] == "PASS" and browser.status == "PASS" else "FAIL"
            qa["exact_capture"] = {"desktop": "1440x1000", "mobile": "390x844"}
            browser_mode = "static_and_browser"
            browser_status = browser.status
        if qa["status"] != "PASS":
            (output_dir / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise BatchProcessingError("QA gate failed", "BROWSER_ERROR" if browser_mode == "static_and_browser" else "QA_ERROR", retryable=False)
        review = build_structured_review(output_dir, qa_report=qa)
        diagnosis = diagnose_quality(output_dir, qa_report=qa, review=review)
        (output_dir / "qa_report.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output_dir / "structured_review.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output_dir / "quality_diagnosis.json").write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        store = OperationsStore()
        project_id = f"{item.batch_id}-{item.item_id}-project"
        project = store.create_project(project_id=project_id, client_id=f"test-client-{item.item_id}", company_id=item.company_id, simulation_mode=True, rubric_version="structured_review_roles_v1", reviewer_contract_version="phase5_batch_contract_v1")
        store.register_research_input(project_id, f"{output_dir}/input.json", content=raw)
        store.advance_project(project_id)
        store.complete_sales_sample(project_id, result.generation_id, str(output_dir / "index.html"), qa_status=qa["status"])
        store.set_hearing_plan(project_id, str(output_dir / "hearing_plan.json"), required=bool(result.safety_report.get("hearing_required")), content=result.safety_report.get("hearing_plan", {}))
        store.register_artifact(project_id, "QA", str(output_dir / "qa_report.json"), generation_id=result.generation_id, metadata={"status": qa["status"], "browser_mode": browser_mode})
        (output_dir / "input.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (output_dir / "operations.json").write_text(json.dumps(store.export(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        project = store.get_project(project_id)
        operations[item.item_id] = store.export()
        quality = {
            "sales_sample_gate": review["sales_sample_gate"],
            "creative_scores": review["reviewer_roles"]["creative_art_direction"]["scores"],
            "average_scores": review["average_scores"],
            "layout_profile": result.stage_outputs["creative_strategy"].get("layout_profile"),
            "diagnosis_status": diagnosis["status"],
            "issue_count": diagnosis["issue_count"],
        }
        status = "HOLD" if result.safety_report.get("safety_status") == "HEARING_REQUIRED" else "COMPLETED"
        return {
            "status": status,
            "project_id": project_id,
            "project_status": project.project_status,
            "generation_id": result.generation_id,
            "safety_status": result.safety_report.get("safety_status"),
            "rights_status": "PASS",
            "qa_status": qa["status"],
            "browser_qa_status": browser_status,
            "browser_qa_mode": browser_mode,
            "quality": quality,
            "artifact_ids": [item["artifact_id"] for item in store.export()["artifacts"]],
            "metrics": {
                "layout_profile": quality["layout_profile"],
                "manual_intervention": [],
                "production_output_allowed": False,
                "test_only": True,
                "rubric_version": "structured_review_roles_v1",
                "reviewer_contract_version": "phase5_batch_contract_v1",
            },
        }
    return process


def run_fault_tests(root: Path) -> dict[str, Any]:
    fault_root = root / "fault-tests"
    registry = BatchRegistry(fault_root)
    batch_id = "phase5-fault-isolation"
    items = make_items(batch_id, 3)
    attempts: dict[str, int] = {}
    recovered = {"item-001": False}

    def processor(item, output_dir, attempt):
        attempts[item.item_id] = attempt
        if item.item_id == "item-001" and not recovered[item.item_id]:
            raise BatchProcessingError("simulated deterministic generation error", "GENERATION_ERROR", retryable=False)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "generation_manifest.json").write_text(json.dumps({"company_id": item.company_id, "evidence_used": []}), encoding="utf-8")
        return {"status": "COMPLETED", "project_id": f"fault-{item.item_id}", "generation_id": f"fault-generation-{item.item_id}"}

    orchestrator = BatchOrchestrator(registry, processor, max_retries=0)
    orchestrator.create_batch(batch_id, items)
    first = orchestrator.run_batch(batch_id)
    unaffected = {item["item_id"]: item["status"] for item in first["items"] if item["item_id"] != "item-001"}
    recovered["item-001"] = True
    second = orchestrator.retry_items(batch_id, ["item-001"])
    return {
        "partial_failure_isolation": unaffected == {"item-002": "COMPLETED", "item-003": "COMPLETED"},
        "targeted_retry": second["manifest"]["status"] == "COMPLETED" and attempts["item-001"] == 2,
        "completed_item_protection": attempts["item-002"] == 1 and attempts["item-003"] == 1,
        "first_statuses": {item["item_id"]: item["status"] for item in first["items"]},
        "final_status": second["manifest"]["status"],
    }


def run_contamination_test(root: Path) -> dict[str, Any]:
    test_root = root / "contamination-test"
    registry = BatchRegistry(test_root)
    batch_id = "phase5-contamination-detection"
    items = make_items(batch_id, 2)

    def processor(item, output_dir, attempt):
        output_dir.mkdir(parents=True, exist_ok=True)
        company_id = items[0].company_id if item.item_id == "item-002" else item.company_id
        (output_dir / "generation_manifest.json").write_text(json.dumps({"company_id": company_id, "evidence_used": []}), encoding="utf-8")
        return {"status": "COMPLETED", "project_id": f"contam-{item.item_id}", "generation_id": f"contam-generation-{item.item_id}"}

    orchestrator = BatchOrchestrator(registry, processor, max_retries=0)
    orchestrator.create_batch(batch_id, items)
    report = orchestrator.run_batch(batch_id)
    return {"detected": report["isolation"]["status"] == "FAIL", "errors": report["isolation"]["errors"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--browser-policy", choices=("all", "representative"), default="all")
    parser.add_argument("--static-only", action="store_true", help="Local dependency-light rehearsal; does not satisfy Stage A Browser QA gate.")
    parser.add_argument("--keep-work", action="store_true")
    args = parser.parse_args()
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    work = output / "work"
    if work.exists() and not args.keep_work:
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    batch_id = "phase5-batch-rehearsal-20260916"
    items = make_items(batch_id, 100)
    operations: dict[str, dict[str, Any]] = {}
    browser_items: set[str] = set()
    processor = run_item_factory(browser_items, operations)
    registry = BatchRegistry(work)
    orchestrator = BatchOrchestrator(registry, processor, engine_version=ENGINE_VERSION, max_retries=2, max_workers=1)
    orchestrator.create_batch(batch_id, items, metadata={"phase": "5", "test_only": True, "contract_version": BATCH_ENGINE_CONTRACT_VERSION, "browser_policy": args.browser_policy})
    stages: list[dict[str, Any]] = []
    started = time.monotonic()
    for stage_name, count in (("A", 10), ("B", 30), ("C", 100)):
        selected = {f"item-{index:03d}" for index in range(1, count + 1)}
        if not args.static_only and args.browser_policy == "all":
            browser_items.update(selected)
        elif not args.static_only:
            browser_items.update({f"item-{index:03d}" for index in range(1, min(count, 10) + 1)})
        report = orchestrator.run_batch(batch_id, item_ids=[f"item-{index:03d}" for index in range(1, count + 1)], resume=True)
        gate = stage_gate(report, stage=f"Stage {stage_name}", expected=count, browser_required=(stage_name == "A" and not args.static_only))
        stages.append(gate)
        (output / f"stage_{stage_name.lower()}_report.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if gate["status"] != "PASS" and not args.static_only:
            raise SystemExit(f"Phase 5 Stage {stage_name} gate failed: {json.dumps(gate, ensure_ascii=False)}")
    final_report = orchestrator.report(batch_id)
    final_report["stages"] = stages
    final_report["test_only"] = True
    final_report["contract_version"] = BATCH_ENGINE_CONTRACT_VERSION
    final_report["rubric_version"] = "structured_review_roles_v1"
    final_report["browser_policy"] = args.browser_policy
    final_report["batch_duration_seconds"] = round(time.monotonic() - started, 3)
    final_report["throughput_items_per_hour"] = round(100 / (final_report["batch_duration_seconds"] / 3600), 2) if final_report["batch_duration_seconds"] else None
    final_report["recovery_tests"] = {
        "fault_isolation": run_fault_tests(work),
        "contamination_detection": run_contamination_test(work),
        "duplicate_submission": orchestrator.create_batch(batch_id, items).batch_id == batch_id,
        "resume": all(item["status"] in {"COMPLETED", "HOLD", "BLOCKED"} for item in final_report["items"]),
    }
    final_report["operations"] = {"project_count": len(operations), "project_states": sorted({project["project_status"] for snapshot in operations.values() for project in snapshot["projects"]})}
    (output / "batch_report.json").write_text(json.dumps(final_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"batch_id": batch_id, "status": final_report["status"], "count": len(final_report["items"]), "browser_qa": final_report["browser_qa"], "duration_seconds": final_report["batch_duration_seconds"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
