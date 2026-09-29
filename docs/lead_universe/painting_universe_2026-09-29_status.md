# 塗装工事業 全国Universe Status

更新日: 2026-09-29

## SSOT

- Industry: 塗装工事業
- MLIT `gyosyu`: `17`
- Branch: `task/painting-universe-76657`
- Issue: #144
- Official reference (2026-03-31): **76,657**
- Live MLIT scrape: **77,640 permit rows**
- Prefecture coverage: **47 / 47**
- Search chunks: **94 / 94** (47 prefectures x GENERAL/SPECIAL)
- Live minus official snapshot: **+983**

The March official count is preserved as a historical snapshot. Production uses the current live MLIT search result rather than fabricating/removing records to force equality with 76,657.

## QA

- missing business name: 0
- missing address: 0
- missing permit number: 0
- missing source URL: 0
- duplicate canonical ID: 0
- prefecture coverage: 47

## Sales-entity dedupe

Permit-level Universe: **77,640**

High-confidence Sales merge: **2 records removed**

1. `RPS` -> `（株）RPS`
   - 三重県松阪市中林町404-21
   - representative: 岡田 力哉
   - old permit: 025008
   - retained permit: 025168
   - rationale: normalized name + normalized address + representative all match; current corporation is separately confirmed.

2. `リファインテック`
   - 大阪府茨木市五十鈴町16-27
   - representative: 柴口 浩光
   - old permit: 156224
   - retained permit: 165586
   - rationale: exact trade name + normalized address + representative all match.

**Sales Entity Universe V1: 77,638**

### HOLD — do not auto-merge

The following same-name/address pairs remain separate until stronger identity evidence is available:

- 小川塗装 / 岐阜県岐阜市萱場町2-14-2 / representatives differ
- 松下建設工業 -> 松下建設工業（株） / 徳島県徳島市南昭和町7-34-3 / representatives differ
- 笠原塗装工業 / 新潟県三条市北入蔵1-6-27 / representatives differ
- （有）親泊木工 vs （株）親泊木工 / 沖縄県島尻郡南風原町字津嘉山1579 / distinct legal forms; do not collapse merely by address/name

## Builder repair

Initial workflow Run `36535024581` completed all 94 MLIT searches and produced 77,640 raw rows, but the dedupe build step failed due to a one-character Python syntax error. The raw artifact remained intact.

Builder fixed in commit:
`93a787f2e2a52873d3c2717d8276a15859231344`

The repaired builder was also validated against the preserved raw artifact locally before commit and produced the counts/QA above.

## Next production gate

1. Build Public Email Source Registry for painting contractors.
2. Join public source records to the 77,638 Sales Entity Universe using strong keys only.
3. Public Email Enrichment (free sources first).
4. Auto Web Reject from explicit source website / identity-confirmed domain signals.
5. Human Verification determines NO_WEB.
6. Final Cross-Dedupe -> Formal Master.

## Hard rules

- no inferred/generated email
- public email source URL mandatory
- no name-only join
- paid API/DB/search excluded from Production V1
- automation never certifies NO_WEB
- Google Business / Maps / SNS / association profile is not an independent official website
