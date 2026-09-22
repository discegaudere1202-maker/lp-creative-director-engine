# Round 3F-M2E — Evidence handoff

This package contains live-browser observations only. It does not classify any site as good/bad, decide Mobile Re-Art-Direction, rank benchmarks, or create production rules.

## What is included

- 11 official public-site cases; each was attempted at 390×844, 375×812, and 320×720.
- Scene captures at 390px: hero, early, material, middle, late, final CTA, ending, plus a full-page image.
- Scene captures at 375px: hero, late, final CTA, ending.
- Scene captures at 320px: hero and ending.
- 1440×960 desktop references for six cases.
- Per-case JSON: rendered headings and line fragments, explicit `<br>`, viewport/overflow, CTA geometry, fixed/sticky elements, section backgrounds/media, CSS motion signals, console errors and failed requests.
- `capture_manifest.json`, `unavailable_cases.json`, `capture_limitations.json`, `viewport_summary.json`, and `artifact_manifest.json`.

## Case list

| Case | Public URL |
| --- | --- |
| SANU 2nd Home | https://www.sa-nu.com/ |
| SANU Stay / booking | https://stay.sa-nu.com/ |
| Yoom product LP | https://lp.yoom.fun/ |
| Yoom Flowbot | https://lp.yoom.fun/features/flowbot |
| Findy corporate | https://findy.co.jp/ |
| Findy recruitment | https://recruit.findy.co.jp/ |
| AI model brand | https://www.ai-model.jp/ |
| AI model careers | https://www.ai-model.jp/careers/ |
| Timee corporate | https://corp.timee.co.jp/ |
| Timee recruitment special | https://corp.timee.co.jp/special-recruit/ |
| Okinawa Kaiho Bank | https://www.kaiho-bank.co.jp/ |

## Evidence limitations

- A successful document load does not imply every third-party resource loaded.
- Cookie/consent overlays are recorded when visible; no consent choices are submitted.
- Cross-origin frames, canvas, lazy media, and hover-only states may be absent or incompletely measured.
- Computed animation inventory is evidence only; it does not prove motion visibly plays.
- No aesthetic or Mobile Re-Art-Direction decisions are made in this package.
- The supplied priority list did not uniquely identify which Findy product, and “AI model” is interpreted as ai-model.jp. These are explicit identity assumptions, not confirmed selection claims.
- Live pages may change between local and CI captures. The CI report compares structural coverage; binary pixel equality is not asserted.

## Re-run

From the repository root, install the repository's existing Playwright dependency and Chromium, then run:

```powershell
python scripts/run_mobile_pixel_evidence.py
```

This contacts each listed public page once at each configured viewport (and once at 1440px for six cases). It writes the evidence bundle to `artifacts/mobile_pixel_evidence_round3fm2e/`.

## Review handoff

Please review the screenshots and case evidence as factual Mobile/Motion observations. Make any creative interpretation or Re-Art-Direction decision separately. No source code or page assets are redistributed.
