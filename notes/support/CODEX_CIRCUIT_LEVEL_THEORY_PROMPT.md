# Codex Research Task: Rigorous circuit-level extension of the fixed-branch color-code swim distance

We are continuing the color-code soft-output project after completion of the perfect-measurement Phase-1 theory and the initial Phase-2A implementation.

The next objective is to construct a rigorous **circuit-level theory** for the fixed-color stage-2 swim distance used with the Lee--Li--Bartlett concatenated MWPM decoder.

Before doing any derivation, read:

- `AGENTS.md`
- `STATUS.md`
- `PROJECT_DETAIL.md`
- `NOTATIONS.md`
- `REFERENCES.md`
- `REVIEW.md`
- the complete current Phase-1 `note.tex`
- the circuit-level theory sketch supplied with this task
- current Phase-2A implementation/status documents, using them only as implementation evidence rather than mathematical proof.

Treat the current project documents as authoritative where they contain later corrections.

---

# Overall goal

Develop a theorem-level circuit-level generalization of the fixed-color stage-2 swim distance that is precise enough to support the next numerical implementation phase.

The final result must answer both:

1. **Mathematical validity:** what exactly is the circuit-level logical class in the `c`-only stage-2 DEM, and why does the proposed soft-output metric measure the minimum opposite-logical fixed-fiber cost?
2. **Executable construction:** given a Stim circuit/DEM, exactly what objects and metadata are transformed and passed to the decoder/soft-output computation?

Do not proceed to sliding-window decoding.

Do not use numerical behavior as a substitute for proof.

---

# Central methodological instruction

Do **not** begin by assuming that the circuit-level graph is simply the code-capacity graph extruded through time.

Investigate that intuition, but use the detector error model as the primary exact object.

Use the hierarchy

```text
DEM algebra
    -> exact logical-class statement
    -> spacetime/correlation-surface interpretation
    -> modified graph / shortest-path algorithm
```

rather than the reverse.

---

# CL1 — Formalize the circuit-level DEM

Start from one Pauli sector of the original circuit DEM

\[
\mathcal M=\{(q_e,D_e,O_e)\}.
\]

Define explicit binary maps

\[
B,\qquad L
\]

for detector incidence and logical-observable/frame-change parity.

Then reproduce Lee--Li--Bartlett's color decomposition carefully:

\[
\mathcal M_{\neg c},
\qquad
\mathcal M_c.
\]

Track:

- X/Z separation;
- compression;
- construction of virtual detectors;
- replacement of non-`c` detector targets;
- logical observable targets;
- graphlike filtering.

Use Lee's original paper and the current implementation as separate sources: the paper establishes the intended algorithm; the code is evidence of the current realization.

For the `c`-only model define

\[
D_c^{\rm circ},
\qquad
L_c^{\rm circ},
\qquad
\omega_c.
\]

Explicitly type:

- physical detector rows;
- stage-1 virtual detector rows;
- artificial matching boundary;
- mechanism/edge IDs;
- observable labels;
- provenance through compression.

---

# CL2 — Prove the fixed-fiber logical quotient

Fix a stage-1 result and the corresponding real stage-2 syndrome `s_c`.

Define

\[
K_c^{\rm circ}
=
\ker D_c^{\rm circ},
\]

\[
R_c^{\rm circ}
=
\ker D_c^{\rm circ}
\cap
\ker L_c^{\rm circ},
\]

\[
\mathcal Q_c^{\rm circ}
=
K_c^{\rm circ}/R_c^{\rm circ}.
\]

Prove

\[
\mathcal Q_c^{\rm circ}
\cong
\operatorname{im}
(L_c^{\rm circ}|_{K_c^{\rm circ}}).
\]

For the one-logical-observable memory experiment, determine and prove the conditions under which

\[
\operatorname{im}
(L_c^{\rm circ}|_{K_c^{\rm circ}})
=
\mathbb F_2.
\]

Interpret the result in decoder language:

```text
same stage-1 fiber
same real stage-2 syndrome
detector-invisible difference
same/opposite logical frame
```

Do not identify `R_c^{circ}` with the static face-stabilizer group unless a separate theorem justifies that statement.

---

# CL3 — Prove observable-faithfulness of Lee's decomposed DEM

Trace the logical observable through

```text
physical circuit
-> original DEM
-> X/Z-separated DEM
-> compression
-> c-restricted DEM
-> c-only DEM
```

Determine exactly which transformations preserve logical target parity and which change the probability model.

Address explicitly:

- X/Z correlation removal;
- compression of same-target mechanisms;
- removal of non-edge-like mechanisms;
- observable targets during compression;
- mapping decomposed mechanisms to original DEM faults.

The likely target claim is:

> The logical label is exact within the decomposed DEM actually used by the concatenated decoder.

Do not promote this to an exact statement about the original correlated circuit-noise distribution unless it is proved.

---

# CL4 — Investigate the spacetime geometry

Now investigate the user's geometric intuition.

Questions:

1. Can the standard triangular 6.6.6 memory protocol be represented as a triangular prism/fault complex in the precise sense needed here?
2. What is the relevant logical correlation surface?
3. How does the `c`-only decomposed DEM relate to that spacetime object?
4. How should stage-1 virtual detectors be represented?
5. What are the distinct spatial, temporal, matching, and logical boundary objects?
6. How do first/last-time one-detector mechanisms behave?
7. Is there a deformation/retraction or exact map from the circuit-level object to the Phase-1 perfect-measurement topology?

Consult, at minimum:

- Hillmann et al., fault complexes;
- Delfosse--Paetznick, spacetime codes;
- Bombín et al., fault-tolerant complexes;
- Herzog et al. (2026), color-code pipe diagrams/correlation surfaces;
- Derks et al., detector-error-model circuit design.

For every claim classify it as:

```text
existing theorem
direct adaptation
our derivation
conjecture/open issue
```

The geometric picture must agree with the exact DEM logical map.

---

# CL5 — Define and interpret the logical cocycle

For the one-observable `c`-only graph define

\[
\lambda_c(e)
=
L_c^{\rm circ}[e].
\]

For

\[
z\in K_c^{\rm circ},
\]

\[
\lambda_c(z)
=
L_c^{\rm circ}z.
\]

Investigate whether this functional is naturally a cohomology class/cocycle of an appropriate circuit/fault complex.

If a logical correlation surface `Sigma_L` exists, prove a pairing of the form

\[
L_c^{\rm circ}z
=
\langle z,\Sigma_L\rangle
\pmod 2.
\]

Define the chain/cochain complex and pairing explicitly.

Do not infer the theorem only from a figure.

---

# CL6 — Define the fundamental circuit-level swim distance

Define, before choosing a special graph representation,

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

Here `bar omega_c` is the residual cost after decoder-cluster contraction.

Prove that this is the minimum contracted cost of a detector-invisible opposite-logical fixed-fiber stage-2 difference.

This is the central circuit-level definition.

A multi-observable extension may be stated as a remark but should not distract from the one-logical memory theorem.

---

# CL7 — Prove exact reduction to Phase 1

Construct the perfect-measurement/code-capacity limit.

Prove that:

- the circuit-level detector map reduces to the Phase-1 stage-2 map;
- the logical observable map reduces to the Phase-1 terminal/logical parity;
- the circuit-level metric satisfies

\[
\phi_c^{\rm circ}
=
\phi_c^{\rm Phase1}.
\]

This consistency theorem is mandatory.

Do not replace it by small-code numerics.

---

# CL8 — Construct an efficient modified logical graph

Develop and compare two constructions.

## A. Correlation-surface cut graph

If the memory spacetime admits a logical correlation-surface cut, construct a graph with two inequivalent boundary sets

\[
B_c^0,\qquad B_c^1
\]

such that an odd logical class has a boundary-to-boundary representative.

Target:

\[
\phi_c^{\rm circ}
=
\operatorname{dist}_{\bar G_c^{\rm cut}}
(B_c^0,B_c^1).
\]

Prove:

- how the graph is cut;
- which vertices/edges are duplicated;
- how half-edges are treated;
- how temporal mechanisms are prevented from creating false shortcuts;
- invariance under equivalent choices of correlation-surface representative.

## B. Logical binary double cover

Independently construct the canonical cover with vertices

\[
(v,a),\qquad a\in\mathbb F_2,
\]

and lifted edge

\[
(u,a)\leftrightarrow(v,a+\lambda_e).
\]

Prove exactly how logical-odd chains are represented in the cover.

Determine the correct shortest-path/shortest-cycle reduction, including matching-boundary handling.

Do not state a one-Dijkstra complexity unless proved.

Use the double cover as a geometry-independent fallback and independent validation of the cut construction.

---

# CL9 — Transfer cluster contraction

Re-read Meister--Pattison--Preskill.

They explicitly state that the same procedure applies to a 3D decoding graph with faulty measurements.

Determine precisely which parts transfer graph-theoretically.

Treat:

- spatial, timelike, and diagonal edges;
- virtual-detector vertices;
- half-edges;
- clusters touching boundaries;
- partial edge coverage;
- duplicated edges in cut/cover graphs.

Prove how residual edge costs are transported through the logical graph construction.

If an edge is duplicated, all copies must inherit the same residual cost from the same original stage-2 mechanism; no independent decoder growth is introduced on the analysis graph.

---

# CL10 — Circuit-level representative-gap theorem

Define

\[
W_{c,\mathrm{base}}^{\rm circ},
\qquad
W_{c,\mathrm{opp}}^{\rm circ}.
\]

Attempt to prove

\[
W_{c,\mathrm{opp}}^{\rm circ}
-
W_{c,\mathrm{base}}^{\rm circ}
\ge
\phi_c^{\rm circ}
\]

under the same class of certified optimal MWPM dual assumptions as Phase 1.

Separate clearly:

1. the theorem under a certified dual;
2. the practical metric computed from currently exported Sparse-Blossom growth balls.

Do not call the current production radii a certified odd-cut dual without proof.

---

# CL11 — Give an executable DEM-to-decoder algorithm

The theory document must end with an algorithm detailed enough for implementation.

Specify:

```text
Stim circuit
-> original DEM
-> detector/observable metadata
-> Lee Pauli/color decomposition
-> stage-1 MWPM
-> virtual syndrome
-> c-only stage-2 graph
-> stage-2 MWPM
-> growth/cluster information
-> logical cut or cover
-> residual graph
-> phi_c^circ
```

For each stage state:

- inputs;
- outputs;
- stable IDs/provenance;
- detector coordinates/time;
- graph vertices;
- graph edges;
- edge probabilities/weights;
- logical labels;
- boundary metadata;
- what goes into PyMatching;
- what is analysis-only.

The preferred architecture leaves the existing hard decoder unchanged.

---

# CL12 — Derive implementation validation tests

At minimum specify:

## Perfect-measurement reduction

\[
\phi_c^{\rm circ}
=
\phi_c^{\rm Phase1}.
\]

## Exhaustive small DEM test

For small `d,T`, enumerate mechanism subsets and compare

\[
\min_{Dz=0,Lz=1}\bar\omega(z)
\]

with the proposed graph algorithm.

## Logical witness

Every returned witness satisfies

\[
Dz=0,\qquad Lz=1.
\]

## Stim comparison

With zero radii and compatible graphlike weights, compare suitable cases to Stim's `shortest_graphlike_error`.

## Cut/cover equivalence

Where both apply, the two computations agree.

## Correlation-surface representative invariance

Equivalent cuts yield the same fundamental metric.

## Temporal-boundary audit

First/last-time half-edges are explicitly checked.

## Hard-decoder invariance

Soft-output construction does not alter the ordinary stage-2 MWPM correction.

---

# Primary-literature audit

Perform a fresh literature search.

At minimum inspect:

1. S.-H. Lee, A. Li, S. D. Bartlett, circuit-level concatenated matching, arXiv:2404.07482 / Quantum 9, 1609 (2025).
2. N. Meister, C. Pattison, J. Preskill, soft-output decoding, arXiv:2405.07433.
3. Stim DEM documentation and `shortest_graphlike_error` semantics.
4. T. Hillmann et al., fault complexes, arXiv:2410.12963.
5. N. Delfosse, A. Paetznick, spacetime codes, arXiv:2304.05943.
6. H. Bombín et al., fault-tolerant complexes, arXiv:2308.07844.
7. L. Herzog et al., color-code pipe diagrams/correlation surfaces, arXiv:2607.05501.
8. P.-J. Derks et al., detector error models, arXiv:2407.13826.

Also search for prior work on:

- circuit-level color-code soft output;
- observable-labelled shortest paths in DEMs;
- `Z_2` logical double covers;
- logical correlation-surface decoding;
- DEM-native minimum undetected logical chains.

Do not make a novelty claim without a dedicated overlap search.

Update `REFERENCES.md`.

---

# Independent adversarial review

After the derivation, separately try to break it.

Check:

1. Is the logical theorem exact for the decomposed DEM or only the original DEM?
2. Can compression merge mechanisms with incompatible observable labels?
3. Can graphlike filtering delete the minimum logical mechanism and change the quotient?
4. Is X/Z separation being confused with physical statistical independence?
5. Are temporal half-edges being assigned a logical class from coordinates alone?
6. Can the artificial matching boundary create a false logical shortcut?
7. Are virtual detectors incorrectly treated as physical checks?
8. Does the cut graph encode `Lz` correctly for every detector-invisible chain?
9. Can a logical odd cycle evade the proposed boundary-to-boundary representation?
10. Does the double-cover proof handle free matching boundaries correctly?
11. Does cluster contraction commute with the cut/cover transformation?
12. Is the Phase-1 reduction exact?
13. Does any statement depend on a specific CNOT schedule?
14. Which statements are limited to the standard triangular 6.6.6 memory circuit?
15. Which statements fail as soon as the future temporal boundary is open, as in sliding-window decoding?

Record unresolved issues in `REVIEW.md`.

Do not suppress counterexamples.

---

# Deliverables

Create a rigorous TeX note, for example:

```text
tex/circuit_level_swim_distance.tex
```

Suggested structure:

```text
1. Circuit-level DEM setup
2. Lee color decomposition
3. Fixed-fiber logical quotient
4. Observable-faithfulness
5. Spacetime/correlation-surface interpretation
6. Logical cut and double cover
7. Cluster contraction
8. Circuit-level swim distance
9. Certified representative-gap bound
10. Concrete DEM/PyMatching algorithm
11. Code-capacity reduction
12. Scope and limitations
```

Also create/update:

- `CIRCUIT_LEVEL_THEORY.md` — readable research summary;
- `NOTATIONS.md`;
- `REFERENCES.md`;
- `PROJECT_DETAIL.md`;
- `STATUS.md`;
- `REVIEW.md`.

Update `AGENTS.md` only for project-level state changes.

---

# Completion criteria

Do not mark this circuit-level theory complete unless:

1. `D_c^{circ}` and `L_c^{circ}` are formally defined.
2. The fixed-fiber logical quotient is proved.
3. The exact scope/approximation of Lee's DEM decomposition is stated.
4. `phi_c^{circ}` is defined independently of a drawing.
5. Phase 1 is recovered exactly in the perfect-measurement limit.
6. An efficient logical graph construction is rigorously justified for the memory experiment, or its absence is explicitly reported.
7. Temporal boundaries are treated correctly.
8. Cluster contraction is proved compatible with the logical graph construction.
9. The certified gap theorem is proved under explicit assumptions or explicitly withheld.
10. The final algorithm specifies exactly how a Stim DEM is processed and what metadata reaches the hard decoder versus the soft-output analyzer.
11. Primary literature has been audited.
12. An adversarial review has been completed.

Then stop.

Do not proceed automatically to sliding-window decoding or numerical implementation changes.
