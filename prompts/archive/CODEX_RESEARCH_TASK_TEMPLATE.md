# Research Task [TASK_ID]: [TASK_TITLE]

We are continuing the research project described in the project directory.

Before doing any work, read:

- `AGENTS.md`
- `STATUS.md`
- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `REVIEW.md`

Treat these files as the current project specification.

Preserve the established notation and definitions unless they are mathematically inconsistent. If an inconsistency is found, do not silently modify it. Record the issue in `REVIEW.md`, explain the correction, and propagate the correction consistently through the project files.

---

# Objective

The sole main objective of this run is:

> **[PRECISE MATHEMATICAL OBJECTIVE]**

This task should establish the mathematical result needed for the next research step.

Do not solve subsequent research tasks unless explicitly required to establish the present result.

---

# Input from previous tasks

The following results should already be available:

- [PREVIOUS RESULT 1]
- [PREVIOUS RESULT 2]
- [PREVIOUS RESULT 3]

Verify that these results are actually established in the project files before using them.

If a required previous result is missing, ambiguous, or only conjectural, stop the downstream argument and resolve or explicitly flag that dependency first.

---

# Primary questions

Resolve the following questions:

1. [QUESTION 1]
2. [QUESTION 2]
3. [QUESTION 3]
4. [QUESTION 4]

Distinguish clearly among:

- assumptions;
- definitions;
- previously established results;
- results derived in this task;
- conjectures/open questions.

---

# Mathematical target

Aim to formulate and, where appropriate, prove statements of the form:

## Definition
[DEFINITION TO ESTABLISH]

## Lemma
[LEMMA TO ESTABLISH]

## Proposition / Theorem
[THEOREM TO ESTABLISH]

Do not force these statements to be true. If the proposed formulation is incorrect, identify the problem and replace it with the strongest statement actually supported by the mathematics.

---

# Literature verification

Search the relevant primary literature for results concerning:

- [TOPIC A]
- [TOPIC B]
- [TOPIC C]

Prefer original papers over reviews or secondary summaries.

For every relevant result:

1. determine exactly what is proved in the source;
2. determine whether it applies directly to our setting;
3. distinguish direct application from analogy;
4. cite the source appropriately.

Do not conflate related but mathematically different constructions.

In particular, check explicitly for possible differences in:

- code geometry;
- boundary conditions;
- noise model;
- decoding graph/hypergraph;
- chain complex;
- number of encoded logical qubits;
- decoder assumptions.

Update `REFERENCES.md` when new primary references are found.

---

# Derivation protocol

Proceed in the following order:

1. Restate the exact object to be analyzed using the notation in `NOTATIONS.md`.
2. List all assumptions required for the argument.
3. Derive the result from definitions and previously established lemmas.
4. Separate geometric intuition from the formal proof.
5. Check boundary, corner, and degenerate cases explicitly.
6. Check whether the result depends on a specific lattice family or holds generally.
7. Identify any hidden dependence on implementation conventions.
8. Only after the derivation is complete, rewrite it in polished mathematical form.

Do not begin with the desired theorem and reverse-engineer a proof.

---

# Independent review

After completing the derivation, perform a separate critical review.

Try to falsify the result.

Check:

1. Are all maps and domains/codomains well-defined?
2. Are all equivalence relations stated explicitly?
3. Are boundaries and corners treated correctly?
4. Has a statement valid for the surface code been imported without proof?
5. Has a decoder-specific construction been confused with a code-level/topological statement?
6. Is any argument based only on a figure or intuition?
7. Does the result depend on unstated assumptions?
8. Are there counterexamples at small code distance?
9. Is the theorem stronger than what the proof actually establishes?
10. Are literature claims accurately represented?

Record all issues in `REVIEW.md`.

If the review invalidates part of the derivation, revise the result before considering the task complete.

---

# Deliverables

Create or update:

- `[MAIN_TEX_FILE]`
- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `STATUS.md`
- `REVIEW.md`

Update `AGENTS.md` only when the project-level overview, directory structure, current milestone, or next task changes.

The TeX file should contain polished, paper-quality mathematical writing, while the Markdown files should preserve research-state information and unresolved issues.

---

# Out-of-scope work

Do **not** perform the following tasks in this run:

- [NEXT TASK 1]
- [NEXT TASK 2]
- [NEXT TASK 3]

You may formulate the exact statement required for the next task, but do not prove or analyze it.

---

# Completion criteria

The task is complete only when:

1. [CRITERION 1]
2. [CRITERION 2]
3. [CRITERION 3]
4. all new notation has been synchronized with `NOTATIONS.md`;
5. all new literature has been synchronized with `REFERENCES.md`;
6. unresolved mathematical issues have been recorded in `REVIEW.md`;
7. `STATUS.md` clearly identifies the next research task.

Then stop.

Do not continue to the next research task.
