# Hearing / Finalization Architecture v1

Phase 3 closes the path from a Sales Sample to a formally completable LP. It is
not a client questionnaire UI and it does not contact a real company.

## Contract

`Sales Sample Report → Evidence Gap Analysis → Hearing Plan → Answer Intake → Evidence Candidate → Verification / Provenance / Rights → Conflict Detection → Safety Re-check → Finalization Spec → Engine Regeneration → Final QA`

The existing Sales Sample creative direction is preserved. Finalization adds
verified evidence; it does not rescue a weak concept or authorize direct HTML,
CSS, or copy editing.

## Real-company boundary

Aoyama and Worsal are run in `production_public_evidence_only` mode. Their
current gaps become Hearing Plans and `FINALIZATION_BLOCKED` remains the honest
status. No client answer is fabricated and no official-site image is assumed to
be reusable.

## Question planning

The planner receives explicit Production requirements plus the canonical Safety
report. A question is emitted only when the requirement is needed, missing and
relevant. Questions are deduplicated by `answer_group`, ranked by P0–P3, and
annotated with `expected_information_gain`, `question_cost`, evidence targets,
affected section, verification class, and requested asset.

## Answer completion

Every answer starts as `UNVERIFIED_CUSTOMER_INPUT`. It becomes a candidate only;
it never becomes copy directly. Promotion requires provenance, verification,
rights, and the canonical Safety selector. Vague answers, unsupported claims,
unknown rights, and conflicts stay blocked or on hold.

Synthetic answers are accepted only in `test` / `simulation` mode and final
outputs from that path are `TEST_ONLY` / `NOT_PRODUCTION_APPROVED`.

## Finalization statuses

- `FINALIZATION_BLOCKED`: a blocking gap, unresolved claim, conflict, or Safety
  gap remains.
- `READY_FOR_FINALIZATION`: all required evidence passed completion and the
  Safety re-check returned `PASS`.

`finalization.py` emits a `finalization_spec_v1` containing newly approved
Evidence IDs, unlocked claims/sections, asset upgrades, remaining blockers and
the zero-manual-intervention invariant.

## Future App contract

An eventual UI may render the schema, questions, answer controls, asset request
briefs and progress. It must not decide Production eligibility in the browser;
all answers must return through Evidence Completion and the mandatory Safety
Gate.

## Validation

See `data/phase3_hearing_finalization_validation_v1.json`. The Synthetic
round-trip and CI browser QA pass at all required widths; Aoyama and Worsal
correctly remain blocked without real client evidence. This is structured
engine validation, not real conversion or client approval evidence.
