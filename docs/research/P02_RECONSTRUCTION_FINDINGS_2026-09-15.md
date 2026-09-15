# P02 Customer-world Translation — Reconstruction Findings

Updated: 2026-09-15

Artifact:
- `examples/prototypes/p02_customer_world_translation_v3.html`

Status:
- craft artifact reconstructed
- 9-width responsive regression added
- formal Blind Tournament: **NOT_RUN**
- provisional frame role: **EXPLAINER / MID_PEAK candidate**

## Why P02 was reconstructed first

P02 is highly transferable to NO_WEB / SME professional-service sales samples because it does not need expensive photography to create Company Truth -> Form causality.

The underlying truth in the Mahora instance is:

> Customers often know what is happening in their company before they know the legal / labor-system term for it.

The visual form therefore does not merely say “we explain clearly.”
It performs the translation:

`specialist classification -> customer situation -> consultation language`

The screen itself demonstrates the service value.

## Iteration findings

### Early reconstruction
The first reconstructed desktop artifact looked clean but exposed a Japanese line-shape failure:

- `相談の言` / `葉へ。`

This was rejected immediately even though the overall composition looked polished.

Lesson:
A visually premium frame can still be production-invalid when the Japanese line shape damages meaning.

### Desktop v2
The semantic headline break was fixed, but the desktop composition left too much inactive space between the main explanation and the closure.

The mobile version was stronger than desktop.

This was treated as an axis-specific failure:
- Form Causality: strong
- Mobile Quality: strong
- Immediate Read: strong
- Desktop Share Impulse / visual tension: weaker

No broad cosmetic redesign was performed.

### Current v3
The desktop composition was rebuilt around the translation operation itself:

- left: promise / interpretation logic
- right: three specialist terms becoming three customer-world questions
- top: verified experience evidence (`20年 / 300社以上`)
- bottom: the conversion idea closes as `制度名ではなく、いまの状況を。`

The larger customer-language typography is caused by the service promise rather than by a desire for “big type.”

## Intermediate-width failure caught

A critical finding appeared only after rendering the full required QA widths.

The 1440px and 390px states both looked healthy, but the first v3 responsive rules broke at 768px / 1024px:

- customer-language content was clipped to the right
- desktop grid minimums were too rigid
- 1024px created a semantic fragment ending in `か。`
- 320px produced a lead-copy fragment ending in `ります。`

These failures were fixed by:

- removing rigid desktop grid minimums
- adding a deliberate tablet composition
- switching to a stacked intermediate composition below 860px
- adding meaning-aware breakpoint line control only where necessary

This validates the existing 9-width policy.

**Endpoint QA is insufficient.**

A candidate can pass 1440px and 390px while being unusable at 768px / 1024px.

## Current nine-width state

Checked widths:

- 320
- 360
- 375
- 390
- 430
- 768
- 1024
- 1280
- 1440

Current reconstructed artifact has:

- no horizontal overflow at all nine widths
- no known 1–2 Japanese-character semantic fragments in the tested copy-bearing selectors
- meaning-aware headline shape
- a distinct tablet composition
- a distinct mobile composition

Regression coverage is now in:
- `tests/test_p02_customer_world_translation.py`

## Mobile re-art direction

390px is not a scaled desktop layout.

Desktop:
- explicit column labels
- horizontal translation arrows
- explanation-logic rail
- two-column interpretation

Mobile:
- labels are removed
- each technical term becomes a compact preface
- the translation arrow turns vertical
- customer language becomes the dominant reading sequence
- explanation-logic rail is removed because it would duplicate the meaning already expressed by the vertical flow

The strategic idea remains the same while the composition changes.

## Owner specificity assessment

Stronger than a generic “we explain simply” section because it contains:

- labor-specific specialist terms
- customer-world labor questions
- Mahora's official experience evidence
- the actual explanation policy as visual grammar

Still not formally benchmark-competitive until it survives anonymous comparison.

## Share Impulse assessment

Current desktop is materially stronger than the earlier reconstruction, but this prototype should not be forced into a HERO job merely to raise visual spectacle.

Its natural role is currently:

**high-craft EXPLAINER / possible MID_PEAK**

If a Blind Tournament shows that Share Impulse is the only losing axis, the next intervention should increase the memorability of the translation event itself—not add unrelated color, grain, cards, bento, parallax, or decorative motion.

## Formal Tournament blocker

Do not label this prototype `BENCHMARK_CHALLENGED` yet.

Production Tournament requires:
- 3–5 relevant Benchmark opponents
- 1440 x 1000 capture for Candidate + every Benchmark
- 390 x 844 capture for Candidate + every Benchmark
- Benchmark mobile evidence grade M3

The current strict Benchmark corpus intentionally has no M3 references yet.

Therefore `NOT_RUN` remains correct.

## Transfer rule extracted

For specialist services:

**Do not explain the service taxonomy first. Visualize the gap between the customer's lived problem and the professional's taxonomy.**

The design opportunity is the translation distance itself.

This can transfer to:
- labor / HR
- legal
- accounting / tax
- insurance
- B2B technical services
- construction / engineering consultation
- IT / security consultation

The styling must not transfer unchanged. Only the causal rule transfers.
