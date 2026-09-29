# Phase 2.1.1 PM Review Report

**Status:** `PHASE_2_1_1_ARCHIVE_AND_SCENE_TRAVERSAL_READY_FOR_PM_REVIEW`  
**Decision scope:** Durable Gold evidence plus five full-page traversals. The remaining 80 and 2,600 are still HOLD.

## Blocker A — archive

- The expiring Actions artifact was retrieved and original ZIP SHA-256 matched `174da4d8f46e48ad20b3aeecde3e42fdd02e9bea48bf78c2dfa3d5b434edfcb5`.
- A new Library file, `libfile_82b0e73d52fc8191a1bba85895a23ebe`, holds all 118 original snapshots, 40 old crops, the original capture manifest and 71 additional scene crops. Its pinned ZIP digest is `4929f73c81d7b8028ad986380ebeb789642a9800cd23685866355c5b41885028`.
- Materialization by pinned file ID succeeded and all 230 ZIP entry hashes matched. Snapshot and Scene ledgers now use the actual authenticated archive URL, member path, file ID/version, SHA-256 and `DURABLE_VERIFIED`. No placeholder S3 URI and no image blobs in Git.
- Retention, monthly verification, recapture/invalidation and archive-loss fail-closed policy are documented. Backend-enforced immutability or a guaranteed retention SLA is unverified; version identity and digest protect against silent replacement.

## Blocker B — full-page traversal

- Five specified existing Gold references, ten viewport captures (1440/390), 71 semantic Scene crops across full captured page heights. P01 14, P05 14, P06 14, P08 13, P12 16.
- 70 scenes are OBSERVED; Stripe's blank mobile closing is NOT_OBSERVED and contributes no mechanism. The archive contains its pixel crop to audit the absence in that capture.
- Fifteen additional candidates were mined with 30 source Scene IDs. These describe later-page service, trust, proof, CTA and closing mechanisms, not unobserved motion. All remain CANDIDATE; unknown agency/campaign independence remains UNKNOWN.
- The five have expanded static observation. The prior 20 numeric scores remain explicitly entry/first-scroll only, with no corpus ranking, Strong or canonical promotion.
- Finance/medical/quantified Stripe claims have three new Scene-linked claim units. Terms and outcomes are unverified. Runtime accessibility, interaction and motion remain NOT_OBSERVED.

## Preserved scope and open risks

The 100-reference Pilot, 20 Gold selections, 25 frozen provisional Phase 2 mechanisms, original 20 Gold candidates and all seven named Gold issue types remain preserved. A 140-row per-record gate ledger marks 31 applicable conditions without converting unknown checks to PASS. Dior's capture target, Airbnb's responsive subject, source discovery trace, financial/medical/beauty terms, runtime accessibility/motion and selector-specific crop reliability still require affected-record resolution. Stripe's mobile closing needs scroll-triggered recapture before anyone mines that footer. Some lazy media remain partially visible in static full-page pixels.

## QA

Pinned Library roundtrip: PASS. ZIP integrity: PASS. 230/230 entry SHA-256: PASS. Scene/snapshot hashes: PASS. Traversal coverage: 10/10 viewport page ranges, with 1 explicit NOT_OBSERVED Scene. Observed-only mechanism provenance and derived counts: PASS. Per-record gates: PASS. 100 Pilot preserved: PASS. Remaining 80 and bulk gates: CLOSED. Eight Phase 2.1.1 tests plus seven prior Gold tests: PASS.

**PM decision requested:** validate the retention governance and missing mobile tail policy, then decide whether to authorize the remaining 80. No expansion was started.
