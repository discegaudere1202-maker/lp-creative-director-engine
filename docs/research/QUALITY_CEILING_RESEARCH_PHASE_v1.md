# Quality Ceiling Research Phase v1

Updated: 2026-09-15
Project: LP制作事業

## 0. North Star

AI利用・自動生成であることは顧客価値と無関係。
目標は、営業サンプルの時点で次の感想を生むこと。

- 「これ、うちのためにここまで作ったの？」
- 「AIで作ったとは到底思えない」
- 「この一画面を誰かに見せたい」
- 「正式版はどうなるんだろう」
- 「100万円払ってでも、この品質で作りたい」

契約後は営業サンプルを作り直さない。
本人写真・実績・代表者の言葉・事例などClient Evidenceを入れることで、
営業サンプルのArt Directionを壊さずDelivery 100万円Gateまで引き上げる。

## 1. 今の課題

現在のEngineは下限品質の制御がかなり強くなっている。

- Fact Safety
- Responsive QA
- Line-break QA
- Screenshot Peak
- Pixel Rhythm
- Motion restraint
- Owner-specificity

しかし、これらは「事故を防ぐ」能力が中心。
森人の試作で、Hard Gateを通ることと市場で一流に見えることは別だと確認した。

次は上限品質を上げる。

## 2. Research Principle

### 2.1 Frame-first
フルLP研究より、強い一画面を大量に比較する。

### 2.2 Relative quality
内部スコアだけでPASSさせない。
日本の一流サイトと並べ、相対的に見劣りしないかを判定する。

### 2.3 Role separation
Creative Director / Copy / Typography / Photo / Motion / CRO / Front-end / Red Team を別工程にする。

### 2.4 Sales reality first
営業対象は原則:
1. NO_WEB
2. WEAK_WEB
GOOD_WEBは営業対象外。研究Benchmarkとしてのみ使用。

## 3. Benchmark Corpus

目標: 100 Screenshot-worthy Frames

### Buckets
- Hero / First View: 20
- Material / Craft / Product: 15
- Person / Philosophy / Editorial: 15
- Evidence / Data / Proof: 15
- Place / Sensory / Photography: 15
- CTA / Conversion / Objection: 10
- Asset-light / Illustration / Typography: 10

同一サイトを複数Frameで使ってよい。
目的はサイト数ではなく「一画面のクラフト」を学ぶこと。

## 4. Initial source corpus

優先して分析する日本事例:
- 佐久間宣行事務所 / Goodpatch
- 集英社 2026年度採用
- ニッカウヰスキー
- 竹中庭園緑化
- 大丸松坂屋 百様図
- WRITING & DESIGN
- AYANA BALI
- KOKUYO
- 東急 新卒採用
- 菁文堂
- 藤原印刷
- 日進化成
- 大松工業
- 吉田水産
- 株式会社ハーツ
- RYDEN
- gmlabs
- MeUMU
- StartPass
- SEVEN ENGINEERING JAPAN
- Shupatto
- Chakin
- Yoom
- Studio.Business
- NPO法人アクション
- IMA
- 文化ノ台所

## 5. Per-frame observation schema

各Frameで必ず記録:

### Strategy
- user state before frame
- job of frame
- dominant message
- proof
- next desired action

### Creative
- Big Idea
- Visual Authority
- memorable device
- company-specific reason

### Typography
- hierarchy
- headline line shape
- contrast
- alignment
- Japanese/Latin relationship

### Composition
- content width mode
- dominant object area
- negative space
- asymmetry
- visual tension

### Asset Direction
- photo / illustration / product / material / data
- distance
- crop
- light
- texture
- authenticity

### Motion
- business verb
- duration class
- trigger
- hold
- stillness
- reduced-motion equivalent

### Rhythm
- energy
- density
- peak / quiet
- transition in/out

### Conversion
- CTA presence
- psychological state
- objection removed
- proof proximity

## 6. Craft Prototype Lab

100 Frameを観察した後、24〜30個の小さなPrototypeを作る。

- Japanese Typography: 5
- Photo Crop / Art Direction: 4
- Material / Physical Motion: 4
- Asset-light Premium Visual: 5
- Evidence as Design: 4
- CTA / Objection / Conversion: 4
- Section Transition / Quiet: 4

Prototypeは会社LPではない。
1 viewportの完成度だけを競う。

## 7. Benchmark Supremacy Tournament

Prototype / Golden Sampleは毎回:
- Desktop 1440
- Mobile 390

で同系統の日本トップ3〜5Frameとブラインド比較する。

比較質問:
1. 一番高価な制作物に見えるのはどれか
2. 一番会社固有に見えるのはどれか
3. 5秒後に覚えているのはどれか
4. 誰かに見せたいのはどれか
5. 一番続きを見たいのはどれか

自社Frameが明確に下ならFAIL。
内部スコアが高くても関係ない。

## 8. Golden Sample restart criteria

Quality Ceiling研究後、Golden Sample 03以降を再開する。

対象:
- NO_WEBを最優先
- 次にWEAK_WEB

Visual Authorityを分散:
- MATERIAL / CRAFT
- PLACE / SERVICE
- SENSORY / FOOD
- PERSON / PROFESSIONAL
- PRODUCT / BEHAVIOR
- DATA / B2B

## 9. Exit criteria from research phase

次の条件を満たすまで「1000件量産最適化」を優先しない。

- 100 Frame catalog completed
- 24+ Craft prototypes
- Benchmark Supremacy rule stable
- 3 NO_WEB/WEAK_WEB Golden Samples pass
- 2+ Screenshot Peak per sample
- Desktop/Mobile Supremacy check pass
- Sales Sample Completion Contract validated
- Client Evidence upgrade slots defined
- Delivery transformation tested at least once

## 10. Core rule

自動化率を品質より先に上げない。

まず一度、
「この品質なら100万円でもおかしくない」
という上限を作る。

その判断を分解してEngineへ戻し、
それから速度と件数を上げる。
