# Issue #87｜Rin Implementation Handoff

## Goal
Implement a generic authored Composition Planner. The renderer must consume an auditable `CompositionPlan`; company/reference/category/Family identity must not directly select a layout/profile/scene sequence.

## Pipeline
`Company Truth → Customer Decision State → Creative Fit → Family inference/ambiguity → Family frozen → compatible grammar → decision signature → rule primitives → CompositionPlan → post-freeze Feasibility adaptation → responsive authored transforms → render → QA/human review`

## Concrete migration targets
- `src/lp_engine/controlled_production.py`: keep Nagi/reference adapters only as regression fixtures/evidence. They must not be the runtime architecture router.
- `src/lp_engine/production_generation.py::_industry_visual_direction`: service-category keywords may remain factual context but must not choose the final visual/layout profile.
- `src/lp_engine/production_generation.py::_layout_profile`: final form selection moves behind `CompositionPlan`; no Family/category/company → fixed renderer profile.

## New runtime contracts
Use:
- `authoring_input_contract_v1.json`
- `composition_plan_contract_v1.json`
- `rule_primitive_registry_v1.json`

Every selected module grammar and primitive needs an audit reason. Ambiguity or unsupported grammar fails closed. There is no silent legacy/generic fallback.

## Variation proof
A same-Family pair must be allowed—and expected—to differ in hero silhouette, public heading progression, topology, proof distribution, media role/framing, density rhythm, CTA choreography and responsive transformation when company truth/decision structure differs.

Differences limited to tokens, photos, logo, nouns or relabeled copies of the same scene sequence are a failure.

## Migration
1. Shadow-generate plans beside legacy output.
2. Validate accepted references through planner with identity routing disabled.
3. Make `CompositionPlan` the primary production composition input.
4. Delete/deactivate runtime identity/category composition shortcuts and add static + behavioral guards.
5. Keep Nagi / Regina / uka / accepted Phase C outputs only as regression fixtures.

## Required QA
- Schema and fail-closed tests.
- Identity mutation invariance.
- Decision-state mutation sensitivity.
- Same-Family variation test.
- No Family→fixed layout/profile.
- No service keyword→final layout/profile.
- Feasibility invariance.
- Verify generation/render truly consumes the plan.
- Nagi / Regina / uka + Phase C regressions.
- 320/360/375/390/430/768/1024/1280/1440 browser, line and overflow QA.
- 320px Japanese optical line gate.

## Human boundary
CI may verify contracts and regressions. It may not self-declare company-specific authorship, Template Resemblance PASS, ¥1M value, or final creative approval. Sarah technical/evidence audit must be followed by Aoi screenshot-level human-visible review where routed.
