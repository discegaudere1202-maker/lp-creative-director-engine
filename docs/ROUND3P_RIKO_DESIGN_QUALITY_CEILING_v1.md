# Round 3P｜Riko Design Quality Ceiling vNext

Status: `RIKO_COMPLETE / SARAH_INTEGRATION_PENDING`

Task SSOT: GitHub Issue #14  
Owner: 璃子（Research / Creative Direction）  
Review owner: Sarah  
Current Nagi screen under diagnosis: PR #12 / HEAD `7d2d071cbbaa427922bc22a509a3cd3f5ce12c64`  
Human reality input: Issue #13 / Round 3O  
Shun final input: Issue #14 trigger = Design / Copy both RETURN

---

## 0. Executive diagnosis

Round 3N / 3O proved that the current gates can verify **presence of intended mechanisms** without verifying the **quality ceiling of the visible result**.

The current Nagi candidate is not failing because it has no art direction. It has art direction. It fails because the art direction remains visibly compressible into a recognizable engine grammar:

- large Japanese Gothic headings
- small English / serial eyebrow labels
- pale mineral green + deep green anchor + warm accent
- fine rules
- tilted translucent planes
- diagonal clipped media
- a repeated centered max-width wrapper
- repeated viewport-height scene pacing

This creates a page that can be described as coherent and intentional while still feeling **designed by the engine before it feels designed for Nagi**.

The key reset is therefore:

> Quality is not `the requested device exists`.
>
> Quality is `the visible decision is resolved at a level where a skilled human would stop noticing the system and start noticing the business`.

Round 3P must move evaluation from **feature / mechanism presence** to **resolution quality**.

---

# 1. Design Quality Rubric vNext

## 1.1 Evaluation state vocabulary

Do not calculate an aggregate design score.

Each axis is judged with one of four anchored states:

### `TEMPLATE_LIKE`
A reasonable implementation exists, but the answer is interchangeable across businesses or visibly driven by system defaults.

### `CRAFTED`
The implementation is clean and deliberate. Local details are handled, but the page can still feel like a competent design system application rather than a singular authored answer.

### `AUTHORED`
The visible treatment is causally connected to this business / customer / scene. Composition, type, image, spacing and rhythm feel selected rather than defaulted.

### `CEILING`
The treatment is both highly resolved and difficult to substitute without losing meaning. Details survive close viewing, whole-page viewing and mobile translation. The system disappears behind the business experience.

`BROKEN` is reserved for floor failures such as overflow, unreadability, broken media, evidence violations or invalid responsive behavior. `BROKEN` is not a design-quality level.

## 1.2 Gate principle

A high-quality page does **not** need every axis at `CEILING`.

It does need:

- no major scene at `TEMPLATE_LIKE`
- no page-wide axis at `TEMPLATE_LIKE`
- business specificity at least `AUTHORED`
- art-direction coherence at least `AUTHORED`
- mobile art direction at least `AUTHORED`
- no late-page drop from `AUTHORED` to `CRAFTED/TEMPLATE_LIKE`
- no unapproved regression against the preserved baseline

A visually spectacular Hero cannot offset a weak late page or weak mobile.

---

## 2. Rubric axes

### DQ-01 Typography craft

Judge:

- whether type role changes by customer / scene job
- Japanese optical line composition
- font-weight, tracking, leading and measure as a relationship, not isolated tokens
- headline/body/label hierarchy
- whether the page relies on one repeated headline treatment
- whether the typography feels like this brand rather than the engine

`TEMPLATE_LIKE` signal:
- one global `h1/h2` treatment repeatedly carries authority
- giant Gothic + tiny English label becomes the visual identity by default

`AUTHORED` signal:
- the typography changes role without losing family coherence
- quiet scenes can be quiet; proof scenes can be precise; entry scenes can carry character

`CEILING` signal:
- line breaks, measures, type scale and surrounding space feel optically inevitable at desktop and mobile

### DQ-02 Spacing / density

Judge:

- whether density follows customer decision difficulty
- whether whitespace has a job beyond looking premium
- whether consecutive scenes have deliberate pressure / release
- whether section height is authored instead of normalized

`TEMPLATE_LIKE` signal:
- repeated min-height / padding / max-width produces the same breathing pattern throughout the page

`CEILING` signal:
- the page can become dense, quiet, compact or expansive without feeling like separate templates

### DQ-03 Visual hierarchy / authority

Judge what the eye notices first, second and third in the actual pixels.

Do not accept an `authority_map` as proof. The screen must visibly enact it.

`TEMPLATE_LIKE` signal:
- every section says it has a different authority, but large headings remain visually dominant everywhere

`AUTHORED` signal:
- information, media, proof, action or silence can each genuinely become primary when the customer decision requires it

### DQ-04 Media selection / crop / integration

Judge:

- why the asset exists
- whether it is evidence, atmosphere, desire, context or identification
- crop specificity
- scale
- edge relationship
- foreground/background integration
- asset quality at rendered size
- whether the media could be swapped with another generic wellness image without loss

`TEMPLATE_LIKE` signal:
- representative media is made to look authored only through the same angled crop / overlay device

`CEILING` signal:
- media and composition are inseparable; removing or replacing the asset materially changes the scene meaning

### DQ-05 Composition

Judge:

- dominant object
- alignment logic
- tension / balance
- containment vs bleed
- edge behavior
- overlap / layering
- negative-space role
- relationship between copy and media

Do not reward a count of composition families. Reward visible necessity.

`TEMPLATE_LIKE` signal:
- different named composition families still share the same wrapper, heading placement, decorative planes and spacing grammar

### DQ-06 Color / contrast

Judge:

- role of color in the customer state
- local contrast hierarchy
- whether color creates material perception, proof clarity or atmosphere
- whether the palette is business-specific or merely tasteful

`TEMPLATE_LIKE` signal:
- pale field / dark anchor / warm accent reads as generic premium-wellness shorthand

### DQ-07 Section rhythm

Judge the whole page before individual scenes.

Look for:

- intensity
- silence
- information load
- image authority
- decision difficulty
- conversion proximity

`TEMPLATE_LIKE` signal:
- visible alternation exists, but the alternation is predictable before reading the content

`CEILING` signal:
- rhythm feels discovered from the decision sequence, including deliberate continuity when a visual change would be noise

### DQ-08 Art-direction coherence

Judge whether the page is one world without becoming the same screen repeatedly.

Key distinction:

- consistency = same world
- sameness = same design grammar

`AUTHORED` requires both coherence and purposeful exception.

### DQ-09 Business / brand specificity

Run the substitution test:

> Remove the name / logo / colors and replace Nagi with a close-category business. What visibly breaks?

If little breaks, specificity is weak even when the screen looks good.

Sources of legitimate specificity include:

- the unusual width of Dry Head Spa / School / Healing
- customer decision differences between receiving / learning / understanding
- actual verified contact reality
- actual evidence boundaries

Color alone is not sufficient causal specificity.

### DQ-10 Authored detail density

This is not the number of details.

Judge whether high-impact surfaces contain resolved micro-decisions:

- edge intersections
- crop endpoints
- label alignment
- line length
- image-to-text distance
- button / link relationship
- section junctions
- mobile optical adjustments

`TEMPLATE_LIKE` signal:
- a strong concept exists, but repeated defaults remain visible in secondary surfaces

### DQ-11 Mobile art direction

Judge mobile as an authored composition, not a responsive proof.

`TEMPLATE_LIKE` signal:
- desktop relationships become vertical stacks
- desktop line chunks are preserved by shrinking type
- media falls below copy everywhere

`AUTHORED` signal:
- order, crop, authority, negative space and CTA proximity are re-resolved while preserving the thesis

### DQ-12 CTA / conversion choreography

Judge:

- whether the page earns the ask
- CTA commitment vs customer readiness
- proximity to resolved objections
- repetition purpose
- visual authority of the action
- ending quality

A styled CTA does not pass this axis by itself.

### DQ-13 Generic-template smell

Hard human question:

> Does the design system show its taste before the business shows its character?

Watch for repeated project signatures:

- giant Gothic
- tiny English serials
- diagonal crop
- translucent tilted plane
- fine rule
- pale / dark field alternation
- same underline CTA

One such device is not a failure. A bundle that becomes the page identity is.

### DQ-14 Screenshot-worthy moments

Do not require spectacle.

Judge whether there are one or more moments where the business idea, information hierarchy and art direction visibly converge into something worth remembering.

A static, quiet composition can qualify.

A decorative hero that cannot explain its role does not.

### DQ-15 Full-page finish

The page is judged as one experience:

- no quality cliff after the hero
- no generic late-page storage
- no unresolved transitions
- no obvious production shortcuts
- no mobile collapse

This axis is the final design-quality synthesis. It cannot be inferred from component PASS states.

---

# 3. Human-visible evaluation protocol

## 3.1 Screen-first

Order:

1. actual desktop full-page render
2. actual mobile full-page render
3. key scene crops
4. only then read strategy / preservation / QA artifacts

A reviewer must not award quality because a contract says a device exists.

## 3.2 Blind comparative check

When a prior approved baseline exists, show baseline and candidate without round names.

For every major scene, record only:

- `CLEAR_GAIN`
- `GAIN`
- `NO_MATERIAL_CHANGE`
- `MIXED`
- `LOSS`

No aggregate score.

Any `LOSS` on a `HARD` or `MATERIAL` preserved element blocks release.

## 3.3 Three viewing distances

Review:

- thumbnail / whole-page: rhythm, hierarchy, sameness, late-page drop
- viewport: composition, authority, scene quality
- close: type, crop, spacing, edge, micro-detail

A page that passes at only one distance is not ceiling quality.

---

# 4. Current Nagi design diagnosis

Target: PR #12 HEAD `7d2d071cbbaa427922bc22a509a3cd3f5ce12c64`.

## 4.1 What should be preserved as principles

The current candidate contains real improvements that should not be casually destroyed:

- customer-state scene separation instead of a generic service-card-only page
- representative media kept non-evidentiary
- layered / tactile visual intent
- a strong dark trust anchor in S6
- late-page scenes with distinct jobs instead of FAQ + CTA-box collapse
- desktop/mobile both have explicit responsive treatment
- the customer-facing route remains the verified official Instagram

These are **preserve principles**, not proof that the current pixels are final-quality.

## 4.2 Why the visible ceiling is still low

### A. Global typography compresses scene roles

The current implementation starts from one global treatment for `h1` and `h2`: large Noto Sans JP, strong negative tracking and similar weight. Scene-specific CSS changes size, but the visual voice remains strongly shared.

This makes the page feel system-authored even where the scene job changes.

### B. Mobile line preservation is achieved partly by shrinking authority

The Round 3N corrective CSS contains a mobile override that forces the Hero heading to `24px !important` while `.line-chunk` uses `white-space: nowrap`.

Technically this can prevent overflow and preserve forced line groups. Human-visibly it demonstrates the wrong priority order: the design protects the authored line chunk by shrinking the most important message.

Browser QA can pass while mobile authority degrades.

### C. Scene pacing is still strongly normalized

Most scenes inherit a shared viewport-height / padding logic and a global max-width wrapper. Scene-specific exceptions exist, but the common skeleton remains visible.

A customer can feel scene variety while still sensing the same production grammar underneath.

### D. Decorative grammar repeats across jobs

Round 3N intentionally restores angled planes, thin lines, off-grid crops and material fields. This solved a previous flattening regression.

The next ceiling problem is that the same vocabulary appears in many scenes regardless of whether the scene job is orientation, desire, learning, ambiguity, trust or action.

The issue is no longer `too little art direction`; it is `art direction with insufficient selective restraint`.

### E. Media integration is better than media authority

S3 / S4 representative media is integrated with crop / bleed / angle rather than card insertion. This is worth preserving.

However, because the media is representative rather than real Nagi evidence, the visible authority must come from exceptional art direction and business-specific relationship to copy. If the same crop grammar would work for another wellness brand, the page remains replaceable.

### F. S2 remains a visible system component

The self-identification scene is useful strategically, but the three-column / stacked state treatment remains one of the most component-like parts of the page. It reads as a clear interaction model before it reads as a singular visual moment.

### G. S6 is strong rhythmically but not sufficient proof

The dark anchor is one of the current page's stronger visible decisions. Preserve the role.

Do not confuse a strong contrast scene with strong trust evidence. The actual information is still intentionally sparse because prices, duration, detailed content and business proof are unknown.

### H. Late page is more authored, but renderer signature remains visible

S7 / S8 avoid generic FAQ storage, which is a gain. Yet fine-line geometry, tilted fields and pale material planes continue the same studio signature. The ending can therefore feel like the system concluding itself rather than Nagi concluding a customer journey.

---

# 5. Benchmark recalibration gap map

This is not a style-reference list. Each reference is used only as a ceiling-calibration anchor.

## Reference A — GORA KADAN FUJI

Current official site: https://www.gorakadan.com/fuji/

Observed transferable ceiling lesson:

- photography carries real asset authority rather than merely filling modules
- information density can fall dramatically when the image already carries place / atmosphere
- late-page modules can stay premium because visual evidence and spatial confidence remain present

Do not copy:

- luxury hospitality tone
- full-bleed resort imagery as a default

Nagi gap:

- Nagi cannot borrow real-place authority, so it needs more selective and higher-resolution art direction where representative media is used
- the current page sometimes compensates for low evidence with repeated design devices rather than stronger scene-specific decisions

## Reference B — SmartHR corporate / service

Current official site: https://smarthr.jp/

Observed transferable ceiling lesson:

- high information density does not require visual flattening when hierarchy, proof, illustrations / media and CTA hierarchy are tightly coordinated
- utility sections remain authored because information roles are sharply differentiated

Do not copy:

- SaaS illustration / rounded UI grammar

Nagi gap:

- current utility scenes still rely on typography + rules + fields with limited evidence variety
- S2/S6/S7 need stronger differentiation in the *relationship* between information and visual hierarchy, not more decoration

## Reference C — SmartHR Recruit

Current official site: https://recruit.smarthr.co.jp/

Observed transferable ceiling lesson:

- company specificity can come from a sustained narrative voice and not only from custom imagery
- late-page functional information can live inside a clear brand voice without reverting to generic corporate templates

Do not copy:

- recruitment narrative or brand language

Nagi gap:

- current Nagi visual voice is more specific than its business voice; the screen grammar is doing too much of the branding work

## Reference D — THE CAMPUS

Current official site: https://the-campus.net/

Observed transferable ceiling lesson:

- physical-world photography, information architecture and identity are treated as one system
- utility pages and experiential pages visibly belong to the same brand without every page using identical composition

Do not copy:

- physical-campus photography or institutional identity

Nagi gap:

- Nagi currently gets coherence through repeated devices; it needs coherence through shared principles while allowing larger scene-specific departures

## Reference E — mount inc.

Current official site: https://www.mount.jp/

Observed transferable ceiling lesson:

- high craft is visible in the relationship among language, typography, media, interaction and composition, not in one signature device
- the brand can change expression across projects / sections while preserving an authored standard

Do not copy:

- agency-portfolio expression itself

Nagi gap:

- current page still risks `agency taste first, business second`
- the renderer should stop using a visible house style as the default answer to uncertainty

---

# 6. Design ceiling rules for the next Rin rebuild

This is a minimum rebuild specification, not an implementation in this task.

## R1 — Start from an approved baseline package

The next Rin task must consume a frozen baseline manifest containing:

- exact candidate HEAD
- exact desktop + mobile screenshots
- exact customer-facing copy snapshot
- approved principles
- rejected signatures
- responsive widths
- evidence/safety state

No rebuild starts from memory.

## R2 — Declare targeted design deltas before code

Every intended change must name:

- target scene / viewport
- current visible problem
- expected human-visible gain
- preserved neighbors
- allowed collateral change
- forbidden collateral change

No `make it more premium` task.

## R3 — Replace global heading authority with scene-role typography

The next implementation must not rely on one global `h1/h2` grammar to carry authorship.

Required outcome:

- hero / self-identification / desire / trust / action / ending are visibly distinct in role
- Japanese line composition remains valid without emergency type shrinking

## R4 — Stop normalizing every scene to one pacing skeleton

Scene height, padding and density can share tokens, but must resolve from scene function.

Do not use viewport-height sameness as a premium proxy.

## R5 — Reduce automatic ornament

Global pseudo-ornament (`before/after`, fine line, tilted plane) must not appear merely because a scene exists.

Each visible device needs a scene-specific reason.

## R6 — Re-resolve S2 as a visual scene, not only a three-option component

Preserve self-identification logic.

Rebuild the visual expression so the scene reads as customer recognition first and component second.

## R7 — Preserve S3/S4 evidence safety while improving media specificity

Keep representative imagery non-evidentiary.

Improve:

- image choice
- crop
- distance
- copy relationship
- mobile crop

Do not compensate by making representative media look like actual Nagi staff / treatment / class evidence.

## R8 — Preserve S6 dark-anchor role, not necessarily its exact pixels

The contrast / trust-authority role is approved as a principle.

Its typography, spacing and internal composition may be improved.

## R9 — Late page must receive the same quality ceiling as Hero

S7 and S8 must not pass merely because they avoid FAQ + CTA-box structure.

They need authored composition, optical typography and a visually earned ending.

## R10 — Mobile cannot protect desktop syntax at the expense of hierarchy

Forbidden workaround:

- forced no-wrap semantic chunks followed by aggressive type shrinking

Mobile may recompose / rebreak / reposition while preserving meaning.

---

# 7. Explicit approved elements that MUST NOT regress

The next rebuild must distinguish `pixel preservation` from `principle preservation`.

## HARD — must not regress

1. No fabricated Nagi staff / customer / premises / treatment / school evidence.
2. No invented prices, durations, reviews, qualifications, outcomes or Healing effects.
3. Official Instagram remains the verified public contact / reservation route.
4. Japanese semantic line composition floor remains active.
5. No mobile overflow / truncation / inaccessible CTA.
6. Representative imagery remains clearly non-evidentiary.
7. Technical QA across project-required widths remains green.

## MATERIAL PRINCIPLE — must survive, pixels may improve

1. Three service width remains understandable: Dry Head Spa / School / Healing.
2. Customer self-identification remains upstream of forced service commitment.
3. The page keeps meaningful scene differentiation.
4. Tactile / layered visual world can remain, but its exact devices are not sacred.
5. S3/S4 media remains compositionally integrated rather than inserted as small stock cards.
6. S6 retains a material trust / information authority shift.
7. Late-page remains authored and does not collapse to generic FAQ + CTA box.
8. Mobile remains same-thesis / separately resolved composition.

## NOT APPROVED FOR PRESERVATION

The following current signatures are explicitly free to change and should not be protected merely because they passed earlier gates:

- exact current Hero composition
- exact headline type scale
- global giant-Gothic behavior
- tiny-English-label frequency
- repeated diagonal clip-path
- repeated fine-rule decoration
- exact pale-green / dark-green alternation
- repeated tilted planes
- exact S2 card geometry
- `24px !important` mobile Hero workaround
- exact section min-heights

---

# 8. Acceptance criteria for later automated + human QA

## G0 Technical Integrity

PASS only if:

- required viewports render without overflow / truncation
- links function
- assets load
- no console-blocking errors
- semantic Japanese line floor passes

G0 does not say anything about premium quality.

## G1 Safety / Evidence

PASS only if:

- no unsupported business claim
- no representative media presented as actual Nagi evidence
- no lost disclosure where disclosure is required
- verified contact remains accurate

## G2 Copy Quality

Owner: Mio / Sarah integration.

Riko interface requirement:

- actual visible copy is reviewed, not only the copy manifest
- internal production vocabulary and safety-meta prose are not allowed to pass merely because factual

## G3 Design Quality

PASS only if:

- whole-page review has no `TEMPLATE_LIKE` major axis
- Hero, at least one mid-page scene, late-page and mobile first viewport each show `AUTHORED` resolution
- business specificity = `AUTHORED` or stronger
- art-direction coherence = `AUTHORED` or stronger
- mobile art direction = `AUTHORED` or stronger
- no visible renderer signature overwhelms Nagi specificity

## G4 Cross-round Preservation / Regression

PASS only if:

- every declared preserved item is `PRESERVED`
- every changed item maps to an intentional-change entry
- no `INCIDENTAL_CHANGE` touches a HARD or MATERIAL preserve entry
- any visual / copy loss is explicitly resolved before review

`Overall looks better` cannot override a preservation failure.

## G5 Full-page Human Reality

Screen-first, copy-first.

Review actual pixels and actual text in this order:

1. desktop full page
2. mobile full page
3. actual copy as rendered
4. major scenes
5. only then internal artifacts

Required result:

- no obvious quality cliff
- no generic-template smell dominating the business
- copy and visuals feel part of one authored decision system
- the experience is materially stronger than the frozen baseline

## G6 Shun Final

Only reached after G0–G5 pass.

Shun is asked for the owner-level human value judgment, not a list of micro-fixes.

---

# 9. Riko routing recommendation

Riko deliverables for Issue #14 are complete when this document, the regression/preservation contract and the Nagi baseline manifest are present in the task PR.

Next routing:

1. Mio completes Copy Quality Rubric vNext / current-copy diagnosis on the same Issue SSOT or paired PR.
2. Sarah integrates Riko + Mio.
3. Sarah emits one Rin rebuild task with frozen baseline + targeted deltas.
4. Rin rebuilds without incidental regressions.
5. Aoi performs independent screen/copy human reality review.
6. Sarah performs G2–G5 review.
7. Shun receives only a candidate that has passed G0–G5.

No broad Nagi implementation belongs in this Riko task.
