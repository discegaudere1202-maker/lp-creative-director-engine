# Seishou Design-to-Code Fidelity — Issue #139

SSOT: Issue #139. Copy/facts: Issue #140. Pixel Master: Library `/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png`.

Master SHA-256: `cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc`.

## Round 1 boundary
Only **Header + Hero + Trust strip** is implemented. Master coordinate crop is `786 × 428px` (Header ≈ 0–40, Hero ≈ 41–330, Trust ≈ 331–427). Real DOM text is locked to Issue #140; AI-generated glyphs in the Master are not OCR source copy.

The hero sample image is derived from the supplied Master solely to preserve the visual experiment's photo composition. It is explicitly labelled `施工イメージ / サンプルビジュアル` and must never be represented as 株式会社清松's actual work.

## Evidence
```bash
npm install
npx playwright install chromium
npm run evidence
```
Outputs in `evidence/iteration_01/`: `expected.png`, `actual_786.png`, `actual_1440.png`, `diff.png`, `comparison.json`, `capture.json`.

Pixel mismatch is diagnostic only. The authoritative review remains human-visible fidelity: photography force, deep-green tonal control, typography hierarchy, spacing, alignment, and Header/Hero/Trust section boundaries.
