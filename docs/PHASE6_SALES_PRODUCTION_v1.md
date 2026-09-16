# Phase 6 Sales Production Contract v1

## Scope
Connect the read-only Sales Master to the existing Production Engine, Safety,
Browser QA and Operations-compatible project/package identifiers.

The committed master snapshot is an input artifact only. The original workbook
is not mutated. Candidate processing and production generation are separate:
excluded or stale candidates produce a blocking record and never reach the
renderer.

## Gates
1. Freshness and identity must be checked.
2. Web Gate must be PASS_WEAK_WEB for ordinary sales production.
3. Contact routes are copied only when public and verified; values are never inferred.
4. Evidence is sourced from the candidate's official source and is tagged for the
   candidate scope.
5. Every generated candidate owns project_id, generation_id, package directory,
   screenshots, QA, evidence, contact, hearing and draft artifacts.
6. Preview mode is LOCAL_PREVIEW/private only. No send and no public deploy.
7. Duplicate candidate rows are deduplicated by name, source and location.
8. Contamination audit rejects foreign candidate identities in package text.

## Stage policy
- Stage A: 10 candidates, sequential baseline.
- Stage B: 30 candidates, concurrency 3.
- Stage C: 100 candidates, concurrency 5.
- The 100 candidate population includes valid, hold and excluded master rows;
  100 candidates does not mean 100 LPs.

## Deliverables
manifest.json, research.json, production_input.json, generated LP,
evidence.json, qa.json, contact, sales readiness, hearing plan, draft and
private screenshot peaks.

## External-action boundary
external_sales_execution = 0, external_production_publish = 0, and
manual_lp_edit = 0 are hard gates.
