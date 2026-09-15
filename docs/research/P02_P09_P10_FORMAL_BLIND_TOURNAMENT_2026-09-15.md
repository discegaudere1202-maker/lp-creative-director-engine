# P02 / P09 / P10 Formal Blind Tournament

更新日: 2026-09-15

## 判定

| Prototype | Status | Win Rate | Desktop | Mobile | Reviewer A | Reviewer B |
|---|---:|---:|---:|---:|---:|---:|
| P02 Customer-world Translation | PASS | 0.6250 | 0.5000 | 0.7500 | 0.7500 | 0.5000 |
| P09 Price Transparency | PASS | 0.6875 | 0.7500 | 0.6250 | 0.9375 | 0.4375 |
| P10 Customer State Transition | PASS | 0.6250 | 0.6667 | 0.5833 | 0.9167 | 0.3333 |

P02/P10は、前回の0.5833からCTA ZoneのTrust / Conversion Architectureを修正して再評価した。P09は候補の大改修を行わず、同一構造を同じFormal setで確認した。

## Method

各候補をtask-specific M3 opponent setと1440×1000 / 390×844で比較した。Candidate sideはpairごとにseed randomizeし、Reviewer-visible bundleにはopaque item ID・匿名LEFT/RIGHT・screenshotだけを含めた。Identity mappingとprovenanceはbundle外に分離した。

各Benchmark × Viewportには、次の異なるstructured review rolesを付与した。

- Reviewer A: Creative / Art Direction
- Reviewer B: Business Owner / Conversion

これは独立した第三者の人間評価ではない。

## 結果

### P02

- kagami: 0勝 / 1分 / 3敗（candidate win rate 0.1250）
- smarthr-product: 3勝 / 1分 / 0敗（0.8750）
- kintone-product: 3勝 / 1分 / 0敗（0.8750）
- strongest axes: Owner Specificity 1.0000, Emotional Pull 0.7083, Mobile Quality 0.7083
- weakest axes: Trust 0.3333, Conversion Intent 0.3333

経験の事実をCTA近傍へ移し、「状況を聞く → 必要な制度を整理する」を加えた。KAGAMIの早い証拠提示と能力の可視化にはまだ負けるが、CTA前の理由とMobile actionの到達性は改善した。

### P09

- aki-design-price: 3勝 / 1分 / 0敗（0.8750）
- jimdo-hp-pack: 2勝 / 1分 / 1敗（0.6250）
- rals-homepage-price: 3勝 / 1分 / 0敗（0.8750）
- studio-price: 1勝 / 1分 / 2敗（0.3750）
- strongest axes: Distinctness 1.0000, Owner Specificity 1.0000, Share Impulse 0.9062
- weakest axes: Conversion Intent 0.3125

400×300mmと4,158円（税込）が、価格ドライバー・対象・判断材料とつながっているため、Business Reviewerが0.4375でも総合PASSを維持した。数字の量ではなく、判断可能性が強みである。

### P10

- carigaku-career: 1勝 / 1分 / 2敗（0.3750）
- sell-step-career: 2勝 / 2分 / 0敗（0.7500）
- lfu-career: 2勝 / 2分 / 0敗（0.7500）
- strongest axes: Owner Specificity 1.0000, Distinctness 0.8750, Share Impulse 0.8750
- weakest axes: Trust 0.3333, Mobile Quality 0.5833

無料・紹介手数料という既存事実をCTA Zoneに残し、「相談では、モヤモヤを聞き、価値観を整理する」「転職するかは、相談してから」を追加した。心理的安全性とConversion Intentは改善したが、人・資格・守秘・勧誘方針などの実在証拠がないためTrustはまだ低い。

## Axis別比較

| Prototype | Immediate | Distinct | Owner | Hierarchy | Craft | Emotion | Trust | Share | Mobile | Conversion |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| P02 | 0.5417 | 0.6667 | 1.0000 | 0.5833 | 0.6667 | 0.7083 | 0.3333 | 0.6667 | 0.7083 | 0.3333 |
| P09 | 0.7812 | 1.0000 | 1.0000 | 0.6875 | 0.8438 | 0.7812 | 0.5000 | 0.9062 | 0.6250 | 0.3125 |
| P10 | 0.6667 | 0.8750 | 1.0000 | 0.6250 | 0.7083 | 0.6667 | 0.3333 | 0.8750 | 0.5833 | 0.5000 |

## Evidence / provenance

- Candidate Capture Run 11: `34962756565`
- Candidate Artifact: `10393223767`, digest `sha256:97721d230783c019611c0f92c26ea0813d738f309875bfdca05169a47b777ee8`
- P02 source SHA256: `20d5306d019b2fa3ac984dc1e0bc819ae22e7b79439827e2b9fa6ca638ccab2e`
- P10 source SHA256: `7a41d812ad034986b6a6d08483ee4dcc61ca62b14d7705eb59e20bf1ef5d1971`
- Benchmark Run 6 Artifact: `10388641096`, digest `sha256:7cb1a74e24fa279af155310e0ddb4b027498b27de1ebd559bd8711993830e8fa`
- Benchmark Run 8 Artifact: `10389977402`, digest `sha256:b582e809bb4464c437ac0094ec239f1f0e4bfc266057a9950beb377c741acaee`
- Candidate-side randomization seed and identity mapping: generated in the Work bundle and stored outside the reviewer-visible bundle.

## Interpretation

P02/P10はFormal Gate（Win Rate >= 0.60）を通過したが、Trust / Business Reviewerはまだ品質上限の研究対象である。`UPPER_MODEL_REVIEW_CANDIDATE` として、対立する視点の再評価を推奨する。Formal PASSをもって即座にGolden Sample 03へは進めない。
