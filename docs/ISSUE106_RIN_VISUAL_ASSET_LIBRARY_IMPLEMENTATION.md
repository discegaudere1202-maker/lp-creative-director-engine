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

## Sarah exact-binary visual-risk correction

Initial Rin evidence replaced two obvious candidates before handoff, but Sarah's technical/evidence audit of the **actual downloaded binaries** found two additional metadata mismatches that automated provider metadata did not reveal:

- `pexels-16378448`: visible `SYAGI` / product-label text on the cosmetic binary;
- `pexels-7518728`: visible `Levi's` signage inside the barbershop binary.

Both exact asset IDs are now blocked before ingestion by:

`data/visual_asset_library/providers/pexels_stage_a_sarah_corrections_v1.json`

They are replaced for final evidence by:

- cosmetics: Pexels `11741343`, blank cosmetic bottle candidate;
- barber: Pexels `19664872`, empty barbershop interior candidate.

The final CI runner applies this correction contract before acquisition, then reacquires, hashes, runs asset-level rights gates, rebinds Production, and regenerates all 81 screenshots. The final Artifact must be visually inspected again before Aoi PASS.

## Evidence convention

Exact final HEAD / workflow run / artifact identifiers are recorded in PR #107 and Issue #106 completion comments so recording them does not mutate the Task branch after the final QA run.

Validated machine gates include:

- 81 / 81 screenshots;
- CompositionPlan / Family / topology / scene order preserved;
- selected rights gate / image load / overflow / 320px semantic regression / renderer trace-hash join pass.

The inventory floor must not be fabricated, so `real_image_sales_sample_qa_start_gate=false` remains explicit until the Issue #104 category minimums are actually satisfied.

## Human boundary

Automated success proves runtime/rights/trace/browser integration only. It does not self-declare `HUMAN_VISIBLE_PASS`, final photo fit, Real-image Sales Sample readiness, or ¥1M quality. Aoi remains the independent human-visible reviewer of the actual selected-image screenshots after Sarah accepts the final regenerated evidence.
