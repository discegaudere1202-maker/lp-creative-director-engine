import copy
import unittest
from pathlib import Path
from scripts.validate_phase2_1_gold import ROOT, lines, validate

class GoldEvidenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes={x["scene_evidence_id"]:x for x in lines(ROOT/"data/creative_mechanism_phase2_1_gold_scene_evidence.jsonl")}
        cls.mechs=lines(ROOT/"data/creative_mechanism_phase2_1_gold_mechanisms.jsonl")

    def test_gold_coverage(self):
        self.assertEqual(validate()["references"],20)

    def test_not_observed_cannot_source_mechanism(self):
        for m in self.mechs:
            for source in m["source_scene_evidence_ids"]:
                self.assertEqual(self.scenes[source]["observation_state"],"OBSERVED")

    def test_counts_are_derived(self):
        for m in self.mechs:
            self.assertEqual(m["evidence_count"],len(m["source_scene_evidence_ids"]))

    def test_independence_unknown_is_not_one(self):
        for m in self.mechs:
            self.assertEqual(m["unique_agency_count"],"UNKNOWN")
            self.assertEqual(m["unique_campaign_count"],"UNKNOWN")

    def test_temporary_capture_blocks_strong(self):
        import csv
        with (ROOT/"data/creative_mechanism_phase2_1_gold_references.csv").open(newline="",encoding="utf-8") as fh:
            rows=list(csv.DictReader(fh))
        self.assertTrue(all(x["strong_hold_reject"] == "HOLD" for x in rows))

    def test_both_viewports_exist(self):
        for ref in {x["reference_id"] for x in self.scenes.values()}:
            self.assertIn(f"GOLD-{ref}-DESKTOP-HERO",self.scenes)
            self.assertIn(f"GOLD-{ref}-MOBILE-HERO",self.scenes)

    def test_final_scores_recompute_and_do_not_promote(self):
        result=validate()
        self.assertEqual(result["final_scored"],20)
        scores=lines(ROOT/"data/creative_mechanism_phase2_1_gold_scores.jsonl")
        self.assertTrue(all(not x["promotion_allowed"] for x in scores))

if __name__ == "__main__": unittest.main()
