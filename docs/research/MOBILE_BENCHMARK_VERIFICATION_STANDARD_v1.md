# Mobile Benchmark Verification Standard v1

Updated: 2026-09-15

## Why
A benchmark is not eligible for CORE status merely because its site is responsive. CORE means the mobile experience has been explicitly reviewed as a deliberate art-direction state.

## Required evidence
A frame can be promoted to mobile-verified only when all of the following are supported:

1. A real smartphone/mobile rendering is visible in a trustworthy source or captured from the live site.
2. The primary message survives without semantic fragmentation.
3. The dominant visual authority survives or is purposefully re-art-directed.
4. The next action / CTA remains clear.
5. The layout does not behave like a mechanically scaled desktop canvas.
6. The mobile state preserves the same Company Truth → Form relationship.

## Evidence grades

### M0 — Unknown
No mobile evidence.

### M1 — Responsive claim only
Source says responsive/mobile-first but no usable mobile visual has been reviewed. Not enough for mobile verification or CORE.

### M2 — Published mobile visual reviewed
A real mobile visual from a trustworthy source has been reviewed for hierarchy and art direction. Eligible for `mobile_verified=true` as research evidence, but **not eligible for CORE**.

### M3 — Live / captured 390px review
A live or faithfully captured 390px page has passed copy, hierarchy, interaction and Company Truth → Form review. **M3 is required for CORE.**

This deliberately separates:
- mobile evidence strong enough to learn from (M2)
- production-grade benchmark evidence strong enough to certify as CORE (M3)

## First M2 candidate: 実家のこと。

Evidence:
- Studio Design Award nominee page explicitly states the site was designed mobile-first because mobile users are the majority.
- The official renewal press release publishes both PC TOP and smartphone TOP visuals.
- The mobile composition preserves the warm, forward-looking editorial tone used to reduce the emotional barrier around family-home / end-of-life topics.

Sources:
- https://designaward2025.studio.design/nominate/jikkanokoto
- https://www.atpress.ne.jp/news/444379

## CORE rule
CORE promotion requires all of the following:

- desktop/source visual verification
- `mobile_verified=true`
- `mobile_evidence_grade=M3`
- the primary message survives at 390px
- CTA / next action survives at 390px
- the dominant authority is preserved or purposefully re-art-directed
- Company Truth → Form causality survives mobile

Responsive existence, device mockups, award commentary, gallery SP screenshots, or M2 evidence alone are insufficient for CORE.

## Reporting rule
Until the M3 corpus is large enough, research reports must show M2 and M3 separately. Never combine M2 into the CORE count.
