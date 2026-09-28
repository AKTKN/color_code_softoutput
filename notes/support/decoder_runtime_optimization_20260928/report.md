# color-code-stim の runtime 最適化と計測 — 2026-09-28

実装は `external_libs/color-code-stim/` の `main`（開始コミット `072a87d`）のローカル変更です。
ユーザー指定どおり、M>1・alpha>0 の perturbation を **shot ごとに独立に再サンプル**する仕様へ変更しました。
固定 seed の同じ stream 位置では、最適化版の hard decision と全詳細出力が、同じ draw を使う再構築版と完全一致します。
旧固定 ensemble の M>1・alpha>0 出力との一致は要求していません。

## 変更した実装と cache

- `decoders/matching_cache.py` を追加。各 decoder が固定 base matching 6個（3色×2段）を所有し、遅延構築して再利用します。
  動的 weighted matching は graph 内容・確率に対する厳密な key の LRU、上限32個です。各 shot の内部 `StagePrior` も compiled object を保持し、comparative hypotheses が同じ draw の graph を再利用します。
  公開 custom 入力は base 配列を参照している場合も内容を fingerprint し、変更された重み・行列から古い matching を返しません。
- `decoders/prior_perturbation.py` は shot/member/source 順の RNG、状態・shot cursor、symbolic probability plan を実装します。
  各 shot/member の元 X/Z DEM probability draw を3色・両段・全 logical hypotheses で共有します。
  既存の probability product の項順、stage-2 の stable sort＋reverse、column/source-map の並べ替えをそのまま再現します。
  毎 shot の DEM オブジェクト再作成・再分解を、検証済み symbolic topology と probability 評価で置き換えました。新しい重みの matching 構築は続けます。
- `decoders/concat_matching_decoder.py` は matching の共通利用、固定 detector/check mask、hard-output の不要 tensor 削減を実装します。
  候補/色/class の順序、argmin と tie、selection weights、original-DEM mapping/scoring、guide schedule、relifting、SWIM は維持します。
  M=1/alpha=0 は元の batch 演算を維持し、浮動小数点の dot 演算まで pristine 出力と一致させます。乱数は消費せず shot cursor のみ進みます。
- `decoders/color_correlated_decoding.py` は immutable plan の検証済み source alignment を使います。元 DEM への correction 再構成と共通 prior scoring は各候補で実行します。
- `color_code.py` は RNG の純粋な状態と cursor を save/load します。native matching/cache は保存せず、load 後に再構築します。
  旧保存形式で stream 状態がない場合は設定 seed から開始します。
- `README.md`、既存 `tests/test_prior_perturbation.py` を更新し、`tests/test_runtime_optimization.py` と pristine fixture/説明を追加しました。
  既存テストの変更は固定 ensemble 前提を廃止し、同じ初期 seed/位置を使った比較と per-shot の呼出し数へ合わせたものです。

固定・動的 graph の数は次のとおりです。確率の完全一致による hit がなければ、perturbed stage 2 は各 shot で6(M−1)個、original stage 2 は3(M−1)個の新しい graph が必要です。
初回のみ base 6個を追加します。M=12で72個が生涯の上限という意味ではありません。
LRU32個のほかに current-shot の最大6(M−1)個の参照がありますが、過去の全 shot は保持しません。
color-correlated guide は stage 1 の動的 graph のみを追加し、stage 2 は base 3個を共有します。既存 symbolic guide-prior cache の上限128も維持しています。

| モード | 固定 base graph | d=3 初回の構築数 | 次の同サイズ call の構築数 | shot/call |
|:---|---:|---:|---:|---:|
| ordinary | 6 | 6 | 0 | 3 |
| M1 | 6 | 6 | 0 | 3 |
| M12_perturbed_stage2 | 6 | 204 | 198 | 3 |
| M12_original_stage2 | 6 | 105 | 99 | 3 |
| M12_comparative | 6 | 204 | 198 | 3 |
| color_correlated | 6 | 66 | 60 | 24 |

上表は rounds=3、uniform p=.02、alpha=1、seed=19、detector seed=51。
M12比較では comparative でも構築数は増えません。通常/M1は warm 後0個、M12は66個/shot、original stage2は33個/shotです。
guide の repeat にも LRU eviction と新規/再出現 prior の構築が含まれます。直接の同一 prior 再利用 hit と cache 上限は独立テストでも確認しました。
大距離の M12 計測でも初回72個、steady66個/shot（10-shotでは660個）でした。

## hard-output の allocation と残る処理

full_output=False では全候補の original correction/native correction/stage-1 hypothesis の大きな診断 tensor、generation weights、candidate metadata を保持しません。
通常・perturbation は候補の logical bit と selection weight を保持します。
guide/relifting は schedule と再利用に必要な baseline 3 correction を保持し、relifting aliases は current-shot の結果を使います。
comparative selection と tie のための weight tensor、各候補の original-DEM reconstruction、共通 prior による scoring は残ります。
SWIM・candidate export・validity などのオプションが correction/hypothesis を必要とする場合は従来の tensor を保守的に保持します。

PyMatching の公開 `add_edge(replace)` は native MWPM 再構築を要求し、parallel-edge の winner/fault IDs と check-matrix tie を保つ安価な bulk reweight API は確認できませんでした。
そのため内部 native weight を直接書き換えず、新規 prior は `Matching.from_check_matrix` で構築します。
PyMatching・他の feature worktree・YAML・保存済み研究データは変更していません。新しい threading、kernel、環境更新はありません。
事前 audit と source review は [audit.md](audit.md) に記録しました。

## 検証

- decoder package: **231 passed, 2 skipped**（既存skip）、21.96秒。
- workspace package: **318 passed**、113.83秒。合計 **549 passed**。
- 独立 oracle は毎 shot、DEM/分解/Matching を再構築し、新しい plan/cache/stage decoder を使いません。
  両 weight basis、stage-2 prior 両設定、comparative off/on で hard/full 出力の全値が一致します。
- actual DEM 再分解との probability/check-matrix/source-map 完全一致を bit-flip、depolarizing、uniform circuit、non-edge-like removal 両設定、comparative、p>.5となる条件を含め確認しました。
- 同一 syndrome でも fresh draws、uneven chunk/empty/single shot、共有 class draws、strict tie、custom mutation/parallel-edge winner、bounded cache、save/load stream 継続、legacy load、predecode options、hard allocation を検証しました。
- pristine `072a87d` の770-array fixtureで、ordinary両basis、guide、relifting、M1、alpha0の全出力を comparative off/on で比較しました。
  fixture は記録時の NumPy/Stim/PyMatching version で実行し、それ以外では独立 oracle を使用します。
- 最終追加計測の M1 は全 timed pair の全 public fields が pristine と完全一致。
  最終 M12 の candidate digest も同仕様比較計測の対応する draw と完全一致しています。

Commands（workspaceから）:

```sh
PYTHONPATH=external_libs/color-code-stim/src /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest -q external_libs/color-code-stim/tests
PYTHONPATH=src:external_libs/color-code-stim/src /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest -q tests
```

## 計測条件と比較基準

CPU: Intel Core i7-13700H、WSL2/Linux、Python3.12.14、NumPy1.26.4、Stim1.16.0、PyMatching2.2.dev2。
PyMatching fork commit: `7a26e6a8ef20080e9eab7240ce33581cc3880d03`。
OMP/OPENBLAS/MKL thread環境変数は未設定の既存環境のままです。
`circuit_type=tri, temp_bdry_type=Z, cnot_schedule=tri_optimal`、uniform circuit p=.001、rounds=d、全 perfect flags=False。
perturbation alpha=1、seed=20260927、original_dem scoring、stage2 perturbed、comparative=False、SWIM/validity/export=False。
同じ回路・physical shotsを seed20260927 で作り、warmupは別seed20260928の1shot。
各版を順次実行し、steady順序を交互に入れ替えました。1shotを3回、10shotを1回、ordinary/M1は100shotも1回。
d17のM12はコストを抑えてsteady1shotを1回のみです。sampling/plan/new graph構築は全て decode wall time に含みます。

比較1は per-shot仕様だけを先に直した未最適化 snapshot と、同じ draw の最適化版です。
比較2は pristine固定ensemble版 `072a87d` と最終実装です。M12の比較2にはsampling仕様変更が含まれます。
最終 M1 を旧batch演算に戻す前の比較1の M1 rows は無効化し、summaryでは除外しました。
M12の動的経路はその修正で変わらず、最終追加計測との候補digest一致も確認しています。
比較1と比較2の測定時間帯は異なり、host状態による壁時計の変動があります。異なる時間帯の数値を混ぜて比率を計算していません。
以下は小標本の動作・runtime確認であり、asymptotic scalingやLER改善を示すものではありません。

## 同じ per-shot 仕様に対する最適化

steady、full_output=False、全 candidate digest/予測/RNG state が paired reference と一致しています。
| d | mode | batch | full_output | 比較元 ms/shot | 最適化後 ms/shot | 比較元/最適化後 |
|---:|:---|---:|:---:|---:|---:|---:|
| 9 | M12 | 10 | False | 18861.464 | 507.576 | 37.16× |
| 13 | M12 | 10 | False | 34801.326 | 539.860 | 64.46× |
| 17 | M12 | 1 | False | 78420.416 | 2098.921 | 37.36× |

d9/d13 の10-shot時の wall-time 削減は約97.3%/98.4%。
未最適化版では毎shotの DEM作成・再分解が約87〜97%を占めます。
通常 decoding の steady 10shot も以下のとおりです（こちらはsampling仕様変更なし）。
| d | mode | batch | full_output | 比較元 ms/shot | 最適化後 ms/shot | 比較元/最適化後 |
|---:|:---|---:|:---:|---:|---:|---:|
| 9 | ordinary | 10 | False | 4.929 | 0.718 | 6.86× |
| 13 | ordinary | 10 | False | 12.728 | 1.501 | 8.48× |
| 17 | ordinary | 10 | False | 10.640 | 1.283 | 8.29× |

## pristine 変更前との最終比較

実ワークフローは perturbation 等で full_output=True を要求するため、詳細出力付きでも計測しました。
M1はsampling変更の影響を受けず、10shotでは約6.3〜9.4倍、84〜89%短縮しました。
| d | mode | batch | full_output | 比較元 ms/shot | 最適化後 ms/shot | 比較元/最適化後 |
|---:|:---|---:|:---:|---:|---:|---:|
| 9 | M1 | 10 | True | 1.445 | 0.231 | 6.27× |
| 13 | M1 | 10 | True | 4.954 | 0.536 | 9.24× |
| 17 | M1 | 10 | True | 10.881 | 1.153 | 9.44× |

100shotでは以下です。
| d | mode | batch | full_output | 比較元 ms/shot | 最適化後 ms/shot | 比較元/最適化後 |
|---:|:---|---:|:---:|---:|---:|---:|
| 9 | M1 | 100 | True | 0.325 | 0.192 | 1.69× |
| 13 | M1 | 100 | True | 1.395 | 0.627 | 2.22× |
| 17 | M1 | 100 | True | 2.728 | 1.527 | 1.79× |

M12を旧固定ensembleと比較すると、10shotでは **d9で約6.0倍、d13で約7.1倍遅く** なります。
旧版はbatchの全shotで同じ72 graphを使用できますが、新版はshotごとに新しい66 graphを構築し、10shotで660 graphを構築します。
これは仕様の異なる旧版からの総runtime差であり、同仕様の最適化が退行したことを意味しません。
d17の1shot比較は約2%短縮ですが、1標本なので改善を確立したとは扱いません。
| d | mode | batch | full_output | 比較元 ms/shot | 最適化後 ms/shot | 比較元/最適化後 |
|---:|:---|---:|:---:|---:|---:|---:|
| 9 | M12 | 10 | True | 31.476 | 188.342 | 0.17× |
| 13 | M12 | 10 | True | 89.028 | 633.573 | 0.14× |
| 17 | M12 | 1 | True | 1621.377 | 1587.758 | 1.02× |

full_output=False、各1shot反復値、初回 decode、warm後のformat switch、構築数、全 wall times は [summary.csv](summary.csv) と raw CSV に保存しています。
first-use と initialization をsteadyから分けており、full_output=Trueの `warm_format_switch` はcold initializationではありません。

## 初期化と初回 decode

ColorCode/circuit/DEM managerとdecoder取得までの固定初期化（秒、sampling仕様変更を含む）：

| d | M | 旧版 initialization s | 最終 initialization s | 旧版 first decode ms | 最終 first decode ms |
|---:|---:|---:|---:|---:|---:|
| 9 | M1 | 0.901 | 0.983 | 21.9 | 21.4 |
| 9 | M12 | 0.820 | 0.974 | 9036.4 | 333.1 |
| 13 | M1 | 2.918 | 3.409 | 70.6 | 47.4 |
| 13 | M12 | 3.063 | 3.031 | 28168.7 | 1080.3 |
| 17 | M1 | 6.530 | 7.209 | 202.7 | 122.9 |
| 17 | M12 | 6.855 | 7.070 | 69728.1 | 2676.4 |

first decode は1shot/full_output=Falseで、旧M12の固定ensemble生成/分解も含みます。
新M12も初回plan/cache/native準備とそのshotのdrawを含み、未来のrandom priorsはwarmupでprecompileしません。

RSS は共有process（比較する2 decoderが同時に生存、allocatorに前のケースの領域も残る）の resident測定です。
比較1で最大4122.7 MiB、比較2で最大4133.3 MiBを観測しました。

各decoder単独のpeak memoryでも、memory削減率でもありません。full-output tensor保持とdynamic graphの領域は依然必要です。

## 残る bottleneck と成果物

最適化M12では新しいweighted graph構築とnative decode（内部初期構築を含む）、symbolic probability評価・stage2並べ替えが主なコストです。
比較1のd9/d13では graph API 約19〜21%、native decode 約37〜40%、sampling/plan 約11〜14%、candidate評価 約2〜3%でした。
多数の候補・original source correction・score計算、full-outputの保持も残ります。
動的重みをshot間で固定することなく、これ以上matching構築を大幅に減らすには別の検証済みnative/API改善が必要です。
本作業ではその範囲へ踏み込んでいません。

- [measurements.csv](measurements.csv): 比較1のraw96行（M1 rowsは上記理由でsummaryから除外）。
- [legacy_comparison.csv](legacy_comparison.csv): 比較2のraw120行。
- [summary.csv](summary.csv): 比較基準/phase/batch/output別の集約と比率。
- [initialization.csv](initialization.csv) / [legacy_initialization.csv](legacy_initialization.csv): 固定初期化。
- [environment.json](environment.json) / [legacy_environment.json](legacy_environment.json) / [system_environment.json](system_environment.json): 版、seed、時刻、計測programのSHA256、環境。
- [cache_observations.json](cache_observations.json): 最終実装のgraph数とcache上限。
- [source_manifest.json](source_manifest.json): base commits、最終変更ファイルと参照snapshotのSHA256。
- [tests_decoder.log](tests_decoder.log) / [tests_workspace.log](tests_workspace.log): 最終テスト結果。

計測用program（benchmark.py / legacy_comparison.py）と一時reference packageは実行後に削除済みです。
削除確認は [cleanup.json](cleanup.json) に記録しています。
commit/pushや大規模simulation campaignは実行していません。
