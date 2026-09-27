# Codex Task: Implement Phase-2A MWPM swim distance for the concatenated color-code decoder

We are beginning the numerical/implementation phase of the color-code swim-distance project.

First, explore this project directory and understand directory structure, then write(update) in AGENTS.md.

Your task is to implement the first validated MWPM version carefully, with correctness gates before numerical scaling.

Before modifying any code, read:

- `AGENTS.md`
- `IMPLEMENTATION_REPORT.md`
- `INTEGRATION_PLAN.md`
- `TEST_PLAN.md`

Also read the current Phase-1 theory note supplied with the project in `/home/quantum_teresheys/workspace/color_code_softoutput/notes`. The implementation must respect its scope and definitions.

The target quantity is a fixed-color, fixed-stage-1-fiber stage-2 swim distance. Do not reinterpret it as a confidence metric already proved for the complete three-color concatenated decoder.

---

# Repositories

## PyMatching soft-output reference fork

```text
https://github.com/Zihan-Chen-PhMA/PyMatching.git
```

Inspected reference state:

```text
branch: master
commit: 2abf455ef58ee67c4232e7896e1468e7c983f372
```

Original soft-output feature commit:

```text
4497499196a30b4fb5e872b9f169866f19bc145e
```

## Color-code implementation

```text
https://github.com/seokhyung-lee/color-code-stim.git
```

Inspected reference state:

```text
branch: main
commit: 0eb35935c1e5ff30ba3db9def30a9d35bca2f16d
```

## Later compatibility target

```text
https://github.com/AKTKN/concatenated-decoder.git
```

Do not modify this third repository during the first implementation campaign unless explicitly requested later.

---

# General working rules

1. Record the actual checked-out commit hashes before changing anything.
2. Work on dedicated branches/worktrees.
3. Do not modify upstream history.
4. Run baseline tests before source edits.
5. Keep an `IMPLEMENTATION_STATUS.md` with files changed, tests, results, and unresolved issues.
6. Stop at a failed correctness gate; do not continue merely to finish the feature.
7. Prefer small explicit tests over broad assumptions about graph geometry.
8. Do not start large numerical simulations in this task.

---

# Milestone 0 — Reproduce baseline behavior

## PyMatching

Build the reference fork and inspect the full soft-output data path.

Run existing tests and the included surface-code SO example.

Document:

- how `region_that_arrived_top`, region radius, and wrapped radius enter SO;
- how boundary half-edges are identified;
- whether parallel edges are distinguishable throughout the SO graph;
- how SO state is reset between shots;
- where the normalising constant is applied;
- which methods are called before blossom shattering.

Do not rely only on comments; trace the source and tests.

## `color-code-stim`

Install editable and run the existing test suite.

Create a deterministic baseline fixture using a small triangular code, for example:

```python
ColorCode(
    d=3,
    rounds=1,
    circuit_type="tri",
    cnot_schedule="tri_optimal",
    noise_model=NoiseModel(bitflip=p),
)
```

with fixed seed and a small batch.

Record:

```text
hard prediction
best color
ordinary solution weight
logical-failure mask
```

Do not modify source until these baselines succeed.

---

# Milestone 1 — Clean the generic PyMatching SO API

The current reference fork is a prototype. Refactor it so SO-enabled decoding returns three distinct products:

```text
hard prediction
ordinary MWPM solution weight
soft-output value(s)
```

Do not overwrite the ordinary solution weight with the soft output.

Requirements:

- SO remains optional;
- historical decode APIs retain their old meaning;
- setup/invalidation behavior is explicit and consistent;
- batch state is fully reset between shots;
- more than one terminal pair can be represented;
- topology configuration is generic;
- no color-code-specific logic is added to PyMatching.

Audit the current boundary-edge API. The existing prototype assumes a special `nullptr` neighbor position. If this is safe only for a unique half-edge at a node, encode that restriction explicitly and test it.

Audit parallel-edge handling. If endpoint-based lookup can lose the identity of multiple physical error mechanisms, fix or generalize the analysis representation before depending on it for color-code DEMs.

Add dedicated C++/Python tests.

Exit condition:

```text
surface-code SO example still works
ordinary prediction unchanged
ordinary solution weight unchanged
SO returned separately
```

---

# Milestone 2 — Independent Phase-1 metric reference

Implement a small, slow Python reference calculator independent of the production SO backend.

Given:

```text
explicit weighted resolved graph
supplied growth radii / interval coverage
logical terminal pair
```

compute the exact residual contracted metric and terminal distance.

Include tests for:

- zero growth;
- partial edge coverage;
- cluster touching one terminal;
- cluster touching both terminals;
- alternative zero-cost route;
- randomized small weighted graphs.

In particular include a partial-edge example where an edge of weight 5 has coverage 1 and 2 from its endpoints, so its residual length is 2.

Compare production C++ SO output against this independent reference.

If they disagree, stop. Determine whether:

- the C++ implementation is wrong;
- the Phase-1 metric and the current Sparse-Blossom radius convention differ;
- or extra internal growth information is necessary.

Do not proceed to color-code integration until this is resolved and documented.

---

# Milestone 3 — Typed stage-2 metadata in `color-code-stim`

Inspect and modify as needed:

```text
src/color_code_stim/dem_utils/dem_decomp.py
src/color_code_stim/dem_utils/dem_manager.py
src/color_code_stim/graph_builder.py
```

Add stable typed metadata for stage 2.

At minimum preserve:

```text
H2 row role: PHYSICAL_C_DETECTOR or STAGE1_VIRTUAL
source detector/virtual id
stage-2 column/error id
original DEM error id/provenance
stage-2 endpoint row ids
available x/y/t coordinates
```

Do not let downstream code infer semantics from current row ordering.

Create a clean soft-output package, preferably:

```text
src/color_code_stim/soft_output/
```

with modules for topology, PyMatching adaptation, reference calculation, and result dataclasses.

For the first perfect-measurement triangular implementation, classify each one-ended stage-2 edge as:

```text
C_SIDE
OPPOSITE_CORNER
```

using row-role provenance.

Then independently validate it against `TannerGraphBuilder` geometry.

For every

```text
d in {3,5,7}
c in {r,g,b}
```

require:

```text
count(C_SIDE) == d
count(OPPOSITE_CORNER) == 1
```

and verify the physical qubit positions.

If these checks fail, stop and repair the topology model.

---

# Milestone 4 — Integrate swim output into `ConcatMatchingDecoder`

Modify the decoder minimally and keep the default path unchanged.

Add an opt-in option such as:

```python
compute_swim_distance=True
```

or an extensible equivalent.

For each color:

1. run the existing stage-1 decode;
2. form exactly the same stage-2 input as the existing decoder;
3. use exactly the same H2 and stage-2 weights;
4. run the SO-enabled stage-2 matcher;
5. receive separately:
   ```text
   stage-2 prediction
   ordinary stage-2 solution weight
   phi_c
   ```

Do not compute a second hard correction inside the SO postprocessor.

Once correctness works, cache one configured stage-2 matching object/topology per color for the standard non-custom DEM path.

Do not silently cache arbitrary `custom_dem_data`.

Under `full_output=True`, expose at least:

```text
color_order
stage2_weights_by_color
swim_distances_by_color
selected_swim_distance
```

Recommended shapes for normal three-color decoding:

```text
stage2_weights_by_color : (shots, 3)
swim_distances_by_color : (shots, 3)
selected_swim_distance  : (shots,)
```

Do not call `selected_swim_distance` a logical gap.

Required regression:

```text
SO off hard result == historical result
SO on hard result  == SO off result
SO on ordinary weight == SO off ordinary weight
```

for fixed seeded shots.

---

# Milestone 5 — Small-code mathematical validation

Before any large Monte Carlo run, validate d=3 and then d=5.

Build an independent resolved c-only graph and compare:

- graph size;
- stage-2 edge/error labels;
- c-side terminal edges;
- opposite-corner terminal edge;
- edge weights.

For selected syndromes:

1. compute production `phi_c`;
2. compute independent reference `phi_c`;
3. extract a shortest terminal path;
4. map it back to physical error support;
5. verify physical syndrome zero;
6. verify nontrivial logical parity.

For d=3, brute-force fixed-stage2-fiber chains where feasible.

If, and only if, the production MWPM growth data satisfy the exact certificate assumptions used by the Phase-1 bound, verify

\[
W_{\mathrm{opp}}^{(2)}-W_{\mathrm{base}}^{(2)}\ge\phi_c.
\]

If the backend does not provide the required certificate convention, do not claim this theorem has been numerically validated. Record the exact missing condition.

---

# Milestone 6 — Pilot numerical experiment

Only after Milestones 0–5 pass.

Start with the clean data-only setting:

```python
ColorCode(
    d=d,
    rounds=1,
    circuit_type="tri",
    cnot_schedule="tri_optimal",
    noise_model=NoiseModel(bitflip=p),
)
```

Use a small grid such as d in {3,5,7}, a few physical error rates, and moderate shot counts suitable for pipeline validation rather than final paper statistics.

Save per-shot data including:

```text
shot id
d
p
actual observable
predicted observable
failure flag
best color
stage2 weights r/g/b
phi_r/phi_g/phi_b
selected phi
repository commit hashes
```

Generate diagnostics:

- swim-distance distribution;
- distribution conditioned on success/failure;
- conditional LER versus swim distance;
- post-selection LER versus acceptance rate;
- runtime overhead.

Review the pilot before scaling shots.

---

# Milestone 7 — Paired comparison with comparative decoding

The project also needs comparison to existing comparative decoding/logical gap.

Build a paired-shot workflow rather than independent simulations.

The desired conceptual flow is:

```text
sample physical shots once
        |
        +-> ordinary concatenated MWPM + swim
        |
        +-> comparative decoding + comparative logical gap
```

First verify that both decoder configurations can be associated with the same physical detector/observable shot identity.

If comparative decoding modifies the circuit/DEM detector representation, solve and document the mapping/pairing problem explicitly before comparing metrics.

Compare primarily:

```text
conditional LER vs retained-shot fraction
```

at matched acceptance/discard fractions. Do not compare raw thresholds directly because the metrics have different scales.

---

# Circuit-level readiness constraint

Do not implement or claim the final circuit-level swim topology in this task.

However, preserve enough metadata for it:

```text
detector coordinates including time
physical/virtual row role
error-mechanism provenance
original DEM mapping
boundary role
```

Use an extensible boundary-role representation with at least:

```text
C_SIDE
OPPOSITE_CORNER
TEMPORAL_INITIAL
TEMPORAL_FINAL
OTHER
UNCLASSIFIED
```

For circuit-level DEMs, ambiguous half-edges must remain `UNCLASSIFIED`. Do not automatically merge temporal boundary mechanisms into the two spatial logical terminals.

---

# Required test gates

Use `TEST_PLAN.md` as the acceptance specification.

Before the pilot experiment, at minimum pass:

- baseline regression;
- hard-decision invariance;
- ordinary-weight invariance;
- batch state-reset tests;
- independent residual-metric tests;
- d=3,5,7 boundary classification for all colors;
- physical logical witness test;
- d=3 brute-force/reference test where feasible.

Add dedicated test files rather than hiding validation in notebooks.

---

# Deliverables from this Codex task

Produce:

1. modified PyMatching source on a dedicated branch/worktree;
2. modified `color-code-stim` source on a dedicated branch/worktree;
3. new/updated unit tests;
4. `IMPLEMENTATION_STATUS.md` containing:
   - exact repository SHAs;
   - source files changed;
   - completed milestones;
   - commands/tests and results;
   - unresolved issues;
5. a reproducible pilot script/config;
6. pilot result files only if all correctness gates pass.

Do not launch the large paper-scale numerical campaign in the same task.

Stop after the pilot and report the implementation state for review.
