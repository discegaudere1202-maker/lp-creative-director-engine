# Phase 2.2.1D — Snapshot-bound Independence Assertion Fix

Correction baseline: `4ae3f53be9cc48f13b22145f1e0a54e68b367c79`.
SSOT: GitHub Issue #143; Sarah PM audit/correction Comment #5918142494.
Branch: `phase2-2-1d/snapshot-binding-fix-20261001`.
The published D handoff remains PASS. Phase D overall technical/semantic acceptance remains HOLD pending Sarah review. This is a bounded fix, not a new research phase.

## Corrected behavior

Same-mechanism candidates correctly retain the SAME `source_contract_sha256 = legacy.digest(mechanism)`. That digest is used by atomic matching. Family independence now uses a separate `REFERENCE_EVIDENCE_SNAPSHOT_V1` digest re-derived from canonical source records. Caller-supplied snapshot digests and the old `snapshot_binding=VERIFIED` flag cannot establish the binding.

A changed valid PC/Mobile scene selection or a changed correctly registered image hash invalidates the old attribution claim even when `trace_valid=True` and `match_decision=MATCH`. Missing mobile evidence, stale pixel readback, swapped unit subjects, changed capture metadata, parent snapshot identity or archive locator, and stale/missing citation records cannot establish VERIFIED_INDEPENDENT. A correctly reviewed same-mechanism pair with distinct references still can establish pair provenance; this does not unlock production.

## Snapshot binding schema

Implementation: `src/lp_engine/evidence_snapshot_binding.py`.
Machine-readable field/policy inventory: `data/phase2_2_1d_snapshot_binding_fix/snapshot_binding_schema.json`.

- Canonical unit source ID: existing `unit_id` or `candidate_id`. The caller's unit/reference/page IDs and selected PC/Mobile scene arrays must equal that registered source record.
- Canonical page identity: active `reference_master.csv` record and its actual canonical URL/page family.
- Both viewports: each selected OBSERVED scene, exact image SHA-256, archive member/locator/container/pinned identity, and the explicitly linked registered parent snapshot. Historic records without a snapshot ID use their existing unambiguous parent screenshot/hash tuple; no ID/date is invented.
- Capture metadata is copied only where present, using the exact allowlist in the schema/module: actual URLs, capture/derivation times, viewport/crop coordinates, run IDs, manifests, capture-log locators/hashes, source artifacts and archive version metadata.
- Digest: the existing `legacy.digest()` canonical JSON SHA-256 algorithm. `source_contract_sha256` is not part of the snapshot payload. The typed payload contains schema, source-record ID, unit identity, reference identity and ordered DESKTOP/MOBILE scene plus parent-snapshot/archive records.

Each family claim uses `SNAPSHOT_BOUND_FAMILY_ASSERTION_V1`, an assertion ID, family, status/basis, explicit reviewer metadata and **unit ID → snapshot SHA-256 mapping**. Its citation digests must match canonical `attribution_evidence.json` records for that family and the SAME unit-to-snapshot mapping, with a primary-source URL and recorded observation. An anonymous sorted list of common mechanism digests is insufficient.

## Invalidation and migration

Legacy `snapshot_contract_digests` assertions do not automatically migrate, even if their old VERIFIED flag is present. Stale/missing/wrongly mapped capture subjects or source citations make that family UNKNOWN. A partially verified pair retains UNKNOWN dimensions and stays ineligible; duplicate pages/reference units and known shared brand/campaign/agency/production/source/template families retain NOT_INDEPENDENT denials.

A future explicit reviewer must inspect the current canonical subject and the source citation, then record a new reviewed claim for those exact digests. A digest does not prove semantic attribution. The fix verification command generates only the versioned derived ledger and binding index; it never stamps or rewrites assertions/citations. In the real correction records both new assertion/citation registries remain `[]`.

## Ledger and production integration

`independence_calibration.derive()` uses canonical evidence sources for pair evaluation and includes re-derived snapshot bindings. `ledger()` compares against the separately stored `data/phase2_2_1d_snapshot_binding_fix/calibration.json`; historical `data/phase2_2_1d/calibration.json` is unchanged. The existing production gate call is unchanged and now consumes this versioned ledger.

The final validator strips only the two newly added binding fields and compares every remaining new row to the historical D ledger. All original candidate decisions, adapter states, HOLD reasons and eligibility outcomes match. There are 39 canonical source-record bindings (13 baseline + 26 existing candidate records) and 380 selected scene links. These counts are source-binding coverage, not new independent units or additional research candidates.

Synthetic integration tests exercise the actual derive → ledger comparison → live admission → `run_generation(..., mode='production')` path, with canonical record fixtures injected only in memory. No pair/ledger/gate PASS result is stubbed. A valid positive provenance pair still hits the existing D HOLD gate; a stale capture assertion stays UNKNOWN even after the ledger is regenerated. Both paths stop before output-directory creation. Real live gate checks reject all 13 mechanisms; the retained D regression checks also reject all five real production routes.

## Actual local execution

| Group | Final execution |
|---|---:|
| New Snapshot Binding regression methods | 38 PASS |
| Adapted D regression methods | 16 PASS |
| C regression methods | 26 PASS |
| B regression methods | 18 PASS |
| Production generation regression methods | 6 PASS |
| Total final run | 104 PASS / 0 FAIL / 0 skipped |
| Separate replay of immutable historical negatives | 18 PASS / 0 FAIL |
| New fix Validator | PASS |
| Canonical binding/preservation QA | PASS |

The final test source hashes and all 104 method outcomes are in `tests_report.json`. Development history records two executions of the 104-method suite, each 104 PASS / 0 FAIL / 0 skipped (208 method executions total). The historical 18 negative specimens were separately replayed in both cycles (36 replay executions total); their final replay report is 18/18. The first run preceded minor review/input guards and better outcome recording; the second validates the final source bytes. These engineering execution counts are not added to the 28 research candidates or historical Failure Evidence 108.

The exact old module was loaded from the reviewed Git object and the two PM mutations were freshly reproduced using declared synthetic records: old trace/match remained valid and old pair returned VERIFIED_INDEPENDENT. `pm_reproduction.json` accurately marks those OLD safety assertions FAIL. The new regression tests assert UNKNOWN for both cases and PASS. Synthetic timestamps/URLs/hashes are explicitly test declarations; no real capture/attribution was created.

The old synthetic positive used distinct a/b contract digests, which cannot represent two references for the same mechanism. Its positive premise is corrected in the test module with the shared-contract canonical-source fixture. Three old partial-negative fixtures lose their only purported legacy binding and now yield UNKNOWN instead of PARTIALLY_INDEPENDENT; their immutable saved specimens/reports are preserved and the new expected statuses are recorded separately in `legacy_negative_replay.json`.

## Historical evidence and scope

The original 66-test report, original Validator report, all old failure records, manifests, research observations and capture bytes are unchanged. Historical evidence preservation verifies 472 A/B/C/D and atomic-evidence files against their original reviewed Git blob IDs and records a SHA-256 index digest. Every other base-commit file is unchanged except the intended independence module and its adapted test module. `production_eligibility.py` retains exactly the already-published D 3-line call; B/C code and manifests are not rewritten.

The prior 16-container/1,414-member corpus readback remains saved evidence. Original corpus archives were not freshly reread. No new discovery, acquisition, screenshot capture, adapter, compatibility extension, semantic candidate judgement or browser render QA was performed. Temporary HTML generation inside retained unit regressions is not new Desktop/Mobile screenshot QA. Fresh D Desktop/Mobile render is N/A because eligibility changed for zero mechanisms. No GitHub Actions run was manually started; these fix tests/validator were LOCAL.

Research remains 13 atomic mechanisms; adapters 10 implemented / 3 HOLD; candidates 26 detailed + 2 targeted = 28; Reject 27 / Match HOLD 1; new validated match 0; new admitted independent unit 0; Failure Evidence 108 = old 40 + D 68. Live eligibility 0 / 0 / 13 / 0, HOLD release 0, Promotion 0, Customer Production Approved 0, agency/campaign UNKNOWN each13, and phase2600_allowed=false remain unchanged.

## Reproduce this fix only

```sh
PYTHONPATH=src python scripts/verify_phase2_2_1d_snapshot_binding_fix.py
PYTHONPATH=src python scripts/validate_phase2_2_1d_snapshot_binding_fix.py --check-manifest
```

The first command intentionally writes ONLY the separate fix report directory; its assertion/citation files must already exist. It does not write old D/B/C reports. Running it again changes execution-history/report hashes and requires a new fix output manifest; this does not re-review attribution. Do not use the historical D build/finalize/test/negative CLI commands to overwrite signed historical reports.

Formal review STOP after durable save and integrity readback: `PHASE_2_2_1D_SNAPSHOT_BINDING_FIX_READY_FOR_PM_REVIEW`. New public-payload permission is separate from the old exact-37-file publication consent. No new correction push or Issue final-fix publication is claimed here; the complete new commit/diff/package identity is recorded in the external correction handoff. Sarah PM formal PASS remains pending.
