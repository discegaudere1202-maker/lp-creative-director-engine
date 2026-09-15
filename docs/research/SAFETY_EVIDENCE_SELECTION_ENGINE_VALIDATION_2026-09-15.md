# Safety / Evidence Selection Engine Validation

更新日: 2026-09-15

## 判定

Safety / Integrity層は、実装・テスト済み。Trust Optimizationの自動生成は未接続。今回の出力は構造化Safety Reviewであり、実CVRや因果効果を証明するものではない。

## Pre-flight

- GitHub repository read / branch / commit / file read: PASS
- GitHub Actions run / job / artifact read: PASS
- GitHub Contents write: PASS（Safety Schemaを最初の可逆な実作業コミットとして確認）
- 公式Web参照: PASS（森人、有限会社シーベ）
- 外部アプリ: 今回は不要。未接続アプリに依存していない
- LATE_APPROVAL_RISK: GitHub pushごとにActionsが自動起動するが、取得・確認権限は確認済み

## Implemented boundary

Engineが行うのは、Conversion GoalとCustomer Objectionに対するVerified Evidenceの選択、Provenance検査、画像等のRights検査、Placement候補提示、Missing検出、HEARING_REQUIRED routingである。

既存研究Ledgerの `id/source_url/verified/strength/placement` 形式は、推測で補完せずUNKNOWNを保持するcanonical adapterでSafety Recordへ正規化する。

Engineは、未検証の安心コピー、保証、人物・実績の推測、条件付きClaimの拡張、権利不明画像のProduction承認を行わない。

`approved_claims` は生成コピーではなく、EligibleなEvidence LedgerのVerified Claim原文一覧である。

## Five-case dry run

| Case | Goal | Primary objections | Eligible | Blocked claims | Hearing | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| P02 | consultation | ACCOUNTABILITY / PROCESS / NEXT / DECISION | 2 | 2 | 2 | BLOCKED |
| P09 | quote_request | ACCOUNTABILITY / PROCESS / NEXT / COST | 3 | 1 | 1 | BLOCKED |
| P10 | consultation | ACCOUNTABILITY / PROCESS / DECISION / CONTINUITY | 4 | 2 | 2 | BLOCKED |
| MORIBITO | visit | ABILITY / PROCESS / NEXT / COST | 3 | 1 | 1 | BLOCKED |
| INDEPENDENT_KOKORO_SEITAI | reservation | ACCOUNTABILITY / PROCESS / NEXT / COST | 2 | 1 | 1 | BLOCKED |

森人のDry Runでは、公式サイトで確認できない返信時間を要求Claimにしたため、危険ClaimとしてBlocked、必要情報をHearingへ回した。これは「来店できる」事実と「予約後の応答保証」を混同しないための境界である。

独立ケースのこころ整体院グループでは、公式サイト上の施術工程と料金条件をVerifiedとして選択できた一方、予約後の返信時間は確認できないためHearingへ回した。公式サイトには、初回の分析・施術の流れ、料金の院別差、無理な勧誘をしない旨、返金条件が併記されているが、Safety層はそれらを治療効果や予約後の保証へ拡張していない。

P02/P09/P10のBlockedは、秘密厳守、完全無料、返信時間、無理な勧誘等を一次確認なしに出さないことを表す。これはLP全体の生成失敗ではなく、危険Claimの承認停止と不足情報のHearing化である。

## Adversarial result

8ケース、8 PASS。危険なcustomer-facing approvedは0件。

- 「たぶん勧誘しません」: BLOCKED
- 口コミだけの秘密厳守: BLOCKED
- 根拠のない返信時間: BLOCKED
- 権利不明の人物写真: Production not approved
- 検証不明のSNS実績数字: HEARING_REQUIRED
- 条件付き無料から完全無料への拡張: BLOCKED
- 出典なしのお客様満足度: BLOCKED
- 出典なしの地域No.1: BLOCKED

## Findings

### Objection first

EvidenceはEvidence Typeの有無で一括表示しない。一次診断したObjectionにtargetが一致するEvidenceだけをEligibleにする。能力の実績は費用不安の説明にはならず、人物名は担当確約を意味しない。

### Safety is cross-domain; optimization is conditional

P02（相談）、P09（見積）、P10（相談）、森人（来店）の4ケースで、Provenance・Verification・Rights・Missingの同じSafety境界を適用できた。一方、Trustを最適化するEvidenceの優先順位は、相談型・見積型・来店型で異なる。よって `OBJECTION_FIRST_SELECTION` は `OBSERVED_CROSS_DOMAIN_CONDITIONAL` に留め、Trust copyの自動最適化は昇格しない。

### WHO / HOW / NEXT

形式を固定するのではなく、Accountability / Process / Nextの不安が実際にPrimaryである場合に、それぞれのEvidenceを接続する。森人では職人の名前だけでなく、実物に触れる来店体験と予算内オーダーが来店・購入の判断材料になった。P09では価格と仕様がCostを直接処理し、ワンストップ工程がProcess / Accountabilityを処理した。

## Rule status

| Rule | Status | Boundary |
| --- | --- | --- |
| UNKNOWN_BOUNDARY | REPLICATED | Safety / Integrityとして実装可能 |
| PROVENANCE_REQUIRED | REPLICATED | Safety / Integrityとして実装可能 |
| MISSING_EVIDENCE_GATE | REPLICATED | 不足はClaim生成ではなくHearingへ |
| RIGHTS_SAFETY | REPLICATED | CLEARED / NOT_APPLICABLEのみProduction eligible |
| MOBILE_ACTION_BUDGET | REPLICATED | 既存QAで維持、今回のSafety層は画面生成を変更しない |
| OBJECTION_FIRST_SELECTION | OBSERVED_CROSS_DOMAIN_CONDITIONAL | Trust最適化の自動化は未承認 |
| OBJECTION_COVERAGE_SEQUENCE | REPLICATED_CONDITIONAL | Conversion Goal / Objection構造ごとに再確認 |
| ACCOUNTABILITY_WITH_PROCESS | CONDITIONAL | WHO単独を一般化しない |
| WHO_HOW_NEXT_BRIDGE | CONDITIONAL | 固定レイアウトではなくObjection接続として利用 |

ENGINE_READY_CANDIDATEはSafety / Integrityに限って候補化可能。Trust Optimization Ruleは未昇格。

## Hearing Schema

- UNIVERSAL_REQUIRED: responsible_person_or_team, service_process, post_click_flow
- DOMAIN_REQUIRED: ability_proof, fee_conditions, continuity_or_aftercare
- CONDITIONAL_REQUIRED: decision_boundary, risk_and_privacy_policy
- HIGH_VALUE: verification_date_and_source, rights_permission_for_visual_assets
- OPTIONAL: owner_portrait, testimonial_or_result_case

Hearing Appは未実装。今回保存したのは、ObjectionをTriggerにしたSchemaのみ。

## False positive / false negative

これは実運用の精度測定ではなく、プログラム化したSafetyケースである。False Positive側では、異なるObjectionのEvidence、条件付き無料、SNSのみの数字、権利不明画像を通さない。False Negativeを重く扱い、今後は「VerifiedだがClaimの強さが違う」ケースをさらに増やす。現時点の過剰Hearingは、Safety優先の意図的な保守設定であり、実データを集めた後にのみ緩和を検討する。

## Overfitting check

P02/P10の相談型構造を、P09の見積型、森人の来店型、独立ケースの予約型へそのまま移植していない。P09はPrice / Specification / Scope、森人はMaterial / Place Experience / Budget Boundary、独立ケースはTreatment Process / Clinic-specific Cost / Risk Policyを中心に選択した。固定CTA、固定WHO/HOW/NEXT、Benchmark固有UIや文言はSafety判断に使用していない。

## Sources used for fixtures

- https://www.mahora-sr.jp/page_001.html
- https://www.mahora-sr.jp/page_009.html
- https://www.tsubudateru.com/
- https://www.tsubudateru.com/lp
- https://www.tsubudateru.com/service
- https://www.tsubudateru.com/member/ayano-miyahara
- https://sign-ya.jp/
- https://sign-ya.jp/menu/
- https://moribito.jp/

## Next phase decision

最優先は **B｜Safety / Evidence Selection Engine実装の継続統合**。理由は、Provenance・UNKNOWN・Rights・Hearing routingが異業種4ケースで同じ安全境界として再現し、Trust最適化より実装確度が高いからである。次は既存のEvidence Ledger形式をcanonical adapterへ統合し、Production EngineへのSafety-only接続と回帰テストを行う。Trust自動最適化・Hearing UI・Golden Sample 03はまだ進めない。


## Safety-only pipeline integration

The validated safety boundary is now available as an optional gate in the existing creative pipeline:

- Python API: `run_pipeline(..., evidence_safety=spec)`
- CLI: `lp-engine <project-spec> --evidence-safety <safety-input.json>`
- Gate: `EvidenceSafetyGate`
- `PASS` remains `PASS`; `HEARING_REQUIRED` maps to pipeline `HOLD`; `BLOCKED` and `INVALID_INPUT` map to pipeline `FAIL`.
- Without the optional input, the existing Creative Direction pipeline is unchanged.

This is a safety integration, not Trust Optimization automation. The gate returns verified claims and evidence records only; it does not write copy, infer reassurance, expand conditional claims, or approve unknown-rights visuals.

The wiring was covered by three pipeline tests: verified evidence passes, a blocked confidentiality request fails without approved copy and emits hearing data, and the legacy pipeline remains unchanged without safety input. The full repository QA remains the SSOT for final regression.


## Research-only versus production usage

The Safety Gate distinguishes a verified research candidate from customer-facing production evidence. A record with `usage_status=RESEARCH_ONLY` may remain visible in research/dry-run outputs, but the production pipeline requires `ELIGIBLE` or `PRODUCTION_ELIGIBLE`. Unknown or unconfirmed usage therefore routes to permission review/hearing; it is never silently promoted by a verified claim or by `NOT_APPLICABLE` rights alone.
