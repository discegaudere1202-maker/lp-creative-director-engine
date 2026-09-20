# Round 2H-C
# Nagi Selected Hybrid Final Creative Specification

Status: Creative specification only / implementation STOP

Repository: `discegaudere1202-maker/lp-creative-director-engine`

Starting reference: `04f44e5a060b8a9f0ffc6132c021d7a3bd1660ec`

Selected hybrid:

- Creative Core: `B / BEFORE TOUCH`
- Routing: `A / ENTRY MAP`
- Clarity: `C / OPEN SERVICE NOTE`
- Final thesis: `HUMAN TRUST × SERVICE CHOICE × RADICAL CLARITY`

This document does not modify renderer code, CSS, HTML, assets, workflows, or dependencies. It is the handoff specification to be reviewed by Shun before any Rin implementation.

## 1. Final Creative Thesis

「人に触れられるサービスだからこそ、予約する前に、誰・何・どれ・どうするかを分かる状態にする。」

The page is not a generic relaxation advertisement. It is a calm, exact decision surface for three different ways into Nagi no Mirai: receive, learn, or discuss healing. Human presence creates trust; service routing creates choice; explicit information creates premium authority.

## 2. Selected Hybrid Definition

| Layer | Adopted principle | Visible consequence |
|---|---|---|
| B / BEFORE TOUCH | Detail → person → boundary → first step | A touch image never appears without human context and service boundary nearby |
| A / ENTRY MAP | One → three | The first view establishes that this is not only a head-spa treatment site |
| C / OPEN SERVICE NOTE | Question → answer | Price, duration, process, qualification, and booking remain replaceable but structurally visible |

The hybrid is not three equal cards, a color-coded menu, or a poetic spa story. It is a guided decision sequence.

## 3. Company Truth Used

### Confirmed and safe to use

- Business name: なぎのみらい
- Area: 福岡市
- Service modes: ドライヘッドスパ / ヘッドスパスクール / ヒーリングサロン
- Business role: a consultation / reservation entry for those three modes
- Official entry: official SNS, Instagram `@happyfuture_02`
- Repository SSOT: `data/photography/nagi_no_mirai_asset_selection_v1.json`

### Unknown and therefore replaceable, not invented

- Founder, staff, instructor, therapist identity
- Qualifications and experience
- Treatment method and exact treatment boundaries
- Price and duration
- Detailed address and opening hours
- Actual room, people, tools, and school setting
- Reviews
- School curriculum and healing details
- Final booking mechanism beyond the official SNS entry

Generated and stock visuals remain explanatory context only. They are not Nagi evidence, staff portraits, room records, treatment records, or testimonials.

## 4. Creative Problem

Nagi no Mirai has three different service intentions but the current public evidence does not yet show enough of the person, boundary, process, or transaction for a first-time visitor to decide what to ask for before being touched, taught, or invited into a healing service.

The specification must therefore make uncertainty legible without making the page feel unfinished.

## 5. Sales Sample State

The sales sample must be a complete creative experience using only safe facts, safe generated/stock context, typography, diagrams, service routing, and explanation.

Visual framing:

- People are labeled through composition and caption as representative experience imagery, never as owner/staff/instructor/therapist.
- Rooms are presented as service-context imagery, never as Nagi's actual room.
- No fake certification, price, duration, review, address, or treatment promise.
- One concise group note may state that people, rooms, and treatment visuals are reference visuals for explaining the service; repeated warning badges are forbidden.
- Every unknown has a designed slot, not a fake value and not an empty hole.

Sales sample quality target: coherent, intentional, premium, and usable as a direction sample. It must not look like a placeholder LP.

## 6. Final Production State

After hearing and evidence collection, replace slots without rebuilding the layout:

- Actual founder/staff portrait and identity
- Actual treatment hand/detail and distance photographs
- Actual room and preparation photographs
- Actual school, instructor, material, and learning photographs
- Verified qualifications and experience
- Verified price, duration, process, review, address, hours, and booking route
- Verified definition and boundary of healing service

The final state should improve evidence fidelity from approximately 85–90% to 100% while preserving the same information architecture and creative grammar.

## 7. Evidence Replacement Architecture

| Role | Sales sample asset | Final replacement | Ratio / crop | Risk | Mobile behavior |
|---|---|---|---|---|---|
| PERSON | Safe representative human context | Actual founder/staff portrait | 4:5 or 3:2; eyes/distance intentional | Fake identity | Portrait becomes first trust block |
| TOUCH | Safe hand/head context image | Actual treatment hand/detail | 1:1 or 4:5; no face-only crop | Implied medical efficacy | Detail precedes person, never alone |
| DISTANCE | Two-person conversation illustration | Actual first-visit conversation | 3:2; retain space between people | Fake consultation claim | Full-width chapter |
| PROCESS | Diagram: before / during / after | Actual arrival-to-treatment sequence | 3:2 sequence | Invented steps | Vertical numbered sequence |
| LEARNING | Safe hands/material context | Actual class/instructor/materials | 4:5 or 3:2 | Fake teaching evidence | One image, then facts |
| SPACE | Generic non-identifying quiet interior | Actual room | 16:10 or 3:2 | Fake Nagi room | Crop-safe background |
| CHOICE | Typography / route map | Verified menu or service-selection image | 1:1 / diagram | False menu detail | Intent selector stays textual |
| PREPARATION | Neutral arrival/context still life | Actual preparation scene | 3:2 | Generic spa signal | Optional, never hero |
| MATERIAL | Neutral non-branded material | Actual tools / class material | 1:1 | Implied technique | Secondary detail |
| REST | Safe abstract rest context | Actual post-service context if available | 3:2 | Benefit overclaim | Use only as atmosphere |

## 8. Hero Final Specification

### Role

The hero must answer in one second: this is なぎのみらい in 福岡市; it includes head spa, school, and healing; a human choice can be discussed through the official SNS.

### Topology

Desktop: editorial split, not a full-bleed spa card. Left is a human-context visual field with a visible distance cue; right is a structured information field containing brand, what, service existence, and next action. A compact `ONE → THREE` route line crosses the seam.

Mobile: human context first, then a short service-intent selector, then the CTA. Do not stack a desktop two-column layout mechanically.

### Hero elements

- Brand: なぎのみらい
- Area / what: 福岡市｜ドライヘッドスパ・スクール・ヒーリング
- Human trust theme: 触れられる前に、選べる
- Service existence: 受ける / 学ぶ / 相談する
- Primary action: 公式SNSで相談する
- Secondary action: どれが合うか見る

### Hero image rule

The first image shows human context and distance rather than a hand close-up. If a detail image is used, it must be paired in the same visual field with a non-identity caption and an adjacent explanation of what is and is not known.

### Hero line composition

Recommended desktop composition:

```
予約する前に、
分かっていたいことを、先に。
```

Recommended mobile composition:

```
予約する前に、
分かっていたいことを
先に。
```

No isolated particle, verb, or single-noun line. The final choice among the five finalists remains with Shun.

## 9. Hero Copy Finalists

All candidates are proposals, not additional Company Truth.

### Candidate 1 — clarity-led

- Main: `予約する前に、分かっていたいことを、先に。`
- Supporting: `なぎのみらいは、福岡市でドライヘッドスパ・ヘッドスパスクール・ヒーリングサロンの入口を案内します。`
- Service line: `受ける｜学ぶ｜相談する`
- CTA: `どれが合うか相談する →`

Desktop: `予約する前に、` / `分かっていたいことを、先に。`
Mobile: `予約する前に、` / `分かっていたいことを` / `先に。`

### Candidate 2 — human-first

- Main: `触れられる前に、話して選ぶ。`
- Supporting: `誰に、何を、どの入口から相談するか。なぎのみらいの三つのサービスを開いて見せます。`
- Service line: `ドライヘッドスパ｜スクール｜ヒーリングサロン`
- CTA: `まず相談する →`

Desktop: `触れられる前に、` / `話して選ぶ。`
Mobile: `触れられる前に、` / `話して選ぶ。`

### Candidate 3 — service-choice-led

- Main: `受ける、学ぶ、相談する。`
- Supporting: `頭に触れる時間、技術を学ぶ入口、ヒーリングについて話す入口。なぎのみらいで選べます。`
- Service line: `福岡市｜なぎのみらい`
- CTA: `入口を選ぶ →`

Desktop: `受ける、学ぶ、` / `相談する。`
Mobile: `受ける、学ぶ、` / `相談する。`

### Candidate 4 — first-step-led

- Main: `何を選ぶか、決めるところから。`
- Supporting: `ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロン。まだ決まっていなくても、公式SNSから相談できます。`
- Service line: `三つの入口｜ひとつの相談先`
- CTA: `相談の入口へ →`

Desktop: `何を選ぶか、` / `決めるところから。`
Mobile: `何を選ぶか、` / `決めるところから。`

### Candidate 5 — question-led

- Main: `あなたが知りたいことから、開きます。`
- Supporting: `受けたい、学びたい、話を聞きたい。なぎのみらいのサービスを、目的から見つけます。`
- Service line: `Treatment｜School｜Healing`
- CTA: `質問から選ぶ →`

Desktop: `あなたが知りたいことから、` / `開きます。`
Mobile: `あなたが知りたいことから、` / `開きます。`

## 10. First 3 Viewports

### V01 — Human trust + What

- Purpose: establish Nagi, Fukuoka, human-service boundary, and the existence of three service modes.
- Copy: selected hero finalist plus `受ける / 学ぶ / 相談する` route line.
- Layout: human-context visual left / information field right on desktop; image, what-line, route preview, CTA on mobile.
- Photography: DISTANCE or PERSON; TOUCH is secondary only.
- Density: medium; enough facts to orient, no invented detail.
- Motion: Detail → Person if a detail is present; then route line opens One → Three.
- Interaction: focusable route preview; keyboard and tap states equivalent.
- Desktop: 12-column composition with broad human field and narrow fact rail.
- Mobile: 390px target first screen; brand and what in first 20%, route starts before first scroll.
- Screenshot peak: a calm human scene joined to an exact three-service route.

### V02 — Service choice

- Purpose: help a visitor choose by intent, not by knowing service terminology.
- Copy: `受けたい / 学びたい / ヒーリングについて相談したい` followed by service names and verified-when-available facts.
- Layout: one vertical decision path that expands into three unequal chapters, not three equal cards.
- Photography: CHOICE plus one contextual image per active path, not three decorative thumbnails.
- Density: high; What / For what intent / What is known / Next action.
- Motion: One → Three; active intent expands and preserves place in the page.
- Interaction: tap, keyboard, and reduced-motion all expose the same content.
- Desktop: selector at left, active service note at right.
- Mobile: horizontal tab strip is forbidden; use vertical intent buttons with persistent selected state.
- Screenshot peak: large `受ける / 学ぶ / 相談する` route with one open service note.

### V03 — Human / process / what happens

- Purpose: reduce touch anxiety and first-contact uncertainty without inventing treatment claims.
- Copy: `触れられる前に、分かること。` / `最初に確認すること` / `分からないことは相談できます`.
- Layout: person context → process diagram → boundary note → CTA.
- Photography: PERSON + PROCESS; actual human replaces representative visual in production.
- Density: medium-high; sequence is explicit and facts are marked replaceable.
- Motion: Question → Answer; each question opens the corresponding known/unknown answer.
- Interaction: accordion with 44px tap targets; no hidden critical information.
- Desktop: wide human image with an adjacent numbered process column.
- Mobile: image first, then three-step vertical sequence, then sticky consultation action.
- Screenshot peak: human distance plus a readable first-step map.

## 11. Full IA

| ID | Purpose / user question | Answer / copy | Visual / proof | Motion | CTA | Density |
|---|---|---|---|---|---|---|
| S01 ORIENT | What is this? | `なぎのみらい｜福岡市` | PERSON / DISTANCE context | Reveal human context | どれが合うか見る | M |
| S02 ROUTE | What can I choose? | `受ける｜学ぶ｜相談する` | Intent route map | One → Three | 入口を選ぶ | H |
| S03 TREATMENT | What is receiving? | `ドライヘッドスパ` + verified facts only | TOUCH / PROCESS | Follow choice | 施術について相談する | M-H |
| S04 SCHOOL | What is learning? | `ヘッドスパスクール` + replaceable course facts | LEARNING / MATERIAL | Follow choice | スクールについて相談する | M-H |
| S05 HEALING | What is healing? | `ヒーリングサロン` + boundary / verified scope | PERSON / SPACE | Follow choice | ヒーリングについて相談する | M-H |
| S06 TRUST | Who / what distance? | `触れられる前に、話して選ぶ。` | PERSON / DISTANCE | Detail → Person | 人について相談する | M |
| S07 PROCESS | What happens first? | `相談 → 内容確認 → 次の案内` only where verified; unknown steps remain replaceable | PROCESS diagram | Question → Answer | 最初の相談へ | H |
| S08 OPEN NOTE | What is known? | price / duration / place / qualification slots with status | editorial fact sheet | Resolve information | 詳細を確認する | H |
| S09 FAQ | What if I am unsure? | intent-based FAQ, no medical claims | text-led | Low reveal | 質問する | M |
| S10 CONTACT | What do I do now? | official SNS entry; final route replaceable | CHOICE / closing context | Three → One | 公式SNSで相談する | M |

## 12. Human Trust Mapping

| Trust layer | LP location | Required visible answer |
|---|---|---|
| Identity | S01 / S06 | Business name, area, human context; actual identity slot in final state |
| Service boundary | S02–S05 | Treatment / school / healing are distinct and not collapsed into “癒し” |
| Encounter distance | S06 | What a first interaction looks like; no fake portrait in sample |
| Competence | S08 | Qualifications and experience slots; show only when verified |
| Process | S07 | First question, next step, and what remains unknown |
| Transaction | S08 / S10 | Price, duration, booking route slots; official SNS is current safe entry |
| First step | S09 / S10 | A visitor can ask a question without selecting the wrong service |

## 13. Three-service Routing

Use `INTENT-FIRST + GUIDED CHOICE`:

1. Ask what the visitor wants to do: receive / learn / discuss.
2. Show the corresponding service name.
3. Reveal only the information that is verified or explicitly marked replaceable.
4. Provide a service-specific CTA.
5. Keep an undecided route: `どれが合うか相談する`.

No equal three-card grid. Each route has a different user question and CTA.

## 14. Service Differentiation

| Service | What is safe to say | Intent | Must be known | Evidence needed | Visual role | CTA | Unknown behavior |
|---|---|---|---|---|---|---|---|
| Treatment | ドライヘッドスパ | 受けたい | method, duration, price, first step | actual hand / room / method | TOUCH + PROCESS | 施術について相談する | show question route, not invented benefit |
| School | ヘッドスパスクール | 学びたい | curriculum, audience, instructor, qualification, schedule | actual class / materials / credentials | LEARNING | スクールについて相談する | show curriculum slots and SNS inquiry |
| Healing | ヒーリングサロン | 話して選びたい | definition, boundary, duration, price, what happens | actual practitioner / room / explanation | PERSON + SPACE | ヒーリングについて相談する | no medical wording or promised outcome |

## 15. Information Density Rhythm

Viewport rhythm: `M → H → M-H → M → H → M → H → M`.

- Human entry: medium
- Choice route: high
- Service notes: medium-high
- Human trust: medium
- Process: high
- Open facts: high
- FAQ: medium
- Closing: medium

Premium is created by hierarchy and editorial pacing, not by hiding practical information.

## 16. Photography System

| Role | Why it exists / user learns | Sales sample | Final asset | Forbidden misread |
|---|---|---|---|---|
| PERSON | Who may be present; human distance | representative human context | actual founder/staff | fake owner/staff |
| TOUCH | What kind of contact is being discussed | safe hand/head context | actual treatment hand | medical efficacy or fake treatment proof |
| DISTANCE | How close the first conversation feels | neutral conversation context | actual welcome scene | fake consultation record |
| PROCESS | What happens before action | diagram / neutral sequence | actual process photos | invented sequence |
| LEARNING | School is a real service mode | material / hands context | actual classroom/instructor | fake course evidence |
| SPACE | How the place may feel | non-identifying interior context | actual room | fake Nagi room |
| CHOICE | Three service modes are navigable | route map / typography | verified menu or selection visual | fake menu |
| PREPARATION | What a first step may involve | neutral preparation still | actual preparation | generic spa filler |
| MATERIAL | Concrete tools or learning objects | non-branded detail | actual tool/material | false technique claim |
| REST | Emotional pause without a benefit promise | quiet context | actual post-service context | promised result |

## 17. Asset Manifest

Required slot IDs for implementation:

`nagi.person.hero_context`, `nagi.touch.treatment_detail`, `nagi.distance.welcome`, `nagi.process.first_step`, `nagi.learning.school_context`, `nagi.space.room_context`, `nagi.choice.service_route`, `nagi.preparation.arrival`, `nagi.material.tool_detail`, `nagi.rest.after_context`.

Each slot requires: `source_type`, `provenance`, `evidence_status`, `sales_asset`, `final_replacement`, `aspect_ratio`, `crop_policy`, `mobile_policy`, and `risk_note`.

## 18. Visual Relationship Contract

| Relationship | Use |
|---|---|
| CROP_FROM_MASTER | Hero context to mobile crop only when identity and distance remain legible |
| WHOLE_DETAIL | Touch/material detail that teaches a concrete thing |
| SECONDARY_CONTEXT | Supporting room or atmosphere, never the main evidence |
| PROCESS_SEQUENCE | Arrival → question → next step, only when verified or labeled as proposed flow |
| ALTERNATIVE_VIEW | Same final asset at another decision-relevant crop |
| CONTEXT_EVIDENCE | Actual room/person/qualification image after hearing |
| INDEPENDENT_EDITORIAL | Typography/diagram used to explain a choice |
| NONE | Decorative filler; forbidden for key visuals |

Fake zoom, meaningless secondary imagery, and stock montage without a decision role are forbidden.

## 19. Typography System

- Display voice: direct Japanese sentences, medium-bold, meaning-unit breaks.
- Body voice: plain, warm, explicit Japanese; no poetic ambiguity.
- Label voice: compact sans, high contrast, service/status labels.
- Number voice: tabular or tight sans for duration, price, dates after verification.
- Service navigation voice: verbs first (`受ける / 学ぶ / 相談する`), noun second.
- Japanese weight: display 600–700, body 400–500.
- English: minimal system labels only; no luxury-serif or decorative English language.
- Line height: display 1.18–1.35; body 1.8–2.0; labels 1.3–1.5.
- Spacing: 8px base rhythm with deliberate 24/40/72px section steps.

SmartHR is adopted for information hierarchy and commercial completeness, not SaaS styling.

## 20. Color System

- Base: soft neutral white, not beige.
- Text: deep ink.
- Surface: white / cool neutral / one deep field for trust chapter.
- Human warmth: restrained skin-compatible warm neutral, never pink wellness.
- Service signal: one accent per active route may be used, but not as the sole differentiator.
- CTA: high-contrast ink or deep field with clear arrow.
- State: active / unavailable / replaceable use text and label as well as color.
- Border: thin neutral rule, used to structure information, not decorate emptiness.

Treatment, School, and Healing must differ through label, verb, composition, and information—not color alone.

## 21. Copy System

### Service choice

`受けたい。` / `学びたい。` / `ヒーリングについて相談したい。`

### Treatment

`ドライヘッドスパ` / `頭に触れるサービスについて、分かることから確認します。`

### School

`ヘッドスパスクール` / `学ぶ内容・進め方・確認したいことを、相談の入口から整理します。`

### Healing

`ヒーリングサロン` / `内容と過ごし方を、分からないまま決めません。`

### Human trust

`触れられる前に、話して選ぶ。`

### Process

`最初に伝えること。確認すること。次に進むこと。`

### Information

`分かっていることと、相談して決めること。`

### FAQ intro

`まだ決めきれないことから、聞いてください。`

### Booking

`公式SNSから、希望の入口を伝えて相談する。`

### Closing

`受けるか、学ぶか、相談するか。まだ決まっていなければ、そこから相談できます。`

All details such as price, duration, qualification, and review remain replaceable until verified.

## 22. Motion Identity

Final name: `TRUST TO CHOICE`.

Motion must change understanding, not merely move pixels:

- detail becomes human context;
- one service-looking entry becomes three intents;
- question becomes answer;
- choice follows into the correct note;
- three routes reunite at one appropriate contact action.

## 23. Motion Grammar

| Grammar | Meaning |
|---|---|
| REVEAL HUMAN CONTEXT | DETAIL → PERSON |
| SPLIT INTENT | ONE → THREE |
| RESOLVE INFORMATION | QUESTION → ANSWER |
| FOLLOW CHOICE | CHOICE → SERVICE |
| REUNITE ACTION | THREE → ONE CONTACT |

Forbidden: fade-up spam, random parallax, cursor gimmicks, floating circles, steam loops, scroll hijack, decorative masks, and slow motion without meaning.

## 24. Motion Peaks

### Peak 1 — Before Touch

- Start: close hand/detail or abstract touch context.
- Intermediate: camera widens; person and distance become visible.
- End: human context aligns with `触れられる前に、話して選ぶ。`.
- Understanding delta: touch is not an anonymous spa promise; the visitor can understand the encounter context.
- Duration: 700–1000ms.
- Trigger: hero entry / first intentional scroll.
- Mobile substitute: stacked reveal, no parallax.

### Peak 2 — One to Three

- Start: one consultation entry.
- Intermediate: intent verbs separate spatially.
- End: `受ける / 学ぶ / 相談する` become selectable routes.
- Understanding delta: Nagi is not treatment-only.
- Duration: 500–800ms.
- Trigger: V02 entering viewport or route focus.
- Mobile substitute: sequential vertical expansion.

### Peak 3 — Question to Answer

- Start: one unknown question (`何をする？`, `いくら？`, `誰に相談する？`).
- Intermediate: known facts and replaceable slots appear with status labels.
- End: the visitor knows what can be answered now and what to ask on SNS.
- Understanding delta: uncertainty becomes an actionable next step.
- Duration: 350–600ms.
- Trigger: tap / keyboard focus.
- Mobile substitute: accordion with critical answer visible in DOM.

## 25. Screenshot Peaks

1. Hero: human-context image + exact brand/area/service line + `触れられる前に、話して選ぶ。`.
2. Service Choice: one-to-three intent map with one open service note.
3. Human / Process: person-distance image beside a numbered first-step explanation.
4. Information / Booking: editorial fact sheet ending in `どれが合うか相談する` and official SNS route.

## 26. Microcraft

- Section numbers are functional orientation, not decoration.
- Use a small `known / ask / replaceable` status system.
- Route labels always pair verb + service name.
- CTA arrow changes direction only when destination changes.
- Active service has a visible rule and focus outline.
- Image captions state role (`人の距離`, `手技の説明`, `相談の入口`) rather than fictional provenance.
- Hover never carries meaning alone; focus and tap reproduce it.
- 44px minimum tap targets.
- Sticky mobile CTA says `相談する`, with selected service appended when known.
- Section transitions use rule, spacing, and semantic shift—not decorative gradients.

## 27. CTA Architecture

- Treatment: `施術について相談する`
- School: `スクールについて相談する`
- Healing: `ヒーリングについて相談する`
- Undecided: `どれが合うか相談する`
- Header: `相談する`
- Closing: the selected intent-specific CTA plus the undecided route.

Do not use one generic `予約する` CTA for all three modes before the booking route is verified.

## 28. Booking Architecture

Current safe route: official SNS / Instagram `@happyfuture_02`.

Sales sample:

- route CTA points to official SNS entry;
- message guidance asks visitor to state `受けたい / 学びたい / 相談したい`;
- no invented LINE, form, reservation platform, phone, hours, price, or address.

Final production: replace destination with verified LINE, form, reservation platform, or other official route without changing CTA semantics.

## 29. Unknown Handling

Every unknown is rendered as a designed question or replaceable fact slot:

- `料金` → `料金を確認する`
- `時間` → `所要時間を確認する`
- `資格・経験` → `担当者について確認する`
- `場所` → `場所とアクセスを確認する`
- `内容` → `内容を相談する`

Do not display `近日公開`, fake dashes, lorem ipsum, invented numbers, or vague claims that conceal missing evidence.

## 30. Hearing Replacement Map

### P0 — direction cannot be completed without it

- Founder / staff identity and whether public display is desired
- Actual treatment and hand photographs
- Actual room and first-contact photographs
- Healing definition and service boundary
- Exact booking destination
- Verified treatment/school/healing process

### P1 — large quality improvement

- Price and duration for each service
- Qualifications and experience
- School curriculum, audience, schedule, and certificate status
- Actual reviews and permission to publish
- Access, address, opening hours

### P2 — further premium lift

- Preparation/material photographs
- Additional staff portraits
- Client-consented process photographs
- FAQ language from real inquiries
- Seasonal or program-specific service notes

## 31. Mobile Art Direction

Order: `WHAT → WHICH → WHO → HOW → NEXT`.

- Hero crop: retain human distance, never hand-only.
- Service selector: vertical intent buttons, no 2×2 card grid or horizontal carousel.
- Human context: precedes process, not buried below a generic benefit section.
- Sticky CTA: one concise `相談する`; selected mode appears when known.
- Density: compact high-information blocks alternate with visual breathing space.
- Interaction: tap/focus equivalent; accordion answers in document order.
- Motion substitute: sequential reveal, no scroll-lock or parallax dependency.
- Image order: context → detail → process → evidence.
- Text: 2–4 short lines per block, meaning-unit Japanese breaks.

## 32. Responsive Rules

Validate design intent at 320, 360, 375, 390, 430, 768, 1024, 1280, and 1440px.

- 320–375: prevent service labels and CTA arrows from wrapping into isolated tokens.
- 390–430: preserve human image plus What line before first route action.
- 768: transition from vertical intent flow to split editorial layout only when text remains readable.
- 1024: maintain route map and fact note without compressing touch targets.
- 1280–1440: increase negative space around human visual, not headline size beyond meaning.
- All widths: no image/text collision, no hidden critical facts, no horizontal overflow, no Japanese orphan particle/verb.

## 33. Anti-generic Gate

The direction fails if it can be described only as calm, gentle, premium, healing, soft, spacious, or beautiful.

Nagi-specific decisions required:

1. The three exact service modes remain distinct.
2. The first interaction is framed around being touched, so human distance comes before touch detail.
3. The official SNS is the current safe consultation entry.
4. Unknown facts are turned into explicit questions and replaceable slots.
5. The route begins from intent verbs, not from equal service cards.
6. Treatment, school, and healing use different proof needs and CTA destinations.
7. Sales visuals are structurally designed to be replaced by actual evidence later.

## 34. Benchmark Traceability

| Direction decision | Benchmark principle | Source examples | Adopt / reject |
|---|---|---|---|
| Human context before touch | TRUST BEFORE ACTION | One Medical, Riraku, prior longleage review | Adopt principle; reject medical/luxury styling |
| Three-service route | CHOICE BEFORE COMMITMENT | Airbnb Experiences, SmartHR service grouping, GORA prior review | Adopt route logic; reject marketplace/card look |
| Open facts | INFORMATION AS AUTHORITY | SmartHR, JHSA certification, Headlife | Adopt hierarchy; reject SaaS appearance |
| Process clarity | FIRST STEP VISIBLE | Riraku booking, JHSA certification flow, Headspace beginner path | Adopt sequence; reject generic wellness benefit claims |
| Learning as a real mode | LEARN / RECEIVE SPLIT | Make a Wish, Headlife, IDEO U, yume | Adopt distinction; reject unsupported Nagi curriculum |
| Atmosphere with information | EXPERIENCE + DETAIL | Imperial Kyoto, Four Seasons Kyoto, Aman Kyoto | Adopt coexistence; reject hotel luxury cues |
| Human replacement readiness | EVIDENCE SLOT DESIGN | prior Nagi asset manifest / GORA quality review | Adopt slot architecture; reject fake evidence |

Official sources inspected include [Make a Wish](https://headspa-school.com/), [JHSA certification](https://www.headspa.co.jp/certification/), [Headlife](https://www.headlife.org/), [yume school](https://www.headspa-yume.jp/seminar), [WALAN SPA](https://www.walanspa.com/), [Riraku Spa booking](https://www.hyatt.com/en-US/spas/Riraku-Spa/booking), [Imperial Hotel Kyoto Spa](https://www.imperialhotel.co.jp/en/kyoto/facility/the-spa), [Four Seasons Kyoto Spa](https://www.fourseasons.com/kyoto/spa/), [Aman Kyoto Spa menu](https://www.aman.com/sites/default/files/2024-04/Aman_Kyoto_Spa_Menu.pdf), [One Medical FAQ](https://www.onemedical.com/faq/), [Headspace beginner path](https://www.headspace.com/content/topics/beginning-meditation/93), [IDEO U learning experience](https://www.ideou.com/pages/learning-experience), [Airbnb Experiences booking guidance](https://www.airbnb.com/help/article/2493), and [SmartHR](https://smarthr.jp/).

## 35. REQUIRED Contract

- Human Trust is visible before a touch close-up.
- The three service modes are distinct in IA, proof, copy, and CTA.
- Intent-first guided routing is implemented as a real information structure.
- Information clarity remains premium and complete.
- Unknown facts are replaceable, never invented.
- Sales Sample and Final Production share the same layout contract.
- Motion changes understanding through `TRUST TO CHOICE`.
- Mobile is re-art-directed as `WHAT → WHICH → WHO → HOW → NEXT`.
- Four screenshot peaks and three motion peaks are present.

## 36. FORBIDDEN Contract

- Generic wellness language as the main idea.
- Beige/serif/spa-candle/water/steam/towel cliché.
- Fake owner, staff, instructor, therapist, room, qualification, review, price, or treatment proof.
- Equal three-card service grid.
- One generic booking CTA for three different modes.
- Medical or treatment-effect claims.
- Slow fade as the only motion.
- Decorative motion without comprehension delta.
- Hidden price/process/booking information for the sake of premium appearance.
- Desktop layout mechanically shrunk to mobile.

## 37. TARGET Contract

- Hero communicates Nagi, Fukuoka, human trust, three services, and next action within one first viewport.
- V01–V03 make the hybrid direction perceptible without reading the full page.
- Sales Sample looks intentional and complete despite evidence gaps.
- Final asset replacement is slot-for-slot, not a redesign.
- GORA KADAN FUJI is the minimum premium ambition for experience sequencing, not a visual template.
- SmartHR is the benchmark for hierarchy, completeness, and micro-information care, not a SaaS skin.
- 320–1440px design intent remains stable.

## 38. Creative Fidelity Contract

Human review must answer YES to all:

- Hero feels fundamentally new from the old Nagi LP.
- First three viewports clearly communicate Human Trust × Service Choice × Radical Clarity.
- B/A/C hybrid is visible as a single grammar, not three pasted modules.
- Human trust is visible without fake identity.
- Service choice is visible before booking.
- Information clarity is visible and premium.
- Motion identity is perceptible and meaningful.
- Mobile has its own art direction.

## 39. Perceptual Delta Contract

Against the old Nagi LP, human-visible change is required in at least 7/8 axes:

1. topology: immersive/split route surface instead of current scene stack;
2. photography logic: human context and decision roles instead of atmosphere-first images;
3. typography: direct information-led Japanese voice;
4. IA: intent-first route before service details;
5. density rhythm: alternating human and information peaks;
6. motion: TRUST TO CHOICE instead of generic reveal;
7. mobile: WHAT → WHICH → WHO → HOW → NEXT;
8. CTA architecture: service-specific and undecided routes.

## 40. 1000件 Experience Library Additions

- `HUMAN_TRUST_BEFORE_TOUCH`
- `INTENT_FIRST_GUIDED_ROUTING`
- `LOW_EVIDENCE_PREMIUM`
- `INFORMATION_AS_AUTHORITY`
- `TOUCH_CONTEXT_BEFORE_DETAIL`
- `UNKNOWN_AS_QUESTION`
- `SERVICE_CHOICE_MOTION`
- `SALES_SAMPLE_TO_FINAL_REPLACEMENT`
- `MOBILE_WHAT_WHICH_WHO_HOW_NEXT`
- `ONE_TO_THREE_TO_ONE_CONTACT`

Failure additions:

- `TOUCH_WITHOUT_PERSON_CONTEXT`
- `THREE_SERVICES_AS_EQUAL_CARDS`
- `POETIC_COPY_BEFORE_SERVICE_CLARITY`
- `FAKE_HUMAN_EVIDENCE`
- `LUXURY_MASKING_FOR_UNKNOWN_FACTS`
- `GENERIC_WELLNESS_AS_IDENTITY`

## 41. Implementation-ready Specification

Rin may implement only after `IMPLEMENTATION GO`:

1. Build data-driven sections from the IA table, not from the old scene DOM.
2. Create asset slots with provenance and sales/final replacement metadata.
3. Implement route state with keyboard, tap, reduced-motion, and DOM-visible content parity.
4. Implement the five motion grammar families and three named peaks; do not add decorative motion.
5. Keep all unknown fact fields explicit and replaceable.
6. Preserve official SNS as the only current safe consultation destination.
7. Add line-composition tests for all Japanese headings at the nine required widths.
8. Add safety tests for fake identity, fake room, unsupported claim, and generic CTA leakage.
9. Generate capture and evidence manifests only after implementation and QA are authorized.

## 42. Risks

- Actual human photography may be unavailable; protect the direction with slot-based replacement rather than weakening the hero.
- Healing terminology can drift into medical claims; require evidence and boundary review.
- Three services can become a menu wall; keep intent verbs and unequal editorial routing.
- Radical clarity can become a specification document; alternate facts with human visual chapters.
- Stock/generated touch imagery can be mistaken for Nagi evidence; keep context, provenance, and role visible in design metadata.
- Mobile can become overly long; use progressive disclosure without hiding critical facts.

## 43. Riko Final Recommendation

### First Recommendation

Proceed with the selected hybrid as specified. The strongest first implementation emphasis is `BEFORE TOUCH`: human context and encounter boundary must appear before a touch close-up. This is the most defensible response to Nagi's low-evidence, high-trust problem.

### Second Recommendation

Make `ENTRY MAP` the visible structural signature of the first three viewports. If the three service modes are not legible before the first contact action, the page will collapse back into a generic head-spa LP.

No final implementation direction beyond this approved hybrid is being selected here.

## 44. Shun Review Points

1. Is the first viewport visibly about choosing safely before being touched, rather than about spa atmosphere?
2. Are `受ける / 学ぶ / 相談する` three genuinely different routes rather than three cards?
3. Does the Sales Sample remain premium without implying a fake owner, staff member, room, or treatment record?
4. Is the information density sufficient to feel trustworthy without becoming a document portal?
5. Should the primary hero finalist be Candidate 1, 2, 3, 4, or 5?

## Stop Condition

Round 2H-C Creative Specification is complete.

No HTML, CSS, renderer, asset generation, workflow change, commit, push, or Rin handoff was performed.

Next gate: Shun review and explicit `IMPLEMENTATION GO`.
