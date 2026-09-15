# Prototype Lab Batch 01 Findings v1

Updated: 2026-09-15

対象:
- P01 Japanese Monumental Type
- P03 Fact-to-Visual Hero
- P05 Evidence Monument
- P15 Quiet Chapter

同一のMahora公開事実を使い、Craft変数だけを変えて検証した。
Desktop 1440 / Mobile 390を必ず別Art Directionとして確認。

---

## Iteration history

### v1
Desktopは一部成立したが、Mobileで意味単位が崩壊。
例:
- 労務の疑問 / を、
- 制度名ではな / く、
- 何の手続きが必 / 要？

学び:
CSS縮小ではPremium Mobileにならない。

### v2
Mobile専用コピー/構図を導入。
しかし:
- P03で「ではな / く。」が残る
- P15はDesktop側で「なく、」「を。」が孤立
- P05巨大数字と補助ラベルが干渉

学び:
Desktop/Mobileを分けるだけでは足りない。
Semantic Lineそのものに幅Contractが必要。

### v3
Semantic Lineをnowrap単位にし、長い行はMobile専用サイズへ再調整。
P05は数字占有率を下げて補助ラベルを独立。
P15はDesktopの列幅・Type Scale自体を再構成。

---

# P01 Japanese Monumental Type

## Result
**CRAFT DIRECTION PASS / Benchmark Supremacy pending**

## Strong points
- Gothic + Minchoの役割差が意味と一致
- Hero copyの意味単位がPC/Mobileで維持
- 左の巨大Typeと右のTranslationが同じBig Ideaを支える
- Mobileでは上下2章に変え、単なる縮小を回避

## Weak points / next
- 右側の縦組みは日本語らしいが、理由なく別案件へ流用するとStyle化する
- Benchmarkと比べた時の固有性/高級感は未検証

## New rule
Mixed Typefaceを使う場合、Font差はMeaning差を持つこと。
「高級感のため明朝」は禁止。

---

# P03 Fact-to-Visual Hero

## Result
**STRUCTURE PASS / Benchmark Supremacy pending**

## Strong points
- Public Factだけでも写真なしHeroを成立させる方向性
- Fact 20 / 300+ とValue Promiseを同じFrameに配置
- Mobile v3でHeadline semantic integrityを確保

## Failure discovered
v2ではMobileの1行を42pxのまま保持し「ではな / く。」が発生。

## Fix
長いMeaning ChunkだけMobileでType Scaleを落とした。
すべてのHeadlineを一律サイズにしない。

## New rule
Semantic Line Contract:
`meaning chunk > available line width` の場合、
文字を途中で折るのではなく、そのChunkだけScale/Tracking/Compositionを再Art Directionする。

## Fact safety improvement
疑似Evidenceとして見える「01」を削除し、定性的なValue表現へ変更。
数字に見える装飾はEvidence領域で使わない。

---

# P05 Evidence Monument

## Result
**STRONGEST CANDIDATE / Benchmark Supremacy pending**

## Strong points
- 20 / 300+をStat Cardではなく画面そのものへ昇格
- Dense Evidenceではなく、巨大数字＋説明の疎密で信頼を作る
- Mobileでも20と300+のHierarchyが崩れない
- 色・余白・Typeだけで成立し、Asset-light営業サンプルとの相性が良い

## Failure discovered
初期版は巨大な20のline boxが補助ラベルと干渉。

## Fix
- 数字占有率を少し下げる
- line-heightを物理的なglyph bboxに合わせる
- labelを独立したblock flowへ戻す

## New rule
Evidence Monumentでは「数字を大きくすれば良い」ではない。
Unit / meaning / proof sentenceが数字の物理bboxと衝突しないこと。

---

# P15 Quiet Chapter

## Result
**RHYTHM COMPONENT PASS / Screenshot Peak対象外**

## Strong points
- Motion/Decorationなしで一度ユーザーを止める
- CTA前の心理整理として有効
- Mobileでも余白を主役として維持

## Failure discovered
v2 Desktopで、Grid幅不足により明示brの内部で再wrapした。
「制度名ではな / く、」「状況 / を。」

## Fix
- Quiet column自体を広げる
- Type Scaleを少し下げる
- Semantic lineをnowrapにする

## New rule
Quiet ChapterをScreenshot Peakと同じ基準で評価しない。
役割はShare Impulseではなく:
- absorption
- pause
- emotional reset
- next CTA readiness

Quietの成功は、前後Sectionとの関係で判定する。

---

# Batch 01 Laws added

1. **Responsive typography is semantic, not geometric.**
2. Headline全体ではなく、Meaning ChunkごとにType Scaleを変えてよい。
3. `br`を入れただけではsemantic lineは保証されない。内部再wrapを検査する。
4. Evidence領域で装飾的な数字を使わない。Factとの誤認を避ける。
5. Screenshot PeakとQuiet Chapterを同じScorecardで評価しない。
6. Giant Typeはglyph bbox / line box / unit labelまで実レンダリングで確認する。
7. MobileはDesktopより小さいだけでなく、Hierarchyの順番自体を変えてよい。
8. Prototypeが3 revision未満でPremium扱いになるケースは例外とする。

---

# Status

このBatchは最終デザイン集ではない。
次は同じ4 Prototypeを日本Benchmark FrameとBlind比較し、
見劣りする要素を特定する。

その後:
- P07 Photo Crop
- P17 Mobile Re-Art Direction
- P19 CTA Emotional Closure
- P21 Sales State → Enriched State
へ進む。
