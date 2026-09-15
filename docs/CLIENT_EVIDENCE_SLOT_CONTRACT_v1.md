# Client Evidence Slot Contract v1

Updated: 2026-09-15

## Purpose

営業サンプルを未完成にしないまま、契約後のヒアリング・実写真で品質をさらに上げるためのMachine Contract。

営業サンプルは常に `SALES_STATE`。
納品版は必要Evidenceを統合した `ENRICHED_STATE`。

## Core rule

Client Evidenceが無い状態でもLPは完成していなければならない。

各Slotは必ず:
- 何のために必要か
- Sales Stateでは何で完成させるか
- Enriched Stateで何を差し替え/追加するか
を持つ。

## Slot types

- HERO_REALITY
- OWNER_PORTRAIT
- CRAFT_ACTION
- PLACE_WIDE
- PRODUCT_DETAIL
- RESULT_CASE
- TESTIMONIAL
- OWNER_QUOTE
- VERIFIED_METRIC
- SERVICE_DETAIL
- CTA_CHANNEL
- TRUST_CREDENTIAL

## Visual slot required fields

写真系SlotではPhoto Directionを持つ。

- purpose
- preferred_orientation
- preferred_aspect_ratio
- focal_subject
- focal_relationship
- shot_distance
- copy_safe_zone
- light_direction
- minimum_resolution_px
- crop_tolerance
- avoid
- mobile_variant

## Example

```python
ClientEvidenceSlot(
    id="hero-storefront",
    kind=EvidenceSlotKind.HERO_REALITY,
    section_id="hero",
    required_for_delivery=True,
    purpose="本人店舗の実在感をHeroへ追加する",
    sales_state_fallback="会社固有Factから作ったTypography/Process visualでHeroを完成させる",
    question_prompt="店舗または工房の外観写真を撮影してください。",
    accepted_formats=["image/jpeg", "image/png", "image/heic"],
    photo_direction=PhotoDirection(
        purpose="看板と入口の関係が一目で分かる実在Evidence",
        preferred_orientation="portrait",
        preferred_aspect_ratio="4:5",
        focal_subject="看板",
        focal_relationship="看板 + 入口 + 建物の一部",
        shot_distance="外観全体が分かり、看板の文字が読める距離",
        copy_safe_zone="right",
        light_direction="自然光。逆光を避ける",
        minimum_resolution_px=1800,
        crop_tolerance="入口と看板を切らない範囲で上下20%程度",
        avoid=["極端な斜め撮影", "夜間で看板が読めない", "車や障害物が主役を隠す"],
        mobile_variant="縦4:5で看板と入口を同時に残す",
    ),
)
```

## Interview app rule

将来のヒアリングアプリは、全顧客へ固定100問を出さない。

LPが宣言したEvidence Slotから質問を生成する。

例えば:
- PERSON Authorityが無ければOWNER_PORTRAITを聞かない場合がある
- PLACEが主役ならPLACE_WIDEを複数要求
- DATAが主役ならVERIFIED_METRICと根拠確認を優先
- Craft企業ならCRAFT_ACTION / PRODUCT_DETAILを優先

## Completion states

### SALES_STATE
- no visible placeholders
- no fake owner assets
- layout/copy/motion/CRO complete
- client slot insertionを前提に見た目を崩さない

### ENRICHED_STATE
- required slots collected
- evidence authenticity confirmed
- actual asset crop/art direction complete
- Sales StateのBig Idea / hierarchyを維持

## Failure conditions

- 実写真が入った瞬間にHero構成を全面変更したくなる
- Sales Stateが灰色Boxや仮画像でしか成立しない
- 「とりあえず写真を10枚ください」のようなSlot非依存ヒアリング
- 同じ写真をPC/Mobileで機械的cropして主役が消える
- Client Evidence追加でFact Safetyが悪化する
