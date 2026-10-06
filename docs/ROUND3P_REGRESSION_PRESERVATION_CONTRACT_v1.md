# Round 3P｜Regression Prevention & Preservation Contract v1

Status: `PROPOSED / RIKO_COMPLETE / SARAH_INTEGRATION_PENDING`

Task: Issue #14  
Purpose: prevent `A improved, B/C/D regressed` across all future LP rounds.

---

# 0. Non-negotiable rule

Every corrective task is executed as:

> **Targeted Delta + Preserve Baseline**

A candidate is not allowed to pass because it is `better overall` when it has lost an approved strength that was outside the intended change scope.

The unit of control is not the round. The unit of control is the **declared change and its preserved neighborhood**.

---

# 1. Required artifacts before a corrective round starts

A correction task MUST have all four artifacts before implementation begins.

## 1.1 Approved Baseline Manifest

Identifies exactly what candidate is being modified.

Required:

- case ID
- baseline HEAD / PR / run / artifact identity
- desktop screenshot set
- mobile screenshot set
- actual rendered copy snapshot
- evidence/safety snapshot
- responsive widths
- approved strengths
- rejected / non-preserved signatures

If no approved baseline is frozen, implementation must stop.

## 1.2 Preserve Ledger

Lists what must survive the task.

Every entry has a preserve level:

### `HARD`
Any loss = hard fail.

Examples:

- factual truth
- rights / safety
- known quality invariant
- verified contact
- no overflow

### `MATERIAL`
The exact pixels may change, but the approved human-visible effect must survive.

Examples:

- S6 remains a material trust / contrast anchor
- S3/S4 representative media remains integrated rather than stock-card insertion
- mobile remains separately authored

### `SOFT`
Preferred continuity, but may be traded intentionally when a stronger solution is documented.

Soft loss still requires an intentional-change record.

## 1.3 Intentional Change Ledger

Every planned change must declare:

- change ID
- target scene(s)
- target viewport(s)
- problem being solved
- human-visible expected gain
- copy impact
- design impact
- responsive impact
- safety/evidence impact
- allowed collateral changes
- forbidden collateral changes
- acceptance evidence

Anything that changes without a ledger entry is an incidental change until proven otherwise.

## 1.4 Comparison Package

Must be possible to review baseline vs candidate without reading implementation history.

Minimum:

- desktop full-page before / after
- mobile full-page before / after
- changed scene crops before / after
- unchanged neighbor scene crops before / after
- rendered copy before / after

---

# 2. Change classification

Every observable delta belongs to exactly one class.

## `INTENTIONAL_CHANGE`
Declared before implementation and linked to an accepted target problem.

## `PRESERVED`
No material human-visible loss in a protected element.

Preserved does not mean pixel-identical when the preserve type is MATERIAL.

## `INCIDENTAL_CHANGE`
Not declared, but visible / semantic / behavioral output changed.

Default handling: FAIL until reviewed and reclassified.

## `REGRESSION`
A prior approved property materially worsened.

Regression is always FAIL.

---

# 3. Regression matrix

Every major section and viewport receives a matrix row.

Recommended columns:

| field | meaning |
|---|---|
| scene | S1…Sn / navigation / footer |
| viewport | 320…1440 or named group |
| layer | COPY / DESIGN / MEDIA / INTERACTION / SAFETY / RESPONSIVE |
| baseline state | frozen human-visible state |
| intended change ID | null if preservation-only |
| candidate state | observed candidate state |
| classification | intentional / preserved / incidental / regression |
| gain | visible improvement if any |
| loss | visible loss if any |
| disposition | PASS / RETURN |

A page-level summary must not hide a section-level regression.

---

# 4. Screenshot difference contract

Pixel diffs are **change detectors**, not quality judges.

Use them to answer:

- did an allegedly untouched area move?
- did media disappear?
- did a crop change?
- did type wrap / scale change?
- did late-page geometry shift?
- did mobile reorder unexpectedly?

Do not use:

> `pixel difference < threshold => quality preserved`

Quality preservation requires human-visible comparison for MATERIAL items.

---

# 5. Copy semantic difference contract

The system must compare actual rendered copy, not only source manifests.

Each changed text block is classified as:

- `INTENTIONAL_SEMANTIC_CHANGE`
- `PUNCTUATION_OR_LINEBREAK_ONLY`
- `INCIDENTAL_SEMANTIC_CHANGE`
- `REMOVED_COPY`
- `ADDED_COPY`

For any copy outside the declared task scope:

- semantic delta = FAIL by default
- punctuation / linebreak delta = review against Japanese line composition

A design task does not get permission to silently rewrite copy.

A copy task does not get permission to silently alter layout authority.

---

# 6. Responsive regression contract

Required baseline widths remain:

`320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440`

At minimum compare:

- first viewport
- each intentionally changed scene
- adjacent preserved scene
- late-page / ending

Responsive PASS requires more than no overflow.

Watch:

- hierarchy loss
- media authority loss
- forced type shrink
- CTA displacement
- line-composition degradation
- excessive stacking
- scene-rhythm flattening

A desktop gain with a mobile loss is FAIL.

---

# 7. Evidence / safety regression contract

Any visual / copy improvement must retain:

- verified fact boundary
- representative media boundary
- disclosure where needed
- rights state
- verified contact state
- no fabricated customer / staff / premises / proof / price / duration / outcome

Safety regression is `HARD` and cannot be traded for visual or copy quality.

---

# 8. Quality gain / loss ledger

For each intentional change, record:

```text
change_id
quality_gain[]
quality_loss[]
neutral_effects[]
preserved_elements[]
reviewer_conclusion
```

Rules:

1. `quality_loss` cannot be omitted because the candidate is better overall.
2. A loss against a HARD preserve item = FAIL.
3. A loss against a MATERIAL preserve item = FAIL unless that exact item was intentionally reopened before implementation.
4. A SOFT loss requires explicit tradeoff acceptance by Sarah.
5. A gain must be visible in actual copy / actual pixels; artifact intention is insufficient.

---

# 9. Gate redesign

## G0 — Technical Integrity

Machine-led.

Checks:

- builds / scripts
- assets load
- links
- no overflow / truncation
- required viewport render
- basic accessibility floor
- Japanese line invariant

G0 can never declare human-visible quality.

## G1 — Safety / Evidence

Machine + evidence review.

Checks:

- factual boundary
- media provenance / role
- public-output safety
- contact integrity

## G2 — Copy Quality

Human-visible copy gate.

Owner: Mio / Sarah.

Inputs:

- rendered page copy
- copy-only transcript
- evidence boundary

Forbidden PASS reason:

> structurally correct / safe / contains persuasion roles

The copy itself must be strong enough relative to the approved copy ceiling.

## G3 — Design Quality

Human-visible design gate.

Owner: Riko / Sarah.

Inputs:

- actual desktop full-page render
- actual mobile full-page render
- scene crops

Internal contracts are hidden on first pass.

Forbidden PASS reason:

> composition family exists / media role exists / art-direction token exists

Actual pixels must reach the rubric ceiling.

## G4 — Cross-round Preservation / Regression

Inputs:

- baseline manifest
- preserve ledger
- intentional-change ledger
- screenshot diff
- semantic copy diff
- regression matrix
- quality gain/loss ledger

Any unexplained incidental delta = RETURN.

Any material regression = FAIL.

## G5 — Full-page Human Reality

Independent human-style review.

Order:

1. screen first
2. actual copy second
3. full-page experience
4. only then rationale

Questions:

- does it feel made for this business?
- does any part look cheaper / more generic than the surrounding page?
- does copy become synthetic / explanatory / safe-but-flat?
- does design become agency-signature-first?
- is the late page as authored as the hero?
- does mobile feel intentionally designed?

G5 must be allowed to contradict G0–G4 mechanism compliance.

## G6 — Shun Final

Only invoked after G0–G5 PASS.

Shun is asked for final owner-level value perception, not day-to-day art direction or copy surgery.

If Shun returns the work despite G0–G5 PASS, the next task must first update the quality / gate model from the miss before patching the screen.

---

# 10. Review order to reduce confirmation bias

Human-visible gates must not begin with the implementation specification.

Correct order:

1. candidate only
2. baseline vs candidate
3. copy-only transcript when evaluating copy
4. section crops
5. mobile
6. then internal rationale / ledgers

A reviewer who reads `S6 is a strong dark anchor` before seeing S6 is biased toward finding that intention.

---

# 11. Preservation rules across specialist handoffs

## Riko → Rin

Riko must hand off:

- design ceiling target
- baseline / preserve ledger
- targeted visual deltas
- rejected engine signatures

Rin may change implementation technique, but may not change preserved customer / copy decisions unless explicitly reopened.

## Mio → Rin

Mio must hand off the exact approved copy snapshot plus allowed display-level adjustments.

Rin must not write marketing copy to solve layout problems.

## Rin → Aoi

Rin supplies actual pixels / actual copy plus provenance artifacts.

Aoi reviews screen/copy first.

## Aoi → Sarah

Aoi reports visible gains / losses by scene. Sarah reconciles against the preservation ledger.

---

# 12. Failure diagnosis after a returned candidate

Do not automatically create a broader architecture after a return.

Classify first:

- `QUALITY_MODEL_MISS`
- `COPY_CEILING_MISS`
- `DESIGN_CEILING_MISS`
- `IMPLEMENTATION_TRANSLATION_MISS`
- `PRESERVATION_MISS`
- `RESPONSIVE_MISS`
- `SAFETY_MISS`
- `HUMAN_CALIBRATION_MISS`

Then reopen only the causal layer.

---

# 13. Hard anti-regression acceptance rules

A candidate is automatically RETURN if any is true:

1. undeclared customer-facing copy changed
2. undeclared major composition changed
3. approved media disappeared or changed role
4. approved scene authority visibly collapsed
5. mobile hierarchy worsened
6. Japanese line quality worsened
7. evidence / safety boundary weakened
8. late-page authorship materially worsened
9. business specificity materially worsened
10. generic engine signature materially increased

The existence of gains elsewhere does not neutralize these failures.

---

# 14. Completion definition for this contract

This contract is complete when Sarah can issue future tasks with:

- a frozen baseline
- explicit preserved elements
- targeted deltas
- visible before/after evidence
- hard regression disposition

without asking Shun to identify micro-failures.
