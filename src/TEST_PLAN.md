# Test Plan: Color-Code MWPM Swim-Distance Integration

Large numerical simulations must not start until the correctness tests through Stage 5 pass.

---

# Stage 0 — Baseline and build tests

## 0.1 PyMatching fork baseline

Before modification:

- build the inspected PyMatching fork from source;
- run all existing C++ tests;
- run Python tests if present;
- run the included surface-code `SO_example`;
- record exact commit and build configuration.

Pass condition:

```text
baseline build/tests succeed
surface-code soft output produces a finite/reproducible output
```

## 0.2 `color-code-stim` baseline

Before modification:

- editable-install the exact inspected commit;
- run `pytest`;
- run a seeded triangular memory experiment;
- save hard predictions and ordinary weights as fixtures.

Suggested fixture:

```text
d=3
rounds=1
circuit_type="tri"
cnot_schedule="tri_optimal"
NoiseModel(bitflip=p)
fixed seed
small shot count
```

---

# Stage 1 — Generic PyMatching API regression tests

## 1.1 Hard-decision invariance

For several small graphlike problems, compare ordinary and SO-enabled decoding.

Require identical hard predictions for:

- single shot;
- batch;
- graph with/without boundary;
- several configured analysis terminal pairs.

## 1.2 Ordinary solution-weight invariance

The ordinary MWPM solution weight from the new SO API must exactly match the existing `decode(..., return_weight=True)` or `decode_batch(..., return_weights=True)` output.

This specifically prevents the reference-fork behavior in which the SO value overwrites the ordinary weight slot.

## 1.3 Setup/invalidation semantics

Exercise:

- `Matching.from_check_matrix`;
- DEM construction if supported;
- graph mutation before/after SO setup.

The implementation must either rebuild explicitly or reject stale SO configuration. Silent stale topology is not acceptable.

## 1.4 Batch state reset

Decode the same shot:

- alone;
- first/middle/last in a batch;
- after another syndrome;
- in reversed batch order.

The soft output must be identical. This catches stale radii/residual weights/discovered-node state.

## 1.5 Zero-syndrome case

With zero growth, verify that phi equals the original terminal-to-terminal shortest path unless a zero-weight path already exists.

## 1.6 Cluster joining both terminals

Construct a case whose covered region connects both terminals. Verify `phi=0` while retaining an expandable physical/path witness in the reference implementation.

## 1.7 Unsupported negative weights

If the metric assumes nonnegative original weights, negative weights must produce a clear validation error or use a separately verified implementation. Never silently clip original negative weights.

---

# Stage 2 — Residual-metric correctness

Compare the production backend with an independent Python reference.

## 2.1 Hand-computable line graphs

Use small line/tree graphs with several supplied growth radii and verify exact residual distances.

## 2.2 Partial-edge coverage

Use the diagnostic case:

```text
edge weight = 5
covered length from endpoint u = 1
covered length from endpoint v = 2
expected residual = 2
```

This prevents Boolean whole-edge zeroing.

## 2.3 Alternative zero-cost route

Construct a cluster that connects the endpoints of an edge through another route while the direct edge interior is not fully covered.

Verify:

- direct-edge residual length is not incorrectly forced to zero;
- quotient/shortest-path metric still sees the correct zero-cost alternative route.

## 2.4 Randomized small graphs

Generate many small connected positive-weight graphs with valid supplied growth data and two terminals. Compare production versus reference phi for many seeds.

## 2.5 Multiple terminal pairs

Configure multiple endpoint pairs and verify independent distances. This exercises the generic backend beyond one surface-code assumption.

---

# Stage 3 — Color-code topology tests

Test at least:

```text
d in {3,5,7}
c in {r,g,b}
```

## 3.1 Stage-2 graphlike columns

For the initial code-capacity/perfect-measurement model, assert that each relevant H2 column has one or two nonzero rows. Any higher-degree column must be explained or rejected.

## 3.2 Row-role completeness

Every H2 row must have exactly one typed role:

```text
PHYSICAL_C_DETECTOR
STAGE1_VIRTUAL
```

## 3.3 Boundary class counts

For each color, require:

```text
count(C_SIDE)          == d
count(OPPOSITE_CORNER) == 1
```

and the classes must be disjoint.

## 3.4 Geometry cross-check

Using `TannerGraphBuilder` independently, verify:

- every `C_SIDE` half-edge maps to a data qubit on the c-colored physical side;
- `OPPOSITE_CORNER` maps to the unique corner not on that side.

Repeat for all colors.

## 3.5 Error/edge provenance

Verify the stage-2 error mechanism metadata used by the SO analyzer maps exactly to the intended H2 column and to the stored original-DEM mapping.

## 3.6 Permutation robustness

Permute H2 rows and columns while consistently permuting metadata. Topology classification and phi must be invariant up to relabeling. This prevents accidental reliance on row ordering.

---

# Stage 4 — Decoder integration regression tests

## 4.1 SO disabled

Modified `color-code-stim` with SO disabled must reproduce baseline:

- predictions;
- best colors;
- ordinary weights;
- seeded logical-failure mask.

## 4.2 SO enabled

On identical shots, require:

```text
prediction(SO on) == prediction(SO off)
best_color(SO on) == best_color(SO off)
ordinary_weight(SO on) == ordinary_weight(SO off)
```

Only new metric fields may be new.

## 4.3 Output shapes

For ordinary all-color decoding:

```text
stage2_weights_by_color.shape == (shots, 3)
swim_distances_by_color.shape == (shots, 3)
selected_swim_distance.shape == (shots,)
```

Also test single-color and color-subset calls.

## 4.4 Single-color direct comparison

Decode one color through the outer decoder and directly through the stage-2 SO backend. The phi arrays must agree.

## 4.5 Empty-shot/filter paths

Exercise code paths yielding no remaining shots. New result arrays must retain consistent empty shapes.

## 4.6 `custom_dem_data`

If not initially supported, SO + custom DEM must raise an explicit `NotImplementedError` rather than use stale cached topology.

---

# Stage 5 — Small-code mathematical validation

## 5.1 Independent d=3 resolved graph

Construct the resolved c-only graph independently from physical geometry and compare:

```text
vertex count
edge count
C_SIDE edges
OPPOSITE_CORNER edge
edge/error labels
weights
```

## 5.2 Terminal-to-terminal logical witness

For every color, obtain a shortest terminal path, map its stage-2 edges to physical support, and independently verify:

```text
physical syndrome = 0
logical parity = 1
```

## 5.3 Closed-chain witness

Generate representative fixed-fiber closed chains and verify:

```text
physical syndrome = 0
logical parity = 0
```

## 5.4 Brute-force d=3 fixed-fiber representatives

For selected d=3 syndromes, enumerate feasible stage-2 chains and identify minimum representatives in both logical classes.

Compare:

```text
ordinary MWPM baseline weight
opposite representative weight
production phi
reference phi
```

When the production growth data satisfy the exact certificate assumptions used in Phase 1, verify

\[
W_{\rm opp}^{(2)}-W_{\rm base}^{(2)}\ge\phi_c.
\]

If the backend does not yet supply the required certificate convention, mark this check not-applicable rather than claiming the theorem was numerically validated.

## 5.5 Logical-class tie case

Construct a tiny case with equal minimum representatives in both classes. Under certified assumptions, verify `phi=0`.

---

# Stage 6 — Monte Carlo sanity tests

These are diagnostics, not theorem tests.

## 6.1 Baseline LER preservation

Run old versus new hard decoder on the exact same sampled shots. The failure mask must be exactly equal when SO is observational only.

## 6.2 Metric range

For connected code-capacity graphs:

```text
phi_c >= 0
phi_c finite
```

for all shots.

## 6.3 Correct/failure separation

On a moderate pilot dataset, inspect broad trends such as median phi for failures versus successes. Do not encode strict monotonicity of every noisy histogram bin as a unit test.

## 6.4 Statistics pipeline unit test

Test binning, Wilson intervals, and post-selection calculations on synthetic data with known counts.

---

# Stage 7 — Comparative-gap paired tests

## 7.1 Shared physical shot identity

Sample physical detector/observable outcomes once and ensure both metric pipelines can be associated with the same shot IDs.

## 7.2 Hard-decision labels

Record separately:

```text
actual observable
baseline prediction
comparative prediction
baseline failure
comparative failure
```

Do not assume comparative decoding has the same hard decision as ordinary decoding.

## 7.3 Metric naming

Serialized outputs must distinguish:

```text
swim_distance
comparative_logical_gap
```

## 7.4 Matched-yield comparison

Test post-selection utilities by sorting on each confidence and retaining equal fractions. The primary comparison is conditional LER versus acceptance fraction.

---

# Stage 8 — Circuit-level readiness tests

These tests protect metadata, not a circuit-level theorem.

## 8.1 Time-coordinate preservation

Build a circuit-level triangular memory DEM and verify that stage-2 metadata retains detector time coordinates.

## 8.2 Safe boundary roles

Every circuit-level half-edge must be explicitly classified or marked `UNCLASSIFIED`. No default should map all half-edges to a spatial logical terminal.

## 8.3 Refusal test

Until a circuit-level topology rule is implemented and validated, requesting the logical swim metric with unresolved temporal roles must fail clearly.

---

# Stage 9 — Performance tests

Measure separately:

1. matcher construction;
2. topology/SO setup;
3. ordinary batch decode;
4. SO-enabled batch decode;
5. incremental SO overhead.

Test multiple distances and record:

```text
shots/s
microseconds/shot
peak memory
one-time setup time
```

Verify matcher/topology caching avoids per-call reconstruction.

---

# CI recommendation

Fast CI on every implementation commit:

```text
generic API regression
hand/reference metric tests
d=3 topology all colors
d=3 decoder integration
batch state-reset test
```

Extended local/release gate:

```text
d=3,5,7 topology all colors
random graph property tests
d=3 brute-force validation
small Monte Carlo regression
performance smoke test
```

Large numerical jobs should not be CI tests.
