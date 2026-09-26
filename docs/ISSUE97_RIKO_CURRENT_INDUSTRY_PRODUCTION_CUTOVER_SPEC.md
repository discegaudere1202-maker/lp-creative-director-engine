# Issue #97 — Current-Industry Production Cutover Specification

Status: Riko research / production-architecture specification
Baseline: `acb4678a7e844a40112e561a722b799a8677a601`
Scope: beauty/cosmetics, hair salon/barber, Pilates/fitness only
Implementation owner after Sarah gate: Rin
Human-visible gate owner after implementation: Aoi

## 1. Decision

The accepted controlled CompositionPlan path becomes the architectural source of truth for current-industry Production composition.

Target runtime order:

`Verified Company Truth → Customer Decision State → Creative Fit → Family inference / ambiguity gate → Family frozen → compatible grammar → CompositionPlan → Production Feasibility → copy/media/motion/responsive realization → renderer → automated QA → screenshot artifact → Aoi human-visible review`

Production must not select topology through company id, reference name, fixture label, category keyword, or Family-to-profile lookup. Category remains factual input and asset-library scoping metadata, never a topology key.

The controlled-render PASS from Issues #92/#96 is a regression lock, not a separate permanent production architecture.

## 2. Cutover boundaries

### 2.1 Promote to Production authority

- `authored_composition_contract.py`: normalized authorship input and deterministic CompositionPlan contract.
- CompositionPlan scene intents, topology, variation vector, responsive authorship, feasibility boundary, and review gate.
- the controlled renderer's demonstrated ability to consume plan-derived directives without identity re-inference.
- nine-width authored responsive evidence and 320px semantic Japanese line hard gate.

### 2.2 Retain as regression / compatibility only

- `controlled_production.py` company-specific reference adapters such as `nagi_reference_input()`.
- Nagi / Regina / uka and current controlled-render fixtures.
- Issue #92 controlled render artifact shape and Issue #96 human-visible observations.
- accepted Phase B/C snapshots and fixture ids for tests, evidence packaging, and regression reports.

Reference identities may label fixtures and artifacts. They must not appear in runtime routing conditions.

### 2.3 Retire from Production composition authority

- `production_generation.py::_industry_visual_direction()` as a final topology/profile selector.
- `production_generation.py::_layout_profile()` as a source of final authored form.
- any Company / Reference / Category / Family → fixed layout, Hero, profile, scene sequence, or CTA lookup.
- silent fallback from CompositionPlan failure to `editorial_rail`, `local_route`, `care_rhythm`, or any legacy generic profile.
- renderer-side creative inference that changes scene order, topology, visual authority, CTA choreography, or breakpoint hierarchy.

Existing helpers may temporarily survive behind compatibility adapters during migration, but Production output is blocked whenever they become the source of an authored decision.

## 3. Production routing replacement

### Stage 0 — freeze regression evidence
Preserve accepted controlled evidence, fixture inputs, screenshot manifests, and Aoi PASS notes as immutable comparison references.

### Stage 1 — normalized Production input adapter
Add a current-industry input derivation boundary that emits the same semantic contract required by generalized authorship. It must carry provenance/confidence per factual field and must not derive topology.

### Stage 2 — shadow Production CompositionPlan
For each current-industry Production fixture, generate a CompositionPlan beside the current route. Record semantic differences but do not change public output.

### Stage 3 — CompositionPlan becomes primary composition input
Allow Production renderer entry only when:
- Company Truth minimum fields pass;
- customer decision state is valid;
- Family is frozen;
- CompositionPlan passes identity-routing guard;
- feasibility cannot change Family;
- required renderer directives are complete.

### Stage 4 — deactivate legacy composition selection
Disable category/profile and reference/company authored routing. Keep a test-only adapter for accepted legacy snapshots where needed.

### Stage 5 — delete obsolete runtime branches
After current-industry matrix passes automated and Aoi review, delete unreachable runtime selection branches. Keep regression fixture builders in test/evidence namespaces only.

### Rollback rule
Rollback may restore the prior release binary for service continuity, but must never make legacy identity/category routing an automatic fallback inside a new run. A CompositionPlan failure is fail-closed, not a reason to silently use legacy form selection.

## 4. Current-industry input derivation

### Required Company Truth
- business category: verified, used for factual context and asset-library scoping only;
- company/business name: verified, output identity only;
- at least one verified offer with stable offer id and customer job;
- verified available action / CTA destination or an explicit `NO_VERIFIED_ACTION` state;
- provenance references for every persuasive fact.

### Required Customer Decision State
- primary decision job: `choose | understand | trust | compare | prepare | act`;
- decision stage: `discover | consider | validate | ready`;
- risk sensitivity: `low | medium | high`;
- at least one question or tension explaining why the page exists.

### Optional truth
Location, price, duration, hours, philosophy, qualifications, reviews, process, instructor/stylist/person data, product details, trial conditions, facilities, outcomes.

Optional does not mean inferable. Missing values remain unknown.

### Derivation rules
- derive decision state from verified offer shape, observed conversion route, evidence-supported objections, and explicitly recorded research/hearing facts;
- do not infer a decision job merely from industry label;
- do not map `cosmetics` to one topology, `hair salon` to another, or `Pilates` to another;
- contradictions affecting offer, price, qualification, proof, contact, or result claims block the affected persuasive use;
- if primary decision job is genuinely ambiguous and alternate jobs would materially change topology, stop with `HUMAN_REVIEW_REQUIRED`;
- insufficient truth never becomes synthetic certainty.

## 5. CompositionPlan → renderer contract

### Mandatory directives
Renderer receives, without re-inference:
- `family_id` and `family_version`, already frozen;
- ordered `scene_intents` with decision purpose;
- Hero topology;
- core decision topology;
- trust/proof topology;
- closing / CTA choreography;
- variation vector;
- media-role requirements by scene;
- responsive authorship for 320/360/375/390/430/768/1024/1280/1440;
- feasibility adaptations and blocked claims;
- review-gate state and reasons.

### Renderer may vary safely
Only realization details inside plan bounds, such as measured spacing within token ranges, crop focal point within an approved media role, non-semantic decorative placement, animation duration/easing within the selected motion role, and browser-safe typographic fitting that preserves semantic chunks.

### Renderer must not re-infer
- Family;
- scene order / decision hierarchy;
- Hero type;
- trust authority;
- CTA strategy;
- company/category/profile mapping;
- new claims;
- media as proof;
- breakpoint hierarchy.

If renderer capabilities cannot realize a directive without changing decision semantics, emit `RENDER_CAPABILITY_BLOCKED` or `HUMAN_REVIEW_REQUIRED`; do not substitute another architecture.

### Family grammar without template locking
Family constrains compatible persuasion/composition grammar. It does not prescribe one Hero, scene list, density rhythm, CTA, or responsive silhouette. Company Truth + decision state + evidence shape must remain capable of producing materially different plans inside the same Family.

## 6. Copy integration

Copy planning occurs after Company Truth and decision structure are available and before final rendering.

Headline inputs:
- primary decision job and stage;
- verified offer/job;
- supported differentiator or tension;
- selected scene intent;
- approved factual claims only.

Section heading inputs:
- current scene intent;
- prior/next decision state;
- evidence available for that scene;
- topology role.

CTA inputs:
- verified action destination;
- decision stage;
- remaining uncertainty;
- selected closing choreography.

Hard copy rules:
- persuasive factual statements require evidence ids;
- unknown, provisional, or contradictory facts cannot become positive claims;
- generated atmosphere is never described as real company proof;
- copy variation follows the decision job and Company Truth, not synonyms around a fixed template;
- semantic Japanese line chunks are authored before render and preserved across breakpoints;
- no isolated Japanese particles, noun fragments, or one-character headline/CTA tails;
- 320px optical review is a Hard Gate, not a best-effort check.

## 7. Media-role / asset-library integration

Asset pipeline:

`Industry scope → Business category → Scene intent → Media Role → required content class → candidate asset pool → provenance/rights gate → feasibility selection`

Category may narrow candidate media pools. It must not change Family or page topology.

Every candidate records:
- asset id;
- source/provider;
- creator when known;
- rights status and license evidence;
- checked date;
- content class;
- media role eligibility;
- whether it is actual company evidence, licensed generic material, generated explanation, or authored atmosphere;
- replacement target where validation media is temporary.

Official-site visibility is not reuse permission.

Architecture-validation media from Issue #92 remains valid for architecture regression only. Later real-image Sales Sample media must pass a separate rights/provenance and human-visible Sales Sample gate. Asset absence may adapt execution after Family freeze but cannot choose another Family.

## 8. Motion and responsive authorship

Motion is selected from scene intent and decision job, not company/category identity. Meaningful motion roles include:
- reveal decision sequence;
- compare alternatives;
- demonstrate process/order;
- disclose proof detail;
- clarify CTA state.

Decorative motion must not become the main distinction between otherwise identical templates.

Responsive contract:
- all nine widths are mandatory: 320, 360, 375, 390, 430, 768, 1024, 1280, 1440;
- mobile may reorder local visual presentation only when plan explicitly allows it;
- decision hierarchy and scene intent remain stable;
- mobile is authored, not desktop shrink;
- line, overflow, clipping, sticky/fixed UI, CTA visibility, media crop, and interaction affordance are tested at every width;
- 320px semantic Japanese optical composition is a Hard Gate.

## 9. Fail-closed states

Production output is blocked for:
- `INPUT_TRUTH_INSUFFICIENT`: minimum Company Truth absent;
- `INPUT_CONTRADICTION_BLOCKED`: unresolved contradiction affects persuasive/transactional content;
- `DECISION_STATE_AMBIGUOUS`: materially different primary decision jobs remain plausible;
- `FAMILY_NOT_FROZEN`: Creative Fit unresolved;
- `IDENTITY_ROUTING_DETECTED`: company/reference/category/fixture identity influences topology;
- `PLAN_INCOMPLETE`: mandatory CompositionPlan directives missing;
- `UNSUPPORTED_GRAMMAR`: plan requests renderer grammar outside accepted registry;
- `FEASIBILITY_FAMILY_MUTATION`: feasibility attempts to change Family;
- `CLAIM_EVIDENCE_BLOCKED`: visible factual claim lacks eligible evidence;
- `MEDIA_RIGHTS_BLOCKED`: media lacks acceptable rights/provenance for intended use;
- `RENDER_CAPABILITY_BLOCKED`: renderer cannot realize semantics safely;
- `RESPONSIVE_HARD_GATE_FAILED`: any required width fails browser/line/overflow/optical gate;
- `TEMPLATE_COLLISION_REVIEW`: anti-template evidence cannot establish distinct authorship;
- `HUMAN_REVIEW_REQUIRED`: human-visible ambiguity/collision remains.

None may silently route to a legacy profile.

## 10. Production QA contract

Automated gates:
1. schema/input provenance validation;
2. deterministic plan and render trace for identical normalized input;
3. static scan for runtime company/reference/fixture topology routing;
4. behavioral identity mutation invariance;
5. behavioral decision/evidence mutation sensitivity;
6. Family frozen before feasibility and unchanged after it;
7. no Family/category → fixed Hero/profile assertion;
8. evidence-bound public claim check;
9. media-role/rights/provenance check;
10. semantic copy and line-shape check;
11. nine-width browser/overflow/interaction check;
12. 320px optical hard gate;
13. screenshot and manifest artifact generation;
14. same-Family divergence / cross-Family collision review signals;
15. controlled-render regression lock.

Aoi boundary:
Automated PASS does not establish human-visible authorship or Sales Sample quality. Aoi reviews actual full-page and key-scene screenshots, focusing on silhouette, decision hierarchy, trust/proof placement, media perception, CTA choreography, motion meaning, mobile transformation, and template resemblance. `HUMAN_VISIBLE_PASS` is required for architectural completion of the cutover fixture matrix.

Real-image Sales Sample QA remains later and is not claimed by Issue #97.

## 11. Current-industry completion matrix

Minimum fixture set before current-industry Production architecture is declared complete:

Beauty/cosmetics:
- B1: product/offer choose job, multiple options, strong verified product evidence;
- B2: trust/understand job, sparse proof, generated/licensed atmosphere only;
- B3: same-Family pair with different decision/evidence shape proving visible divergence.

Hair salon/barber:
- H1: first-visit choose/prepare job, services and booking verified;
- H2: trust job with stylist/process proof and medium/high risk sensitivity;
- H3: sparse media or missing price variant proving feasibility adapts without Family mutation.

Pilates/fitness:
- P1: trial/act job with price/schedule/CTA verified;
- P2: trust/prepare job with instructor/process evidence and high risk sensitivity;
- P3: same-Family counterpart preserving the accepted 320px semantic optical lock.

Cross-cutting negative fixtures:
- X1 contradiction in price/qualification/contact → fail closed;
- X2 identity mutation with identical semantic input → identical CompositionPlan;
- X3 category mutation used only as asset-pool scope, with authored inputs held constant → no topology mutation;
- X4 cross-Family near-collision → `HUMAN_REVIEW_REQUIRED`, never forced visual divergence;
- X5 media-rights unknown → media blocked without Family change.

Completion requires all applicable automated gates plus Aoi human-visible PASS on representative positive fixtures and explicit expected fail-closed outcomes on negative fixtures.

## 12. Explicit implementation targets for Rin

1. Promote `authored_composition_runtime.consume_composition_plan()` from shadow-only adapter into a production-capable, guarded directive boundary; production mode must require all accepted contracts rather than merely switching a flag.
2. Build current-industry normalized input derivation before CompositionPlan inference.
3. Make `production_generation.run_generation()` consume plan-derived architecture as authoritative composition input.
4. Move `_industry_visual_direction()` and `_layout_profile()` out of final Production composition authority; either delete after migration or isolate behind regression-only compatibility code.
5. Keep `controlled_production.py` reference builders out of runtime Production routing; move or mark them fixture/regression-only.
6. Add no-identity static + behavioral tests, deterministic tests, plan-consumption tests, and fail-closed tests.
7. Add the completion matrix as current-industry production fixtures.
8. Emit trace showing input provenance → frozen Family → CompositionPlan → feasibility → renderer directives → QA.
9. Package nine-width screenshots for Aoi; do not infer human-visible PASS from CI.

## 13. Acceptance criteria

Issue #97 research/spec is complete when:
- routing replacement is explicit and tied to current repository surfaces;
- normalized input derivation and insufficiency/contradiction gates are defined;
- CompositionPlan→renderer ownership is unambiguous;
- copy/media/motion/responsive integration preserves evidence and non-template authorship;
- rollback is fail-closed and cannot silently restore identity/category routing;
- minimum current-industry fixture matrix covers all three current industry groups and meaningful decision/evidence variants;
- explicit deletion/deprecation targets are named;
- Aoi review boundary is specified;
- Rin can implement without inventing architecture decisions.

No industry expansion, Production-code implementation, merge, Sales Sample readiness claim, or ¥1M quality claim is part of Issue #97.