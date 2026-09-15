# Prototype Lab Batch 03 Findings v1

Updated: 2026-09-15

Targets:
- P04 Business Verb Motion
- P10 Document / Annotation
- P11 Material Physicality
- P12 Product Behavior
- P13 Asymmetric Editorial Composition
- P20 Objection as Design
- P23 Proof Proximity
- P24 Restraint Delta

Artifact:
`prototype_lab_batch03_v2.html`（research runtime artifact; generated outside repo）

Important:
Lab text / generic material / generic product visuals are research devices unless explicitly marked as previously verified Golden Sample facts.
Do not treat generic lab data as client evidence.

---

# Browser QA history

## v1
Visual direction was usable, but semantic line QA failed repeatedly.
Observed examples:
- 街の顔にな / る。
- 難しい言葉 / を、
- 重ねるほ / ど、
- 小さく持っ / て、
- 任せられ / る。

Failures appeared not only at 320/390 but also 768/1440 in some compositions.

## v2
Fixes:
- semantic line spans
- viewport-specific type scale
- document row stacking before mobile breakpoint
- headline recomposition
- smaller Type where preserving a meaning chunk mattered more than visual size

QA:
- 320: horizontal overflow 0 / short semantic fragments 0
- 390: horizontal overflow 0 / short semantic fragments 0
- 768: horizontal overflow 0 / short semantic fragments 0
- 1440: horizontal overflow 0 / short semantic fragments 0

### New lesson
**Semantic integrity outranks intended type size.**
If a premium-looking 56px headline causes a bad Japanese fragment, the type scale/composition is wrong, not the QA rule.

---

# P04 Business Verb Motion

## Result
**METHOD PASS / PREMIUM HOLD**

What works:
- `つくる → 立てる → 街の顔になる` gives motion a business/process reason.
- One object changes state instead of using 3 Step Cards.
- Still frame retains the process idea.

Why Premium HOLD:
The current three rectangles are generic geometry.
They demonstrate the method but do not yet encode a specific owner's material, sign construction, mounting method, proportions or site context.

### New rule
Business Verb alone is not enough.
Premium Form needs:
`business verb + owner-specific object/constraint/material`.

A generic “assemble” animation is still AI-smell if many industries can reuse it unchanged.

---

# P10 Document / Annotation

## Result
**STRONG METHOD PASS / BENCHMARK TOURNAMENT NEXT**

What works:
- Technical term and plain-language meaning coexist in one physical document.
- Annotation is not decoration; it visually performs “understanding”.
- Works particularly well for Asset-light professional services.
- Mobile stacks technical/plain language instead of shrinking the desktop table.

Risk:
Annotations can accidentally create legal meaning or advice not explicitly verified.

### New rule
Document/Annotation requires two data layers:
- `SOURCE_TEXT` — verified wording
- `PLAIN_LANGUAGE_INTERPRETATION` — review-required interpretation

Never allow an interpretation to look like an official document quote.

---

# P11 Material Physicality

## Result
**FAIL**

Why:
- Generic stacked ellipses imply “layers” but not a real material.
- Grain background is a visual effect, not material observation.
- The physical behavior does not identify wood/paper/paint/metal/liquid.
- Could be reused by unrelated industries.

This is exactly the kind of polished abstraction that can look AI-generated.

### New rule — Material Observation Contract
Material authority cannot enter prototype build until we can specify at least 3 of:
- weight
- resistance/friction
- layering
- reflection
- transparency
- deformation
- edge behavior
- surface irregularity
- tool interaction
- time/change behavior

If source evidence does not support these, use another Visual Authority.

---

# P12 Product Behavior

## Result
**METHOD HOLD / PREMIUM FAIL**

What works:
State A → Action → State B is immediately understandable.

Why Premium FAIL:
The bars are generic.
There is no product-specific geometry or mechanical reason.
It demonstrates “expand/fold”, but cannot identify why this product deserves this behavior.

### New rule
Product Behavior prototype must include:
- actual product geometry OR verified schematic abstraction
- actual trigger/action
- actual benefit caused by that behavior

No generic “fold/expand” motion as signature visual.

---

# P13 Asymmetric Editorial Composition

## Result
**METHOD PASS / OWNER-SPECIFICITY PENDING**

What works:
- Clearly escapes center-aligned / equal-grid defaults.
- Large headline, vertical index, micro-note and delayed answer create hierarchy without cards.
- Mobile maintains asymmetry rather than snapping into generic centered stack.

Risk:
“Asymmetry” itself can become a style template.

### New rule
Every intentional break from grid must answer:
**What company-specific reason earns this break?**

If none, return to a simpler grid.

---

# P20 Objection as Design

## Result
**STRONG METHOD PASS / EVIDENCE REQUIRED**

What works:
- Objections are presented as the prospect's mental state, not FAQ Cards.
- Hover/de-emphasis moves confusion toward one actionable starting point.
- The final message can close a prior value promise.

Critical risk:
For a real sales sample, objection chips cannot be invented as if they were known customer voice.

### New rule
Objection source priority:
1. verified FAQ / public review / official explanation
2. industry-common objection clearly labeled as hypothesis internally
3. generic UX hypothesis

Only level 1 can be presented as owner/customer-specific evidence.
Levels 2–3 may shape architecture but must not masquerade as testimonials or known customer concerns.

---

# P23 Proof Proximity

## Result
**METHOD PASS / CRAFT HOLD**

What works:
- Evidence is placed immediately beside/under the promise instead of exiled to a later “実績” section.
- Shows why claim/proof distance is an art-direction variable.

Current weakness:
The frame is intentionally sparse, but the proof relation is still mostly textual.
It does not yet transform evidence into a unique Form.

### New rule
Proof Proximity and Evidence Monument are different:
- Proximity = where proof appears
- Monument = how proof becomes visual authority

Premium can require both.

---

# P24 Restraint Delta

## Result
**REVIEW TOOL PASS / NOT A CLIENT FRAME PATTERN**

What works:
The side-by-side experiment makes “AI premium clichés” easy to see:
- gradient
- blobs
- multiple rounded cards
- unnecessary visual events

The restrained version makes the editorial decision legible.

### New rule
P24 is not a design template.
It becomes a required Creative Red Team operation:
1. duplicate candidate
2. remove ~20% labels / decoration / ambient motion
3. compare hierarchy, brand meaning, share impulse
4. keep the reduced version when meaning becomes stronger

---

# Preliminary external-benchmark critic

This is **not** an official Blind Tournament because candidate/benchmark identity was not fully hidden and identical screenshot conditions were not yet available.

Directionally:
- P10 is closest to a Core60-quality method because Form performs the service value.
- P20 has strong sales-LP transferability but needs verified objection inputs.
- P13 is visually authored but can become a generic art-direction trick unless Owner Truth earns the asymmetry.
- P04 has a correct semantic-motion principle but generic object form.
- P23 is useful architecture but not yet a screenshot peak.
- P11/P12 are below benchmark quality and remain FAIL.
- P24 belongs to the review process, not final visual language.

---

# Batch 03 new laws

1. Business Verb must combine with owner-specific object/material/constraint.
2. Material Style without Material Observation is not Premium.
3. Product Behavior without real geometry/mechanics is not Premium.
4. Interpretation and source text need distinct visual/data provenance.
5. Asymmetry requires a reason, not taste.
6. Objection Design requires evidence provenance.
7. Proof position and proof visual authority are separate variables.
8. Restraint Delta is a mandatory review operation, not a look.
9. Semantic Japanese line integrity outranks visual size intention.
10. Method prototype PASS is distinct from Benchmark Supremacy PASS.

---

# Status after Batch 03

Validated as methods:
- P04 HOLD-to-PASS method
- P10 PASS
- P13 PASS
- P20 PASS with evidence contract
- P23 PASS method
- P24 review-tool PASS

Failed at Premium level:
- P11 Material Physicality
- P12 Product Behavior

Next:
1. Rebuild P11 from a real observed material
2. Rebuild P12 from a real product mechanism
3. Put P10/P20/P13 through Core60 Blind Tournament
4. Add P18 Logo-off Owner Specificity as an automated review operation
5. Add P20 evidence provenance to future hearing-data contract
