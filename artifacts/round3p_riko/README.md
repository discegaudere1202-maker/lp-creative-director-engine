# Round 3P｜Riko Completion Report

Task: Issue #14  
Owner: 璃子（Research / Creative Direction）  
Status: `READY_FOR_SARAH_REVIEW — RIKO SCOPE`

## Delivered

1. `docs/ROUND3P_RIKO_DESIGN_QUALITY_CEILING_v1.md`
   - Design Quality Rubric vNext
   - screen-first human-visible quality protocol
   - current Nagi design diagnosis
   - ceiling benchmark gap map
   - minimum Rin rebuild specification
   - explicit preserve / non-preserve design decisions
   - G0–G6 acceptance interface

2. `docs/ROUND3P_REGRESSION_PRESERVATION_CONTRACT_v1.md`
   - Targeted Delta + Preserve Baseline contract
   - baseline / preserve / intentional-change / comparison requirements
   - screenshot + semantic-copy diff rules
   - responsive / safety regression rules
   - quality gain/loss ledger
   - cross-specialist handoff rules
   - hard anti-regression returns

3. `registries/round3p_preservation_manifest.schema.json`
   - machine-readable preservation manifest contract
   - HARD / MATERIAL / SOFT preservation levels
   - intentional / preserved / incidental / regression classification
   - release policy that forbids overall-quality override of regression

4. `artifacts/round3p_riko/nagi_preservation_baseline_v1.json`
   - frozen Round 3N Nagi baseline identity
   - 9-width responsive set
   - explicit approved principles that must not regress
   - explicit current engine signatures that are **not** approved for preservation

## Riko conclusion

The current failure is not adequately described as “missing design features.” The quality model was over-rewarding the existence of intended mechanisms.

Current Nagi can have:

- composition families
- scene authority
- layered backgrounds
- representative media
- responsive PASS
- human-review PASS

and still remain below Shun's human-visible quality ceiling because the same renderer / studio grammar is visible across too many decisions.

The replacement quality question is:

> Is this decision resolved so specifically and completely that the viewer notices the business before noticing the system that produced it?

## Highest-leverage current Nagi gaps

- global Gothic headline behavior compresses scene-role differences
- common wrapper / viewport pacing remains visible beneath scene variation
- repeated tilted planes / fine rules / diagonal crop / pale-dark field vocabulary behaves like an engine signature
- representative media is safer and better integrated than older builds, but not yet sufficiently business-specific in authority
- S2 remains component-like
- late-page authorship improved, but it still inherits too much of the same studio grammar
- mobile technical quality can be preserved by type shrinking instead of true mobile hierarchy resolution

## What MUST NOT be lost in the next rebuild

Hard:

- evidence / rights / truth boundary
- official Instagram contact integrity
- Japanese semantic line quality
- no overflow / truncation / broken responsive behavior

Material principles:

- customer self-identification before forced commitment
- meaningful scene differentiation
- representative media remains non-evidentiary and compositionally integrated
- material trust / information authority shift around S6
- authored late-page logic
- mobile is separately resolved rather than mechanically stacked

## What is explicitly free to change

Do not preserve these just because prior gates passed them:

- exact current Hero pixels
- global large-Gothic signature
- tiny English / serial-label frequency
- repeated diagonal clipping
- repeated tilted translucent planes
- repeated fine-line ornament
- exact pale-green / dark-green alternation
- exact S2 card geometry
- forced nowrap + mobile type-shrink workaround
- uniform viewport-height pacing

## QA performed for this research task

- Issue #14 and PM Issue #3 re-read as SSOT / routing contract.
- Current Round 3N PR #12 implementation and Round 3O human-review evidence inspected.
- Round 3N artifact identity re-verified:
  - HEAD `7d2d071cbbaa427922bc22a509a3cd3f5ce12c64`
  - workflow `35889186035`
  - artifact ID `10763863010`
  - digest `sha256:29d39e62a3a93a7b1c7bbb98747c7927ca53e57b3fb8c7accb9933b7e5137a30`
- Preservation schema and baseline manifest re-fetched from the task branch after write.
- No LP implementation was performed in this task.

## Integration still required before Issue #14 is complete

This is the Riko specialization output only.

Still required by the shared Issue #14 SSOT:

- Mio Copy Quality Rubric vNext
- Mio current Nagi copy diagnosis / copy ceiling delta
- Sarah integration of Design + Copy ceilings into one Rin rebuild task

Sarah should not issue the rebuild until both specialties are reconciled into one preserve baseline and one targeted change ledger.
