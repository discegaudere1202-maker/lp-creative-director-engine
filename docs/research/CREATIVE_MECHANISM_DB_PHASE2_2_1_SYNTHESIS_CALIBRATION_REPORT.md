# Phase 2.2.1 — Synthesis Calibration / Capture Recovery / Coverage Reconciliation

**Status: BLOCKED — NOT READY FOR PM REVIEW**  
**2,600-reference expansion: HOLD (`phase2600_allowed=false`)**  
**Input:** Phase 2.2 HEAD `a7012e961e4869964d819a299f39033dfac3cfab`; Sarah PM review #5892469390.

## Work completed in this recovery pass

- Re-materialized and SHA-256 verified all 11 pinned evidence archives, their ZIP integrity, and all indexed member hashes. No source image was modified.
- Recomputed viewport coverage from the snapshot ledger instead of the denormalized `Reference Master.archive_status` field.
- Isolated the coverage bug: `scripts/assemble_phase2_2_ledgers.py` computes `both_viewports_durable_count` as the count of master rows with a single `archive_status == DURABLE_VERIFIED`. That value is not a per-viewport join. Only the five legacy full-page records have that master flag, so the 20-cell matrix sums to 5 even though the snapshot ledger has 73 references with durable Desktop and Mobile screenshots.
- Built an independently generated 20-cell reconciliation matrix and a 27-reference / 54-attempt failure ledger. The 502 case P01-R05 received one normal browser retry and remained unavailable; this retry was not durably snapshotted. For 403/405/429 the bundle records only a generic HTTP denial, so subtype remains UNKNOWN; no control was bypassed.
- Opened and reviewed pinned Desktop and Mobile scene crops for 13 calibration references: P01-R01, P03-R04, P05-R04, P06-R02, P07-R02, P08-R02, P11-R01, P13-R04, P15-R01, P16-R03, P17-R01, P18-R01, P20-R01. Thirteen reference-specific visual grammar records link back to observed scene IDs, hashes, crop identifiers, archive members, and original URLs. Every record remains `PROVISIONAL_VARIANT`; no canonical promotion is proposed.
- Prepared three machine-readable Scene Spec fixtures for local landscape service, B2B SaaS, and a public information portal. These are calibration fixtures only. They do not claim that the repository's production renderer executed or that compatibility is established.

## Aggregate truth — generated from one source function

| Measure | Reconciled value |
|---|---:|
| Attempted references | 100 |
| Usable references (durable Desktop 1440 + Mobile 390) | 73 |
| Failed references | 27 |
| Desktop durable | 73 |
| Mobile durable | 73 |
| Both viewports durable | 73 |
| Snapshot rows / durable snapshots | 444 / 390 |
| Scene rows | 1,240 |
| OBSERVED / NOT_OBSERVED / NOT_APPLICABLE | 906 / 334 / 0 |
| Durable observed scenes | 906 |
| Claim rows | 59 |
| Existing Phase 2.2 candidate rows | 6 |
| Archive index entries | 1,442 |

Legacy Matrix sum = **5**; snapshot-derived matrix sum = **73**. The Reference Master, old Matrix, QA report, and old PM report were not silently rewritten. They remain discrepant source artifacts until the corrected builder and all report consumers are integrated and rerun. This report does not label the reconciliation gate PASS.

## Capture failure triage

| Root cause | References | Viewport attempts | Policy |
|---|---:|---:|---|
| HTTP 403 Access Denied (subtype unknown) | 16 | 32 | Stop; subtype was not archived; no security bypass or alternate route probing |
| HTTP 405 Method Not Allowed (response body not archived) | 1 | 2 | Stop; body not retained, so do not infer a challenge |
| HTTP 429 (rate-limit vs access denial unverified) | 1 | 2 | Only one delayed normal retry if the visible response is not a challenge; otherwise stop |
| HTTP 404 | 1 | 2 | Check official canonical/redirect once, then replace if absent |
| HTTP 502 | 1 | 2 | One bounded ordinary retry; retry remained 502 in Cloud Browser |
| Navigation timeout | 1 | 2 | One bounded fresh-context retry, then replace if still unavailable |
| HTTP/2 protocol error | 5 | 10 | One normal browser retry only; do not change fingerprint/network path |
| HTTP 200 but no visible body | 1 | 2 | One normal wait + scroll retry |

**Replacement status: NOT STARTED.** No same-cell replacement is counted until its official page has been captured at both required viewports, traversed, archived to a retrievable pinned object, and its hashes verified. Therefore the required 100-usable-reference condition is **not met**. Attempted=100, usable=73, failed=27 is the truthful state; failure records are retained.

## Atomic visual mechanism calibration

Thirteen atomic candidates were written from observed crop review. They describe scene job, composition, hierarchy, typography relationships, media role, spacing, desktop-to-mobile re-composition, implementation boundary, feasibility, and misuse constraints. Static captures do not establish motion or interaction; those fields remain `NOT_OBSERVED`. Every mechanism is a single-reference provisional variant. Candidate names are not evidence of generalization.

No compatibility edge is promoted from simple co-occurrence. A retrieval/recipe fixture that needs an unknown edge returns HOLD. No CVR or sales outcome is inferred.

## Renderability

Three Scene Spec fixtures demonstrate the target handoff fields: content slots, composition, asset requirements, responsive rules, DOM/asset boundary, and prohibitions. One case has only a single mechanism and therefore demonstrates a scoped spec, not a validated combination recipe. Cross-mechanism compatibility is still unknown, and the repository production pipeline was not executed. **Downstream Renderability gate: NOT PASSED.**

## Remaining blockers / next action

1. Re-run same-cell recovery for non-security transient failures under a hard one-retry limit; preserve all failures.
2. Collect and verify replacements in their original `(archetype, industry, market, discovery source)` cells until there are 100 usable references. Durable archive writing must use an actual retrievable pinned store; no placeholder URI or Actions artifact as sole source.
3. Integrate the snapshot-derived aggregator into the production builder and regenerate Master, Matrix, QA and PM summaries from the same aggregate object; validator must compare all copies and fail closed on any mismatch.
4. Test candidate compatibility with evidence-backed composition constraints, then run the actual Creative Profile → Retrieval → Recipe → Scene Spec production path for multiple industries and profiles. Unknown compatibility must block a recipe.
5. Only after those gates pass, request Sarah PM review. Keep `phase2600_allowed=false` until PM decision.

## QA result

- Archive provenance and hashes: **PASS for the 11 recovered input archives**.
- Snapshot-derived count calculation: **PASS (73)**.
- Corrected matrix sum: **PASS (73 across 20 cells)**.
- Old matrix/report agreement: **FAIL (old matrix sum 5; old report says 73)**.
- Failure classification: **PASS (27 refs / 54 attempts classified)**.
- 100 usable references: **FAIL (73/100)**.
- Atomic candidate evidence links: **PASS for 13 provisional variants**.
- Generalized/canonical promotion: **NONE**.
- Compatibility proof: **FAIL / UNKNOWN**.
- Production renderability: **NOT RUN**.
- 2,600 gate: **PASS, remains false**.

This status is intentionally not `PHASE_2_2_1_SYNTHESIS_CALIBRATION_READY_FOR_PM_REVIEW`.
