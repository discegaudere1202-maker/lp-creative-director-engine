# Issue #104｜Current-Industry Visual Asset Library｜Media Role + Rights Contract

Owner: Riko / Research & Creative Direction Architecture  
Baseline: `c7bbcb6b234a88cd3400ce3eb8faeea87ee3d00f`  
Scope: research/spec only  
Industries: Beauty/Cosmetics, Hair Salon/Barber, Pilates/Fitness

---

## 1. Decision

The current Production path already has an authoritative generalized CompositionPlan and has passed current-industry human-visible validation.

The next Production boundary is therefore **not** a new Creative Family or layout system. It is a reusable, auditable Visual Asset Library that can replace architecture-validation media with rights-safe production imagery **without allowing assets to choose the creative architecture**.

Target sequence:

```text
Verified Company Truth
→ Customer Decision State
→ Creative Fit
→ Family frozen
→ CompositionPlan
→ Scene Intent
→ Media Role
→ required content conditions
→ Industry / Business Category candidate pool
→ Rights Gate
→ deterministic visual-fit + reuse-aware selection
→ crop / placement
→ Renderer
→ provenance trace
→ automated QA
→ 9-width screenshot evidence
→ Aoi human-visible review
```

The hard invariant is:

> Asset choice may change visual realization after Creative Fit is frozen. Asset scarcity must never switch Creative Family, topology, layout profile, Hero logic or scene order.

---

## 2. Current evidence lock

Issue #103 closed with `HUMAN_VISIBLE_PASS` on the normal Production CompositionPlan path after inspecting 9 fixtures × 9 widths (81 screenshots).

That accepted state is a regression lock for Asset Library implementation:

- CompositionPlan remains authoritative in normal Production;
- same-Family authored structural divergence remains visible;
- cross-Family near-collision remains honestly reviewable;
- 320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440 remain the browser widths;
- 320px Japanese semantic line composition remains a Hard Gate;
- final intrinsic photo quality / real-image Sales Sample quality is still a later gate.

---

## 3. Existing implementation surface

`src/lp_engine/photography.py` already provides useful mechanics:

- photo-role records;
- asset manifest normalization;
- local binary resolution;
- SHA-256 calculation;
- photo-to-composition binding;
- fake-evidence copy guard;
- image renderer helper.

But its current role/approval/selection boundary was designed before the generalized Production cutover:

- `_family_roles(family, category)` derives a role pack from a visual family/category;
- role selection still reflects earlier family/category-driven assumptions;
- asset rights are represented by simplified `RESEARCH_APPROVED_*` statuses;
- `select_asset_for_role()` primarily selects a matching role by source priority;
- actual stock discovery/library acquisition was intentionally deferred.

Issue #104 does not modify code. It defines the Production replacement contract for Rin.

---

## 4. Library taxonomy

Canonical hierarchy:

```text
Industry
→ Business Category
→ Scene Intent
→ Media Role
→ Content Class
→ Candidate Assets
```

### 4.1 Industry scope

Only:

1. `beauty_cosmetics`
2. `hair_salon_barber`
3. `pilates_fitness`

No industry expansion.

### 4.2 Business Category role

Business Category exists to make asset retrieval semantically useful. It may:

- scope candidate assets;
- restrict inappropriate Media Roles;
- restrict content classes;
- improve content-class matching.

It must not:

- choose Creative Family;
- choose topology;
- choose renderer/layout profile;
- choose scene order;
- act as a fixed template lookup.

### 4.3 Current category buckets

Beauty/Cosmetics:

- skincare/cosmetics product;
- beauty treatment/esthetic;
- beauty retail/consultation.

Hair Salon/Barber:

- hair salon;
- barber;
- head spa/hair care.

Pilates/Fitness:

- Pilates studio;
- personal training/fitness;
- small-group fitness.

These are **asset-pool categories**, not new Creative Families.

---

## 5. Media Role contract

Canonical roles:

- Hero;
- person/staff context;
- consultation;
- process/treatment/training;
- interior/environment;
- result/finish;
- tools/material/detail;
- trust/proof support;
- lifestyle/context.

Not every role is valid for every category.

The category-specific inventory is stored in:

`artifacts/issue104_riko/media_role_inventory_current_industries_v1.json`

### 5.1 Important evidence boundary

Generic visual material may illustrate:

- atmosphere;
- category context;
- generic service process;
- generic training/treatment/craft gesture;
- generic product/lifestyle context.

Generic visual material must not establish:

- actual staff identity;
- actual customer/client identity;
- actual salon/studio/store/interior;
- actual company treatment/training result;
- testimonials;
- qualifications;
- medical/body-transformation/efficacy claims;
- company-specific performance facts.

### 5.2 Result / finish roles

Result/finish is deliberately restricted.

Examples:

- a generic hairstyle may illustrate a hairstyle category but cannot be presented as an actual salon customer/result;
- a generic body/fitness image must not be used as a body-transformation result;
- cosmetics imagery must not function as efficacy proof;
- esthetic/head-spa imagery must not imply therapeutic outcome.

---

## 6. Asset metadata contract

Every Production candidate uses one normalized record defined by:

`artifacts/issue104_riko/asset_metadata_contract_v1.json`

Required areas:

### Provenance

- stable asset id;
- provider;
- provider source id;
- provider/detail-page URL;
- creator when known;
- acquisition/check dates;
- exact binary SHA-256 after acquisition.

### Rights

- license state;
- terms URL;
- terms checked date;
- commercial-use state;
- modification permission;
- crop permission;
- attribution requirement;
- person/model release status;
- property release status;
- trademark/logo risk;
- recheck triggers.

### Visual semantics

- content class;
- industry/category tags;
- eligible scenes/roles;
- orientation/aspect;
- people count/type;
- tone/material-quality tags;
- evidence-vs-illustrative state;
- prohibited/misleading uses.

### Provenance confidence

- HIGH;
- MEDIUM;
- LOW;
- UNKNOWN.

LOW/UNKNOWN does not silently become Production approved.

---

## 7. Rights Gate

Machine-readable contract:

`artifacts/issue104_riko/rights_gate_contract_v1.json`

### 7.1 Gate order

1. source identity;
2. license terms present;
3. commercial-use permission;
4. modification/crop permission;
5. attribution compatibility;
6. person/property/trademark review;
7. evidence boundary;
8. binary integrity;
9. freshness/recheck;
10. Production eligibility.

### 7.2 Hard locks

- Official-site visibility is **not** reuse permission.
- Unknown/insufficient rights fail closed.
- Provider commercial license is not a blanket waiver of person/property/trademark rights.
- Generic stock remains illustrative.
- Generated imagery remains illustrative unless separately proven as company evidence (normally it is not).
- Rights failure cannot change Family.

### 7.3 Primary fail/review states

- `MEDIA_SOURCE_UNKNOWN`
- `MEDIA_LICENSE_UNKNOWN`
- `MEDIA_COMMERCIAL_USE_BLOCKED`
- `MEDIA_MODIFICATION_BLOCKED`
- `MEDIA_ATTRIBUTION_UNSATISFIED`
- `MEDIA_PERSON_RIGHTS_REVIEW_REQUIRED`
- `MEDIA_PROPERTY_RIGHTS_REVIEW_REQUIRED`
- `MEDIA_TRADEMARK_REVIEW_REQUIRED`
- `MEDIA_EVIDENCE_BOUNDARY_MISMATCH`
- `MEDIA_BINARY_CHANGED`
- `MEDIA_RIGHTS_STALE`
- `MEDIA_ROLE_UNSATISFIED`
- `HUMAN_REVIEW_REQUIRED`

No silent fallback to an unsafe stock asset.

---

## 8. Evidence status

Four states:

### `ACTUAL_COMPANY_EVIDENCE`

Can support factual claims only when:

- company identity/provenance matches;
- rights to publish are verified;
- relevant evidence ledger entry exists;
- recognizable people have an appropriate verified rights basis or company warranty where required;
- fact scope matches copy.

### `GENERIC_ILLUSTRATIVE_STOCK`

May create context, not fact.

### `PROJECT_OWNED_GENERATED_ILLUSTRATION`

May create context/atmosphere, not company fact.

### `ARCHITECTURE_VALIDATION_ONLY`

Current validation media remains regression evidence. It does not automatically enter Real-image Sales Sample production inventory.

---

## 9. Free-first sourcing policy

Initial acquisition must remain free-first while business profitability is unproven.

Current provider research on 2026-09-26 supports Pexels, Unsplash and Pixabay as **candidate providers**, not universal asset whitelists.

### Pexels

Provider materials state free commercial use, modification permission and no mandatory attribution, with restrictions including misleading endorsement/brand use and standalone redistribution.

### Unsplash

Provider materials allow most commercial uses without mandatory attribution, but explicitly warn that recognizable people, private property and trademarks can create additional rights requirements and that release scope cannot be guaranteed for every upload.

### Pixabay

Provider materials allow free use/modification subject to prohibited uses and generally do not require attribution, while explicitly noting separate trademark/personality/property/privacy rights and responsibility for necessary consent.

Durable source notes:

`artifacts/issue104_riko/free_source_license_evidence_registry_v1.json`

Policy consequence:

> Provider license PASS is the first gate. It is never the final asset approval.

Official company websites/social accounts are evidence sources only; do not harvest their binaries as reusable stock without explicit permission.

Paid sources such as PIXTA may be considered only after an explicit profitability/budget gate or when free inventory cannot meet quality/uniqueness/rights needs.

---

## 10. Deterministic selection contract

Machine-readable contract:

`artifacts/issue104_riko/selection_reuse_contract_v1.json`

Selection order:

```text
Family already frozen
→ Scene Intent
→ Media Role
→ Required Content Conditions
→ Current Industry
→ Business Category pool
→ Rights Gate
→ Visual Fit Ranking
→ Reuse Penalty
→ Crop Feasibility
→ Stable tie-break
```

No randomness.

Same:

- CompositionPlan;
- catalog version;
- rights state;
- usage-ledger snapshot;
- placement request

must produce the same selection.

### 10.1 Visual-fit sort dimensions

1. exact content class;
2. scene intent;
3. Media Role;
4. orientation/crop feasibility;
5. tone fit to frozen CompositionPlan;
6. material-quality fit;
7. people-context fit;
8. reuse penalty;
9. stable asset-id tie-break.

Renderer must not re-infer another role/family because a better-fitting asset is unavailable.

---

## 11. Reuse without template smell

Photos may be reused across companies in the same industry/category. A zero-reuse policy would be unnecessarily expensive and would not itself guarantee authored quality.

The correct contract is **controlled reuse with usage memory**.

### Hard rules

- one exact binary cannot occupy multiple dominant roles in one LP;
- Hero assets must be unique inside the same active generation batch unless explicitly reviewed;
- same asset + same role + same crop must not repeat across adjacent/current Production outputs;
- do not reuse another company's complete media-role asset bundle;
- reuse pressure cannot alter Family/topology;
- crop changes alone do not make the same bundle authored/distinct.

### Logged similarity signals

- recent same-role reuse;
- recent same-category reuse;
- same crop fingerprint;
- same asset-sequence overlap;
- same Hero + supporting pair overlap.

Issue #104 intentionally does **not** invent a universal numeric Template Resemblance threshold. Log the metrics first, generate batches, then calibrate thresholds from actual Aoi reviews.

---

## 12. Asset provenance trace

Every renderer-bound asset must remain auditable.

Contract:

`artifacts/issue104_riko/asset_provenance_trace_contract_v1.json`

Trace must include:

- CompositionPlan id / frozen Family;
- scene + Media Role;
- content conditions;
- candidate query;
- all candidate asset ids;
- candidate rejection reasons;
- selected asset id;
- provider/source/license references;
- rights result/conditions;
- evidence status;
- usage-ledger snapshot;
- reuse penalties;
- crop variant/focal point;
- binary SHA;
- renderer binding id.

The screenshot manifest must be joinable back to asset id + binary hash.

---

## 13. Minimum current-industry inventory

Contract:

`artifacts/issue104_riko/minimum_current_industry_asset_inventory_matrix_v1.json`

Counts are distinct approved binaries, not crop variants.

### Global minimum

- every required Hero pool: at least 3 assets;
- every required supporting role: generally at least 2 assets;
- Hero pool must include at least two materially different subject/composition clusters;
- every Hero pool must have landscape-safe and mobile-crop-safe candidates;
- validation-only media does not count;
- person-bearing assets individually pass person/endorsement review.

### Minimum totals by category

| Industry | Category | Minimum distinct assets |
|---|---|---:|
| Beauty/Cosmetics | skincare/cosmetics product | 10 |
| Beauty/Cosmetics | beauty treatment/esthetic | 14 |
| Beauty/Cosmetics | beauty retail/consultation | 11 |
| Hair Salon/Barber | hair salon | 18 |
| Hair Salon/Barber | barber | 18 |
| Hair Salon/Barber | head spa/hair care | 14 |
| Pilates/Fitness | Pilates studio | 16 |
| Pilates/Fitness | personal training/fitness | 16 |
| Pilates/Fitness | small-group fitness | 12 |

If all nine current-scope categories are enabled, the defined minimum is **129 distinct approved assets**.

This is an acquisition floor, not a proof of quality.

---

## 14. Acquisition sequence

### Stage A — Core

Acquire rights-approved pools for:

- skincare/cosmetics product;
- hair salon;
- barber;
- Pilates studio.

Goal: enough visual diversity to run real Production library integration and multi-company anti-reuse tests.

### Stage B — Adjacent current scope

Add:

- beauty treatment/esthetic;
- beauty retail/consultation;
- head spa/hair care;
- personal training/fitness;
- small-group fitness.

No new industries.

### Stage C — Batch diversity calibration

Generate multiple companies per category and measure:

- Hero reuse;
- role reuse;
- crop fingerprint reuse;
- media sequence overlap;
- same-Family visual repetition.

Aoi reviews screenshot batches. Only then calibrate numeric reuse/Template Resemblance limits if evidence supports them.

---

## 15. Real-image Sales Sample QA start gate

A category may enter **Real-image Sales Sample QA** only after:

- its minimum inventory is complete;
- 100% selected assets pass rights/provenance gates;
- no generic asset is represented as company evidence;
- Hero uniqueness in generation batch passes;
- renderer trace includes selected ids + hashes;
- all 9 widths can render screenshots;
- Aoi can inspect actual selected visuals.

Passing this gate means only **QA may start**.

It does not mean:

- Sales Sample Ready;
- ¥1M quality achieved;
- final real-company visual truth is complete.

---

## 16. Rin implementation handoff

Full handoff:

`artifacts/issue104_riko/rin_implementation_handoff.md`

Implementation units:

1. normalized Asset schema;
2. provider-neutral ingestion;
3. Production cache by binary SHA;
4. rights evaluator;
5. candidate query;
6. deterministic selector;
7. usage ledger;
8. anti-reuse gates;
9. renderer AssetBinding;
10. provenance trace;
11. automated tests;
12. 9-width screenshot artifact.

### Existing `photography.py` disposition

Retain/adapt:

- render helper mechanics;
- local asset hash verification concept;
- fake-evidence safety intent;
- role-binding concept.

Replace/deprecate as Production authority:

- `_family_roles()`;
- simplified `RESEARCH_APPROVED_*` as sufficient rights approval;
- source-type priority as the primary selector;
- first-match role selection.

New Production authority is:

```text
Frozen CompositionPlan scene intent
→ Media Role contract
→ rights-safe category candidate pool
→ deterministic selection
```

---

## 17. Automated QA required after implementation

### Data/schema

- required metadata;
- enum validation;
- provider/detail URL;
- terms reference;
- binary SHA;
- recheck state.

### Rights

- unknown rights fail closed;
- commercial-use blocked fails;
- official-site-only asset blocked from reusable stock pool;
- generic stock blocked from factual company evidence slot;
- attribution handling;
- person/trademark conditional review;
- stale/revoked/hash-changed blocked.

### Selection

- deterministic generation;
- no random selection;
- no identity routing;
- category changes candidate pool only;
- asset scarcity leaves Family unchanged;
- empty pool fails/reviews explicitly;
- reuse penalty only changes allowed asset choice.

### Anti-template

- batch Hero uniqueness;
- repeated role+crop surfaced;
- bundle cloning surfaced;
- same-Family authored structural divergence preserved.

### Browser/render

- selected hash appears in trace;
- no broken image;
- no destructive crop;
- attribution visible when required;
- all 9 widths;
- 320px semantic text regression lock;
- screenshot manifest with asset ids/hashes.

---

## 18. Aoi human-visible boundary

After implementation/technical audit, Aoi must inspect actual selected visual outputs.

Aoi reviews:

- incorrect staff/store/company implication;
- stock-photo obviousness;
- scene/category semantic mismatch;
- implausible human context;
- crop quality;
- visual rhythm;
- Hero authority;
- same-category repetition;
- full-page template smell;
- mobile media composition;
- consistency with the authored LP rather than a generic stock collage.

CI may confirm contracts and screenshots exist. It cannot establish the final human-visible judgment.

---

## 19. Acceptance criteria for Issue #104

Issue #104 research/spec is complete when GitHub contains durable contracts for:

- taxonomy;
- current-industry Media Role inventories;
- Asset metadata;
- Rights Gate;
- deterministic selection;
- reuse/anti-repetition;
- free-first sourcing;
- source-license evidence registry;
- minimum current-industry inventory;
- provenance trace;
- Rin implementation handoff;
- Aoi boundary;
- machine-readable contract check.

And all Hard Locks remain true:

- no industry expansion;
- no Production Family/topology redesign;
- no official-site reuse assumption;
- no fabricated evidence;
- no stock-as-company-evidence;
- no asset-driven Family switching;
- research/spec only;
- no Sales Sample readiness claim;
- no merge from this task.

---

## 20. Routing after acceptance

```text
Riko Issue #104
→ Sarah research / rights / architecture audit
→ Rin Visual Asset Library implementation + acquisition tooling
→ Sarah technical/evidence audit
→ Aoi human-visible Asset Library Production QA
→ Real-image Sales Sample QA (separate later Hard Gate)
```
