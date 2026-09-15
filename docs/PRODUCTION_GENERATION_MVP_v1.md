# Production Generation MVP v1

Status: **MVP implemented; Andy validation is HOLD at the 100万円価値Gate**.

## Boundary

The MVP is a deterministic, structured baseline. It is not a one-shot HTML
authoring prompt and it does not optimise Trust copy. The stages are:

`Company Understanding → Creative Strategy → IA → Copy → Art Direction → Design Tokens → Composition → Render Spec → Renderer`

`src/lp_engine/production_generation.py` owns the stage contract. The renderer
only receives the generated spec and Safety-approved evidence. It does not
know Andy, and there is no company-name branch or Andy-specific token.

Production input must contain company facts, customer state, conversion goal,
primary objections and the canonical evidence ledger. Production Mode calls
the existing Safety selector before any copy or HTML is written. `PASS` is
required; `HEARING_REQUIRED` and invalid input fail closed. Research and test
outputs are marked `NOT_PRODUCTION_APPROVED`.

## Output contract

Each generation writes stage JSON files, `index.html`,
`evidence_manifest.json` and `generation_manifest.json`. The manifest records
the input digest, engine/renderer versions, Safety-approved evidence,
`claim → evidence_id → source` traceability, Hearing requirements and manual
intervention. A valid MVP generation has `manual_intervention: []`.

## Andy fixture

The new fixture uses public official social sources only for customer-facing
facts:

- [Andy motorcycle official X](https://x.com/Andy_moto_co)
- [Andy motorcycle official Instagram](https://www.instagram.com/andymotorcycle/?hl=ja)
- [Official contact post](https://www.instagram.com/p/C2RAJIGp5W9/)
- [Andy motorcycle official Facebook](https://www.facebook.com/p/Andy-motorcycle-100086583196409/)

Verified facts used are the consultation invitation, Fukuoka Minami-ku /
Wakahisa location and published phone, email and address. No social image is
used because public availability does not establish LP reuse rights. A
third-party Webike listing was retained as `RESEARCH_ONLY` for an experience
claim and is not rendered; it is not treated as Company Truth.

The fixture deliberately leaves official proof of qualifications, detailed
experience, price conditions, response expectation, policies and image rights
unavailable. The engine does not fill those gaps with reassurance. They remain
future Hearing requirements.

## Generation 1 → Generation 2

Generation 1 exposed a generic reassurance sentence that was not backed by an
approved policy evidence record. The improvement changed the generic copy rule
and renderer input to neutral, verifiable contact/process language, and also
corrected the headline line-shape fallback so Japanese words are not split.
Generation 2 was regenerated from the input; its HTML was not manually edited.

## QA and review

`scripts/run_production_qa.py` checks the nine required widths, approved
evidence traceability, unsupported reassurance markers, responsive rule
presence and section count. When Playwright is available it invokes the
existing real-browser QA and captures exact `390×844` and `1440×1000` views.
The GitHub Actions workflow ran this browser QA with Chromium successfully at
Run 3 (`35033983101`) on head
`06f84fb692583cb086ff4d39c3b525a8b6bf8bb7` and uploaded the captures and
manifests as Artifact `10422841297`
(`sha256:553abea8ab9aa5e60c70f3ed81dd53e6f88ec7898a98a5a7d558ae23a689c713`).
The existing LP Engine regression was also successful at Run 371
(`35033983094`).

The reviews in each generation directory are structured review roles only:
Creative / Art Direction and Business Owner / Conversion. They are not claims
of independent human review. Gen 2 is a safe and coherent Production MVP
output, but remains HOLD for the 100万円価値Gate because sparse verified
Company Evidence limits owner accountability, service detail and decision
confidence.

## Responsibility boundary

- Safety: verifies evidence eligibility, provenance, rights and blocked claims.
- Creative stages: select a form from the structured Company Truth and customer
  state; they do not invent facts.
- Renderer: renders the approved spec; it never bypasses Safety.
- Hearing: remains the route for missing facts; no Hearing UI is implemented.

The next roadmap phase is **Phase 2｜Production QA Loop**: use more genuinely
new fixtures, capture the generated outputs in CI, and improve generic stage
rules only when the structured QA identifies a repeatable issue.
