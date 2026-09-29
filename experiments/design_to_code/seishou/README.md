# Seishou Design-to-Code Fidelity — Issue #139

SSOT: Issue #139. Copy/facts: Issue #140. Pixel Master: Library `/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png`.

Master SHA-256: `cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc`.

## Current boundary — v2
Only **Header + Hero + Trust strip** is implemented. No Problem / Need or later section work is included.

The Master coordinate crop is exactly `786 × 428px` (Header ≈ 0–40, Hero ≈ 41–330, Trust ≈ 331–427). Real DOM text is locked to Issue #140; AI-generated glyphs in the Master are not OCR source copy.

## Exact Expected
The formal pixelmatch Expected is the **lossless top 786 × 428 crop from the exact Library Master**.

- Master SHA-256: `cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc`
- Exact crop raw RGB SHA-256: `1a5104d22c63f003f2262f45300c31b021dd335754d042442ad94692a124649a`
- Proxy / downscaled Expected: prohibited for the v2 gate

The persistent Library Master is not mounted inside GitHub-hosted Actions. CI therefore captures deterministic 786px / 1440px Actuals. Exact pixelmatch is executed only in the controlled environment where the locked Library Master is mounted, using `SEISHOU_MASTER_PATH`. This prevents a proxy or incomplete repository transport from becoming the formal Expected.

## Hero photography v2
The low-resolution Master-derived Hero crop is no longer used as production photography. v2 uses one high-resolution clean photograph from Pexels / Max Vakhtbovych (`7360 × 4912` source, requested at 2400px render width). Duplicate background redraw/shade is disabled.

Source page: `https://www.pexels.com/photo/frontage-of-a-residential-house-with-garden-8134817/`

The visual remains explicitly labelled `施工イメージ / サンプルビジュアル` and must never be represented as 株式会社清松's actual work.

## Final v2 evidence
- Final capture head before this documentation-only commit: `72921c0ece4d78c0c27c4c359db6e9e0e87ceb68`
- Fidelity workflow: `36523120880` — SUCCESS
- Artifact: `11013224946`
- Artifact digest: `sha256:34bd3be73126070f8ddcf731470310e68cd5ab6bb262d7f367e645f4e8880072`
- Actual 786 SHA-256: `c89a84794b62f4695baab0a9ddadf3f8ff97c080b869a8528647d57d5d3f7246`
- Actual 1440 SHA-256: `e18e0d192766211c3e98fdf1cf0a039bff2a2b510e55b03ac358f980b9dfb674`
- pixelmatch: v7.1.0 / threshold `0.10` / `includeAA: true`
- mismatch pixels: `171,205 / 336,408`
- mismatch ratio: `0.5089207153218711`

Mismatch is diagnostic only. Exact AI-rendered Master glyph pixels are intentionally not the clean-DOM typography target. Human-visible review remains authoritative for photography force, sharpness at 1440px, crop, deep-green tonal balance, typography hierarchy, spacing, alignment, and Header/Hero/Trust boundaries.

## Commands
CI capture:

```bash
npm install
npx playwright install chromium
npm run evidence
```

Exact Library comparison in a Master-mounted environment:

```bash
SEISHOU_MASTER_PATH=/absolute/path/to/Seishou_PC_Master_v1.png npm run compare:exact
```

Do not continue to the next section until this first boundary is accepted by human review.
