"""Receive authored P01 records as internal design-decision references.

This local envelope preserves the existing P01 field IDs and wrappers. It does
not author company hypotheses, certify facts, run a P01 Gate, select a theme, or
turn any field into publishable copy. See docs/PILOT_AUTHORING.md for the source
scope and the distinction between supplied inputs and semantic completion.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from .pilot_intake import IntakeError, build_p01_handoff


AUTHORING_SCHEMA = "pilot-p01-authoring-input/v1"
BRIEF_SCHEMA = "pilot-p01-design-brief/v1"
# Original P01 dictionary identifiers, not new Production Contract fields.
P01_FIELDS = {
    "P01_F01": "industry",
    "P01_F02": "service_category",
    "P01_F03": "primary_service",
    "P01_F04": "secondary_services",
    "P01_F05": "service_area",
    "P01_F06": "business_model",
    "P01_F07": "estimated_price_band",
    "P01_F08": "purchase_type",
    "P01_F09": "current_web_condition",
    "P01_F10": "primary_end_user",
    "P01_F11": "secondary_end_user",
    "P01_F12": "main_situation",
    "P01_F13": "main_need",
    "P01_F14": "primary_strength",
    "P01_F15": "secondary_strengths",
    "P01_F16": "current_marketing_problem",
    "P01_F17": "website_problem",
    "P01_F18": "lp_opportunity",
    "P01_F19": "primary_cv",
    "P01_F20": "secondary_cv",
    "P01_F21": "direction_keywords",
    "P01_F22": "avoid_keywords",
}
PUBLICATION_POLICIES = {"DISPLAY_OK_FACT", "DISPLAY_OK_FRAMING", "INTERNAL_ONLY"}
PLACEHOLDERS = {"不明", "未設定", "情報なし", "未確認", "要確認", "unknown", "tbd", "null", "none", "n/a"}


class AuthoringError(ValueError):
    """The submitted authoring cannot be transported without ambiguity."""


def _json(value: Any) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        text.encode("utf-8")
        return text
    except (TypeError, ValueError, UnicodeError) as exc:
        raise AuthoringError("Expected finite JSON data") from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _object(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AuthoringError(f"Expected an object: {path}")
    return value


def _text(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip() or value.strip().casefold() in PLACEHOLDERS:
        raise AuthoringError(f"Author a concrete value: {path}")
    return value


def _value(value: Any, path: str, *, root: bool = True) -> None:
    # A decided empty optional list (e.g. related industries) is meaningful. A
    # wholly empty field or a leaf saying "unknown" is not authored P01 input.
    if value is None or (root and isinstance(value, (Mapping, list)) and not value):
        raise AuthoringError(f"Author a concrete value: {path}")
    if isinstance(value, str):
        _text(value, path)
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise AuthoringError(f"Expected a string property name: {path}")
            _value(item, path + "." + key, root=False)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _value(item, f"{path}[{index}]", root=False)


def _string_list(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise AuthoringError(f"Expected {'nonempty ' if nonempty else ''}string list: {path}")
    for index, item in enumerate(value):
        _text(item, f"{path}[{index}]")
    return value


def _source_only(evidence: Mapping[str, Any]) -> bool:
    """Recognize explicit non-fact status; do not infer verified status."""
    unconfirmed = {"SOURCE_RECORDED_ONLY", "LEGACY_ASSERTION", "HYPOTHESIS", "UNVERIFIED", "NOT_VERIFIED", "NOT_EVALUATED", "NOT_RUN"}
    return any(isinstance(evidence.get(key), str) and evidence[key] in unconfirmed
               for key in ("verification_status", "current_status", "classification"))


def build_theme_design_brief(intake: Mapping[str, Any], authoring: Mapping[str, Any]) -> dict[str, Any]:
    """Check authored-input completeness and preserve its design references.

    All 22 existing field records must be explicitly supplied. Values remain in
    their original wrappers; no industry default or source observation fills a
    field. FACT is an author's classification with evidence references, not a
    new verification performed here. The adapter checks no semantic-quality
    threshold and grants no publication permission.
    """
    # Reuse the intake's original-source integrity check before accepting a
    # company-linked authoring packet.
    try:
        input_handoff = build_p01_handoff(intake)
    except IntakeError as exc:
        raise AuthoringError(str(exc)) from exc
    authoring = _object(authoring, "authoring")
    _json(authoring)
    if authoring.get("schema_version") != AUTHORING_SCHEMA:
        raise AuthoringError("Unsupported local P01 authoring schema")
    if authoring.get("intake_id") != intake["intake_id"]:
        raise AuthoringError("Authoring intake_id does not match this source record")
    source = _object(authoring.get("authoring_source"), "authoring_source")
    for key in ("source_id", "source_locator"):
        _text(source.get(key), "authoring_source." + key)
    evidence_registry = _object(authoring.get("evidence_registry", {}), "evidence_registry")
    for evidence_id, evidence in evidence_registry.items():
        _text(evidence_id, "evidence_registry key")
        _object(evidence, "evidence_registry." + evidence_id)
    records = authoring.get("fields")
    if not isinstance(records, list):
        raise AuthoringError("fields must contain the original P01 records")
    source_observation_ids = {record["observation_id"] for record in input_handoff["source_observations"]}
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        record = _object(record, "field")
        field_id = _text(record.get("field_id"), "field_id")
        if field_id not in P01_FIELDS:
            raise AuthoringError(f"Unknown original P01 field: {field_id}")
        if field_id in by_id:
            raise AuthoringError(f"Duplicate original P01 field: {field_id}")
        if record.get("field_key", P01_FIELDS[field_id]) != P01_FIELDS[field_id]:
            raise AuthoringError(f"field_id and field_key differ: {field_id}")
        _value(record.get("value"), field_id + ".value")
        classification = record.get("classification")
        if not isinstance(classification, str) or classification not in {"FACT", "HYPOTHESIS"}:
            raise AuthoringError(f"Preserve FACT/HYPOTHESIS classification: {field_id}")
        _text(record.get("basis"), field_id + ".basis")
        if not isinstance(record.get("confidence"), str) or record["confidence"] not in {"HIGH", "MEDIUM", "LOW"}:
            raise AuthoringError(f"Invalid original confidence: {field_id}")
        policy = record.get("publication_policy")
        if not isinstance(policy, str) or policy not in PUBLICATION_POLICIES:
            raise AuthoringError(f"Invalid original publication_policy: {field_id}")
        refs = _string_list(record.get("evidence_ids"), field_id + ".evidence_ids", nonempty=classification == "FACT")
        if classification == "HYPOTHESIS":
            if policy == "DISPLAY_OK_FACT" or record.get("verified") is True or record.get("production_evidence_eligible") is True:
                raise AuthoringError(f"Hypothesis cannot assert fact or proof permission: {field_id}")
        else:
            for ref in refs:
                if ref in source_observation_ids:
                    raise AuthoringError(f"Source observation cannot establish a current FACT: {field_id}")
                if ref not in evidence_registry:
                    raise AuthoringError(f"Referenced fact evidence was not supplied: {field_id}: {ref}")
                if _source_only(evidence_registry[ref]):
                    raise AuthoringError(f"Unconfirmed evidence cannot establish a current FACT: {field_id}: {ref}")
        by_id[field_id] = deepcopy(dict(record))
    missing = sorted(set(P01_FIELDS) - set(by_id))
    if missing:
        raise AuthoringError("Author remaining P01 fields: " + ", ".join(missing))

    # Only F21 has the explicit design-direction shape used here. The current
    # source's other value-type proposals are not made mandatory by this code.
    direction = _object(by_id["P01_F21"]["value"], "P01_F21.value for design reference")
    keywords = _string_list(direction.get("keywords"), "P01_F21.value.keywords", nonempty=True)
    for key in ("target_impression", "reason", "usage_scope"):
        _text(direction.get(key), "P01_F21.value." + key)

    original_authoring = deepcopy(dict(authoring))
    counts = {classification: sum(record["classification"] == classification for record in by_id.values())
              for classification in ("FACT", "HYPOTHESIS")}
    packet = {
        "schema_version": BRIEF_SCHEMA,
        "intake_id": intake["intake_id"],
        "industry": deepcopy(intake["industry"]),
        "authoring_source": deepcopy(dict(source)),
        "input_handoff": input_handoff,
        "authoring_snapshot": original_authoring,
        "authoring_snapshot_sha256": _hash(original_authoring),
        "fields_by_key": {P01_FIELDS[field_id]: by_id[field_id] for field_id in P01_FIELDS},
        "evidence_registry": deepcopy(dict(evidence_registry)),
        "design_reference": {
            "direction_field_id": "P01_F21",
            "direction_record": deepcopy(by_id["P01_F21"]),
            "keywords": deepcopy(keywords),
            "target_impression": direction["target_impression"],
            "reason": direction["reason"],
            "usage_scope": direction["usage_scope"],
            "website_problem_field_id": "P01_F17",
            "website_problem_record": deepcopy(by_id["P01_F17"]),
            "use": "P14_DESIGN_DECISION_REFERENCE",
            "formal_p14_field_binding": False,
        },
        "status": {
            "authored_input": "ALL_22_SUPPLIED",
            "original_field_count": len(P01_FIELDS),
            "author_classifications": counts,
            "facts_verified_by_adapter": 0,
            "p01_semantic_quality": "NOT_RUN",
            "p01_stage_completion": "NOT_ASSERTED",
            "theme_selection": "NOT_RUN",
            "public_copy_generation": "NOT_RUN",
            "publication_permission_granted": False,
            "formal_contract_changed": False,
            "production_eligible": False,
        },
    }
    # Pin the entire derived view as well as its original author input, so a
    # consumer can detect projection-only edits before selecting a theme.
    packet["packet_sha256"] = _hash(packet)
    return packet


def validate_theme_design_brief(brief: Mapping[str, Any]) -> None:
    """Recompute the packet from its original inputs before consuming it."""
    brief = _object(brief, "brief")
    if brief.get("schema_version") != BRIEF_SCHEMA:
        raise AuthoringError("Unsupported local P01 design brief schema")
    input_handoff = _object(brief.get("input_handoff"), "input_handoff")
    expected = build_theme_design_brief(input_handoff.get("intake_snapshot"), brief.get("authoring_snapshot"))
    if _hash(brief) != _hash(expected):
        raise AuthoringError("Design brief differs from its original inputs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake", type=Path, required=True, help="One private normalized intake JSON record")
    parser.add_argument("--authoring", type=Path, required=True, help="Explicit authored P01 envelope JSON")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = build_theme_design_brief(json.loads(args.intake.read_text()), json.loads(args.authoring.read_text()))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (AuthoringError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2, f"P01 authoring input rejected: {exc}\n")
    print(json.dumps({"status": result["status"], "output": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
