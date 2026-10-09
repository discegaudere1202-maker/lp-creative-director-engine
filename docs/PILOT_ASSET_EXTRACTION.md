# Local original-image extraction

`extract_pool_originals()` connects an already received original-image ZIP to
the existing pool-selection input. It retrieves only explicitly requested
asset IDs, preserving image bytes and the complete source records.

```python
from lp_engine.pilot_asset_extraction import extract_pool_originals
from lp_engine.pilot_asset_selection import build_preview_asset_selection

retrieved = extract_pool_originals(
    pool,
    asset_ids=selected_asset_ids,
    archive_files=received_local_archives,
    output_dir=new_private_directory,
)
selection = build_preview_asset_selection(
    pool,
    placements=explicit_placements,
    local_files=retrieved["local_files"],
    context=original_context,
)
```

`pool` comes from `load_landscaping_pool()` with its known source hash.
`archive_files` maps exact recorded archive names to absolute local ZIP paths.
Supply exactly the archives needed by the requested IDs. The existing source
catalog stores archive names as `file` or `name`; the extractor retains that
rule and rejects conflicting names or duplicate archive rows.

The output directory must be new, with an existing parent. Archive and output
paths must not follow symlinks. The function checks the existing pool seal,
the record/storage/archive relationship, archive byte count and SHA-256, and
then reads the same verified byte snapshot as a ZIP. It does not reread the
path to obtain potentially different contents.

Each requested member must have a safe relative path and exactly one matching
ordinary-file entry, without a duplicate or case alias. Encrypted members,
links, directories and other special entries are rejected. The recorded
member size is checked before decompression. Its actual bytes and SHA-256,
image decoding, supported format (JPEG/PNG/WEBP) and dimensions must match the
source record. Unrequested members are not extracted; this is not a complete
audit of all other ZIP members.

Validated images are saved under `assets/` using their original member
basenames. Colliding output names are rejected. Files are read back to verify
the written bytes. A write failure removes only the newly created output
directory; an output that already exists, including one created during input
validation, is preserved. Input ZIPs and the source pool are never edited.

The returned `local_files` can be passed directly to
`build_preview_asset_selection()`. `extraction_receipt.json` retains each full
source record and archive record beside the new local path and observed byte
check. Historical `local_original` and storage-receipt fields remain as they
were; the current retrieval result is a separate record.

This is `ARTIFACT_ONLY`, with quality `NOT_RUN`, no formal Stage/Gate receipt
and `production_ready=false`. Extraction does not select or adopt an image.
Even an explicitly requested rejected candidate retains its rejection; the
existing selection function still rejects it. Role suitability, disclosures,
near-duplicate rules, rights, full-resolution visual review, crop review and
publication conditions remain the responsibility of the existing selection
and production processes.

There are no network requests, remote downloads, automatic searches or image
transformations. No missing or inaccessible original archive is repaired or
declared received by this function. Actual source indexes, archive IDs,
private paths and extracted originals belong in private task data, not Git.
