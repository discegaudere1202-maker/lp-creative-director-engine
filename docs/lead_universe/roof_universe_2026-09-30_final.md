# 屋根工事業 全国Universe Production — FINAL

更新日: 2026-09-30

## Scope
GitHub Issue #146 Gate 1 — National Universe Productionのみ。
Public Email Enrichment / Web Precheck / Human Verification / toC Fit判定は未実施。

## Official Baseline
国土交通省 令和8年3月末 建設業許可業者数:
- 屋根工事業: 58,276業者
- 前年: 56,807業者
- 前年差: +1,469 / +2.6%

Official Baselineは年度末Referenceとして保持し、ProductionではLive取得件数を正とする。

## Live selector / parameter verification
Production前にMLIT実フォームを取得し、業種parameterを推測せず確認した。

Live form:
- selector name: `gyosyu`
- option label: `屋`
- option value: `7`
- permit type `一般建設業`: value `1`
- permit type `特定建設業`: value `2`

国交省検索システム利用マニュアルでも略号 `屋` = `屋根工事業` を確認。

Pilot（東京都）:
- GENERAL: 4,964件 / 100 pages / response echo `屋` + `一般建設業`
- SPECIAL: 2,317件 / 47 pages / response echo `屋` + `特定建設業`
- Pilot Gate: PASS

## GitHub Actions Production
- Branch: `task/roof-universe-58276`
- GitHub Actions Run: `36686727510` — SUCCESS
- Production Run HEAD: `e3aa58c27fdb8176619d91985b87074fad21639a`
- Artifact: `roof-universe-live`
- Artifact ID: `11085035982`
- Digest: `sha256:2147873925976998a74cf6be0185a1f784e49114915524d78ec203a4927c9a85`

## Live Search
- 47 prefectures × GENERAL / SPECIAL = 94 searches
- Completed: 94 / 94
- Failed search: 0
- Prefecture coverage: 47 / 47
- Raw search rows: 59,087

## Permit Universe
- Live Permit Universe: **59,087**
- Permit duplicate rows collapsed: 0
- Official 58,276との差: **+811**
- Difference Rate: **+1.3917%**

Live件数をそのまま採用し、Official 58,276への件数合わせは行っていない。

## Permit QA Hard Gate
- business_name missing: 0
- address missing: 0
- permit_no missing: 0
- source_url missing: 0
- canonical_permit_id missing: 0
- canonical_permit_id duplicate: 0
- wrong trade rows: 0
- failed search: 0
- prefecture coverage: 47 / 47
- Hard Gate: PASS

## Sales Entity Universe
High-confidence Auto Merge条件:
- normalized business_name一致
- exact normalized address一致
- representative一致

Result:
- Permit Universe: 59,087
- High-confidence Auto Merge groups: **1**
- Auto Merge rows removed: **1**
- Sales Entity Universe: **59,086**
- KEEP_SEPARATE_PENDING_ENRICHMENT: **3 groups / 6 rows**

Ambiguous groupsは商号のみで統合せず、後工程Enrichmentまで分離維持。

## Stable Entity Structure
- Permit PK: `canonical_permit_id` (`ROOF-P-*`)
- Sales Entity PK: `canonical_entity_id` (`ROOF-E-*`)
- `toc_fit`, `toc_fit_evidence`, `toc_fit_reason`, `toc_fit_verified` は今回すべて未判定/空欄。

## Durable Save
Personal Library:
`/LP制作事業/LeadList/Roof/RoofNationalUniverseProduction_2026-09-30`

Required payload:
- `roof_permit_universe.csv`
- `roof_sales_universe.csv`
- `sales_entity_merges.csv`
- `sales_entity_holds.csv`
- `roof_prefecture_stats.csv`
- `roof_universe_stats.json`
- `roof_universe_qa.json`
- `selector_discovery.json`
- `pilot_validation.json`
- `search_summary.json`
- `roof_universe_2026-09-30_final.md`
- durable ZIP bundle

## Next Gate
STOP at National Universe Production.
Public Email / Web / Human Verification / toC Fitへは紬PMの次指示まで進まない。
