"""Fail-closed validation for approved replacement rows and isolated smoke rows."""
from __future__ import annotations
import csv, json
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CELL = ("business_archetype", "industry", "market_scope", "discovery_source_class")
REQUIRED = ("replacement_reference_id", "replaces_reference_id", "slot_id", *CELL,
            "original_official_url", "evidence_source_roles", "replacement_reason")

class ValidationError(ValueError): pass

def load_rows(path: Path):
    rows=[]
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: row=json.loads(line)
        except json.JSONDecodeError as e: raise ValidationError(f"line {n}: invalid JSONL: {e}") from e
        if not isinstance(row,dict): raise ValidationError(f"line {n}: each row must be an object")
        rows.append(row)
    return rows

def original_indexes():
    with (ROOT/"data/creative_mechanism_phase2_pilot_references.csv").open(encoding="utf-8",newline="") as f:
        originals={r["reference_id"]:r for r in csv.DictReader(f)}
    failures={r["reference_id"]:r for r in load_rows(ROOT/"data/creative_mechanism_phase2_2_1_failure_recovery_ledger.jsonl")}
    return originals,failures

def validate(rows, mode="approved_batch"):
    if mode not in {"approved_batch","smoke"}: raise ValidationError("mode must be approved_batch or smoke")
    if mode=="smoke" and len(rows)!=1: raise ValidationError("smoke mode requires exactly one isolated fixture")
    if mode=="approved_batch" and not rows: raise ValidationError("approved batch is empty")
    originals,failures=original_indexes(); seen=set(); seen_slots=set(); results=[]
    for row in rows:
        missing=[k for k in REQUIRED if k not in row or row[k] in (None, "", [])]
        if missing: raise ValidationError(f"missing replacement metadata: {missing}")
        rid=row["replacement_reference_id"]
        if rid in seen: raise ValidationError(f"duplicate replacement_reference_id: {rid}")
        seen.add(rid)
        if rid in originals: raise ValidationError(f"replacement ID is in original 100: {rid}")
        parsed=urlparse(row["original_official_url"])
        if parsed.scheme!="https" or not parsed.netloc: raise ValidationError(f"URL must be absolute HTTPS: {rid}")
        if not isinstance(row["evidence_source_roles"],list) or not row["evidence_source_roles"]:
            raise ValidationError(f"evidence_source_roles must be a non-empty list: {rid}")
        if not set(row["evidence_source_roles"]).intersection({"ORIGINAL_LIVE","OFFICIAL_BRAND","OFFICIAL_PRODUCT_SERVICE","OFFICIAL_CONVERSION_PAGE"}):
            raise ValidationError(f"replacement requires an Original/Official evidence role: {rid}")
        if mode=="smoke":
            if row.get("record_kind")!="SMOKE_ONLY" or row.get("production_eligible") is not False:
                raise ValidationError("smoke fixture must be explicitly SMOKE_ONLY and production_eligible=false")
            if row["replaces_reference_id"] not in failures: raise ValidationError("smoke fixture must bind to a known failed slot")
            expected=failures[row["replaces_reference_id"]]
        else:
            if row.get("record_kind")=="SMOKE_ONLY" or row.get("production_eligible") is False:
                raise ValidationError("smoke-only record is not valid in approved batch")
            failed_id=row["replaces_reference_id"]
            if failed_id not in failures: raise ValidationError(f"replaces_reference_id is not in failed ledger: {failed_id}")
            if failed_id not in originals: raise ValidationError(f"failed slot is not a row in the immutable original pilot: {failed_id}")
            expected=failures[failed_id]
        mismatch={k:(row[k],expected[k]) for k in CELL if str(row[k])!=str(expected[k])}
        if mismatch: raise ValidationError(f"same-cell mismatch for {rid}: {mismatch}; REPLACEMENT_EXCEPTION_REQUIRED")
        if row["slot_id"]!=expected["slot_id"]: raise ValidationError(f"slot mismatch for {rid}")
        if row["replaces_reference_id"] in seen_slots: raise ValidationError(f"failed slot appears more than once: {row['replaces_reference_id']}")
        seen_slots.add(row["replaces_reference_id"])
        if row["replaces_reference_id"] in originals and row["replaces_reference_id"] not in failures:
            raise ValidationError("replacement must preserve a failed original row")
        results.append(row)
    return results

def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--input",required=True,type=Path);p.add_argument("--mode",choices=["approved_batch","smoke"],required=True)
    a=p.parse_args(); rows=validate(load_rows(a.input),a.mode); print(json.dumps({"validated_count":len(rows),"mode":a.mode,"phase2600_allowed":False}))

if __name__=="__main__": main()
