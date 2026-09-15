# Benchmark Blind Tournament v1
更新日: 2026-09-15

## 目的
内部Scoreが高いだけの「自称Premium」を防ぐ。

Candidate Frameを
同じVisual Authority / 目的を持つ日本上位Benchmark 3–5件と匿名で比較する。

## 0. Tournament Readiness Gate
正式Tournamentを開始する前に、比較Package自体を検証する。

必須:
- Benchmark 3–5件
- Candidateと全Benchmarkに1440px Screenshot
- Candidateと全Benchmarkに390px Screenshot
- Viewportは正式比較では1440 / 390の2種に固定
- Benchmark ID重複なし
- CandidateをBenchmark側へ混入させない
- Production BenchmarkはM3（live / faithfully captured 390px review）済み

M2の公開Mobile画像は研究には使用できるが、Production Benchmark Supremacyの対戦相手には数えない。

Screenshotが揃っていないPreliminary比較を正式Tournament PASSへ昇格しない。

## 1. Blind化
比較時に隠す:
- 会社名
- 制作会社名
- Award名
- 自社/他社フラグ
- URL

表示:
- 同一Viewport Screenshot
- 必要なら1行だけのContext

A/Bの左右位置は毎回Randomize。

## 2. 比較軸
各PairでReviewerは -1 / 0 / +1。

+1 = Candidate優位
0 = 同等
-1 = Benchmark優位

Axes:
1. Immediate Read
2. Distinctness
3. Owner-specificity
4. Visual Hierarchy
5. Craft Detail
6. Emotional Pull
7. Trust
8. Share Impulse
9. Mobile Quality
10. Conversion Intent

Visual-only FrameではTrust/ConversionをN/A可。

ただし、Owner-specificity / Share ImpulseはPremium Peak比較のCritical Axisとして欠落させない。

## 3. Tournament判定
最低:
- Benchmark 3件
- Reviewer 2系統以上
- Desktop 1440
- Mobile 390

Candidate win-rate:
`(wins + ties*0.5) / comparisons`

### PASS候補
- win_rate >= 0.60
- 3 Benchmark以上
- Share Impulse / Owner-specificityが明確に負けていない
- Desktop/MobileともOUTCLASSEDではない

### HOLD
- 0.45–0.60
- Reviewer間で大きく意見が割れる
- Desktopは勝つがMobileが負ける
- 比較Package / reviewer matrixが不完全

### FAIL
- win_rate < 0.45
- 2件以上のBenchmarkに明確負け
- Owner-specificityかShare Impulseで継続的に負ける

## 4. Important
Benchmark Supremacyは「Benchmarkに似せる」Gateではない。

勝つ方法は:
- 違うVisual Authority
- より強いCompany Truth
- より明快なCopy
- より深いCraft
でよい。

Benchmarkの見た目を模倣したらOwner-specificityで落とす。

## 5. Review Loop
Candidate v1
→ Readiness Gate
→ Blind Tournament
→ 負けたAxisだけ抽出
→ Specialist Pass
→ Candidate v2
→ 再Tournament

## 6. Golden Sample条件
Hero/Mid Peakの最低2 Frameが、Visual Authority別Benchmark TournamentでPASSする。
Full LP Scoreだけでは認定しない。

## 7. Evidence level rule
研究段階と認定段階を混ぜない。

- M2: 公開されたMobile Visualを確認済み。Research-ready。
- M3: live / faithfully captured 390pxでCopy・Hierarchy・Interaction・Form Causalityを確認済み。Production Tournament-ready。

CORE / Production SupremacyにM2を混ぜない。