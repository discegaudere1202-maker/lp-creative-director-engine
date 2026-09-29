# Creative Mechanism Database — Phase 2 Procedure v1.2.2

Phase 2はArchitecture v1.2.2のPM Approval後に開始する。Phase 1.2.2中はReference収集を開始しない。

## 1. Preflight before any collection

1. `config/creative_mechanism_db_architecture_v1_2_2.json`をValidatorで検証する。
2. `data/creative_mechanism_phase1_2_pilot_coverage_matrix.csv`の100 slotを固定する。
3. Business ArchetypeとReference Pool Typeを別フィールドで確定する。
4. Discovery SourceとEvidence Source Roleを別々に記録する。
5. E0〜E4とSnapshot fieldsを有効化する。
6. Evidence Archive Preflightを通過させる。S3互換Versioned Object Storage、Object Lock/WORM、24か月Pilot Retention、90日CI二次キャッシュ、URI形式、Expiration、Re-capture queueを確認する。期限切れCI Artifactを唯一のStrong/Deep Evidenceにしない。
7. Creative ProfileのAxis導出にTruth Evidenceが無ければUNKNOWNにする。全16 Axisは`PROFILE_AXIS_NUMERIC_V2`の離散Rubricで決定し、Conflict Ruleを適用する。
8. Evidence QualityはRaw Floatを入力せず、`relevance_level / directness_level / confidence_level`を固定MappingからNumericへ変換する。
9. `phase2_gate.pilot_allowed_only_after = Phase 1.2.2 PM Approval`と`collection_started=false`を確認する。Preflight完了だけでは収集開始を意味しない。

## 2. Pilot 100件の取得順

Coverage Matrixの各slotから計画数だけ取得する。上位検索結果を100件連続採用しない。

各候補に登録する最低項目：

```text
reference_id
pool_type
business_archetype
industry
market_scope (JP / GLOBAL)
discovery_source_class
evidence_source_roles[]
original_url
canonical_url
```

## 3. Evidence workflow

```text
Discovery Source
 → Original / Official verification
 → Desktop observation
 → Mobile observation
 → Scene Evidence snapshot
 → Scoring
 → Mechanism mining
 → Strong / Hold / Reject
```

Award・Gallery・Portfolioは候補発見または制作意図の補助に使えるが、Original / Official Evidenceの代替にはならない。

## 4. Scoring workflow

Raw scoreは0〜5。JSONのDimension Weightで正規化する。各DimensionにApplicabilityとObservation Stateを記録する。

```text
category_score = Σ((raw / 5) × weight for OBSERVED applicable dimensions) / Σ(applicable weights) × category_target_max
overall = Σ(applicable category scores) / Σ(applicable category targets) × 100
```

Conversion Architectureは観察可能な設計評価であり、CVRや売上成果ではない。公開Measurementは別の`observed_performance_evidence`へ登録する。

Creative Profile Evidenceは次の順序で処理する。

```text
relevance_level / directness_level / confidence_level
  → fixed enum / grade mapping
  → relevance / directness / confidence
  → evidence_weight = relevance × directness × confidence
  → axis_signal_value weighted mean
```

Evidenceの不在・未観測は`UNKNOWN`。`axis_signal_value = 0.50`は、Observed Evidenceが明示的にmid-market / mixed / moderate / balancedである場合だけに使う。単なる「記載なし」はNeutral Evidenceに変換しない。

Motion / Interactionが存在しない静的LPは`OPTIONAL + NOT_APPLICABLE`または`OPTIONAL + MISSING`として扱い、Motion不在だけでStrongから除外しない。Motion Mechanism Evidenceとして登録する場合だけMotionをREQUIREDに切り替え、Pool別Motion thresholdを適用する。`NOT_OBSERVED`はHOLDであり、0点ではない。

Promotionは`promotion_rules_by_pool_type`に従う。CONVERSION_INDUSTRYはConversion Architecture / Evidence / Mobile / Feasibilityを重視し、CREATIVE_BENCHMARKはDesign Distinctiveness / Mechanism Clarity / Transfer Job / Original Evidence / Mobile / Feasibilityを重視する。Creative BenchmarkのConversion Architectureは保存するが必須閾値にしない。

## 5. Mechanism promotion workflow

候補Mechanismには独立数を必ず記録する。

```text
independent_lp_count
unique_brand_count
unique_agency_count
unique_campaign_count
```

同一Agency、同一Brand family、同一Campaign variationだけでSupported / Canonicalへ昇格させない。

## 6. Retrieval dry run

Eligibility / Evidence Hard Gateを最初に実行し、その後にScore、Compatibility、Recipe Assembly、Novelty Rerankingの順で処理する。Noveltyは不適格なMechanismを復活させない。

同じCompany Truth / Sales Storyから最低3 Recipeを出す。

```text
Conversion-safe
Authority-led
Novelty-led
```

## 7. Evidence Archive

Gitには次だけを保存する。

```text
captured_at
viewport
original_url
evidence_locator
screenshot_identifier
content_hash
archive_uri
rights_note
```

画像・動画本体はS3互換Versioned Object Storageへ保存する。URIは `s3://<versioned-evidence-bucket>/evidence/<reference_id>/<captured_at>/<viewport>/<content_hash>.<ext>` とする。Pilotは24か月保持、CI Artifactは90日以内の二次キャッシュのみとし、Archive Objectが失われたら該当EvidenceはHOLDへ戻す。URL変更、Hash変更、期限切れ、または大規模リニューアル時は再Captureし、旧Recordを消さずに新しいSnapshotを作る。

## 8. Pilot risk coverage

100件は20セル×5件を固定する。Source / JP-Globalだけでなく、次のArchitecture Riskを必ず含める。

- `FINANCE_INSURANCE`: regulated claims and evidence safety
- `MEDICAL_DENTAL_CLINIC`: medical claims, accessibility and sensitive-state fit
- `BEAUTY_SALON_BODYCARE`: before/after, testimonials and high-claim-risk handling
- `PUBLIC_NONPROFIT`: accessibility-critical and public-service communication

市場比率の完全再現より、これらのリスクがRubric・Evidence・Mobile Observationで処理できることを優先する。

## 9. Pilot QA and exit

100件完了後、次を集計する。

- Source discovery bias
- Original / Official Evidence coverage
- E0〜E4分布
- Rubric missingness
- Profile UNKNOWN率
- Mechanism duplicate / merge rate
- Agency / Brand independence
- Mobile snapshot failure
- Local / SME transfer coverage
- Regulated claims / evidence-safety incidents
- Accessibility-critical observation failures
- Beauty before/after and testimonial claim-risk findings

Pilot QAでArchitectureの変更が必要になった場合、2,000〜3,000件へ進まず、Architecture v1.3として再レビューする。
