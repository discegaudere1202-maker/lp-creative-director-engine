# Phase 4｜Production Operations Contract v1

Phase 4 makes one LP production case a first-class object. The contract is
provider-neutral and persistence-neutral so that a database, API, or future
operations UI can use the same gates.

## Lifecycle

```text
NEW
→ RESEARCH_READY
→ SALES_SAMPLE_GENERATING
→ SALES_SAMPLE_READY
→ HEARING_REQUIRED
→ HEARING_IN_PROGRESS
→ FINALIZATION_READY
→ FINAL_GENERATING
→ CLIENT_REVIEW
→ REVISION_REQUIRED
→ REVISION_GENERATING
→ QA_REVIEW
→ CLIENT_REVIEW
→ APPROVAL_REQUIRED
→ RELEASE_CANDIDATE
→ PUBLISH_READY
→ DELIVERED
→ ARCHIVED
```

`CLIENT_REVIEW → APPROVAL_REQUIRED` is allowed only after an explicit client
review approval. A revision always creates a new Version; it never mutates a
released Version. `DELIVERED` and `ARCHIVED` may receive a new structured
revision request, which starts a new draft lifecycle.

## Project contract

`Project` stores the lifecycle state and operational pointers:

- identity: `project_id`, `client_id`, `company_id`
- state: `project_status`, `current_version`
- generation: `sales_sample_generation_id`, `final_generation_id`
- gates: `hearing_status`, `evidence_status`, `safety_status`, `rights_status`, `qa_status`
- human operations: `client_review_status`, `release_status`, `delivery_status`, `exception_status`
- reproducibility: `rubric_version`, `reviewer_contract_version`, timestamps

Every transition is validated against the declared transition map and writes an
Audit Entry containing the previous state, next state, actor, reason, related
generation, and related approval. Illegal transitions fail closed.

## Artifact and Version registry

The registry records research input, evidence, strategy, IA, copy, art
direction, render spec, HTML, captures, QA, hearing, revision, approval, and
delivery artifacts. Each record may point to a Version and Generation and may
include a content digest.

Versions contain `parent_version`, `generation_id`, `change_reason`, changed
inputs/evidence/sections, and a state. Drafts are mutable by workflow; Releases
are immutable snapshots. `update_release()` always raises an immutable-release
error. A later request must enter the revision workflow.

## Revision workflow

Client text is classified into one of:

`FACT_UPDATE`, `COPY_PREFERENCE`, `ASSET_REPLACEMENT`, `DESIGN_PREFERENCE`,
`STRUCTURAL_CHANGE`, `BUSINESS_CHANGE`, or `OUT_OF_SCOPE`.

The request also records affected section, evidence/copy/visual/scope changes,
Safety impact, Rights impact, and priority. The only path to a new output is:

```text
Revision Request
→ Structured Change
→ Engine regeneration
→ Safety / Rights
→ QA
→ Client review
→ Approval
→ Release
```

Unsupported ranking, guarantee, or absolute claims become
`BLOCKED_PENDING_EVIDENCE`. Image or logo replacements become
`RIGHTS_RECHECK_REQUIRED` and cannot regenerate with unknown rights.

## Approval, release, and publish

Four approvals are required for a Release Candidate:

`CONTENT_APPROVAL`, `DESIGN_APPROVAL`, `RIGHTS_APPROVAL`, and
`RELEASE_APPROVAL`.

Each approval stores scope, approver, source, timestamp, and
`production_validity`. Simulated approvals can only attach to a
`simulation_mode` Project and are labeled `SIMULATED_TEST_ONLY`. They cannot
be used to fake approval on a real fixture.

The Release Manifest snapshots evidence, rights, Safety, QA, approvals, files,
the release Version, and a digest. The deployment adapter separates
`prepare`, `validate`, `publish`, `verify`, and `rollback`. Phase 4 invokes
publish only as a dry run; external production changes, DNS changes, domain
changes, and customer account operations are out of scope.

## Delivery and rollback

Delivery records include the release Version, method, package files, timestamp,
and delivery status. Archive retains the full Project, Artifact, Version,
Approval, Release, Delivery, and Audit history.

Rollback requires a second approved Release, an existing target manifest, and
the target Safety snapshot. The adapter performs a dry-run rollback in Phase 4;
the operation is auditable and does not rewrite the target Release.

## Work queue

`next_action(project_id)` returns the required action, blocking reason, owner
role, and priority. Exceptions include `WAITING_FOR_CLIENT`,
`WAITING_FOR_RIGHTS`, `WAITING_FOR_DOCUMENT`, `QA_FAILED`,
`SAFETY_BLOCKED`, and `APPROVAL_REQUIRED`. No blocked case fails silently.

## Validation scope

`scripts/run_phase4_operations.py` validates:

- Synthetic full lifecycle through Archive;
- safe Revision → Engine regeneration;
- Safety-blocked claim request;
- Rights-blocked asset request;
- QA-failure publication block;
- release immutability and rollback;
- Aoyama and Worsal real-fixture dry runs without synthetic answers or fake approvals;
- static and, in CI, nine-width browser QA.

The Synthetic output remains `NOT_PRODUCTION_APPROVED`. Phase 4 does not publish
an external site.
