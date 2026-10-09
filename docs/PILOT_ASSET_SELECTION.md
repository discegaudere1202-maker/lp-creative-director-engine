# Existing photo-pool connection for internal previews

`pilot_asset_selection.py` connects the existing landscape photo index to the
explicit local-image input accepted by `pilot_composition.compose_preview`.
The original DB's classification, adoption state, use restrictions, source
metadata and storage pointers remain unchanged. This is not a new production
contract, rights decision, crop decision, or formal adoption process.

## What is connected

The collected index stores `records`, each with `asset_id`, image hash/size/
dimensions, a `classification` object and original `storage` metadata. The
classification contains `scene`, `usable_roles`, `visual_notes`, recorded fit
text, `excluded_uses`, misattribution instructions and status. These actual
fields are consumed directly. The older `visual_asset_library` module targets
different industries and a different rights schema; its current scope and
required fields are unchanged.

The bridge does not invent missing service/season/focal-point/crop values or
convert the collected records into the more detailed planned photo schema.
Width/height determine only the original image's orientation. They do not
prove PC/SP cropping quality or text readability.

## API

1. `load_landscaping_pool(path, expected_sha256=...)` reads a materialized
   original ZIP or index JSON with an independently known hash. For a ZIP it
   reads `output-196-final/LANDSCAPING_ASSET_POOL_196_INDEX.json`. It retains the
   complete index, including fields the adapter does not interpret, and seals
   both the source identity and loaded snapshot against accidental changes.
2. `rank_landscaping_candidates(pool, industry=..., media_role=...,
   context_terms=..., preferred_orientation=..., used_asset_ids=...,
   used_near_duplicate_groups=...)` returns compatible candidates with each
   literal context match and each exclusion reason. Context terms must come
   from the business/design brief. An industry by itself cannot return a
   default Hero. No matches means no candidates. Exclusion text is not used
   as positive suitability evidence.
3. `build_preview_asset_selection(pool, placements=..., local_files=...,
   context=...)` accepts explicit choices, checks the exact local originals'
   hashes/bytes/decoded dimensions, retains the complete source records and
   returns `images: {slot: {path, sha256}}`. Different slots cannot silently
   reuse one original. It never downloads assets, crops them, or edits images.
4. `attach_preview_assets(composition_input, selection)` copies that mapping
   into an explicitly empty `images` object and preserves the selection in
   `context.asset_selection`. Existing images/context are never overwritten.
   Each declared target part must already contain `ILLUSTRATIVE_DISCLOSURE`
   in its authored `note`; the adapter does not rewrite the author's copy.
   The normal composition text-retention checker then checks the note is
   rendered.
5. After `compose_preview`, call `validate_composed_asset_usage(selection,
   composition_trace)` before handing the preview downstream. It checks the
   preserved selection context, exact selected/rendered slot hashes, and each
   slot's declared target parts against the renderer's actual
   `sections[].image_slots`. A Hero image declared only for FAQ or an undeclared
   reuse in another part is rejected. This verifies static binding only.

Each placement supplies:

```python
{
    "slot": "hero",
    "asset_id": chosen_id,
    "media_role": "HERO_BRAND",   # exact role from the source classification
    "context_terms": ["住宅", "庭"],
    "parts": ["hero"],
    "selection_reason": "事業者の仮説と構成に合う具体的な理由",
}
```

`CONTEXT_LIMITED` candidates are excluded from ordinary ranking. Explicit
limited-context ranking is available; a selected limited record additionally
needs `context_limit_handling`. That text is retained as an unreviewed author
statement, not interpreted as an approval or permission. `REJECT`, source
validation issues, role mismatch and missing context matches are excluded.
The origin's `NONE` duplicate label is not treated as a globally verified
duplicate-group identifier. Caller-supplied recent-use exclusions remain
explicit; this adapter does not itself maintain a production usage ledger.

## Boundaries and remaining work

The bridge supports the observed third-party landscape index only. Requests
for painting/bar fail with `INDUSTRY_POOL_UNAVAILABLE`; no landscape image or
catalog demonstration picture is silently substituted. A source record that
allows company/staff/project evidence is outside this illustrative adapter.

The manifest is `INTERNAL_COMPOSITION_PREVIEW`, `production_ready=false`,
`visual_approval=NOT_ASSERTED`, `crop_validation=NOT_RUN`, and
`rights_reassessment=NOT_RUN`. Original source status is retained separately.
Selecting and decoding an original does not approve it for a real company,
prove ownership/release, confirm current license terms, or clear its individual
LP layout. Existing source exclusions and misattribution rules still apply.

In the observed landscape collection, the full-resolution visual/crop checks
remain a separate task. If source bytes cannot be materialized, the bridge can
complete candidate ranking and a precise missing-original list, but cannot
produce a selection manifest claiming the bytes were checked. It never uses
demo images as a substitute for missing DB originals.

All pool contents, local paths, storage identifiers, business context and
selection manifests belong in private execution artifacts. Only synthetic
fixtures are checked into this repository.
