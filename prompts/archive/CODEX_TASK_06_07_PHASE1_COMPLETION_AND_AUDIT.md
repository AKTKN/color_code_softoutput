# Research Tasks 6 and 7: Define the color-code swim distance, complete Phase 1, and perform a full consistency and literature audit

We are continuing the research project on efficient soft-output decoding for color codes using the concatenated-matching decoder.

This run is intended to **complete Phase 1 of the project**.

Before doing any work, read the complete current project state:

- `AGENTS.md`
- `STATUS.md`
- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `REVIEW.md`

Also read every TeX file produced during Research Tasks 1–5.

Treat the current project files as authoritative.

If the numbering or naming of Research Tasks 6 and 7 in `PROJECT_DETAIL.md` differs from the labels below, preserve the current project numbering and map this prompt onto the remaining Phase-1 objectives. Do not overwrite a newer project definition merely to match this prompt.

Do not assume earlier results are correct merely because they have been marked complete. This run includes a final global audit.

---

# Phase-1 target

The completed Phase-1 result should establish a rigorous method for defining and computing a Meister-style cluster-gap / swim-distance quantity for a fixed color branch of the concatenated-matching decoder on a triangular color code.

The intended logical progression is

\[
L_{2D}
\longrightarrow
L_c^*
\longrightarrow
\widetilde L_c^*
\longrightarrow
\text{logical boundary-to-boundary topology}
\longrightarrow
\text{decoder-cluster contraction}
\longrightarrow
\phi_c.
\]

The final Phase-1 manuscript must distinguish exactly what has been proved, what is inherited from prior work, and what remains for later phases.

The primary target is the **per-color stage-2 swim-distance construction and its validity**. Do not automatically proceed to the final three-color aggregation problem.

---

# Research Task 6 — Cluster contraction and swim-distance definition

## 1. Re-extract the Meister construction from the primary paper

Re-read Meister–Pattison–Preskill and extract only the ingredients needed here:

- decoder-generated clusters;
- quotient / zero-cost interpretation of a cluster;
- inequivalent logical boundaries;
- the shortest path covering a logical operator;
- the shortest-path algorithm used to compute the soft output.

Distinguish carefully between:

- Union-Find clusters;
- MWPM / Blossom dual-growth clusters;
- surface-code-specific facts;
- purely graph-theoretic facts.

Do not silently transfer surface-code-specific theorems to the color-code stage-2 graph.

## 2. Define the stage-2 decoder clusters

For fixed color branch \(c\), define exactly what cluster information is required from the stage-2 decoder.

For MWPM, use the correct Blossom / LP-dual growth notion adopted by Meister, not an arbitrary connected component of the final correction.

If the practical implementation uses PyMatching or another library, distinguish:

- the mathematical cluster object required by the theory;
- the data actually exposed by the implementation;
- any additional instrumentation needed to reconstruct the required cluster/radius information.

If Union-Find is discussed, define its cluster object separately.

## 3. Define the cluster-contracted / zero-cost graph

Starting from the boundary-resolved graph \(\widetilde L_c^*\) and a decoder-generated cluster set \(\mathcal C_c\), define the quotient graph/metric in which each connected decoder cluster is contracted to a point.

Equivalently, if more convenient algorithmically, define modified edge weights

\[
\bar w_c(e)
\]

such that edges internal to fully grown clusters have zero cost while all other edges retain their stage-2 weight.

Prove that the chosen implementation is equivalent to the intended quotient construction.

Treat explicitly:

- clusters touching one boundary class;
- clusters touching both boundary classes;
- merged clusters;
- zero-length logical paths;
- disconnected components;
- nonuniform weighted decoding.

## 4. Define the per-color swim distance

Using the logical-topology theorem proved in Task 4, define the per-color stage-2 swim distance \(\phi_c\).

If Tasks 4–5 establish two inequivalent boundary classes \(B_c^{(0)}\) and \(B_c^{(1)}\), the expected form is

\[
\phi_c
=
\operatorname{dist}_{\bar G_c}
\bigl(B_c^{(0)},B_c^{(1)}\bigr),
\]

or the exact equivalent in the notation established by the project.

The definition must follow from the logical-topology theorem rather than from analogy alone.

Explain explicitly why the shortest chain between these classes represents a nontrivial logical operator after cluster contraction.

## 5. Give a concrete computation algorithm

Provide a precise algorithm for calculating \(\phi_c\) after stage-2 decoding.

Specify:

1. input stage-2 graph and weights;
2. decoder output and cluster information;
3. reconstruction/use of the boundary-resolved graph;
4. zeroing or contracting cluster-internal edges;
5. shortest-path calculation between inequivalent boundary classes;
6. returned soft-output value.

State the graph-theoretic computational complexity in terms of \(|V|\) and \(|E|\), and separate worst-case complexity from practical decoder-side overhead.

---

# Research Task 7 — Phase-1 validity statement and integration

## 6. State exactly what \(\phi_c\) measures

Give a precise interpretation of \(\phi_c\) and separate claims that must not be conflated.

At minimum distinguish:

1. \(\phi_c\) as the minimum cluster-contracted cost of a nontrivial logical chain in the fixed \(c\)-branch stage-2 graph;
2. \(\phi_c\) as a geometry-based decoder-confidence proxy;
3. a possible lower bound on a minimum-representative opposite-logical-class weight difference, if a Meister-type theorem transfers;
4. the syndrome-conditioned logical-class LLR, which is not automatically equal to \(\phi_c\);
5. the full comparative/logical gap of the complete concatenated decoder, which is not automatically equal to \(\phi_c\) because stage 1 and the three-color branch selection have not yet been included.

State only claims that are proved.

## 7. Determine which Meister analytical results transfer

Review the relevant Meister proofs in detail.

Determine which ingredients depend only on:

- weighted graph structure;
- MWPM dual variables / cluster growth;
- two logical equivalence classes;
- a boundary-to-boundary representative of the nontrivial class;

and which use special surface-code geometry.

Attempt to transfer the strongest justified result to the fixed stage-2 branch.

A possible target, **only if rigorously supported**, is

\[
W_{c,\mathrm{opp}}^{(2)}-W_{c,\mathrm{base}}^{(2)}
\ge \phi_c.
\]

Do not assume this inequality.

If it can be proved, state all hypotheses and prove it carefully.

If it cannot be proved, identify exactly where the Meister proof fails and retain \(\phi_c\) only as a geometrically justified soft-output proxy.

This distinction is essential.

## 8. Delimit Phase 1 explicitly

At the end of the mathematics, state exactly what Phase 1 has accomplished.

Phase 1 should contain only what is established for a **fixed color branch and its stage-2 decoding graph**.

Explicitly list what remains outside Phase 1, including as applicable:

- stage-1 uncertainty;
- failures originating in the first restricted matching;
- combination of \(\phi_r,\phi_g,\phi_b\);
- interaction with final minimum-weight branch selection;
- relation to the full comparative/logical gap;
- numerical calibration against logical failure probability;
- circuit-level extensions not yet proved;
- BP-LSD / hypergraph generalization.

Do not accidentally solve or claim these later problems.

---

# Phase-1 manuscript integration

After Tasks 6 and 7 are complete, consolidate the entire Phase-1 theory into one coherent LaTeX manuscript section or technical note.

The final text should read as a continuous mathematical development rather than a sequence of research logs.

A reasonable structure is:

```text
1. Mathematical setup and triangular color codes
2. Concatenated-matching decoder
3. Stage-2 monochromatic lattice and boundary structure
4. Boundary-resolved stage-2 graph
5. Stage-2 chains and physical Pauli operators
6. Logical-topology correspondence
7. Meister-type modified decoding graph
8. Decoder clusters and cluster contraction
9. Color-code stage-2 swim distance
10. Scope, limitations, and next phase
```

Use the actual project notation and theorem numbering.

Remove duplicated definitions, reconcile notation, and resolve contradictions among earlier TeX files.

Do not write a broad motivation/related-work introduction unless necessary for local mathematical context; that writing phase is separate.

---

# Comprehensive prior-work audit

Perform a serious literature check before finalizing Phase 1.

Search primary literature for all major structural claims used in the derivation, including:

- foundational color-code papers;
- homological / topological formulations of 2D color codes;
- Delfosse projection decoding;
- color-code-to-surface/toric-code mappings and unfolding;
- color-code boundaries, anyon condensation, strings, and string-nets;
- triangular color-code logical operators;
- Lee–Li–Bartlett concatenated-matching decoder;
- follow-up work using its logical gap or post-selection;
- Meister–Pattison–Preskill soft-output / cluster-gap method;
- later work on bounded cluster gap, extra-cluster gap, swim distance, or related confidence metrics;
- any work that may already extend cluster-gap/swim-distance ideas beyond surface codes.

For every potentially relevant result:

1. read the original source;
2. record exactly what it proves;
3. compare its assumptions with ours;
4. determine whether our statement is equivalent, weaker, stronger, or unrelated;
5. verify that our notation and terminology do not misrepresent the source.

Do not make a priority or novelty claim merely because an immediate search does not find an overlap.

If a directly overlapping result exists, revise the Phase-1 positioning accordingly.

Update `REFERENCES.md`.

---

# Full independent review / claim audit

After the manuscript is integrated, perform a separate second pass whose sole purpose is to find errors.

First compile the review in `REVIEW.md`; do not silently edit away problems while reading.

For every Definition, Lemma, Proposition, Corollary, and Theorem, classify it as:

- imported directly from prior work;
- straightforward adaptation;
- new derivation;
- conjectural / unresolved.

Then test every new derivation for:

- logical gaps;
- circular reasoning;
- unstated assumptions;
- ambiguous domains/codomains;
- misuse of graph versus chain-complex language;
- incorrect corner/boundary handling;
- confusion between physical and artificial boundary nodes;
- confusion between stage-1 and stage-2 structures;
- misuse of the \(\epsilon_c\) bijection;
- claims that hold only for one lattice drawing;
- small-distance counterexamples;
- incorrect generalization from the surface code;
- incorrect relative-homology statements;
- accidental assumptions that all graph cycles are stabilizers;
- accidental assumptions that all logical operators are simple paths;
- incorrect or unverifiable citations;
- unsupported novelty statements.

Pay special attention to whether the proof of the logical-path theorem establishes exactly the statement needed by the shortest-path swim-distance algorithm.

---

# Hallucination control

For every citation-dependent claim:

- verify it against the original source;
- remove or weaken the claim if the source does not support it;
- do not retain references based only on title/abstract similarity;
- do not cite a paper for a theorem it does not contain.

For every mathematical claim generated during this project:

- independently rederive it;
- list all assumptions;
- test representative small-code cases analytically or computationally when feasible;
- mark unproved statements as open issues rather than established facts.

If a claim cannot be verified, remove it from the theorem-level manuscript and place it in `REVIEW.md` or an open-issues subsection.

---

# Consistency checks against prior work

Explicitly check for contradictions with:

1. Lee–Li–Bartlett's definitions of \(L_{\neg c}^*\), \(L_c^*\), \(\epsilon_{\neg c}\), and \(\epsilon_c\);
2. their proof that concatenated matching returns a valid correction;
3. known boundary and logical-string structure of triangular color codes;
4. Delfosse's projection formalism;
5. color-code-to-surface/toric-code equivalence literature;
6. Meister's exact cluster-gap definition and the hypotheses of its analytical results.

If our formulation differs from prior notation, explain the translation explicitly.

If a contradiction is found, resolve it before Phase 1 is declared complete.

---

# Optional finite-size sanity checks

Where useful, construct small triangular color-code examples and verify claims explicitly.

Suggested tests include:

- enumerate physical data-qubit supports at small \(d\);
- construct \(L_c^*\) and \(\widetilde L_c^*\);
- verify the edge/qubit bijection;
- verify boundary classification;
- test representative boundary-to-boundary paths;
- map them to physical Pauli operators;
- verify syndrome triviality and logical parity;
- test representative closed cycles;
- verify cluster contraction and shortest-path calculation.

These tests are supporting evidence only and do not replace a general proof.

If scripts are used, save them in an appropriate research-support directory and document exactly what each script verifies.

---

# Final Phase-1 deliverables

Produce or update:

- a coherent Phase-1 TeX manuscript/note;
- `NOTATIONS.md`;
- `REFERENCES.md`;
- `PROJECT_DETAIL.md`;
- `STATUS.md`;
- `REVIEW.md`;
- `AGENTS.md` if the project milestone or next phase changes.

If useful, create a dedicated file such as

```text
tex/phase1_swim_distance.tex
```

or consolidate into the existing manuscript structure.

`STATUS.md` should explicitly state:

- which Phase-1 theorems are proved;
- which statements remain conditional;
- which open issues remain;
- what begins Phase 2.

`REVIEW.md` should retain unresolved concerns even if the main manuscript is polished.

---

# Phase-1 completion criteria

Phase 1 is complete only when:

1. the boundary-resolved stage-2 graph is rigorously defined;
2. the edge-chain to physical-Pauli map is rigorous;
3. the logical-topology correspondence is proved at the required level;
4. the relation to Meister's modified decoding graph is precise;
5. decoder clusters and cluster contraction are defined correctly;
6. the per-color swim distance \(\phi_c\) is rigorously defined;
7. the shortest-path computation is justified by the logical-topology theorem;
8. any transferred Meister bound is either rigorously proved under explicit assumptions or explicitly withheld;
9. the scope of \(\phi_c\) relative to the full concatenated decoder is stated correctly;
10. all major claims have been checked against primary literature;
11. the manuscript has passed an independent logical and citation audit;
12. unsupported, hallucinated, or overly strong statements have been removed or downgraded;
13. all project files are mutually consistent.

Only after all of these conditions are satisfied should `STATUS.md` mark Phase 1 as complete.

Then stop.

Do not proceed automatically to the three-color aggregation problem, numerical validation, or later phases.
