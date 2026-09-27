# Initial Codex research prompt

You are working in a research repository on **efficient soft-output computation for 2D color codes using the concatenated-matching decoder**. Your task in this run is to establish a source-grounded mathematical foundation and refine the project state. Do **not** attempt the main proof yet, do **not** write the paper introduction yet, and do **not** make claims about how the three color branches should be aggregated.

## 1. Read the project state first
Read the following files in full before doing anything else:

- `AGENTS.md`
- `STATUS.md`
- `NOTATIONS.md`
- `REFERENCES.md`
- `PROJECT_DETAIL.md`
- `REVIEW.md`

Treat `AGENTS.md` as the operating contract for this project. If you find an inconsistency among the project files, do not silently choose one version; record the inconsistency and resolve it explicitly in the appropriate files.

## 2. Inspect the primary literature and local source material
Locate and read the relevant local papers if they are available in the repository or project context. At minimum, study the following primary references carefully:

1. Nadine Meister, Christopher A. Pattison, and John Preskill, *Efficient soft-output decoders for the surface code*, arXiv:2405.07433.
2. Seok-Hyung Lee, Andrew Li, and Stephen D. Bartlett, *Color code decoder with improved scaling for correcting circuit-level noise*, Quantum 9, 1609 (2025), arXiv:2404.07482.
3. Markus S. Kesselring, Fernando Pastawski, Jens Eisert, and Benjamin J. Brown, *The boundaries and twist defects of the color code and their applications to topological quantum computation*, Quantum 2, 101 (2018), arXiv:1806.02820.
4. Nicolas Delfosse, *Decoding color codes by projection onto surface codes*, Phys. Rev. A 89, 012317 (2014), arXiv:1308.6207.
5. Aleksander Kubica, Beni Yoshida, and Fernando Pastawski, *Unfolding the color code*, New J. Phys. 17, 083026 (2015), arXiv:1503.02065.

Also inspect any directly relevant later work already listed in `REFERENCES.md`, but do not let broad related-work searching dominate this run.

Use the literature to verify exact definitions, notation, theorem hypotheses, and boundary conventions. Prefer the published paper or author arXiv version over secondary sources. Whenever possible, record exact section/definition/equation/appendix locations for facts that the later proof will reuse.

You may perform targeted literature searches for missing mathematical ingredients, especially:
- homological or chain-complex descriptions of triangular color codes with boundaries;
- logical string/string-net operators and color-boundary termination rules;
- the relation between triangular color-code boundaries and folded/unfolded surface-code descriptions;
- any prior theorem specifically relating the monochromatic/`c`-only graph of a color-code decoder to physical logical operators.

Do not claim novelty based only on an unsuccessful search. If you find no direct prior result, state only the search scope and that no direct result was found in that scope.

## 3. Current research goal
The present project is trying to justify a Meister-style swim distance on the **stage-2 monochromatic graph** `L_c^*` of the concatenated-matching decoder.

For a fixed color `c`, the working geometric idea is:
- ordinary stage-2 matching uses a single virtual boundary node `v_bdry` to connect dangling edges;
- in a triangular patch, those dangling edges appear to contain topologically inequivalent boundary sectors;
- if the merged boundary is split into the correct inequivalent components, a path joining those components may correspond, under `epsilon_c^{-1}`, to a nontrivial physical logical operator;
- if this is proved, the modified graph can potentially play the same role as the modified planar-surface-code decoding graph in Meister et al., after which cluster contraction and a shortest logical path can define a per-color swim distance `phi_c`.

This is a **hypothesis to formalize**, not a result to assume.

## 4. Scope of this run: preliminary theory + research-task formalization only
Perform the following two project tasks now.

### Task A — Build the mathematical preliminaries
Construct a rigorous source-grounded preliminary account sufficient for the later proof. This should include:

1. The 2D triangular color code:
   - cellulation and colorability assumptions;
   - data-qubit and stabilizer placement;
   - three physical color boundaries and corners;
   - encoded logical qubit;
   - physical logical Pauli operators as strings/string-nets, including deformation by stabilizers;
   - the algebraic/topological description needed to discuss when two supports are logically equivalent.

2. The concatenated-matching decoder:
   - define the stage-1 restricted graph `L_{\neg c}^*` and the map `epsilon_{\neg c}`;
   - define the stage-2 monochromatic graph `L_c^*` and the map `epsilon_c`;
   - reproduce the stage-1 and stage-2 decoding equations using the notation of Lee et al.;
   - study Appendix A carefully and reuse its chain spaces, projectors, and boundary maps whenever useful;
   - explain exactly what the ordinary `v_bdry` represents in the graph construction;
   - identify, but do not yet prove, how its incident stage-2 dangling edges are distributed over the physical triangular boundaries/corners.

3. Meister's surface-code construction, only to the extent needed later:
   - modified graph with inequivalent boundary nodes;
   - fully grown MWPM/UF clusters;
   - quotient / zero-internal-weight construction;
   - shortest path representing a logical operator;
   - exact hypotheses and limitations of the analytical claims.

This preliminary account should be mathematically explicit enough that the subsequent proof work can proceed without repeatedly returning to basic definitions.

### Task B — Refine the research object and proof program
Using Task A, sharpen the six-step target already described in `PROJECT_DETAIL.md`:

1. Define the boundary structure of `L_c^*` rigorously.
2. Split the ordinary merged stage-2 boundary into topologically inequivalent components.
3. Extend / define `epsilon_c^{-1}` as the map from stage-2 edge chains to physical Pauli support.
4. Formulate the exact theorem that appropriate paths between inequivalent boundary components are nontrivial logical operators, and characterize the relevant trivial path differences/cycles modulo stabilizers using relative homology or another exact quotient.
5. State the precise conditions under which `\widetilde L_c^*` can be treated as the modified logical decoding graph needed by Meister's construction.
6. State the resulting definition of per-color cluster contraction and swim distance `phi_c`.

For this run, **formulate these objects and proof obligations but stop before proving the central theorem**. If a small auxiliary fact is already explicitly proved in the literature, cite it rather than reproving it.

## 5. Required file updates
After the source audit and preliminary formulation, update all six root project files.

### `NOTATIONS.md`
- Align notation with Lee et al. and the relevant color-code topology literature.
- Remove or mark any symbol that was guessed incorrectly.
- Clearly distinguish source notation from project-specific notation.
- Define the candidate relative-homology/quotient objects only as far as justified.

### `REFERENCES.md`
- Verify bibliographic metadata.
- Add primary references that are mathematically necessary.
- For each core reference, state exactly what result/definition it supports.
- Record section/definition/equation/appendix pointers for the key reused results.

### `PROJECT_DETAIL.md`
- Expand the preliminary formulation.
- Refine the research questions.
- Replace vague geometric language with candidate formal statements.
- Give a dependency graph for definitions, lemmas, and the central theorem.
- Explicitly list assumptions that still need proof or verification.
- Keep three-color aggregation and later performance questions out of the active milestone.

### `REVIEW.md`
Perform an independent adversarial review of the refined setup. In particular, test for:
- incorrect identification of color-code and surface-code homology;
- conflation of Delfosse projection with Lee's concatenated decoder;
- unjustified claims that graph cycles are stabilizers;
- hidden corner/boundary exceptions;
- misuse of `epsilon_c^{-1}` beyond its proved domain;
- importing Meister's theorem without checking its hypotheses;
- accidental claims about the full three-color decoder.

Add every unresolved issue with a severity/status label and a concrete required action.

### `STATUS.md`
Record:
- sources actually checked;
- mathematical setup now established;
- unresolved blocking questions;
- exact next task for the later theory-construction run.

### `AGENTS.md`
Update only if the source audit changes the project scope, workflow, or non-negotiable rules. Update `Last update` and `Next task`.

## 6. Research standards
- Do not fill gaps from intuition while presenting them as established facts.
- Prefer precise algebraic statements over pictures, but use geometry to guide definitions.
- If two papers use incompatible chain-complex conventions, state the translation explicitly.
- Separate physical Pauli support, graph edge chains, syndrome chains, stabilizer equivalence, and logical equivalence.
- For every imported theorem, check the hypotheses one by one.
- Preserve the distinction between an exact logical/comparative gap and a cluster-gap/swim-distance proxy.
- Do not analyze the final three-color output in this run.
- Do not begin numerical experiments in this run.
- Do not create `paper/main.tex` yet.
- Do not write the broad motivation/related-work section yet; that is intentionally deferred until the central theory is stable.

## 7. Final response for this run
At the end, give a concise research handoff containing:
1. files changed;
2. primary sources actually inspected;
3. the refined central theorem statement or theorem skeleton (not a proof);
4. unresolved blocking issues;
5. the single best next task for the following Codex run.

The repository files, not the chat response, are the authoritative output of this run.
