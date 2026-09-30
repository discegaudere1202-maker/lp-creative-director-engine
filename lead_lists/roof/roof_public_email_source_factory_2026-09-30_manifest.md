# Roof Public Email Source Factory — Registry Manifest

- Status: checkpoint in progress; nationwide Source Discovery and extraction are not complete.
- Date: 2026-09-30
- Universe input: Sales Entity Universe, 59,086 rows.
- Durable Library path: `/LP制作事業/LeadList/Roof/RoofPublicEmailSourceFactory_2026-09-30/`

## Checkpoint counts

| Measure | Count |
|---|---:|
| Source Registry records | 18 |
| Source families | 15 |
| All瓦連 prefecture index coverage | 47 / 47 (45 show nonzero registered counts) |
| Local prefectural source territories in registry | 13 |
| Raw published-email rows before cross-source dedupe | 271 |
| Public Email Candidates | 267 |
| Unique normalized public emails | 267 |
| Safe Universe matches | 128 |
| JOIN_HOLD | 139 |
| Explicit toC source-text evidence rows | 8 |

The 8 toC evidence rows are verbatim service-description text from Kumamoto member profiles. No HIGH / MEDIUM / LOW fit determination was made.

## Productive bulk sources checked

- Japan Roof & Exterior Construction Association (RWTA), east / central / west branch lists: 70 roster entries checked, 73 published email rows before cross-source dedupe.
- Nagano Prefectural Tile Business Association: 35 email-bearing rows captured; this is a partial extraction of the larger roster.
- Kyoto Prefecture Tile Contractors Cooperative: all 61 member detail pages checked; 28 publish email.
- Osaka Prefecture Tile Commerce Cooperative: 13 email-bearing member rows extracted.
- Kumamoto Prefecture Tile Industry Cooperative: all 31 member profiles checked; 20 publish email.
- Miyazaki Central Tile Association, city-hosted 2026 roster: 14 businesses, 13 publish email.
- Yamanashi Tile Contractors Federation: all 21 roster rows checked; 9 publish email rows, with one duplicate already represented by RWTA.
- Yokohama Construction Association: 314 member rows checked; 94 carry the published building-work category whose scope includes roofing, and 80 of those publish mailto Email. Civil-work entries were excluded.

Additional no-email source directories were registered for the national All瓦連 index and association rosters in Fukuoka, Shiga, Aichi, Shizuoka, Fukui, and Gifu. Candidate discovery must continue nationally.

## QA

- Missing public_email / source URL / source_id: 0 / 0 / 0
- Invalid email strings: 0
- Duplicate candidate business + email keys: 0
- Email generation or correction: 0
- Name-only joins: 0
- Universe-outside joins: 0
- Ambiguous joins: 0
- Non-roof candidate rows: 0
- Final toC classifications: 0
- All candidates account for the 128 joined rows plus 139 JOIN_HOLD rows.

## Durable outputs

- `roof_public_email_source_registry.csv`
- `roof_public_email_candidates.csv`
- `roof_public_email_joined_candidates.csv`
- `roof_public_email_join_holds.csv`
- `roof_public_email_source_stats.json`
- `roof_public_email_source_registry.md`

This manifest records an interim checkpoint only. No Web Verification, NO_WEB / WEB_PRESENT decision, Human Verification, or Formal Master update has been performed.