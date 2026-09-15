# SME Craft Prototype Batch 02 — Findings

更新日: 2026-09-15

対象:
- P07 Owner Voice → Typography Rhythm
- P08 Service Area → Spatial Composition
- P09 Price Transparency → Trust Composition
- P10 Before Contact → After Contact
- P11 Real Photo Crop Direction
- P12 Mobile-only Re-art Direction

---

## P07 — Owner Voice → Typography Rhythm

判定: CONDITIONAL PASS

強み:
- 代表者本人の言葉が強い会社では、Quote Cardより深く人格を出せる
- 行長 / 句読点 / 間をBrand Rhythmへ昇格できる

注意:
- 営業サンプル時点で本人写真がない場合、Portrait Placeholderを見せてはいけない
- 公開発言が弱い会社へ“それっぽい名言”を作るのは禁止

Sales Sample運用:
- 本人写真なし → Typography-only variant
- 契約後 → OWNER_PORTRAIT Slotを同じFrameへ差し込む

Rule:
`Owner voice must be source-backed before it becomes typography.`

---

## P08 — Service Area → Spatial Composition

判定: HOLD

強み:
- 「地域密着」を抽象コピーではなく範囲/距離として扱える
- Local businessとの相性は良い

弱点:
- 円を置いただけではVenn図テンプレに見える
- 福岡市 / 福岡県 / 九州のような包含関係を正確な地理表現と誤認させる危険

採用条件:
- 実際のService Areaが確認可能
- 地図 / 所要距離 / 訪問頻度 / 拠点との関係など、現実のSpatial Truthがある

Rule:
`Locality needs spatial truth, not decorative circles.`

---

## P09 — Price Transparency → Trust Composition

判定: PASS Prototype

強み:
- 価格表をCard GridにしなくてもTrustを作れる
- 金額そのものより「何で変動するか」を理解させられる
- 依頼前の不安を直接下げる

向く案件:
- 公開料金あり
- 基本料金 + 変動条件
- 見積型だが変動要因を説明できる

Fact Safety:
非公開価格を推測しない。
金額が分からない場合は“価格決定ロジック”も確認できる範囲だけ。

Rule:
`Price transparency = decision clarity, not cheapness.`

---

## P10 — Before Contact → After Contact

判定: PASS Prototype

強み:
- 顧客の心理変化そのものをConversion Narrativeへできる
- 士業 / 修理 / 建設 / 医療周辺 / B2Bなど「何を聞けばいいか分からない」業種に強い
- CTAを“問い合わせ”ではなく“次の心理状態”として設計できる

弱点:
Before側の悩みを勝手に作るとGeneric Pain Marketingになる。

採用条件:
- FAQ / 口コミ / 公開情報 / ヒアリングから実際の障壁を確認

Rule:
`CTA should move the customer to a clearer state.`

---

## P11 — Real Photo Crop Direction

判定: SYSTEM PASS

これは完成Frameではなく撮影/Asset Contract。

重要:
営業サンプル時点で以下を決める。
- subject
- relation
- distance
- negative space
- copy safe zone
- mobile crop
- replacement rule

これにより契約後の「写真をもらったらLayoutが崩れた」を防ぐ。

Rule:
`Art direction happens before the photo arrives.`

---

## P12 — Mobile-only Re-art Direction

判定: PASS Principle

強み:
- Desktopの左右分割をMobileで縦に縮小するだけ、を禁止できる
- Visual first / Copy firstの順番をMobileで再判断できる

重要:
同じCreative Conceptを守れば、
- order
- crop
- type scale
- alignment
- motion sequence
を変えてよい。

Rule:
`Responsive means concept-preserving re-art-direction, not geometric shrinking.`

---

# Batch 02総括

実戦投入優先:
1. P09 Price Transparency
2. P10 Customer State Transition
3. P12 Mobile Re-art Direction

System Contract:
4. P11 Photo Direction

条件付き:
5. P07 Owner Voice
6. P08 Spatial Locality

---

# Quality Ceilingへの追加原則

## A. TrustもScreenshot-worthyになりうる
派手なVisualだけをPeakと定義しない。
価格や不安の解消を非常に美しく整理した画面もPremium Peakになり得る。

## B. Local SMEでは“固有の仕事の仕方”が最重要Asset候補
写真がなくても、
- 誰が対応
- どこまで対応
- どう価格が決まる
- 相談後どうなる
をFormへできる。

## C. 営業サンプルから納品版へのUpgradeは事前設計する
写真差替え後にDesignを救済するのではなく、営業Sample時点でReplacement Contractを持つ。

---

# 次の優先研究

- Benchmark Blind TournamentをPrototypeへ実施
- P02 / P04 / P05 / P09 / P10をCore Prototype候補として比較
- 390pxでのHeadline shapeを追加検証
- Client Evidence Slotとヒアリング質問の対応表をまだ作り込まず、Slot種類だけ蓄積
