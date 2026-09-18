from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lp_engine.batch import validate_publish_ready
from lp_engine.creative_composition import build_creative_composition
from lp_engine.editorial_quality import (
    EDITORIAL_GATES,
    build_editorial_contract,
    internal_label_gate,
    make_text_ir,
    naturalness_gate,
    repair_text_ir,
    render_text_ir,
    scan_internal_labels,
    validate_text_ir,
)
from lp_engine.company_research_v2 import build_maylynn_research_snapshot
from lp_engine.customer_decision import build_customer_decision_model
from lp_engine.evidence_graph_v2 import build_evidence_graph
from lp_engine.experience_architecture import build_experience_architecture
import run_round2e_b_maylynn as round2e


class Round2ECEditorialEngineTests(unittest.TestCase):
    def source_creative(self) -> dict:
        snapshot = build_maylynn_research_snapshot()
        graph = build_evidence_graph(snapshot)
        decisions = build_customer_decision_model(snapshot, graph)
        experience = build_experience_architecture(snapshot, decisions)
        return build_creative_composition(snapshot, experience)

    def test_semantic_ir_preserves_meaning_and_protected_phrases(self) -> None:
        ir = make_text_ir(
            "住まいの気になるところから、相談できます。",
            role="hero_headline",
            semantic_chunks=["住まいの気になるところから、", "相談できます。"],
            preferred_lines=["住まいの気になるところから、", "相談できます。"],
            protected_phrases=["気になるところ", "相談できます"],
        )
        self.assertEqual(validate_text_ir(ir)["status"], "PASS")
        rendered = render_text_ir(ir, tag="h1")
        self.assertIn("data-editorial-role=\"hero_headline\"", rendered)
        self.assertIn("住まいの気になるところから、", rendered)
        self.assertIn("相談できます。", rendered)
        self.assertNotIn("renderer-break", rendered)

    def test_generic_repair_merges_orphan_fragments(self) -> None:
        ir = make_text_ir(
            "塗る前に、まず状態を見る。",
            role="hero_headline",
            semantic_chunks=["塗る前", "に、", "まず状態を見る。"],
            preferred_lines=["塗る前", "に、", "まず状態を見る。"],
            protected_phrases=["塗る前に", "状態を見る"],
        )
        repaired = repair_text_ir(ir)
        self.assertEqual(repaired["repair_status"], "PASS")
        self.assertFalse(any(len("".join(ch for ch in line if not ch.isspace())) <= 2 for line in repaired["preferred_lines_desktop"]))
        self.assertIn("塗る前に、", "".join(repaired["preferred_lines_desktop"]))

    def test_naturalness_gate_rejects_ambiguous_copy_and_accepts_v06(self) -> None:
        self.assertEqual(naturalness_gate("公開されている仕事で、確かめる。", role="lead")["status"], "FAIL")
        creative = self.source_creative()
        v06 = creative["copy"]["V06"]
        self.assertEqual(naturalness_gate(v06["headline"][0] + v06["headline"][1], role="headline")["status"], "PASS")
        self.assertEqual(naturalness_gate(v06["lead"], role="lead")["status"], "PASS")

    def test_internal_label_gate_is_strict_but_public_labels_are_allowed(self) -> None:
        self.assertEqual(internal_label_gate(visible_text="参考イメージ NOT EVIDENCE")["status"], "FAIL")
        self.assertEqual(scan_internal_labels("SERVICE / PROCESS / FAQ / AREA"), [])
        self.assertEqual(internal_label_gate(visible_text="SERVICE / PROCESS / FAQ / AREA")["status"], "PASS")

    def test_publish_ready_fails_closed_for_missing_or_false_gate(self) -> None:
        self.assertEqual(validate_publish_ready({})["status"], "FAIL")
        contract = {"status": "PASS", "gates": {name: True for name in EDITORIAL_GATES}}
        self.assertEqual(validate_publish_ready(contract)["status"], "PASS")
        contract["gates"]["rendered_line_shape"] = False
        self.assertEqual(validate_publish_ready(contract)["status"], "FAIL")

    def test_renderer_uses_public_labels_and_corrected_v06(self) -> None:
        creative = self.source_creative()
        snapshot = build_maylynn_research_snapshot()
        graph = build_evidence_graph(snapshot)
        decisions = build_customer_decision_model(snapshot, graph)
        experience = build_experience_architecture(snapshot, decisions)
        rendered = round2e.render_html(snapshot, experience, creative, round2e.load_media())
        self.assertIn("工事の内容を、", rendered)
        self.assertIn("確かめる。", rendered)
        self.assertIn("住まいの状態を見るための参考イメージ", rendered)
        self.assertNotIn("NOT EVIDENCE", rendered)
        self.assertNotIn("FIELD OBSERVATION", rendered)

    def test_contract_requires_every_engine_gate(self) -> None:
        blocks = [make_text_ir("初めての方でも、安心して相談できます。", role="lead")]
        rendered = {"line_status": "PASS", "internal_label_status": "PASS", "responsive_status": "PASS", "broken_visual_status": "PASS"}
        interactions = {"status": "PASS"}
        contract = build_editorial_contract(blocks, rendered=rendered, interactions=interactions)
        self.assertEqual(contract["status"], "PASS")
        self.assertEqual(set(contract["gates"]), set(EDITORIAL_GATES))


if __name__ == "__main__":
    unittest.main()
