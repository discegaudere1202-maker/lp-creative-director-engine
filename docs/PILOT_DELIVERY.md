# Checked selected-preview delivery

`pilot_delivery.deliver_selected_preview` connects the existing image
selection, authored P01, static composition, actual-image-use check, and local
artifact receiver in one call. This closes a sequencing gap: previously a
caller could compose a preview and forget to call the image-use check before
handing the files downstream.

## Inputs and result

The caller supplies an original validated P01 brief, explicit company copy,
theme and ordered design IDs, and an already-built image-selection manifest.
The composition's `images` mapping must be empty before attachment. The source
bundle's previously recorded SHA-256 is mandatory for this connection. No
candidate ranking, theme selection, image download, or copy generation occurs.

```python
from lp_engine.pilot_delivery import deliver_selected_preview

result = deliver_selected_preview(
    private_p01_brief,
    explicit_composition,
    explicit_asset_selection,
    source_root=trusted_materialized_source,
    expected_source_sha256=recorded_source_bundle_sha256,
    receiver_dir=private_receiver_directory,
    revision=existing_package_revision,
    expected_revision=expected_package_revision,
    handoff_context=existing_handoff_context,
    expected_context=expected_handoff_context,
)

receipt = result["artifact_receipt"]
received_preview_directory = result["preview_dir"]
```

Handoff context and expected context are caller-supplied objects. They may be
empty when the existing handoff does not have such metadata. Their keys are
not renamed, overwritten, or made into new formal Stage requirements. The
receiver still checks every supplied expected-context entry and the explicit
expected revision using its existing rules.

## Mandatory order within the call

1. Attach the sealed selection with `attach_preview_assets`. Existing images,
   a replaced selection context, and missing authored image disclosures are
   rejected by the existing adapter.
2. Preserve the entire original P01 with
   `build_authored_composition_input`. Its original-snapshot validation and
   industry match run before composition. Internal hypotheses remain context;
   they do not become displayed company copy.
3. Run `compose_preview` with the caller-pinned source in a fresh private
   temporary producer directory. Image bytes are rechecked against the
   selection's original hashes. There is no browser or network operation.
4. Run `validate_composed_asset_usage` against the actual image slots and
   rendered sections. A declared FAQ placement actually used in Hero, or an
   undeclared reuse, fails before any receiver call.
5. Save `asset_usage_check.json` beside the original three composition files.
   Build a fixed four-file handoff manifest. Compare its pins with the checked
   input, returned trace, HTML pin and saved image-use result, so a staged file
   changed before pinning is not silently accepted as a fresh artifact.
6. Call `receive_artifacts` only after these checks. Its existing copy-time
   hash check, immutable receipt, and idempotent delivery behavior are retained.

The received files are exactly:

- `index.html`
- `composition_input.json`
- `composition_manifest.json`
- `asset_usage_check.json`

The full brief and selected image-source records remain in the composition's
preserved context. The usage file records the selection-manifest hash and the
actual slot/part bindings. The artifact receipt pins all four files together.
Original source paths, field wrappers, publication policies, conditions, and
quality states are not rewritten.

## Failure and retry behavior

The optional `staging_parent` must be an existing directory; otherwise the
system temporary directory is used. Every call creates its own private child
directory. A validation or transfer failure cleans only that call's temporary
producer directory. It does not delete or overwrite any previously received
preview, historical receipt, source file, or user directory.
The temporary producer and receiver must be disjoint after resolving aliases;
equal paths and parent/child overlap are rejected before rendering or receipt.

There is no separate completed producer directory to promote. The successful
receiver directory is the completed artifact output. Missing images, missing
source files, a wrong source pin, changed P01 or selection contents, or failed
image-use checks never issue a new receipt through this connection.

To retry, call the same function with the same original inputs, paths, package
revision and handoff metadata. Temporary producer paths are not embedded in
the generated files, so identical inputs produce identical delivery pins. The
existing receiver then verifies the supplied bytes and stored copy and returns
the exact first receipt. A changed source path, content or metadata legitimately
changes delivery identity or fails validation; this API does not merge jobs or
invent a replacement history. If the receiver itself is interrupted after
installing a complete delivery, its existing orphan-recovery behavior applies.

## Scope

The result remains `INTERNAL_COMPOSITION_PREVIEW`, `quality_status=NOT_RUN`,
and `production_ready=false`. The receipt remains `ARTIFACT_ONLY`, with
`stage_receipt_issued=false`. The image-use result is static binding evidence;
it does not approve appearance, PC/SP cropping, current rights, company truth,
formal P14 direction, or production completion. The observed photo adapter is
still landscape-only. Missing painting/bar pools or real image originals are
not replaced with catalog demo images.

All business inputs, image-source records, local paths and generated artifacts
remain private execution material. This repository contains only synthetic
tests. See [PILOT_ASSET_SELECTION.md](PILOT_ASSET_SELECTION.md),
[PILOT_PIPELINE.md](PILOT_PIPELINE.md), and the existing artifact handoff module
for their unchanged contracts and limits.
