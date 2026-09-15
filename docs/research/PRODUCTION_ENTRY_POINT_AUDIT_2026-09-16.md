# Production Entry Point Audit｜2026-09-16

## Scope

This audit closes the path from raw company evidence to customer-facing
production output. It does not automate Trust Optimization or generate copy.

## Entry point inventory

| entry_id | file / function | input | production capable | safety | bypass risk | action |
| --- | --- | --- | --- | --- | --- | --- |
| EP-01 | `src/lp_engine/cli.py:main` | project JSON + optional safety JSON | yes | mandatory by default | CLI flag omission | omission now fails closed; `--mode research/test` is explicit |
| EP-02 | `src/lp_engine/pipeline.py:run_pipeline` | creative specs + safety spec | yes | mandatory in `production` | direct API call | default mode is `production`; no safety input is `PAGE_BLOCK` |
| EP-03 | `src/lp_engine/pipeline.py:run_production_pipeline` | creative specs + safety kwargs | yes | mandatory | wrapper misuse | explicit production wrapper delegates to the mandatory path |
| EP-04 | `src/lp_engine/evidence_safety.py:evaluate_evidence_selection` | objection + Evidence Ledger | selection layer | production clearance switch | raw record injection | provenance, verification, rights, usage and objection match are checked |
| EP-05 | `scripts/run_evidence_safety_dry_run.py` | research target fixtures | no | research only | confusing research output with delivery | output is marked research-only and is not a production page |
| EP-06 | `src/lp_engine/client_evidence.py` | evidence slot contracts | no direct claim output | contract/schema | treating a slot as evidence | slots remain requirements; verification is still required |
| EP-07 | `scripts/generate_evidence_selection_variants.py` | prototype HTML fixtures | no | research fixture | benchmark/prototype confusion | remains outside Production mode |
| EP-08 | capture workflows | HTML + capture config | no claim export | `contents: read` | artifact mistaken for production output | capture artifacts remain QA evidence only |

No separate batch renderer, template copy exporter, or customer-facing export
path exists in the repository. The only implemented Production-capable engine
entry is the CLI/Pipeline path above; future batch callers must use the same
Production mode contract.

## Mode boundary

- `production`: Safety input is mandatory. Only `ELIGIBLE` or
  `PRODUCTION_ELIGIBLE` usage records can enter the manifest.
- `research`: research evidence may be inspected, but report output is
  `NOT_PRODUCTION_APPROVED`.
- `test`: fixtures may be used for tests, but are never delivery evidence.

## Fail-closed scopes

- `CLAIM_BLOCK`: a requested unsupported claim is removed while independently
  safe evidence may continue.
- `SECTION_HOLD`: a primary objection has no eligible evidence and routes to
  `HEARING_REQUIRED`.
- `PAGE_BLOCK`: missing Safety input, invalid input, or selector failure prevents
  Production output entirely.

## Invariant

Every item in `production.evidence_manifest` must be emitted from the
Safety-selected eligible records and retain:

`claim → evidence_id → source → verification_status → rights_status`

The pipeline never accepts a raw customer-facing claim as approved evidence.

## Bypass audit

The anti-bypass suite covers Safety omission, raw unsupported claims,
missing provenance, unknown rights, malformed Ledger, selector exceptions,
non-primary missing evidence, legacy Ledger normalization and manifest
traceability. The expected Production bypass count is zero.

## Responsibility boundary

- Safety: eligibility, provenance, verification, rights, usage status and
  hearing routing.
- Creative: visual form, hierarchy, copy presentation and responsive art
  direction using approved evidence only.
- Trust Optimization: evidence effectiveness and sequence research; not
  automatically decided by this integration.

## Open risks

Live conversion, stale-source policy and conflicting official evidence remain
review workflows rather than automatic truth resolution. The conservative
fallback is `HOLD` / `HEARING_REQUIRED`.


## Production E2E

The E2E suite exercises five named cases (P02, P09, P10, 森人 and
INDEPENDENT_KOKORO_SEITAI) through the actual Pipeline entry. Positive
fixtures produce a traceable manifest. Negative fixtures verify that
unsupported claims are omitted, while missing provenance or unknown rights
produce no Production manifest. Research-mode output remains explicitly
`NOT_PRODUCTION_APPROVED`.
