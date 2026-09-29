# Creative Mechanism Database Project

## Phase 1.2 — Final Architecture Hardening v1.2

更新日: 2026-09-29  
Status: **ARCHITECTURE_V1_2_READY_FOR_PM_FINAL_REVIEW**  
SSOT: GitHub Issue #143 / Sarah PM Comment #5884152124

## 1. Review disposition

Phase 1の中核は維持する。

```text
Reference LP
 → Scene Evidence
 → Creative Mechanism
 → Compatibility / Constraint
 → Combination Recipe
 → Scene Spec
```

今回の変更は、v1.1の中核を維持したまま、Strong昇格のMotion依存、Pool別Promotion、Archetype配分、Risk Coverage、Profile数値再現性、Evidence Archive Preflightを最終Hardeningしたものである。100件Pilotと大量収集は開始していない。

## 2. v1.1 → v1.2 差分

| Review item | v1 | v1.1 |
|---|---|---|
| Score | Raw dimension数と満点が不整合 | 0〜5 Raw → Weight正規化。40/30/15/15 = 100。v1.2でApplicabilityとObservation Stateを導入 |
| Retrieval | Weight合計と順序が曖昧 | 合計1.00、Hard Gate→Score→Compatibility→Recipe→Novelty→3案 |
| Creative pool | Archetypeへ混在。300/300 Strong | Business Archetypeから分離したPool Type。500候補→300 Strong→120 Deep |
| Source | DiscoveryとEvidenceが混在 | `discovery_source_class`と`evidence_source_roles[]`を分離 |
| Conversion | Conversion Qualityという誤解余地 | Conversion Architecture Qualityへ変更。実績は別Entity |
| Authority | Evidence根拠と表現方法が混在 | Evidence Authority / Expression Driverへ分離 |
| Profile | Axis値の根拠が弱い | 全AxisにEvidence / Derivation / Confidence / Unknown Policy。v1.2で離散値とConflict Ruleを固定 |
| Mechanism Evidence | LP数中心 | Brand / Agency / Campaign独立性を追加 |
| Distinctiveness | Template Riskの方向が曖昧 | Design Distinctivenessを0〜5高いほど良いに統一 |
| Evidence | E系とM系の表記揺れ | E0〜E4へ統一。M0〜M3は禁止 |
| Snapshot | URL中心 | captured_at / viewport / locator / screenshot ID / hashを必須化 |
| Pilot | 上から100件 | Archetype×Industry×JP/Global×Discovery Source Coverage Matrix。v1.2でMedical / Finance / Beauty / Public Riskを追加 |
| Strong Gate | Global Motion >= 9 と全Dimension >= 2 | Pool別Promotion。MotionはOptional、Motion Mechanism Evidence時のみ閾値適用 |
| Sampling | Archetype名のみMachine-readable | 16 ArchetypeのDiscovery / Strong / Deep Allocation、Lower/Upper、Saturation Stop |
| Archive | External archiveの抽象方針 | Versioned S3-compatible object storage、24か月Retention、URI、Expiration、Re-captureを固定 |

## 3. Scoring Rubric v1.2

全Scoreは「高いほど良い」に統一する。Raw scoreは0〜5、Unknownはnullとする。

```text
normalized_category_score
  = Σ((raw / 5) × weight for OBSERVED applicable dimensions)
    / Σ(weight for OBSERVED applicable dimensions)
    × category_target_max

overall_score
  = Σ(applicable category scores)
    / Σ(target_max for applicable categories)
    × 100
```

| Category | Dimensions | Weight合計 |
|---|---|---:|
| Design Quality | Hero Originality, Typography, Layout Composition, Image Treatment, Visual Hierarchy, Section Rhythm, Section Boundary, Brand Distinctiveness, Screenshot-worthy Quality, Design Distinctiveness | 40 |
| Conversion Architecture Quality | Proof Presentation, CTA Clarity, Navigation Utility, Conversion Clarity, Objection Coverage, Decision Size, Customer State Fit | 30 |
| Motion Quality | Motion Job, Interaction Legibility, Scroll Experience, Timing/Rhythm, Reduced Motion Safety | 15 |
| Implementation Feasibility | HTML/CSS Feasibility, Asset Availability, Mobile Quality, Responsive Recomposition, Performance Discipline, Accessibility/Maintenance Safety | 15 |

### Applicability and Observation State

各Dimensionには `REQUIRED` / `OPTIONAL` / `NOT_APPLICABLE` を記録し、観測状態には `OBSERVED` / `MISSING` / `NOT_OBSERVED` / `NOT_APPLICABLE` を記録する。

- `MISSING`: 必要なDimensionだがEvidenceまたはAssetが存在しない。Hard Gateなら昇格不可。
- `NOT_OBSERVED`: まだ観測していない。品質0ではなくHOLD。
- `NOT_APPLICABLE`: そのLP・Sceneに正当なJobがなく、分母から除外。
- `OPTIONAL`の不在は低品質の証拠にしない。

Motion / Interactionは標準で `OPTIONAL`。静的で優秀なConversion LP、Local Trust、Document-heavy B2BをMotion不在だけで除外しない。Motion Mechanism Evidenceとして昇格するRecordのみ、Motion dimensionsを`REQUIRED`へ切り替え、Motion >= 9 / 15を適用する。

全Dimension一律の `minimum_raw_dimension_score >= 2` は廃止し、Pool別に次のHard Gateだけを適用する。

### Pool別Strong Promotion Rule

| Pool | 必須閾値 | Motion | Conversion Architecture |
|---|---|---|---|
| CONVERSION_INDUSTRY | Design >= 28, Implementation >= 9, Overall >= 70 | Optional。Motion Mechanism Evidence時のみ >= 9 | >= 20。CTA / Proof / Mobile / AccessibilityをHard Gate |
| CREATIVE_BENCHMARK | Design >= 32, Implementation >= 9, Overall >= 65 | Optional。Motion Mechanism Evidence時のみ >= 9 | 観察・保存するが必須閾値ではない |

両PoolともOriginal / Official EvidenceとMobile Observationを必須とする。Creative BenchmarkではさらにMechanism ClarityとTransfer Jobを明示する。Award受賞や有名ブランドで自動Strong昇格させない。

### Template resemblance

`Design Distinctiveness`を採用する。

```text
0 = generic / highly template-like
5 = clearly authored and distinctive
template_resemblance_risk = 5 - design_distinctiveness
```

RiskはPositive Design Scoreとして加点しない。

## 4. Retrieval Pipeline v1.2

Retrievalの順序を固定する。

```text
1. Eligibility / Evidence Hard Gate
2. Mechanism Candidate Scoring
3. Compatibility Solver
4. Recipe Assembly
5. Diversity / Novelty Re-ranking
6. Final 3 Recipe Output
```

Noveltyは、Hard Gateを通過したRecipeだけを再順位づけする。Evidence Safety、Conversion Architecture Fit、Compatibilityを上書きできない。最終出力は、Low-risk / Authority-led / Novelty-led等の3案とし、Noveltyだけを唯一の正解にしない。

Retrieval WeightはJSONで合計1.00として機械検証する。

## 5. Business ArchetypeとReference Poolの分離

`CREATIVE_BENCHMARK`はBusiness / Conversion Archetypeではない。したがって、別Entityの`reference_pool_type`として管理する。

```text
CONVERSION_INDUSTRY:
  Discovery Candidates 2,100
  Strong 900
  Deep 480

CREATIVE_BENCHMARK:
  Discovery Candidates 500
  Strong 300
  Deep 120

Total:
  Discovery Candidates 2,600
  Strong 1,200
  Deep 600
```

Creative Benchmarkは、Award受賞・有名ブランド・派手な表現だけでStrongへ昇格しない。Mechanism、Transfer Job、Original Evidence、Mobile、Feasibilityを確認する。

## 6. Archetype Sampling Allocation

`archetype_sampling_allocation[]`をMachine-readable SSOTとして復活させた。16 Business Archetypeの合計は次の通りである。

| Pool | Discovery | Strong | Deep |
|---|---:|---:|---:|
| CONVERSION_INDUSTRY | 2,100 | 900 | 480 |

各Archetypeには `lower_bound` / `upper_bound` / `rationale` / `saturation_stop_rule` を持たせる。Mechanismが2連続Batchで増えず、Conversion Patternも増えない場合はTarget未達でも停止できる。一方、重要領域で独立した新Mechanismが継続発生する場合はUpper Boundまで追加する。これは均等Quotaではなく、Evidence DiversityとMechanism Saturationを優先する。

## 7. Creative Profile Numeric Derivation

全16 Axisは `UNKNOWN` または `0 / 0.25 / 0.50 / 0.75 / 1.00` の離散値だけを取る。各Axisには `numeric_derivation_policy: PROFILE_AXIS_NUMERIC_V1` を持たせ、次の式を共通適用する。

```text
contribution = relevance × directness × confidence
axis_score = weighted_mean(contribution for distinct evidence classes)
axis_score = nearest({0, 0.25, 0.50, 0.75, 1.00})
```

Relevance、Directness、Evidence Gradeの値はJSONに固定し、Evidenceが1つもない場合は`UNKNOWN`とする。公式PositioningとMass価格帯のようなConflictではEvidence classごとの加重平均を取り、最高・最低のDirect Evidence差が0.50以上ならScoreを0.50以下にCapし、ConfidenceをLOWへ落とす。新しい公式事実が確認できる場合だけ、古い一般記述を上書きする。

## 8. Source Model v1.2

### Discovery source

候補を見つけた入口。

```text
AWWWARDS
CSS_DESIGN_AWARDS
WEB_GRAND_PRIX
JAPANESE_WEB_GALLERY
GLOBAL_WEB_GALLERY
ORIGINAL_SITE_DIRECT
PRODUCTION_PORTFOLIO
MOTION_INTERACTION_SHOWCASE
CONVERSION_LP_GALLERY
```

### Evidence source roles

Candidateの主張を確認する出所。1Referenceに複数付与できる。

```text
ORIGINAL_LIVE
OFFICIAL_BRAND
OFFICIAL_PRODUCT_OR_SERVICE
OFFICIAL_CONVERSION_PAGE
OFFICIAL_CASE_STUDY
PRODUCTION_CASE
AWARD_ENTRY
GALLERY_ENTRY
PUBLIC_STANDARD
```

実運用例：

```text
AWWWARDS discovery
 → ORIGINAL_LIVE evidence
 → PRODUCTION_CASE intent context
```

Source mixはDiscovery Biasを抑えるためだけに使う。Strong昇格にはDiscovery元を問わず、Original / Official Evidenceを必須とする。旧v1の「Original最大35%」と「Original 35%以上確保」という矛盾は廃止した。

## 9. Conversion Architecture Quality

LPを見ただけではCVR・売上・問い合わせ増加は観察できない。したがって、評価対象は次の観察可能な設計だけとする。

```text
CTA Clarity
Objection Coverage
Decision Size
Proof Presentation
Customer State Fit
Conversion Clarity
Navigation Utility
```

実績数値は`observed_performance_evidence`へ分離する。公式Case Study等に、Metric、Value、Measurement Period、Population、Methodology、Source URLが揃う場合のみ保存する。

「このMechanismはCVが高い」「このLPは売れる」といった因果主張は、公開された測定Evidenceなしには作らない。

## 10. Creative Authority v1.2

### Evidence Authority

表現や主張を正当化する根拠。

```text
PERSON / PLACE / MATERIAL / CRAFT / PRODUCT
DOCUMENT / PROOF / HERITAGE / COMMUNITY
```

### Expression Driver

注意・気分・読み方を制御する表現上の駆動力。

```text
EDITORIAL / MOVEMENT / PRECISION / TASTE / PLAY
```

`PLAY`があるからポップにする、`TASTE`があるからLuxury Templateにする、という検索は禁止する。まずCompany Truth・Buyer State・Marketing Jobを適合させ、その後にExpression Driverを補助として選ぶ。

## 11. Creative Profile Derivation

Axisは形容詞ではなく、Company Truth / Buyer Stateから導出する。

各Axisに次を持たせる。

```text
input_evidence_candidates
derivation_rule
confidence_rule
unknown_policy
```

例：PREMIUMは、価格帯・顧客層・販売チャネル・公式Positioning・希少性のEvidenceが必要であり、色や余白だけでは上げない。Evidenceが無ければUnknownとし、無理に0や1へ埋めない。

全16 Axisのルールは`creative_mechanism_db_architecture_v1_2.json`に保存する。各Axisの数値は離散Rubricで決定し、同じTruth入力から同じ値を再現できるようにする。

## 12. Mechanism Evidence Independence

独立LP数と、Brand / Agency / Campaignの独立数を分ける。

### Candidate → Supported

```text
independent_lp_count >= 3
unique_brand_count >= 3
unique_agency_count >= 2
unique_campaign_count >= 3
single_agency_share <= 0.66
```

### Supported → Canonical

```text
independent_lp_count >= 5
unique_brand_count >= 4
unique_agency_count >= 3
unique_campaign_count >= 4
archetype_count >= 2
single_agency_share <= 0.50
single_brand_family_share <= 0.50
```

同一Agencyの似た制作実績だけで汎用Mechanismへ昇格させない。

## 13. Evidence Grade / Snapshot / Storage

Evidence GradeはE0〜E4へ統一する。

```text
E0 = Discovery pointer only
E1 = Award / Gallery / Portfolio description only
E2 = Original or Official live page verified
E3 = Original / Official + Desktop and Mobile snapshot review
E4 = E3 + multi-scene mechanism evidence + transfer note
```

M0〜M3はv1.1では使用しない。

Scene Evidenceの必須Snapshot：

```text
captured_at
viewport
original_url
evidence_locator
screenshot_identifier
content_hash (sha256)
```

GitにはMetadata・Hash・Locator・Archive URIだけを保存し、Bulk Screenshotや動画を直接コミットしない。CaptureはS3互換のVersioned Object Storage（Object Lock/WORM）へ保存し、Bounded CI Artifactは90日以内の二次キャッシュだけにする。Pilot Evidenceはcaptured_atから24か月保持し、Strong / DeepはCanonicalまたは権利条件が続く間保持する。

```text
evidence/<reference_id>/<captured_at>/<viewport>/<content_hash>.<ext>
```

Archive URIは `s3://<versioned-evidence-bucket>/evidence/<reference_id>/<captured_at>/<viewport>/<content_hash>.<ext>` とする。期限切れ・削除・Hash変更・大規模リニューアル時は再Captureし、旧Recordを保持したまま新しいcaptured_at / hashを作る。Archive Objectが失われた場合、MetadataだけでEvidenceを再現したことにせず、該当RecordをHOLDへ戻す。

## 14. Phase 2 Pilot Coverage Matrix

Pilot 100件は順位順に取らない。`data/creative_mechanism_phase1_2_pilot_coverage_matrix.csv`で、以下を先に固定する。

```text
Reference Pool Type
Business Archetype
Industry
JP / Global
Discovery Source Class
Planned Count
Validation Focus
```

目的は市場構成の完全再現ではなく、Taxonomy、Rubric、Mechanism Mining、Mobile Observation、Source Bias、Regulated Claims、Beauty Before/After Risk、Public Accessibilityの早期検出である。Matrixは100件分の計画のみであり、実際のReference収集はPhase 1.2最終レビュー後まで開始しない。

## 15. QA Hard Gates

- Rubric category weights: 40 / 30 / 15 / 15
- Overall normalized score: 100
- Motion N/A / static reference can remain Strong Candidate
- MISSING / NOT_OBSERVED / NOT_APPLICABLE are distinct
- Pool別Strong Promotion Ruleが存在し、Creative BenchmarkにConversion必須閾値を掛けない
- Retrieval weights: 1.00
- Archetype allocation totals: 2,100 / 900 / 480
- Creative BenchmarkはBusiness Archetype配列に存在しない
- Creative candidate 500、Strong 300、Deep 120で自動全件昇格しない
- Discovery SourceとEvidence Source roleが別フィールド
- StrongにはOriginal / Official Evidenceが必要
- Conversion ArchitectureとMeasured Performanceを分離
- 全Creative Profile AxisにDerivation RuleとUnknown Policyがある
- 全16 AxisにNumeric Derivation Policy、離散値、Conflict Ruleがある
- Canonical MechanismにLP / Brand / Agency / Campaign独立条件がある
- Evidence GradeはE0〜E4のみ
- Evidence Snapshot必須フィールドがある
- Pilot Coverage Matrixが100件に合計される
- PilotにMedical/Finance、Beauty、Public Accessibility Riskが含まれる
- Evidence Archive PreflightにBackend / Retention / URI / Expiration / Re-captureがある
- Phase 2収集開始フラグはfalse

## 16. Phase 1.2終了条件

```text
ARCHITECTURE_V1_2_READY_FOR_PM_FINAL_REVIEW
```

Phase 2 Pilot、大量収集、Mechanism実データ蓄積は、Sarah PMがv1.2を最終レビューした後に開始する。
