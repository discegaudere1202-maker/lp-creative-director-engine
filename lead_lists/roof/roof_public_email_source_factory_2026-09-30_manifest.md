# Roof Public Email Source Factory — Registry Manifest

- Status: **CHECKPOINT_NOT_COMPLETE**; nationwide Source Discovery and extraction remain open.
- Date: 2026-10-01
- Universe input: Sales Entity Universe, 59,086 rows across 47 prefectures.
- Durable Library path: `/LP制作事業/LeadList/Roof/RoofPublicEmailSourceFactory_2026-09-30/`
- This update preserves the current checkpoint and does not mark the Source Factory COMPLETE.

## Current checkpoint

| Measure | Count |
|---|---:|
| Source Registry records | 25 |
| Source families | 22 |
| All瓦連 prefecture index coverage | 47 / 47; 45 nonzero detail routes checked |
| Local tile/roof route status | 12 EMAIL_SOURCE_FOUND; 5 CHECKED_NO_PUBLIC_EMAIL; 30 IN_PROGRESS |
| Sheet-metal route status | 3 EMAIL_SOURCE_FOUND; 1 CHECKED_NO_PUBLIC_EMAIL; 43 IN_PROGRESS |
| National MLIT public directory | Reviewed; no public Email field |
| Prefecture/municipal public-directory routes | Open in all 47 prefectures |
| Raw published-email rows before cross-source dedupe | 411 |
| Public Email Candidates | 397 |
| Unique exact public Emails | 396 |
| Safe multi-field Universe matches | 198 |
| JOIN_HOLD | 199 |
| Explicit source-text evidence rows | 19 |
| Partial Email-bearing source extractions | 1 |

Ishikawa Prefectural Sheet Metal Cooperative is newly registered as `ISHIKAWA-BANKIN`. Its official association introduction reports approximately 160 member shops. Two individual contact pages have been checked; both publish an Email. This source remains partial. One business is safely joined to the Sales Entity Universe; the other remains JOIN_HOLD.

## Productive bulk sources checked

- Japan Roof & Exterior Construction Association (RWTA), east / central / west: 70 roster entries and 73 published Email rows before cross-source dedupe.
- Nagano Tile Business Association: 55 member rows reviewed; 36 explicit Email entries captured.
- Kyoto Tile Contractors Cooperative: all 61 member detail pages checked; 28 publish Email.
- Osaka Tile Commerce Cooperative: 13 Email-bearing member rows extracted.
- Kumamoto Tile Industry Cooperative: all 31 member profiles checked; 20 publish Email.
- Miyazaki Central Tile Association, city-hosted 2026 roster: 14 businesses; 13 publish Email.
- Yamanashi Tile Contractors Federation: all 21 roster rows checked; 9 publish Email rows, with one duplicate removed.
- Yokohama Construction Association: 314 member rows checked; 94 relevant building-work entries, of which 80 publish mailto Email.
- Shizuoka Construction Association: all 110 roof-permit results and detail pages checked; 74 publish Email, with 64 distinct strings.
- Okayama Sheet Metal Cooperative: all 45 business rows checked; 26 publish Email.
- Yamaguchi Tile Cooperative: all 14 member detail pages checked; 11 publish Email.
- Wakayama Sheet Metal Cooperative: all 8 district rosters checked; 52 businesses and 21 published Email rows.
- Toyama Tile Cooperative: all 106 member detail pages checked; 5 publish Email.
- Ibaraki Sheet Metal Cooperative: all 13 branch tables checked (127 businesses); no member Email field is published.

## QA

- Missing public Email / source URL / source ID: 0 / 0 / 0
- Invalid email strings: 0
- Duplicate candidate business + Email keys: 0
- Candidate partition mismatch or overlap: 0
- Email generation or correction: 0
- Name-only joins: 0
- Universe-outside joins: 0
- Ambiguous joins accepted: 0
- Non-roof candidates: 0
- Final toC fit classifications: 0
- All 397 candidates partition into 198 joined rows plus 199 JOIN_HOLD rows.

For 新生工業, the source and Universe business name and address match after explicitly normalizing the address variant `ヶ` / `ケ`. 上出建築板金 has no multi-field Universe match and remains in JOIN_HOLD.

## Durable Library versions

| File | Version |
|---|---:|
| `roof_public_email_source_registry.csv` | 6 |
| `roof_public_email_candidates.csv` | 5 |
| `roof_public_email_joined_candidates.csv` | 5 |
| `roof_public_email_join_holds.csv` | 5 |
| `roof_public_email_source_stats.json` | 6 |
| `roof_public_email_source_registry.md` | 6 |

The stats JSON contains the 47-prefecture route ledger and explicitly records the Ishikawa extraction as partial.

## Work not performed

No Web Precheck, WEB_PRESENT / NO_WEB decision, Human Verification, final toC Fit classification, or Formal Master update has been performed. The Source Factory remains a checkpoint until every required source route is closed, all discovered Email-bearing sources are fully extracted, and final dedupe / safe JOIN / QA are complete.