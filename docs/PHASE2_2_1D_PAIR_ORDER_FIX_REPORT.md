# Phase 2.2.1D Pair Order Fix

担当は澪、正式レビューはサラ、最終判断者はしゅんです。本報告はIssue #143のSarah PM監査・修正指示 #5920002088に対する限定修正です。公開済み修正元 `c6f135e2f229270f46d694b51f333a9830d89479` から別Branch `phase2-2-1d/pair-order-fix-20261001` を作成しました。

左右双方の派生資料を呼出情報と正式Source Recordから拒否し、Pair判定とSetの返却結果を順序不変にしました。最終実行は270 PASS、別集計の歴史的Negative replayは18 PASS、Versioned ValidatorはPASSです。Live HOLD13、Promotion0、Customer Production Approved0、`phase2600_allowed=false`を維持します。Phase D全体のSarah PM判定は保留です。

## 修正差分

既存ファイルの変更は `src/lp_engine/independence_calibration.py` の9行追加・5行削除のみです。旧Commit、Source Record、Snapshot Binding Schema、Family assertion、Ledger、Evidence、Failure、旧Report、旧Manifestは保持しています。

1. 派生種別を `DERIVATIVE_SOURCES` に集約し、呼出側のleft／rightのどちらにも `GALLERY_DUPLICATE`、`ARCHIVE_MIRROR`、`LOCALIZATION_ONLY` があれば `NOT_INDEPENDENT` にします。
2. 正式Source Recordで解決した両Unitにも同じ拒否を適用します。呼出側が欄を省略した場合、非派生値に変更した場合、別の派生値へ変更した場合も、正式記録の拒否を隠せません。
3. `calibrate_units()` のUnit IDをソートしてペアを列挙します。Setの判定だけでなく、pairsの順序・左右・理由・dimensionsを含めた返却値を固定します。
4. 矛盾する同一Unit IDのレコードが存在する場合、全IDを数えた後にUNKNOWNを返します。従来の途中returnでは、同じ矛盾集合でもdistinct countが入力順で変わりました。曖昧性の拒否は保持し、件数も固定しました。

Family確認を無条件UNKNOWNにする変更はありません。正しい現在のAttributionを持つ同一Mechanism・別Referenceのペアは双方の順序でVERIFIED_INDEPENDENTです。3件の全独立集合も全6順列でVERIFIED_INDEPENDENTです。独立2件と派生1件の混合集合は、派生を含む2ペアがNOT_INDEPENDENT、残りの正しいペアがVERIFIED_INDEPENDENTであり、全6順列のSet結果はPARTIALLY_INDEPENDENTです。

## 監査再現と順序検証

Git objectから修正元c6の実際のmodule bytesを読み、SHA-256 `21db0fad697fef00ce18c03c7c72c8f241d4824b6fab4766654e3fb612c592c4` を照合してから、監査の最小再現を実行しました。合成入力で両方のtraceが有効、両方のatomic MatchがMATCHのまま、3種類とも以下が再現されました。

| c6に対する合成制御 | 派生が左のPair／Set | 逆順のPair／Set |
| --- | --- | --- |
| GALLERY_DUPLICATE | VERIFIED_INDEPENDENT／VERIFIED_INDEPENDENT | NOT_INDEPENDENT／NOT_INDEPENDENT |
| ARCHIVE_MIRROR | VERIFIED_INDEPENDENT／VERIFIED_INDEPENDENT | NOT_INDEPENDENT／NOT_INDEPENDENT |
| LOCALIZATION_ONLY | VERIFIED_INDEPENDENT／VERIFIED_INDEPENDENT | NOT_INDEPENDENT／NOT_INDEPENDENT |

これは旧c6に対する再現で、修正後テストのFAILではありません。新規研究Evidenceや現在の本番Gate突破の主張には使用しません。

修正後の派生マトリクスは120の独立したunittest methodです。各methodの実行ID、パラメータ、実際のPair／Set verdictを保存しました。

| パラメータ | 値 | 数 |
| --- | --- | --- |
| 派生種別 | Gallery duplicate／Archive mirror／Localization only | 3 |
| 派生資料の元位置 | A／B | 2 |
| 呼出情報 | 正式記録と一致／省略／非派生値への矛盾／呼出側だけ派生／別派生値への矛盾 | 5 |
| 引数・リスト順 | 正順／逆順 | 2 |
| 実行対象 | pair_independence／calibrate_units | 2 |
| 合計 | 全ケースNOT_INDEPENDENT | 120 |

新規順序テスト全体は164 methods、実際のPair verdict照合128回、Set verdict照合204回です。両順序の正しい独立ペア、3件の全6順列、曖昧Unitを含む4件の全24順列、同一Unitの重複、曖昧Relation、6 Familyの共有拒否、Reference／Page重複、Scene／Pixel／Capture metadata／旧readback hash／Snapshot mapping／Citation／Mobile不足／未レビュー／部分Family、混合3件集合の全順列を含みます。

## 今回の実行結果

実行コマンドは `PYTHONPATH=src python scripts/verify_phase2_2_1d_pair_order_fix.py`。このrunnerは今回1回実行し、出力を新しい `data/phase2_2_1d_pair_order_fix/` に限定しました。既存build、finalize、研究runner、旧Snapshot Fix runnerは実行していません。

| Test module | 実行 | PASS | FAIL | skipped |
| --- | ---: | ---: | ---: | ---: |
| 新規Pair Order Fix | 164 | 164 | 0 | 0 |
| Snapshot Binding Fix | 40 | 40 | 0 | 0 |
| D | 16 | 16 | 0 | 0 |
| C | 26 | 26 | 0 | 0 |
| B | 18 | 18 | 0 | 0 |
| Production | 6 | 6 | 0 | 0 |
| 合計 | 270 | 270 | 0 | 0 |

歴史的Negative specimenを変更せず別に18件replayし、18 PASS／0 FAILです。以前のSnapshot Binding修正で既に無効化された3件の旧PARTIALLY_INDEPENDENT期待値は、今回もUNKNOWNとして別Reportに記録します。旧specimen・旧期待値・旧Reportは変更していません。

30件の実行ソースHashを `tests_report.json` に記録しました。対象は実際にロードされたRepository内Python sourceと、選択した全Test module／runnerです。行coverageや全Repository実行を意味しません。全270件の実行ID／結果、120件のmatrix metadata、全332回の順序verdict照合を新Reportに収録しています。

Version `PAIR_ORDER_FIX_V1` Validatorは、正式SourceからのLedger再導出一致、実際の13 MechanismのLive Gate拒否、保存した実行結果と現在ソースHash、120件のmatrix completeness、旧c6 objectに対する監査再現、旧成果の保持を確認してPASSしました。Snapshot Fixの既存Validatorは構造検証関数のみ再利用し、旧結果を書き換えていません。新Manifestを作成した後の `--check-manifest` は別のreadback receiptに記録し、manifest作成前のvalidator_reportを遡及変更しません。

Production回帰には実際の `run_generation` のauthor-owned fixture pathと一時HTML生成、Dの5 profileのproduction route停止、Snapshot Fixの合成Ledger／production admission制御が含まれます。Liveの13 Mechanismは今回もGateで拒否されました。新規Desktop／Mobile browser renderはN/A、顧客公開は0です。

## 旧成果の保持と検証範囲

c6の3,957 tracked filesのうち、今回の判定コード以外の3,956ファイルは元のGit blobと一致しました。data／artifacts 3,253ファイルを保持し、そのHash index digestも保存しました。公開済みSnapshot Fixの20件Manifestと11件の旧実行ソースHashはc6 objectに対して一致し、旧106 PASS、旧66 PASS、Candidate28、Failure108の記録は保持しています。旧Manifestがc6のソースを指すことを維持し、新コード用に書き換えていません。

今回のSource Record／Ledger構造・ローカル拒否EvidenceのHash検証は新しい実行です。元durable100の16 archive container／1,414 memberのfresh readback、入口screening、Candidate比較、新規Discovery／Capture／Adapter、Browser QAは実行していません。テストの合成Attributionを研究Evidenceとして採用していません。

## 保存と公開状態

正式Report／Recovery Packageは `/LP制作事業/` に新規保存します。Git Bundleはc6をprerequisiteとし、今回の新Commit objectを同一SHAで復元できる形で保存します。Final Commit／Tree／Inventory／全変更PathのSize・SHA-256／Bundle・Package Hash／実際の復元readbackは完全引継ぎに記録します。

今回の差分は未公開です。#5919687061の承認は既存の2修正Commit／21ファイルの公開に限定され、今回の新差分を含みません。今回のBranchへPushやIssueへ未公開差分を投稿する前に、新規差分だけの具体的な公開承認が必要です。旧公開・旧承認・Git認証の工程は完了済みです。

停止状態は `PHASE_2_2_1D_PAIR_ORDER_FIX_READY_FOR_PM_REVIEW`。Sarah PM正式PASSの自己付与、次の研究Phase、Live HOLDの解除、Mechanism昇格、顧客本番解禁、2,600-reference Expansionは行いません。
