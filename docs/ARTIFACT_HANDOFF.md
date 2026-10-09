# 実ファイルのローカル受渡し

`lp_engine.artifact_handoff` は、実ファイルの版・bytes・SHA256を受信先で照合し、コピーと不変の受領証を保存する。制作・品質・営業可否の判定を行わず、既存Stage ReceiptやGate Receiptを発行・変更しない。外部LLM、Chat送信、次工程の自動起動を呼び出す処理はない。

## 入力と出力

- producerが選んだファイルから、`build_handoff_manifest` で期待値を確定する。
- consumerは保存済みmanifestを受け取り、`expected_revision` と必要な `expected_context` を独立に指定する。受信時のファイルから期待hashを作り直さない。
- `revision` は既存の入力版・package版を指定する。工程版や過去job IDを推定しない。既存Library ID・保存版などはファイルごとの `sources` に渡す。未確認の出所は `null` のまま。
- 元ファイルと受信コピーのbytesは変えない。JSONの再整形、画像の再圧縮、本文の補完をしない。
- 同じrevision・context・ファイルpin群は同じdeliveryとなる。ローカルsource pathや受領時刻はそのidentityに使わない。sourceのID/保存版はidentityに含める。

受信先には次を保存する。

```text
handoff.sqlite
deliveries/<delivery_key>/receipt.json
deliveries/<delivery_key>/files/<original relative paths>
```

受領証は `ARTIFACT_RECEIVED` / `ARTIFACT_ONLY`、`quality_status: NOT_RUN`、`stage_receipt_issued: false`、`automatic_downstream_execution: false` を持つ。これらはローカル輸送記録であり、正式Contractのrequired fieldや新Gateではない。

同一入力の再受領では、送られたファイルを再照合したうえで、保存コピーの健全性も確認し、初回と同じ受領証を返す。受領数は増やさない。別接続・並列受領はSQLiteの一意キーとトランザクションで直列化する。保存コピーに欠損・破損がある場合は `STORE_CORRUPT` とし、過去の受領証を消したり修正したりしない。ファイル設置直後にDB記録が中断した場合は、完全な既存deliveryだけを再照合して回復できる。

## 関数から使う

```python
from pathlib import Path
from lp_engine.artifact_handoff import build_handoff_manifest, receive_artifacts

# Existing values supplied by the caller. No company or Task is inferred.
context = {"company_id": "fixture-company", "batch_id": "fixture-batch"}
manifest = build_handoff_manifest(
    "producer", ["generation_manifest.json", "index.html", "assets/style.css"],
    revision="fixture-input-v1", context=context,
)
receipt = receive_artifacts(
    source_dir="producer", manifest=manifest, receiver_dir="receiver",
    expected_revision="fixture-input-v1", expected_context=context,
)
received_html = Path("receiver") / receipt["storage_subdir"] / "index.html"
```

実際の連携では、producerの結果をJSONとして保存し、consumerへ固定manifestを渡す。例の会社・版はfixtureであり、本番入力へ流用しない。必要なCSS・写真などは明示的なfiles一覧へ含める。対象ファイル一覧の妥当性、manifestの出所の認証、会社事実・権利・品質は呼出し側と既存担当の責任である。

既存 `BatchRegistry` の `registry.json` は工程・品質の状態管理であり、受領台帳とは別に保持する。生成manifestの `input_digest` は入力内容のdigestであり、出力ファイルのbyte hashとして流用しない。`BatchInput.input_version` など、実際に存在する版を呼出し側が選び、会社/Task等の明示contextとともに渡す。受領証を返しただけでBatchItemをCOMPLETEDや品質PASSに変更しない。

## CLI

インストール済み環境、またはrepoの `PYTHONPATH=src` で使う。

```bash
PYTHONPATH=src python -m lp_engine.artifact_handoff pin \
  --source-root producer --file index.html --file assets/style.css \
  --revision fixture-input-v1 --out handoff-manifest.json

PYTHONPATH=src python -m lp_engine.artifact_handoff receive \
  --source-root producer --manifest handoff-manifest.json \
  --receiver-root receiver --expected-revision fixture-input-v1
```

`pin --context context.json --sources sources.json` で既存ID/出所を渡せる。`receive --expected-context expected-context.json` はその各値の一致を要求する。出力はJSON。エラーはstderrのJSONとexit 2。同じreceiveを繰り返すと同じ受領証を返す。`--out` は同一内容のみ再利用し、異なる内容を上書きしない。

主な輸送エラーは `REVISION_MISMATCH`、`CONTEXT_MISMATCH`、`CONTENT_MISMATCH`、`MISSING_FILE`、`STORE_CORRUPT`。正式StageのFAIL/HOLDへ自動変換しない。相対path以外、親への脱出、symlink、同名/case-aliasやfile/directory衝突は受け付けない。

## r09実装との出典・互換範囲

設計根拠は、監査で実読した非公開のr09 offline receiving/ACK packageにある、固定pin、実bytes/hash、SQLiteの不変Receipt、重複受領、輸送と品質の分離である。原ZIP・実会社資料・非公開source IDをこのrepoへ同梱していない。

本moduleはPythonエンジン向けの独立adapterであり、r09のNode CLI/SQLiteとのファイル形式互換を主張しない。r09固定3役 `diff/candidate/manifest` と特定manifestのcandidate/diff階層は取り込まず、呼出し側が明示した実ファイル一覧を使う。r09のLibrary publication/親ACK接続、外部認証、全22工程の自動配送は追加していない。今回の受領証も元のr09 Receiptや正式Stage Receiptの代用品ではない。

## 限定検証

```bash
PYTHONPATH=src python -m unittest discover -s tests -p test_artifact_handoff.py -v
```

初回受領、同一再受領、期待版/会社不一致、送信ファイル破損/欠損、保存コピー破損、出所版の保持、同時受領、受領ファイル設置後の台帳復帰、unsafe path、CLI往復をfixtureで確認する。受領成功による品質状態変更や外部処理は行わない。
