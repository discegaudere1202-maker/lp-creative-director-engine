import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from lp_engine.operations import (
    APPROVAL_TYPES,
    GateError,
    IllegalTransitionError,
    ImmutableReleaseError,
    OperationsStore,
    classify_revision,
)


def fake_runner(raw, output_dir, *, generation_id, mode):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir, "index.html").write_text("<html></html>", encoding="utf-8")
    return SimpleNamespace(
        manifest={"generation_id": generation_id, "mode": mode},
        safety_report={"safety_status": "PASS"},
        production_output_allowed=mode == "production",
    )


class OperationsFixture:
    def __init__(self):
        self.store = OperationsStore()
        self.store.create_project(
            project_id="project-test",
            client_id="client-test",
            company_id="company-test",
            simulation_mode=True,
            rubric_version="premium-v1",
            reviewer_contract_version="review-v1",
        )
        self.store.register_research_input("project-test", "inputs/research.json", content={"company_id": "company-test"})
        self.store.advance_project("project-test")
        self.store.complete_sales_sample("project-test", "sales-1", "sales/index.html")
        self.store.set_hearing_plan("project-test", "hearing/plan.json", content={"question_count": 1})
        self.store.transition("project-test", "HEARING_REQUIRED", reason="Synthetic evidence gap")
        self.store.start_hearing("project-test")
        self.store.complete_evidence("project-test", evidence_path="evidence/ledger.json", safety_status="PASS", rights_status="PASS")
        self.store.mark_finalization_ready("project-test")
        self.store.start_final_generation("project-test")
        self.store.complete_generation("project-test", "final-1", "v1/index.html", version_label="v1 Final", change_reason="Initial final")
        self.store.move_to_client_review("project-test")

    def approve_current(self):
        project = self.store.get_project("project-test")
        self.store.submit_client_review("project-test", approved=True, simulation_mode=True)
        for approval_type in APPROVAL_TYPES:
            self.store.record_approval(
                "project-test",
                version_id=project.current_version,
                approval_type=approval_type,
                approval_scope="full version",
                approved_by="synthetic-client",
                approval_source="SIMULATED_TEST_FIXTURE",
                production_validity="SIMULATED_TEST_ONLY",
                simulation_mode=True,
            )

    def release_current(self):
        self.store.record_qa("project-test", status="PASS", report_path="v1/qa.json")
        release = self.store.create_release_candidate(
            "project-test",
            files=["index.html", "assets/site.css", "assets/site.js"],
            evidence_snapshot={"digest": "evidence-v1", "status": "PASS"},
            rights_snapshot={"digest": "rights-v1", "status": "PASS"},
            safety_result={"safety_status": "PASS"},
            qa_result={"status": "PASS"},
        )
        self.store.prepare_publish("project-test", dry_run=True)
        self.store.deliver("project-test", package_files=release.files)
        return release


class OperationsLifecycleTest(unittest.TestCase):
    def test_happy_path_closes_with_simulated_publish_and_archive(self):
        fixture = OperationsFixture()
        fixture.approve_current()
        release = fixture.release_current()
        fixture.store.archive("project-test")
        project = fixture.store.get_project("project-test")
        self.assertEqual(project.project_status, "ARCHIVED")
        self.assertEqual(project.delivery_status, "DELIVERED")
        self.assertEqual(release.production_validity, "SIMULATED_TEST_ONLY")
        self.assertFalse(fixture.store.publish_packages[release.release_id]["publication"]["published"])
        self.assertEqual(fixture.store.next_action("project-test").required_action, "NONE")

    def test_illegal_transition_cannot_skip_lifecycle(self):
        fixture = OperationsFixture()
        with self.assertRaises(IllegalTransitionError):
            fixture.store.transition("project-test", "DELIVERED", reason="skip")

    def test_revision_creates_new_version_and_never_edits_old_release(self):
        fixture = OperationsFixture()
        fixture.approve_current()
        first_release = fixture.release_current()
        first_version = first_release.version_id
        revision = fixture.store.request_revision(
            "project-test", target_version=first_version, request_text="見出しの表現を短くしてください。", requested_type="COPY_PREFERENCE", affected_section="hero"
        )
        fixture.store.transition("project-test", "REVISION_REQUIRED", reason="Client requested copy change", context={"revision_id": revision.revision_id})
        fixture.store.start_revision("project-test", revision.revision_id)
        with tempfile.TemporaryDirectory() as temp:
            version = fixture.store.regenerate_revision(
                "project-test", revision.revision_id, input_data={"company_id": "company-test"}, output_dir=temp,
                runner=fake_runner, generation_id="final-2", mode="test"
            )
        fixture.store.complete_qa("project-test", status="PASS", report_path="v2/qa.json")
        fixture.store.submit_client_review("project-test", approved=True, simulation_mode=True)
        project = fixture.store.get_project("project-test")
        for approval_type in APPROVAL_TYPES:
            fixture.store.record_approval(
                "project-test", version_id=project.current_version, approval_type=approval_type,
                approval_scope="full version", approved_by="synthetic-client", approval_source="SIMULATED_TEST_FIXTURE",
                production_validity="SIMULATED_TEST_ONLY", simulation_mode=True,
            )
        second_release = fixture.store.create_release_candidate(
            "project-test", files=["v2/index.html"], evidence_snapshot={"status": "PASS"},
            rights_snapshot={"status": "PASS"}, safety_result={"safety_status": "PASS"}, qa_result={"status": "PASS"},
        )
        self.assertNotEqual(first_version, version.version_id)
        self.assertEqual(fixture.store.get_release(first_release.release_id).version_id, first_version)
        with self.assertRaises(ImmutableReleaseError):
            fixture.store.update_release(first_release.release_id, version="mutate")

    def test_release_immutability_is_explicit(self):
        fixture = OperationsFixture()
        fixture.approve_current()
        release = fixture.release_current()
        payload = fixture.store.get_release(release.release_id).to_dict()
        payload["files"].append("tampered")
        self.assertNotIn("tampered", fixture.store.get_release(release.release_id).files)
        with self.assertRaises(ImmutableReleaseError):
            fixture.store.update_release(release.release_id, files=["tampered"])

    def test_safety_blocked_claim_revision_stops_before_regeneration(self):
        fixture = OperationsFixture()
        revision = fixture.store.request_revision("project-test", target_version="", request_text="地域No.1と書いてください。")
        fixture.store.transition("project-test", "REVISION_REQUIRED", reason="Unsafe claim request", context={"revision_id": revision.revision_id})
        with self.assertRaises(GateError):
            fixture.store.start_revision("project-test", revision.revision_id)
        self.assertEqual(fixture.store.get_project("project-test").exception_status, "SAFETY_BLOCKED")

    def test_rights_blocked_asset_revision_stops_before_regeneration(self):
        fixture = OperationsFixture()
        fixture.store.projects["project-test"].rights_status = "UNKNOWN"
        revision = fixture.store.request_revision("project-test", target_version="", request_text="人物写真を差し替えてください。", requested_type="ASSET_REPLACEMENT")
        fixture.store.transition("project-test", "REVISION_REQUIRED", reason="Asset replacement requested", context={"revision_id": revision.revision_id})
        with self.assertRaises(GateError):
            fixture.store.start_revision("project-test", revision.revision_id)
        self.assertEqual(fixture.store.get_project("project-test").exception_status, "WAITING_FOR_RIGHTS")

    def test_qa_failure_cannot_reach_release(self):
        fixture = OperationsFixture()
        revision = fixture.store.request_revision("project-test", target_version="", request_text="本文を短くしてください。")
        fixture.store.transition("project-test", "REVISION_REQUIRED", reason="Copy revision", context={"revision_id": revision.revision_id})
        fixture.store.start_revision("project-test", revision.revision_id)
        with tempfile.TemporaryDirectory() as temp:
            fixture.store.regenerate_revision("project-test", revision.revision_id, input_data={}, output_dir=temp, runner=fake_runner, generation_id="final-fail", mode="test")
        fixture.store.complete_qa("project-test", status="FAIL", report_path="v-fail/qa.json")
        self.assertEqual(fixture.store.get_project("project-test").project_status, "QA_REVIEW")
        with self.assertRaises((IllegalTransitionError, GateError)):
            fixture.store.transition("project-test", "APPROVAL_REQUIRED", reason="bypass failed QA")

    def test_approval_and_fake_client_guards(self):
        fixture = OperationsFixture()
        project = fixture.store.get_project("project-test")
        with self.assertRaises(GateError):
            fixture.store.record_approval(
                "project-test", version_id=project.current_version or "", approval_type="CONTENT_APPROVAL", approval_scope="full",
                approved_by="fake", approval_source="SIMULATED_CLIENT", production_validity="PRODUCTION_APPROVED", simulation_mode=False,
            )

    def test_rollback_requires_approved_target_and_preserves_audit(self):
        fixture = OperationsFixture()
        fixture.approve_current()
        first_release = fixture.release_current()
        revision = fixture.store.request_revision("project-test", target_version=first_release.version_id, request_text="本文を短くしてください。", requested_type="COPY_PREFERENCE")
        fixture.store.transition("project-test", "REVISION_REQUIRED", reason="Rollback test revision", context={"revision_id": revision.revision_id})
        fixture.store.start_revision("project-test", revision.revision_id)
        with tempfile.TemporaryDirectory() as temp:
            fixture.store.regenerate_revision("project-test", revision.revision_id, input_data={}, output_dir=temp, runner=fake_runner, generation_id="rollback-v2", mode="test")
        fixture.store.complete_qa("project-test", status="PASS", report_path="rollback-v2/qa.json")
        fixture.store.submit_client_review("project-test", approved=True, simulation_mode=True)
        project = fixture.store.get_project("project-test")
        for approval_type in APPROVAL_TYPES:
            fixture.store.record_approval("project-test", version_id=project.current_version or "", approval_type=approval_type, approval_scope="full", approved_by="synthetic-client", approval_source="SIMULATED_TEST_FIXTURE", production_validity="SIMULATED_TEST_ONLY", simulation_mode=True)
        second_release = fixture.store.create_release_candidate("project-test", files=["v2/index.html"], evidence_snapshot={"status": "PASS"}, rights_snapshot={"status": "PASS"}, safety_result={"safety_status": "PASS"}, qa_result={"status": "PASS"})
        fixture.store.prepare_publish("project-test", dry_run=True)
        fixture.store.deliver("project-test", package_files=second_release.files)
        fixture.store.archive("project-test")
        result = fixture.store.rollback("project-test", target_release_id=first_release.release_id, dry_run=True)
        self.assertEqual(result["target_version"], first_release.version)
        self.assertFalse(result["dry_run"] is False)
        self.assertTrue(any(item["rollback_id"] == result["rollback_id"] for item in fixture.store.rollback_history))


class RevisionClassificationTest(unittest.TestCase):
    def test_classification_is_structured_and_claims_require_evidence(self):
        classified = classify_revision("日本一と書いてください。")
        self.assertEqual(classified["request_type"], "FACT_UPDATE")
        self.assertEqual(classified["safety_impact"], "BLOCKED_PENDING_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
