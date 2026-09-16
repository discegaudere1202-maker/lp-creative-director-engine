# LP品質最終実地検証Phase — NO_WEB field validation

更新日: 2026-09-16

## Phase Status

HOLD

## Purpose

実在のNO_WEB事業者に対し、実写真未取得の営業前提で、公開情報だけからEngineのみで営業サンプルLPを生成できるかを最終実地検証した。自動QA PASSではなく、実際に経営者へ送れるか、100万円価値Gateを満たすかで判定した。

## Test Population / Scope

20社。NO_WEB限定、地域ローカル中心。ケア、店舗、施工、現場サービス、物販・機械、学習、相談、撮影、生活支援を混在させ、公開情報量にも差を持たせた。WEAK_WEBは対象外。

## Evidence Policy

Phase 6 Sales Masterの公開調査結果を引き継ぎ、公式SNSの公開プロフィール・公開サービス範囲・地域情報・公開連絡導線のみをEvidence化した。各社4件（OWNER_IDENTITY / SERVICE_SCOPE / PLACE_WIDE / CTA_CHANNEL）。料金、実績、口コミ、資格、受賞、保証、写真は未確認として主張しなかった。Safetyは20/20 PASS、生成物は研究・営業サンプル扱いで `NOT_PRODUCTION_APPROVED`。

## Visual Policy

権利不明素材は使わず、Engine生成の非事実ベクターシーンを、将来の同役割・同比率の実写真へ差し替えるEvidence Slot代理として配置した。実在店舗・実施工・実人物・実商品であるような表記は置かない。内部制作ラベルは表示しない。

## Production Method / QA

Engine only。Manual LP Edit = 0。Research → Evidence → Safety → Strategy → IA → Copy → Art Direction → Design Tokens → Composition → Renderer → Browser QAを一気通しした。

最終GitHub Run `35075746574`（commit `3b2bcee`）で、Chromium実機による320 / 360 / 375 / 390 / 430 / 768 / 1024 / 1280 / 1440の9幅、desktop 1440×1000、mobile 390×844のcaptureを実施した。契約テスト30件、Chromium導入、生成・capture・artifact uploadは成功。最終artifact: `10438457004`。

## Per-case Review

全20件を人間の目でdesktop/mobile capture、Hero、中盤、CTA、Photo Replacement Readiness、営業送付可否の観点から確認した。全件の最終判定はHOLD。自動QAが通っても、実写真に依存せず100万円価値を感じる営業サンプルとしては未達とした。

| ID | 事業者 / 業種 | Profile | 判定 | 主な良点 | 主な不足 |
|---|---|---|---|---|---|
| R4-G001-003 | あったか鍼灸整骨院 美容部門 / 鍼灸院 | care_rhythm | HOLD | ケアの余白と予約導線 | 施術者・空間・手技の実在感が弱い |
| R4-G002-002 | スタジオポエ / ヨガ | care_rhythm | HOLD | 静かな呼吸のリズム | スタジオ固有の温度と人物証拠が弱い |
| R4-G004-001 | Lumina Beauty Salon / 脱毛 | care_rhythm | HOLD | 柔らかなケア表現 | 店舗・接客・機器の具体性が弱い |
| R4-G005-002 | なぎのみらい / ヘッドスパ | care_rhythm | HOLD | 予約前の不安からCTAへ接続 | 施術環境・手元の写真役割が不足 |
| R4-G009-003 | クリーンアップ薬院 / ハウスクリーニング | field_ledger | HOLD | 範囲確認と見積導線 | 作業現場・道具・仕上がりの証明が弱い |
| R4-G010-046 | Brush Up Sapporo / エアコン清掃 | field_ledger | HOLD | 現場系の情報順序 | 機材・作業・地域性の視覚証拠が弱い |
| R4-G011-047 | Maylynn Paint / 外壁塗装 | field_ledger | HOLD | 施工範囲から見積へ接続 | 外壁・職人・工程の主役写真が必要 |
| R4-G012-046 | 黒岩瓦工事 / 屋根修理 | field_ledger | HOLD | 問題確認の順番が明快 | 屋根・雨漏り・安全作業の具体性が弱い |
| R4-G013-046 | 株式会社石川造園 / 造園 | field_ledger | HOLD | 素材・現場系の構造 | 庭・植物・施工前後の実在感が不足 |
| R4-G014-046 | 株式会社マルックス / 害虫・害獣駆除 | field_ledger | HOLD | 状態→対応→相談の因果 | 作業対象・衛生・現場の説明力が弱い |
| R4-G015-046 | かたずけや / 不用品回収 | field_ledger | HOLD | 対応範囲と入口が明快 | 人・車両・搬出現場の証拠が弱い |
| R4-G016-046 | 有限会社高宮 / カーコーティング | machine_catalogue | HOLD | 商品・機械系の骨格 | 車両・仕上がり・工房写真が不足 |
| R4-G018-046 | Future Bike Store / バイク修理 | machine_catalogue | HOLD | 用途確認の導線 | 車体・工具・作業者の固有性が弱い |
| R4-G019-002 | 堤祥子音楽教室 / 音楽教室 | studio_invitation | HOLD | 参加までの3段階 | 教室・講師・楽器の体験価値が弱い |
| R4-G020-001 | T-wing / ダンス教室 | studio_invitation | HOLD | 動きの入口を整理 | レッスンの熱量・人物・空間が不足 |
| R4-G021-001 | わたしの台所 / 料理教室 | studio_invitation | HOLD | 体験の順序が明快 | 食材・手元・教室の具体性が弱い |
| R4-G023-047 | こっとんフォト / 撮影 | image_story | HOLD | 撮影シーンを想定した構図 | カメラ・被写体・成果物の写真性が弱い |
| R4-G024-001 | 福岡料理×婚活 宮崎家 / 結婚相談 | conversation_rail | HOLD | 相談の心理障壁とCTAが接続 | 人の信頼感・相談空間の証明が弱い |
| R4-G025-001 | SY WORK / 家事代行 | local_route | HOLD | 地域導線と行動順序 | 担当者・訪問・生活場面の固有性が弱い |
| R4-G008-046 | ドッグトレーニングスクールAID / 犬のしつけ | local_route | HOLD | 地域サービスの入口 | 犬・トレーナー・訓練場面が不足 |

## Quality Review Summary

業種別visual family、CTAの因果、390pxの可読性、9幅のoverflow耐性は改善した。Heroは一目で業種が分かり、同じ3列カードの連発も避けられた。一方、会社名・地域・サービス範囲を構造へ入れても、写真のない現場で「その会社専用」の説得力を作り切れていない。抽象ベクターはEvidence Slotの代理としては成立するが、Photography DirectionとVisual Authorityが100万円水準には不足する。

## PASS / HOLD / FAIL Summary

最終人間判定: PASS 0 / HOLD 20 / FAIL 0。Browser QAの最終Runは20/20 PASS。人間判定はQA PASSをもってPASSへ繰り上げない。

## Photo Replacement Readiness

構造ゲートは全20件で成立（同役割・同比率、文字重なりなし、data属性とart_direction manifestに差し替え対象を記録）。ただし `実店舗・実現場・実商品・実人物写真` という汎用ターゲットに留まっており、業種ごとの撮影指示（誰が、何を、どの距離・構図で、何を証明するか）が粗い。Readinessは「構造PASS / Art Direction未達」と評価する。

## Good Patterns

* Company Truth・Customer State・CTAを1本の順序へ変換できた。
* 7系統のvisual familyでケア、現場、学習、相談、撮影、機械、地域を分岐できた。
* Evidenceが薄い案件でも、主張を増やさず余白・タイポ・抽象素材で見せ場を作れた。
* MobileはCTAを全幅化し、主要9幅でoverflowとconsole/page errorを検証できる。

## Root Causes

1. 実写真の役割設計が汎用的で、業種別の撮影brief・証明対象まで落ちていない。
2. 生成ベクターが雰囲気と構図は担うが、施工・接客・商品・人物の信頼を代替できない。
3. 5セクションの基本骨格とEvidence面の反復が残り、Company Truth → Formの差がprofile差に留まる案件がある。
4. CTAは因果が通るが、公開情報が薄い案件では「問い合わせる理由」の具体性が弱い。

## Engine Improvements

* NO_WEB field validation用に7 visual familyと業種別profileを追加。
* Customer Stateに応じたprocess steps、supporting、contact、close copyを追加。
* visual scene、role、same-role photo replacement、crop/layout constraintsをart_direction/compositions/manifestへ出力。
* Heroの長いサービス範囲を意味単位の短い業種名へ再アートし、全文はEvidence・本文面へ保持。
* 中黒を意味境界として扱う日本語改行ロジックを追加。
* 回転要素がline detectorを誤認させる問題を解消。
* 内部制作ラベルをHTMLから除去し、metadataのみに保持。

## Re-test Result

同一20社を3回のEngine改善反映後に再生成。baselineからimprovedへvisual familyの多様化、内部placeholder除去、Hero/見出し改行、QA誤検知要因を横断修正した。最終CI Run `35075746574` は成功し、最終成果物はartifact `10438457004`。自動QAを満たしても人間判定は20件HOLDであり、PASS率だけで量産可否を出さない。

## PoC Readiness

100件PoCへは進めない。追加ブラッシュアップが必要。次のGateは、業種別の実写真撮影brief生成、抽象素材からの脱却または生成画像の適切な役割分担、会社固有のMid-frame証拠、profileごとのIA差分、実営業者による送付判定である。

## GitHub

Repository: `discegaudere1202-maker/lp-creative-director-engine`

Latest main: `f04ab1f591ec87a86c8d08124c9c7b796cce7379`

Final validation Run: `35075746574` / success / artifact `10438457004`

Tests: 30 production/Safety/e2e/quality/form-causality contract tests PASS。CI上でChromium install、生成、9幅Browser QA、exact capture、artifact upload PASS。

## Remaining Risks

* 実写真取得後の差し替え結果は未検証。
* 無料素材・生成画像の権利・ライセンス・利用規約の個別確認フローは未接続。
* NO_WEBの公開情報量がさらに薄いケース、Instagram以外の導線、予約媒体のみのケースは追加検証が必要。
* 現在の自動QAは視覚的な100万円価値やAIテンプレ臭を完全には判定できない。

## Final Conclusion

Phase StatusはHOLD。NO_WEB 20社をEngine only・Manual LP Edit=0で通し生成し、安全境界、9幅Browser QA、captures、visual family分岐、Photo Replacementの構造準備は確認できた。しかし、実写真未取得でもそのまま営業に送れる「その会社専用の100万円価値」には未達。写真役割の業種別設計、Company Specificity、Mid-frameの証拠性、構造の反復を改善してから100件PoCへ進む。
