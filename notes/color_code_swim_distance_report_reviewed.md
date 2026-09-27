# Concatenated MWPM に基づく Color-Code Swim Distance の定式化

**Status:** literature survey + mathematical formulation + internal peer-review reflected  
**Date:** 2026-09-11  
**Scope:** 2D triangular color code, initially one CSS sector and one logical qubit; extension to circuit-level detector error models (DEMs) is treated separately.

## 1. Executive summary

本研究で定義すべき量は、color code 自体に対する decoder-independent な「距離」ではなく、**concatenated MWPM が生成する matching-cluster geometry を利用した decoder-relative soft output** と考えるのが最も自然である。

Surface code に対する Meister–Pattison–Preskill の soft output は、MWPM/UFD が生成した最終 cluster を収縮し、その quotient graph 上で非自明な logical operator を形成する最短経路の重みを測る。後続研究ではこの量は *cluster gap*、または *swim distance* と呼ばれている。Surface code の MWPM では、この量 \(\phi\) は opposite logical class の最小重み correction との weight gap に対する下界を与える。

Color code では単一物理 Pauli error が一般に三つの check を反転させるため、native decoding object は graph ではなく 3-uniform hypergraph/string-net であり、surface-code swim distance をそのまま適用できない。一方、concatenated MWPM は各色 \(c\in\{r,g,b\}\) について

1. \(c\)-restricted matching graph \(G_{\neg c}\) で第1段 MWPMを行い、
2. その出力を virtual syndrome として \(c\)-only matching graph \(G_c\) に渡し、第2段 MWPMを行う

という構造を持つ。2D perfect-measurement setting では **\(G_c\) の edge は physical data qubit と一対一対応する**。したがって、最終 correction と logical class に直接対応する graph は第1段の restricted graph よりも **第2段の monochromatic / \(c\)-only graph** であり、ここを Meister 型 swim distance の主要な定義域とするのが妥当である。

各色の第2段 MWPM から correction weight \(W_c\)、logical prediction \(\lambda_c\)、最終 cluster set \(\mathcal C_c\) を得る。cluster を収縮した quotient graph 上で opposite logical class へ移る最小 nontrivial chain の重みを \(\phi_c\) と定義する。その後、concatenated decoder が三色の候補の最小 weight を選択することを反映し、最終 soft output を

\[
\boxed{
\Phi_{\mathrm{CC}}
=
\min_{c\in\{r,g,b\}}
\left[
W_c-W_*
+
\mathbf 1(\lambda_c=\lambda_*)\,\phi_c
\right],
}
\]

\[
W_*:=\min_c W_c,
\qquad
c_*:=\arg\min_c W_c,
\qquad
\lambda_*:=\lambda_{c_*}
\]

と定義することを提案する。これは単純な \(\min_c\phi_c\) より適切である。別色 branch がすでに opposite logical class を出している場合、その branch までの追加 cost は \(W_c-W_*\) だけであり、同一 logical class の branch に対してのみ追加 topological cost \(\phi_c\) が必要だからである。

ただし、この \(\Phi_{\mathrm{CC}}\) が直接近似するのは、**第1段 MWPM の出力を固定した conditional complementary gap** である。full comparative decoding は logical forcing ごとに第1段から再実行するため、現段階では \(\Phi_{\mathrm{CC}}\) と full logical gap の間に一般的な rigorous bound は主張できない。これは本研究で最も重要な理論上の注意点である。

---

## 2. 研究目的と soft-output の target

### 2.1 Exact comparative target

一つの CSS sector を考える。独立 error mechanism を \(e\in\mathbb F_2^N\)、detector/check matrix を \(H\in\mathbb F_2^{m\times N}\)、logical observable matrix を \(L\in\mathbb F_2^{\ell\times N}\) とする。syndrome と logical class は

\[
s=He,
\qquad
\lambda=Le\in\mathbb F_2^\ell.
\]

error mechanism \(i\) の prior を \(p_i\) とし、MWPM 型の nondegenerate log-likelihood weight を

\[
w_i=\log\frac{1-p_i}{p_i},
\qquad
W(e)=\sum_i w_i e_i
\]

とする。logical class \(\lambda\) に条件づけた最小 correction weight は

\[
W_\lambda(s)
=
\min_{e:\,He=s,\,Le=\lambda}W(e).
\]

一つの relevant logical bit \((\ell=1)\) なら

\[
\lambda_*=\arg\min_{\lambda\in\{0,1\}} W_\lambda(s),
\qquad
\Delta_{\mathrm{comp}}(s)
=
W_{1-\lambda_*}(s)-W_{\lambda_*}(s).
\]

baseline correction \(\hat e\) を固定すれば同値に

\[
\Delta_{\mathrm{comp}}
=
\min_{z\in\ker H:\,Lz=1}
\bigl[W(\hat e\oplus z)-W(\hat e)\bigr].
\]

これは「同じ syndrome を持つ correction の中で、logical class を変える最小追加 cost」である。本研究の swim distance は、この quantity を直接 comparative decoding せずに decoder の cluster geometry から近似することを目的とする。

### 2.2 posterior logical LLR との区別

\(\Delta_{\mathrm{comp}}\) は各 logical class の **minimum-weight representative** を比較する量であり、degeneracy を含めた真の posterior class likelihood

\[
\Lambda(s)
=
\log
\frac{\sum_{e:\,He=s,\,Le=\lambda_*}P(e)}
{\sum_{e:\,He=s,\,Le\neq\lambda_*}P(e)}
\]

とは一般に一致しない。したがって、本 report では *logical gap/complementary gap* と *posterior LLR* を区別する。

---

## 3. Color code の代数的・topological structure

### 3.1 Stabilizer structure

2D color code は trivalent かつ face-three-colorable な lattice \(\mathcal L\) 上に定義される。data qubit は vertex に置かれ、各 face \(f\) に

\[
S_f^X=\prod_{v\in f}X_v,
\qquad
S_f^Z=\prod_{v\in f}Z_v
\]

を持つ。CSS かつ self-dual なので、まず \(X\) error / \(Z\)-check decoding の一 sector のみ考えればよい。

Interior data qubit は red/green/blue の三 face に接するため、単一 \(X\) error は三つの \(Z\)-checks を反転させる。dual lattice で見ると、一 physical error は三色の syndrome vertices \(\{v_r,v_g,v_b\}\) に incident する **3-hyperedge** である。この点が surface code と根本的に異なる。

### 3.2 String-net と anyon picture

Color-code excitation は color label \(r,g,b\) と Pauli label \(x,y,z\) を持つ bosons で記述できる。同色 string operator は対応する excitation を移動させ、一般 error configuration は複数色 string の junction を許す string-net になる。triangular patch の color boundary は同じ color label の anyon を condense できる。

このため logical operator は単純な「一種類の edge chain」だけでなく、native color-code description では string-net / relative-homology object として現れる。ただし color code は topological phase として two copies of the toric code に locally equivalent であり、logical information が topological path data で表せること自体は明確である。この equivalence と、projection decoder が用いる three restricted surface-code-like graphs は関連するが、**同一の mapping ではないので混同しない**。

### 3.3 Decoding hypergraph

一 Pauli sector の color-code decoding problem は概念的には

\[
H_{\mathrm{CC}}e=s
\]

であり、\(H_{\mathrm{CC}}\) の interior column weight は 3 である。Lee–Li–Bartlett の Appendix A では、dual lattice の三色 vertex tripletを hyperedge とする decoding hypergraph \(\mathcal H\) を導入し、

\[
\partial_1^{\mathcal H}\{v_r,v_g,v_b\}=v_r+v_g+v_b
\]

と表現している。したがって native hypergraph 上で Meister 型の「cluster contraction 後に Dijkstra で logical path」を行うのは自明ではない。通常の shortest-path graph structure が失われるからである。

---

## 4. Projection decoder と concatenated MWPM の数理構造

### 4.1 Projection decoder

Delfosse の projection decoder は color-code error/syndrome を restricted lattices 上の surface-code-like decoding problems に射影し、それぞれを surface-code decoder（典型的には MWPM）で解いた後、複数 projection の結果を **lifting** して physical color-code correction を復元する。

色 \(c\) を一つ除いた restricted graph を \(G_{\neg c}\) と書く。たとえば \(c=r\) なら、vertex は green/blue checks であり、red physical edge が green/blue faces を結ぶ graph edge に対応する。抽象的には

\[
\pi_c:\; C_1(\mathcal H)\rightarrow C_1(G_{\neg c})
\]

という projection を考え、projected syndrome を MWPM で処理する。最終 physical correction は複数 projection の matching の単純和ではなく lifting step で決まる。

この構造から、**restricted graph 一つだけで計算した swim distance は、その projected matching の ambiguity を測るが、最終 color-code logical ambiguity を直接測るとは限らない**。lifting が三 projection を再結合するためである。

### 4.2 Concatenated MWPM

Concatenated MWPM は projection の情報を別の MWPM に渡すことで lifting 自体を matching problem にする。perfect syndrome measurement の場合、色 \(c=r\) の sub-decoder は次の二段である。

第1段:

\[
\widetilde E_r
=
\operatorname{MWPM}
\bigl(\sigma_Z^{(g)}\cup\sigma_Z^{(b)};G_{\neg r}\bigr).
\]

\(\widetilde E_r\) は original lattice の red edges の odd error parity の prediction \(E_r\) に戻される。

第2段では red-only graph \(G_r\) を用いる。its vertices は red faces と red physical edges（および boundary）であり、**各 original data qubit \(v\) が一つの edge \(\epsilon_r(v)\in E(G_r)\) に対応する**。syndrome は

\[
s_r^{(2)}
=
\sigma_Z^{(r)}\cup E_r,
\]

であり、

\[
F_r
=
\operatorname{MWPM}(s_r^{(2)};G_r)
\]

を physical data-qubit correction に逆写像する。green/blue について同様に計算し、最小 weight candidate を最終 correction とする。

したがって concat decoder では

\[
\boxed{
\text{stage 1: projected parity inference}
\quad\longrightarrow\quad
\text{stage 2: physical-error reconstruction by MWPM}
}
\]

という明確な階層がある。

### 4.3 なぜ stage 2 graph が swim distance に適するか

Projection decoder の restricted lattice edge は physical data error そのものではなく、特定色の edge parity information を表す。一方、2D concat decoder の \(G_c\) では graph edge と physical data qubit が bijective である。このため

- correction weight、
- physical logical observable、
- nontrivial zero-syndrome deformation、
- MWPM dual clusters

を一つの graph 上で対応づけやすい。

これが、本研究では **stage-2 \(c\)-only graph を primary swim graph とする**理由である。

### 4.4 Circuit-level DEM version

Circuit-level では original DEM \(\mathcal M\) を各色について \(\mathcal M_{\neg c}\) と \(\mathcal M_c\) に分解する。第1段 error mechanism ごとに virtual detector を導入し、第2段 \(\mathcal M_c\) では

- \(c\)-colored physical detectors,
- stage-1由来 virtual detectors,
- logical observables

を保持する。edge-like mechanisms のみを残すことで \(\mathcal M_c\) は matching graph として表現され、edge weight は

\[
w_e=\log\frac{1-q_e}{q_e}
\]

となる。

ここでも stage 2 matching graph は final candidate correction の weight と observable prediction を直接返すため、swim construction の自然な対象である。

---

## 5. Meister 型 swim distance の本質

### 5.1 Surface-code definition

Meister–Pattison–Preskill は MWPM/UFD が最終的に形成した cluster set

\[
\mathcal C=\bigsqcup_i C_i
\]

を用い、各 connected cluster \(C_i\) を一点に identify した quotient metric space を作る。実装上は cluster 内部の edge weight を zero にすることと等価である。その quotient graph 上で、inequivalent boundaries を結ぶ shortest logical path の長さを

\[
\phi(\mathcal C)
=
\operatorname{dist}_{G/\mathcal C}(b_0,b_1)
\]

と定義する。

MWPM の場合、cluster は arbitrary connected components ではなく Blossom/MWPM LP の dual growth が生成する geometry である。dual variables \(y_S\) から syndrome vertex の radius

\[
r_v=\sum_{S\ni v} y_S
\]

が定まり、これらの balls の union が cluster geometry を与える。

### 5.2 complementary gap との関係

Surface code の一 logical sector で、MWPM correction を \(F\)、opposite logical class の minimum-weight valid correction を \(M\) とすると、Meister et al. は

\[
\log\frac{P(E=F\mid\sigma)}{P(E=M\mid\sigma)}
=
W(M)-W(F)
\ge \phi(\sigma)
\]

を示す。したがって \(\phi\) は minimum-representative complementary gap に対する conservative lower bound と解釈できる。

ただし、同論文は reverse inequality \(W(M)-W(F)\lesssim C\phi\) を一般に証明しておらず、\(\phi\) と exact gap が定数因子で一致する theorem ではない。さらに true posterior logical-class LLR には degeneracy が含まれるので、それとも区別が必要である。

---

## 6. Proposed definition: per-color color-code swim distance

以下では一 logical bit を仮定する。multi-logical extension は Sec. 9.4 で述べる。

### 6.1 Ordinary concatenated decoding

各色 \(c\) について通常の concat decoding を行い、

\[
a_c = \text{stage-1 MWPM output},
\]

\[
s_c^{(2)}=s_c^{\rm phys}\oplus J_c a_c,
\]

\[
F_c=\operatorname{MWPM}(s_c^{(2)};G_c),
\qquad
W_c=W(F_c),
\qquad
\lambda_c=L_cF_c
\]

を得る。\(J_c\) は stage-1 output を stage-2 virtual syndrome に写す map である。2D lattice formulation では \(a_c\) は \(c\)-colored edge parity set であり、それ自体が stage-2 syndrome vertex set の一部になる。

### 6.2 Cluster quotient

第2段 MWPM の Blossom dual growth から cluster set \(\mathcal C_c\) を抽出し、quotient graph

\[
\bar G_c:=G_c/\mathcal C_c
\]

を作る。equivalently、各 cluster 内を通る edge segment の cost を zero とする。quotient weight を \(\bar w_c\) と書く。

### 6.3 Topological/logical constraint

最も安全な定式化は「どの boundary pair が logical か」を見た目だけで固定するのではなく、stage-2 edge に logical label を付けることである。各 edge \(e\in E(G_c)\) に

\[
\ell_c(e)\in\mathbb F_2
\]

を与え、対応する physical error mechanism が target logical observable を flip するかを記録する。

boundary rows を除いた incidence/check matrix を \(B_c\) とすると、zero-syndrome deformation \(z\in\mathbb F_2^{|E_c|}\) は

\[
B_c z=0
\]

を満たす relative cycle/chain であり、logical class を変える条件は

\[
\ell_c^T z=1.
\]

そこで per-color swim distance を

\[
\boxed{
\phi_c
:=
\min_{z:\,B_cz=0,\,\ell_c^Tz=1}
\bar W_c(z),
}
\]

\[
\bar W_c(z)=\sum_{e:z_e=1}\bar w_c(e)
\]

と定義する。

Triangular code の \(G_c\) が二つの inequivalent boundary classes \(b_c^{(0)},b_c^{(1)}\) を持ち、nontrivial logical chain がちょうどその二 boundary classes を結ぶ path と同値であることを一度証明できれば、これは Meister と同じ

\[
\phi_c
=
\operatorname{dist}_{\bar G_c}
\bigl(b_c^{(0)},b_c^{(1)}\bigr)
\]

に簡約され、Dijkstra で計算できる。

**研究上の重要点:** concat decoder の通常実装では、MWPM に不要な複数 boundary vertices を zero-cost で一つに contract する場合がある。swim distance では logical topology を失わないよう、inequivalent boundary identity を復元するか、observable label \(\ell_c\) を明示的に保持する必要がある。

### 6.4 Logical-label double cover

Boundary geometry を hard-code したくない場合、logical label を用いた 2-sheet covering graph が便利である。各 vertex \(v\) を

\[
(v,0),\;(v,1)
\]

に複製し、edge \(e=(u,v)\) を

\[
(u,q)\longleftrightarrow(v,q\oplus\ell_c(e))
\]

として張る。logical parity 1 の path/cycle は sheet 0 から sheet 1 へ移る path になる。適切に boundary states を指定すれば、\(\phi_c\) はこの lifted graph 上の一回の shortest-path problem に帰着できる。この formulation は circuit-level DEM の observable labels と相性がよい。

---

## 7. Three-color aggregation: concatenated swim gap

### 7.1 なぜ \(\min_c\phi_c\) だけでは不十分か

Concatenated MWPM の最終 decision は、三色 branch の stage-2 correction weight を比較して

\[
W_*:=\min_c W_c,
\qquad
c_*:=\arg\min_cW_c
\]

を選ぶ。したがって confidence も三 branch の競合を含まなければならない。

たとえば \(c_*\) と異なる色 \(c\) がすでに \(\lambda_c\neq\lambda_*\) を予測しているなら、その opposite logical candidate はすでに存在し、追加 cost は \(\phi_c\) ではなく

\[
W_c-W_*
\]

だけである。一方、\(\lambda_c=\lambda_*\) なら、その branch を opposite class に変更する追加 topological cost として \(\phi_c\) が必要になる。

### 7.2 Proposed global quantity

したがって

\[
\boxed{
\Phi_{\mathrm{CC}}
=
\min_{c\in\{r,g,b\}}
\left[
W_c-W_*
+
\mathbf 1(\lambda_c=\lambda_*)\phi_c
\right]
}
\]

を **concatenated color-code swim gap** の第一候補とする。

別の書き方では、各 branch に対する opposite-class weight estimate/lower bound を

\[
\widehat W^{(c)}_{\bar\lambda_*}
=
\begin{cases}
W_c, & \lambda_c\neq\lambda_*,\\
W_c+\phi_c, & \lambda_c=\lambda_*,
\end{cases}
\]

として

\[
\Phi_{\mathrm{CC}}
=
\min_c\widehat W^{(c)}_{\bar\lambda_*}-W_*.
\]

この式は concat decoder の「三色の候補から minimum weight を選ぶ」という decision structure をそのまま soft output に反映している。

---

## 8. Conditional theorem candidate

### 8.1 Fixed-stage-1 complementary gap

各色について ordinary stage-1 output \(a_c\) を固定し、その条件下で stage-2 problem の logical class \(\lambda\) に制約した minimum weight を

\[
W_{c,\lambda}^{(2)}(s\mid a_c)
\]

と定義する。concat branch をまたいだ conditional class minimum は

\[
W_{\lambda}^{\mathrm{cond}}
:=
\min_c W_{c,\lambda}^{(2)}(s\mid a_c).
\]

ordinary concat output の class を \(\lambda_*\) とすれば

\[
W_{\lambda_*}^{\mathrm{cond}}=W_*.
\]

conditional complementary gap は

\[
\Delta_{\mathrm{cond}}
:=
W_{1-\lambda_*}^{\mathrm{cond}}-W_*.
\]

### 8.2 Proposition under Meister-type assumptions

各 \(G_c\) が graphlike MWPM problem であり、opposite logical class の difference が \(\phi_c\) の定義で用いた nontrivial relative path/cycle を必ず含み、Meister et al. の cluster argument が適用できると仮定する。このとき branch \(c\) について

\[
\lambda_c=\lambda_*
\quad\Longrightarrow\quad
W_{c,1-\lambda_*}^{(2)}-W_c\ge\phi_c.
\]

また \(\lambda_c\neq\lambda_*\) のとき ordinary stage-2 MWPM output 自体が opposite-class candidate なので

\[
W_{c,1-\lambda_*}^{(2)}=W_c.
\]

したがって

\[
\boxed{
0\le \Phi_{\mathrm{CC}}\le \Delta_{\mathrm{cond}}.
}
\]

**Proof sketch.** 各色について

\[
LB_c=
\begin{cases}
W_c,&\lambda_c\neq\lambda_*,\\
W_c+\phi_c,&\lambda_c=\lambda_*,
\end{cases}
\]

と置くと、上記 assumption より \(LB_c\le W_{c,1-\lambda_*}^{(2)}\)。よって

\[
\min_c LB_c
\le
\min_cW_{c,1-\lambda_*}^{(2)}
=W_{1-\lambda_*}^{\mathrm{cond}}.
\]

両辺から \(W_*\) を引けば \(\Phi_{\mathrm{CC}}\le\Delta_{\mathrm{cond}}\)。また \(W_c\ge W_*\) かつ \(\phi_c\ge0\) なので \(\Phi_{\mathrm{CC}}\ge0\)。\(\square\)

この proposition は研究の最初の理論結果として狙いやすい。ただし「Meister-type assumptions が color-code \(G_c\) で成立すること」の厳密証明は別途必要である。

### 8.3 Full comparative gap にはまだ拡張できない

Current concatenated comparative decoding は logical class を force したとき **stage 1 から再実行する**。したがって full class-conditioned optimum を

\[
W_\lambda^{\rm full}
=
\min_c
W_{c,\lambda}^{(2)}
\bigl(s\mid a_{c,\lambda}\bigr)
\]

と書くと、一般には

\[
a_{c,\lambda}\neq a_c.
\]

よって

\[
\Delta_{\rm full}
=W_{1-\lambda_*}^{\rm full}-W_{\lambda_*}^{\rm full}
\]

と \(\Phi_{\mathrm{CC}}\) の間には、追加仮定なしでは単純な inequality を置けない。ここを曖昧にして「color-code swim は logical gap の rigorous lower bound」と主張するのは過剰である。

---

## 9. Stage-1 ambiguity: 本手法の主要 limitation

### 9.1 Concatenated MWPM 自体の failure mechanism

Concat decoder の既知の adversarial family では、第1段 restricted MWPM が間違った pairing を選ぶことが第2段の logical failure を誘発する。Lee–Li–Bartlett は \(O(3d/7)\) weight の uncorrectable pattern が存在し得ることを議論し、特定構成では最小例が \(d=25\) に現れることを示している。

これは本研究に直接重要である。第2段だけの \(\phi_c\) が大きくても、第1段 prediction \(a_c\) 自体が fragile なら decoder confidence を過大評価し得る。

### 9.2 First-stage swim signal

各 restricted graph \(G_{\neg c}\) について同様に final cluster quotient を作り、その matching ambiguity を表す

\[
\chi_c
\]

を計算することは可能である。ただし \(\chi_c\) は projected edge-parity inference の confidence であり、単独では physical logical class の flip cost ではない。

したがって初期実験では

\[
\Phi_{\mathrm{CC}}
\quad\text{and}\quad
\chi_{\min}:=\min_c\chi_c
\]

を二つの feature として保持し、

\[
P(\text{logical failure}\mid\Phi_{\mathrm{CC}},\chi_{\min})
\]

を評価することを推奨する。根拠なしに \(\min(\Phi_{\mathrm{CC}},\alpha\chi_{\min})\) と一 scalar に潰すより、まず二次元 calibration で stage-1 information の incremental value を確認する方がよい。

### 9.3 Coupled two-stage deformation problem

より原理的には、stage 1 と stage 2 の deformation を同時に最適化する quantity を考えられる。baseline stage-1 solution からの変化を \(\delta a\)、stage-2 correction の変化を \(\delta f\) とすると、概念的には

\[
H_{1c}\delta a=0,
\]

\[
H_{2c}\delta f=J_c\delta a,
\]

\[
L_{2c}\delta f=1
\]

を満たす変形の最小 decoder-internal cost

\[
\Psi_c
=
\min_{\delta a,\delta f}
\left[
\bar w_{1c}^{T}\delta a
+
\bar w_{2c}^{T}\delta f
\right]
\]

を定義できる。

ただし、これは現段階では **physical log-likelihood gap と解釈してはいけない**。同じ original circuit fault が restricted DEM と only-color DEM の両方に projection/decomposition され得るため、stage-1 と stage-2 weight を単純加算すると同じ physical evidence を二重計数する危険がある。physical likelihood metric にするには original DEM mechanism への map を保持して cost を一度だけ数える formulation が必要である。

したがって \(\Psi_c\) は phase-II の理論課題とし、最初の paper/experiment では \(\Phi_{\mathrm{CC}}\) を primary quantity とする方が明確である。

---

## 10. Circuit-level implementation

### 10.1 Required information

各 color branch の stage-2 DEM graph に対して最低限次を保持する。

- detector nodes（physical \(c\)-detectors + stage-1 virtual detectors）;
- graphlike error-mechanism edges;
- edge weights \(w_e=\log((1-q_e)/q_e)\);
- original observable / logical-fault label \(\ell_c(e)\);
- MWPM dual-growth cluster information;
- physical/temporal boundary identity, または logical parity を追跡できる equivalent boundary representation.

### 10.2 Existing software structure

Current `color-code-stim` implementation already performs two-stage matching per color and obtains the **stage-2 matching weight** for each color; final selection and comparative logical gap are performed from these stage-2 weights.したがって proposed \(W_c\) は既存 decoder の decision statistic と整合する。

User-provided PyMatching fork の soft-output example では、surface-code memory に対して

- `SO_calculator_setup()`,
- `add_boundary_node_SO(...)`,
- `add_boundary_edge_SO(...)`,
- `add_cycle_endpoints_pair_SO(...)`,
- `decode_batch_soft_output(..., return_weights=True)`

という interface が使用されている。したがって実装上は、\(G_c\) の inequivalent logical boundaries を正しく構成できれば既存 machinery をかなり再利用できる可能性が高い。

### 10.3 Recommended implementation path

最初は circuit-level generality を狙わず、2D perfect-measurement triangular 6.6.6 code で次を実装する。

```text
for c in {r,g,b}:
    a_c = MWPM_stage1(s, c)
    s2_c = build_stage2_syndrome(s, a_c, c)

    F_c, W_c, clusters_c = MWPM_stage2_with_clusters(s2_c, c)
    lambda_c = logical_label(F_c)

    Gbar_c = contract_or_zero_cluster_interior(G_c, clusters_c)
    phi_c = shortest_nontrivial_logical_chain(Gbar_c)

c_star = argmin_c W_c
W_star = W[c_star]
lambda_star = lambda[c_star]

Phi_CC = min_c(
    W[c] - W_star
    + (phi[c] if lambda[c] == lambda_star else 0)
)
```

その後、同じ API を \(c\)-only DEM graphs に一般化する。

### 10.4 Complexity

標準 concat decoder は既に三色それぞれで二回、計六回の matching を行う。swim calculation を各 stage-2 graph に一回の Dijkstra として追加できれば

\[
T_{\mathrm{SO}}
=\sum_{c\in\{r,g,b\}}
O(|E_c|+|V_c|\log|V_c|)
\]

である。\(c_*\) のみ計算すれば安いが、他色 branch が小さな \(W_c-W_*\) で opposite logical decision を持つ ambiguity を見落とすため、研究の baseline としては三色すべての \(\phi_c\) を計算する方が妥当である。

---

## 11. Numerical validation plan

### 11.1 Phase I: perfect syndrome measurement

**Code:** triangular 6.6.6 color code, odd \(d\).  
**Noise:** iid \(X\) noise first; self-dualityにより \(Z\) sector は同型。  
**Reference decoder:** concatenated MWPM.  
**Ground-truth confidence proxy:** existing full comparative logical gap \(\Delta_{\rm full}\).

各 shot で少なくとも次を保存する。

\[
(W_r,W_g,W_b),\quad
(\lambda_r,\lambda_g,\lambda_b),\quad
(\phi_r,\phi_g,\phi_b),\quad
\Phi_{\mathrm{CC}},\quad
\Delta_{\rm full},\quad
\text{logical-failure flag}.
\]

可能なら stage-1 \((\chi_r,\chi_g,\chi_b)\) も保存する。

### 11.2 Metrics

1. **Correlation with comparative gap**
   \[
   \rho_{\rm Spearman}(\Phi_{\rm CC},\Delta_{\rm full}),
   \]
   および scatter/conditional quantiles。

2. **Calibration to logical failure**
   \[
   P(L=1\mid\Phi_{\rm CC}\in[g,g+\Delta g]).
   \]
   Surface-code literature と同様に exponential/logistic scaling が出るかを確認する。

3. **Post-selection curve**
   threshold \(\tau\) について
   \[
   \mathrm{LER}_{\rm accepted}(\tau)
   =P(L=1\mid\Phi_{\rm CC}\ge\tau)
   \]
   versus abort rate
   \[
   A(\tau)=P(\Phi_{\rm CC}<\tau).
   \]

4. **Failure classification**: ROC-AUC / PR-AUC。ただし研究主目的が post-selection なら LER–abort curve を優先する。

5. **Runtime overhead**: hard decoding + swim vs full comparative decoding。

### 11.3 Ablation study

少なくとも次を比較する。

- selected branch only: \(\phi_{c_*}\);
- naive: \(\min_c\phi_c\);
- proposed: \(\Phi_{\rm CC}\);
- color weight spread: \(W_{(2)}-W_{(1)}\) among three branches;
- stage-1 signal: \(\chi_{\min}\);
- two-feature model: \((\Phi_{\rm CC},\chi_{\min})\);
- full comparative logical gap \(\Delta_{\rm full}\).

この ablation により「topological cluster geometry が本当に情報を追加しているか」と「単なる color-branch weight difference で十分ではないか」を分離できる。

### 11.4 Stress tests

特に次の subgroup を分離して評価する。

- \(\lambda_r=\lambda_g=\lambda_b\) vs disagreement;
- \(W_{(2)}-W_*\) が小さい vs 大きい;
- constructed \(O(3d/7)\)-type stage-1 failure patterns;
- boundary/corner near errors;
- low-\(p\) regime where clusters are sparse;
- \(p\) near threshold;
- increasing \(d\).

Stage-1 failure family で \(\phi_c\) が高 confidence を誤って出すなら、\(\chi_c\) または coupled formulation が必要であることが明確になる。

### 11.5 Phase II: circuit-level noise

次に `color-code-stim` の actual DEM decomposition を用いる。ここでは

- original DEM observable label を stage-2 edge へ保持できているか、
- DEM compression 後の edge probability が swim metric の weight と一致しているか、
- virtual detector を含む cluster topology が physical logical class と整合するか、
- spatial/temporal boundaries が accidental shortcut を作らないか

を unit test する必要がある。

---

## 12. Relation to previous work and likely novelty

### 12.1 Established ingredients

既存研究で既に確立している部分は次である。

- Color code の topological/string-net/anyon structure。
- Projection decoder による restricted surface-code-like lattices への mapping。
- Concatenated MWPM による two-stage matching および circuit-level DEM generalization。
- Concatenated MWPM に対する comparative decoding / logical gap calculation。
- Surface code MWPM/UFD に対する cluster-gap/swim-distance construction。

### 12.2 What appears new in this formulation

2026-09-11 時点で行った文献検索では、**concatenated MWPM の monochromatic/stage-2 matching graphs の cluster geometry を利用し、三色 branch selection まで含めて Meister 型 swim distance を color code に定式化した査読済み研究は確認できなかった**。ただしこれは exhaustive nonexistence proof ではないため、「first」などの priority claim は追加の文献確認なしには避けるべきである。

特に研究上の新規成分になり得るのは次である。

1. stage-2 \(c\)-only graph を logical swim graph と同定すること;
2. logical labels / inequivalent boundaries を用いた per-color \(\phi_c\) の定式化;
3. 三色 branch competition を組み込んだ
   \[
   \Phi_{\rm CC}
   =\min_c[W_c-W_*+\mathbf1(\lambda_c=\lambda_*)\phi_c]
   \]
   の定義;
4. fixed-stage-1 conditional gap \(\Delta_{\rm cond}\) に対する lower-bound theorem の証明;
5. stage-1 ambiguity を含む failure mode の解析と、two-stage confidence extension。

単に「surface code の swim を color code の restricted graph に適用した」だけでは contribution は弱い。一方、**concat decoder の二段構造と color-selection rule に整合する soft-output quantity を数学的に定義し、exact comparative gap との関係を証明・検証する**ところまで行けば、独立した研究として十分明確な形になる。

---

## 13. Immediate theoretical tasks

最初に証明すべき順序は次がよい。

1. **Stage-2 logical-chain lemma.** Triangular color code の各 \(G_c\) について、\(\epsilon_c^{-1}\) で戻した zero-syndrome chain が nontrivial color-code logical operator になることと、\(G_c\) 上の relative homology/logical label condition が同値であることを証明する。

2. **Boundary characterization.** Standard decoder が contract している boundary vertices を分離し、どの boundary classes の接続が \(L_cz=1\) に対応するかを厳密に示す。geometry だけで曖昧なら observable-labelled double cover を primary definition とする。

3. **Per-color Meister lemma.** Stage-2 MWPM cluster \(\mathcal C_c\) と opposite-class minimum correction に対し
   \[
   W_{c,1-\lambda_c}^{(2)}-W_c\ge\phi_c
   \]
   を証明する。既存 theorem の proof dependencies を一つずつ確認し、surface-code-specific な assumption を color-code stage-2 graph が満たすことを示す。

4. **Global aggregation theorem.** 上記が得られれば
   \[
   \Phi_{\rm CC}\le\Delta_{\rm cond}
   \]
   は短い corollary として得られる。

5. **Full-gap relation.** \(a_{c,\lambda}\) が forcing で変化する effect を解析し、\(\Delta_{\rm cond}\) と \(\Delta_{\rm full}\) の差を数値・理論の両方で評価する。

この順序なら、最初から二段 coupled optimization に入り込まず、明確な theorem → numerical benchmark → extension の流れを作れる。

---

## 14. Assessment of the research direction

本アイデアで最も自然な最初の研究対象は、**“swim distance for color codes” 一般ではなく “cluster-geometric soft output for concatenated MWPM color-code decoding”** である。Color code の native hypergraph topology を直接 shortest-path metric にすることは難しいが、concat decoder がすでに graphlike subproblems に factorize しているため、その internal graph structure を利用すれば Meister の方法をかなり直接的に移植できる。

一方で本質的な新しさは、単一 \(G_c\) 上の Dijkstra ではない。重要なのは

- stage 2 の topology が physical logical class をどのように encode しているか、
- three-color candidate selection を soft output にどう反映するか、
- stage 1 の ambiguity を無視した quantity がどこまで valid か

の三点である。

したがって最初の prototype としては \(\Phi_{\rm CC}\) を実装し、既存 comparative logical gap を reference target にして benchmark するのが最短経路である。その結果、stage-1 ambiguity が主要 error source と確認された場合にのみ two-stage coupled metric へ進むのが合理的である。

---

## References

[1] H. Bombín and M. A. Martín-Delgado, “Topological quantum distillation,” *Physical Review Letters* **97**, 180501 (2006). DOI: 10.1103/PhysRevLett.97.180501.

[2] M. S. Kesselring, F. Pastawski, J. Eisert, and B. J. Brown, “The boundaries and twist defects of the color code and their applications to topological quantum computation,” *Quantum* **2**, 101 (2018). arXiv:1806.02820.

[3] N. Delfosse, “Decoding color codes by projection onto surface codes,” *Physical Review A* **89**, 012317 (2014). DOI: 10.1103/PhysRevA.89.012317; arXiv:1308.6207.

[4] S.-H. Lee, A. Li, and S. D. Bartlett, “Color code decoder with improved scaling for correcting circuit-level noise,” *Quantum* **9**, 1609 (2025). DOI: 10.22331/q-2025-01-27-1609; arXiv:2404.07482.

[5] N. Meister, C. A. Pattison, and J. Preskill, “Efficient soft-output decoders for the surface code,” arXiv:2405.07433 (2024).

[6] K. Kishi, R. Toshio, J. Fujisaki, H. Oshima, S. Sato, and K. Fujii, “Even More Efficient Soft-Output Decoding with Extra-Cluster Growth and Early Stopping,” arXiv:2602.03336 (2026).

[7] O. Higgott and C. Gidney, “Sparse Blossom: correcting a million errors per core second with minimum-weight matching,” *Quantum* (2025), arXiv:2303.15933.

[8] S.-H. Lee, L. H. English, and S. D. Bartlett, “Efficient Post-Selection for General Quantum LDPC Codes,” *npj Quantum Information* **12**, 96 (2026). DOI: 10.1038/s41534-026-01242-x.

[9] S.-H. Lee, F. Thomsen, N. Fazio, B. J. Brown, and S. D. Bartlett, “Low-Overhead Magic State Distillation with Color Codes,” *PRX Quantum* **6**, 030317 (2025).

[10] J. Zhang, Y.-C. Wu, and G.-P. Guo, “Facilitating practical fault-tolerant quantum computing based on color codes,” *Physical Review Research* **6**, 033086 (2024). DOI: 10.1103/PhysRevResearch.6.033086.

[11] `seokhyung-lee/color-code-stim`, current repository inspected 2026-09-11. The repository implements concatenated MWPM, comparative decoding, and logical-gap evaluation.

[12] `timchan0/PyMatching`, user-provided repository/fork inspected 2026-09-11, especially `SO_example`, which exposes the surface-code soft-output setup used for explicit inequivalent boundaries and cycle endpoint pairs.

---

## Source-traceability notes

The formulation above separates three levels of claim.

- **Established:** facts directly stated/proved in Refs. [2–5,8] (color-code topology, projection/concat algorithms, Meister soft output and its surface-code lower bound).
- **Derived:** algebraic consequences of combining established decoder structure with the Meister construction (notably the fixed-stage-1 aggregation inequality).
- **Proposed:** the specific color-code quantities \(\phi_c\), \(\Phi_{\rm CC}\), the double-cover implementation for this setting, and the stage-1-aware extensions. These are not attributed to prior work.

