# 先行3業種の統合実装：入力・受渡し・品質状態

## 今回接続した範囲

制作入力が旧業種へ置き換わること、ファイル受領が制作完了として扱われること、
未実施の品質審査が固定点やPASSへ変わることを防ぐための実装。
既存の正式Contract、工程の完了条件、品質Gateの閾値は変更しない。

| 対象 | 実装後の動作 | 接続先に残る仕事 |
| --- | --- | --- |
| 名簿の入力 | 造園・塗装の原CSVと3業種共通の明示入力を、出所付きのP01作成入力へ変換する | P01の実作成、仮説の採否、正式Production Contractへの対応 |
| 実ファイルの受渡し | 保存済みmanifestの版・サイズ・SHA256を受信先で照合し、同一配送には同じ受領証を返す | 各実工程からの呼出し、既存工程Receiptへの正式接続 |
| 品質状態 | 明示の点数・判定を保持し、欠落した審査はNOT_RUN、未採点の平均と合格率はnullとする | 実際の視覚審査結果を返す工程の接続 |
| 営業用サンプル生成 | 技術QAだけではSALES_READYにせず、実際に保存したPNGをmanifestへ記録する | 新3業種のデザイン・素材・本文接続、営業可否の最終判定 |

名簿件数、ファイル受領数、処理完了件数、品質合格件数、LP制作完了件数は
それぞれ異なる集計。`BatchManifest.success_count` は明示の処理完了数であり、
品質合格数は `aggregate_quality` の `premium_pass_count` で確認する。
明示のHOLD/FAILの点数も失わず、採点数と判定数を別の分母で集計する。

## P01入力から受信までの使用例

原本取得のreceiptまたは明示入力を用意し、入力変換を実行する。
実名簿や実出力は公開Gitへ保存しない。以下のpath・版は説明用。

```bash
PYTHONPATH=src python -m lp_engine.pilot_intake \
  --input-receipt /private/input_receipt.json \
  --out /private/p01_producer

PYTHONPATH=src python -m lp_engine.artifact_handoff pin \
  --source-root /private/p01_producer \
  --file intake_records.jsonl \
  --file p01_handoffs.jsonl \
  --file intake_report.json \
  --revision example-input-package-v1 \
  --out /private/p01_handoff_manifest.json

PYTHONPATH=src python -m lp_engine.artifact_handoff receive \
  --source-root /private/p01_producer \
  --manifest /private/p01_handoff_manifest.json \
  --receiver-root /private/p01_receiver \
  --expected-revision example-input-package-v1
```

本番呼出しでは送信側の既存版と、受信側が期待する版・案件contextを渡す。
受信時に期待hashを作り直さない。名簿の旧VERIFIEDやYESは過去の記載として
保存する。P01では不足情報について根拠を明記した仮説を作成できる。
入力アダプター自体はP01を完成したことにせず、確認済みFactへ昇格しない。

## 検証

関連する非ブラウザテストは66件、追加のsubtestは37件PASS。
造園・塗装CSVとバーの明示入力を同時に受領する合成例で、元情報・仮説・
業種・品質未審査状態の保持を確認した。固定後のファイル変更は受領を停止し、
同じ配送の再実行は受領証を増やさない。

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_batch.py tests/test_quality_state.py \
  tests/test_sales_production.py tests/test_pilot_intake.py \
  tests/test_artifact_handoff.py tests/test_pilot_intake_handoff.py \
  tests/test_operations.py tests/test_sales_sample_policy.py
```

既存営業エンジンの合成サンプルを実ブラウザへ通す検査は
`tests/test_sales_browser_smoke.py` に分離した。既存CIはChromium導入後に
`LP_RUN_SALES_BROWSER_SMOKE=1` を指定して実行する。ローカル単体検査の
mock結果や、この旧業種の合成例を、新3業種の見た目の合格根拠にしない。

`scripts/run_phase5_batch.py` のTEST ONLY合成採点は実評価ではない。
stateを返さないfixtureは、この変更ではHOLDとなる。

## 次の実装単位

1. P01の作成結果を、事業者に合うテーマ選択へ渡す。
2. テーマ、選択パーツ、写真、本文を実LPとして接続する。
3. 参照LPとの比較、PC/SPの実表示、実際の品質審査をつなぐ。
4. 各工程の受領記録を使って通し制作し、時間・合格率・再実行を測る。

バーは共通入力形式で受領できる。バー原CSVへの直接対応は列定義の確認後に
追加する。テーマやパーツのカタログ上の存在だけでは、Production Contractへの
接続、実画像の使用、全工程の自動実行が完成したことにはならない。

詳細は [入力仕様](PILOT_INTAKE_V1.md) と
[ファイル受渡し仕様](ARTIFACT_HANDOFF.md) を参照。
