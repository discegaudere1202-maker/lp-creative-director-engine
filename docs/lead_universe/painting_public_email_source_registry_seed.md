# 塗装工事業 Public Email Source Registry Seed

更新日: 2026-09-29

目的: Sales Entity Universe 77,637件へ、無料・公開SourceからEmailをSource-firstでJOINする。

## Priority S

### 1. 日本塗装工業会 神奈川県支部 会員紹介
- URL: https://kanagawa-nittoso.jp/members/
- 公開項目: 会社名 / 所在地 / TEL / Mail / Website（一部）
- Join key: normalized name + prefecture/city/address, phone補助
- Notes: MailとWebsiteが同一会員ページで確認可能。Email取得とAuto Web Rejectを同時に行える。

### 2. 日本塗装工業会 鹿児島県支部 会員企業の案内
- URL: https://jpca-kg.jp/members/
- 公開項目: 会社名 / 代表者 / 住所 / TEL / FAX / e-mail / URL
- Join key: normalized name + address / representative / phone
- Notes: URLが「準備中」の会員も多く、公開Email × NO_WEB Candidate供給源として高期待。

### 3. 日本工業塗装協同組合連合会 工場リスト
- URL: https://n-kotoren.jp/list/
- 公開項目: 会社名 / 所在地 / 電話 / FAX / HP / Mail / 特徴
- Join key: normalized name + address / phone
- Notes: 全国横断。Mail列とHP列が明示され、Email EnrichmentとWeb Precheckを一括処理可能。

## Priority A

### 4. 日本塗装工業会 全国支部一覧
- URL: https://www.nittoso.or.jp/about/overview/
- Branch PDF: https://www.nittoso.or.jp/wp-content/themes/nittoso/images/about/overview/branches.pdf?v=5
- 用途: 全国支部Discoveryの起点。支部Email自体はCandidate EmailではなくSource Discovery用。

### 5. 日本塗装工業会 本部
- URL: https://www.nittoso.or.jp/
- 入会条件: 原則として塗装工事業の建設業許可業者
- 用途: MLIT UniverseとのJOIN適合性が高い会員母集団として利用。

## Source Registry Fields
各Sourceについて最低以下を保持する。

- source_id
- source_name
- source_type
- source_url
- prefecture
- coverage_scope
- estimated_members
- public_email_field
- public_website_field
- phone_field
- address_field
- representative_field
- access_method
- last_checked_at
- join_keys
- licensing_or_public_access_note
- production_status

## Extraction / JOIN Rules
1. EmailはSource原文からのみ取得し、推測・生成しない。
2. name-only JOIN禁止。
3. 原則: normalized name + address。住所が弱い場合のみphone / representative / permit情報で補強。
4. Email Source URL必須。
5. HP/URL欄が本人公式Webと確認できる場合はAuto Web Reject candidateへ。
6. HP空欄はNO_WEB確定ではない。Human Verification前提。
7. 団体ページ自体は独立公式Web扱いしない。
8. 1事業者に複数Sourceが一致した場合、Source provenanceをすべて保持する。

## Next Discovery Families
- 日本塗装工業会 47都道府県支部の会員一覧
- 都道府県塗装工業協同組合 / 塗装看板協同組合
- 防水・外壁改修系の県協同組合
- 自治体の住宅改修・空き家修繕・小規模工事登録事業者一覧
- 公共工事入札参加資格者名簿でEmailを持つ公開CSV/XLSX/PDF
- 工業塗装・焼付塗装組合のMail列付き会員名簿

## Production Strategy
Universe-firstを主軸、Source-firstを補完とする。

77,637 Sales Universe
→ Public Email Source bulk JOIN
→ Email FoundのみWeb Precheck
→ High-probability NO_WEB Queue
→ Human Verification
→ Final Formal Master
