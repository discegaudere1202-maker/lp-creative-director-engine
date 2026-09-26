# Issue #104｜Rin Implementation Handoff

## 0. Scope lock

Implement **current-industry Visual Asset Library only** for:

- `beauty_cosmetics`
- `hair_salon_barber`
- `pilates_fitness`

Do not add industries. Do not redesign Production Family/topology. Do not route by company/reference identity.

The normal Production path already treats CompositionPlan as authoritative. Asset implementation happens **after Creative Family is frozen** and must not mutate Family/topology/scene order.

## 1. Target runtime sequence

```text
CompositionPlan (Family frozen)
→ scene_intent
→ media_role
→ required_content_conditions
→ current-industry/business-category candidate query
→ rights/provenance gate
→ visual-fit + reuse-aware deterministic rank
→ crop/placement feasibility
→ renderer binding
→ asset provenance trace
→ automated QA
→ 9-width screenshots
→ Aoi human-visible QA
```

No candidate / rights failure:

```text
MEDIA_ROLE_UNSATISFIED | HUMAN_REVIEW_REQUIRED
```

Never:

```text
asset scarcity → different Family/layout/profile
```

## 2. Proposed storage/data structure

```text
data/visual_asset_library/
  schema/
    asset_metadata_v1.json
    rights_gate_v1.json
    usage_ledger_v1.json
  providers/
    pexels_terms_snapshot.json
    unsplash_terms_snapshot.json
    pixabay_terms_snapshot.json
  catalog/
    beauty_cosmetics.jsonl
    hair_salon_barber.jsonl
    pilates_fitness.jsonl
  category_index/
    <industry>/<business_category>.json
  usage/
    asset_usage_ledger.jsonl
```

Exact image binaries should not be duplicated unnecessarily in git. Use a deterministic Production cache/object-store boundary keyed by `binary_sha256`; CI evidence can package selected binaries/screenshots as workflow artifacts. The catalog record keeps stable provider/source provenance.

Suggested cache identity:

```text
<provider>/<source_id>/<binary_sha256>.<ext>
```

## 3. Asset schema implementation

Create one normalized `VisualAssetRecord` matching:

- `artifacts/issue104_riko/asset_metadata_contract_v1.json`

Required implementation characteristics:

1. strict enum validation;
2. source detail URL required;
3. provider license terms URL + checked date required;
4. commercial/modification/crop permission required;
5. person/property/trademark risk fields required;
6. evidence boundary required;
7. current industry/category/content-class/role tags required;
8. exact binary hash required before Production render;
9. recheck trigger state required;
10. incomplete rights metadata fails closed.

Do not map legacy `RESEARCH_APPROVED_FREE_STOCK` directly to Production approval without the new metadata/rights checks.

## 4. Ingestion pipeline

Implement ingestion as schema-first, source-provider-neutral adapters:

```text
provider asset/detail page
→ source id/url normalize
→ license snapshot reference
→ metadata extraction
→ binary acquisition
→ sha256
→ content classification
→ role/category tagging
→ third-party rights flags
→ rights gate
→ catalog insert/update
```

The adapter must preserve raw/source fields for audit. It must never infer company-specific evidence from visual similarity.

Minimum ingestion statuses:

- `INGESTED_UNREVIEWED`
- `RIGHTS_BLOCKED`
- `RIGHTS_CONDITIONAL_REVIEW`
- `PRODUCTION_ELIGIBLE_ILLUSTRATIVE`
- `PRODUCTION_ELIGIBLE_COMPANY_EVIDENCE`
- `REVOKED_OR_STALE`

## 5. Rights gate

Implement `evaluate_visual_asset_rights(asset, target_use)` using:

- `artifacts/issue104_riko/rights_gate_contract_v1.json`

Hard behavior:

- official-site visibility ≠ reuse permission;
- unknown license/commercial-use state = fail;
- unresolved crop/modification restriction = fail when crop is required;
- required attribution must survive renderer placement;
- identifiable person/property/trademark may require review;
- generic stock may not bind to an `ACTUAL_COMPANY_EVIDENCE` placement;
- stale/changed binary or terms triggers recheck;
- rights failure removes the asset candidate, not the Family.

## 6. Candidate query contract

Suggested function boundary:

```python
query_asset_candidates(
    *,
    industry,
    business_category,
    scene_intent,
    media_role,
    required_content_classes,
    target_orientation,
    target_aspect,
    evidence_boundary,
    catalog_version,
) -> list[VisualAssetRecord]
```

Business category is allowed only to **scope the asset pool**. It must not feed Production Family/topology selection.

## 7. Deterministic selector

Suggested boundary:

```python
select_visual_asset(
    candidates,
    *,
    frozen_composition_plan,
    scene,
    media_role,
    target_placement,
    usage_ledger_snapshot,
) -> AssetSelectionResult
```

Ordering must follow `selection_reuse_contract_v1.json`:

1. exact content class;
2. scene intent;
3. media role;
4. orientation/crop feasibility;
5. visual tone fit to frozen CompositionPlan;
6. material-quality fit;
7. people-context fit;
8. reuse penalty;
9. stable `asset_id` tie-break.

No randomness.

Persist rejected-candidate reasons in the provenance trace.

## 8. Usage ledger / anti-template protection

Persist at least:

- generation/company surrogate id (for usage accounting only, never routing);
- asset id;
- role;
- scene;
- crop fingerprint;
- placement prominence;
- industry/category;
- generation timestamp/batch id.

Hard gates:

- no duplicate binary in multiple dominant roles on one LP;
- hero assets unique within a current generation batch unless explicit human exception;
- no repeated same asset + same role + same crop fingerprint across adjacent/current outputs;
- never copy another company's full media-role asset bundle.

Initially log reuse metrics rather than invent a global Template Resemblance score threshold. Calibrate numeric limits from actual batches + Aoi judgment.

## 9. Renderer binding

Renderer consumes an `AssetBinding` produced after selection. Suggested fields:

```json
{
  "asset_id": "...",
  "binary_sha256": "...",
  "media_role": "hero",
  "scene_id": "recognize",
  "evidence_status": "GENERIC_ILLUSTRATIVE_STOCK",
  "source_provider": "Pexels",
  "source_url": "...",
  "rights_gate": "RIGHTS_PASS_WITH_RENDER_CONDITIONS",
  "crop_variant_id": "...",
  "focal_point": [0.5, 0.4],
  "alt_text_mode": "illustrative",
  "attribution_payload": null
}
```

Renderer may apply only approved crop/focal/responsive variants. It must not relabel generic imagery as actual company evidence.

## 10. Integration with existing `photography.py`

Current `photography.py` contains useful renderer helpers but also legacy assumptions:

- `_family_roles(family, category)` derives role packs from a visual family/category;
- `ASSET_SOURCE_PRIORITY` is source-type-based;
- approval is simplified to `RESEARCH_APPROVED_*` values;
- `select_asset_for_role()` primarily chooses by role/source priority.

Implementation direction:

### Retain/adapt

- `render_photo_asset()` rendering mechanics;
- local binary resolution + hash verification concept;
- `guard_fake_evidence_copy()` safety intent;
- role-to-composition binding concept.

### Replace/deprecate as Production authority

- `_family_roles()` as role inventory authority;
- `RESEARCH_APPROVED_FREE_STOCK` / `RESEARCH_APPROVED_GENERATED_VISUAL` as sufficient Production rights gates;
- source-type priority as the primary selector;
- first matching role asset selection.

New Media Role request should come from frozen CompositionPlan scene intent + current-industry role contract, not identity/category→fixed role pack.

## 11. Automated QA

Required tests:

### Schema / ingestion
- required metadata complete;
- enums valid;
- source/detail URL and license reference present;
- binary SHA required before Production;
- stale/revoked assets excluded.

### Rights
- unknown rights fail closed;
- commercial-use blocked fails;
- generic stock cannot satisfy actual-company evidence placement;
- official-site-only asset cannot enter reuse pool;
- attribution-required asset fails when target placement cannot carry attribution;
- person/trademark conditional cases route to review.

### Selection
- same inputs/catalog/usage ledger → same asset;
- no random selection;
- category mutation with frozen authored inputs changes only candidate pool, never Family/topology;
- scarcity leaves Family unchanged;
- no rights-safe candidate returns explicit fail/review state;
- reuse penalty changes asset choice only within allowed pool.

### Anti-template
- same hero blocked inside one generation batch;
- same role/crop repetition surfaced;
- asset bundle cloning surfaced;
- same-Family structural divergence from Issue #99/#103 remains intact.

### Rendering / browser
- exact selected binary hash appears in trace;
- no broken image;
- no destructive crop;
- required attribution visible when applicable;
- all 9 widths: `320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440`;
- 320px semantic text regression lock preserved;
- screenshot manifest includes selected asset ids + hashes.

## 12. Production fixtures for implementation

Start with the Issue #99 current-industry completion fixtures B1-B3 / H1-H3 / P1-P3.

Add asset-specific negatives:

- unknown license;
- source URL missing;
- commercial use prohibited;
- person release/endorsement risk;
- trademark/logo risk;
- illustrative asset forced into factual evidence slot;
- stale binary hash;
- hero reuse collision in same batch;
- empty category role pool.

Expected: explicit fail/review states, Family unchanged.

## 13. Minimum acquisition gate

Use:

- `minimum_current_industry_asset_inventory_matrix_v1.json`

Counts refer to distinct approved binaries. Architecture-validation media does not count.

Acquisition order:

1. Core: skincare/cosmetics product, hair salon, barber, Pilates studio;
2. adjacent current-scope categories;
3. multi-company batch-diversity calibration;
4. then Real-image Sales Sample QA may start for a category that meets its gate.

## 14. Human-visible Aoi boundary

CI is not enough. Aoi must inspect actual selected images and 9-width screenshots for:

- image/brand/company misidentification risk;
- stock-photo obviousness;
- human plausibility;
- category/scene semantic fit;
- crop quality;
- hero/media rhythm;
- same-category repetition/template smell;
- misleading result/staff/store perception;
- mobile optical quality;
- overall LP authorship continuity.

Aoi PASS at this stage validates the **asset-library Production integration** only. Real-image Sales Sample QA remains a later explicit Hard Gate.

## 15. Definition of implementation-ready

Rin may begin implementation after Sarah accepts Issue #104 when all of the following remain true:

- current industries only;
- CompositionPlan/Family authority untouched;
- rights metadata/gate implemented fail-closed;
- generic-vs-evidence boundary machine-enforced;
- deterministic role selection implemented;
- usage ledger and anti-reuse checks implemented;
- provenance trace survives renderer;
- minimum inventory acquisition path exists;
- Issue #99/#103 Production regression lock retained;
- Aoi review is planned on actual screenshots.
