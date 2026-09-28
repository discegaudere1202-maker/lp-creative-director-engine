# SEISHO v3.1 Premium Polish Report

Date: 2026-09-28
Owner: Sarah PM
Target: 株式会社清松

## Context

Shun's v2 feedback established that the new Scene Spec architecture improved the result, but the visual ceiling still felt too simple / template-like for a ¥1M-class custom LP.

v3 replaced the safer `Grounded Landscape Editorial` direction with `TERRAIN / CRAFT EDITORIAL` and produced a stronger validation image plus DOM/CSS implementation.

v3.1 is an autonomous polish pass intended to move the HTML closer to the validation-image quality while preserving the Scene-Spec-first architecture.

## v3.1 Changes

### Removed prototype-looking UI from the client-facing page
- Removed the sticky developer/sample explanation bar from the top of the LP.
- Kept Truth-safe disclosure in the footer and `MOOD IMAGE` labels where needed.
- Added an actual client-facing navigation layer over the Hero.

### Removed methodology copy from the LP body
The visitor-facing page no longer explains Scene Spec, the LP-production method, or why the sample was built. Those are internal production notes, not customer-facing sales copy.

### Hero polish
- Site navigation integrated into Hero.
- Signature oversized headline retained.
- Vertical / editorial SEISHO language retained.
- Public fact strip retained as technical annotation.
- Terrain SVG boundary retained.
- Terrain contour line now draws on entry.

### Scene identity / anti-template polish
- Public Truth remains a technical ledger rather than cards.
- Four work categories remain horizontal editorial bands, not equal cards.
- Dark Craft scene remains an irregular image collage.
- Value scene was rewritten as client-facing `From Ground to Landscape`, replacing internal proposal-explanation copy.
- Contact remains a dark immersive field with giant phone typography and paper-slip company ledger.

### Motion polish
Added Scene-Spec-consistent motion rather than generic decoration:
- document scroll progress datum
- Hero terrain line draw
- scope band directional entry
- Craft collage micro parallax
- value ground-line progress
- Hero image parallax
- reduced-motion fallback retained

### Client-facing copy cleanup
Removed or replaced visible phrases that made the page feel like a design presentation rather than the company's actual LP.

## Truth Safety

Still not fabricated:
- construction result counts
- testimonials
- awards
- pricing
- free-estimate policy
- service-area promises

Generated images remain explicitly `MOOD IMAGE / 提案用` and are not presented as actual construction evidence.

## Static QA

PASS:
- HTML parses
- 5 major content sections + Hero
- 4 work-category bands
- no client-visible `Scene Spec` methodology phrase
- no prototype sticky topbar
- client-facing site navigation present
- phone and mail CTA present
- responsive rules present for tablet/mobile
- `prefers-reduced-motion` present
- JavaScript syntax check PASS
- generated mood-image disclosure retained

## Artifact

Local review artifact:
- `SEISHO_landscaping_sales_sample_v3_1_premium.html`

## Status

`OPEN — SHUN HUMAN REVIEW REQUIRED`

Do not call the ¥1M premium-quality target achieved until Shun reviews the actual v3.1 HTML.
