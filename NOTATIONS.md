# NOTATIONS.md

Last audit: 2026-09-19. Source keys and edition-specific locations are in [refs/REFERENCES.md](refs/REFERENCES.md). This registry separates source definitions, direct translations, and proposed objects. Research Tasks 1–7 are established in notes/note.tex, including the cluster metric and certified fixed-stage-2 representative bound. Deferred initial proposals are preserved in notes/deferred_proof_program.md.

## 1. Conventions and physical code

### BP fallback X/Z mechanism weights (2026-09-29)

For BP fallback only, `q[e]` is the unclipped global mechanism posterior,
`p[j]` its independent-XOR aggregation into X/Z DEM mechanism `j`, and
`w[j] = -log(p[j])`. The effective probability `p_eff[j] = p[j]/(1+p[j])`
encodes this weight for the existing log-odds API. It is a surrogate prior,
not the projected posterior itself. This conversion precedes color/stage
decomposition and follows global-to-X/Z aggregation. Numerical regularization
floors the effective probability at `1e-14`. Global BP weighting version is 3.

### Canonical YAML ensemble SWIM score (2026-09-27)

For each generated concatenated-matching candidate `a`, `phi_a` is the
original stage-2 growth-cluster terminal distance evaluated on that
candidate's stage-2 syndrome with the unmodified matching prior. Let `L_a`
be the observable parity of its generated correction and `L_*` the parity of
the hard correction finally selected by the decoder. The canonical YAML
`swim_distance.parquet` value is `min{phi_a : L_a = L_*}`. This is distinct
from the historical decoder `selected_swim_distance`, which is `phi` of the
single hard-selected candidate. The decoder exposes the new reduction as
`class_min_swim_distance`. In perturbation, the base-prior stage-2 matcher
is run on the perturbed member's stage-1 hypothesis to obtain `phi_a`.
For a closed `rounds=d` circuit memory, `phi_a` uses the existing completed
effective stage-2 graph: base-prior growth radii, residual edge weights and
the minimum odd-logical-support path in its cut or logical cover. The
generated candidate's original-DEM correction still supplies `L_a`.
Both metrics are soft-output proxies and have no LLR claim.

### Circuit DEM-Y signed gap (2026-09-19)

The new circuit metric uses local notation in `notes/support/CIRCUIT_DEM_Y.md`:
`H_all,o_all` describe ordered error instructions of the decoder's separated
`dem_xz`; `R_Z,C_Z` are explicit sector row/column maps and `H,o` their
restrictions. `E=E_all[C_Z]`, `a_j=(1-2E_j)log((1-p_j)/p_j)` and
`S_DEMY=min_{L in Y_DEM} a^T L`. Columns are DEM mechanisms, not physical
qubits. Outside-sector corrections are frozen. `G_c^0` has base first
operations; `G_c^1` has base and one-temporal-link enriched tail operations.
`U_c(v)` is the offline all-suffix fault union; `J` is the exact root/first
XOR cap. `q_c` includes the first operation's observable parity; tail parity
is `lambda_c=q_c xor oP_c`. `b(S)=a(S)-2a_i 1_{i in S}` folds root i.
These symbols do not redefine the historical physical/stage-2 objects.


### Monotone-Y signed gap (2026-09-19)

Simulation columns `ordinary_monotone_y_gap` and `comparative_monotone_y_gap`
are S_Y evaluated on each decoder's final physical correction, paired with
`ordinary_logical_error` and `comparative_logical_error` respectively.
`forced_gap` retains comparative failures and its existing decoder definition.
Version `monotone_y_signed_v1`; root IDs are canonical physical column indices,
not circuit qids or selected decoder colors. Template IDs reference the
archived metric's geometry construction. The existing matched-retention and
reduction conventions below apply to these named scores as well.

The separately authorized monotone-Y prompt uses local notation in
`external_libs/color-code-stim-monotone-y/docs/monotone_y_signed_gap.md`:
`a_q(E)=(1-2E_q)w_q`, physical check matrix `H_Z`, physical logical vector
`ell_Z`, and `Delta_E=min_{H_Z L=0, ell_Z L=1}[W(E xor L)-W(E)]`.
`Y_right` is the specified one-junction, three-monotone-arm support family;
`S_Y` is its minimum signed cost. `Gamma=m_1-m_0` compares exact physical
class minima relative to E; `eta=W(E)-m_0` and `rho_Y=S_Y-Delta_E` give
`S_Y=Gamma-eta+rho_Y`. These are distinct from SWIM and decoder logical_gaps.
Locally `B=3(d-1)/2`, `(u,v)=(B-y,(x-2y)/4)`, and
`(h_r,h_g,h_b)=(B-u,v,u-v)`. The local DAG distances `D_c` and pair graphs
`G_c` do not redefine the historical stage-2 matrices/graphs below.

### Post-selection quantitative comparison (2026-09-19)

`reduction_rate = 1 - residual_ler / baseline_ler`, where the baseline is
the same hard decoder before selection. `reduction_factor = baseline_ler /
residual_ler`. The comparison ratio is path-gap residual LER divided by
forced-gap residual LER, at matched retained counts. A zero denominator is
undefined, not evidence of equality. `matched_abort` splits only boundary
score ties by outcome-independent shot ID; `whole_ties` uses the most
selective attainable threshold within the abort budget. The latter's actual
abort rates may differ across metrics. A configurable 1.25 ratio margin is a
descriptive convention, not a proved bound or a statistical equivalence test.

### Final-correction monochromatic path gap (2026-09-18)

Experiment columns (2026-09-19): `ordinary_path_gap` and
`comparative_path_gap` evaluate this phi on their respective FINAL corrections.
Their failure labels are respectively `ordinary_logical_error` and
`comparative_logical_error`; `forced_gap` keeps the latter label and its
existing definition. `{decoder}_distance_{c}`, `{decoder}_phi_{c}` and
`{decoder}_correction_weight` record D_c(E), phi_c(E) and W(E).
The hard-selected color and path-gap minimizing color are distinct fields.

The separately authorized `prompts/codex_monochromatic_path_gap_prompt.md`
defines a new heuristic in `color_code_stim.metrics`, distinct from SWIM.
Within that API/document only, E is the FINAL physical X correction,
`Q_c(a)` is a suppressed edge's immutable singleton/pair physical support,
`s_c` is the opposite corner, and `t_c` is the boundary missing c checks.
`D_c(E) = dist_{sum_{q in Q_c(a) minus E} w_q}(s_c,t_c)`,
`W(E)=sum_{q in E} w_q`. Under the 2026-09-19 overlap revision, L_c is
the returned nonnegative-Dijkstra path support, O_c(E)=W(E intersect L_c),
`phi_c(E)=D_c(E)-O_c(E)=W(E symmetric_difference L_c)-W(E)`, and
`phi(E)=min_c phi_c(E)`, with rgb ties. These local symbols do not redefine
the historical incidence matrix D_c, syndrome s_c, or certified SWIM phi_c.
`overlap_weight_by_color` / `{decoder}_overlap_{c}` store O_c(E). Version
`path_overlap_v2` replaces the historical `global_subtraction_v1` formula
D_c(E)-W(E); saved legacy data retain that original meaning. Path ties keep
igraph's returned witness without optimizing the postprocessed score.
Negative scores remain valid. Canonical physical positions sort stable Tanner
qids; DEM error-only columns have a separately verified permutation.
Exact d=3 diagnostics distinguish signed `Delta_class`, signed `Delta_corr`,
within-class suboptimality and nonnegative optimal-class gap. No posterior
or universal full-gap bound is asserted.

### Comparative correction-origin analysis (2026-09-18)

`weight_class_{l}_{c}` stores the existing comparative decoder weight `w[l,c]`
for logical class `l=0,1` and restricted color branch `c=r,g,b`.  The
`baseline_logical_class` is the class of the global minimum, and
`forced_logical_class` is its binary complement.  `baseline_color` and
`forced_color` are the rgb-order minimizing colors inside those classes;
`forced_gap = forced_weight - baseline_weight`.  “Baseline” here means the
class selected by comparative decoding, not the ordinary decoder branch.
Class ties use class 0 and color ties use r then g then b, matching the existing
class-major/rgb-minor `argmin`.  These are empirical provenance fields, not new
soft-output definitions.

### Empirical three-color output-selection strategies (2026-09-16)

For saved per-shot circuit-level values
`(swim_distance_r, swim_distance_g, swim_distance_b) = (phi_r,phi_g,phi_b)`,
the notebook `notebooks/circuit_level_swim_selection_strategies.ipynb` uses:

- `selected_color`: `phi_sel = phi[ordinary_selected_color]`, the implemented
  ordinary decoder output already stored as `selected_swim_distance`;
- `minimum`: `phi_min = min(phi_r,phi_g,phi_b)`;
- `maximum`: `phi_max = max(phi_r,phi_g,phi_b)`;
- `mean`: `bar_phi = (phi_r+phi_g+phi_b)/3`.

The latter three are post-hoc empirical analysis strategies, not new decoder
outputs or theorem-level aggregations. Every strategy uses the same stored
ordinary hard decision and `ordinary_logical_error` label. Optional
`round_digits` acts after aggregation and before grouping or thresholds; it
does not change saved values.

### Surface-code companion conventions (2026-09-16)

`surface_code_test` stores `swim_distance` and `complementary_gap` in unrounded
natural-log matching costs. Its `class_weight_0` and `class_weight_1` are the
minimum weights with the ordinary surface matching graph's observable parity
forced to 0 and 1. `complementary_gap = abs(class_weight_1-class_weight_0)`;
both surface scores use `ordinary_logical_error` on the same physical shots.
This is distinct from the color-code experiment's comparative-decoder alias.
Display dB means multiplication by `10/ln(10)`, without integer rounding.
Surface `rounds` counts explicit `SO_example.SE_round` calls; the X-initialization
gadget contains an additional extraction. No new theorem or certification is
introduced. Existing balanced label-gauge algebra is checked on the actual graph.

### Circuit implementation conventions (2026-09-16)

The closed-memory implementation uses the existing `D`, `L2`, `b_star`,
`bar omega` and `phi_c^circ` definitions below. `method=two_boundary` means
the internal balance gate passed; `logical_cover` means the exact same-base-
vertex opposite-sheet fallback. `status=no_opposite_class` means infinity
and no witness, with method/topology absent, never a fabricated boundary split.
`swim_coverage_convention=original_completed_labelled_stage2_graph_v1`
specifies coverage on the original graph before cut/cover transport.
The unchanged `sparse_blossom_final_defect_metric_balls_v1` growth export uses
natural-log-weight units and remains uncertified. `selected_swim_distance`
is exactly the ordinary hard decoder's selected branch. Stable IDs refer to
the effective DEM hash, color and pre-sort retained column; they are not
physical gate-fault locations. Circuit witnesses contain original H2 columns,
not the Phase-1 physical-qubit bijection.

### Circuit-level extension (2026-09-12)

The circuit-level symbols below apply only in the new circuit-level part of
`notes/note.tex` (source `notes/support/circuit_level_theory.tex`). They do not
replace the static symbols in the subsequent historical registry.

- `E_0`, `B`, `L`: flattened original DEM mechanism IDs, detector-incidence
  matrix, observable/frame-change matrix. A separator groups components of
  one event; it does not declare independent faults.
- `A_rec`, `P_det`, `P_obs`: fault-to-measurement-flip map and measurement
  parity selectors, so `B=P_det A_rec`, `L=P_obs A_rec`.
- `E_sep`, `E_c^circ`: full-target-compressed separated mechanisms and
  retained stage-2 mechanism IDs. `A_e` and `N_e` are the physical c and
  non-c detector target sets of a separated mechanism, respectively.
- `V_c^phys`, `V_c^virt`, `V_c^real`: physical c detector rows, constrained
  stage-1 virtual rows, and their tagged union. `v_N` labels a nonempty
  restricted target set; `Q_virt` maps stage-2 mechanisms to these rows.
- `D_c^circ`, `L_c^circ`, `omega_c`: real stage-2 detector map, observable
  map, and inherited nonnegative mechanism cost. Locally `D,L_2,w` abbreviate
  them; `L_2` is a matrix, never Lee's lattice `mathcal L_c^*`.
- `K_c^circ=ker D_c^circ`, `R_c^circ=ker D_c^circ intersect ker L_c^circ`,
  `mathcal Q_c^circ=K_c^circ/R_c^circ`. The circuit denominator means frame
  triviality, not a proved static-face stabilizer group.
- `G_c^bullet`: labelled multigraph completing every half-edge at one
  artificial node `b_*`; a zero-detector mechanism is a labelled loop there.
  `lambda_c(e)=L_c^circ[e]` (one observable). This extends the Phase-1
  logical functional to edge labels; they agree on the controlled limit's kernel.
- `hat G_c`, `(v,a)`: logical binary cover and sheet index `a in F_2`.
  `g` is a real-vertex gauge; equivalent labels differ by `g^T D`.
- `bar omega_c`, `phi_c^circ`: transported uncovered interval cost and
  `min_{Dz=0,L_2 z=1} bar omega_c(z)`, with the empty minimum `+infinity`.
- `U_R -> F_2^{E_c^circ} -> F_2^{V_c^real}`: algebraic complex with the
  first map a chosen basis inclusion of `R_c^circ`. It asserts no local cells.
- `Sigma_L`: a specified correlation cochain, or a separately certified
  geometric representative of it. `J_fault` maps effective mechanisms to a
  specified physical fault complex only when its detector/logical identities hold.
- `I_T`, `p_T`, `i_T`, `h_T`: cellular time interval, augmentation, inclusion
  at time zero, and path homotopy in the ideal tensor-product comparison.
- `W_{c,base}^circ`, `W_{c,opp}^circ`: baseline and opposite-frame minimum
  costs in the same nonempty real stage-2 fiber. A certified inequality
  requires exactly the Phase-1 nonnegative optimal odd-cut certificate.
- `H_rest`, `Q_virt`, `Lambda_c^circ`: restricted incidence, virtual-row
  incidence, and `(a,v) -> (a,H_rest v)`, so the retained separated
  detector map is `Lambda_c^circ D_c^circ`.
- `P_comp`: XOR projection from independent same-full-target mechanisms
  to compressed mechanisms; provenance membership is not its inverse.
- `G_int`: subgraph on constrained vertices, excluding matching half-edges
  and zero-detector mechanisms. Its label balance is the gate for the
  two-terminal cut theorem. `b_*` is never a measured detector.


All vector spaces are over $\mathbb F_2$. A subset denotes its indicator vector; addition is symmetric difference. A set of cells is written $\Delta_i$, its span $C_i$. Use $\subseteq\Delta_i$ for a support, not $\in\Delta_i$; the latter denotes one basis cell. Orientations do not affect binary incidence.

**Lee source notation:** $\mathcal L_{2D}$ (called $\mathcal L$ in Appendix A), $\Delta_i(\mathcal L_{2D})$, colors $c\in\{r,g,b\}$, and $\Delta_i^{(c)}$ for colored edges or faces ($i=1,2$). An interior primal edge has the color absent from the two real faces it separates. An edge on a physical boundary of color a, incident to a single real face of color b, has the third color (a and b differ); this agrees with the color of the faces it connects in the shrunk-lattice picture. Primal data vertices have no color.

**Project physical notation:**

- $Q=\Delta_0(\mathcal L_{2D})$, $E=\Delta_1(\mathcal L_{2D})$, $F=\Delta_2(\mathcal L_{2D})$, $A=\mathbb F_2^Q$, $U=\mathbb F_2^F$.
- $H:A\to U$, $(Ha)_f=\sum_{q\in f}a_q$, is the physical face-check incidence matrix. For the ordinary color-boundary CSS code, $H_X=H_Z=H$.
- $J=H^\mathsf T:U\to A$ sends a physical face to its qubit support. $HJ=0$ is the CSS commutation condition, required of the chosen patch.
- $S_X=\operatorname{im}J$ is a binary support space, distinct from the Pauli stabilizer group $\mathcal S$. $Z_X=\ker H$ and $\mathcal L_X=Z_X/S_X$ describe zero-syndrome X supports and their logical classes. For the standard one-qubit triangular patch, $\dim\mathcal L_X=1$.
- $S_f^X=\prod_{q\in f}X_q$ and $S_f^Z=\prod_{q\in f}Z_q$ are the real-face Pauli checks; $q\in f$ denotes incidence.
- $P_X(a)=\prod_{q\in Q}X_q^{a_q}$ and $P_Z(a)=\prod_{q\in Q}Z_q^{a_q}$. Equality of $a$ is stronger than equality modulo $S_X$; logical equivalence is used for zero-syndrome supports or differences of corrections with the same syndrome.
- Fix a physical logical-Z support $\ell_Z\in\ker H\setminus S_X$. Then $\lambda_X(a)=\ell_Z^\mathsf Ta$ is the commutation parity of $P_X(a)$ with that representative. On $Z_X$ it detects the logical-X class. For nonzero-syndrome corrections, compare $\lambda_X(a+a_0)$ to a chosen same-syndrome reference $a_0$.
- $\Gamma_c$ denotes the physical boundary arc of color $c$; $q_{c_1c_2}$ denotes the standard corner where $\Gamma_{c_1}$ and $\Gamma_{c_2}$ meet. These are project labels, not graph vertices.

We work in the X-error sector, with measured Z-check syndrome $\sigma_Z=Ha$. Exchanging X and Z gives the same algebra for this CSS code; it does not assert statistical independence under arbitrary noise. Initial stochastic assumptions, when needed, are independent X errors with $0<p<1/2$.

## 2. Lee's graph and hypergraph spaces

**Source:** [Lee2025], Sec. 3, Definitions 1–2, and Appendix A.1.

- $\mathcal L^*$: augmented dual triangulation when boundaries are present. Its real vertices correspond to physical faces, its physical triangles to data qubits, and a dual edge joins faces separated by a primal edge.
- Its ordinary cellular maps are $\partial_1^*\{u,v\}=u+v$ and $\partial_2^*t=\{u_r,u_g\}+\{u_g,u_b\}+\{u_b,u_r\}$ for a triangle $t$. These map dual edges to vertices and dual triangles to edges. They are distinct from the hypergraph map that sends one physical qubit directly to three syndrome vertices.
- $\mathcal H$: decoding hypergraph. A physical qubit $q$ gives a hyperedge $h_q=\{u_r(q),u_g(q),u_b(q)\}$. The $u_c$ are dual face vertices, completed by colored boundary labels when a face is missing.
- In the boundary-free source complex, $C_0(\mathcal H)$ is spanned by dual vertices, $C_1(\mathcal H)$ by physical hyperedges, and $C_2(\mathcal H)$ by hyperfaces (incident hyperedges around a dual vertex). Write $\partial_1^\mathcal H h_q=u_r+u_g+u_b$ and $\partial_2^\mathcal H h_f=\sum_{q\in f}h_q$.
- For the patch, physical stabilizer generators are **only real faces**. Do not add a check or data qubit for a virtual boundary face/triangle. Deleting the virtual syndrome coordinates identifies the physical maps with $H$ and $J$ above.

Let $c_1,c_2$ be the other colors.

**Stage 1:** $\mathcal L_{\neg c}^*$ is the restricted lattice. In the main-text merged convention its vertices are the physical $c_1,c_2$ faces and $v_{\rm bdry}$. Its edges are in bijection with primal $c$ edges under
\[
\epsilon_{\neg c}:\Delta_1^{(c)}(\mathcal L_{2D})\longrightarrow
\Delta_1(\mathcal L_{\neg c}^*).
\]
A primal $c$ edge separating two real faces gives an edge between those faces; one incident to only one face gives an edge to the matching boundary.

**Stage 2:** $\mathcal L_c^*$ is the monochromatic lattice. Its main-text vertices are the disjoint types of physical $c$ faces, primal $c$ edges, and $v_{\rm bdry}$. For each $q$,
\[
\epsilon_c:Q\longrightarrow\Delta_1(\mathcal L_c^*)
\]
joins its incident $c$ face to its incident $c$ edge, or the one present object to $v_{\rm bdry}$ if the other is absent. Edges retain qubit identities, including parallel edges.

Appendix A identifies $C_1(\mathcal L_c^*)\cong C_1(\mathcal H)$ already. The ordinary-domain alias
\[
T_c^{\rm ord}:\mathbb F_2^{\Delta_1(\mathcal L_c^*)}\longrightarrow A,\qquad
T_c^{\rm ord}(\epsilon_c(q))=q
\]
is the linear physical-support version of $\epsilon_c^{-1}$. The canonical $T_c$ below is reserved for the resolved graph. This extension needs no new inverse-existence theorem. It is **not** a claim about homology or stabilizers. Task 3 defines the resolved-domain version of this same support identification in §6 below. The logical-path interpretation is proved in Task 4 (§7 below).

## 3. Appendix A projectors and decoding equations

**Source:** [Lee2025], Appendix A.1, Eq. (10). The superscript in $\pi_0^{(c)}$ means *remove color c*, not *keep color c*:
\[
\pi_0^{(c)}u=\begin{cases}0&u\text{ has color }c,\\u&\text{otherwise}.\end{cases}
\]
In the source augmented convention (including the virtual restricted edge between the two non-c boundary labels),
\[
C_0(\mathcal L_c^*)=
C_1(\mathcal L_{\neg c}^*)\oplus\operatorname{im}(1-\pi_0^{(c)}).
\]
The two source projectors onto these summands give
\[
p_{\rm edge}^{(c)}=P_{C_1(\mathcal L_{\neg c}^*)}\partial_1^{\mathcal L_c^*},
\quad
p_{\rm vert}^{(c)}=P_{\operatorname{im}(1-\pi_0^{(c)})}\partial_1^{\mathcal L_c^*}.
\]
On $h_q$, they give $\{u_{c_1},u_{c_2}\}$ and $u_c$, respectively. Their sum is the stage-2 incidence map, with values in distinct summands. Lee's identity used in Claims 1–2 is
\[
\partial_1^\mathcal H
=p_{\rm vert}^{(c)}
+\partial_1^{\mathcal L_{\neg c}^*}p_{\rm edge}^{(c)}.
\tag{N1}
\]

The exact main-text set notation is
\[
\widetilde E_{\rm pred}^{(c)}
=\operatorname{MWPM}(\sigma_Z^{(c_1)}\cup\sigma_Z^{(c_2)};
\mathcal L_{\neg c}^*,v_{\rm bdry}),\qquad
E_{\rm pred}^{(c)}=\epsilon_{\neg c}^{-1}(\widetilde E_{\rm pred}^{(c)}),
\]
\[
\widetilde V_{\rm pred}^{(c)}
=\operatorname{MWPM}(\sigma_Z^{(c)}\cup E_{\rm pred}^{(c)};
\mathcal L_c^*,v_{\rm bdry}),\qquad
V_{\rm pred}^{(c)}=\epsilon_c^{-1}(\widetilde V_{\rm pred}^{(c)}).
\tag{N2}
\]
Unions here combine disjoint vertex types. The tilde symbols were correct in the scaffold; their status is now source-verified.

In Appendix A's chain notation, $b_c$ is the stage-1 chain and $x$ the stage-2 chain, under the source identifications. Without boundaries, Eq. (11) reads
\[
\partial_1^{\mathcal L_{\neg c}^*}b_c=\pi_0^{(c)}\sigma,\qquad
\partial_1^{\mathcal L_c^*}x=(1-\pi_0^{(c)})\sigma+b_c.
\tag{N3}
\]
For boundaries these equalities hold **modulo the respective boundary spaces**, as in Eq. (13). The scaffold's ordinary-incidence equality with zero boundary parity imposed is superseded.

## 4. Translation between sources

- Lee's physical qubit is a primal vertex, a dual triangular face, a hyperedge of $\mathcal H$, and a stage-2 graph edge. These are different bases related by stated identifications; $C_0(\mathcal L)$ is not geometrically $C_1(\mathcal L_c^*)$.
- Delfosse's $G^*(c)$ corresponds to Lee's **restricted** graph $\mathcal L_{\neg c}^*$ in the closed setting. His $\pi_0^c$ matches $\pi_0^{(c)}$, and his hyperedge projection $\pi_1^c$ matches $p_{\rm edge}^{(c)}$ there. It is not $T_c$ or $\epsilon_c$.
- Delfosse's chain-complex convention uses $H_X=\partial_1$ and analyzes Z errors; our X-error convention uses $H_Z=H$. Swap X/Z using the color-code self-duality (his Lemma 4.3), not silently.
- Kubica et al.'s local Clifford map $U$ (write $U_{\rm KYP}$ in project formulas to avoid the face-space symbol $U$) and shrunk lattices $\mathcal L_A,\mathcal L_B$ are separate from Lee's support bijection. Theorem 3 attaches the layers along one boundary; it does not identify $G_c$ with either layer.


## 5. Task 1 boundary notation (adopted and proved)

All graph vertex sets below are tagged disjoint unions. A primal edge serving as
a stage-2 vertex is not a stage-2 edge. The notation agrees with the physical
and source symbols above; new symbols describe the ordinary merged graph only.

- $\mathcal C=\{r,g,b\}$; $F_c=\Delta_2^{(c)}(\mathcal L_{2D})$ and
  $E_c=\Delta_1^{(c)}(\mathcal L_{2D})$ are sets of real faces and primal edges.
- $Q_a=Q\cap\Gamma_a$ includes both corner qubits. Thus
  $Q_a\cap Q_b=\{q_{ab}\}$ for distinct colors; no qubit is on all three sides.
- $\mathcal F_c(q)=\{f\in F_c:q\in f\}$,
  $\mathcal E_c(q)=\{e\in E_c:q\in e\}$,
  $n_c^F(q)=|\mathcal F_c(q)|$, $n_c^E(q)=|\mathcal E_c(q)|$.
  Each count is zero or one. Their sum is never zero for the selected family.
- $\delta_{\neg c}$ and $\delta_c$ are binary incidence maps of the ordinary
  stage-1 and stage-2 graphs with the single boundary row deleted. These avoid
  reusing the archived $D_c$ of the proposed split graph.
- $s_c$ is the stage-2 real-vertex syndrome: $\sigma_Z^{(c)}$ on face vertices
  and $E_{\rm pred}^{(c)}$ on primal-edge vertices.
- $\mathcal B_c^{\rm dang}=\{e\in\Delta_1(\mathcal L_c^*):
  v_{\rm bdry}\in e\}$ denotes physical-qubit-labelled dangling edges.
- $\mathcal B_c^{\rm missF}=\{\epsilon_c(q):\mathcal F_c(q)=\varnothing\}
  =\epsilon_c(Q_c)$ and
  $\mathcal B_c^{\rm missE}=\{\epsilon_c(q):\mathcal E_c(q)=\varnothing\}
  =\{\epsilon_c(q_{c_1c_2})\}$.
  Superscripts name the **missing** object, not the surviving endpoint.
  These sets are disjoint, exhaust $\mathcal B_c^{\rm dang}$, and have sizes
  $d$ and $1$. Task 1 establishes them as geometric terminal classes, not connected
  components of the merged graph; Task 4 additionally proves their physical
  logical inequivalence.
- For a stage-2 edge subset $S$,
  $\tau_c^F(S)=|S\cap\mathcal B_c^{\rm missF}|\bmod2$ and
  $\tau_c^E(S)=|S\cap\mathcal B_c^{\rm missE}|\bmod2$.
  The ordinary boundary incidence is their sum. Neither parity is being
  identified with a physical logical parity in Task 1.

### Explicit family used by the proof

$d=2t+1$, $t\ge1$, $L=3t$,
$\Omega_t=\{(i,j)\in\mathbb Z_{\ge0}^2:i+j\le L\}$.
Face centers $F_t$ have $i-j\equiv2\pmod3$; $Q_t=\Omega_t\setminus F_t$.
The identification of $F_t$ with physical faces and $Q_t$ with $Q$ is fixed
in the note. Face colors are $\chi(0)=g,\chi(1)=b,\chi(2)=r$ for $j\bmod3$.
The cyclic neighbor offsets are
$N=((-1,1),(0,1),(1,0),(1,-1),(0,-1),(-1,0))$.
The face at $f$ has the cyclic support $(f+N)\cap Q_t$; consecutive retained
vertices, including the wraparound pair, form its primal edges.
Sides are $\Gamma_r:j=0$, $\Gamma_g:i=0$, $\Gamma_b:i+j=L$.
The rotation $R(i,j)=(L-i-j,i)$ permutes sides and colors.
These are coordinates for the full standard odd-distance 6.6.6 family, not
an extension to arbitrary three-colored cellulations.

### Source boundary labels and deferred symbols

Lee Appendix A.3 retains the source labels
$\{v_{\rm bdry}^c,\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}\}$.
The nested pair is one virtual stage-2 vertex. They record a missing c face
and a missing c edge respectively. Task 1 identifies the physical origins
of those types while keeping the ordinary graph merged.

Task 2 activates the boundary-resolved graph symbols and Task 3 the chain-map symbols in §6. The geometric CW symbol $\widehat G_c$ remains a reserved historical proposal in [the deferred program](notes/deferred_proof_program.md). Task 4 activates $A_c$ and its algebraic complex below. Tasks 6–7 activate $\phi_c$ with the precise certified-cluster definition at the end of this registry; no geometric CW model is asserted. The set $\mathcal B_c^{\rm dang}$ consists of ordinary edges; $\mathcal B_c$ below consists of resolved boundary vertices.

## 6. Tasks 2 and 3: adopted resolved graph and physical chain map

These definitions use exactly the Task 1 incidence classes. Their physical logical inequivalence is now proved in Task 4; the definitions below do not assume it.

- $G_c=\widetilde{\mathcal L}_c^*$ has real vertices $F_c\sqcup E_c$ and
  two virtual vertices $b_c^0,b_c^1$; $\mathcal B_c=\{b_c^0,b_c^1\}$.
  Their source labels are $v_{\rm bdry}^c$ and the single nested-pair
  vertex $\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}$.
  $\mathcal B_c^{(i)}=\{b_c^i\}$ denotes a singleton terminal set, not a
  claim about logical inequivalence or a connected component of the full graph.
- $\widetilde\epsilon_c:Q\to\Delta_1(G_c)$ creates one labelled edge per
  qubit. Both real endpoints, when present, stay fixed. Missing-face
  edges terminate at $b_c^0$ and the missing-edge opposite-corner edge
  at $b_c^1$. No new physical edge or qubit is added.
- $q_c:G_c\to\mathcal L_c^*$ identifies the two terminals and fixes real
  vertices; $q_{c,0},q_{c,1}$ are its linear vertex/edge maps.
  $q_{c,1}\widetilde\epsilon_c(q)=\epsilon_c(q)$, and
  $\partial_1^{\mathcal L_c^*}q_{c,1}=q_{c,0}\partial_c$.
  This is vertex identification, not contraction of an added edge.
- $C_i(G_c)=\mathbb F_2^{\Delta_i(G_c)}$ for $i=0,1$,
  $\partial_c=\partial_1^{G_c}$ sends an edge to its two endpoints.
  $C_{\rm bdry}(G_c)=\mathbb F_2^{\mathcal B_c}$.
  No $C_2$ or relative homology is introduced by this notation.
- $W_c=\mathbb F_2^{F_c}\oplus\mathbb F_2^{E_c}$,
  $\rho_c:C_0(G_c)\to W_c$ deletes both terminal rows, and
  $D_c=\rho_c\partial_c=\delta_c q_{c,1}$.
  The ordinary $\delta_c$ keeps the meaning fixed in Task 1.
- $\omega_c(\widetilde\epsilon_c(q))=\omega_c^{\rm ord}(\epsilon_c(q))$
  transports the supplied nonnegative edge weights. The cost of a binary
  chain is the sum over its support, with no auxiliary terminal shortcut.
- $T_c:C_1(G_c)\to A$, $T_c\widetilde\epsilon_c(q)=q$, is the linear
  isomorphism to physical support. This is the resolved-domain version
  of the §2 source support inverse; equivalently $T_c=T_c^{\rm ord}q_{c,1}$. We do not apply the ordinary inverse
  directly to an untyped resolved edge.
- $V_\Gamma=\operatorname{supp}(T_c\Gamma)$ and
  $\mathscr P_{X,c}(\Gamma)=P_X(T_c\Gamma)$.
  Use $\mathscr P_{Z,c}$ for the exchanged CSS sector. The notation
  keeps $P_X$'s original domain $A$ intact.
- $H_c:A\to\mathbb F_2^{F_c}$ is the c-face row restriction of $H$.
  $M_c:A\to\mathbb F_2^{E_c}$ is physical c-edge parity:
  $(M_ca)_e=a_u+a_v$ for $e=\{u,v\}$.
  $D_c\Gamma=(H_cT_c\Gamma,M_cT_c\Gamma)$.
- $\Lambda_c:W_c\to U$ has
  $(\Lambda_c(y,z))_f=y_f$ for $f\in F_c$, and
  $(\Lambda_c(y,z))_f=\sum_{e\in E_c:e\subset f}z_e$ for other faces.
  **Exact syndrome identity:** $HT_c=\Lambda_cD_c$.
  Boundary deletion alone gives stage-2 data, not the physical syndrome.
- $\eta_c(v)=\Lambda_c\rho_c(v)$ is a physical syndrome vector assigned
  to a graph endpoint: a c-face basis vector for a face vertex, the sum
  of incident real non-c faces for an edge vertex, zero for either terminal.
- A walk is mapped through its mod-two traversal chain; repeated edges
  cancel. A simple path is a special binary chain; arbitrary supports
  may have branching, cycles, and disconnected components.

### Objects used by the Task 4 theorem

$K_c=\ker D_c$ is the difference space for fixed real stage-2 syndrome.
Its elements map into $Z_X$ by the proved syndrome identity.
For $z\in K_c$,
$\beta_c(z)=(\partial_cz)_{b_c^0}=(\partial_cz)_{b_c^1}$; this equality
is graph parity only.
Define $R_c=K_c\cap T_c^{-1}(S_X)$ and $\mathcal Q_c=K_c/R_c$.
Define $\lambda_c(z)=\ell_Z^{\mathsf T}T_cz$ for the already fixed
physical logical-Z support.

Task 4 now proves $\lambda_c=\beta_c$ on $K_c$ and
$R_c=\ker\partial_c=\operatorname{im}A_c$.
The proof and exact induced complex are recorded below. The bare graph
still does not quotient out its stabilizer cycles.

## 7. Tasks 4 and 5: logical quotient and induced physical complex

- Pure-sector physical equivalence:
  $\mathscr P_{X,c}(\Gamma_1)\sim_{\mathcal S}
  \mathscr P_{X,c}(\Gamma_2)$ iff
  $T_c(\Gamma_1+\Gamma_2)\in S_X$.
  This definition makes sense for all chains; the graph-cycle iff uses
  the additional condition $D_c\Gamma_1=D_c\Gamma_2$.
- $Q_c$ is also used as its physical binary indicator. The source-backed
  side operator $P_Z(Q_c)$ is nontrivial logical Z. For any fixed
  nontrivial $\ell_Z$, $\ell_Z+Q_c\in S_X$ in this self-dual one-qubit code.
- **Proved:** for $z\in K_c$,
  $\beta_c(z)=Q_c^{\mathsf T}T_cz=\ell_Z^{\mathsf T}T_cz=\lambda_c(z)$.
  Hence $R_c=\ker(\beta_c|_{K_c})=Z_1(G_c)=\ker\partial_c$.
- $\overline T_c:\mathcal Q_c=K_c/R_c\to\mathcal L_X=Z_X/S_X$,
  $[z]\mapsto[T_cz]$, is a proved isomorphism. Both spaces are one-dimensional.
  Every nontrivial relative chain contains a simple terminal-joining path;
  its remaining cycle part maps to a stabilizer.
- $F_{\neg c}=F\setminus F_c$, $U_{\neg c}=\mathbb F_2^{F_{\neg c}}$,
  and $\iota_{\neg c}:U_{\neg c}\to U$ is the face-coordinate inclusion.
- The formerly proposed $A_c$ is now the explicit linear map
  $A_c=T_c^{-1}J\iota_{\neg c}:U_{\neg c}\to C_1(G_c)$.
  It is injective and $\operatorname{im}A_c=R_c$.
  Thus the non-c physical face supports form a basis of the graph cycle
  space under $T_c^{-1}$; no additional corner generators or relations
  are needed for this family.
- The induced binary complex is
  $\mathfrak C_c=(U_{\neg c}\xrightarrow{A_c}C_1(G_c)
  \xrightarrow{D_c}W_c)$.
  The triple $(\iota_{\neg c},T_c,\Lambda_c)$ is a chain map to
  $(U\xrightarrow J A\xrightarrow H U)$ and induces the logical isomorphism
  $H_1(\mathfrak C_c)\cong\mathcal L_X$.
  This is an algebraic complex with relative vertex coordinates, not an
  asserted geometric CW realization $\widehat G_c$.
- The bare-graph relative homology $H_1(G_c,\mathcal B_c;\mathbb F_2)$
  has no two-cell denominator and equals $K_c$; its dimension is
  $t(t+1)+1$, not one. The induced complex removes the physical-face
  cycle space of dimension $t(t+1)$.
- $n=|Q|=3t^2+3t+1$, $|F_c|=t(t+1)/2$,
  $|E_c|=(n-1)/2$, $|F_{\neg c}|=t(t+1)$.
  These are counts in the already defined finite family.

Task 5 adopts no new graph or altered weights. The existing
$(G_c,\mathcal B_c,\omega_c)$ is a Meister-type modified decoding graph
for **fixed-stage-2 relative differences**, whose effective check map
is $D_c$. It is not the decoding graph of the full physical matrix $H$.
The unmodified minimum nontrivial chain cost equals a shortest terminal
path cost for $\omega_c\ge0$; this is not a cluster-contracted metric.

For genuine positive edge-length metrics required by Meister's later
construction, require $\omega_c>0$; uniform bit-flip log-odds weights
with $0<p<1/2$ satisfy this. Nonnegative weights still satisfy the
topological and unmodified path-cost statements.

The following Phase-1 metric notation is now active; arbitrary solver growth is still not identified across boundary splitting.


## Phase-1 decoder clusters and metric (Tasks 6–7)

- Write \(V=\Delta_0(G_c)\), \(E=\Delta_1(G_c)\) only inside metric/algorithm sections; these local aliases do not denote primal edges.
- \(\Sigma_c=\operatorname{supp}s_c\subset V\setminus\mathcal B_c\), \(k=|\Sigma_c|\); \(f_c\in C_1(G_c)\) is the actual returned correction, \(D_cf_c=s_c\). Lowercase \(f_c\) avoids the physical-face set \(F_c\).
- \(d_c\): positive-weight metric on the interval realization \(X_c\) of \(G_c\); \(a_u=d_c(u,\mathcal B_c)\); \(d_c^\circ(u,v)=\min\{d_c(u,v),a_u+a_v\}\), the merged matching metric.
- \(\mathcal O_c=\{S\subseteq\Sigma_c:|S|\text{ odd}\}\).
  The boundary-normalized nonnegative odd-cut dual has variables \(y_S\ge0\), load
  \(l_{uv}(y)=\sum_{S:|\{u,v\}\cap S|=1}y_S\le d_c^\circ(u,v)\), and
  \(r_u=\sum_{S\ni u}y_S\le a_u\). Its value is \(Y_c=\sum_Sy_S\).
  Set radii zero at all nonsyndrome vertices, including both terminals.
  This is Meister's radius rule in an explicit free-boundary T-join dual; it is not a raw signed singleton potential from an arbitrary Blossom backend.
- Certified MWPM data satisfy \(Y_c=\omega_c(f_c)\). Exact weights and optimality are hypotheses of the representative bound. Distinct optimal dual choices can give different swim values; a fixed solver/tie convention is part of the definition.
- \(\mathcal C_c=\bigcup_{v\in V}B_{r_v}(v)\subset X_c\); “cluster” means a connected component of this union. UF radii are separately obtained from a specified growth run on the resolved graph.
- \(\bar X_c\): interval graph with every connected cluster contracted, with the induced length pseudometric; \(\bar G_c=(V,E,\bar\omega_c)\) retains original physical edge labels.
- \(h_v=\max\{0,\max_{u\in V}(r_u-d_c(u,v))\}\) and
  \(\bar\omega_c(uv)=|uv\setminus\mathcal C_c|_{\omega_c}
  =\max\{0,\omega_c(uv)-h_u-h_v\}\).
  This is total uncovered interval length, not a boolean test of endpoint cluster IDs.
- \(\phi_c(\mathcal C_c)=\operatorname{dist}_{\bar\omega_c}(b_c^0,b_c^1)
  =\min_{z\in K_c,\beta_c(z)=1}\bar\omega_c(z)\).
  Dependence on syndrome alone presupposes fixed decoder/dual choices.
- \(W_{c,\mathrm{base}}^{(2)}=\omega_c(f_c)\);
  \(W_{c,\mathrm{opp}}^{(2)}=\min\{\omega_c(m):D_cm=s_c,\ \beta_c(m+f_c)=1\}\).
  The proved certified-MWPM bound is \(W_{\mathrm{opp}}^{(2)}-W_{\mathrm{base}}^{(2)}\ge\phi_c\).
  It is not a summed-class LLR or full concatenated-decoder gap.
- Zero original lengths are handled as a pseudometric on labelled edges, retaining their original chain incidence for logical witnesses; no physical labels are discarded.

Natural logarithms are used for probability weights in the note. Other
logarithm bases rescale weights and phi together. The local r-values of
Chen et al.'s fill-region convention and the cluster-norm statistics of
Lee–English–Bartlett are distinct source objects, not new aliases for our
r_u or phi_c. The primary-source comparisons are in refs/REFERENCES.md.

## Phase-2A implementation conventions — 2026-09-12

The authorized implementation retains all Phase-1 symbols and hypotheses.
`swim_growth_convention = sparse_blossom_final_defect_metric_balls_v1` names
an implementation convention: final original-defect radii (top-region
intercept plus wrapped radius, in ordinary weight units) define metric balls
on the explicit resolved graph. These exported radii are **not identified**
with the certified `r_u` of Definition 10.1. No odd-cut variables or exact
certificate equality are exported; `swim_bound_certified` is false.

`Stage2RowRole` distinguishes `PHYSICAL_C_DETECTOR`, `STAGE1_VIRTUAL`, and
`INACTIVE_PADDING`. The third type records historical zero H2 rows belonging
to other colors; it is not an additional parity constraint. All active rows
have one of the first two types. Same-color inactive time rows remain typed
physical rows, with `active=False`. Source detector IDs and full coordinates
are retained for both physical and virtual rows.

Analysis edges are labelled by stage-2 column IDs with explicit original DEM
IDs and audited physical-qubit IDs. `C_SIDE` corresponds to b_c^0 and
`OPPOSITE_CORNER` to b_c^1. Circuit-level half-edges remain `UNCLASSIFIED`;
temporal roles are reserved, not inferred. `selected_swim_distance` is the
per-color value selected by the unchanged ordinary best-color rule. This
selection has no new full-decoder gap or probability theorem.

## Phase-2B empirical analysis conventions

`forced_gap` is the experiment-layer alias of the existing comparative-decoding
`logical_gaps`, stored also as `comparative_logical_gap`. It pairs with
`comparative_logical_error`; selected-color swim pairs with
`ordinary_logical_error`. No theorem identifies these metrics.
`k` and `l` are empirical shot-level success-logit coefficients:
`logit P(success | selected_swim_distance) = k * selected_swim_distance + l`.
They are unrelated to physical logical parity or the fixed-fiber quotient.
`G(d), C(d)` retain Lee's subthreshold log-rate notation. Confidence intervals
default to 99%; abort rate is one minus the retained-shot fraction.

## Surface-code global-subtraction path gap v1 (2026-09-19)

Implementation convention: `path_gap = path_gap_residual_distance -
path_gap_correction_weight`, version `global_subtraction_v1`. For the ordinary
merged matching-graph correction E (XOR edge support returned by PyMatching),
`path_gap_correction_weight` is the sum of original floating edge weights over
ALL of E, including edges outside the X-boundary analysis component. The
residual distance uses the existing split-X-boundary topology, assigning zero
to precisely those retained edges in E and leaving all others at original
weight. It uses no growth radii. Signed values are retained, without absolute
value or clipping. `ordinary_solution_weight` remains the separate backend
quantized matching cost. This is a heuristic, not a certified gap or LLR.
