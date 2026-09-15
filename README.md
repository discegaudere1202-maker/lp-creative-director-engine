# LP Creative Director Engine

1000件のLP自動生成を「テンプレ生成」ではなく、
**AI Creative Director System**として実装するためのPythonプロトタイプ。

## 現在実装済み
- Visual Authority classifier
- Owner-specificity Gate
- Screenshot Peak Gate
- Section Rhythm Gate
- Motion timing/restraint Gate
- Static copy fragment Gate
- Playwright real-browser QA
- Tier-2 Visual QA
- Pixel Rhythm comparison
- Golden Sample regression data

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
- pixel-derived rhythm metrics

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
It is **not** a standalone creative-quality score. It must be read with Screenshot Score,
Owner Specificity, CRO and Section context.

## Run

```bash
python -m unittest discover -s tests -v
PYTHONPATH=src python -m lp_engine.cli examples/mahora_v2.json --out out/mahora_report.json
```
