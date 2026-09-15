# Cross-domain Evidence Validation — 2026-09-15

## Scope

これはP02/P10で得た `Customer Objection → Evidence Selection` を、異なる業種・異なるConversion Goalへ移した検証である。評価は匿名化した画面に対する内部のstructured review rolesであり、独立第三者の人間評価でも、実CVRの因果検証でもない。

CaptureはRun `34981119495`、Artifact `10400574684`（`cross-domain-validation-capture-v1`）、digest `sha256:51428c3bc15c9b1f06eeb9b1151fa9b05153e8f338f0d732fdfd33f2dcc91214`。Desktopは1440×1000、Mobileは390×844。9幅runtime QAは320/360/375/390/430/768/1024/1280/1440を対象とする。

## Cases and diagnosis

| Case | Industry | Conversion Goal | Primary Objections | Selected Evidence |
|---|---|---|---|---|
| CROSS_P09_SIGNAGE | 建設・看板制作 | 見積相談 | O2 ACCOUNTABILITY / O3 PROCESS / O4 NEXT | デザイン・製作・施工までワンストップで対応 |
| CROSS_MORIBITO_VISIT | 手作り家具・店舗来店 | 実物確認を伴う来店・購入相談 | O1 ABILITY / O3 PROCESS / O4 NEXT / O6 COST | 店内展示の実物に触れられる＋予算内でのオーダーメイド |

P09は既に `400×300mm / 4,158円（税込）` によるCOST/DECISION supportが強いため、価格Evidenceを増やさず、責任主体と工程連続性だけをCTA Zoneへ追加した。森人は新PrototypeやGolden Sample 03ではなく、既存Golden SampleのCompany Truthを使った検証ケースであり、公式画像の再利用はしていない。

## Evidence provenance

- P09: [公式トップ](https://sign-ya.jp/) と [公式価格表](https://sign-ya.jp/menu/)。公式サイトで、企画・デザイン・製作・施工の一貫対応、相談から完成まで一つの窓口、工程の説明を確認した。
- 森人: [公式サイト](https://moribito.jp/)。楠の木の香り、一枚板、店内展示、実物に触れる案内、オーダーメイド、できるだけ予算内で制作、住所・営業時間・電話を確認した。
- 森人の公式写真URLはAsset Ledgerに存在するが、権利移転を推定できないため今回のVariantでは不使用。
- 予約方法、返信時間、守秘、保証、キャンセル、契約義務なし、無理な勧誘をしない旨は公式一次情報で今回確認できず、UNKNOWNとした。

## Baseline vs evidence-selected

Win Rateは `wins + 0.5 × ties` を比較数で割った方向スコアである。

| Case | Overall | Trust | Conversion Intent | Creative role | Business role | Mobile |
|---|---:|---:|---:|---:|---:|---:|
| P09 selected vs baseline | 0.5000 | 0.5000 | 0.2500 | 0.5000 | 0.7500 | 0.0000 |
| 森人 selected vs baseline | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

P09ではDesktopのTrust/Conversionは動いたが、追加EvidenceがMobileの最初の意思決定フレームに入らず、全体Win Rateは上がらなかった。これはEvidence選択が正しくてもPlacementとAction Budgetを外すと成果へ接続しないことを示す。既存P09のページ自体は変更せず、Variantは研究用である。

森人では、Heroの「香りまで、家具にする。」を変更せず、CTA Zoneに「触れて相談できる」「予算内でオーダーメイド」という来店理由と判断境界を追加した。画面全体を情報化せず、Company Truth → 来店体験 → 購入相談の接続が明瞭になった。ただし、予約フローや返信期待を埋めた結果ではないため、来店予約CVRの証明ではない。

## Findings

### Reproduced / conditional

- `OBJECTION_FIRST_SELECTION`: P02/P10以外の2ケースでも、Evidenceを先に並べるのではなく、Conversionを止める不安から選ぶことが説明可能。ただし「選んだEvidenceを最初のAction frameへ届ける」条件付きで、statusは `OBSERVED_CROSS_DOMAIN_CONDITIONAL` とする。
- `OBJECTION_COVERAGE_SEQUENCE`: P09はACCOUNTABILITY/PROCESSを補うとTrustが動き、森人はPROCESS/NEXT/COSTを補うと全軸が同方向に動いた。異なる業種で同じ証拠を使うのではなく、Objection coverageを組むRuleとして `REPLICATED_CONDITIONAL` とする。
- `ACCOUNTABILITY_WITH_PROCESS`: P09で有効方向。ただし、人物名を足すRuleではなく、責任主体と工程の一貫性を同じ判断箇所へ接続する条件付きRuleである。森人の職人名は今回は主Deltaにしなかったため、人物単独の一般化はしない。
- `WHO_HOW_NEXT_BRIDGE`: 森人ではWHOを無理に前面化せず、素材・触れる・相談という `WHAT / EXPERIENCE / NEXT` の橋が自然だった。したがって汎用の順序固定Ruleには昇格しない。

### Rule failures / non-generalization

- 「人物Evidenceは必ずHero」は不成立。森人ではMaterial/Sensory Heroを守り、Place/Process evidenceをCTA Zoneへ置いた。
- 「E5が常に最強」は未検証。P09の価格E5は既に十分で、今回効いたのはE3の責任・工程Evidenceだった。
- 「CTA直前に足せば効く」は不成立。P09 mobileでEvidenceが見えず、Action Zoneの下端も余裕がない。
- `WHO_HOW_NEXT` の語順を全業種へテンプレート化しない。見積型は責任主体→工程、来店型は素材の実物→触れる→相談という因果に変わる。

## Objection → Evidence mapping update

| Objection | Preferred evidence | Placement condition | Fallback |
|---|---|---|---|
| O1 ABILITY | qualification / verified metric / material or product proof | Hero only when it explains the offer; otherwise early proof | HEARING_REQUIRED |
| O2 ACCOUNTABILITY | owner/team identity + responsibility scope | Middle or CTA Zone, adjacent to process; not name alone | HEARING_REQUIRED |
| O3 PROCESS | service process / production steps / touch-and-choose experience | Where the visitor asks “what happens in this service?” | HEARING_REQUIRED |
| O4 NEXT | post-click flow / visit reason / next step | Before or inside CTA Zone, visible in first action frame | HEARING_REQUIRED |
| O5 DECISION | decision boundary / estimate conditions / budget boundary | Immediately around the decision, not decorative footer | HEARING_REQUIRED |
| O6 COST | published price / fee condition / budget boundary | Before CTA or beside the product/offer; do not add generic price cards | HEARING_REQUIRED |
| O7 RISK | verified policy, privacy, cancellation or scope boundary | Before CTA only when verified | UNKNOWN + HEARING_REQUIRED |
| O8 CONTINUITY | continuity policy / aftercare / support scope | After-action expectation when verified | HEARING_REQUIRED |

Evidence Strength remains orthogonal to objection: E1 Weak, E2 Specific, E3 Operational, E4 Risk Reducing, E5 Decision Enabling. Placement is also orthogonal. The P09 result specifically shows that an E3 fact can matter more than adding another E5 price fact when the missing objection is responsibility/process.

## Hearing schema

### UNIVERSAL_REQUIRED

`conversion_goal`, `primary_objections`, `responsible_person_or_team`, `service_scope_or_process`, `next_action_or_post_click_flow`, `fee_or_price_condition`, `source_url_and_verification_status`.

### DOMAIN_REQUIRED

- 見積・施工: material/spec, installation/site conditions, quote triggers, responsibility boundary, production-to-installation scope.
- 来店・予約: who serves, visit/appointment method, duration, price/fee conditions, what happens after arrival, risk/cancellation boundary.
- 相談・伴走: named role, consultation process, business model, continuity, decision boundary.

### HIGH_VALUE

`response_expectation`, `verified_case_or_testimonial`, `rights-cleared owner portrait`, `customer-selectable options`, `privacy/confidentiality policy`。

### OPTIONAL

`additional metrics`, `office/place photo`, `owner quote`, `detailed result case`。追加はObjectionが残る場合だけとする。

## Engine readiness decision

Safety / Integrity rules (`UNKNOWN_BOUNDARY`, `PROVENANCE_REQUIRED`, `MOBILE_ACTION_BUDGET`, `MISSING_EVIDENCE_GATE`) は、今回も異業種で適用可能であり、先行実装の候補としては十分。ただし今回の指示範囲では実装しない。

Trust Optimization rulesは、P02/P10と今回の2ケースで方向再現を確認したが、P09 mobileのPlacement failure、森人のdomain-specific experience bridge、structured reviewの小標本が残る。したがって `ENGINE_READY_CANDIDATE` には昇格しない。現在のschema candidateに、case/objection/strength/placement/fallbackのフィールドを追加する段階が妥当である。

## Overfitting check

P09は既存ページをほぼそのまま使い、追加は公式の一貫対応事実1点のみ。森人はP02/P10の見た目やCTA文言をコピーせず、楠・触れる・予算内という公式Company TruthからMaterial/Sensory表現を維持した。2ケースでCTA Zoneが同じ見た目になっていないため、Benchmark-specific optimizationではない。一方、森人は新規LPではなく既存Golden Sample由来の検証ケースであり、一般化の強さは限定的と記録する。

## Decision

今回の最優先次工程は **B｜Safety / Evidence Selection Engine実装**。理由は、Trustの最適化Ruleを全面実装できるほどの因果確定ではないが、Evidence provenance、UNKNOWN境界、Objection-first schema、Placement、HEARING_REQUIREDという安全な判断の骨格は異業種で再利用可能と確認できたためである。Trust optimizationの自動コピー生成はまだ実装せず、Safetyとledger/schemaの薄い先行実装に限定する。
