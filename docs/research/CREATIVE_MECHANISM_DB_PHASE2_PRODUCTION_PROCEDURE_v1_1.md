# Creative Mechanism Database — Phase 2 Procedure v1.1

Phase 2はArchitecture v1.1のPM Review後に開始する。Phase 1.1中はReference収集を開始しない。

## 1. Preflight before any collection

1. `config/creative_mechanism_db_architecture_v1_1.json`をValidatorで検証する。
2. `data/creative_mechanism_phase1_1_pilot_coverage_matrix.csv`の100 slotを固定する。
3. Business ArchetypeとReference Pool Typeを別フィールドで確定する。
4. Discovery SourceとEvidence Source Roleを別々に記録する。
5. E0〜E4とSnapshot fieldsを有効化する。
6. Screenshot Archiveの保存先・Retention・Archive URIを確認する。
7. Creative ProfileのAxis導出にTruth Evidenceが無ければUNKNOWNにする。

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

Raw scoreは0〜5。JSONのDimension Weightで正規化する。

```text
category_score = Σ((raw / 5) × weight)
overall = design + conversion_architecture + motion + feasibility
```

Conversion Architectureは観察可能な設計評価であり、CVRや売上成果ではない。公開Measurementは別の`observed_performance_evidence`へ登録する。

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

画像・動画本体は外部Versioned ArchiveまたはBounded CI Artifactへ保存する。Archive Objectが失われたら、該当EvidenceはHOLDへ戻す。

## 8. Pilot QA and exit

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

Pilot QAでArchitectureの変更が必要になった場合、2,000〜3,000件へ進まず、Architecture v1.2として再レビューする。
