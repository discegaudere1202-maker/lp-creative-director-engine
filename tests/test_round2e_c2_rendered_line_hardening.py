from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lp_engine.editorial_quality import (  # noqa: E402
    allowed_break_indices,
    make_text_ir,
    render_text_ir,
    validate_rendered_breaks,
)


class Round2EC2RenderedLineTests(unittest.TestCase):
    def test_positive_fixtures_preserve_semantic_boundaries(self) -> None:
        fixtures = [
            ("塗る前に、まず状態を見る。", ["塗る前に、", "まず状態を見る。"], ["状態を見る"]),
            ("色は654通り。塗料は、住まいに合わせて。", ["色は654通り。", "塗料は、", "住まいに合わせて。"], ["住まい", "合わせて"]),
            ("気になるところを、まず見せてください。", ["気になるところを、", "まず見せてください。"], ["気になる", "ところ"]),
            ("住まいの気になるところから、相談できます。", ["住まいの気になるところから、", "相談できます。"], ["住まい", "気になるところ"]),
            ("初めての方でも、安心して相談できます。", ["初めての方でも、", "安心して相談できます。"], ["初めて", "安心して"]),
        ]
        for source, lines, protected in fixtures:
            ir = make_text_ir(source, role="hero_headline", semantic_chunks=lines, preferred_lines=lines, protected_phrases=protected)
            report = validate_rendered_breaks(ir, lines)
            self.assertEqual(report["status"], "PASS", report)

    def test_negative_lexical_and_protected_splits_fail(self) -> None:
        fixtures = [
            ("住まい", ["住", "まい"], ["住まい"]),
            ("ところ", ["と", "ころ"], ["ところ"]),
            ("まず状態を見る。", ["まず状態", "を見る。"], ["状態を見る"]),
        ]
        for source, lines, protected in fixtures:
            ir = make_text_ir(source, role="hero_headline", semantic_chunks=lines, preferred_lines=lines, protected_phrases=protected)
            report = validate_rendered_breaks(ir, lines)
            self.assertEqual(report["status"], "FAIL", report)
            self.assertTrue(report["protected_phrase_violations"] or report["lexical_split_violations"], report)

    def test_allowed_boundaries_are_not_character_count_heuristics(self) -> None:
        ir = make_text_ir("住まいの気になるところから、相談できます。", role="hero_headline", semantic_chunks=["住まいの気になるところから、", "相談できます。"], preferred_lines=["住まいの気になるところから、", "相談できます。"])
        self.assertEqual(allowed_break_indices(ir), [14])
        self.assertNotIn(1, allowed_break_indices(ir))

    def test_renderer_marks_headline_chunks_as_protected_units(self) -> None:
        ir = make_text_ir("塗る前に、まず状態を見る。", role="hero_headline", semantic_chunks=["塗る前に、", "まず状態を見る。"], preferred_lines=["塗る前に、", "まず状態を見る."])
        rendered = render_text_ir(ir, tag="h1")
        self.assertIn("semantic-protected-line", rendered)
        self.assertIn("data-semantic-index=\"0\"", rendered)
        self.assertIn("data-semantic-source=", rendered)


if __name__ == "__main__":
    unittest.main()
