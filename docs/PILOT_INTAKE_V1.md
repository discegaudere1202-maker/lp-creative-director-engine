# 先行3業種：名簿受領とP01への受渡し

`lp_engine.pilot_intake` は造園・塗装・バーの営業入力を、出所付き観測値と
P01用の仮説作成入力へ変換する。営業名簿の受領、P01の完成、制作入力の承認、
描画対応、最終品質は異なる状態として保持する。

## 対応入力

- 原CSV：実列を確認済みの `landscape` / `painting` NO_WEB名簿。
- `pilot-lead-input/v1`：3業種共通の明示的な正規化入力。
- `no-web-intake/1.0`：既存の造園・塗装部分抽出。部分抽出の由来と
  `original_bytes_verified=false` を現在の完全取得へ読み替えない。

バー専用の原名簿の列定義は未確定。造園・塗装CSV列をバーに流用せず、
明示入力を受ける。業種キーは `landscape` / `painting` / `bar` のみ。
旧美容系の業種キーへ置換しない。

## 実行

公開リポジトリ内には実名簿・実連絡先・実出力を置かない。以下のパスは例。

```bash
PYTHONPATH=src python -m lp_engine.pilot_intake \
  --input-receipt /private/input_receipt.json \
  --out /private/intake_full

PYTHONPATH=src python -m lp_engine.pilot_intake \
  --normalized-jsonl /private/explicit_leads.jsonl \
  --hypotheses /private/p01_hypotheses_by_intake_id.json \
  --out /private/intake_explicit

PYTHONPATH=src python -m unittest discover -s tests -p 'test_pilot_intake.py' -v
```

原CSV receipt は `files` 配列を持ち、各要素に `profile`, `local_path`,
`source_id`（または `library_file_id`）を指定する。`bytes`, `sha256`,
`row_count` があれば全て照合する。3値全ての照合ができた時だけ
`original_bytes_verified=true` とする。これはファイル同一性であり、
現在の営業状況・メール到達性・事業者Factの再確認ではない。

出力は `intake_records.jsonl`, `p01_handoffs.jsonl`, `intake_report.json`。
入力だけに由来する安定した値で作り、実行時刻を新たな確認時点に使わない。
同じsource IDと原record IDが同一batchに重複したら停止し、自動統合しない。
`intake_id` は出所内record用で、正式 `lead_entity_id` 等への採番ではない。

## 明示入力の最小形（合成例）

```json
{
  "schema_version": "pilot-lead-input/v1",
  "source_record_id": "SYNTHETIC-BAR-1",
  "industry": "bar",
  "identity": {"business_name": "架空のテストバー"},
  "provenance": {
    "source_id": "SYNTHETIC-DATASET",
    "source_locator": "synthetic://master",
    "input_kind": "SYNTHETIC_TEST_ONLY"
  }
}
```

`identity`, `location`, `contact`, `business` の対応フィールドは文字列かnull。
名簿の名称を法的法人名、住所をサービス対応エリア、出典URLを公式SNSへ
昇格しない。連絡routeとidentifierは同一チャネルの値を照合する。
元入力全体とraw row、source/version/row位置、ハッシュを保存し、未対応の
列もsource snapshotに残す。投影値がsnapshotから変更されれば受渡しを停止する。

## FactとHypothesis、未確認の扱い

`source_observations` は `SOURCE_RECORDED_ONLY`。元のYES/VERIFIEDは
`legacy_assertions`へ残し、現在の確認済みFactを作らない。

`build_p01_handoff(intake, hypotheses=[...])` は、明示された合理的仮説を
別配列へ保持する。各仮説には `hypothesis_id`, `field`, `value`, `rationale`
が必要。根拠メモ等の補足値はそのまま保持する。検証済み・確定Factとしての
指定は受けない。仮説のconfidenceの高さと、事実確認済みの状態は分ける。

**名簿で未確認の項目があっても、P01は仮説を作成できる。**
`missing_source_fields` は元情報の不足一覧で、P01以降の全項目をunknownに
する要求ではない。仮説生成そのものは次のP01工程で行う。

現在の出力は `READY_FOR_HYPOTHESIS_AUTHORING`。
`SalesCandidate.from_master`, `build_research`, `build_input`, `run_generation`
へ自動投入しない。`verified_facts=[]`, `generation_input=null`,
`render_support=NOT_ASSERTED`, `production_eligible=false` のまま。
既存の正式Contract・required・品質Gateを増減する変更ではない。

## Python API

- `adapt_no_web_row(row, *, industry, source, row_number)`
- `adapt_normalized_lead(record)`
- `load_no_web_csv(path, *, industry, source)`
- `build_p01_handoff(intake, *, hypotheses=None)`
- `write_intake_batch(records, out, *, hypotheses_by_id=None)`

P01の実作成結果や正式Production Contractへ接続するときは、元のFact参照、
仮説の採否、顧客の判断課題、公開可能な本文・素材・CTAを次の工程で扱う。
このintakeの件数を、生成済みLP数や3業種の描画対応済み件数へ加算しない。
