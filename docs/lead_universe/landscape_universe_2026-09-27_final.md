# 造園工事業 全国実名Universe｜Final Manifest

更新日: 2026-09-27
担当: 紬（リスト作成部門PM）
Branch: `task/landscape-universe-24070`

## Final SSOT

Universeは用途別に2層で管理する。

### 1. Permit Universe（公的許可レコード母集団）

国土交通省「建設業者・宅建業者等企業情報検索システム」から2026-09-27に取得した **23,971許可事業者レコード**。

対象条件:
- 建設業許可業種: 造園工事業（略号: 園）
- 47都道府県
- 一般建設業 / 特定建設業の両方を取得
- 全ページ取得

QA:
- Raw取得行数: 23,971
- Permit Universe行数: 23,971
- 都道府県カバレッジ: 47 / 47
- missing business_name: 0
- missing address: 0
- missing permit_no: 0
- missing source_url: 0
- canonical_entity_id duplicates: 0

### 2. Sales Entity Universe（営業用・保守的重複統合後）

同一住所・同一屋号で、個人事業から法人への承継と判断できる2組を統合し、**23,969 Sales Entities** を現行営業母集団SSOTとする。

統合:
1. 三重県 `森田造園` 第011014号 → `森田造園株式会社` 第011834号
2. 大阪府 `植忠` 第102202号 → `株式会社植忠` 第158021号

類似社名・同住所でも別法人/関連会社と判断し得る組は自動統合しない。保守的な重複統合を採用する。

## 24,070者との関係

国土交通省「令和7年度末 建設業許可業者数調査」の2026-03-31時点では、造園工事業許可業者数は **24,070者**。

一方、本Production Universeは2026-09-27時点のライブ企業情報検索システムから取得し、Permit Universeは **23,971者**。
差分は **-99者**。

国土交通省は企業情報検索システムについて、建設業者情報を月2回更新し、新規許可・許可内容変更は概ね1か月程度で掲載されると案内している。
したがって、24,070は2026-03-31時点の歴史的ベンチマークとして保持し、現在の営業ProductionではライブDBを基準とする。

過去時点の24,070者を無理に補完すると、2026-03-31以降に許可失効・廃業・変更された事業者を営業母集団へ混入させる可能性があるため採用しない。

## GitHub Actions Evidence

- Workflow: `Landscape Universe Full Build`
- Run: `36321510451`
- Build HEAD: `a86120d57587b4754f3be378135f05572d33c4b3`
- Artifact: `landscape-universe-live`
- Artifact ID: `10932890391`
- Artifact SHA-256: `82019c81d83014869f744f37fb4dc67ea3bde11591e5c109545aa1c558e90dc2`

## Outputs

Artifact:
- `landscape_universe_live.csv`
- `landscape_universe_live.xlsx`
- `prefecture_stats.csv`
- `universe_stats.json`
- Raw prefecture × permit-type evidence files

営業用追加成果物:
- `造園_全国実名Universe_SalesDeduped_2026-09-27.csv`（23,969 entities）

## Next Production Stage

Sales Entity Universe 23,969件をUniverse V1として、以下を実施する。

1. 公開Email Enrichment
2. Website / domain Precheck
3. NO_WEB高確率候補のPriority化
4. Verification TeamによるNO_WEB最終確認
5. Formal Master統合

最終営業リスト条件は `公開Emailあり × 独立公式Webなし`。
