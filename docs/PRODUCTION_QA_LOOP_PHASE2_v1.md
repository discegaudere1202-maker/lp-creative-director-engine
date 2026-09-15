# Production QA Loop Phase 2

This phase validates that the Production Generation Engine can diagnose its
own first-pass weaknesses and improve the Engine before regenerating output.
Generated HTML, CSS and copy are never edited directly.

## Loop contract

`Fixture → Gen1 → Capture/QA → structured review → quality diagnosis → generic Engine change → Gen2 → re-capture/review`

The review is a deterministic structured role rubric with two declared roles:
Creative / Art Direction and Business Owner / Conversion. It is not an
independent human review and is not a conversion-rate experiment.

## New validation fixtures

| Fixture | Domain | Goal | Evidence signal | Form profile |
| --- | --- | --- | --- | --- |
| 有限会社筑紫興産 | metal fabrication / B2B | quote request | rich | technical_drawing |
| LOVST PHOTO STUDIO | photo studio | reservation | rich | experience_calendar |
| 青山フラワーマーケット | flower retail | purchase | sparse | catalogue_spread |

The facts are drawn from official company pages: [筑紫興産](https://www.chikushi-k.co.jp/),
[LOVST](https://lovstmade.com/), and [青山フラワーマーケット](https://www.aoyamaflowermarket.com/).
Only text facts with Production-eligible provenance are used. Photos and logos
remain out of the generated sample unless rights are confirmed.

## Diagnosis contract

`src/lp_engine/quality_diagnosis.py` emits `quality_diagnosis.json` with issue
type, severity, affected axis/viewport/section, observed problem, root cause,
recommended Engine layer and priority. It may recommend a change but cannot
write to `index.html`.

The first generic calibration is `customer_state_bridge_and_profile_composition`:
Gen2 exposes the starting customer state in supporting copy and uses a
conversion/evidence-driven form profile. It is available to every fixture and
does not branch on company name.

## Authoritative validation

GitHub Actions run [35036544098](https://github.com/discegaudere1202-maker/lp-creative-director-engine/actions/runs/35036544098)
completed successfully on `a169bf59bdf86a70839a328a9b285948c8492587`.
The run installed Chromium and executed the three-fixture Gen1→Gen2 loop with
static and browser QA, 9 widths, exact 1440×1000 and 390×844 captures, then
passed the Andy regression. Artifact `production-qa-loop` is ID
`10423154849` with digest
`sha256:7cde0720a8bbdb21c59bc72b0ac084c17e43ffdd7bb2ca978ac8c089c93dda29`.

Gen1 diagnosis found the same copy-level starting-state bridge issue for all
three fixtures; the generic Engine calibration removed it for Chikushi and
LOVST. Aoyama remains `IMPROVEMENT_REQUIRED` only for sparse evidence, which
is non-blocking and correctly remains visible in the diagnosis. All three
fixtures improved according to the structured review. The strict 100万円
sales-sample gate remains HOLD for all three.

The existing QA workflow [run 35036544072](https://github.com/discegaudere1202-maker/lp-creative-director-engine/actions/runs/35036544072)
also passed as run 374 with 193 tests. P02, P09 and P10 remain regression-safe.

## Boundaries

- Safety-approved evidence is the only evidence rendered in Production.
- `RESEARCH_ONLY` facts never reach customer-facing output.
- Trust optimisation remains a research/structured-review responsibility.
- Phase 2 is HOLD until the deterministic output clears the sales-sample bar
  and the sparse-evidence weakness is improved without reducing diversity.
