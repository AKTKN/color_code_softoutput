# Codex Task: Circuit-Level Swim-Distance Algorithm Note and Implementation

We have completed the perfect-measurement/code-capacity Phase-1 theory, the Phase-2A code-capacity implementation, and a circuit-level theoretical extension.

The next task is to convert the circuit-level theory into:

1. a concise, implementation-facing TeX algorithm note;
2. a modular circuit-level swim-distance implementation;
3. component-level correctness tests;
4. a small end-to-end `d`-round memory experiment under the uniform circuit-level noise model;
5. a thin notebook workflow analogous to the existing code-capacity workflow;
6. updated project state documents.

This task is restricted to **fully terminated memory experiments with a closed temporal boundary**.

Do **not** implement sliding-window/open-future-boundary decoding in this task.

---

# 0. Workspace and repository layout

Main project:

```text
/home/quantum_teresheys/workspace/color_code_softoutput
```

Main reusable package:

```text
/home/quantum_teresheys/workspace/color_code_softoutput/src/color_code_softoutput
```

External packages:

```text
/home/quantum_teresheys/workspace/color_code_softoutput/external_libs
```

At minimum this contains the project-specific PyMatching fork and `color-code-stim`.

Do not copy external package source into the main package.

Before modifying anything, inspect the actual repositories, branches, HEAD SHAs, remotes, dirty state, installed editable packages, and current tests.

The previously reported Phase-2A implementation commits were:

```text
PyMatching:
83cee05cc16d6fce9deafdbbf7952b4b96a7f21e

color-code-stim:
ba6f7dc8b7aaab237d98ad5f08825be4225864c6
```

These are historical references only. Verify the actual current HEADs.

If new external-library work is required, create a dedicated development branch such as:

```text
phase2b/circuit-level-swim
```

Do not rewrite upstream history.

---

# 1. Read the complete project state first

Before coding, read at minimum:

```text
AGENTS.md
STATUS.md
PROJECT_DETAIL.md
IMPLEMENTATION_STATUS.md
REVIEW.md
NOTATIONS.md
REFERENCES.md
```

Read the complete current theory note and especially:

```text
notes/support/circuit_level_theory.tex
```

or the actual equivalent path in the project.

Also inspect:

- the Phase-2A PyMatching soft-output implementation;
- the Phase-2A color-code topology adapter;
- the current code-capacity simulation package;
- the current code-capacity Getting Started notebook;
- the reusable analysis package and `figure_style.py`;
- `color-code-stim`'s DEM manager/decomposition and concatenated decoder;
- current circuit-level tests/fixtures.

Do not re-derive behavior from memory when the repository already contains an implementation or test that defines it.

---

# 2. Authoritative circuit-level theory for this implementation

The implementation must follow the current circuit-level theory note.

The central objects are the retained stage-2 `c`-only DEM maps:

\[
D \equiv D_c^{\rm circ},
\qquad
L_2 \equiv L_c^{\rm circ}.
\]

For a fixed stage-1 fiber and fixed real stage-2 syndrome, an opposite-logical difference satisfies

\[
Dz=0,
\qquad
L_2z=1.
\]

The fundamental circuit-level swim distance is

\[
\boxed{
\phi_c^{\rm circ}
=
\min_{Dz=0,\;L_2z=1}
\sum_e \bar\omega_c(e)z_e
}
\]

where `bar omega_c(e)` is the residual uncovered interval length after transporting the decoder cluster coverage from the **original labelled stage-2 graph**.

This definition is authoritative.

Do not redefine circuit-level swim distance from detector coordinates, Euclidean geometry, or a hand-drawn spacetime surface.

Detector color/time/location metadata may be used for:

- typing;
- validation;
- diagnostics;
- visualization;
- provenance;

but the exact logical class is determined by `(D, L_2)`.

---

# 3. Important theorem-level implementation rules

The current theory establishes the following implementation rules.

## 3.1 Fixed-fiber class existence

For one observable, the opposite logical class exists iff:

\[
L_2 \notin \operatorname{rowspan}D,
\]

equivalently:

\[
\operatorname{rank}
\begin{pmatrix}
D\\L_2
\end{pmatrix}
=
\operatorname{rank}D+1.
\]

If the opposite class does not exist for the retained model, return an explicit:

```text
no_opposite_class
phi = +inf
witness = None
```

Do not fabricate a two-boundary graph.

## 3.2 General exact algorithm: logical binary cover

Complete one-detector stage-2 mechanisms at one artificial matching vertex `b_star`.

Represent zero-detector logical mechanisms as labelled loops at `b_star`.

For every base graph vertex `v`, create:

```text
(v, 0)
(v, 1)
```

For an edge `e=(u,v)` with logical label:

```text
lambda_e = L_2[e]
```

create:

\[
(u,a)\leftrightarrow(v,a+\lambda_e).
\]

Every lifted copy inherits the same residual weight and source edge ID.

Then:

\[
\phi_c^{\rm circ}
=
\min_v
\operatorname{dist}
\bigl((v,0),(v,1)\bigr).
\]

The projected modulo-two witness must satisfy:

\[
Dz=0,\qquad L_2z=1.
\]

This logical-cover implementation is the **general exact fallback** for the closed-memory retained graph.

Do not replace the `min_v` by arbitrary zero-sheet-to-one-sheet multisource distance. The two endpoints must project to the same base vertex.

## 3.3 Fast special case: two-boundary cut

The internal real-real graph is eligible for the two-boundary algorithm iff all internal cycles have logical parity zero.

Equivalently there exists a binary potential `g(v)` satisfying:

\[
\lambda_{uv}=g(u)+g(v)
\]

for every internal real-real edge.

Check this offline using a spanning forest / BFS / DFS.

This check is `O(V+E)` and depends only on the fixed labelled decoding graph, not on the shot syndrome.

If it passes:

1. gauge transform logical labels by the detector-row coboundary;
2. internal edge labels become zero;
3. split `b_star` into:
   ```text
   b0
   b1
   ```
4. attach every half-edge to `b0` or `b1` according to its gauged logical label;
5. map an odd zero-detector loop to an edge `b0--b1`;
6. keep an even zero-detector loop logically trivial;
7. compute:
   \[
   \phi_c^{\rm circ}
   =
   \operatorname{dist}(b0,b1).
   \]

This is the preferred practical algorithm when the balance condition passes.

If the condition fails, automatically fall back to the logical binary cover.

Do not assume closed temporal boundary alone implies the balance condition.

## 3.4 Cluster coverage is computed on the original graph

The decoder growth/coverage belongs to the original labelled stage-2 graph.

Compute residual edge lengths there first.

Only afterward transport the residual edge weights to the cut/cover analysis graph.

Do **not** rerun matching growth on the cut graph or logical cover.

Do not erase logical labels from fully covered edges: an odd logical cycle may have zero residual cost.

## 3.5 Hard decoder remains unchanged

The circuit-level soft-output implementation must be read-only with respect to the existing hard decoder.

It may inspect:

- matrices;
- weights;
- detector metadata;
- stage-1 prediction;
- stage-2 input;
- stage-2 correction;
- observable map;
- exported growth data.

It must not alter:

- the physical sampling circuit;
- H1/H2 used by the current hard path;
- hard edge merge/tie policy;
- stage-1 prediction;
- stage-2 prediction;
- selected color;
- hard correction weight.

---

# 4. Phase A — First write the implementation-facing TeX algorithm note

Before changing production code, create or refine a concise TeX note describing the concrete algorithm.

If the current `circuit_level_theory.tex` already contains a section titled similar to:

```text
Executable DEM-to-decoder construction specification
```

do not duplicate it unnecessarily.

Instead create a compact implementation-facing algorithm section/file, for example:

```text
notes/support/circuit_level_swim_algorithm.tex
```

and include it from the appropriate master note, or refactor the existing algorithm section if that is cleaner.

The note should be substantially shorter than the full proof.

It must contain:

## Inputs

For each color `c`:

```text
retained c-only stage-2 check matrix D/H2
stage-2 edge/mechanism probabilities or weights
stage-2 logical observable labels L2
physical detector metadata
virtual detector metadata
stable stage-2 column IDs
source DEM/provenance IDs
stage-1 prediction
stage-2 syndrome
stage-2 hard correction
MWPM growth/radius information
```

## Offline graph preprocessing

For each fixed:

```text
d
rounds
circuit
schedule
noise-model structure
color
```

perform:

1. build the labelled base graph;
2. classify constrained physical/virtual rows;
3. preserve time/color/location/source metadata;
4. complete half-edges at `b_star`;
5. retain zero-detector logical loops;
6. test class existence;
7. run the internal balance test;
8. if balanced, prebuild/cache the two-boundary cut topology;
9. otherwise prebuild/cache the logical-cover topology.

Explain explicitly that the balance test is graph-structural and need not be repeated shot-by-shot.

## Per-shot computation

For each shot:

1. run unchanged stage 1;
2. build unchanged stage-2 syndrome;
3. run unchanged stage 2;
4. obtain current growth radii/coverage data;
5. compute residual edge lengths on the original labelled graph;
6. transport residuals to the prebuilt cut or cover;
7. run shortest-path computation;
8. recover and verify the logical witness if requested;
9. return:
   ```text
   phi_c
   witness
   method = two_boundary | logical_cover
   class_exists
   balance_passed
   certification_flag
   ```
10. leave the hard result unchanged.

## Selected-color output

The full concatenated decoder still selects one of `r,g,b` using its existing hard decision rule.

For the initial circuit-level numerical workflow define:

```text
selected_swim_distance
=
phi of the color branch selected by the unchanged ordinary hard decoder
```

Do not replace this by:

```text
min(phi_r, phi_g, phi_b)
```

in this implementation task.

That aggregation study is a later research task.

## Complexity

State separately:

- offline balance/preprocessing cost;
- per-shot residual computation;
- two-boundary shortest-path cost;
- logical-cover fallback cost;
- growth extraction cost, which is not part of the Dijkstra bound.

Do not claim the current growth export is a certified optimal odd-cut dual.

---

# 5. Phase A review gate

Before implementation, perform a short self-review of the TeX algorithm.

Verify:

1. it agrees with the current theorem labels/statements;
2. it does not infer logical topology from coordinates alone;
3. it distinguishes hard-decoder graph from analysis graph;
4. it handles half-edges and zero-detector logical mechanisms;
5. it uses the balance test before two-boundary reduction;
6. it provides logical-cover fallback;
7. it preserves covered odd logical cycles;
8. it excludes open temporal boundaries/sliding windows.

If any point is unresolved, update the algorithm note before coding.

---

# 6. Implementation architecture

The new circuit-level swim-specific processing should be modular and live primarily in:

```text
src/color_code_softoutput
```

A recommended structure is:

```text
src/color_code_softoutput/
├── circuit_level/
│   ├── __init__.py
│   ├── model.py
│   ├── dem_adapter.py
│   ├── graph.py
│   ├── logical_topology.py
│   ├── coverage.py
│   ├── swim.py
│   ├── witness.py
│   └── validation.py
├── experiments/
│   └── circuit_level_memory_test.py
└── ...
```

This exact structure is not mandatory, but preserve separation of concerns.

## Suggested responsibilities

### `model.py`

Typed immutable dataclasses/enums for:

```text
Stage2Mechanism
DetectorMeta
LogicalLabel
BoundaryRole
CircuitLevelGraph
CircuitLevelTopology
CircuitLevelSwimResult
Witness
```

### `dem_adapter.py`

Adapter from current `color-code-stim` structures:

```text
DemManager
DemDecomp
H1/H2
probability arrays
observable matrix
error maps
detector coordinates
detector color/type/time metadata
```

into the main project's stable typed analysis model.

Do not make this module reimplement Lee decomposition if the existing hard path already materializes the authoritative matrices.

Prefer consuming the frozen actual matrices used by the hard decoder.

### `graph.py`

Construct the labelled base multigraph:

- constrained physical detector vertices;
- constrained virtual detector vertices;
- artificial `b_star`;
- two-real-endpoint edges;
- one-detector half-edges completed at `b_star`;
- zero-detector loops;
- parallel mechanisms retained by stable source/column ID.

### `logical_topology.py`

Implement:

```text
class-existence/rank test
internal balance test
binary potential construction
label gauge transform
two-boundary cut topology
logical binary cover topology
```

This module should be independent of a particular shot.

### `coverage.py`

Consume Phase-2A PyMatching growth/radius data and compute residual edge lengths on the original labelled stage-2 graph.

Preserve existing units/normalization.

Do not interpret missing growth as zero.

### `swim.py`

High-level per-color API:

```python
compute_circuit_level_swim(...)
```

or a class-based equivalent.

It should:

1. receive a preprocessed topology;
2. receive per-shot residual edge weights;
3. choose prevalidated two-boundary or cover method;
4. compute `phi`;
5. optionally return a witness;
6. independently verify witness parity/cost.

### `validation.py`

Central reusable checks:

```text
D f == s
witness D z == 0
witness L z == 1
witness cost == phi
hard-output invariance
edge/provenance consistency
balance/cut/cover equivalence
```

---

# 7. Use detector metadata, but do not make it the theorem

The user expects detector color, time, and location metadata to help build the decoding graph.

Use these fields extensively for:

- mapping `H2` rows back to physical detectors;
- distinguishing physical and virtual rows;
- debugging stage-1/stage-2 source provenance;
- plotting/inspection;
- temporal-boundary audits;
- stable graph diagnostics;
- validating that the generated graph corresponds to the expected closed-memory geometry.

However:

> logical class must be derived from `L2`, not guessed from color/time/location.

Coordinates alone are insufficient to determine logical action.

The theory note explicitly distinguishes spatial boundary, temporal boundary, artificial MWPM boundary, correlation-surface boundary, and analysis cut.

Preserve that distinction in code.

---

# 8. External `color-code-stim` changes

Prefer adding a non-invasive adapter in the main package first.

Modify `color-code-stim` only if the required data are not externally accessible without fragile private-state dependence.

If changes are necessary, expose stable read-only metadata rather than embedding swim-distance logic directly into the hard decoder.

Potential additions may include public/read-only access to:

```text
stage-2 H2 column IDs
stage-2 probabilities/weights
stage-2 observable labels
physical detector IDs
virtual detector source IDs
detector color/type/time/coordinates
error-map/provenance information
row-role metadata
column permutation/sort mapping
```

Do not duplicate circuit-level swim computation inside `color-code-stim` unless there is a clear architectural reason.

Any external-package change requires dedicated tests in that repository.

---

# 9. External PyMatching changes

Reuse the Phase-2A generic soft-output API wherever possible.

Do not modify PyMatching unless the circuit-level implementation proves that a required generic capability is missing.

Potential reasons for a PyMatching change include:

- growth/radius export fails on circuit-level graphs;
- boundary half-edges or parallel mechanisms lose required analysis provenance;
- repeated decode state is not reset correctly;
- observable-neutral graph structures trigger unsupported assumptions;
- current API cannot map growth data back to stable stage-2 column IDs.

If a PyMatching change is required:

1. keep it generic;
2. do not add color-code-specific logic;
3. preserve hard predictions and ordinary solution weights;
4. add C++ and Python regression tests;
5. retain existing Phase-2A soft-output behavior exactly where applicable.

Do not attempt certified odd-cut-dual extraction unless separately required to unblock correctness.

The production score may remain:

```text
swim_bound_certified = False
```

when using the existing final-defect metric-ball convention.

---

# 10. Closed-memory experiment scope

This task targets a standard fully terminated triangular 6.6.6 color-code memory experiment.

Required experimental form:

```text
distance = d
rounds = d
triangular color code
tri_optimal schedule unless the current standard circuit-level API establishes the equivalent canonical schedule
uniform circuit-level noise model
ordinary concatenated MWPM hard decoder
per-color circuit-level swim soft output
```

Use the current `color-code-stim` definition of its uniform circuit-level noise model.

Do not hand-create a different depolarizing model merely because it looks equivalent.

Record the exact package noise-model configuration in metadata.

Do not implement open future temporal boundaries.

Do not implement sliding-window decoding.

---

# 11. Component test plan

Every new component must have tests before end-to-end integration.

## M0 — Freeze baseline

Before changes:

- record SHAs/branches/remotes;
- run current main-project tests;
- run relevant PyMatching tests;
- run relevant color-code-stim tests;
- run the current code-capacity soft-output regression fixture;
- save baseline logs.

Stop if baseline is unexpectedly broken.

## M1 — Circuit-level adapter

Test:

- H2 shape and active row typing;
- physical versus virtual row metadata;
- observable-label vector shape;
- probability/weight alignment;
- column/source mapping;
- row/column sort permutation;
- stable IDs;
- detector coordinate/time/color preservation;
- zero padding handling;
- parallel mechanisms retained in the analysis model.

Use at least:

```text
d = 3,5
rounds = d
all three colors
```

## M2 — Base graph construction

Test:

- every retained active H2 column becomes exactly one labelled mechanism edge/loop;
- one-detector columns complete at `b_star`;
- two-detector columns retain both real endpoints;
- zero-detector logical columns become labelled loops;
- parallel mechanisms remain distinguishable;
- graph incidence reproduces `D`;
- edge labels reproduce `L2`.

Construct matrix-vs-graph round-trip tests.

## M3 — Class-existence test

For actual retained memory graphs:

- verify the rank criterion;
- construct an explicit odd kernel witness where the class exists;
- compare rank result against witness result.

Test all colors at small `d`.

If any standard measured-sector color has no opposite class, stop and investigate before proceeding.

## M4 — Balance test and two-boundary preprocessing

Implement the spanning-forest potential algorithm.

Test on:

- synthetic balanced graphs;
- synthetic unbalanced graphs with an internal odd cycle;
- parallel edges;
- disconnected components;
- actual circuit-level `c`-only graphs.

For actual memory graphs record:

```text
distance
rounds
color
balance_passed
number of vertices
number of mechanisms
number of half-edges
number of internal odd-cycle obstructions
```

Sweep at least:

```text
d = 3,5,7
rounds = d
colors = r,g,b
```

If balance always passes in this sample, report that as implementation evidence only, not a family-wide theorem.

## M5 — Logical cover

Test the exact theorem independently on hand-built graphs:

- odd triangle;
- even triangle;
- labelled loop;
- two parallel half-edges with different labels;
- disconnected graph;
- graph with `ker D = 0`;
- graph where arbitrary cross-sheet multisource distance would be wrong.

For small actual DEM subgraphs, compare the cover result to brute-force enumeration of:

\[
\min_{Dz=0,\;Lz=1} w(z).
\]

## M6 — Cut versus cover

Whenever the balance test passes:

- build the two-boundary cut;
- compute uncontracted logical distance;
- compute the cover logical distance;
- require equality;
- recover witnesses from both;
- verify:
  \[
  Dz=0,\quad Lz=1.
  \]

This is a critical correctness gate.

## M7 — Cluster residual transport

Reuse/extend the independent Phase-2A residual-metric reference.

Test:

- spatial edge;
- timelike edge;
- diagonal/hook edge;
- virtual-detector incident edge;
- partial coverage;
- complete coverage;
- boundary half-edge;
- loop;
- parallel edges;
- covered odd logical cycle;
- zero residual logical witness.

Do not reduce an entire covered connected component to an unlabelled vertex before logical parity is preserved.

## M8 — PyMatching growth integration

On actual circuit-level stage-2 decoding:

- obtain growth/radii;
- map growth centers to original graph vertices;
- compute residuals;
- compare production residuals against an independent small Python reference for selected small instances;
- check repeated/batched decode state reset;
- check soft-output on/off hard result invariance.

## M9 — Per-color circuit-level swim

For each color return:

```text
phi_c
method
balance_passed
class_exists
optional witness
certification flag
```

Verify every witness.

## M10 — Full concatenated decoder integration

For each shot compute:

```text
phi_r
phi_g
phi_b
ordinary_selected_color
selected_swim_distance
```

with:

```text
selected_swim_distance = phi[ordinary_selected_color]
```

Do not use the minimum over colors.

Hard prediction, hard weights, selected color, and failure labels must match exactly with circuit-level swim disabled.

## M11 — Comparative/forced-gap pairing

Reuse the existing paired comparative-decoding workflow if available.

Store the current comparative logical gap under the experiment-layer alias:

```text
forced_gap
```

and retain:

```text
forced_gap_source =
"existing color-code-stim comparative-decoding logical gap"
```

Pair swim and comparative outputs on the same physical shots whenever the current circuit representations permit the already validated mapping.

If circuit-level comparative pairing requires a new mapping not already established, test that mapping explicitly before using it.

---

# 12. End-to-end small memory experiment

After all correctness gates pass, create a small end-to-end validation experiment analogous to the current code-capacity workflow.

Create a reusable experiment entry point, for example:

```text
src/color_code_softoutput/experiments/circuit_level_memory_test.py
```

and a thin notebook:

```text
notebooks/circuit_level_getting_started.ipynb
```

The notebook must not contain production implementation logic.

## Default validation grid

Use a deliberately small validation grid.

Preferred initial configuration:

```text
d = [3, 5, 7]
rounds = d
uniform circuit-level noise
p = one representative sub-threshold value from the project's existing circuit-level conventions
shots_per_point ≈ 2000
```

If the repository already has an agreed small circuit-level fixture value, reuse it.

Otherwise use:

```text
p = 0.003
```

and document that this is an implementation-validation point, not a paper-reproduction point.

Do not expand to a threshold sweep in this task.

The purpose is end-to-end correctness and macroscopic sanity, not reproduction of Lee's circuit-level threshold.

---

# 13. Reuse the existing simulation/analysis infrastructure

Do not build a second unrelated simulation framework.

Reuse and extend the current main-package infrastructure for:

```text
parallel workers
batching
deterministic seeds
Parquet storage
metadata
dataset loading
analysis classes
figure_style.py
```

The circuit-level experiment should produce the same style of timestamped result directory as the current code-capacity workflow.

Store at minimum per shot:

```text
experiment_id
config_id
batch_id
shot_index
seed/batch_seed

distance
rounds
physical_error_rate
noise_model_name

actual_observable

ordinary_prediction
ordinary_logical_error
ordinary_selected_color

stage2_weight_r
stage2_weight_g
stage2_weight_b

swim_distance_r
swim_distance_g
swim_distance_b
selected_swim_distance

swim_method_r
swim_method_g
swim_method_b

balance_passed_r
balance_passed_g
balance_passed_b

class_exists_r
class_exists_g
class_exists_b

comparative_prediction
comparative_logical_error
forced_gap
```

Add certification flags where useful.

Keep per-color values even if current plots use only the selected color.

---

# 14. Metadata for reproducibility

Record at minimum:

```text
run timestamp/timezone
experiment name
distance list
rounds rule
physical error rates
shots per point
batch size
num workers
master seed

exact circuit type
exact CNOT schedule
exact uniform circuit-level noise-model configuration
DEM conversion/decomposition options

main repository SHA + dirty status
PyMatching SHA + dirty status
color-code-stim SHA + dirty status

Python version
package versions

balance-test results for each static graph
logical-topology method used per color/config
growth convention name
swim-bound certification status

source script hashes
TeX algorithm note hash
```

If the actual hard-decoder DEM differs from the paper algorithm, record the actual implementation path and do not silently relabel it as the paper algorithm.

---

# 15. Notebook workflow

The notebook should be concise and mirror the current code-capacity Getting Started workflow.

Suggested cells:

1. import package;
2. show chosen circuit-level validation configuration;
3. choose:
   ```text
   shots
   num_workers
   seed
   verbose
   ```
4. run or load a timestamped experiment;
5. print static topology diagnostics:
   ```text
   balance result by d/color
   cut vs cover method
   class-existence status
   ```
6. load Parquet data;
7. plot selected swim-distance distribution;
8. plot conditional LER versus selected swim distance;
9. plot post-selection curve;
10. optionally overlay forced-gap post-selection curve;
11. inspect a few logical witnesses / disagreement shots;
12. print hard-output invariance summary.

Reuse the existing analysis classes where possible.

If minor extensions are needed for the `rounds`/noise-model dimensions, make them generic rather than circuit-level special cases.

---

# 16. End-to-end acceptance criteria

The circuit-level implementation is accepted only if all of the following pass.

1. Current baseline tests pass.
2. `(D,L2)` reconstructed from the adapter matches the authoritative retained stage-2 matrices.
3. Base graph incidence exactly reproduces `D`.
4. Edge logical labels exactly reproduce `L2`.
5. Opposite-class existence test is correct.
6. Balance test is validated on synthetic and actual graphs.
7. Two-boundary and cover distances agree whenever balance passes.
8. Cover agrees with brute force on small exact instances.
9. Residual metric agrees with an independent reference on small instances.
10. Every returned witness satisfies:
   \[
   Dz=0,\quad L_2z=1.
   \]
11. Returned witness cost equals computed `phi` within the declared numerical tolerance.
12. Soft-output on/off does not change:
   ```text
   hard prediction
   ordinary stage-2 weight
   selected color
   failure label
   ```
13. Repeated/batch execution does not leak growth state.
14. The ~2000-shot end-to-end experiment completes and saves valid Parquet/metadata.
15. Notebook can load the saved run and generate the standard plots.
16. Open temporal/sliding-window behavior is not accidentally enabled.

If a correctness gate fails, stop and fix it before interpreting numerical plots.

---

# 17. Circuit-level theory versus implementation limitations

The final implementation/status report must preserve the following distinctions.

## Proven/defined

- fixed-fiber logical quotient from `(D,L2)`;
- general logical-cover computation;
- gated two-boundary reduction;
- residual-coverage transport;
- controlled Phase-1 reduction;
- certified representative-gap theorem under its exact dual assumptions.

## Practical current implementation

- current hard `color-code-stim` effective DEM/decomposition;
- current Phase-2A PyMatching growth-ball export;
- likely `swim_bound_certified=False` unless a new exact certificate is actually implemented and verified.

## Not part of this task

- open temporal boundary;
- sliding-window decoding;
- temporal escape confidence;
- circuit-level threshold reproduction;
- paper-scale simulations;
- ILP exact logical-gap benchmarking;
- optimal three-color aggregation strategy;
- proof that every standard memory graph for every `d,T,schedule` always passes the balance condition.

---

# 18. Engineering quality

Use English for source code, docstrings, comments, metadata keys, logs, and public APIs.

Use modern type hints.

Every public class/function must document:

```text
purpose
Args
Returns
Raises
units
array shapes
valid options
scientific semantics
```

Prefer:

- immutable typed dataclasses for static topology;
- explicit enums for topology method/status;
- pure functions for graph transforms where practical;
- dependency injection instead of globals;
- no magic detector-index ranges;
- no coordinate-only topology inference;
- stable source IDs;
- deterministic tests;
- atomic Parquet writes;
- explicit errors instead of silent fallback.

Comments should explain **why**, especially where DEM semantics are subtle.

---

# 19. Final project-state updates

After implementation and the small end-to-end run, update the project state.

At minimum review/update:

```text
AGENTS.md
STATUS.md
PROJECT_DETAIL.md
IMPLEMENTATION_STATUS.md
REVIEW.md
NOTATIONS.md
REFERENCES.md
```

Update `AGENTS.md` only with durable project-level knowledge, not transient debugging history.

Record:

- new circuit-level module architecture;
- current external SHAs/branches;
- balance-test findings;
- cut/cover behavior;
- test totals;
- e2e configuration and output directory;
- known limitations;
- certification status;
- explicit deferral of sliding-window/open-temporal-boundary work.

Do not modify the Phase-1 theorem claims unless a genuine contradiction is found.

---

# 20. Final deliverables

Provide:

## TeX

A concise implementation-facing circuit-level swim algorithm integrated into the theory notes.

## Main package source

Reusable circuit-level modules under:

```text
src/color_code_softoutput
```

## External changes

Only if required, committed on dedicated branches with their own tests.

## Tests

Component tests plus end-to-end tests.

## Experiment

One small `d`-round uniform circuit-level memory run with approximately 2000 shots per point on a deliberately small validation grid.

## Notebook

A Getting Started-style circuit-level notebook using only reusable modules.

## Report

Update the implementation/project status and summarize:

```text
files added/changed
external SHAs
test totals
actual balance results
how often two-boundary vs cover was used
e2e configuration
runtime
saved result directory
hard-output invariance result
known limitations
next task = sliding-window/open-temporal-boundary integration
```

Then stop.

Do not automatically begin sliding-window decoding, large-scale numerics, or further confidence-aggregation research.
