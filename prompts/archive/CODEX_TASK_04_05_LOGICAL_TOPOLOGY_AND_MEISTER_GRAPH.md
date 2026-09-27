# Research Tasks 4 and 5: Prove the logical-topology correspondence and identify the Meister-type modified decoding graph

We are continuing the research project on efficient soft-output decoding for color codes using the concatenated-matching decoder.

Before doing any work, read the current project state carefully:

- `AGENTS.md`
- `STATUS.md`
- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `REVIEW.md`

Also read all TeX files produced in Research Tasks 1–3, especially the mathematical preliminaries, the rigorous boundary structure of the stage-2 monochromatic lattice, the boundary-resolved graph, and the map from stage-2 edge chains to physical Pauli operators.

Treat the current project files as authoritative. Do not rely on earlier prompts when the project files contain a more recent corrected formulation.

Before beginning the new derivation, verify that the definitions and lemmas from Tasks 1–3 are sufficient and internally consistent. If a dependency is incomplete or incorrect, repair that dependency first and record the issue in `REVIEW.md`.

---

# Objectives

This run has exactly two central mathematical objectives.

## Research Task 4

> **Prove the logical-topology correspondence for the boundary-resolved stage-2 graph \(\widetilde L_c^*\): characterize which stage-2 chains map to stabilizer-trivial physical Pauli operators and which chains connecting the topologically inequivalent boundary classes map to the nontrivial logical Pauli class.**

## Research Task 5

> **Use the result of Task 4 to identify \(\widetilde L_c^*\), in the precise sense required for soft-output computation, with a Meister-type modified decoding graph whose inequivalent boundary components encode the nontrivial logical topology.**

Do **not** yet define cluster contraction or the final swim-distance quantity. Those are deferred to Tasks 6 and 7.

---

# Part I: Restate the precise setup

Fix a color \(c\in\{r,g,b\}\) and one CSS decoding sector.

Restate, using the current notation in `NOTATIONS.md`:

- the triangular color-code patch \(L_{2D}\);
- the stage-2 monochromatic graph \(L_c^*\);
- the boundary-resolved graph \(\widetilde L_c^*\);
- its boundary components/classes;
- the forgetful/quotient map to \(L_c^*\);
- the edge/qubit bijection induced by \(\epsilon_c\);
- the map from a chain \(\Gamma\in C_1(\widetilde L_c^*;\mathbb F_2)\) to a physical Pauli operator \(P_c(\Gamma)\);
- the graph-boundary / syndrome compatibility established in Task 3.

Clearly separate physical color-code boundaries, artificial matching boundary nodes, boundary classes in \(\widetilde L_c^*\), physical syndrome/check vertices, and stage-1 virtual syndrome.

---

# Part II: Research Task 4 — Logical-topology correspondence

The central question is:

> Which chains in \(\widetilde L_c^*\) correspond, under the stage-2 edge-to-physical-Pauli map, to stabilizers, and which correspond to a nontrivial logical Pauli?

This must be proved from the color-code structure, not assumed from the surface-code analogy.

## 1. Define the relevant equivalence relation

Define physical Pauli equivalence modulo the stabilizer group in the chosen CSS sector. For stage-2 chains \(\Gamma_1,\Gamma_2\), define precisely when

\[
P_c(\Gamma_1)\sim_{\mathcal S}P_c(\Gamma_2).
\]

Translate this into a statement about the symmetric difference \(\Gamma_1\oplus\Gamma_2\).

## 2. Characterize stabilizer-trivial chains

Prove the strongest correct statement relating graph cycles / relative cycles in \(\widetilde L_c^*\) to stabilizer operators of the color code.

Do not assume that every graph-theoretic cycle is a stabilizer.

Determine precisely:

- which closed chains correspond to products of face stabilizers;
- whether additional relations are required near boundaries or corners;
- whether relative homology is the correct language;
- whether the relevant homology lives on \(\widetilde L_c^*\) itself or on a chain complex induced from the physical color-code lattice;
- how the map \(P_c\) descends to the resulting quotient.

If a chain-complex map is required, define it explicitly.

## 3. Prove the boundary-to-boundary logical statement

Using the exact boundary classes established in Tasks 1 and 2, prove the main theorem.

The intended form is:

> A chain/path in \(\widetilde L_c^*\) whose relative boundary connects the two topologically inequivalent boundary classes maps to a physical Pauli operator in the nontrivial logical class of the triangular color code.

Write the theorem using the exact current notation.

State explicitly every required hypothesis, including any dependence on connectedness, simple-path representatives, fixed CSS sector, one encoded logical qubit, triangular boundary structure, odd distance, or a particular class of 2-colex lattices.

Do not generalize beyond what is proved.

## 4. Prove the converse needed for swim-distance computation

Determine and prove the converse statement actually required later: the nontrivial logical class must admit an appropriate boundary-to-boundary representative in \(\widetilde L_c^*\).

Aim for the strongest justified statement of the form

\[
[P_c(\Gamma)]\neq[I]
\quad\Longleftrightarrow\quad
[\Gamma]\neq 0
\]

in the appropriate relative-homology or quotient space.

If full equivalence is too strong, formulate the exact one-sided statement sufficient for the later shortest-path construction.

## 5. Cross-check with standard color-code logical representatives

Check the theorem against standard descriptions of triangular color-code logical operators:

- logical operators supported along one physical color boundary;
- colored string operators terminating at color boundaries;
- string-net representatives terminating at the three boundaries;
- stabilizer deformation between equivalent representatives.

Explain how these descriptions correspond to the stage-2 boundary-resolved chain picture. This is a consistency check, not a substitute for the proof.

## 6. Surface-code comparison

Only after the color-code proof is complete, compare the result with the planar surface-code case.

State clearly:

- what is mathematically identical;
- what is only analogous;
- what role is played by the monochromatic stage-2 representation;
- why the full color-code string-net structure reduces to a path-like object in the fixed \(c\)-branch stage-2 representation.

Do not use the surface-code argument as the primary proof unless a rigorous chain-map equivalence has independently been established.

---

# Part III: Research Task 5 — Meister-type modified decoding graph

Meister et al. define the surface-code soft output on a decoding graph with inequivalent boundary nodes, where a path between those boundaries covers a logical operator.

Using Task 4, establish the corresponding structure for \(\widetilde L_c^*\).

## 7. State the exact correspondence

Formulate a proposition stating that, for fixed \(c\) and a chosen CSS sector:

1. stage-2 edges correspond bijectively to physical data-qubit errors;
2. the graph boundary reproduces the relevant stage-2 syndrome constraints, modulo artificial boundary nodes;
3. the inequivalent boundary classes encode the endpoints of the nontrivial relative logical class;
4. a chain connecting these boundary classes represents a nontrivial logical Pauli.

Do not claim that the entire concatenated decoder is equivalent to a surface-code decoder. The identification is only at the level required for stage-2 soft-output topology.

## 8. Define the modified-decoding-graph interpretation

Explain precisely in what sense \(\widetilde L_c^*\) plays the role of Meister's modified decoding graph.

If useful, use terminology such as **boundary-resolved stage-2 decoding graph** rather than literally calling it a surface-code graph.

State explicitly which assumptions of the Meister construction are already satisfied and which will only become relevant when cluster contraction is introduced.

## 9. Check compatibility with stage-2 weights

Verify that the ordinary stage-2 edge weights transfer to \(\widetilde L_c^*\) without ambiguity.

Define the weight function, e.g.

\[
w_c:\Delta_1(\widetilde L_c^*)\to\mathbb R_{\ge0},
\]

or the weighted version already adopted in the project.

Explain why boundary splitting does or does not alter any physical edge weight.

Do not yet modify weights according to decoder clusters.

---

# Literature verification

Conduct a focused literature search using primary sources for:

- triangular color-code logical operators;
- color-code boundaries and anyon condensation;
- string and string-net operators;
- homological / chain-complex formulations of color codes;
- projection decoding and restricted lattices;
- concatenated-matching decoding and monochromatic lattices;
- local mappings between color codes and surface/toric codes;
- Meister et al.'s soft-output / cluster-gap construction.

For every borrowed theorem or structural statement:

1. identify exactly what the source proves;
2. determine whether it applies directly to our object;
3. distinguish imported fact, adaptation, and new derivation.

Specifically check that our result does not contradict known color-code topology or Lee–Li–Bartlett's definitions and validity proof.

Do not invent a novelty claim.

Update `REFERENCES.md` with newly verified primary sources.

---

# Independent mathematical review

After deriving Tasks 4 and 5, perform a separate adversarial review and try to disprove the main theorem.

Check at least:

1. Are all chain groups and boundary maps well-defined?
2. Is the stabilizer quotient correctly represented?
3. Are all boundary and corner cases handled?
4. Can a boundary-to-boundary path map to a stabilizer?
5. Can a nontrivial logical operator fail to admit the claimed stage-2 representative?
6. Are there closed stage-2 cycles that are logical rather than stabilizer-trivial?
7. Does the proof accidentally assume the desired result?
8. Does it rely on a particular drawing of the 6.6.6 code?
9. Does it apply to the intended family of triangular 2-colexes?
10. Is the role of stage-1 virtual syndrome irrelevant to the topological theorem, and has that been shown rather than assumed?
11. Has the color-code / two-toric-code equivalence been used too strongly?
12. Has projection decoding been conflated with concatenated matching?
13. Is the Meister analogy invoked only after the color-code theorem has been established?

Record every unresolved issue in `REVIEW.md`.

If a claimed theorem fails, weaken or correct it. Do not preserve a desired theorem at the expense of correctness.

---

# TeX deliverables

Write the results in polished, paper-quality mathematical form.

Use the existing TeX structure. Create or update a file such as

```text
tex/logical_topology.tex
```

or another path consistent with `AGENTS.md`.

The TeX output should contain, where justified:

- Definition: stabilizer equivalence for stage-2 chains;
- Lemma: characterization of trivial chain classes;
- Theorem: boundary-to-boundary logical correspondence;
- Corollary / converse: representation of the nontrivial logical class;
- Proposition: \(\widetilde L_c^*\) satisfies the structural requirements of a Meister-type modified decoding graph;
- Remark: exact scope and limitations.

Do not define the cluster-contracted swim distance in this run.

---

# Project files to update

At the end of the task, update:

- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `STATUS.md`
- `REVIEW.md`

Update `AGENTS.md` only when the project-level state, directory structure, current milestone, or next task changes.

The next task should be the cluster-contraction / swim-distance construction.

---

# Completion criteria

This run is complete only when:

1. the relevant stabilizer-equivalence classes of stage-2 chains are mathematically characterized;
2. the boundary-to-boundary logical theorem is proved with all assumptions explicit;
3. the required converse or representative theorem is proved at the strongest justified level;
4. the result is checked against standard triangular color-code logical/string descriptions;
5. \(\widetilde L_c^*\) is rigorously identified as the appropriate Meister-type modified decoding graph for the fixed stage-2 branch;
6. edge-weight compatibility is established;
7. all literature dependencies are verified from primary sources;
8. an independent adversarial review has been completed;
9. all project-state files are synchronized.

Then stop.

Do not begin cluster contraction or the swim-distance definition.
