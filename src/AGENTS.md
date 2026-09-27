# AGENTS.md — Phase-2A Color-Code Swim-Distance Implementation

## Current monotone-Y simulation integration (2026-09-19)

The user's follow-up authorizes paired sampling and all existing analysis
families for the newly implemented monotone-Y signed gap. Source is in
`color_code_softoutput/experiments/monotone_y_test.py` and
`analysis/monotone_y.py`; the thin notebook is
`../notebooks/monotone_y_getting_started.ipynb`. Use ordinary `color_code_so`.
The feature adapter loads in an isolated namespace without external edits.
Preserve signed scores, ordinary/comparative hard outputs, paired shots and
explicit failure associations. The notebook mirrors the current reference's
six-point configuration (d=9,13,15; p=.04/.05; 1M shots/point), starts with
sampling disabled, and analyzes the completed 768-shot smoke. Main API/CLI
retain the existing shared grid defaults. No full study was launched.
See `../notes/support/MONOTONE_Y_EXPERIMENT.md` and `../STATUS.md`.

## Current selectable path-gap versions (2026-09-19)

The follow-up user request authorizes selecting v1 or v2 at simulation time.
`run_experiment(config, metric_version="v1")` and `sample_batch` accept v1/v2
or canonical names; the CLI exposes `--metric-version`. The notebook selects
v1, while API/CLI defaults remain v2. The simulation adapter uses the feature
API's residual distances and full physical correction weight for v1, leaving
external sources unchanged. New versioned v1/v2 runs support replay; historical
unversioned v1 runs retain their old schema and saved-data audit route.

## Current path-gap overlap revision (2026-09-19)

The latest user request replaces global correction-weight subtraction with
returned-path overlap subtraction on the existing feature branch. New runner
outputs use `path_overlap_v2`, per-color overlaps and explicit metric-version
fields. Analysis retains the legacy schema/formula for unversioned saved runs;
legacy replay requires archived source. No original SWIM checkout changed.
See `../STATUS.md` and the feature worktree's `docs/path_gap_overlap_v2.md`.

## Current path-gap experiment (2026-09-19)

The user additionally authorized the same experiment as the Phase-2A Getting
Started notebook using final-correction path-gap. Reusable worker/runner and
signed schema live in `color_code_softoutput/experiments/path_gap_test.py`,
with dataset/audit/matched retention in `analysis/path_gap.py`. Shared plotters
accept explicit metric names while keeping original SWIM defaults unchanged.
The 2026-09-19 follow-up requests normal `color_code_so` execution. The metric
loader isolates the feature source namespace while using the installed SWIM
decoder/PyMatching; no environment switching or external edits are needed.
Keep both original SWIM repositories unchanged. The full-grid 7,680-shot smoke
and saved-data notebook pass. No full 6M-shot study was run. See
`../notes/support/PATH_GAP_EXPERIMENT.md` and `../IMPLEMENTATION_STATUS.md`.

## Current closed-memory circuit-level implementation

The 2026-09-16 user request authorizes
`../prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md`, superseding the
historical circuit stop below only for its closed-memory scope. Reusable
implementation is in `color_code_softoutput/circuit_level/`, with the runner
in `experiments/circuit_level_memory_test.py` and shared analysis extension
in `analysis/circuit_level.py`. Use `color_code_so`. Both external sources
remain unchanged. Consume actual public retained H2/L2 and metadata; preserve
the ordinary hard result exactly. Compute coverage before a balance-gated cut
or general same-base-vertex cover. Selected swim uses the ordinary selected
branch; all current growth remains uncertified. Do not infer temporal or
spatial logical terminal classes from coordinates. Algebraic boundary roles
and physical time/coordinate provenance are separate in the new graph model.
The bounded d=3,5,7 uniform-noise validation is the only authorized new run.
See `../notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md`; await separate
authorization for sliding windows or open future boundaries.

## Active Phase-2B state

The user authorized CODEX_PHASE2B_GETTING_STARTED_NUMERICS_PROMPT.md and requested
the Conda environment `color_code_so`. That implementation and moderate study
are complete. Reusable source lives under color_code_softoutput/, external
Phase-2A decoder commits are unchanged, and current results are recorded in
../IMPLEMENTATION_STATUS.md. The older implementation guidance below retains
its mathematical contract but does not authorize further simulations or decoder
changes beyond a new user task.

## Project mission

Implement and validate a fixed-color stage-2 swim-distance soft output for the concatenated MWPM decoder of triangular color codes.

The immediate goal is a correct, reproducible data-only/perfect-measurement implementation suitable for numerical experiments and rapid paper preparation.

Correctness has priority over performance. Do not start large simulations until the independent reference tests pass.

---

# Repository responsibilities

## Modified PyMatching backend

Reference:

```text
Zihan-Chen-PhMA/PyMatching
master @ 2abf455ef58ee67c4232e7896e1468e7c983f372
```

Soft-output feature reference commit:

```text
4497499196a30b4fb5e872b9f169866f19bc145e
```

Responsibility:

```text
MWPM growth data
-> residual/contracted graph metric
-> distance between configured logical terminals
```

Do not put color-code-specific geometry or boundary rules into this repository.

## `color-code-stim`

Reference:

```text
seokhyung-lee/color-code-stim
main @ 0eb35935c1e5ff30ba3db9def30a9d35bca2f16d
```

Responsibility:

```text
color-code circuit/DEM
color decomposition
typed stage-2 metadata
resolved color-code terminal classification
ConcatMatchingDecoder integration
simulation output
```

## `AKTKN/concatenated-decoder`

Reference:

```text
main @ 8f817004a5a28a219767f71d048235bd48a5ad9b
```

Do not duplicate core swim code here in Phase 2A. Adapt this package only after the PyMatching + `color-code-stim` interface is stable.

---

# Mathematical contract

Do not change these semantics without reviewing Phase 1.

For the initial standard triangular odd-distance 6.6.6 code, fixed color `c`, one CSS sector, perfect measurements, and fixed stage-1 fiber:

1. Every stage-2 c-only edge corresponds to one physical data qubit.
2. The ordinary stage-2 boundary merges two distinct dangling-edge classes.
3. The classes are:
   - all `d` qubits on the complete physical c-colored side;
   - the unique corner opposite that side.
4. The resolved analysis graph uses:
   - `b_c^0`: c-side terminal;
   - `b_c^1`: opposite-corner terminal.
5. A fixed-fiber difference chain joining the terminals represents the nontrivial physical logical class.
6. A fixed-fiber closed difference chain is stabilizer-trivial.
7. The swim distance is the decoder-cluster-contracted distance between the two terminals.
8. The result is fixed-color/fixed-stage1-fiber only.
9. It is not a full concatenated-decoder logical gap or posterior LLR.

Never rename a per-color swim value as a full logical gap.

---

# Critical software invariants

## Hard decision is read-only to the SO layer

Soft-output computation must not alter the ordinary decoder.

For identical input and tie-breaking:

```text
hard prediction with SO == historical hard prediction
ordinary solution weight with SO == historical solution weight
best color with SO == historical best color
```

If this fails, stop.

## Preserve ordinary solution weight separately

Do not reproduce the reference-fork API behavior that stores swim output in the ordinary `weight` slot.

Return named separate values.

## Preserve edge/error-mechanism identity

The theory is about labelled stage-2 edges. Do not collapse parallel edges or identify an error mechanism only by an endpoint pair when provenance matters.

## No implicit row-order semantics

Do not classify H2 rows from hard-coded positional ranges unless that range is explicitly created and stored by the decomposition layer.

Prefer typed row metadata.

## No unproved circuit-level fallback

The first validated topology is code-capacity/perfect-measurement. Ambiguous circuit-level boundary mechanisms must remain `UNCLASSIFIED` and cannot be silently assigned to a logical terminal.

---

# Preferred `color-code-stim` source architecture

Add a package similar to:

```text
src/color_code_stim/soft_output/
├── __init__.py
├── topology.py
├── pymatching_backend.py
├── reference.py
└── results.py
```

Semantics:

```text
topology.py
    typed H2 row/edge metadata
    code-capacity logical terminal classification

pymatching_backend.py
    adapter to modified PyMatching
    static matcher/topology cache
    structured stage-2 decode result

reference.py
    independent slow Phase-1 metric implementation
    validation/testing only

results.py
    dataclasses / output schema
```

Exact file names can differ for a strong organizational reason, but do not mix physical topology classification into the generic C++ matching backend.

---

# Initial experimental definition

Use the following first correctness/pilot setting:

```python
ColorCode(
    d=d,
    rounds=1,
    circuit_type="tri",
    cnot_schedule="tri_optimal",
    noise_model=NoiseModel(bitflip=p),
)
```

`NoiseModel(bitflip=p)` injects data bit flips at the start of every round, so `rounds=1` is the cleanest single-layer validation.

If repeated perfect-syndrome memory rounds are studied later, label them separately. Do not describe `rounds>1` with repeated bit-flip injection as a single code-capacity error layer.

---

# Output contract

For ordinary non-comparative three-color decoding with swim enabled, expose explicit per-shot fields:

```text
color_order
stage2_weights_by_color
swim_distances_by_color
selected_swim_distance
best_colors
```

Recommended shapes:

```text
stage2_weights_by_color : (shots, 3)
swim_distances_by_color : (shots, 3)
selected_swim_distance  : (shots,)
```

`selected_swim_distance` is exploratory. It is not a theorem-level full-decoder gap.

Keep the existing comparative-decoding `logical_gaps` field under its current meaning.

---

# Implementation workflow

Read `IMPLEMENTATION_REPORT.md`, `INTEGRATION_PLAN.md`, and `TEST_PLAN.md` before source changes.

Milestones are gated:

```text
M0 baseline reproduction
M1 generic PyMatching SO API cleanup
M2 independent residual-metric reference
M3 typed color-code stage-2 topology
M4 ConcatMatchingDecoder integration
M5 small-code mathematical validation
M6 pilot numerics
M7 paired comparative-gap analysis
```

At each milestone:

1. run specified tests;
2. record exact commands/results;
3. review the diff for semantic changes;
4. update `IMPLEMENTATION_STATUS.md`;
5. do not continue if a correctness gate fails.

---

# PyMatching-specific instructions

The reference fork adds `gap_dijkstra/dijkstra_graph.cc/.h` and API methods such as:

```text
SO_calculator_setup
add_boundary_node_SO
add_boundary_edge_SO
add_cycle_endpoints_pair_SO
decode_batch_soft_output
```

Treat these as prototypes, not final API contracts.

Before extension:

1. separate ordinary solution weights from SO values;
2. validate internal growth/radius semantics against `reference.py`;
3. audit parallel-edge behavior;
4. audit boundary-half-edge identification;
5. audit reset between shots;
6. add dedicated tests.

Do not redesign Sparse Blossom itself unless required by correctness.

---

# `color-code-stim`-specific instructions

Relevant files include:

```text
src/color_code_stim/decoders/concat_matching_decoder.py
src/color_code_stim/dem_utils/dem_decomp.py
src/color_code_stim/dem_utils/dem_manager.py
src/color_code_stim/graph_builder.py
src/color_code_stim/simulation/simulator.py
```

The stage-2 decoder currently builds a new `pymatching.Matching` from H2 on each call.

First make the SO implementation correct. Then cache static matchers/topologies for the standard non-custom DEM path.

Do not silently cache `custom_dem_data` without an explicit cache key/invalidation rule.

`DemDecomp` should be the primary source of typed stage-2 row/error metadata. Use Tanner geometry as an independent validation source.

---

# Comparative-decoding comparison policy

The paper needs a fair comparison with conventional comparative decoding.

Do not compare independent physical Monte Carlo samples as the primary plot.

Target workflow:

```text
sample physical shots once
        |
        +-> ordinary concat MWPM + swim
        |
        +-> comparative decoder + comparative logical gap
```

First verify that both pipelines can consume a common detector/observable representation. If comparative decoding changes the circuit/DEM detector representation, implement/document a correct pairing strategy rather than assuming equivalence.

Compare confidence methods primarily at matched retained-shot fraction.

---

# Future circuit-level compatibility

Preserve:

```text
detector coordinates including time
physical/virtual row role
stage-2 edge/error mechanism provenance
original DEM mapping
boundary role
```

Use an extensible boundary-role representation containing at least:

```text
C_SIDE
OPPOSITE_CORNER
TEMPORAL_INITIAL
TEMPORAL_FINAL
OTHER
UNCLASSIFIED
```

Phase 2A validates only `C_SIDE` and `OPPOSITE_CORNER`.

Do not automatically group temporal boundary edges into the spatial terminals.

---

# Performance policy

Do not optimize before correctness.

After correctness:

- cache matchers and topology;
- use batch C++ APIs instead of Python per-shot loops;
- benchmark setup separately from per-shot overhead;
- return path witnesses only in debug mode unless needed for analysis.

Keep slow reference/debug paths until paper data and validation are frozen.

---

# Documentation policy

For every new confidence-related API or comment, distinguish:

```text
theory-guaranteed behavior
implementation convention
future extension
```

Do not claim:

- full-decoder LLR;
- full comparative-gap equivalence;
- circuit-level validity;
- Union-Find equivalence;

unless those results are separately established.

---

# Acceptance criteria for Phase 2A implementation

The first implementation is acceptable only if:

1. modified PyMatching passes baseline tests;
2. hard decisions and ordinary solution weights are unchanged;
3. production SO agrees with independent reference tests;
4. d=3,5,7 boundary classifications pass for all colors;
5. terminal path witnesses have zero syndrome and nontrivial logical parity;
6. batch decoding has no stale-state dependence;
7. `color-code-stim` exposes per-color swim values under `full_output`;
8. a small code-capacity pilot is reproducible;
9. outputs record exact repository commit hashes.
