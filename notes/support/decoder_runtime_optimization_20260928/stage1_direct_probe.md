# stage 1 priorへの直接perturbation: 一時試作の比較 — 2026-09-28

ユーザーの「元DEMではなく、stage 1のoriginal priorに直接perturbationし、stage 2をoriginalに固定したらどうなるか」という質問に対する限定的な試作計測です。
production decoderファイルを変更せず、各ColorCodeインスタンス内のsamplerを一時的に差し替えました。試作は現在のAPIに追加された新modeではありません。

## PyMatchingへの入力配列はlive viewではない

同じcheck matrixを使えることと、既存Matchingの重みを配列の代入だけで更新できることは別です。
公式APIは `Matching.from_check_matrix(H, weights=...)` で列ごとの重みを指定してmatching graphを読み込みます。
[公式API](https://pymatching.readthedocs.io/en/stable/api.html#pymatching.Matching.from_check_matrix)

実際のinstalled forkでH=[[1,1]]、weights=[3,1]からMatchingを作り、入力weightsを[1,3]へ変更しました。
既存Matchingのpredictionは[0,1]のまま、新しいweightsで作り直すと[1,0]になりました。
元のNumPy配列の変更は、読み込み済みのnative graphへ反映されません。

公開 `add_edge(..., merge_strategy='replace')` でweightを更新することはできますが、installed forkの
`src/pymatching/sparse_blossom/driver/user_graph.cc` では変更時に `_mwpm_needs_updating` が立ち、次のget_mwpmでupdate_mwpm/to_mwpmを呼びます。
安価なbulk weight-vector更新として、そのまま再利用できる仕組みではありません。
また同じcheck-matrix列がparallel edgeとなる場合、weight変更によってwinnerとfault IDsも変わり得ます。

## 試した4方式

1. 現行の元X/Z DEM perturbation、stage 1/stage 2ともperturbed。
2. 現行の元X/Z DEM perturbation、stage 2はoriginal（use_original_prior_for_stage2=True）。
3. 2と同じ元DEM draw・同じstage 1 priorを使い、使わないstage 2 probability/column sorting/map permutationだけを省略。
4. 各色の分解済みstage 1 priorに直接 `clip(p1*(1+alpha*U[-1,1]), eps, 1-eps)` を適用。stage 2はoriginal。

全方式が各shotでfresh drawsを使います。4ではshot/member/color/stage-1-column順に独立drawを取り、logical hypotheses間は同じpriorを共有する設計です。
4の3色prior間の相関とperturbation分布は、元DEMに共通drawを適用する現行方式と異なります。
候補生成ルールの変更なのでLERの優劣はこの小標本のtimingからは判断できません。
元stage 2 prior、baseline member0、original-DEM priorによる最終scoringは維持しています。

3は2の**全public outputsが全測定callで完全一致**しています。
全方式・全callの全candidate original correctionsについて、物理syndromeを満たすことをtiming外で検証しました。
4の候補が2と一致することは要求していません。

## 条件と計測

d=9/13、rounds=d、closed triangular Z memory、tri_optimal、uniform circuit p=.001、perfect flags=False。
M=12、alpha=1、perturbation seed20260927、physical seed20260927、warmup physical seed20260928。
full_output=True、comparative=False、original_dem scoring、SWIM/validity/export=False。
既存のcolor_code_so環境、PyMatching2.2.dev2、変更なしのCPU/thread環境。
各方式を順次実行し、steady順序を反転させ、1shot×3回と10shot×1回を測定しました。
各方式のprior分布が異なるため、native matching探索の実行量も異なり得ます。小標本なので速度比は暫定値です。
この比較の内部の数値だけを使い、前の異なる時間帯の測定値とは混ぜません。

steady 10-shot batchのms/shot:

| 方式 | d=9 | d=13 | 新規Matching / shot |
|:---|---:|---:|---:|
| 元DEMにperturbation、stage 2もperturbed（現行） | 216.61 | 647.73 | 66 |
| 元DEMにperturbation、stage 2はoriginal（現行） | 85.16 | 250.11 | 33 |
| 元DEMにperturbation、stage 2はoriginal、不要計算を省略（試作） | 64.37 | 191.73 | 33 |
| 分解済みstage 1 priorへ直接perturbation、stage 2はoriginal（試作） | 58.07 | 150.51 | 33 |

元DEM perturbation＋original stage 2（方式2）に対するdirect stage 1（方式4）の速度比:

- d=9: direct方式は1.47倍高速（31.8%短縮）。出力を維持する不要計算省略だけでも1.32倍高速。
- d=13: direct方式は1.66倍高速（39.8%短縮）。出力を維持する不要計算省略だけでも1.30倍高速。

先の「旧固定版より6〜7倍遅い」計測は方式1（stage 2もperturbed）でした。
original stage 2設定では現在の実装もstage 2 graphをcacheし、各shotの新規graphはstage 1の33個だけです。
方式4でも新規graph数33個は変わりません。方式1から方式4への構築数は66→33です。
stage 2のgraphをcacheしても、stage 1 hypothesisでstage 2 syndromeが変わるため、各candidateのstage 2 decodeは引き続き必要です。

## 10-shot計測の内訳（ms/shot）

stage 1/stage 2時間はstage API全体を含みます。graph API時間はその内数で、加算してはいけません。
native Matchingの初回準備もstage API時間に含みます。

| d | 方式 | prior作成 | stage 1全体 | stage 2全体 | graph API（内数） | 総時間 |
|---:|:---|---:|---:|---:|---:|---:|
| 9 | 現行 original stage 2 | 26.56 | 53.07 | 2.28 | 14.01 | 85.16 |
| 9 | 不要stage 2 prior省略 | 3.97 | 55.22 | 2.25 | 14.73 | 64.37 |
| 9 | direct stage 1 | 0.87 | 52.01 | 2.16 | 13.73 | 58.07 |
| 13 | 現行 original stage 2 | 75.88 | 160.22 | 5.49 | 35.93 | 250.11 |
| 13 | 不要stage 2 prior省略 | 7.94 | 169.05 | 5.55 | 37.85 | 191.73 |
| 13 | direct stage 1 | 1.64 | 137.42 | 4.54 | 30.21 | 150.51 |

d13のdirect stage 1ではprior作成が約1.6ms/shotに収まる一方、stage 1のMatching準備＋decodeが約137ms/shot残ります。
乱数の生成・数値リスト更新より、新しい重みを取り込むnative準備・matching処理が主な残余コストです。
元DEMからstage 1 priorを計算すること自体が「接続関係を作り直す必要」を生むわけではなく、
接続関係が固定でも現在のPyMatching経路が重みごとに内部のweighted matchingを準備する点が重要です。

成果物: `stage1_direct_probe.csv`（40行、warm/steady・全wall/API内訳）、
`stage1_direct_probe_environment.json`（条件・input mutation実験・一致検証・program SHA256）、
`stage1_direct_probe.log`。計測programと一時directoryは削除済みで、`stage1_direct_probe_cleanup.json`に記録しています。
production decoderの10ファイルのSHA256は先のsource_manifestから変化していません。新規production mode追加・commit/push・LER campaignは行っていません。
