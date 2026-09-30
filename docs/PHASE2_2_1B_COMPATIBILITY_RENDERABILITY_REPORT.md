# Phase 2.2.1B — Compatibility Calibration and Multi-profile Renderability

## Result

`PHASE_2_2_1_COMPATIBILITY_RENDERABILITY_READY_FOR_PM_REVIEW`

This is a scoped implementation/calibration checkpoint, pending Sarah PM review.
The 100-reference durable corpus is unchanged. `phase2600_allowed=false`.

- Approved source commit: `cafbab3678c6ade4be9fdf4649df6280f5bf077d`.
- Sarah PM approval: Issue #143, comment #5907666653.
- Branch: `phase2-2-1b/compatibility-renderability-20260930`.
- Final commit: the immutable commit linked in the Issue #143 completion comment.

| Metric | Final result |
|---|---:|
| Atomic mechanisms | 13, all PROVISIONAL_VARIANT / CANDIDATE |
| Compatibility edges | 83 |
| COMPATIBLE | 0 |
| CONDITIONAL | 5 |
| INCOMPATIBLE | 2 |
| UNKNOWN | 76 |
| Materially distinct profiles | 5 |
| Scene Specs | 10 |
| Actual production-code rendering, unique final profiles | 5 |
| Final desktop 1440px | 5 PASS / 0 FAIL |
| Final mobile 390px | 5 PASS / 0 FAIL |
| Additional widths | 320 / 360 / 375 / 430 / 768 / 1024 / 1280, all five profiles PASS |
| Final browser page executions | 45: 10 required viewport executions + 35 breakpoint executions |
| Retained failure/rejection evidence | 17 |
| Mechanism promotion | 0 |
| Evidence trace QA / independent validator | PASS / PASS |
| Tests | 18 fail-closed + 6 existing production-generation regression = 24 PASS |
| Selected-fixture implementation blockers | None |
| Expansion permission | false |

## Evidence and compatibility scope

The 16 pinned source archive containers were byte-hash checked, and all 26 source
Scene members attached to the 13 existing atomic records were individually checked.
`source_audit.json` records the pinned file/version/member/digests. All recovered
corpus output hashes are independently rechecked by the new validator.

The 78 unordered pairs have a SAME_SCENE ledger entry. Two complete-grammar
contradictions are explicitly INCOMPATIBLE: environmental overlay vs cinematic
proposition-after-media; equal campaign diptych vs narrow-index/large-feature
container. These verdicts apply to simultaneous ownership of the **same container**.
They do not imply that these mechanisms cannot exist in separate LP sections.
The other 76 entries remain UNKNOWN. Separate source observations and same-LP
co-occurrence are not positive combination evidence.

Five **additional ADJACENT_SCENES** entries carry actual execution evidence. Their
CONDITIONAL verdict is limited to the exact registered profile/Truth/asset digest,
two separate semantic containers, truthful routes, semantic DOM typography, static
motion and independently tested mobile recomposition. Changes to those conditions
are rejected. Other profiles and same-scene blends remain unproven.

| Profile | Tested adjacent combination | Buyer job and resulting structure |
|---|---|---|
| Local Trust Service | Environmental hero + public utility grid | Understand the consultation entry, then inspect process information |
| B2B Technical / SaaS | Product UI stage + audience split | Inspect the running owned app, then choose a role-specific guide |
| D2C / Product | Campaign diptych + brand/index feature | Compare two categories, then navigate a featured product category |
| Premium / Place | Cinematic destination entry + public utility grid | Inspect atmosphere, then locate visit information |
| Public / Information-heavy | Public utility grid + audience split | Search procedural information, then choose the initial/returning route |

Source references are separately identified; agency, campaign and source-family
independence remain UNKNOWN. A successfully tested combination is not independent
reference confirmation and cannot promote a mechanism to SUPPORTED or CANONICAL.
Seven grammar adapters were implemented. The six unimplemented provisional
mechanisms reject with `IMPLEMENTATION_BLOCKER_UNIMPLEMENTED_GRAMMAR` if requested.

## Actual repository rendering path

The opt-in connection is inside `lp_engine.production_generation.run_generation`
and its public `render_html` entry point:

`Company Truth → Buyer Problem / State → Sales Story → Creative Profile → Scene Job
→ Mechanism Retrieval → scoped Compatibility Solver → Recipe → Scene Spec
→ production renderer HTML/DOM → asset binding → Chromium execution`.

All ordinary generation stages run; no generation or browser component is mocked.
The `mechanism_scene_plan` is persisted inside the actual production `render_spec`
and consumed by `render_html`, rather than being an external calibration-only JSON.
The renderer also independently rejects edited/untraced Scene Specs.

**The company facts in this cohort are authored, fictional validation fixtures.**
They run with `mode=test` through actual production code and remain
`NOT_PRODUCTION_APPROVED`. No fabricated VERIFIED client facts are placed in the
ordinary evidence ledger. Generated repository imagery is explicitly illustrative;
it never becomes actual construction, property, client, product or efficacy proof.
The SaaS panel is a separately implemented owned test app: table filtering was
actually executed and recorded, rather than implying a static image was interactive.
All CTA destinations are real local fixture destinations and submit nothing.

The mechanism route is opt-in; existing customer generation remains on its existing
renderer path. Real customer use requires client-specific authority/asset rights,
current UI, business claims, appropriate scope and further evidence. This checkpoint
does not certify finished sales LP quality or conversion lift.

## Derivation without reference screenshots

Each Scene Spec stores the source mechanism, source and target Scene Job, reference
and Scene Evidence IDs, saved composition/hierarchy/type/media/rhythm/responsive/
implementation/misuse fields, their digest, conditions, recipe and Truth trace.
Generation reads these DB fields, not source archive pixels. The test that makes
all source image/archive reads inaccessible regenerates all ten exact Scene Specs.
Illustrative fixture assets are separately bound and hash-checked.

The final screenshot audit reviewed structural hierarchy, boundaries, crop subject,
grid-to-stack transformation and honest asset labeling. Ground-truth asset review
identified and corrected an initial human-treatment image that did not fit the
Premium PLACE job. Source screenshots are not a generation crutch.

## QA and retained failures

Per profile/viewport, browser records include DOM validity, actual HTTP asset/font
resolution, overflow, clipping, layout, responsive recomposition, crop settings,
type hierarchy and authored meaning-unit bounds, section boundaries, animation
absence, reduced-motion preference and identical pixels, implementation feasibility,
evidence safety, keyboard focus and the available search/product interactions.
Every final HTML, Scene Spec and screenshot is SHA-256 addressed. The independent
validator rejects missing/changed pixels, changed HTML/specs and intermediate-width
failures as well as required-viewport failures.

17 failure/rejection records are retained in `failure_evidence.jsonl`:

- 10 initial Reduced Motion comparison probe failures caused by unequal keyboard
  focus state. The focus ring caused pixel differences; this is a measurement setup
  failure, not a finding of unsafe static motion. Corrected comparisons match.
- 2 actual D2C responsive failures at 768/1024px: a shared CSS class applied the tile
  grid to the outer scene too. The scene class was isolated and all widths retested.
- 1 media-role audit mismatch, corrected with a reviewed environment illustration.
- 4 actual solver rejections: unknown scope, incompatible pair, unmet condition and
  unimplemented grammar. Rejected recipes never reach browser rendering.

Prior records, Scene Specs, HTML and screenshots are preserved under
`artifacts/phase2_2_1b_attempt1`; the final outputs are under `artifacts/phase2_2_1b`.
`output_hashes.json` covers both final and retained attempts. This includes failures;
only the final five fixtures contribute to the final PASS counts.

## Verification and reproduction

Executed checks:

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_phase2_2_1b.py' -v
PYTHONPATH=src python -m unittest discover -s tests -p 'test_production_generation.py' -v
PYTHONPATH=src python scripts/validate_phase2_2_1b.py
git diff --check
```

The unit tests prove unsupported/UNKNOWN edge rejection, incompatible set rejection,
all six conditional requirements, exact-profile digest scope, trace/regeneration,
actual production/browser nonexecution rejection, one-profile gate failure,
mobile and intermediate-width failure propagation, screenshot/asset loss rejection,
untraced renderer input rejection and evidence-insufficient promotion rejection.
Fixtures cannot be customer-production approved.

The committed inputs and records allow independent validation without a live source
LP. A new browser run requires Node Playwright, Chromium and a local HTTP server
serving the repository root on port 8765. `P221B_PLAYWRIGHT_MODULE` and
`P221B_CHROMIUM` optionally select installed binaries; the JP font is already in
the repository. Browser collection is `scripts/render_phase2_2_1b.cjs --accepted`.
Creating a new experiment batch requires a fresh output checkpoint; do not overwrite
immutable failure evidence or reuse an earlier PASS without new execution.

## Remaining limits and stop

No unresolved blocker remains for the selected five registered fixtures. Six other
mechanisms have no adapter; untested scopes/profiles remain UNKNOWN and fail closed.
Motion source evidence is absent, so no source motion was inferred: this batch tests
the static/reduced-motion equivalent only. Client-specific factual/rights clearance
and source-family independence are outside these authored fixtures.

No 2,600-reference expansion was started. `phase2600_allowed=false`.

STOP: `PHASE_2_2_1_COMPATIBILITY_RENDERABILITY_READY_FOR_PM_REVIEW`.
