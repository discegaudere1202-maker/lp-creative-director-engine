"""Source-preserving intake for the landscaping, painting and bar pilot.

This is a receipt and P01 handoff, not SalesCandidate, evidence approval, or a
renderer route. P01 may author hypotheses from incomplete source observations;
those hypotheses never become verified facts in this adapter.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any


INPUT_SCHEMA = "pilot-lead-input/v1"
INTAKE_SCHEMA = "pilot-lead-intake/v1"
HANDOFF_SCHEMA = "p01-intake-handoff/v1"
INDUSTRIES = {"landscape": "造園・庭管理", "painting": "塗装工事業", "bar": "バー"}
COMMON_COLUMNS = {"formal_id", "business_name", "address", "prefecture", "web_status", "web_lookup_status", "identity_status", "sales_email_ready"}
NO_WEB_COLUMNS = {
    "painting": {"public_email", "public_email_source_url", "active_status", "verified_at"},
    "landscape": {"email", "email_source_url", "operating_status", "web_verified_at"},
}
FIELDS = {
    "identity": ("business_name", "legal_company_name", "source_canonical_entity_id", "lead_entity_id", "sales_account_id", "representative", "corporate_number", "permit_no"),
    "location": ("prefecture", "city", "address", "service_area"),
    "contact": ("route", "identifier", "email", "phone", "alternate_email", "official_url", "instagram", "line", "contact_form", "source_url", "source_name", "source_type", "legacy_verified_at"),
    "business": ("service_scope", "service_category", "description", "business_model", "hours", "price_description"),
}


class IntakeError(ValueError):
    """An input cannot be received without guessing or losing its identity."""


def _object(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise IntakeError(f"Expected an object: {field}")
    return value


def _text(value: Any, field: str, *, required: bool = False) -> str | None:
    if value is not None and not isinstance(value, str):
        raise IntakeError(f"Expected a string or null: {field}")
    value = value.strip() if value is not None else None
    if required and not value:
        raise IntakeError(f"Missing required source field: {field}")
    return value or None


def _json(value: Any) -> str:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        encoded.encode("utf-8")
        return encoded
    except (TypeError, ValueError, UnicodeError) as exc:
        raise IntakeError("Input must contain finite JSON values") from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _industry(value: Any) -> dict[str, str]:
    if isinstance(value, str):
        key, label, basis = value, None, "EXPLICIT_INPUT_CLASSIFICATION"
    else:
        value = _object(value, "industry")
        key, label, basis = value.get("key"), value.get("label"), value.get("basis")
    if not isinstance(key, str) or key not in INDUSTRIES:
        raise IntakeError("Unsupported pilot industry; use landscape, painting, or bar")
    return {"key": key, "label": _text(label, "industry.label") or INDUSTRIES[key],
            "basis": _text(basis, "industry.basis") or "EXPLICIT_INPUT_CLASSIFICATION"}


def _provenance(value: Any) -> dict[str, Any]:
    source = dict(_object(value, "provenance"))
    source_id = _text(source.get("source_id") or source.get("library_file_id"), "provenance.source_id", required=True)
    locator = _text(source.get("source_locator") or source.get("source_path") or source.get("local_path"), "provenance.source_locator", required=True)
    source["source_id"], source["source_locator"] = source_id, locator
    raw = source.get("raw_row")
    if raw is not None:
        raw = dict(_object(raw, "provenance.raw_row"))
        digest = _hash(raw)
        if source.get("raw_row_sha256") is not None and source["raw_row_sha256"] != digest:
            raise IntakeError("Source row hash mismatch")
        source["raw_row_sha256"] = digest
    _json(source)
    return deepcopy(source)


def adapt_normalized_lead(record: Mapping[str, Any]) -> dict[str, Any]:
    """Accept an explicit pilot input or the earlier no-web-intake/1.0 export.

    No bar-specific master columns are guessed. A bar uses the explicit input
    contract with its own source identity until its master schema is verified.
    """
    record = _object(record, "record")
    if record.get("schema_version") not in {INPUT_SCHEMA, "no-web-intake/1.0"}:
        raise IntakeError("Unsupported intake input schema")
    industry = _industry(record.get("industry"))
    if record.get("schema_version") == "no-web-intake/1.0" and industry["key"] not in NO_WEB_COLUMNS:
        raise IntakeError("Legacy NO_WEB schema has no observed bar profile")
    groups = {}
    for group, fields in FIELDS.items():
        original = _object(record.get(group, {}), group)
        groups[group] = {field: _text(original.get(field), group + "." + field) for field in fields}
    if not groups["identity"]["business_name"]:
        raise IntakeError("Missing required source field: identity.business_name")
    channel_fields = {"email": "email", "phone": "phone", "Instagram DM": "instagram", "LINE": "line", "contact form": "contact_form"}
    contact = groups["contact"]
    if contact["route"] is not None:
        if contact["route"] not in channel_fields:
            raise IntakeError("Unknown explicit contact route")
        expected = contact[channel_fields[contact["route"]]]
        if expected is None or contact["identifier"] != expected:
            raise IntakeError("Contact route and identifier differ; no fallback is inferred")
    source_record_id = _text(record.get("source_record_id") or record.get("identity", {}).get("source_formal_id"), "source_record_id", required=True)
    source = _provenance(record.get("provenance"))
    intake_id = "pilot-" + _hash([source["source_id"], source_record_id])[:24]
    legacy = deepcopy(dict(_object(record.get("legacy_assertions", {}), "legacy_assertions")))
    # Keep every supplied field, including fields unknown to this adapter. Only
    # explicitly mapped source observations are projected into the P01 input.
    snapshot = deepcopy(dict(record))
    _json(snapshot)
    observations = []
    for group, fields in groups.items():
        for field, value in fields.items():
            if value is not None:
                observations.append({"observation_id": intake_id + ":" + group + "." + field,
                    "field": group + "." + field, "value": value,
                    "verification_status": "SOURCE_RECORDED_ONLY",
                    "source_id": source["source_id"], "source_record_id": source_record_id})
    return {"schema_version": INTAKE_SCHEMA, "intake_id": intake_id,
        "identity_scope": "SOURCE_RECORD_ONLY", "source_record_id": source_record_id,
        "industry": industry, **groups, "legacy_assertions": legacy,
        "source_observations": observations, "provenance": source,
        "source_snapshot": snapshot, "source_snapshot_sha256": _hash(snapshot),
        "current_verification": {"identity": None, "contact": None, "web": None, "business_facts": None},
        "state": {"intake": "RECEIVED", "p01_handoff": "AVAILABLE",
            "sales_readiness": "NOT_EVALUATED", "production_readiness": "NOT_EVALUATED",
            "render_support": "NOT_ASSERTED", "production_eligible": False}}


def adapt_no_web_row(row: Mapping[str, str], *, industry: str, source: Mapping[str, Any], row_number: int) -> dict[str, Any]:
    """Map only the two observed original NO_WEB CSV schemas."""
    row = dict(_object(row, "CSV row"))
    if industry not in NO_WEB_COLUMNS:
        raise IntakeError("No observed NO_WEB CSV schema for this industry; use explicit normalized input")
    missing = (COMMON_COLUMNS | NO_WEB_COLUMNS[industry]) - set(row)
    if missing:
        raise IntakeError("Unconfirmed CSV schema; missing columns: " + ", ".join(sorted(missing)))
    if type(row_number) is not int or row_number < 1:
        raise IntakeError("row_number must be a positive integer")
    for key, value in row.items():
        _text(value, "CSV." + key)
    painting = industry == "painting"
    email_key = "public_email" if painting else "email"
    email = _text(row.get(email_key), email_key)
    url_key = "public_email_source_url" if painting else "email_source_url"
    name_key = "public_email_source_name" if painting else "email_source_name"
    contact_time_key = "verified_at" if painting else "email_verified_at"
    active_key = "active_status" if painting else "operating_status"
    web_time_key = "verified_at" if painting else "web_verified_at"
    original_source = deepcopy(dict(_object(source, "source")))
    original_source.update({"source_row_ordinal": row_number, "raw_row": deepcopy(row),
        "raw_row_sha256": _hash(row), "field_mapping": {"email": email_key,
            "contact_source_url": url_key, "contact_verified_at": contact_time_key,
            "web_verified_at": web_time_key, "active_status": active_key}})
    explicit = {"schema_version": INPUT_SCHEMA, "source_record_id": row.get("formal_id"),
        "industry": {"key": industry, "label": INDUSTRIES[industry], "basis": "SOURCE_DATASET_CLASSIFICATION"},
        "identity": {"business_name": row.get("business_name"),
            "source_canonical_entity_id": row.get("canonical_entity_id"),
            "representative": row.get("representative"), "corporate_number": row.get("corporate_number"),
            "permit_no": row.get("permit_no")},
        "location": {key: row.get(key) for key in ("prefecture", "city", "address")},
        "contact": {"route": "email" if email else None, "identifier": email, "email": email,
            "phone": row.get("phone"), "alternate_email": row.get("alternate_email"),
            "source_url": row.get(url_key), "source_name": row.get(name_key),
            "source_type": "LEGACY_PUBLIC_EMAIL_REFERENCE" if row.get(url_key) else None,
            "legacy_verified_at": row.get(contact_time_key)},
        "legacy_assertions": {"identity_status": row.get("identity_status"),
            "active_status": row.get(active_key), "web_status": row.get("web_status"),
            "web_lookup_status": row.get("web_lookup_status"), "web_verified_at": row.get(web_time_key),
            "sales_email_ready": row.get("sales_email_ready"), "email_verified": row.get("email_verified"),
            "email_source_verified": row.get("email_source_verified"), "formal_status": row.get("formal_status"),
            "formal_eligible": row.get("formal_eligible"), "finalized_at": row.get("finalized_at")},
        "provenance": original_source}
    return adapt_normalized_lead(explicit)


def build_p01_handoff(intake: Mapping[str, Any], *, hypotheses: list[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """Receive source observations and separately supplied P01 hypotheses.

    Missing observations are inputs to P01 reasoning, not a rule requiring all
    downstream fields to stay unknown. This function does not author P01 itself.
    """
    intake = _object(intake, "intake")
    if intake.get("schema_version") != INTAKE_SCHEMA:
        raise IntakeError("Expected normalized pilot intake")
    if _hash(intake.get("source_snapshot")) != intake.get("source_snapshot_sha256"):
        raise IntakeError("Intake source snapshot changed")
    canonical = adapt_normalized_lead(intake["source_snapshot"])
    if _hash(canonical) != _hash(intake):
        raise IntakeError("Intake projection differs from its source snapshot")
    _industry(intake.get("industry"))
    if hypotheses is not None and not isinstance(hypotheses, list):
        raise IntakeError("hypotheses must be an explicit list")
    separate, seen = [], set()
    for item in hypotheses or []:
        item = _object(item, "hypothesis")
        hid = _text(item.get("hypothesis_id"), "hypothesis_id", required=True)
        if hid in seen:
            raise IntakeError("Duplicate hypothesis_id")
        seen.add(hid)
        if (item.get("verified") is True or item.get("production_evidence_eligible") is True
                or item.get("verification_status") not in {None, "HYPOTHESIS", "UNVERIFIED", "NOT_EVALUATED"}
                or str(item.get("status", "")).upper() in {"VERIFIED", "CONFIRMED", "FACT"}
                or str(item.get("confidence", "")).upper() in {"VERIFIED", "CONFIRMED"}):
            raise IntakeError("A P01 hypothesis cannot assert verified fact status")
        if "value" not in item or item["value"] is None:
            raise IntakeError("A supplied hypothesis must contain a value")
        _json(item)
        separate.append({**deepcopy(dict(item)), "hypothesis_id": hid,
            "field": _text(item.get("field"), "hypothesis.field", required=True),
            "rationale": _text(item.get("rationale"), "hypothesis.rationale", required=True),
            "verification_status": "HYPOTHESIS", "verified": False,
            "production_evidence_eligible": False})
    missing = [group + "." + field for group in FIELDS for field, value in intake[group].items() if value is None]
    return {"schema_version": HANDOFF_SCHEMA, "intake_id": intake["intake_id"],
        "industry": deepcopy(intake["industry"]),
        "source_observations": deepcopy(intake["source_observations"]),
        "verified_facts": [], "hypotheses": separate, "missing_source_fields": missing,
        "legacy_assertions": deepcopy(intake["legacy_assertions"]),
        "source_provenance": deepcopy(intake["provenance"]),
        "intake_snapshot": deepcopy(dict(intake)),
        "p01": {"status": "READY_FOR_HYPOTHESIS_AUTHORING", "hypothesis_authoring_allowed": True,
            "missing_source_values_force_unknown_hypotheses": False, "completion": "NOT_ASSERTED"},
        "production": {"generation_input": None, "render_route": None, "render_support": "NOT_ASSERTED",
            "production_eligible": False, "quality_status": "NOT_EVALUATED"}}


def load_no_web_csv(path: str | Path, *, industry: str, source: Mapping[str, Any]) -> list[dict[str, Any]]:
    path = Path(path)
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected_hash = source.get("expected_original_sha256", source.get("sha256"))
    expected_bytes = source.get("expected_original_bytes", source.get("bytes"))
    expected_rows = source.get("expected_original_rows", source.get("row_count"))
    if expected_hash is not None and digest != expected_hash:
        raise IntakeError("Original CSV hash mismatch")
    if expected_bytes is not None and len(raw) != expected_bytes:
        raise IntakeError("Original CSV byte count mismatch")
    try:
        reader = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
        header = next(reader)
        if len(header) != len(set(header)) or any(not col for col in header):
            raise IntakeError("CSV header has duplicate or empty columns")
        rows = []
        for row_number, values in enumerate(reader, 1):
            if not values:
                continue
            if len(values) != len(header):
                raise IntakeError(f"CSV row {row_number}: column count mismatch")
            rows.append((row_number, dict(zip(header, values))))
    except (UnicodeError, csv.Error, StopIteration) as exc:
        raise IntakeError("CSV is empty, malformed, or not UTF-8") from exc
    if expected_rows is not None and len(rows) != expected_rows:
        raise IntakeError("Original CSV row count mismatch")
    meta = deepcopy(dict(source))
    meta.update({"source_locator": str(path.resolve()), "input_kind": "RAW_CSV_BYTES",
        "input_sha256": digest, "input_bytes": len(raw),
        "original_bytes_verified": all(x is not None for x in (expected_hash, expected_bytes, expected_rows))})
    results = [adapt_no_web_row(row, industry=industry, source=meta, row_number=n) for n, row in rows]
    _unique_records(results)
    return results


def _unique_records(records: list[dict[str, Any]]) -> None:
    identities = [record["intake_id"] for record in records]
    if len(identities) != len(set(identities)):
        raise IntakeError("Duplicate source record identity; no row was silently merged")


def write_intake_batch(records: list[dict[str, Any]], out: str | Path, *, hypotheses_by_id: Mapping[str, list[Mapping[str, Any]]] | None = None) -> dict[str, Any]:
    """Write a private handoff batch; output contains source contact information."""
    _unique_records(records)
    hypotheses_by_id = hypotheses_by_id or {}
    if set(hypotheses_by_id) - {r["intake_id"] for r in records}:
        raise IntakeError("Hypotheses refer to an intake outside this batch")
    handoffs = [build_p01_handoff(record, hypotheses=hypotheses_by_id.get(record["intake_id"])) for record in records]
    report = {"schema_version": "pilot-intake-report/v1", "status": "INTAKE_AND_P01_HANDOFF_WRITTEN",
        "record_count": len(records), "industry_counts": dict(Counter(r["industry"]["key"] for r in records)),
        "source_observation_count": sum(len(r["source_observations"]) for r in records),
        "supplied_hypothesis_count": sum(len(h["hypotheses"]) for h in handoffs),
        "current_business_revalidation": False, "verified_fact_count": 0,
        "p01_completion": "NOT_ASSERTED", "generation_attempts": 0, "rendered_count": 0,
        "render_support": "NOT_ASSERTED", "external_actions": 0, "source_rows_auto_merged": 0}
    encoded = {"intake_records.jsonl": "".join(_json(r) + "\n" for r in records),
        "p01_handoffs.jsonl": "".join(_json(h) + "\n" for h in handoffs),
        "intake_report.json": json.dumps(report, ensure_ascii=False, indent=2) + "\n"}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, content in encoded.items():
        target = out / name
        pending = out / (name + ".tmp")
        pending.write_text(content, encoding="utf-8")
        pending.replace(target)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--input-receipt", type=Path, help="Private raw-CSV receipt with a files array")
    inputs.add_argument("--normalized-jsonl", type=Path, help="Explicit pilot-lead-input/v1 or old no-web-intake/1.0 records")
    parser.add_argument("--hypotheses", type=Path, help="Optional private mapping of intake_id to explicit P01 hypotheses")
    parser.add_argument("--out", required=True, type=Path, help="Private output directory outside the public repository")
    args = parser.parse_args(argv)
    try:
        if args.input_receipt:
            receipt = _object(json.loads(args.input_receipt.read_text(encoding="utf-8")), "receipt")
            files = receipt.get("files")
            if not isinstance(files, list) or not files:
                raise IntakeError("Receipt must list its source files")
            records = []
            for source in files:
                source = _object(source, "receipt.file")
                records.extend(load_no_web_csv(source["local_path"], industry=source["profile"], source=source))
        else:
            records = [adapt_normalized_lead(json.loads(line)) for line in args.normalized_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
        hypotheses = json.loads(args.hypotheses.read_text(encoding="utf-8")) if args.hypotheses else None
        if hypotheses is not None:
            _object(hypotheses, "hypotheses_by_id")
        report = write_intake_batch(records, args.out, hypotheses_by_id=hypotheses)
    except (IntakeError, KeyError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, "Intake failed: " + str(exc) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
