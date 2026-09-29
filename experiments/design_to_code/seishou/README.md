# Seishou Design-to-Code Fidelity — Issue #139

SSOT: Issue #139. Copy/facts: Issue #140. Pixel Master: Library `/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png`.

Master SHA-256: `cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc`.

## Current boundary — v2
Only **Header + Hero + Trust strip** is implemented. No Problem / Need section work is included.

The Master coordinate crop is `786 × 428px` (Header ≈ 0–40, Hero ≈ 41–330, Trust ≈ 331–427). Real DOM text is locked to Issue #140; AI-generated glyphs in the Master are not OCR source copy.

### Exact Expected
The official pixelmatch Expected is now the **lossless top 786 × 428 crop from the exact Library Master**. CI reconstructs `reference/expected_header_hero_trust_exact.png` from a lossless transport and validates the raw RGB SHA-256 before comparison. No 196 × 107 proxy is used as the formal Expected.

### Hero photography v2
The low-resolution Master-derived hero crop is no longer used as production photography. v2 uses a high-resolution clean stock photograph from Pexels / Max Vakhtbovych (`7360 × 4912` source, requested at 2400px render width) as an illustrative/sample visual. It must never be represented as 株式会社清松's actual work.

Source page: `https://www.pexels.com/photo/frontage-of-a-residential-house-with-garden-8134817/`

## Evidence
```bash
npm install
npx playwright install chromium
npm run evidence
```

Outputs in `evidence/iteration_02/`:
- `expected_exact.png`
- `actual_786.png`
- `actual_1440.png`
- `diff_exact.png`
- `expected_vs_actual_786.jpg`
- `comparison.json`
- `capture.json`

`comparison.json` also records the v1 Artifact / mismatch values so the before → after correction round remains auditable.

Pixel mismatch is diagnostic only. The authoritative review remains human-visible fidelity: photography force, sharpness at 1440px, deep-green tonal control, typography hierarchy, spacing, alignment, and Header/Hero/Trust section boundaries.
