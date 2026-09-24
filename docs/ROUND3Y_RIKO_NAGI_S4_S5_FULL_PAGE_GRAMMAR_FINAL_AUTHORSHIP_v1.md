# Round 3Y｜Nagi S4/S5 + Full-page Grammar Final Authorship Pass

Issue: #29  
Owner: 璃子（Research / Creative Direction + Copy）  
Baseline: PR #27 / `e03a669d6a8ee7c696840666d357372a2304c9ec`  
Baseline artifact: `10790710792`  
Status: `READY_FOR_SARAH_REVIEW — RIKO CONTRACT SCOPE`

## 0. Scope lock

This contract does **not** reopen research, strategy, scene order, service taxonomy, evidence policy, S3, S6, S7 message-draft device, S8 ending, responsive QA baseline, or production architecture.

Only the following are intentionally reopened:

1. S4 authored composition / continuation hierarchy / mobile scene entry.
2. S4/S5 customer-facing copy.
3. Minimum visible motif changes in S1/S2/S4/S5/S7/S8 required to stop the page repeatedly announcing one editorial-engine grammar.

No production code is implemented in this task.

---

# 1. Pixel diagnosis from Round 3W

The actual Round 3W artifact was reviewed before writing this contract.

### S4 desktop

The opening question and notebook media are credible, but after the image the argument disappears into a very large beige void. The three continuation paragraphs sit far down and right, so the user has to search for where the scene continues. The whitespace is therefore perceived as unresolved space, not authored silence.

### S4 mobile

At both 390 and 430 saved captures, the sticky navigation visibly crosses the opening region; at 390 it obscures the first persuasive headline line. This remains a human-visible failure even though machine geometry previously reported PASS.

### Full page

S3 is now authored and should not be reopened. The remaining page-wide problem is repeated construction: tiny meta/serial eyebrow → oversized dark Gothic heading → thin line → sparse field → isolated text link. The pattern is especially legible across S1/S2/S4/S5/S7/S8.

The correction therefore changes **motif assignment**, not the visual thesis of the whole site.

---

# 2. Final exact S4 copy

## Customer state

Before: `ヘッドスパには興味があるが、スクールを選ぶ段階ではない。やり方そのものへの興味だけが残っている。`

After: `「やり方まで知りたい」という自分の興味を認識し、スクールの存在が自分に関係する理由を持つ。分からない詳細は境界として残し、次にInstagramを見るところまで進める。`

## Final customer-facing copy

**service label**  
ヘッドスパスクール

**headline — semantic line intent**

> ヘッドスパを見ていて、  
> 「どうやっているんだろう」が残ったら。

Desktop intent: 2 lines preferred at 1440/1280; 2–3 semantic lines allowed at 1024/768. Never split `どうやっているんだろう` internally.  
Mobile intent: 3 lines allowed; the quoted question remains one semantic unit.

**body**

> ヘッドスパを見ているうちに、やり方のほうまで知りたくなることがあります。  
> なぎのみらいには、その興味の先にヘッドスパスクールがあります。  
> 何を学べるのか。受講条件はどうか。このページでは、そこまでは分かりません。  
> もう少し知りたくなったら、公式Instagramを開く。

## Why this is more human/persuasive than Round 3W

Round 3W:

> 技術そのものを知りたくなったら、なぎのみらいにはヘッドスパスクールがあります。  
> カリキュラムや受講条件は、このページでは確認できていません。  
> そこまで知りたいなら、公式Instagramを開く。

Problems in Round 3W:

- jumps from customer moment into inventory explanation (`スクールがあります`),
- uses a production/evidence sentence as the emotional center,
- ends with an abrupt instruction,
- makes the school feel like an item in a service list instead of a continuation of curiosity.

Round 3Y keeps the evidence boundary but places it **after** the customer has a reason to care. The phrase `その興味の先に` connects the business fact to the customer moment without promising curriculum, outcome, qualification, staff, or response policy.

---

# 3. Final exact S5 copy

## Customer state

Before: `ヒーリングという名前だけでは判断材料が足りず、離脱しやすい。`

After: `分からなさを無理に肯定せず、「何なのか知ってから考える」という自分の判断軸を持ち、Instagramを開くところまで進める。`

## Final customer-facing copy

**service label**  
ヒーリングサロン

**headline — preserve direction**

> ヒーリングは、  
> 分かってから考えたい。

Desktop: 2 lines. Mobile: 2 lines preferred, 3 only if needed to preserve semantic units.

**body**

> 名前だけでは、何をするものなのか、自分に関係があるのかまでは見えてきません。  
> 分かっているのは、なぎのみらいにヒーリングサロンがあること。具体的な内容は、このページではまだ分かりません。  
> 「何なんだろう」が残ったら、次に開くのは公式Instagramです。

## Why this is more human/persuasive than Round 3W

Round 3W ended with:

> そのまま選ぶより、公式Instagramを見てから考える。

That is process guidance. Round 3Y instead names the real remaining customer state — `何なんだろう` — and makes the next event explicit without claiming what the business will answer or how it will respond.

The copy does **not** add healing effects, treatment details, staff, qualifications, outcomes, price, duration, testimonials, or response policy.

---

# 4. S4 authored desktop composition contract

## Scene thesis

`Question → work surface → immediate continuation.`

S4 should feel like the moment when passive interest turns into closer inspection. The notebook image is not a decorative service image; it is the **work-surface authority** that sits between the question and the next layer of curiosity.

## 1440 geometry

Use viewport coordinates relative to the S4 section box.

- Section target visual height: `980–1040px`, not the current ~1220px.
- Section top padding: `150–170px`.
- Service label: x `104–132`, y `150–175`; readable 14–16px, not tiny serial metadata.
- Headline block: x `104–132`, y `205–235`, width `760–860px`; 48–54px type, line-height 1.20–1.28.
- Media: x `170–210`, y `360–390`, width `1020–1080px`, height `360–400px`.
- Crop: landscape work-surface crop. Keep open notebook occupying upper/left field; hand + small notebook/pencil occupy lower/right. Do not crop into a generic hand-only image.
- Disclosure `イメージ`: directly under media, aligned to media left; 12–14px; no bordered label box if the existing component allows plain text.
- Continuation body begins `38–56px` after the media/disclosure, not hundreds of pixels later.
- Body width `500–560px`, aligned around x `690–760` so it reads as the continuation of the right-side writing action, not a detached footer paragraph.
- Paragraph spacing `18–24px`; boundary sentence may use slightly lower contrast but must remain normal readable body copy.
- Final Instagram sentence remains part of the body flow; do not isolate it as a thin-underlined decorative link.
- Section bottom padding after body: `90–120px`.

## 1280 degradation

- Section height `940–1010px`.
- Headline x `72–88`, width `700–760px`, type `46–50px`.
- Media x `90–110`, width `1040–1080px`, height `350–380px`.
- Body x `620–680`, width `470–520px`.
- Keep body within 64px of disclosure/media continuation region.

## 1024 degradation

- Section height `900–980px`.
- Headline x `56–64`, width `680–760px`, type `40–44px`.
- Media x `56`, width `calc(100% - 112px)`, height `320–350px`.
- Body width `480–540px`; align right half but not flush to viewport edge.
- Body begins max `52px` below disclosure.

## 768 degradation

- Keep desktop/tablet authored relationship rather than prematurely switching to the mobile stack.
- Label/headline x `40–48`.
- Headline type `36–40px`, max width `640px`.
- Media x `40`, width `688px` max, aspect approx `1.8:1`.
- Body starts `32–44px` after media; width `430–500px`; x approx `250–280` to retain a quiet right-side continuation.
- No collision; no large empty beige area exceeding the height of the body block itself.

## Desktop fail conditions

FAIL if any of the following is true:

- S4 returns to a balanced left/right split,
- body starts more than `96px` below media/disclosure,
- the empty area between media and continuation visually exceeds the continuation body height,
- notebook becomes a small card or thumbnail,
- headline, image, and body can be read as three unrelated modules,
- the S3 composition is mirrored to make S4 “different.”

---

# 5. S4 mobile art-direction contract

## Static geometry and capture behavior are separate contracts

A CSS spacing metric alone is not sufficient. The saved human-review capture must also prove the opening copy is visible.

### Static mobile geometry — 430 / 390

- Header/sticky-nav height must be measured in the rendered DOM.
- S4 entry clearance: first visible service label **and** first headline glyph must begin at least `20px` below `nav.getBoundingClientRect().bottom` after the scene-entry scroll settles.
- S4 section top padding must therefore be `header height + 28–36px` minimum in the actual rendered state; do not hard-code a visually insufficient `156px` and assume that this proves clearance.
- Service label: plain readable label `ヘッドスパスクール`, 14–16px. The tiny `02 / 学ぶ` serial is removed from the primary mobile opening.
- Headline follows label after `16–20px`.
- Headline type: 30–33px at 430/390; line-height 1.32–1.40.
- Media begins `24–30px` after headline.
- Media at 430: width `100%`, landscape aspect `1.45–1.55:1`, edge-aligned to content or with max 8px inset.
- Media at 390: width `100vw` or `calc(100% + content gutters)` only if no horizontal overflow; shallow landscape crop, not current portrait 4:5.
- Focal point: open notebook remains clearly visible; hand/writing action sits lower-right; crop must preserve both “learning surface” and action.
- Disclosure is a quiet plain line directly under image, `8–12px` gap.
- Body begins `22–28px` after disclosure, no large empty interval.
- Body grouping: first two sentences together; unknown-boundary sentence receives `18–22px` top gap; final Instagram sentence receives `18–22px` top gap. No cards, rules, or bordered fact boxes.
- Scene exit after final sentence: `68–84px` before next scene.

### 375 / 360 / 320 degradation

- Keep the same **question → landscape work surface → compact continuation** rhythm.
- At 375/360: headline 28–31px; body 16–17px; media remains landscape, minimum aspect `1.35:1`.
- At 320: headline 26–28px; preserve quoted phrase as a semantic unit; media may become `1.25–1.35:1` but may not become portrait.
- At all widths, no semantic orphan, truncation, horizontal overflow, or fixed-header overlap.
- Do not reduce fixed-header clearance by shrinking typography alone.

## Capture/scroll protocol — human-visible acceptance

For each `430/390/375/360/320` capture:

1. Measure the actual sticky header bottom after fonts/layout settle.
2. Scroll to S4 using scene entry semantics, then offset so the S4 label/headline is intentionally framed below the nav.
3. Wait two animation frames after the final scroll.
4. Capture a **viewport screenshot** of the entry state in addition to any element screenshot.
5. Record `nav_bottom`, `label_top`, `headline_top`, and `clearance_px`.
6. PASS only if both geometry and the saved screenshot visibly show the complete opening label/headline.

A numeric PASS with a screenshot that visibly clips glyphs is automatically FAIL.

---

# 6. Full-page grammar KEEP / ALTER matrix

The goal is not “more variety.” Each scene should expose the customer moment before the engine grammar.

| Scene | Decision | Tiny eyebrow/meta | Headline treatment | Thin rule | Sparse field | Link treatment | Why |
|---|---|---|---|---|---|---|---|
| S1 | ALTER minimally | KEEP business/location context, REMOVE serial/editorial feel | KEEP hero authority but avoid same S3/S4 scale logic | REMOVE decorative thin rule | KEEP atmospheric space | Route is not an isolated underline link | Hero is orientation/recognition, not another numbered article |
| S2 | ALTER | REMOVE `02 / ...` meta; use plain section cue | Reduce headline dominance; service/customer-state rows carry authority | REMOVE thin rule dividers where decorative | Compress dead vertical space | No isolated underlined CTA | S2 is recognition density, not editorial essay |
| S3 | KEEP/FROZEN | KEEP current service cue | KEEP authored headline | KEEP only existing functional treatment | KEEP | KEEP only if already necessary | Closed strength; no redesign |
| S4 | ALTER strongly | REMOVE tiny serial from primary opening; use readable service label | Medium-large question, not giant Gothic poster | REMOVE service-label underline/rule | Replace unresolved void with immediate continuation | Final Instagram sentence stays in body flow | Learning scene should feel like closer inspection/work surface |
| S5 | ALTER | REMOVE `03 / 知る` serial from primary hierarchy | Headline can remain strong but smaller than S3; abstract media carries atmosphere | REMOVE decorative rule | Keep atmospheric field but tighten body-to-image relation | No isolated underline CTA; final sentence integrated | Uncertainty scene should feel open, not another editorial module |
| S6 | KEEP/FROZEN | KEEP | KEEP | KEEP current trust architecture | KEEP dark break | KEEP | Closed strength |
| S7 | ALTER minimally | Replace `07 / 公式Instagram` with plain `公式Instagram` if shown | Keep natural spoken headline; message-draft device is primary authority | REMOVE decorative rule | Keep enough utility space | CTA belongs to message-draft utility, not isolated underline token | This scene is functional assistance, not editorial chapter |
| S8 | ALTER minimally | Remove serial/meta if present; keep brand/contact context | KEEP ending hierarchy but do not clone S1/S3 headline treatment | REMOVE decorative rule | KEEP open ending space | Keep one clear Instagram action; no duplicate underlined secondary link | Ending should resolve, not repeat the system |

## Motif substitutions

- Serial numbers: use only where service sequence itself helps comprehension (S3 may preserve; S4/S5 do not need to announce `02/03` as engine metadata).
- Service labels: use readable plain text, not tiny eyebrow + underline pair.
- Rules: retain only where they separate actual information; remove ornamental horizontal rules.
- Headline scale: assign by authority, not global token. S3 may remain the strongest persuasive service headline. S4 = question/inspection. S5 = uncertainty/reframing. S7 = utility.
- Sparse fields: whitespace must terminate into a visible continuation; no field whose next text requires visual searching.
- Links: one scene-specific action treatment. Do not repeat isolated underlined text links after every section.

## Regression rule — no new replacement signature

FAIL if a new motif becomes mechanically repeated across three or more of S1/S2/S4/S5/S7/S8.

Examples of prohibited replacement signatures:

- every scene gets a rounded pill label,
- every scene gets a colored card,
- every scene gets a huge serif headline,
- every scene gets the same bottom-right CTA block,
- every scene gets the same image-overlap trick.

Each scene must preserve its authority source: S1 atmosphere, S2 recognition density, S3 human-scale desire, S4 work-surface curiosity, S5 uncertainty/abstract openness, S6 trust information, S7 message utility, S8 resolution.

---

# 7. Preserve / intentional / forbidden ledger

## HARD preserve

- Evidence / truth / rights boundary.
- Verified Instagram destination `@happyfuture_02`.
- CTA accessibility.
- Nine-width responsive floor.
- No overflow, truncation, or semantic orphan.
- S1–S8 semantic order.

## MATERIAL preserve

- S3 copy/editorial finish.
- S3 desktop authorship.
- S3 mobile authorship.
- S6 dark trust/authority break.
- S7 message-draft device and example-message logic.
- S8 ending function.
- Representative-media `イメージ` disclosure where required.
- Current S3/S4 non-collision gain.

## Intentional changes

- S4 copy and continuation hierarchy.
- S5 copy.
- S4 desktop geometry.
- S4 430/390/375/360/320 mobile entry/crop/rhythm.
- Motif de-systemization in S1/S2/S4/S5/S7/S8 only.

## Forbidden changes

- New service promises, curriculum, qualifications, staff facts, pricing, duration, outcomes, treatment/healing effects, reviews, response policy.
- Rewriting S3.
- Re-authoring S6.
- Removing or replacing S7 message-draft device.
- Replacing S8 ending with a generic CTA panel.
- Broad palette/brand redesign.
- Broad typography-family reset.
- New photography search or asset strategy.
- Motion expansion.

---

# 8. Rin minimum implementation specification

Implement only the delta in this document against Round 3W HEAD `e03a669d6a8ee7c696840666d357372a2304c9ec`.

## Required implementation order

1. Replace S4/S5 customer-facing copy exactly from this SSOT.
2. Rebuild S4 desktop geometry for 1440; validate continuation before responsive work.
3. Add 1280/1024/768 degradation without reverting to split-template grammar.
4. Rebuild S4 mobile 430/390 first, including actual scene-entry capture behavior.
5. Extend same mobile contract to 375/360/320.
6. Apply only the explicit motif ALTER items in S1/S2/S4/S5/S7/S8.
7. Run regression against frozen S3/S6/S7 device/S8/evidence/accessibility/9 widths.
8. Generate actual artifact and human-review captures.

## Required artifacts

- full page: 1440 and 390 minimum.
- S4 desktop: 1440/1280/1024/768.
- S4 mobile entry viewport: 430/390/375/360/320.
- S4 element captures: same mobile widths.
- S5 desktop/mobile capture.
- S1/S2/S7/S8 before/after motif comparison.
- fixed-header measurement JSON containing nav bottom + label/headline top + clearance.
- preserve/intentional/regression ledger.
- exact rendered-copy snapshot.

## Do not let implementation improvise

Rin may adjust pixel values within the stated ranges for optical balance and collision safety. Rin may **not** rewrite copy, invent new motif families, alter S3/S6, introduce new business claims, or replace the notebook media.

---

# 9. Human-regression checklist mapped to Issue #28

### HR-01 — S4 post-image void
PASS only if continuation copy is visually discoverable immediately after media; body begins within the specified continuation distance and no unresolved beige void dominates the scene.

### HR-02 — S4 mobile header obstruction
PASS only if the saved 430/390/375/360/320 entry screenshots show the complete service label and first persuasive headline glyphs below the nav. Numeric geometry alone cannot override visible clipping.

### HR-03 — S4 copy persuasion
FAIL if S4 reads as `service inventory → evidence disclaimer → instruction`.

### HR-04 — S5 copy persuasion
FAIL if S5 reads as `category explanation → missing-info disclaimer → process guidance`.

### HR-05 — repeated engine grammar
FAIL if S1/S2/S4/S5/S7/S8 still mechanically repeat tiny eyebrow + giant Gothic + thin rule + sparse field + isolated underline/link.

### HR-06 — new replacement grammar
FAIL if one new decorative motif replaces the old grammar across three or more altered scenes.

### HR-07 — S3 regression
FAIL on any material S3 copy, desktop, or mobile degradation.

### HR-08 — S6/S7/S8 regression
FAIL if S6 dark trust, S7 message-draft device, or S8 ending function weakens.

### HR-09 — safety/accessibility regression
FAIL on evidence-boundary violation, Instagram destination change, CTA accessibility loss, overflow/truncation, or semantic line orphan.

### HR-10 — collision regression
FAIL if prior S3/S4 non-collision gains regress at 1440/1280/1024/768 or any supported mobile width.

---

# 10. Riko completion claim

This document claims only that the **creative/copy correction contract is implementation-ready**. It does not claim Human G5 PASS. Human-visible quality remains downstream of Rin implementation, regenerated pixels, Aoi G5, Sarah actual-pixel/copy review, and Shun only if READY.
