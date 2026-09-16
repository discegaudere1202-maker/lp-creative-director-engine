import json
import tempfile
import unittest
from pathlib import Path

from lp_engine.batch import (
    BatchItem,
    BatchOrchestrator,
    BatchProcessingError,
    BatchRegistry,
    BatchValidationError,
    validate_batch_items,
)


def make_item(batch_id: str, index: int, *, company_id: str | None = None) -> BatchItem:
    company_id = company_id or f"p5-company-{index:03d}"
    payload = {
        "company_id": company_id,
        "company": {
            "company_name": f"TEST_ONLY Company {index:03d}",
            "industry": "test",
            "location": f"福岡市テスト区{index}",
        },
    }
    return BatchItem(
        batch_id=batch_id,
        item_id=f"item-{index:03d}",
        company_id=company_id,
        company_name=payload["company"]["company_name"],
        source_urls=[f"synthetic://phase5/{index:03d}"],
        industry="test",
        location=payload["company"]["location"],
        conversion_goal="inquiry",
        evidence_density="MEDIUM",
        input_version="test-input-v1",
        input_payload=payload,
        test_only=True,
    )


class BatchContractTest(unittest.TestCase):
    def test_duplicate_identity_is_rejected(self):
        items = [make_item("batch", 1), make_item("batch", 2, company_id="p5-company-001")]
        with self.assertRaises(BatchValidationError):
            validate_batch_items(items)

    def test_idempotency_resume_and_checkpoint(self):
        calls: list[str] = []

        def processor(item, output_dir, attempt):
            calls.append(item.item_id)
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "generation_manifest.json").write_text(json.dumps({"company_id": item.company_id, "evidence_used": []}), encoding="utf-8")
            return {"status": "COMPLETED", "project_id": f"project-{item.item_id}", "generation_id": f"generation-{item.item_id}", "qa_status": "PASS"}

        with tempfile.TemporaryDirectory() as temp:
            registry = BatchRegistry(temp)
            orchestrator = BatchOrchestrator(registry, processor, engine_version="test-engine")
            orchestrator.create_batch("batch", [make_item("batch", 1), make_item("batch", 2)])
            first = orchestrator.run_batch("batch")
            second = orchestrator.run_batch("batch")
            recovered = registry.recover("batch")
            self.assertEqual(first["manifest"]["success_count"], 2)
            self.assertEqual(second["manifest"]["success_count"], 2)
            self.assertEqual(calls, ["item-001", "item-002"])
            self.assertEqual(len(recovered["items"]), 2)

    def test_retry_is_bounded_and_non_retryable_block_isolated(self):
        attempts: dict[str, int] = {}

        def processor(item, output_dir, attempt):
            attempts[item.item_id] = attempt
            if item.item_id == "item-001" and attempt == 1:
                raise BatchProcessingError("temporary browser error", "BROWSER_ERROR")
            if item.item_id == "item-002":
                raise BatchProcessingError("claim lacks evidence", "SAFETY_BLOCK", terminal_state="BLOCKED")
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "generation_manifest.json").write_text(json.dumps({"company_id": item.company_id, "evidence_used": []}), encoding="utf-8")
            return {"status": "COMPLETED", "project_id": f"project-{item.item_id}", "generation_id": f"generation-{item.item_id}"}

        with tempfile.TemporaryDirectory() as temp:
            registry = BatchRegistry(temp)
            orchestrator = BatchOrchestrator(registry, processor, max_retries=2)
            orchestrator.create_batch("batch", [make_item("batch", 1), make_item("batch", 2), make_item("batch", 3)])
            report = orchestrator.run_batch("batch")
            statuses = {item["item_id"]: item["status"] for item in report["items"]}
            self.assertEqual(statuses, {"item-001": "COMPLETED", "item-002": "BLOCKED", "item-003": "COMPLETED"})
            self.assertEqual(attempts["item-001"], 2)
            self.assertEqual(report["manifest"]["retry_count"], 1)
            self.assertEqual(report["isolation"]["status"], "PASS")

    def test_targeted_retry_does_not_regenerate_completed_items(self):
        calls: list[str] = []
        permanent = {"item-001": True}

        def processor(item, output_dir, attempt):
            calls.append(item.item_id)
            if item.item_id == "item-001" and permanent[item.item_id]:
                raise BatchProcessingError("temporary generation failure", "GENERATION_ERROR")
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "generation_manifest.json").write_text(json.dumps({"company_id": item.company_id, "evidence_used": []}), encoding="utf-8")
            return {"status": "COMPLETED", "project_id": f"project-{item.item_id}", "generation_id": f"generation-{item.item_id}"}

        with tempfile.TemporaryDirectory() as temp:
            registry = BatchRegistry(temp)
            orchestrator = BatchOrchestrator(registry, processor, max_retries=0)
            orchestrator.create_batch("batch", [make_item("batch", 1), make_item("batch", 2)])
            first = orchestrator.run_batch("batch")
            self.assertEqual(first["manifest"]["failed_count"], 1)
            permanent["item-001"] = False
            orchestrator.retry_items("batch", ["item-001"])
            self.assertEqual(calls, ["item-001", "item-002", "item-001"])
            self.assertEqual(registry.load_job("batch").status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
