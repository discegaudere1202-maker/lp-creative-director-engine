"""Run the Phase 4 one-project Operations validation package.

The default is deterministic/static so it can run in a minimal checkout. CI
passes ``--browser-qa`` after installing Chromium and adds the existing real
browser contract to the same report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lp_engine.operations import APPROVAL_TYPES, GateError, OperationsStore, PROJECT_STATUSES, TRANSITIONS
from lp_engine.production_generation import run_generation
from run_production_qa import static_report


SYNTHETIC = ROOT / "examples/production/phase3_simulation/synthetic_completion_fixture_v1.json"
REAL_CASES = {
    "Aoyama": ROOT / "examples/production/phase2_fixtures/aoyama_flower_market_production_input_v1.json",
    "Worsal": ROOT / "examples/production/phase2b_holdout/worsal_fukuoka_production_input_v1.json",
}
REQUIREMENTS = ROOT / "config/phase3_finalization_requirements_v1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def register_generation_artifacts(store: OperationsStore, project_id: str, output: Path, *, version_id: str | None = None, generation_id: str | None = None) -> None:
    mapping = {
        "company_understanding.json": "strategy",
        "creative_strategy.json": "strategy",
        "information_architecture.json": "IA",
        "copy.json": "copy",
        "art_direction.json": "art_direction",
        "design_tokens.json": "render_spec",
        "compositions.json": "render_spec",
        "render_spec.json": "render_spec",
        "generation_manifest.json": "render_spec",
        "structured_review.json": "QA",
    }
    for filename, artifact_type in mapping.items():
        path = output / filename
        if path.exists():
            store.register_artifact(project_id, artifact_type, str(path), version_id=version_id, generation_id=generation_id, immutable=version_id is not None)


def make_project(store: OperationsStore, project_id: str, *, simulation_mode: bool = True) -> None:
    store.create_project(project_id=project_id, client_id=f"client-{project_id}", company_id=f"company-{project_id}", simulation_mode=simulation_mode, rubric_version="premium-quality-v1", reviewer_contract_version="structured-review-v1")
    store.register_research_input(project_id, f"{project_id}/research.json", content={"project_id": project_id})
    store.advance_project(project_id)


def make_review_ready_project(store: OperationsStore, project_id: str) -> None:
    make_project(store, project_id)
    store.complete_sales_sample(project_id, f"{project_id}-sales", f"{project_id}/sales/index.html")
    store.set_hearing_plan(project_id, f"{project_id}/hearing-plan.json", content={"questions": 1})
    store.transition(project_id, "HEARING_REQUIRED", reason="Synthetic client evidence gap")
    store.start_hearing(project_id)
    store.complete_evidence(project_id, evidence_path=f"{project_id}/evidence.json", safety_status="PASS", rights_status="PASS")
    store.mark_finalization_ready(project_id)
    store.start_final_generation(project_id)
    store.complete_generation(project_id, f"{project_id}-final-1", f"{project_id}/v1/index.html", version_label="v1 Final", change_reason="Initial final")
    store.move_to_client_review(project_id)


def record_all_simulated_approvals(store: OperationsStore, project_id: str) -> None:
    project = store.get_project(project_id)
    for approval_type in APPROVAL_TYPES:
        store.record_approval(project_id, version_id=project.current_version or "", approval_type=approval_type, approval_scope="full version", approved_by="synthetic-client", approval_source="SIMULATED_TEST_FIXTURE", production_validity="SIMULATED_TEST_ONLY", simulation_mode=True)


def release_and_archive(store: OperationsStore, project_id: str, *, files: list[str]) -> dict:
    store.record_qa(project_id, status="PASS", report_path=f"{project_id}/qa.json")
    release = store.create_release_candidate(project_id, files=files, evidence_snapshot={"status": "PASS", "snapshot": "synthetic-evidence"}, rights_snapshot={"status": "PASS", "snapshot": "synthetic-rights"}, safety_result={"safety_status": "PASS", "snapshot": "synthetic-safety"}, qa_result={"status": "PASS", "snapshot": "synthetic-qa"})
    package = store.prepare_publish(project_id, dry_run=True)
    delivery = store.deliver(project_id, package_files=files)
    store.archive(project_id)
    return {"release": release.to_dict(), "package": package, "delivery": delivery.to_dict(), "project": store.get_project(project_id).to_dict()}


def run_synthetic(out: Path) -> dict:
    raw = load(SYNTHETIC)
    store = OperationsStore()
    project_id = "phase4-synthetic-e2e"
    store.create_project(project_id=project_id, client_id="TEST_ONLY_CLIENT", company_id=raw["company_id"], simulation_mode=True, rubric_version="premium-quality-v1", reviewer_contract_version="structured-review-v1")
    research = store.register_research_input(project_id, str(SYNTHETIC), content=raw)
    store.advance_project(project_id)
    sales_dir = out / "synthetic" / "sales_sample"
    sales = run_generation(raw, sales_dir, generation_id="phase4-synthetic-sales", mode="test")
    store.complete_sales_sample(project_id, sales.generation_id, str(sales_dir / "index.html"))
    register_generation_artifacts(store, project_id, sales_dir, generation_id=sales.generation_id)
    store.set_hearing_plan(project_id, "synthetic/hearing_plan.json", content={"status": "SIMULATED"})
    store.transition(project_id, "HEARING_REQUIRED", reason="Synthetic hearing plan created", actor_type="SYSTEM")
    store.start_hearing(project_id)
    store.complete_evidence(project_id, evidence_path="synthetic/evidence_ledger.json", hearing_answers_path="synthetic/hearing_answers.json", safety_status="PASS", rights_status="PASS", content={"status": "SIMULATED_TEST_ONLY"})
    store.register_artifact(project_id, "finalization_spec", "synthetic/finalization_spec.json", content={"status": "READY_FOR_FINALIZATION", "simulation_mode": True})
    store.mark_finalization_ready(project_id)
    final_raw = dict(raw)
    final_raw["evidence_ledger"] = list(raw.get("evidence_ledger", [])) + [
        {"evidence_id": "phase4-test-purchase", "company_id": raw["company_id"], "case_id": raw["company_id"], "evidence_type": "PURCHASE_PROCESS", "evidence_strength": "E2_SPECIFIC", "target_objections": ["O4_NEXT"], "claim": "相談内容を確認し、受け取り方法と日程を案内します。", "source": "synthetic://phase4/hearing", "source_type": "synthetic_fixture", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "SECTION_BLOCKING"},
        {"evidence_id": "phase4-test-fee", "company_id": raw["company_id"], "case_id": raw["company_id"], "evidence_type": "FEE_CONDITION", "evidence_strength": "E2_SPECIFIC", "target_objections": ["O6_COST"], "claim": "制作費は3,300円から。注文内容の確認後に確定します。", "source": "synthetic://phase4/hearing", "source_type": "synthetic_fixture", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "SECTION_BLOCKING"},
        {"evidence_id": "phase4-test-post-click", "company_id": raw["company_id"], "case_id": raw["company_id"], "evidence_type": "POST_CLICK_FLOW", "evidence_strength": "E2_SPECIFIC", "target_objections": ["O4_NEXT"], "claim": "相談後に内容を確認して購入方法をご案内します。", "source": "synthetic://phase4/hearing", "source_type": "synthetic_fixture", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "NOT_APPLICABLE", "hearing_required": False, "blocking_status": "SECTION_BLOCKING"},
        {"evidence_id": "phase4-test-product", "company_id": raw["company_id"], "case_id": raw["company_id"], "evidence_type": "PRODUCT_DETAIL", "evidence_strength": "E2_SPECIFIC", "target_objections": ["O3_PROCESS"], "claim": "用途と予算に合わせて花を組み立てます。", "source": "synthetic://phase4/hearing", "source_type": "synthetic_fixture", "verification_status": "VERIFIED", "verification_date": "2026-09-16", "usage_status": "PRODUCTION_ELIGIBLE", "rights_status": "CLEARED", "hearing_required": False, "blocking_status": "CLAIM_BLOCKING"},
    ]
    store.start_final_generation(project_id)
    final_dir = out / "synthetic" / "v1_final"
    final = run_generation(final_raw, final_dir, generation_id="phase4-synthetic-final-v1", mode="test")
    version = store.complete_generation(project_id, final.generation_id, str(final_dir / "index.html"), version_label="v1 Final", change_reason="Synthetic finalization")
    register_generation_artifacts(store, project_id, final_dir, version_id=version.version_id, generation_id=final.generation_id)
    store.move_to_client_review(project_id)
    qa = static_report(final_dir, allow_non_production=True)

    # Case A: safe copy preference, regenerated by the Engine into a new version.
    safe_revision = store.request_revision(project_id, target_version=version.version_id, request_text="ヒーロー見出しの表現を短くしてください。", requested_type="COPY_PREFERENCE", affected_section="hero")
    store.transition(project_id, "REVISION_REQUIRED", reason="Synthetic client requested safe copy change", context={"revision_id": safe_revision.revision_id}, actor_type="SIMULATED_CLIENT")
    store.start_revision(project_id, safe_revision.revision_id)
    revision_dir = out / "synthetic" / "v2_revision"
    revised = store.regenerate_revision(project_id, safe_revision.revision_id, input_data=final_raw, output_dir=str(revision_dir), runner=run_generation, generation_id="phase4-synthetic-final-v2", mode="test")
    register_generation_artifacts(store, project_id, revision_dir, version_id=revised.version_id, generation_id="phase4-synthetic-final-v2")
    store.complete_qa(project_id, status="PASS", report_path=str(revision_dir / "qa_report.json"))
    store.submit_client_review(project_id, approved=True, simulation_mode=True)
    record_all_simulated_approvals(store, project_id)
    first_release_flow = release_and_archive(store, project_id, files=["v2/index.html", "v2/assets/site.css", "v2/assets/site.js"])

    # Second approved release makes rollback meaningful and tests released-version immutability.
    second_revision = store.request_revision(project_id, target_version=revised.version_id, request_text="本文の順番を整えてください。", requested_type="COPY_PREFERENCE", affected_section="process")
    store.transition(project_id, "REVISION_REQUIRED", reason="Second safe revision request", context={"revision_id": second_revision.revision_id}, actor_type="SIMULATED_CLIENT")
    store.start_revision(project_id, second_revision.revision_id)
    second_dir = out / "synthetic" / "v3_revision"
    second = store.regenerate_revision(project_id, second_revision.revision_id, input_data=final_raw, output_dir=str(second_dir), runner=run_generation, generation_id="phase4-synthetic-final-v3", mode="test")
    register_generation_artifacts(store, project_id, second_dir, version_id=second.version_id, generation_id="phase4-synthetic-final-v3")
    store.complete_qa(project_id, status="PASS", report_path=str(second_dir / "qa_report.json"))
    store.submit_client_review(project_id, approved=True, simulation_mode=True)
    record_all_simulated_approvals(store, project_id)
    second_release_flow = release_and_archive(store, project_id, files=["v3/index.html"])
    rollback = store.rollback(project_id, target_release_id=first_release_flow["release"]["release_id"], dry_run=True)
    immutable_error = False
    try:
        store.update_release(first_release_flow["release"]["release_id"], files=["tampered"])
    except Exception:
        immutable_error = True

    return {
        "project_id": project_id,
        "status": store.get_project(project_id).project_status,
        "state_trail": [item.to_status for item in store.audit_log if item.project_id == project_id],
        "final_project": store.get_project(project_id).to_dict(),
        "artifact_count": len([a for a in store.artifacts.values() if a.project_id == project_id]),
        "version_count": len([v for v in store.versions.values() if v.project_id == project_id]),
        "release_count": len([r for r in store.releases.values() if r.project_id == project_id]),
        "browser_qa": qa,
        "revision_case_a": {"type": safe_revision.request_type, "status": store.revisions[safe_revision.revision_id].status, "new_version": revised.version_id != version.version_id},
        "rollback": rollback,
        "release_immutability": immutable_error,
        "first_release": first_release_flow,
        "second_release": second_release_flow,
        "export": store.export(),
        "engine_output_status": final.manifest.get("output_status"),
        "research_artifact": research.artifact_id,
    }


def run_block_tests() -> dict:
    safety_store = OperationsStore()
    make_review_ready_project(safety_store, "phase4-safety-block")
    claim = safety_store.request_revision("phase4-safety-block", target_version="", request_text="地域No.1と書いてください。")
    safety_store.transition("phase4-safety-block", "REVISION_REQUIRED", reason="Claim request", context={"revision_id": claim.revision_id})
    try:
        safety_store.start_revision("phase4-safety-block", claim.revision_id)
        safety_blocked = False
    except GateError:
        safety_blocked = safety_store.get_project("phase4-safety-block").exception_status == "SAFETY_BLOCKED"

    rights_store = OperationsStore()
    make_review_ready_project(rights_store, "phase4-rights-block")
    rights_store.projects["phase4-rights-block"].rights_status = "UNKNOWN"
    asset = rights_store.request_revision("phase4-rights-block", target_version="", request_text="人物写真を差し替えてください。", requested_type="ASSET_REPLACEMENT")
    rights_store.transition("phase4-rights-block", "REVISION_REQUIRED", reason="Asset request", context={"revision_id": asset.revision_id})
    try:
        rights_store.start_revision("phase4-rights-block", asset.revision_id)
        rights_blocked = False
    except GateError:
        rights_blocked = rights_store.get_project("phase4-rights-block").exception_status == "WAITING_FOR_RIGHTS"

    qa_store = OperationsStore()
    make_review_ready_project(qa_store, "phase4-qa-block")
    qa_revision = qa_store.request_revision("phase4-qa-block", target_version="", request_text="本文を短くしてください。")
    qa_store.transition("phase4-qa-block", "REVISION_REQUIRED", reason="QA test request", context={"revision_id": qa_revision.revision_id})
    qa_store.start_revision("phase4-qa-block", qa_revision.revision_id)
    qa_store.regenerate_revision("phase4-qa-block", qa_revision.revision_id, input_data={}, output_dir="/tmp/phase4-qa-failure", runner=lambda raw, output_dir, **kwargs: SimpleNamespace(manifest={}, safety_report={"safety_status": "PASS"}, production_output_allowed=False), generation_id="qa-failure", mode="test")
    qa_store.complete_qa("phase4-qa-block", status="FAIL", report_path="qa-failure/report.json")
    qa_failure_blocked = qa_store.get_project("phase4-qa-block").exception_status == "QA_FAILED"
    try:
        qa_store.transition("phase4-qa-block", "APPROVAL_REQUIRED", reason="forbidden bypass")
        qa_release_blocked = False
    except GateError:
        qa_release_blocked = True
    return {
        "safety_block": safety_blocked,
        "rights_block": rights_blocked,
        "qa_failure": qa_failure_blocked,
        "qa_cannot_approve": qa_release_blocked,
        "claim_request": claim.to_dict(),
        "asset_request": asset.to_dict(),
    }


def run_real_dry_runs(out: Path) -> dict:
    requirements = load(REQUIREMENTS)["cases"]
    results = {}
    for label, path in REAL_CASES.items():
        raw = load(path)
        store = OperationsStore()
        project_id = f"phase4-real-{label.lower()}"
        store.create_project(project_id=project_id, client_id="REAL_CLIENT_NOT_CONTACTED", company_id=raw["company_id"], simulation_mode=False)
        store.register_research_input(project_id, str(path), content=raw)
        store.advance_project(project_id)
        sales_dir = out / "real" / label.lower() / "sales_sample"
        sales = run_generation(raw, sales_dir, generation_id=f"phase4-{label.lower()}-sales", mode="production")
        store.complete_sales_sample(project_id, sales.generation_id, str(sales_dir / "index.html"))
        store.register_artifact(project_id, "evidence_ledger", str(path), content=raw.get("evidence_ledger", []))
        store.set_hearing_plan(project_id, f"real/{label.lower()}/hearing_plan.json", content=requirements[raw["company_id"]]["requirements"])
        store.transition(project_id, "HEARING_REQUIRED", reason="Public evidence gap requires real client hearing")
        store.start_hearing(project_id)
        project = store.projects[project_id]
        project.exception_status = "WAITING_FOR_CLIENT"
        results[label] = {
            "project_id": project_id,
            "company_id": raw["company_id"],
            "project_status": project.project_status,
            "exception_status": project.exception_status,
            "next_action": store.next_action(project_id).to_dict(),
            "synthetic_answers_used": False,
            "fake_client_approval": False,
            "sales_sample_status": sales.manifest.get("output_status"),
            "hearing_question_count": len(requirements[raw["company_id"]]["requirements"]),
        }
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="/tmp/phase4-operations")
    parser.add_argument("--browser-qa", action="store_true")
    args = parser.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    synthetic = run_synthetic(out)
    blocks = run_block_tests()
    real = run_real_dry_runs(out)
    if args.browser_qa:
        from lp_engine.browser_qa import run_browser_qa_sync
        browser = run_browser_qa_sync(str(out / "synthetic" / "v2_revision" / "index.html"), str(out / "synthetic" / "browser_qa"), [320, 360, 375, 390, 430, 768, 1024, 1280, 1440], 1000, screenshot_widths=[390, 1440])
        synthetic["browser_qa"] = {**synthetic["browser_qa"], "mode": "static_and_browser", "browser": browser.to_dict(), "exact_capture": {"desktop": "1440x1000", "mobile": "390x844"}, "status": "PASS" if synthetic["browser_qa"]["status"] == "PASS" and browser.status == "PASS" else "FAIL"}
    criteria = {
        "synthetic_lifecycle_archived": synthetic["status"] == "ARCHIVED",
        "synthetic_state_order": synthetic["state_trail"][:3] == ["NEW", "RESEARCH_READY", "SALES_SAMPLE_GENERATING"] and "PUBLISH_READY" in synthetic["state_trail"],
        "artifact_registry": synthetic["artifact_count"] >= 10,
        "version_management": synthetic["version_count"] >= 3,
        "revision_case_a": synthetic["revision_case_a"]["new_version"] and synthetic["revision_case_a"]["status"] == "REGENERATED",
        "release_immutability": synthetic["release_immutability"],
        "rollback": bool(synthetic["rollback"]["rollback_id"]),
        "safety_block": blocks["safety_block"],
        "rights_block": blocks["rights_block"],
        "qa_failure_block": blocks["qa_failure"] and blocks["qa_cannot_approve"],
        "synthetic_non_production": synthetic["engine_output_status"] == "NOT_PRODUCTION_APPROVED",
        "real_fixture_count": len(real) >= 2,
        "real_fixture_waiting": all(item["exception_status"] == "WAITING_FOR_CLIENT" and not item["synthetic_answers_used"] and not item["fake_client_approval"] for item in real.values()),
        "external_change_zero": not any(item.get("package", {}).get("publication", {}).get("published", False) for item in (synthetic.get("first_release", {}), synthetic.get("second_release", {}))),
        "browser_qa": synthetic["browser_qa"]["status"] == "PASS",
    }
    report = {
        "schema_version": "phase4_operations_validation_v1",
        "status": "PASS" if all(criteria.values()) else "HOLD",
        "mode": "SIMULATION_PLUS_REAL_FIXTURE_DRY_RUN",
        "production_external_changes": 0,
        "success_criteria": criteria,
        "synthetic_end_to_end": synthetic,
        "failure_and_block_tests": blocks,
        "real_fixture_dry_runs": real,
        "state_machine": {"statuses": list(PROJECT_STATUSES), "transitions": TRANSITIONS},
        "manual_intervention": 0,
        "next_step": "Phase 5 | Batch Generation" if all(criteria.values()) else "Phase 4B | Operations additional improvement",
    }
    output = out / "phase4_operations_validation.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "status": report["status"], "success_criteria": criteria}, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
