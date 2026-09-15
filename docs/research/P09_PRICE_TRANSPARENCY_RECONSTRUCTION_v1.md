# P09 Price Transparency Reconstruction v1

更新日: 2026-09-15

## 目的

Price Transparencyを「料金表を見やすくするUI」ではなく、
**総額が何によって変わるかを理解させるTrust Composition**として再構築する。

## Source-backed reference

対象: 有限会社シーベ

Official source:
- https://sign-ya.jp/menu/

公開情報として確認したFact:
- パネルサイン 400mm × 300mm: 4,158円（税込）
- 面板: アルミ複合板
- 意匠: インクジェット出力 + UVラミネート加工
- 公開価格表にはデザイン・編集などデータ制作費を含まない
- 枚数割引 / 別注サイズの相談が可能
- 看板費用はサイズ・仕様・設置場所によって変わる
- デザインから施工まで一括対応できる

## Big Idea

**見積もりは、条件から見えてくる。**

初稿の「見積もりは、足し算で見える。」はScreenshot Copyとしては強かったが、
価格要因が厳密な加算式であるように誤認させる余地があったため撤回した。

PremiumよりFact Safetyを優先する。

## Company Truth → Form

公開価格 4,158円
→ 価格Anchorとして固定

400mm × 300mm
→ **4:3の実寸比をPrice Anchorの形そのものへ反映**

サイズ / 仕様 / 設置場所で変動
→ 3つのFactorを同じ画面で分解

データ制作費は価格表外
→ 「表示価格 = 依頼全体の総額」ではないことを明示

つまり、

`Published price → Real product dimension → Price drivers → Quote clarity`

を画面構造そのものにする。

## Craft Catch

**400 × 300 mm → 4:3 panel form**

気づかなくても画面は成立するが、実商品の寸法を知ると
Price Anchorの長方形が装飾ではなくCompany/Product Truth由来だと分かる。

この比率は回帰テストでも固定し、将来の自動レイアウト最適化で破壊しない。

## Art Direction

P02のDOCUMENT Translationとは意図的に別方向。

- Card Gridを使わない
- 価格表をそのまま再現しない
- 実寸比のPrice Anchor + 条件分解
- 罫線と数字の組版をAuthorityにする
- Accentは価格の「安さ」ではなく、変動理由の理解へ使う
- 派手な装飾ではなくTrustをScreenshot Peakにする

## 1440px visual critique

初回:
- 左右構成は成立
- ただし内部研究用コピーが露出していた
- 4,158円が商品から浮いていた
- `+ / =` が厳密な計算式に見える危険があった

修正:
- 研究用コピーを顧客向けCopyへ変更
- 4,158円を4:3のPanel Objectへ格納
- `+ / =` を撤回し、条件から見積もりへ進むDirectional Formへ変更
- 3 Factorを `Index / Factor / Explanation / Direction` の4列へ明示

現在:
- Immediate Read: 強い
- Trust: 強い
- Form Causality: 強い
- Owner/Product Specificity: 初稿より改善
- Emotional Pull: 意図的に中程度。Trust Peakとして扱う
- Share Impulse: Benchmark比較前なので未認定

## Mobile Re-art Direction

Desktop:
- Published priceと3 Factorsを横方向の関係として読む
- 4:3 Panel Objectを独立した価格Anchorとして置く

Mobile:
- Published price / Panel Objectを最初に固定
- 3 Factorsを縦に一つずつ理解
- Desktop用Formula Headerを消す
- Mobile専用Summaryを追加

縮小ではなく、理解順を変更する。

## Runtime QA Contract

Widths:
- 320
- 360
- 375
- 390
- 430
- 768
- 1024
- 1280
- 1440

Hard checks:
- horizontal overflow = 0
- prose/headlineのJapanese one/two-character fragment = 0
- semantic fragment = 0
- category labelsは短語を許可するが1行tokenとして維持
- Mobile structure differs from Desktop
- source-backed price logic remains visible
- 400×300のProduct Truthが4:3 Formとして維持される

Local rendered QAでは9幅すべてoverflow 0 / fragment 0まで確認。
CI Greenまでは正式なRuntime QA PASSへ昇格しない。

## Benchmark opponent research

PaynをPrice Transparency / Conversion Actionの研究候補へ追加。

比較したいのは色・レイアウトではなく:
- 料金構造が何秒で理解できるか
- 不安を価格説明でどこまで下げられるか
- CTA前のDecision Clarity
- Mobileで料金ロジックが崩れないか

## Current status

Stage: VISUAL_REVIEWED / CI_PENDING

まだBenchmark Tournament PASSではない。
COMPETITIVEへ昇格させない。

次:
1. CI 9-width QA Green確認
2. Prototype Registryへreproducible artifactとして正式登録
3. M3 Benchmarkが3–5件揃った後に1440 / 390正式Blind Tournament
4. 負けたAxisだけSpecialist Return
