# Native stage-1 perturbation と Tesseract の復号時間比較

2026-09-29、現在の実装環境で新しく測定した結果。各距離で同じ物理20 shotsを3つのデコーダーに渡した。今回の平均復号時間は native M=8/M=16 の両方が Tesseract より短かった。

## 1 shot あたりの時間

単位は **ms/shot**。各行20 shots。min–max は標本内の最小・最大であり、信頼区間ではない。

| distance / rounds | decoder | mean | min–max | median |
| --- | --- | ---: | ---: | ---: |
| 9 / 9 | concatenated MWPM, native M=8 | 4.177 | 3.023–5.707 | 4.047 |
| 9 / 9 | concatenated MWPM, native M=16 | 7.387 | 5.318–10.549 | 7.032 |
| 9 / 9 | Tesseract | 17.948 | 5.108–67.967 | 10.816 |
| 13 / 13 | concatenated MWPM, native M=8 | 12.642 | 10.037–17.502 | 12.379 |
| 13 / 13 | concatenated MWPM, native M=16 | 23.932 | 18.248–40.861 | 21.842 |
| 13 / 13 | Tesseract | 559.282 | 43.194–2771.277 | 181.631 |

Tesseract mean / native mean は d=9 で M=8: **4.30倍**、M=16: **2.43倍**、d=13 で M=8: **44.24倍**、M=16: **23.37倍**。これは今回の設定・入力での平均時間比。d=13 の Tesseract は中央値181.631 ms、最大2771.277 msで、長い探索を要する shots が平均に影響している。20 shots から普遍的な速度比や尾部の分布、LER の優劣は結論しない。

## 条件

- uniform circuit-level noise: `NoiseModel.uniform_circuit_noise(0.003)`。
- d=9,13、rounds=d、triangular Z memory、`tri` / `tri_optimal`。完全初期化・完全最終測定等のオプションは既定の False。
- native: `stage1_perturbation=True`、M=8,16、alpha=1.0、perturbation seed=20260929、RNG scheme version=1。M は摂動しない member 0 を含む。
- 分解後の stage-1 edge probability に PyMatching 内部で `clip(p1*(1+alpha*Uniform(-1,1)),1e-14,1-1e-14)` を適用。shot/member/colour ごとに独立。stage 2 はキャッシュした元の prior、最終候補採点は `original_dem`。3 colours を使用し、comparative/SWIM/guide/relifting は無効。
- `remove_non_edge_like_errors=True`。両 native 設定の回路・元の X/Z DEM は一致。Tesseract にも同じ `dem_xz` をそのまま入力。
- Tesseract は前回の時間比較・`configs/main.yaml` と同じ設定: `pqlimit=1000000`, `det_beam=20`, `beam_climbing=True`, `no_revisit_dets=True`, `num_det_orders=21`, `det_order_method=Index`, `seed=2384753`, `sparsify_errors=False`。その他は現在のライブラリ既定値。
- 各距離で Stim seed=20260929 により20 shotsを一度だけサンプルし、全デコーダーで共有。別seed=20260930 の10 shotsでウォームアップ。native warmup の絶対shot IDは1000–1009、計測は0–19。

## 計測範囲

単一プロセスで1 shotずつ逐次実行し、`perf_counter_ns` で decode 呼び出し全体を測定。native は現在の compact API `ColorCode.decode(full_output=False, metrics=(), perturbation_shot_offset=i)` で予測を返し、Tesseract は `decoder.decode(bool_syndrome)` で予測を返す。候補生成・両matching段階・候補採点・最終選択・APIの出力生成を含む。診断用full outputとsoft-output metricの計算は含めない。最小の呼び出し関数のオーバーヘッドは双方に含む。内部処理の計測ラッパーは使用していない。

回路生成、DEM生成/分解、サンプリング、Tesseract compile、nativeの遅延初期化を含むウォームアップ、CSV書き込み、実際のobservableとの比較、検証は計測外。これは初回呼び出しのlatencyや20-shot一括処理のthroughputではなく、ウォームアップ済み1-shot呼び出し時間。デコーダーの順番は shot ごとに `M8,M16,Tesseract` → `M16,Tesseract,M8` → `Tesseract,M8,M16` と循環。CPU/周波数固定は行っていない。

## 初期化の参考値

単位は秒。native construction は ColorCode 構築、Tesseract construction は共有DEMからの compile。native first decode は遅延初期化を含む。warmup 列は first decode を含む10 shotsの合計である。

| d | decoder | construction | first decode | warmup 10 shots |
| --- | --- | ---: | ---: | ---: |
| 9 | native M=8 | 0.050207 | 0.037209 | 0.070325 |
| 9 | native M=16 | 0.049149 | 0.036229 | 0.092817 |
| 9 | Tesseract | 0.022162 | 0.006636 | 0.135416 |
| 13 | native M=8 | 0.108676 | 0.111432 | 0.219798 |
| 13 | native M=16 | 0.111431 | 0.120100 | 0.332492 |
| 13 | Tesseract | 0.080585 | 0.037636 | 5.357109 |

## 検証と保存物

- 全120個の時間は有限・正、各条件のshot IDは0–19、同一shotのactual observableとdetector event数・測定順を確認。
- 各nativeの測定済み20個の1-shot予測は、同じ seed・絶対shot IDで再実行した `full_output=True` の20-shot診断出力と完全一致。
- 実際の ensemble は `NativeStage1Ensemble`、native matcherは各colourに1個、`enable_prior_perturbation` / `use_original_prior_for_stage2` は True と確認。
- CSVのmean/min/max/medianを個別時間から独立に再計算して一致。
- [per_shot.csv](per_shot.csv): 全120個の個別時間。予測・actual・failureは入力/出力検証用で、LER比較の報告ではない。
- [summary.csv](summary.csv)、[initialization.csv](initialization.csv)、[verification.json](verification.json)。
- [inputs.npz](inputs.npz): 共通detector/observable配列のみ。実行プログラムではない。
- [environment.json](environment.json): 正確な設定、実行時刻、入力/回路/DEM/binary/program SHA256、依存版、commitとbranch。
- 計測プログラムは実行後に削除。[cleanup.json](cleanup.json) に確認結果を保存。decoder実装、既存YAML、既存データは変更していない。

## 実行環境

Intel Core i7-13700H、WSL2 Linux、Python 3.12.14 (`color_code_so`)、NumPy 1.26.4、Stim 1.16.0、PyMatching 2.2.dev2、Tesseract 0.1.1.dev20260910235247。スレッド数の環境変数は未指定。

- root: `2f70d4ef58794688dfbfdbd31cdc1b89b9cc0c7b`
- color-code-stim: `3955196a9d2280fab555f0cf97510e37b6dd9d23`
- PyMatching: `40ef9296f1d73aa4d629460bdc80bcf57bb1f7b5`
- 3 checkout のbranch: `codex/native-stage1-perturbation-20260929`。

測定前からあるユーザーの notebook 編集は保持。外部2 checkout は測定前後ともclean。過去の p=.001 / M=12 / full-output / 異なるcandidate law の時間とは混合していない。
