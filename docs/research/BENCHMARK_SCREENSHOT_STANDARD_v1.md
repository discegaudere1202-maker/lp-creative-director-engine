# Benchmark Screenshot Standard Contract v1

Updated: 2026-09-15

## Purpose
Blind Benchmark Tournamentで、Design Quality以外のCapture差が勝敗へ混ざるのを防ぐ。

比較画像は“参考画像を拾う”のではなく、可能な限り同条件で作る。

---

# 1. Required viewports

Every Tournament candidate/benchmark pair:
- Desktop: **1440 × 1000 CSS px viewport**
- Mobile: **390 × 844 CSS px viewport**

Device pixel ratioは同一Run内で統一。

MobileはDesktop縮小画像を使わない。
実Mobile layoutをCaptureする。

---

# 2. Frame types

TournamentではPage全体ではなくFrame roleを合わせる。

Allowed:
- HERO vs HERO
- MID_PEAK vs MID_PEAK
- CTA_CLOSURE vs CTA_CLOSURE
- EXPLAINER vs EXPLAINER
- MATERIAL_PEAK vs MATERIAL_PEAK
- PRODUCT_DEMO vs PRODUCT_DEMO

禁止:
HeroをBenchmarkのFooter/Utility sectionと戦わせる。

---

# 3. Capture state

Default:
- cookie / consent / campaign modal closed when legally/technically possible
- browser chrome not included
- scroll position fixed to intended frame start
- hover none unless interaction frame comparison
- focus ring none unless accessibility/UI comparison
- animation settles to designed resting state
- lazy-load completed
- font loading completed

If the frame's meaning depends on animation:
Capture:
1. `STILL_FINAL`
2. optional `MOTION_KEYFRAME`

Tournament overall should never require motion to understand the basic message.

---

# 4. Identity masking

Reviewer must not see:
- company name when masking is technically possible and would not destroy the frame
- production company name
- award label
- source URL
- self/benchmark flag
- filename exposing identity

However:
Product/brand identity that is structurally inseparable from the design may remain.
When it remains, mark Tournament as `PARTIAL_BLIND`.

Do not edit imagery so aggressively that the design itself is damaged just to hide identity.

---

# 5. Context line

Reviewer may receive one neutral line:

`industry / frame role / conversion objective`

Examples:
- `professional service / HERO / consultation`
- `manufacturing / MATERIAL_PEAK / trust`
- `D2C product / PRODUCT_DEMO / purchase interest`

Context must not contain:
- company name
- benchmark prestige
- award status
- whether the item is ours

---

# 6. Screenshot normalization

Do not normalize away real design decisions.

Allowed:
- crop browser chrome
- close overlays
- same viewport
- same file format/background rendering

Not allowed:
- recolor benchmark
- replace benchmark copy
- blur benchmark logo but not candidate logo if identity masking changes hierarchy
- resize individual elements
- enhance image quality on one side only

---

# 7. Mobile rule

A candidate cannot PASS Benchmark Supremacy if:
- Desktop win-rate >= .60
- Mobile win-rate < .45

Reason:
Quality Ceiling is not Desktop-only.

Mobile reviewer additionally inspects:
- semantic line shape
- thumb/CTA reachability when relevant
- crop meaning
- content order
- hierarchy after re-art-direction

---

# 8. Screenshot provenance

Each screenshot record stores:
- `benchmark_id`
- `frame_role`
- `viewport`
- `captured_at`
- `source_url`
- `capture_method`
- `identity_blindness`: FULL / PARTIAL
- `motion_state`: STILL / FINAL / KEYFRAME
- `notes`

Source metadata is excluded from reviewer UI but retained in research ledger.

---

# 9. Benchmark eligibility

A reference enters a live Tournament only when:
- Source is verified
- frame role is identified
- screenshot is current enough for the intended comparison
- capture quality is sufficient
- no overlay/capture error dominates the frame

Old historical award screenshot can remain a research reference, but live Tournament should prefer a usable captured frame or official high-quality case screenshot.

---

# 10. Outcome handling

Tournament loss does not mean “copy the winner”.

Loss axes determine specialist return path:
- Owner specificity → Source Depth / Form Causality
- Craft detail → Typography/Photo/Motion specialist pass
- Immediate read → Copy/Hierarchy pass
- Trust → Evidence/Proof pass
- Conversion → CRO/CTA pass
- Mobile → Mobile Re-Art Direction
- Share impulse → Big Idea / Screenshot Peak pass

Benchmark is an opponent, not a template.
