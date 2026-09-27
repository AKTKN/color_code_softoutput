# Implement a modular circuit-level DEM-Y signed-gap metric in color-code-stim

Implement the algorithm below in my fork of **color-code-stim**, normally `AKTKN/color-code-stim`. Deliver working modular code, focused correctness tests, a paper-style algorithm description, and a runnable integration example.

The objective is a useful logical-gap proxy from the correction already selected by the ordinary decoder, with no further decoding. The primary target is the standard triangular 6.6.6 color code, `tri_optimal` syndrome extraction, and uniform circuit-level noise. The soft-output calculation must be a reusable module.

Read the actual checkout and applicable repository instructions. Preserve existing code-capacity monotone-Y functionality and unrelated work. The current checkout is authoritative for APIs; the mathematical and algorithmic requirements below define this new metric. This prompt is self-contained: do not assume access to a previous conversation, external scratch scripts, or serialized reference graphs.

## 1. Objective, model, and implementation boundaries

### 1.1 Required behavior

Compute the signed score after obtaining the final decoder correction. The metric must not:

- Call MWPM, BP, UF, another decoder, comparative decoding, or forced decoding.
- Re-run stage 1 or stage 2, change the hard prediction, or search for a new baseline correction.
- Apply iterative stabilizer descent or unrestricted opposite-class optimization.
- Rebuild geometry, certify graph supports, or enumerate whole paths per shot.
- Enumerate the full Cartesian product of root choices in the production scoring kernel.
- Replace signed costs by absolute values, zero corrected faults, clip negative outputs, or subtract the baseline correction weight a second time.

This method does minimize over a restricted family of logical fault supports. Describe that operation accurately; its advantage is a fixed set of DAG computations and local junction calculations rather than another decoder execution.

### 1.2 Initial supported package configuration

Support:

- `circuit_type="tri"`: triangular 6.6.6 code, odd `d >= 3`.
- Integer `rounds=T >= 1`, not necessarily `T=d`.
- `cnot_schedule="tri_optimal"`, `superdense_circuit=False`.
- Z-memory, `temp_bdry_type="Z"`, one target logical observable.
- `NoiseModel.uniform_circuit_noise(p)`, with valid positive probabilities as specified below.
- `perfect_init_final=False`, `perfect_logical_initialization=False`,
  `perfect_logical_measurement=False`, `perfect_first_syndrome_extraction=False`.
- `exclude_non_essential_pauli_detectors=False` for the initial adapter.

Check effective settings, including granular noise overrides. In the inspected snapshot, uniform circuit noise sets reset, measurement, CNOT, and idle noise to `p`; additional initial-data depolarization, per-round bitflip/depolarization, and additional post-CNOT one-qubit depolarization are zero. Use the package factory and its actual semantics. Do not accidentally add a code-capacity noise layer.

The schedule may be stored as a list after construction. Compare with the checkout's `CNOT_SCHEDULES["tri_optimal"]` rather than checking only a string. The inspected vector was `[2,3,6,5,4,1,3,4,7,6,5,2]`; verify rather than silently assume it.

Reject unsupported circuits, full joint X/Z DEMs, superdense extraction, growing/cultivation, arbitrary schedules, open sliding-window boundaries, and multiple target observables clearly. Do not silently approximate them using this adapter.

### 1.3 Probability model

Use the same **X/Z-separated DEM**, `dem_xz`, that the existing concatenated decoder uses. In the inspected fork, `DemManager._generate_dem` calls `separate_depolarizing_errors(circuit)` and then generates a flattened DEM.

This is a circuit-level model: it includes gate, reset, measurement, idle, hook, and temporal effects within the selected sector. It does **not** retain joint X/Z correlations from the original depolarizing circuit. Do not claim the score is an exact likelihood quantity for that original joint model.

"Original DEM column" below means an error instruction of this fixed `dem_xz`. Stim may already have merged several circuit locations into that instruction. Do not equate a column with a physical qubit or necessarily with one elementary gate location.

### 1.4 Repository contracts to verify

| Component | Required use |
|---|---|
| `color_code.py` | Construct the specified experiment and obtain ordinary decoder results. |
| `dem_utils/dem_manager.py` | Obtain the exact `dem_xz`, `H`, `obs_matrix`, `probs_xz` used for the correction. |
| `stim_utils.dem_to_parity_check` | Verify error-instruction-only column indexing and detector/observable parity conventions. |
| `decoders/concat_matching_decoder.py` | Use final `extra_outputs["error_preds"]` after conversion to original DEM coordinates and any predecoding composition. |
| `graph_builder.py` and detector metadata | Recover physical face coordinates and colors, including boundary geometry. |
| Existing metrics modules | Reuse conventions where appropriate; keep code-capacity and circuit-level metrics distinct. |

The legacy `get_swim_distance` path in the inspected snapshot can affect decoder weights and final selection. Do not use that flag to implement this postprocessor. Neither `best_colors` nor stage-2 syndrome defines the new metric graph.

## 2. Mathematical definition and indexing

### 2.1 Sector extraction with explicit maps

Let the complete fixed `dem_xz` have detector matrix \(H_{\rm all}\), target observable row \(o_{\rm all}\), and \(M\) error columns.

Let \(\mathcal R_Z\) contain the Z-detector rows. Let

\[
\mathcal C_Z=\{j:\varnothing\ne D_j\subseteq\mathcal R_Z\},
\]

where \(D_j\) is the detector support of the original error instruction. Define

\[
H=H_{\rm all}[\mathcal R_Z,\mathcal C_Z],\qquad
o=o_{\rm all}[\mathcal C_Z],\qquad m=|\mathcal C_Z|.
\]

Store explicit local-to-full row and column maps and inverse maps where needed. For the final full-coordinate correction \(E_{\rm all}\), use

\[
E=E_{\rm all}[\mathcal C_Z].
\]

Parse `dem_xz.flattened()`, counting **only error instructions**. Validate the parsed supports, observable bits, probabilities, and ordering against the matrices and probability vector. Do not infer order from equal array lengths. Preserve the parity semantics of targets and retain each original error instruction as one mechanism; `^` separators must not become independent variables.

For this narrow adapter, verify that all omitted nonempty columns belong entirely to the other Pauli sector and do not flip the target Z-memory observable. Reject mixed-sector columns. Explicitly detect zero-detector columns: a nonzero target-observable column must cause a clear unsupported-model error in this initial version, not disappear during filtering. Zero-detector/zero-observable columns may be omitted with the frozen-outside-sector convention below.

When returning a witness, embed the sector vector into full DEM coordinates using zeros outside \(\mathcal C_Z\). Validate it against the full matrices.

### 2.2 Signed costs

Use the actual marginal DEM probabilities \(p_j\), not the uniform physical circuit parameter \(p\):

\[
w_j=\log\frac{1-p_j}{p_j},\qquad
W(F)=\sum_j w_jF_j,\qquad
a_j(E)=(1-2E_j)w_j.
\tag{1}
\]

The package adapter requires finite \(0<p_j<1/2\). The standalone mathematical evaluator may accept arbitrary finite nonnegative weights, including zero, for explicit certified inputs and tests. Cast unsigned/Boolean corrections before forming signed costs.

For every fault support \(L\),

\[
a^\mathsf TL=W(E\oplus L)-W(E).
\tag{2}
\]

The correction-relative sector gap is

\[
\Delta_{E,Z}
=\min_{\substack{HL=0\\oL=1}}a^\mathsf TL.
\tag{3}
\]

All arithmetic in detector and observable constraints is over \(\mathbb F_2\). Outside-sector components of \(E_{\rm all}\) are held fixed. Consequently, (2) is also the difference of full-coordinate correction weights for the embedded candidate.

The new metric will be

\[
S_{\rm DEMY}(E)
=\min_{L\in\mathscr Y_{\rm DEM}}a^\mathsf TL,\qquad
\mathscr Y_{\rm DEM}\subseteq\{L:HL=0,\ oL=1\}.
\tag{4}
\]

This defines a minimum **within the specified restricted family**, not a class-summed posterior log-odds.

If \(m_0,m_1\) are the minimum weights in the same/opposite sector classes relative to \(E\), then

\[
\Gamma=m_1-m_0,\quad
\eta=W(E)-m_0\ge0,\quad
\rho=S_{\rm DEMY}-\Delta_{E,Z}\ge0,
\qquad
S_{\rm DEMY}=\Gamma-\eta+\rho.
\tag{5}
\]

Do not identify the package's `logical_gaps` with (3) or (5) without checking its baseline and weight conventions.

## 3. Detector geometry

Use stable detector identities plus original face coordinates. In the inspected package, detector coordinates are

\[
(x_{\rm draw},y,t,\text{Pauli code},\text{color code}).
\]

Z detectors have Pauli code 2. Color codes are \(0=r,1=g,2=b\). Verify these through the checkout's constants and metadata. Z-ancilla drawing coordinates are shifted left: \(x_{\rm face}=x_{\rm draw}+1\). Prefer `face_x, face_y` through the detector-to-check map when available.

Let \(B=3(d-1)/2\). For face coordinates \((x,y)\), use

\[
h_r=y,\qquad
h_g=\frac{x-2y}{4},\qquad
h_b=\frac{4B-2y-x}{4}.
\tag{6}
\]

Their sum is \(B\). Validate the integral coordinate conventions and mapping. Keep time \(t\) separately; two detectors on the same spatial face at different times are different vertices.

A spatial transport \(v\to u\) of color \(c\) is admissible exactly when

\[
h_c(u)<h_c(v),\qquad
h_k(u)\ge h_k(v)\quad(k\ne c).
\tag{7}
\]

There is no requirement that \(t(u)\ge t(v)\). Spatial monotonicity, not temporal monotonicity, defines the DAG order.

## 4. Compile native transport operations

Every operation stores an exact short support list of **sector DEM column IDs**, its full detector XOR, and its observable parity. Parallel operations with different fault supports must remain distinct.

### 4.1 Structural scope check

For the supported circuit, require each retained column to have one of these forms:

- Type A: at most one detector of each color, including one-/two-color boundary reductions.
- Type B: exactly two detectors, both of one color.

Validate this on the actual DEM. A failure is not permission to split that column into independent edges or discard it without reporting an unsupported configuration.

For each color \(c\), write

\[
D_j^c=D_j\cap V_c,\qquad
\sigma_c(j)=D_j\setminus V_c.
\]

### 4.2 Direct operations

For columns with \(\sigma_c(j)=\varnothing\):

- One detector \(v\): add a base terminal operation \(v\to\bot_c\) with support \(\{j\}\).
- Two detectors on different spatial faces: add an oriented base operation if (7) holds.
- Two detectors on the same face at adjacent times: record both temporal directions as elementary temporal links, with support \(\{j\}\).

A temporal link is eligible only if the spatial face is identical and \(|\Delta t|=1\), in the package's round coordinate. Other same-height operations are not admitted.

The sink \(\bot_c\) is an algebraic terminal: its detector vector is zero. A terminal operation must be justified by an actual singleton detector XOR. Never add arbitrary edges to an initial/final time boundary or remove measured detector constraints.

### 4.3 Paired operations and the terminal level cut

Group columns by their exact **nonempty** signature \(\sigma_c(j)\), including detector times. Never place the empty signature in a global all-pairs group.

For each unordered pair \(i\ne j\) in a group, form

\[
P=\{i,j\},\qquad
HP=D_i\triangle D_j.
\tag{8}
\]

Only the following pairs are admitted:

- Two remaining c-detectors: orient as a base spatial operation if (7) holds.
- One remaining c-detector: consider a base terminal operation, subject to the level cut below.

Ignore zero-detector pairs and purely temporal paired operations in this family. In particular, the temporal links of Section 4.2 are **single original columns**, not pairs.

For each group, compute its real c-endpoint heights

\[
A_c(\sigma)=
\{h_c(v):D_j^c=\{v\},\ \sigma_c(j)=\sigma\}.
\]

In the audited circuit, this set has at most two values. Validate this structural condition. For a paired terminal operation at \(v\), require

\[
|A_c(\sigma)|\le1
\quad\text{or}\quad
h_c(v)=\max A_c(\sigma).
\tag{9}
\]

This is part of the chosen family. Without this cut, a path can use one pair from a higher to a lower real endpoint and then reuse the same fault in a lower-endpoint-to-terminal pair.

Equivalently, the two-level case resembles a directed bipartite graph: higher c-endpoint \(\to\) signature vertex \(\to\) lower c-endpoint or sink. Original column IDs must be preserved even if pairs are stored as contracted operations.

Do not hard-code a maximum group size of five or truncate larger groups. Report actual group sizes and enforce the structural/cost assumptions explicitly.

### 4.4 Two distinct graph families

Keep a raw base-operation collection \(A_c\) containing all spatial and terminal operations above. Obtain \(G_c^0\) by pruning \(A_c\) to operations that can reach a justified sink using base operations alone.

The **tail** graph \(G_c^1\) contains:

1. Every operation of the raw collection \(A_c\).
2. For every elementary direct temporal link \(v\to z\) and every raw base operation \((z\to u)\in A_c\), one composite operation \(v\to u\) with support
   \[
   P=P_{\rm time}\triangle P_{\rm base}.
   \tag{10}
   \]

Use XOR even when an assumed disjointness should make it equivalent to union; validate the support. The tail graph admits at most one temporal link before each spatial or terminal operation.

Do not insert raw temporal links into the online DAG. Do not build composites recursively from \(G_c^1\). Do not allow paired temporal links or multiple consecutive temporal links in this version.

Root first operations use **\(G_c^0\)**. All subsequent tail operations use **\(G_c^1\)**. This distinction is essential to the proposed computational cost.

All nonterminal operations in either graph satisfy strict spatial descent. Deduplicate only operations identical in source, destination, and original fault support; preserve distinct supports and observable labels. Prune the enriched graph by its own sink reachability after constructing composites from the raw base collection. Do not accidentally construct it from an already pruned base graph. Root first options use the independently pruned \(G_c^0\).

## 5. Certify all-path fault nonreuse offline

For each tail graph, compute reachable fault-support unions

\[
U_c(\bot_c)=\varnothing,\qquad
U_c(v)=\bigcup_{(v\to u,P)\in G_c^1}
\bigl(P\cup U_c(u)\bigr).
\tag{11}
\]

Evaluate vertices in increasing \(h_c\), using only sink-reaching operations.

Require for every retained tail operation

\[
P\cap U_c(u)=\varnothing.
\tag{12}
\]

This checks all possible suffixes, not just a sampled or minimum-cost path. It ensures that adding operation costs along a path equals the signed weight of the resulting fault XOR.

Implement a reference compiler using integer/packed bitsets if useful. For this compiler, reachable-support storage can be quadratic in the number of fault columns in the worst case. Report setup time and peak memory separately; do not claim linear preprocessing merely because online scoring is linear.

Do not rerun (11) per shot. Once local junction compatibility and graph certificates are compiled, the production evaluator need not retain all global \(U_c(v)\) bitsets. A more scalable local geometric certificate is acceptable only if it provably gives the same accepted candidate family. A merely conservative substitute can reject additional valid caps and change the metric, so it is not an equivalent implementation. Arbitrary truncation of reachable sets is incorrect.

If (12) fails, report the source, operation support, suffix vertex, and repeated column IDs. Fix mapping or construction errors where demonstrated. Do not continue using additive distances on a graph that fails this condition.

## 6. Roots and certified junctions

### 6.1 Root options

Use every Type-A column \(i\) as a root \(R=\{i\}\). Its syndrome has at most one c-detector \(v_c(i)\) per color.

For each color:

- If \(D_i^c=\{v_c\}\), a first option \(\alpha_c\) is a base operation
  \((v_c\to u_{\alpha_c},P_{\alpha_c})\in G_c^0\), followed by a tail in \(G_c^1\).
- If \(D_i^c=\varnothing\), the only option is
  \((u_{\alpha_c},P_{\alpha_c})=(\bot_c,\varnothing)\).

Do not invent a missing endpoint at an arbitrary face or time. Missing endpoints are handled by the actual syndrome equation, and nontriviality will be enforced by the observable parity.

The cap support is

\[
J=R\triangle P_{\alpha_r}
       \triangle P_{\alpha_g}
       \triangle P_{\alpha_b}.
\tag{13}
\]

Intersections among first supports and the root are allowed and must cancel by XOR.

### 6.2 Strong cap certificate as unary and pairwise constraints

Write \(F_\alpha=U_c(u_\alpha)\) for a first option of color c.

Keep an option only when

\[
F_\alpha\cap(R\cup P_\alpha)=\varnothing.
\tag{14}
\]

Two options \(\alpha,\beta\) of different colors are compatible exactly when

\[
F_\alpha\cap F_\beta=\varnothing,\qquad
F_\alpha\cap P_\beta=\varnothing,\qquad
P_\alpha\cap F_\beta=\varnothing.
\tag{15}
\]

Thus the three tails avoid one another and the **union** of root/first-operation supports. This strong certificate is the definition of the retained family, even if weaker conditions based only on the XOR cap would admit additional candidates.

Compile unary filtering and pairwise incompatibility offline. Do not silently replace this with checking only the three currently chosen shortest tails.

Every retained candidate has the form

\[
L=J\triangle L_r\triangle L_g\triangle L_b,
\tag{16}
\]

where each \(L_c\) is any sink-reaching tail from \(u_{\alpha_c}\) in \(G_c^1\), and \(oL=1\). These candidates define \(\mathscr Y_{\rm DEM}\).

Record eligible roots/options and rejected junction conditions. Require a nonempty odd-observable candidate family; a structurally empty result must produce a clear compilation error rather than infinite confidence. Do not require every root to produce every parity.

## 7. Signed DAG evaluation with observable parity

For each color, store two distance values per vertex:

\[
D_c(\bot_c,0)=0,\qquad D_c(\bot_c,1)=+\infty,
\]

\[
D_c(v,\lambda)=
\min_{(v\to u,P)\in G_c^1}
\left[
a(P)+D_c(u,\lambda\oplus oP)
\right],\qquad
a(P)=\sum_{j\in P}a_j.
\tag{17}
\]

Here \(\lambda\) is the observable parity of the complete tail. Use increasing spatial height. Negative costs are legitimate; do not use Dijkstra, heap-based nonnegative shortest paths, or another matching solver.

For any compatible first-option triple,

\[
V=
a(J)+
\min_{\lambda_r\oplus\lambda_g\oplus\lambda_b=1\oplus oJ}
\sum_cD_c(u_{\alpha_c},\lambda_c).
\tag{18}
\]

The reference evaluator may enumerate first-option triples and the four parity choices on tiny tests. The production evaluator must compute the same minimum using the exact sparse junction solver below.

Keep only scalar distances and, when requested, predecessor operation IDs for witnesses. Do not propagate whole fault bitsets through the online DP.

## 8. Exact sparse junction solver

This section is a required part of the implementation, not an optional optimization. A per-shot scan of all certified cap triples can dominate decoding time.

### 8.1 Root sign folding and parity convention

For a fixed root i, define conceptually

\[
b_j=(1-2\,\mathbf1_{j=i})a_j.
\tag{19}
\]

Never allocate or copy a length-m b vector for every root. For a short set S, evaluate

\[
b(S)=a(S)-2a_i\,\mathbf1_{i\in S}.
\]

Let \(q_c\) be the observable parity of the **first operation plus its tail**. For a first option \(\alpha\) of color c, its unary cost is

\[
x_\alpha(q_c)
=b(P_\alpha)+
D_c(u_\alpha,q_c\oplus oP_\alpha).
\tag{20}
\]

Enumerate the four assignments satisfying

\[
q_r\oplus q_g\oplus q_b=1\oplus o_i.
\tag{21}
\]

For a compatible triple, the exact objective is

\[
\begin{aligned}
C(\alpha_r,\alpha_g,\alpha_b)
={}&a_i+\sum_c x_{\alpha_c}(q_c)\\
&-2\sum_{c<k}b(P_{\alpha_c}\cap P_{\alpha_k})\\
&+4b(P_{\alpha_r}\cap P_{\alpha_g}\cap P_{\alpha_b}).
\end{aligned}
\tag{22}
\]

The coefficient of the triple intersection is +4. Root folding and the triple term are required even when the root occurs in all three first supports. Do not approximate XOR by union.

### 8.2 Static interaction graph

For each root, construct a tripartite graph whose parts are the surviving first options of the three colors. Connect options of different colors if:

- They are incompatible by (15); or
- Their first supports intersect.

Retain the incompatibility flag and shared-column IDs separately. An edge can be both incompatible and sharing; it is then forbidden.

This graph is structural. Never delete a sharing edge merely because its numerical interaction weight happens to be zero for one shot. Triple interactions are also structural.

First supports contain at most two original columns. Store short intersections directly. No exponential table over the union of all possible shared column IDs is needed.

For each parity assignment, options with infinite unary cost are unavailable. Options of degree zero may be collapsed to the cheapest one in that color for that assignment, preserving its original option ID for witness reconstruction.

Let \(\Delta\) be the maximum total degree in the structural tripartite graph before parity-dependent filtering. A query for the cheapest option in a part avoiding the neighborhoods of at most two fixed options is answered exactly by checking its cheapest \(2\Delta+1\) finite options (or all if fewer). At most \(2\Delta\) options can be excluded.

Find these shortlists without sorting a length-m global array per root. Local stable partial selection, bounded heaps, or a small local sort are acceptable; the actual option counts must be reported.

### 8.3 Exact zero-interaction case without Cartesian enumeration

For consistent comparison, all three case routines below return the objective in (22) **excluding the common root constant \(a_i\)**. Add \(a_i\) exactly once after taking the per-root minimum. Do not compare a full objective from one case against a root-constant-free objective from another.

Define `best(part, blocked_options)` as the cheapest finite option in that part not adjacent to any blocked option, with deterministic ties. All calls below block at most two options, so the shortlist bound applies.

First define `independent_pair(anchor z; remaining parts X,Y)`:

1. Set \(x_0=\operatorname{best}(X,\{z\})\). If none exists, return infinity.
2. Evaluate \(x_0\) with \(\operatorname{best}(Y,\{z,x_0\})\).
3. For every \(y\in N(x_0)\cap Y\) that is finite and not adjacent to z, evaluate
   \(y\) with \(\operatorname{best}(X,\{z,y\})\).
4. Skip any candidate whose lookup returns no finite option. Return the least unary pair sum and the actual two option IDs, or infinity if none exists.

To find the minimum triple with no interaction edges:

1. Choose one part A and its cheapest finite option \(a_0\). If a part is empty, no triple is feasible.
2. Consider anchors \(\{a_0\}\cup N(a_0)\), excluding unavailable options.
3. For each anchor z, add its unary cost to `independent_pair` on the other two parts.
4. Return the minimum; these triples have no pair or triple intersection terms.

Proof: for an optimal independent triple, either \(a_0\) can replace its A-option without increasing cost, or that triple contains a neighbor of \(a_0\). The analogous replacement argument with \(x_0\) proves the two-part routine. This avoids even a three-way shortlist Cartesian product.

### 8.4 Exactly one interaction edge

For every compatible interaction edge \((\alpha,\beta)\):

- Find the cheapest option \(\gamma\) of the remaining color nonadjacent to both.
- Evaluate the three unary terms and the pair correction
  \(-2b(P_\alpha\cap P_\beta)\).

No other pair correction or triple term can occur in this case. An incompatible edge is never an eligible selected edge.

### 8.5 At least two interaction edges

Enumerate wedges: a center option and one neighbor in each of the other two parts.

- Reject a triple if any selected option is unavailable for this parity assignment or any selected pair is incompatible.
- Evaluate expression (22) minus its common root constant \(a_i\), including all pair terms and the triple term.
- Repeated examination of the same triple is harmless for the minimum; deduplicate only if worthwhile.

Every three-option selection with at least two interaction edges has such a wedge. Together with Sections 8.3 and 8.4, this is an exact partition of the possibilities.

For each root, minimize over these cases and the four parity assignments, then add \(a_i\) once. Minimize these full root scores over roots. Retain the minimizing root, first options, and tail parity states when witness output is requested.

### 8.6 Complexity and implementation constraints

Let A be the total number of tail operations, Q_i the number of first options at root i, F_i the number of interaction edges, and \(\Delta_i\) its maximum degree. A conservative per-root bound is

\[
O\!\left(
Q_i\log(\Delta_i+2)
+(\Delta_i+1)^3
+F_i(\Delta_i+1)
+\sum_{\alpha}\deg(\alpha)^2
\right).
\tag{23}
\]

The exact bound depends on the local selection implementation. State the bound actually achieved; do not hide a full Cartesian scan inside a helper.

For a fixed local circuit schedule with bounded groups/options/degrees, total online work is \(O(M+A+\sum_i\text{local work}_i)=O(M)\), including the input map. The constants matter. Do not infer a faster wall-clock time than MWPM or forced gap from this asymptotic statement alone.

Prohibited production patterns include a full b vector per root, a full witness per root, an exponential parity-mask frontier, an expanded list of every cap triple per shot, and graph reconstruction per shot.

## 9. Correctness claims to document and prove

Include concise propositions with proofs:

1. **Cost identity.** Derive (2) directly from binary XOR and additive DEM weights.
2. **Transport validity.** Direct and paired operations have syndrome consisting exactly of their real endpoints; temporal composition cancels its intermediate endpoint.
3. **Logical validity.** Root, first operations, and tails telescope to zero detector syndrome. Enforcing the DEM observable parity gives \(oL=1\). Odd physical-qubit weight is not an appropriate substitute.
4. **Path additivity.** Condition (12) ensures no original column repeats along any arm.
5. **Junction additivity.** Conditions (14)–(15) isolate all possible cancellations within the cap, whose XOR is evaluated exactly.
6. **Exactness within the family.** The parity DP, exact local solver, and root minimum produce (4).
7. **Gap relation.**
   \[
   \Delta_{E,Z}\le S_{\rm DEMY}.
   \tag{24}
   \]
   Equality holds if a minimizing sector complementary support belongs to the retained family.
8. **Relation to a forced candidate.** For an opposite-class correction F differing from E only in the selected sector, if \(E\oplus F\in\mathscr Y_{\rm DEM}\), then
   \[
   \Delta_{E,Z}\le S_{\rm DEMY}\le W(F)-W(E).
   \tag{25}
   \]
   Do not apply this to arbitrary package logical-gap outputs without the premise.
9. **Scope of full-model comparisons.** Allowing changes outside the sector in the same separated DEM can only lower its exact correction-relative minimum. No such inequality between different probability models follows automatically.
10. **Complexity.** Separate the proven DAG/local-join online costs from empirical bounded constants and from the support-union compiler's setup cost.

The native paired operations already allow staggered detector times; in the reference circuit their endpoint time differences reached two rounds. Tail enrichment incorporates original measurement-fault costs. The remaining exclusions include spatial backtracking, long stationary temporal stretches, extra junctions, added temporal motion within the root cap, and uncertified junction combinations. These can create an upward bias in the proxy. There is no proved uniform approximation ratio or forced-gap-equivalent post-selection guarantee.

This is a proposed method. The cited papers supply DEM/decoding background, not a theorem about this new algorithm.

## 10. Modular implementation and API

### Execution outline

~~~text
COMPILE(code):
    Resolve the fixed DEM, target sector, probabilities, and explicit maps.
    Validate scope, column types, and detector geometry.
    Build raw base operations and elementary direct temporal links.
    Build and independently prune base-root and enriched-tail graphs.
    Compute tail support unions and certify all-path nonreuse.
    For each root:
        Build base first options; apply unary support filtering.
        Compile pair incompatibility and shared-support interaction metadata.
    Check that an odd-observable candidate exists.
    Cache graph arrays, evaluation order, maps, and local interactions.
    Release global support unions when no longer needed.

EVALUATE(final_correction, compiled_geometry):
    Map the final correction to sector columns and compute signed costs once.
    Evaluate the three two-parity tail DPs.
    For each root:
        Compute short-support root-folded unary costs without copying a vector.
        For each of four admissible arm-parity assignments:
            Run the exact zero-edge / one-edge / wedge junction routines.
        Add the root constant once to that root's minimum.
    Select the least full root score.
    If requested, reconstruct only its winning fault support.
    Return the signed score and requested metadata.
~~~

### Module boundaries

Adapt file placement to existing package conventions. A reasonable layout is:

~~~text
src/color_code_stim/metrics/
    circuit_dem_y_gap.py          # public result/evaluator interfaces
    _dem_y_geometry.py           # extraction, transport compiler, certificates
    _dem_y_junction.py           # exact sparse local optimizer
    _dem_y_adapter.py            # ColorCode and decoder-output integration
~~~

Reuse existing shared utilities where appropriate. Keep the mathematical core independent of `ColorCode` and decoder classes. Keep reference/oracle implementations in tests or an explicitly diagnostic module.

Suggested interfaces, to implement as new APIs if equivalents do not exist:

~~~python
geometry = CircuitDemYGeometry.from_color_code(code)
metric = CircuitDemYGapEvaluator(geometry, weights=geometry.default_weights)

result = metric.evaluate_sector(E_sector, return_witness=False)
batch_result = metric.evaluate_sector_batch(E_sector_batch)

adapter = CircuitDemYGapAdapter.from_color_code(code)
batch_result = adapter.evaluate_decode_output(
    extra_outputs,
    return_witness=False,
)
~~~

Requirements:

- Unambiguous methods or explicit arguments for full-DEM versus sector-coordinate inputs; never infer solely from dimensions.
- Boolean or exactly binary corrections, shape validation, empty batches, and stable single-shot/batch semantics.
- Reject NaNs, infinities, invalid probabilities, and nonbinary corrections.
- Output at least `signed_gap` and model/ordering metadata.
- Optional root ID, first-option IDs, correction weight, and a sector/full-DEM logical-support witness.
- Witness reconstruction follows only the winning root/options and three tail predecessor chains.
- Preserve hard predictions and all existing decoder outputs.
- If a valid correction for the measured syndrome is required, offer validation using detector outcomes; in tests always verify it. A failed baseline correction must not be presented as confidence about a successful syndrome-consistent decode.
- No noise-parameter-dependent calibration, clipping, probability conversion, or post-selection threshold selection inside the core.
- No use of logical ground-truth outcomes in score computation.

Cache immutable geometry and junction metadata. Keys must cover exact ordered D/O column data, detector row identities/coordinates, target observable, circuit/schedule/boundary settings, graph policy, and compiler version. Cache or validate weights separately using the exact probability vector. A noise update must not reuse stale weights; a topology/order change must not reuse stale maps.

Use compact arrays for hot loops. Reuse the repository's acceleration facilities or implement compiled/JIT kernels where justified. The mathematical reference should remain readable. Do not introduce a large dependency solely to compute this metric.

### Integration example

Provide and run a small example equivalent to:

~~~python
from color_code_stim import ColorCode, NoiseModel
from color_code_stim.metrics import CircuitDemYGapAdapter

code = ColorCode(
    d=5,
    rounds=5,
    circuit_type="tri",
    temp_bdry_type="Z",
    cnot_schedule="tri_optimal",
    superdense_circuit=False,
    noise_model=NoiseModel.uniform_circuit_noise(1e-3),
    perfect_init_final=False,
    perfect_logical_initialization=False,
    perfect_logical_measurement=False,
    perfect_first_syndrome_extraction=False,
    exclude_non_essential_pauli_detectors=False,
    comparative_decoding=False,
)

# Constructing the adapter is one-time setup, outside shot timing.
adapter = CircuitDemYGapAdapter.from_color_code(code)

sampler = code.circuit.compile_detector_sampler(seed=12345)
detectors, actual_observables = sampler.sample(
    shots=1000, separate_observables=True
)
predictions, extra = code.decode(
    detectors,
    full_output=True,
    bp_predecoding=False,
    get_swim_distance=False,
)
soft = adapter.evaluate_decode_output(extra)
scores = soft.signed_gap
~~~

Verify import/export locations and exact decode arguments against the checkout. This example contains only one ordinary decode. `actual_observables` may be used for external evaluation, never by the scorer. Ordinary and already-produced comparative corrections may both be accepted, but the module itself never requests comparative decoding.

## 11. Focused validation

### A. Model and geometry

- Verify sector/full maps by parsing the exact DEM and by matrix comparison.
- Exercise detector-row and error-column permutations, including witness inverse mapping.
- Verify every transport and composite support against H and o.
- Test spatial boundaries, absent root colors, parallel supports, temporal motion in both directions, the level cut, and first-operation/tail-policy separation.
- Include an adversarial case where omitting the terminal level cut enables fault reuse; the compiler must detect it.
- Verify all-path nonreuse and cap compatibility independently.
- Reject mixed-sector models, unsupported endpoint patterns, and nontrivial zero-detector columns.

### B. Independent exact oracles

- On a tiny synthetic DEM and d=3,T=3, enumerate supports of the declared root/tail family independently and compare minimum signed costs with the production evaluator.
- Verify every enumerated/winning logical support satisfies the full embedded H/O constraints.
- Include negative, positive, zero, and tied costs. Correctly handle unreachable parity states.
- Compare the sparse junction solver with a Cartesian reference on many small synthetic option graphs. Include arbitrary pair incompatibility, all interaction-edge cases, zero numerical sharing costs, triple overlaps, the root appearing in all three first supports, isolated-option collapsing, empty parts, and infinities.
- Ensure the optimized solver preserves the exact family; a beam search, top-1-per-arm approximation, or fixed arbitrary shortlist is not a substitute.
- Optionally use a small independent MILP oracle for (24). Do not run exponential/MILP checks in production or large routine tests.

### C. End-to-end checks

- Run ordinary decoding for small supported circuits and compute scores from final `error_preds`.
- Reconstruct a selection of winning witnesses; check syndrome neutrality, observable flip, and the direct full-coordinate weight difference.
- Verify enabling postprocessing leaves the hard predictions and original extras unchanged.
- Instrument decoder entry points to establish that the scorer makes zero decoder calls.
- Verify score-only and witness-enabled modes agree.
- Verify p/geometry/cache invalidation and empty-batch handling.

### D. Preliminary reference observations, not hard-coded axioms

A previous independent audit used the supplied source snapshot, uniform circuit noise \(p=10^{-3}\), the noisy initialization/final flags above, and d=T:

| d=T | Retained Z-sector DEM columns |
|---|---:|
| 3 | 59 |
| 5 | 329 |
| 7 | 973 |

All columns had the required Type-A/Type-B structure. Nonempty signature groups had at most five columns; real c-endpoint heights in each group had at most two values, separated by three when distinct. Every audited root had at least one strong-certified cap.

For d=5,T=5, the preferred tail-enriched graphs had 511/500/545 operations for r/g/b after sink-reachability pruning, and enumerating/deduplicating strong caps for a reference oracle gave 70,755 cap/head tuples. Production scoring must not scan this tuple list.

At d=7,T=7, allowing temporal enrichment also in root first operations produced roughly 11.8 million root-choice triples after unary filtering. The specified base-root/enriched-tail policy reduced that count to roughly 0.52 million before sparse processing. These observations motivate the explicit root policy and sparse solver; they are not runtime benchmarks.

A small d=3,T=3 version without tail temporal enrichment yielded 3,337 distinct odd-observable supports; random signed-cost minima agreed with full enumeration. For the preferred d=5,T=5 construction, 20 random signed-weight witness checks satisfied full detector/observable constraints and direct weight recomputation.

These counts depend on the precise DEM/circuit/version and deduplication convention. Reproduce or explain differences; never modify a correct implementation merely to force matching counts. Finite audits do not prove all-distance degree bounds, coverage of all minimum circuit logical faults, or post-selection equivalence.

### E. Practical timing

Provide a small reproducible timing script, not a large Monte Carlo campaign:

- Report setup/certification time and peak memory separately.
- Exclude compilation/JIT warmup, sampling, plotting, and I/O from per-shot scoring time.
- Report score-only and witness-enabled timings separately.
- Compare ordinary decode, score alone on stored corrections, and ordinary decode plus score.
- If a separate forced/comparative timing is available, place it in the benchmark harness only; do not add those calls to the metric.
- Report actual graph sizes, local option/interaction counts, and the absence of root Cartesian scans.
- Use comparable batching and hardware; avoid comparing a batch scorer with a single-shot decoder unfairly.

If the implementation is slower than an additional decode, report that result and the measured bottleneck, and optimize the permitted DAG/local-join implementation. Do not claim the user's efficiency objective is met solely because the nominal scaling is linear, and do not silently change the score to a cheaper unvalidated heuristic.

## 12. Required deliverables and final report

Complete:

1. A reusable public module and minimal postdecode integration.
2. Immutable compiled geometry/certificates and the exact sparse junction kernel.
3. Focused tests with independent oracles and witness validation.
4. A standalone paper-style description containing definitions, assumptions, pseudocode, proofs, complexity, and limitations.
5. A runnable uniform-circuit-noise example and a small timing script.

In the final implementation report, state what changed, the supported model, validation results, measured timing/setup costs, and any unresolved limitations. Distinguish correctness within the retained family from empirical proxy quality. Do not claim forced-gap-equivalent post-selection performance without simulation evidence.

## References to cite accurately

- Seok-Hyung Lee, Andrew Li, Stephen D. Bartlett, *Color code decoder with improved scaling for correcting circuit-level noise*, arXiv:2404.07482, especially Section 4 and Algorithm 1: https://arxiv.org/abs/2404.07482
- Stim, *The Detector Error Model File Format*: https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md
- Nadine Meister, Christopher A. Pattison, John Preskill, *Efficient soft-output decoders for the surface code*, arXiv:2405.07433, for the soft-output motivation and the distinction between efficient confidence proxies and complementary decoding: https://arxiv.org/abs/2405.07433

The native grouping is informed by DEM decompositions in existing work. The specific base-root/enriched-tail family, strong cap certificate, signed parity-DAG evaluation, and exact sparse junction solver above are the proposed implementation specification; do not attribute their guarantees to those papers.
