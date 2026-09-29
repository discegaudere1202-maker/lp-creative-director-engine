# Phase 2.2 evidence bundle

The complete machine-readable Phase 2.2 ledgers are stored in the six base64 parts under `data/phase2_2_completion_bundle/`. The extracted bundle contains the original CSV, JSONL, JSON, and report files listed in `phase2_2_bundle_manifest.json`, with per-file SHA-256 values.

Reassemble from a checkout:

```bash
cat data/phase2_2_completion_bundle/part-*.b64 | base64 -d > /tmp/phase2_2_data_bundle.tar.gz
sha256sum /tmp/phase2_2_data_bundle.tar.gz
tar -xzf /tmp/phase2_2_data_bundle.tar.gz -C /tmp/phase2_2_data_bundle
```

Verify the bundle hash against `creative_mechanism_phase2_2_bundle_manifest.json`. The archive contains metadata and ledgers only; screenshot/crop binaries remain in the separately pinned durable evidence archives recorded by the archive registry.
