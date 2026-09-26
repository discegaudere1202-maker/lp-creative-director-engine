# Rin Handoff｜Issue #114 Premium Uplift Implementation Contract

## Goal

Implement the minimum premium-authorship uplift on the existing current-industry Production path without changing Family taxonomy or the accepted Stage A safety/rights architecture.

This is **not** permission to add industries, introduce company-ID templates, map Family to one fixed layout, fabricate missing evidence, weaken Visual Asset Library rights gates, or replace CompositionPlan authority.

## 1. Public Copy Transformation Layer

Add a renderer-facing authored-copy stage after CompositionPlan/scene intent is frozen.

Inputs: verified company truth, customer decision state, frozen Family, scene intent, verified evidence, offer/contact conditions.

Outputs per scene: public headline, support copy, proof copy, CTA microcopy, evidence refs.

Hard failures:
- `recognize/choose/trust/prepare/compare/act` rendered as raw public headings when they are only internal intent tokens;
- generic QA phrases such as `CompositionPlanの意図から...` rendered on the sales surface;
- factual copy without eligible evidence.

Tests: banned internal-token surface test; banned validation-copy surface test; factual-claim provenance test; deterministic semantic-input test.

## 2. Hero Authority Composer

Do not replace the current plan with a Family→Hero map. Derive visual authority source, proposition type, media/text geometry, proof/context adjacency and mobile Hero recomposition. The same Family must produce materially different Hero silhouettes when decision/evidence/company truth differ.

## 3. Scene Dramaturgy Planner

Extend plan directives with scene weight, density mode, width mode, media/text relationship, transition/chapter boundary, proof adjacency and mobile recomposition instruction. Fail if every scene collapses to an undifferentiated stacked block.

## 4. Media Story Binder

Reuse Issue #104 Visual Asset Library authority. For each selected asset add story function, linked scene intent, linked evidence ids where applicable, crop intent, caption mode, sequence role and mobile priority. Generic illustrative media must remain illustrative.

## 5. Proof + CTA Choreographer

Proof: map objection/question → verified evidence → scene placement. Never promote illustrative media to evidence.

CTA: require verified destination/action before rendering an actionable positive CTA; render primary/secondary hierarchy; stage reassurance before action when the plan requires; allow controlled re-entry points; render actual actionable `<a>`/button semantics.

No verified destination: do not invent one. Emit a traceable blocked/review state or transparent non-action fallback.

## 6. Premium Visual Voice Primitives

Keep one engineering system, but allow plan-derived visible expression: type relationship/scale, text measure, spacing cadence, rule/border treatment, surface depth, image geometry and emphasis style. Do not create `family_id -> css_file` lookup. Add trace showing which authored inputs selected each primitive.

## 7. Meaningful Motion

Motion is optional per scene. If used, require purpose (`hierarchy`, `sequence`, `comparison`, `feedback`), trigger, element and reduced-motion fallback. Reject random/decorative motion as a uniqueness mechanism.

## 8. Mobile Premium Recomposition

At 320 / 360 / 375 / 390 / 430, re-evaluate media order, proof adjacency, text measure, CTA placement, chapter pacing and semantic line units. Do not merely inherit desktop DOM order if it weakens the first persuasive job.

## Regression fixtures

Exact cases: `SK1 SK2 SK3 HS1 HS2 BR1 BR2 PI1 PI2`.

Exact widths: `320 360 375 390 430 768 1024 1280 1440`.

Expected screenshot count: `81`.

Preserve Issue #111 rights/provenance, deterministic selection, reuse controls, Family freeze, same-Family divergence, near-collision honesty, 320px semantic gate and no overflow/clipping.

## New automated gates

1. no internal scene-intent token leaked to public headings;
2. no Stage A validation copy leaked to sales surface;
3. every factual public claim has evidence trace;
4. positive CTA requires verified destination and actionable element;
5. no Family/identity/category direct visual-template lookup;
6. Premium visual primitives have authored-input trace;
7. motion has purpose and reduced-motion fallback if present;
8. mobile authored directives exist at 320–430;
9. all 81 screenshots render;
10. before/after contact sheets are produced.

## Evidence package for Sarah / Aoi

Produce 81 full-page screenshots, contact sheets at 320/390/768/1440, before/after contact sheets vs Artifact `10912860741`, per-case composition + uplift trace, public-copy provenance trace, asset trace, CTA trace, motion trace, mobile authorship trace and automated QA manifest.

## Aoi boundary

Aoi reviews actual screenshots for Hero authority, full-page authored rhythm, typography hierarchy, media/story integration, proof choreography, CTA choreography, meaningful motion, mobile premium feel, detail richness, template smell and evidence perception.

Aoi should not fail the Engine merely because a future real client has not yet supplied actual staff/store/result/testimonial evidence. That is `CLIENT-EVIDENCE-DEPENDENT` unless the Engine falsely simulates it.

## Stop / escalate

Return `HUMAN_REVIEW_REQUIRED` or explicit blocked state when evidence contradicts, CTA destination is unavailable but a transactional CTA would otherwise be claimed, near-collision remains unresolved, rights/provenance fail, or renderer cannot honor authored plan without a legacy template fallback.

Do not silently fall back to the Stage A validation UI.
