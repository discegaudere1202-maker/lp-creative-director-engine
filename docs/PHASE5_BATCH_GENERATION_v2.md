# Phase 5｜Batch Generation v2

## Result

The Phase 5 rehearsal completed with a successful GitHub Actions run. Stage A
uses 10 items sequentially, Stage B uses 30 items at controlled concurrency 3,
and Stage C uses 100 items at controlled concurrency 5. Every item is processed
through the batch contract and real Chromium browser QA at:

`320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440px`

with exact captures at `1440x1000` and `390x844`.

## Isolation contract

Project, generation, artifact, input, and output-directory identities are
batch-scoped. The registry checkpoints each item and resumes completed items
without regenerating them. Transient errors are retried within a bounded limit;
deterministic Safety/Rights errors are recorded as blocks and are never retried
to bypass a gate.

The rehearsal checks both presence of the item's own identity and absence of
every other fixture identity in its HTML. Failure isolation includes a
deterministic Rights block, a transient generation error, bounded retry, and
completion of unaffected items.

## Quality contract

Each item records the ten formal quality axes, evidence density, conversion
goal, deterministic layout profile, Premium Gate result, and peak count. The
reports retain stage-level quality distribution and browser coverage. Fixtures
are TEST ONLY; no client approval, external publish, DNS change, DM, email,
phone call, or manual HTML repair is performed.

## Evidence

- Workflow run: `35056178123`
- Artifact: `10430243447`
- Artifact digest: `sha256:6e822b61479b9aa786434792de0293eedb85291db1c0622af9767e0249adadff`
- Implementation commit: `0151be9d9c78f9fbff766fb5967a0f42964043d1`
