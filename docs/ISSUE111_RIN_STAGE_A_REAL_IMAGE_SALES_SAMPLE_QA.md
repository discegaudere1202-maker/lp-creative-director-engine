# Issue #111｜Rin Stage A Real-image Sales Sample QA

Baseline main: `116fb0d7e19e16cbcf97343d7f96566f07d044c6`

This task validates the four Stage A category paths through the normal Production path using only the merged Issue #109 `62 / 62` rights-approved Visual Asset Library inventory.

## Sample matrix

Nine synthetic QA samples are used so every Stage A category has same-category authored-divergence coverage while the final browser artifact remains the familiar `81` screenshot matrix.

- skincare/cosmetics product: SK1 / SK2 / SK3
- hair salon: HS1 / HS2
- barber: BR1 / BR2
- Pilates studio: PI1 / PI2

Each sample renders at:

`320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440`

Total: `9 samples × 9 widths = 81 screenshots`.

## Production locks

- CompositionPlan and Creative Family are frozen before any asset selection.
- Business category scopes only the media candidate pool.
- Company/reference identity is recorded for invariance tests and is never used for routing.
- Asset scarcity cannot change Family/topology/scene order.
- Every selected asset is reacquired from the exact merged Issue #109 inventory, SHA-256 fixed, and passed through the asset-level rights/provenance gate again.
- Generic stock stays `GENERIC_ILLUSTRATIVE_STOCK` in machine state and renders with visible `イメージ写真` semantics.
- No generic stock is promoted to actual staff/store/customer/result evidence.
- Hero selection is deterministic and batch-unique.
- Exact asset reuse is prohibited across the Issue #111 sample batch so support bindings cannot create a repeated bundle smell.

## Durable evidence

The workflow artifact contains:

- exact normalized 62-asset runtime catalog;
- reacquisition report;
- nine generated Production outputs;
- complete per-binding trace including full candidate set and rights decisions;
- usage ledger;
- batch hero / bundle uniqueness report;
- 81 full-page screenshots;
- contact sheets for all nine widths;
- final Issue #111 manifest.

For each rendered binding the trace preserves:

`CompositionPlan → Scene Intent → Media Role → complete candidate set → rights decisions → selected asset id + exact binary SHA → crop variant/focal placement → renderer binding → screenshot`.

## Automated browser gates

The Issue #111 workflow fails on:

- broken images;
- horizontal overflow;
- 320px semantic-unit regression;
- rendered binding count mismatch;
- selected asset/hash mismatch between binding trace and DOM;
- missing generic-illustrative caption/evidence state;
- destructive crop heuristic below the conservative visible-fraction threshold;
- repeated Hero;
- repeated exact asset binding across the batch;
- repeated bundle signature;
- same-category candidate-pool mutation by company identity;
- missing company-specific authored divergence;
- Family/topology/scene-order mutation after asset binding.

## Human boundary

Issue #111 does **not** self-declare:

- `HUMAN_VISIBLE_PASS`;
- Real-image Sales Sample readiness;
- final photo-fit quality;
- ¥1M quality.

The completed artifact is routed to Sarah technical/evidence audit and then Aoi independent human-visible review.
