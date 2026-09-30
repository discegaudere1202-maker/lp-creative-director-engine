# Phase 2.2.1D — Independent Evidence Acquisition / Eligibility Unlock Calibration

Approved baseline: `b3d4607277c3e13a24505e70b94bf3ec03b67362`; Sarah PM approval: Issue #143 comment `5914339229`.

The bounded review finds **zero admissible new independent units and zero HOLD releases**. All 13 mechanisms remain live HOLD. Ten adapters remain implemented and three remain HOLD. This is a research checkpoint for PM review, not customer-production approval or mechanism maturity promotion. `phase2600_allowed=false`.

## Evidence and scope

The sixteen pinned durable100 archives were materialized and their original container SHA-256 values verified. All 1,414 distinct referenced image members, 498 snapshot records and 1,024 scene records were checked against those bytes. One hundred desktop/mobile **entry viewport pairs** were visually screened. Twenty-six shortlisted reference/mechanism comparisons received detailed inspection against the source contract and the first three recorded scene images per viewport. Long full-page thumbnails provide overview only. This is **not** a claim that every pixel of all 100 full pages was visually examined, or that the corpus is semantically exhausted.

The comparison records cover composition, hierarchy, typography, media role, spatial behavior, responsive behavior, implementation boundary and Scene Job. Differences in color/type styling alone do not reject a mechanism: the notes identify changes to action hierarchy, proof/media roles, paired scene grouping, responsive ordering or unresolved source boundaries. Framer is the strongest partial dark UI Stage comparator; media proof boundary, focused workflow cadence and responsive UI legibility remain unresolved. It is retained as a match HOLD rather than silently counted as an independent unit.

Twenty-five existing-corpus comparisons are atomic-core rejects and one is unresolved. Two additional official-page candidates were selected only after recording the mechanism/independence hypotheses. Standard Chromium at the required 1440/390 sizes returned `ERR_EMPTY_RESPONSE` for both candidates. This is a network failure; no target-served bot block was observed and no security bypass was attempted. Ordinary cloud-browser observations were possible, but the screenshots have the wrong required widths, missing mobile counterparts, incomplete lower lazy-media loading and no admissible recorded capture clock. They are saved **only as rejection/limitation evidence**, never added to the usable corpus or independent-unit count. Roth separates the large proposition below the garden photograph; Rijksmuseum uses a huge museum title and explicit visit/ticket purpose rather than resolving the original UNCLASSIFIED work-entry job.

Primary production cases are scoped to their actual subject and period. Linear's UI redesign does not credit its marketing homepage; Coosy's corporate freee page does not credit the service homepage; Sony's card/app design does not credit the rate homepage; Roseau Pensant's SABON project direction leaves other partners/campaign production unresolved; historical Aman platform/booking cases cannot establish the maker of the pinned campaign. Agency and campaign independence remain UNKNOWN for all 13 baseline mechanisms.

## Machine gate

`src/lp_engine/independence_calibration.py` requires both viewports to resolve to scene IDs, reference identity and verified archive-member hashes. Every critical match axis must be evidenced; partial/unknown observations cannot pass via an average score. Family pairs require snapshot-bound primary-source assertions for brand/parent-family resolution, campaign, agency, production company, source family and template family. A shared family rejects; unresolved relations remain UNKNOWN or PARTIALLY_INDEPENDENT. A singleton can never become VERIFIED_INDEPENDENT. Desktop/mobile, gallery, archive mirror and localization derivatives do not add independent units.

The actual production path consults the D source-derived ledger before the existing C independence gate. All C truth, rights, compatibility, desktop/mobile, accessibility, implementation, evidence trace, motion and reduced-motion constraints remain active. Author-owned test fixtures remain separate from actual production. No source photograph/screenshot is supplied to customer render output. No static evidence is interpreted as animation or carousel interaction. No adapter is added. No maturity is promoted.

No new fully validated atomic match is admitted, so no mechanism receives a new-evidence eligibility recalculation. The unchanged C eligibility is copied as HOLD with an explicit D retention reason. There is no pending ELIGIBLE/CONDITIONAL row and therefore no conditional scope or prohibited-combination list to invent.

## Validation and counts

Run `python scripts/exercise_phase2_2_1d_rejections.py` for eighteen replayable negative specimens, and `python scripts/test_phase2_2_1d.py` for the D cases plus the complete 50-case C/B/production regression selection. The runner loads test files by absolute path and refuses an empty suite. The independent trace validator additionally checks original approved git blobs, saved C browser evidence, discovery ZIP/member/image hashes, authored comparison aggregation and negative specimen replay. The original C validator runs in an isolated archive of the approved commit, because its original code Hash cannot also describe the new D gate. The validator checks that the sole changed C-hashed code file contains exactly the additive D admission call and that every other C output Hash is unchanged. Fresh regression tests exercise the current D code. It is a structural/trace validator, not a second human semantic approval.

Run `python scripts/validate_phase2_2_1d.py --archive-directory <materialized-original-archives>` to repeat all sixteen original container and 1,414 member checks. Without that optional directory it still checks the pinned source records and recorded readback results, but explicitly reports that original ZIP bytes were not re-read in that invocation. The final run used the actual directory.

The five production profile routes are executed as negative gate checks and reject before creating output. Since eligibility changes are zero, changed-eligibility production renders are **NOT APPLICABLE**, and fresh desktop/mobile render PASS counts are not claimed. The prior C desktop/mobile 8/8 PASS evidence is preserved and validated as historical evidence.

All 40 old failures (B 17 + C 23) are byte-preserved. D adds 68 separately identified failure records: 25 atomic rejects, one match HOLD, thirteen live independence HOLD checks, two targeted rejects, four required-viewport capture failures, eighteen intentional negative cases and five real production-route rejects. Total: 108. Per-mechanism failure counts include records explicitly assigned to that mechanism; the eighteen synthetic negatives and five multi-mechanism profile rejects remain global to avoid arbitrary allocation. Six resolved execution incidents are separately retained and excluded from those research-failure counts.

The mechanism-level independence counts describe the **accepted evidence set**: VERIFIED 0 / PARTIAL 0 / NOT_INDEPENDENT 13 / UNKNOWN 0. Each mechanism still has one accepted reference unit. Candidate independence stays UNKNOWN and is separately reported; rejected or unresolved candidates do not increase accepted units. Different URL, domain or brand never changes that result.

## Review files

| File | Review purpose |
|---|---|
| `corpus_readback.json` / `corpus_screening.json` | Original pinned archive hashes and exact screening scope |
| `baseline_units.json` | Thirteen accepted baseline units with both viewport scene IDs |
| `candidate_reviews.json` / `detailed_review_index.json` | Twenty-six eight-axis comparisons and actual inspection scope |
| `source_attribution_audit.json` | Thirteen bounded attribution checks and scope/period limitations |
| `targeted_precapture.json` / `targeted_capture_manifest.json` / `targeted_outcomes.json` | Two prior hypotheses, actual failures and candidate denial reasons |
| `discovery_archive_registry.json` | Five-member rejection archive SHA-256/readback and image dimensions |
| `calibration.json` / `final_report.json` | Derived per-mechanism outcomes, counts and remaining blockers |
| `negative_test_report.json` / `failure_evidence.jsonl` | Replayable specimens and append-only phase-D failures |
| `production_gate_revalidation.json` | Five actual live route denials, zero changed-eligibility renders |
| `phase_b_c_preservation.json` / `output_hashes.json` | Approved original byte preservation and reviewed D artifact hashes |
| `tests_report.json` / `validator_report.json` | Actual fresh test and validator results |

The exact final SHA and branch are supplied in the Issue #143 final comment, which binds the Git repository archive path to a concrete immutable commit. Sarah PM may dispute or refine any semantic comparison using its source scene IDs and pinned original archive bytes. No claim that the search found every possible independent instance is made.

STOP only after validation succeeds: `PHASE_2_2_1_INDEPENDENCE_ELIGIBILITY_READY_FOR_PM_REVIEW`.
