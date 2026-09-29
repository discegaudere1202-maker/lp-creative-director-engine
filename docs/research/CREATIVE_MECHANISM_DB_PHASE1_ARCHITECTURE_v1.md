# Creative Mechanism Database Project

## Phase 1 — Creative Mechanism DB Architecture v1

更新日: 2026-09-29  
Status: **ARCHITECTURE_READY_FOR_REVIEW**  
Owner: しゅん  
PM: サラ  
Research: 澪

## 1. Phase 1 の結論

Phase 1では、LPを「業界別テンプレート」や「POP / Luxury / NaturalのようなStyle」として保存しない。

保存単位を次の5層に分離する。

```text
Reference LP
  └─ Scene Evidence
      └─ Creative Mechanism
          └─ Compatibility / Constraint
              └─ Combination Recipe
                  └─ Scene Spec
```

最終Production Flowは次の通り。

```text
Company Truth
 → Buyer / Sales Story
 → Creative Profile
 → Mechanism Retrieval
 → Compatibility Solver
 → Mechanism Combination Recipe
 → Scene Spec
 → HTML / CSS / Motion
 → Desktop + Mobile + Conversion QA
```

### Phase 1で確定した原則

1. Reference LPは実装用テンプレートではなく、再利用可能なMechanismの証拠源である。
2. 1 LP = 1 Styleとして保存しない。1 LPから複数Scene Evidenceを抽出し、同一Mechanismの再現例として扱う。
3. Award評価とConversion評価を分離する。有名ブランド、受賞歴、見た目の派手さだけではStrong判定しない。
4. Creative AuthorityはColorや雰囲気ではなく、顧客が信頼する「何を根拠にその表現が成立しているか」として扱う。
5. Motionは装飾ではなく、注意・理解・順序・期待・ProofのいずれかのJobを持つ場合のみ採用する。
6. Mobileは縮小版ではない。保存するMechanismに、DesktopからMobileへのRecomposition Ruleを必須化する。
7. Low-evidence事業者には、実績・資格・工程・数値・顧客の声を推測して付けない。UnknownはUnknownとして扱い、Evidence-safeなMechanismだけを選ぶ。

## 2. DBの正規化モデル

### 2.1 Entity

| Entity | 役割 | 必須キー |
|---|---|---|
| `reference_lp` | 参照対象のLP / Webページ | `reference_id`, canonical URL, source class |
| `source_evidence` | 公式ページ・Award・Portfolio等の根拠 | `source_id`, URL, source role, captured date |
| `scene_observation` | Hero / Proof / CTA等の画面単位観察 | `scene_id`, reference ID, viewport, evidence |
| `mechanism` | 再利用可能な表現上の因果メカニズム | `mechanism_id`, category, purpose |
| `compatibility_edge` | Mechanism間の相性・競合 | `source_id`, `target_id`, relation |
| `recipe` | 1つのSales Storyに対するMechanism組み合わせ | recipe ID, profile, selected mechanisms |
| `creative_profile` | 事業者Truthから抽出した表現要求 | axes, tags, weights, negatives |
| `scene_spec` | 実制作へ渡す実装可能な仕様 | scene role, content slots, responsive rules |
| `evaluation` | Design / Conversion / Motion / Feasibility評価 | rubric version, scores, gates |
| `mobile_evidence` | 390px等でのRecomposition検証 | viewport, evidence grade, review |

### 2.2 ID規則

```text
REF-<source>-<slug>
SCN-<reference>-<scene>
MECH-<layer>-<slug>
EDGE-<mechanism-a>-<mechanism-b>
REC-<archetype>-<sequence>
PROF-<company-or-case>
SPEC-<recipe>-<scene>
```

IDに業界名やStyle名だけを埋め込まない。`MECH-layout-asymmetric-editorial`は可、`MECH-landscaper-natural-template`は不可。

## 3. Business / Conversion Archetype Taxonomy

ArchetypeはIndustryではなく、購入理由・意思決定・必要な証拠・Conversion Modelを束ねる。1案件にPrimary 1つ、Secondary最大2つを付与する。

| ID | Archetype | 購買構造 | 主なConversion |
|---|---|---|---|
| `LOCAL_TRUST_SERVICE` | 地域密着・相談型サービス | 人・場所・対応範囲への不安 | 電話 / 相談 / 見積 |
| `HIGH_CONSIDERATION_HOME` | 住宅・改修・大型生活投資 | 高額、比較、現地条件、家族合意 | 来店 / 現地相談 / 資料請求 |
| `PROFESSIONAL_ADVICE` | 士業・専門家・伴走支援 | 専門性と相談しやすさの両立 | 相談 / 問い合わせ |
| `MEDICAL_WELLNESS` | 医療・健康・治療選択 | 安全、適応、期待値、資格 | 予約 / 相談 |
| `BEAUTY_PERSONAL` | 美容・身体変化・個人施術 | 自分への適合、痛み、結果、雰囲気 | カウンセリング / 予約 |
| `B2B_TECHNICAL_SOLUTION` | B2B技術・設備・業務改善 | 複雑な要件、稟議、導入リスク | 問い合わせ / デモ / 資料 |
| `B2B_PRODUCT_MANUFACTURING` | B2B製品・製造・部材 | 仕様、品質、供給、担当者信頼 | 見積 / サンプル / 商談 |
| `SAAS_WORKFLOW` | SaaS・デジタルプロダクト | 理解、比較、導入容易性、ROI | 無料体験 / デモ / 登録 |
| `D2C_PRODUCT` | D2C・EC・単品商品 | 欲求、差別化、使用イメージ、価格 | 購入 / 定期購入 |
| `RETAIL_FOOD_HOSPITALITY` | 飲食・小売・宿泊 | 場所、味、体験、空席、予約 | 予約 / 来店 / 購入 |
| `EDUCATION_COACHING` | 教育・スクール・コーチング | 自分や子どもの適合、成果、継続 | 体験 / 説明会 / 資料 |
| `RECRUITING_EMPLOYER` | 採用・雇用ブランド | 働く人、仕事の実態、文化、条件 | 応募 / 見学 / エントリー |
| `PREMIUM_LUXURY` | 高級・審美・限定体験 | 希少性、信頼、世界観、所有理由 | 来店 / 指名 / 購入 |
| `CULTURE_ENTERTAINMENT_CAMPAIGN` | 文化・娯楽・キャンペーン | 興味、参加、共有、期間性 | 参加 / チケット / シェア |
| `CORPORATE_BRAND` | 企業・ブランド・採用以外の公式サイト | 理解、記憶、関係構築 | 問い合わせ / 回遊 |
| `PUBLIC_SOCIAL` | 公共・社会・非営利 | 理解、参加、支援、安心 | 申請 / 参加 / 寄付 |

### Archetype付与規則

```text
Primary = conversion_model + purchase_process + dominant trust problem
Secondary = industry-specific context or creative transfer context
```

たとえば造園会社は、住宅向けなら `HIGH_CONSIDERATION_HOME + LOCAL_TRUST_SERVICE`、法人緑化なら `B2B_TECHNICAL_SOLUTION + LOCAL_TRUST_SERVICE` とする。業種「造園」だけでは検索しない。

## 4. Industry Taxonomy

Industryは市場・証拠・規制・素材の出所を決めるために使う。Creative Retrievalの主キーにはしない。

```text
CONSTRUCTION_HOME
LANDSCAPE_GARDEN
RENOVATION_REPAIR
DEMOLITION_INFRA
REAL_ESTATE
PROFESSIONAL_LEGAL_TAX_ACCOUNTING
CONSULTING_SUPPORT
MEDICAL_DENTAL_CLINIC
BEAUTY_SALON_BODYCARE
MANUFACTURING_MATERIALS
LOGISTICS_MAINTENANCE
IT_SAAS_DIGITAL
FINANCE_INSURANCE
RETAIL_D2C_CONSUMER
FOOD_RESTAURANT
HOTEL_TRAVEL
EDUCATION_SCHOOL
RECRUITMENT_HR
FASHION_LUXURY
AUTOMOTIVE_MOBILITY
ART_CULTURE
ENTERTAINMENT_MEDIA
PUBLIC_NONPROFIT
AGRICULTURE_FOOD_PRODUCER
OTHER
```

Industryレコードは、`regulated_claim_risk`, `typical_evidence`, `typical_purchase_process`, `locality_relevance`, `mobile_context`を持つ。これにより、同じMechanismでも医療・金融・地方サービスではEvidence Gateを変えられる。

## 5. Creative Authority Taxonomy

Creative Authorityは「誰が／何がその表現を正当化するか」を記録する。これは雰囲気の形容詞ではない。

| ID | Authority | 典型的な根拠 | 主なTransfer先 |
|---|---|---|---|
| `PERSON` | 人・顔・声 | 代表、職人、担当者、利用者 | Local / Professional / Recruit |
| `PLACE` | 場所・地域 | 店舗、現場、土地、アクセス | Local / Hospitality / Public |
| `MATERIAL` | 素材・手触り | 木、金属、料理、製品表面 | Craft / D2C / Luxury |
| `CRAFT` | 技術・工程 | 手順、精度、仕上げ、道具 | Manufacturing / Beauty / Construction |
| `PRODUCT` | 商品・性能 | 形状、機能、使用場面 | D2C / SaaS / B2B |
| `DOCUMENT` | 情報・比較・仕様 | 表、図、料金、FAQ、要件 | SaaS / B2B / Professional |
| `PROOF` | 実績・第三者・結果 | 数値、事例、資格、受賞、レビュー | High consideration / B2B |
| `EDITORIAL` | 編集・言葉・視点 | 見出し、章立て、記事性 | Corporate / Culture / Recruit |
| `MOVEMENT` | 変化・エネルギー | 動き、反応、転換、速度 | Campaign / Entertainment / Tech |
| `PRECISION` | 精密さ・制御 | グリッド、規格、データ、UI | Technical / Finance / SaaS |
| `HERITAGE` | 歴史・継承 | 年代、家系、地域文化、製法 | Luxury / Craft / Food |
| `COMMUNITY` | 共感・参加 | 顧客、仲間、地域、社会課題 | Recruit / Public / Education |
| `TASTE` | 審美・選定 | 余白、質感、キュレーション | Premium / Fashion / Hospitality |
| `PLAY` | 遊び・発見 | ゲーム性、驚き、参加 | Entertainment / Campaign / D2C |

各Referenceには `authority_primary` 1つ、`authority_supporting` 最大4つ、`authority_evidence`を付ける。Authorityを付けても証拠がなければ強度は上がらない。

## 6. Mechanism Category Taxonomy

### 6.1 Layer / Category

| Layer | 何を制御するか | 代表Subcategory |
|---|---|---|
| `ENTRY` | 最初の認知と意味づけ | hero composition, opening proof, promise reveal |
| `TYPE` | 読みの速度・階層・声 | scale, contrast, density, direction, kinetic type |
| `COLOR_SURFACE` | 温度・信号・材質 | palette, surface, contrast, accent behavior |
| `SPACE_LAYOUT` | 視線・比較・順序 | asymmetry, split, grid, layering, sticky narrative |
| `MEDIA` | 何を見せ、どう切り取るか | people, place, product, macro, document, collage |
| `GEOMETRY` | 形・境界・構造 | mask, frame, curve, line, modular geometry |
| `RHYTHM` | ページの呼吸・速度 | pause, chapter, repetition, escalation, release |
| `MOTION` | 時間をどう意味づけるか | reveal, parallax, transform, transition, reaction |
| `INTERACTION` | 操作と理解の関係 | hover, drag, filter, cursor, progress, expand |
| `PROOF` | 信頼を見える形にする | case, process, comparison, metric, source, qualification |
| `CONVERSION` | 次のDecisionを設計する | CTA, permission, calculator, booking, contact, price |
| `NAVIGATION` | 迷わず進む構造 | persistent, chapter, progress, utility, anchor |

### 6.2 Phase 1 seed mechanisms

Phase 1では、次のようなCandidate Mechanismを初期語彙とする。正式採用は、Phase 2で最低3件の独立LP Evidenceと、最低2つのArchetypeで再現した後に行う。

```text
MECH-entry-proof-led-hero
MECH-entry-split-situation-to-offer
MECH-entry-editorial-opening
MECH-entry-product-first-stage
MECH-entry-customer-state-opening
MECH-type-oversized-meaning-unit
MECH-type-editorial-contrast
MECH-type-vertical-directional-type
MECH-type-kinetic-verb
MECH-type-documentary-density
MECH-space-asymmetric-editorial
MECH-space-layered-composition
MECH-space-bento-explanation
MECH-space-sticky-narrative
MECH-space-full-bleed-chapter
MECH-media-person-in-place
MECH-media-craft-macro
MECH-media-material-sequence
MECH-media-product-use-context
MECH-media-document-as-visual
MECH-geometry-mask-reveal
MECH-geometry-framed-proof
MECH-geometry-line-as-route
MECH-rhythm-chapter-pause
MECH-rhythm-escalation-release
MECH-motion-scroll-reveal-with-job
MECH-motion-parallax-depth-with-job
MECH-motion-scene-transition
MECH-motion-kinetic-type-as-meaning
MECH-interaction-progressive-disclosure
MECH-interaction-compare-or-configure
MECH-proof-process-as-proof
MECH-proof-bounded-claim
MECH-proof-source-backed-result
MECH-conversion-permission-to-verify
MECH-conversion-next-known-outcome
MECH-conversion-bounded-commitment
MECH-conversion-price-scope-transparency
MECH-navigation-chapter-progress
MECH-navigation-persistent-action
```

### 6.3 MechanismとStyleの違い

```text
Style: 「Luxuryで作る」
Mechanism: 「余白・低彩度・素材の近接撮影・遅いRevealで、希少性と手触りを知覚させる」

Style: 「ポップに作る」
Mechanism: 「短いVerb、跳ねるAccent、カードの反復、軽いHoverで、参加の入口を小さくする」
```

Mechanismには必ず `purpose`, `marketing_job`, `user_effect`, `avoid_when`, `conversion_utility`, `evidence_requirement`を持たせる。見た目だけのタグはMechanismとして登録しない。

## 7. Reference LP Scoring Rubric

すべて0〜5点。`0=未確認 / 1=弱い / 3=成立 / 5=明確な強み`。評価理由とEvidence locatorを必須にする。

### 7.1 Design Quality（40点）

| Dimension | 見るもの |
|---|---|
| Hero Originality | 最初の意味と構図が固有か |
| Typography | 読みの速度、意味単位、階層、文字の声 |
| Layout Composition | 配置の意図、視線、密度 |
| Image Treatment | 写真・動画・図の選定と扱い |
| Visual Hierarchy | 最初に何が伝わるか |
| Section Rhythm | 速度、休止、章立て、反復 |
| Section Boundary | 境界が意味の転換を支えるか |
| Brand Distinctiveness | 会社のTruthから出た固有性か |
| Screenshot-worthy Quality | 切り取っても記憶に残るか |
| Template Resemblance Risk | 既視感・色替え感。逆スコア |

### 7.2 Conversion Quality（30点）

| Dimension | 見るもの |
|---|---|
| Conversion Clarity | 誰に何をしてほしいか |
| Proof Presentation | Evidenceが不安の位置にあるか |
| CTA Fit | Customer Stateに合うActionか |
| Decision Size | 次の判断が小さく具体的か |
| Objection Coverage | 費用、時間、範囲、適合、断りにくさ |
| Navigation Utility | 回遊や戻り道が機能するか |

### 7.3 Motion Quality（15点）

| Dimension | 見るもの |
|---|---|
| Motion Job | 注意・理解・順序・Proofの役割があるか |
| Timing / Rhythm | 動きが文章と画面の呼吸に合うか |
| Interaction Legibility | 操作可能性、反応、状態変化 |
| Reduced Motion Safety | 無効化しても意味が残るか |
| Performance Discipline | LCP / INP / CLSへの配慮 |

### 7.4 Implementation Feasibility（15点）

| Dimension | 見るもの |
|---|---|
| HTML / CSS Feasibility | 標準技術で再現可能か |
| Asset Availability | 事業者が用意できる素材か |
| Responsive Recomposition | 320〜1440pxで再構成できるか |
| Accessibility Risk | コントラスト、キーボード、代替、動き |
| Maintenance / Performance Risk | 更新・速度・故障のリスク |

### 7.5 Strong判定

```text
Strong candidate:
  design_total >= 32/40
  conversion_total >= 20/30
  implementation_total >= 9/15
  no hard gate <= 1
  source evidence >= 1 official/original source
  mobile status is not unknown for production-core promotion

Creative benchmark candidate:
  design_total >= 35/40
  mechanism evidence is explicit
  conversion may be lower, but transfer job must be stated

Production-core:
  Strong candidate + mobile M3 evidence + no legal/evidence safety failure
```

Design / Conversion / Motion / Feasibilityは合算して一つの「おしゃれ度」にしない。用途に応じて別々に検索できるようにする。

## 8. Mechanism Schema

```json
{
  "mechanism_id": "MECH-motion-scroll-reveal-with-job",
  "mechanism_name": "Job-bound scroll reveal",
  "category": "MOTION",
  "subcategory": "reveal",
  "purpose": "視線の順序と理解のタイミングを制御する",
  "marketing_job": "複雑な工程・比較・変化を一段ずつ理解させる",
  "user_effect": ["attention", "comprehension", "progress_confidence"],
  "best_for": ["B2B_TECHNICAL_SOLUTION", "CRAFT", "PRODUCT"],
  "avoid_when": ["low_bandwidth", "no_sequential_meaning", "weak_asset_evidence"],
  "best_scene": ["HERO", "PROCESS", "FEATURE_EXPLAINER", "PROOF"],
  "compatible_archetypes": ["B2B_TECHNICAL_SOLUTION", "B2B_PRODUCT_MANUFACTURING", "SAAS_WORKFLOW"],
  "visual_authority": ["PRECISION", "CRAFT", "PRODUCT"],
  "visual_impact": 4,
  "conversion_utility": 4,
  "automation_difficulty": 3,
  "html_implementation_difficulty": 3,
  "motion_dependency": "medium",
  "responsive_risk": "medium",
  "performance_risk": "medium",
  "accessibility_risk": "medium",
  "required_media": ["sequence_or_state_assets", "reduced_motion_fallback"],
  "reference_lps": ["REF-existing-benchmark-..."],
  "implementation_notes": "CSS/IntersectionObserverを基本とし、スクロール位置だけに意味を依存させない",
  "combination_notes": ["MECH-space-sticky-narrative", "MECH-proof-process-as-proof"],
  "anti_pattern": "意味のないRevealを全セクションへ適用する",
  "confidence": "candidate",
  "evidence_count": 0,
  "evidence_requirement": "独立LP3件、異なるArchetype2件、mobile observation 1件",
  "mobile_recomposition_rule": "状態を縦積みへ再構成し、同じ順序とCTAを保持する"
}
```

全フィールド定義とseedレコードは `config/creative_mechanism_db_architecture_v1.json` に保存する。

## 9. Compatibility Matrix Architecture

Mechanismを足し算しない。CompatibilityはLayer間の関係と、主役 / 補助 / 禁止を持つ有向Edgeで保存する。

```text
relation:
  SYNERGY       相互に意味を強める
  CONDITIONAL   条件を満たす場合のみ併用
  CONFLICT      同時に主役にすると意味が衝突
  EXCLUSIVE     同一Sceneで同時使用禁止
  SUPPORTS      targetの補助としてのみ使用
```

Edgeは次を持つ。

```text
source_mechanism
target_mechanism
relation
role_rule: PRIMARY | SUPPORT | ALTERNATE
allowed_scene_roles
required_profile_conditions
conflict_reason
evidence
confidence
```

### Phase 1 seed edge

| Pair | Relation | 理由 |
|---|---|---|
| Editorial contrast × Craft macro | SYNERGY | 言葉の編集と手触りの証拠が相互補強 |
| Sticky narrative × Process as proof | SYNERGY | 順序と工程の意味が一致 |
| Product-first stage × Product-use-context | SUPPORTS | Heroで商品、下部で使用場面 |
| Oversized meaning unit × Documentary density | CONDITIONAL | Hero / detailで役割分担が必要 |
| Kinetic verb × Proof source-backed-result | CONDITIONAL | 主張が強いほど直後に根拠が必要 |
| Slow parallax × Precision technical grid | CONFLICT | 速度感と精密制御が同一主役だと衝突しやすい |
| POP sticker UI × Dark luxury typography | CONFLICT | 温度・密度・authorityが分裂 |
| Kinetic type × Reduced-motion-safe static hierarchy | SUPPORTS | 動けない環境でも意味を保持 |
| Permission to verify × Bounded commitment | SYNERGY | 相談・見積など小さな次行動に落とせる |
| Full-bleed chapter × Persistent action | CONDITIONAL | CTAの常時可視性を損なわない余白が必要 |

Compatibility Solverは、

```text
profile fit
 × authority fit
 × scene job fit
 × pairwise compatibility
 × evidence safety
 × feasibility budget
```

で候補を絞る。上位Mechanismを全層へ投入する設計は採用しない。

## 10. Creative Profile Schema

Creative Profileは、事業者のTruthとBuyer Stateから生成する。形容詞だけでProfileを作らない。

### 10.1 Axes

```text
TRUST
CRAFT
PLACE
PREMIUM
ENERGY
TECHNICAL
WARMTH
INNOVATION
HUMAN
AUTHORITY
EDITORIAL
PLAY
PRECISION
TRANSPARENCY
INTIMACY
URGENCY
```

各Axisは0〜1の `value` と、理由・Evidence・confidenceを持つ。

### 10.2 Profile record

```json
{
  "profile_id": "PROF-example-company",
  "truth_tags": ["local_owner", "visible_workshop", "quote_before_contract"],
  "buyer_state": "exploring_but_afraid_to_contact",
  "purchase_process": "consultation_then_quote",
  "conversion_model": "lead_generation",
  "authority_primary": "CRAFT",
  "axes": {"TRUST": 0.86, "CRAFT": 0.91, "PLACE": 0.78, "PREMIUM": 0.42},
  "weights": {"evidence": 1.4, "mobile": 1.2, "conversion": 1.3, "novelty": 0.8},
  "negative_constraints": ["no_unverified_awards", "no_luxury_posture", "no_hidden_price"],
  "required_jobs": ["recognize_problem", "show_work", "make_first_contact_safe"],
  "asset_budget": {"photo": "medium", "video": "low", "illustration": "low"},
  "implementation_budget": "standard_html_css_js",
  "evidence_confidence": "medium"
}
```

### 10.3 Retrieval logic

```text
candidate_score =
  0.22 * axis_similarity
+ 0.16 * truth_tag_match
 0.14 * buyer_state_fit
 0.14 * marketing_job_fit
 0.10 * authority_fit
 0.08 * archetype_fit
 0.06 * conversion_utility
 0.05 * novelty_against_recent_recipes
 0.05 * evidence_confidence
 0.10 * implementation_fit
```

ScoresはHard Gate適用前の順位づけであり、以下は加点でなく除外する。

```text
unverified_claim_required
mobile_failure_for_mobile_critical_scene
pairwise_conflict
asset_not_available
accessibility_hard_failure
performance_budget_failure
template_resemblance_above_threshold
```

Retrievalは1つの答えではなく、最低3つのRecipe候補を返す。

```text
Recipe A: authority-preserving / low-risk
Recipe B: novelty-forward / medium-risk
Recipe C: conversion-forward / evidence-dense
```

## 11. Reference Universe Sampling Plan

Phase 2の推奨基準値は、初回実測後に補正する。

```text
Reference Universe total: 2,400 LP
  Conversion / Industry Benchmark: 2,100
  Creative / Award / Experimental Benchmark: 300

Strong Corpus total: 1,200 LP
  Conversion / Industry: 900
  Creative / Award / Experimental: 300

Deep Annotation total: 600 LP
  Conversion / Industry: 480
  Creative / Award / Experimental: 120
```

2,400を最初から固定して埋めるのではなく、各バケットに下限・上限を設定する。市場規模だけで均等配分せず、LP利用頻度、Conversion Complexity、Design Diversity、B2B/B2C、Consideration、Locality、Transferabilityを使う。

### 11.1 Archetype allocation（初期推奨）

| Archetype | Universe | Strong | Deep | 配分理由 |
|---|---:|---:|---:|---|
| LOCAL_TRUST_SERVICE | 235 | 111 | 60 | WEBITの主要営業対象、地域差と証拠差が大きい |
| HIGH_CONSIDERATION_HOME | 172 | 81 | 47 | 高単価・比較・現地条件の研究価値 |
| PROFESSIONAL_ADVICE | 135 | 64 | 34 | 相談障壁・専門性翻訳が重要 |
| MEDICAL_WELLNESS | 108 | 43 | 24 | 規制・安全Evidenceのため量より質 |
| BEAUTY_PERSONAL | 108 | 47 | 24 | 写真・人物・不安解消のTransfer |
| B2B_TECHNICAL_SOLUTION | 163 | 68 | 36 | 複雑なSales StoryとProof構造 |
| B2B_PRODUCT_MANUFACTURING | 126 | 51 | 28 | 仕様・工程・供給のEvidence |
| SAAS_WORKFLOW | 135 | 60 | 33 | デモ・比較・導入障壁・UI説明 |
| D2C_PRODUCT | 153 | 64 | 31 | Product-first、購入、レビュー、使用文脈 |
| RETAIL_FOOD_HOSPITALITY | 144 | 60 | 29 | Place・taste・reservationの組み合わせ |
| EDUCATION_COACHING | 108 | 43 | 22 | 適合・体験・継続不安 |
| RECRUITING_EMPLOYER | 144 | 55 | 30 | People / work reality / application |
| PREMIUM_LUXURY | 99 | 47 | 24 | Creative authority上限、量は限定 |
| CULTURE_ENTERTAINMENT_CAMPAIGN | 108 | 47 | 24 | Creative benchmarkとの接続 |
| CORPORATE_BRAND | 108 | 38 | 22 | 情報構造とブランド記憶 |
| PUBLIC_SOCIAL | 54 | 21 | 12 | 社会的信頼・アクセシビリティ |
| CREATIVE_BENCHMARK_POOL | 300 | 300 | 120 | 他業界からMechanismをTransferする専用枠 |
| **合計** | **2,400** | **1,200** | **600** |  |

`CREATIVE_BENCHMARK_POOL`は他Archetypeと重複しうるが、二重計上はしない。Conversion側のUniverseは2,100件、Creative枠は300件を別母集団として管理する。

### 11.2 Strong selection rules

Strongは次をすべて満たすものだけにする。

1. Original / official sourceを確認できる。
2. 具体的なMechanismとMarketing Jobを言語化できる。
3. Design Qualityだけでなく、Conversion / User Effect / Feasibilityを評価できる。
4. 同一Campaign variationや同一テンプレート展開を水増ししない。
5. Mobileの意味保持・Recompositionを確認する。
6. 日本向けTransferに必要な調整点を残す。
7. `Template Resemblance Risk`が高い場合は、見た目が綺麗でもStrongにしない。

## 12. Research Source Map

Sourceは役割ごとに分散し、単一Gallery依存を禁止する。

| Source class | 役割 | 初期上限 | 証拠の扱い |
|---|---|---:|---|
| Original Brand / Service | Truth・Conversion・CTA | 35% | 最優先。Live pageを確認 |
| Japanese Award / Gallery | 国内の表現・構造候補 | 15% | Awardは候補発見に使い、公式で再確認 |
| Global Award / Gallery | Creative upper bound | 15% | Transfer jobを必須化 |
| Production Company Portfolio | Mechanismの制作意図 | 10% | Original live pageとの照合が必要 |
| Motion / Interaction Showcase | Motion vocabulary | 10% | Motion Jobとfeasibilityを記録 |
| Conversion LP Gallery | CTA・価格・導線の実用例 | 10% | 見た目よりCustomer Stateを見る |
| Public / Accessibility / Performance docs | Hard Gateの基準 | 5% | W3C / Google等の一次資料 |

### Phase 1で確認したEvidence examples

| Reference | Observation | Transfer / Caution |
|---|---|---|
| SmartHR Product / 採用 | Plain language、情報構造、人物・信頼の組み合わせ | B2B / RecruitへTransfer。Heroを派手にしなくても理解を作れる |
| Kintone Product | 顧客の業務世界をUI・イラスト・説明へ翻訳 | Technical SaaS。機能一覧だけにしない |
| Aki Design / Studio Pricing / Jimdo | 料金・範囲・プランの比較を意思決定の材料にする | Low-evidence制作会社でも透明性を採用可能 |
| 中村総合解体 採用 | 実際の現場・機械・人物をEvidenceにする | Local SMEへ強くTransfer。素材が無い場合は生成しない |
| マルヨシ自動車 | 地域・人・サービス・行動を近接させる | Local Trust Service。親しみとCTAを分離しない |
| 実家のこと。 | 感情の入口から情報理解へ段階化 | Emotional barrier案件。言葉を詩だけにしない |
| IMA / 佐久間宣行事務所 / 百様図 | Verb、編集、素材、動きがブランド概念と結びつく | Creative benchmark。Conversion transferを別途説明 |
| Awwwards Storytelling / CSS Design Awards | Storytelling、interaction、scroll、WebGL等の候補発見 | Award scoreを品質の証拠にしない |
| Web Grand Prix | B2B / B2C / public等の国内評価枠 | 国内Transferの候補発見に使う |

### External guardrails

W3C WCAG 2.2の4原則、GoogleのResponsive / Mobile-first指針、Core Web Vitals（LCP・INP・CLS）をImplementation FeasibilityのHard Gateに接続する。Awardの演出がこれらを壊す場合、Referenceとしては保存できてもProduction-coreには昇格させない。

## 13. QA / Dedupe Policy

### 13.1 Dedupe

```text
canonical URL normalize
→ redirect resolve
→ domain + path fingerprint
→ campaign / brand / agency fingerprint
→ visual similarity review
→ variation policy
```

同一企業の色違い・季節違い・広告Variationは1 Referenceにまとめ、差異はScene Evidenceとして記録する。別制作・別Sales Story・別構造が明確な場合のみ独立Referenceとする。

### 13.2 Evidence grades

```text
E0 = gallery thumbnail / secondary mention only
E1 = award or portfolio description
E2 = original live page / official page confirmed
E3 = original page + desktop and 390px mobile visual review
E4 = E3 + mechanism observed across multiple scenes and conversion evidence
```

Production-core Mechanismは原則E3以上、Conversion-critical MechanismはE4を目標にする。

### 13.3 Reject / Hold

以下はStrongへ昇格しない。

- original pageが消失し、Evidenceを再確認できない
- Award画像しかなく、Mechanismの因果が不明
- 有名ブランドであること以外に学習点がない
- mobileで意味・CTA・可読性が破綻
- Motionが意味を増やさず、速度・アクセシビリティ・保守を悪化
- 事業者へのTransfer時に、未確認の資格・実績・工程・価格を要求
- 単に既存Templateの色・写真・コピーを交換しただけ

## 14. Phase 2 Production Procedure

### Pass 0 — Sampling lock

`config/creative_mechanism_db_architecture_v1.json`の配分表、Source上限、Archetype / Industryの組み合わせを固定する。件数を埋めるための追加はしない。

### Pass 1 — Discovery

Source classごとに候補を収集し、URL・会社・Industry・Archetype仮説・Source role・初期Evidenceを登録する。

### Pass 2 — Normalization / Dedupe

Canonical URL、Campaign fingerprint、Variation、既存Referenceとの重複を処理する。`HOLD`は候補数としては残すが、Strongには入れない。

### Pass 3 — Live observation

Desktopと390px前後を確認し、Hero / Type / Layout / Media / Rhythm / Motion / Proof / CTA / NavigationをScene単位で記録する。

### Pass 4 — Scoring

Rubricを別々に採点する。説明が薄い点数は無効。各スコアにlocatorと観察理由を付ける。

### Pass 5 — Mechanism mining

見た目をコピーせず、`customer problem → creative intervention → user effect → marketing job`に分解する。1LPから複数Mechanismを採掘してよい。

### Pass 6 — Strong / Deep promotion

Strongは選定ルール、Deepは複数Scene・Responsive・Conversion・Transfer・Riskまで注釈する。Creative benchmarkはConversionが低くても、Transfer可能なMechanismが明確なら保存する。

### Pass 7 — Compatibility / Recipe

独立Mechanismを組み合わせ、主役 / 補助、Conflict、必要Evidence、Feasibility budgetを判定する。各Creative Profileに最低3 Recipe候補を出す。

### Pass 8 — Production dry run

同じCompany Truth・同じSales Storyに対して、3 RecipeをHTML化し、Template Resemblance Risk、Mobile、Conversion Clarity、Performanceを比較する。

### Pass 9 — Closure

新規Mechanismの増加が止まり、既存Mechanismの再確認が中心になったら、ArchetypeごとのSaturationを確認して採掘を止める。件数到達だけを理由に継続しない。

## 15. Phase 1終了条件

以下を満たしたため、Phase 2大量収集へ進めるArchitecture状態にある。

- DB Entity / ID / relationが定義済み
- Business / Conversion ArchetypeとIndustryを分離
- Creative Authorityを独立層として定義
- Mechanism CategoryとMechanism Schemaを定義
- Design / Conversion / Motion / Feasibilityを分離評価
- Compatibility MatrixとHard Gateを定義
- Creative ProfileとRetrieval Logicを定義
- Reference / Strong / Deepの配分を提示
- Creative benchmark 300枠を別管理
- Source Map、Dedupe、Evidence grade、Phase 2 procedureを定義
- Phase 1で実サイトの国内外サンプルEvidenceを確認

推奨初期値は `2,400 / 1,200 / 600 / 150〜250 canonical mechanisms`。これは固定値ではなく、Phase 2のMechanism discovery rate、重複率、Archetype coverage、Recipe dry run結果で調整する。

## 16. 残るリスク

1. Gallery / Awardの選定バイアスが残るため、Original Brand sourceを35%以上確保する。
2. Creative benchmarkのTransfer過程で、装飾だけを持ち込むリスクがある。RecipeにMarketing Jobを必須化する。
3. Low-evidence SMEへ高級・先進・実績豊富な表現を誤適用する危険がある。Evidence SafetyをHard Gateにする。
4. Motionの実装難易度を過小評価しやすい。Reduced Motion、LCP・INP・CLS、390pxを同じGateで見る。
5. 同じMechanism名でもIndustryごとに意味が変わる。`scope`, `supported_industries`, `low_evidence_fit`を必須にする。
6. Creative ProfileのAxisが形容詞の寄せ集めになる危険がある。各AxisにTruth・Buyer State・Evidenceを要求する。

## 17. Source notes

Phase 1の設計根拠として、既存リポジトリのBenchmark Pool / Frame Registry / Mobile Verificationと、以下の外部ソース群を参照した。

- Awwwards Storytelling / Interaction / category pages
- CSS Design Awards website pages and gallery
- 日本アドバタイザーズ協会デジタルマーケティング研究機構 Web Grand Prix
- W3C WAI WCAG 2.2
- Google Search Central responsive / mobile-first guidance
- web.dev Core Web Vitals

URLの機械可読一覧は `data/creative_mechanism_phase1_source_evidence.csv` に保存する。
