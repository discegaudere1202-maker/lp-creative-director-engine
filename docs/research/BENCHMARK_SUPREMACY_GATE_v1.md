# Benchmark Supremacy Gate v1

Updated: 2026-09-15

## Purpose

内部採点だけで「Premium」と判断しない。
現実の日本トップクラスのWeb表現と横に並べて見劣りしないことを要求する。

## 1. Reference selection

1 Frameにつき3〜5 reference。

優先:
1. Same Visual Authority
2. Same Frame Job
3. Similar audience / trust context
4. Same industry only if relevant

例:
社労士Heroを、士業サイトだけで比較しない。
DOCUMENT / TYPOGRAPHY / TRUSTの強い日本サイトとも比較する。

## 2. Frame jobs

- HERO_STOP
- VALUE_REFRAME
- EVIDENCE_MONUMENT
- MATERIAL_PROOF
- PERSON_TRUST
- PROCESS_EXPLAIN
- PRODUCT_BEHAVIOR
- PLACE_DESIRE
- OBJECTION_RESOLVE
- CTA_CLOSURE

## 3. Test formats

必須:
- Desktop 1440
- Mobile 390
- normal
- logo-off

推奨:
- grayscale
- blur

## 4. Blind review questions

Reviewerには制作元を隠す。

5問:
1. どれが最も高い制作費に見えるか
2. どれが最も会社固有に見えるか
3. どれが最も5秒後に記憶に残るか
4. どれを誰かに見せたいか
5. どれの続きを一番見たいか

各Frameを順位付け。

## 5. Gate

PASS候補:
- 5問のうち3問以上で上位2位
- Company-specificityがreference平均未満ではない
- DesktopとMobileの両方で明確な格落ちがない

FAIL:
- 「整っているが安く見える」
- referenceを横に置いた瞬間にgenericに見える
- desktopだけ強い
- motionを止めると弱い
- logoを消すと何も残らない

## 6. Why this matters

森人試作の教訓:
内部ルールを満たしても、既存サイトと比較すると魅力が下がる場合がある。

Premiumは自己採点では決まらない。

## 7. Review notes

Benchmarkはコピー対象ではない。

収集するのは:
- tension
- hierarchy
- asset treatment
- rhythm
- idea-to-form relationship
- restraint
- conversion placement

Visual motif / illustration / compositionをそのまま模倣しない。

## 8. Engine integration plan

将来:
- reference frame registry
- pairwise tournament
- model critic 3 personas
- human spot review
- rank aggregation
- regressions stored per Golden Sample

自動Gateは補助。
最終Premium判定はCreative Red Teamを含む。
