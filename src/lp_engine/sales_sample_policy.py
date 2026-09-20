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
DERIVED = "derived"
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


@dataclass(frozen=True)
class DerivedCopyRecord:
    """A public sentence assembled only from an explicit fact trace."""

    key: str
    value: str
    source_fact_keys: tuple[str, ...]
    status: str = DERIVED

    def __post_init__(self) -> None:
        if self.status != DERIVED:
            raise ValueError("derived copy must use the derived status")
        if not self.source_fact_keys:
            raise ValueError("derived copy requires source facts")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_ASK_LATER_TOKENS = ("相談時に確認", "事前に確認", "確認してください", "お問い合わせください", "TBD", "未定")


def validate_derived_copy(
    facts: Iterable[FactRecord], derived: Iterable[DerivedCopyRecord]
) -> dict[str, object]:
    """Fail closed when derived public copy loses its fact provenance.

    Verified and provisional facts are both publishable under the existing
    replacement contract.  A derived sentence may not point at a forbidden or
    missing fact, and it may not defer a fact that is already known.
    """

    fact_map = {row.key: row for row in facts}
    rows = list(derived)
    errors: list[str] = []
    traces: list[dict[str, object]] = []
    for row in rows:
        missing = [key for key in row.source_fact_keys if key not in fact_map]
        forbidden = [key for key in row.source_fact_keys if key in fact_map and fact_map[key].status == FORBIDDEN]
        deferred = [token for token in _ASK_LATER_TOKENS if token.casefold() in row.value.casefold()]
        if missing:
            errors.append(f"missing_source:{row.key}:{','.join(missing)}")
        if forbidden:
            errors.append(f"forbidden_source:{row.key}:{','.join(forbidden)}")
        if deferred:
            errors.append(f"deferred_known_fact:{row.key}:{','.join(deferred)}")
        traces.append({"key": row.key, "status": row.status, "value": row.value, "source_fact_keys": list(row.source_fact_keys), "source_statuses": [fact_map[key].status for key in row.source_fact_keys if key in fact_map]})
    return {"schema_version": "derived_copy_propagation_gate_v1", "status": "PASS" if not errors else "FAIL", "errors": errors, "records": traces, "count": len(rows)}


def provisional_propagation_gate(
    facts: Iterable[FactRecord], derived: Iterable[DerivedCopyRecord]
) -> dict[str, object]:
    """Named gate used by round runners and future company generators."""

    report = validate_derived_copy(facts, derived)
    report["gate"] = "PROVISIONAL FACT PROPAGATION GATE"
    return report
