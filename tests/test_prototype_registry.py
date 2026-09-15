import json
import unittest
from pathlib import Path

from lp_engine.prototype_registry import (
    PrototypeRecord,
    audit_prototypes,
    is_reproducible,
    validate_prototype,
)


ROOT = Path(__file__).resolve().parents[1]
WIDTHS = [320, 360, 375, 390, 430, 768, 1024, 1280, 1440]


class PrototypeRegistryTest(unittest.TestCase):
    def test_registry_is_structurally_valid(self):
        payload = json.loads(
            (ROOT / "config/prototype_registry_v1.json").read_text(encoding="utf-8")
        )
        records = [PrototypeRecord(**item) for item in payload["prototypes"]]
        audit = audit_prototypes(records)
        self.assertEqual(audit["status"], "PASS")
        self.assertEqual(audit["total"], len(payload["prototypes"]))
        self.assertEqual(audit["counts"]["COMPETITIVE"], 1)
        self.assertIn("P09", audit["golden_sample_importable"])

    def test_competitive_requires_benchmark_pass(self):
        record = PrototypeRecord(
            prototype_id="PX",
            name="Test",
            principle="A real company truth causes a specific reusable form decision.",
            target_sales_contexts=["NO_WEB"],
            visual_authority=["TYPOGRAPHY"],
            desktop_verified=True,
            mobile_verified=True,
            form_causality_verified=True,
            benchmark_tournament_status="HOLD",
            benchmark_win_rate=0.58,
            stage="COMPETITIVE",
            artifact_path="examples/prototypes/px.html",
            runtime_qa_status="PASS",
            runtime_qa_widths=WIDTHS,
        )
        issues = validate_prototype(record)
        self.assertIn("COMPETITIVE requires tournament PASS", issues)
        self.assertIn("COMPETITIVE requires benchmark_win_rate >= 0.60", issues)

    def test_competitive_requires_reproducible_artifact(self):
        record = PrototypeRecord(
            prototype_id="PX",
            name="Test",
            principle="A real company truth causes a specific reusable form decision.",
            target_sales_contexts=["NO_WEB"],
            visual_authority=["TYPOGRAPHY"],
            desktop_verified=True,
            mobile_verified=True,
            form_causality_verified=True,
            benchmark_tournament_status="PASS",
            benchmark_win_rate=0.67,
            stage="COMPETITIVE",
        )
        issues = validate_prototype(record)
        self.assertIn(
            "COMPETITIVE requires a reproducible artifact with 9-width runtime QA PASS",
            issues,
        )

    def test_reproducible_requires_all_nine_widths(self):
        record = PrototypeRecord(
            prototype_id="PX",
            name="Test",
            principle="A real company truth causes a specific reusable form decision.",
            target_sales_contexts=["NO_WEB"],
            visual_authority=["TYPOGRAPHY"],
            artifact_path="examples/prototypes/px.html",
            runtime_qa_status="PASS",
            runtime_qa_widths=[320, 390, 1440],
        )
        self.assertFalse(is_reproducible(record))
        record.runtime_qa_widths = WIDTHS
        self.assertTrue(is_reproducible(record))

    def test_only_competitive_is_importable(self):
        draft = PrototypeRecord(
            prototype_id="P1", name="Draft", principle="A sufficiently specific prototype principle for testing.",
            target_sales_contexts=["NO_WEB"], visual_authority=["TYPE"], stage="DRAFT"
        )
        competitive = PrototypeRecord(
            prototype_id="P2", name="Winner", principle="A sufficiently specific competitive prototype principle.",
            target_sales_contexts=["NO_WEB"], visual_authority=["TYPE"],
            desktop_verified=True, mobile_verified=True, form_causality_verified=True,
            benchmark_tournament_status="PASS", benchmark_win_rate=0.67, stage="COMPETITIVE",
            artifact_path="examples/prototypes/p2.html", runtime_qa_status="PASS",
            runtime_qa_widths=WIDTHS,
        )
        audit = audit_prototypes([draft, competitive])
        self.assertEqual(audit["golden_sample_importable"], ["P2"])
        self.assertEqual(audit["reproducible_ids"], ["P2"])


if __name__ == "__main__":
    unittest.main()
