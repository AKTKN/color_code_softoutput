# Circuit-Level Generalization of the Color-Code Swim Distance
## Theory sketch for the next research phase

### Status

This document is a **research sketch**, not a finished theorem statement. Its purpose is to provide a disciplined starting point for extending the Phase-1 fixed-branch swim-distance theory from perfect syndrome measurements to the circuit-level noise model used by the Lee--Li--Bartlett concatenated MWPM decoder.

The main methodological conclusion is:

> The circuit-level theory should be formulated first at the level of the **detector error model (DEM)**, using its detector-incidence map and logical-observable map. The intuitive picture of extruding the triangular color code through time is useful and is supported by spacetime/fault-complex and color-code correlation-surface literature, but it should be treated as a geometric realization of the DEM algebra rather than as the primary proof assumption.

This is important because the actual circuit-level concatenated decoder performs DEM decomposition, compression, virtual-detector substitution, Pauli-sector separation, and graphlike filtering. Its stage-2 `c`-only graph is therefore not literally the Cartesian product of the code-capacity graph with a time interval.

---

# 1. Research roadmap

The remaining theory program can be separated into three parts.

## A. Further code-capacity theory

Study additional properties of the fixed-color swim distance, including:

- scaling with code distance and physical error rate;
- conditions for equality or tightness of the representative-gap bound;
- dependence on the selected MWPM dual/growth convention;
- relations to degeneracy and logical-class probabilities;
- theoretically justified three-color aggregation, if possible.

This is important, but is not the immediate task because the next numerical implementation requires a circuit-level definition first.

## B. Circuit-level extension

Generalize the fixed-color soft output to the circuit-level noise model.

The final result should specify:

1. the mathematical object constructed from the circuit DEM;
2. how Lee--Li--Bartlett's `c`-restricted and `c`-only DEMs enter;
3. how a logical class is represented in the stage-2 circuit-level problem;
4. how a modified graph suitable for swim-distance computation is constructed;
5. how MWPM cluster information is transferred to that graph;
6. exactly what metadata must be retained from Stim, DEM decomposition, and PyMatching;
7. why the resulting shortest-path/minimum-cost quantity represents the opposite logical class.

This is the next immediate research task.

## C. Sliding-window decoding

Sliding-window decoding should be treated separately.

An open future temporal boundary changes the relative logical topology. The closed-memory result should not be imported automatically. A new treatment of temporal escape, logical parity, and the relevant confidence object will likely be required.

Do not mix the sliding-window problem into the present circuit-level memory theorem.

---

# 2. Phase-1 input

For the perfect-measurement standard odd-distance triangular 6.6.6 code, Phase 1 established the following for fixed color `c` and one CSS sector.

The ordinary stage-2 monochromatic graph `L_c^*` has one edge per physical data qubit. Its single artificial matching boundary merges two geometrically distinct terminations:

- the complete physical `c`-colored side;
- the unique corner opposite that side.

Resolving them gives two virtual terminals

\[
b_c^0,\qquad b_c^1.
\]

For two corrections in the same stage-2 fiber, their difference `z` obeys the real stage-2 homogeneous constraint. Phase 1 proves:

\[
\partial z=0
\]

if and only if the difference is physically logical-trivial, whereas

\[
\partial z=b_c^0+b_c^1
\]

corresponds to the nontrivial logical class.

After decoder-cluster contraction,

\[
\phi_c
=
\operatorname{dist}_{\bar G_c}(b_c^0,b_c^1)
\]

is exactly the minimum residual cost of a nontrivial fixed-fiber logical chain.

The Phase-1 result is deliberately limited to perfect measurements. It also notes that DEM reduction/reweighting requires a separate physical-edge and weight audit before the perfect-measurement theory can be used at circuit level.

---

# 3. Assessment of the "triangular prism in time" intuition

The user's intuition is useful and likely points in the correct geometric direction, but it is too strong if interpreted literally.

For a repeated memory experiment, the physical protocol naturally forms a spacetime object. Recent work on triangular color-code pipe diagrams represents a 6.6.6 memory protocol by a triangular-prism-like spacetime geometry and explicitly constructs logical **correlation surfaces**. Likewise, fault-complex and spacetime-code formalisms describe repeated QEC by promoting a static code into a spacetime complex.

This strongly suggests the schematic picture

```text
triangular color-code patch
        ×
time interval
        ->
spacetime memory object
```

with logical information represented by an extended correlation surface.

However, Lee--Li--Bartlett's **actual decoder graph** is not simply the static `c`-only graph times an interval. The circuit-level DEM contains and/or generates:

- timelike fault edges;
- spatial fault edges;
- diagonal/hook-like edges;
- initialization/readout half-edges;
- stage-1 virtual-detector vertices;
- compressed mechanisms;
- mechanisms retained after graphlike filtering.

Therefore the theorem should not assume

\[
G_c^{\rm circ}=G_c^{\rm code}\times I.
\]

Instead, the product/prism picture should be derived as a useful topological interpretation of the exact DEM construction.

---

# 4. DEM-native formulation

Consider one Pauli sector of a Clifford memory circuit.

Write the detector error model as

\[
\mathcal M
=
\{(q_e,D_e,O_e)\}_{e\in E}.
\]

For each mechanism `e`:

- `q_e` is its probability;
- `D_e` is the set of flipped detectors;
- `O_e` is the set of flipped logical observables.

After fixing detector and observable orderings, define binary matrices

\[
B\in\mathbb F_2^{m\times |E|},
\qquad
L\in\mathbb F_2^{k\times |E|}.
\]

For a binary fault vector

\[
x\in\mathbb F_2^{|E|},
\]

the DEM semantics are

\[
s=Bx,
\qquad
\ell=Lx.
\]

Thus `B` is the detector-incidence map and `L` is the logical frame-change map.

This pair is the natural circuit-level replacement for the Phase-1 pair consisting of the stage-2 real incidence and the physical logical-parity functional.

The key benefit is that logical information is already encoded in the DEM. It is unnecessary, and potentially dangerous, to infer the logical class only from a spacetime drawing.

---

# 5. Lee--Li--Bartlett circuit-level color decomposition

For each color `c`, Lee--Li--Bartlett construct a `c`-restricted DEM

\[
\mathcal M_{\neg c}
\]

and a `c`-only DEM

\[
\mathcal M_c.
\]

The construction includes:

1. separating X- and Z-type detector sectors;
2. compressing mechanisms with identical target sets;
3. constructing the restricted DEM by removing `c`-colored detectors;
4. introducing one virtual detector for each restricted mechanism;
5. replacing the non-`c` detector set of a full mechanism by the corresponding virtual detector;
6. retaining logical-observable targets in the `c`-only DEM;
7. retaining only graphlike mechanisms appropriate for MWPM.

For the stage-2 `c`-only DEM define

\[
D_c^{\rm circ}:
\mathbb F_2^{E_c^{\rm circ}}
\rightarrow
\mathbb F_2^{V_c^{\rm real}}
\]

and

\[
L_c^{\rm circ}:
\mathbb F_2^{E_c^{\rm circ}}
\rightarrow
\mathbb F_2^k.
\]

The real stage-2 vertices split conceptually into

\[
V_c^{\rm real}
=
V_c^{\rm physical}
\sqcup
V_c^{\rm virtual},
\]

where the second set consists of stage-1-derived virtual detectors.

The ordinary matching-boundary coordinate is not constrained by `D_c^{circ}`.

For each effective stage-2 error mechanism with probability `q_e`, use

\[
\omega_e
=
\log\frac{1-q_e}{q_e}
\]

when that is the weight convention used by the decomposed matching problem.

---

# 6. Fixed-stage-1 fiber

Fix the stage-1 result and hence the complete real stage-2 syndrome

\[
s_c.
\]

A stage-2 candidate `x` satisfies

\[
D_c^{\rm circ}x=s_c.
\]

For two candidates `x,x'` in the same stage-2 fiber, define their difference

\[
z=x+x'.
\]

Then

\[
D_c^{\rm circ}z=0.
\]

Define

\[
K_c^{\rm circ}
=
\ker D_c^{\rm circ}.
\]

Now define the logically trivial same-fiber difference space

\[
R_c^{\rm circ}
=
\ker D_c^{\rm circ}
\cap
\ker L_c^{\rm circ}.
\]

The corresponding quotient is

\[
\mathcal Q_c^{\rm circ}
=
K_c^{\rm circ}/R_c^{\rm circ}.
\]

At circuit level, this is preferable to declaring every trivial difference to be a product of static code stabilizers. A detector-invisible circuit fault combination can be logically trivial without admitting a simple static-Pauli interpretation on one time slice.

---

# 7. First core theorem: DEM fixed-fiber logical quotient

The logical map restricted to `K_c^{circ}` has kernel exactly `R_c^{circ}`. Therefore the first isomorphism theorem gives

\[
\boxed{
\mathcal Q_c^{\rm circ}
\cong
\operatorname{im}
\left(
L_c^{\rm circ}|_{K_c^{\rm circ}}
\right).
}
\]

For the one-logical-observable memory experiment, if

\[
\operatorname{im}
\left(
L_c^{\rm circ}|_{K_c^{\rm circ}}
\right)
=
\mathbb F_2,
\]

then the fixed stage-2 fiber has exactly two logical equivalence classes.

For

\[
z\in K_c^{\rm circ},
\]

\[
L_c^{\rm circ}z=0
\]

means the same logical frame, whereas

\[
L_c^{\rm circ}z=1
\]

means the opposite logical frame.

This theorem is DEM-native and does not require a spacetime drawing.

The decoder-specific research task is to verify carefully that Lee's decomposed `c`-only DEM satisfies the assumptions needed for this interpretation.

---

# 8. Observable-faithfulness of the decomposed DEM

A separate proposition is required.

Trace logical-observable information through

```text
physical circuit
-> original DEM
-> X/Z-separated DEM
-> compressed mechanisms
-> c-restricted DEM
-> c-only DEM
```

and prove exactly what `L_c^{circ}` means.

The likely correct claim is:

> The logical label of a stage-2 mechanism set is exact **within the decomposed DEM actually used by the concatenated decoder**.

This is weaker than saying that the decomposed DEM is an exact factorization of the complete correlated physical circuit-noise distribution.

The following approximations/transformations must be stated explicitly:

- X/Z correlations may be separated;
- mechanisms with identical targets are compressed;
- non-edge-like mechanisms may be removed;
- the decoder therefore works with an effective graphlike model.

Compression is harmless to detector/logical target identity only if mechanisms are merged with the complete relevant target set, including logical observables. This must be checked against the actual implementation and Lee's Algorithm 1.

---

# 9. Fundamental circuit-level swim-distance definition

Define the circuit-level quantity before choosing a geometric representation.

Let decoder growth define a cluster set

\[
\mathcal C_c
\]

on the interval realization of the weighted stage-2 graph. After contracting covered regions, let

\[
\bar\omega_c(e)
\]

be the residual uncovered length of stage-2 mechanism edge `e`.

For one logical observable define

\[
\boxed{
\phi_c^{\rm circ}
=
\min_{\substack{
D_c^{\rm circ}z=0\\
L_c^{\rm circ}z=1
}}
\bar\omega_c(z).
}
\]

More generally, for several observables one may define a quantity over `Lz != 0` or per target logical label, but that is not required for the first memory theorem.

Interpretation:

> `phi_c^{circ}` is the minimum decoder-cluster-contracted cost of a detector-invisible stage-2 fault difference in the opposite logical class, conditioned on the fixed stage-1 fiber.

This is the natural circuit-level analogue of Phase 1.

---

# 10. Reduction to Phase 1

A mandatory consistency theorem is:

> In the perfect-measurement/code-capacity limit corresponding to the Phase-1 construction, the DEM-native logical label reduces to the Phase-1 terminal-parity functional.

Concretely, one should recover

\[
L_c^{\rm code}z=\beta_c(z).
\]

Then

\[
\min_{\substack{
D_c z=0\\
L_c^{\rm code}z=1
}}
\bar\omega_c(z)
\]

becomes

\[
\operatorname{dist}_{\bar G_c}(b_c^0,b_c^1).
\]

Thus the new theory should prove

\[
\boxed{
\phi_c^{\rm circ}
=
\phi_c^{\rm Phase1}
}
\]

in the perfect-measurement limit.

This must be a theorem, not merely a numerical comparison.

---

# 11. Logical cocycle and correlation surface

For the one-observable stage-2 graph define an edge label

\[
\lambda_c(e)
=
L_c^{\rm circ}[e]
\in\mathbb F_2.
\]

For

\[
z\in K_c^{\rm circ},
\]

the logical parity is

\[
L_c^{\rm circ}z
=
\sum_{e\in z}\lambda_c(e)
\pmod 2.
\]

Thus the logical observable is a `Z_2`-valued functional on the detector-invisible chain space.

When the DEM graph admits a spacetime embedding, the desired geometric interpretation is

\[
L_c^{\rm circ}z
=
\langle z,\Sigma_L\rangle
\pmod 2,
\]

where `Sigma_L` is an appropriate logical **correlation surface**.

This is the precise form of the triangular-prism intuition: the static logical topology becomes a spacetime logical pairing.

The actual chain/cochain complex and pairing must be specified rigorously. A drawn surface alone is not a proof.

---

# 12. Triangular prism interpretation

Recent color-code pipe-diagram work explicitly represents a triangular 6.6.6 color-code memory experiment by a triangular-prism-like spacetime object:

- horizontal sections are triangular code patches;
- the vertical direction represents repeated syndrome extraction;
- horizontal end faces encode initialization/readout information;
- logical Pauli flow is captured by correlation surfaces.

This provides strong geometric support for the user's intuition.

However, the correlation surface in the **decomposed `c`-only DEM** need not be a flat prism wall. Hook faults, diagonal graph edges, virtual detectors, and mechanism compression can deform the microscopic graph.

Therefore the theorem should state topological/algebraic equivalence rather than exact geometric equality to a simple prism lattice.

---

# 13. Temporal-boundary caution

A critical terminology point:

> "The memory experiment has a closed logical temporal boundary" does **not** mean that the DEM contains no one-detector mechanisms at the first or final time.

Circuit initialization and readout can generate one-detector mechanisms. These become matching half-edges.

The following are different objects and must not be conflated:

- spatial code boundary;
- initial/final temporal circuit boundary;
- artificial MWPM boundary;
- boundary of a logical correlation surface;
- logical cut used by the soft-output analysis.

The correct classification of first/last-time half-edges should be derived from DEM logical labels and/or the circuit fault complex, not merely from their time coordinate.

This is one of the central points to verify in the circuit-level theory.

---

# 14. Two candidate logical-graph constructions

The fundamental definition in Section 9 is exact but does not yet provide the most efficient shortest-path implementation.

Two constructions should be developed.

## 14.1 Correlation-surface cut graph

If a correlation surface `Sigma_L` can be chosen as a cut, open the stage-2 spacetime graph along it.

The cut should produce two copies/sides

\[
B_c^0,\qquad B_c^1
\]

such that a detector-invisible chain has odd logical parity if and only if it has a representative joining the two sides.

Then

\[
\boxed{
\phi_c^{\rm circ}
=
\operatorname{dist}_{\bar G_c^{\rm cut}}
(B_c^0,B_c^1).
}
\]

This is the closest circuit-level analogue of the Phase-1 two-terminal graph and would permit one standard shortest-path computation.

For the memory experiment this is the preferred final construction if it can be proved.

## 14.2 Canonical logical double cover

As a geometry-independent fallback, construct a binary logical cover.

Create two copies of every graph vertex:

\[
(v,0),\qquad(v,1).
\]

For each edge

\[
e=(u,v)
\]

with logical label

\[
\lambda_e\in\mathbb F_2,
\]

add lifted edges

\[
(u,a)
\leftrightarrow
(v,a+\lambda_e),
\qquad
a\in\mathbb F_2.
\]

Logical-even edges stay on one sheet; logical-odd edges switch sheets.

An odd-logical closed walk on the original graph lifts to a path between opposite sheets.

This construction is canonical and does not require physical coordinates.

The following must still be proved:

- treatment of free matching boundaries/half-edges;
- exact equivalence with the constrained minimum `Dz=0,Lz=1`;
- whether one Dijkstra suffices in the memory case;
- or whether a minimum over source copies / a shortest odd cycle calculation is required.

Do not state a complexity result before the reduction is exact.

The double cover should also serve as an independent check of the geometric cut construction.

---

# 15. Why the correlation-surface cut may be the best final algorithm

The double cover gives a general algebraic construction. The memory circuit has extra physical structure, however: the logical observable comes from a physical correlation through the spacetime protocol.

If that logical class is represented by a codimension-one correlation surface, cutting along it should transform a nontrivial `Z_2` logical cycle into a relative path problem.

This would recover a Meister-like structure:

```text
weighted c-only circuit-level graph
        |
MWPM cluster contraction
        |
logical correlation-surface cut
        |
two inequivalent logical boundaries
        |
shortest path
```

The main topology theorem should decide whether this is valid for the actual Lee `c`-only DEM rather than for an idealized spacetime lattice.

---

# 16. Cluster contraction is dimension-independent

The cluster-contraction part of Phase 1 is fundamentally graph-metric, not two-dimensional.

For any finite weighted graph with nonnegative edge lengths and decoder radii:

1. realize edges as metric intervals;
2. take the union of decoder metric balls;
3. identify each connected covered component to a point;
4. charge only uncovered edge length.

Under the same validated interval-coverage convention, a residual edge length can still be written as

\[
\bar\omega(e)
=
\max\{0,\omega(e)-h_u-h_v\}.
\]

Meister--Pattison--Preskill explicitly note that the same soft-output procedure applies to a **3D decoding graph corresponding to faulty measurements**.

Therefore the hard part of the circuit-level color-code extension is not cluster contraction itself. It is the proof of the logical topology of the circuit-level `c`-only DEM.

---

# 17. Candidate circuit-level representative-gap theorem

Let `f_c` be an exact MWPM stage-2 solution for fixed stage-1 fiber and circuit-level syndrome.

Define

\[
W_{c,\mathrm{base}}^{\rm circ}
=
\omega_c(f_c),
\]

and

\[
W_{c,\mathrm{opp}}^{\rm circ}
=
\min_{\substack{
D_c^{\rm circ}m=s_c\\
L_c^{\rm circ}(m+f_c)=1
}}
\omega_c(m).
\]

For clusters generated by the required certified optimal MWPM dual/radius convention, the target theorem is

\[
\boxed{
W_{c,\mathrm{opp}}^{\rm circ}
-
W_{c,\mathrm{base}}^{\rm circ}
\ge
\phi_c^{\rm circ}.
}
\]

The Phase-1 proof is largely graph-theoretic and may transfer once the circuit-level logical quotient is established.

This theorem must remain distinct from the practical current implementation. The existing Phase-2A Sparse-Blossom growth balls are not yet proved to be the exact nonnegative odd-cut dual certificate required by the certified bound.

---

# 18. Concrete implementation-facing algorithm to target

The theory should culminate in an algorithm precise enough to implement directly.

## Step 1: generate the original circuit DEM

From Stim retain:

```text
error mechanism ID
probability
detector targets
logical observable targets
detector coordinates including time
observable IDs
```

Do not throw away provenance required later.

## Step 2: perform Lee's Pauli/color decomposition

Construct

\[
\mathcal M_{\neg c},
\qquad
\mathcal M_c.
\]

Retain a provenance map from each decomposed stage-2 mechanism to the original DEM mechanism(s) and target set.

Logical observable labels must be retained.

## Step 3: decode stage 1

Decode `M_{\neg c}` and map the selected restricted mechanisms to the virtual detector syndrome used in `M_c`.

## Step 4: construct the labelled stage-2 graph

For every mechanism in `M_c`, retain:

```text
stage-2 mechanism/edge ID
weight/probability
physical detector endpoints
virtual detector endpoints
ordinary matching half-edge status
logical observable label
original DEM provenance
detector coordinates / time provenance
```

The hard decoder may continue to use the ordinary merged matching-boundary representation.

## Step 5: run stage 2

Return:

```text
hard correction
ordinary MWPM correction weight
decoder growth / cluster data
```

The soft-output computation must not alter the hard decision.

## Step 6: build the logical analysis graph

Use one of the rigorously validated constructions:

- correlation-surface cut graph, preferably for the memory case;
- logical double cover as the geometry-independent fallback/reference.

Do not assign logical topology solely from coordinate heuristics.

## Step 7: transport cluster coverage

The analysis graph inherits the residual length of each original labelled stage-2 mechanism.

If the logical construction duplicates an edge, every lift represents the same original mechanism and inherits the same residual cost.

Do not independently grow decoder clusters on duplicated analysis edges.

## Step 8: compute the circuit-level swim distance

If the cut theorem is established:

\[
\phi_c^{\rm circ}
=
\operatorname{dist}
(B_c^0,B_c^1).
\]

Otherwise use the rigorously proved logical-cover algorithm.

## Step 9: optional witness

For debugging and validation, return a shortest logical witness and map it back through the decomposed DEM to original error-mechanism provenance.

Verify

\[
D_c^{\rm circ}z=0,
\qquad
L_c^{\rm circ}z=1.
\]

---

# 19. Required validation checks

The theorem should directly imply implementation tests.

## A. Perfect-measurement reduction

Verify theoretically and computationally:

\[
\phi_c^{\rm circ}
=
\phi_c^{\rm Phase1}
\]

in the `T=1` perfect-measurement limit.

## B. Logical witness test

Every returned witness must satisfy

\[
D_c^{\rm circ}z=0,
\qquad
L_c^{\rm circ}z=1.
\]

## C. Exhaustive small DEM

For small `d,T`, enumerate stage-2 mechanism subsets and compute independently

\[
\min_{Dz=0,\;Lz=1}\bar\omega(z).
\]

Compare with the proposed cut/cover algorithm.

## D. Stim graphlike-logical comparison

With zero cluster radii and compatible graphlike weights, compare against Stim's `shortest_graphlike_error`, which searches for a detector-invisible graphlike error with nonzero logical frame change.

This is an independent validation, not the definition of the color-code metric.

## E. Cut/cover equivalence

Whenever both constructions apply, prove and test that they return the same minimum.

## F. Correlation-surface gauge invariance

If two equivalent correlation-surface representatives define different microscopic cuts, the fundamental constrained metric should be invariant.

## G. Temporal-boundary audit

Explicitly enumerate/inspect first- and last-time one-detector mechanisms and verify their logical labels and analysis-graph treatment.

## H. Hard-decoder invariance

Soft-output graph construction must not alter the stage-2 hard correction.

---

# 20. Prior work to audit

The following literature is particularly relevant.

## Lee, Li, Bartlett

S.-H. Lee, A. Li, S. D. Bartlett,  
*Color code decoder with improved scaling for correcting circuit-level noise*, Quantum 9, 1609 (2025), arXiv:2404.07482.

Primary decoder-specific source for:

- circuit-level DEM decomposition;
- `c`-restricted and `c`-only DEMs;
- virtual detectors;
- logical-observable handling;
- graphlike filtering.

## Meister, Pattison, Preskill

N. Meister, C. A. Pattison, J. Preskill,  
*Efficient soft-output decoders for the surface code*, arXiv:2405.07433.

Important point:

- the cluster-contraction procedure is explicitly stated to apply to a 3D decoding graph for faulty measurements.

This supports the graph-metric portion, not the color-code logical-topology theorem.

## Stim DEM semantics

Stim represents mechanisms by probability, detector symptoms, and logical frame changes.

Its `shortest_graphlike_error` functionality is directly relevant because it searches graphlike combinations with zero detector syndrome and nonzero frame change.

## Hillmann et al.

T. Hillmann, G. Dauphinais, I. Tzitrin, M. Vasmer,  
*Single-shot and measurement-based quantum error correction via fault complexes*, arXiv:2410.12963.

Relevant for:

- dynamic QEC fault complexes;
- product constructions involving a code complex and a repetition-code/time complex;
- homological descriptions of logical correlations and faults.

## Delfosse and Paetznick

N. Delfosse, A. Paetznick,  
*Spacetime codes of Clifford circuits*, arXiv:2304.05943.

Relevant for mapping circuit fault correction to an associated spacetime stabilizer-code problem.

## Bombín et al.

H. Bombín et al.,  
*Fault-tolerant complexes*, arXiv:2308.07844.

Relevant as a broader homological treatment covering circuit-based fault-tolerant protocols and color-code families.

## Herzog et al. (2026)

L. S. Herzog, G. Kishony, R. Wille, A. Fowler,  
*Towards Lattice Surgery Compilation for the Color Code Using Pipe Diagrams*, arXiv:2607.05501.

Especially relevant to the geometric intuition:

- triangular 6.6.6 color-code spacetime/pipe representation;
- explicit correlation surfaces;
- stabilizers and syndrome-extraction circuits.

This is recent preprint-level prior work and should be described accordingly.

## Derks et al.

P.-J. H. S. Derks, A. Townsend-Teague, A. G. Burchards, J. Eisert,  
*Designing fault-tolerant circuits using detector error models*, arXiv:2407.13826.

Relevant for a DEM-first description of circuit-level fault tolerance.

---

# 21. Claims not to make yet

Do **not** claim any of the following before proof.

1. `M_c` is literally a Cartesian product of the code-capacity graph with time.
2. Every temporal matching half-edge is logically trivial.
3. All temporal boundary mechanisms can be merged into one spatial terminal class.
4. Every circuit-level logical fault is a simple boundary-to-boundary path in the raw `c`-only DEM.
5. The current Phase-2A PyMatching radii constitute the certified odd-cut dual required by the Phase-1 bound.
6. The selected-color circuit-level swim distance is a full-decoder logical gap or posterior LLR.
7. Lee's decomposed graphlike DEM exactly preserves the full correlated physical circuit-noise likelihood after X/Z separation and filtering.

These are either research questions or false without additional assumptions.

---

# 22. Target theorem package

A successful circuit-level theory phase should finish with approximately the following statements.

## Theorem A — fixed-fiber DEM logical quotient

\[
K_c^{\rm circ}/R_c^{\rm circ}
\cong
\operatorname{im}
(L_c^{\rm circ}|_{K_c^{\rm circ}}).
\]

For the one-observable memory setting, prove when the quotient has two classes.

## Theorem B — code-capacity reduction

\[
\phi_c^{\rm circ}
=
\phi_c^{\rm Phase1}
\]

in the perfect-measurement limit.

## Theorem C — circuit-level logical graph

Prove at least one of:

- a correlation-surface cut whose two sides encode odd logical parity;
- a canonical logical-cover algorithm computing the constrained logical minimum.

Ideally prove both and their equivalence for the memory setting.

## Theorem D — exact geometric/optimization meaning

\[
\phi_c^{\rm circ}
=
\min_{\substack{
D_c^{\rm circ}z=0\\
L_c^{\rm circ}z=1
}}
\bar\omega_c(z).
\]

## Theorem E — certified representative-gap lower bound

Under the required exact MWPM/dual assumptions,

\[
W_{c,\rm opp}^{\rm circ}
-
W_{c,\rm base}^{\rm circ}
\ge
\phi_c^{\rm circ}.
\]

## Algorithm — executable DEM pipeline

Specify, down to retained metadata, the map

```text
Stim DEM
-> Lee decomposition
-> fixed stage-1 fiber
-> labelled c-only graph
-> MWPM clusters
-> logical analysis graph
-> circuit-level swim distance
```

so that the numerical implementation can follow the theory directly.

---

# 23. Proof philosophy

Use the simplest mathematical layer that proves each statement.

- Use DEM linear algebra for detector/logical equivalence.
- Use Lee's Algorithm 1 for decoder-specific decomposition validity.
- Use fault-complex/spacetime topology only when geometric structure is needed.
- Use graph theory for cuts and logical covers.
- Use Meister's graph metric for cluster contraction.
- Use matching duality only for the certified representative-gap theorem.

Do not force the whole result into a heavy homological formalism if a shorter exact argument exists.

For a paper, the DEM/logical-map argument can likely live in the main text, while the full correlation-surface/fault-complex equivalence can be placed in an appendix.
