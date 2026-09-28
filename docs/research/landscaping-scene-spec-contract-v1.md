# 造園業 Scene Spec Contract v1

更新日: 2026-09-28
Owner: Sarah PM
Status: READY_FOR_TARGET

## Purpose

造園業サンプルでScene SpecがRenderer任せの「雰囲気指定」に戻らないよう、HTML実装前にCreative / Visual / Conversion判断を構造化する。

---

## Required top-level fields

```yaml
company_truth:
  name:
  location:
  service_area:
  primary_services: []
  verified_strengths: []
  verified_proof: []
  unknowns: []

archetype:
  primary: MAINTENANCE_FIRST | DESIGN_REFORM_FIRST | PREMIUM_DESIGN_FIRST | GENERAL_B2B_MIXED
  secondary:

conversion:
  primary_action:
  secondary_action:
  verified_claims: []
  prohibited_unverified_claims: []

creative_direction:
  one_sentence:
  primary_visual_authority: []
  secondary_visual_authority: []
  anti_template_rules: []

scene_system:
  section_order: []
  global_grid:
  rhythm:
  material_language:
  image_language:
  type_system:
  boundary_system:
  motion_system:

asset_provenance:
  actual_works: []
  people: []
  logo: []
  stock_or_generated_mood: []
  forbidden_as_proof: []
```

---

# Section contract

各sectionは最低限以下を持つ。

```yaml
- id:
  marketing_job:
  question_to_answer:
  evidence_used: []
  copy:
    eyebrow:
    headline:
    body:
    proof_labels: []
    cta:
  composition:
    family:
    columns:
    dominant_area:
    tension:
    whitespace:
    overlap:
  media:
    source:
    provenance: ACTUAL_WORK | ACTUAL_PERSON | PUBLIC_COMPANY_ASSET | MOOD_ONLY
    crop_intent:
    focal_point:
    may_be_labelled_as_work: true|false
  material:
    palette_role:
    texture:
    lighting:
  boundary:
    owner:
    geometry:
    overlap_px_or_ratio:
  motion:
    trigger:
    layers: []
    meaning:
  responsive:
    mobile_priority:
    stack_order: []
    crop_change:
```

---

# Visual Authority Vocabulary

造園系で優先して利用可能:

- `PLACE` — 完成した庭 / 居場所 / 暮らし
- `CRAFT` — 剪定 / 石組 / 植栽 / 手仕事
- `MATERIAL` — 石 / 土 / 苔 / 樹皮 / 水 / 金属 / 木
- `TRANSFORMATION` — Before / After
- `SEASON` — 季節 / 経年 / 時間
- `ARCHITECTURE_RELATION` — 建築と庭の関係
- `PERSON` — 庭師 / 代表 / 職人
- `TRUST` — 価格 / 資格 / 対応範囲 / 施工体制
- `SYSTEM` — 設計→施工→管理の一貫体制

Primaryは原則2つ以下。全部を主役にしない。

---

# Archetype starter logic

## MAINTENANCE_FIRST

Hero responsibility:
- 何を直せる / 整えられるか
- どこで頼めるか
- 安心して見積できるか

Early proof:
- Before / After
- Price / Estimate policy
- Area
- Human / Craft

Visual form:
- Transformation比重を高くする
- 過度なBrand manifestoをHero直後に置かない

## DESIGN_REFORM_FIRST

Hero responsibility:
- どんな暮らし / 庭を作れるか
- 写真でDesign rangeを示す

Early proof:
- Signature works
- Building + garden relation
- Planning process
- Budget navigation

Visual form:
- PLACE + ARCHITECTURE_RELATION
- Worksをgalleryではなくstoryとして扱う

## PREMIUM_DESIGN_FIRST

Hero responsibility:
- 一目で作品性 / 審美性を示す

Early proof:
- one signature project
- material / detail
- philosophy
- designer / craftspeople

Visual form:
- large photo field
- asymmetric editorial composition
- restrained typography
- motionは空間のdepth / timeを補助

## GENERAL_B2B_MIXED

Hero responsibility:
- 何を相談できる会社か

Early proof:
- Needs → Solutions
- Cases by scale / use
- credentials / system

Visual form:
- WORLDだけに寄せずSYSTEM / CONSULTABILITYを明示

---

# Boundary Rule

画像→HTMLで発生した境界認識問題を再発させない。

Scene Spec段階で各境界について以下を決める。

```yaml
boundary:
  owner: lower_section
  type: flat | diagonal | bezier | mask | media_overlap
  path_definition:
  overlap:
  mobile_behavior:
```

同じ境界を上下sectionが別々に持たない。

---

# Motion Rule

Motionは最低限 `meaning` が説明できるものだけ採用。

例:

- Before / After reveal → 施工変化を理解する
- plan line draw → 設計から空間へ至る流れ
- slow parallax → 庭の奥行き
- light drift → 木漏れ日 / 時間の移ろい
- sequential works reveal → 視線移動 / 園路

`見栄えがいいから` だけのMotionは禁止。

---

# Proof Safety

`asset_provenance` と `verified_claims` はRendererで消せないHard Gateとする。

以下の組み合わせは禁止:

- MOOD_ONLY image + `施工事例`
- 未確認の数字 + 実績訴求
- 架空のCustomer Voice
- 未確認の無料 / 値引き / 追加費用なし
- Awardの推測

---

# Quality Exit Gate

Scene Specの段階で以下にYESでなければHTMLへ進めない。

1. Company TruthがFormの原因になっている
2. Heroを他社名へ置換すると違和感が出る
3. Primary Visual Authorityが明確
4. Early proofがArchetypeと一致
5. Actual WorksとMood imageを区別できる
6. CTA claimがPublic Evidenceと一致
7. Section boundaryが構造データとして定義済み
8. Motionに意味がある
9. Mobile priorityが定義済み
10. Rendererが大きなCreative判断を発明する必要がない
