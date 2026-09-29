# Stage 1摂動のnative実装・検証・計測 — 2026-09-29

`stage1_perturbation=True`で、PyMatchingが各shotのstage 1候補をまとめて生成します。color-code-stimは固定original priorのstage 2と既存の候補選択を担当します。M=12、full output、10-shot batchの総decode時間は、**同じ摂動仕様の再構築参照に対して11.61〜11.77倍**、**保存したoriginal DEM摂動方式に対して24.58〜41.83倍**速くなりました。後者には方式変更が含まれます。

## per-shot再サンプル導入前の固定ensembleとの比較

ご指摘の比較対象は、2026-09-28の固定ensemble版 `072a87d` です。この版は同じM=12 ensembleを全shotで使い回し、対応する3条件すべてで旧測定のgraph_countは72でした。前節の「original_dem」行は既にper-shot再サンプルする版の値であり、ここでの旧固定ensembleとは別の比較です。

両レポートのfull output測定を、距離・batch sizeが一致する行で比べます。旧版は各条件1回の測定、native版は同じ入力shotによる3回測定の平均です。測定日とStim shot seedは異なるためpaired比較ではありません。

| d | batch | 旧固定ensemble `072a87d` (ms/shot) | 今回native (ms/shot) | 旧版/native | decode時間短縮 |
|---:|---:|---:|---:|---:|---:|
| 9 | 10 | 31.476 | 3.499 | 9.00倍 | 88.9% |
| 13 | 10 | 89.028 | 10.171 | 8.75倍 | 88.6% |
| 17 | 1 | 1621.377 | 28.127 | 57.64倍 | 98.3% |

したがって、今回のnative版は**shotごとに再サンプルしなかった旧固定ensembleの計測値よりも**、この記録上は約9.0倍（d=9）、8.75倍（d=13）、57.64倍（d=17、1-shot）速いです。

この比較は全decoderの実測差であり、速度差をsampling lifecycleだけに帰属させることはできません。旧 `072a87d` の測定はstage 2にもperturbed priorを使い、今回のnative版は計画どおりoriginal stage 2を固定しています。また、stage 1候補の摂動対象も異なります。測定は別日・別shotで、旧版は1回、nativeは3回です。固定ensembleとの候補・LER同一性を示す比較ではありません。元の数値は[旧legacy CSV](../decoder_runtime_optimization_20260928/legacy_comparison.csv)、対応する今回のnative値はこのレポートの`measurements.csv`、集約は[`pre_resampling_fixed_ensemble_comparison.csv`](pre_resampling_fixed_ensemble_comparison.csv)です。

## 実装した仕様

- `stage1_perturbation=False`は、各shot/memberのoriginal X/Z DEM摂動を維持します。固定stage 2のcacheも保存用commitに含めています。
- Trueではoriginalの分解済みstage 1 priorを、辺・色・shot・memberごとに独立に摂動します。Mには無摂動member 0を含めます。同じshot・色の乱数を比較用の各logical classで共有します。
- 実効設定は`enable_prior_perturbation=True`、`use_original_prior_for_stage2=True`です。M=1 / alpha=0は既存の対応モードと全出力が一致します。
- PyMatchingはoriginal solverと再利用work solverを保持します。MatchingGraphと64個超のfault ID用SearchGraphの重みを更新し、既存と同じ候補ごとの整数化・normalizationを行います。queue・探索状態・arenaを初期化して領域を再利用します。より複雑なsyndromeではarenaの容量が増えることはあります。
- 出力はshot-majorの`(N*M,F)`、重みは`(N*M,)`です。乱数scheme version 1はSplitMix64＋`mt19937_64`上位53bitです。実効seed・version・絶対shot位置を保存します。色streamはr=0/g=1/b=2です。
- simulationのworkerは`shot_start`を渡します。seed未指定はrun開始時に一度解決して共有・保存します。同じ入力shotの摂動・訂正はbatch分割・worker数・cache再生成によらず再現します。既存Stim samplingのchunk seed規則はそのままです。
- 対象は単純なcheck-matrix graph、有限・非負log oddsです。parallel edge、負の重みを生む可能性のあるprior、構築後の接続変更、特殊なdecode APIはTrueの場合に明確なエラーになります。Falseの既存SWIM/path-gap機能を保持しています。

APIと使用例は各packageのREADME、および`docs/native_perturbation.md` / `docs/native_stage1_perturbation.md`にあります。rootの専用設定は`configs/native_stage1_perturbation_comparison.yaml`です。`configs/main.yaml`は変更していません。

## 検証結果

| suite | 保存前 | 実装後 |
| --- | --- | --- |
| PyMatching Python | 117 passed | 129 passed |
| PyMatching C++ | 95 passed | 99 passed |
| color-code-stim | 231 passed、既存skip 2 | 252 passed、既存skip 2 |
| color_code_softoutput | 318 passed | 325 passed |

C++全テストをAddressSanitizer・UndefinedBehaviorSanitizer・leak検査付きで実行しました。新規4 C++テストは乱数値、fresh solverとの一致、64個超fault ID、pointer/構築回数の安定性、infeasible syndrome後の復帰を検証します。

Pythonの独立MT19937-64実装が乱数・摂動lawを確認します。nativeと各候補のfresh Matchingの訂正・重みが一致します。境界、零syndrome、零重み、同点、反復呼び出し、unsupported入力も検証しました。decoderではcode-capacity/circuit、両選択basis、comparative off/onの全candidate・最終訂正・選択重み・baseline・補助出力を独立fresh pipelineと比較しています。M=1/alpha=0、pristine既存fixture、SWIM/validity、保存復元、空batch、一括/分割/明示offset、worker 1/2、cache再生成が通過しました。

同じ実装エージェントによるsource reviewと独立数値oracleによる検証です。外部peer reviewではありません。正確なコマンドと結果は`validation.json`、C++ログおよび`root_tests.log`に記録しました。

## 計測方法

- d=9/13/17、uniform circuit noise p=0.001、rounds=d、triangular Z memory、tri_optimal。
- M=1/12、alpha=1、perturbation seed=20260929、final selection basis=`original_dem`、comparative=False。`full_output=False/True`の両方を測定。
- 距離ごとに同じ10 physical shotsを先に生成しました（Stim seed=817+d）。N=1はその先頭shot、N=10は全shotです。各方式に同じ配列を渡しています。
- 各方式/d/M/full_outputを別processで初期化しました。constructorと最初の10-shot decodeを別記録し、同じ入力によるwarmup後にN=1/10を各3回測定しました。測定前に乱数位置を戻し、GCを行います。入力検証・出力hash・syndrome検査はtimerの外です。
- **original_dem**: 保存したdecoder commit `ddfd777`をtemporary archiveからimportし、original DEM摂動＋固定original stage 2を実行します。
- **reference**: 新方式と同じstage 1 prior・同じdrawを用い、M−1候補ごとにordinary Matchingを新規構築します。無摂動member 0はpristine solverを再利用します。stage 2は新方式と共通の固定cacheです。drawはnativeの診断APIから取得し、log計算も揃えます。乱数lawは別のpure Python oracleで検証済みです。この参照はnative templateを保持するため、RSSを最小構成のPython実装のメモリ量とは解釈しません。
- **native**: 再利用solverで辺重みを更新し、C++内でshot×memberをdecodeします。
- 全方式で同じCMake Release PyMatching binaryを使用しました。Python 3.12.14、NumPy 1.26.4、Stim 1.16.0、Intel i7-13700H、WSL2/Linux、GNU 11.4.0、`-O3 -mno-avx2`。詳細・binary/program/input SHA256は`environment.json`にあります。
- 裸の総時間216行と、別callのinstrumented profile 72行、初期化36行を保存しました。profileは計測wrapperのoverheadを含むため、裸の平均総時間と混ぜません。factory/PM API時間はstageの内数であり、独立した加算項ではありません。
- 実行順は距離、M、full_output、original→reference→nativeでした。CPU affinity・thread設定は変更していません。3回の有限測定であり、OS schedulingなどのばらつきがあります。平均・標準偏差・min/maxを`summary.csv`に保存しています。

## warmup後の総decode時間

M=12、10-shot batch。すべて3回の平均で、単位は**ms/shot**です。比率は平均時間の比です。

| d | N | full_output | original DEM (ms/shot) | stage 1再構築 (ms/shot) | native (ms/shot) | 同仕様の高速化 | 旧方式との実測比 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 10 | False | 92.357 | 44.541 | 5.987 | 7.44× | 15.43× |
| 9 | 10 | True | 86.024 | 40.626 | 3.499 | 11.61× | 24.58× |
| 13 | 10 | False | 304.767 | 120.000 | 13.337 | 9.00× | 22.85× |
| 13 | 10 | True | 281.889 | 119.750 | 10.171 | 11.77× | 27.72× |
| 17 | 10 | False | 829.464 | 275.757 | 25.624 | 10.76× | 32.37× |
| 17 | 10 | True | 1085.620 | 302.632 | 25.956 | 11.66× | 41.83× |

同仕様の比率は、stage 1摂動＋固定stage 2という同じ処理の高速化です。旧方式との比率はoriginal DEM摂動から直接stage 1摂動への変更も含みます。M>1ではcross-colour相関も変わるため、訂正やLERの同一性を主張しません。

M=12、1-shot batch、full output:

| d | N | full_output | original DEM (ms/shot) | stage 1再構築 (ms/shot) | native (ms/shot) | 同仕様の高速化 | 旧方式との実測比 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 1 | True | 95.068 | 53.913 | 7.670 | 7.03× | 12.39× |
| 13 | 1 | True | 226.052 | 137.744 | 17.515 | 7.86× | 12.91× |
| 17 | 1 | True | 666.712 | 315.014 | 28.127 | 11.20× | 23.70× |

M=1、10-shot batch、full output:

| d | N | full_output | original DEM (ms/shot) | stage 1再構築 (ms/shot) | native (ms/shot) | 同仕様の高速化 | 旧方式との実測比 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 10 | True | 0.305 | 0.392 | 0.330 | 1.19× | 0.92× |
| 13 | 10 | True | 0.729 | 0.700 | 0.716 | 0.98× | 1.02× |
| 17 | 10 | True | 1.705 | 1.634 | 1.867 | 0.88× | 0.91× |

M=1は全方式が無摂動の固定graphを使います。今回のnative版はd9で約8%、d17で約10%長く、d13ではほぼ同等でした。sub-ms級の測定には大きなばらつきがあり、M=1の速度改善は示していません。出力は全方式一致しています。

`full_output=False`とTrueには既存decoderの異なるobservable出力経路があり、Falseが必ず速いとは限りません。両者の実測を上表とCSVに保存しました。

## stage別内訳と構築回数

M=12、full output、10-shot batchの**別のprofile call**です。時間をms/shotに換算しています。stage 1はnativeの場合に乱数生成・重み更新・reset・matchingを含みます。mapping/selection列はCandidateEvaluatorのmappingとscore時間です。最終argmin、observable計算、Python loop等はotherに含みます。旧方式のDEM摂動・再分解等もotherです。

| d | 方式 | stage 1 (ms/shot) | stage 2 (ms/shot) | mapping/score (ms/shot) | other (ms/shot) | stage 1 factory | stage 1 C++ build | stage 2 factory | stage 2 C++ build |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | original_dem | 67.150 | 2.591 | 1.444 | 27.133 | 330 | 330 | 0 | 0 |
| 9 | reference | 38.630 | 0.731 | 0.636 | 0.319 | 330 | 330 | 0 | 0 |
| 9 | native | 1.895 | 0.694 | 0.607 | 0.273 | 0 | 0 | 0 | 0 |
| 13 | original_dem | 240.340 | 5.644 | 3.189 | 70.675 | 330 | 330 | 0 | 0 |
| 13 | reference | 113.021 | 1.775 | 1.636 | 0.575 | 330 | 330 | 0 | 0 |
| 13 | native | 5.799 | 1.740 | 1.550 | 0.554 | 0 | 0 | 0 | 0 |
| 17 | original_dem | 1247.028 | 16.057 | 10.791 | 193.671 | 330 | 330 | 0 | 0 |
| 17 | reference | 293.231 | 4.739 | 3.832 | 1.410 | 330 | 330 | 0 | 0 |
| 17 | native | 20.272 | 4.660 | 4.022 | 1.187 | 0 | 0 | 0 | 0 |

nativeのwarmup後は全72 profile条件中の対応native条件でstage 1/2 factory・C++ buildとも0回です。M=12の再構築参照と旧方式はN=1で33回、N=10で330回のstage 1 graphを構築します。全方式の固定stage 2はwarmup後0回です。stage 2 matchingそのものは各candidateで引き続き実行します。

## 初期化

M=12、full outputのconstructorと**最初の10-shot decode（profile wrapperあり）**を秒で示します。最初のdecodeはlazy DEM分解・symbolic prior/mapping準備・初回solver構築などを含みます。

| d | 方式 | constructor (s) | first decode (s) | 合計 (s) | stage 1 factory | stage 1 C++ build | stage 2 factory | stage 2 C++ build |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | original_dem | 0.047 | 1.804 | 1.851 | 333 | 333 | 3 | 3 |
| 9 | reference | 0.049 | 1.337 | 1.386 | 333 | 336 | 3 | 3 |
| 9 | native | 0.048 | 0.957 | 1.005 | 3 | 6 | 3 | 3 |
| 13 | original_dem | 0.104 | 5.482 | 5.586 | 333 | 333 | 3 | 3 |
| 13 | reference | 0.115 | 4.536 | 4.651 | 333 | 336 | 3 | 3 |
| 13 | native | 0.120 | 3.183 | 3.304 | 3 | 6 | 3 | 3 |
| 17 | original_dem | 0.193 | 13.372 | 13.565 | 333 | 333 | 3 | 3 |
| 17 | reference | 0.181 | 10.178 | 10.359 | 333 | 336 | 3 | 3 |
| 17 | native | 0.187 | 7.744 | 7.931 | 3 | 6 | 3 | 3 |

nativeは3色のstage 1 Matchingがpristine/work solverを各1個ずつ作るためC++ buildは6、stage 2は3です。warmup後の再構築はありません。参照版の初回数にはtemplate solverの構築も含みます。

## メモリ

process全体のOS報告resident memoryです。Python/import/circuit/DEMを含み、backend作業領域だけの量ではありません。cold RSSは初回decode後、warm RSSは10-shot bare timing後の3回平均、peakは子processの全計測後の`getrusage`報告値です。

| d | 方式 | cold RSS (MiB) | warm RSS (MiB) | process peak RSS (MiB) |
| --- | --- | --- | --- | --- |
| 9 | native | 259.6 | 262.2 | 261.9 |
| 9 | original_dem | 293.4 | 296.4 | 296.1 |
| 9 | reference | 259.7 | 262.7 | 262.5 |
| 13 | native | 359.4 | 367.8 | 367.9 |
| 13 | original_dem | 470.9 | 480.8 | 481.1 |
| 13 | reference | 359.5 | 369.0 | 368.4 |
| 17 | native | 550.4 | 570.0 | 570.2 |
| 17 | original_dem | 809.5 | 832.8 | 834.0 |
| 17 | reference | 550.3 | 572.1 | 571.9 |

固定topologyとworkspaceを保持します。大きいsyndromeに遭遇するとarenaは容量を追加し得るので、あらゆるsyndromeでallocationが0であるとは主張しません。旧方式は動的graph LRUも保持します。ASan/UBSan/leak検査はすべて成功しました。

## artifact・依存commit・cleanup

- `measurements.csv`: 裸の216測定、repeat、時間、digest、RSS。
- `profiles.csv`: 72個のstage/factory/PM API内訳とPython/C++構築回数。
- `initialization.csv`: 36個のconstructor、初回decode、構築回数、RSS。
- `summary.csv` / `comparisons.csv`: 全条件の平均・標準偏差・範囲、および今回実装前のper-shot版に対する二種類の比較比率。
- `pre_resampling_fixed_ensemble_comparison.csv`: 前回レポートの旧固定ensemble `072a87d` とnative版の距離/batch対応比較。
- `timing_verification.json`: 全reference/native digest一致、M1一致、全候補syndrome、warm構築回数の検査結果。
- `validation.json` / `baseline_cpp.log` / `native_cpp.log` / `root_tests.log`: 回帰・新規・sanitizer検査の結果。
- `environment.json` / `source_manifest.json` / `dependencies.json`: 環境、hashと依存commit。
- `cleanup.json`: 計測専用program・temporary checkpoint/input/child JSONの削除記録。

保存用branchはroot/decoderの`codex/per-shot-runtime-20260929`です（root `5c7d355`、decoder `ddfd777`）。native実装は3repoとも`codex/native-stage1-perturbation-20260929`です。PyMatching baseは`7a26e6a8ef20080e9eab7240ce33581cc3880d03`です。公開依存commitはPyMatching `40ef9296f1d73aa4d629460bdc80bcf57bb1f7b5`、color-code-stim `6a6bd8b30b3de62c0a4132fcf440bde48c3e3f3a`です。rootの公開HEADは同名branch、詳細は`dependencies.json`を参照してください。mainへのmergeは行いません。

これらは有限入力での正しさとruntimeの検証です。新方式のLER優位性、一般の負の重み/parallel graph対応、漸近速度や新しいsoft-output theoremは評価していません。大きなsampling campaignは実施していません。
