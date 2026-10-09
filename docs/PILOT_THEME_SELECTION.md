# 事業者の設計方向に基づくテーマ候補の比較

`pilot_theme_selection` は、作成済み P01 の F21 と、明示的に渡されたテーマ
資料を照合し、根拠を辿れる候補一覧を作る。業種は候補を絞るために使い、
同じ業種でも F21 の方向語が違えば候補順は変わる。

これは**語句一致による選定ヒューリスティック**である。意味の理解、見た目の
完成品質、正式な P14 採用は判定しない。一致件数を品質点・適合度に換算しない。

## 入力と出力

```python
from lp_engine.pilot_theme_selection import build_theme_recommendations

recommendations = build_theme_recommendations(
    validated_p01_brief,
    theme_contract_path="/private/theme_contract.json",
    expected_theme_contract_sha256=previously_recorded_contract_sha256,
)
```

入力の brief は `pilot_authoring.build_theme_design_brief()` の出力。
既存の検証関数で元の名簿・P01 原稿から再計算し、抜粋だけの書換えを検出する。
原テーマ JSON は外部の実ファイルとして明示入力する。事前記録した SHA-256 と
**読んだ実バイト**の一致が必要で、JSON の重複キー・重複テーマ ID も拒否する。
出力にも元資料の hash と各一致箇所の JSON Pointer を記録する。

このモジュールが読むテーマ項目は `id`、`industry`、`label`、`fit`、
`description`、`designMoves`。これはこの照合処理の入力条件であり、正式工程の
required、意味定義、Gate を変更するものではない。パーツの既定 `pick`、
デモ画像、色指定、参考 ID から推薦理由を生成しない。

## 比較方法と判断待ち

1. brief の業種と一致するテーマだけを対象にする。
2. F21 `keywords` の各語と、原テーマの `fit`・`description`・
   `designMoves` を Unicode NFKC・casefold・前後空白除去で正規化する。
3. 方向語が原文の連続した部分文字列として現れる箇所を記録する。
   類義語の追加、単語分割、意味の推測はしない。
4. 一致した異なる方向語の件数で候補を並べる。同じ語を繰り返した入力や、
   1 語が複数の箇所に現れた場合は件数を増やさない。

| 状態 | 意味 |
| --- | --- |
| `CANDIDATE_FOR_REVIEW` | 一致語数が最も多い候補が 1 件。設計担当の判断に使える候補で、採用は未実施。 |
| `JUDGMENT_REQUIRED / TOP_MATCH_COUNT_TIED` | 最多件数が同じ候補をすべて保持。配列順・乱数・事業者 ID で勝者を作らない。 |
| `JUDGMENT_REQUIRED / NO_LITERAL_DIRECTION_OVERLAP` | 原文との一致なし。新たな方向語を勝手に補完しない。 |
| `JUDGMENT_REQUIRED / NO_THEMES_FOR_INDUSTRY` | 指定資料に対象業種のテーマがない。別業種へ自動置換しない。 |

件数 0 の候補は rank が null。同点は同じ rank のまま資料順で表示する。
`decision.leading_theme_ids` は比較上の先頭候補であり、
`decision.selected_theme_id` は常に null。判断待ちは設計担当へ返す状態であり、
しゅんさんへの確認を必須とする状態ではない。

語句一致は否定・文脈・含意を理解しない。例えば原文と同じ語があっても、
その語が意図する設計や事業者の状況が合うかは別途判断する必要がある。
一致語数の多さだけで制作対象のテーマを確定しない。

## P01 と設計判断の境界

元 brief を `brief_snapshot` に丸ごと保持し、FACT/HYPOTHESIS、根拠、
confidence、publication_policy、原 F21・F17 wrapper を変えない。

F21 の target_impression・reason・usage_scope は設計担当が見る文脈として
保持するが、自由記述から方向語を自動抽出しない。F17 の Web 上の問題を
好みのデザインへ読み替えず、F22 のコピー禁止表現をテーマの禁止条件に
置き換えない。仮説や内部用文章を公開コピーへ変換する処理も含まない。

正式 P14 採用・品質審査・公開許可・production_eligible は進めない。
選定後のパーツ、表示する文章、写真は、既存 `pilot_pipeline` の明示入力で
別途渡す。参考資料の写真やデモ本文が自動的に選ばれることはない。

## 保存した候補の再検証

```python
from lp_engine.pilot_theme_selection import validate_theme_recommendations

validate_theme_recommendations(
    saved_recommendations,
    brief=original_p01_brief,
    theme_contract_path="/private/theme_contract.json",
    expected_theme_contract_sha256=previously_recorded_contract_sha256,
)
```

元 brief と外部資料から候補を再計算する。保存後に順位、理由、採用状態、
元 wrapper を書き換えたものを、そのまま次の判断へ渡さない。

出力には元の事業者情報とテーマ資料の該当本文が含まれるため、非公開の
実行記録として扱う。公開 Git にはモジュール・独自の合成 fixture・この説明
だけを置き、原テーマ本文、実事業者情報、非公開資料の ID は入れない。
