"""Synthetic checks of the source -> authored P01 -> design-reference boundary."""
from copy import deepcopy
import unittest

from lp_engine.pilot_authoring import (
    AUTHORING_SCHEMA,
    AuthoringError,
    P01_FIELDS,
    build_theme_design_brief,
    validate_theme_design_brief,
)
from lp_engine.pilot_intake import INPUT_SCHEMA, adapt_normalized_lead


def synthetic_intake(industry="painting"):
    return adapt_normalized_lead({
        "schema_version": INPUT_SCHEMA,
        "source_record_id": "SYNTHETIC-" + industry,
        "industry": industry,
        "identity": {"business_name": "合成テスト事業者"},
        "location": {"prefecture": "合成テスト地域"},
        "legacy_assertions": {"identity_status": "VERIFIED", "web_status": "NO_WEB"},
        "provenance": {"source_id": "synthetic-source", "source_locator": "synthetic/input.json"},
    })


def synthetic_authoring(intake):
    # Every value is explicitly authored for this fictional exercise. The
    # production adapter has no equivalent industry/default-value generator.
    values = {
        "industry": "塗装を題材にした合成テストの事業領域",
        "service_category": [{"service_name": "外壁塗装の相談", "overview": "塗り替えの検討材料を整理", "target": "住宅所有者", "classification": "HYPOTHESIS"}],
        "primary_service": {"current_main_service": {"name": "外壁塗装", "basis_type": "HYPOTHESIS"},
            "future_priority_service": {"name": "状態に応じた塗り替え相談", "reason": "比較検討時の入口を具体化"},
            "lp_priority_candidate": {"name": "初回の外壁相談", "reason": "工事の要否を整理しやすい", "decision_status": "CANDIDATE"},
            "selection_reason": "P02の相談目的との照合用候補", "service_scope": {"included_services": ["外壁塗装の相談"]}, "target_customer": "塗り替えを検討する住宅所有者"},
        "secondary_services": [{"service_name": "色選びの検討", "role": "外壁相談の補足", "publication_policy": "INTERNAL_ONLY"}],
        "service_area": {"real_area": "合成テストの拠点周辺を仮の検討範囲とする", "public_area": "地域範囲は今回表示しない"},
        "business_model": {"revenue_type": "工事ごとの受注を仮定", "customer_type": "住宅所有者", "delivery_flow": "相談後に条件を整理する想定"},
        "estimated_price_band": {"amount": "30万円を内部構成検討の仮額に置く", "tax_type": "税別として比較検討", "unit": "仮の1工事", "included_content": "仮に外壁の塗り替え", "variation_condition": "広さと状態による変動を想定", "publication_policy": "会社の実価格として表示しない"},
        "purchase_type": {"purchase_pattern": "単発工事を想定", "comparison_period": "家族と条件整理後に比較する想定", "decision_maker": "所有者と同居家族"},
        "current_web_condition": "元資料のNO_WEBは過去記載として保全し、現時点のWeb有無は観測せず、独立した相談説明ページを提案する初期仮説。",
        "primary_end_user": {"user": "住宅所有者", "situation": "劣化の兆候を見て塗り替え時期を考える", "decision_relation": "同居家族と検討", "exclusion": ["DIYだけで解決する予定の方"]},
        "secondary_end_user": {"user": "所有者の家族", "usage_condition": "比較を手伝う場合", "priority": "SECONDARY"},
        "main_situation": {"current_state": "壁の色褪せが気になる", "trigger_period": "住まいの手入れを考える時期", "background": "工事の必要性から判断したい"},
        "main_need": {"need": "塗り替えを検討する条件を理解したい", "priority": "HIGH", "expected_change": "相談で確認する内容を整理できる"},
        "primary_strength": {"strength_candidate": "状態に応じた説明を提案", "customer_benefit": "必要な工事の検討を進めやすい", "comparison_axis": "条件説明のわかりやすさ"},
        "secondary_strengths": [{"strength_candidate": "色を比べる説明を提案", "customer_benefit": "暮らしとの相性を検討できる", "basis": "合成ケースの相談状況に基づく制作案", "confidence": "LOW", "publication_policy": "INTERNAL_ONLY"}],
        "current_marketing_problem": {"current_state": "相談前の判断材料が伝わりにくい可能性", "goal_state": "確認したい点を持って相談できる", "barrier": "依頼時の条件が想像しにくい可能性", "lp_role": "検討順序を説明する"},
        "website_problem": {"observed_issue": "Webを新たに観測した欠陥は主張しない", "impact_hypothesis": "初回相談の説明が意思決定を助けると仮定", "evidence_scope": "今回の合成資料のみ"},
        "lp_opportunity": {"improvement_target": "初回相談の見通しを示す", "user_state_change": "比較条件を整理できる", "expected_role": "相談の判断材料を伝える"},
        "primary_cv": {"business_action": "外壁についての相談", "sample_safety_separation": "NO_REAL_SUBMISSION"},
        "secondary_cv": {"support_action": "検討項目の確認", "role": "相談前の補助"},
        "direction_keywords": {"keywords": ["整然", "明るい", "説明の見通し"], "target_impression": "落ち着いて条件を比べられる印象", "reason": "初回相談前の疑問を整理する合成ケースのため", "usage_scope": "P14 design direction"},
        "avoid_keywords": {"expression": ["地域No.1", "保証された最安値"], "reason": "会社実績や価格優位を証明していないため", "check_target": "P07/P13_FINAL_COPY確認"},
    }
    fields = [{"field_id": fid, "value": values[key], "classification": "HYPOTHESIS",
               "basis": "合成ケースの相談状況から、この項目を内部制作案として設定。実会社の条件・実績ではない。",
               "confidence": "LOW", "publication_policy": "INTERNAL_ONLY", "evidence_ids": []}
              for fid, key in P01_FIELDS.items()]
    return {"schema_version": AUTHORING_SCHEMA, "intake_id": intake["intake_id"],
            "authoring_source": {"source_id": "synthetic-authoring", "source_locator": "synthetic/p01.json"},
            "fields": fields, "evidence_registry": {}}


class PilotAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.intake = synthetic_intake()
        self.authoring = synthetic_authoring(self.intake)

    def test_all_records_keep_original_wrappers_and_decision_boundaries(self):
        before = deepcopy(self.authoring)
        brief = build_theme_design_brief(self.intake, self.authoring)
        validate_theme_design_brief(brief)
        self.assertEqual(brief["authoring_snapshot"], before)
        self.assertEqual(self.authoring, before)
        self.assertEqual(brief["status"]["authored_input"], "ALL_22_SUPPLIED")
        self.assertEqual(brief["status"]["author_classifications"], {"FACT": 0, "HYPOTHESIS": 22})
        self.assertEqual(brief["status"]["p01_stage_completion"], "NOT_ASSERTED")
        self.assertFalse(brief["status"]["production_eligible"])
        self.assertFalse(brief["status"]["publication_permission_granted"])
        self.assertEqual(brief["design_reference"]["keywords"], before["fields"][20]["value"]["keywords"])
        self.assertFalse(brief["design_reference"]["formal_p14_field_binding"])
        self.assertEqual(brief["fields_by_key"]["estimated_price_band"], before["fields"][6])
        candidate = brief["fields_by_key"]["primary_service"]["value"]
        self.assertNotEqual(candidate["current_main_service"]["name"], candidate["lp_priority_candidate"]["name"])
        self.assertEqual(candidate["lp_priority_candidate"]["decision_status"], "CANDIDATE")
        self.assertEqual(brief["input_handoff"]["legacy_assertions"]["identity_status"], "VERIFIED")
        self.assertEqual(brief["input_handoff"]["verified_facts"], [])

    def test_all_pilot_routes_keep_author_direction_without_an_industry_default(self):
        for industry, keywords in (("landscape", ["余白", "静かな時間"]), ("painting", ["整然", "比較しやすい"]), ("bar", ["暗い背景", "夜の余韻"])):
            with self.subTest(industry=industry):
                intake = synthetic_intake(industry)
                authored = synthetic_authoring(intake)
                authored["fields"][0]["value"] = industry + "という架空の事業区分を明示入力"
                authored["fields"][20]["value"]["keywords"] = keywords
                brief = build_theme_design_brief(intake, authored)
                self.assertEqual(brief["industry"]["key"], industry)
                self.assertEqual(brief["design_reference"]["keywords"], keywords)

    def test_missing_duplicate_and_wrong_original_fields_are_rejected(self):
        cases = []
        missing = deepcopy(self.authoring); missing["fields"].pop(10); cases.append(missing)
        duplicate = deepcopy(self.authoring); duplicate["fields"].append(deepcopy(duplicate["fields"][0])); cases.append(duplicate)
        unknown = deepcopy(self.authoring); unknown["fields"][0]["field_id"] = "P01_F99"; cases.append(unknown)
        mismatch = deepcopy(self.authoring); mismatch["fields"][0]["field_key"] = "primary_cv"; cases.append(mismatch)
        for authored in cases:
            with self.subTest(authored=authored["fields"][0]["field_id"]), self.assertRaises(AuthoringError):
                build_theme_design_brief(self.intake, authored)

    def test_placeholders_are_not_completed_authoring(self):
        for value in (None, {}, [], "不明", "未設定", "情報なし", {"need": "UNKNOWN"}, {"need": "具体的な目的", "expected_change": None}):
            with self.subTest(value=value):
                authored = deepcopy(self.authoring)
                authored["fields"][12]["value"] = value
                with self.assertRaises(AuthoringError):
                    build_theme_design_brief(self.intake, authored)

    def test_fact_requires_supplied_evidence_and_does_not_reuse_source_observation(self):
        record = self.authoring["fields"][0]
        record["classification"] = "FACT"
        record["publication_policy"] = "DISPLAY_OK_FACT"
        for refs in ([], ["NOT-SUPPLIED"], [self.intake["source_observations"][0]["observation_id"]]):
            with self.subTest(refs=refs):
                record["evidence_ids"] = refs
                with self.assertRaises(AuthoringError):
                    build_theme_design_brief(self.intake, self.authoring)

    def test_author_classification_and_evidence_are_preserved_without_reverification(self):
        record = self.authoring["fields"][0]
        record.update(classification="FACT", evidence_ids=["SYNTHETIC-E1"], publication_policy="INTERNAL_ONLY")
        evidence = {"fact_id": "SYNTHETIC-E1", "value": record["value"], "source_url": "https://example.test/synthetic-evidence", "current_status": "AUTHOR_RECORDED", "evidence_note": "Synthetic fixture only; not an observed business."}
        self.authoring["evidence_registry"]["SYNTHETIC-E1"] = evidence
        brief = build_theme_design_brief(self.intake, self.authoring)
        self.assertEqual(brief["evidence_registry"]["SYNTHETIC-E1"], evidence)
        self.assertEqual(brief["status"]["author_classifications"], {"FACT": 1, "HYPOTHESIS": 21})
        self.assertEqual(brief["status"]["facts_verified_by_adapter"], 0)
        self.assertEqual(brief["status"]["p01_semantic_quality"], "NOT_RUN")

    def test_known_unconfirmed_evidence_is_not_a_current_fact(self):
        self.authoring["fields"][0].update(classification="FACT", evidence_ids=["E1"])
        for status in ("SOURCE_RECORDED_ONLY", "LEGACY_ASSERTION", "HYPOTHESIS", "NOT_VERIFIED"):
            with self.subTest(status=status):
                self.authoring["evidence_registry"] = {"E1": {"verification_status": status}}
                with self.assertRaises(AuthoringError):
                    build_theme_design_brief(self.intake, self.authoring)

    def test_hypothesis_cannot_assert_public_fact_or_verified_permission(self):
        for key, value in (("publication_policy", "DISPLAY_OK_FACT"), ("verified", True), ("production_evidence_eligible", True)):
            with self.subTest(key=key):
                authored = deepcopy(self.authoring)
                authored["fields"][6][key] = value
                with self.assertRaises(AuthoringError):
                    build_theme_design_brief(self.intake, authored)

    def test_p14_reference_requires_its_known_shape_without_migrating_other_values(self):
        self.authoring["fields"][20]["value"] = "説明として保存されていた方向性"
        with self.assertRaisesRegex(AuthoringError, "P01_F21.value"):
            build_theme_design_brief(self.intake, self.authoring)

    def test_wrong_company_and_altered_intake_are_rejected(self):
        authored = deepcopy(self.authoring); authored["intake_id"] = "another-intake"
        with self.assertRaisesRegex(AuthoringError, "intake_id"):
            build_theme_design_brief(self.intake, authored)
        altered = deepcopy(self.intake); altered["industry"]["key"] = "bar"
        with self.assertRaisesRegex(AuthoringError, "source snapshot"):
            build_theme_design_brief(altered, self.authoring)

    def test_projection_and_permission_tampering_are_detected(self):
        baseline = build_theme_design_brief(self.intake, self.authoring)
        for section, key, value in (("design_reference", "keywords", ["改変された方向"]), ("status", "production_eligible", True), ("status", "p01_stage_completion", "COMPLETE")):
            with self.subTest(key=key):
                altered = deepcopy(baseline); altered[section][key] = value
                with self.assertRaises(AuthoringError):
                    validate_theme_design_brief(altered)
        altered = deepcopy(baseline)
        altered["authoring_snapshot"]["fields"][20]["value"]["reason"] = "後から変更"
        with self.assertRaises(AuthoringError):
            validate_theme_design_brief(altered)


class AuthoredCompositionBoundaryTests(unittest.TestCase):
    """Check context delivery without invoking the separately tested renderer."""

    def setUp(self):
        from lp_engine.pilot_pipeline import build_authored_composition_input
        self.build_input = build_authored_composition_input

    @staticmethod
    def composition(industry):
        # This fixture exercises the context boundary only. Concrete selected
        # IDs, image bytes and renderer field shapes are tested by composition.
        return {"schema_version": "lp54-composition-input/v1",
                "company": {"industry": industry, "name": "合成接続テスト"},
                "selection": {}, "images": {},
                "context": {"existing_notes": ["元の補足情報を保持"]}}

    def test_three_industries_keep_the_original_brief_and_private_hypotheses(self):
        for industry in ("landscape", "painting", "bar"):
            with self.subTest(industry=industry):
                intake = synthetic_intake(industry)
                brief = build_theme_design_brief(intake, synthetic_authoring(intake))
                composition = self.composition(industry)
                before_brief, before_composition = deepcopy(brief), deepcopy(composition)
                payload = self.build_input(brief, composition)
                self.assertEqual(payload["context"]["p01_design_brief"], before_brief)
                self.assertEqual(payload["context"]["existing_notes"], before_composition["context"]["existing_notes"])
                self.assertEqual(brief, before_brief)
                self.assertEqual(composition, before_composition)
                received = payload["context"]["p01_design_brief"]
                self.assertEqual(received["fields_by_key"]["estimated_price_band"]["publication_policy"], "INTERNAL_ONLY")
                self.assertEqual(received["status"]["p01_semantic_quality"], "NOT_RUN")
                self.assertFalse(received["status"]["production_eligible"])
                received["design_reference"]["keywords"].append("受信後だけの変更")
                self.assertEqual(brief, before_brief)

    def test_mismatched_industry_is_rejected(self):
        intake = synthetic_intake("painting")
        brief = build_theme_design_brief(intake, synthetic_authoring(intake))
        with self.assertRaises(AuthoringError):
            self.build_input(brief, self.composition("bar"))

    def test_changed_design_projection_cannot_be_connected(self):
        intake = synthetic_intake()
        brief = build_theme_design_brief(intake, synthetic_authoring(intake))
        brief["design_reference"]["keywords"] = ["作者の原稿と違う選択理由"]
        with self.assertRaises(AuthoringError):
            self.build_input(brief, self.composition("painting"))

    def test_reserved_context_is_rejected_even_for_an_equal_brief(self):
        intake = synthetic_intake()
        brief = build_theme_design_brief(intake, synthetic_authoring(intake))
        for supplied in (None, deepcopy(brief)):
            with self.subTest(supplied=supplied is None):
                composition = self.composition("painting")
                composition["context"]["p01_design_brief"] = supplied
                with self.assertRaises(AuthoringError):
                    self.build_input(brief, composition)


if __name__ == "__main__":
    unittest.main()
