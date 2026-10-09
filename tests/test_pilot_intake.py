"""Synthetic intake boundaries; no real master rows or contacts live here."""
import copy
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from lp_engine.pilot_intake import (
    INPUT_SCHEMA, IntakeError, adapt_no_web_row, adapt_normalized_lead,
    build_p01_handoff, load_no_web_csv, main, write_intake_batch,
)


def source():
    return {"source_id": "SYNTHETIC-DATASET", "source_locator": "synthetic://master",
            "version_number": 0, "input_kind": "SYNTHETIC_TEST_ONLY"}


def raw_row(industry="painting", **overrides):
    row = {"formal_id": "SYNTHETIC-001", "business_name": "架空のテスト工房",
        "address": "架空県テスト市", "prefecture": "架空県", "web_status": "NO_WEB",
        "web_lookup_status": "CHECKED", "identity_status": "VERIFIED",
        "sales_email_ready": "YES", "phone": "", "canonical_entity_id": "",
        "email_verified": "YES", "email_source_verified": "YES"}
    if industry == "painting":
        row.update(public_email="intake@example.invalid", public_email_source_url="https://directory.example.invalid/1",
            active_status="ACTIVE", verified_at="2026-09-29")
    else:
        row.update(email="garden@example.invalid", email_source_url="https://directory.example.invalid/2",
            operating_status="ACTIVE", email_verified_at="2026-09-27", web_verified_at="2026-09-28")
    row.update(overrides)
    return row


def explicit_bar():
    return {"schema_version": INPUT_SCHEMA, "source_record_id": "SYNTHETIC-BAR-1", "industry": "bar",
        "identity": {"business_name": "架空のテストバー"},
        "business": {"description": "テスト専用の入力記録"}, "provenance": source()}


class PilotIntakeTest(unittest.TestCase):
    def test_original_email_source_and_historical_flags_are_preserved_without_promotion(self):
        row = raw_row(unknown_column="unmapped source value")
        original = copy.deepcopy(row)
        result = adapt_no_web_row(row, industry="painting", source=source(), row_number=1)
        self.assertEqual(row, original)
        self.assertEqual(result["contact"]["identifier"], "intake@example.invalid")
        self.assertEqual(result["contact"]["source_type"], "LEGACY_PUBLIC_EMAIL_REFERENCE")
        self.assertIsNone(result["contact"]["instagram"])
        self.assertIsNone(result["identity"]["lead_entity_id"])
        self.assertIsNone(result["business"]["service_scope"])
        self.assertEqual(result["provenance"]["raw_row"], original)
        self.assertEqual(result["legacy_assertions"]["identity_status"], "VERIFIED")
        self.assertIsNone(result["current_verification"]["identity"])
        self.assertFalse(result["state"]["production_eligible"])
        self.assertTrue(all(x["verification_status"] == "SOURCE_RECORDED_ONLY" for x in result["source_observations"]))

    def test_landscape_contact_and_web_timestamps_remain_distinct(self):
        result = adapt_no_web_row(raw_row("landscape"), industry="landscape", source=source(), row_number=7)
        self.assertEqual(result["contact"]["legacy_verified_at"], "2026-09-27")
        self.assertEqual(result["legacy_assertions"]["web_verified_at"], "2026-09-28")
        self.assertEqual(result["industry"]["key"], "landscape")
        self.assertNotIn("beauty", json.dumps(result))

    def test_empty_email_stays_absent_and_phone_is_not_used_as_email(self):
        result = adapt_no_web_row(raw_row(public_email="", phone="0123456789"), industry="painting", source=source(), row_number=1)
        self.assertIsNone(result["contact"]["identifier"])
        self.assertIsNone(result["contact"]["route"])
        self.assertEqual(result["contact"]["phone"], "0123456789")

    def test_bar_explicit_input_and_hypothesis_handoff_do_not_claim_renderer_support(self):
        intake = adapt_normalized_lead(explicit_bar())
        hypothesis = {"hypothesis_id": "P01-H1", "field": "audience.primary_job",
            "value": "静かに会話できる場を探している", "rationale": "バーという入力分類を起点に検討する仮説"}
        handoff = build_p01_handoff(intake, hypotheses=[hypothesis])
        self.assertEqual(handoff["industry"]["key"], "bar")
        self.assertEqual(handoff["verified_facts"], [])
        self.assertEqual(handoff["hypotheses"][0]["value"], hypothesis["value"])
        self.assertEqual(handoff["hypotheses"][0]["verification_status"], "HYPOTHESIS")
        self.assertTrue(handoff["p01"]["hypothesis_authoring_allowed"])
        self.assertFalse(handoff["p01"]["missing_source_values_force_unknown_hypotheses"])
        self.assertIsNone(handoff["production"]["generation_input"])
        self.assertEqual(handoff["production"]["render_support"], "NOT_ASSERTED")

    def test_unconfirmed_bar_csv_and_old_beauty_scope_are_rejected(self):
        with self.assertRaises(IntakeError):
            adapt_no_web_row(raw_row(), industry="bar", source=source(), row_number=1)
        for wrong in ["beauty_cosmetics", "美容", "hair_salon_barber", [], None]:
            row = explicit_bar(); row["industry"] = {"key": wrong}
            with self.subTest(wrong=wrong), self.assertRaises(IntakeError):
                adapt_normalized_lead(row)

    def test_old_normalized_export_keeps_partial_original_provenance(self):
        old = {"schema_version": "no-web-intake/1.0", "industry": {"key": "landscape", "label": "造園・庭管理", "basis": "SOURCE_DATASET_CLASSIFICATION"},
            "identity": {"business_name": "架空の旧入力", "source_formal_id": "OLD-1"},
            "contact": {}, "legacy_assertions": {"sales_email_ready": True},
            "provenance": {"library_file_id": "SYNTHETIC-LIB", "file_id": "SYNTHETIC-FILE", "source_path": "synthetic://partial",
                "input_kind": "PARTIAL_TEXT_EXTRACT", "original_bytes_verified": False}}
        result = adapt_normalized_lead(old)
        self.assertFalse(result["provenance"]["original_bytes_verified"])
        self.assertEqual(result["provenance"]["input_kind"], "PARTIAL_TEXT_EXTRACT")
        self.assertIsNone(result["current_verification"]["contact"])
        self.assertEqual(build_p01_handoff(result)["p01"]["completion"], "NOT_ASSERTED")

    def test_intake_identity_is_stable_across_row_reordering_but_source_qualified(self):
        first = adapt_no_web_row(raw_row(), industry="painting", source=source(), row_number=1)
        reordered = adapt_no_web_row(raw_row(), industry="painting", source=source(), row_number=9)
        other_source = {**source(), "source_id": "SYNTHETIC-OTHER-DATASET"}
        other = adapt_no_web_row(raw_row(), industry="painting", source=other_source, row_number=1)
        self.assertEqual(first["intake_id"], reordered["intake_id"])
        self.assertNotEqual(first["intake_id"], other["intake_id"])
        with tempfile.TemporaryDirectory() as td, self.assertRaises(IntakeError):
            write_intake_batch([first, reordered], td)

    def test_contact_identifier_cannot_fall_back_to_another_channel(self):
        record = explicit_bar()
        record["contact"] = {"route": "email", "email": "intake@example.invalid", "phone": "0123456789", "identifier": "0123456789"}
        with self.assertRaises(IntakeError):
            adapt_normalized_lead(record)

    def test_source_and_projection_mutations_fail_before_handoff(self):
        intake = adapt_normalized_lead(explicit_bar())
        for field in ["source", "projection", "observation_value", "observation_verification", "contact", "current_verification"]:
            changed = copy.deepcopy(intake)
            if field == "source":
                changed["source_snapshot"]["identity"]["business_name"] = "別の架空名"
            elif field == "projection":
                changed["industry"]["key"] = "painting"
            elif field == "observation_value":
                changed["source_observations"][0]["value"] = "別の架空名"
            elif field == "observation_verification":
                changed["source_observations"][0]["verification_status"] = "VERIFIED"
            elif field == "contact":
                changed["contact"]["email"] = "changed@example.invalid"
            else:
                changed["current_verification"]["identity"] = True
            with self.subTest(field=field), self.assertRaises(IntakeError):
                build_p01_handoff(changed)

    def test_hypothesis_cannot_be_passed_as_a_verified_or_eligible_fact(self):
        intake = adapt_normalized_lead(explicit_bar())
        base = {"hypothesis_id": "H1", "field": "audience", "value": "テスト仮説", "rationale": "合成テスト"}
        for change in [{"verified": True}, {"verification_status": "VERIFIED"}, {"production_evidence_eligible": True}, {"confidence": "confirmed"}]:
            with self.subTest(change=change), self.assertRaises(IntakeError):
                build_p01_handoff(intake, hypotheses=[{**base, **change}])

    def test_source_row_hash_mismatch_and_malformed_types_are_rejected(self):
        record = explicit_bar()
        record["provenance"].update(raw_row={"test": "source"}, raw_row_sha256="wrong")
        with self.assertRaises(IntakeError):
            adapt_normalized_lead(record)
        record = explicit_bar(); record["identity"]["business_name"] = 123
        with self.assertRaises(IntakeError):
            adapt_normalized_lead(record)

    def test_raw_csv_bytes_hash_and_rows_are_verified_before_receipt(self):
        row = raw_row()
        stream = io.StringIO(newline=""); writer = csv.DictWriter(stream, fieldnames=list(row)); writer.writeheader(); writer.writerow(row)
        raw = stream.getvalue().encode("utf-8")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.csv"; path.write_bytes(raw)
            metadata = {**source(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "row_count": 1}
            result = load_no_web_csv(path, industry="painting", source=metadata)
            self.assertTrue(result[0]["provenance"]["original_bytes_verified"])
            for key, bad in [("bytes", len(raw) + 1), ("sha256", "wrong"), ("row_count", 2)]:
                with self.subTest(key=key), self.assertRaises(IntakeError):
                    load_no_web_csv(path, industry="painting", source={**metadata, key: bad})

    def test_truncated_or_duplicate_csv_is_not_padded_or_silently_merged(self):
        row = raw_row(); stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=list(row)); writer.writeheader(); writer.writerow(row)
        valid = stream.getvalue()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthetic.csv"
            path.write_text(valid + "INCOMPLETE,only-two-columns\n", encoding="utf-8")
            with self.assertRaises(IntakeError):
                load_no_web_csv(path, industry="painting", source=source())
            writer.writerow(row); path.write_text(stream.getvalue(), encoding="utf-8")
            with self.assertRaises(IntakeError):
                load_no_web_csv(path, industry="painting", source=source())

    def test_cli_writes_three_deterministic_handoff_files_without_generation(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); input_path = td / "synthetic.jsonl"
            input_path.write_text(json.dumps(explicit_bar(), ensure_ascii=False) + "\n", encoding="utf-8")
            out = td / "out"
            self.assertEqual(main(["--normalized-jsonl", str(input_path), "--out", str(out)]), 0)
            first = {p.name: p.read_bytes() for p in out.iterdir()}
            self.assertEqual(set(first), {"intake_records.jsonl", "p01_handoffs.jsonl", "intake_report.json"})
            self.assertEqual(main(["--normalized-jsonl", str(input_path), "--out", str(out)]), 0)
            self.assertEqual(first, {p.name: p.read_bytes() for p in out.iterdir()})
            report = json.loads(first["intake_report.json"])
            self.assertEqual(report["industry_counts"], {"bar": 1})
            self.assertEqual(report["generation_attempts"], 0)
            self.assertEqual(report["verified_fact_count"], 0)


if __name__ == "__main__":
    unittest.main()
