# Phase 2.2.1A — Final Reconciliation

**Status: FAIL-CLOSED — NOT READY FOR PM REVIEW**  
**Required success status not reached:** `PHASE_2_2_1_CAPTURE_RECOVERY_READY_FOR_PM_REVIEW`  
**Recovery branch at audit start:** `phase2-2-1/reconciliation-calibration-in-progress`  
**Recovery branch HEAD at audit start:** `435b1ab3e185342107f4df43f57cb9699467ef14`  
**Expansion gate:** `phase2600_allowed=false`

## Source and rebuild

The six committed bundle parts were reassembled and matched the pinned tarball SHA-256 `cf710cd8b25657944a5da295af91c21ab491778259390618663cbb3a7719da9f`. The Integrated Builder (`scripts/reconcile_phase2_2_1.py`) was rerun from the extracted source ledgers. The Validator (`scripts/validate_phase2_2_1.py`) passed against those regenerated outputs. The corrected matrix has 20 cells and sums to 73; the legacy matrix input still sums to 5 and remains historical.

## Required counts

| Measure | Final observed value | Gate |
|---|---:|---|
| attempted_reference_count | 100 | — |
| original_usable_count | 73 | — |
| recovered_original_count | 0 | — |
| unrecoverable_original_count | 0 | 27 remain unresolved; none may be relabeled unrecoverable |
| same_cell_replacement_count | 0 | — |
| replacement_attempt_count | 0 production attempts | Smoke-only lane test is excluded |
| final_usable_reference_count | **73** | **FAIL; required 100** |
| desktop_1440_durable_count | **73** | **FAIL; required 100** |
| mobile_390_durable_count | **73** | **FAIL; required 100** |
| both_viewports_durable_count | **73** | **FAIL; required 100** |
| Scene Evidence rows | 1,240 | — |
| OBSERVED / NOT_OBSERVED / NOT_APPLICABLE | 906 / 334 / 0 | — |
| Durable Archive Containers | 11 | 11/11 container SHA match |
| Durable Archive Members | 1,442 | 1,442/1,442 member hash match; zero missing; ZIP integrity PASS |

The 27 failed original references remain unresolved, not confirmed unrecoverable. No same-cell production replacement has been selected or attempted.

## Replacement Capture Lane evidence

The separate infrastructure branch is `phase2-2-1a/replacement-capture-lane`, HEAD `c30b1a889a75b56a1af43d27183af284bf789fb0`. Its successful Actions run `36670569233` captured only the isolated `SMOKE_ONLY` target `SMOKE-EXAMPLE-001` at `https://example.com/`; it is not an approved replacement and is not part of the Pilot.

- Primary temporary artifact: `phase2-2-1a-replacement-evidence-36670569233`
- Artifact ID: `11077991547`
- Artifact digest: `sha256:65abe0cfece0a258a5429fc108778c1f24751b2a78200f68f9ea81e75125ff06`
- Retention: 30 days; temporary Actions evidence only, not Durable Archive ingestion
- Manifest SHA-256: `7fbe84149cf10606d8ca6efd612a770c48c7c0a5d73ce9db41ed0e6900d949cb`
- Desktop image SHA-256: `919499c62e416f2890a962d95ce37dd137a339fa07a329e7838471c9a31604f4`
- Mobile image SHA-256: `cecce9d7eedfa3dcbb844dc9e23387b13ea9b567896327eb020537c64726cd0a`
- HTTP 200, full-page traversal observed and complete at both viewports; all artifact member hashes rechecked.

The smoke run demonstrates the infrastructure path only. It adds zero durable replacement archive members and contributes zero usable Pilot references.

## Reconciliation and QA

- Integrated Builder generated: Master, 20-cell Matrix, Aggregate, QA, PM Summary, and failure ledger from the same snapshot/scene/claim/candidate/archive ledgers.
- `Master == Matrix == Aggregate == QA == PM Summary`: **PASS at the observed 73-reference totals**.
- Durable archive registry digest: `377c24f49213e1a76a78b912e8dc29c0911334827e6f32f594168890fc3cd6fe`; container and member verification: **PASS**.
- Replacement Cell QA: **not applicable to production; zero replacement candidates**. The smoke fixture's validator cell check is infrastructure-only and cannot count as replacement QA.
- Recovery Validator: **PASS** for internally consistent ledgers; this does not make the 100-reference gate pass.
- Tests: reconciliation **3/3 PASS**; replacement capture lane **13/13 PASS**.
- Security bypass: **0**; no CAPTCHA/WAF/fingerprint/proxy/protected-route/credential bypass used.
- `phase2600_allowed=false`: **PASS**.

## Unresolved blockers and decision

The four mandatory thresholds are all unmet: final usable 73/100, Desktop durable 73/100, Mobile durable 73/100, both durable 73/100. Same-cell replacement selection, production replacement capture, and durable archive ingestion of replacement evidence remain unperformed. The 27 original failure rows remain in their audit trail.

Accordingly, this report does **not** claim `PHASE_2_2_1_CAPTURE_RECOVERY_READY_FOR_PM_REVIEW`. The task remains blocked pending completion of same-cell recovery/replacement and durable evidence capture. Compatibility Calibration, Production Renderability, and 2,600-reference expansion remain out of scope; `phase2600_allowed=false` is preserved.
