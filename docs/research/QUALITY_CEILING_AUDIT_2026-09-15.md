# Quality Ceiling Audit — 2026-09-15

## Purpose
This audit re-establishes the factual baseline for the Quality Ceiling Research Phase from the GitHub SSOT. It intentionally separates research volume from strict benchmark certification.

## 1. Strict Frame Registry baseline

`config/frame_registry_v1.json`

- Total strict records: 14
- VERIFIED: 11
- CANDIDATE: 3
- CORE: 0
- REJECTED: 0

Interpretation:
- The corpus is intentionally small.
- Research-note volume must not be reported as strict verified volume.
- No benchmark may be described as CORE until the highest mobile evidence requirement is met.

## 2. Mobile evidence baseline

`config/mobile_benchmark_verification_v1.json`

Current M2 research candidates:
- 実家のこと。
- IMA株式会社
- SmartHR 採用サイト
- JMC 採用サイト

All four have published/trustworthy mobile visual evidence and preserve hierarchy, primary message and action strongly enough to learn from.

However:
- M2 is **not CORE**.
- CORE now requires M3: live / faithfully captured 390px review.
- Responsive claims, device mockups, award commentary and gallery SP screenshots are not sufficient for CORE.

This closes the gap between “mobile evidence exists” and “we personally verified the production-grade 390px state”.

## 3. Blind Tournament readiness

The formal comparison package now requires:
- 3–5 benchmarks
- exactly 1440px and 390px comparison views
- both screenshots for Candidate and every Benchmark
- unique Benchmark IDs
- Candidate identity separated from Benchmark identity in the reviewer UI

Current prototype registry contains 12 reusable-pattern candidates, but no prototype has a formal benchmark tournament result yet.

Reason:
- the repository currently stores prototype findings/registry data but not a complete 1440px + 390px screenshot package for the current P01–P12 registry.

Therefore:
- `NOT_RUN` is correct.
- A qualitative preliminary review must not be relabeled as a formal Blind Tournament.
- The next valid step is to reconstruct/capture the current prototype frames, then build anonymous comparison bundles.

## 4. Prototype registry baseline

`config/prototype_registry_v1.json`

- Total: 12
- CRAFT_VERIFIED: 11
- DRAFT: 1 (`P11 Real Photo Crop Direction`)
- Formal Tournament PASS: 0

Priority prototypes for first formal tournament:
1. P02 Customer-world Translation
2. P04 Evidence Landscape
3. P05 Work Style Scene
4. P09 Price Transparency
5. P10 Customer State Transition
6. P12 Mobile Re-art Direction

These are prioritized because they are directly transferable to NO_WEB / WEAK_WEB SME sales samples and can create premium differentiation without relying on expensive client assets.

## 5. New benchmark research — high-value candidates

### 菁文堂
Why it matters:
- MATERIAL / PRODUCT / CRAFT
- the actual act of writing and the physical book/pen shapes generate the hero composition
- page-turning behavior becomes transition logic
- unusually strong `Business Reality -> Form` causality for a manufacturer

SME transfer hypothesis:
- for manufacturers, printers, sign shops and craft businesses, real tool/material/action can generate composition and motion instead of decorative texture.

Status: research source exists; do not promote to strict VERIFIED until explicit visual review is completed.

### 大松工業
Why it matters:
- local industrial SME
- environmental action accumulated for 10+ years becomes brand platform rather than CSR footnote
- useful counterexample to “small manufacturer = generic company profile”

SME transfer hypothesis:
- operational discipline, environmental practice, process quality or local history can become the central Brand Truth even when product photography is not spectacular.

Status: research source exists; visual verification required.

### StartPass
Why it matters:
- B2B / ASSET_LIGHT / CONVERSION_ACTION
- creates a new category, “スタートアップ経営企画室”, then invests equally in understanding and action
- reported outcome includes lower communication cost because leads arrive with deeper business understanding

SME transfer hypothesis:
- when a service is difficult to explain, the page should reduce future sales explanation work, not merely look premium.

Status: research source exists; visual verification required.

## 6. Research rule strengthened

A strong benchmark now needs three independent kinds of evidence:

1. **Rationale evidence** — why the form exists
2. **Visual evidence** — what the frame actually does
3. **Transfer evidence** — what judgment can move into NO_WEB / WEAK_WEB sales samples without copying style

Award status alone satisfies none of these.

## 7. Historical ID hygiene

`BENCHMARK_TOURNAMENT_BATCH01_PRELIM_v1.md` used prototype IDs before the current P01–P12 registry existed.

Those IDs are now explicitly marked `LEGACY-Pxx` so historical findings cannot be accidentally attributed to current prototypes.

## 8. Immediate next research sequence

1. Keep strict CORE count at 0 until genuine M3 evidence exists.
2. Expand visually verified SME-relevant benchmarks, prioritizing:
   - ASSET_LIGHT
   - LOCAL_SME_TRANSFER
   - B2B_EXPLAINER_DOCUMENT
   - MATERIAL_PHOTO_CRAFT
   - CONVERSION_ACTION
3. Reconstruct current high-priority SME prototypes as actual 1440px / 390px artifacts.
4. Run formal anonymous tournaments only after screenshot readiness passes.
5. Repair only losing axes; do not cosmetically redesign passing axes.
6. Do not select Golden Sample 03 until at least Hero and Mid Peak can compete against the relevant benchmark pool.

## Principle
The research phase is not complete when the engine can score a design.

It is complete only when the system can reliably distinguish:

- polished template quality
- owner-specific premium quality
- benchmark-competitive premium quality

and can explain **which Company Truth caused the winning form**.