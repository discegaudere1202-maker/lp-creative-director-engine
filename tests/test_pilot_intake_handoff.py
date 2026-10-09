"""Exercise the pilot input -> P01 files -> receiving boundary together.

All businesses here are synthetic. No real lead list, renderer, provider or
browser is involved in this integration check.
"""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from lp_engine.artifact_handoff import (
    HandoffError,
    build_handoff_manifest,
    receive_artifacts,
)
from lp_engine.pilot_intake import (
    INPUT_SCHEMA,
    adapt_normalized_lead,
    load_no_web_csv,
    write_intake_batch,
)


FILES = ["intake_records.jsonl", "p01_handoffs.jsonl", "intake_report.json"]


def csv_intake(root, industry):
    row = {
        "formal_id": "SYNTHETIC-" + industry,
        "business_name": "合成テスト事業者 " + industry,
        "prefecture": "テスト県",
        "address": "テスト住所",
        "web_status": "NO_WEB",
        "web_lookup_status": "CHECKED",
        "identity_status": "VERIFIED",
        "sales_email_ready": "YES",
        "source_only_note": "保持する原文\n二行目",
    }
    if industry == "painting":
        row.update(public_email="painting@example.test",
                   public_email_source_url="https://example.test/painting",
                   active_status="ACTIVE", verified_at="2026-09-01")
    else:
        row.update(email="landscape@example.test",
                   email_source_url="https://example.test/landscape",
                   operating_status="ACTIVE", web_verified_at="2026-09-01")
    path = root / (industry + ".csv")
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    raw = path.read_bytes()
    return load_no_web_csv(path, industry=industry, source={
        "source_id": "synthetic-input-" + industry,
        "expected_original_sha256": hashlib.sha256(raw).hexdigest(),
        "expected_original_bytes": len(raw),
        "expected_original_rows": 1,
    })[0]


def all_industry_inputs(root):
    records = [csv_intake(root, "landscape"), csv_intake(root, "painting")]
    records.append(adapt_normalized_lead({
        "schema_version": INPUT_SCHEMA,
        "industry": "bar",
        "source_record_id": "SYNTHETIC-BAR",
        "identity": {"business_name": "合成テストバー"},
        "contact": {"route": "email", "email": "bar@example.test",
                    "identifier": "bar@example.test"},
        "provenance": {"source_id": "synthetic-input-bar",
                       "source_locator": "fixture://explicit-normalized-bar"},
    }))
    return records


class PilotIntakeHandoffIntegrationTest(unittest.TestCase):
    def test_all_three_industries_survive_receiving_without_quality_promotion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            records = all_industry_inputs(root)
            output, receiver = root / "producer", root / "receiver"
            hypothesis = {"hypothesis_id": "SYNTHETIC-H01",
                          "field": "customer_need", "value": "庭の手入れ負担を減らしたい",
                          "rationale": "合成テスト用に設定した仮説"}
            report = write_intake_batch(records, output, hypotheses_by_id={
                records[0]["intake_id"]: [hypothesis],
            })
            context = {"task_id": "synthetic-intake-integration", "target_stage": "P01"}
            manifest = build_handoff_manifest(output, FILES, revision="fixture-input-v1", context=context)
            receipt = receive_artifacts(source_dir=output, manifest=manifest,
                receiver_dir=receiver, expected_revision="fixture-input-v1", expected_context=context)
            received = receiver / receipt["storage_subdir"]
            for name in FILES:
                self.assertEqual((received / name).read_bytes(), (output / name).read_bytes())
            copied = [json.loads(line) for line in (received / "p01_handoffs.jsonl").read_text().splitlines()]
            self.assertEqual({item["industry"]["key"] for item in copied}, {"landscape", "painting", "bar"})
            self.assertEqual(report["record_count"], 3)
            self.assertEqual(report["rendered_count"], 0)
            self.assertEqual(report["external_actions"], 0)
            self.assertTrue(all(not item["verified_facts"] for item in copied))
            self.assertTrue(all(item["p01"]["completion"] == "NOT_ASSERTED" for item in copied))
            self.assertTrue(all(not item["production"]["production_eligible"] for item in copied))
            self.assertEqual(copied[0]["hypotheses"][0]["verification_status"], "HYPOTHESIS")
            self.assertEqual(copied[0]["source_provenance"]["raw_row"]["source_only_note"], "保持する原文\n二行目")
            self.assertEqual(receipt["scope"], "ARTIFACT_ONLY")
            self.assertEqual(receipt["quality_status"], "NOT_RUN")
            self.assertFalse(receipt["automatic_downstream_execution"])
            second = receive_artifacts(source_dir=output, manifest=manifest,
                receiver_dir=receiver, expected_revision="fixture-input-v1", expected_context=context)
            self.assertEqual(second, receipt)

    def test_a_changed_handoff_output_is_rejected_after_it_was_pinned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output, receiver = root / "producer", root / "receiver"
            write_intake_batch(all_industry_inputs(root), output)
            manifest = build_handoff_manifest(output, FILES, revision="fixture-input-v1")
            path = output / "p01_handoffs.jsonl"
            data = path.read_bytes()
            path.write_bytes(data.replace(b'"verified_facts":[]', b'"verified_facts":[1]', 1))
            with self.assertRaises(HandoffError) as caught:
                receive_artifacts(source_dir=output, manifest=manifest,
                    receiver_dir=receiver, expected_revision="fixture-input-v1")
            self.assertEqual(caught.exception.code, "CONTENT_MISMATCH")
            self.assertFalse((receiver / "handoff.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
