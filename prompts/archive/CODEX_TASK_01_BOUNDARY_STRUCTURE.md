# Task: Build the mathematical preliminaries and rigorously define the boundary structure of \(L_c^*\)

We are continuing the research project on efficient soft-output decoding for color codes using the concatenated-matching decoder.

Before doing any work, read the current project state carefully:

- `AGENTS.md`
- `STATUS.md`
- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `REVIEW.md`

Treat these files as the current project specification. Preserve the notation and terminology already agreed upon unless there is a clear mathematical inconsistency. If you find such an inconsistency, do not silently change it: document it in `REVIEW.md`, explain the proposed correction, and propagate the correction consistently through the project files.

Also inspect the primary references already collected in the project, especially:

1. Lee, Li, and Bartlett, *Color code decoder with improved scaling for correcting circuit-level noise*.
2. Meister, Pattison, and Preskill, *Efficient soft-output decoders for the surface code*.
3. The relevant literature on color-code boundaries, logical operators, anyons/string operators, and the color-code/surface-code correspondence already listed in `REFERENCES.md`.

Use primary literature whenever it is available. Do not rely on secondary descriptions for mathematical claims that can be checked in the original source.

---

## Overall goal of this task

This task has exactly two goals:

1. Write the mathematical preliminaries of the project in LaTeX at a level suitable for eventual inclusion in a research paper.
2. Complete Research Task 1:

> **Define the boundary structure of the stage-2 \(c\)-only lattice \(L_c^*\) rigorously.**

Do **not** proceed to Research Task 2 yet. In particular, do not yet construct the split-boundary graph \(\widetilde L_c^*\), prove the logical-path theorem, define the swim distance, or analyze the three-color output.

The objective is to establish a mathematically reliable foundation on which those later steps can be built.

---

# Part I: Mathematical preliminaries

Create or update a LaTeX file for the mathematical preliminaries.

Follow the directory structure specified in `AGENTS.md`. If no suitable TeX location currently exists, create:

```text
color_code_softoutput/notes/note.tex
```

The preliminaries should be written in polished academic style, but their primary purpose at this stage is mathematical precision rather than motivation.

## 1. Two-dimensional color code

Define the lattice and code using notation consistent, as far as practical, with Lee–Li–Bartlett.

Include at least:

- the trivalent, three-face-colorable lattice \(L_{2D}\);
- vertex, edge, and face sets;
- color partitions;
- physical qubits on vertices;
- \(X\)- and \(Z\)-type face stabilizers;
- syndrome notation;
- triangular patches with red, green, and blue boundaries;
- the logical Pauli structure relevant to a single encoded qubit.

Clearly distinguish:

- physical lattice vertices;
- faces/checks;
- colored edges;
- Pauli operators;
- error supports;
- syndrome/check excitations.

Do not use informal geometric language where a precise set-theoretic or chain-complex statement is possible.

## 2. String operators and logical operators

Summarize only the amount of color-code topology needed later.

In particular:

- define or explain colored Pauli string operators;
- explain how string endpoints correspond to violated checks / anyonic excitations;
- explain the role of colored boundaries as condensing boundaries;
- state carefully that triangular-color-code logical operators may be represented by appropriate string or string-net representatives and may be deformed by stabilizers.

Do not yet prove the specific stage-2 logical-path statement needed later.

If relative homology is introduced, define it carefully and explain exactly which lattice or chain complex it refers to. Do not import surface-code relative-homology formulas without checking that the same chain complex is actually being used.

## 3. Concatenated-matching decoder

Use the original notation of Lee–Li–Bartlett whenever possible.

For every color \(c\in\{r,g,b\}\), define:

\[
L_{\neg c}^*,
\qquad
L_c^*,
\qquad
\epsilon_{\neg c},
\qquad
\epsilon_c.
\]

Explain precisely:

- what the vertices of \(L_{\neg c}^*\) are;
- what its edges represent;
- what the vertices of \(L_c^*\) are;
- what its edges represent;
- the bijection
  \[
  \epsilon_c:\Delta_0(L_{2D})\to \Delta_1(L_c^*);
  \]
- stage-1 matching;
- how the stage-1 result contributes to the stage-2 syndrome;
- stage-2 matching;
- how the stage-2 edge set is mapped back to a physical color-code correction;
- how the three color branches are combined in the ordinary concatenated decoder.

The distinction between the two graphs is essential:

\[
L_{\neg c}^*
\quad\text{versus}\quad
L_c^*.
\]

Do not loosely call both of them “restricted lattices”.

## 4. Boundary-node convention used by matching

Explain the ordinary matching convention involving the artificial/virtual boundary node \(v_{\mathrm{bdry}}\).

In particular, explain what it means when an edge of \(L_c^*\) is incident to only one ordinary stage-2 vertex and is represented as an edge connecting that vertex to \(v_{\mathrm{bdry}}\).

This discussion should prepare the notation required for Research Task 1 below.

---

# Part II: Research Task 1 — Rigorous boundary structure of \(L_c^*\)

The main research task for this run is:

> **Define the boundary structure of the stage-2 monochromatic lattice \(L_c^*\) rigorously.**

Do not assume the answer from the surface code.

The goal is to determine precisely what geometric or topological information is hidden when all dangling stage-2 edges are attached to the single matching boundary vertex \(v_{\mathrm{bdry}}\).

## Questions that must be resolved

For a triangular color-code patch and a fixed color \(c\):

1. Which physical vertices
   \[
   v\in\Delta_0(L_{2D})
   \]
   map under
   \[
   \epsilon_c(v)
   \]
   to edges incident on \(v_{\mathrm{bdry}}\)?

2. Classify these physical vertices geometrically in the original triangular patch.

3. Determine how these dangling edges are distributed among the physical boundaries and corners of the triangular patch.

4. Determine whether the set of dangling edges naturally decomposes into distinct geometric or topological boundary components.

5. Explain exactly which information is lost when the ordinary matching implementation identifies all of these endpoints with one vertex \(v_{\mathrm{bdry}}\).

6. Determine the role of the corners carefully. Do not assume that a corner belongs unambiguously to only one boundary class unless this follows from the lattice definition.

7. Verify, rather than assume, the current geometric intuition that for a fixed color \(c\), the relevant stage-2 geometry contains two inequivalent terminal regions corresponding roughly to:
   - the appropriate corner/vertex-side termination;
   - the opposite \(c\)-colored boundary.

   If this intuition is inaccurate, refine or replace it.

The final definition must be valid at the combinatorial level, not merely visually obvious from a diagram.

---

## Desired mathematical output

Introduce clean notation for the boundary-related subsets of \(L_c^*\).

For example, if appropriate after analysis, define subsets such as

\[
\partial^{(1)}_c L_c^*,
\qquad
\partial^{(2)}_c L_c^*,
\]

or another notation that better matches the actual structure.

Do **not** force the answer into two components unless the mathematics supports it.

The output should include formal definitions and, where justified, lemmas such as:

- characterization of when \(\epsilon_c(v)\) is a dangling edge;
- classification of dangling edges according to the physical boundary geometry;
- corner classification;
- a decomposition theorem or lemma for the boundary-adjacent edges of \(L_c^*\), if such a decomposition is valid.

Every statement must distinguish clearly among:

1. the physical color-code boundary;
2. boundary-adjacent physical qubits;
3. dangling edges in \(L_c^*\);
4. the artificial matching vertex \(v_{\mathrm{bdry}}\);
5. any topologically distinct classes that will later be separated.

---

# Important restriction

Do **not** yet perform the next research steps.

In particular, this task must stop before:

- constructing the split graph \(\widetilde L_c^*\);
- rewiring \(v_{\mathrm{bdry}}\) into multiple boundary nodes;
- proving that a path between the split boundary components is a nontrivial logical operator;
- defining \(\epsilon_c^{-1}\) on arbitrary stage-2 paths for the purpose of the main logical theorem;
- proving a relative-homology equivalence;
- defining the cluster gap / swim distance \(\phi_c\);
- proving any Meister-type soft-output bound;
- combining the three color instances.

You may state precisely what the next lemma should be, but do not prove it.

---

# Literature verification

While performing this task, check the primary literature for any existing formal characterization of:

- boundaries of triangular color codes;
- colored string termination;
- monochromatic / restricted lattices used in color-code decoders;
- chain-complex descriptions of these lattices;
- mappings between color-code logical operators and surface-code-like objects.

If a useful result already exists, cite it and use it rather than reproving it unnecessarily.

However:

- distinguish the global equivalence between a color code and copies of the surface/toric code from the decoder-specific lattice \(L_c^*\);
- distinguish Delfosse-style projection decoding from the concatenated-matching construction;
- do not treat these mappings as identical unless explicitly proved.

Update `REFERENCES.md` when new relevant primary literature is found.

---

# Independent mathematical review

After completing the derivation, perform a separate critical review of the result.

The review should explicitly ask:

1. Is every boundary class defined from the actual combinatorics of \(L_{2D}\) and \(L_c^*\)?
2. Have any conclusions been inferred merely from figures?
3. Are corners handled correctly?
4. Is the artificial node \(v_{\mathrm{bdry}}\) being confused with a physical/topological boundary?
5. Has any surface-code property been imported without proof?
6. Has the color-code / two-surface-code equivalence been used too strongly?
7. Is every use of \(\epsilon_c\) and \(\epsilon_c^{-1}\) well-defined?
8. Does the statement remain correct for the intended family of triangular color-code lattices, rather than only one 6.6.6 drawing?
9. Are there hidden assumptions about odd distance, lattice family, or perfect-measurement decoding?

Record unresolved issues, possible counterexamples, or missing proofs in `REVIEW.md`.

Do not suppress problems in order to obtain a clean theorem.

---

# Files to update

At the end of this task:

1. Create or update  TeX file.
2. Create a dedicated TeX note for Research Task 1 if useful, e.g.
   ```text
   color_code_softoutput/notes/note.tex
   ```
   unless the project structure suggests a better location.
3. Update `NOTATIONS.md` with all new notation actually adopted.
4. Update `REFERENCES.md` with newly verified sources.
5. Update `PROJECT_DETAIL.md` to record the precise result of Task 1 and the formulation of Task 2.
6. Update `STATUS.md` with:
   - what was completed;
   - what remains unresolved;
   - the next task.
7. Update `AGENTS.md` only where project-level state, directory structure, or the next major task has changed.
8. Update `REVIEW.md` with the independent review findings.

---

# Style and rigor requirements

- Write mathematics first; do not optimize for persuasive prose.
- Use precise definitions before intuitive explanations.
- Reuse established notation from primary references whenever practical.
- Clearly label:
  - Definition
  - Lemma
  - Proposition
  - Remark
  - Open issue
- Do not promote an observation to a lemma unless it has been justified.
- Do not invent citations.
- For every nontrivial imported mathematical fact, identify the source.
- When a statement is inferred rather than explicitly stated in the literature, mark it as our derivation.
- If a claimed statement turns out to be false or ill-posed, revise the project formulation rather than forcing a proof.

---

# Completion criterion

This task is complete only when:

1. the color-code and concatenated-decoder preliminaries are written coherently in LaTeX;
2. the boundary structure of \(L_c^*\) has a precise combinatorial definition;
3. the dangling stage-2 edges and their physical-boundary origin are fully classified, including corners;
4. the role of the single matching boundary node \(v_{\mathrm{bdry}}\) is mathematically clear;
5. the exact statement required for the next task—splitting topologically inequivalent boundary components—can be formulated without relying on a figure;
6. all project tracking Markdown files have been updated consistently.

Then stop.

Do not begin Research Task 2.
