# Stable Section ID Contract v1

更新日: 2026-09-15

Pixel Rhythm回帰比較では、SectionをDOM上で同一人物として追跡できる必要がある。
そのため、今後自動生成するLPの主要Sectionには意味のある安定IDを付与する。

## Recommended

```html
<section data-section-id="hero">...</section>
<section data-section-id="recognition">...</section>
<section data-section-id="evidence">...</section>
<section data-section-id="services">...</section>
<section data-section-id="quiet-story">...</section>
<section data-section-id="objection">...</section>
<section data-section-id="cta">...</section>
```

## Rules
- `section-1`, `section-2` のような順番依存IDは回帰比較用として不十分。
- IDは見た目のレイアウト名ではなく、Narrative / Conversion上の役割を表す。
- 同一LP内で重複禁止。
- Section順が変わってもIDは維持する。
- Creative Concept変更で役割自体が変わった場合のみID変更可。
- `data-section-id` をMachine Contractとし、HTML `id`はNavigation用途と分離してよい。

## Why
安定IDがあれば、改修前後で
- quiet_score
- visual density
- height ratio
- section-to-section transition energy
を同じ役割同士で比較できる。

数値差はCreative FAILではなく、Creative Red Teamへ戻すための観測信号として扱う。
