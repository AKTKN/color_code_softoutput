# BP predecoding audit — 2026-09-29

## 結論

今回の悪化を実装レベルで再現した。明確な **全体LERの保存欠落** があり、
また **BP設定だけで結果が大きく変わる反例** がある。一方、global DEM の列順、
observable 対応、収束判定、fresh 色分解の接続に、今回の条件で誤った補正を
生成する配線バグは見つからなかった。後者は検査した範囲の結論であり、
全条件でバグがないという保証ではない。

本家との相違を「細かい違い」として無視できない。しかし0.5 clippingだけを
悪化の原因と断定することもできない。d5二重エラーの検査では、clippingを
外すだけでは13失敗から15失敗へ悪化した。

実装・設定・ノートブック・既存実験データは変更していない。今回追加したのは
この監査記録、列挙検証プログラムと小さな結果ファイルのみ。新しい乱数sampling、
大規模campaign、commit/pushは行っていない。

## 1. 対象の同定

対象run: `results/bpmatching/26_09_29_20_26_20_449d8157`。
元workspaceのdecoderは旧BP実装であり、このrunを実行した実装ではない。
対象実装は `/home/quantum_teresheys/workspace/color_code_softoutput_bp_global`。

- root: `666ade3e422a21eb019dbd9a2e9904daf8763f2e`
- color-code-stim: `65ef2ad7514a3d67f5f286ef02a3abd5824cad97`
- PyMatching: `0f143d6f9bb2683de5e8872fd6586f56065d0d22`
- run metadata: global BP version 2, cap 0.5, ldpc 2.4.1
- BP: `min_sum`, `parallel`, `max_iter=20`; scaling指定なし（ldpc 2.4.1の既定1.0）
- d=5/7/9, p=.03/.04/.05, depol, rounds=1, Z memory, original_dem scoring

実行時ソースhashはrun_logに含まれないため、保存メタデータと整合する現存
worktreeの監査である。実行当日の全ソースの同一性をhashで遡及証明はできない。
今回使ったソースhash・環境は `verification.json` に記録した。

## 2. 本家との相違

一次資料:
[Higgott et al., PRX 13, 031007, Appendix C](https://arxiv.org/html/2203.04948#A3)
および [公式BeliefMatching実装](https://github.com/oscarhiggott/BeliefMatching/blob/main/src/beliefmatching/belief_matching.py)。
2026-09-29に閲覧。

| 項目 | 公式実装／論文 | 今回 |
|---|---|---|
| 収束時 | BP補正からobservableを返す | 同じ |
| 公式APIのBP既定値 | product_sum、20反復 | YAMLでmin_sum、20反復を指定 |
| posteriorから辺確率 | 分解元のposteriorを加算、上限ほぼ1 | globalで上限.5、その後XOR縮約・色分解 |
| matching重み | -log(p) | log((1-p)/p) |
| matching構造 | surface-code matching graph | 2段階concatenated graph、3色候補選択 |

論文脚注ではXOR集約も代案として挙げる。log oddsも代案だが、その場合は
**負重みを扱う**。posteriorを.5で切ることとは異なる。
公式の既定BP methodとの比較であり、原論文の全実験が同一BP設定という主張ではない。

ソース位置（上記worktreeの `external_libs/color-code-stim/src/color_code_stim/` 配下）:

- `decoders/belief_concat_matching_decoder.py:148`: global cap
- `dem_utils/dem_manager.py:384`: posterior view、射影後もcap
- `dem_utils/global_dem.py:57`: XOR集約
- `decoders/matching_cache.py:76`: log oddsによるmatching graph構築
- `decoders/color_correlated_decoding.py:139`: original_dem候補スコア

例えばposterior .6 と .99 は現在どちらも .5、log odds 0になる。
本家の -log(p) は両者を区別する。これは数値安定化だけの処理ではなく、
目的関数を変更する設計選択である。以前の実装報告ではユーザー指定の規則と
記録されており、今回「仕様違反のcoding bug」とは判定していない。

## 3. 再現できた低重みの問題

global DEM列を1本／2本ずつ反転し、syndromeと実際のobservableを独立に
生成した。BP側は通常の公開APIを使用し `check_validity=True`。
乱数を使用せず、観測値は採点にのみ使用した。

| d | 単一機構数 | 単一失敗 通常/BP | 二重機構数 | 通常失敗 | min_sum BP失敗 | product_sum BP失敗 |
|---|---:|---:|---:|---:|---:|---:|
| 5 | 19 | 0/0 | 171 | 0 | **13** | **0** |
| 7 | 37 | 0/0 | 666 | 0 | 0 | 0 |
| 9 | 61 | 0/0 | 1830 | 0 | 0 | 0 |

d5の13失敗は全てBP非収束fallbackにある。BP methodだけをproduct_sumに変更すると
全て修正される。これは現行min_sum＋fallbackが二重エラーの一部を誤復号する
具体的反例であって、BP一般の不可能性やproduct_sumの全距離保証ではない。

最小再現例: d5,p=.03、global機構列0と13（0始まり）。
syndromeの非zero detectorは0,2,7、actual observableはFalse。
通常はFalse、min_sum BPはTrueを返す。LLRは `pairs.json` に保存した。
syndromeは一致したまま論理クラスを誤るため、syndrome妥当性testだけでは検出できない。

d5二重エラーに対する切分け（in-memory検証専用、production変更なし）:

- 現行: 13/171失敗
- 両capを外し、確率を[1e-14,1-1e-14]とし、log oddsを維持: 15/171失敗
- 非収束時に元priorの通常decoderを使う: 0/171失敗
- product_sumだけに変更: 0/171失敗

したがって「capを外せば直る」とは言えない。非収束時のposteriorを含む
BP method／fallbackの組合せの影響が実測で確認された。

## 4. d5の全列挙による全体LER

19機構の全2^19=524,288パターンを列挙し、512種類のsyndromeごとに
observableとエラー重みの個数を集計した。各機構の確率は2p/3。
各decoderを全512syndromeで実行し、全パターンの失敗確率を加算した。
これはMonte Carlo推定ではなく、このDEMに対する全列挙値（浮動小数演算）。
独立なGray-code XOR列挙でも全count tensorが一致した。

| physical p | 通常concat | 現行min_sum BP | product_sum BP | 最大尤度論理クラスの下限 |
|---|---:|---:|---:|---:|
| .03 | .0019904105 | **.0062123695** | .0022396056 | .0019853921 |
| .05 | .0083527886 | **.0183714756** | .0089519373 | .0083358868 |

現在のBPは通常の約3.12倍／2.20倍。product_sumに変えると通常にかなり近づくが、
通常より良くはならない。このd5設定では通常decoder自体が論理MLに非常に近い。
この有限条件の評価を他の距離・rounds・noiseへ一般化しない。

## 5. 保存されたlogical_errorは全体LERではない

`belief_concat_matching_decoder.py:137–148` は全metricをmask状態で初期化し、
非収束shotについてのみ埋める。収束時に返すpredictionはあるが、
`simulation/worker.py:192` はpredictionを捨て、masked logical_errorを保存する。
これは従来指定されたnullable concatenated-metric schemaに沿うが、
**全体のBP+MWPM性能評価には必要な失敗ラベルが欠落している**。

BPの「収束」はsyndromeを満たす意味であり、論理成功を保証しない。
全shot分母を維持したまま言うと、保存True数/全shot数は非収束側の失敗寄与であり、
全体LERの下限。収束側の失敗寄与を加える必要がある。
今回、ユーザー指定の分母や既存analysis実装は変更していない。

全列挙で確認した例:

| p / method | 保存可能な非収束失敗寄与 | 欠落する収束失敗寄与 | 全体LER |
|---|---:|---:|---:|
| .03 / min_sum | .0058644318 | .0003479377 | .0062123695 |
| .03 / product_sum | .0010893693 | .0011502364 | .0022396056 |
| .05 / min_sum | .0169781753 | .0013933003 | .0183714756 |
| .05 / product_sum | .0046457743 | .0043061630 | .0089519373 |

特にproduct_sumではnull側の失敗を落とすと見かけの改善を過大評価する。
この欠落はBPの悪化を作る方向ではなく、BPを実際より良く見せる方向。
保存nullをFalseに置換しても回復しない。全体失敗を別metricとして保存するか、
全体logical_errorをpredictionから計算することが必要。

36pointの直接Parquet集計は `saved_counts.json`。
BP_MWPM/通常MWPMのd5,p=.03は54/29失敗、d7,p=.03は18/5、d9,p=.05は48/21。
各分母は10000。ただしBP側に上記欠落がある。
plain同士で一様に10倍の差ではない。perturbationのd7,p=.03では23/2という
比もあるが、分母側が2失敗と少なく、別aliasの物理shotも独立なので、
これだけで10倍という性能比を確定できない。

## 6. このcode-capacity回路にBPが見ている情報

d5/7/9全てについて、global DEMのH、observable行列、priorは既存CSS DEMと一致した。
active detectorはZ sectorだけ、各射影groupはsingleton。
この設定ではglobal BPへ変更しても追加のX/Z相関syndromeは入っていない。
d5は18detector行のうち9行が非zero、19機構の全priorは.02（p=.03）。

これはglobal BPが誤ってX/Zを捨てた結果ではなく、元のone-round Z-memory回路の
Stim DEMに既にそう現れる。`circuit_builder.py:415` ではdepolarizationを
syndrome抽出の前に入れる。任意の既知論理状態についてX/Z両syndromeを利用する
code-capacity復号実験と同一であるとはみなせない。

この観察から、今回のrunを本家の相関利用の評価と直接対応づけることはできない。
コード族の差を論じる前に、比較対象の利用可能syndromeを揃える必要がある。
ただし、この監査は回路の仕様変更を提案実装するものではない。

## 7. 検証と次の優先順位

既存global BP/projectionの28testが通過した。既存testは接続・確率縮約・
syndrome整合性を検査するが、今回見つけた低重みの論理失敗を禁止していない。
全列挙countは別アルゴリズムで照合し、重み別総数は二項係数に一致した。
実装の配線妥当性と復号性能は別の検証項目である。

次に行うべき順序:

1. 全shotのpredictionから全体logical_errorを記録する。nullのconcat診断とは区別する。
2. 同じsyndromeでproduct_sumと現在設定を比較する。今回のd5は既に全列挙済み。
3. 本家に近い -log(p)／加算集約と、現行cap／XOR／log oddsを別optionで切り分ける。
   concatenatedのstage1、stage2、最終候補評価のどこを変えるかも明示する。
4. X/Z両syndromeを使う実験を意図するなら回路定義を先に検証する。

既存結果は変更せず、物理的説明や改善保証はこの段階では置かない。

## 再現

workspace rootから実行:

```bash
export PYTHONPATH=/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/color-code-stim/src:/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/PyMatching/src
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python notes/support/bp_predecoding_audit_20260929/probe.py
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python notes/support/bp_predecoding_audit_20260929/pairs.py
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python notes/support/bp_predecoding_audit_20260929/exact_d5.py
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python notes/support/bp_predecoding_audit_20260929/verify.py
```

既存test（cwd: BP worktree `external_libs/color-code-stim`）:

```bash
PYTHONPATH=src:../PyMatching/src /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest -q tests/test_global_bp.py tests/test_global_dem_projection.py
# 28 passed in 9.91s
```
