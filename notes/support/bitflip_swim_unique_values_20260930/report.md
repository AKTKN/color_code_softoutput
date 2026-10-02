# Bit flip ノイズで SWIM に固有の離散値が現れる理由

指定の `notebooks/workflow_swim_soft_output.ipynb` と、その参照先
`results/bitflip_swim/26_09_30_17_48_23_a219af0b` を調査した。
結論は、**logical gap の奇数倍の間に現れる SWIM の偶数倍は、現在の定義から生じる値であり、今回の検証ではバグを示すものではない**。
SWIM は物理補正どうしの重み差ではなく、論理経路のうち成長クラスタに覆われていない長さを測る。
半辺の被覆と、補正に含まれない辺への被覆が、物理的な重み差の奇偶制約を外す。

以下の量子ビット番号は **Stim circuit の qid** であり、DEM 列番号ではない。
具体例は現行デコーダへ明示的に入力して再現したエラー配置である。
保存 Parquet にはエラー配置・検出器ビット列がなく、過去の特定ショットの実エラーを復元したという意味ではない。

## 保存値と対象設定

保存 run は、一様独立 bitflip、rounds=1、tri、tri_optimal、Z memory、
d=5,7,9,11,13、p=0.02,0.04、各系列100,000 shots。
通常デコーダの SWIM と comparative decoder の logical gap を重ねている。
両方の最終選択基準は `color_correlated_weight_basis="original_dem"`。
BP、摂動、color-correlated decoding は使っていない。

単位重みは自然対数の

\[
w=\log\frac{1-p}{p},\qquad p=0.04:\quad w=\log24=3.178053830347946.
\]

未丸め Parquet で確認したところ、両 p、全距離について logical gap は
\(w,3w,\ldots,dw\)、SWIM は \(w,2w,\ldots,dw\) を取る。
整数倍からの最大ずれは \(5.33\times10^{-15}\) 以下。
`bins="auto"`, `round_digits=2` によるヒストグラム中心の人工的な中間点ではない。
`signed_logical_errors=True` は失敗ショットの符号を表示用に反転するだけである。

| d | p=0.04 で SWIM が偶数倍の shots | 全100,000 shots に対する割合 |
|---|---:|---:|
| 5 | 3,341 | 3.341% |
| 7 | 10,603 | 10.603% |
| 9 | 18,892 | 18.892% |
| 11 | 26,092 | 26.092% |
| 13 | 31,462 | 31.462% |

d=5, p=0.04 では \(2w=6.3561076607\) が1,323 shots、
\(4w=12.7122153214\) が2,018 shots。
表示上はそれぞれ6.36、12.71になる。
全20系列の未丸め値の監査結果は [audit.json](audit.json) にある。

## 二つの重みの意味

**この一様 bitflip 設定の物理重み。** エラー集合 \(E\) の確率は
\(P(E)=p^{|E|}(1-p)^{n-|E|}\) なので

\[
-\log P(E)=-n\log(1-p)+w|E|.
\]

従って二つの具体的補正集合の重み差は、両者の確率比の対数になる。
ただし論理クラス全体の確率は代表元の確率を足し合わせるので、
minimum-representative gap と論理クラスの posterior LLR は別物である。

**奇数倍になる理由の直接導出。** この奇数距離の三角形 color code では
X stabilizer の生成元は偶数重みで、論理 X の代表元は奇数重み。
同じシンドロームで反対論理クラスの補正 \(F_0,F_1\) について、
\(F_0\mathbin\triangle F_1\) は論理 X と X stabilizer の積であり、奇数重みを持つ。
そこで

\[
|F_1|-|F_0|\equiv |F_1\mathbin\triangle F_0|\equiv1\pmod2.
\]

よって、一様物理重みで計算する logical gap は奇数倍になる。
この奇偶性は、候補が各クラスの厳密な大域最小解であることを必要としない。
実装の comparative gap を一般距離で厳密最小 gap と同一視する主張ではない。
今回 d=5 については全物理エラーの列挙から厳密最小との一致も別途確認した。

**SWIM の実装定義。** 色 c の stage-2 成長半径から、元のグラフの各辺を
連続区間としてクラスタで覆う。辺 \(e=uv\) に残る重みは

\[
\bar w_e=\max(0,w_e-h_u-h_v),\qquad
h_v=\max\{0,\max_a(r_a-d_c(a,v))\}.
\]

その残余重みで、物理 c-side と opposite-corner の二端点を結ぶ最短路を探す。
これは [Meister ほかの cluster 定義と Algorithm 2](https://arxiv.org/html/2405.07433v2)
に対応する区間被覆の考え方であり、当プロジェクトの物理経路対応は
[notes/note.tex](../../note.tex) の `thm:swim` にある。
実装上の半径は `sparse_blossom_final_defect_metric_balls_v1` という規約。
一般のショットについて厳密な odd-cut dual certificate は出力していないので、
`swim_bound_certified=False` という既存の制限もそのまま維持する。

元の辺は1個のデータ量子ビットの X エラーに対応するが、\(\bar w_e=w/2\) は
「半分の量子ビットエラー」ではない。**確率の対数を長さの単位にした辺の、
クラスタ外に残る半分の区間**である。
クラスタは、選択補正に含まれない隣接辺にも広がる。

同じ物理論理経路 \(L\) についても、二つの量は一般に違う。

\[
W(F\mathbin\triangle L)-W(F)
 =w\bigl(|L|-2|F\cap L|\bigr),
\]
\[
\bar W(L)=w|L|-\operatorname{length}(L\cap\mathcal C).
\]

被覆長は \(2w|F\cap L|\) に固定されない。
これが、奇数長の物理論理経路から偶数倍の SWIM が出る直接の理由である。

## 具体例

![物理エラー配置と論理経路の部分被覆](examples.png)

左は物理配置。黒い X は入力エラーで、これらの例では最終補正と一致する。
各パッチに r・g・b の3色の証拠経路を重ね、右に各色の被覆区間を並べた。
2つのエラー配置×3色の合計6通りを示している。
色付きの点と接続線は stage-2 の証拠経路を物理量子ビット集合へ写したもの。
接続線は読みやすさのために量子ビットを順に結んでおり、物理格子上の相互作用辺を意味しない。
右は各経路の5本の stage-2 辺。橙色の斜線部を無料にした残りの赤・緑・青色の長さが SWIM。
最短路が縮退している場合は各色につき一つの最小経路を表示している。
6通りの経路と被覆区間は [examples_all_colors.json](examples_all_colors.json) に保存した。
元の選択色だけの図は [examples_selected.pdf](examples_selected.pdf) として保持している。

### 中央に X エラーを1個置く例

d=5 の中央 q20、座標 \((12,2)\) に X エラーを置く。
検出器シンドロームは \(\{D_3,D_4,D_6\}\)。
3色とも補正 \(F=\{20\}\) を返し、同率選択で最終色は r。
3色の SWIM はすべて \(4w\) で、色の最小値選択なしでも偶数倍が生じる。

r の stage-2 シンドロームは行4と23。
その2点の成長半径はそれぞれ \(w/2\)、他の半径は0。
独立参照計算が返した最短論理経路の一つは

\[
L=(q1,q11,q25,q31,q36).
\]

各辺の残余重みは

\[
(w,\tfrac12w,\tfrac12w,w,w),
\qquad \phi=4w.
\]

経路は補正の q20 を含まない。それでも q20 の端点から成長したクラスタが
q11 と q25 の半辺をそれぞれ覆うため、合計 \(w\) が差し引かれる。

一方、最小の反対論理クラスの物理補正は6量子ビット。
例えば \(F\triangle L=\{1,11,20,25,31,36\}\) はその一つで、
同じシンドロームと反対の論理パリティを持つ。
全 \(2^{19}\) 物理エラーの列挙でも最小6を確認した。
従って logical gap は \((6-1)w=5w\)。

**SWIM の \(4w\) は、補正1個と補正5個の比較を意味しない。**
この二つの具体的代表元の確率比は \(e^{5w}\) であって \(e^{4w}\) ではない。

### 最終補正は同じでも SWIM を選ぶ色が変わる例

入力エラー \(E=\{q16,q17\}\)、座標 \((22,1),(4,2)\)。
シンドロームは \(\{D_1,D_2,D_4,D_5\}\)。
3色とも補正は \(F=\{16,17\}\)、重みは \(2w\)、論理パリティは0。
最終色は r だが、SWIM は

\[
(\phi_r,\phi_g,\phi_b)=(3w,2w,2w).
\]

YAML の保存値は
\(\min\{\phi_c:L(F_c)=L(F_*)\}\) なので \(2w\)。
従来の `selected_swim_distance` を使うなら、このショットは \(3w\) になる。
ただし前の中央1エラー例はその変更でも \(4w\) のままであり、
色の選択を変えるだけで中間値が消えるわけではない。

g の証拠経路の一つは \((q17,q11,q4,q5,q8)\)。残余重みは

\[
(0,0,w,\tfrac12w,\tfrac12w),\qquad \phi_g=2w.
\]

この経路を補正へ XOR すると \(\{4,5,8,11,16\}\) の5量子ビットになり、
重み差は \(3w\)。列挙で調べた同じ g-stage-1 制約下の反対クラス最小も5。
一方、物理シンドロームだけを固定すると \(\{1,12,15\}\) の3量子ビット補正があり、
comparative gap は \((3-2)w=w\)。

この具体例で **SWIM \(2w\) > full physical representative gap \(w\)**。
stage-1 制約を固定する SWIM の問題と、logical gap の比較問題が違うためである。
SWIM を full comparative gap の普遍的下界と扱うことはできない。

### 反対論理クラスの候補を除外する例

\(E=\{q17,q32\}\)、シンドローム \(\{D_2,D_4,D_6,D_8\}\) では次の結果になる。

| 色 | 候補補正 | 重み | 論理パリティ | SWIM | 保存値の候補になるか |
|---|---|---:|---:|---:|---|
| r | {17,32} | 2w | 0 | 2w | はい |
| g | {17,32} | 2w | 0 | 3w | はい |
| b | {0,25,33} | 3w | 1 | w | いいえ |

最終補正は r。b の \(w\) は反対クラスなので除外され、保存 SWIM は \(2w\)。
logical gap は \(w\)。無条件の3色最小値を取る処理とは区別が必要である。

## 検証とバグ判定の範囲

- d=5 の全512シンドロームを通常・comparative の両方で復号した。
- 全 \(2^{19}=524,288\) 物理エラーを列挙し、各シンドローム・各論理クラスの厳密最小を求めた。comparative の1,024クラス最小値は全部一致した。この一致を一般距離へ外挿しない。
- 全512シンドローム×3色の1,536件で、C++ の距離と独立 Python 区間和・最短路計算を照合した。最大差は \(8.89\times10^{-16}\)。辺ごとの残余重みも一致した。
- 全証拠経路を元の物理 DEM に写し、ゼロ物理シンドローム・非自明論理パリティを検証した。
- full output と scalar metrics が一致し、SO を無効化しても最終論理予測は変わらなかった。逆順 batch でも予測・SWIM が一致した。
- 偶数倍 SWIM を持つシンドロームは16個。\(4w\) は中央1エラーと同じシンドローム1個、\(2w\) は15個。うち10個は最終選択色自身の SWIM も同じ偶数値だった。

従って今回の偶数倍は、浮動小数点のずれ、描画の丸め、scalar 出力の縮約バグで説明する必要がない。
半辺被覆を手で追える例があり、既存のクラスタ外長という定義と実装が一致している。
一般ショットの成長半径を認証済み最適双対とする主張や、全距離についての不具合不存在の証明は行っていない。

保存 run の2つの decoder alias は point identity に含まれ、それぞれの Stim seed が異なる。
従って保存ファイルの同じ `shot_index` 同士を物理的に同一ショットとして比較してはいけない。
上の具体例・全シンドローム照合では、両デコーダに同じ物理シンドロームを明示的に入力した。

ノートブックの現在の未実行ソースには `"distane": [, 9]` という編集中の構文がある。
保存出力は d=5,7,9,11,13、p=0.04 を含む以前の実行のもので、今回は生データから監査した。
この編集中の内容は変更していない。

## 再現と実装箇所

リポジトリ root から `color_code_so` の Python で実行する。

```bash
python notes/support/bitflip_swim_unique_values_20260930/audit.py
python notes/support/bitflip_swim_unique_values_20260930/plot_examples.py
```

[audit.py](audit.py)、[JSON と選択例の全辺情報](audit.json)、
[全512シンドロームの表](d5_all_syndromes.csv)、[実行結果](audit.log)、
[図の PDF](examples.pdf) を保存した。元の notebook、saved run、decoder source は変更していない。

主な確認箇所は以下の通り。

- [stage-2 backend](../../../external_libs/color-code-stim/src/color_code_stim/soft_output/pymatching_backend.py): 物理確率の log odds と stage-2 matcher。
- [空間 topology と物理ラベル](../../../external_libs/color-code-stim/src/color_code_stim/soft_output/topology.py): 元 DEM・qid・2端点の対応。
- [独立参照](../../../external_libs/color-code-stim/src/color_code_stim/soft_output/reference.py): all-pairs 距離、区間和、証拠経路。
- [C++ 残余重み](../../../external_libs/PyMatching/src/pymatching/sparse_blossom/gap_dijkstra/metric_graph.h): 半径伝播と `max(0, weight-h[u]-h[v])`。
- [成長半径抽出](../../../external_libs/PyMatching/src/pymatching/sparse_blossom/driver/mwpm_decoding.cc): 最終 defect 半径の規約。
- [候補選択と full output](../../../external_libs/color-code-stim/src/color_code_stim/decoders/concat_matching_decoder.py)、[scalar 集約](../../../external_libs/color-code-stim/src/color_code_stim/decoders/experiment_metrics.py): 同じ論理クラスに限定した最小値。
- [NOTATIONS](../../../NOTATIONS.md): 現在の YAML SWIM 定義と証明の制限。

実行時の3リポジトリの commit は `audit.json` に記録した。
root には調査開始前から notebook・描画関連などの未コミット変更があり、そのまま保持している。
