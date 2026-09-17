import json
import re
import tempfile
import unittest
from pathlib import Path

from lp_engine.creative_genome import derive_creative_genome, public_copy_gate
from lp_engine.production_generation import run_generation
from lp_engine.structural_similarity import compare, signature
from lp_engine.narrative_architecture import derive_narrative_architecture, narrative_gates

FIXTURE = Path(__file__).parents[1] / "examples/production/andy_motorcycle/andy_motorcycle_production_input_v1.json"


class CreativeGenomeTest(unittest.TestCase):
    def test_genome_is_truth_derived_and_complete(self):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            result = run_generation(raw, Path(directory) / "out", generation_id="genome-test")
        genome = result.stage_outputs["creative_genome"]
        self.assertIn(genome["dominant_narrative"], {"craft", "mastery", "sensory_experience", "guidance", "participation", "discovery"})
        self.assertGreaterEqual(len(genome["composition_logic"]), 4)
        self.assertGreaterEqual(len(genome["screenshot_peak_plan"]), 2)
        self.assertGreaterEqual(len(genome["cta_progression"]), 3)
        self.assertGreaterEqual(len(genome["mobile_redirection"]), 2)

    def test_public_copy_does_not_leak_internal_fields(self):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            result = run_generation(raw, Path(directory) / "out", generation_id="hygiene-test")
            html = (Path(directory) / "out" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(public_copy_gate(html)["status"], "PASS")
        self.assertNotRegex(html, r"andy-e-|photo_role|provenance state|generation_id")
        self.assertEqual(result.manifest["presentation_hygiene"]["status"], "PASS")

    def test_structural_comparison_reports_lower_new_similarity(self):
        a = {"section_sequence": ["hero", "truth"], "composition_sequence": ["split", "detail"]}
        b = {"section_sequence": ["hero", "truth"], "composition_sequence": ["split", "detail"]}
        c = {"section_sequence": ["hero", "process"], "composition_sequence": ["immersive", "sequence"]}
        report = compare({"a": a, "b": b, "c": a}, {"a": a, "b": c, "c": b})
        self.assertIn("pairwise", report["baseline"])
        self.assertIn("pairwise", report["new"])
        self.assertLess(report["new"]["average"], report["baseline"]["average"])

    def test_engine_has_no_company_slug_special_case(self):
        source = Path(__file__).parents[1] / "src/lp_engine/production_generation.py"
        text = source.read_text(encoding="utf-8")
        for slug in ("maylynn_paint", "nagi_no_mirai", "watashi_no_daidokoro"):
            self.assertNotIn(slug, text)

    def test_two_synthetic_truths_generate_distinct_genomes_without_company_branch(self):
        base = json.loads(FIXTURE.read_text(encoding="utf-8"))
        genomes = []
        for company, industry, goal in (("North Fork Cycles", "自転車修理", "consultation"), ("Quiet Seed Studio", "音楽教室", "application")):
            raw = dict(base)
            raw["company_id"] = company.lower().replace(" ", "-")
            raw["company"] = {**base["company"], "company_name": company, "industry": industry, "service_category": industry, "company_truth": f"{industry}の相談を地域で受け付ける。"}
            raw["conversion_goal"] = goal
            with tempfile.TemporaryDirectory() as directory:
                result = run_generation(raw, Path(directory) / "out", mode="research", generation_id="synthetic")
                genomes.append(result.stage_outputs["creative_genome"])
        self.assertNotEqual(genomes[0]["composition_logic"], genomes[1]["composition_logic"])

    def test_narrative_architecture_has_arc_purposes_and_distinct_grammar(self):
        raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            result = run_generation(raw, Path(directory) / "out", generation_id="narrative-test")
        architecture = result.stage_outputs["narrative_architecture"]
        self.assertEqual(len(architecture["narrative_arc"]), 5)
        self.assertEqual(len(architecture["section_purposes"]), 5)
        gates = narrative_gates(architecture, result.stage_outputs["creative_genome"])
        self.assertEqual(gates["generic_heading_gate"]["status"], "PASS")
        self.assertEqual(gates["renderer_grammar_diversity_gate"]["status"], "PASS")
        self.assertEqual(gates["cta_delta_gate"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
