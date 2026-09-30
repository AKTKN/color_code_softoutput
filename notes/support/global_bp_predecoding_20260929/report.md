# Global DEM BP predecoding implementation — 2026-09-29

実装場所は `/home/quantum_teresheys/workspace/color_code_softoutput_bp_global`。
root、color-code-stim、PyMatching の独立した worktree を、同じ
`codex/global-bp-predecoding-20260929` branch に作成した。
元の workspace の branch と未コミット変更は保持している。

| Repository | Base commit |
| --- | --- |
| color_code_softoutput | `2f70d4ef58794688dfbfdbd31cdc1b89b9cc0c7b` |
| color-code-stim | `3955196a9d2280fab555f0cf97510e37b6dd9d23` |
| PyMatching | `40ef9296f1d73aa4d629460bdc80bcf57bb1f7b5` |

## 実装した処理

API は `code.decode(..., bp_predecoding=True, bp_prms={...})`。
`decode_bp` も global DEM の機構空間を使う。optional dependency
`[bp]` を両 Python package に追加した。

1. 元の circuit から未分解の global DEM を作る。X/Z DEM と色分解は遅延生成する。
2. global DEM の H と元の機構確率で BP を実行する。comparative の論理仮説 detector 行は検査から外すが、機構列と observable 行列は保持する。
3. BP が収束した shot は `observable_global @ correction_global mod 2` を返す。収束判定と syndrome の一致を検証し、X/Z分解・MWPMを実行しない。
4. 非収束 shot は `q[e] = min(expit(-LLR[e]), 0.5)` を global 機構の新しい prior とする。
5. global 機構を detector の Pauli metadata で X/Z に射影する。同じ detector と observable の集合に射影された機構は、`(1-product(1-2*q[e]))/2` で XOR 縮約する。微小確率の桁落ちは `log1p`/`expm1` で避ける。
6. 縮約後の matching 確率に従来と同じ有限重み用の下限 `1e-14` を設け、上限 0.5 と正確な log odds を使う。p=0.5 の重みは 0。
7. この shot の posterior X/Z DEM を色分解して通常の concatenated decoder に渡す。stage 2 の列と元機構への対応行列を同時に生成する。共有の元 DEM/caches は変更しない。

L0 等の logical labels は `temp_bdry_type=X` なら X detector sector、Z なら Z detector sector へ入れる。
Y memory と cultivation postselection は BP 開始前に明示的な error にする。
global と射影後 X/Z の機構番号・observable 行列は混同しない。

縮約は BP の各機構確率を独立 prior とみなした surrogate の各 sector の周辺分布を保存する。
BP の joint posterior や X/Z 相関をそのまま保存する主張ではない。
参照した `BeliefMatching/src/beliefmatching/belief_matching.py` の早期終了と posterior 利用の流れを採用し、縮約・重みはユーザー指定の XOR 確率と log odds とした。

## 戦略、perturbation、再現性

ordinary / comparative / color-correlated / relifting / original-DEM perturbation / native stage-1 perturbation を接続した。
比較の basis と候補順、同率の選択規則は既存 decoder に委譲する。BP 有効時の base prior は、その shot の posterior DEM。
color-correlated の普通の baseline も同じ posterior DEM で計算する。
SWIM scorer はこの shot の posterior DEM に付け替え、同じ hard logical class の選択規則を保持する。

従来の native PyMatching は、可能な perturbation が負重みになる場合を reject しており、常に 0.5 に clipping していたわけではなかった。
明示的 option `clip_perturbed_probabilities=True` を追加し、BP 有効時だけ使用する。
perturbation 後の確率を `[1e-14, 0.5]` に clip し、その確率から log odds を計算する。
member 0、乱数の draw 順、native topology の制約は保持する。BP 無効時の reject 規則は従来のまま。
BP の power-guide と original-DEM perturbation も確率の上限を 0.5 にする。

追加 API `bp_shot_offset` は physical shot の絶対位置を指定できる。
BP 収束で skip した位置を詰めない。native の絶対 shot/color seed は従来と同じで、clip law の state は scheme version 2。
BP original-DEM perturbation は `SeedSequence([resolved_uint64_seed, absolute_shot])` を使う新しい law。
各 shot 内の draw は色・論理仮説で共有し、global-BP version 2 として save/load に保存する。
YAML runner は entropy seed も spawn 前に解決し、設定・実行ログに保存する。
BP 無効時の NumPy sampling law は変更していない。

## 出力と解析

`bp_converged.parquet` は `shot_index:int64, bp_converged:bool`。
既存の各 concatenated metric の dtype、shot 順、ファイル名を保持し、BP 収束した shot だけ値を null にする。
`logical_error` もこの規則に含む。predictions API は全 shot の予測を返す。
Python metrics は `np.ma.MaskedArray`、full output の `concat_outputs[i]` は非収束 shot の diagnostic dictionary / 収束 shot の `None`。
diagnostic correction は射影後 X/Z 機構空間であり、BP correction は global 空間。

Parquet 書込・finalize・読込で null mask と BP flag の一致を検証する。
解析の LER / confidence interval / soft-output は非収束 shot のみを分母にする。
summary は `physical_shots`, `bp_converged_shots`, `statistics_scope="BP-nonconverged shots"` を明示する。
全 shot が収束した場合、concatenated LER と confidence interval は NaN。null を成功扱いにしない。
保存形式から全体の BP+MWPM LER は計算できない。既存 BP 無効の schema/解析は保持する。

## 妥当性の検証

- toy global DEM の全機構パターンと射影 DEM の全パターンを独立に列挙し、各 sector と logical の分布を比較した。
- 衝突確率 0.1/0.2 は 0.26、0.2/0.3 は 0.38。0、0.5、1、極小確率も検証した。
- posterior を元の prior とした射影と、既存 circuit noise 分離後 DEM の機構集合・確率が、X/Z memory、regular/superdense の d3/T3 で一致した。
- posterior 列順を意図的に反転し、symbolic `DecompositionPlan` の H・確率・補正対応行列を fresh decomposition と比較した。実際に stage-2 order が変化することも確認した。
- 6 種の strategy の fallback を、同じ posterior DEM で直接実行した decoder と比較した。返却 correction の physical syndrome と observable を独立に再計算した。
- real BP の収束 syndrome、収束/非収束混合、zero noise、空 batch、save/load、split batches、skip を含む絶対 shot ID を確認した。
- X/Z noise separation と color decomposition を禁止したテストでも、BP 収束時の decoder と worker が成功した。
- PyMatching の clip law は独立 Python MT19937-64 reference と fresh Matching の全候補に比較し、C++ 側でも非負重みと member 0 を検証した。
- YAML full/compact mode を同じ shot で比較し、15 strategy/soft-output 組合せの全 metric と Parquet null mask を確認した。
- serial/spawn 実行、JSON/YAML roundtrip、全 shot 収束時の undefined 統計、nullable 読込と不整合 null の reject を確認した。
- 元 workspace から未変更で複製した BP 無効時の凍結 fixture を使用し、従来結果との一致を確認した。既存 incompatible-mode tests の BP 制限だけを新機能の test に置換し、その他の制限を保持した。

d5/T5 でも 4 条件 × 8 shot の bounded check を行った。全非収束 shot の physical syndrome と observable が一致した。

| 条件 | BP 収束 | fallback |
| --- | ---: | ---: |
| Z memory / regular / ordinary | 3 | 5 |
| X memory / superdense / ordinary | 1 | 7 |
| Z memory / superdense / comparative | 1 | 7 |
| Z memory / regular / native M3 alpha1 | 3 | 5 |

実行ログも native の実際の clip law を記録する。BP native は scheme 2、通常 native は scheme 1。
混在する run は `scheme_version="mixed"` と `scheme_version_by_point` を保存する。
BP 有無が異なる native decoder を同じ YAML run で実行し、保存された point ごとの version を検証した。
凍結 fixture の元/複製 SHA256 は共に
`aed4e9f0971e0ccff2b451a8e1911c7d235b2695e104983e5d87b6067422adf6`。

最終全体回帰テスト:

| Suite | Result |
| --- | --- |
| root package | **386 passed** |
| color-code-stim | **336 passed, 2 existing skips** |
| PyMatching Python | **131 passed** |
| PyMatching C++ | **100 passed** |

root の最終 full run は 229.68 秒。decoder の full run は 33.60 秒。
decoder の既存 skip は rectangular stability comparative の 2 件。
3 repository の `git diff --check` と Conda environment の `pip check` が成功した。
source hashes / environment / dependency commits は [acceptance.json](acceptance.json)。

外部 repository の実装 commit:

- color-code-stim: `65ef2ad7514a3d67f5f286ef02a3abd5824cad97`
- PyMatching: `0f143d6f9bb2683de5e8872fd6586f56065d0d22`

root と両 dependency はローカル branch に commit し、merge/push は実行していない。
新しい大規模 sampling campaign、性能/LER 改善の評価は行っていない。
非収束 shot ごとに matching graph を再準備する初期実装であり、性能改善を主張しない。

## 環境と実行

`color_code_so` に不足していた ldpc 2.4.1 と依存の tqdm 4.70.1 を追加した。
NumPy/SciPy/Stim/PyMatching の既存環境は upgrade していない。
`python -m pip check`: `No broken requirements found.`

検証時: Python 3.12.14, numpy 1.26.4, scipy 1.17.1, stim 1.16.0,
ldpc 2.4.1, pymatching metadata 2.2.dev2, pyarrow 25.0.1, pytest 9.1.1。
import paths は新 worktree の root/decoder/backend `src` を指すことを確認した。
PyMatching extension は新 worktree 内で build し、元の editable installation は切り替えていない。
独立 feature modules の既存 root tests に必要な ignored fixture / reference src は、元 workspace から変更せず複製した。

```bash
cd /home/quantum_teresheys/workspace/color_code_softoutput_bp_global
conda activate color_code_so
export PYTHONPATH="$PWD/src:$PWD/external_libs/color-code-stim/src:$PWD/external_libs/PyMatching/src"
python -m pytest -q
./scripts/run_experiment.sh configs/global_bp_example.yaml
```

PyMatching build (cwd: `external_libs/PyMatching`):

```bash
git submodule update --init --recursive
env -u DEBUG CMAKE_ARGS="-DPython_EXECUTABLE=/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python" \
  CMAKE_BUILD_PARALLEL_LEVEL=4 /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python setup.py build_ext --inplace
```

補足 API は decoder の `docs/global_bp_predecoding.md`、native clip は
PyMatching の `docs/native_perturbation.md` に記載した。

テスト command の cwd/PYTHONPATH:

```text
root:
  PYTHONPATH=src:external_libs/color-code-stim/src:external_libs/PyMatching/src python -m pytest -q
color-code-stim:
  PYTHONPATH=src:../PyMatching/src python -m pytest -q
PyMatching:
  PYTHONPATH=src python -m pytest -q
  python_build_stim/temp.linux-x86_64-cpython-312/pymatching._cpp_pymatching/pymatching_tests --gtest_brief=1
```
