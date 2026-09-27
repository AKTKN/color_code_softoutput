# Deferred proof program from the initial source audit

Archived on 2026-09-11 before implementing prompts/CODEX_TASK_01_BOUNDARY_STRUCTURE.md.
This preserves prior notation and conditional proposals; it is not an active
specification, a construction performed in Task 1, or a record of proved results.
Current state and next-task authorization are in the six project-state documents.
In particular, all split-graph, logical-path, relative-homology and swim-distance
material below remains deferred. Historical 'next task' and 'to verify' wording
is superseded by the reviewed Task 1 note.

## Historical notation sections 4 and 6

## 4. Boundary spaces and the candidate split graph

**Source:** [Lee2025], Appendix A.3, pp. 22–23:
\[
V_{\rm bdry}(\mathcal H)=\{v_{\rm bdry}^r,v_{\rm bdry}^g,v_{\rm bdry}^b\},
\quad V_{\rm bdry}(\mathcal L_{\neg c}^*)=
\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\},
\]
\[
V_{\rm bdry}(\mathcal L_c^*)=
\left\{v_{\rm bdry}^{c},\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}\right\},
\quad C_{\rm bdry}(G)=\mathbb F_2^{V_{\rm bdry}(G)}.
\tag{N4}
\]
The nested pair is **one stage-2 vertex**, representing a dual boundary edge, not two additional stage-2 vertices.

**Project names:** $b_c^0=v_{\rm bdry}^c$,
$b_c^1=\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}$,
$\mathcal B_c=\{b_c^0,b_c^1\}$.
Let $G_c=\widetilde{\mathcal L}_c^*$ denote the graph retaining these source boundary labels and only physical-qubit edges. Its status as a *logical* decoding graph is proposed.

Let $\rho_c:C_0(G_c)\to C_0(G_c)/C_{\rm bdry}(G_c)$ delete the boundary coordinates and
\[
D_c=\rho_c\partial_1^{G_c},\qquad K_c=\ker D_c.
\]
The project affine-fiber notation is $\mathcal A_c(\sigma,b_c)=\{x:D_cx=t_c\}$. For a fixed compatible $(\sigma,b_c)$, $t_c=\rho_c((1-\pi_0^{(c)})\sigma+b_c)$ is the stage-2 syndrome and the feasible corrections satisfy $D_cx=t_c$. Differences of two such corrections belong to $K_c$. Claim 2 supplies physical syndrome validity; it does not identify the logical class.

For $z\in K_c$ define
\[
\beta_c(z)=(\partial_1^{G_c}z)_{b_c^0}
=(\partial_1^{G_c}z)_{b_c^1},\qquad
\lambda_c(z)=\ell_Z^\mathsf T T_cz .
\]
The equality of the two endpoint coefficients is binary graph parity; $\beta_c=\lambda_c$ is the **unproved target**, not a definition.

The exact proposed physical-equivalence quotient is
\[
R_c=K_c\cap T_c^{-1}(S_X),\qquad \mathcal Q_c=K_c/R_c.
\tag{N5}
\]
The intersection matters: an arbitrary physical stabilizer need not preserve the fixed stage-1 auxiliary constraints.

A graph by itself has no 2-cells, so $H_1(G_c,\mathcal B_c)$ does not automatically quotient out physical stabilizers. Write $A_c$ for the proposed map sending each real non-c face $f$ to $T_c^{-1}Jf$. An optional cellular model $\widehat G_c$ may attach the non-c physical-face cells suggested by Lee Appendix A.1. The boundary attachment maps, $\partial_1\partial_2=0$ in the relative complex, and $\operatorname{im}\partial_2=R_c$ must be checked before identifying $H_1(\widehat G_c,\mathcal B_c)$ with $\mathcal Q_c$. Generic $Z_1=\ker\partial_1$, $B_1=\operatorname{im}\partial_2$, and $H_1=Z_1/B_1$ apply only to a specified complex.


## 6. Cluster metric and conditional swim notation

**Meister source notation:** weighted decoding graph $G_D$, modified graph $G_D'$, metric realization $(X_G,d_G)$ with edges as intervals, radii $r_v$, and
\[
\mathcal C(\{r_v\})=\bigcup_v B_{r_v}(v)=\bigsqcup_i C_i.
\]
Here $V_\sigma$ is the set of active syndrome vertices, $O_\sigma$ its odd-cardinality subsets, and for a syndrome-vertex pair $e=(u,v)$ the source cut set $\delta(e)$ consists of odd subsets containing exactly one endpoint. The pair cost $w_e=d_{G_D}(u,v)$ is a shortest-path cost, not necessarily the weight of one physical edge. In the source dual, $y_S\ge0$ and $\sum_{S\in\delta(e)}y_S\le w_e$.
MWPM radii are $r_v=\sum_{S\in O_\sigma:v\in S}y_S$, from the matching dual (Definition 7, Eq. (6)); fully grown radii use a final optimal dual solution. UF radii come from Algorithm 1/Definition 8, whose displayed version uses uniform weights.

**Project notation:** $\mathcal C_c$ denotes a verified realization of actual stage-2 growth on $G_c$. For $0<p<1/2$, take physical edge weights $\omega_e=\log((1-p)/p)>0$ initially; arbitrary positive weights are a proposed metric extension. $W(x)=\sum_{e\in x}\omega_e$ is matching cost, not a posterior class probability.

Conditional on the topology and growth-transfer obligations in [PROJECT_DETAIL.md](../PROJECT_DETAIL.md),
\[
\phi_c(\sigma,b_c;\mathcal C_c)
=d_{X_{G_c}/\{C_i\}}([b_c^0],[b_c^1])
=\min_{z\in K_c:\,\beta_c(z)=1}|z\setminus\mathcal C_c|_\omega .
\tag{N6}
\]
This is a **planned per-color definition**, not a proved confidence theorem. Zeroing costs means zeroing precisely covered edge segments; subdivide partially covered edges when necessary. No matching-only virtual shortcut between the two boundaries belongs to this metric. If one cluster connects them, the candidate value is zero; disconnected boundaries give $+\infty$ and indicate a failed connectivity obligation for the intended patch.


For the surface-code source theorem only, write $F_{\rm MWPM}$ for its correction edge set and $M_{\rm opp}$ for a minimum-weight syndrome-valid edge set in the opposite logical class. These are aliases for Meister's $F,M$, avoiding collision with the physical-face set $F$. Its endpoint-pair notation $\partial M$ (Definitions 3–4) is a set of pairs in a disjoint-path decomposition, not the binary syndrome map $\partial_1 M$. With these local aliases, its Lemmas 11–12 give
\[
|M_{\rm opp}\cap\mathcal C|_\omega
\ge\sum_{e\in\partial M_{\rm opp}}\sum_{S\in\delta(e)}y_S
\ge |F_{\rm MWPM}|_\omega.
\]
This is an imported source statement with source path and optimal-dual hypotheses, not an established inequality for the color graph.

## Historical project formulation

# PROJECT_DETAIL.md

Last audit: 2026-09-11. This document is the authoritative preliminary formulation. Notation is defined in [NOTATIONS.md](../NOTATIONS.md); source editions and precise pointers are in [refs/REFERENCES.md](../refs/REFERENCES.md).

**Outcome of this run:** the source audit and theorem formulation are complete at the level stated below. The central theorem is not proved. The strongest correction to the scaffold is that Lee Appendix A.3 already retains two stage-2 boundary vertices. Their physical logical interpretation, rather than their mere existence, is the main remaining task.

Status labels: **[SOURCE]** is a result explicitly supported by an inspected source; **[TRANSLATION]** is its stated algebraic re-expression; **[PROPOSED]** is a definition or target of this project; **[OPEN]** is an unresolved proof/verification obligation.

## 1. Physical preliminaries and selected patch class

### 1.1 Lattice, checks, and boundary convention

**[SOURCE]** Lee Sec. 2.1, Eq. (1), and Fig. 1 place data qubits at primal vertices and an X check and Z check on every physical face:
\[
S_f^X=\prod_{q\in f}X_q,\qquad S_f^Z=\prod_{q\in f}Z_q.
\]
The bulk is trivalent and faces are properly three-colored. The standard triangular patch has three differently colored boundary arcs and encodes one logical qubit. A boundary of color $c$ is adjacent only to faces of the other two colors. “Boundary” here is a colored arc of the physical disk, not a separate connected component of the disk's entire topological boundary.

**[PROPOSED scope restriction]** Begin with the standard finite, simply connected triangular 6.6.6 patch of odd distance $d\ge3$ used in Lee's figures. Boundary checks are the usual even-weight truncated face checks; corners have their usual single-face incidence. Exclude holes, twists, Pauli boundaries, extra logical qubits and the degenerate distance-one patch. Trivalence describes the bulk/completed construction; do not demand three retained physical edges at every truncated boundary vertex.

The required combinatorial input is the physical vertex/edge/face incidence and its color labels, not just a drawing. For any subsequent generalization, require commuting checks, the same boundary/corner incidence types, and $\dim(\ker H/\operatorname{im}H^\mathsf T)=1$ explicitly. Face colorability alone does not establish all of these patch properties.

### 1.2 Physical support, syndrome, stabilizers, and logical class

**[TRANSLATION]** Work with the binary physical complex
\[
U\xrightarrow{J=H^\mathsf T}A\xrightarrow{H}U,\qquad HJ=0.
\tag{P1}
\]
Here $A$ is spanned by physical qubits and $U$ by physical faces. This is the color-code hypergraph complex in the physical basis, not the ordinary cellular complex of the primal disk. Its first homology is exactly the X-sector logical-support space
\[
\mathcal L_X=\ker H/\operatorname{im}J.
\]
A correction $a$ is syndrome-valid when $Ha=\sigma_Z$. It succeeds for actual error $e$ when $e+a\in\operatorname{im}J$, and fails logically when $e+a\in\ker H\setminus\operatorname{im}J$. A nonzero-syndrome correction itself is not a normalizer element.

Fix a physical logical-Z representative $\ell_Z$ (for example a standard boundary representative after the patch is fixed). For a zero-syndrome X support, its logical label is $\ell_Z^\mathsf Ta$. Changing that support by a physical X stabilizer preserves the label. These statements use the CSS support algebra, independently of any proposed graph topology.

### 1.3 Strings, string-nets, and boundary termination

**[SOURCE]** Bombín–Martín-Delgado, pp. 2–3, Eqs. (4)–(6) and Figs. 2–3, give colored string operators and their deformations modulo face stabilizers. Strings of matching color may end at that color boundary. Three colored strings can join to form a logical string-net on the standard triangle; the paper gives anticommuting X/Z representatives. Lee Sec. 2.1 additionally gives representatives supported along a physical boundary.

Kesselring Secs. 3.3–3.4 and 4.2–4.3 describe same-color charge condensation and show a corner between two color boundaries with only a face of the third color incident to its qubit (Fig. 6(c)). These are physical endpoint rules. A path in Lee's stage-2 graph must still be mapped through $T_c$ before these rules can be applied; its alternating face/edge vertices are not physical string positions.

**[SOURCE, limited use]** Kubica et al., Sec. III B, Eq. (44), Theorem 3, show that the triangular code unfolds to one folded surface-code patch formed by attaching two layers. This explains why two independent surface-code layers are the wrong boundary model. No equality between that Clifford map and $T_c$ is imported.

## 2. Exact concatenated-decoder preliminaries

### 2.1 The two graph constructions

**[SOURCE]** Lee Sec. 3, Definitions 1–2:

For fixed $c$, stage 1 uses $\mathcal L_{\neg c}^*$: real vertices are $c_1,c_2$ faces, and graph edges correspond to primal $c$ edges via $\epsilon_{\neg c}$. Stage 2 uses $\mathcal L_c^*$: real vertices have two distinct types, $c$ faces and primal $c$ edges. Each physical qubit becomes one edge via $\epsilon_c$, between its incident objects of those two types. A missing endpoint is attached to the ordinary matching boundary. Preserve edge identities even if endpoint pairs coincide.

With perfect measurements, Lee's set equations are
\[
\widetilde E_{\rm pred}^{(c)}
=\operatorname{MWPM}(\sigma_Z^{(c_1)}\cup\sigma_Z^{(c_2)};
\mathcal L_{\neg c}^*,v_{\rm bdry}),\quad
E_{\rm pred}^{(c)}=\epsilon_{\neg c}^{-1}(\widetilde E_{\rm pred}^{(c)}),
\]
\[
\widetilde V_{\rm pred}^{(c)}
=\operatorname{MWPM}(\sigma_Z^{(c)}\cup E_{\rm pred}^{(c)};
\mathcal L_c^*,v_{\rm bdry}),\quad
V_{\rm pred}^{(c)}=T_c\widetilde V_{\rm pred}^{(c)}.
\tag{P2}
\]
These combine different types of syndrome vertices. In this project the color and first-round output are fixed throughout the stage-2 analysis. No claim about color-branch aggregation follows.

### 2.2 Appendix A's exact factorization

**[SOURCE]** Associate physical qubit $q$ with a hyperedge
$h_q=\{u_r,u_g,u_b\}$ of $\mathcal H$. For fixed $c$, its stage-2 edge has endpoints
\[
u_c\quad\text{and}\quad\{u_{c_1},u_{c_2}\}.
\]
The second endpoint is a dual edge, viewed as a stage-2 vertex. Appendix A.1 identifies the two chain bases already.

The projector $\pi_0^{(c)}$ removes color $c$. Eq. (10) decomposes the incidence map as
\[
\partial_1^{\mathcal L_c^*}=p_{\rm vert}^{(c)}+p_{\rm edge}^{(c)},\quad
p_{\rm vert}^{(c)}h_q=u_c,\quad
p_{\rm edge}^{(c)}h_q=\{u_{c_1},u_{c_2}\}.
\]
The source identity underlying Claim 1 is
\[
\partial_1^\mathcal H
=p_{\rm vert}^{(c)}
+\partial_1^{\mathcal L_{\neg c}^*}p_{\rm edge}^{(c)}.
\tag{P3}
\]
Without boundaries, $\partial_1^{\mathcal L_{\neg c}^*}b_c=\pi_0^{(c)}\sigma$ and
$\partial_1^{\mathcal L_c^*}x=(1-\pi_0^{(c)})\sigma+b_c$
imply $\partial_1^\mathcal Hx=\sigma$ (Claim 1, Eqs. (11)–(12)).

**Translation caution:** Delfosse Theorem 5.6 concerns projection onto the restricted graphs. Its degree-one map matches the closed-setting $p_{\rm edge}^{(c)}$, not the bijection between physical qubits and stage-2 edges. His complex describes Z errors; our X-error version uses the explicitly stated CSS exchange. His closed-surface hypotheses are not a proof of boundary behavior.

### 2.3 What the ordinary matching boundary represents

**[SOURCE]** In Appendix A.3, the dual graph is completed with $v_{\rm bdry}^r,v_{\rm bdry}^g,v_{\rm bdry}^b$ and their pairwise dual edges. A missing face is represented by the boundary vertex of its color. The source lists
\[
V_{\rm bdry}(\mathcal L_c^*)=
\{v_{\rm bdry}^{c},\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}\}.
\tag{P4}
\]
The main-text $v_{\rm bdry}$ suppresses this distinction for matching. Its incident dangling edges need not terminate at one physical location. Matching imposes parity at real checks, while boundary parity is free.

Claim 2, Eq. (13), is precisely
\[
\partial_1^{\mathcal L_{\neg c}^*}b_c-\pi_0^{(c)}\sigma
\in C_{\rm bdry}(\mathcal L_{\neg c}^*),
\]
\[
\partial_1^{\mathcal L_c^*}x-(1-\pi_0^{(c)})\sigma-b_c
\in C_{\rm bdry}(\mathcal L_c^*),
\tag{P5}
\]
and concludes $\partial_1^\mathcal Hx-\sigma\in C_{\rm bdry}(\mathcal H)$.
Deleting virtual coordinates gives the physical syndrome. **It does not conclude trivial logical residual error.**

The augmented restricted graph also has a boundary-only dual edge. It is not an extra primal data edge covered by the main-text $\epsilon_{\neg c}$ bijection. Its coefficient in $b_c$ is ignored in the stage-2 relative syndrome because it corresponds to a boundary vertex there. Keep this distinct from the ordinary physical-edge stage-1 prediction.

## 3. Candidate boundary structure and physical interpretation

### 3.1 A concrete graph to audit

**[PROPOSED, source-guided]** Define $G_c=\widetilde{\mathcal L}_c^*$ using Lee's retained boundary labels
\[
b_c^0=v_{\rm bdry}^c,\qquad b_c^1=\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}.
\]
For each physical qubit only, form its augmented triple $h_q$ and add the edge
$(u_c(q),\{u_{c_1}(q),u_{c_2}(q)\})$ labeled $q$. Retain the real face/edge vertices and these two boundary vertices. This is an explicit candidate construction; it does not define “inequivalent” by fiat.

Equivalently, in the main-text graph reattach a dangling edge missing its $c$-face endpoint to $b_c^0$, and an edge missing its primal $c$-edge endpoint to $b_c^1$. All other physical edges keep their endpoints.

There is no new data qubit associated with an exterior triangle made from all three boundary vertices. Pairwise boundary **dual edges** are endpoint labels in this construction, not license to add a zero-cost physical path between $b_c^0$ and $b_c^1$. Any auxiliary matching edges must be excluded from the physical logical metric.

### 3.2 Boundary incidence table to verify

The following is the source-guided interpretation for the standard triangular patch, read from Definition 2, Appendix A.3, Lee Fig. 2, and the physical corner convention. The table is an audit specification, **not a completed proof for every distance or lattice family**.

| Physical qubit location | Augmented triple | Stage-2 boundary incidence |
|---|---|---|
| Bulk | Three real face vertices | Both endpoints real |
| Interior of $\Gamma_c$ | $v_{\rm bdry}^c,u_{c_1},u_{c_2}$ | Incident to $b_c^0$; real $c$-edge endpoint |
| Interior of $\Gamma_{c_1}$ or $\Gamma_{c_2}$ | One non-c boundary vertex and two real vertices | Real $c$ face and real $c$-edge endpoint; no stage-2 dangling edge |
| Corner $\Gamma_{c_1}\cap\Gamma_{c_2}$ | $u_c,v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}$ | Incident to $b_c^1$; real $c$-face endpoint |
| Corner $\Gamma_c\cap\Gamma_{c_1}$ (or $c_2$) | $v_{\rm bdry}^c,v_{\rm bdry}^{c_1},u_{c_2}$ | Incident to $b_c^0$; other endpoint is a real boundary $c$ edge |

Thus the expected $b_c^0$ family includes the entire $\Gamma_c$ support, including its endpoints, while $b_c^1$ represents the opposite corner sector. The source explicitly gives the two vertex labels. Exhaustiveness of this physical edge partition, absence of extra incidences, and its logical meaning remain separate obligations.

## 4. Physical equivalence before graph homology

### 4.1 The exact domain

Let $D_c=\rho_c\partial_1^{G_c}$ omit both boundary rows and let $K_c=\ker D_c$. For compatible fixed $(\sigma,b_c)$ define the affine fiber
\[
\mathcal A_c(\sigma,b_c)=\{x:D_cx=t_c\}.
\]
If $x_0$ exists, this fiber is $x_0+K_c$. A difference $z\in K_c$ preserves all real stage-2 constraints, including auxiliary $c$-edge parity. Ordinary $\ker\partial_1^{G_c}$ is smaller because it also imposes zero parity at both boundaries.

**[TRANSLATION of a source result]** Under the physical-edge identification of the candidate construction with Appendix A.3, Claim 2 specialized to zero syndrome and zero stage-1 chain gives $T_c(K_c)\subseteq\ker H$. This is syndrome validity supplied by the source, not a new proof of the logical theorem. The explicit boundary-incidence audit must check that the chosen finite graph realizes this identification.

Define
\[
R_c=K_c\cap T_c^{-1}(\operatorname{im}J),\qquad
\mathcal Q_c=K_c/R_c .
\tag{P6}
\]
This gives precisely the relation $z\sim z'$ when $T_c(z+z')$ is a physical stabilizer while both chains preserve the stage-2 constraints. It defines a map
\[
\overline T_c:\mathcal Q_c\longrightarrow\mathcal L_X.
\]
With syndrome validity established this map is well-defined and injective by the definition of $R_c$; whether its image contains the nontrivial physical logical class remains part of the target.

Do not replace $R_c$ with all physical stabilizers without checking the auxiliary constraints. For instance, a $c$-face support can have odd overlap with the primal $c$ edges leaving it and therefore change the stage-1 parity data. A fixed stage-2 fiber is not the space of all physically syndrome-valid corrections.

### 4.2 Optional cellular route

Appendix A.1 gives stage-2 2-cells around non-c dual vertices in the closed setting. For the patch, a candidate is to attach cells with boundaries $T_c^{-1}Jf$ for **real non-c faces** $f$. Define this candidate attaching map $A_c$ on that face span.

The precise obligations are
\[
D_cA_c=0,\qquad \operatorname{im}A_c=R_c,
\tag{P7}
\]
together with a correct treatment of boundary attachments. Only then could
$H_1(\widehat G_c,\mathcal B_c;\mathbb F_2)$ be identified with $\mathcal Q_c$.

The plain graph $G_c$ has $C_2=0$. Calling two paths “homologous in the graph” does not quotient out any nonzero face cycles. Nor does ordinary homology of a physical disk encode this color-code support complex. The algebraic quotient (P6) is the primary formulation; a surface-like cell complex is optional.

## 5. Central theorem skeleton — statement only

**T-LOGICAL [PROPOSED; UNPROVED].** Let the physical code be the standard triangular patch in Sec. 1, fix $c$ and the X-error sector, and construct the physical-edge graph $G_c$ by Sec. 3. The explicit incidence audit must establish its correspondence to Lee Appendix A.3. For every $z\in K_c$, define its endpoint parity $\beta_c(z)$ as the coefficient of $b_c^0$ in $\partial_1^{G_c}z$; the coefficient at $b_c^1$ is equal by binary graph parity.

The target assertions are:

1. The retained boundary vertices belong to a common component containing a physical-edge path.
2. For every $z\in K_c$,
   \[
   \lambda_X(T_cz)=\beta_c(z).
   \tag{T1}
   \]
3. Equivalently, using the physical one-qubit quotient and syndrome validity,
   \[
   R_c=\ker(\beta_c|_{K_c}),\qquad
   \mathcal Q_c\cong\mathcal L_X\cong\mathbb F_2,
   \tag{T2}
   \]
   with the nonzero class represented by a boundary-to-boundary path.

Consequences to establish with the theorem: every such path maps to a nontrivial physical logical X operator; every zero-endpoint-parity relative chain maps to a stabilizer; two relative chains have the same physical logical class exactly when their endpoint parities agree. In particular, closed cycles in the **split** graph would be stabilizer-trivial. A cycle in the **merged** graph can instead lift to an open boundary-to-boundary chain, so the same claim must never be applied indiscriminately to the merged graph.

An optional strengthening identifies $R_c$ with the non-c face-cell boundaries of (P7). It is not needed merely to state (T1) and must not be assumed in its proof.

No proof of (T1), (T2), or the generating-set equality is attempted here. The theorem is specific enough to refute: any $z\in K_c$ with $\lambda_X(T_cz)\ne\beta_c(z)$ would invalidate it for the specified patch.

## 6. Meister preliminaries and transfer conditions

### 6.1 What the source actually establishes

**[SOURCE]** Meister Sec. II B.1 chooses a modified surface-code graph in which paths between inequivalent boundary vertices represent logical operators and cycles are stabilizer-trivial. In the metric realization, edges are intervals of positive length. Definition 1 forms a cluster set as a union of metric balls and takes its connected components.

For MWPM, Definition 7 gives $r_v=\sum_{S\in O_\sigma:v\in S}y_S$. Fully grown clusters use the final optimal matching dual solution. For UF, Definition 8 uses the terminal radii of Algorithm 1; the displayed algorithm assumes uniform weights, and clusters stop when their defects can be paired or absorbed at a boundary. A component of the final correction support is not this growth object.

Definition 9 contracts each cluster component to a point; Algorithm 2 computes the shortest path between inequivalent boundaries with covered edge costs zero. At partial coverage, the metric definition is controlling: subdivide the edge at coverage endpoints instead of zeroing an entire edge merely because one portion is covered.

Meister's Lemmas 11–12 use valid loop-free path sets, the matching dual, and strong duality to compare intersection costs inside clusters. Theorem 13 then bounds the log ratio of an MWPM error representative to an opposite-class minimum representative by the cluster quantity. It does not sum probabilities across degenerate logical classes. The exact UF posterior identity is Theorem 10 for the odd repetition code, not a theorem for this color code.

More explicitly, with the source-only aliases defined in NOTATIONS §6, Theorem 13 states
\[
\log\frac{\Pr(E=F_{\rm MWPM}\mid\sigma)}
{\Pr(E=M_{\rm opp}\mid\sigma)}
=|M_{\rm opp}|_\omega-|F_{\rm MWPM}|_\omega
\ge\phi(\sigma).
\tag{P9}
\]
The probability-to-weight identity uses the source's independent bit-flip model and log-odds weights. The underlying lemmas compare the competitor's cluster-intersection weight with the optimal correction weight via the optimal matching dual. Their explicit inequalities and the distinction between physical-edge incidence and endpoint-pair cuts are recorded in NOTATIONS §6. This is the surface-code source result only; proving an analogue is outside this preliminary run.

### 6.2 Hypothesis audit

| Requirement | Current state | Required action before use |
|---|---|---|
| Physical errors give individually labeled graph edges | Source Definition 2 supplies it in the perfect-measurement model | Verify the concrete boundary construction; retain multiplicities |
| Relative stage-2 syndrome equations imply physical syndrome equations | Source Claim 2, with explicit translation | Check real/virtual row conventions against $D_c$ |
| Paths and graph cycles have the required physical logical meaning | **Open: T-LOGICAL** | Establish (T1), including zero-parity chains |
| Both logical classes occur in a fixed feasible stage-2 fiber | **Open**, follows from a nontrivial path once proved | Establish connectivity and nontrivial image; do not assume it from $k=1$ alone |
| Cluster radii correspond to the actual stage-2 decoder and weights | Definition available; extraction/lift not established | Specify and verify growth records, including boundary behavior |
| Splitting retains the needed matching optimum and cluster support | **Open** | Show equivalence of real-check feasible costs; track dual data through boundary handling |
| No zero-cost boundary shortcut contaminates the metric | Required by construction | Keep matching auxiliaries out of the physical graph |
| Correction/competitor path decomposition fits source Lemmas 11–12 | **Open for transfer** | Verify source loop-free/path hypotheses and boundary endpoints, or state a justified extension |
| Positive weights define the base metric | Adopted initially: uniform $0<p<1/2$ log-odds | Handle zero/negative weights separately before generalization |
| Probability ratio equals representative weight difference | Holds for independent physical bit flips | Do not infer independence or a posterior model from a fixed stage-1 prediction |
| A claimed UF bound has a matching source theorem | Not established here | Restrict UF to a candidate geometric quantity; do not import repetition-code equality |

Ordinary boundary merging is harmless for matching feasibility in the source sense, but metric balls on a graph with merged boundaries need not coincide with balls on the split graph. Growth and splitting cannot be assumed to commute. A lift must preserve the physical edge metric, source radii interpretation, and coverage properties. Current local decoder methods return predictions and weights, not the dual record.

The source describes a valid loop-free set as disjoint paths. Do not silently equate that with every cycle-free graph or every minimum representative on an arbitrary new graph. The source hypotheses and their needed extension, if any, belong in the later review.

The topology conditions support a geometric definition; they alone do not transfer an analytical likelihood theorem. Neither Theorem 10 nor Theorem 13 is asserted for the color code in this run.

### 6.3 Conditional per-color construction

**D-SWIM [PROPOSED, conditional].** Given a compatible fixed $(\sigma,b_c)$, the graph $G_c$ satisfying T-LOGICAL, positive physical edge weights, and an admissible realization $\mathcal C_c=\bigsqcup_i C_i$ of fully grown stage-2 clusters, define
\[
\phi_c(\sigma,b_c;\mathcal C_c)
=d_{X_{G_c}/\{C_i\}}([b_c^0],[b_c^1])
=\min_{z\in K_c:\,\lambda_X(T_cz)=1}|z\setminus\mathcal C_c|_\omega .
\tag{P8}
\]
The equivalence of the logical-chain optimization and the boundary shortest path is conditional on T-LOGICAL and the nonnegative metric/path reduction. The quotient is formed by contracting **each connected cluster**, not all clusters together. After subdividing partially covered edges, setting covered segment costs to zero implements the metric.

If a cluster spans both boundaries, the candidate value is zero. The definition does not require all clusters to be topologically trivial; that property must not be assumed when failures or ambiguous syndromes are precisely the cases of interest. A value of zero is not proof of logical failure. A positive value is not an exact posterior confidence.

## 7. Six-step proof program and dependencies

| Step | Concrete output | Status |
|---|---|---|
| 1. Boundary structure | Verify every qubit's augmented triple, including all three corners; prove the table exhaustive for the chosen patch family | Source construction located; finite-family audit open |
| 2. Split boundary | Identify $G_c$ with the physical-edge version of Appendix A.3; establish connectivity and absence of extra edges | Definition specified; verification open |
| 3. Physical-support map | Use the existing linear inverse $T_c$; apply Claim 2 with the exact real-row quotient | Source map available; concrete incidence compatibility open |
| 4. Logical/trivial quotient | Establish T-LOGICAL; characterize $R_c$, optionally by (P7) | Central theorem unproved |
| 5. Modified logical graph | Check all topology and decoder-growth conditions required for the intended Meister construction | Conditional checklist specified |
| 6. Per-color swim distance | Activate D-SWIM only after the required topology and growth checks | Conditional definition specified |

Dependency graph:

~~~mermaid
flowchart TD
    A["Physical patch and CSS complex P1"] --> B["Boundary-incidence audit"]
    L["Lee Definitions 1-2 and Appendix A.3"] --> B
    B --> G["Physical-edge split graph G_c"]
    L --> T["Support map T_c and Claim 2"]
    G --> T
    T --> Q["Exact quotient K_c / R_c"]
    G --> E["Endpoint parity and connectivity"]
    Q --> MAIN["T-LOGICAL: physical parity equals endpoint parity"]
    E --> MAIN
    Q --> CELLS["Optional: non-c face-cell generators"]
    MAIN --> TOPO["Modified logical decoding graph"]
    M["Meister definitions and hypothesis audit"] --> C["Verified stage-2 cluster realization"]
    TOPO --> SWIM["Conditional per-color swim definition"]
    C --> SWIM
~~~

Every later proof must state its patch assumptions, map domains, boundary handling and source dependencies, and undergo an adversarial review before use. The existing notes' three-color aggregation, conditional/full-gap inequalities, prototypes and experiments are deferred material, not established results of this milestone.

## 8. Single best next task

Verify the full boundary-incidence model for the standard odd-distance triangular 6.6.6 family: enumerate the physical bulk/side/corner incidence types symbolically, identify the two Appendix A.3 boundary labels under $\epsilon_c$, and write the exact matrices/maps $D_c,T_c,H$ with the compatibility statement $D_cz=0\Rightarrow HT_cz=0$. Check the source's distance-7 figure as a diagrammatic sanity check, not as a proof of the family.

Then state the boundary-classification lemma and review it before proceeding to T-LOGICAL. Do not jump to cluster extraction, an aggregation formula, numerical benchmarking, or a manuscript introduction.

## Historical initial-audit status

# STATUS.md

Last update: 2026-09-11.

## Current state

**Source audit and preliminary formulation completed. Central theorem unproved.**

The active milestone is the physical logical interpretation of one fixed-color stage-2 graph for standard triangular 6.6.6 patches with perfect syndrome measurements. This run implemented CODEX_INITIAL_PROMPT.md through mathematical preliminaries, explicit theorem formulation, and an adversarial review. It did not start the central proof.

## Work completed in this run

- Read the six authoritative state documents and the initial prompt using the corrected bibliography path.
- Checked the primary-source definitions and proof hypotheses listed below.
- Corrected the scaffold: Lee Appendix A.3 already retains two stage-2 boundary vertices. What remains unproved is their logical inequivalence and the full stabilizer/path correspondence.
- Transcribed Lee's two-stage equations, Eq. (10) projectors, and Claims 1–2 with the correct boundary-space residuals.
- Defined the physical CSS support complex and separated it from graph chains, hypergraph chains, and graph homology.
- Specified a physical-qubit-edge candidate split graph and an explicit bulk/side/corner incidence table to verify.
- Defined the fixed-stage-2 difference space $K_c$, exact physical-equivalence denominator $R_c$, and proposed endpoint-parity theorem T-LOGICAL.
- Recorded a conditional per-color swim definition and a hypothesis-by-hypothesis audit of Meister's construction.
- Performed a separate adversarial review pass by the same agent; no second-reviewer sign-off is claimed. The current unresolved findings are in REVIEW.md.
- Updated all six authoritative documents and retained five additional primary-source PDFs in refs/source_audit/.

## Sources actually inspected

Full version and location details are in [refs/REFERENCES.md](../refs/REFERENCES.md).

| Source | Checked material |
|---|---|
| Lee–Li–Bartlett, arXiv:2404.07482v2 / Quantum 9, 1609 | Secs. 2.1–2.2, Sec. 3 graph definitions and algorithm, Appendix A.1–A.3 including Claims 1–2; visual check of Fig. 2 and p. 23 boundary formula |
| Meister–Pattison–Preskill, arXiv:2405.07433v2 | Sec. II A–C; Sec. III A–B, Definitions 1, 7–9, Algorithms 1–2, Theorem 10, Lemmas 11–12, Theorem 13 and their proofs; Appendix B |
| Kesselring et al., arXiv:1806.02820v3 | Secs. 3.3–3.4, 4.1–4.3 and color-boundary discussion in Sec. 9; visual check of Fig. 6 |
| Delfosse, arXiv:1308.6207v1 | Secs. 3.1–3.2, 4.1–4.3, 5.2–5.3; hypergraph/CSS conventions, self-duality, projection chain map |
| Kubica–Yoshida–Pastawski, arXiv:1503.02065v1 | Theorem 1's scope; Sec. III A–B, Eq. (44), Figs. 8–10, Theorem 3 |
| Bombín–Martín-Delgado, quant-ph/0605138v3 | pp. 2–3, face/string operators, boundary termination and triangular logical string-nets |
| Kishi et al., arXiv:2602.03336v1 | Sec. II A–C, Fig. 1 and definition portions of Sec. III A–B; no later theorem imported |
| Lee–English–Bartlett, npj Quantum Information 12, 96 | Online publisher PDF pp. 1–2, introductory distinction of cluster heuristics and comparative weights |
| Local color-code-stim | README, triangular graph-construction entry point and stage-1/stage-2 matching methods at commit 0eb35935c1e5ff30ba3db9def30a9d35bca2f16d |

These are the inspected sections, not claims of complete cover-to-cover audits of every paper. The focused literature queries and their limits are recorded in the bibliography. No novelty claim is made.

## What is established versus proposed

**Established in the inspected literature:** the standard triangular code and physical logical representatives; Lee's graph definitions and qubit/stage-2-edge bijection; the Appendix A chain identification and syndrome-validity factorization; the two retained stage-2 boundary labels; Meister's actual cluster definitions and the stated scope of its surface-code/repetition-code results.

**Defined precisely in this project:** the physical support complex, fixed-stage-2 affine fiber, $D_c$, $K_c$, $R_c=K_c\cap T_c^{-1}(S_X)$, endpoint parity $\beta_c$, and the theorem skeleton comparing it with physical logical parity. The quotient is a definition, not a discovered geometric characterization.

**Still proposed:** exhaustive physical boundary-edge classification for the selected finite family; T-LOGICAL; any identification of the quotient with a particular cellular relative homology; cluster realization on the retained-boundary graph; and activation of the conditional swim definition as a justified color-code quantity.

## Blocking questions

1. Does the explicit finite-family incidence model realize the Appendix A.3 labels exactly at every side and corner, without introducing virtual physical qubits or collapsing parallel edges?
2. For every $z\in K_c$, does $\lambda_X(T_cz)=\beta_c(z)$ hold, and is a physical boundary-to-boundary path present?
3. Which physical stabilizers preserve the auxiliary constraints? Do non-c physical-face cells generate exactly $R_c$?
4. How can actual stage-2 growth data be realized on the split graph without assuming that boundary splitting and growth commute?
5. If an analytical transfer is later requested, do the valid-path, optimal-dual, metric and noise hypotheses in Meister's proof hold?

## Phase state

| Phase | State |
|---|---|
| 0. Scaffold | Complete |
| 1. Source audit and preliminaries | Complete for the inspected scope |
| 2. Research-object and theorem formulation | Complete as proposed statements with explicit open obligations |
| 3. Theory construction | Not started; next task below |
| 4. Paper-level theory | Deferred |
| 5. Broad motivation and positioning | Deferred |

The full research milestone is not complete: it requires the reviewed logical-path theorem and a justified per-color metric. No numerical experiments, prototype decoder, aggregation analysis, broad introduction, or paper/main.tex were produced.

## Exact next task

Carry out the symbolic boundary-incidence audit for the standard odd-distance triangular 6.6.6 family with $d\ge3$. Enumerate all bulk/side/corner incidence types, identify the two Appendix A.3 boundary labels under $\epsilon_c$, and state the concrete maps $D_c,T_c,H$ and their source-backed compatibility. Review that boundary-classification lemma before beginning T-LOGICAL. The next task is not another broad source search or an implementation benchmark.

## Verification and limitations

Checked the key equations against source text and rendered pages, reviewed map domains and proof statuses across the documents, and checked local links and retained source PDFs. The supplied Lee PDF generated extraction cross-reference warnings; the critical nested-boundary formula was visually verified. The npj direct download returned HTML and was discarded; its successfully read online passages are listed above.

Supporting notes remain historical inputs, and their aggregation/prototype proposals are superseded for the current milestone by AGENTS.md and PROJECT_DETAIL.md. The external decoder checkout was inspected without modifications.

## Historical initial-audit review

# REVIEW.md

Audit date: 2026-09-11. Reviewed objects: [NOTATIONS.md](../NOTATIONS.md), [PROJECT_DETAIL.md](../PROJECT_DETAIL.md), and the inspected-source ledger in [refs/REFERENCES.md](../refs/REFERENCES.md).

Review method: a separate adversarial pass by the same agent against the primary-source passages and the drafted formulation. This is not a second person's independent sign-off. No programmatic patch experiment or central-theorem proof was performed. The review tests the formulation and its dependencies, not the truth of the proposed theorem.

Labels: **[BLOCKING]** prevents a dependent claim from being used; **[OPEN]** needs further work; **[RESOLVED]** has a stated resolution; **[REJECTED]** identifies an invalid shortcut; **[REVISE]** requires a narrower statement. A resolved formulation issue does not mark its associated theorem proved.

## R-001 — Source boundary structure versus logical inequivalence

Severity: critical. Status: **[BLOCKING]**, with the source-availability question resolved.

Finding: contrary to the initial scaffold, Lee Appendix A.3 explicitly retains two stage-2 boundary vertices (p. 23):
$\{v_{\rm bdry}^c,\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}\}$.
Calling them “inequivalent” in the physical logical sense still needs a theorem.

Action: verify the physical-edge realization of the two source labels and establish T-LOGICAL. Definitions and exact source pointers now appear in NOTATIONS §4 and PROJECT_DETAIL §3. The source formula was checked visually, not only by PDF text extraction.

## R-002 — Opposite corner to c boundary

Severity: critical. Status: **[REVISE]**; theorem remains **[BLOCKING]**.

Finding: the informal “corner to opposite boundary” claim now has an explicit incidence table and target
$\lambda_X(T_cz)=\beta_c(z)$ for every $z\in K_c$. The physical interpretation is consistent with the inspected standard-patch figures, but no all-distance proof was completed.

Action: prove the table exhaustive for the standard odd-distance 6.6.6 family, including both corners on the c boundary, before proving the parity identity. A diagram at one distance cannot establish the family statement.

## R-003 — Graph cycles are not automatically physical stabilizers

Severity: critical. Status: **[BLOCKING]**.

Finding: the statement must distinguish the split graph from the merged graph. A cycle after boundary merging may lift to a chain connecting the retained boundaries. Even in the split graph, cycle triviality is currently a conclusion of T-LOGICAL, not a premise supported by Lee's validity proof.

Action: establish $R_c=\ker(\beta_c|_{K_c})$. If using non-c face cells, additionally establish the generating-set equality in PROJECT_DETAIL Eq. (P7). Do not use the claimed cycle result while proving it.

## R-004 — Unfolding is a different map

Severity: high. Status: **[RESOLVED]** as a formulation issue.

Finding: Kubica Theorem 3 describes attached layers and a local Clifford map. The draft now explicitly avoids identifying it with $T_c$ or with one stage-2 graph.

Resolution: NOTATIONS §5 and PROJECT_DETAIL §1.3 make unfolding background only. Any later proof using unfolding must supply a map correspondence and its boundary action before relying on it.

## R-005 — Projection and concatenated decoding

Severity: high. Status: **[RESOLVED]** as a notation issue.

Finding: Delfosse's degree-one projection is comparable to Lee's restricted-edge projection in the closed setting, not to the stage-2 bijection. His chain convention analyzes Z errors where this project analyzes X errors.

Resolution: explicit closed-setting map and Pauli-convention translation in NOTATIONS §5. No boundary theorem is imported from Delfosse Theorem 5.6, whose geometric assumptions differ.

## R-006 — Relative homology of a bare graph

Severity: critical. Status: shortcut **[REJECTED]**; cellular identification **[BLOCKING]** if used.

Finding: a graph with only a boundary-vertex subspace has no 2-cells. Its relative first homology does not identify nonzero face cycles with zero. Ordinary homology of the primal disk also omits the physical color-code support structure.

Resolution/action: use the exact quotient $K_c/R_c$ as the primary object. To use cellular language, specify the actual non-c physical-face attachments, check the relative chain-complex identity, and prove their image equals $R_c$. No artificial choice of cells may encode the desired conclusion without a physical justification.

## R-007 — Corners and degenerate patches

Severity: critical. Status: **[BLOCKING]**.

Finding: a corner between the non-c boundaries contributes the nested-pair stage-2 vertex; the two other corners belong to the c-boundary family. Treating every corner identically would produce the wrong partition. The d=1 patch does not have the same real-face incidence.

Action: audit every corner type algebraically for $d\ge3$, starting with the explicitly selected patch family. The distance-7 figure and Kesselring Fig. 6 are sanity checks only. Small-patch numerical checks are deferred, as the user excluded numerical experiments in this run.

## R-008 — Fixed stage-1 scope

Severity: high. Status: **[RESOLVED]** as a scope issue.

Resolution: all correction differences lie in one affine stage-2 fiber with fixed color and compatible first-stage prediction. T-LOGICAL concerns these differences. No aggregation, stage-1 confidence, or full comparative-gap statement is made. The later questions in the old supporting reports do not expand the active milestone.

## R-009 — Actual clusters and the boundary split

Severity: critical for D-SWIM. Status: **[BLOCKING]**.

Finding: Meister's Definitions 1, 7–8 require decoder growth radii; final correction components are insufficient. Moreover, shortest-path balls in a graph with merged boundaries need not be the same as balls in the split graph. The inspected local matching methods return predictions and weights, not dual radii.

Action: specify an actual stage-2 growth record and a boundary-aware realization on the physical-edge graph. Check metric, optimal-dual interpretation and correction support. Do not assume splitting commutes with growth or that a Tanner graph is the matching graph.

## R-010 — Representative gap versus posterior confidence

Severity: high. Status: **[RESOLVED]** in current claims; further analytical transfer deferred.

Finding: Meister Theorem 13 bounds the ratio of two particular error representatives. It is not a ratio of summed logical-class probabilities. Theorem 10's exact UF identity is for odd repetition codes.

Resolution: PROJECT_DETAIL §6 and the source table distinguish these statements. Neither is asserted for the color code. Any later likelihood theorem must verify the source noise model and combinatorial hypotheses, independently of topology.

## R-011 — General lattice-family scope

Severity: high. Status: **[RESOLVED]** by narrowing; generalization **[OPEN]**.

Resolution: standard simply connected triangular 6.6.6 patches, odd $d\ge3$, ordinary color boundaries, no twists or holes, one logical qubit. The physical check commutation and rank requirements are explicit. Arbitrary trivalent, three-colored patches are not silently included. Future 4.8.8/general-cellulation claims require another boundary audit.

## R-012 — Appendix A maps and inverse domain

Severity: high. Status: **[RESOLVED]** for the source audit.

Finding: $\pi_0^{(c)}$ removes c; $p_{\rm edge}^{(c)}$ and $p_{\rm vert}^{(c)}$ project distinct stage-2 vertex types. Appendix A.1 already identifies stage-2 1-chains with hyperedges. Claim 2 uses boundary-space residuals, not zero parity at virtual vertices.

Resolution: source Eq. (10), Claims 1–2 and Eqs. (11)–(13) are transcribed and translated. The basis inverse extends linearly without a new theorem. Inducing the desired physical logical isomorphism is still unproved. Hyperface incidence is typed explicitly, avoiding the source's ambiguous set typography.

## R-013 — Auxiliary boundary edges and fictitious qubits

Severity: critical. Status: **[BLOCKING]** for the concrete construction audit.

Finding: the augmented dual's edge between two boundary vertices becomes a stage-2 vertex. It is not itself a physical-qubit edge. Completing an exterior dual triangle as if it were a real data qubit, or retaining an auxiliary zero-cost matching connection between the two stage-2 boundaries, could make the proposed distance spuriously zero.

Action: retain exactly one stage-2 edge per physical qubit and no extra exterior-triangle qubit. Track the boundary-only restricted edge separately from the physical stage-1 prediction. Check edge multiplicities and all endpoint types in the next task.

## R-014 — Full physical stabilizer space is the wrong fixed-fiber denominator

Severity: critical. Status: unrestricted denominator **[REJECTED]**; generator characterization **[BLOCKING]**.

Finding: physical syndrome preservation does not imply preservation of the auxiliary c-edge parities. A physical stabilizer may move between stage-1 fibers.

Resolution/action: $R_c=K_c\cap T_c^{-1}(S_X)$ is the exact denominator. The definition makes the logical map injective once syndrome validity holds; it does not prove a nonzero image, connectivity, or endpoint-parity detection. Verify a geometric generating set separately.

## R-015 — Partial cluster coverage and zero values

Severity: medium. Status: **[RESOLVED]** at definition level.

Finding: zeroing an entire partly covered edge changes the metric. Assuming every grown cluster is logically trivial would also omit important ambiguous cases.

Resolution: use the metric interval realization and subdivide at coverage endpoints. Contract each connected component independently. A cluster joining both boundaries yields a candidate distance of zero, without a claim that a logical failure occurred. Concrete growth extraction remains R-009.

## R-016 — Exact hypotheses in Meister's proof

Severity: high for analytical transfer. Status: **[BLOCKING]** if invoking Lemmas 11–12 or Theorem 13.

Finding: Definitions 3–4 impose a disjoint-path notion of loop-free sets, and the proof uses optimal dual variables, valid competitor paths, and cluster intersections. These properties do not follow merely because a graph looks planar. “Acyclic” and the source's “loop-free” must not be interchanged without justification.

Action: check the actual correction/competitor representation and boundary-matching reduction. Either fit the source hypotheses or state and justify the needed extension. Keep the geometric definition separate from any likelihood bound while this remains open.

## R-017 — Stale project state and supporting reports

Severity: medium. Status: **[RESOLVED]**.

Finding: the initial root-bibliography paths were stale; source availability was overstated; the setup marked source maps as guessed; the supporting reports discussed aggregation and experiments outside this task.

Resolution: use refs/REFERENCES.md and an inspected-source inventory. Update all six authoritative documents. Supporting notes remain historical inputs; their proposed results and their old “resolved” labels are not adopted as proofs. No root-level duplicate bibliography or manuscript was created.

## Review disposition and next gate

The formulation now separates source validity, physical logical equivalence, geometric boundary classification, and cluster-transfer assumptions. It is ready for the boundary-incidence task, not for use as an established logical-path or confidence theorem.

Next review gate: inspect the finite-family boundary-classification lemma and the explicit physical/graph incidence maps. Verify that all corners are covered, no virtual qubit is introduced, the source Claim 2 applies to the chosen $D_c$, and the statement does not already assume T-LOGICAL. Only after that review should the logical parity proof begin.

## Historical Task 1 review (superseded by current Tasks 2–3 state)

# REVIEW.md

Audit date: 2026-09-11. Current reviewed objects:
[notes/note.tex](../notes/note.tex), the six state files, and the primary-source
passages listed in [refs/REFERENCES.md](../refs/REFERENCES.md).

Method: a separate adversarial pass after drafting, performed by the same
agent. This is not a second person's independent sign-off. The review
rederived the incidence cases symbolically, checked the claims against
the source passages, inspected notation domains, and checked the task's
stopping boundary. No finite patch simulation was used as proof.

**Disposition: Task 1 accepted within its explicitly defined family.
Task 2 and the physical logical-path theorem remain unproved.**
The original detailed review is retained in
[the deferred program](../notes/deferred_proof_program.md), with its
historical next-task statements superseded here.

## The nine requested critical questions

| Question | Finding and evidence |
|---|---|
| 1. Are classes defined from actual combinatorics? | Yes. Definition 3.1 fixes the qubits, face supports, edges and sides. Definition 3.2 defines incidence sets. Definition 5.1 and Proposition 5.3 use those sets, not presumed logical classes. |
| 2. Is any conclusion inferred merely from figures? | No. Lemma 3.3 enumerates both qubit residue types for arbitrary t≥1, checks red-side neighbors and one corner explicitly, and uses a verified color-permuting rotation for the remaining cases. Source figures are corroboration only. |
| 3. Are corners handled correctly? | Yes. A corner belongs to two physical sides, has one real face of the third color and two primal edges of the side colors. For fixed c, both c-side corners are in the missing-face class; the opposite corner alone is in the missing-edge class. |
| 4. Is the virtual node confused with a physical boundary? | No. §4.2 distinguishes the absent endpoint, the virtual matching vertex, and the physical boundary arc. Remark 5.4 rejects interpreting the classes as connected components of the boundary circle or merged graph. |
| 5. Is a surface-code property imported without proof? | No. Meister's distinct logical-boundary convention is background only. Neither terminal-type parity is equated to physical logical parity. |
| 6. Is the two-surface-code correspondence used too strongly? | No. §4.4 distinguishes Kubica's attached folded layers and local Clifford map from Lee's qubit-edge identification. Delfosse's restricted projection is also distinguished. |
| 7. Are epsilon and inverse uses well-defined? | Yes. Definition 4.2 has one labelled edge per qubit; parallel edges are retained. Lemma 3.3 excludes same-color multiplicities and the zero-real-endpoint case. The inverse is used on correction/edge subsets, not to prove a logical-path theorem. |
| 8. Does the result cover the intended family? | Yes, the whole explicitly defined standard triangular 6.6.6 family, every odd d≥3. The proof is symbolic in t. It does not cover arbitrary three-colored patches or infer that extension from one drawing. |
| 9. Are there hidden assumptions? | Odd distance, d≥3, ordinary color boundaries, no holes/twists, and perfect measurements are explicit in §§1 and 3. X/Z exchange does not imply noise independence. Uniform p<1/2 appears only when explaining ordinary candidate-weight selection. |

## Corrections made during this task

### R-018 — Latest-task scope versus earlier conditional constructions

**Resolved.** The initial state already contained proposed split-graph,
logical-parity, and swim definitions. The latest prompt expressly says to
stop before those steps. Their historical text and symbols were preserved
in notes/deferred_proof_program.md; active project files now report Task 1
and reserve later symbols without activating those constructions.
The TeX note contains only the ordinary graph and an exact next obligation.

### R-019 — Bulk-only edge-color rule and corner trivalence

**Resolved.** The initial registry described an edge color using two
separated real faces. Boundary edges have only one real face.
The corrected rule uses that face color and the physical side color.
The finite corners are degree two, despite the trivalent bulk description.
Definition 1.1 and Lemma 3.3 establish the applicable cases; NOTATIONS.md
records the correction. Omitting either qualification would invalidate a
corner proof.

### R-020 — Meaning of information lost by merging

**Resolved.** A claim that all terminal provenance is irretrievably lost
would be too strong: qubit labels preserve location and the tagged
surviving endpoint identifies which object is absent.
Proposition 5.5 states only that the single boundary incidence row records
the sum of the two type parities, not both coordinates. Its following
paragraph explicitly distinguishes that fact from recoverability using
the full labelled edge set.

### R-021 — Geometric classes versus topological components

**Resolved by narrowing.** The two types are well-defined and disjoint,
but the full physical boundary is connected and the ordinary graph
merges the endpoints. The phrases “two connected boundary components”
and “logically inequivalent terminals” are not used as proved results.
The exact physical side-plus-opposite-corner partition is proved;
logical inequivalence is a later theorem.

### R-022 — Overstating Lee's validity claims

**Resolved.** The first draft said Lee Claims 1–2 also established
second-round feasibility. Their displayed statements are conditional on
the two rounds returning feasible matchings. Removed that attribution.
The note gives the exact conditional validity argument and does not
claim a separate feasibility or connectivity theorem. Such a theorem
is not required for the Task 1 boundary classification.

## Updated disposition of the earlier findings

| ID | Current disposition |
|---|---|
| R-001: source labels / logical inequivalence | Source labels and their physical origins resolved by Remark 5.4 and Proposition 5.3; logical inequivalence still blocks later claims. |
| R-002: side versus opposite corner | Geometric classification resolved for all allowed distances by Lemma 3.3 and Proposition 5.3. The endpoint/logical parity identity is still unproved. |
| R-003: cycles versus stabilizers | Still blocking any later cycle-triviality claim; not used in Task 1. |
| R-004: unfolding map | Resolved as a source distinction, restated in §4.4; no decoder-map correspondence claimed. |
| R-005: Delfosse projection | Resolved as a map/Pauli-convention distinction; no unverified boundary extension imported. |
| R-006: bare graph relative homology | Shortcut remains rejected; any later cellular identification needs a specified complex and physical stabilizer image. |
| R-007: corners and d=1 | Resolved for the selected d≥3 family by the explicit corner proof. At d=1 the real-face incidence disappears, so that excluded case cannot be inserted into the theorem. |
| R-008: fixed-stage scope | Retained for the later logical-path problem. Ordinary three-candidate correction selection is explicitly required background, not a new soft-output combination. |
| R-009: actual growth and splitting | Still blocking later growth transfer; no growth data or split graph used here. |
| R-010: representative versus posterior gap | Source distinction retained in REFERENCES and historical program; no probability bound asserted here. |
| R-011: lattice-family scope | Resolved by explicit standard-family coordinates; generalization remains open. |
| R-012: Appendix A maps | Source map audit retained. The ordinary real-row maps use new symbols delta_negc and delta_c to avoid conflating them with the deferred split-graph D_c. |
| R-013: fictitious qubits / auxiliary edges | Resolved for the ordinary graph: exactly one labelled edge per physical qubit, no exterior-triangle qubit, no extra physical matching shortcut. Must be checked again for any later construction. |
| R-014: fixed-fiber stabilizer denominator | The unrestricted quotient shortcut remains rejected; the actual generator characterization is deferred and unproved. |
| R-015: partial cluster coverage | Historical metric caution retained; no metric is defined in Task 1. |
| R-016: Meister proof hypotheses | Still blocking any analytical transfer; no such theorem is invoked for the color graph. |
| R-017: stale paths and note authority | Resolved again after the directory change: prompts live under prompts/, bibliography under refs/, and notes/note.tex is the reviewed derivation rather than a scratch placeholder. |

## Review limits and next gate

No unresolved issue was found in the stated ordinary-graph classification.
That is a bounded review conclusion, not external peer-review certification.
The coordinate realization deliberately excludes 4.8.8 patches, holes,
twists, Pauli boundaries and circuit-level detector graphs; a new local
incidence audit is necessary before any such extension.

Next gate: review Research Task 2's actual distinct-terminal realization,
preservation of physical edges, recovery under identification, and
connectivity. Task 1 supplies the two input edge subsets, not a proof
of that construction or of logical inequivalence. Do not proceed directly
from this acceptance to a swim-distance or relative-homology theorem.

## Historical Tasks 2–3 review (before the Task 4 proof)

# REVIEW.md

Audit date: 2026-09-11. Reviewed [notes/note.tex](../notes/note.tex),
the six state files, and Lee Appendix A.1–A.3 against the primary text.

Method: a separate adversarial pass after the Tasks 2–3 derivation, by
the same agent. This is not external peer-review certification.
The pass rechecked the Task 1 dependency, every endpoint type, the
all-distance connectivity descent, chain-map domains, matching parity
conditions, and the precise boundary between syndrome and logical claims.

**Disposition: Tasks 2 and 3 accepted within the stated family and
matching convention. Task 4 remains unproved.**
Initial and Task 1 review details are preserved in
[the historical program](../notes/deferred_proof_program.md); current
dispositions below supersede their earlier next-task statements.

## The 13 requested adversarial checks

| Check | Finding and evidence |
|---|---|
| 1. Is the graph defined without a figure? | Yes. Definition 6.1 fixes the tagged vertex set and the endpoints for each of the three possible local incidence cases. |
| 2. Is every original edge represented once? | Yes. Both edge sets are labelled by the same physical Q; q_{c,1} is bijective. No edge connects the two terminals directly. |
| 3. Are boundary classes disjoint and exhaustive? | Yes. Task 1 Proposition 5.3 partitions exactly the formerly dangling edges into missing-face and missing-edge sets; the other edges retain both real endpoints. |
| 4. Are corners consistent? | Yes. The two corners on the c side attach to b_c^0; the single opposite corner attaches to b_c^1. Both physical side memberships of each corner are retained in its interpretation. |
| 5. Is the forgetful map well-defined? | Yes. It identifies just the two virtual vertices, fixes real vertices, and bijects edge labels. Lemma 6.5 checks every endpoint case and proves incidence compatibility. It is vertex identification, not contraction of an added edge. |
| 6. Is the physical-qubit bijection preserved? | Yes. Definition 7.1 inverts the resolved edge basis. It never creates a qubit for an auxiliary source edge or an exterior triangle. |
| 7. Is the inverse applied on the right domain? | Yes. The resolved map is T_c and the ordinary alias is T_c^ord; T_c=T_c^ord q_{c,1}. The Pauli map has its own symbol so P_X keeps its physical-support domain. |
| 8. Are artificial nodes treated as checks? | No. rho_c deletes both terminal rows. Real edge vertices carry auxiliary c-edge parity; they are not physical face checks either. Lambda_c explicitly translates those auxiliary coordinates. |
| 9. Is syndrome compatibility exact? | Yes. Lemma 7.4 proves H T_c=Lambda_c D_c for every binary chain using the local non-c-face partition, with all corner incidences included. It does not assert the ill-typed equality H T_c=D_c. |
| 10. Is Task 4 silently assumed? | No. The proved cycle/path consequence is only zero syndrome. Logical nontriviality, cycle-stabilizer triviality and R_c=ker beta_c occur only as the unproved Open issue 8.1. |
| 11. Is this all-distance rather than one drawing? | Yes. Task 1's two-residue incidence proof is rechecked; Lemma 6.3 descends arbitrary red face coordinates (1+3m,2+3n), and rotation covers the other colors. |
| 12. Are there small-distance or corner exceptions? | The t=1/d=3 case is included in the descent base case. Its unique opposite-corner edge also gives the explicit cost-1 versus cost-2 example when a terminal is wrongly constrained even. d=1 is excluded because its missing-object incidence differs. No counterexample was found within the defined family. |
| 13. Is global unfolding used too strongly? | No. Kubica's local Clifford map and attached layers remain distinct; Delfosse's restricted projection is not the resolved support inverse. No surface-code logical theorem is imported. |

## R-023 — “Topologically inequivalent” was not an input theorem

**Resolved by precise scope.** Task 1 proves two geometric incidence
classes, not their physical logical inequivalence. The Tasks 2–3 prompt
calls them inequivalent while reserving their logical correspondence
for Task 4. Section 6.1 states the distinction explicitly and constructs
the graph from the proved combinatorial classes. No Task 4 conclusion
is used as a premise. Their logical interpretation remains open.

## R-024 — Typed inverse and Pauli-map domains

**Resolved.** Keeping the same unqualified inverse on two graph domains
would hide a change of endpoint structure. The adopted convention is
tilde-epsilon on resolved edges, T_c on resolved chains, and T_c^ord
on ordinary chains, related through the edge quotient. P_X still takes
physical supports; script-P_{X,c} takes resolved chains. Source Appendix A
already supplies the linear basis identification, so no unsupported
inverse-existence result is invented.

## R-025 — Boundary deletion is not the full physical syndrome map

**Resolved.** D_c contains both real c-face syndrome and the c-edge
parities supplied by stage 1. Lambda_c is necessary to obtain all
physical face checks. Its non-c rows sum the primal c edges of each
real face. Lemma 7.4 proves the exact factorization on every chain.
The two terminal counts are graph incidence data only.

## R-026 — Splitting does not unconditionally preserve MWPM behavior

**Resolved with an explicit hypothesis.** Proposition 6.6 proves
identical feasible sets and costs only for the same physical weights
with both terminal rows omitted. At d=3, constraining the opposite-corner
terminal even changes the single-red-face syndrome optimum from one to
two. Thus an arbitrary matching-library boundary setting is not covered.
The adopted workflow keeps ordinary decoding on the merged graph.
No transfer of distances, tie-breaking, duals or growth data is claimed.

## R-027 — Walk supports and Pauli phases

**Resolved.** A walk maps through traversal multiplicity modulo two,
not through its set of visited edges. Repeating an edge twice cancels.
Pauli multiplication is exact in the pure X or pure Z sector; no mixed
Pauli phase or statistical-independence claim is made.

## R-028 — Source augmentation versus physical stage-1 edges

**Resolved.** Lee's retained-boundary chain-space direct sum includes a
virtual restricted edge between the two non-c boundary labels.
That virtual source edge is the provenance of b_c^1, not an extra
physical stage-2 edge. NOTATIONS §3 now states the augmented convention
explicitly. The real-row proof uses only physical E_c and Q.

## Updated earlier findings and remaining blockers

| Earlier issue | Current disposition |
|---|---|
| R-001 / R-002: labels, physical side/corner interpretation | Geometric classification and resolved realization complete; physical logical inequivalence still belongs to Task 4. |
| R-003: graph cycles versus stabilizers | Still blocking a stabilizer-triviality claim. Proposition 7.5 proves zero physical syndrome only. |
| R-004 / R-005: unfolding and projection distinctions | Retained and explicit; neither supplies the missing decoder-specific theorem. |
| R-006: bare-graph relative homology | Shortcut remains rejected. No two-cell model or homological equivalence is defined. |
| R-007 / R-011: corners and family scope | Resolved for the explicit d≥3 ordinary-boundary 6.6.6 family; other families remain unaudited. |
| R-008 / R-014: fixed stage-1 fiber and denominator | K_c, R_c=K_c intersect T_c^{-1}(S_X), and the Task 4 target are now active definitions. Generator and cycle characterizations remain unproved. |
| R-009 / R-015 / R-016: growth, partial metric coverage, source bounds | Still deferred; matching optimum equivalence supplies none of these transfer results. |
| R-010: representative versus posterior quantities | Source distinction retained; no probability bound or soft-output definition appears here. |
| R-012 / R-013: source maps and fictitious qubits | Resolved for Tasks 2–3 by typed maps, exact boundary identity and one edge per qubit. |
| R-017: paths and document authority | Prompt listing now includes Tasks 2–3; the existing note remains the mathematical source rather than introducing an unneeded tex/ tree. |
| R-018: initial conditional definitions versus authorization | Latest prompt now authorizes the resolved graph and chain map. Only those objects and the Task 4 statement are activated. Swim/cellular proposals stay historical. |
| R-019: edge coloring and corner trivalence | Rechecked, no further correction needed. The boundary rule uses the physical side color and one real-face color. |
| R-020 / R-021: merging information and geometric classes | Retained: edge labels preserve provenance; a single boundary row stores only the sum; logical inequivalence is not a proved classification. |
| R-022: conditional source validity versus feasibility | Lee Claims 1–2 remain conditional. A separate project connectivity argument now proves real-row feasibility; it is not attributed to those claims. |

## Review limits and next gate

No unresolved dependency was found in the stated graph construction,
matching compatibility under its explicit conditions, or physical
syndrome map. The proof does not generalize automatically to 4.8.8,
holes, twists, Pauli boundaries or circuit-level detector graphs.

Next gate is Task 4: prove or refute the exact logical-parity identity
of Open issue 8.1 on K_c, with the correct physical-equivalence
denominator. In this run that identity was stated only. Its proof,
cycle-stabilizer classification, relative homology and soft output
were not attempted.
