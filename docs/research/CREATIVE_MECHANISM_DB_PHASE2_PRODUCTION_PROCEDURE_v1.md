# Creative Mechanism Database — Phase 2 Production Procedure v1

Phase 2は、Phase 1 Architecture Review後に開始する。開始条件は、配分表・Rubric・Evidence grade・Dedupe policy・Safety gateの承認である。

## 実行単位

1. `reference_lp`候補を1件登録
2. Original / Award / Portfolio等の出所を分離
3. Canonical URLとCampaign fingerprintを付与
4. Desktopと390px前後を観察
5. Scene単位でMechanismを採掘
6. Design / Conversion / Motion / Feasibilityを別採点
7. Strong / Deep / Hold / Rejectへ分類
8. Mechanism Evidenceを既存Registryへ統合
9. Compatibility EdgeとRecipe候補を更新
10. Batchごとに重複・Mobile・Evidence SafetyをQA

## Batch設計

初回は100件を1 Batchとし、次を出力する。

```text
references.jsonl
scene_observations.jsonl
evaluations.jsonl
mechanism_evidence.jsonl
mobile_evidence.jsonl
batch_qa.json
```

100件を機械的にStrongへ送らない。BatchごとにArchetype・Industry・Source classの偏りを確認する。

## Discovery query設計

検索語はIndustry単語だけで作らない。

```text
<industry> + <conversion model> + <source class>
<archetype> + <authority> + <web design / site / LP>
<scene job> + <interaction mechanism> + <original site>
```

例：

```text
local service consultation original website people place trust
B2B manufacturing process proof website Japan
product landing page bounded price scope official
recruiting site people work reality mobile web award
scroll storytelling process proof official brand website
```

## Deep Annotation minimum

Deepは最低限、Hero / first viewport、Section Headline、Body / Transition、Proof、CTA、Navigation、Mobile、Motion Job、Transfer Note、Riskを持つ。1 LPに複数Sceneがある場合、`unique_lp_count`と`component_count`を分ける。

## Mechanism promotion

Candidate → Supportedの最低条件：

- 独立LP 3件以上
- 少なくとも2つのArchetypeで再現、またはIndustry限定でScope明示
- Marketing JobとUser Effectが説明可能
- Referenceの見た目をコピーせず、別素材・別Colorでも成立する説明が可能
- Mobile Recomposition ruleがある
- Evidence / feasibility / accessibility riskが記録済み

Supported → Canonicalの追加条件：

- 5件以上の独立LP、または4Archetype以上の再現
- Compatibility edgeを最低1つ登録
- Recipe dry runで別Company Truthに2回以上転用
- Human / QA reviewでTemplate Resemblance Riskが許容範囲

## Recipe dry run

同一のCompany Truth・Sales Storyから次の3レシピを生成し、比較する。

```text
1. Conversion-safe: Evidence / clarity / low implementation risk
2. Authority-led: primary Creative Authorityを強くする
3. Novelty-led: Creative benchmark mechanismを1つだけ導入
```

3案が色替え程度にしか見えない場合、Mechanism組み合わせの多様性が不足しているか、Scene SpecがTemplateへ退化している。RecipeをRejectして原因を記録する。

## Batch QA hard gates

- Original sourceが無いReferenceはStrong不可
- Award名・ブランド名を品質根拠にしない
- 未確認の価格、資格、工程、実績、顧客結果を生成しない
- 390pxでHero / CTA / primary messageが残る
- Motion disabledでも意味と操作が残る
- `prefers-reduced-motion`に対応する
- LCP / INP / CLSを測定またはRisk記録する
- 画像・動画に権利・代替テキスト・容量の注記がある
- 同一Campaign variationを独立LPとして数えない
- 既存Mechanismとの重複・統合候補を確認する

## 停止条件

ArchetypeごとにLast 30 Deepを見て、

```text
new_canonical_mechanism <= 1
existing_reinforcement_ratio >= 0.8
new_candidates_are_mergeable = true
mobile_and_local_sme_coverage = sufficient
```

を満たしたら、そのArchetypeのDiscoveryを止める。全体件数を埋めるために新規探索を続けない。
