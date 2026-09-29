# Phase 2.2.1 Production Foundation

## Aggregate source contract

The aggregate is calculated only from:

- reference IDs and slot attributes: `creative_mechanism_phase2_2_reference_master.csv`
- viewport and snapshot hash/archive status: `creative_mechanism_phase2_2_snapshots.jsonl`
- scene state and evidence: `creative_mechanism_phase2_2_fullpage_scene_evidence.jsonl`
- observed claims: `creative_mechanism_phase2_2_claim_ledger.jsonl`
- candidate rows: `creative_mechanism_phase2_2_mechanism_candidates.jsonl`
- archive member identities: `creative_mechanism_phase2_2_archive_index.jsonl`

`Reference Master.archive_status` is descriptive legacy data and MUST NOT decide both-viewport coverage. A reference is usable only when both viewport labels have durable snapshot rows with actual archive locator/member and SHA-256. For each row, recompute booleans from the snapshot ledger and join by `reference_id`; derive the Cell, whole-pilot, QA and PM summaries from the resulting aggregate object. Reports must serialize the shared aggregate values rather than independently count.

Current reconciliation found an old Matrix sum of 5 and snapshot-derived sum of 73. Root cause: the old builder summed one master-level archive flag and did not join desktop/mobile snapshots. The corrected generated Matrix is in `creative_mechanism_phase2_2_1_coverage_matrix.csv`; old Phase 2.2 artifacts remain preserved as history.

## Bounded Recovery contract

See `phase2_2_1_capture_recovery_policy.json` for machine-readable limits. A recovery attempt is one ordinary browser retry per reference, with finite waits. Redirect resolution, canonical URL observation, visible-body wait, lazy-load scroll, new ordinary context, and bounded tiled capture are allowed. A captured security challenge is never solved or bypassed. If exact response semantics are not preserved, keep the subtype `UNKNOWN` and stop until a visible response supports the next action.

An unresolved row becomes `FAILED_UNRECOVERABLE`; it stays in the failure ledger. A replacement is a separate new reference that matches all four original cell dimensions and passes every usable-evidence requirement before it increments usable count.

## Atomic mechanism and compatibility contract

Every atomic record points to OBSERVED scene IDs and hash-pinned image members. Its evidence/reference/brand counts are derived from the IDs and reference master. A single independent Reference can only support `PROVISIONAL_VARIANT`. Agency and campaign independence remain UNKNOWN if not evidenced. Screenshot-only interaction and motion are NOT_OBSERVED.

Compatibility is its own evidence claim. Same-page co-occurrence is not sufficient. A recipe solver must reject or hold on an UNKNOWN required edge. Only a verified compatible edge with explicit conditions can authorize a mechanism combination; conflicts and mobile collisions are hard constraints.

## Downstream Scene Spec contract

A Scene Spec includes scene job, input content slots, visual composition, hierarchy, asset and DOM boundaries, desktop/mobile recomposition, CTA/proof placement, constraints, and prohibitions. It is brand-neutral and does not contain copied reference content/assets. When profile evidence is synthetic or compatibility is UNKNOWN, mark the case as a fixture and do not treat it as production ready.

## Gate

Do not set PM-ready until (a) 100 usable references, (b) exact aggregate equality across Master/Matrix/QA/report, (c) capture/replacement evidence is durable and hash verified, (d) evidence-backed compatibility and recipe tests pass for multiple profiles/industries, and (e) actual production renderer accepts the generated Scene Specs. Keep the 2,600 gate false until a later PM decision.
