# 塗装工事業 Public Email Source Registry v1

更新日: 2026-09-29

目的: 塗装工事業 Sales Entity Universe 77,638件へ、公開Emailを推測せずSource URL付きでJOINするためのSource Registry。

## Priority A — Email列/Email本文が明示された公開名簿

| Priority | Source | Coverage | Public fields | URL | Notes |
|---|---|---|---|---|---|
| A1 | 日本塗装工業会 新潟県支部 会員紹介 | 新潟県 | 会社名 / 所在地 / 代表者 / TEL / FAX / Email | https://niigata-nittoso.jp/introduction/ | Email掲載密度が高い。住所JOIN可能。 |
| A1 | 茨城県塗装工業組合 組合員名簿 | 茨城県 | 商号 / 代表者 / 郵便番号 / 住所 / TEL / FAX / Email / URL | https://tosouiba.com/meibo/meibo.html | 地区別ページ。EmailとURLを同時取得可能。 |
| A1 | 日本塗装工業会 神奈川県支部 会員紹介 | 神奈川県 | 会社名 / 区 / 住所 / TEL / Mail / Website | https://kanagawa-nittoso.jp/members/ | Web有無Precheckにも利用可能。重複表示QA必要。 |
| A1 | 日本塗装工業会 静岡県支部 会員一覧 | 静岡県 | 会社名 / 代表者 / 住所 / TEL / FAX / Email / URL | https://www.nittososhizuoka.com/?page_id=7 | Email/URL併記あり。 |
| A1 | 日本塗装工業会 香川県支部 会員紹介 | 香川県 | 会社名 / 代表者 / 住所 / TEL / FAX / Email / Website | https://ww8.tiki.ne.jp/~jpcakagawa/activity/sp/service.html | free/provider mail多め。NO_WEB候補抽出に向く。 |
| A1 | 日本塗装工業会 宮崎県支部 会員紹介 | 宮崎県 | 会社名 / 所在地 / TEL / Email | https://nittoso-miyazaki.sakura.ne.jp/sp/kaiin.html | Email明示。更新日は要検証。 |
| A1 | 日本塗装工業会 鹿児島県支部 会員一覧 | 鹿児島県 | 会社名 / 代表者 / 住所 / TEL / FAX / Email / URL | https://jpca-kg.jp/aboutus/ | EmailとURL同時取得。 |
| A1 | 日本工業塗装協同組合連合会 工場リスト | 全国 | 会社名 / 所在地 / TEL / FAX / HP / Mail / 特徴 | https://n-kotoren.jp/list/ | 全国横断。Mail列あり。建設塗装以外の工業塗装も含むためUniverse JOINで対象限定。 |

## Priority B — 全国/大規模会員母集団、Emailは個別詳細または一部

| Priority | Source | Coverage | Public fields | URL | Notes |
|---|---|---|---|---|---|
| B1 | 日本塗装工業会 | 全国47都道府県 / 約2,300社 | 全国支部・会員導線 | https://www.nittoso.or.jp/about/overview/ | 47支部すべての入口。支部ごとに会員ページ形式が異なるためSource Factoryで巡回。 |
| B1 | 日本塗装工業会 支部一覧 | 全国47都道府県 | 支部住所 / TEL / FAX / 支部Email | https://www.nittoso.or.jp/wp-content/themes/nittoso/images/about/overview/branches.pdf | 各支部サイト探索のSeed。支部事務局Emailは営業Candidate Emailとしては使わない。 |
| B1 | 全国マスチック事業協同組合連合会 組合員名簿検索 | 全国 | 商号 / 都道府県 / 保証情報 / 個別詳細導線 | https://www.mastic.or.jp/member/ | 建築仕上・塗装系全国母集団。個別詳細で連絡先取得可否を確認。 |
| B1 | 大阪府塗装工業協同組合 組合員名簿 | 大阪府 / 96社規模 | 組合員一覧 / 地域 / 個別詳細 | https://pco.or.jp/meibo/ | 2026年7月時点96社。個別Email公開率を調査。 |

## JOIN rules

1. permit number if source exposes it
2. corporate number if available
3. normalized business name + normalized full address
4. normalized business name + prefecture/city + phone
5. normalized business name + representative + locality

**Name-only JOINは禁止。**

## Email rules

- Source上に公開された文字列のみ採用
- `mailto:` / visible textを正規化
- Unicode confusable / combining markを検知
- current public sourceと保存値が不一致ならcurrent sourceを優先し、旧値を履歴保存
- inquiry formはEmail扱いしない
- 支部事務局EmailはCandidate企業の営業Emailとして採用しない

## Web Precheck fields

SourceにURL/HPが併記される場合は同時に保存:

- `source_website_url`
- `source_website_status`
- `email_domain`
- `email_type` = FREE_MAIL / CUSTOM_DOMAIN / PUBLIC_PROVIDER / UNKNOWN

Source上に明示された公式WebsiteはAuto Web Reject候補。ただし、企業同一性を確認してから除外する。

## Next expansion target

日本塗装工業会47都道府県支部を全件巡回し、各支部を以下に分類する:

- `EMAIL_TABLE_PUBLIC`
- `EMAIL_DETAIL_PUBLIC`
- `MEMBER_ONLY_NO_EMAIL`
- `MEMBER_LIST_NO_EMAIL`
- `NO_PUBLIC_MEMBER_LIST`
- `BLOCKED_OR_UNAVAILABLE`

各Sourceについて `estimated_members`, `email_count`, `website_count`, `access_method`, `last_verified_at` を記録する。
