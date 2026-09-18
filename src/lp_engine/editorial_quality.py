"""Engine-wide Japanese editorial and rendered-text quality contracts.

The production boundary keeps copy intent as data until rendering.  This
module intentionally contains no company slug or sentence exception: the same
IR, source checks, repair loop and public-label policy apply to every LP.
"""
from __future__ import annotations

from copy import deepcopy
import html
import re
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = "editorial_text_ir_v1"
EDITORIAL_GATES = (
    "japanese_editorial_structure",
    "rendered_line_shape",
    "rendered_break_boundary",
    "protected_phrase_integrity",
    "lexical_split_integrity",
    "font_determinism",
    "internal_label_leakage",
    "interaction_reality",
    "copy_naturalness",
    "responsive_render",
    "no_broken_visual",
)

# These are production taxonomy values, not public copy.  Public words such
# as SERVICE, PROCESS and FAQ are deliberately not in this denylist.
INTERNAL_LABEL_DENYLIST = (
    "NOT EVIDENCE",
    "PROXY",
    "GENERATED",
    "PLACEHOLDER",
    "EVIDENCE_PENDING",
    "INTERNAL",
    "DEBUG",
    "CLAIM TRACE",
    "FIELD OBSERVATION",
    "SOURCE",
)

PARTICLES = {"を", "に", "へ", "が", "は", "と", "で", "や", "の", "も", "ば", "て", "から", "まで", "より"}
OPENING_PUNCTUATION = set("、。！？!?：:）」』】〕〉》〉〉\"'")
PUNCTUATION_ONLY = set("、。！？!?：:・,./／—ー…()（）[]【】「」『』")

DEFAULT_LEXICAL_UNITS = (
    "住まい",
    "ところ",
    "初めて",
    "気になる",
    "状態を見る",
    "相談する",
    "相談できます",
    "安心して",
    "合わせて",
)


def _text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _visible_chars(value: str) -> list[str]:
    return [ch for ch in value if not ch.isspace() and ch not in PUNCTUATION_ONLY]


def split_semantic_chunks(text: str) -> list[str]:
    """Split at sentence/meaning punctuation, never at a character count."""
    value = _text(text)
    if not value:
        return []
    chunks: list[str] = []
    current = ""
    for char in value:
        current += char
        if char in "、。！？!?":
            chunks.append(current)
            current = ""
    if current:
        chunks.append(current)
    if len(chunks) == 1 and len(_visible_chars(value)) > 16:
        # A fallback for generated text without punctuation.  It uses a
        # particle boundary, not N characters, and leaves the phrase intact.
        candidates = [m.end() for m in re.finditer(r"(?:から|まで|について|には|を|に|で|の|が|は)", value)]
        midpoint = max(1, len(value) // 2)
        boundary = min((x for x in candidates if x >= midpoint), key=lambda x: abs(x - midpoint), default=0)
        if boundary and boundary < len(value):
            chunks = [value[:boundary], value[boundary:]]
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def make_text_ir(
    text: str,
    *,
    role: str,
    semantic_chunks: Sequence[str] | None = None,
    preferred_lines: Sequence[str] | None = None,
    protected_phrases: Sequence[str] | None = None,
    paragraphs: Sequence[str] | None = None,
    context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the renderer-facing semantic text contract."""
    value = _text(text)
    chunks = [_text(item) for item in (semantic_chunks or split_semantic_chunks(value)) if _text(item)]
    lines = [_text(item) for item in (preferred_lines or chunks) if _text(item)]
    return {
        "schema_version": SCHEMA_VERSION,
        "role": _text(role) or "body",
        "text": value,
        "semantic_chunks": chunks,
        "preferred_lines_desktop": lines,
        "protected_phrases": [_text(item) for item in (protected_phrases or []) if _text(item)],
        "paragraphs": [_text(item) for item in (paragraphs or [value]) if _text(item)],
        "context": dict(context or {}),
    }


def _line_violations(lines: Sequence[str], protected_phrases: Sequence[str] = ()) -> list[dict[str, Any]]:
    cleaned = [_text(line) for line in lines if _text(line)]
    violations: list[dict[str, Any]] = []
    lengths = [len(_visible_chars(line)) for line in cleaned]
    max_length = max(lengths or [0])
    for index, line in enumerate(cleaned):
        visible = _visible_chars(line)
        if not visible or all(char in PUNCTUATION_ONLY for char in line.strip()):
            violations.append({"type": "punctuation_only_line", "line": index + 1, "value": line})
        if line[:1] in OPENING_PUNCTUATION:
            violations.append({"type": "opening_punctuation_line_start", "line": index + 1, "value": line})
        if line.strip("、。！？!?：: ") in PARTICLES:
            violations.append({"type": "isolated_particle", "line": index + 1, "value": line})
        if len(visible) <= 1 and max_length >= 5:
            violations.append({"type": "one_character_line", "line": index + 1, "value": line})
        if len(visible) == 2 and max_length >= 6:
            violations.append({"type": "short_fragment_anywhere", "line": index + 1, "value": line})
    if len(cleaned) >= 2 and lengths[-1] <= 2 and max_length >= 6:
        violations.append({"type": "extreme_last_line", "line": len(cleaned), "value": cleaned[-1]})
    joined = "".join(cleaned)
    for phrase in protected_phrases:
        phrase = _text(phrase)
        if not phrase or phrase not in joined:
            continue
        offset = 0
        for line in cleaned[:-1]:
            offset += len(line)
            if joined[max(0, offset - len(phrase) + 1):offset + len(phrase)] == phrase:
                violations.append({"type": "protected_phrase_split", "phrase": phrase})
                break
    return violations


def validate_text_ir(ir: Mapping[str, Any]) -> dict[str, Any]:
    lines = list(ir.get("preferred_lines_desktop") or ir.get("semantic_chunks") or [ir.get("text", "")])
    violations = _line_violations(lines, ir.get("protected_phrases") or [])
    paragraphs = list(ir.get("paragraphs") or [])
    if ir.get("role") in {"body", "lead"} and not paragraphs:
        violations.append({"type": "missing_paragraph_structure"})
    return {"status": "PASS" if not violations else "FAIL", "role": ir.get("role", "body"), "line_count": len(lines), "violations": violations}


def repair_text_ir(ir: Mapping[str, Any], *, max_attempts: int = 4) -> dict[str, Any]:
    """Repair generic semantic structure before browser rendering.

    The repair loop is deterministic and auditable.  It never invents copy;
    it only recomposes existing semantic chunks and paragraphs.
    """
    repaired = deepcopy(dict(ir))
    audit: list[dict[str, Any]] = []
    for attempt in range(1, max_attempts + 1):
        report = validate_text_ir(repaired)
        audit.append({"attempt": attempt, "status": report["status"], "violations": report["violations"]})
        if report["status"] == "PASS":
            break
        chunks = [_text(item) for item in repaired.get("semantic_chunks") or split_semantic_chunks(repaired.get("text", "")) if _text(item)]
        if len(chunks) >= 2:
            bad = _line_violations(chunks, repaired.get("protected_phrases") or [])
            if bad:
                # Merge the shortest adjacent unit into its neighbor.  This
                # preserves the source words and removes orphan particles.
                index = min(range(len(chunks)), key=lambda i: len(_visible_chars(chunks[i])))
                if index == 0:
                    chunks[0:2] = [chunks[0] + chunks[1]]
                else:
                    chunks[index - 1:index + 1] = [chunks[index - 1] + chunks[index]]
        repaired["semantic_chunks"] = chunks
        repaired["preferred_lines_desktop"] = chunks
    final = validate_text_ir(repaired)
    repaired["repair_audit"] = audit
    repaired["repair_status"] = final["status"]
    return repaired


def render_text_ir(ir: Mapping[str, Any], *, tag: str = "p", escape: Callable[[Any], str] | None = None) -> str:
    """Render semantic lines without renderer-owned sentence splitting."""
    esc = escape or (lambda value: html.escape(str(value or ""), quote=True))
    lines = list(ir.get("preferred_lines_desktop") or ir.get("semantic_chunks") or [ir.get("text", "")])
    role = html.escape(str(ir.get("role", "body")), quote=True)
    protected_class = " semantic-protected-line" if str(ir.get("role", "")).endswith("headline") or str(ir.get("role", "")) == "headline" else ""
    spans = "".join(
        f'<span class="semantic-line headline-line{protected_class}" data-semantic-role="{role}" '
        f'data-semantic-index="{index}" data-semantic-source="{esc(line)}">{esc(line)}</span>'
        for index, line in enumerate(lines)
    )
    return f"<{tag} data-editorial-role=\"{role}\">{spans}</{tag}>"


def _compact_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _boundary_indices(source: str, lines: Sequence[str]) -> list[int]:
    compact_source = _compact_text(source)
    compact_lines = [_compact_text(line) for line in lines if _compact_text(line)]
    if not compact_lines:
        return []
    cursor = 0
    indices: list[int] = []
    for line in compact_lines[:-1]:
        cursor += len(line)
        indices.append(cursor)
    return indices if "".join(compact_lines) == compact_source else [-1]


def allowed_break_indices(ir: Mapping[str, Any]) -> list[int]:
    """Return the union of semantic chunk and preferred-line boundaries."""
    source = _compact_text(ir.get("text", ""))
    boundaries: set[int] = set()
    for key in ("semantic_chunks", "preferred_lines_desktop"):
        values = [_compact_text(item) for item in (ir.get(key) or []) if _compact_text(item)]
        cursor = 0
        for value in values[:-1]:
            cursor += len(value)
            boundaries.add(cursor)
        if values and "".join(values) != source:
            return []
    return sorted(boundaries)


def _phrase_ranges(source: str, phrases: Sequence[str]) -> list[tuple[str, int, int]]:
    compact_source = _compact_text(source)
    ranges: list[tuple[str, int, int]] = []
    for phrase in phrases:
        compact_phrase = _compact_text(phrase)
        if not compact_phrase:
            continue
        start = compact_source.find(compact_phrase)
        while start >= 0:
            ranges.append((compact_phrase, start, start + len(compact_phrase)))
            start = compact_source.find(compact_phrase, start + 1)
    return ranges


def validate_rendered_breaks(
    ir: Mapping[str, Any],
    rendered_lines: Sequence[str],
    *,
    lexical_units: Sequence[str] | None = None,
    font: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate actual Chromium line boundaries against the semantic IR."""
    source = _compact_text(ir.get("text", ""))
    lines = [_compact_text(line) for line in rendered_lines if _compact_text(line)]
    breaks = _boundary_indices(source, lines)
    allowed = allowed_break_indices(ir)
    boundary_violations = (
        [{"type": "rendered_text_mismatch", "source": source, "rendered_lines": lines}]
        if breaks == [-1]
        else [{"break_index": index, "allowed_break_indices": allowed} for index in breaks if index not in allowed]
    )
    protected_violations = [
        {"phrase": phrase, "break_index": index, "range": [start, end]}
        for index in breaks
        for phrase, start, end in _phrase_ranges(source, ir.get("protected_phrases") or [])
        if start < index < end
    ]
    lexical_violations = [
        {"unit": phrase, "break_index": index, "range": [start, end]}
        for index in breaks
        for phrase, start, end in _phrase_ranges(source, lexical_units or DEFAULT_LEXICAL_UNITS)
        if start < index < end
    ]
    font_payload = dict(font or {})
    font_ok = font is None or all(font_payload.get(key) not in (None, "") for key in ("font_family", "font_size", "letter_spacing", "element_width"))
    issues = boundary_violations + protected_violations + lexical_violations
    return {
        "status": "PASS" if not issues and font_ok else "FAIL",
        "source": source,
        "semantic_chunks": list(ir.get("semantic_chunks") or []),
        "preferred_lines": list(ir.get("preferred_lines_desktop") or []),
        "rendered_lines": lines,
        "break_indices": breaks,
        "allowed_break_indices": allowed,
        "boundary_violations": boundary_violations,
        "protected_phrase_violations": protected_violations,
        "lexical_split_violations": lexical_violations,
        "font": font_payload,
        "font_status": "PASS" if font_ok else "FAIL",
    }


def scan_internal_labels(text: str) -> list[str]:
    haystack = re.sub(r"\s+", " ", str(text or "")).upper()
    return [label for label in INTERNAL_LABEL_DENYLIST if label in haystack]


def internal_label_gate(*, source_html: str = "", visible_text: str = "", pseudo_text: str = "") -> dict[str, Any]:
    hits = sorted(set(scan_internal_labels(source_html) + scan_internal_labels(visible_text) + scan_internal_labels(pseudo_text)))
    return {"status": "PASS" if not hits else "FAIL", "leak_count": len(hits), "labels": hits, "denylist": list(INTERNAL_LABEL_DENYLIST), "public_allowlist": ["SERVICE", "PROCESS", "FAQ", "AREA"]}


def naturalness_gate(text: str, *, role: str = "body", context: Mapping[str, Any] | None = None) -> dict[str, Any]:
    value = _text(text)
    issues: list[dict[str, str]] = []
    if re.search(r"公開されている仕事で[、,]?\s*確かめる", value):
        issues.append({"type": "ambiguous_subject_object", "reason": "公開情報から何を理解するかが明示されていない"})
    if re.search(r"(?:で|に)\s*[、,]?\s*確かめる。?$", value) and "何" not in value and not re.search(r"(内容|条件|範囲|状態|工事|施工|料金|保証)", value):
        issues.append({"type": "unclear_object", "reason": "確認対象が明示されていない"})
    if role == "cta" and len(value) > 24:
        issues.append({"type": "cta_not_concise", "reason": "CTAは原則1行の行動表現にする"})
    if not value:
        issues.append({"type": "empty_copy", "reason": "空のコピー"})
    ctx = dict(context or {})
    if ctx.get("subject_required") and not any(token in value for token in ctx["subject_required"]):
        issues.append({"type": "subject_clarity", "reason": "sectionが扱う対象が明示されていない"})
    return {"status": "PASS" if not issues else "FAIL", "text": value, "role": role, "issues": issues}


def build_editorial_contract(blocks: Sequence[Mapping[str, Any]], *, rendered: Mapping[str, Any] | None = None, interactions: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source_reports = [validate_text_ir(block) for block in blocks]
    natural_reports = [naturalness_gate(block.get("text", ""), role=str(block.get("role", "body")), context=block.get("context")) for block in blocks]
    rendered = dict(rendered or {})
    interactions = dict(interactions or {})
    gates = {
        "japanese_editorial_structure": all(row["status"] == "PASS" for row in source_reports),
        "rendered_line_shape": rendered.get("line_status", "PASS") == "PASS",
        "rendered_break_boundary": rendered.get("rendered_break_boundary_status", "PASS") == "PASS",
        "protected_phrase_integrity": rendered.get("protected_phrase_status", "PASS") == "PASS",
        "lexical_split_integrity": rendered.get("lexical_split_status", "PASS") == "PASS",
        "font_determinism": rendered.get("font_determinism_status", "PASS") == "PASS",
        "internal_label_leakage": rendered.get("internal_label_status", "PASS") == "PASS",
        "interaction_reality": interactions.get("status", "PASS") == "PASS",
        "copy_naturalness": all(row["status"] == "PASS" for row in natural_reports),
        "responsive_render": rendered.get("responsive_status", "PASS") == "PASS",
        "no_broken_visual": rendered.get("broken_visual_status", "PASS") == "PASS",
    }
    return {
        "schema_version": "editorial_quality_contract_v1",
        "status": "PASS" if all(gates.values()) else "FAIL",
        "gates": gates,
        "source_copy_qa": {"status": "PASS" if all(x["status"] == "PASS" for x in source_reports) else "FAIL", "reports": source_reports},
        "copy_naturalness_qa": {"status": "PASS" if all(x["status"] == "PASS" for x in natural_reports) else "FAIL", "reports": natural_reports},
        "repair_policy": {
            "max_attempts": 4,
            "steps": ["layout_width_adjustment", "font_measure_adjustment", "preferred_semantic_lines", "headline_recompose", "copy_resegmentation"],
            "on_exhaustion": "GENERATION_FAIL_OR_HUMAN_REVIEW_QUEUE",
        },
        "batch_policy": "publish_ready_requires_all_editorial_gates",
    }


def editorial_gate_names() -> tuple[str, ...]:
    return EDITORIAL_GATES
