"""Generic policy for safely publishing completion-style sales facts.

The policy is deliberately company-agnostic.  It separates verified facts
from plausible-but-unconfirmed completion facts and from forbidden claims.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping

VERIFIED = "verified"
PROVISIONAL = "provisional"
FORBIDDEN = "forbidden"
LAYERS = frozenset({VERIFIED, PROVISIONAL, FORBIDDEN})
FORBIDDEN_PUBLIC_TOKENS = ("sample", "dummy", "placeholder", "仮", "未確認", "Coming Soon")


@dataclass(frozen=True)
class FactRecord:
    key: str
    value: str
    status: str
    hearing_field: str | None = None
    replacement_required: bool = False

    def __post_init__(self) -> None:
        if self.status not in LAYERS:
            raise ValueError(f"unknown fact status: {self.status}")
        if self.status == PROVISIONAL and (not self.replacement_required or not self.hearing_field):
            raise ValueError("provisional facts require replacement_required and hearing_field")
        if self.status == VERIFIED and self.replacement_required:
            raise ValueError("verified facts cannot require replacement")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def validate_fact_records(records: Iterable[FactRecord]) -> dict[str, object]:
    rows = list(records)
    errors: list[str] = []
    for row in rows:
        if row.status == FORBIDDEN:
            errors.append(f"forbidden:{row.key}")
        if row.status == PROVISIONAL and not (row.replacement_required and row.hearing_field):
            errors.append(f"unreplaceable_provisional:{row.key}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "count": len(rows)}


def public_forbidden_hits(text: str) -> list[str]:
    lowered = text.casefold()
    return [token for token in FORBIDDEN_PUBLIC_TOKENS if token.casefold() in lowered]


def replacement_manifest(records: Iterable[FactRecord]) -> dict[str, object]:
    rows = [row.to_dict() for row in records if row.status == PROVISIONAL]
    return {
        "schema_version": "provisional_replacement_manifest_v1",
        "status": "PASS" if all(row["replacement_required"] and row["hearing_field"] for row in rows) else "FAIL",
        "records": rows,
        "replacement_count": len(rows),
    }


def classify_public_facts(records: Iterable[FactRecord], public_text: str) -> dict[str, object]:
    rows = list(records)
    record_report = validate_fact_records(rows)
    hits = public_forbidden_hits(public_text)
    return {
        "schema_version": "fact_classification_report_v1",
        "status": "PASS" if record_report["status"] == "PASS" and not hits else "FAIL",
        "verified_count": sum(row.status == VERIFIED for row in rows),
        "provisional_count": sum(row.status == PROVISIONAL for row in rows),
        "forbidden_public_count": len(hits),
        "forbidden_public_hits": hits,
        "record_validation": record_report,
    }
