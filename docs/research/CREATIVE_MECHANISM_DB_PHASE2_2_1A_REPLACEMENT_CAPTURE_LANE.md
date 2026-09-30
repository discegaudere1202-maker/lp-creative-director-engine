# Phase 2.2.1A-R — Replacement Capture Lane

## Scope and invariants

This lane adds infrastructure only. It does not select replacement candidates, edit the historical 100-reference pilot, or change mechanism research. The original pilot CSV and `phase2_2_uniform_capture.yml` remain untouched. `phase2600_allowed` is false.

Production input is one JSON object per line in `data/phase2_2_1a_replacement_candidates.jsonl`. Every row must include the replacement identity, failed slot identity, the four exact cell fields, official URL, evidence source roles, and reason. Validation checks the failed-reference ledger and original 100. Any missing field, reused ID, unknown failed slot, exception, or cell mismatch fails closed. Near-cell substitution is not implemented.

The separately committed smoke fixture is explicitly `SMOKE_ONLY`, `production_eligible=false`, and cannot be accepted in approved-batch mode. The smoke URL is an infrastructure target only; it is not a selected replacement and is not appended to any corpus ledger.

## Capture contract

One normal Playwright Chromium context is created for each required viewport: Desktop 1440×1000 and Mobile 390×844. Redirects are followed normally and requested/final URL and main-document HTTP status are recorded. Navigation uses a bounded 30-second timeout and at most one ordinary retry for timeout errors. The script scrolls normally to trigger lazy loading, observes semantic page nodes, captures viewport and full-page images, and uses individually hashed visible tiles if a full-page screenshot fails. Pages exceeding the 30,000-pixel traversal bound fail closed.

HTTP errors, visible security challenges, empty body, viewport mismatch, incomplete traversal, missing image, or missing/mismatched SHA-256 produce a failed capture. No CAPTCHA, WAF, challenge, fingerprint, proxy, alternate protected route, or credential bypass option is exposed. A security challenge is recorded as failure and is never interacted with.

## Evidence and storage status

The capture manifest includes requested/final URL, HTTP status per viewport, UTC capture time, viewport, page and traversal facts, image identifier and SHA-256, capture/failure state, and archive-ingestion state. Output from Actions is a **temporary ingestion package**, not a durable archive. The workflow retains it for 30 days and records run ID, artifact name, artifact ID, Actions-provided digest, and retention in an artifact receipt and job summary. Durable archive ingestion must pin/reverify the package later; no S3 or other archive URI is fabricated here.

The workflow always attempts to upload the manifest and any captures, including on capture failure. Missing package files, missing artifact ID/digest, or failed capture keep the run failed. A failed target is not represented as successful evidence.

## Running

- Pushes to `phase2-2-1a/replacement-capture-lane` touching the lane run the isolated smoke fixture.
- `workflow_dispatch` defaults to `smoke`.
- `approved_batch` consumes only the separately maintained JSONL ledger after candidates have been approved and entered with exact same-cell values.
- Smoke outputs are never production corpus rows.

## Verification

Run `python -m unittest tests.test_phase2_2_1a_replacement_capture`. The GitHub Actions smoke run is the network/browser integration test and must show two successful viewport captures, full traversal, per-file hashes, a primary evidence artifact, and an artifact trace receipt before this lane is considered ready.
