# 森人 Golden Sample 03 Postmortem v1

更新日: 2026-09-15

## 結論

森人を営業用Golden Sample 03として選定した判断は誤り。

理由:
- MATERIAL / SENSORY研究対象として魅力的であることを優先しすぎた
- 既存Webの完成度を制作前にbaseline評価していなかった
- 既存サイトが持つ本物の写真・空気感・素材感を、新試作が上回れるか確認していなかった
- 制作側の画像取得制約を、事業者側のAsset不足と誤認した

結果として、新試作は既存Webより弱いものになった。

---

## 何が弱くなったか

### 1. Authenticityを減らした
既存Webに存在する本物の家具・木・工房・人・店の雰囲気は、MATERIAL系ブランドでは非常に強い。

新試作は「写真を大きく使えない」という制作都合から、Typographyと抽象的な一枚板モチーフへ寄せた。
そのため、森人の本質である実物感を薄めた。

### 2. Creative Conceptを強くしすぎた
「香りまで、家具にする。」というConceptはCompany Truthとの接続はあるが、Web体験全体をその一軸へ寄せすぎると、実際の森人が持つ家具・職人・店・時間の豊かさを狭める。

### 3. Asset Limitedの定義を間違えた
森人はAsset Poorではない。

正しくは:
`Business assets = strong`
`Our asset access = limited`

この差を区別できていなかった。

### 4. Golden Sample選定とBenchmark選定を混同した
Strong existing siteは、研究には向く。
しかし営業サンプル対象にするには「既存より明確に良くなる仮説」が必要。
それを通さず制作へ進んだ。

---

## 新ルール

森人は今後:
- `BENCHMARK_ONLY`
- MATERIAL / SENSORY Craftの研究対象
- Existing Site Superiority Gateの失敗例
- Asset Reality Gateの失敗例

として保持する。

営業用Golden Sample 03からは取り下げる。

---

## 1000件生成への学び

```text
既存サイトがある
↓
まず既存サイトを評価
↓
強いなら制作しない
↓
弱い場合も「何を改善するか」を2つ以上言語化
↓
それからCreative Conceptへ進む
```

そして:

```text
画像を取得できない
≠
その会社に画像資産がない
```

この2つは必ず別フィールドで管理する。

---

## 次のGolden Sample 03条件

- MATERIAL / 職人・製造系
- Webなし、または明確に弱いWeb
- 本人性のある公開Factあり
- 写真が少なくても、事業者自身が本当にAsset Poorなのかを確認
- 既存Webがある場合は、制作前にBaseline Scoreと改善仮説を記録
- 既存より良くなる見込みが弱ければ候補から外す
