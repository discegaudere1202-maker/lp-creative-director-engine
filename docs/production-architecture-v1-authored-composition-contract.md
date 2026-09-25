# Production Architecture v1 — Company Truth → Authored Composition Contract

Status: implementation-ready research specification for Issue #87
Scope: current beauty / cosmetics / hair salon / Pilates-fitness domains only
Baseline: Phase C accepted outputs, starting from e25b7371642f6f1444c4ec4c4ebf5b609d4e0b94

## 1. Contract boundary

This document defines the input-to-authorship contract for Rin. It does not change the renderer, generate assets, or infer facts from company identity. The contract consumes normalized, provenance-bearing inputs and produces an authored plan plus a feasibility plan.

Two stages are intentionally separate:

1. Creative Fit selects and freezes the Creative Family from customer decision work, evidence shape, and offer logic.
2. Production Feasibility adapts execution to available media, viewport constraints, and verified proof without changing the selected Family.

A missing asset can change how a Family is executed; it cannot silently select another Family.

## 2. Normalized input contract

Required fields:
- Company Truth: category, name, offers, and unknowns.
- Customer decision state: primary job, tensions, questions, risk sensitivity, decision stage.
- Frozen Creative Family: family ID/version, rationale, fit score.
- Evidence inventory: facts, proof gaps, contradictions.
- Media roles: role, required content class, rights, evidence boundary.

Optional fields:
- location, hours, philosophy, qualifications, reviews, price, duration, CTA destination, renderer capabilities.

Every factual value carries confidence (verified, provisional, unknown, contradictory) and source references. Every source records authority and rights. Unknown values stay unknown. Contradictory values never collapse into positive claims. A required unknown or contradiction becomes a feasibility gap and may force human review.

Normative data shapes:

    CompanyTruth
      businessCategory: verified domain category
      name, location, offers, contact, hours, philosophy
      qualifications, experience, reviews
      unknowns: string[]

    CustomerDecisionState
      primaryJob: choose | understand | trust | compare | prepare | act
      tensions: string[]
      questions: string[]
      riskSensitivity: low | medium | high
      decisionStage: discover | consider | validate | ready

    CreativeFamilyInput
      familyId, familyVersion, rationale, fitScore
      frozen: true

    EvidenceInventory
      facts, proofGaps, contradictions, mediaRoles

    MediaRoleInput
      roleId, role, requiredContentClass
      actualProof: false
      rights: owned | licensed | generated | unknown

## 3. Authorship inference

The authored plan is deterministic. Every decision records an input path and an explanation.

It produces:
- scene intents and scene order;
- hero topology;
- core decision composition;
- trust/proof composition;
- media cadence;
- closing and CTA choreography;
- responsive authorship;
- variation vector;
- fit trace;
- feasibility plan;
- review gate.

Deterministic rules:
- Scene intents derive from decision state and verified offer jobs, not company ID.
- Scene order follows the dominant decision path, with trust/proof before action when risk sensitivity is medium or high.
- Hero topology is chosen from decision tension, media authority, and evidence shape. It is not Family-fixed.
- Core decision composition uses offer count, asymmetry, and comparison burden.
- Trust/proof composition is fact-led when verified facts exist, and transparency/process-led when proof is sparse.
- Media cadence is derived from available Media Roles and scene requirements.
- Generated imagery can supply atmosphere or explanation only.
- Closing choreography derives from verified CTA destinations and remaining decision state.
- Responsive authorship re-evaluates hierarchy, density, and interaction affordance per breakpoint; it is not a desktop shrink.

The same Family must produce different silhouettes when, for example, one fixture has one dominant offer plus strong proof while another has three equal offers and sparse proof.

## 4. Variation and anti-template constraints

Allowed bounded dimensions:
- hero topology: full-bleed, editorial split, text-led field, or anchored media;
- decision topology: guided sequence, comparison rail, intent-first choice, or evidence-led path;
- type voice: direct commercial, human editorial, instructional, or restrained technical;
- density rhythm: sparse-opening/compact-proof, compact-opening/layered-middle, or alternating pause/detail;
- media cadence: hero-led, interstitial, contact-sheet, detail-led, or proof-adjacent;
- trust authority: person, process, factual ledger, review, or transparent unknowns;
- CTA choreography: direct action, guided choice, or one-endpoint merge;
- mobile composition: stacked chapters, preserved split, scroll-led reveal, or interaction-to-detail.

Hard gates:
- no Family maps to one fixed hero, scene order, module list, or CTA pattern;
- at least four variation dimensions must differ for materially different decision/evidence inputs;
- repeated topology across three unrelated fixtures requires a review explanation;
- layout cannot be selected by company slug, reference name, or fixture label;
- no random choice, time-based seed, or arbitrary shuffle;
- a plan fails closed if its rationale has no input references.

## 5. Fit vs Feasibility

Fit is computed and frozen before feasibility.

    fit = f(customer_decision_state, offer_jobs, evidence_shape, media_roles, family_principles)

Feasibility is computed afterward.

    feasibility = f(frozen_fit, available_media, rights, renderer_capabilities, viewport_constraints)

Feasibility may replace a photo with an authored material visual, shorten a scene, or remove an unsupported claim. It must preserve scene intent, decision job, and Family identity. A proposed Family switch is a new fit decision and must stop with HUMAN_REVIEW_REQUIRED.

## 6. Media integration

The future asset pipeline is:

    Family → Scene Intent → Media Role → required content class
    → industry asset library → candidate selection → rights/provenance gate

A candidate is eligible only when role, content class, rights, and evidence boundary match. Public visibility never establishes reuse rights. Every media decision records whether the visual is actual evidence, licensed evidence, generated explanation, or authored atmosphere. Generated or stock visuals must not render as company-specific proof.

## 7. Mandatory human-review conditions

Set HUMAN_REVIEW_REQUIRED for:
- genuine co-dominance between two Families or primary decision jobs;
- insufficient Company Truth to explain audience or available action;
- contradictory evidence affecting headline, offer, price, qualification, or proof;
- unsupported persuasion claim or benefit implication;
- ambiguous CTA destination or unverified contact route;
- imagery reasonably perceived as actual company/staff/customer/venue evidence without disclosure;
- responsive silhouette materially changing decision hierarchy;
- automated anti-template checks passing while screenshot review cannot establish distinct authorship.

Human review cannot be inferred from passing contract tests.

## 8. Rin implementation contract

Implement these structures as pure planning boundaries before renderer integration.

    infer_authored_plan(input):
        validate_required_truth(input.company_truth)
        validate_family_is_frozen(input.family)
        fit = select_composition_fit(input)       # no company lookup
        plan = author_scene_graph(fit, input)
        feasibility = adapt_execution(plan, input) # cannot change plan.family_id
        review = evaluate_review_gates(plan, feasibility, input)
        return plan with feasibility and review

Shared renderer infrastructure may remain shared:
- HTML/CSS emission;
- typography and responsive primitives;
- accessibility and interaction infrastructure;
- screenshot/capture tooling;
- safety and provenance validators;
- browser QA and artifact packaging.

Must be inferred/authored per input:
- scene intents/order;
- hero and decision topology;
- visual authority;
- density rhythm;
- media cadence;
- trust/proof authority;
- CTA choreography;
- breakpoint-specific composition;
- customer-facing copy and claims.

Migration path:
1. Add normalized input adapters and decision-state validation beside existing generation.
2. Introduce AuthoredCompositionPlan and trace output without changing accepted renders.
3. Run shadow planning against Nagi, Regina, and uka; report divergences without routing production through it.
4. Replace company-keyed authored maps with plan outputs for one current-domain fixture at a time.
5. Delete reference/company lookup routing only after regression and human-visible comparisons pass.
6. Keep accepted Phase C snapshots and locks as immutable regression baselines.

Forbidden: identity-to-layout lookup, silent Family switching, random variation, fabricated facts, and weakening visual gates.

## 9. Validation plan — current industries only

Use unseen or synthetic verified-truth fixtures in beauty, cosmetics, hair salon, and Pilates-fitness:

- Fixture A: one primary service, strong process proof, direct booking.
- Fixture B: three equal services, sparse proof, compare-before-contact.
- Fixture C: education-led offer, instructor qualification verified, consultation CTA.
- Fixture D: Pilates trial offer, high risk sensitivity, schedule and price verified.
- Fixture E: synthetic contradiction and missing-evidence cases.

Validation must prove:
- same input gives byte-stable plan and trace;
- different decision/evidence inputs produce materially different variation vectors;
- no plan contains a company ID or reference name as an inference source;
- no three-fixture collapse into one hero/layout/module sequence;
- Nagi, Regina, uka, and accepted Phase C outputs remain regression baselines;
- feasibility gaps do not change Family;
- rights/evidence boundary is preserved.

Automated QA:
- schema and required-field validation;
- deterministic repeatability hash;
- no company-keyed routing;
- fit/feasibility separation;
- variation-vector divergence;
- unsupported-claim and contradiction fail-closed;
- media role, rights, and evidence-boundary checks;
- responsive contract and screenshot manifest checks.

Aoi human-visible QA:
- compare full-page and key scenes across current-domain fixtures;
- verify genuinely different silhouettes and decision hierarchies;
- verify media is explanatory rather than fabricated proof;
- verify mobile retains the intended decision job;
- review every HUMAN_REVIEW_REQUIRED trace and outlier plan.

## 10. Artifacts and trace

Every generated plan must emit:
- normalized input snapshot with source IDs;
- authored plan;
- fit trace;
- feasibility trace;
- variation vector;
- media-role/provenance decisions;
- automated QA report;
- screenshot manifest;
- human-review reasons.

This specification is research-only for Issue #87. No production renderer, asset, Creative Family, industry scope, or accepted Phase C output is changed by this commit.
