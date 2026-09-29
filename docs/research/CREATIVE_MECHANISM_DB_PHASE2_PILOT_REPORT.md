# Creative Mechanism Database — Phase 2 100-Reference Pilot Report

- Status: `PHASE_2_100_REFERENCE_PILOT_READY_FOR_PM_REVIEW`
- SSOT: Architecture v1.2.2 / Issue #143 / Final Approval Comment #5884858285
- Captured date: 2026-09-29
- Scope: 100 references only; the 2,600-reference Universe collection was not started.

## Executive Result

The data model survives the Pilot as a traceable structure, but the Pilot exposes an important operational distinction: a known official URL is not the same as a captured Original Evidence Snapshot, and a responsive claim is not the same as a 390px Mobile Observation. The current Work browser allowed one live desktop AX observation but not a mobile-viewport capture. Candidate Mechanisms are therefore retained as `CANDIDATE`; no mechanism is promoted to Supported or Canonical from this Pilot alone.

## Coverage QA

- References: **100 / 100**
- Matrix cells: **20 / 20**, each planned count **5**
- Scene evidence records: **400** (4 per reference)
- Mechanism candidates: **25**
- Architecture issue records: **10**
- Strong / Hold / Reject: **0 / 80 / 20**
- Duplicate canonical URLs: 0 within the Pilot ledger
- Phase 2 collection_started: false for the post-Pilot Universe lane

## Strong / Hold / Reject

Strong requires Original/Official evidence, desktop and mobile observation, scene-level mechanisms and pool-specific review. This run produced no Strong promotion because mobile capture was unavailable. HOLD is used where the reference is useful but capture/evidence is incomplete. REJECT records candidates that should not enter Strong Corpus.

## Source Distribution

| Discovery Source | Count |
|---|---:|
| AWWWARDS | 20 |
| CONVERSION_LP_GALLERY | 10 |
| CSS_DESIGN_AWARDS | 10 |
| GLOBAL_WEB_GALLERY | 5 |
| JAPANESE_WEB_GALLERY | 10 |
| MOTION_INTERACTION_SHOWCASE | 5 |
| ORIGINAL_SITE_DIRECT | 20 |
| PRODUCTION_PORTFOLIO | 5 |
| WEB_GRAND_PRIX | 15 |

## Archetype Distribution

| Archetype | Count |
|---|---:|
| B2B_PRODUCT_MANUFACTURING | 10 |
| B2B_TECHNICAL_SOLUTION | 10 |
| BEAUTY_PERSONAL | 5 |
| CULTURE_ENTERTAINMENT_CAMPAIGN | 5 |
| D2C_PRODUCT | 10 |
| HIGH_CONSIDERATION_HOME | 10 |
| LOCAL_TRUST_SERVICE | 10 |
| MEDICAL_WELLNESS | 5 |
| PREMIUM_LUXURY | 5 |
| PROFESSIONAL_ADVICE | 5 |
| PUBLIC_SOCIAL | 5 |
| RETAIL_FOOD_HOSPITALITY | 10 |
| SAAS_WORKFLOW | 10 |

## Industry Distribution

| Industry | Count |
|---|---:|
| ART_CULTURE | 5 |
| BEAUTY_SALON_BODYCARE | 5 |
| CONSTRUCTION_HOME | 5 |
| FASHION_LUXURY | 10 |
| FINANCE_INSURANCE | 5 |
| FOOD_RESTAURANT | 5 |
| HOTEL_TRAVEL | 5 |
| IT_SAAS_DIGITAL | 15 |
| LANDSCAPE_GARDEN | 5 |
| LOGISTICS_MAINTENANCE | 5 |
| MANUFACTURING_MATERIALS | 10 |
| MEDICAL_DENTAL_CLINIC | 5 |
| PUBLIC_NONPROFIT | 5 |
| REAL_ESTATE | 5 |
| RENOVATION_REPAIR | 5 |
| RETAIL_D2C_CONSUMER | 5 |

## JP / Global

- JP: 60
- Global: 40

## Evidence Grade Distribution

| Grade | Count |
|---|---:|
| E0 | 0 |
| E1 | 9 |
| E2 | 21 |
| E3 | 0 |
| E4 | 70 |
- Live browser page observation: 70 loaded pages; 30 remained unobserved before failure classification.
- Screenshot archive: 0 archive-backed screenshots; all 100 records retain `screenshot_identifier=NOT_CAPTURED` pending Evidence Archive integration.

### Live Page Status

| Status | Count |
|---|---:|
| LIVE_403_REQUEST_BLOCKED | 2 |
| LIVE_404_OR_MOVED_PAGE | 1 |
| LIVE_502_BAD_GATEWAY | 2 |
| LIVE_BLANK_IFRAME_OR_SRCDOC | 1 |
| LIVE_BLANK_PAGE | 7 |
| LIVE_BROWSER_BLOCKED | 2 |
| LIVE_MINIMAL_RENDER | 1 |
| LIVE_NAVIGATION_TIMEOUT | 12 |
| LIVE_REDIRECTED_THIRD_PARTY_API | 1 |
| LIVE_SITE_UNAVAILABLE | 1 |
| OBSERVED_LIVE_BROWSER | 70 |

## Evidence and Missingness Findings

- Original/Official evidence status: VERIFIED=70, candidate=21, unconfirmed=9.
- Desktop observation failure / not observed: 30
- Mobile observation failure / not observed: 100
- Average Creative Profile UNKNOWN rate: 76.6%
- Measured CVR, revenue or inquiry lift was not inferred. No `observed_performance_evidence` was claimed.

## Risk Findings

- Regulated claims: Finance, Medical and Beauty were included and flagged for claim-unit/source review.
- Accessibility: Public/Social and Medical references require keyboard, contrast, alt text and reduced-motion checks beyond gallery metadata.
- Before/After: Beauty and renovation references require consent, context, date and non-guarantee metadata.
- Source bias: Award/Gallery discovery remained separate from Original/Official evidence.
- Mobile: A responsive label is not accepted as a Mobile Observation; all 100 records retain NOT_OBSERVED until a 390px capture path is available.

## Architecture Validation

### What held

- Reference → Scene Evidence → Mechanism Candidate → decision status remained representable.
- Discovery Source and Evidence Source remained separate.
- Evidence Quality enums and Axis Signal values remained separate.
- Motion `NOT_APPLICABLE` was representable without automatic quality failure.
- Creative Benchmark avoided a mandatory Conversion Architecture threshold.

### What broke or stayed ambiguous

- Evidence Snapshot storage and capture provenance need an operational artifact archive before Strong Corpus promotion.
- `design_agency` and `campaign_family` are frequently unavailable from official pages; UNKNOWN must remain first-class.
- Regulated claim and accessibility checks need scene-level subfields, not only a reference-level note.
- Mechanism independence cannot be proven from five references per cell; all mined items remain Candidate.
- Performance risk needs a runtime observation field for motion-heavy pages.

## Pilot Mechanism Sample

| ID | Mechanism | Scene | Transfer Job | Automation Difficulty |
|---|---|---|---|---:|
| CM-CAND-001 | Proof-led Hero | Hero | front-load credible proof | 4 |
| CM-CAND-002 | Split Value Proposition Hero | Hero | separate promise from proof | 4 |
| CM-CAND-003 | Editorial Process Stack | Solution | explain how trust is earned | 4 |
| CM-CAND-004 | Full-bleed Place Image with Anchored CTA | Hero | make destination value tangible | 4 |
| CM-CAND-005 | Product Macro with Ingredient Proof | Product | convert sensory detail into evidence | 3 |
| CM-CAND-006 | Case-study Proof Rail | Case Study | reduce perceived decision risk | 5 |
| CM-CAND-007 | Objection Ladder FAQ | FAQ | remove late-stage hesitation | 5 |
| CM-CAND-008 | Sticky Mobile Action Bar | CTA | reduce action friction | 4 |
| CM-CAND-009 | Vertical Evidence Rail | Proof | surface supporting authority | 4 |
| CM-CAND-010 | Asymmetric Specification Grid | Service | make complexity legible | 4 |
| CM-CAND-011 | Document-first Technical Proof | Proof | compress trust-building for expert readers | 5 |
| CM-CAND-012 | Progressive Disclosure Pricing | Pricing | match information to consideration state | 5 |
| CM-CAND-013 | Guided Decision Quiz | Conversion | qualify without a form wall | 4 |
| CM-CAND-014 | Controlled Before/After Compare | Case Study | make outcome concrete | 4 |
| CM-CAND-015 | Appointment Slot CTA | CTA | translate trust into commitment | 4 |
| CM-CAND-016 | Service-area Map Proof | Service Area | answer can-you-serve-me uncertainty | 4 |
| CM-CAND-017 | Identity-rich Testimonial | Proof | reduce similarity risk | 4 |
| CM-CAND-018 | Compliance Trust Band | Proof | support safe decision-making | 5 |
| CM-CAND-019 | Motion-led Scroll Reveal | Reframe | control narrative timing | 5 |
| CM-CAND-020 | Horizontal Product Journey | Service | turn feature list into progression | 5 |
| CM-CAND-021 | Kinetic Type Statement | Hero | brand an idea without extra imagery | 4 |
| CM-CAND-022 | Image Mask Scene Transition | Section Boundary | make section change memorable | 4 |
| CM-CAND-023 | Editorial Catalog Navigation | Navigation | reduce scroll disorientation | 4 |
| CM-CAND-024 | Bento Feature Comparison | Service | support scan and selection | 4 |
| CM-CAND-025 | Campaign Participation Counter | Proof | make participation tangible | 3 |

## Recommendation

**Do not start the 2,600-reference collection yet.** First resolve the high-severity operational issues (live snapshot archive, mobile capture, regulated claim unit, accessibility checklist), then run a controlled re-check on the same 100 references or a small replacement set. The Architecture is structurally viable but not yet safe for unsupervised Strong Corpus scaling.

## Phase 3 Recommendation

1. Add a bounded, durable Evidence Archive with immutable snapshot identifiers.
2. Add a required 390px mobile capture step and an accessibility observation checklist.
3. Add claim-level evidence records for Finance, Medical and Beauty.
4. Keep all 25 items as Candidate and test independence across brands/agencies before Supported.
5. Re-run QA and request PM review before opening the 2,600-reference lane.
