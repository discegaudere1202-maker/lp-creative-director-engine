# Prototype Lab Batch 02 Findings v1

Updated: 2026-09-15

Targets:
- P07 Photo Crop Direction
- P17 Mobile Re-Art Direction
- P19 CTA Emotional Closure
- P21 Sales State → Enriched State

Lab note:
P07/P21 use an existing free/context test photograph only to evaluate crop and layout mechanics.
It is **not client evidence** and must never be represented as such in an actual sales sample.

---

# P07 Photo Crop Direction

Three versions used the same source image.

## P07A — default center/cover
### Finding
Functional, but visually weak.
The photograph occupies space without a clear visual job.

### Lesson
`good image + cover:center` is not Photo Direction.

---

## P07B — material/context first crop
### Finding
Strongest of the three for showing the sign in its street/store context.
The crop deliberately keeps:
- sign
- entrance
- surrounding facade
while removing some irrelevant edges.

### Lesson
Crop brief should name the focal relationship, not only focal object.
Example:
`sign + entrance + street context`
not just `sign`.

---

## P07C — copy-safe crop
### Finding
Demonstrates that negative space is part of the asset specification.
Text and subject can share a frame without blindly placing a dark overlay over the entire image.

### Risk
Gradient/overlay can quickly become a generic Web-design trick.
Use only when the source photo naturally supports the intended copy zone.

### New rule
Every major image slot should specify:
- focal subject
- focal relationship
- copy-safe zone
- allowed crop loss
- viewport-specific focal point

---

# P17 Mobile Re-Art Direction

## Result
**PASS as a method prototype**

Desktop:
copy and process visual are shown side-by-side.

Mobile:
visual comes first, copy second.
The order changes but the factual message remains the same:
- 看板一式
- 取付まで
- 文字だけ

### Finding
Responsive quality is not only type scaling.
**Narrative order can change by viewport.**

### New rule
A mobile art-direction contract may change:
- order
- crop
- type scale by semantic line
- visual ratio
- amount of secondary copy

It may not change:
- factual meaning
- core promise
- primary CTA intent

---

# P19 CTA Emotional Closure

## Result
**Direction PASS / copy fact-safety review remains project-specific**

### Finding
A CTA can close the service structure instead of introducing a generic sales message.
The prototype uses the three verified service-range ideas as the lead-in to action.

### Lesson
Final CTA should answer:
`What promise from earlier in the page is being completed here?`

If answer is only `contact us`, CTA is weak.

### New rule
CTA Emotional Closure requires:
- callback to Hero/Big Idea
- last objection reduction
- single action
- no new major claim

---

# P21 Sales State → Enriched State

## Result
**Core hypothesis validated in layout prototype**

Sales State:
- no client photo
- complete frame using typography + verified service structure + abstract facade visual
- no visible photo placeholder in a real deliverable

Enriched State simulation:
- same grid
- same headline
- same evidence row
- visual slot receives a photographic asset
- Art Direction is not rebuilt

### Important
The screenshot used for Enriched simulation is a research asset, not a client-owned photo.
The purpose is to test insertion mechanics only.

## Pixel Rhythm observation
Using the same composition:

### Desktop 1440
Sales State:
- edge_mean_avg: 0.0527
- quiet_score_avg: 0.4677

Enriched State:
- edge_mean_avg: 0.0924
- quiet_score_avg: 0.2291

### Mobile 390
Sales State:
- edge_mean_avg: 0.0469
- quiet_score_avg: 0.6300

Enriched State:
- edge_mean_avg: 0.0762
- quiet_score_avg: 0.4533

### Interpretation
Real photography naturally increases pixel density substantially, while the information hierarchy can remain unchanged.

Therefore:
**Sales State and Enriched State must not be compared as if they were ordinary visual regressions.**
They are intentional asset-state variants.

---

# New concept — Asset State Contract

Every project should explicitly declare:
- `SALES_STATE`
- `ENRICHED_STATE`

Pixel Rhythm regression should normally compare:
- SALES v1 → SALES v2
- ENRICHED v1 → ENRICHED v2

Do not automatically review:
- SALES → ENRICHED density increase

unless hierarchy/order/crop contracts break.

---

# Client Evidence Slot specification learned from P21

A slot needs more than a name.

Example:
`HERO_REALITY`

Fields:
- purpose
- preferred_orientation
- preferred_aspect_ratio
- focal_subject
- focal_relationship
- shot_distance
- copy_safe_zone
- light_direction
- minimum_resolution
- crop_tolerance
- avoid
- mobile_variant

For a storefront/sign example:
- focal_subject: sign
- focal_relationship: sign + entrance
- shot_distance: whole facade, readable sign
- preferred_orientation: portrait or near-square if the visual column is tall
- avoid: extreme angle / night darkness / cut-off sign

This becomes future interview-app input.

---

# Batch 02 Laws

1. Photo selection and Photo Direction are separate tasks.
2. `center/cover` is not art direction.
3. Negative space should be requested at capture time when possible.
4. Mobile may change narrative order while preserving meaning.
5. CTA should close the Big Idea, not merely append a button.
6. Sales State can be a finished design without client photos.
7. Enriched State should strengthen evidence, not replace the design concept.
8. Client Evidence slots require a shot specification.
9. Pixel Rhythm needs an explicit asset-state dimension.
10. Future interview tooling should be generated from slot requirements, not from a generic questionnaire.
