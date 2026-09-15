# Benchmark Tournament Batch 01 — Preliminary v1

Updated: 2026-09-15

> Historical naming note: the `P01 / P03 / P05 / P15` identifiers in this document are **LEGACY PRE-REGISTRY prototype IDs**. They must not be mapped to the current `config/prototype_registry_v1.json` P01–P12 IDs. This document is retained as research history only.

対象Prototype（legacy pre-registry）:
- LEGACY-P01 Japanese Monumental Type v3
- LEGACY-P03 Fact-to-Visual Hero v3
- LEGACY-P05 Evidence Monument v3
- LEGACY-P15 Quiet Chapter v3

注意:
これは正式なBlind Tournament前のCreative Red Team preliminary。
Reference画像の解像度・Frame jobが完全一致していないため、最終Supremacy PASSではない。

References considered:
- StartPass — bold typography / understand→act
- Acompany Recruit — bold UI / professional×playful
- 佐久間宣行事務所 — personality-specific visual language
- RYDEN — minimalist typography / whitespace / motion
- Chakin — category reframe / evidence / conversion
- ベイジ採用 — deliberate visual restraint / content-first

---

## LEGACY-P01 Japanese Monumental Type

### Preliminary
**REVIEW — close, not Supremacy yet**

### Strong
- 高級感/編集感は一定水準
- Hero copyが一瞬で読める
- Translation panelによってMahoraの価値と接続
- Mobileも別Compositionとして成立

### Why not PASS
Reference群は、Typographyだけでなく
**ブランド固有の“癖”や態度が一画面で残る。**
LEGACY-P01はまだ「良いEditorial design」と説明できてしまう。

### Required upgrade
Mahora固有のCraft Catchが必要。
候補:
- 専門語→平易語の文字幅/weight/line behaviorの変化
- 注釈/翻訳記号を独自Grammar化
- “どなたにでも分かりやすく”がType mechanicsへ影響

Generic Japanese vertical typeを追加するだけでは不可。

---

## LEGACY-P03 Fact-to-Visual Hero

### Preliminary
**REWORK**

### Strong
- 写真なしでも清潔なPremium direction
- FactとPromiseが同一Frameにある
- v3 Mobile semantic breakは解消

### Why not PASS
現在の造形:
large serif + red accent + bottom stat row
は、士業/コンサル/ブランドサイトへ広く転用可能。

**Factを置いたが、Factが造形を生成していない。**

### Required upgrade
20年 / 300社 / 分かりやすい説明が、
layout / repetition / grouping / motionの原因になること。

新しい問い:
「社名と数字を差し替えたら別会社に使えるか？」
YESならFAIL。

---

## LEGACY-P05 Evidence Monument

### Preliminary
**CRAFT STRONG / OWNER-SPECIFICITY REVIEW**

### Strong
- Batch 01で最も高価な制作物に見えやすい
- Stat Card臭がない
- Desktop/MobileともHierarchyが強い
- Asset-light sampleで使いやすい

### Why not PASS
20 / 300+の巨大組版だけなら、
多くのProfessional Serviceへ転用可能。

### Required upgrade
数字そのものではなく、
**20年で扱ってきた問題の幅 / 300社の個別性 / “分かる言葉”への整理**を
visual behaviorとして統合する。

例の方向:
- 300 fragments → 6 understandable issue groups
- years / casesをTranslation outputへ収束

ただしDots/Count-upをGeneric data-vizとして使うだけは禁止。

---

## LEGACY-P15 Quiet Chapter

### Preliminary
**ROLE PASS / Supremacy score対象外**

### Strong
- v3 Desktop/MobileでSemantic line shape安定
- Section自体が休符として成立
- CTA前の心理負荷を下げる可能性

### Why no Supremacy competition
Quiet ChapterのJobはShare Impulseではない。
Peak Frame用の5問で競わせると誤評価になる。

### New benchmark questions for Quiet
1. 前Sectionの情報を吸収できるか
2. スクロールを止めすぎないか
3. 次のSectionへの期待が残るか
4. “何もない”ではなく意図的に見えるか
5. Mobileでも呼吸が残るか

---

# Key finding

**Craft Quality ≠ Owner-specific Quality.**

Batch 01は、レイアウト/タイポ/余白の質を上げるだけでは
「AIっぽい高品質テンプレ」から完全には抜けられないことを再確認した。

次Iterationでは:
`Company Truth → visual mechanics`
の結合を強制する。

---

# Gate amendment candidate

## Form Causality Gate

Premium Frameでは、主要な造形判断の最低2つについて
「どのCompany Truthが原因か」を説明できること。

Examples:
- headline behavior ← explanation philosophy
- repeated fragments ← number/variety of cases
- material crop ← actual material property
- transition ← actual business process

FAIL:
「Premiumに見えるから」
「今っぽいから」
「参考サイトがそうだから」

このGateは次Prototype batchで検証後、正式化する。