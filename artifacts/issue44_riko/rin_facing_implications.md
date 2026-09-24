# Issue #44 — Rin-facing implications (NO implementation)

This file is a handoff of research constraints only. It does not authorize Nagi rebuild or Production implementation.

## 1. Separate inputs

- `CreativeFitProfile` decides which family/art-direction logic fits the business/customer.
- `ProductionFeasibility` decides how that selected logic can be realized safely with available media/evidence.
- Feasibility must never silently downgrade or replace the selected creative family.

## 2. Family selection is not template selection

Do not map `industry -> family -> fixed page`.
Use compatible family hypotheses as resolution-space inputs; compare authored candidates when implementation is later authorized.

## 3. Module patterns are decision/composition grammars

A module ID should encode the customer-decision job and composition thesis, not generic UI names such as `cards`, `two-column`, or `FAQ`.

## 4. Template resemblance must be multimodal

Do not build a naive threshold from color or token distance. Highest-signal dimensions are:

- hero silhouette
- module sequence
- dominant grid/alignment behavior
- typography hierarchy
- media framing / crop / mask pattern
- whitespace / density rhythm
- material/decorative grammar
- CTA choreography
- screenshot-level gestalt

## 5. No numeric resemblance hard gate yet

The recovered research does not contain enough actual **same-template-looking labeled pairs** to calibrate a trustworthy numeric threshold.
Schema/storage may follow after Sarah accepts this research contract; hard thresholds require pair calibration.

## 6. Preserve authored exceptions

Stable grammar is allowed. Repeated dominant signatures across unrelated businesses are not.
Do not normalize business-specific scene authority back into one renderer grammar.

## 7. Mobile is re-art-direction

Family/module contracts need mobile authority rules. Desktop collapse/stack is not sufficient.

## 8. Quality locks remain independent

Template distinctness can never excuse evidence, rights, responsiveness, Japanese line composition, accessibility, or functional regressions.

## 9. Suggested later implementation boundaries

If Sarah accepts these findings, implementation can later introduce **data structures** for:

- Creative Fit dimensions
- Creative Family hypotheses
- module/composition pattern metadata
- compatibility/prohibited combination metadata
- Template Resemblance evidence

This Issue does **not** authorize the engine, components, ranking, numeric scoring, or Nagi regeneration.

## STOP

No code, Nagi rebuild, family component library, or template implementation is authorized by Issue #44.
