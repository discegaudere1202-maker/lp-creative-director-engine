"""Explainable, unadopted theme candidates from an authored P01 design brief.

This adapter compares explicit F21 keywords with an externally supplied theme
contract. Literal overlap is a selection heuristic, not a semantic assessment,
design approval, P14 field binding, or permission to publish company claims.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

from .pilot_authoring import validate_theme_design_brief


RECOMMENDATIONS_SCHEMA = "pilot-theme-recommendations/v1"
INDUSTRIES = {"landscape", "painting", "bar"}


class ThemeSelectionError(ValueError):
    """A source or recommendation cannot be consumed without ambiguity."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _hash(value: Any) -> str:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ThemeSelectionError("INVALID_JSON", "Expected ordinary finite JSON data") from exc
    return hashlib.sha256(raw).hexdigest()


def _normal(text: str) -> str:
    return unicodedata.normalize("NFKC", text).casefold().strip()


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ThemeSelectionError("AMBIGUOUS_CONTRACT", "Duplicate JSON property: " + key)
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ThemeSelectionError("INVALID_CONTRACT", "Non-finite JSON value: " + value)


def _text(value: Any, pointer: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ThemeSelectionError("INVALID_CONTRACT", "Expected theme text at " + pointer)
    return value


def _read_contract(path: str | Path, expected_sha256: str) -> tuple[list[dict], dict]:
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise ThemeSelectionError("SOURCE_PIN_REQUIRED", "An explicit SHA-256 pin for the theme contract is required")
    try:
        local = Path(path)
        if not local.is_file() or local.is_symlink():
            raise OSError("Not an ordinary local file")
        raw = local.read_bytes()
    except (OSError, TypeError, ValueError) as exc:
        raise ThemeSelectionError("CONTRACT_READ_ERROR", "Unable to read the supplied local theme contract") from exc
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ThemeSelectionError("CONTRACT_HASH_MISMATCH", "Theme contract bytes differ from the expected source pin")
    try:
        contract = json.loads(raw.decode("utf-8"), object_pairs_hook=_object_pairs, parse_constant=_nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ThemeSelectionError("INVALID_CONTRACT", "Theme contract must be UTF-8 JSON") from exc
    if not isinstance(contract, list) or not contract:
        raise ThemeSelectionError("INVALID_CONTRACT", "Theme contract must contain an explicit nonempty theme list")
    seen = set()
    for index, theme in enumerate(contract):
        pointer = f"/{index}"
        if not isinstance(theme, dict):
            raise ThemeSelectionError("INVALID_CONTRACT", "Expected theme object at " + pointer)
        theme_id = _text(theme.get("id"), pointer + "/id")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", theme_id) or theme_id in seen:
            raise ThemeSelectionError("INVALID_CONTRACT", "Theme IDs must be unambiguous identifiers: " + theme_id)
        seen.add(theme_id)
        if not isinstance(theme.get("industry"), str) or theme["industry"] not in INDUSTRIES:
            raise ThemeSelectionError("INVALID_CONTRACT", "Unsupported theme industry at " + pointer)
        for key in ("label", "fit", "description"):
            _text(theme.get(key), pointer + "/" + key)
        moves = theme.get("designMoves")
        if not isinstance(moves, list) or not moves:
            raise ThemeSelectionError("INVALID_CONTRACT", "Expected explicit designMoves at " + pointer)
        for move_index, move in enumerate(moves):
            _text(move, pointer + f"/designMoves/{move_index}")
    return contract, {"sha256": actual, "bytes": len(raw), "theme_count": len(contract)}


def _source_texts(theme: dict, index: int) -> list[tuple[str, str]]:
    return [(f"/{index}/fit", theme["fit"]), (f"/{index}/description", theme["description"])] + [
        (f"/{index}/designMoves/{move_index}", value) for move_index, value in enumerate(theme["designMoves"])
    ]


def build_theme_recommendations(
    brief: Mapping[str, Any],
    *,
    theme_contract_path: str | Path,
    expected_theme_contract_sha256: str,
) -> dict[str, Any]:
    """Return source-traced candidate ordering; never adopt a theme.

    Industry filters the candidate set only. Distinct normalized F21 keywords
    are matched as contiguous substrings of fit, description and designMoves.
    The number of matching keywords orders candidates; it is not a quality or
    suitability score. Equal counts retain equal rank. Zero overlap, ties at
    the top, or no same-industry source return JUDGMENT_REQUIRED.

    F17 and all P01 wrappers remain in brief_snapshot. Problem descriptions,
    author rationale, claims, and F22 copy restrictions are not transformed
    into preferred styles or design exclusions. The caller owns the actual
    design decision and must explicitly select parts and images separately.
    """
    validate_theme_design_brief(brief)
    contract, source_pin = _read_contract(theme_contract_path, expected_theme_contract_sha256)
    industry = brief["industry"]["key"]
    direction = brief["design_reference"]
    keywords = direction["keywords"]
    candidates = []
    excluded = []
    for index, theme in enumerate(contract):
        if theme["industry"] != industry:
            excluded.append({"theme_id": theme["id"], "industry": theme["industry"], "reason_code": "DIFFERENT_INDUSTRY"})
            continue
        matches = []
        matched_norms = set()
        for keyword_index, keyword in enumerate(keywords):
            normalized = _normal(keyword)
            sources = []
            for pointer, value in _source_texts(theme, index):
                normalized_source = _normal(value)
                start = normalized_source.find(normalized)
                if start != -1:
                    sources.append({
                        "json_pointer": pointer,
                        "text": value,
                        "text_sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(),
                        "normalized_span": {"start": start, "end": start + len(normalized)},
                    })
            if sources:
                matched_norms.add(normalized)
                matches.append({"keyword_index": keyword_index, "keyword": keyword,
                                "normalized_keyword": normalized, "source_matches": sources})
        count = len(matched_norms)
        candidates.append({
            "theme_id": theme["id"],
            "label": theme["label"],
            "industry": theme["industry"],
            "contract_index": index,
            "matched_keyword_count": count,
            "unmatched_keywords": [word for word in keywords if _normal(word) not in matched_norms],
            "matches": matches,
            "match_state": "LITERAL_OVERLAP_FOUND" if count else "NO_LITERAL_OVERLAP",
            "explanation": f"P01_F21 の異なる方向語 {count} 件が、同業種のテーマ説明に文字列として一致。意味上の適合・完成品質は未判定。",
        })
    # Python's stable sort leaves tied records in source order for display only.
    # Equal count means equal rank; source order never creates a winner.
    candidates.sort(key=lambda item: -item["matched_keyword_count"])
    for candidate in candidates:
        count = candidate["matched_keyword_count"]
        candidate["rank"] = 1 + sum(other["matched_keyword_count"] > count for other in candidates) if count else None
    best_count = candidates[0]["matched_keyword_count"] if candidates else 0
    leaders = [candidate["theme_id"] for candidate in candidates if best_count and candidate["matched_keyword_count"] == best_count]
    if not candidates:
        state, reason = "JUDGMENT_REQUIRED", "NO_THEMES_FOR_INDUSTRY"
        explanation = "対象業種のテーマが入力資料にありません。別業種のテーマへ自動置換しません。"
    elif not leaders:
        state, reason = "JUDGMENT_REQUIRED", "NO_LITERAL_DIRECTION_OVERLAP"
        explanation = "明示された方向語との文字列一致がありません。類義語や意図を推測して推薦を確定しません。"
    elif len(leaders) > 1:
        state, reason = "JUDGMENT_REQUIRED", "TOP_MATCH_COUNT_TIED"
        explanation = "一致語数が同じ候補を残しました。設計担当が原文・事業者の意図を見て判断する必要があります。"
    else:
        state, reason = "CANDIDATE_FOR_REVIEW", "MOST_LITERAL_DIRECTION_MATCHES"
        explanation = "文字列一致が最も多い候補を先頭にしました。設計担当による意味・見た目の確認と明示採用はまだです。"
    result = {
        "schema_version": RECOMMENDATIONS_SCHEMA,
        "intake_id": brief["intake_id"],
        "industry": industry,
        "brief_packet_sha256": brief["packet_sha256"],
        "brief_snapshot": deepcopy(dict(brief)),
        "theme_contract": source_pin,
        "method": {
            "id": "F21_LITERAL_KEYWORD_OVERLAP_V1",
            "type": "HEURISTIC",
            "normalization": "Unicode NFKC, casefold, trim outer whitespace",
            "comparison": "Contiguous normalized keyword substring",
            "ranking": "Distinct matching keyword count descending; ties share rank",
            "theme_fields": ["fit", "description", "designMoves"],
            "direction_field_id": "P01_F21",
            "context_only_field_ids": ["P01_F17"],
            "semantic_interpretation": "NOT_RUN",
            "synonyms_inferred": False,
            "quality_score_generated": False,
            "theme_default_picks_used": False,
            "f22_copy_rules_used_as_design_exclusions": False,
        },
        "candidates": candidates,
        "excluded_themes": excluded,
        "decision": {"status": state, "reason_code": reason, "explanation": explanation,
                     "leading_theme_ids": leaders, "selected_theme_id": None},
        "status": {
            "p14_adoption": "NOT_ASSERTED",
            "formal_p14_field_binding": False,
            "quality_review": "NOT_RUN",
            "public_copy_generation": "NOT_RUN",
            "facts_verified_by_adapter": 0,
            "publication_permission_granted": False,
            "formal_contract_changed": False,
            "production_eligible": False,
        },
    }
    result["packet_sha256"] = _hash(result)
    return result


def validate_theme_recommendations(
    recommendations: Mapping[str, Any],
    *,
    brief: Mapping[str, Any],
    theme_contract_path: str | Path,
    expected_theme_contract_sha256: str,
) -> None:
    """Recompute against caller-pinned sources before consuming saved candidates."""
    if not isinstance(recommendations, Mapping):
        raise ThemeSelectionError("INVALID_RECOMMENDATION", "Expected a recommendation packet")
    expected = build_theme_recommendations(
        brief, theme_contract_path=theme_contract_path,
        expected_theme_contract_sha256=expected_theme_contract_sha256,
    )
    if _hash(dict(recommendations)) != _hash(expected):
        raise ThemeSelectionError("RECOMMENDATION_MISMATCH", "Candidates differ from the supplied original brief and pinned theme contract")
