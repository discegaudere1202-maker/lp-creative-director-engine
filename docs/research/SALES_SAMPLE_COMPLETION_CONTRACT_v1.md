# Sales Sample Completion Contract v1

Updated: 2026-09-15

## 0. Definition

営業サンプルは「途中版」ではない。

**Client Evidenceだけが未追加の完成LP**

と定義する。

顧客が見る営業サンプルには:
- 仮画像
- lorem ipsum
- 「正式版では〜」
- 「ヒアリング後に〜」
- 「ここに写真が入ります」
のような未完成表現を出さない。

写真や情報がない状態でも、そのまま見せて成立すること。

## 1. Sales Sampleで100%完成させるもの

### Strategy
- target hypothesis
- customer problem
- value proposition
- differentiation hypothesis grounded in public facts
- narrative / conversion architecture

### Copy
- Hero
- section copy
- proof copy from confirmed facts
- CTA copy
- FAQ if fact-safe
- semantic line breaks

### Creative
- Big Idea
- Visual Authority
- Art Direction
- typography
- composition
- screenshot peaks
- color/material system
- meaningful motion

### UX/CRO
- section order
- CTA cadence
- objection handling
- mobile hierarchy
- interaction states

### Front-end quality
- 9-width QA
- 200% reflow
- reduced motion
- runtime error
- accessibility baseline
- performance review

## 2. Client EvidenceでEnhanceするもの

営業サンプルを「修理」しない。
Client Evidenceは完成品をさらに強くする。

### Typical upgrade slots
- HERO_REALITY: 本人/現場/商品/店舗のHero候補
- OWNER_PORTRAIT: 代表者
- CRAFT_ACTION: 作業中
- PLACE_WIDE: 店舗/工房/オフィス
- PRODUCT_DETAIL: 商品/素材Macro
- RESULT_CASE: 実績写真
- TESTIMONIAL: 顧客の声
- OWNER_QUOTE: 代表者の言葉
- VERIFIED_METRIC: 数字
- SERVICE_DETAIL: 公開情報では分からないサービス差分
- CTA_CHANNEL: 正式問い合わせ先
- TRUST_CREDENTIAL: 資格/認定/加盟など

全案件ですべて要求しない。
Visual Authorityに応じて必要なSlotを選ぶ。

## 3. Dual-state design

各重要Sectionは必要に応じて2状態を設計する。

### Sales State
Client Evidenceなしで完成している状態。

### Enriched State
本人写真・実績・言葉を入れた状態。

重要:
Enriched StateはSales Stateの思想を変えない。
同じBig Ideaの証拠密度を上げる。

例:
Sales:
Typography + verified process diagram

Enriched:
同じ構図に実際の職人写真/工程写真を統合

NG:
契約後にHeroも構成もコンセプトも全部作り直す。

## 4. No visible placeholders

営業サンプルで禁止:
- grey image box
- generic avatar
- fake testimonial
- dummy metric
- AI人物を本人風に使用
- stock officeを本人事務所として使用
- `PHOTO HERE`

代わりに:
- typography
- diagrams
- verified numeric evidence
- licensed context images clearly non-owner
- illustration
- material abstraction
- geographic/context visual
- actual public assets with rights-safe use

で完成させる。

## 5. Client Evidence Mapping

LP内のUpgrade可能箇所にはMachine-readable IDを持たせる。

例:
```html
<section data-section-id="hero" data-client-slots="HERO_REALITY,VERIFIED_METRIC">
...
</section>

<section data-section-id="owner-story" data-client-slots="OWNER_PORTRAIT,OWNER_QUOTE">
...
</section>
```

将来のヒアリングアプリは、このSlot一覧を読み、
必要な質問・写真だけを動的に表示する。

## 6. Interview app principle (deferred)

アプリは最後に作る。

理由:
先にフォームを作ると不要な質問を大量に聞くことになるため。

Golden Sample検証から、
「納品品質を上げるため本当に必要だったClient Evidence」
を蓄積し、その集合から質問UIを作る。

目標:
顧客はWeb制作の要件定義をしない。
質問に答え、指定された写真を撮るだけ。

## 7. Photo request is art direction

将来アプリでは「写真をアップしてください」だけにしない。

例:
- 工房全体を入口側から横位置で1枚
- 作業中の手元を近距離で3枚
- 商品正面ではなく45度から1枚
- 代表者は窓の自然光側を向いて胸上
- 店舗外観は営業時間内/看板が読める距離

各Slotに:
- purpose
- orientation
- distance
- subject
- light
- avoid
を持たせる。

これにより、素人撮影でもLPに使いやすい素材を得る。

## 8. Completion Gate

Sales Sample PASS:
- Client Evidenceなしで未完成感ゼロ
- 2+ premium screenshot peaks
- Benchmark Supremacy PASS
- factual integrity PASS
- CRO architecture PASS
- mobile PASS

Delivery PASS:
- Sales Sample PASSを維持
- required Client Evidence collected
- Enriched State integration complete
- owner/client facts confirmed
- final CTA operational
- delivery visual QA PASS
