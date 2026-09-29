# Phase 2.1 Gold Evidence Recovery — Review checkpoint

**Status: IN PROGRESS / HOLD FOR SCORE AND DURABLE ARCHIVE.** This checkpoint is not `PHASE_2_1_GOLD_EVIDENCE_READY_FOR_PM_REVIEW`. It records what is actually recoverable after a Work runtime transition. Do not start the remaining 80 references or the 2,600 Universe.

## Verified recovery

| Item | Result |
| --- | ---: |
| Existing Pilot preserved | 100 / 100 |
| Gold slots | 20 / 20, one per matrix cell |
| Official desktop 1440px captures | 20 / 20 |
| Official mobile 390px captures | 20 / 20 |
| Snapshot records with actual file hashes | 118 |
| Scene records | 80: 78 OBSERVED, 2 NOT_APPLICABLE |
| New evidence-linked candidates | 20, all CANDIDATE |
| Original candidates frozen | 25 PROVISIONAL_FROM_PHASE2 |
| Claim review units | 4 |
| Accessibility records | 2 partial, not PASS |
| Performance records | 9 screenshot/DOM observations; no runtime measurement |
| Strong / Hold / Reject | 0 / 20 / 0 |
| Final audited scores | **0 / 20 — blocker** |

Evidence: [GitHub Actions capture artifact](https://github.com/discegaudere1202-maker/lp-creative-director-engine/actions/runs/36541693976/artifacts/11020298341), run 36541693976, artifact 11020298341. ZIP digest: `sha256:174da4d8f46e48ad20b3aeecde3e42fdd02e9bea48bf78c2dfa3d5b434edfcb5`. The artifact expires 2026-10-29 08:19:47 UTC. Screenshot hashes in `gold_snapshots.jsonl` were checked against the downloaded artifact bytes. This is **temporary**, not durable storage.

## Mechanism findings

The 20 candidate records give a reference, exact Hero/Entry scene ID, crop, observed job hypothesis and mobile rule. The candidate count is deliberately limited to entry scenes that were linked to real snapshots. `evidence_count` is derived from 20 desktop sources and 18 eligible mobile sources. P04 Airbnb mobile and P19 Dior mobile were captured but excluded as sources for their entry mechanisms due to mismatched/obscured target content. These records are hypotheses, not multi-brand reusable canonical mechanisms. Agency and campaign independence are UNKNOWN.

Concrete examples: P01-R01 shows garden photography and a centered title panel at Hero; P08-R02 places Linear product UI under a large product proposition; P10-R02 shifts Bosch's desktop research image/case card into stacked mobile cards; P18-R01 stacks public notices and topic tiles. P19-R01 loaded Dior's country/language gate rather than a campaign LP, so no luxury campaign mechanism was inferred from it.

## Blockers and risks

1. **Score recovery:** Earlier manual dimension vectors were not persisted before the workspace changed. Reusing the old 100 numeric scores would violate Sarah's evidence-backed scoring requirement. All 100 are flagged PROVISIONAL_UNAUDITED; Gold 20 are `EVIDENCE_CAPTURED_RESCORING_REQUIRED`. No corpus ranking or Strong promotion is possible yet.
2. **Durable archive:** The 118 screenshots and scene crops exist in an expiring Actions artifact. An object-storage archive with verified URI, retention and recapture policy is still needed; all Gold references remain HOLD.
3. **Discovery source precision:** Some earlier Pilot discovery URLs are gallery roots rather than reference-specific listings. The current original URLs are verified, but the discovery provenance remains incomplete.
4. **Runtime risk:** Static screenshots and DOM counts do not test keyboard/focus, reduced motion, animation timing or performance. Those fields stay NOT_OBSERVED, not PASS.
5. **Regulated claims:** Finance rates, beauty language and offer conditions were recorded as claim units, not approved as accurate or compliant. Medical record only asserts no quantified efficacy in the reviewed entry scene, not whole-site clearance.
6. **Crop selector:** Some hero crop selectors returned only a site header. The full viewport screenshots and hash-linked scenes remain the authoritative entry evidence; crop selector improvement is an architecture issue.

## QA and next gate

`validate_phase2_1_gold.py` checks 20 unique slots, 40 viewports, 118 hash-backed snapshots, observed-only mechanism provenance, derived counts, temporary-archive Strong block, claim/accessibility presence, original 100 Pilot preservation and disabled expansion gates. Six focused tests pass. **Gold final completion is not asserted** until a reviewer can reproduce per-dimension scores from the screenshots and the archive becomes durable. Then rerun the validator, report 20 evidence-backed final scores, and request Sarah PM review. The next 80 and 2,600 remain stopped.
