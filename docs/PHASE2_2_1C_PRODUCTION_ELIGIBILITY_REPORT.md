# Phase 2.2.1C — Production Eligibility Boundary, Adapter Coverage, Independence

Source: `17268b741ada3d2db7565806e7f86327eec1c3b9`.
Authorization: Issue #143, Sarah PM comment #5910542210.
Branch: `phase2-2-1c/production-eligibility-20260930`.
Final Commit: immutable commit linked by the final Issue #143 handoff.

## Result and scope

`PHASE_2_2_1_PRODUCTION_ELIGIBILITY_READY_FOR_PM_REVIEW`.
This is a fail-closed eligibility/calibration checkpoint awaiting PM acceptance.
No customer deliverable is approved and `phase2600_allowed=false`.

| Metric | Result |
|---|---:|
| Atomic mechanisms | 13, all PROVISIONAL_VARIANT / CANDIDATE |
| Implemented adapters | 10 (7 retained + 3 newly implemented static adapters) |
| Adapter HOLD | 3 |
| ELIGIBLE / CONDITIONAL / HOLD / INELIGIBLE for live production | 0 / 0 / 13 / 0 |
| VERIFIED_INDEPENDENT / PARTIALLY_INDEPENDENT / NOT_INDEPENDENT / UNKNOWN | 0 / 0 / 13 / 0 |
| Agency / campaign independence UNKNOWN | 13 / 13 |
| Required materially different profiles | 5 |
| Additional individual-adapter profiles | 3 |
| Desktop 1440 / mobile 390 | 8 / 8 PASS; 0 failures |
| Additional widths | 320, 360, 375, 430, 768, 1024, 1280: all 8 PASS |
| Actual browser page executions | 72 |
| Scene Specs | 13 (10 existing cohort scenes + 3 individual adapters) |
| Deliberate negative experiments | 21 PASS / 0 FAIL |
| Unit/regression tests | 50 PASS / 0 FAIL (26 C + 18 B + 6 production) |
| Failure evidence | 17 B + 23 C = 40 retained |
| Automatic promotions / customer-approved outputs | 0 / 0 |

The **13 live HOLDs are deliberate decisions**, not a request to fill counts.
Each mechanism has only one independent reference/page unit. Fixture permission
is a separate, exact, authored test authorization and never changes its live
`production_eligibility` or evidence maturity. No caller-provided boolean can turn
a fixture into an independent reference, client evidence or a live approval.

## Eligibility contract

`data/phase2_2_1c/eligibility_contracts.json` defines every requested contract field
for all 13 mechanisms: adapter identity/version, independence, compatibility,
desktop/mobile/static/reduced motion, asset, truth, rights, accessibility,
implementation, known failure modes, supported/unsupported jobs, eligibility,
reasons and reference/scene trace. The contract is re-derived from the pinned
source grammar on admission; contract or independence-ledger edits fail closed.

`supported_scene_jobs` is an allowlist. The PRODUCT_DISCOVERY use of the existing
brand-index adapter is the previously accepted exact Phase B fixture translation,
not evidence that every product-discovery composition is supported. Other jobs,
changed content/truth/assets and other combinations remain untested and denied.

Current adapter decisions:

| Newly evaluated mechanism | Decision | Evidence-backed boundary |
|---|---|---|
| Clinical human hero | IMPLEMENTED: clinical_human_static v1.0.0 | Darkened human-image canvas, left proposition, three real fixture routes, stacked mobile routing. No medical outcome or live appointment claim. |
| Renovation portal hero | IMPLEMENTED: renovation_portal_static v1.0.0 | Photo-led entry, two distinct task links and separate participant rail. Fictional textual participant labels cannot establish actual membership/partner proof. |
| Finance rate panel | IMPLEMENTED: finance_rate_static v1.0.0 | Semantic numeric cards, immediately adjacent disclosure and routes; cards stack on mobile. Values are explicitly fictional layout-test values, not rates/offers/returns. |
| Editorial product carousel | HOLD | Operation, pagination state and keyboard behavior were never observed/tested. A static panel substitute would not implement the complete mechanism. |
| Industrial product carousel | HOLD | Unobserved carousel/control behavior cannot be invented or borrowed from another adapter. |
| Culture fullbleed work entry | HOLD | Recorded Scene Job is UNCLASSIFIED. The production job cannot be guessed from atmosphere. |

The three new adapters have separate semantic DOM and composition code. No source
pixel template, reference styling tokens or similar-adapter substitution is used.
The seven prior adapters remain unchanged; the legacy Phase B test-only route is
preserved for exact reproduction and cannot bypass the new live-production gate.

## Independence calibration

`independence.json` records reference ID, brand, agency/production source,
campaign, domain/page family, scene IDs and independent evidence unit for every
mechanism. Both viewport scenes collapse into one `REFERENCE-PAGE` unit.

`NOT_INDEPENDENT` here means **the two submitted scene observations are not two
independent sources**. It does not mean every external site has the same agency.
Agency/campaign/parent-brand relationships remain UNKNOWN. Separate brands,
gallery listings, screenshots, domains or successful authored fixtures never
manufacture an independent confirmation of the same mechanism.

`source_attribution_audit.json` records a bounded primary-homepage check of the
13 existing references on 2026-09-30. No attributable production/campaign credit
was established for the captured grammar. Search absence is not evidence of
in-house production. teamLab returned only one extracted line. Current live
pages were not assumed to match the pinned historical design/campaign; none was
added as a second reference or used to change the source grammar.

## Actual production path and hard gates

`production_generation.run_generation` consumes `mechanism_eligibility_context`:

Company Truth → Buyer State → Sales Story → Creative Profile → Mechanism Retrieval
→ Eligibility Gate → Compatibility Solver → Combination Recipe → Scene Spec
→ `render_html` → eligibility-validating renderer → browser execution.

Every generated manifest/spec saves the exact profile/input/authorization/contract
digests, per-mechanism decisions and stage trace. Admission happens before output
creation and before the pair solver. The public renderer regenerates and compares
the complete eligibility envelope before rendering; changing a permit or plan is
rejected. Ordinary non-mechanism customer generation retains its existing path.

Hard denials include no adapter, insufficient live independence, unsupported job,
missing truth, missing asset/purpose rights, UNKNOWN motion or invented animation,
missing reduced-motion requirement, mobile/desktop support loss, missing
accessibility/implementation conditions, missing evidence trace, changed authored
input/profile and generated imagery offered as proof. The existing pair solver
still rejects incompatible sets, required UNKNOWN pairs and unmet CONDITIONAL
conditions. Its five conditional edges remain exact Phase B digest-scoped
ADJACENT_SCENES edges; no compatibility verdict was promoted/generalized.

All thirteen contracts are STATIC_ONLY with explicit STATIC_EQUIVALENT_ONLY
reduced-motion requirements. No source motion, hover, carousel or video behavior
was inferred. Authored search/UI filtering already owned and tested in Phase B
remains separate from reference-motion evidence.

The input authorizations apply only to registered, fictional company truths in
`mode=test`. The existing generated repository imagery is VISUAL_CONTEXT only,
never actual person/place/product/achievement, before-after, testimonial or client
proof. Real use would require claim-unit primary evidence, current actual UI,
client authority, subject consent and purpose-specific rights, plus independent
mechanism support and fresh output QA. This checkpoint enables no live client.

## Revalidation and failures

All five required Phase B profiles and three new single-adapter fixtures were
freshly generated and executed in Chromium at nine widths each. QA includes
loaded assets/fonts, actual HTTP/page errors, semantic DOM/routes, section bounds,
overflow/clipping, mobile recomposition, meaning-unit wrapping, conservative text
contrast, image labels, keyboard focus, existing owned UI/search interactions and
pixel-identical reduced-motion rendering. These are bounded implementation checks,
not a blanket WCAG, sales-quality, medical/financial-content or conversion claim.

Screenshot inspection confirmed the added human, place/participant and numeric
panel roles; mobile routing remains visible and disclosures remain with offers.
Independent validation binds each PNG, HTML and Scene Spec by SHA-256, checks all
breakpoints, regenerates eligibility traces and verifies Phase B preservation.

The 17 prior failure records and every committed prior output remain byte-identical.
`failure_evidence.jsonl` adds 21 actually executed deliberate denials and two real
development failures: an initial loopback server connection refusal, and one
existing test's exception-message compatibility assertion. The latter still
rejected live output; its historical identifier was restored alongside the new
diagnostic. All 50 scoped tests subsequently passed. These failures were retained.
No new responsive failure occurred; no rejection or failed attempt was counted
as successful browser execution or independent evidence.

Reproduce:

```bash
PYTHONPATH=src python scripts/test_phase2_2_1c.py
PYTHONPATH=src python scripts/validate_phase2_2_1c.py
PYTHONPATH=src python scripts/validate_phase2_2_1b.py
```

The committed output/hash records are sufficient for independent offline review.
Fresh browser collection requires Playwright, Chromium and the bundled loopback
runner. Do not overwrite immutable accepted/failure checkpoints; collect a new
attempt under a fresh output directory, not over the accepted records.

No unresolved blocker remains for this boundary/calibration checkpoint. The
13 live HOLDs, three adapter HOLDs, unverified relationships and client evidence
requirements remain explicit restrictions. Promotion remains 0. The next phase
requires a separate PM decision. **2,600 expansion has not started.**

STOP: `PHASE_2_2_1_PRODUCTION_ELIGIBILITY_READY_FOR_PM_REVIEW`.
