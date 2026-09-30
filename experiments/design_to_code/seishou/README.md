# Seishou Design-to-Code Fidelity — Issue #139

SSOT: Issue #139. Copy/facts: Issue #140. Pixel Master: Library `/LP制作事業/Design-to-Code/Seishou/Seishou_PC_Master_v1.png`.

Master SHA-256: `cc879352445655f84f460dd41b9267d34bd1eafc3b984486b4b09e6d9c4a1bbc`.

## Current boundary — Hero Asset Fidelity v3
Only **Header + Hero + Trust strip** is implemented. No Problem / Need or later-section work is included.

The Master coordinate crop is `786 × 428px` (Header ≈ 0–40, Hero ≈ 41–330, Trust ≈ 331–427). Real DOM text remains locked to Issue #140; AI-generated glyphs in the Master are not OCR source copy.

### Hero photography v3
v2 recovered sharpness but remained architecture-first. v3 replaces only the Hero visual with the Saya research candidate:

- Pexels / Aleksandr Poklad
- source page: `https://www.pexels.com/photo/charming-garden-pathway-leading-to-house-36742224/`
- served render: `2400 × 3600`
- mirrored to push the house entrance into the rear/right visual field
- crop/focal: `center 56%`
- garden/foliage, stone path, entrance, foliage light/shadow are the scene-authority cues
- `施工イメージ / サンプルビジュアル` remains required; the image is not represented as Seishou work

### Evidence
```bash
npm install
npx playwright install chromium
npm run evidence
```

Outputs in `evidence/iteration_03/`:
- `actual_786.png`
- `actual_1440.png`
- `before_v2_786.png`
- `before_v2_1440.png`
- `before_v2_vs_after_v3_786.png`
- `before_v2_vs_after_v3_1440.png`
- `capture.json`
- `hero_asset_manifest_v3.json`

Exact Master comparison is recorded separately in `reference/iteration_03_exact_master_metrics.json` using the locked Library Master crop. Pixel mismatch remains diagnostic only; the authoritative review is Human-visible scene/composition fidelity and 1440px sales-sample quality.

## Scope lock
Hero Asset Fidelity v3 only. Header and Trust remain in the same boundary and no next section is implemented until Saya/Shun review.
