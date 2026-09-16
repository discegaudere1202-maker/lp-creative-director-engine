# Phase 5 Batch Generation Contract v1

Phase 5 extends the Phase 4 Operations reference implementation to multiple
projects. `BatchRegistry` persists a manifest, immutable input snapshots, and
one checkpoint directory per item. `run_batch` validates identity, isolates
processing, supports bounded concurrency, retries only transient failures, and
resumes completed items without regeneration.

Each item receives independent `project_id`, `generation_id`, `artifact_id`,
output directory, safety result, QA result, quality result, and retry audit.
Deterministic Safety/Rights/Input failures are recorded as `BLOCKED` or `HOLD`;
they are never bypassed by retry. External publish, customer contact, and
manual HTML repair are outside this rehearsal.

Stage A uses ten new fixtures sequentially and browser-QA checks every item.
Stage B uses thirty fixtures with bounded concurrency of three. Stage C uses
100 fixtures with bounded concurrency of five. Reports include completion,
quality, evidence density, layout profiles, browser coverage, and hard-gate
invariants. The JSON registry is a reference persistence layer and can later be
replaced by a database without changing the orchestration contract.
