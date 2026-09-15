# Enriched Evidence Trust Validation — 2026-09-15

## 結論

P02/P10とも、既存のSales Sample構造を保ったまま実在Company EvidenceをCTA Zoneへ接続すると、今回のStructured Work ReviewではTrustとConversion Intentが改善した。P02はTrust 0.3333→0.6250、P10は0.3333→0.5417。Creative側の主要軸とMobile Qualityは低下しなかった。

これは2候補・1回の正式Structured Reviewでの観測であり、一般則のVALIDATEDや本番Engine実装完了を意味しない。

## Research question

Owner Specificityが高くてもTrustが低いのは、会社らしさが「誰の何か」を示すだけで、「相談時に何が起き、どの時点で判断できるか」まで接続されていないためである。Enrichedでは、固有事実を単独バッジにせず、WHO → HOW → NEXTへ接続した。

## Verified Evidence Ledger

| Variant | Verified and used | Strength | Placement |
| --- | --- | --- | --- |
| P02 | 緒方幸一／社労士、20年・300社以上、問い合わせ→内容確認→サービス説明・見積→納得後契約 | E2/E5 | 既存の翻訳構造を邪魔しないCTA直前 |
| P10 | 価値観整理からの伴走、公式プロフィール掲載の宮原彩乃、転職後も無料でキャリア伴走 | E2/E3/E4 | 状態遷移を保ったCTA Zone |

P02の公式根拠は[代表挨拶](https://www.mahora-sr.jp/page_001.html)、[トップの業務・相談案内](https://www.mahora-sr.jp/)、[契約までの流れ](https://www.mahora-sr.jp/page_009.html)および[スポット相談](https://www.mahora-sr.jp/page_008.html)。P10の公式根拠は[公式LP](https://www.tsubudateru.com/lp)、[サービス一覧](https://www.tsubudateru.com/service)、[公式プロフィール](https://www.tsubudateru.com/member/ayano-miyahara)。

## Formal Enriched Tournament

両方とも全Opponent、1440×1000／390×844、2 structured review roles、10 axes、score／provenance／identity maskingを満たした。

| Variant | Win Rate | Trust | Conversion | Business role | Desktop | Mobile |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P02 Enriched | 0.7083 | 0.6250 | 0.6250 | 0.6667 | 0.5833 | 0.8333 |
| P10 Enriched | 0.7083 | 0.5417 | 0.5417 | 0.5000 | 0.7500 | 0.6667 |

### Opponent results

- P02: kagami 0W/3T/1L; smarthr-product 3W/1T/0L; kintone-product 3W/1T/0L.
- P10: carigaku-career 1W/2T/1L; sell-step-career 2W/2T/0L; lfu-career 3W/1T/0L.

P09は未変更で、既存0.6875／COMPETITIVEを維持する。

## Hypotheses and observed rules

1. **WHO-HOW-NEXT Bridge** — Identity evidence is weak when it ends at a name or credential; it becomes useful when adjacent to the first real service action and decision boundary.
2. **Proof Before Ask** — Put one verifiable operational proof before the action so the CTA answers “why this company?” before asking for contact.
3. **Decision Boundary CTA** — “相談してよい” is not enough; the CTA must show the next decision boundary (P02:納得後契約、P10:相談・整理から).
4. **Evidence Economy** — One or two strong facts plus a company-specific process beat a volume of cards/FAQ.
5. **Unknown Boundary** — An absent privacy, solicitation, response-time or guarantee fact remains UNKNOWN and becomes a future hearing slot.
6. **Mobile Action Budget** — Evidence must be re-art-directed so the 390px action remains visible; all 9 widths are runtime-checked for overflow and action integrity.

Rules 1–5 are OBSERVED/HYPOTHESIS, not fully validated. PROOF_TO_PROCESS, AFTER_CLICK_CERTAINTY, EVIDENCE_ECONOMY, MOBILE_ACTION_BUDGET are ENGINE_READY_CANDIDATE only; Production Engine implementation is deliberately out of scope.

## Evidence Strength Model

- E1 Weak: generic explanation; do not use as Trust proof.
- E2 Specific: company-specific identity, credential, experience, scope.
- E3 Operational: shows what actually happens.
- E4 Risk Reducing: directly lowers customer downside or anxiety.
- E5 Decision Enabling: supports a concrete next-step decision.

## Hearing Requirements

### REQUIRED

Responsible person/team; scope and exclusions; first action and post-click flow; fee/free condition or explicit UNKNOWN; source/provenance for every claim.

### HIGH_VALUE

Response expectation; method/time/place; confidentiality/privacy; solicitation policy; what happens if the customer does not contract or change jobs; customer choices and refusal boundary; owner voice; verified case/testimonial.

### OPTIONAL

Rights-cleared portrait; verified metrics; detailed result case; office/place photo.

## Rejected / UNKNOWN

No owner portrait was used because reuse permission was not confirmed. P02 confidentiality/privacy wording, reply time, non-contract treatment and non-phone flow were UNKNOWN. P10 assigned consultant, consultation duration, reply/interview flow, privacy/confidentiality and no-pressure policy were UNKNOWN. No testimonials, metrics, guarantees or claims of “no solicitation” were added.

## Next decision

最優先はA（Evidence研究をさらに継続）。今回の2候補では同じ方向の改善が観測されたが、サンプル数が少なく、P10 Business roleは0.5000、P02 desktopは0.5833で境界に近い。次はTrust Core／Fullの小規模ablationまたは追加候補で再現性を確認してから、Engine実装やGolden Sample 03へ進む。
