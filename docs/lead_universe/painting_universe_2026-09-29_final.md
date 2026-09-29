# 塗装工事業 全国Universe V1 SSOT

更新日: 2026-09-29

## Official reference
- 国土交通省 建設業許可業者数調査 2026-03-31: 塗装工事業 76,657業者
- Referenceは期末スナップショットとして保持し、Current Live検索をSales Productionの基準にする。

## Live acquisition
- Source: 国土交通省 建設業者・宅建業者等企業情報検索システム
- MLIT gyosyu: 17（塗装工事業）
- Coverage: 47都道府県 × 一般/特定 = 94検索
- GitHub Actions Run: 36537307802
- HEAD: 93a787f2e2a52873d3c2717d8276a15859231344
- Artifact: painting-universe-live
- Artifact ID: 11019980244
- Digest: sha256:d05f2373792a8616b7e3079395606554f456c20f98f1909bbded4ce3b02b3c22

## Permit Universe
- Raw rows: 77,640
- Permit canonical entities: 77,640
- Live - 2026-03-31 reference: +983
- Prefecture coverage: 47 / 47

## Permit Universe QA
- missing business_name: 0
- missing address: 0
- missing permit_no: 0
- missing source_url: 0
- canonical_entity_id duplicates: 0

## Sales Entity Universe
営業アプローチの重複防止目的で、Permit Universeとは別にSales Entity Layerを作る。

Auto-merge rule:
- normalized business name一致
- exact normalized address一致
- representative一致

上記すべてを満たす場合のみ高確度Merge。原Permit情報は保持する。

Result:
- Permit Universe: 77,640
- High-confidence merged rows: 3
- Sales Entity Universe V1: **77,637**
- Ambiguous same-name/same-address groups: 3 groups / 6 rows
- Ambiguous groupsは誤統合防止のためKEEP_SEPARATE_PENDING_ENRICHMENT

High-confidence groups:
1. RPS / （株）RPS, 三重県松阪市, representative一致
2. リファインテック, 大阪府茨木市, representative一致
3. （有）親泊木工 / （株）親泊木工, 沖縄県南風原町, representative一致。Current public siteは株式会社親泊木工表記。

## Durable data
Personal Library:
`/LP制作事業/LeadList/Painting/painting_sales_universe_2026-09-29.zip`

ZIP contains:
- painting_sales_universe.csv
- sales_entity_merges.csv
- sales_entity_holds.csv
- sales_universe_stats.json

## Production rule
Production V1の母集団は **Sales Entity Universe 77,637件** を使用する。
Permit Universe 77,640件は監査用に保持する。

## Next Gate
1. Public Email Source Registry構築
2. Source-first bulk JOIN
3. Public Email Enrichment（無料Source優先）
4. Email-found rowsだけWeb Precheck
5. Human VerificationでNO_WEB確定
6. Final Cross-Dedupe / Sales Formal Master

## Hard rules
- Paid API / paid DBはV1で使用しない
- Email推測・生成禁止
- name-only JOIN禁止
- Email Source URL必須
- AutomationだけでNO_WEB確定禁止
- Google Business / Maps / SNS / 団体ページは独立公式Web扱いしない
