# Issue #57｜Reference Companies #2–#3 Cross-Company Transfer Validation Design

## Status

**RESEARCH / SELECTION / SPECIFICATION COMPLETE**

This task prepares Phase B transfer validation. It does not implement Production output.

## Selected Reference Companies

### Reference Company #2 — レジーナクリニック

- Issue #49 case: `V49-03`
- expected dominant Family: **BW-F02 — Clinical Calm / Structured Reassurance**
- secondary influence: **BW-F06 — Proof-Led Process Authority**
- first persuasive job: reduce safety / suitability / wrong-choice anxiety before commitment
- expected CTA logic: reassurance and process clarity → **free counseling reservation**

Why selected: Regina creates a materially different high-trust decision state from Nagi. The page should be driven by medical boundaries, counseling/process transparency and suitability reassurance rather than atmosphere or category discovery.

### Reference Company #3 — uka

- Issue #49 case: `V49-08`
- expected dominant Family: **BW-F04 — Human Craft / Provenance-Led Intimacy**
- secondary influence: **BW-F06 — Proof-Led Process Authority**
- acceptable alternatives for explicit ambiguity review: BW-F06 / BW-F01
- first persuasive job: establish trust in human technique, accumulated salon method and practitioner judgment
- expected CTA logic: method / menu understanding → **salon-specific booking**

Why selected: uka is the strongest negative control against Nagi because both are head-spa-adjacent, yet their customer decision jobs differ. If the architecture is real, the system must not map the shared service category to Nagi’s BW-F08 composition.

## Reference Set #1–#3

| Reference | Company | Dominant Family | Primary decision job |
| --- | --- | --- | --- |
| #1 | なぎのみらい | BW-F08 | category education / open discovery before choosing a service |
| #2 | レジーナクリニック | BW-F02 | safety / suitability / wrong-choice reassurance |
| #3 | uka | BW-F04 | human craft / provenance / practitioner-method trust |

The three-reference set deliberately spans materially different trust logic and composition grammar.

## Creative Fit / Production Feasibility Boundary

For both selected companies:

1. Company Truth and customer decision state determine Creative Fit.
2. Runtime inference determines dominant Family + optional secondary influence.
3. The Family is frozen.
4. Production Feasibility is evaluated afterward.
5. Feasibility may adapt safe realization/media usage but **may not change the Family**.

Asset quantity, official-site media abundance, evidence quantity, scraping difficulty and rights convenience were not used to select the companies or their Families.

## Composition Transfer Hypotheses

### Nagi / BW-F08
Expected center of gravity:

- recognition / open discovery
- tension naming
- intent-routed service field
- low-pressure next event

Known Issue #53 grammar includes `M-HERO-01`, `M-PROBLEM-01`, `M-SERVICE-01`, `M-CTA-01`.

### Regina / BW-F02
Expected center of gravity:

- evidence/reassurance first view
- visible known/unknown and suitability boundaries
- distributed proof
- process-as-proof
- commitment ladder toward counseling

Minimum implementation evidence: `M-HERO-02`, `M-TRUST-01`, `M-PROCESS-01`, `M-CTA-01`.

### uka / BW-F04
Expected center of gravity:

- method/provenance story
- human technique / relationship evidence
- atmosphere only when it supports the authored method story
- state-specific salon booking

Minimum implementation evidence: `M-STORY-01`, `M-HUMAN-01`, `M-CTA-01`.

The current accepted registry contains no F04-specific hero pattern. This is a **registry coverage boundary**, not permission to invent a fixed F04 hero template and not evidence for a ninth Family. The opening must be authored from the F04 decision job and compatible grammar, then human-reviewed.

## Cross-Company Non-Template Requirements

Transfer success requires visible differences in:

- screenshot gestalt
- hero silhouette
- section topology
- module sequence
- grid/alignment
- typography hierarchy
- media framing
- whitespace/density rhythm
- material grammar
- CTA choreography
- responsive authorship

Color, photo, logo or copy replacement alone does not establish uniqueness.

### Template-swap failure examples

- Regina or uka keeps Nagi’s hero and section topology and only replaces content/tokens.
- The same pale wellness field, rounded-image rhythm, serif hierarchy, beige pills and whitespace cadence becomes the universal system grammar.
- uka uses Nagi’s three-service/category-routing structure despite its different first persuasive job.
- Regina remains atmosphere-led while clinical boundaries/process reassurance are visually secondary.
- Family metadata changes but screenshot gestalt and composition grammar do not.
- Production Feasibility causes a Family switch.

## Evidence / Safety

### Regina

- Medical claims must remain first-party and source-bounded.
- Do not invent efficacy, pain, duration, eligibility or outcome claims.
- Generated people cannot be represented as actual doctors, staff or patients.
- Before/after proof requires verified provenance, consent, rights and claim context.
- Price, campaign, clinic and operational details are volatile and must be re-verified at implementation time.

### uka

- Do not fabricate practitioners, customers or documentary salon scenes.
- Do not convert wellness language into medical claims.
- Official media visibility does not establish reuse rights.
- If rights-safe practitioner imagery is unavailable, preserve BW-F04 through composition/copy/provenance logic rather than switching Family or fabricating human proof.
- Current menu, price, salon and campaign facts must be re-verified at implementation time.

## Next Rin Task

Recommended next task:

**[Rin] Reference Companies #2–#3 Controlled Production Transfer Validation × Cross-Company Non-Template QA**

Rin should generalize the Issue #53 controlled Production runner to accept versioned reference contracts, then run both selected companies through:

`Company Truth → Customer Decision State → Creative Fit → Runtime Family Inference → Family freeze → Production Feasibility → Module/Composition grammar → generation → QA/evidence`

Required evidence:

- 9 widths per company: 320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440
- architecture trace
- selector output
- frozen Family + feasibility profile
- module grammar provenance
- browser evidence
- line/overflow QA
- manifest/digest
- three-company Nagi / Regina / uka screenshot comparison

Required regression:

- Issue #51 16-case selector regression
- Issue #53 controlled-production regression
- generic LP Engine QA
- feasibility counterfactual per new company
- no `layout_id`
- no company-name/case-ID lookup masquerading as inference

## Known Uncertainty

- Official-site image availability does not establish Production reuse rights.
- Volatile facts must be re-verified on the implementation date.
- F04 hero realization remains human-reviewed because the current module registry has no F04-specific hero grammar.
- Three references provide meaningful Phase B transfer evidence but do not prove universal robustness across all eight Families.
- Human-visible authorship/template distinctness cannot be closed by research or CI; it requires rendered cross-company review.

## Verdict

Issue #57 research/specification is complete for Sarah audit.

**No Production code changes. No fixed layouts. No feasibility-driven Family switching. No numeric Template Resemblance threshold.**
