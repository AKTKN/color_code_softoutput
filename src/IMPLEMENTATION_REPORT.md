# Implementation Report: Color-code Swim-Distance Integration

## 1. Goal and theoretical contract

The immediate Phase-2 goal is to implement the Phase-1 fixed-branch swim distance for the concatenated MWPM color-code decoder and use it in numerical experiments.

The intended pipeline is

```text
color-code-stim circuit / DEM
        |
        v
color-specific DEM decomposition
        |
        +---- stage 1 MWPM
        |
        v
stage-2 c-only matching graph
        |
        +---- ordinary MWPM hard decision
        |
        +---- resolved-boundary soft-output analysis
                    |
                    v
                 phi_c
```

For a fixed color `c` and one CSS sector, Phase 1 establishes the following contract for the standard odd-distance triangular 6.6.6 family under perfect measurements.

- Each stage-2 edge corresponds to one physical data qubit.
- The ordinary c-only matching graph merges two geometrically different dangling-edge classes into one artificial boundary.
- Those classes are (i) all `d` qubits on the complete physical c-colored side and (ii) the unique corner opposite that side.
- Resolving them into terminals `b_c^0` and `b_c^1` leaves the physical edge identities and weights unchanged.
- Within a fixed stage-1 fiber, a difference chain joining the two terminals represents the nontrivial physical logical class, while a closed difference chain is stabilizer-trivial.
- After decoder-cluster contraction,
  \[
  \phi_c=\operatorname{dist}_{\bar G_c}(b_c^0,b_c^1).
  \]

This is a per-color, fixed-stage-1-fiber metric. It is not automatically the full concatenated-decoder logical gap, a logical-class LLR, or a three-color aggregate confidence.

For exact MWPM with the appropriate certified growth/dual data, Phase 1 also proves a one-sided minimum-representative bound. The implementation should therefore distinguish the geometric metric from the stronger certified-bound interpretation.

---

# 2. `seokhyung-lee/color-code-stim`

Inspected snapshot:

```text
repository: seokhyung-lee/color-code-stim
branch:     main
commit:     0eb35935c1e5ff30ba3db9def30a9d35bca2f16d
```

This should remain the primary color-code circuit and concatenated-decoder package.

Relevant source structure:

```text
src/color_code_stim/
├── color_code.py
├── circuit_builder.py
├── graph_builder.py
├── noise_model.py
├── decoders/
│   ├── base.py
│   ├── concat_matching_decoder.py
│   └── ...
├── dem_utils/
│   ├── dem_decomp.py
│   └── dem_manager.py
└── simulation/
    ├── sampling_utils.py
    └── simulator.py
```

The package currently depends on standard `pymatching>=2.1.0`.

## 2.1 `ColorCode` and initial experiment configuration

`ColorCode` is the main experiment interface. For triangular memory experiments it supports

```python
ColorCode(
    d=...,
    rounds=...,
    circuit_type="tri",
    cnot_schedule="tri_optimal",
    noise_model=...,
)
```

The default schedule is already `tri_optimal`, documented as

```text
(2, 3, 6, 5, 4, 1, 3, 4, 7, 6, 5, 2).
```

`NoiseModel(bitflip=p)` applies bit-flip noise to data qubits at the start of each syndrome-extraction round. Consequently:

- `rounds=1` is the cleanest first validation of a single data-noise layer with perfect measurement;
- `rounds>1` with `bitflip=p` is repeated data-only memory noise with perfect measurements, not literally one code-capacity error layer.

This distinction should be explicit in experiment metadata and in the paper.

## 2.2 `TannerGraphBuilder`

`graph_builder.py` carries useful physical geometry metadata:

- spatial coordinates `x`,`y`;
- face/check color;
- physical boundary labels;
- data/ancilla identity;
- lattice-edge colors.

This is an excellent independent source for validating the stage-2 boundary classifier for `d=3,5,7,...`.

It should not be the sole runtime source of soft-output topology, because future circuit-level support should be based on decoder/DEM metadata as well.

## 2.3 `DemManager`

`DemManager` extracts detector metadata from Stim detector coordinates, including spatial position, time, Pauli type, and color. It constructs the original DEM and three color-decomposed `DemDecomp` objects.

This is the natural future extension point for circuit-level topology metadata.

## 2.4 `DemDecomp`

For each color, `DemDecomp` constructs two models:

```text
stage 1: restricted DEM
stage 2: monochromatic DEM
```

and stores objects including

```python
Hs = (H1, H2)
probs = (p1, p2)
dems_symbolic
error_map_matrices
obs_matrix_stage2
```

Stage 1 creates virtual information that becomes detector-like constraints in stage 2. Hence stage-2 rows have two semantic types:

```text
physical c-colored detector rows
stage-1 virtual parity rows
```

The stage-2 mapping back to original DEM error mechanisms is retained. This is exactly the metadata needed to construct the resolved c-only topology robustly.

For the initial perfect-measurement setting, a one-ended H2 column should be classified by the type of its surviving row:

```text
surviving STAGE1_VIRTUAL row
    -> missing c-face
    -> c-side terminal b_c^0

surviving PHYSICAL_C_DETECTOR row
    -> missing c-edge
    -> opposite-corner terminal b_c^1
```

This should be treated as a hypothesis to validate against the physical Tanner geometry, not merely assumed from row numbering.

## 2.5 `ConcatMatchingDecoder`

The current implementation is structurally well aligned with the Phase-1 construction.

Stage 1:

```text
H1, p1
-> weights = log((1-p1)/p1)
-> pymatching.Matching.from_check_matrix(...)
-> decode_batch(...)
```

Stage 2:

```text
mask detector outcomes to color c
concatenate stage-1 prediction
H2, p2
-> pymatching.Matching.from_check_matrix(...)
-> decode_batch(..., return_weights=True)
```

The outer decoder loops over colors and, if comparative decoding is enabled, logical classes. It maps the stage-2 result back to the original DEM and chooses the final best correction.

Current `full_output` includes fields such as

```text
best_colors
weights
error_preds
logical_gaps       # comparative decoding
logical_values
```

but it does not expose per-color stage-2 weights or swim distances.

### Existing comparative gap

`_get_final_predictions` computes the current comparative logical gap by first minimizing over colors within each forced logical class, then subtracting the smallest class minimum from the second smallest.

This is conceptually different from a fixed-color stage-2 swim distance and the two values must remain separately named in code and data.

### Performance observation

Both `_decode_stage1` and `_decode_stage2` currently construct fresh `pymatching.Matching` objects inside decoding calls. The swim topology is static for fixed H/color, so after correctness is established the implementation should cache configured stage-2 matchers/topologies for the default non-custom path.

Do not introduce cache complexity before regression correctness is established.

## 2.6 Simulation output

`Simulator.sample()` provides per-shot detector and observable outcomes. `Simulator.simulate(full_output=True)` computes the failure mask and merges decoder outputs.

Therefore conditional LER analysis is straightforward once per-shot swim fields are added to decoder output.

## 2.7 Test coverage

The inspected repository has a relatively small top-level test surface, notably `tests/test_circuit_generation_simulation.py`. Dedicated topology, soft-output, and decoder-regression tests are required.

---

# 3. `Zihan-Chen-PhMA/PyMatching`

Inspected snapshot:

```text
repository: Zihan-Chen-PhMA/PyMatching
branch:     master
commit:     2abf455ef58ee67c4232e7896e1468e7c983f372
soft-output feature commit:
            4497499196a30b4fb5e872b9f169866f19bc145e
```

This fork is the most relevant reference because it integrates a Meister-style soft output with Sparse Blossom.

The soft-output feature touches:

```text
src/pymatching/matching.py
src/pymatching/sparse_blossom/driver/mwpm_decoding.cc/.h
src/pymatching/sparse_blossom/driver/user_graph.cc/.h
src/pymatching/sparse_blossom/driver/user_graph.pybind.cc
src/pymatching/sparse_blossom/gap_dijkstra/dijkstra_graph.cc/.h
```

and includes an `SO_example/` for a rotated surface-code memory circuit.

## 3.1 Added API

The fork exposes methods including

```python
SO_calculator_setup()
add_boundary_node_SO(...)
add_boundary_edge_SO(...)
add_cycle_endpoints_pair_SO(...)
add_cycle_endpoints_pair_mono_SO(...)
decode_batch_soft_output(...)
decode_batch_soft_output_2d(...)
```

plus lower-level image-node and edge-redirection helpers.

The surface-code example parses DEM coordinates, identifies logical boundary detectors, adds two analysis-only boundary nodes, reconnects boundary half-edges to them, configures the terminal pair, and calls `decode_batch_soft_output`.

That high-level pattern is directly reusable for the color-code c-only resolved graph.

## 3.2 Internal soft-output graph

`SoftOutputDijkstra` builds a Boost weighted graph corresponding to the MWPM graph. After Sparse Blossom growth completes, it reads region information, derives local radii, modifies residual edge lengths, and runs Dijkstra between configured endpoint pairs.

This is valuable because the soft output is computed while the final graph-fill regions still exist and before the decoder's internal blossom structures are destroyed.

## 3.3 Important concerns before reuse

### A. Returned “weight” is overwritten by the soft output

In the fork's `decode_detection_events_soft_output`, the ordinary solution is extracted but the final code assigns the soft-output value into the same `weight` output slot. Thus `decode_batch_soft_output(..., return_weights=True)` returns the soft output under a field/API shape that ordinarily means solution weight.

For this project the API must instead return separately:

```text
hard prediction
ordinary MWPM solution weight
swim distance(s)
```

Soft-output enablement must not alter the meaning of an existing weight field.

### B. Boundary configuration is node-based and fragile

`add_boundary_edge_from_mwpm(inner_index, ...)` assumes a boundary half-edge appears as the first `nullptr` neighbor entry of a detector node. This is fragile if a node has multiple mechanisms, multiple boundary half-edges, or if circuit-level decomposition generates parallel mechanisms.

For the first code-capacity implementation it is acceptable only with strict validation that the assumed half-edge is unique. Long term, the topology API should identify error mechanisms/edges explicitly.

### C. Parallel-edge provenance needs an audit

Several analysis-graph helper operations use endpoint lookup. The color-code theory depends on labelled edge/error-mechanism identity. A generalized backend must not silently collapse parallel edges or address them ambiguously.

### D. Radius/reweight semantics must be verified against Phase 1

The fork derives a local radius from Sparse Blossom internals and subtracts endpoint radii from edge weights. Phase 1 formulates exact interval coverage/contraction. These may agree for the intended growth state, but that equivalence must be tested rather than assumed.

A slow independent Python reference implementation is therefore mandatory before the color-code integration is trusted.

### E. SO setup is inconsistent across constructors

The modified `Matching.__init__` auto-runs `SO_calculator_setup()` in the check-matrix path, while graph/DEM constructors can return earlier; the example manually calls setup for DEM construction.

A cleaned API should make setup explicit and consistent.

### F. Dedicated SO tests are insufficient

The new C++ source is compiled, but the inspected CMake test list does not include a dedicated `gap_dijkstra` test file. This project should add explicit soft-output unit/regression tests.

---

# 4. `AKTKN/concatenated-decoder`

Inspected snapshot:

```text
repository: AKTKN/concatenated-decoder
branch:     main
commit:     8f817004a5a28a219767f71d048235bd48a5ad9b
```

This repository should initially remain an experiment/prototype consumer rather than a second implementation site.

Its `src/concatbp` package contains comparative decoding, decoders, experiment tools, and `concat_mwpm/`. The current `concat_mwpm/runner.py` dynamically imports `color_code_stim`, constructs `ColorCode`, supports variants including `mwpm`, `uf`, and `mwpm_bplsd`, and already has a memory-experiment output workflow.

Recommended role:

1. stabilize the generic PyMatching soft-output backend;
2. integrate it into `color-code-stim`;
3. expose a stable `full_output` schema;
4. then update this repository to consume those fields.

Do not duplicate the swim-distance computation in this package.

---

# 5. Recommended software boundary

The central design rule is:

> PyMatching should know how to compute a generic graph soft output from MWPM growth data; `color-code-stim` should know which stage-2 edges belong to which color-code logical terminal.

Recommended layers:

```text
Layer A: generic modified PyMatching backend
    - access MWPM growth/cluster data
    - compute residual graph metric
    - shortest distance between configured logical terminals

Layer B: color-code stage-2 topology adapter
    - type stage-2 rows/error mechanisms
    - classify c-side versus opposite-corner half-edges
    - configure Layer A

Layer C: ConcatMatchingDecoder
    - ordinary stage 1
    - ordinary stage 2
    - optional per-color phi_c
    - hard decision unchanged

Layer D: experiment runner
    - sample physical shots
    - save failures, weights, phi values
    - compare with comparative gap
```

This is also the cleanest route to circuit-level support later.

---

# 6. Future circuit-level design constraint

The current Phase-1 proof is spatial/perfect-measurement. Do not silently generalize it.

Nevertheless, preserve generic metadata now:

```text
error mechanism id
stage-2 column/edge id
real detector endpoint ids
stage-1 virtual endpoint ids
detector coordinates
time coordinate
physical/virtual row role
boundary role
original DEM mapping
```

Use an extensible boundary-role enum such as

```text
C_SIDE
OPPOSITE_CORNER
TEMPORAL_INITIAL
TEMPORAL_FINAL
OTHER
UNCLASSIFIED
```

The code-capacity classifier should require exactly the first two logical classes. Circuit-level ambiguous half-edges should remain `UNCLASSIFIED` and cause a clear refusal to compute a logical swim distance until a validated topology rule is supplied.

---

# 7. Initial numerical dataset

First validation experiment:

```python
ColorCode(
    d=d,
    rounds=1,
    circuit_type="tri",
    cnot_schedule="tri_optimal",
    noise_model=NoiseModel(bitflip=p),
    comparative_decoding=False,
)
```

Recommended per-shot data fields:

```text
d
p
seed/task id
actual observable
predicted observable
logical failure
selected color
stage2 weights r/g/b
phi_r, phi_g, phi_b
selected phi
```

For a paired comparative-decoding study, add `comparative_gap` only after a shared-shot protocol has been verified.

Primary analyses:

- histogram/ECDF of swim distance;
- success/failure-conditioned distributions;
- `P(fail | phi-bin)` with Wilson intervals;
- post-selection conditional LER versus acceptance/discard fraction;
- swim versus comparative gap at matched acceptance fraction;
- runtime overhead.

`phi_selected = phi_[best_color]` is useful for exploratory plots, but Phase 1 has not proved it to be a full-decoder gap.

---

# 8. Main risks

The highest-risk implementation points are:

1. verifying that Sparse Blossom internal growth state implements the intended Phase-1 contraction metric;
2. preserving edge/error-mechanism identity, especially with parallel edges;
3. classifying the two boundary types from robust metadata rather than ordering conventions;
4. proving soft-output enablement leaves hard decisions and ordinary weights unchanged;
5. preventing C++ state leakage between batch shots;
6. building a genuinely paired comparison with comparative decoding;
7. resisting premature circuit-level boundary assumptions.
