# Round 3V｜Nagi Final Narrow Authorship Correction

Task Issue: #24  
Owner: 璃子（Research / Creative Direction）  
Parent PM: Issue #3 Sarah Orchestration Protocol  
Implementation baseline: Issue #21 / PR #22 / `1f0bed6f90212a35cec7e1ea560dd071612a4a0d`  
Artifact reviewed directly: `10788443033` / `sha256:5c7b679607e24ffd034e3a04700d0bd4bb575f395f0515ce9547bc8672290eeb`  
Human return source: Issue #23 / Round 3U Aoi G5 = RETURN  
Status: `READY_FOR_SARAH_REVIEW — RIKO CONTRACT SCOPE`

---

## 0. Scope lock

Round 3V is a **final narrow authorship correction**, not a redesign and not a new research phase.

Frozen:

- S1–S8 order and persuasion architecture
- service taxonomy
- verified Company Truth / evidence boundary
- representative-media role
- S6 dark trust / authority break
- S7 message-draft visual device
- S8 ending
- verified Instagram conversion destination
- generic QA baseline and 9-width responsive floor

Only these surfaces may change:

1. customer-facing copy in S1 / S2 / S3 / S4 / S5 / S7
2. S3 / S4 desktop composition
3. S3 / S4 mobile art direction
4. micro-spacing needed to implement the exact new copy without semantic-orphan or collision regression

No production code is implemented in this task.

---

# 1. Round 3U blocker → Round 3V correction map

| Issue #23 human blocker | Round 3V correction | Rin must prove with |
|---|---|---|
| S3 headline repeated verbatim as first body sentence | S3 body is rewritten to advance the customer tension instead of restating the headline | normalized headline/body first-sentence inequality + rendered copy snapshot |
| S1/S2 expose directory / UX-navigation grammar | S1 opens on one customer truth; S2 names inner states without telling the user how to operate the page | exact-copy assertion + forbidden UX phrase scan |
| S4/S5 lost customer-moment specificity | S4 restores the concrete `どうやっているんだろう` moment; S5 names the specific uncertainty around Healing without inventing content/effect | exact-copy assertion + evidence-safety scan |
| S7 sounds system-authored | natural spoken Japanese replaces `うまく聞こうと、しなくて大丈夫。`; message-draft device remains | exact-copy + unchanged message-draft structure |
| S3/S4 are safe mirrored splits | S3 becomes a quiet text-led scene that lands in a low/right image field; S4 becomes headline → central work-surface → below-image continuation | 1440 scene captures + layout-signature assertions |
| Mobile S3/S4 are stacked desktop reductions | S3 ends in a full-bleed quiet image; S4 is media-first with an attached solid headline field | 390 scene captures + DOM visual-order assertions |
| S4 mobile label is hidden by fixed header | explicit fixed-header clearance and bounding-box acceptance | scroll-to-scene nav/label collision assertion |

---

# 2. Final exact customer-facing copy SSOT

The strings below are the final customer-facing copy for Rin. Do not paraphrase them during implementation.

`｜` below marks an authored semantic line boundary for headings. It is **not** a literal glyph to render.

## S1 — Hero

### Final

**Eyebrow**

`なぎのみらい｜福岡市`

**Headline**

`「休みたい」から始まって、｜やり方まで知りたくなることもある。`

Desktop preferred line shape:

> 「休みたい」から始まって、  
> やり方まで知りたくなることもある。

390 preferred line shape:

> 「休みたい」から始まって、  
> やり方まで  
> 知りたくなることもある。

**Lead**

> ドライヘッドスパを受ける。  
> ヘッドスパの技術を学ぶ。  
> ヒーリングは、内容を知ってから考える。  
>  
> 福岡市のなぎのみらいには、その3つがあります。

**Route labels — preserve**

`受ける / 学ぶ / 知る`

### Round 3T → Round 3V comparison

Round 3T:

> 今日は受けたい。  
> いつか学びたい。  
> ヒーリングは、まず知りたい。

and

> なぎのみらいには、ドライヘッドスパ、ヘッドスパスクール、ヒーリングサロンという三つの入口があります。

Round 3V changes the hero from a symmetric three-service inventory into **one customer transition**: interest can start in rest and move toward technique. The Lead carries the business width. This removes the directory tone while still making the three verified services explicit.

Evidence class:

- headline = CUSTOMER HYPOTHESIS
- service statements = FACT
- Healing framing = CUSTOMER-SIDE DECISION FRAME
- location = FACT
- no Business Policy Claim

---

## S2 — Recognition, not navigation

### Final

**Eyebrow**

`02 / いま近い気持ち`

**Intro**

> いま欲しいのは、休む時間か。  
> 技術を知ることか。  
> ヒーリングの中身か。

**Card 1**

Label: `受ける`  
Primary: `今日は、何もしない時間がほしい。`  
Service: `ドライヘッドスパ`

**Card 2**

Label: `学ぶ`  
Primary: `受けるうちに、やり方まで気になってきた。`  
Service: `ヘッドスパスクール`

**Card 3**

Label: `知る`  
Primary: `ヒーリングは、名前だけでは判断できない。`  
Service: `ヒーリングサロン`

**Closing line**

Delete the Round 3T closing line. Do not replace it.

### Round 3T → Round 3V comparison

Delete:

> 同じ日に全部を決める必要はありません。いま一番近い気持ちから、その先を読めます。

Delete:

> ひとつに決めなくて大丈夫。近い入口から、先へ。

Those lines explain how to use the page. The new copy names what the customer may actually want and stops. The cards perform recognition; the page does not tell the customer how to navigate itself.

Evidence class:

- primary card copy = CUSTOMER HYPOTHESIS
- service names = FACT
- no acceptance / welcome / response policy

---

## S3 — Receive / Dry Head Spa

### Final

**Eyebrow**

`01 / 受ける`

**Service label**

`ドライヘッドスパ`

**Headline**

`一日が終わっても、｜頭の中だけ｜切り替わらない日がある。`

1440 preferred:

> 一日が終わっても、  
> 頭の中だけ  
> 切り替わらない日がある。

390 preferred:

> 一日が終わっても、  
> 頭の中だけ  
> 切り替わらない日がある。

**Body**

> もう何かを足すより、何もしない時間を取りたくなる。  
>  
> ドライヘッドスパを探したくなるのは、そんなときかもしれません。

### Round 3T → Round 3V comparison

Round 3T incorrectly begins the body with the headline verbatim:

> 一日が終わっても、頭の中だけ切り替わらない日がある。

That line is **deleted from the body**. The new first body sentence advances from recognition to desire: the customer does not need the same diagnosis twice; the body now explains what the moment makes them want without claiming treatment effects.

Evidence class:

- all primary copy = CUSTOMER HYPOTHESIS
- Dry Head Spa name = FACT
- no effect claim

---

## S4 — Learn / Head Spa School

### Final

**Eyebrow**

`02 / 学ぶ`

**Service label**

`ヘッドスパスクール`

**Headline**

`ヘッドスパを見ていて、｜「どうやっているんだろう」が残ったら。`

1440 preferred:

> ヘッドスパを見ていて、  
> 「どうやっているんだろう」が残ったら。

390 preferred:

> ヘッドスパを見ていて、  
> 「どうやっているんだろう」が  
> 残ったら。

**Body**

> 技術そのものを知りたくなったら、なぎのみらいにはヘッドスパスクールがあります。  
>  
> カリキュラムや受講条件は、このページでは確認できていません。  
>  
> そこまで知りたいなら、公式Instagramを開く。

### Round 3T → Round 3V comparison

Replace:

> 受けるだけでは、足りなくなったら。

with the observed customer-moment language:

> ヘッドスパを見ていて、「どうやっているんだろう」が残ったら。

The Round 3T line can be read as “learning is superior to receiving” and is abstract. The Round 3V line names the exact moment when attention shifts from experience to technique. It creates forward curiosity without adding outcomes such as qualification, work, opening a business, or income.

Replace the generic explanatory body with one clear bridge to the verified school fact, one explicit UNKNOWN boundary, and one bounded customer action. `公式Instagramを開く` does not promise what Nagi will answer or that the unknown facts are published there.

Evidence class:

- curiosity = CUSTOMER HYPOTHESIS
- school existence = FACT
- curriculum / conditions unavailable on this LP = EVIDENCE BOUNDARY
- Instagram action = INVITATION to verified route
- no Business Policy Claim

---

## S5 — Know / Healing

### Final

**Eyebrow**

`03 / 知る`

**Service label**

`ヒーリングサロン`

**Headline**

`ヒーリングは、｜分かってから考えたい。`

**Body**

> 名前だけでは、何をするのかも、自分に関係があるのかも判断しにくい。  
>  
> なぎのみらいには、ヒーリングサロンがあります。  
>  
> 具体的な内容は、このページでは確認できていません。  
>  
> そのまま選ぶより、公式Instagramを見てから考える。

### Round 3T → Round 3V comparison

Replace:

> 分からないまま、選ばなくていい。

The Round 3T line is safe but could appear on almost any low-evidence service LP. Round 3V keeps the same agency but attaches it directly to `ヒーリング`, where the uncertainty actually exists.

The body no longer treats “permission not to decide” as the destination. It moves from the unclear category name → verified Nagi service existence → explicit UNKNOWN → a bounded next action, while making no Healing effect claim.

Evidence class:

- uncertainty = CUSTOMER HYPOTHESIS
- Healing Salon existence = FACT
- detailed contents unavailable on this LP = EVIDENCE BOUNDARY
- Instagram action = INVITATION to verified route
- no Healing effect / policy claim

---

## S7 — Action / message draft

### Final

**Eyebrow**

`07 / 公式Instagram`

**Headline**

`何て送ろう、と迷ったら。｜聞きたいことを、一文だけ。`

Preferred line shape:

> 何て送ろう、と迷ったら。  
> 聞きたいことを、一文だけ。

**Body**

> 言葉に迷うときの参考に、たとえば。

**Message draft examples — preserve meaning**

> 「ドライヘッドスパについて聞きたいです」  
> 「スクールについて知りたいです」  
> 「ヒーリングについて、内容を確認したいです」

**Message draft footer**

`こんな一文から。`

**Aside**

Delete the Round 3T aside completely. Do not replace it.

**CTA — preserve**

`公式Instagramを開く ↗`

### Round 3T → Round 3V comparison

Replace:

> うまく聞こうと、しなくて大丈夫。

The comma and construction are unnatural spoken Japanese and sound machine-edited. The new line starts from the actual friction — `何て送ろう` — then reduces the next decision to one sentence.

Delete:

> まだ決めきれていなくても、いま知りたいことから始められます。

It reads like an unverified acceptance policy and repeats the “permission” pattern. The draft examples themselves already reduce action friction, so the surface copy should stop there.

Evidence class:

- message examples = CUSTOMER-SIDE EXAMPLE
- CTA destination = VERIFIED FACT / INVITATION
- no promise of response, consultation acceptance, pricing answer, or booking handling

---

# 3. Copy hard rules for Rin

1. S3 normalized headline must not equal the first body sentence.
2. Do not restore any of these Round 3T phrases:
   - `その先を読めます`
   - `近い入口から、先へ`
   - `決めきれていなくても大丈夫`
   - `うまく聞こうと、しなくて大丈夫`
   - `受けるだけでは、足りなくなったら`
   - `分からないまま、選ばなくていい`
3. `このページでは確認できていません` is allowed only as an evidence boundary. It must not be converted into “Instagramで回答してもらえます” or similar policy.
4. Do not add: prices, duration, staff, qualifications, outcomes, school curriculum, treatment effects, Healing effects, reviews, proprietary method, opening/career/income claims.
5. Do not mechanically insert line breaks by character count. Preserve the semantic chunks above; natural reflow between chunks is acceptable at narrower widths.
6. No sentence may exist only to explain how to operate the LP.

---

# 4. S3 desktop authored composition contract

## 4.1 Scene thesis

**Customer moment:** the day is over, but the mind has not switched off.  
**Visual job:** create a sense of *stopping after the thought*, not a product/service showcase.  
**Media job:** the representative resting-hands image is a quiet landing field after the copy, not proof and not a side-by-side product card.

The S3 authored idea is:

> **text resolves first → the page lowers its visual center of gravity → the image becomes the scene exit.**

This is intentionally not a left-copy/right-photo split.

## 4.2 1440 geometry

Scene background: preserve the current pale green family; no new gradient plane, diagonal decoration, card, border, or rule ornament.

Scene minimum visual height: `1060–1120px` excluding the fixed site nav.

Coordinates are relative to the S3 scene box.

- scene horizontal content inset: `96px` left / `72px` right
- eyebrow/service block:
  - x `100–360`
  - y `132–204`
- headline:
  - x `100`
  - y starts `226 ± 12`
  - max width `720px`
  - target rendered size `56–62px`
  - weight `600–640`
  - line-height `1.12–1.18`
  - no all-page “giant Gothic” override
- body:
  - x `100`
  - starts `32–40px` after headline box
  - max width `520px`
  - `17–19px`, line-height `1.85–1.95`
- representative media:
  - x begins `44%–46%` of scene width (`≈634–662px` at 1440)
  - right edge `≤ 72px` from scene edge
  - y begins `560–600px`
  - width `50–51%` of scene width
  - rendered height `410–450px`
  - **horizontal crop**, no rotation, no clip-path, no shadow plane
  - `object-fit: cover`
  - focal target: the hands remain completely legible; source focal region around `x 50–56% / y 60–72%`
  - recommended `object-position: 52% 66%`
- disclosure:
  - outside the text field
  - anchored `12–16px` below or above the media’s left edge
  - must say `イメージ`
  - must not cover the hands

Collision rule at 1440:

- headline/body box and media box must have either `>=64px` horizontal gap when their y-ranges overlap, or `>=48px` vertical gap when x-ranges overlap.
- no text may be painted over the photo.

## 4.3 Why this is authored for the moment

The customer has just named an overstimulated end-of-day state. A mirrored split asks them to process copy and photo simultaneously. S3 instead lets the thought finish, then lets the image close the scene. The visual pause is the persuasion mechanism; no unsupported “relaxation effect” needs to be written.

## 4.4 S3 desktop degradation

### 1280

- headline max width `680px`
- media x `42%`, width `53%`, height `400–430px`
- minimum text/media gap `56px`
- same lower-right landing logic; do not convert to two equal columns

### 1024

- headline max width `620px`
- body max width `500px`
- media width `68–72%`, aligned right, after the body
- minimum vertical gap `40px`
- horizontal crop remains; no portrait-card fallback

### 768

- order: meta/service → headline → body → media → disclosure → scene exit
- media width `76–84%`, aligned right, not a 50/50 split
- aspect ratio `16:9–1.7:1`
- minimum gap body→media `36px`
- no overlap and no rotation

---

# 5. S4 desktop authored composition contract

## 5.1 Scene thesis

**Customer moment:** attention moves from “receiving” to “how it is done.”  
**Visual job:** make the work/study surface itself the center of the scene.  
**Media job:** the notebook/hand representative image is a **field of attention**, not an illustration placed beside copy.

The S4 authored idea is:

> **question → work surface → information boundary / next action.**

This is intentionally different from S3 and must not mirror it.

## 5.2 1440 geometry

Scene background: preserve current warm neutral family. No diagonal clipping, no repeated thin-rule decoration, no card grid.

Scene minimum visual height: `1180–1260px` excluding fixed nav.

- eyebrow/service block:
  - x `100–420`
  - y `132–204`
- headline:
  - x `100`
  - starts `220 ± 12`
  - max width `900px`
  - target size `48–54px`
  - weight `600–640`
  - line-height `1.14–1.20`
- representative media — **central work surface**:
  - x `12–13%` (`≈173–187px`)
  - y `392–420px`
  - width `74–76%` (`≈1065–1095px`)
  - height `490–520px`
  - no tilt, no clip-path, no shadow card
  - `object-fit: cover`
  - use a **wide crop** that keeps the open notebook as the dominant field and the writing hand visible on the right-lower quadrant
  - recommended focal target: `x 48–55% / y 35–50%`
  - recommended `object-position: 52% 43%`
- disclosure:
  - inside the media’s upper-left safe corner with an opaque disclosure chip, or immediately above the media left edge
  - never over the writing hand
- body:
  - begins only **after** the media field
  - x `52–55%` of scene width (`≈750–790px`)
  - max width `500px`
  - top `media.bottom + 34–42px`
  - `17–19px`, line-height `1.85–1.95`

No headline/body sits beside the image as a balanced second column.

## 5.3 Why this is authored for the moment

The notebook image already contains the strongest visual cue available for “attention shifting to technique.” Making it the central field allows the customer to move from the question in the headline into a work/study visual before encountering the unknown boundary. This is a specific persuasion sequence, not a stylistic alternation from S3.

## 5.4 S4 desktop degradation

### 1280

- headline max width `820px`
- media x `8%`, width `84%`, height `460–500px`
- body x `50%`, max width `500px`
- body remains below media

### 1024

- headline max width `760px`
- media x `5.5%`, width `89%`, height `420–460px`
- body max width `540px`, aligned right after media
- minimum media→body gap `36px`

### 768

- order: meta/service → headline → media → disclosure → body
- media width `100%` of inner scene width
- aspect ratio `16:9–1.75:1`
- body max width `560px`, margin-left `auto`
- no overlap, no mirrored left/right split

---

# 6. 390px mobile re-art-direction

## 6.1 Shared fixed-header rule

Current fixed nav is approximately `60px` high. Both S3 and S4 must be authored so their scene entry survives an actual scroll/capture with the nav fixed.

Implementation contract:

- `scroll-margin-top: 60px` minimum on `#s3` and `#s4`
- scene inner top padding at 390: `156px` minimum
- after `scene.scrollIntoView({block:'start'})`, the first customer-visible eyebrow must satisfy:
  - `eyebrowRect.top >= navRect.bottom + 20px`
- the service label must also be fully below the nav
- no negative translate may move the label back under the header

This exact bounding-box condition is required because Round 3T’s saved S4 capture visibly failed despite machine-green collision metrics.

---

## 6.2 S3 mobile — quiet landing rhythm

**390 order**

1. `01 / 受ける`
2. `ドライヘッドスパ`
3. headline
4. complete S3 body
5. full-bleed representative image
6. disclosure
7. scene-exit whitespace

This is **not** headline → image → body. The thought is completed before the visual pause.

Geometry at 390:

- horizontal text inset `22px`
- top padding `156px`
- headline `32–35px`, line-height `1.24–1.30`, max 3 semantic lines
- headline→body `22–26px`
- body line-height `1.85–1.95`
- body→media `32–38px`
- media:
  - true viewport-width bleed: `100vw`
  - use `margin-left: calc(50% - 50vw)` or equivalent without creating document overflow
  - aspect ratio `1.55–1.65:1`
  - no rotation / clip-path / shadow
  - `object-position: 52% 66%`
  - hands must remain visible, not cropped at fingers/wrists
- disclosure:
  - below image, left aligned to text inset
  - `8–12px` image→disclosure
- disclosure→scene exit whitespace `48–64px`

Psychological rhythm:

**recognition → desire → quiet visual landing.**

Do not append another explanatory tail after the image.

---

## 6.3 S4 mobile — media-first curiosity rhythm

S4 must be materially different from S3.

**390 order**

1. `02 / 学ぶ`
2. `ヘッドスパスクール`
3. inset-right representative media
4. disclosure chip
5. solid-background headline field attached across the image’s lower-left edge
6. body
7. scene-exit whitespace

The headline field may overlap the image **only as a solid scene-background block**. Text itself must never render directly on photography.

Geometry at 390:

- scene horizontal text inset `22px`
- top padding `156px`
- media:
  - width `342–348px`
  - right aligned
  - left inset `20–26px`
  - aspect ratio `4:5`
  - `object-fit: cover`
  - `object-position: 50% 42%`
  - keep open notebook visible; writing hand remains in lower/right field
  - no tilt / clip-path / shadow
- disclosure:
  - solid opaque chip inside media at `12px` from top/left
  - must remain legible at 320
- headline field:
  - width `calc(100% - 24px)`
  - margin-top `-32px` to `-38px`
  - z-index above media
  - background exactly the S4 scene background, not white card stock
  - no radius / border / shadow
  - padding `22px 18px 8px 0`
  - headline `29–32px`, line-height `1.26–1.32`
- headline→body `16–20px`
- body line-height `1.85–1.95`
- final body→scene exit `64–76px`

Psychological rhythm:

**see the work surface → recognize the question → understand what is known/unknown → choose whether to open Instagram.**

This visual order is intentionally the inverse of S3’s text-led landing.

---

# 7. Mobile degradation rules

## 430

S3:

- text inset `24px`
- media remains `100vw` full bleed, aspect `1.65:1`
- headline max `36px`

S4:

- media width `366–374px`, right aligned
- left inset `32–40px`
- overlap headline field `36px`
- headline max `33px`

## 375

S3:

- text inset `20px`
- media full bleed, aspect `1.55–1.60:1`
- headline `31–33px`

S4:

- media width `330–336px`, right aligned
- headline field overlap `30–34px`
- headline `29–31px`

## 360

S3:

- text inset `18px`
- media full bleed, aspect `1.52–1.58:1`
- headline `30–32px`

S4:

- media width `318–326px`, right aligned
- overlap `28–32px`
- headline `28–30px`

## 320

S3:

- text inset `16px`
- media full bleed, aspect `1.45–1.55:1`
- headline `27–29px`
- no line-chunk narrower than its semantic phrase

S4:

- media width `286–294px`, right aligned
- aspect `4:5`
- overlap reduced to `22–26px`
- headline `26–28px`
- headline field remains solid and does not become an editorial card

All mobile widths:

- page `scrollWidth <= innerWidth`
- no semantic orphan / one-character final line caused by forced breaks
- S3 and S4 must remain visibly different in order and media treatment

---

# 8. Background / transition handling

No new background strategy is introduced.

Preserve:

- S3 pale green customer-rest field
- S4 warm learning field
- S5 current cool-light transition
- S6 dark authority break

Do **not** add transition wedges, diagonal planes, ornamental rules, gradients, or floating cards to signal scene difference. The S3/S4 difference must come from **customer-moment choreography**, not decoration.

S3 exits on image/whitespace. S4 exits on copy/whitespace. That difference is intentional.

---

# 9. Rin minimum implementation instructions

Rin must implement only the following targeted delta against Round 3T:

1. Replace S1/S2/S3/S4/S5/S7 customer copy with the exact strings in §2.
2. Preserve S6 copy and pixels unless a mechanical responsive adjustment is strictly required; any visual restyle is forbidden.
3. Preserve S8 copy and pixels unless a mechanical responsive adjustment is strictly required; any visual restyle is forbidden.
4. Preserve the S7 message-draft component DOM / layout / visual device. Change only its customer-facing words specified here.
5. Replace S3 desktop split layout with §4 lower-right landing-field composition.
6. Replace S4 desktop split layout with §5 headline → central work-surface → below-image body composition.
7. At mobile, implement §6 independently rather than deriving both scenes from one shared stack CSS rule.
8. Add explicit fixed-header/scene-entry collision QA.
9. Keep representative-media disclosure visible and readable.
10. Do not introduce new assets, claims, service facts, or creative motifs.

Implementation may use scene-specific classes. It should **not** generalize these two scene arrangements into a new global engine template in this narrow fix.

---

# 10. Preserve / intentional-change / forbidden-change ledger

## HARD preserve

- generic QA baseline remains green
- verified Instagram target `@happyfuture_02`
- evidence / truth / rights boundary
- representative media stays non-evidentiary and disclosed
- 9-width no-overflow/no-truncation/no-semantic-orphan floor
- CTA keyboard/focus/accessibility behavior
- S1–S8 order

## MATERIAL preserve

- S2 spacing/density gain; micro-height may change for new copy
- S6 dark trust/information authority break
- S7 message-draft visual device
- S8 ending
- current S3/S4 non-collision gain

## INTENTIONAL change

- S1/S2/S3/S4/S5/S7 exact copy
- S3 1440/1280/1024/768 geometry
- S4 1440/1280/1024/768 geometry
- S3/S4 mobile order, crop, scale, scene-entry spacing and disclosure placement

## FORBIDDEN change

- new research / new service taxonomy / new persuasion architecture
- fake founder/staff/customer/premises/proof
- price, duration, qualification, curriculum, outcome or effect claims
- stronger booking/consultation/response promise than verified evidence supports
- changing S6/S8 for “consistency”
- removing S7 message-draft device
- restoring mirrored alternating split layouts
- solving mobile by one generic `text → image → body` rule for both scenes
- engine-signature decoration: repeated giant Gothic, thin-rule ornament, automatic diagonal planes, generic editorial cards

---

# 11. Human-regression acceptance checklist

These are **fail-closed acceptance criteria** for Rin / Aoi / Sarah.

### AC-01 — S3 duplicate-line regression

FAIL if normalized S3 headline text equals S3 first body sentence, or if the first body sentence contains the full normalized headline verbatim.

### AC-02 — Customer-visible UX grammar regression

FAIL if S1/S2 restores page-operation phrases such as:

- `その先を読めます`
- `読み進めて`
- `近い入口から、先へ`
- `同じ日に全部を決める必要はありません`

Evidence-boundary wording such as `このページでは確認できていません` is not a UX failure.

### AC-03 — Mirrored split regression

At 1440, FAIL if S3 and S4 both resolve into balanced left/right two-column compositions with media occupying one column and copy the other.

Required visible distinction:

- S3: text-led upper/left field → lower/right image landing
- S4: top question → central wide work surface → below-image body

### AC-04 — Mobile fixed-header regression

At 430/390/375/360/320, after programmatically scrolling S3/S4 to scene start, FAIL if the first eyebrow or service label intersects the fixed nav rectangle.

Required: `eyebrow.top >= nav.bottom + 20px` at 390 and `>= nav.bottom + 16px` at the other mobile widths.

### AC-05 — Same mobile stack regression

FAIL if both S3 and S4 produce the same DOM/visual order `headline → image → body`.

Required:

- S3: meta/service → headline → body → full-bleed image → disclosure → exit
- S4: meta/service → inset image → disclosure → attached solid headline field → body → exit

### AC-06 — Safe-but-generic copy regression

FAIL if implementation substitutes the exact S4/S5 customer-moment copy with the weaker Round 3T generic lines:

- `受けるだけでは、足りなくなったら`
- `分からないまま、選ばなくていい`

or with new generic Permission copy that removes `ヘッドスパ / ヒーリング` specificity.

### AC-07 — Preserve regression

FAIL on any unauthorized S6 or S8 copy/visual change, removal of S7 message-draft device, wrong Instagram destination, missing disclosure, CTA accessibility regression, or evidence-boundary expansion.

### AC-08 — Non-collision regression

At 1440/1280/1024/768, text may not render directly over representative photography. Any intended solid-background S4 headline-field overlap is allowed only if the field fully occludes the image behind every glyph.

### AC-09 — Semantic-line regression

At all 9 widths, FAIL on overflow, truncation, orphaned Japanese particles, isolated one-character semantic fragments, or character-count-driven forced breaks.

### AC-10 — Engine-signature regression

FAIL if the correction introduces a new repeated motif across S3 and S4 merely to create difference: matching diagonal clips, matching tilt, matching thin-rule frames, matching card shells, or matching giant-heading treatment.

---

# 12. Riko contract QA performed

- Issue #24 re-read as SSOT.
- Issue #23 Aoi RETURN inspected line-by-line.
- Round 3T PR #22 source inspected for exact current copy and composition logic.
- Artifact `10788443033` downloaded and actual pixels directly inspected:
  - desktop `S1/S2/S3/S4/S5/S7` at 1440
  - mobile `S3/S4` at 390
  - desktop/mobile full-page captures
  - source representative images for S3/S4
- The S4 390 fixed-header clipping was reproduced visually from the saved artifact.
- S3/S4 source media focal content was checked before defining crop/object-position rules.
- No new benchmark research performed.
- No architecture, service taxonomy, or production code changed.

Riko specialist contract status: **PASS**.

Human-visible quality status: **NOT CLAIMED**. It remains downstream of Rin implementation → regenerated artifact → Aoi G5 → Sarah actual-pixel/copy review.

---

# 13. Routing

`Riko contract complete → Sarah review → Rin narrow implementation → actual artifact regeneration → Aoi G5 → Sarah final actual-pixel/copy review → Shun only if READY`

No additional Shun feedback is required to implement this contract.