# Phase 2B｜Premium Quality Uplift

## Scope

Phase 2B improves the generic Production Engine from a technically valid
Generation 2 loop toward a bespoke, premium sales-sample gate. The change is
not a fixture-specific layout or copy patch. It adds:

- Company Truth → Form Causality Manifest
- independent Art Direction dimensions (composition, type, density, negative
  space, surface, authority, crop, transitions, rhythm and motion)
- Evidence Utility and `premium_without_claim_inflation` for sparse cases
- customer hesitation → resolved uncertainty → reason to act → after-click
  conversion metadata
- a stricter all-check Premium Gate
- a hold-out generation path explicitly excluded from rule selection

Safety-approved evidence remains the only evidence rendered. Client images and
other rights-unclear assets remain excluded.

## Authoritative result

GitHub Actions workflow [35041679631](https://github.com/discegaudere1202-maker/lp-creative-director-engine/actions/runs/35041679631)
completed successfully on commit `31220fdee7696317e4f6349e887105a7d497d022`.
It ran the three existing fixtures through Gen2 and Gen3, then generated the
unseen hold-out. Artifact `phase2b-premium-quality` is ID `10425307001` with
digest `sha256:b6a36e88d2874c25368fd45c41c6209f0a7745b95d66604c095a7ff8a71ea1ae`.

The real-browser QA covered 320, 360, 375, 390, 430, 768, 1024, 1280 and
1440px, with exact 1440×1000 and 390×844 captures. All generated outputs were
Safety PASS and had zero manual intervention. The three existing Gen3 gates
were Chikushi PASS, LOVST PASS and Aoyama HOLD. The unseen hold-out was Safety
PASS, browser QA PASS and sales-sample HOLD. Four distinct generic layout
profiles passed the diversity audit.

The 10-axis structured scores did not numerically increase from the current
control Gen2 run to Gen3, so no numeric uplift is claimed. The meaningful
result is that the Premium Gate and the new manifests make the creative and
conversion requirements auditable; the prior authoritative Phase 2 record had
all three sales-sample gates HOLD. This remains structured-review evidence,
not a real conversion-rate experiment.

## Hold-out provenance

The hold-out is ワーサル福岡校, an action/acrobatics school with an application
goal. Its official site describes the school, instructors, one-on-one lessons,
dedicated facilities, trial pricing and reservation routes; these facts were
used only as a provenance-backed fixture. See the [official ワーサル福岡校
site](https://f-bakuten.com/). Official photographs were not reused because
production rights were not established.

## Gate decision

Phase 2B is `PASS` on the requested minimum technical/premium criteria:

- existing three fixtures remain at least HOLD
- Chikushi and LOVST clear the Premium Gate
- manual LP edit count is 0
- Safety and rights boundaries remain intact
- hold-out remains at least HOLD without rule-selection leakage
- diversity audit PASS
- 9-width browser QA PASS
- Andy and P02/P09/P10 regression PASS

`STRONG PASS` is not claimed: Aoyama and the hold-out are still HOLD, and a
Gen2→Gen3 numerical score uplift is not established.

## Boundaries

Quality Diagnosis supplies generic hypotheses and a structured gate. It does
not determine a universally best CTA, guarantee conversion, or turn sparse
facts into reassurance. If a future change is needed, modify an Engine layer
and regenerate all fixtures; never edit generated HTML, CSS or copy directly.
