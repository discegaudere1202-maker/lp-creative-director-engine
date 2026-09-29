# Creative Mechanism Database — Phase 2.2 100-Reference Pilot Report
**Status:** `PHASE_2_2_100_REFERENCE_PILOT_READY_FOR_PM_REVIEW`  
**SSOT:** Issue #143 / Sarah PM Comment #5888589418  
**Architecture:** v1.3.1  
**Capture Run:** `36558472328` / temporary Artifact `11028964368` (`sha256:7c32d38a9cfc16108c0e65b522b93e9b903355d877e96b5705363f7f31eb22aa`)
## Decision and scope

All original 100 pilot records remain in the master ledger and all 20 coverage cells retain five references each. The 15 remaining Gold references received full-page backfill. Five already traversed Gold references retain their v1.3.1 evidence and archive provenance. There are **100 uniform ledger records**, but **27 references still lack visual captures** because the official site returned an error or denied access at both viewports. Their durable capture-failure records are linked; these references remain `HOLD`. No score, Strong promotion, or mechanism promotion was made from missing or unobserved evidence. The 2,600-reference gate remains `false`.
## Coverage and observation

| Measure | Result |
|---|---:|
| References / preserved cells | 100 / 20 × 5 |
| JP / Global | 60 / 40 |
| Pool: Conversion / Creative Benchmark | 90 / 10 |
| Industries / business archetypes represented | 16 / 13 |
| Gold 15 full-page backfill | 15 / 15 both viewports captured |
| References with durable 1440 + 390 screenshot evidence | 73 / 100 |
| References with both viewport screenshots unavailable | 27 / 100 |
| Scene rows / OBSERVED / NOT_OBSERVED | 1240 / 906 / 334 |
| Semantic-job coverage rows | 200 (100 × 2 viewports; six jobs each) |
| Runtime / accessibility observation rows | 200 (runtime behaviors remain NOT_OBSERVED unless independently tested) |
| Explicit capture-failure records | 54 |

`NOT_APPLICABLE` was not assigned merely because a keyword was absent. If the captured DOM and pixels did not support a positive scene classification, the job remains `NOT_OBSERVED` pending human semantic review. Scene/job coverage by matrix cell is in `data/creative_mechanism_phase2_2_coverage_matrix.csv`.
### Matrix cells

| Cell | Archetype | Industry | Market | Discovery source | Durable both views | Scenes | Observed | Not observed |
|---|---|---|---|---|---:|---:|---:|---:|
| P01 | LOCAL_TRUST_SERVICE | LANDSCAPE_GARDEN | JP | ORIGINAL_SITE_DIRECT | 1 / 5 | 78 | 66 | 12 |
| P02 | LOCAL_TRUST_SERVICE | CONSTRUCTION_HOME | JP | JAPANESE_WEB_GALLERY | 0 / 5 | 70 | 58 | 12 |
| P03 | HIGH_CONSIDERATION_HOME | RENOVATION_REPAIR | JP | CONVERSION_LP_GALLERY | 0 / 5 | 46 | 46 | 0 |
| P04 | HIGH_CONSIDERATION_HOME | REAL_ESTATE | GLOBAL | GLOBAL_WEB_GALLERY | 0 / 5 | 48 | 24 | 24 |
| P05 | PROFESSIONAL_ADVICE | FINANCE_INSURANCE | JP | WEB_GRAND_PRIX | 1 / 5 | 75 | 39 | 36 |
| P06 | MEDICAL_WELLNESS | MEDICAL_DENTAL_CLINIC | GLOBAL | AWWWARDS | 1 / 5 | 60 | 36 | 24 |
| P07 | B2B_TECHNICAL_SOLUTION | MANUFACTURING_MATERIALS | JP | PRODUCTION_PORTFOLIO | 0 / 5 | 43 | 31 | 12 |
| P08 | B2B_TECHNICAL_SOLUTION | IT_SAAS_DIGITAL | GLOBAL | AWWWARDS | 1 / 5 | 78 | 78 | 0 |
| P09 | B2B_PRODUCT_MANUFACTURING | LOGISTICS_MAINTENANCE | JP | ORIGINAL_SITE_DIRECT | 0 / 5 | 44 | 44 | 0 |
| P10 | B2B_PRODUCT_MANUFACTURING | MANUFACTURING_MATERIALS | GLOBAL | CSS_DESIGN_AWARDS | 0 / 5 | 54 | 30 | 24 |
| P11 | SAAS_WORKFLOW | IT_SAAS_DIGITAL | JP | ORIGINAL_SITE_DIRECT | 0 / 5 | 71 | 71 | 0 |
| P12 | SAAS_WORKFLOW | IT_SAAS_DIGITAL | GLOBAL | MOTION_INTERACTION_SHOWCASE | 1 / 5 | 71 | 70 | 1 |
| P13 | D2C_PRODUCT | RETAIL_D2C_CONSUMER | JP | CONVERSION_LP_GALLERY | 0 / 5 | 59 | 35 | 24 |
| P14 | D2C_PRODUCT | FASHION_LUXURY | GLOBAL | CSS_DESIGN_AWARDS | 0 / 5 | 59 | 11 | 48 |
| P15 | RETAIL_FOOD_HOSPITALITY | FOOD_RESTAURANT | JP | ORIGINAL_SITE_DIRECT | 0 / 5 | 41 | 41 | 0 |
| P16 | RETAIL_FOOD_HOSPITALITY | HOTEL_TRAVEL | GLOBAL | AWWWARDS | 0 / 5 | 88 | 52 | 36 |
| P17 | BEAUTY_PERSONAL | BEAUTY_SALON_BODYCARE | JP | WEB_GRAND_PRIX | 0 / 5 | 67 | 55 | 12 |
| P18 | PUBLIC_SOCIAL | PUBLIC_NONPROFIT | JP | JAPANESE_WEB_GALLERY | 0 / 5 | 78 | 66 | 12 |
| P19 | PREMIUM_LUXURY | FASHION_LUXURY | GLOBAL | AWWWARDS | 0 / 5 | 50 | 2 | 48 |
| P20 | CULTURE_ENTERTAINMENT_CAMPAIGN | ART_CULTURE | JP | WEB_GRAND_PRIX | 0 / 5 | 60 | 51 | 9 |

### Discovery mix and capture failures

Discovery mix (counts): AWWWARDS: 20, CONVERSION_LP_GALLERY: 10, CSS_DESIGN_AWARDS: 10, GLOBAL_WEB_GALLERY: 5, JAPANESE_WEB_GALLERY: 10, MOTION_INTERACTION_SHOWCASE: 5, ORIGINAL_SITE_DIRECT: 20, PRODUCTION_PORTFOLIO: 5, WEB_GRAND_PRIX: 15.

Capture-failure response/status mix (54 viewport attempts): 200: 2, 403: 32, 404: 2, 405: 2, 429: 2, 502: 2, Error: 10, TimeoutError: 2.

Failures affect 27 complete reference pairs. They include HTTP 403/404/405/429/502, response pages with no usable content, timeout, and HTTP/2 protocol errors. `creative_mechanism_phase2_2_capture_failures.jsonl` records each URL, viewport, HTTP status/error, and durable capture-manifest locator. No blocked page was bypassed.

| Market | Durable both views | Partial / missing |
|---|---:|---:|
| GLOBAL | 23 | 17 |
| JP | 50 | 10 |

## Evidence Archive

The 95-reference capture was packaged in 10 immutable-by-version Library ZIPs. Each is pinned to `file_id` / version 0, is retrievable through its actual Library locator, and was re-downloaded for byte-for-byte Container SHA verification. All image/member hashes were checked against the archive index. The five earlier Full-page Gold references retain the preexisting `GOLD20-FULLPAGE-V1` archive. Repository stores manifests and indices only, not screenshot binaries.

| Archive | File | Bytes | SHA-256 |
|---|---|---:|---|
| P22-EVIDENCE-01 | `phase2_2_batch_01_sha256-7cf3cbd70747.zip` | 18009196 | `7cf3cbd70747d4a88cf6bdca5eb515d2cb5351a0b0e82ccb33bd59025560f642` |
| P22-EVIDENCE-02 | `phase2_2_batch_02_sha256-65715e19990d.zip` | 22484864 | `65715e19990d7fa4b9ab900710c32df1f87fbe910e1ef9b19d0ab90ad327e3cd` |
| P22-EVIDENCE-03 | `phase2_2_batch_03_sha256-8850dcf9f52c.zip` | 17998457 | `8850dcf9f52cafe033698a1ec6fa51e249320698033ba98094e95894d6b0fe04` |
| P22-EVIDENCE-04 | `phase2_2_batch_04_sha256-420483d21c41.zip` | 9549905 | `420483d21c411ac601324bdbbd3061cea4e1469c5a63d67aacfa53328dc89157` |
| P22-EVIDENCE-05 | `phase2_2_batch_05_sha256-8adc6726bdd0.zip` | 17189712 | `8adc6726bdd091c81270093bb2e79c83405116eccd63e5cbc8cd883b296f40d5` |
| P22-EVIDENCE-06 | `phase2_2_batch_06_sha256-ecba0888d53a.zip` | 17654574 | `ecba0888d53a3c5a4afb4f1953378393b3cab2853413588e7d590b18527e039f` |
| P22-EVIDENCE-07 | `phase2_2_batch_07_sha256-586da70ab3d7.zip` | 8055465 | `586da70ab3d727e6752e6c7aa9327007f0e5b6cd5c75e25db6205f91014301fb` |
| P22-EVIDENCE-08 | `phase2_2_batch_08_sha256-38fcfd3cc389.zip` | 12480880 | `38fcfd3cc38944a4248229875ef70efc95bac31c60e6cb41ac19e4542daed599` |
| P22-EVIDENCE-09 | `phase2_2_batch_09_sha256-73087214e390.zip` | 11790552 | `73087214e390a824757a91bfd23ff715b79a485a92adf3272f73014b3c6ee08d` |
| P22-EVIDENCE-10 | `phase2_2_batch_10_sha256-5ce9607ade47.zip` | 7215037 | `5ce9607ade47b1b91fa973448b2542c288bad48206ea78fd6cb318bcaf74003d` |

New archive batches contain 1117 screenshot/crop members and durable attempt manifests. All 54 unavailable viewport attempts point to the exact archived `manifest_subset.json` entry and its SHA-256. Retention policy is three years after last mechanism use with yearly review; monthly retrieval/hash verification, recapture on URL/page change, and fail-closed `HOLD` on archive loss are recorded per archive in `creative_mechanism_phase2_2_archive_registry.json`. The storage backend does not provide a claimed retention SLA.

## Mechanism synthesis

Extraction used only `OBSERVED` scenes with a concrete locator, archived crop, and pinned archive. Candidate source IDs and counts are derived from `source_scene_evidence_ids[]`; no evidence from `NOT_OBSERVED`, `MISSING`, or `NOT_APPLICABLE` scenes is eligible. Candidate definitions were narrowed after checking both desktop and mobile crops. Confidence remains `HEURISTIC_NEEDS_PIXEL_REVIEW`; each remains `CANDIDATE`, not `SUPPORTED` or `CANONICAL`.

| Candidate | Scene evidence | Refs / brands | Desktop sample | Mobile sample | Mobile transfer rule |
|---|---:|---:|---|---|---|
| `CUSTOMER_CASE_PROOF` | 6 | 3 / 3 | `P22-P03-R01-DESKTOP-SCENE-002` — P03-R01, 施工事例を見る | リノベのお役立ちブログを読む; pixel y=703:1668 | `P22-P03-R01-MOBILE-SCENE-003` — P03-R01, 施工事例を見る; pixel y=1194:2294 | 390pxでは施工事例カードを縦に積み、写真・物件名の順を保つ。 |
| `MULTI_ITEM_SERVICE_CLUSTER` | 15 | 8 / 8 | `GOLD-P06-R02-DESKTOP-TRAV-02` — P06-R02, Cancer / full-page y=1100:2050 | `GOLD-P06-R02-MOBILE-TRAV-02` — P06-R02, Cancer / full-page y=800:2100 | 390pxでは診療科目が縦の開閉リストへ再配置される。項目名を残し、画面横幅に依存する列数は引き継がない。 |
| `MULTI_PATH_CTA` | 54 | 26 / 26 | `P22-P03-R04-DESKTOP-SCENE-002` — P03-R04, 相談する・探す "優良なリノベーション"「統一規格」に則ったリノベーション物件や相談先を掲載しています。; pixel y=856:1392 | `P22-P03-R04-MOBILE-SCENE-002` — P03-R04, 相談する・探す "優良なリノベーション"「統一規格」に則ったリノベーション物件や相談先を掲載しています。; pixel y=564:1267 | 390pxでは相談・検索の3選択肢が縦カードになり、各カードの目的と個別CTAを維持する。 |
| `PRICING_COMPARISON` | 4 | 2 / 2 | `P22-P11-R03-DESKTOP-SCENE-004` — P11-R03, 料金プラン; pixel y=2905:3680 | `P22-P11-R03-MOBILE-SCENE-005` — P11-R03, 料金プラン; pixel y=3978:5411 | 390pxでは料金3プランを縦積みにし、プラン名・月額・CTAを各カード内で保持する。 |
| `QUESTION_ANSWER_CLUSTER` | 2 | 1 / 1 | `P22-P11-R03-DESKTOP-SCENE-008` — P11-R03, よくある質問; pixel y=6803:8859 | `P22-P11-R03-MOBILE-SCENE-009` — P11-R03, よくある質問; pixel y=9146:10863 | 390pxではFAQ行を縦並びにする。開閉動作自体は未テストなので静的構造だけを移植対象にする。 |
| `TRUST_DISCLOSURE_LIST` | 17 | 9 / 9 | `P22-P05-R01-DESKTOP-SCENE-006` — P05-R01, 重要なお知らせ; pixel y=4887:5865 | `P22-P05-R01-MOBILE-SCENE-006` — P05-R01, 重要なお知らせ; pixel y=3665:4607 | 390pxでは日付付きのお知らせを一列に並べ、各項目の見出しと遷移手掛かりを保つ。 |

Across these six mined families: **6 exact rule families / 98 scene links / 35 distinct reference sources**. The duplicate map contains exact family identifiers and non-automatic variant-review edges; possible variants are not merged by text similarity alone. Co-observed pairs are not marked compatible.

**Status of older candidates:** existing 20 Gold candidates, 15 Phase 2.1.1 candidates, and 25 `PROVISIONAL_FROM_PHASE2` records are preserved in `creative_mechanism_phase2_2_frozen_legacy_candidates.jsonl` (60 total). They were not automatically affirmed or promoted.

## Scores, claims, and runtime checks

All 100 full-page scores are `NOT_SCORED`; ranking and Strong / mechanism promotion flags are false. The 20 Gold legacy scores remain explicitly scoped to `CAPTURED_ENTRY_AND_FIRST_SCROLL_ONLY`. The other 80 legacy scores are `PROVISIONAL_UNAUDITED`. All 100 records remain `HOLD` pending PM review and unresolved record gates.

The claim ledger has 59 units. Visible numeric/outcome statements remain `VISIBLE_TEXT_ONLY_NOT_VERIFIED` or their inherited not-verified status; claim truth was not inferred. Finance/medical/beauty records remain subject to claim-unit review. Accessibility keyboard/focus/contrast/reduced-motion and runtime motion/performance were not tested, so they remain `NOT_OBSERVED` / `NOT_MEASURED`, never PASS.

## QA result

`validate_phase2_2.py`: **PASS**. Machine checks confirmed 100 unique references; 20 × 5 matrix preservation; desktop/mobile snapshot state for every reference; 200 semantic-job and 200 runtime rows; explicit missingness; 1,240 Scene rows; 1,442 indexed archive references (image members, attempt manifests, and preserved Gold archive); archive container/member integrity; observed-only provenance; derived candidate evidence/reference/brand counts; no duplicate canonical URLs; no unsupported promotion; scoped scores; and `bulk_collection_allowed = false`. Unit tests cover heading-anchored scene boundaries, semantic missingness, and observed + durable-only mechanism provenance.

## Unresolved risks and stop point

1. Twenty-seven references have no usable desktop/mobile pixels. Their durable HTTP/error records are retained; leave them `HOLD` until an approved accessible official page or fresh recapture can be reviewed.
2. 100 / 100 design agencies and campaign families remain `UNKNOWN`; the pilot does not infer independence.
3. Semantic-job absence is conservatively `NOT_OBSERVED` unless a reviewer confirms the scene is genuinely inapplicable.
4. Motion, interaction behavior, runtime accessibility, and performance were not established by static captures.
5. Mechanism families are pilot candidates. Broader pixel review and independent-reference/brand/agency gates remain before any promotion.
6. The evidence Archive has actual Library locators and pinned file versions; backend long-term availability is not guaranteed. Monthly verification and fail-closed recovery are required.

**Recommendation:** stop at PM review. Resolve or explicitly accept the 27 capture holds and inspect the candidate definitions/source crops before authorizing the next stage. **Do not begin the 2,600-reference universe.**
