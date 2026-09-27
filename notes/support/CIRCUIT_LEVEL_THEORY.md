# Circuit-level fixed-color swim distance

Research deliverable, 12 September 2026. The derivation is integrated into
[notes/note.tex](../note.tex), Part II, with source in
[circuit_level_theory.tex](circuit_level_theory.tex) and compiled
[note.pdf](../note.pdf). This implements the
[theory prompt](CODEX_CIRCUIT_LEVEL_THEORY_PROMPT.md); the
[original sketch](CIRCUIT_LEVEL_THEORY_SKETCH.md) remains a proposal to compare
against the proved statements here.

The result is an exact residual-cost minimum for the **retained effective
stage-2 DEM**, conditioned on one stage-1 output. A logical double cover gives
a general polynomial graph algorithm. A simpler two-terminal cut is valid
when an explicit internal-cycle balance test passes. An exact local prism
realization and a universal geometric one-search cut for all extraction
schedules remain open; the cover algorithm does not require them.

## The mathematical object

An original DEM mechanism has a probability, detector parity column, and
observable parity column. Flattening repeats and offsets gives binary maps
`B` and `L`. Separator components of one error instruction remain one event.
Measurement-record selectors give `B=P_det A_rec` and `L=P_obs A_rec`, so
logical parity is traced from the circuit instead of inferred from coordinates.

For fixed color `c`, write `A_e` for a separated mechanism's c-detector set
and `N_e` for its non-c detector set. A restricted mechanism is indexed by a
nonempty retained `N`. Its predicted occupancy becomes a constrained virtual
row `v_N` in stage 2. The retained stage-2 columns are:

| Original target structure | Stage-2 detector column | Observable column |
|---|---|---|
| `N_e` empty, at most two c targets | `A_e` | Original separated label |
| One or two non-c targets, at most one c target | `A_e + v_N_e` | Original separated label |
| Otherwise | Removed | Removed with mechanism |

Physical c-detector rows and stage-1 virtual rows are both constrained.
The artificial matching boundary has no detector row. Padding is a third
storage role, not a physical or virtual constraint with inferred meaning.
The maps are `D=D_c^circ` and `L_2=L_c^circ`, with the subscript avoiding
confusion between an observable matrix and Lee's matching lattice.

The virtual construction gives an exact retained-model identity:
`B_ret = Lambda_c^circ D`, where `Lambda(a,v)=(a,H_rest v)`.
Thus feasible stage-1 and stage-2 results reconstruct the retained physical
syndrome. Filtering does not guarantee feasibility for arbitrary input shots.

For any nonempty fixed fiber `Dx=s`, define

```
K = ker D
R = ker D intersect ker L_2
Q = K/R ≅ image(L_2 restricted to K).
```

This quotient is proved by the first isomorphism theorem. In one observable
there are exactly two frame classes iff adding `L_2` as a row increases the
binary rank of `D` by one. This condition does not follow from “one encoded
qubit” alone: the retained fault set might lack an odd invisible chain.
An all-distance sufficient condition is presence of all single-qubit final
readout-flip effects. They contain the Phase-1 terminal-path witness on the
final detector layer, for every odd d≥3 and every number of closed-memory
rounds. The denominator means frame-trivial circuit differences; it is not
identified with static face stabilizers.

## What decomposition preserves

Lee's Algorithm 1 compresses identical **complete** target sets using
`q_C=(1-product(1-2q_e))/2`. This preserves their detector/observable parity
and the independent effective distribution under an XOR projection. It does
not preserve individual minimum representative costs. A list of original
sources is not an inverse: selecting every member of a two-member class has
even parity, whereas selecting the compressed mechanism has odd parity.

X/Z separation keeps the corresponding sector labels but removes correlations.
Graphlike filtering preserves surviving labels and can change the quotient
and minimum. The literal paper drops empty-detector sector parts, including
observable-only parts if present. The general cover theorem can retain such
mechanisms, but must not silently add them to the hard decoder's actual model.

The current code is separately audited at `ba6f7dc`:

- The manager separates depolarization at circuit level before DEM extraction.
  Sector marginals have explicit formulas; joint X/Z correlations change.
  A probability cutoff of 1e-15 also changes the represented fault set.
- Complete target dictionary keys retain logical labels. The already-separated
  unique-target domain has a checked source-selection map and sorted column map.
- The mixed-sector fallback overwrites a duplicate target key's source list;
  it does not implement general parity compression. A reproducer gives .2
  where two probabilities .1 and .2 should parity-compress to .26.
- The code jointly filters stage-1/stage-2 candidates before computing stage-1
  probabilities; the paper includes some sources in stage 1 that it removes
  from stage 2. A reproducer gives .1 instead of paper stage-1 probability .26.

These observations are documented rather than repaired in the external decoder.
The theorem for the frozen effective matrices remains valid. Exact original
correlated-noise likelihood or a canonical physical fault lift is not claimed.

## Metric and graph algorithm

Assign each retained mechanism its supplied nonnegative weight and uncovered
interval length `bar_w(e)`. The definition is

```
phi_c^circ = min { sum_e bar_w(e) z_e : Dz=0, L_2 z=1 }.
```

This is exactly the minimum contracted cost of an opposite-frame difference
within the fixed fiber. The empty minimum is infinity, with no witness.
Missing growth data is a different status: growth unavailable.

Complete half-edges at one artificial node `b_*`; a zero-detector mechanism
becomes a labelled loop there. A zero real syndrome forces zero incidence at
`b_*` by handshake. Thus this completion introduces no false invisible chain.

For every vertex make copies `(v,0)` and `(v,1)`. For each mechanism
`e=(u,v)` with label `lambda_e`, connect `(u,a)` to `(v,a XOR lambda_e)`.
Both copies inherit the same residual cost and original mechanism ID. Then

```
phi_c^circ = min over base vertices v of dist((v,0),(v,1)).
```

Every invisible odd chain contains an odd cycle; an odd cycle lifts between
opposite copies of a common vertex. Conversely such a cover path projects
to an odd invisible chain after XOR reduction. Nonnegative costs prove exact
minimum equality and supply a witness, including at zero cost. A straightforward
implementation uses n Dijkstra runs, O(n(m+n)log(2+n)) time and O(m+n) working
storage after residuals are available. This is a proved upper bound, not a
performance measurement or an optimal-complexity claim.

Starting only at the boundary can miss the minimum: an odd unit triangle
joined to the boundary by a weight-10 bridge has fundamental value 3 and
boundary-rooted cover distance 23. Searching between arbitrary sheet-0 and
sheet-1 vertices can instead underestimate: their endpoints need not project
to the same vertex.

A two-terminal cut is available if every cycle among constrained vertices is
logically even. A spanning forest computes a potential `g` with
`lambda_uv=g(u)+g(v)` on internal edges. Gauge away those labels and attach
each half-edge to terminal `b^0` or `b^1` according to its gauged label.
Odd zero-detector loops become actual labelled terminal-to-terminal edges.
The terminal distance then equals the fundamental minimum. This gate is
necessary for a boundary-only resolution that represents every invisible
chain by terminal parity. Equivalent labels `L_2+g^T D` give identical values
with fixed coverage. General geometric cuts need a separate lifting proof;
unmatched endpoints on a drawn correlation surface do not suffice.

## Coverage and the certified bound

Compute coverage once on the declared original metric. For vertex balls,
`h_v=max(0,max_s(r_s-dist(s,v)))` and
`bar_w(uv)=max(0,w(uv)-h_u-h_v)`. A loop uses the same vertex twice.
Spatial, timelike, diagonal and virtual-incident edges all obey this interval
formula. Copies of an edge inherit its residual length; there is no fresh
decoder growth on a cut or cover.

Retain logical labels while contracting. A covered cluster can contain an
odd cycle, making the true value zero. Contracting it to one unlabelled base
vertex loses that witness. Keeping original labelled zero-cost edges, or
contracting their lifted components with expansion data, is correct.
Certified boundary-normalized radii cannot propagate positive coverage through
the artificial boundary; this is what permits Phase-1 boundary splitting.
Arbitrary production radii require an explicitly recorded metric convention.

Under an exact optimal nonnegative odd-cut certificate for the same labelled
graph and weights, the proof establishes

```
W_opp^circ - W_base^circ >= phi_c^circ.
```

The proof decomposes corrections into edge-disjoint trails, counts odd-cut
loads, and shows the optimal correction has zero uncovered cost. Its XOR
with an opposite correction lies in the admissible logical set. It requires
no planar embedding. Current exported Sparse-Blossom final-defect radii are
**not** this certificate; the production bound flag remains false. No summed
logical-class LLR, calibration or full-decoder inequality is established.

## Exact Phase-1 limit and spacetime scope

The controlled limit has one independent data-X layer before the first ideal
extraction, followed by noiseless operations and readout. Only the first Z
detector layer is affected; later detector differences cancel. Restricted
sets identify the physical c edges, giving exactly `D_c=(H_c,M_c)T_c`, and the
observable reduces on the kernel to Phase-1 terminal parity. With identical
weights and coverage the feasible sets and costs coincide, proving
`phi_c^circ=phi_c^Phase1`. Additional noiseless rounds do not change this proof.
Repeated noisy data layers or independently chosen duals are different inputs.

The note defines an algebraic chain/cochain complex and proves the observable
pairing. A separately specified physical fault lift pulls back a correlation
cochain to `L_2`. Hillmann's fault-complex construction, Delfosse–Paetznick's
adjoint propagation, Bombín's geometric complexes, Herzog's triangular prisms,
and Derks's DEM factorization provide precise comparisons, not an assumed
isomorphism to Lee's graph. An ideal interval tensor product retracts onto the
static algebraic complex; that homotopy equivalence alone does not preserve
weights or prove an actual circuit graph is a Cartesian product.

Initial/final detector definitions, temporal half-edges, physical boundaries,
matching boundaries and analysis cuts remain distinct. Removing future checks
changes the kernel. Sliding-window theory is outside this deliverable.

## Deliverables, checks and implementation handoff

The final section of the TeX note specifies the complete circuit → DEM →
metadata → actual decomposition → stage 1 → virtual syndrome → unchanged
stage 2 → growth → residuals → cut/cover → witness pipeline. It specifies
stable IDs, probabilities, provenance, row roles, source coordinates, logical
labels and boundary metadata. It distinguishes the exact objects supplied to
PyMatching from analysis-only graph copies and temporary search arcs.

The validation contract covers all requested gates, including exact reduction,
exhaustive small DEMs, witnesses, compatible Stim comparison, cut/cover and
gauge equivalence, temporal endpoints, compression, interval transport, hard
invariance and conditional certificate checks.

Finite support checks in [check_circuit_theory.py](check_circuit_theory.py)
were run in `color_code_so` (Stim 1.16.0): 400 random tiny labelled multigraphs
with exhaustive subset oracles, 211 valid cuts, gauge and residual checks;
all-color Phase-1 unit-cost reductions at d=3,5,7; complete enumeration of six
d=3 measurement-noise DEMs (T=1: 10 mechanisms/1024 subsets per color;
T=2: 13 mechanisms/8192 subsets per color), including Stim and frame-map checks;
and explicit source-discrepancy counterexamples. These checks support the
proofs; they are not a campaign or a production integration test.

The separate same-agent adversarial review is recorded in [REVIEW.md](../../REVIEW.md).
This is not external peer-review certification. Source passages, versions,
search scope and failed retrievals are in the
[audited bibliography](../../refs/REFERENCES.md). No novelty claim is made.
The task stops at theory and the implementation specification.
