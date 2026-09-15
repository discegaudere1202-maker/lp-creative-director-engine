# LP Creative Director Engine

1000件のLP自動生成を「テンプレ生成」ではなく、
**AI Creative Director System**として実装するためのPythonエンジン。

現在: **v0.7.0 + Quality Ceiling Research Phase**

## North Star

AI利用・自動生成であることは顧客価値と無関係。
営業サンプルの時点で、
**「腕のいいアートディレクターとデザイナーが、その会社のためだけに設計した」**
と思われる品質を目指す。

営業サンプルは途中版ではなく、
**Client Evidenceだけが未追加の完成LP**として扱う。

## 現在実装済み
- Sales Eligibility / Existing Site Baseline Gate
- Asset Reality classification
- Visual Authority classifier
- Owner-specificity Gate
- Screenshot Peak Gate
- Section Rhythm Gate
- Motion timing/restraint Gate
- Static copy fragment Gate
- Playwright real-browser QA
- Tier-2 Visual QA
- Pixel Rhythm / Section Pixel Rhythm
- Advisory Rhythm Regression
- Golden Sample regression baselines
- Strict Frame Registry (`CANDIDATE / VERIFIED / CORE / REJECTED`)
- Authority-specific Benchmark Pool config
- Blind Benchmark Tournament aggregation
- Blind Benchmark Review UI generator
- Strict Form Causality checks
- Safety-only Evidence Selection Gate with provenance, rights and hearing routing
- GitHub Actions CI

## Current R&D priority — Quality Ceiling

量産最適化より先に品質上限を引き上げる。

### Official research counter

**研究Markdownに書かれた候補数と、正式に品質比較へ使えるFrame数を分離する。**

公式カウンターは `config/frame_registry_v1.json` のみ。

2026-09-15時点:
- Registry records: **15**
- Strict desktop VERIFIED: **11**
- CANDIDATE: **4**
- CORE: **0**

`CORE`へ昇格するには、少なくとも:
- Source rationale確認
- Desktop visual確認
- Mobile visual確認
- Sales-sample transfer principle明文化
- Benchmarkとして何を比較するか明確

が必要。

以前の研究ノートにある「100 Frame」「Core60」は**探索・仮分類の研究資産**であり、Strict Verified/Core完了を意味しない。
今後「100件到達」と報告する際は、Registry上のStageを明示する。

### Quality Ceiling exit criteria

- [ ] Strict VERIFIED Frames: 100
- [ ] Visual AuthorityごとにCORE Benchmark 3件以上
- [x] Blind Tournament aggregation logic
- [x] Blind reviewer UI generator
- [ ] 20–30 externally challenged Craft Prototypes
- [ ] 3 NO_WEB / WEAK_WEB Golden Samples passing Benchmark Supremacy
- [x] Sales State → Enriched State layout hypothesis validated
- [ ] Client Evidence Upgrade Slot library finalized

## Pipeline

```text
Candidate
→ Existing Site Check
→ Existing Site Baseline Score
→ Asset Reality Check
→ Sales Eligibility
→ Source Depth
→ Fact Ledger
→ Company Truth
→ Visual Authority
→ 3–5 Creative Concept Competition
→ Hero/Mid/CTA Frame Build
→ Benchmark Pool Selection
→ Blind Benchmark Tournament (1440 / 390)
→ Benchmark Supremacy
→ Form Causality
→ Screenshot Gate
→ Full LP
→ Rhythm/Motion/Copy QA
→ Browser Render QA
→ Creative Red Team
→ CRO Red Team
→ Owner Simulation
→ Sales Sample Premium Gate
→ Client Evidence collection
→ Enriched State
→ Delivery Premium Gate
```

**Creative production must not start before Sales Eligibility.**
A company can be an excellent design benchmark and still be the wrong sales-sample target.

## Sales Eligibility

- `SALES_CANDIDATE` — no site, or an existing site with at least two concrete improvement gaps
- `BENCHMARK_ONLY` — existing site is already strong; study it, do not automatically redesign it
- `REDESIGN_CHALLENGE` — explicit R&D challenge to beat a strong existing baseline, separated from sales targeting
- `REVIEW` — redesign value has not yet been proven

Asset access is also separated from business asset reality:

`ACCESS_CONSTRAINT_NOT_ASSET_POOR` means the company owns strong real assets, but we cannot currently access/use them well. This must never be treated as an asset-poor brand.

See `docs/SALES_ELIGIBILITY_GATE_v1.md` and `docs/research/MORIBITO_POSTMORTEM_v1.md`.

## Benchmark Supremacy

Benchmark data is a **comparison dictionary, not a template library**.

- `config/benchmark_pool_v1.json` — individual benchmark candidates
- `config/benchmark_pools_v1.json` — comparison families by authority/purpose
- `config/frame_registry_v1.json` — strict verification status

Pool selection chooses **who the candidate must compete against**, never what the candidate should look like.

Generate an anonymous reviewer UI:

```bash
lp-benchmark-review review_manifest.json --out out/blind_review.html --seed 42
```

The reviewer only sees anonymous LEFT/RIGHT screenshots at 1440px and 390px.
Scores are converted to candidate-relative `-1 / 0 / +1` JSON and passed to the tournament aggregator.
Company names, production company names, award labels and candidate/benchmark identity must not be exposed during review.

## Form Causality

Premium candidateは、Company TruthをCopyに載せるだけでは不十分。
主要なVisual Decisionが、確認済みCompany Truthによって**実際に形を変えていること**を要求する。

Required checks:
- confirmed truth → form decision
- Hero/MidなどRequired Frameに因果がある
- Mobileでも因果が残る
- 社名だけ差し替えて他社へ転用できない

Rule:
**If the company truth changes, the form should have to change.**

## Evidence Safety Gate

The optional pipeline safety input selects only verified, production-eligible
evidence. It checks provenance, verification date, usage status and rights,
blocks unsupported reassurance, and routes missing evidence to
`HEARING_REQUIRED`. It never generates trust copy.

```bash
lp-engine examples/mahora_v2.json --evidence-safety evidence_safety_input.json
```

The safety input contains `conversion_goal`, `primary_objections`, an
`evidence_ledger`, and optional `requested_claims`. Without this option, the
existing creative-direction pipeline is unchanged.

## QA tiers

### Tier 1 — all candidates
- 320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440px
- horizontal overflow
- real Line Box
- 1–2 character fragments
- isolated particles
- 200% reflow proxy

### Tier 2 — premium candidates
- real-asset screenshots
- grayscale
- strong blur
- logo-off
- section screenshots
- full-page Pixel Rhythm
- DOM section-aligned Pixel Rhythm

### Tier 3 — outbound sales candidates
- production motion / interaction
- Reduced Motion
- runtime errors
- final visual review

## Pixel Rhythm

Pixel Rhythm observes Peak / Quiet clusters, visual-density transitions and flatness risk.
It is **not** a standalone creative-quality score.

Regression is deliberately advisory:
- `STABLE` — no large unintended shift detected
- `REVIEW` — Creative Red Team should inspect the changed section(s)

Different companies should retain different breathing patterns.

## Golden Sample principle

A new Gate re-certifies old Golden Samples. A previous PASS is not permanent.
The engine should become stricter as the portfolio grows, while preserving company-specific creative direction.

A Golden Sample is not selected only because the company is visually interesting. It must first be eligible as a real sales-sample target, or be explicitly labeled as an R&D redesign challenge.

Current target priority:
1. **NO_WEB** — highest priority
2. **WEAK_WEB** — second priority
3. **GOOD_WEB** — benchmark only by default
