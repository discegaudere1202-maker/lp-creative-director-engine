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
Source says responsive/mobile-first but no usable mobile visual has been reviewed. Not enough for CORE.

### M2 — Mobile visual reviewed
Real mobile visual available and hierarchy/art direction reviewed. Eligible for `mobile_verified=true`.

### M3 — Live 390px review
Live/captured 390px page has additionally passed copy, hierarchy and interaction review. Preferred for production-grade Benchmark Supremacy.

## First M2 candidate: 実家のこと。

Evidence:
- Studio Design Award nominee page explicitly states the site was designed mobile-first because mobile users are the majority.
- The official renewal press release publishes both PC TOP and smartphone TOP visuals.
- The mobile composition preserves the warm, forward-looking editorial tone used to reduce the emotional barrier around family-home / end-of-life topics.

Sources:
- https://designaward2025.studio.design/nominate/jikkanokoto
- https://www.atpress.ne.jp/news/444379

## Rule
CORE research count must report M2 and M3 separately until enough M3 benchmarks exist.
