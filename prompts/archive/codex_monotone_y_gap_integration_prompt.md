# Implement a modular monotone-Y signed-gap metric in color-code-stim

Implement the algorithm specified below in my fork of **color-code-stim**, as a reusable package module. Complete the implementation, focused correctness tests, documentation, and a small runnable integration example. Produce working code, not just a plan.

The objective is a soft-output score from the **already selected final physical correction**, with no additional decoder call, comparative decoding inside the metric, or iterative optimization of an opposite-class correction. Compute the score using three signed DAG dynamic programs and bounded local work per physical qubit.

This specification is the implementation contract and the basis for a paper-style algorithm description. Distinguish proved conditional statements, independently reproduced finite-size checks, and unproved generalizations. Do not present this proposal as a published algorithm or claim forced-gap-equivalent post-selection performance without evidence.

## 1. Repository grounding and scope

Work in the supplied checkout of my fork, normally `AKTKN/color-code-stim`. Read applicable `AGENTS.md`, package metadata, relevant source, and nearby tests. Preserve unrelated work. Treat the actual checkout as authoritative if its APIs have changed.

The supplied source snapshot has these contracts; verify them before reuse:

| File or component | Relevant contract |
|---|---|
| `src/color_code_stim/color_code.py` | `ColorCode` constructs the code and exposes `decode`, `tanner_graph`, `qubit_groups`, circuit/DEM information, and lazy decoder instances. |
| `graph_builder.py` | `TannerGraphBuilder` constructs the triangular lattice. Data vertices have `pauli=None`; check vertices have `pauli="Z"` or `"X"`. |
| Tanner vertex metadata | Stable `qid`, `name`, `x`, `y`, `boundary`. Check vertices additionally have `face_x`, `face_y`, and `color`. Check drawing coordinates are shifted relative to face centers. |
| Tanner edge metadata | `kind="tanner"` denotes check-data incidence; `kind="lattice"` denotes physical lattice links. |
| `decoders/concat_matching_decoder.py` | `ConcatMatchingDecoder.decode(..., full_output=True)` returns final DEM-coordinate corrections in `extra_outputs["error_preds"]`, after color/class selection and predecoding composition. |
| Decoder extras | `best_colors` and `weights` describe decoder choices. They must not determine metric geometry; matching weights must not replace physical correction weights. |
| `dem_utils/dem_manager.py` | `DemManager` supplies `dem_xz`, detector matrix `H`, `obs_matrix`, probabilities, and detector-to-check metadata. |
| `stim_utils.py` | `dem_to_parity_check` flattens the DEM and assigns columns to **error instructions only**, not all raw DEM instructions. |
| Legacy soft output | `get_swim_distance`, notebook graph builders, and modified PyMatching calls implement separate algorithms. Do not enable, replace, or depend on them. |

If the checkout exposes `ColorCode.errors_to_qubits`, inspect and verify its indexing before reuse. Its name alone is not evidence of a correct map.

Initial physical adapter scope:

- Standard triangular 6.6.6 color code, odd `d >= 3`.
- `circuit_type="tri"`, `rounds=1`, Z-memory (`temp_bdry_type="Z"`).
- `cnot_schedule="tri_optimal"`, `superdense_circuit=False`.
- Independent data-qubit X noise: `NoiseModel(bitflip=p)`, `0 < p < 1/2`.
- All other effective noise channels, including granular overrides, are zero.
- Verify that the circuit has the intended single data-X-error layer. In the supplied snapshot, `perfect_first_syndrome_extraction=True` suppresses first-round bit-flip noise; do not accidentally construct a noiseless experiment.
- Multi-round, phenomenological, circuit-level, depolarizing, cultivation/growing, rectangular, and 4.8.8 adapters are outside this first implementation. Reject unsupported configurations clearly.
- The mathematical core must nevertheless accept arbitrary finite nonnegative physical weights, including zero weights, for explicit inputs and deterministic tests.

The physical-correction API must be decoder-independent. Ordinary and comparative concatenated-MWPM outputs may both be inputs, but the scorer itself must never perform comparative decoding.

## 2. Mathematical setting and target quantity

Let \(Q\) be the physical data-qubit set, \(n=|Q|\), and

\[
H_Z\in\mathbb F_2^{m\times n}
\]

the **physical Z-check incidence matrix**, not the circuit detector matrix. Let \(\ell_Z\in\mathbb F_2^n\) represent a physical logical-Z observable, and let \(E\in\mathbb F_2^n\) be the final X correction from the chosen decoder.

For independent X errors, use natural-log weights

\[
w_q=\log\frac{1-p_q}{p_q},\qquad
W(F)=\sum_{q:F_q=1}w_q.
\]

The physical adapter uses \(p_q=p\). Explicit core inputs may include \(w_q=0\).

Define signed qubit costs

\[
a_q(E)=(1-2E_q)w_q.
\tag{1}
\]

Cast Boolean/unsigned corrections to a signed or floating dtype before evaluating \(1-2E_q\), avoiding unsigned underflow. For every binary support L,

\[
\sum_{q:L_q=1}a_q(E)=W(E\oplus L)-W(E).
\tag{2}
\]

Define the nontrivial X-logical support family

\[
\mathscr L=\{L:H_ZL=0,\;\ell_Z^\mathsf TL=1\}
\tag{3}
\]

and the exact correction-relative complementary gap

\[
\Delta_E=\min_{L\in\mathscr L}\sum_{q:L_q=1}a_q(E).
\tag{4}
\]

The algorithm minimizes over an explicitly restricted family
\(\mathscr Y_{\rightarrow}\subseteq\mathscr L\):

\[
S_{\mathrm Y}(E)
=\min_{L\in\mathscr Y_{\rightarrow}}\sum_{q:L_q=1}a_q(E).
\tag{5}
\]

Do not zero costs on E, subtract \(W(E)\) again, take an absolute value, clip negative scores, average three color scores, or reinterpret this as a posterior probability.

If \(m_0,m_1\) are the minimum correction weights in the same/opposite logical classes relative to E, then

\[
\Gamma=m_1-m_0,\quad
\eta=W(E)-m_0\ge0,\quad
\rho_{\mathrm Y}=S_{\mathrm Y}-\Delta_E\ge0,
\]

\[
S_{\mathrm Y}=\Gamma-\eta+\rho_{\mathrm Y}.
\tag{6}
\]

Thus \(S_{\mathrm Y}\) upper-bounds \(\Delta_E\), not necessarily \(\Gamma\). It is not a class-summed posterior log-odds.

## 3. Canonical geometry and mapping to the fork

### 3.1 Physical ordering

Choose a documented canonical ordering, preferably sorted stable data-qubit `qid`. Store explicit maps between canonical data columns, physical `qid`/name, geometric coordinates, and DEM error-only columns where the adapter establishes that mapping.

Do not use mutable igraph indices after graph deletion as physical identities. Build \(H_Z\) using Z-check/data `kind="tanner"` incidences. Obtain the physical logical-Z vector independently from the code's observable support, verifying the convention.

### 3.2 Coordinate conversion

Let

\[
B=\frac{3(d-1)}2.
\]

For package data coordinates \((x,y)\), define canonical integer coordinates

\[
u=B-y,\qquad v=\frac{x-2y}{4}.
\tag{7}
\]

For check faces, use `face_x, face_y`, **not** shifted ancilla drawing coordinates.

The patch domain is \(0\le v\le u\le B\). Face positions satisfy
\((u+v)\bmod3=2\); other positions are data qubits. For the inspected builder,

\[
u\bmod3=0\mapsto g,\quad
u\bmod3=1\mapsto r,\quad
u\bmod3=2\mapsto b.
\tag{8}
\]

This differs from some reference numeric-color conventions; do not assume reference color 0 means package color r.

Define normalized boundary coordinates

\[
h_r=B-u=y,\qquad
h_g=v=\frac{x-2y}{4},\qquad
h_b=u-v=\frac{4B-2y-x}{4}.
\tag{9}
\]

Their sum is B. The c-boundary is \(h_c=0\), the boundary missing c-colored checks. This matches package boundaries r at \(y=0\), g at \(x=2y\), and b at \(x=4B-2y\).

Verify these formulas against the checkout. Adapt through a verified equivalent map if representation changed; do not silently change the logical-support family.

### 3.3 Incident real and virtual faces

For a data site \((u,v)\), consider

\[
(u-1,v-1),\;(u-1,v),\;(u,v-1),\;
(u,v+1),\;(u+1,v),\;(u+1,v+1).
\]

Retain positions satisfying the face congruence. There is one incident face of each color under (8); denote it \(f_c(q)\).

An in-patch face is a real check. An out-of-patch face is a virtual endpoint at the corresponding color boundary. Retain its coordinates and color when constructing/orienting edges. It is an absorbing zero-distance terminal, never a transit vertex.

If \(f_c(q)\) is virtual, the c-arm at q is empty. This handles boundary sites and corners.

Independently check the real-face incidences against \(H_Z\). Never insert virtual faces as physical stabilizer constraints.

## 4. Pair graphs and directed paths

For each color c, construct \(G_c\) with real c-faces and the needed virtual c-faces as vertices. Each edge e has an immutable two-qubit support

\[
Q_c(e)=\{q_1,q_2\}.
\]

Use this canonical construction, matching the proposed reference family:

1. Group data qubits by identical **real-check incidence signatures in the other two colors**.
2. A group of size two defines one pair edge.
3. Its endpoints are \(f_c(q_1)\) and \(f_c(q_2)\).
4. Omit the singleton at the c-corner from the pair graph: the root singleton in the Y construction accounts for it.
5. Reject unexpected group sizes or inconsistent incidences. Preserve parallel edges and their distinct physical supports.

Independently verify for every pair

\[
H_Z\,\mathbf1_{Q_c(e)}
=
\mathbf1_{f_c(q_1)\text{ real}}
\oplus
\mathbf1_{f_c(q_2)\text{ real}},
\tag{10}
\]

where the right-hand side uses physical check rows. Cross-check existing lattice links where appropriate, but do not lose boundary pair operations or parallel supports by simplification.

Retain orientation \(z\to z'\) exactly when

\[
h_c(z')<h_c(z),\qquad
h_{c'}(z')\ge h_{c'}(z)\quad(c'\ne c).
\tag{11}
\]

The tail is real; the head may be real or a virtual c-face. Exclude edges without a permitted orientation from the declared family.

Call the result \(G_c^\rightarrow\). Strict decrease of \(h_c\) makes it acyclic. Precompute the reverse topological evaluation order once.

Verify that, within a color, pair supports partition participating qubits into disjoint pairs, apart from the omitted corner. This makes a single arm's cost the sum of its pair-edge costs.

## 5. Monotone-Y supports and separation

For root \(q\in Q\), let \(P_c\) be any directed path from \(f_c(q)\) to a virtual c-face, or the empty path when \(f_c(q)\) is virtual. Lift each path by XOR of its pair supports.

Define

\[
L(q,P_r,P_g,P_b)
=\{q\}\oplus P_r\oplus P_g\oplus P_b.
\tag{12}
\]

All such supports constitute \(\mathscr Y_\rightarrow\). Multiple descriptions of the same support do not affect the minimum.

### Proposition 1: logical validity

Every support in (12) is syndrome-free: the c-arm cancels the root's c-check syndrome and terminates at a boundary missing that charge. Each pair changes support parity by an even amount, so the full support has odd cardinality. For the specified one-logical-qubit triangular self-dual CSS code with even-weight stabilizers, it is nontrivial.

Document this argument and independently verify witnesses using

\[
H_ZL=0,\qquad \ell_Z^\mathsf TL=1.
\tag{13}
\]

Odd cardinality is not a substitute for verifying the physical observable mapping.

### Required geometric separation condition

Acyclicity alone is insufficient for the fast exact recurrence.

For each q, remove the first edge of every nonempty arm. Require, for **every admissible combination of arms**, that:

- the remaining tails have pairwise disjoint physical supports;
- these tails are disjoint from the root and all first-edge physical supports;
- a single arm never uses a physical qubit twice.

All inter-arm cancellations are then confined to the root/first-edge neighborhood.

This condition was checked in a preliminary reference construction at selected finite distances. Do not assume it holds on arbitrary lattices. Establish it for the package geometry by a coordinate/local-pattern argument and an independent geometry checker.

A sufficient offline checker can compute possible tail supports by DAG reachability and check intersections. It must cover **all possible paths**, not just paths selected by one random weight vector. Report and cache its actual setup complexity separately; prefer local-pattern certification once justified.

Do not enumerate all paths during production scoring. Do not approximate XOR by union. If separation fails, identify the root, colors, edges, and shared qubit. Fix a demonstrated mapping/boundary error and recheck. Do not silently omit templates, use independently optimized overlapping arms without their cancellations, or substitute a different metric. Report a genuine failure of the specified geometric condition explicitly.

## 6. Signed dynamic program

For fixed E, form the signed costs (1) and pair-edge costs

\[
A_c^E(e)=\sum_{z\in Q_c(e)}a_z(E).
\tag{14}
\]

Set virtual distances to zero and compute in reverse topological order

\[
D_c(z)=\min_{e:z\to z'}
\left[A_c^E(e)+D_c(z')\right].
\tag{15}
\]

Negative costs are allowed. Dijkstra is neither needed nor appropriate. Use \(+\infty\) for unreachable real states; validate expected reachability at setup. Unknown real vertices must never inherit terminal cost zero.

For each root q, let \(\alpha\) choose the first edge \(e_c\) of every nonempty arm. An already-virtual incident face has one empty-arm option. Let \(t_{\alpha,c}\) be the chosen edge head or an empty-arm terminal.

Precompute local XOR supports

\[
J_{q,\alpha}
=\{q\}\oplus
\bigoplus_{c:e_c\text{ nonempty}}Q_c(e_c).
\tag{16}
\]

Store J as canonical physical column IDs after parity cancellation. Its size is at most seven. A qubit appearing four times cancels completely.

Compute

\[
V_{q,\alpha}(E)
=\sum_{z\in J_{q,\alpha}}a_z(E)
+\sum_c D_c(t_{\alpha,c}),
\tag{17}
\]

\[
S(q)=\min_\alpha V_{q,\alpha}(E),\qquad
S_{\mathrm Y}(E)=\min_q S(q).
\tag{18}
\]

The reference geometry has two outgoing choices per interior face and at most three near boundaries: ordinarily eight root configurations and at most 27. Derive counts from geometry and verify the bound; never truncate a larger set silently.

### Proposition 2: exactness within the family

Assume logical validity, within-color pair disjointness, and the separation condition. For a fixed root/template, every remaining physical contribution belongs to exactly one tail. Its signed cost is additive, so independently minimizing the tails is valid. Equation (15) gives those exact minimum costs. Minimizing (17) over templates/roots yields precisely (5).

Include this proof. Acyclicity alone does not prove exactness; separation is essential.

### Proposition 3: complementary-gap relation

Since \(\mathscr Y_\rightarrow\subseteq\mathscr L\),

\[
\Delta_E\le S_{\mathrm Y}(E).
\tag{19}
\]

For an opposite-class syndrome-consistent correction F, if
\(E\oplus F\in\mathscr Y_\rightarrow\), then

\[
\Delta_E\le S_{\mathrm Y}(E)\le W(F)-W(E).
\tag{20}
\]

Apply this to a forced-decoding candidate only after verifying the physical map and membership premise. The package's `extra_outputs["logical_gaps"]` may use a different baseline or matching weights; do not assume it equals the right side.

If a globally minimizing complementary support is retained, \(S_{\mathrm Y}=\Delta_E\). Do not assert equality for arbitrary corrections.

### Proposition 4: complexity

For \(K_q\) first-edge templates at root q, per-shot work is

\[
O\!\left(n+\sum_c(|V_c|+|E_c|)+\sum_qK_q\right).
\tag{21}
\]

Bounded-degree 6.6.6 graphs and bounded template size/count give \(O(n)\) time and \(O(n)\) working memory. B-shot output storage adds \(O(B)\); chunked batches may use \(O(bn)\) workspace for chunk size b.

Separate setup, geometry certification, DEM mapping, and online cost. Asymptotic notation alone does not establish a speedup over optimized matching.

### Algorithm 1: geometry compilation

~~~text
Input: supported physical Tanner graph, distance, physical logical observable
Output: immutable geometry and template tables

1. Choose canonical stable data-qubit ordering.
2. Build physical Z-check incidence; verify coordinate conversion.
3. Determine f_c(q), preserving real/virtual identity and geometry.
4. Build pair graphs from other-two-color incidence signatures.
5. Verify pair syndromes and preserve parallel physical supports.
6. Orient by (11); verify DAGs and boundary reachability.
7. Verify within-color pair disjointness and geometric separation.
8. Store evaluation orders, adjacency arrays, and pair-support indices.
9. For every root q and first-edge choice alpha:
       J <- XOR of {q} and selected first-edge supports
       store J and the three tail-start IDs
10. Return geometry, ordering, scope, and certification metadata.
~~~

### Algorithm 2: score evaluation

~~~text
Input: compiled geometry, final physical correction E, physical weights w
Output: signed score; optional minimizing witness

1. Validate E and w; form a = (1 - 2*E) * w in a signed dtype.
2. For each color:
       set virtual-terminal distances to zero
       for real vertex v in reverse topological order:
           D_c[v] <- min over outgoing e=(v,u):
                         a[q1(e)] + a[q2(e)] + D_c[u]
           optionally store the argmin edge
3. best <- +infinity
4. For each precompiled template (q, alpha):
       value <- sum(a[z] for z in J[q,alpha])
                + sum_c D_c[tail_start[q,alpha,c]]
       update best with a documented deterministic tie rule
5. If requested, trace only the selected tails and XOR with J.
6. Return best and requested diagnostics.
~~~

Do not propagate full physical support bitsets through the production DP. Store scalar distances and optional predecessor edge IDs. Reconstructing the one winning physical witness is optional and linear-time.

## 7. Module design and public API

Use an existing appropriate namespace or create, for example:

~~~text
src/color_code_stim/metrics/
    __init__.py
    monotone_y_gap.py
    _monotone_y_geometry.py
    _physical_correction_adapter.py
~~~

Equivalent focused organization is acceptable. Do not implement only in notebooks or depend on `my_graph_builder.py`.

Separate immutable geometry, ordering/configuration adapters, the numerical kernel, and optional diagnostics. Provide a reusable interface equivalent to:

~~~python
geometry = MonotoneYGapGeometry.from_color_code(code)
metric = MonotoneYGapEvaluator(geometry, weights=physical_weights)

single = metric.evaluate(E_physical, return_witness=False)
batch = metric.evaluate_batch(E_physical_batch, return_witness=False)

adapter = MonotoneYGapAdapter.from_color_code(code)
scores = adapter.evaluate_decode_output(extra_outputs, return_witness=False)
~~~

These names specify proposed **new** APIs, not existing methods. Adapt naming to repository conventions while preserving responsibilities.

Requirements:

- Corrections: `(n,)` or batches `(shots,n)`. Weights: `(n,)`; a documented scalar-uniform constructor is acceptable.
- Accept Boolean or exact binary integer corrections. Reject nonbinary values, wrong shapes, invalid weights, NaNs, and infinities.
- Handle empty batches without fabricated corrections or zero scores.
- Return at least `signed_gap` and canonical ordering metadata, directly or through the evaluator.
- Optional results: deterministic root/template ID, `correction_weight`, per-root minima, internal distance fields, physical logical-support witness.
- Keep expensive diagnostics out of normal batch output.
- There is no “winning color” for a three-color Y-net. Do not label the score as the minimum of three independently computed logical gaps.
- `correction_weight` is diagnostic and is not subtracted again.
- Preserve weights, geometry, corrections, and all decoder outputs.
- Use deterministic ties; alternate witnesses must not change the minimum value.
- Precompile compact arrays. Avoid per-shot sorting, graph rebuilding, or dictionary-heavy geometry work.
- Reuse existing acceleration facilities if available; do not require a heavyweight new dependency without a concrete need. Retain a readable reference implementation for tests.

## 8. Integration after final correction selection

Use postprocessing as the primary integration:

~~~python
from color_code_stim import ColorCode, NoiseModel
from color_code_stim.metrics import MonotoneYGapAdapter

code = ColorCode(
    d=7,
    rounds=1,
    circuit_type="tri",
    temp_bdry_type="Z",
    cnot_schedule="tri_optimal",
    superdense_circuit=False,
    noise_model=NoiseModel(bitflip=0.01),
    perfect_first_syndrome_extraction=False,
    comparative_decoding=False,
)
adapter = MonotoneYGapAdapter.from_color_code(code)  # cached setup
det, obs = code.sample(shots=100, seed=12345)
pred, extra = code.decode(
    det,
    full_output=True,
    concat_unionfind=False,
    get_swim_distance=False,
)
result = adapter.evaluate_decode_output(extra)
scores = result.signed_gap
~~~

Update this example to the implemented API and execute it.

Do not reuse `get_swim_distance=True` as the new trigger. The supplied fork invokes legacy soft-output behavior during stage 2 and feeds its values through selection-related arrays. Score **after normal hard correction selection**.

A minimal `ColorCode` convenience method is acceptable, but the standalone reusable module and postprocessing path are mandatory. If adding an opt-in decode wrapper, score once after all color/class selection, predecoder merges, and partial-correction composition; preserve defaults and existing extras.

### DEM-to-physical mapping

`extra_outputs["error_preds"]` follows the original flattened DEM's **error-only column order**. Equal column counts do not establish physical-qubit order.

Build or verify an explicit map for the supported single X-error layer. Evidence can include circuit error locations and independently checked detector/observable signatures. Never infer the map from raw instruction positions.

Validate:

- each physical X operation's detector signature;
- its physical Z-check syndrome;
- logical-observable parity;
- probabilities and the single-layer noise model.

Keep \(H_Z\), \(H_{\rm det}\), and the DEM observable matrix distinct. Comparative decoding can introduce observable-related detector bookkeeping; account for it explicitly.

If a column has ambiguous physical realizations or represents a non-single-qubit fault, do not arbitrarily choose a qubit. Establish uniqueness for the supported adapter or report a precise unsupported map. A general fault-to-qubit XOR map does not automatically preserve additive physical likelihood weights.

Always use the fully assembled final `error_preds`, not per-color candidates, stage-1 output, or `best_colors`. Do not replace the hard correction using the minimizing Y-net or change hard predictions when scores are negative.

Never use sampled true errors or failure labels to compute scores.

## 9. Focused validation

Use independent oracles, not tests that merely restate the implementation.

### A. Geometry

- At d=3,5,7, independently construct physical check/observable incidence and verify the coordinate map.
- Verify pair syndromes, boundaries, virtual endpoints, parallel supports, singleton corners, and DAG orientation.
- Check separation across possible paths, including boundary/corner cases.
- Deliberately malformed geometry must fail clearly.
- Add larger geometry-only cases such as d=9,15,31 without exponential logical enumeration.

### B. Exact restricted-family oracle

For small codes, independently enumerate directed arms, XOR their physical supports using (12), deduplicate, and minimize signed costs directly. The oracle must not call the production DP/template scorer.

- At d=3, test all \(2^7\) correction masks.
- Include nonuniform and zero physical weights.
- At d=5,7, compare selected deterministic/random signed-weight cases to restricted-family enumeration where tractable.
- Test a junction where q appears four times and cancels, pairwise first-edge overlap, and empty boundary arms.
- Verify each optional witness using (13) and recompute \(W(E\oplus L)-W(E)\) independently.

### C. Finite-size reference observations

A previous exploratory implementation produced:

| Distance | Distinct directed-Y supports | Minimum-weight nontrivial X-logical supports | Minimum-weight supports covered |
|---|---:|---:|---:|
| 3 | 8 | 7 | 7 |
| 5 | 69 | 36 | 36 |
| 7 | 308 | 140 | 140 |

These are observations to **reproduce independently**, not axioms or targets that justify modifying the geometry. Explain discrepancies before making claims.

Use full logical enumeration at d=3 to verify (19). Keep larger unrestricted enumeration in an optional small-code validation script. Do not claim all-distance minimum-weight coverage or equality with the full complementary gap.

### D. Analytic checks

- Uniform w and \(E=\varnothing\): global score \(dw\), since a weight-d corner path is retained and no nontrivial support is lighter. Not every root must have value \(dw\).
- If E itself is retained in the Y family, \(S_{\mathrm Y}(E)=-W(E)\).
- Uniform positive w: \(S_{\mathrm Y}/w\in2\mathbb Z+1\), up to floating tolerance.
- Uniform w:
  \[
  dw-2w|E|\le S_{\mathrm Y}(E)\le dw.
  \]
- Explicit negative-score and unequal-weight fixtures.
- Correct unreachable-state treatment: no unknown real state may default to terminal cost zero.

### E. Integration/cache tests

- DEM column permutations and inserted non-error DEM instructions.
- Ordinary/comparative correction sources, unchanged hard predictions.
- A fixture with different intermediate color corrections: all three DAGs use the same final physical E.
- A composed-correction postprocessing fixture; irrelevant intermediate metadata cannot affect fixed-E scores.
- Single/batch equivalence, row permutation, empty batch, E1/E2/E1 order, input immutability, cache reuse.
- Unsupported effective noise/round/geometry and invalid input diagnostics.
- Normal upstream PyMatching for relevant integration tests; no modified legacy swim backend.

Run focused tests and the relevant existing suite. Report unrelated pre-existing failures separately. Do not weaken invariants or silently change the metric to pass tests.

## 10. Documentation, runtime evidence, and completion

Add a paper-style note, e.g. `docs/monotone_y_signed_gap.md`, with:

1. physical assumptions and notation;
2. coordinate, pair, and DAG construction;
3. restricted Y family and separation condition;
4. propositions and concise proofs;
5. Algorithms 1 and 2;
6. preprocessing versus online complexity;
7. APIs, ordering contracts, runnable example;
8. verified finite-size facts and unproved extensions.

The approximation is restricted geometry: monotone arms and one Y junction. Signed cost evaluation is exact inside the family once separation is established.

Provide one small runnable example importing the module. Include an inexpensive timing comparison with normal decoding and, only if readily available, an existing forced-gap calculation. Reuse the same final corrections when comparing score costs. Separate warm-up/compilation, setup, mapping, and per-shot evaluation; report batch size and environment. Large Monte Carlo/post-selection runs are not prerequisites for this implementation.

O(n) alone does not prove smaller wall-clock time than every decoder. Report measured constants honestly. No local-stabilizer descent, BP iteration, matching, HUF growth, LP/MILP, or unrestricted signed shortest-path solver belongs in the online scorer.

Finish with the public API/example, geometry/separation argument and validation status, final-correction mapping, test results, setup/online complexity and timing, changed files, and concrete limitations.

## References and attribution

Use these only for the structures they establish:

- Lee, Li, and Bartlett, *Color code decoder with improved scaling for correcting circuit-level noise*, Definition 2 and Appendices A/C:
  https://arxiv.org/html/2404.07482v2
- Kesselring et al., *The boundaries and twist defects of the color code and their applications to topological quantum computation*:
  https://arxiv.org/abs/1806.02820
- Meister, Pattison, and Preskill, *Efficient soft-output decoders for the surface code*:
  https://arxiv.org/abs/2405.07433
- Standard triangular 6.6.6 coordinates:
  https://qecsim.github.io/api/models/color.html

The signed monotone-Y recurrence is the proposed construction specified here. Do not attribute its correctness, all-distance coverage, runtime, or post-selection quality to these papers.
