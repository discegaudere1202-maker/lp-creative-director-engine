# P02 / P09 / P10 Formal Blind Tournament

更新日: 2026-09-15

## 判定

| Prototype | Status | Win Rate | Desktop | Mobile | Reviewer A | Reviewer B |
|---|---:|---:|---:|---:|---:|---:|
| P02 Customer-world Translation | HOLD | 0.5833 | 0.5000 | 0.6667 | 0.7500 | 0.4167 |
| P09 Price Transparency | PASS | 0.6875 | 0.7500 | 0.6250 | 0.9375 | 0.4375 |
| P10 Customer State Transition | HOLD | 0.5833 | 0.6667 | 0.5000 | 0.9167 | 0.2500 |

## Method

Each task-specific M3 opponent set was compared at 1440×1000 and 390×844. Candidate side was randomized per pairing. The Reviewer-visible bundles contained only opaque item IDs, anonymous LEFT/RIGHT labels and screenshots; identity mapping and provenance were kept outside those bundles. Every benchmark×viewport cell received two different structured review roles:

- Reviewer A: Creative / Art Direction
- Reviewer B: Business Owner / Conversion

These are structured internal Work review roles, not independent human-third-party evidence.

## Benchmark-level result

### P02

- kagami: candidate 0.1250 — clear loss
- smarthr-product: candidate 0.7500 — strongest relative result
- kintone-product: candidate 0.8750 — candidate leads on situation framing

The candidate's strongest axes were Owner Specificity (1.0000), Mobile Quality (0.7083), Emotional Pull (0.7083) and Share Impulse (0.6667). Weakest were Trust (0.0000) and Conversion Intent (0.2500). The first improvement added a visible situation-based consultation entry and raised the result from 0.5417 to 0.5833, but did not clear PASS.

### P09

- aki-design-price: candidate 0.8750
- jimdo-hp-pack: candidate 0.6250
- rals-homepage-price: candidate 0.8750
- studio-price: candidate 0.3750 — strongest opponent

The candidate won on Distinctness (1.0000), Owner Specificity (1.0000), Share Impulse (0.9062) and Craft Detail (0.8438). The remaining ceiling is Conversion Intent (0.3125), with Trust at 0.5000; the result passes overall because price clarity and authored specificity consistently outperformed the selected set.

### P10

- carigaku-career: candidate 0.3750 — clear loss
- sell-step-career: candidate 0.6250
- lfu-career: candidate 0.7500

The candidate won on Owner Specificity (1.0000), Distinctness (0.8750) and Share Impulse (0.8750). Weakest axes remain Conversion Intent (0.4583), Trust (0.3333) and Mobile Quality (0.5833). The second improvement made the mobile CTA fully visible inside 390×844 and raised Conversion Intent from 0.2083 to 0.4583, but the business-owner role still scored only 0.2500.

## Research rules extracted

1. A conceptually strong hero does not compensate for a missing or delayed next action.
2. Owner Specificity and Share Impulse can be strong while Trust and Conversion Intent remain below a competitive threshold.
3. A single factual Craft Catch can create a stronger pricing decision aid when it is tied to the actual product/specification.
4. Mobile re-art must include the action timing, not only the copy order and crop.
5. P02 and P10 remain BENCHMARK_CHALLENGED. P09 is the only prototype eligible for COMPETITIVE promotion because it is reproducible, has 9-width runtime QA PASS, and passed the formal tournament.

## Evidence

- Candidate Capture Run 5: run 34958882921, artifact 10392184712, digest sha256:41f7108ab3ea5aba678329f076bd7da28377cf6a5834477220762dd6f4c60d6c
- Candidate head SHA: 86d8de0c562085e91842bd1215f0014b770dd8ea
- Benchmark Run 6 Artifact: 10388641096, digest sha256:7cb1a74e24fa279af155310e0ddb4b027498b27de1ebd559bd8711993830e8fa
- Benchmark Run 8 Artifact: 10389977402, digest sha256:b582e809bb4464c437ac0094ec239f1f0e4bfc266057a9950beb377c741acaee
- QA Run 227: 34958882870, conclusion success
