# Integration Plan: MWPM Swim Distance for the Color-Code Concatenated Decoder

## 1. Design objective

Implement a production-quality path from the existing concatenated-MWPM stage-2 decoder to a per-color swim distance \(\phi_c\), while preserving the existing hard-decision decoder exactly.

The software interfaces should be general, but the first validated topology is only:

```text
triangular 6.6.6 color code
odd distance
memory experiment
perfect measurement / data-only bit-flip noise
fixed color stage-2 branch
MWPM
```

---

# 2. Modified PyMatching backend

Use the inspected `Zihan-Chen-PhMA/PyMatching` fork as the starting reference, but clean the API before color-code integration.

A target API may look conceptually like

```python
result = matching.decode_batch_with_soft_output(
    shots,
    soft_output_config=config,
)
```

with separate structured fields:

```text
predictions
solution_weights
soft_outputs
```

Do not reuse the ordinary solution-weight field for swim distance.

The backend needs generic capabilities only:

1. initialize/reset a soft-output analysis graph from the MWPM graph;
2. create analysis-only logical terminal nodes;
3. associate specific boundary half-edges/error mechanisms with those terminals;
4. read final MWPM growth information;
5. construct the residual contracted metric;
6. compute shortest distance between one or more terminal pairs;
7. return soft output separately from ordinary decode data;
8. preserve edge identity sufficiently for parallel mechanisms;
9. reset all per-shot analysis state in batch decoding.

Do not hard-code triangular color-code logic in C++.

The operational sequence should remain

```text
run existing Sparse Blossom
freeze/read final growth state
compute soft-output metric
extract ordinary MWPM correction
return both
```

---

# 3. Independent reference calculator

Before relying on the C++ backend, implement a slow independent Python reference, suggested location:

```text
src/color_code_stim/soft_output/reference.py
```

It should directly implement the Phase-1 metric on explicit small weighted graphs:

```text
input:
    resolved graph
    original nonnegative edge weights
    supplied growth radii / interval coverage
    logical terminals

output:
    exact residual edge weights
    shortest terminal distance
    optional witness path
```

It does not need to be fast. NetworkX, SciPy, or a simple heap-based Dijkstra implementation is acceptable.

The production backend must agree with this implementation on hand-calculated and randomized small graphs before color-code integration proceeds.

---

# 4. New `color-code-stim` soft-output package

Recommended package:

```text
src/color_code_stim/soft_output/
├── __init__.py
├── topology.py
├── pymatching_backend.py
├── reference.py
└── results.py
```

## 4.1 `topology.py`

Represent semantic roles explicitly. Suggested concepts:

```python
class Stage2RowRole(Enum):
    PHYSICAL_C_DETECTOR = ...
    STAGE1_VIRTUAL = ...

class BoundaryRole(Enum):
    C_SIDE = ...
    OPPOSITE_CORNER = ...
    TEMPORAL_INITIAL = ...
    TEMPORAL_FINAL = ...
    OTHER = ...
    UNCLASSIFIED = ...
```

Suggested edge metadata:

```python
@dataclass(frozen=True)
class Stage2EdgeMeta:
    column_id: int
    original_error_id: int | None
    endpoint_rows: tuple[int, ...]
    boundary_role: BoundaryRole | None
    physical_qubit_id: int | None
    coordinates: tuple[float, ...] | None
```

and topology:

```python
@dataclass(frozen=True)
class Stage2SoftOutputTopology:
    color: str
    row_roles: tuple[Stage2RowRole, ...]
    edges: tuple[Stage2EdgeMeta, ...]
    terminal_edge_columns: dict[BoundaryRole, tuple[int, ...]]
```

Exact names may differ, but downstream code must not reconstruct semantics from raw row order.

## 4.2 `pymatching_backend.py`

Responsibilities:

- construct/cache the production MWPM object;
- configure the generic soft-output topology;
- batch decode;
- return prediction, ordinary solution weight, and swim value separately.

It must not decide which color-code boundary role a column has.

## 4.3 `results.py`

Use explicit result structures, for example:

```python
@dataclass
class Stage2DecodeResult:
    predictions: np.ndarray
    solution_weights: np.ndarray
    swim_distances: np.ndarray
```

and a higher-level output that can retain all three color branches.

---

# 5. Stage-2 topology construction for code capacity

The first classifier should use H2 together with explicit row-role metadata produced during `DemDecomp` construction.

For the initial perfect-measurement triangular model, each relevant H2 column should have one or two nonzero entries.

```text
2 endpoints -> ordinary interior stage-2 edge
1 endpoint  -> boundary half-edge
```

For one-ended columns:

```text
surviving STAGE1_VIRTUAL row
    -> missing c-face
    -> C_SIDE terminal

surviving PHYSICAL_C_DETECTOR row
    -> missing c-edge
    -> OPPOSITE_CORNER terminal
```

Cross-check this classification independently with Tanner geometry.

For every tested odd distance and color, require:

```text
count(C_SIDE)          = d
count(OPPOSITE_CORNER) = 1
```

Any failure should stop the integration.

---

# 6. Required `DemDecomp` changes

The current decomposition creates H1/H2 but should expose typed metadata explicitly.

Add or derive stable fields such as:

```text
stage2_row_roles
stage2_row_source_ids
stage2_error_source_ids
stage2_error_endpoint_metadata
stage2_error_original_dem_ids
```

For every H2 row, downstream code must know whether it is:

```text
physical c detector
stage-1 virtual detector
```

For every H2 column, preserve:

```text
stage-2 column id
original DEM error mechanism(s)
endpoint row ids
known detector coordinates/time
mapping back to original DEM
```

These fields should survive even if the first experiment does not use every field. They are the main hook for future circuit-level support.

---

# 7. `ConcatMatchingDecoder` changes

## 7.1 Opt-in configuration

Add an explicit optional soft-output mode, e.g.

```python
soft_output: None | Literal["swim"] = None
```

or

```python
compute_swim_distance: bool = False
```

An extensible mode is preferable if more metrics will be added later.

The default must preserve current behavior.

## 7.2 Cache static matching objects after correctness is established

For the standard non-custom path, cache:

```text
stage1_matchers[color]
stage2_matchers[color]
stage2_soft_output_topology[color]
```

Do not silently cache `custom_dem_data` without a defined cache key/invalidation rule.

## 7.3 Stage-2 return contract

When swim output is enabled, `_decode_stage2` should return:

```text
predictions
ordinary_solution_weights
swim_distances
```

The first two must be bit-for-bit/float-identical to the old path for the same matcher and input.

## 7.4 Outer decoder output

For normal non-comparative three-color decoding, retain per-color arrays and expose under `full_output=True`:

```python
extra_outputs["color_order"]
extra_outputs["stage2_weights_by_color"]
extra_outputs["swim_distances_by_color"]
extra_outputs["selected_swim_distance"]
```

Recommended shapes:

```text
stage2_weights_by_color : (num_samples, num_colors)
swim_distances_by_color : (num_samples, num_colors)
selected_swim_distance  : (num_samples,)
```

Do not name the selected quantity `logical_gap`.

If comparative mode later requests swim values, preserve a logical-class axis rather than collapsing it prematurely.

---

# 8. Circuit-level readiness without circuit-level claims

Preserve metadata now:

```text
detector id
x/y/t coordinates
color
Pauli type
physical/virtual row role
error mechanism id
original DEM id
stage-2 column id
boundary role
```

For circuit-level DEMs, do not force every half-edge into the two spatial logical terminal roles.

Unverified mechanisms should be `UNCLASSIFIED`. Until the circuit-level topology is proved, requesting the logical swim metric with unresolved roles should fail clearly.

This avoids a second major refactor while preventing an unproved physics assumption from entering the implementation.

---

# 9. Milestone sequence

## M0 — Freeze snapshots and reproduce baselines

- clone/fork exact inspected revisions;
- record SHAs;
- build the PyMatching fork;
- run its existing tests and SO surface-code example;
- install `color-code-stim` editable;
- run existing tests;
- save a seeded d=3 baseline prediction/weight fixture.

Exit condition: all baselines reproduced before modifications.

## M1 — Clean generic PyMatching soft-output API

- separate solution weight and soft output;
- make SO initialization consistent;
- add structured batch return;
- validate topology setup;
- audit half-edge and parallel-edge semantics;
- add C++/Python tests.

Exit condition: old hard decode unchanged; surface-code SO example still works.

## M2 — Validate metric against independent reference

- implement Python residual-metric reference;
- test hand-computable graphs;
- test partial-edge coverage;
- test randomized small graphs.

Exit condition: production backend agrees with reference on all tests.

## M3 — Typed color-code stage-2 topology

- expose H2 row roles and edge provenance;
- implement code-capacity two-terminal classifier;
- cross-check with Tanner geometry for d=3,5,7 and r/g/b.

Exit condition: `C_SIDE=d`, `OPPOSITE_CORNER=1` for every case.

## M4 — Integrate swim output into stage 2

- configure one stage-2 SO analyzer per color;
- decode exactly the same stage-2 syndrome and weights;
- return phi alongside ordinary result;
- preserve hard decision and ordinary weight.

Exit condition: SO off/on regression-identical for historical outputs.

## M5 — Small-code mathematical validation

For d=3 then d=5:

- construct independent resolved graph;
- compare phi;
- map shortest path back to physical support;
- verify zero syndrome and nontrivial logical parity;
- brute-force tiny fixed-fiber representative gaps where feasible.

If production growth data satisfy the certified Phase-1 assumptions, additionally verify the one-sided representative-gap inequality.

## M6 — Pilot numerical experiment

Only after M0–M5 pass.

Start with a small grid such as d in {3,5,7}, a few p values, and moderate shots. Save raw per-shot fields and generate diagnostic distributions/post-selection curves.

Do not start paper-scale jobs until the pilot is reviewed.

## M7 — Paired comparative-gap comparison

Build a shared-shot protocol and compare swim versus comparative gap at matched retained-shot fraction.

Do not use independent Monte Carlo samples for the primary metric comparison.

## M8 — Large numerical campaign

After pilot review:

- freeze d/p/shots/configs;
- run PBS/cluster jobs;
- save exact repository SHAs;
- aggregate statistics and plots.

## M9 — `AKTKN/concatenated-decoder` compatibility

Once the API is stable, update its runner/stats layer to consume new `color-code-stim` outputs. Do not duplicate the core metric implementation.

Union-Find remains a separate later backend.

---

# 10. Experiment data schema

Recommended raw per-shot fields:

```text
experiment_id
shot_index
seed
distance
rounds
physical_error_rate
noise_model
actual_observable
predicted_observable
logical_failure
best_color
weight_r
weight_g
weight_b
phi_r
phi_g
phi_b
phi_selected
comparative_gap       # optional paired analysis
decoder_commit
pymatching_commit
color_code_stim_commit
```

Parquet is preferable for large raw datasets; CSV is adequate for aggregated curves.

---

# 11. First statistical analyses

## Swim distribution

Plot overall and conditional distributions:

```text
P(phi)
P(phi | success)
P(phi | failure)
```

## Conditional logical error rate

Bin by phi and estimate

\[
P(L=1\mid \phi\in\text{bin})
\]

with Wilson intervals and explicit fail counts.

## Post-selection

For threshold \(\tau\), accept when \(\phi\ge\tau\). Report:

```text
acceptance rate
conditional LER
number of failures
confidence interval
```

## Comparative-gap comparison

Compare conditional LER at matched acceptance/discard rate, not matched raw threshold.

## Runtime

Separate:

```text
one-time graph/topology setup
ordinary decode
extra swim computation
total batch runtime
```

---

# 12. Stop conditions

Stop and review if any of the following occurs:

- enabling swim changes a hard correction;
- ordinary MWPM solution weight changes;
- expected boundary counts fail;
- production C++ metric disagrees with the independent reference;
- shot order changes batch outputs;
- repeated decoding reveals stale state;
- circuit-level half-edges are silently classified using an unproved rule;
- comparative decoding cannot be paired cleanly with the same physical samples.
