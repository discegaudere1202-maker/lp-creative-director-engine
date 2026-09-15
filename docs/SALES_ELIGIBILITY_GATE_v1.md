# Sales Eligibility / Existing Site Baseline Gate v1

更新日: 2026-09-15

## 目的

Creative QAより前に、そもそも「この会社へ営業サンプルを作る意味があるか」を判定する。

今回の森人検証で、MATERIAL系の研究対象として面白いことと、営業サンプル対象として適切であることを混同した。
このGateは同じ誤りを1000件生成で繰り返さないためのPreflight。

---

## 1. 候補の3分類

### SALES_CANDIDATE
営業サンプル制作へ進めてよい。

主な条件:
- Webサイトなし
- または既存サイトに具体的な改善余地が2つ以上ある
- 改善仮説を顧客価値 / Conversion / ブランド表現の言葉で説明できる

### BENCHMARK_ONLY
既存サイトが強い。
営業サンプルとして勝手に作り直さず、研究・Benchmark対象として扱う。

### REDESIGN_CHALLENGE
既存サイトが強いことを認識した上で、R&D目的で明示的に「既存を超える」ことへ挑む。
営業候補とは分離する。

### REVIEW
サイトはあるが、作り直す価値がまだ証明されていない。
Production開始禁止。

---

## 2. Existing Site Baseline Score

各0–10点。

- Visual Design
- Brand Specificity
- Authentic Assets
- Message Clarity
- Trust Evidence
- Mobile UX
- Conversion Path

合計70点。

内部初期ルール:
- 49点以上: Strong baseline候補
- 42点以上かつBrand Specificity / Authentic Assetsが各7以上: Strong baseline候補

これは市場の絶対点ではなく、営業サンプルを作る価値があるかを判断する内部Preflight。

---

## 3. Existing Site Superiority Gate

既存サイトがStrong baselineなら、通常の営業サンプル制作へ進めない。

重要:
「うちならもっと格好よくできそう」だけでは改善仮説として認めない。

必要なのは例えば:
- Smartphoneで主要CTAまで到達しにくい
- 何を頼める会社なのか5秒で分からない
- 強い実績が深い階層に埋もれている
- 本物の写真資産は強いがConversion pathがない
- 求人目的なのに応募者の不安が解消されていない

のような具体Gap。

---

## 4. Asset Reality Gate

### 最重要

**Asset Access制約とBusiness Asset不足を混同しない。**

Business Asset Strength:
事業者自身が持っている実在資産の強さ。

例:
- 本人写真
- 施工写真
- 工房
- 店舗
- 商品
- 職人
- 実績
- 歴史資料

Accessible Asset Strength:
制作時点で、こちらが合法・確実に利用できる資産の強さ。

Business Asset >= 7 かつ Accessible Asset <= 3 の場合:

`ACCESS_CONSTRAINT_NOT_ASSET_POOR`

と分類する。

この場合、勝手に「写真の弱い会社」と解釈して抽象UIへ置換してはいけない。

---

## 5. 森人で起きた失敗

森人は既存Web上に、家具・木・工房・人・店の空気というOwner-specificな本物の資産が存在していた。

しかし制作側で画像取得に制約があったため、これをAsset Limited案件と誤認した。
その結果、本来の強いMaterial / Sensory Realityを抽象的なTypography / UIへ置換し、既存サイトよりブランド体験を弱くした。

### 判定

- Golden Sample 03: 取り下げ
- Sales Prospect: 対象外
- Research role: MATERIAL / SENSORY Benchmarkとして保持
- Failure role: Existing Site Superiority / Asset RealityのPostmortemとして保持

---

## 6. 新しい候補選定順序

```text
Candidate
→ Existing Site Check
→ Existing Site Baseline Score
→ Asset Reality Check
→ Sales Eligibility
→ Source Depth
→ Fact Ledger
→ Company Truth
→ Creative Concept Competition
→ Production
```

**Creative Conceptを考える前にSales Eligibilityを通す。**

---

## 7. Golden Sampleの選定ルール

Golden Sampleは単に「面白い会社」を選ばない。

必要条件:
1. 検証したいVisual Authorityが明確
2. 既存サイトなし、または明確な改善余地
3. 公開Factが十分
4. 営業対象として現実的
5. 新LPが既存より良くなる仮説を制作前に説明できる

既存サイトが強い会社を使う場合は、`REDESIGN_CHALLENGE`として別枠にする。
