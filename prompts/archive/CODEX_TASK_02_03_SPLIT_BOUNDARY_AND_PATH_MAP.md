# Research Tasks 2 and 3: Split the stage-2 boundary structure and define the path-to-physical-operator map

We are continuing the research project on efficient soft-output decoding for color codes using the concatenated-matching decoder.

Before doing any work, read the current project state carefully:

- `AGENTS.md`
- `STATUS.md`
- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `REVIEW.md`

Also read all TeX files produced so far, especially the mathematical preliminaries and the output of Research Task 1, including the rigorous boundary classification of the stage-2 monochromatic lattice \(L_c^*\).

Treat the current project files as the authoritative project state.

Do not assume that Research Task 1 is correct merely because it was completed. First verify that its definitions and lemmas are internally consistent and sufficient for the present tasks. If a problem is found, record it in `REVIEW.md` and repair the dependency before proceeding.

---

# Objective

This run has exactly two mathematical objectives:

## Research Task 2

> **Construct a boundary-resolved version of the stage-2 monochromatic graph \(L_c^*\) by separating the topologically inequivalent boundary components that are merged into the ordinary matching boundary vertex \(v_{\mathrm{bdry}}\).**

## Research Task 3

> **Define rigorously how an edge set or path in the boundary-resolved stage-2 graph maps, through \(\epsilon_c^{-1}\), to a physical Pauli operator on the original color-code patch.**

The purpose of this run is to establish the precise mathematical objects required for the next major theorem.

Do **not** prove yet that a path connecting the inequivalent boundary components is a nontrivial logical operator. That is Research Task 4 and is explicitly out of scope.

Do **not** define the swim distance yet.

---

# Required input from Research Task 1

Research Task 1 should already have established, for each color \(c\in\{r,g,b\}\):

1. the combinatorial boundary structure of \(L_c^*\);
2. the characterization of physical vertices \(v\in\Delta_0(L_{2D})\) for which \(\epsilon_c(v)\) is incident on \(v_{\mathrm{bdry}}\);
3. the classification of these dangling edges according to the physical boundaries and corners of the triangular color-code patch;
4. the topologically distinct classes that are hidden by the single matching boundary vertex.

Before beginning Task 2, restate these results precisely and identify which statements are proved and which remain assumptions.

If the previous task did not actually justify a decomposition into the required boundary classes, stop and repair Task 1 instead of forcing the construction below.

---

# Part I: Research Task 2 — Boundary-resolved stage-2 graph

## 1. Define the new graph

Using the boundary classification established in Research Task 1, define a new graph, tentatively denoted

\[
\widetilde L_c^*,
\]

obtained from the ordinary stage-2 graph \(L_c^*\) by replacing the single artificial matching boundary vertex \(v_{\mathrm{bdry}}\) with the distinct boundary objects required to preserve the relevant topological information.

The notation may be changed if a different notation is mathematically cleaner, but synchronize any adopted notation with `NOTATIONS.md`.

The definition must explicitly specify:

- the vertex set \(\Delta_0(\widetilde L_c^*)\);
- the edge set \(\Delta_1(\widetilde L_c^*)\);
- which ordinary interior vertices and edges are unchanged from \(L_c^*\);
- how every edge formerly incident on \(v_{\mathrm{bdry}}\) is reassigned;
- how corner-associated dangling edges are treated;
- whether the new boundary objects are vertices, sets of vertices, or another combinatorial object.

Do not describe the construction only pictorially.

---

## 2. Define the relation between \(L_c^*\) and \(\widetilde L_c^*\)

Introduce an explicit map that forgets the boundary distinction and recovers the ordinary matching graph. For example, if appropriate, define a quotient / contraction map

\[
q_c:\widetilde L_c^*\to L_c^*
\]

that identifies all boundary-resolved nodes back to \(v_{\mathrm{bdry}}\) and is otherwise the identity.

State precisely what \(q_c\) does on vertices and edges.

If the correct mathematical structure is not literally a graph quotient, use a more appropriate map and explain why.

The key requirement is that the relation between the ordinary decoder graph and the boundary-resolved graph is mathematically explicit.

---

## 3. Check compatibility with ordinary stage-2 decoding

Determine what is and is not preserved when passing from \(\widetilde L_c^*\) to \(L_c^*\).

At minimum, analyze:

- the correspondence between physical data-qubit errors and stage-2 edges;
- edge weights;
- the stage-2 syndrome constraints;
- the role of the ordinary boundary vertex in MWPM;
- whether the boundary-resolved graph is intended to be used directly for ordinary MWPM, or only as a post-decoding/topological analysis graph.

Do not assume that simply splitting \(v_{\mathrm{bdry}}\) leaves the matching optimization unchanged.

If ordinary MWPM fundamentally relies on the merged boundary node, say so explicitly.

The intended construction may be:

\[
\text{ordinary decoding on } L_c^*
\quad\longrightarrow\quad
\text{topological/soft-output analysis on } \widetilde L_c^*,
\]

rather than replacing the decoder itself.

Establish this point carefully.

---

## 4. Formal boundary classes

Give names to the inequivalent boundary components of \(\widetilde L_c^*\).

If Research Task 1 confirms that there are exactly two relevant classes for fixed \(c\), define them explicitly, for example

\[
B_c^{(0)},\qquad B_c^{(1)}.
\]

However, do not force this notation or the number two if the Task-1 mathematics implies a different structure.

State exactly which dangling edges terminate on which boundary class.

The classification should be combinatorial and independent of a particular drawing.

---

# Part II: Research Task 3 — Mapping stage-2 edge sets to physical Pauli operators

The original concatenated-matching construction provides a bijection

\[
\epsilon_c:\Delta_0(L_{2D})\to \Delta_1(L_c^*).
\]

Research Task 3 should extend this notation carefully to edge subsets or paths.

---

## 5. Define \(\epsilon_c^{-1}\) on edge subsets

For an edge subset

\[
\Gamma\subseteq \Delta_1(\widetilde L_c^*),
\]

define the corresponding physical support

\[
V_\Gamma
:=
\epsilon_c^{-1}(\Gamma)
\subseteq
\Delta_0(L_{2D}),
\]

with whatever adjustment is required because \(\widetilde L_c^*\) is boundary-resolved rather than the original \(L_c^*\).

Be precise about whether \(\epsilon_c\) itself is redefined as a bijection

\[
\widetilde\epsilon_c:
\Delta_0(L_{2D})
\to
\Delta_1(\widetilde L_c^*)
\]

or whether one uses the ordinary \(\epsilon_c\) together with the forgetful map \(q_c\).

Choose one mathematically clean convention and use it consistently.

---

## 6. Define the associated physical Pauli operator

Fix one CSS decoding sector first.

For example, when analyzing \(X\)-type data errors, define the physical Pauli associated with \(\Gamma\) as

\[
P_X(\Gamma)
=
\prod_{v\in V_\Gamma} X_v,
\]

or the corresponding \(Z\)-type expression for the other CSS sector.

State explicitly:

- which physical Pauli sector is being considered;
- how the support is obtained;
- how symmetric difference of edge sets corresponds to multiplication of Pauli supports modulo phase;
- which statements rely on CSS separation.

If a basis-independent notation is preferable, define it carefully.

---

## 7. Establish the syndrome relation

Prove the precise relation between the boundary of an edge set in the stage-2 graph and the syndrome of its corresponding physical Pauli operator.

This is a key deliverable of Task 3.

Formulate the strongest correct statement of the form

\[
\partial^{\widetilde L_c^*}\Gamma
\quad\leftrightarrow\quad
\text{syndrome data of } P(\Gamma),
\]

while carefully accounting for:

- ordinary stage-2 vertices;
- the virtual syndrome originating from stage 1;
- physical \(c\)-colored checks;
- boundary-resolved terminal nodes;
- the fact that artificial boundary nodes are not physical checks.

Do not claim that boundary nodes are syndrome checks.

If the relation only holds after projecting away the artificial boundary vertices, define the required projection explicitly.

This should be written as a lemma if it can be proved rigorously.

---

## 8. Paths versus general edge sets

Clarify the distinction among:

- a single path in \(\widetilde L_c^*\);
- a collection of paths;
- cycles;
- arbitrary \(\mathbb F_2\) 1-chains / edge subsets.

Use chain notation if it makes the algebra clearer.

In particular, determine whether the map to a physical Pauli operator should fundamentally be defined on

\[
C_1(\widetilde L_c^*;\mathbb F_2)
\]

rather than only on simple paths.

This is important because the next research task will compare path topology with stabilizer/logical equivalence.

If chain notation is adopted, define the chain groups and boundary map explicitly.

---

# Part III: Algebraic properties needed later

Without proving the main logical-path theorem, establish the algebraic properties of the mapping that will be needed for it.

At minimum, determine whether the following are true and prove them if justified:

## Linearity under symmetric difference

For edge sets / chains \(\Gamma_1,\Gamma_2\),

\[
P(\Gamma_1\oplus\Gamma_2)
\sim
P(\Gamma_1)P(\Gamma_2),
\]

up to irrelevant Pauli phase.

## Boundary compatibility

The syndrome map of \(P(\Gamma)\) is determined by the graph boundary of \(\Gamma\), after the appropriate projection removing artificial boundary nodes.

## Interior-cycle property

Characterize what is known at this stage about

\[
\partial\Gamma=0.
\]

Do **not** yet claim that every such cycle maps to a stabilizer unless that statement has actually been proved from the color-code structure.

This point should be left explicitly open if it belongs to Research Task 4.

---

# Part IV: Connection to the next theorem

At the end of this task, formulate—but do not prove—the exact statement to be addressed in Research Task 4.

It should have the general form:

> A suitable chain/path in \(\widetilde L_c^*\) connecting two topologically inequivalent boundary components maps to a physical Pauli operator representing the nontrivial logical class, whereas the appropriate trivial path differences / cycles map to stabilizer-equivalent operators.

Do not assume this formulation is correct until Tasks 2 and 3 have made every object precise.

Write the final Task-4 statement using the exact notation established in this run.

---

# Literature verification

Check the primary literature for mathematical results relevant to:

- monochromatic / restricted lattices of color-code decoders;
- the bijection \(\epsilon_c\);
- chain-complex descriptions of the concatenated-matching decoder;
- color-code string operators and stabilizer deformations;
- relative homology or equivalent formulations of color-code logical operators;
- mappings from color codes to surface/toric-code structures.

Use the original sources wherever possible.

In particular:

- distinguish Lee–Li–Bartlett's \(L_c^*\) construction from Delfosse projection decoding;
- distinguish decoder-specific graph maps from the global local-Clifford equivalence between the color code and two copies of the toric/surface code;
- do not use a surface-code path theorem as if it automatically applied to \(\widetilde L_c^*\).

If a published chain-map or homological result can directly justify part of Task 3, cite it precisely.

Update `REFERENCES.md` with any newly verified primary references.

---

# Independent mathematical review

After deriving Tasks 2 and 3, conduct a separate adversarial review.

Explicitly check:

1. Is \(\widetilde L_c^*\) defined without relying on a figure?
2. Is every original stage-2 edge represented exactly once?
3. Are the boundary-resolved classes disjoint and exhaustive where they should be?
4. Are corners handled consistently?
5. Is the forgetful / quotient map back to \(L_c^*\) well-defined?
6. Is the edge-to-physical-qubit bijection preserved?
7. Is \(\epsilon_c^{-1}\) being applied only where it is mathematically defined?
8. Are artificial boundary nodes incorrectly being treated as physical syndrome checks?
9. Is the graph-boundary / physical-syndrome relation exact?
10. Does any statement silently assume the result of Research Task 4?
11. Does the construction depend on a specific 6.6.6 drawing, or does it apply to the intended triangular color-code family?
12. Are there small-distance counterexamples or corner degeneracies?
13. Has any global color-code/surface-code equivalence been used more strongly than justified?

Record all unresolved issues in `REVIEW.md`.

If the review invalidates a definition or lemma, repair the result before declaring the task complete.

---

# TeX deliverables

Write the results in polished mathematical form.

Use the existing TeX structure from the previous task. Depending on the current project layout, either:

- extend `tex/boundary_structure.tex`, or
- create a new file such as
  ```text
  tex/split_boundary_and_path_map.tex
  ```

The TeX output should contain, where justified:

- Definition: boundary-resolved stage-2 graph;
- Definition: boundary components;
- Definition: forgetful / quotient map;
- Definition: edge-chain to physical-support map;
- Definition: associated physical Pauli operator;
- Lemma: linearity under symmetric difference;
- Lemma: graph-boundary / syndrome compatibility;
- Remark/Open issue: statements deferred to Research Task 4.

Do not write the swim-distance definition yet.

---

# Project files to update

At the end of the task, update:

- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `STATUS.md`
- `REVIEW.md`

Update `AGENTS.md` only if the directory structure, project-level milestone, or next task changes.

`STATUS.md` should make clear that:

- Research Task 2 is complete or partially complete;
- Research Task 3 is complete or partially complete;
- all unresolved assumptions are listed;
- the next task is Research Task 4: proving the logical-topology correspondence.

---

# Out of scope

Do **not** perform any of the following in this run:

- prove that a boundary-to-boundary path is a nontrivial logical operator;
- prove that all relevant closed cycles are stabilizers;
- identify \(\widetilde L_c^*\) with Meister's modified surface-code decoding graph;
- define cluster contraction;
- define the swim distance \(\phi_c\);
- prove a Meister-type lower bound;
- analyze the three color branches jointly;
- analyze the final soft-output aggregation rule;
- study numerical performance.

These belong to later tasks.

---

# Completion criteria

This task is complete only when:

1. the boundary-resolved graph \(\widetilde L_c^*\) is rigorously defined;
2. its relation to the ordinary stage-2 graph \(L_c^*\) is explicit;
3. every stage-2 edge has a precise physical data-qubit interpretation;
4. the extension of \(\epsilon_c^{-1}\) from individual edges to edge chains/subsets is mathematically precise;
5. the corresponding physical Pauli operator is defined;
6. the graph-boundary / physical-syndrome relation is proved at the appropriate level of generality;
7. corners and artificial boundary nodes are handled explicitly;
8. the exact statement required for Research Task 4 is formulated, but not proved;
9. all project state files are updated consistently;
10. an independent review has been completed and all unresolved issues are recorded.

Then stop.

Do not begin Research Task 4.
