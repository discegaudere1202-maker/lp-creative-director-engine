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
- 100-record source-backed quality research ledger
- Core60 benchmark decision dictionary
- Authority-specific benchmark pools
- Blind Benchmark Tournament aggregation
- Blind Benchmark Review UI generator
- GitHub Actions CI

## Current R&D priority — Quality Ceiling

量産最適化より先に品質上限を引き上げる。

Research status:
- [x] 100 source-backed benchmark records
- [x] 100 → Core60 selection
- [x] Authority-specific benchmark pools
- [x] Blind Tournament aggregation logic
- [x] Blind reviewer UI generator
- [ ] 20–30 externally challenged Craft Prototypes
- [ ] 3 NO_WEB / WEAK_WEB Golden Samples passing Benchmark Supremacy
- [x] Sales State → Enriched State layout hypothesis validated
- [ ] Client Evidence Upgrade Slot library finalized

See:
- `docs/research/QUALITY_CEILING_RESEARCH_PHASE_v1.md`
- `docs/research/SALES_SAMPLE_COMPLETION_CONTRACT_v1.md`
- `docs/research/BENCHMARK_SUPREMACY_GATE_v1.md`
- `docs/research/CORE_FRAME_SELECTION_RULES_v1.md`
- `docs/research/CORE_FRAME_SELECTION_v1.md`
- `docs/research/FRAME_ANALYSIS_BATCH_01.md` … `FRAME_ANALYSIS_BATCH_06.md`
- `docs/research/CRAFT_PROTOTYPE_BACKLOG_v1.md`
- `benchmarks/core_benchmark_pool_v1.json`

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

Core60 is a **decision dictionary**, not a template library.
`benchmarks/core_benchmark_pool_v1.json` groups Core examples by comparison purpose such as:
- PERSON / EDITORIAL
- MATERIAL / PHOTO / CRAFT
- PRODUCT BEHAVIOR
- B2B / EXPLAINER / DOCUMENT
- WORLD / CATEGORY
- TYPOGRAPHY / MOTION
- UTILITY / ACCESSIBILITY / TRUST
- CONVERSION / ACTION
- MOBILE FIRST
- ASSET LIGHT
- LOCAL SME TRANSFER

Pool selection chooses **who the candidate must compete against**, never what the candidate should look like.

Generate an anonymous reviewer UI:

```bash
lp-benchmark-review review_manifest.json --out out/blind_review.html --seed 42
```

The reviewer only sees anonymous LEFT/RIGHT screenshots at 1440px and 390px.
Scores are converted to candidate-relative `-1 / 0 / +1` JSON and passed to the tournament aggregator.
Company names, production company names, award labels and candidate/benchmark identity must not be exposed during review.

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
- Benchmark Supremacy Desktop/Mobile comparison

## Pixel Rhythm

```bash
lp-rhythm path/to/fullpage.png
lp-rhythm sample_a.png sample_b.png --out out/rhythm_compare.json
```

Pixel Rhythm observes Peak / Quiet clusters, visual-density transitions and flatness risk.
It is **not** a standalone creative-quality score.

Section-level visual QA also maps real DOM section boundaries back to rendered pixels so that
quietest/densest sections and the strongest visual gear-change can be observed.

## Rhythm Regression

```bash
lp-rhythm-regression baseline.json current.json
```

Regression is deliberately advisory:
- `STABLE` — no large unintended shift detected
- `REVIEW` — Creative Red Team should inspect the changed section(s)

It never returns creative `FAIL`. Different companies should retain different breathing patterns.
See `docs/SECTION_ID_CONTRACT_v1.md` for stable machine-readable section IDs.

## Run

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python -m lp_engine.cli examples/mahora_v2.json --out out/mahora_report.json
```

## Golden Sample principle

A new Gate re-certifies old Golden Samples. A previous PASS is not permanent.
The engine should become stricter as the portfolio grows, while preserving company-specific creative direction.

A Golden Sample is not selected only because the company is visually interesting. It must first be eligible as a real sales-sample target, or be explicitly labeled as an R&D redesign challenge.
