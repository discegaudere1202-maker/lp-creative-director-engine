# SME Craft Prototype Batch 01 — Findings

更新日: 2026-09-15

対象:
- P01 Business Verb Hero
- P02 Customer-world Translation
- P03 Emotional Barrier Art Direction
- P04 Long-form Evidence without Cards
- P05 Work Style as Single Scene
- P06 Sales State → Enriched State

検証:
- 1440px実レンダリング
- 390px実レンダリング
- 日本語改行の目視
- Company Truth依存度
- NO_WEB / WEAK_WEB営業サンプルへの転用可能性

---

## P01 — Business Verb Hero

判定: HOLD / 原理は強いが乱用危険

良かった:
- 1つのVerbをHeroの支配原理にできる
- Assetなしでも強いHierarchyを作りやすい
- Mobileでも主役を維持しやすい

弱点:
- 「つなぐ」「支える」「変える」など抽象Verbでは一気にGenericになる
- 円/線など抽象Geometryを合わせるだけではAI広告感が残る

採用条件:
- その会社が実際に使う固有Verb
- Verbが事業行為として確認可能
- Form/MotionまでVerbの性質と一致

Rule:
`Generic verb + generic geometry = FAIL`

---

## P02 — Customer-world Translation

判定: PASS Prototype

良かった:
- 専門業務一覧より顧客の困りごとが先に理解できる
- 士業/専門工事/B2B/医療周辺などに強い
- Asset-lightでもCompany-specific Copyを作りやすい

実レンダリングで発見した問題:
初稿1440pxでは「社員が辞める」が不自然に分割された。
Conceptは正しくても、日本語のLine Shapeが崩れると一気に低品質化する。

修正:
- semantic chunkで明示的にBreak
- DesktopのHeadline sizeを少し下げる
- Mobileは縦順へ再構成

重要な学び:
**Craft GateはConcept Gateの後にも必要。**
良いConceptは悪い組版を救わない。

---

## P03 — Emotional Barrier Art Direction

判定: HOLD

良かった:
- 問い合わせ自体が重い業種では非常に有効
- 「サービス機能→CTA」より心理状態へ先回りできる
- Visual temperatureをConversion理由から決められる

弱点:
- pastel / blob / rounded pillへ逃げると一気にテンプレ化
- 「安心してください」だけならOwner-specificityがない

採用条件:
- 実際の顧客障壁をSourceから特定
- Barrierを下げる根拠がFactとして存在
- 色/形ではなくCopy/CTA/情報順まで変える

Rule:
`Emotional barrier must change narrative, not only color palette.`

---

## P04 — Long-form Evidence without Cards

判定: PASS Prototype

良かった:
- 「20年」「300社+」をBadge/Cardから解放できる
- 数字→何を見てきたか、へ意味を展開できる
- B2B/士業/職人/老舗で使いやすい
- Dense→QuietのRhythmを作りやすい

弱点:
- 右側のEvidence項目がGenericなら数字を巨大化しただけと同じ

採用条件:
- 数字を構成する具体的経験カテゴリが確認可能
- 数字の大きさより「その経験が顧客に何を意味するか」を優先

Rule:
`Evidence number → evidence landscape`

---

## P05 — Work Style as Single Scene

判定: PASS Prototype

良かった:
- 「一緒に考える」「最後まで担当」「現場で決める」など仕事の進め方をScene化できる
- ありがちな3 Step Cardを避けられる
- 個人事業主/小規模企業ほど強い可能性がある

弱点:
- Work Styleが公開情報で確認できない企業へ勝手に使えない
- Genericな付箋/紙表現へするとAgency Template化する

採用条件:
- 実際の仕事の進め方を確認
- Scene内のObject/順番/言葉をその会社固有にする

Rule:
`Work style → one visual situation, not a process-card row.`

---

## P06 — Sales State → Enriched State

判定: SYSTEM PASS / Creative Frameとしては評価対象外

良かった:
- 「実写真がないから未完成」を防げる
- Sales Sample時点でLayout/Copy/Hierarchyを完成可能
- 契約後の写真が“救済”ではなく“Evidence強化”になる
- ヒアリングアプリへ直接つながる

重要:
このFrame自体を営業LPへ表示するわけではない。
これは制作Systemの設計思想。

Required Evidence Slot fields:
- subject
- action
- distance
- framing
- light
- negative space
- mobile crop
- replacement rule

Rule:
`Client evidence enriches; it must not rescue a weak sales sample.`

---

# Batch 01総括

最も営業サンプルへ直結:
1. P02 Customer-world Translation
2. P04 Evidence Landscape
3. P05 Work Style Scene

条件付き:
4. P01 Business Verb Hero
5. P03 Emotional Barrier

System layer:
6. P06 Sales → Enriched

## 新しい品質原則

### 1. Concept PASSとCraft PASSを分離
良い考えでも、日本語組版/Responsiveが崩れればPremiumではない。

### 2. Asset-light ≠ Abstract-heavy
写真がないからGeometry/Blob/Gradientへ逃げない。
Fact / Verb / Process / Document / EvidenceからFormを作る。

### 3. 小規模企業ほどWork Styleが資産になり得る
大企業のようなBrand Assetがなくても、
「誰がどう対応するか」はCompany Truthになりやすい。

### 4. Sales Sampleの完成度をClient Assetへ依存させない
Client AssetはEnrichment。
営業サンプルはその前から完成している必要がある。

---

# 次Prototype

- P07 Owner Voice → Typography Rhythm
- P08 Local/Service Area → Spatial Composition
- P09 Price Transparency → Trust Composition
- P10 Before Contact / After Contact emotional transition
- P11 Real Photo Crop + same-frame asset replacement
- P12 Mobile-only Art Direction variant
