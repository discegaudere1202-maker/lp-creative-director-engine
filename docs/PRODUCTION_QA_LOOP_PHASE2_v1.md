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

## Results snapshot

The local static loop produced Gen2 QA PASS for all three fixtures, with zero
manual intervention and three distinct form profiles. Gen1 diagnosis found a
copy-level starting-state bridge issue for each fixture; Gen2 removed that
issue. Real-browser 9-width QA is authoritative in the GitHub Actions run.

Sparse or missing evidence must lower Trust/100万円-value judgment; the Engine
must use visual composition to create clarity, never to imply unverified facts.

## Boundaries

- Safety-approved evidence is the only evidence rendered in Production.
- `RESEARCH_ONLY` facts never reach customer-facing output.
- Trust optimisation remains a research/structured-review responsibility.
- The next phase is Production QA Loop expansion and finalization, not a new
  Golden Sample or Hearing UI.
