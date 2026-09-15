# LP Creative Director Engine

1000件のLP自動生成を「テンプレ生成」ではなく、
**AI Creative Director System**として実装するためのPythonエンジン。

現在: **v0.5.0**

## 現在実装済み
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
- GitHub Actions CI

## Pipeline

```text
Source Depth
→ Fact Ledger
→ Company Truth
→ Visual Authority
→ 3 Creative Concept Competition
→ Hero/Mid Frame Build
→ Screenshot Gate
→ Full LP
→ Rhythm/Motion/Copy QA
→ Browser Render QA
→ Creative Red Team
→ CRO Red Team
→ Owner Simulation
→ Premium Gate
```

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
