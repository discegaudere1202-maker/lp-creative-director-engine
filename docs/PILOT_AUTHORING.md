# P01作成結果から全体デザイン判断への接続

`pilot_authoring` は、明示的に作成した事業者仮説の22項目を受け取り、
全体デザインの判断に使う参考情報を渡す。事業者ごとの仮説を作る担当と、
その結果を受け取る処理を分けている。業種ごとの固定値による穴埋めはしない。

## 元定義を使う範囲

基礎資料は `P01_P02_CURRENT_DEFINITION_VIEW.txt` のP01部分、
`P01_P02_CURRENT_DEFINITION_INDEX.json`、その参照元のP01辞書である。
全22工程の資料整備が完了した記録と照合したうえで、以下を接続した。
個別資料の取得先・版・読取範囲は非公開の実行記録で管理する。

| 元項目 | 今回の扱い | 後工程で行う判断 |
| --- | --- | --- |
| P01_F01〜F22 | 元のID・value・classification・basis・confidence・publication_policy・evidence_idsを保持 | 各項目の意味、根拠、項目間の整合の確認 |
| F21 `direction_keywords` | 既存のkeywords・target_impression・reason・usage_scopeをP14の設計参考へ渡す | 全体テーマの選択と設計理由 |
| F17 `website_problem` | 元wrapperのままP12/P14の判断参考へ渡す | 情報階層・見せ方への反映 |
| F03 `primary_service` | 現在主力とLP優先候補を別のまま保持 | P02で目的・CVと照合した採用判断 |
| F10 `primary_end_user` | P03の候補として保持 | P03で利用者仮説を決める |
| F22 `avoid_keywords` | コピー確認の対象と理由をそのまま保持 | P07/P13で禁止表現を確認 |

F17の原文は「正式field移送ではない」、F21は「P14 design direction参考」
としている。このモジュールもP14の正式field名や新たなrequiredを定めない。
F22の禁止表現を、デザインの禁止色・禁止テーマへ読み替えない。

元の22項目を受け取るローカル入力形式は `pilot-p01-authoring-input/v1`。
出力形式は `pilot-p01-design-brief/v1`。どちらも技術的な受渡し形式であり、
正式Production ContractやP01のGateを置き換えない。

## 入力

```python
from lp_engine.pilot_authoring import build_theme_design_brief

brief = build_theme_design_brief(intake, authoring)
```

`intake` は `pilot_intake.adapt_normalized_lead()` 等で作った1事業者分の記録。
元の名簿から変えられていないことを、既存の入力処理で再確認する。

`authoring` は次の形式を明示的に作る。

```json
{
  "schema_version": "pilot-p01-authoring-input/v1",
  "intake_id": "対象のintake_id",
  "authoring_source": {
    "source_id": "今回作成したP01原稿の識別子",
    "source_locator": "P01原稿の所在"
  },
  "fields": [
    {
      "field_id": "P01_F21",
      "value": {
        "keywords": ["整然", "明るい", "比較しやすい"],
        "target_impression": "落ち着いて条件を比較できる印象",
        "reason": "この事業者向けの相談場面を踏まえた具体的な選定理由",
        "usage_scope": "P14 design direction"
      },
      "classification": "HYPOTHESIS",
      "basis": "事業者情報と利用場面に基づく制作仮説の根拠",
      "confidence": "LOW",
      "publication_policy": "INTERNAL_ONLY",
      "evidence_ids": []
    }
  ],
  "evidence_registry": {}
}
```

上例はF21の形式を示す抜粋。実行にはF01〜F22を各1件ずつ渡す。
任意の `field_key` を付ける場合は原IDと一致させる。
元wrapper内の追加情報・内側の公開条件も保持される。

値が空、null、または「不明」「未設定」「情報なし」等の置き残しなら受け取らない。
根拠が不足する項目は、作者がその事業者について具体的な合理的仮説と根拠を作る。
空の関連業種リストなど、値の内側にある意図的な空配列は保持できる。
原資料の文章形式の例を新keyへ移すことは要求せず、F21の設計参考だけを、
既に示された構造で受け取る。F21が文章形式のときは勝手に分解せず明示的に拒否する。

現在のWeb情報を観測していないときにURLを作り出す必要はない。
F09は、過去の観測範囲と今回の制作仮説を区別した具体的な説明でも保持できる。
価格・対応地域・実績等を内部仮説として置くことと、会社の約束として掲載することは別である。
このモジュールは公開文を生成しない。

## 事実・仮説の扱い

FACTには元定義どおり根拠IDが必要で、その根拠原文を `evidence_registry` で渡す。
名簿のSOURCE_RECORDED_ONLY観測や、根拠に明記された未検証状態を、
現在のFACTの根拠として使う入力は拒否する。HYPOTHESISにDISPLAY_OK_FACTや
検証済み・実績利用可のフラグを付けることも拒否する。

受け取ったFACTは**作者がFACTと分類した記録**である。この処理が情報を再調査し、
正確性・公開許可・証拠の適合性を認定したことにはしない。
`facts_verified_by_adapter` は常に0で、後工程の意味品質・根拠審査は残る。
根拠レコード自体の形式も既存の原文を保持し、別の正式Evidence schemaを追加しない。

## 出力と状態

`fields_by_key` には22項目すべてを元wrapperのまま入れる。
`design_reference` はF21・F17の原recordと設計参考の抜粋を持つ。
`input_handoff` は過去の名簿記載とSOURCE_RECORDED_ONLYを保持する。

`status.authored_input=ALL_22_SUPPLIED` は、22項目の値と分類・根拠が
明示入力されたことを表す。事業内容との整合、仮説の妥当性、元の項目別Doneの
意味判断を機械だけで証明した結果ではない。

- `p01_semantic_quality=NOT_RUN`
- `p01_stage_completion=NOT_ASSERTED`
- `theme_selection=NOT_RUN`
- `public_copy_generation=NOT_RUN`
- `publication_permission_granted=false`
- `production_eligible=false`

元P01の入力・出所と、その抜粋表示をそれぞれ保持する。後からkeywordsや状態だけを
書き換えていないか、消費側は次の関数で検査できる。

```python
from lp_engine.pilot_authoring import validate_theme_design_brief

validate_theme_design_brief(brief)
direction = brief["design_reference"]
# directionと他工程の採用済み判断を使い、次の担当がテーマを選ぶ。
```

この検査は原入力からの再計算による整合確認であり、署名や作者本人の認証ではない。
別ファイルでの受渡しは `artifact_handoff` の元manifestと組み合わせて固定する。

## CLI

```bash
PYTHONPATH=src python -m lp_engine.pilot_authoring \
  --intake /private/intake.json \
  --authoring /private/authored-p01.json \
  --out /private/design-reference.json
```

実事業者の入力・連絡先・調査原文・生成したbriefは公開Gitへ保存しない。
テストは合成情報だけを使う。

今回の接続後に残るものは、実事業者ごとのP01作成と意味審査、P02の目的・CV採用、
P03の対象利用者の判断、P14の全体テーマ決定、P13の確定本文・素材・各パーツへの
接続である。既存22工程の定義資料を再作成する必要はない。
