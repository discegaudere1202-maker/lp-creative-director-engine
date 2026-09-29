# Phase 2.1.1 — Durable Evidence Archive / Full-page Scene Traversal

Status: `PHASE_2_1_1_ARCHIVE_AND_SCENE_TRAVERSAL_READY_FOR_PM_REVIEW`. Scope is the existing Gold 20 and five selected full-page references. The remaining 80 and the 2,600-reference universe remain blocked. Sarah PM review in Issue #143, comment #5888095904, is the decision record.

## Durable bytes and locator

The original GitHub Actions artifact (run 36541693976, artifact 11020298341, expiry 2026-10-29 08:19:47 UTC) was downloaded and its original ZIP digest `174da4d8f46e48ad20b3aeecde3e42fdd02e9bea48bf78c2dfa3d5b434edfcb5` checked. Its images were repackaged without changing source image bytes together with the 71 new full-page scene crops.

| Property | Verified value |
|---|---|
| Backend | ChatGPT Library, authenticated file storage |
| Library ID / pinned file ID | `libfile_82b0e73d52fc8191a1bba85895a23ebe` / `file_000000005b588209a215e3daf141e7cd` |
| Version / filename | `0` / `creative_mechanism_gold20_fullpage_v1_sha256-4929f73c.zip` |
| Retrieval | `https://chatgpt.com/api/library/files/libfile_82b0e73d52fc8191a1bba85895a23ebe/download` (authenticated) |
| Container SHA-256 | `4929f73c81d7b8028ad986380ebeb789642a9800cd23685866355c5b41885028` |
| ZIP contents | 159 original artifact files (including 118 snapshots, 40 original crops, manifest) + 71 full-page crops = 230 entries |
| Verification | Uploaded, materialized back by pinned file ID, container digest compared byte for byte, every entry digest checked |

The locator is an actual retrievable file URL. `archive_entry` identifies the member inside the ZIP. `archive_index.jsonl` pins every member digest; each Scene and Snapshot carries its own `content_hash`, archive URL, member path, pinned file ID/version, container hash and `DURABLE_VERIFIED` status. The repository contains ledgers and hashes, not the 36.8 MB image archive.

This is versioned at the application level by a distinct file ID, name and digest. Library immutability and retention are **not guaranteed by this review**. Operational policy: do not replace this file; retain at least three years after last mechanism use and review yearly; materialize and verify monthly and before promotion/reuse. If the file is unavailable, its version changed or any digest fails, set `ARCHIVE_UNAVAILABLE`, HOLD the affected references, and suppress scores and mechanisms in retrieval. Recapture the original URL into a new snapshot/version; never overwrite the old ledger. A changed live page invalidates the affected downstream score and candidate pending review. The CLI validator requires the pinned materialized ZIP and fails closed without it.

## Scene traversal and missingness

Existing Playwright full-page captures at 1440px desktop and 390px mobile were traversed from top to bottom for P01-R01 (landscaping), P05-R04 (finance), P06-R02 (medical), P08-R02 (SaaS) and P12-R01 (media-rich SaaS). Pixel y-ranges are contiguous from zero to the captured full-page height in all ten viewport records. This is semantic decomposition of **existing captured pages**, not a fresh 100-reference collection.

| Reference | Desktop scenes | Mobile scenes | Distinct later-page observation |
|---|---:|---:|---|
| P01-R01 | 7 | 7 | Garden service mosaic, maker portrait, contact, footer |
| P05-R04 | 7 | 7 | Service cards, dated notices, support routes, footer |
| P06-R02 | 7 | 7 | Concern-to-care guidance, appointment/support split, human proof, footer |
| P08-R02 | 7 | 6 | Product workflows, updates, dual CTA, footer |
| P12-R01 | 8 | 8 | Metrics, business examples, technical explanation, closing |

There are 71 records: 70 OBSERVED and one `NOT_OBSERVED` (`GOLD-P12-R01-MOBILE-TRAV-08`). Stripe's captured mobile tail is blank. Its footer is not evidenced by those pixels. This is a capture gap rather than evidence that the original page lacks a footer. Each viewport has six semantic-job coverage states; an absent job is `NOT_APPLICABLE`, and an unobservable capture is `NOT_OBSERVED`. A Scene role name alone never proves the visual subject. Some lazy/rendered media in Linear/Stripe have incomplete static pixels; `media_runtime_status` records this. Motion, hover, keyboard, focus and reduced-motion behavior remain `NOT_OBSERVED` unless runtime-tested. DOM video presence does not pass a motion score.

Scene records contain concrete location, captured URL/time/viewport, screenshot and crop hashes, visible DOM headings/actions and media metadata, plus separate type/layout/media/geometry/rhythm/proof/conversion/navigation observations. Pixel crops are reviewable against the parent full-page screenshot. Image-only areas rely on the crop and cannot be mined for unverified semantic claims.

## Provenance, claims and scores

Fifteen late-page `CANDIDATE` mechanisms were mined from the observed full-page scenes. `source_scene_evidence_ids[]` resolves to 30 source instances; `evidence_count`, reference count and independent brand count are derived. Agency/campaign independence stays `UNKNOWN` where source evidence is absent. Existing 20 Gold candidates remain candidates, and the 25 Phase 2 provisional candidates remain frozen. No SUPPORTED or CANONICAL promotions occurred. The unseen Stripe mobile closing contributes to no candidate.

Three additional full-page claim units point to finance rates, medical history copy and Stripe's quantified scale panel. They are **visible brand claims, not independently verified terms, effectiveness, compliance or CVR**. Existing claim, accessibility and performance ledgers remain. Keyboard/focus/reduced-motion and runtime performance were not measured; do not infer PASS.

The Gold 20 numeric scores remain `CAPTURED_ENTRY_AND_FIRST_SCROLL_ONLY` even for the five with later-page static Scene coverage. `additional_fullpage_static_scene_ids` records the expanded observation without recycling those numbers as full-LP scores. `full_lp_score_status=NOT_SCORED`, `corpus_ranking_allowed=false`, and promotion flags false. New scoring requires dimension-level review of later scenes and missing runtime behavior.

## Per-record issues and gates

The original `DISCOVERY_TRACE`, `CAPTURE_TARGET`, `RESPONSIVE_SUBJECT`, `TEMPORAL_MOTION`, `ACCESSIBILITY_RUNTIME`, `CLAIM_TERMS` and `CROP_SELECTOR` issues are retained. The 20×7 record-gate ledger records applicability and affected use; 31 entries are applicable. Dior's selector issue applies to P19, Airbnb/Stripe responsive-subject concerns to P04/P12, accessibility runtime to medical/public records, claims to relevant regulated and quantified cases. A selector-derived crop never substitutes for the archived viewport/full-page pixels. These are reference-specific holds, not a fabricated global PASS. All 20 Gold references remain HOLD pending PM review and any record-specific recapture or runtime review.

## QA and next decision

`python scripts/validate_phase2_1_1.py --archive <pinned-materialized-zip>` checks: real local archive bytes and pinned identity, 230 entry hashes, 118 snapshots, 80 prior + 71 new scenes, no temporary Gold capture, contiguous full-page pixel coverage and semantic-job states, observed-only provenance and derived counts, scoped scores, seven per-record risk gates, 100 Pilot preservation, and `remaining_80_allowed=false`. `PHASE2_1_1_ARCHIVE=<path> python -m unittest discover -s tests -p 'test_phase2_1*.py' -v` also exercises bad hash, missing archive, temporary capture, false PASS, wrong count and NOT_OBSERVED source rejection.

PM should review archive access/retention assumptions, the one blank mobile tail, per-record risk gates and whether a scroll-triggered recapture is required before expanding to the remaining 80. This work grants no permission to expand.
