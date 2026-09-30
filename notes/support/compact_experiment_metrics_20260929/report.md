# Requested scalar experiment output — 2026-09-29

実装した通常のYAML workerは、`full_output=False`のまま保存schemaから必要な
指標を要求し、decoderから各指標につき`(N,)`の配列を受け取る。
既存の`full_output=True`は明示的な診断・比較用に保持した。
同じ入力shotに対する予測・全保存指標・dtype・shot順序・Parquet schemaと値は一致する。

**メモリ確保は削減できたが、全条件での高速化は達成していない。**
native M12の10-shot batchでは、decode中のtracemallocピークを約79.5%削減した。
一方、総decode時間はd9/d13で34.4%/15.7%増加し、d17で2.8%短縮した。
comparativeを含むnativeではピーク約83.1%減、時間0.7–5.5%減だった。
メモリ削減率はプロセス全体のRSS削減率とは異なる。下の表に両方を記録する。

## 出力と実装

- decoder API: `ColorCode.decode(metrics=(...), actual_observables=..., full_output=False)`。
  戻り値は`(prediction, requested_metrics)`。指定していない指標や候補診断は返さない。
- schemaを決める`simulation.task.metric_names`をworkerと保存処理で共有する。
  simulationの指標名・意味・dtype・ファイル名は変更しない。
- logical error、paired baseline error、strict better weight、effect、run category、
  comparative logical gap、SWIMをdecoder内で集約する。`weights`もAPIで指定可能だが、
  simulationが保存しない場合は返さない。
- 最終補正と、必要な場合のbaseline補正を保持する。全候補の補正・native stage-2
  診断・stage-1診断の保持と出力を省く。各候補のmatchingとoriginal-priorでの
  scoring、候補順序、同点処理、member 0、shotごとの乱数は維持する。
- circuit SWIMは既存geometry backendをcallbackとして使用する。候補補正の
  observable parity別の最小値を保持し、最終予測と同じparityの値を返す。
  nativeでは既存stage-1 batchのviewを採点し、reliftingのaliasは同じstage-2
  syndromeの採点結果を再利用する。途中からSWIMを要求するcache再利用にも対応する。
- actual observablesは失敗指標の計算にだけ使用し、matchingや候補選択には渡さない。
  不正なshape・要求・offsetと、保存用指標の非有限値を明示的に拒否する。

保存ファイルとworker間の転送データは以前からshotごとの小さな指標だった。
今回減らしたのは、その指標を得るまでdecoder内で保持・返却していた診断データである。
補正配列の列はDEMのエラー機構／check matrix列の選択bitであり、グラフの全辺の
属性を保存していたという意味ではない。guide/relift用のordinary補正、nativeの
stage-1 batch、matching作業領域は引き続き必要で、decoder全体のメモリが
`N×指標数`になるわけではない。

既存のper-color研究用sampling APIと詳細candidate auditは、それぞれが明示的に
要求する診断APIを保持する。既存結果・main.yaml・PyMatching実装は変更していない。
APIの詳細: [decoder guide](../../../external_libs/color-code-stim/docs/experiment_metrics.md)。

## 妥当性検証

変更前: decoder **252 passed / 2 existing skips**、root **325 passed**。
最終版: decoder **308 passed / 2 existing skips**、root **361 passed**。

実行環境は`color_code_so`。コマンド:

```text
python -m pytest tests -q  # root: 361 passed
python -m pytest tests -q  # external_libs/color-code-stim: 308 passed, 2 skipped
```

新規検証は通常・color-correlated・relifting・original-DEM摂動・native摂動を対象とする。
ordinary/ensemble、comparative、data-only/circuit SWIMを比較し、同じshot・seedで
全指標を`assert_array_equal`で検証した。保存後も全Parquet列のschemaと値を比較した。
zero syndromeの同点、M=1、alpha=0、分割batch、absolute offset、空batchとcursor、
異常後の復帰、actual outcomeを変えても予測が変わらないことを確認した。
指定されたd3/superdense_default設定のcomparative False/Trueも一致した。
全候補補正テンソルを作らないことと、warm nativeでmatching factoryを呼ばないことを
検証した。既存のworker 1/2・cache再作成・保存復元の回帰も成功した。

新規検証の場所:

- `external_libs/color-code-stim/tests/test_experiment_metrics.py`
- `tests/test_compact_workflow_metrics.py`
- `tests/test_native_stage1_workflow.py`

## 計測条件と解釈

旧側はdecoder commit `6a6bd8b30b3de62c0a4132fcf440bde48c3e3f3a`のsrcを一時展開した
**変更前のソース**を使用した。新側は今回のsource hashで識別する実装である。
PyMatchingは両側とも`40ef9296f1d73aa4d629460bdc80bcf57bb1f7b5`。
rootの基点は`ad0d1c93da074f10305d553157a788b0931b6388`。
候補生成の方式・prior・seed・perturbation法則は両側で同じであり、旧固定ensembleや
original-DEM摂動との方式差を含む比較ではない。

- d=9/13/17、rounds=d、uniform circuit noise p=.001、tri_optimal、Z memory。
- ordinary、color-correlated (b=2)、native M=12 (alpha=1、seed=321)。
- batch N=10。nativeではN=1も計測。comparativeとd9 circuit SWIMも記録。
- Stim seed=83219。同じcaseの旧／新input hashは一致する。
- setupと最初のdecodeを別記録。warm後に3反復。
  nativeのabsolute offsetは`1000 + repetition*N`。
- 反復ごとに保存指標と予測のchecksumを比較し、16条件すべてで一致した。
  memory計測offset=2000のchecksumも一致した。
- **総decode時間**は、configured decode・必要なordinary baseline decode・全要求指標の
  計算を含む。samplingとディスクI/Oは含まない。旧SWIM採点はdecode後、新SWIM採点は
  decode内部なので、比較には総時間を使う。
- `decoder_ms`と`baseline_ms`はCSVに別記録。cold setup/first decodeは`setup.csv`。
- memory計測は時間計測とは別に行った。tracemallocのdecode中ピーク、返却NumPy
  buffer量、プロセスpeak RSSを記録した。tracemallocはnative arena全体を捉えない。
  RSSはimport・構築・warmupも含むので、decode単体の値ではない。
- i7-13700H / WSL2 Linux。BLAS/OMP/MKLは1 thread。環境・ソースhashは`environment.json`。

時間は3反復のwall time平均で、比率`旧/新 > 1`が高速化、`< 1`が低速化である。
反復ごとの範囲もCSVに残した。短時間条件には変動があり、小さな差を一般化しない。
コピー・winner更新・matchingの費用を個別に分離計測していないため、どれが
時間差の主因かという結論は出さない。メモリ削減から速度改善を推定しない。

## 計測結果

以下は総decodeのms/shotとdecode中のtracemallocピーク。全条件を掲載する。

| mode | soft output | d | N | 旧 ms/shot | 新 ms/shot | 旧/新 | 旧 peak MiB | 新 peak MiB | peak削減 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ordinary | none | 9 | 10 | 0.475 | 0.426 | 1.115 | 0.578 | 0.504 | 12.8% |
| correlated | none | 9 | 10 | 1.076 | 0.874 | 1.231 | 0.997 | 0.659 | 33.9% |
| native | none | 9 | 1 | 10.272 | 6.220 | 1.651 | 0.451 | 0.126 | 72.1% |
| native | none | 9 | 10 | 3.882 | 5.217 | 0.744 | 4.007 | 0.818 | 79.6% |
| native | comparative | 9 | 10 | 14.259 | 13.478 | 1.058 | 7.742 | 1.305 | 83.1% |
| ordinary | none | 13 | 10 | 1.147 | 1.179 | 0.973 | 1.861 | 1.618 | 13.0% |
| correlated | none | 13 | 10 | 3.226 | 2.766 | 1.166 | 3.690 | 2.111 | 42.8% |
| native | none | 13 | 1 | 22.077 | 16.572 | 1.332 | 1.406 | 0.375 | 73.3% |
| native | none | 13 | 10 | 11.238 | 12.997 | 0.865 | 12.919 | 2.649 | 79.5% |
| native | comparative | 13 | 10 | 46.307 | 43.761 | 1.058 | 24.956 | 4.212 | 83.1% |
| ordinary | none | 17 | 10 | 2.008 | 2.453 | 0.819 | 4.310 | 3.746 | 13.1% |
| correlated | none | 17 | 10 | 76.714 | 80.733 | 0.950 | 11.698 | 6.062 | 48.2% |
| native | none | 17 | 1 | 24.480 | 26.297 | 0.931 | 3.233 | 0.855 | 73.5% |
| native | none | 17 | 10 | 24.737 | 24.042 | 1.029 | 29.931 | 6.144 | 79.5% |
| native | comparative | 17 | 10 | 116.088 | 115.301 | 1.007 | 57.810 | 9.757 | 83.1% |
| native | swim | 9 | 10 | 349.782 | 382.264 | 0.915 | 6.667 | 1.977 | 70.3% |

## RSSと返却buffer量

RSSはプロセス全体のピークである。返却bufferはpredictionも含み、NumPyのbase配列を重複計上しない。旧側にはdecoder診断と抽出した指標、新側にはpredictionと要求指標が含まれる。

| mode / soft | d | N | 旧 peak RSS MiB | 新 peak RSS MiB | 旧返却 bytes | 新返却 bytes |
|---|---:|---:|---:|---:|---:|---:|
| ordinary / none | 9 | 10 | 259.47 | 259.90 | 39630 | 20 |
| correlated / none | 9 | 10 | 300.64 | 298.89 | 160080 | 60 |
| native / none | 9 | 1 | 261.52 | 260.89 | 346316 | 5 |
| native / none | 9 | 10 | 263.82 | 261.16 | 3463160 | 50 |
| native / comparative | 9 | 10 | 268.47 | 262.34 | 6896562 | 130 |
| ordinary / none | 13 | 10 | 351.21 | 350.48 | 127990 | 20 |
| correlated / none | 13 | 10 | 536.97 | 531.05 | 1663810 | 60 |
| native / none | 13 | 1 | 356.02 | 354.80 | 1121424 | 5 |
| native / none | 13 | 10 | 367.20 | 357.86 | 11214240 | 50 |
| native / comparative | 13 | 10 | 380.27 | 360.65 | 22314202 | 130 |
| ordinary / none | 17 | 10 | 525.48 | 524.79 | 296670 | 20 |
| correlated / none | 17 | 10 | 1026.37 | 1016.03 | 3856650 | 60 |
| native / none | 17 | 1 | 536.51 | 534.64 | 2601044 | 5 |
| native / none | 17 | 10 | 564.18 | 541.88 | 26010440 | 50 |
| native / comparative | 17 | 10 | 593.38 | 547.72 | 51741762 | 130 |
| native / swim | 9 | 10 | 291.05 | 286.00 | 3463240 | 130 |

## 記録

- [全反復時間](timings.csv)、[cold/first decode](setup.csv)、[memory](memory.csv)
- [比較表](summary.csv)、[input/output checksumと全測定値](measurements.json)
- [環境・基点commit・計測source/program hash](environment.json)
- [公開branchと依存commit](dependencies.json)。decoderの公開commitは
  `3955196a9d2280fab555f0cf97510e37b6dd9d23`、PyMatchingは上記の既存commitを使用する。
  rootの公開commitはこのレポートを含むcommitで識別する。

計測専用プログラムと旧srcの一時展開・中間計測ファイルは実行後に削除した。既存resultsと保存形式は変更していない。
