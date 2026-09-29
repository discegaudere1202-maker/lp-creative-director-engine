# Phase 2.1 Gold Evidence Recovery — Review checkpoint

**Status: `PHASE_2_1_GOLD_EVIDENCE_READY_FOR_PM_REVIEW`.** This is a 20-reference evidence audit for Sarah, with temporary screenshots and scoped visual scores. It does **not** promote any reference to Strong or authorize the remaining 80 references or the 2,600 Universe.

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
| Evidence-backed scoped scores | 20 / 20, entry + first scroll only |

Evidence: [GitHub Actions capture artifact](https://github.com/discegaudere1202-maker/lp-creative-director-engine/actions/runs/36541693976/artifacts/11020298341), run 36541693976, artifact 11020298341. ZIP digest: `sha256:174da4d8f46e48ad20b3aeecde3e42fdd02e9bea48bf78c2dfa3d5b434edfcb5`. The artifact expires 2026-10-29 08:19:47 UTC. Screenshot hashes in `gold_snapshots.jsonl` were checked against the downloaded artifact bytes. This is **temporary**, not durable storage.

Matrix coverage is 12 JP / 8 GLOBAL by `market_scope`; the eight global references keep `country=UNKNOWN` rather than a guessed country. Discovery classes: Original Direct 4, Japan Gallery 2, Conversion Gallery 2, Global Gallery 1, Web Grand Prix 3, Awwwards 4, Production Portfolio 1, CSS Design Awards 2, Motion Showcase 1. The pool split is 18 Conversion Industry / 2 Creative Benchmark. These are exactly the existing Pilot selections, not a new source sample.

## Mechanism findings

The 20 candidate records give a reference, exact Hero/Entry scene ID, crop, observed job hypothesis and mobile rule. The candidate count is deliberately limited to entry scenes that were linked to real snapshots. `evidence_count` is derived from 20 desktop and 20 mobile sources. P04 Airbnb represents the captured search/category state only; P19 Dior represents the captured country/language gate only. Neither record is used to claim the unobserved accommodation or fashion campaign page. These records are hypotheses, not multi-brand reusable canonical mechanisms. Agency and campaign independence are UNKNOWN.

Concrete examples: P01-R01 shows garden photography and a centered title panel at Hero; P08-R02 places Linear product UI under a large product proposition; P10-R02 shifts Bosch's desktop research image/case card into stacked mobile cards; P18-R01 stacks public notices and topic tiles. P19-R01 loaded Dior's country/language gate rather than a campaign LP, so no luxury campaign mechanism was inferred from it.

The legacy 25 remain frozen. Five have a **possible or partial** Gold overlap for review: `CM-CAND-001` (Stripe logo proof is below rather than leading the Hero), `002` (Sekisui split proposition), `004` (place image suggests two distinct jobs at Ishihara and Aman), `008` (mobile contact is visible but stickiness is untested), and `023` (Shiseido brand rail). The other 20 have no Gold confirmation. These are mapping hypotheses only; none inherits Gold evidence or becomes Supported/Canonical.

## Blockers and risks

1. **Score scope:** Earlier manual dimension vectors were not persisted before the workspace changed, so 20 scores were independently re-reviewed from saved desktop/mobile screenshots. The new raw vectors, source Scene IDs and formula are in `gold_scores.jsonl`; all 100 old scores stay PROVISIONAL_UNAUDITED. The Gold `EVIDENCE_BACKED_FINAL` label applies to observed entry and first scrolled viewport dimensions only. Motion, deep conversion, performance and accessibility remain NOT_OBSERVED. These limited scores cannot rank the full corpus or promote Strong.
2. **Durable archive:** The 118 screenshots and scene crops exist in an expiring Actions artifact. An object-storage archive with verified URI, retention and recapture policy is still needed; all Gold references remain HOLD.
3. **Discovery source precision:** Some earlier Pilot discovery URLs are gallery roots rather than reference-specific listings. The current original URLs are verified, but the discovery provenance remains incomplete.
4. **Runtime risk:** Static screenshots and DOM counts do not test keyboard/focus, reduced motion, animation timing or performance. Those fields stay NOT_OBSERVED, not PASS.
5. **Regulated claims:** Finance rates, beauty language and offer conditions were recorded as claim units, not approved as accurate or compliant. Medical record only asserts no quantified efficacy in the reviewed entry scene, not whole-site clearance.
6. **Crop selector:** Some hero crop selectors returned only a site header. The full viewport screenshots and hash-linked scenes remain the authoritative entry evidence; crop selector improvement is an architecture issue.

## QA and next gate

`validate_phase2_1_gold.py` checks 20 unique slots, 40 viewports, 118 hash-backed snapshots, observed-only mechanism provenance, derived counts, all score vectors and weighted formulas, temporary-archive Strong block, claim/accessibility presence, original 100 Pilot preservation and disabled expansion gates. Seven focused tests pass. Sarah's review should explicitly decide whether the limited score scope and temporary archive are acceptable for the Gold evidence contract. The next 80 and 2,600 remain stopped.
