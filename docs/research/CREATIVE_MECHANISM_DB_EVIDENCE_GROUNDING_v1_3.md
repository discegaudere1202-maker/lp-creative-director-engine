# Creative Mechanism DB — Evidence Grounding Contract v1.3

Status: **EVIDENCE_RECOVERY_IN_PROGRESS**. Sarah PM Issue #143 comment #5885732952 is the review source. v1.2.2 taxonomy, sampling, pool types, retrieval weights and 100-reference Pilot remain unchanged.

## Trace contract

`Reference → Evidence Snapshot → Scene Observation → Mechanism Evidence → Candidate`

- The 20 Gold references are selected from existing Phase 2 rows, exactly one per P01–P20 matrix slot. No new discovery is included.
- Each viewport was captured at 1440px or 390px in the GitHub Actions Playwright lane. Screenshot byte hashes are SHA-256 and are revalidated against the [capture artifact](https://github.com/discegaudere1202-maker/lp-creative-director-engine/actions/runs/36541693976/artifacts/11020298341).
- A Scene stores a reference-specific locator, visible structure, observed facts, viewport, original/final URLs, screenshot ID, scene crop ID, hash and archive locator. A section with no additional scroll range is `NOT_APPLICABLE`.
- Only `OBSERVED` Scenes with a visible Mechanism subject can be a candidate source. Static screenshots never prove animation, keyboard operability or real CVR.
- `source_scene_evidence_ids[]` is the only source for `evidence_count`, reference count and evidence-backed brand count. Unknown agency/campaign independence remains `UNKNOWN`; candidates cannot be promoted to Supported or Canonical in this Pilot.
- Original Pilot scores are `PROVISIONAL_UNAUDITED` for all 100 references and are excluded from ranking and promotion. The 20 Gold score audit remains blocked until dimension-level rescoring is recovered and reviewed.
- `TEMPORARY_CAPTURE` is an actual GitHub Actions artifact locator; no S3 URI is invented. Expiry is 2026-10-29T08:19:47Z. This storage state blocks Strong promotion. Before further rollout, copy and verify screenshots into a durable archive with access and retention policy.

## Safety and missingness

Finance, medical, beauty and offer statements have scene-linked claim units; an unverified term is explicitly marked. Public and medical references have partial accessibility records, never an untested PASS. Motion-heavy pages have screenshot/DOM-only performance observations and no fabricated Lighthouse values. Discovery URLs from the original Pilot are retained, and any generic gallery root must not be treated as a verified reference-specific discovery listing.

## QA and phase gate

Run `python scripts/build_phase2_1_gold.py --artifact-root <downloaded-artifact-directory>` then `python scripts/validate_phase2_1_gold.py --artifact-root <downloaded-artifact-directory>` and `python -m unittest discover -s tests -p test_phase2_1_gold.py -q`. All fields of the 100 Pilot and v1.2.2 config are retained. Remaining 80 and 2,600 Universe remain blocked pending PM review and complete Gold score/archive audit.
