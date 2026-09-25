# Issue #57｜Rin Implementation Handoff

## Next controlled validation
Implement Reference Companies #2–#3 through the accepted Production Architecture after Sarah PASS on Issue #57.

### RC57-02 — レジーナクリニック
- expected dominant Family: **BW-F02**
- secondary: **BW-F06**
- first persuasive job: reduce safety/suitability/wrong-choice anxiety before commitment
- minimum grammar evidence: `M-HERO-02`, `M-TRUST-01`, `M-PROCESS-01`, `M-CTA-01`
- CTA: free counseling reservation after reassurance/process clarity
- do not reproduce Nagi's BW-F08 recognition/service-routing topology

### RC57-03 — uka
- expected dominant Family: **BW-F04**
- secondary: **BW-F06**
- first persuasive job: establish trust in human technique/provenance and accumulated method
- minimum grammar evidence: `M-STORY-01`, `M-HUMAN-01`, `M-CTA-01`
- CTA: method/menu understanding → salon-specific booking
- same head-spa-adjacent context as Nagi must still produce a materially different composition

## Required implementation shape
Generalize the Issue #53 controlled Production runner to accept a versioned reference-company contract. Preserve the sequence:

`Company Truth → Customer Decision State → Creative Fit → Runtime Family Inference → Family freeze → Production Feasibility → Module/Composition grammar → generation → QA/evidence`

Do not add company-name/case-ID lookup rules. Do not add `family_id -> layout_id`.

## Feasibility invariance
For each company, run at least one counterfactual that changes only asset/rights/evidence feasibility. The inferred Family must remain frozen.

For uka, specifically test a no-reusable-practitioner-photo state. The system must adapt realization without switching away from BW-F04 or fabricating practitioner proof.

For Regina, test a reduced-photo/rights state. The system must remain BW-F02 and rely more heavily on verified boundary/process information rather than atmosphere.

## Module contract
Use only `data/production_architecture/module_composition_registry_v1.json` as the accepted grammar source.

RC57-03 exposes an important coverage boundary: the registry contains no F04-specific HERO pattern. Do **not** solve this by creating a fixed F04 hero template. Author the opening from the F04 decision job and compatible story/human/atmosphere grammar, and keep the result human-reviewed.

If a secondary-Family module is selected, record why the secondary influence authorizes it; do not silently treat it as dominant-Family compatibility.

## Evidence package
For each of the two companies capture:
- 320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440
- architecture trace
- selector output
- frozen Family + feasibility profile
- selected module grammar + provenance
- browser evidence
- line/overflow QA
- manifest + digest

Also produce a **three-company cross-reference comparison**: Nagi / Regina / uka.

## Cross-company human-visible gate
Review structure, not just tokens:
- screenshot gestalt
- hero silhouette
- section topology / module sequence
- grid and alignment
- typography hierarchy
- media framing
- whitespace/density rhythm
- material grammar
- CTA choreography
- responsive authorship

Color/photo/logo/copy swaps alone do not establish uniqueness. No numeric resemblance threshold.

## Safety
### Regina
Keep medical claims source-bounded. Do not fabricate outcomes, suitability, pain, duration or before/after proof. Generated people cannot be represented as actual doctors/staff/patients.

### uka
Do not fabricate practitioners/customers or documentary salon scenes. Do not convert wellness language into medical claims. Current menus/prices/stores must be re-verified at implementation time.

Official-site image availability is **not** reuse permission for either company.

## Required QA
- dedicated transfer-integration tests
- Issue #51 16-case selector regression
- Issue #53 controlled-production regression
- generic LP Engine QA
- 18-width line/overflow QA
- PM-OPS Ready-for-Review PASS
- complete screenshot package for Sarah/Aoi human-visible review

## Routing
Rin controlled transfer implementation → Sarah technical/evidence audit → Aoi independent human-visible cross-company review → Sarah decides whether Phase B transfer evidence is sufficient for the next Production Architecture lock step.
