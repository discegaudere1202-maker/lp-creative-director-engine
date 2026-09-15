# P10 Customer State Transition Reconstruction v1

更新日: 2026-09-15

## 目的

CTAを「相談するボタン」で終わらせず、
**相談前と相談後で顧客の認知状態がどう変わるか**を一画面のFormとして表現する。

## Source-backed reference

対象: 株式会社つぶだてる

Official source:
- https://www.tsubudateru.com/

公開情報として確認したFact:
- キャリアに対するモヤモヤの段階から相談可能
- 転職意思が固まっていない人も相談可能
- 「価値観」を重視している
- 履歴書だけでは表せない人柄や価値観をもとに支援する
- 個人向けサービスは無料
- 企業からの紹介手数料で運営している
- Missionとして「次の一歩を踏み出す人を応援」する

## Big Idea

**「転職したい」が、なくてもいい。**

CTAの前提を「転職意思がある人」に置かない。
会社が実際に許容している相談開始状態を、そのままHeroの入口にする。

## Company Truth → Form

モヤモヤ段階から相談できる
→ BEFORE側を未整理な短文群として散らす

価値観を重視する
→ AFTER側の最初の変化を「価値観が言葉になる」にする

転職意思が固まっていなくてよい
→ AFTERを「転職する」に固定せず、「転職するかを選べる」とする

次の一歩を応援する
→ 状態遷移の終点を「次の一歩が具体になる」にする

つまり、

`Unformed anxiety → Dialogue → Value language → Choice → Concrete next step`

を画面構造そのものにする。

## Art Direction

- BEFOREは少し不規則な配置・角度で、未整理な認知状態を表す
- 中央軸は「相談して整理する」という介入
- AFTERは整列した3段の文章で、認知が整理された状態を表す
- CTAを独立ボタンにせず、画面全体をCTAの意味説明にする
- generic Before/After cardは禁止

## Mobile Re-art Direction

Desktop:
- BEFORE / 相談軸 / AFTERを横並びで一度に比較
- BEFOREの短文は空間的に散らす

Mobile:
- BEFOREを通常の読み順へ戻す
- 中央の縦軸を消し、「相談して、言葉にする」というMobile専用Bridgeを追加
- AFTERを縦に順番で読む

縮小ではなく、比較から物語順へ構造を変更する。

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
- Mobile prose/headline semantic fragments = 0
- Desktop BEFORE fragments remain single-line and inside the BEFORE column
- source-backed state transition remains visible
- Mobile transition axis is re-authored, not scaled

## Current status

Stage: RECONSTRUCTED / QA_RUNNING

まだBenchmark Tournament PASSではない。
COMPETITIVEへ昇格させない。

次:
1. CI 9-width QAをGreenにする
2. 1440 / 390 visual critique
3. Prototype Registryへartifact/test pathを登録
4. M3 Benchmark 3–5件とのBlind Tournament
