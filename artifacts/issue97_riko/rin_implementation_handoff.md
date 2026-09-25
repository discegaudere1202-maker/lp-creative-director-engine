# Issue #97 — Rin Implementation Handoff

## Goal
Move the accepted controlled CompositionPlan render architecture into the normal current-industry Production path without reintroducing template routing.

Current industries only:
- beauty/cosmetics;
- hair salon/barber;
- Pilates/fitness.

Do not expand industries in this implementation.

## Architectural order

`Verified Company Truth → Customer Decision State → Creative Fit → Family ambiguity gate → Family frozen → compatible grammar → CompositionPlan → Production Feasibility → copy/media/motion/responsive realization → renderer → QA → screenshot artifact → Aoi`

Every implementation change should make this order easier to prove from trace output.

## Repository surfaces

### Promote
`src/lp_engine/authored_composition_contract.py`
- keep normalized semantic input deterministic;
- extend only where the Issue #97 Production input contract requires missing truth/action/evidence fields;
- preserve no-identity inference.

`src/lp_engine/authored_composition_runtime.py`
- replace shadow-only restriction with an explicit guarded Production mode;
- Production mode requires a complete plan, frozen Family, accepted grammar, nine widths, no identity routing, and no unresolved blocking review state;
- retain shadow mode for comparison/regression.

### Rewire
`src/lp_engine/production_generation.py::run_generation`
- CompositionPlan-derived renderer directives become authoritative for page composition;
- existing evidence safety, provenance, text quality, photography, and browser infrastructure may remain shared;
- no helper may override plan topology after consumption.

### Demote / isolate
`src/lp_engine/controlled_production.py`
- Nagi/reference builders become regression/test adapters only;
- do not use reference identity to enter a unique Production route.

### Deprecate then delete/isolate
`_industry_visual_direction()`
- category can remain factual/asset-pool context;
- category must not choose final Family/profile/topology.

`_layout_profile()`
- must not choose final authored form independently of CompositionPlan.

## Required implementation units

1. `derive_current_industry_authorship_input(raw, evidence)`
   - returns normalized Company Truth, decision state, evidence, media roles, action state;
   - carries source ids/confidence;
   - fails closed on minimum truth/decision ambiguity.

2. `plan_current_industry_production(normalized_input)`
   - invokes generic planner;
   - confirms Family frozen;
   - emits deterministic CompositionPlan + trace.

3. `consume_composition_plan(plan, mode="production")`
   - validates complete Production directives;
   - never selects Family/profile/topology from identity;
   - emits renderer directives or explicit block state.

4. Production renderer integration
   - scene order, Hero/core/trust/closing topology, media-role requirements, responsive authorship, and CTA choreography originate from directives;
   - renderer owns realization, not creative re-inference.

5. copy integration
   - create public copy from scene intent + decision job + verified truth/evidence;
   - every factual persuasive claim is traceable to eligible evidence;
   - preserve semantic Japanese line chunks;
   - 320px orphan/particle/one-character tails fail hard.

6. asset-library boundary
   - use current industry/category only to scope asset candidates;
   - select by Scene/Media Role/content class/rights;
   - asset availability cannot change Family;
   - official/public media requires explicit reuse rights.

7. motion/responsive
   - motion role derives from scene intent/decision need;
   - implement all nine widths;
   - preserve decision hierarchy, not exact desktop geometry.

## Fail-closed behavior
Return explicit non-render or non-production state for:
- `INPUT_TRUTH_INSUFFICIENT`;
- `INPUT_CONTRADICTION_BLOCKED`;
- `DECISION_STATE_AMBIGUOUS`;
- `FAMILY_NOT_FROZEN`;
- `IDENTITY_ROUTING_DETECTED`;
- `PLAN_INCOMPLETE`;
- `UNSUPPORTED_GRAMMAR`;
- `FEASIBILITY_FAMILY_MUTATION`;
- `CLAIM_EVIDENCE_BLOCKED`;
- `MEDIA_RIGHTS_BLOCKED`;
- `RENDER_CAPABILITY_BLOCKED`;
- `RESPONSIVE_HARD_GATE_FAILED`;
- `TEMPLATE_COLLISION_REVIEW`;
- `HUMAN_REVIEW_REQUIRED`.

Never catch these and continue through a legacy profile.

## Required tests

Static:
- scan Production composition path for company/reference/fixture routing;
- detect category→final profile and Family→single layout maps;
- detect legacy fallback after CompositionPlan error.

Behavioral:
- same normalized semantic input + changed company id/name/reference id => equivalent CompositionPlan semantics;
- changed decision job/evidence shape => plan changes where expected;
- category mutation with authored inputs fixed => topology unchanged;
- feasibility change => Family unchanged;
- unsupported grammar / missing truth / contradiction => fail closed;
- Production render proves it consumed plan directives;
- same-Family pair produces human-visible structural divergence;
- cross-Family near-collision remains reviewable rather than forced apart.

Regression:
- keep accepted controlled cases and Issue #96 320px correction;
- 320/360/375/390/430/768/1024/1280/1440 browser, overflow, line, CTA, crop, interaction QA;
- package screenshot manifests for Aoi.

## Completion fixture matrix
Use `artifacts/issue97_riko/current_industry_completion_fixture_matrix.json` as the minimum architectural-completion set. Do not substitute one golden fixture per industry; decision/evidence variants are required.

## Human review boundary
CI can establish deterministic routing, safety, provenance, responsive mechanics, and expected fail-closed behavior. It cannot establish human-visible authorship or Template Resemblance PASS.

After technical/evidence audit, Aoi must inspect actual screenshots. Real-image Sales Sample QA remains a later gate.

## Definition of implementation complete
- Production no longer needs company/reference/category/Family→fixed-profile routing;
- CompositionPlan is demonstrably authoritative;
- current-industry matrix passes expected automated outcomes;
- controlled-render PASS remains green as regression;
- all nine widths pass;
- Aoi can review packaged actual screenshots;
- deprecated runtime surfaces are removed or explicitly isolated as regression-only;
- no industry expansion is introduced.