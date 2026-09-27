# Design-to-Code Fidelity Research Log

Status: ACTIVE  
Owner: Sarah PM  
Human Ground Truth: Shun  
GitHub SSOT Issue: #135  
Parent PM Governance: #3

## Purpose

Preserve the complete research history for converting AI-generated full-page LP Master Designs into production HTML/CSS/Motion without visible quality loss.

This file stores durable, reusable learnings. The detailed chronological feedback log lives in Issue #135.

## Review authority

1. Shun Human Feedback
2. Approved Master Design image
3. Same-viewport screenshot / Visual Diff evidence
4. Sarah PM review
5. Aoi / other AI human-reality review
6. Automated QA / technical tests

AI PASS never overrides a Shun-visible FAIL.

## Current leading production architecture

```text
Evidence
→ Copy / Information Architecture
→ Creative Direction
→ Full-page Master Design image
→ Design lock
→ clean high-resolution visual assets
→ section-by-section DOM conversion
→ same-viewport screenshot
→ Visual Diff
→ correction loop
→ Motion
→ Responsive QA
```

## Confirmed learnings

### Creative diversity

- Direct HTML generation tends to converge toward similar clean/minimal website patterns.
- Treating the LP as one finished visual composition first produces much greater Creative Direction diversity.
- With the same MELT SKIN information architecture, generated Master Designs successfully varied across minimal, pop, luxury, cinematic, editorial, product-led, and immersive directions.
- Therefore the primary current bottleneck is not Master Design generation; it is Design-to-Code Fidelity.

### Fidelity

- Eyeballing a Master image and rewriting it as CSS causes large losses in spacing, crop, typography, layering, asymmetric composition, and section rhythm.
- Full-image pixel-lock preserves composition but creates text-as-image, resolution, SEO, accessibility, responsive, and real-DOM limitations.
- Splitting an approved Master into section-level locked scenes reduced the perceived `HTML became a different design` problem.
- Shun explicitly confirmed the section-sliced Master + Motion experiment was closer than previous implementations.
- Moving one section at a time to real DOM is superior to converting the entire page in one pass because the exact quality-loss step remains observable.
- Section transitions must have exactly one boundary owner. Hero and Concept must not each introduce independent separators.
- Raster alpha masks traced from low-resolution references create stair-stepping and visible roughness when scaled. Curved boundaries should be implemented as vector/SVG Bézier geometry or equivalent resolution-independent masks.
- When replacing only one section with DOM, the adjacent locked section must preserve all of its content; seam fixes must never crop away approved content.

## Known anti-patterns

Do not repeat these:

- direct HTML as the first creative artifact
- one-shot CSS recreation from a full-page reference
- loose/manual photo crops from text-heavy generated composites
- stretching low-resolution full-page Masters to desktop widths
- overlaying DOM text on top of baked-in text
- masking baked text while leaving ghost letters or inconsistent background
- recropping hero photography independently from the approved composition
- browser-default anchor colors or underlines appearing in visual output
- using merely `similar` fonts without accounting for font metrics, tracking, leading, and baseline
- declaring Human Visible PASS from AI-only review
- converting all sections before Shun inspects the first conversion
- treating small visual discomfort as non-actionable noise
- fixing a section seam by cropping away approved neighboring content
- giving both adjacent sections separate boundary shapes
- rasterizing a curved seam into a low-resolution alpha mask and scaling it up
- inventing decorative microcopy or labels not required by the approved design

## Current section conversion rule

For the current reference LP:

1. Lock Master Design.
2. Convert only one section to real DOM.
3. Keep all other sections pixel-locked.
4. Present artifact to Shun.
5. Record every Shun feedback item in #135.
6. Diagnose and fix the exact cause.
7. Do not move to the next section until Shun confirms perceived fidelity is maintained.

## Feedback logging rule

Every relevant Shun feedback must be recorded in Issue #135 with:

- Date / Experiment ID
- Target artifact / section
- Shun feedback, preserving meaning and specifics
- Screenshot / evidence reference when available
- Diagnosis
- Fix / next action
- Result: OPEN / IMPROVED / SHUN_CONFIRMED / REJECTED
- Reusable learning / anti-pattern

Small details are not to be omitted.

Operational guarantee:
- Log the feedback before or together with the next artifact delivery.
- Do not tell Shun `recorded` unless the GitHub comment / commit actually exists.
- Each user-facing artifact response must state the exact GitHub Issue and comment/commit evidence.

## Current experiment history

### D2C-001 — Full-page Master → direct CSS recreation

Result: FAIL

Observed:
- Design became a generic clean website.
- Master-level photographic crop and spatial rhythm were lost.

### D2C-002 — Full-page Pixel Lock

Result: PARTIAL PASS

Observed:
- Visual composition held.
- Resolution and text-as-image limitations made it unsuitable as the final architecture.

### D2C-003 — Section-sliced Master + Motion

Result: IMPROVED

Shun feedback:
- `以前より別物になった感減ってるよ`

Reusable learning:
- preserve approved composition at section level before progressively replacing pixels with DOM.

### D2C-004 — Hero real-DOM conversion v1/v2/v3

Status: IN_PROGRESS / NOT APPROVED

Shun feedback captured so far:
- image positioning still drifts
- typeface does not match the reference image
- text color does not match
- header/nav contains fine positional differences
- baked text and DOM text can visually overlap
- `SKIN / FOR A / FULLER / TOMORROW` area overlaps / drifts
- Hero lower boundary has visible inconsistencies
- v3 still contains fine misalignment

Current technical conclusion:
- do not continue stacking masks over a text-baked Hero image.
- use a clean Hero photographic asset with no UI/text, then reconstruct typography and decoration in DOM/CSS using the Master solely as the coordinate/visual reference.

### D2C-005 — Clean Hero asset + transition fidelity v4→v12

Status: IN_PROGRESS / NOT APPROVED

Shun feedback preserved:
- unnecessary microcopy must not be added
- seam / white transition must be intentional, not an implementation artifact
- Concept top content must not disappear during seam correction
- original Concept wave + newly invented Hero boundary created a double boundary
- Hero and Concept boundary geometry must match
- v10 still did not fix the transition
- v11 boundary remained visually wrong and rough / jagged

Reusable conclusions:
- one boundary owner only; current owner is Concept
- preserve Concept content below its original boundary
- stop raster-alpha seam tracing
- use vector/SVG Bézier clipping for curved section transitions
- keep the new Hero extended under the Concept overlap so transparent/vector-clipped regions reveal actual Hero instead of white background

Current implementation target:
- `MELT_SKIN_hero_dom_fidelity_v12.html`
- Concept boundary rendered with smooth SVG vector clip rather than raster alpha mask

## Next experiment

Continue D2C-005 until Shun confirms Hero→Concept transition quality. Do not move to Concept DOM conversion yet.

Only after Shun confirms Hero fidelity should the project proceed to Concept DOM conversion.

## Exit criteria

Design-to-Code Fidelity is not solved until all are true:

- no meaningful perceived design-quality drop from Master to production HTML
- typography, color, crop, whitespace, spatial hierarchy, and composition stay faithful
- Motion improves the design without changing its art direction
- production output is real DOM, not merely a single flattened image
- responsive PC/mobile output maintains the same design intent
- Shun explicitly confirms completed reference LP quality
