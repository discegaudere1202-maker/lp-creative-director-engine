# Issue #49｜Riko Multi-Company Creative Fit × Family Selector Validation

## Status

**OWN-SCOPE VALIDATION COMPLETE / PM AUDIT CANDIDATE**

This task validates the Issue #44 eight-family research taxonomy against the merged Issue #47 Production Architecture contract. It does not rebuild Nagi and does not implement a renderer/runtime selector.

## Validation design

- 16 real Beauty/Wellness or directly adjacent companies
- 8 Creative Families
- 2 materially different dominant cases per Family
- 23 accepted Creative Fit dimensions annotated for every case
- first-party official source/provenance recorded for every case
- Production Feasibility kept outside Creative Fit

Dominant-family coverage:

- BW-F01 Sensory Sanctuary / Atmospheric Rest: THREE, BAUM
- BW-F02 Clinical Calm / Structured Reassurance: Regina Clinic, Takami Clinic
- BW-F03 Editorial High-Consideration / Aspirational Authority: kakimoto arms, pilates K
- BW-F04 Human Craft / Provenance-Led Intimacy: SHIRO, uka
- BW-F05 Guided Choice / Diagnostic Clarity: POLA APEX, FANCL
- BW-F06 Proof-Led Process Authority: BODY ARCHI, zen place
- BW-F07 Local Human / Community Warmth: Lino Hair, Barbaro
- BW-F08 Category Education / Open Discovery: Rintosull, LAVA

## Main verdict

# READY_WITH_EXPLICIT_AMBIGUITY_RULES

The validation does **not** justify a ninth Family. It also does **not** justify a naive fully automatic winner-takes-all selector.

The eight-family taxonomy covers all 16 cases when the selector reasons from the customer's first persuasive job and supports dominant Family + secondary influence. The principal remaining problem is collision handling between adjacent Families.

## Key collision rules

### BW-F02 vs BW-F06

Both can have high trust, clinical expertise and process inspectability. Use **F02** when the page must first reduce safety/suitability/wrong-choice anxiety. Use **F06** when the page must first prove that a method or mechanism can credibly produce change.

### BW-F05 vs BW-F08

Use **F05** when the customer already accepts the category but cannot choose among options. Use **F08** when the customer still needs to understand the category and self-place before option routing.

### BW-F01 vs BW-F04

Use **F01** when sensory/experiential imagination itself carries desire. Use **F04** when maker, human technique or material provenance is indispensable to trust and meaning.

### BW-F03 vs BW-F04

Use **F03** when aspirational/premium authority leads. Use **F04** when premium authority must resolve into maker/provenance/craft authority.

### BW-F04 vs BW-F07

Human warmth is not enough for F07. **F07 requires locality/community/ongoing nearby relationship to materially change the buying decision.** Otherwise human craft/provenance remains F04.

### BW-F06 vs BW-F08

Use **F06** when mechanism credibility is the gating question; **F08** when category understanding is the gating question.

## Creative Fit vs Production Feasibility

A controlled rich-asset vs sparse-asset counterfactual was applied to all 16 cases using only the accepted Production Feasibility variables.

Result: **16 / 16 dominant Families unchanged.**

Therefore the Issue #47 hard boundary remains valid:

> Production Feasibility can adapt realization after selection, but cannot select or silently change Creative Family.

## Family is not a template

Two different cases were compared inside each of the eight Families. Result: **8 / 8 Family pairs require materially different composition possibilities.**

Examples:

- Clinical Calm can be counseling/risk/price-led or diagnosis/treatment-path-led.
- Human Craft can be producer/material/factory provenance or practitioner/technique/method provenance.
- Proof-Led Process can be measurement/device/before-after proof or research/explanation/practice proof.
- Category Education can teach machine-Pilates mechanics or hot-yoga trial/category understanding.

A runtime shortcut of `family_id -> fixed layout_id` is therefore invalid.

## Comparison with current Issue #47 architecture

Issue #47 correctly established:

- separate Creative Fit and Production Feasibility schemas
- dominant Family + secondary influence representation
- post-selection feasibility adaptation
- Family != fixed template

However the current architecture is a **validation contract, not yet an inference selector**. The current `select_family()` path validates a dominant Family already supplied in the Creative Fit profile. Issue #49 provides the evidence-backed inference rules that must precede that validation step.

## Rin-facing runtime requirement

The runtime selector should:

1. start from verified company truth and customer decision state;
2. reject Production Feasibility fields at the family-inference stage;
3. identify the first persuasive job before CTA;
4. generate plausible Family candidates from that job + Creative Fit;
5. apply explicit collision and misfit rules;
6. return dominant Family + optional secondary + acceptable alternatives;
7. return `HUMAN_REVIEW_REQUIRED` rather than force a winner when two Families remain co-dominant;
8. freeze the Family result before Production Feasibility adaptation;
9. preserve provenance and reasoning.

No calibrated family probability or numeric threshold is claimed here.

## Human review must remain for

- genuine co-dominance after collision rules
- unclear customer category readiness
- unclear decision relevance of locality
- premium authority vs provenance when neither is subordinate
- clinical reassurance vs mechanism proof when neither is subordinate
- materially novel contexts outside validated Beauty/Wellness and adjacent coverage

## Closure / confidence limits

The 16-case set is deliberately balanced qualitative validation, not a statistically representative market sample. The second materially different case in every Family sharpened composition and boundary rules but did not expose a new Family. Further work should therefore expand regression coverage around edge cases rather than reopen broad taxonomy discovery by default.

Creative Fit values are expert ordinal annotations, not learned weights. Conversion superiority between a dominant Family and an acceptable alternative has not yet been experimentally measured.

## Durable artifacts

- `artifacts/issue49_riko/validation_company_registry.json`
- `artifacts/issue49_riko/creative_fit_expected_labels.json`
- `artifacts/issue49_riko/collision_ambiguity_report.json`
- `artifacts/issue49_riko/feasibility_invariance_checks.json`
- `artifacts/issue49_riko/family_composition_variation_validation.json`
- `artifacts/issue49_riko/selector_rule_proposal.json`
- `artifacts/issue49_riko/rin_facing_selector_contract.json`
- `artifacts/issue49_riko/validation_closure_report.json`
- `artifacts/issue49_riko/issue49_contract_check.json`

## Routing

**Riko Issue #49 → Sarah research/contract audit → if PASS, Rin runtime selector implementation + automated multi-company regression.**

No merge, Nagi rebuild or Production visual implementation is authorized by this research task.
