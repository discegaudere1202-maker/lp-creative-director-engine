# Evidence Selection Logic Validation — 2026-09-15

## 結論

Trust改善の起点を「Evidenceの種類」ではなく「行動前のCustomer Objection」に置くschema候補を作成した。P10のsingle-Evidence比較では、Continuityが最もバランスよく、Business ModelがTrustを直接動かし、Accountability単独は部分改善に留まった。P10 Full Enrichedの改善を単一Evidenceへ還元できなかったため、Trust最適化Ruleは `ENGINE_READY_CANDIDATE` に昇格しない。

この結果は、2つのstructured internal Work review rolesによる方向的な比較であり、実CVRまたは統計的因果の証明ではない。

## 実行範囲とProvenance

- Internal blind ablation: Core vs P10 Accountability / Continuity / Business Model、CoreまたはBaseline系統 vs P02 Process / Authority
- External formal validation: P10 Continuity vs `carigaku-career` / `sell-step-career` / `lfu-career`
- Viewport: 1440×1000、390×844。新規5 Variantは9幅QA（320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440）をCIで実行
- Candidate Capture: Run `34974786412` / Artifact `10398639415` / digest `sha256:fcc25d79e93f6e0e24e273ee82d5f920f3dda71ad88d410d3c5b81397ca5a80d`
- Result: `data/evidence_selection_ablation_results_v1.json`
- External result: `data/formal_tournament_results/P10_CONTINUITY_formal_blind_tournament_v1.json`
- Reviewer-visible bundleはopaque IDとLEFT/RIGHTのみ。Identity mappingはbundle外に分離。Reviewerは独立第三者ではなく、Creative / Art Direction と Business Owner / Conversion のstructured roles。

## Customer Objection Model

| ID | 顧客の不安 | 優先Evidence |
| --- | --- | --- |
| O1 ABILITY | 本当にできるのか | VERIFIED_METRIC / EXPERIENCE / QUALIFICATION / RESULT_CASE |
| O2 ACCOUNTABILITY | 誰が責任を持つのか | OWNER_IDENTITY / TEAM_IDENTITY |
| O3 PROCESS | 何をしてくれるのか | SERVICE_PROCESS / POST_CLICK_FLOW / SCOPE_BOUNDARY |
| O4 NEXT | 問い合わせ後に何が起きるのか | POST_CLICK_FLOW / RESPONSE_EXPECTATION / CONSULTATION_METHOD |
| O5 DECISION | いつ決断しなければならないのか | DECISION_BOUNDARY / SCOPE_BOUNDARY |
| O6 COST | 何に、いつ費用が発生するのか | PRICE / FEE_CONDITION / BUSINESS_MODEL |
| O7 RISK | 相談で不利益が起きないか | RISK_POLICY / PRIVACY_POLICY / SCOPE_BOUNDARY |
| O8 CONTINUITY | 一回きりなのか | CONTINUITY_POLICY / SERVICE_SCOPE |

## Ablation Findings

### P10

| Variant | 対象Objection | Internal overall | Trust軸 | Conversion軸 | 解釈 |
| --- | --- | ---: | ---: | ---: | --- |
| Accountability | O2 | 0.5000 | 0.5000 | 0.2500 | 実在する対応者情報は「誰がいるか」を埋めるが、担当保証・Process・継続性までは埋めない |
| Continuity | O8 / O7 | 0.7500 | 0.5000 | 0.5000 | 行動後に見捨てられないという具体的なafter-state。CreativeとConversionのバランスが最良 |
| Business Model | O6 / O7 | 0.5000 | 1.0000 | 0.5000 | 個人無料の根拠と企業手数料を可視化し、費用・利害不安を直接下げるが、情緒の終わりを少し冷やす |

P10 ContinuityのExternal Formalは `5W / 6T / 1L`、Win Rate `0.6667`、Desktop `0.7500`、Mobile `0.5833`、Reviewer A `0.9167`、Reviewer B `0.4167`、Trust `0.5417`、Conversion Intent `0.5000`。したがって単独でもPASS相当の競争力はあるが、Full Enrichedの既存 `0.7083` を超えてはいない。

判断：P10のFull改善は、人物単独では説明できない。Business ModelはCost/Risk、Continuityはpost-decision Risk、Accountabilityは責任主体を埋める。相互補完によるobjection coverageが最も整合的だが、今回の小標本では組合せ因果を確定しない。

### P02

AuthorityはAbility / Accountabilityの明確さを上げる。一方ProcessはNext / Decisionの不確実性を直接下げる。Authority vs ProcessではAuthorityがOwner SpecificityとAbility側、ProcessがConversion Intent側で優位となった。したがって「20年 / 300社を載せる」だけでTrustが成立するのではなく、相談後の工程と「納得後契約」の境界まで行動に接続する必要がある。

## Evidence Strength と Objection の関係

StrengthとTypeは分離する。

- E1 Weak: 一般論。Trust proofに原則不使用
- E2 Specific: 氏名、資格、経歴、実績、対応範囲など会社固有情報
- E3 Operational: 誰が何をするか、問い合わせ・相談・提供工程
- E4 Risk Reducing: 費用条件、継続条件、契約・不利益に関わる確認済み情報
- E5 Decision Enabling: 次へ進むか、どの境界で判断するかを明確にする情報

E5が常にE4より強いとは扱わない。例えばP10のBusiness ModelはE4としてTrustを直接動かす一方、P02のProcess / Decision BoundaryはE5としてConversionの迷いを減らした。Strengthは量や権威ではなく、その不安に対する意思決定上の有用性で判定する。

## Evidence × Placement

- OWNER_IDENTITY: Middle / Before CTA。役割またはProcessに隣接。名前だけで担当保証を示さない
- VERIFIED_METRIC / EXPERIENCE: Early proof。ただしImmediate Readを変えるときのみHero
- SERVICE_PROCESS: MiddleからBefore CTA。相談の一手を短く示す
- POST_CLICK_FLOW / RESPONSE_EXPECTATION: CTA Zone。Before/After CTAの期待値に接続
- DECISION_BOUNDARY: CTA後またはCTA直前の境界。契約・転職などの判断時点を明示
- FEE_CONDITION / BUSINESS_MODEL: CTA直前。費用と利害の不安を下げる
- CONTINUITY_POLICY: CTA Zoneのafter-state。行動後の継続条件に置く
- RISK_POLICY / PRIVACY_POLICY: Before CTA。ただしUNKNOWNなら安心コピーを生成しない

Hero固定Ruleは採用しない。Evidenceが出現する位置ではなく、Objectionが意思決定を止める位置へ置く。

## Selection Logic（schema candidate）

1. Conversion goalと訪問者が決めることを特定
2. 行動を止めるObjectionを列挙
3. ObjectionごとにPreferred Evidence Typeを要求
4. Evidence Ledgerから `VERIFIED` のみ検索
5. Typeとは別にStrengthを判定
6. 最小のSequenceで高リスクObjectionを被覆
7. Objectionが発生する場所にPlacement
8. 必須Evidenceが `UNKNOWN` なら `HEARING_REQUIRED`。安心文を生成しない
9. Creative Protection、9幅QA、CTA visibilityを通過してから採用

Production safetyとして確定度が高いのは `UNKNOWN_BOUNDARY`、`PROVENANCE_REQUIRED`、`MOBILE_ACTION_BUDGET`。Trust optimizationの `OBJECTION_FIRST_SELECTION`、`ACCOUNTABILITY_WITH_PROCESS`、`OBJECTION_COVERAGE_SEQUENCE` は今回Observedの範囲で、Engine-ready候補にはしない。

## Hearing Requirements

### REQUIRED

- 責任主体（担当者またはチーム）と役割
- 対応範囲・対象外
- 最初の相談／問い合わせ後の流れ
- 料金、無料条件、費用発生タイミング
- 各Claimの一次Evidence URLまたは確認方法

### HIGH_VALUE

- 返信目安、相談方法・時間・場所
- 守秘・個人情報の扱い
- 勧誘方針、契約・転職を進めない場合の扱い
- 継続支援の条件
- 顧客が選べること・断れること
- 代表者の言葉、実在事例

### OPTIONAL

- 権利許諾済み人物写真
- 検証可能な実績数値・結果事例の詳細
- 現場・オフィス写真

写真はTrustの必須条件ではない。Evidence Ledgerに存在しない人物割当、守秘、無勧誘、返信時間、保証、完全無料等は `UNKNOWN` とし、Hearingへ戻す。

## Overfitting Check

変更はKAGAMI / Carigakuの表面構造や文言を模倣せず、P02/P10の公式Company Truthと各Objectionから導いた。既存の状態遷移・専門語翻訳・Strong Screen + Quiet Chapterを維持している。External Formalは最良single Variantの一般競争力確認に使ったが、Structured Reviewであり市場CVRではない。

## Rule Status

- Safety / Integrity: `UNKNOWN_BOUNDARY` / `PROVENANCE_REQUIRED` / `MOBILE_ACTION_BUDGET` = REPLICATED
- Trust Optimization: `OBJECTION_FIRST_SELECTION` = OBSERVED、`ACCOUNTABILITY_WITH_PROCESS` = OBSERVED、`OBJECTION_COVERAGE_SEQUENCE` = OBSERVED / combination effect unresolved
- `ENGINE_READY_CANDIDATE`: なし
- Logic schema: `SCHEMA_CANDIDATE_NOT_PRODUCTION_IMPLEMENTED`

## 次工程判断

最優先は **A｜Evidence研究継続**。理由は、P10で単独効果と組合せ効果の境界が残り、P02でもAuthorityとProcessが異なるObjectionを解消したためである。現時点でSafety schemaは次回Engine実装の土台にできるが、Trust OptimizationをProduction Engineへ全面実装するには、別業種・別Objectionでの再現確認が先。
