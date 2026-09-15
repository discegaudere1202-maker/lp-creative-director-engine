# Evidence Ablation & Engine-Ready Validation

更新日：2026-09-15

## 結論

今回のAblationでは、Full Enrichedの改善を「人物情報だけ」「数字だけ」に還元できなかった。P02ではTrust CoreでもBaselineからTrust / Conversionが上がったが、Fullの方がTrustは強かった。P10ではTrust CoreがBaselineと同等で、Fullに加えた「担当者の公開プロフィール」と「転職後も続く支援」の組み合わせで初めて追加の改善が観測された。

したがって、現時点で `ENGINE_READY` またはTrust因果の `ENGINE_READY_CANDIDATE` へ昇格するRuleはない。次はEvidence研究の継続を優先する。

## 方法

各Prototypeについて、同じFormal Opponent Setに対して次の3状態を比較した。

| 状態 | 定義 |
|---|---|
| Baseline | Enriched前のFormal PASS版。P02/P10とも12票、Win Rate 0.6250。 |
| Trust Core | 会社固有事実1つ＋Operational Evidence 1つ＋Decision/Risk Boundary 1つ。 |
| Full Enriched | 前回Formal PASS済みの実在Evidence追加版。 |

CaptureはFull/Coreを同一Run `34970228505`、Artifact `10397341100` で取得し、Desktop `1440×1000` / Mobile `390×844` を確認した。全レコードで `scrollWidth == clientWidth`、`scrollHeight == clientHeight`、DPR 1。9幅QAは既存runtime testにCoreを追加し、320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440を対象にした。

Reviewerは独立第三者ではなく、Creative / Art DirectionとBusiness Owner / Conversionのstructured review rolesである。結果は統計実験や実CVRではない。

## Formal結果

| Prototype / Variant | Win Rate | Trust | Conversion Intent | Reviewer A | Reviewer B | Mobile |
|---|---:|---:|---:|---:|---:|---:|
| P02 Baseline | 0.6250 | 0.3333 | 0.3333 | 0.7500 | 0.5000 | 0.7500 |
| P02 Trust Core | 0.7083 | 0.5417 | 0.5417 | 0.7500 | 0.6667 | 0.7500 |
| P02 Full Enriched | 0.7083 | 0.6250 | 0.6250 | 0.7500 | 0.6667 | 0.8333 |
| P10 Baseline | 0.6250 | 0.3333 | 0.5000 | 0.9167 | 0.3333 | 0.5833 |
| P10 Trust Core | 0.6250 | 0.3333 | 0.5000 | 0.9167 | 0.3333 | 0.5833 |
| P10 Full Enriched | 0.7083 | 0.5417 | 0.5417 | 0.9167 | 0.5000 | 0.6667 |

### P02

Trust CoreはBaseline比でTrust `+0.2084`、Conversion Intent `+0.2084`、Reviewer B `+0.1667`。CoreのFormal Win RateはFullと同じ `0.7083` だが、TrustはFullより `0.0833` 低い。したがって「少ないEvidenceで総合競争力を維持」は観測されたが、「少ないEvidenceでTrustもFullと同等」は未成立。

P02のCoreで最も意味があるのは、緒方幸一氏というWHO単独ではなく、問い合わせ→内容確認→サービス説明・見積→納得後契約というHOW / NEXT / DECISIONの接続である。20年・300社以上はBaselineから保持した定数なので、今回のAblationだけではその数値単独の効果は特定できない。

### P10

Trust CoreはBaselineと同じ結果になった。これは失敗ではなく、Baseline自体がすでに「個人相談無料＋モヤモヤを聞き価値観を整理＋転職するかは相談してから」という最小CTA構造を持っていたためである。

FullだけがTrust `+0.2084`、Reviewer B `+0.1667`、Mobile `+0.0834` を示した。担当者名だけ、または継続支援だけの単独効果は今回分離していない。現時点の最も妥当な仮説は、担当者の人間的責任主体と、相談後も続く支援の連続性が、相談の安全性を補完しているということ。

## Ablationの直接比較

下表は同一Benchmark × Viewport × Reviewerの12票で、後者が前者に勝った軸の割合。Tieは0.5としている。これは内部structured reviewの方向指標であり、Real-world conversion liftではない。

| 比較 | Trust | Conversion Intent | 解釈 |
|---|---:|---:|---|
| P02 Baseline → Core | 0.7500 | 0.7500 | HOW / NEXT / DECISIONの接続が方向改善。 |
| P02 Core → Full | 0.8333 | 0.8333 | Fullの追加Verified Evidenceがさらに効いた。 |
| P10 Baseline → Core | 0.5000 | 0.5000 | 全体としてTie。最小CTA Evidenceだけでは追加効果なし。 |
| P10 Core → Full | 0.7500 | 0.7500 | WHOの責任主体＋継続性の組み合わせが追加効果の候補。 |

## Evidence分類とPlacement

| Evidence | Strength | 推奨Placement | 今回の観測 |
|---|---|---|---|
| 代表者／担当者の実名・資格 | E2 Specific | Middle〜Before CTA | 名前だけでは足りず、何をする人かとの接続が必要。 |
| 20年・300社以上 | E2 Specific | HeroまたはQuiet Chapter | P02ではBaseline定数。単独因果は未分離。 |
| 問い合わせ→説明→見積 | E3 Operational / E5 Decision Enabling | CTA Zone直前 | P02 Coreの改善候補。 |
| 納得後契約／転職するかは相談後 | E4 Risk Reducing / E5 Decision Enabling | After CTA | 行動の判断境界として機能。保証や無勧誘方針とは混同しない。 |
| 無料条件 | E4 Risk Reducing / E5 Decision Enabling | Before CTA | P10 Coreでは既存Baselineと同等。単独では追加効果なし。 |
| 転職後も無料でキャリア伴走 | E4 Risk Reducing | CTA Zone近傍 | P10 Fullの追加改善候補。継続性を具体化。 |
| 企業から紹介手数料 | E2 Specific | CTA Zone近傍の短い補助説明 | 無料条件の仕組みを説明するが、人物・継続性との組合せ効果は未分離。 |

## Most / Least Effective Evidence

「最も効いた」と断言できる単独Evidenceはまだない。P02ではProcess＋Decision Boundaryのまとまりが最有力で、P10ではPerson＋Continuity / Business Modelの組合せが最有力である。

Least effectiveに近い結果はP10 Trust Core。無料・価値観整理・相談前の判断境界を残してもBaselineから追加改善しなかった。これは「無料」や「相談してから」というコピーを足せばTrustが上がる、というRuleを否定する材料である。

## Evidence Interaction

P02は `Core < Full` なので、Fullに追加されたEvidenceに増分価値がある。ただし、どの1項目かは未分離。P10は `Baseline ≒ Core < Full` なので、最小CTA構造だけでなく、責任主体・継続性・事業モデルの接続が必要な可能性が高い。単独効果と相互作用を分離するには、次回は1つだけEvidenceを変える必要がある。

## Rule Status

| Rule | Status | 根拠 |
|---|---|---|
| PROOF_TO_PROCESS | OBSERVED | P02 Core方向改善。ただしP10 CoreはBaseline同等。 |
| PERMISSION_BEFORE_ASK | OBSERVED | P10の相談許可は構造として有効だが、Core単独の増分効果はなし。 |
| AFTER_CLICK_CERTAINTY | OBSERVED | P02の契約判断境界が改善候補。 |
| EVIDENCE_ECONOMY | HYPOTHESIS | Coreは総合競争力を維持したが、TrustはFull未満。 |
| MOBILE_ACTION_BUDGET | REPLICATED | Core / Fullとも9幅QAとExact viewportでAction visibilityを維持。 |
| WHO_HOW_NEXT_BRIDGE | OBSERVED | P02で方向改善、P10ではFullの追加Evidenceが必要。 |
| UNKNOWN_BOUNDARY | REPLICATED | 不明な守秘・返信時間・無勧誘等を捏造せずLedgerに保持。 |
| EVIDENCE_STRENGTH_MODEL | OBSERVED | E1〜E5をPlacementと分離して運用できたが、強度の因果順位は未確定。 |

Rule Cardsは `config/trust_conversion_architecture_v1.json` の `ablation_validation.rule_cards` に保存した。今回のENGINE_READY_CANDIDATEは空。`UNKNOWN_BOUNDARY`と`MOBILE_ACTION_BUDGET`は実装安全策として扱いやすいが、Trust因果の6条件を満たしたとは判定していない。

## Hearing Requirements

### REQUIRED

- 誰が対応するか（個人名または担当チーム）
- 対応範囲と対象外
- 問い合わせ／相談の最初の一手と、その後の流れ
- 料金・無料条件・費用発生タイミング
- 各主張を裏付ける公開一次Evidenceまたは明示的なUNKNOWN

### HIGH_VALUE

- 対応者の経歴・資格・役割
- 相談方法・時間・場所・返信目安
- 守秘・個人情報の扱い
- 勧誘方針、契約・転職を進めない場合の扱い
- 顧客が選べること、断れること
- 継続支援の条件、紹介手数料など意思決定に関わる事業モデル
- 代表者の言葉、実在事例、検証可能な実績

### OPTIONAL

- 権利許諾済み人物写真
- 詳細な実績数値・結果事例
- 現場／オフィス写真

人物写真はREQUIREDではない。名前や写真だけではTrust因果を成立させないため、対応内容・範囲・次の流れを優先して聞く。

## Official Evidence Provenance

P02は[まほら社労士事務所の代表挨拶](https://www.mahora-sr.jp/page_001.html)、[公式トップ](https://www.mahora-sr.jp/)、[契約までの流れ](https://www.mahora-sr.jp/page_009.html)、[スポット相談](https://www.mahora-sr.jp/page_008.html)を参照した。P10は[つぶだてる公式LP](https://www.tsubudateru.com/lp)、[サービスページ](https://www.tsubudateru.com/service)、[宮原彩乃氏の公式プロフィール](https://www.tsubudateru.com/member/ayano-miyahara)を参照した。

公式サイトの写真・人物情報は研究用の出典として扱い、正式LPでの再利用にはClient Permissionが必要。確認できない守秘、返信時間、無理な勧誘をしない方針、担当確約、保証は使用していない。

## Overfitting Check

- Core変更はBenchmarkのレイアウトを模倣せず、P02/P10各社の公式事実から設計した。
- P02はKAGAMIの画面構造をコピーせず、自社の問い合わせ〜見積〜納得後契約の流れをCTA Zoneに置いた。
- P10はキャリアBenchmarkの写真・料金カードを模倣せず、公式のモヤモヤ相談・無料条件・価値観整理を維持した。
- External comparisonは既存Opponent Setを維持し、CoreとFullの同一Capture系統を記録した。

## Data / Provenance

- Ablation結果：`data/evidence_ablation_results_v1.json`
- Capture report：`data/evidence_captures/evidence_ablation_capture_2026-09-15.json`
- Core Formal結果：`data/formal_tournament_results/P02_CORE_formal_blind_tournament_v1.json`、`P10_CORE_formal_blind_tournament_v1.json`
- Core identity mapping：`data/formal_tournament_provenance/P02_CORE.json`、`P10_CORE.json`

Previous Full Formal結果は、候補HTMLが変更されていないため再利用し、今回のArtifact `10397341100`で同一HTMLの再Captureを確認した。Fullを「今回新たに再採点した」とは扱わない。
