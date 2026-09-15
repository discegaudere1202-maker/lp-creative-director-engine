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

**見積もりは、足し算で見える。**

ただし「固定の計算式が存在する」と誤認させない。
画面上の足し算は、総額を動かす要因を理解するためのVisual Grammarである。

## Company Truth → Form

公開価格 4,158円
→ 価格Anchorとして固定

サイズ / 仕様 / 設置場所で変動
→ 3つのFactorを同じ画面で分解

データ制作費は価格表外
→ 「表示価格 = 依頼全体の総額」ではないことを明示

つまり、

`Published price → Price drivers → Quote clarity`

を画面構造そのものにする。

## Art Direction

P02のDOCUMENT Translationとは意図的に別方向。

- Card Gridを使わない
- 価格表をそのまま再現しない
- 大きな価格Anchor + 一本の計算構造
- 罫線と数字の組版をAuthorityにする
- Accentは価格の「安さ」ではなく、変動理由の理解へ使う
- 派手な装飾ではなくTrustをScreenshot Peakにする

## Mobile Re-art Direction

Desktop:
- Published priceと3 Factorsを横方向の関係として読む

Mobile:
- Published priceを最初に固定
- 3 Factorsを縦に一つずつ理解
- Desktop用Formula Headerを消す
- Mobile専用Summaryを追加

縮小ではなく、理解順を変更する。

## QA Contract

Runtime widths:
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
- Japanese one/two-character line fragments = 0
- semantic fragment = 0
- Mobile structure differs from Desktop
- source-backed price logic remains visible

## Current status

Stage: RECONSTRUCTED / QA_RUNNING

まだBenchmark Tournament PASSではない。
COMPETITIVEへ昇格させない。

次:
1. CI 9-width QA
2. 1440 / 390 visual critique
3. Screenshot Peak specialist pass
4. M3 Benchmarkが3–5件揃った後に正式Blind Tournament
