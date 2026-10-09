"""Synthetic tests; no private theme source or company data is vendored here."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from lp_engine.pilot_authoring import AuthoringError, build_theme_design_brief
from lp_engine.pilot_theme_selection import (
    ThemeSelectionError,
    build_theme_recommendations,
    validate_theme_recommendations,
)
from test_pilot_authoring import synthetic_authoring, synthetic_intake


def synthetic_contract():
    # Authored fixture descriptions, independent of the external LP54 source.
    choices = (
        ("landscape", "still", "calm", "serif", "whitespace"),
        ("landscape", "friendly", "friendly", "circles", "warm"),
        ("landscape", "precise", "precise", "grid", "panorama"),
        ("painting", "gentle", "gentle", "round", "pastel"),
        ("painting", "technical", "technical", "angular", "contrast"),
        ("painting", "refined", "refined", "fine", "minimal"),
        ("bar", "evening", "quiet", "navy", "copper"),
        ("bar", "tea", "tea", "paper", "vertical"),
        ("bar", "gather", "social", "bold", "overlap"),
    )
    return [{"id": f"synthetic-{industry}-{name}", "industry": industry,
             "label": "Synthetic " + name, "fit": "For an expressly " + first + " direction.",
             "description": "An authored fixture using " + second + " visual treatment.",
             "designMoves": ["Use " + third + " as the compositional exercise."],
             "pick": {"hero": 1}, "tokens": {"private_unused_test_note": "not a ranking source"}}
            for industry, name, first, second, third in choices]


class PilotThemeSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.contract_path = Path(self.temp.name) / "synthetic_theme_contract.json"
        self.contract = synthetic_contract()
        self.pin = self.save_contract()

    def save_contract(self, contract=None):
        if contract is None:
            contract = self.contract
        raw = (json.dumps(contract, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.contract_path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def brief(self, industry="landscape", keywords=None):
        intake = synthetic_intake(industry)
        authoring = synthetic_authoring(intake)
        authoring["fields"][0]["value"] = industry + " synthetic exercise"
        authoring["fields"][20]["value"] = {
            "keywords": keywords if keywords is not None else ["calm", "serif"],
            "target_impression": "An explicitly authored direction for this synthetic comparison.",
            "reason": "Test the direction assigned to this case, without a production default.",
            "usage_scope": "P14 design direction",
        }
        return build_theme_design_brief(intake, authoring)

    def recommend(self, brief=None, pin=None):
        return build_theme_recommendations(
            self.brief() if brief is None else brief,
            theme_contract_path=self.contract_path,
            expected_theme_contract_sha256=self.pin if pin is None else pin,
        )

    def validate(self, packet, brief):
        validate_theme_recommendations(packet, brief=brief, theme_contract_path=self.contract_path,
                                       expected_theme_contract_sha256=self.pin)

    def test_same_industry_different_business_directions_change_leading_candidate(self):
        cases = (
            ("landscape", ["calm", "serif"], "still"),
            ("landscape", ["friendly", "circles"], "friendly"),
            ("landscape", ["precise", "panorama"], "precise"),
            ("painting", ["gentle", "pastel"], "gentle"),
            ("painting", ["technical", "angular"], "technical"),
            ("painting", ["refined", "minimal"], "refined"),
            ("bar", ["quiet", "copper"], "evening"),
            ("bar", ["tea", "vertical"], "tea"),
            ("bar", ["social", "overlap"], "gather"),
        )
        for industry, keywords, suffix in cases:
            with self.subTest(industry=industry, direction=keywords):
                packet = self.recommend(self.brief(industry, keywords))
                self.assertEqual(packet["decision"]["status"], "CANDIDATE_FOR_REVIEW")
                self.assertEqual(packet["decision"]["leading_theme_ids"], [f"synthetic-{industry}-{suffix}"])
                self.assertEqual(packet["candidates"][0]["matched_keyword_count"], 2)
                self.assertEqual(len(packet["candidates"]), 3)
                self.assertEqual({candidate["industry"] for candidate in packet["candidates"]}, {industry})
                self.assertIsNone(packet["decision"]["selected_theme_id"])

    def test_every_reason_resolves_to_exact_keyword_and_pinned_source_text(self):
        brief = self.brief()
        packet = self.recommend(brief)
        self.validate(packet, brief)
        self.assertEqual(packet["theme_contract"]["sha256"], self.pin)
        for candidate in packet["candidates"]:
            for match in candidate["matches"]:
                self.assertEqual(match["keyword"], brief["design_reference"]["keywords"][match["keyword_index"]])
                for source in match["source_matches"]:
                    value = self.contract
                    for component in source["json_pointer"].strip("/").split("/"):
                        value = value[int(component)] if isinstance(value, list) else value[component]
                    self.assertEqual(source["text"], value)
                    self.assertEqual(source["text_sha256"], hashlib.sha256(value.encode("utf-8")).hexdigest())
                    span = source["normalized_span"]
                    self.assertEqual(value.casefold()[span["start"]:span["end"]], match["normalized_keyword"])

    def test_no_keyword_overlap_returns_judgment_without_an_industry_default(self):
        packet = self.recommend(self.brief(keywords=["direction-absent-from-the-source"]))
        self.assertEqual(packet["decision"]["reason_code"], "NO_LITERAL_DIRECTION_OVERLAP")
        self.assertEqual(packet["decision"]["status"], "JUDGMENT_REQUIRED")
        self.assertEqual(packet["decision"]["leading_theme_ids"], [])
        self.assertIsNone(packet["decision"]["selected_theme_id"])
        self.assertTrue(all(candidate["rank"] is None for candidate in packet["candidates"]))

    def test_equal_evidence_keeps_ties_instead_of_using_source_order_as_a_winner(self):
        for theme in self.contract[:3]:
            theme["fit"] += " CommonDirection."
        self.pin = self.save_contract()
        brief = self.brief(keywords=["CommonDirection"])
        first = self.recommend(brief)
        self.contract.reverse()
        self.pin = self.save_contract()
        second = self.recommend(brief)
        self.assertEqual(first["decision"]["reason_code"], "TOP_MATCH_COUNT_TIED")
        self.assertEqual(second["decision"]["status"], "JUDGMENT_REQUIRED")
        self.assertEqual(set(first["decision"]["leading_theme_ids"]), set(second["decision"]["leading_theme_ids"]))
        self.assertEqual({candidate["rank"] for candidate in first["candidates"]}, {1})
        self.assertIsNone(second["decision"]["selected_theme_id"])

    def test_repeated_or_normalization_equivalent_keywords_do_not_inflate_counts(self):
        packet = self.recommend(self.brief(keywords=["SERIF", "ｓｅｒｉｆ", " serif "]))
        best = packet["candidates"][0]
        self.assertEqual(best["matched_keyword_count"], 1)
        self.assertEqual(len(best["matches"]), 3)
        self.assertFalse(packet["method"]["quality_score_generated"])

    def test_f17_rationale_and_copy_exclusions_remain_context_and_do_not_change_preferences(self):
        original = self.brief()
        baseline = self.recommend(original)
        authoring = deepcopy(original["authoring_snapshot"])
        authoring["fields"][16]["value"] = {"issue": "friendly circles warm; this is a problem statement, not a preferred style"}
        authoring["fields"][20]["value"]["reason"] = "friendly circles warm appear in prior observations; do not infer a new direction"
        authoring["fields"][21]["value"] = {"expression": ["calm", "serif"], "reason": "Synthetic copy restrictions, not design prohibitions"}
        changed = build_theme_design_brief(original["input_handoff"]["intake_snapshot"], authoring)
        packet = self.recommend(changed)
        self.assertEqual(packet["candidates"], baseline["candidates"])
        self.assertEqual(packet["brief_snapshot"]["design_reference"]["website_problem_record"], authoring["fields"][16])
        self.assertEqual(packet["brief_snapshot"]["fields_by_key"]["avoid_keywords"], authoring["fields"][21])

    def test_fact_hypothesis_wrappers_permissions_and_input_objects_are_preserved(self):
        brief = self.brief()
        authoring = deepcopy(brief["authoring_snapshot"])
        authoring["fields"][20].update(classification="FACT", evidence_ids=["SYNTHETIC-OWNER-DIRECTION"],
                                      publication_policy="INTERNAL_ONLY")
        authoring["evidence_registry"] = {"SYNTHETIC-OWNER-DIRECTION": {"value": "Explicit synthetic owner preference", "current_status": "AUTHOR_RECORDED"}}
        brief = build_theme_design_brief(brief["input_handoff"]["intake_snapshot"], authoring)
        before = deepcopy(brief)
        packet = self.recommend(brief)
        self.assertEqual(packet["brief_snapshot"], before)
        self.assertEqual(brief, before)
        self.assertEqual(packet["brief_snapshot"]["fields_by_key"]["direction_keywords"]["classification"], "FACT")
        self.assertEqual(packet["brief_snapshot"]["status"]["p01_stage_completion"], "NOT_ASSERTED")
        self.assertEqual(packet["status"]["facts_verified_by_adapter"], 0)
        self.assertFalse(packet["status"]["publication_permission_granted"])
        self.assertFalse(packet["status"]["production_eligible"])
        packet["brief_snapshot"]["design_reference"]["keywords"].append("receiver-only edit")
        self.assertEqual(brief, before)

    def test_matching_words_in_other_industries_do_not_enter_the_candidate_set(self):
        packet = self.recommend(self.brief("painting", ["navy", "copper"]))
        self.assertEqual(packet["decision"]["reason_code"], "NO_LITERAL_DIRECTION_OVERLAP")
        self.assertIn("synthetic-bar-evening", {item["theme_id"] for item in packet["excluded_themes"]})
        self.assertTrue(all(item["industry"] == "painting" for item in packet["candidates"]))

    def test_missing_same_industry_source_is_not_replaced_with_another_industry(self):
        self.pin = self.save_contract([theme for theme in self.contract if theme["industry"] == "bar"])
        packet = self.recommend(self.brief("painting", ["navy"]))
        self.assertEqual(packet["candidates"], [])
        self.assertEqual(packet["decision"]["reason_code"], "NO_THEMES_FOR_INDUSTRY")
        self.assertEqual(packet["decision"]["status"], "JUDGMENT_REQUIRED")

    def test_source_pin_is_required_and_modified_bytes_are_rejected(self):
        for pin in (None, "", "not-a-pin", "A" * 64):
            with self.subTest(pin=pin), self.assertRaises(ThemeSelectionError) as caught:
                build_theme_recommendations(self.brief(), theme_contract_path=self.contract_path,
                                            expected_theme_contract_sha256=pin)
            self.assertEqual(caught.exception.code, "SOURCE_PIN_REQUIRED")
        self.contract_path.write_bytes(self.contract_path.read_bytes() + b" ")
        with self.assertRaises(ThemeSelectionError) as caught:
            self.recommend()
        self.assertEqual(caught.exception.code, "CONTRACT_HASH_MISMATCH")

    def test_original_brief_projection_tampering_is_rejected_before_recommendation(self):
        brief = self.brief()
        brief["design_reference"]["keywords"] = ["friendly", "circles"]
        with self.assertRaises(AuthoringError):
            self.recommend(brief)

    def test_saved_ranking_evidence_and_adoption_tampering_cannot_pass_validation(self):
        brief = self.brief()
        original = self.recommend(brief)
        mutations = (
            lambda packet: packet["candidates"][0].update(rank=9),
            lambda packet: packet["candidates"][0]["matches"][0]["source_matches"][0].update(text="invented reason"),
            lambda packet: packet["decision"].update(selected_theme_id="synthetic-landscape-still"),
            lambda packet: packet["status"].update(p14_adoption="COMPLETE"),
            lambda packet: packet["brief_snapshot"]["design_reference"].update(keywords=["friendly"]),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = deepcopy(original)
                mutate(changed)
                with self.assertRaises(ThemeSelectionError) as caught:
                    self.validate(changed, brief)
                self.assertEqual(caught.exception.code, "RECOMMENDATION_MISMATCH")

    def test_a_packet_cannot_be_rebound_to_a_different_authored_direction(self):
        packet = self.recommend(self.brief())
        with self.assertRaises(ThemeSelectionError) as caught:
            self.validate(packet, self.brief(keywords=["friendly", "circles"]))
        self.assertEqual(caught.exception.code, "RECOMMENDATION_MISMATCH")

    def test_ambiguous_or_incomplete_contracts_are_rejected(self):
        duplicate = deepcopy(self.contract); duplicate.append(deepcopy(duplicate[0]))
        missing = deepcopy(self.contract); del missing[0]["fit"]
        invalid_industry = deepcopy(self.contract); invalid_industry[0]["industry"] = "unknown-industry"
        for contract in (duplicate, missing, invalid_industry):
            with self.subTest(contract=contract[0]["industry"]):
                self.pin = self.save_contract(contract)
                with self.assertRaises(ThemeSelectionError) as caught:
                    self.recommend()
                self.assertEqual(caught.exception.code, "INVALID_CONTRACT")
        for raw, code in ((b'[{"id":"first","id":"second"}]', "AMBIGUOUS_CONTRACT"),
                          (b'[{"weight":NaN}]', "INVALID_CONTRACT")):
            with self.subTest(raw=raw):
                self.contract_path.write_bytes(raw)
                self.pin = hashlib.sha256(raw).hexdigest()
                with self.assertRaises(ThemeSelectionError) as caught:
                    self.recommend()
                self.assertEqual(caught.exception.code, code)


if __name__ == "__main__":
    unittest.main()
