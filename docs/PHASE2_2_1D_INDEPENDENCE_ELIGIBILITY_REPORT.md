# Phase 2.2.1D — Independent Evidence Acquisition / Production Eligibility Unlock Calibration

**Ready for Sarah PM review. HOLD released: 0; remaining HOLD: 13.**

Approved baseline: `b3d4607277c3e13a24505e70b94bf3ec03b67362`; Sarah PM authorization: Issue #143 comment #5914339229.
Branch: `phase2-2-1d/independence-eligibility-20261001`. Exact final commit and tree are bound in the Issue #143 submission.

## Result and review boundary

No new independently validated atomic mechanism unit was admitted. Eligibility remains **0 ELIGIBLE / 0 CONDITIONAL / 13 HOLD / 0 INELIGIBLE**. Each mechanism retains one accepted reference unit. Accepted-set independence remains **0 VERIFIED / 0 PARTIAL / 13 NOT_INDEPENDENT / 0 UNKNOWN**; agency and campaign independence remain UNKNOWN for all 13. Candidate independence is separately UNKNOWN and is not represented by the accepted-set counts.

The review is bounded screening, not a claim of semantic exhaustion. All 100 desktop/mobile entry pairs and all 1,024 scene records were screened; 26 selected reference/mechanism pairs received detailed scene comparison. Every full-page pixel was not visually inspected. Two additional official references were attempted after precapture hypotheses; both failed required 1440/390 network acquisition. Cloud screenshots are wrong-width, unpaired rejection evidence only.

## Per mechanism

All rows: existing units 1; newly accepted independent units 0; previous/new eligibility HOLD/HOLD; accepted independence NOT_INDEPENDENT; agency/campaign UNKNOWN; motion STATIC_ONLY; promotion 0. Desktop/mobile fresh render revalidation is NOT APPLICABLE because eligibility did not change. The JSON report contains rejection reasons, scene/contract/hash trace and per-mechanism failure counts.

| Mechanism | Candidates | Reject | Match HOLD | Adapter |
|---|---:|---:|---:|---|
| CM-VIS-ENVIRONMENTAL-HERO-01 | 3 | 3 | 0 | IMPLEMENTED |
| CM-VIS-CLINICAL-HUMAN-HERO-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-PRODUCT-UI-STAGE-01 | 2 | 1 | 1 | IMPLEMENTED |
| CM-VIS-EDITORIAL-PRODUCT-CAROUSEL-01 | 2 | 2 | 0 | HOLD |
| CM-VIS-CINEMATIC-DESTINATION-ENTRY-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-PUBLIC-UTILITY-MODULE-GRID-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-RENOVATION-PORTAL-HERO-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-FINANCE-RATE-PANEL-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-INDUSTRIAL-PRODUCT-CAROUSEL-01 | 2 | 2 | 0 | HOLD |
| CM-VIS-SaaS-AUDIENCE-PATH-SPLIT-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-RETAIL-CAMPAIGN-TILE-DIPTYCH-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-BEAUTY-BRAND-INDEX-FEATURE-01 | 2 | 2 | 0 | IMPLEMENTED |
| CM-VIS-CULTURE-FULLBLEED-WORK-ENTRY-01 | 3 | 3 | 0 | HOLD |

## Validation and preservation

- Scoped D/C/B/production regression: **66 PASS / 0 FAIL / 0 skipped** (16 + 26 + 18 + 6).
- Deliberate independence/match negatives: **18 PASS / 0 FAIL**, replayable specimens retained.
- Production routes: Local Trust, B2B Technical, D2C Product, Premium Place and Public Information all reject before output creation.
- Final structural/trace Validator: **PASS**, including real reread of **16 containers / 1,414 members**.
- Historical C Desktop/Mobile **8/8 PASS** evidence is preserved; no fresh D render PASS is claimed.
- Original C validator executed on an isolated archive of the approved commit; the current C-hashed code file is checked for the exact additive D gate call, every other C output Hash remains unchanged. Original manifests are preserved.
- Failure Evidence: **108 = B 17 + C 23 + D 68**. D: 25 match rejects, 1 match HOLD, 13 eligibility HOLDs, 2 targeted rejects, 4 viewport capture failures, 18 intentional negatives and 5 live solver/gate rejects.
- Six resolved engineering incidents are recorded separately from the 68 research/gate/capture records.
- Adapter coverage stays **10 IMPLEMENTED / 3 HOLD**. No adapter was auto-implemented.
- Promotion **0**; customer production approved **0**; `phase2600_allowed=false`.

## Unresolved blockers

Framer is a partial Product UI Stage comparator, not an admitted atomic match: media/proof role, workflow cadence, mobile UI legibility and implementation boundary remain unresolved. Other compared candidates change atomic structure, hierarchy, media roles, scene job or responsive ordering. Historical or adjacent-page creator cases do not prove the maker/campaign of the pinned snapshot. The two targeted acquisitions lack admissible paired evidence. Carousel interaction semantics and the culture UNCLASSIFIED Scene Job remain HOLD. Client truth/rights/current output QA are still required.

These limitations remain available to PM. HOLD retention is an evidence-backed decision; this submission does not assert that the corpus has no other possible matching mechanisms.

## Reproduce

```sh
PYTHONPATH=src python scripts/exercise_phase2_2_1d_rejections.py
PYTHONPATH=src python scripts/test_phase2_2_1d.py
PYTHONPATH=src python scripts/validate_phase2_2_1d.py --archive-directory <materialized-original-archives>
```

`data/phase2_2_1d/README.md` maps the detailed audit records. `final_report.json` includes all mechanism-level metrics and `validator_report.json` records actual archive readback. Original corpus container/member locators and SHA-256 are pinned in `corpus_readback.json`. New rejection images and manifest have a separate commit-addressed discovery archive.

**STOP: `PHASE_2_2_1_INDEPENDENCE_ELIGIBILITY_READY_FOR_PM_REVIEW`.**
Sarah PM semantic review is pending. No next phase or 2,600-reference expansion is authorized.
