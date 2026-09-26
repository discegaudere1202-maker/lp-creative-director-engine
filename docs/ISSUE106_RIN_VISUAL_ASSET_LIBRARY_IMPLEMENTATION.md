# Issue #106｜Rin Visual Asset Library Runtime

This implementation consumes the accepted Issue #104 contract without changing Creative Family/topology authority.

Runtime order:

`Frozen CompositionPlan → Scene/Media Role → category-scoped candidate pool → asset-level rights gate → deterministic visual-fit/reuse selection → AssetBinding → Production render → binary/provenance trace → browser evidence`

## Production locks

- Current industries only: `beauty_cosmetics`, `hair_salon_barber`, `pilates_fitness`.
- Category scopes asset candidates only.
- Company/reference identity never routes asset architecture.
- Asset scarcity returns an explicit media failure/review state; it never switches Family/topology/scene order.
- Generic stock is rendered with illustrative semantics and cannot satisfy `ACTUAL_COMPANY_EVIDENCE`.
- Exact selected binary SHA-256 is carried through AssetBinding and screenshot manifest.
- Legacy `photography.py` remains available for older paths, but its family role packs/source-priority/first-match logic are not Production authority for Issue #106.

## Acquisition scope

The checked-in Pexels Stage A seed is a candidate registry, not an approval whitelist. CI downloads each exact binary, calculates SHA-256, validates dimensions, executes the asset-level rights gate, stores an artifact-local cache keyed by source id + hash, and only then permits Production binding.

The seed intentionally does not fabricate the Issue #104 minimum 129-asset inventory. Artifact output reports actual rights-pass coverage and explicit remaining gaps before Real-image Sales Sample QA may begin.

## Final candidate correction

Initial evidence exposed one cosmetics candidate with visible product branding and one hair-salon candidate with signage / branding risk. They were removed from the Stage A seed before review handoff.

Replacement assets were independently inspected before final evidence generation:

- cosmetics: Pexels `15369086`, an unlabeled cosmetic container;
- hair salon: Pexels `7750098`, a salon interior without visible target-company identity / store signage.

Both replacements were reacquired, hashed, re-run through the rights gate, rebound into Production, and regenerated across all 81 screenshots.

## Evidence convention

Exact final HEAD / workflow run / artifact identifiers are recorded in PR #107 and Issue #106 completion comments so recording them does not mutate the Task branch after the final QA run.

Validated gates include:

- 81 / 81 screenshots;
- CompositionPlan / Family / topology / scene order preserved;
- selected rights gate / image load / overflow / 320px semantic regression / renderer trace-hash join pass.

Actual Stage A inventory: `11 / 62`; remaining gap `51`.

- skincare/cosmetics product: `3 / 10`, gap 7.
- hair salon: `2 / 18`, gap 16.
- barber: `3 / 18`, gap 15.
- Pilates studio: `3 / 16`, gap 13.

The inventory floor is not fabricated, so `real_image_sales_sample_qa_start_gate=false` remains explicit.

## Human boundary

Automated success proves runtime/rights/trace/browser integration only. It does not self-declare `HUMAN_VISIBLE_PASS`, final photo fit, Real-image Sales Sample readiness, or ¥1M quality. Aoi remains the independent human-visible reviewer of the actual selected-image screenshots.
