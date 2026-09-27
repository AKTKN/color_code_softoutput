# PROJECT_DETAIL.md

## Circuit DEM-Y signed-gap implementation — 2026-09-19

The new authorization implements a distinct circuit-level logical support
family in the existing monotone-Y feature worktree. Its dependency chain is
exact ordered separated DEM and sector maps → original-column native transports
→ independently pruned base-root and enriched-tail DAGs → all-suffix fault
nonreuse → strong unary/pair cap separation → signed parity DP and exact sparse
junction minimization → a final-correction score and optional full DEM witness.
The offline compiler releases global fault-union bitsets after certification;
preprocessing can use quadratic storage. Online linear scaling is conditional
on bounded local circuit structure, not inferred from the finite count audit.

Ten proved conditional propositions, definitions and pseudocode are in
`external_libs/color-code-stim-monotone-y/docs/circuit_dem_y_algorithm.tex` and
its standalone PDF. On each accepted geometry `Delta_E,Z <= S_DEMY` follows
from family inclusion; `S_DEMY=Gamma-eta+rho` retains both baseline suboptimality
and restricted-family effects. Existing decoder logical_gaps are not identified
with these quantities. Native scoring remains slower than ordinary decoding in
the bounded measurements. See `notes/support/CIRCUIT_DEM_Y.md` for implementation,
independent oracle acceptance, exact scope and unresolved scientific limits.
No earlier SWIM or code-capacity theorem, source or dataset is changed.


## Monotone-Y numerical workflow — 2026-09-19

The user-authorized extension adds the existing experiment/analysis workflow
to the monotone-Y package: certified final-correction adapter → paired
ordinary/comparative sampler → versioned signed Parquet columns → shared
failure-aware distributions, conditional LER/logistic fits, threshold and
matched-retention analyses. The isolated metric loader preserves installed
decoder imports. Deterministic batch IDs/seeds, bounded process scheduling,
source snapshots and first-batch-per-point replay reuse existing infrastructure.
The notebook mirrors the current path-gap settings; acceptance uses 768 shots.
No mathematical claim or empirical superiority result is added. See
`notes/support/MONOTONE_Y_EXPERIMENT.md` and `STATUS.md`.

## Monotone-Y signed-gap implementation — 2026-09-19

The new prompt authorizes a distinct three-arm, one-junction physical logical
family, without changing the earlier SWIM/path-gap constructions. The
dependency chain is physical incidence and observable verification → canonical
pair DAGs → per-geometry local coordinate separation certificate → exact signed
tail recurrence and first-edge XOR templates → final DEM-correction adapter.
The user's requested pre-implementation review is in
`notes/support/MONOTONE_Y_THEORY_AUDIT.md`.

For every accepted geometry, the conditional proof establishes that the
returned score minimizes W(E xor L)-W(E) over the declared restricted family.
It upper-bounds correction-relative Delta_E; S_Y=Gamma-eta+rho_Y does not give
an unconditional bound on the exact class-minimum gap Gamma. The physical
observable and one-qubit CSS quotient are explicitly checked. No SWIM dual,
matching radius or sampled error is used. Negative results do not alter E.

Reusable code, paper-style algorithm note, independent finite oracles and
small examples live in `external_libs/color-code-stim-monotone-y/`, on
`feature/monotone-y-gap` based on clean origin/main. All-path geometry checks
pass d=3,5,7,9,15,31; exhaustive small logical-coset enumeration reproduces
the reference 8/69/308 family and 7/36/140 minimum-support coverage counts.
This is finite coverage evidence, not an all-distance coverage theorem.
The adapter is restricted to one triangular Z-memory data-X layer; the core
accepts arbitrary finite nonnegative weights. See STATUS.md for acceptance.

## Path-overlap revision — 2026-09-19

The separately authorized feature-branch update changes only post-Dijkstra
subtraction to W(E intersect L_c), on the returned path for the same final E.
All three scores precede color selection. The metric is `path_overlap_v2`;
legacy saved runs keep their global-subtraction v1 meaning. No physical-model
restriction, decoder, topology or theorem has changed. See STATUS.md.

## Path-gap numerical workflow — 2026-09-19

Environment follow-up: the default is now ordinary `color_code_so`, with the
feature metric's source loaded under an isolated namespace. Installed SWIM
decoder/backend imports and all external source trees remain unchanged. Both
source origins are tracked in provenance; no algorithm copy is maintained.

The user additionally requested the same experiment as the Phase-2A Getting
Started notebook using the new metric, especially post-selection performance.
`notebooks/path_gap_getting_started.ipynb` is the thin entry point for a new
streaming experiment in `src/color_code_softoutput/experiments/path_gap_test.py`.
It consumes the feature worktree package without modifying either SWIM
checkout. Shared statistical and plotting functions retain their old defaults;
new named-score parameters preserve explicit decoder/failure associations.
The default grid is six distances times ten probabilities, 6M physical shots;
only its 7,680-shot functional smoke was executed during implementation.
Whole-tie threshold and shot-ID-tiebroken equal-retention analyses have distinct
documented semantics. This extends the numerical workflow, not any theorem.
See `notes/support/PATH_GAP_EXPERIMENT.md` and STATUS.md for acceptance.

## Final-correction monochromatic path gap — 2026-09-18

The user separately authorized the full prompt under
`prompts/codex_monochromatic_path_gap_prompt.md`. The installable feature is
in `external_libs/color-code-stim-path-gap/src/color_code_stim/metrics/`, based
on origin/main rather than earlier SWIM implementations. It uses physical
colored primal-edge incidence, degree-two suppression with immutable physical
supports, two distinct terminals, and igraph nonnegative shortest paths.
The same returned FINAL correction is mapped once from error-only DEM columns
and supplied to all three colors. The complete original physical correction
weight is subtracted once. This scope expressly includes the prompt's minimum
over colors, as a new heuristic definition rather than a theorem about SWIM.

Only triangular odd-distance 6.6.6, tri_optimal, one extraction round, Z memory
and one independent data-X layer are supported by the adapter. Topology/core
and DEM mapping are separable; normal upstream PyMatching suffices. Independent
Steane face-incidence path enumeration tests all 128 masks and unequal weights;
d=5 independent coordinates and d=3,5,7 physical matrices check the topology.
The evaluation compares phi, D_min and -W on identical corrections/labels,
with ordinary and comparative decoding as separate cohorts. The exact d=3
class minima are not posterior odds; the signed quantities stay distinct.
See [API and evaluation guide](external_libs/color-code-stim-path-gap/docs/monochromatic_path_gap.md).

## Comparative correction-origin colors — 2026-09-18

For each saved circuit-memory shot, let `w[l,c]` be the existing comparative
decoder's correction weight with its single observable forced to logical class
`l in {0,1}` and its concatenated branch restricted to `c in {r,g,b}`.  The
baseline class is the class containing the global minimum of this 2-by-3 array;
the forced class is its complement.  `baseline_color` and `forced_color` are the
within-class minimizers.  This reproduces the external implementation's flat
class-major, rgb-minor `argmin` tie convention.  The reconstructed baseline
class and `min_c w[forced,c] - min_c w[baseline,c]` must equal the saved
comparative prediction and nonnegative forced gap.

The six weights were absent from the original raw schema, so deterministic
seed replay writes them to separate companion shards rather than mutating the
archived shot data or external decoder.  This is an implementation-level audit
of which branch supplied each of the two minima.  It does not define a new
decoder, alter the gap, or establish a theorem about color aggregation.

## Empirical three-color selection study — 2026-09-16

The separately requested saved-data notebook evaluates four scalar maps from
the same per-shot branch vector `(phi_r,phi_g,phi_b)`: the ordinary selected
branch, coordinatewise minimum, coordinatewise maximum and arithmetic mean.
It holds the physical sample, hard prediction and ordinary failure label fixed.
Thus observed differences in distribution, conditional LER and retention curves
come only from ranking/grouping shots by a different derived scalar.

This is an analysis layer over existing circuit-level data. It neither changes
the fixed-fiber per-color definition nor supplies a theorem connecting any
aggregate to the comparative gap or full physical logical quotient. The source
Parquet shards remain immutable. The reusable adapter exposes the derived score
under the existing plotter interface, allowing exact reuse of rounding,
statistics, Wilson intervals and post-selection semantics. See
[the notebook](notebooks/circuit_level_swim_selection_strategies.ipynb) and
`analysis/swim_selection.py` for the executable definitions.

## Surface-code companion — 2026-09-16

A separately requested companion under `surface_code_test/` now applies the
existing PyMatching SO_example circuit/hard graph to closed rotated-surface-code
X memory. Its pipeline is original noisy circuit → existing pruned/merged hard
graph → checked internal label gauge → paired ordinary swim and forced-class
minimum gap → shared raw-data storage and statistical plots. It does not alter
the color-code proofs, decoder matrices or selected-color convention.

The default circuit uses p=.001 and 2d explicit extraction rounds, with an
additional extraction inside the example's X-init gadget. Both surface scores
use the same ordinary hard decisions and physical shots. The checked balanced
cut supports an extra constrained logical-parity row for complementary gap;
independent exhaustive and integer-program checks validate that construction.
No physical observable is supplied to the score calculation. Details and
validation are in [surface_code_test/VALIDATION.md](surface_code_test/VALIDATION.md).
The modern generic growth API remains uncertified; no posterior interpretation,
family-wide topology result, threshold or window support is added.


## Closed-memory implementation — current handoff, 2026-09-16

The [implementation prompt](prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md)
superseded the theory-only production stop for fully terminated triangular Z
memory. The dependency chain is now executable: actual public effective H2/L2
and source metadata → immutable completed labelled multigraph → class existence
and internal balance → cached cut or exact same-base-vertex cover → original
graph growth-ball residuals → verified original-column logical witness.
No proof assumption is inferred from coordinates. An absent class yields no
analysis topology, infinity and no witness; odd zero-cost mechanisms survive.

`CircuitLevelDecoder` returns the existing ordinary hard result and replays its
frozen public matrices solely to obtain growth through the Phase-2A generic API.
Exact equality of hard predictions, weights, selected colors and corrections
is mandatory. This additional decode work is included in the reported runtime;
no negligible-overhead claim is made. `selected_swim_distance` is the ordinary
selected branch. Comparative decoding uses the same physical shots and its own
failure labels. Existing batching/seeding/storage/analysis is extended in place.

The d=3,5,7 validation found all nine graphs balanced and completed 6,000 shots
with no hard mismatches. This is finite implementation evidence. Current growth
is not an optimal odd-cut dual; the conditional certified theorem is unchanged.
See [implementation report](notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md) for
file inventory, gates, runtime, saved data and source limitations. The compact
algorithm is integrated in the main note. Open temporal boundaries/sliding
windows require a separate next authorization; no new aggregation is defined.

The 2026-09-12 theory handoff and earlier stages below remain historical.


Historical theory milestone: 2026-09-12. Phase 1 complete (Tasks 1–7).
The authoritative derivation is [notes/note.tex](notes/note.tex), with
[compiled PDF](notes/note.pdf). The final audit is in [REVIEW.md](REVIEW.md).

## Circuit-level extension — current theory handoff

The separately authorized [circuit prompt](notes/support/CODEX_CIRCUIT_LEVEL_THEORY_PROMPT.md)
is implemented in Part II of [the integrated note](notes/note.tex), sourced in
[the circuit TeX section](notes/support/circuit_level_theory.tex), with
[readable summary](notes/support/CIRCUIT_LEVEL_THEORY.md). This changes the
theoretical scope beyond Phase 1; it does not authorize production circuit
integration or a new numerical campaign. Earlier stop statements below are
historical milestones.

The dependency chain is exact DEM record/target algebra → actual Lee
Pauli/color decomposition and source-map audit → fixed-fiber logical quotient
and rank criterion → logical cochain → residual minimum → logical binary
cover (or a gated two-terminal cut) → certified representative inequality.
The controlled one-data-layer perfect-measurement limit has the exact
Phase-1 detector map, logical parity and metric under identical coverage.

The general cover is geometry independent and costs
O(n(m+n)log(2+n)) for a straightforward n-source implementation, excluding
coverage/certificate extraction. The faster cut requires every cycle on
constrained vertices to be logically even. A spanning forest certifies this
condition; a boundary-only cut is invalid in its absence. Unlabelled
contraction can erase a zero-cost odd cycle, so original mechanism labels or
cover-component expansion data must survive. The gap theorem transfers the
Phase-1 nonnegative optimal odd-cut coverage proof, with the same exact
primal/dual equality; production radii remain uncertified.

Observable labels are exact within the retained effective model. X/Z
separation, probability cutoff and graphlike filtering are not claimed to
preserve the original correlated circuit distribution. The code's fallback
source overwrite and pre-stage-1 filtering discrepancy are explicitly recorded
in REVIEW; no external decoder is changed. A source membership relation is
not automatically a physical fault lift after compression.

The protocol-level triangular-prism interpretation is compared with the
specified primary literature. An algebraic correlation pairing and an ideal
interval-product retraction are proved; a local physical prism map for the
actual Lee graph and a universal geometric one-search cut remain open.
The note ends with the full Stim-to-hard-decoder-to-analysis metadata algorithm
and a validation contract. Finite checks and a separate same-agent adversarial
review are complete; no sliding-window decoding, calibration or aggregation
claim is introduced.

## 1. Scope and authority

The latest [Tasks 6–7 prompt](prompts/CODEX_TASK_06_07_PHASE1_COMPLETION_AND_AUDIT.md)
authorizes the per-color cluster metric, analytical transfer and complete
Phase-1 audit. Earlier stop-before-clusters instructions are superseded.
The standard triangular 6.6.6 family is fixed by note Definition 3.1,
at odd d≥3, with ordinary color boundaries, one encoded qubit, perfect
measurement and one pure CSS sector. No other lattice or circuit DEM
is silently included.

## 2. Mathematical preliminaries completed

Note §§1–2 define physical vertices, edges and faces; their colors; real
face checks; the binary physical support complex; syndrome; physical
stabilizer and logical equivalence; and the one-qubit logical representatives.
The string discussion explains elementary colored two-qubit operators,
endpoint excitations, same-color condensation, string-nets, and stabilizer
deformation, with source-specific citations.

Note §4 defines Lee's distinct restricted and monochromatic graphs and the
two bijections. It gives the exact two-round matching equations, their
real-row parity constraints, the physical correction, and the ordinary
smallest-candidate selection over the three colors. That selection is part
of the ordinary decoder, not soft-output aggregation. The real-coordinate
validity argument translates Lee Claims 1–2 and is conditional on feasible
round outputs, as the claims are.

The virtual node has no measured parity check; its parity is nevertheless
determined by the real syndrome through graph parity. No spurious zero
boundary parity is imposed. Delfosse's projection, the physical CSS
complex, the dual cellular boundary, the hypergraph boundary, and Kubica's
local Clifford unfolding are explicitly distinguished.

## 3. Research Task 1 result

The adopted local sets are
$\mathcal F_c(q)=\{f\in F_c:q\in f\}$ and
$\mathcal E_c(q)=\{e\in E_c:q\in e\}$.
Note Lemma 3.3 proves the exhaustive incidence table symbolically for
arbitrary $t\ge1$, using the two qubit residue classes, all three side
equations, and a color-permuting rotation. No finite diagram or numerical
sample is used as proof.

| Location | Real-face colors | Primal-edge colors |
|---|---|---|
| Bulk | r, g, b | r, g, b |
| Open side of color a | Other two colors | r, g, b |
| Corner between a and b | Third color | a, b |

At a physical boundary edge the missing-color rule uses the side color
and the one real-face color. Corners are degree two and belong to both
incident sides. These qualifications correct the incomplete bulk-only
wording in the initial notation.

Note Lemma 5.2 proves the dangling criterion:
$\epsilon_c(q)$ meets the artificial boundary exactly when
$|\mathcal F_c(q)|+|\mathcal E_c(q)|=1$; neither both counts zero nor
multiple same-color incidences occur.

Note Proposition 5.3 proves
\[
\mathcal B_c^{\rm dang}
 =\mathcal B_c^{\rm missF}\sqcup\mathcal B_c^{\rm missE},\qquad
\mathcal B_c^{\rm missF}=\epsilon_c(Q_c),\qquad
\mathcal B_c^{\rm missE}=\{\epsilon_c(q_{c_1c_2})\}.
\]
The sizes are $d$, $1$, and $d+1$ in total. The side set includes its two
corner qubits; the remaining corner is on the other two sides.
The superscripts describe the missing object, not the surviving endpoint.

This establishes **two geometric terminal types**, not two connected
components of the physical boundary circle or the merged graph, and does not by itself establish inequivalent physical logical boundaries.
That additional statement is now proved in §6 below. The types correspond to
the provenance of Lee Appendix A.3's two source boundary labels.

Note Proposition 5.5 states exactly what the merged boundary incidence
row records: the sum of the two terminal-type parities. It does not retain
the pair as separate coordinates. A fully labelled edge set can still
recover both counts, and qubit labels recover physical positions.
Thus merging is not claimed to erase all information irreversibly.

## 4. Research Task 2: completed resolved graph

Note Definition 6.1 constructs $G_c=\widetilde{\mathcal L}_c^*$ with vertices
$F_c\sqcup E_c\sqcup\{b_c^0,b_c^1\}$. Its physical edge bijection is
$\widetilde\epsilon_c:Q\to\Delta_1(G_c)$.
The $d$ missing-face edges go to $b_c^0$ and the one opposite-corner
missing-edge edge goes to $b_c^1$. All real incidences stay fixed.
No boundary shortcut or exterior-triangle qubit is introduced.

Definition 6.2 gives the graph quotient $q_c$ by terminal identification.
Its linear edge map $q_{c,1}$ is bijective. Lemma 6.5 proves
\[
\partial_1^{\mathcal L_c^*}q_{c,1}=q_{c,0}\partial_c,\qquad
D_c=\rho_c\partial_c=\delta_cq_{c,1}.
\]
Here $\rho_c$ deletes both terminal rows, and $\delta_c$ is the ordinary
real-row map. The quotient identifies vertices; it contracts no edge.

Lemma 6.3 proves connectivity for every allowed distance. In the red
coordinate instance each face $(1+3m,2+3n)$ connects by a two-edge step to
the face three rows below, or to $b_r^0$ at the base row. Every primal-edge
vertex joins this component and the opposite-corner terminal is a leaf
on a real face. Rotation covers the other colors. The proof includes
$t=1$ directly. Connectivity also gives surjectivity of $D_c$ onto the
real stage-2 syndrome space.

Proposition 6.6 proves equality of feasible chains, costs and minimizer
sets under transported weights **when both terminals have no parity
constraint**. This is not unconditional invariance of a matching solver.
The note's exact distance-3 example changes the optimum from one to two
if the opposite-corner terminal is incorrectly constrained even.
Ordinary decoding remains on $\mathcal L_c^*$, with output relabelled for
analysis on $G_c$. No assertion about unchanged shortest-path distances,
tie-breaking, matching duals or growth histories follows.

## 5. Research Task 3: completed chain and Pauli maps

Definition 7.1 defines $T_c:C_1(G_c)\to A$ on the full binary edge space
by $T_c\widetilde\epsilon_c(q)=q$, with
$T_c=T_c^{\rm ord}q_{c,1}$. It is a linear isomorphism.
The physical operator is $\mathscr P_{X,c}(\Gamma)=P_X(T_c\Gamma)$.
Lemma 7.2 proves exact multiplication under symmetric difference in the
pure X sector; the same applies after exchanging X and Z.

Definition 7.3 and Lemma 7.4 give the exact syndrome factorization
\[
D_c\Gamma=(H_cT_c\Gamma,M_cT_c\Gamma),\qquad
HT_c=\Lambda_cD_c.
\]
$M_c$ records physical c-edge endpoint parity. $\Lambda_c$ passes the
c-face coordinates through and applies restricted incidence to the
primal-edge coordinates, producing non-c physical checks.
Deleting terminal coordinates alone does not produce a physical syndrome.
The proof uses the local partition of every non-c face into its primal
c edges and applies to **every** binary chain, including all corner edges.

The two terminal boundary coefficients are the Task 1 terminal-type
counts; neither is a measured check. Real primal-edge vertices carry
stage-1 auxiliary parity information, distinct from the free terminals.
The source is Lee Appendix A.1 Eq. (10) and A.3 Claim 2 / Eq. (13);
the note supplies its explicit physical real-row proof.

Proposition 7.5 gives the endpoint syndrome of a path or walk:
$HT_c\Gamma=\eta_c(u)+\eta_c(v)$, where terminal endpoints contribute zero,
face endpoints one c check, and primal-edge endpoints their incident
non-c checks. Walk traversals are counted modulo two. General supports
may branch or contain disconnected cycles. Closed chains and
terminal-joining paths have zero physical syndrome; their physical
logical class is determined by the additional Task 4 argument below.

## 6. Research Task 4: logical correspondence proved

Note Definition 8.1 makes physical equivalence explicit for arbitrary
chain pairs. Within equal real stage-2 syndrome, differences lie in
$K_c=\ker D_c$ with exact denominator $R_c=K_c\cap T_c^{-1}(S_X)$.

Lemma 8.2 proves the central identity
\[
\beta_c(z)=Q_c^{\mathsf T}T_cz=\ell_Z^{\mathsf T}T_cz\quad(z\in K_c).
\]
The first equality is the qubit-incidence classification at $b_c^0$.
The second uses the independently known physical logical Z on $Q_c$,
the one-qubit logical quotient, and $HT_cz=0$.
It does not assume a surface-code theorem or the desired graph result.

Theorem 8.3 and Corollary 8.4 establish
\[
R_c=\ker(\beta_c|_{K_c})=\ker\partial_c,\qquad
\overline T_c:K_c/R_c\overset{\cong}{\longrightarrow}Z_X/S_X\cong\mathbb F_2.
\]
Every terminal-joining relative chain is nontrivial logical, every
closed resolved chain is a physical stabilizer, and every nontrivial
chain contains a simple terminal path whose removal leaves a stabilizer
cycle. Connectivity gives existence; the odd-degree component argument
gives a path contained in an arbitrary nontrivial support.

The converse is a statement about physical equivalence classes:
every nontrivial physical logical has a terminal-path representative.
It does not say every physical support is already in K_c.
Indeed the physical c-side support Q_c has $HQ_c=0$ but $M_cQ_c\ne0$.
The other two side supports map directly to simple terminal paths.
String-net representatives can be deformed into this class; doing so
may change the auxiliary parity fiber. Inside a fixed fiber, path
deformations use precisely the non-c face generators below.

### Complete face-generator characterization

Definition 8.5 and Proposition 8.6 activate
$A_c=T_c^{-1}J\iota_{\neg c}$ on the real non-c faces and prove it is
injective with $\operatorname{im}A_c=\ker\partial_c=R_c$.
The proof checks local c-edge parity, then uses the independent physical
face checks and exact family-wide counts:
\[
|Q|=3t^2+3t+1,\quad |F_c|=t(t+1)/2,\quad |E_c|=(|Q|-1)/2.
\]
Connected graph incidence gives cycle dimension $t(t+1)$, exactly the
number of independent non-c face images. No extra corner generator or
relation is needed. In particular $S_X\cap\ker M_c$ is exactly the
non-c face support space, not all of S_X.

Definition 8.7 supplies the induced binary complex
\[
\mathfrak C_c=(U_{\neg c}\xrightarrow{A_c}C_1(G_c)\xrightarrow{D_c}W_c)
\]
and its chain map $(\iota_{\neg c},T_c,\Lambda_c)$ to the physical CSS
complex. Its first homology is the physical logical quotient.
The bare graph pair has $H_1(G_c,\mathcal B_c)=K_c$ and dimension
$t(t+1)+1$; it must not be substituted for the induced complex.
A geometric CW attachment model is neither needed nor asserted.

All of these results are for the explicit standard ordinary-boundary
6.6.6 family, odd d≥3, perfect measurements, one encoded qubit, and one
CSS sector. They are not an automatic extension to arbitrary colexes.

## 7. Research Task 5: modified decoding-graph topology established

Proposition 9.1 identifies $(G_c,\mathcal B_c,\omega_c)$ as a
Meister-type modified decoding graph for fixed-stage-2 relative
differences: physical edge identities, effective parity map D_c,
two physically inequivalent terminal classes, stabilizer-trivial
closed chains, and simple representatives of nontrivial classes.

The correspondence is at the graph-topology and fixed-fiber quotient
level. D_c contains stage-1 auxiliary rows; it is not the full physical
H. Neither the whole concatenated decoder nor a particular surface-code
lattice is identified with G_c. Delfosse's projection and Kubica's
local Clifford unfolding remain distinct constructions.

Existing weights transfer edgewise without alteration.
Corollary 9.2 proves that the minimum unmodified nontrivial relative
chain cost equals a shortest terminal-path cost for nonnegative weights.
It does not minimize over all unrestricted physical logical supports
with arbitrary weights and is not a cluster-contracted quantity.
Positive supplied weights give the interval metric; §9 below specifies
labelled pseudometrics for original zero weights.

The topology is independent of the numeric first-stage prediction,
because all fixed real-syndrome fibers share K_c. The fiber restriction
is essential: the true physical error need not have the predicted
M_c parity. No noise-conditioning or decoder-success claim follows.

## 8. Research Task 6: decoder data and contraction

Note §10 defines a free-boundary matching dual, with nonnegative variables
on odd subsets of the actual stage-2 syndrome support. Pair constraints
use the ordinary merged matching distances, and the boundary constraint
is r_u≤distance(u,{b0,b1}). Proposition 10.2 proves its optimum equals
the original matching optimum using the Edmonds–Johnson parity polyhedron
on the syndrome metric closure with one auxiliary matching boundary.
That boundary is included in the odd set iff the syndrome has odd size.
No physical edge is added.

The certificate consists of a feasible correction f_c and dual y with
sum y=weight(f_c). Meister's radius sum gives metric balls on the resolved
graph. Their covered physical intervals agree with normalized merged
growth, but connected components must be recomputed with the two
terminals distinct. Generic merged components or signed singleton
Blossom potentials are not substituted. A separately defined UF growth
variant exports its own radii; no MWPM theorem is asserted for UF.

The local _decode_stage2 call returns predictions and total weights,
not a dual/radius certificate. Exporting such a certificate needs
instrumentation or a companion optimization. The latter is defined
explicitly and used in the finite sanity checks, but is not a claim
about the internal PyMatching history.

Note §11 contracts connected metric-ball components, retaining original
qubit-labelled edges with cost equal to uncovered interval length:
\[
h_v=\max(0,\max_u(r_u-d_c(u,v))),\qquad
\bar\omega_c(uv)=\max(0,\omega_c(uv)-h_u-h_v).
\]
Subdivision and contraction prove exact distance equivalence. This
handles nonuniform lengths, partial coverage, overlapping clusters,
single/both-terminal contacts and zero cost. Nonnegative original
weights use the labelled pseudometric extension.

The two-Dijkstra computation takes O((|V|+|E|)log|V|) time and
O(|V|+|E|) storage with radii already supplied. The explicit certificate
LP has exponentially many variables in syndrome size; decoder-side
extraction/conversion is a separate implementation obligation.

## 9. Research Task 7: exact geometric and conditional analytical result

Theorem 11.4 proves
\[
\phi_c=\operatorname{dist}_{\bar G_c}(b_c^0,b_c^1)
=\min_{z\in K_c,\beta_c(z)=1}\bar\omega_c(z).
\]
The earlier physical logical theorem supplies the interpretation.
A quotient route expands through connected covered components to an
original-edge chain; a simple path can then be extracted. If both
terminals contract, the value is zero but an internal physical logical
path still exists. An empty quotient walk is not a Pauli support.

Lemma 12.1 rebuilds Meister's covered-weight argument using edge-disjoint
trails, allowing shared vertices and free terminal endpoints. Odd-cut
counting gives covered weight≥dual value for every feasible correction.
Strong duality makes the base correction's uncovered cost zero.
For certified MWPM data, Theorem 12.3 proves
\[
W_{c,\mathrm{opp}}^{(2)}-W_{c,\mathrm{base}}^{(2)}\ge\phi_c.
\]
This is an exact cost inequality with nonnegative weights, fixed
auxiliary stage-1 parity and an optimal nonnegative dual. With physical
independent-bit-flip log-odds it bounds the ratio of two specified
representatives. It is not a bound on a summed logical-class LLR.

Arbitrary radii, nonoptimal duals, or UF corrections lack these
hypotheses. The d=3 single-face example has gap 1 but swim 3 for zero
radii; certified radius 1 gives swim 1. The confidence interpretation
beyond the representative inequality is a proxy, not a calibration.

## 10. Audit, delivery and Phase 2

The integrated note has one continuous development, no task-number
section headings, and a complete 41-item classification in REVIEW.md.
The core physical sources, Meister proofs and later confidence metrics
were checked against originals. The bibliography distinguishes exact
source reuse, adaptations and project derivations without priority claims.
The finite support script verifies all d=3 chains and 144 complete
fiber/weight/color cases, plus family incidence and ranks through d=11;
it is supporting evidence, not a substitute for proof. The resumed check
also verifies actual heap predecessor paths as physical logical witnesses
and handles disconnected terminal components. See
[reproduction instructions](notes/support/README.md).

Practical optimal-dual extraction and overhead, stage-1 errors and
conditioning, aggregate color scores, the complete decoder gap, posterior
calibration, circuit-level noise and further code families remain open
for a separately authorized Phase 2. No later phase is begun here.


## 11. Authorized Phase-2A implementation and pilot

The user separately authorized the implementation prompt in `src/`. The
Phase-1 definitions/proofs remain unchanged. Generic C++ analysis now retains
explicit edge IDs, computes metric-ball residuals and returns a value for each
terminal pair while keeping ordinary matching weight and hard output separate.
Final original-defect radii are read before blossom shattering; they instantiate
an explicitly named ball convention, not Definition 10.1's exact certificate.

The decomposition layer records physical/virtual row sources, original DEM
provenance, and full detector coordinates including time. Other-color inert
H2 rows are explicitly `INACTIVE_PADDING`; the two requested roles classify
all active constraints. Spatial half-edge roles were checked against Tanner
geometry at d=3,5,7 for r/g/b. Hard H2, weights and stage-2 inputs are unchanged.
The opt-in decoder caches configured standard stage-2 matchers and exposes
per-color weights/swim plus the value selected by the ordinary best-color rule.
Custom/predecoded/comparative/circuit-level SO is refused in this version.

Independent d=3/d=5 coordinate graphs and physical witnesses, exhaustive d=3
fibers, metric and hard-regression gates passed. The backend lacks original
odd-cut variables, verified nonnegative dual feasibility, and exact primal/dual
equality, so the representative-bound numerical claim remains unavailable.
The pilot only studies the exploratory score under this documented convention.

Comparative pairing preserves the physical measurement record: its extra
detector is ordinary observable 0. Common-detector parity sets and record
positions agree; both converters were tested on the same measurement batch.
The forced-class decoder overwrites the extra bit, so actual observable values
are not used as decoded answers. Separate hard predictions/failure labels and
matched acceptance curves were saved for 3072 paired shots. No full-gap theorem,
posterior calibration, large campaign or final circuit topology is claimed.
See IMPLEMENTATION_STATUS.md and implementation_artifacts/pilot/REVIEW.md.

## 12. Authorized Phase-2B numerical layer

The 2026-09-12 user request authorizes the reusable package and fixed moderate
code-capacity study in src/CODEX_PHASE2B_GETTING_STARTED_NUMERICS_PROMPT.md.
This is an empirical extension; it does not change Phase-1 proofs or the
Phase-2A external decoder implementation. Source is under
`src/color_code_softoutput`, in experiment/simulation/analysis layers.

The fixed study uses d=3,5,7,9,11,13, T=1, tri_optimal and corrected bitflip-only
noise. Near-threshold p=.076,.080,.084,.088 and subthreshold p=.02,.03,.04,.05
are explicitly the fallback approximation, because no exact original grid was
recovered. Ordinary selected-color swim and existing comparative logical-gap
(alias forced_gap) use the same physical shots and separate decoder failure
labels. There is no minimum-over-colors aggregation or new gap theorem.

Batch Parquet storage, source/environment manifests, atomic writes, deterministic
SeedSequence schedules and a bounded process pool make the study reproducible.
The root has no Git SHA; full main-source snapshots accompany source hashes.
Analysis uses 99% Wilson intervals, Lee-style log-rate OLS and explicitly
identified project LOWESS crossing estimation; weak/degenerate fits are retained
as such. Production optimal-dual certification remains open.

The completed Phase-2B study is results/20260912_145540_phase2a_test: 4.8 million
paired shots, four workers, sampling wall time 93.58 s. Audit and notebook
execution pass; 262 Python tests pass with two upstream skips. The primary
crossing remains unresolved at the upper grid endpoint. Fitted G/C slopes are
.4547/1.165 with broad 99% intervals; exact reproduction is not claimed.
The final report distinguishes exploratory larger-distance crossing sensitivity
from the all-distance estimator. Stop at this completed study.

## Surface-code path-gap v1 implementation (2026-09-19)

The user authorized modifying the existing PyMatching checkout for an
additional paired surface-code score. `Matching.decode_batch_with_path_gap`
computes residual shortest terminal distance with ordinary correction edges
zeroed, then subtracts the original-weight sum of the full correction. The
existing SWIM terminal topology is reused, including its X-boundary split;
ordinary decoding and the color-code source are unchanged. This explicitly
supersedes the earlier fixed-PyMatching instruction for this task only.

The surface runner stores this signed `global_subtraction_v1` score, residual
distance, correction weight and version alongside SWIM and complementary gap.
The notebook plots the new distribution/conditional LER and paired three-score
postselection. Legacy runs keep their original schema and two metrics. This
adds an empirical implementation convention, no theorem or calibration claim.
See `surface_code_test/VALIDATION.md` and
`external_libs/PyMatching/docs/path_gap.md`.
