# Surface-code path-gap v1 extension — 2026-09-19

Implemented the user-requested global-subtraction metric in the existing
PyMatching C++ batch binding, with its public Python result API. It zeros the
ordinary correction's edges in the original terminal topology, runs Dijkstra,
and subtracts the original floating weight of the FULL correction. SWIM and
ordinary hard decoding remain unchanged. The feature is explicitly versioned
`global_subtraction_v1`; it is a signed heuristic, not an LLR or certified gap.

## Acceptance

In `color_code_so`:

- **117 PyMatching tests pass**, including 12 new path-gap cases: exhaustive
  tiny-graph syndrome/simple-path oracle, disconnected correction contribution
  (`9-20=-11`), zero costs, multiple pairs, merged-edge identity, >64 observables,
  no observables, unreachable paths, impossible-syndrome recovery, invalid
  mapping/weights/input, stale configuration and existing SWIM coexistence.
- **33 surface tests pass**: independent Bellman–Ford checks at d=3,5,7,
  exact ordinary prediction/quantized-weight invariance, reverse/single/empty
  batches, serial/parallel identity, one physical sample per batch, signed
  schema/formula/version checks, legacy two-score loading, audit/replay and all
  five plot outputs.
- **171 main-project regression tests pass**. Color-code-stim is unchanged.
- Native `git diff --check` passes. The source checkout remains locally modified
  on `phase2a/swim-distance` at base `83cee05`; no commit/push was requested.

The first independent surface comparison used bitwise equality for a Python
3.12 compensated sum versus sequential C++ addition. Differences were at most
about 1e-14 in those failures; the independent oracle now uses atol=1e-12.
Production stored formula equality remains exact, as do SO-on/off hard outputs.
The first build inherited `DEBUG=release`; explicitly setting `DEBUG=0` fixed
that setup-script environment issue. No decoder algorithm change was needed.

## Bounded end-to-end run

[Saved run](results/20260919_103105_369356_surface_code_memory/metadata.json):
p=.003, d=3,5,7, explicit rounds=d, 256 shots/distance, 64-shot batches,
three workers, seed 20260919. **768 shots, 12 shards**, ordinary failure counts
1/2/0. Full schema/source/model/count audit passes, including exact saved-seed
replay of one 64-shot batch per distance and zero hard-output mismatches.
Path gap is negative in 21/131/234 shots respectively. This demonstrates
signed storage and the full-correction convention; three total failures do
not support a ranking of post-selection performance.

All **11 notebook code cells execute** on this saved run with sampling disabled.
The executed copy is `artifacts/path_gap_v1_getting_started.executed.ipynb`.
After notebook execution, full current-source and saved-seed audit passes again.
The source snapshot includes native backend files and the notebook. Five
PDF/PNG pairs and count/retention tables are saved. Distribution and combined
post-selection figures were visually checked. The existing 300,000-shot run
loads read-only with its 600 legacy shards; no path gaps were invented for it.
The user's configured 300,000-shot notebook experiment was not launched.

## Commands

```bash
DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=3 conda run -n color_code_so python -m pip install --no-build-isolation --no-deps -e external_libs/PyMatching
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run -n color_code_so python -m pytest external_libs/PyMatching/tests -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run -n color_code_so python -m pytest surface_code_test/tests -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run -n color_code_so python -m pytest tests -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run -n color_code_so python -m surface_code_test.scripts.run_memory --distances 3 5 7 --p .003 --rounds-factor 1 --shots 256 --batch-size 64 --workers 3 --seed 20260919 --analyze
```

Logs: `artifacts/path_gap_v1_{build,backend_tests,surface_tests,main_tests,smoke,notebook}.log`.
The following 2026-09-16 record is historical; its fixed-external restriction
was superseded only for this explicitly requested PyMatching feature.

---

# Surface-code companion validation — 2026-09-16

Completed the requested surface-code version of the circuit-level notebook.
All implementation, scripts, tests, notebook, artifacts and numerical results
are under `surface_code_test/`. Existing color-code source and both external
repositories were left unchanged. Usage and model semantics are in [README.md](README.md).

## Acceptance evidence

**29 tests pass in 22.38 s** in `color_code_so`:

- Exhaustive edge-support enumeration in eight detector-row gauges validates
  both complementary class weights for every syndrome of a tiny graph.
- Independent integer programs on the original actual d=3 incidence/observable
  matrix validate both classes for three physical shots (six forced solves).
  These tests do not use the production label-gauge construction.
- Independent explicit interval-union reference checks validate three actual
  exported-radius swim scores. The full graph retains the example's X-boundary
  interpretation; unsupported half-edge/observable relationships fail explicitly.
- d=3,5,7 checks validate hard SO-on/off identity, forced minimum weights,
  opposite boundary labels, repeated/reversed/single/empty batches.
- The d=5, rounds=10, p=.001 physical circuit exactly equals the frozen baseline
  example; hard predictions match its 64 saved shots.
- Configuration rejection, serial/parallel equality, one physical sample per
  batch, schema/seed corruption rejection, semantic labels/gaps, full saved-run
  audit, source archive checks, plots and exact whole-tie thresholds pass.

The initial plotting test exposed an all-zero-failure log-axis failure. The
surface plotting layer now supplies a valid empty logarithmic frame and a
no-observed-failures annotation; numerical zero counts and confidence intervals
remain in the saved tables. This was fixed before the validation run. Two
subsequent failures were test assertions (schema-rejection wording and boolean
XOR dtype), corrected before the final 29-pass gate.

This is a separate same-agent implementation review with independent numerical
oracles, not external peer review. Existing color-code regressions were not
rerun because their source did not change; their previously recorded totals
remain historical. No new external C++ tests or build was required.

## Saved experiment

Run: [20260916_202936_323053_surface_code_memory](results/20260916_202936_323053_surface_code_memory/metadata.json).

Configuration: rotated X memory, exact unmodified `SO_example` circuit and DEM
parser, p=.001, distances3,5,7, `rounds_factor=2`, 2,000 shots per point, batch250,
three workers, master seed20260916. `rounds` counts explicit `SE_round` calls;
X initialization includes one additional noisy extraction. All samples are
fully terminated. No physical postselection/herald discards or windows occur.

| Distance | Explicit rounds | Shots | Ordinary failures |
|---|---:|---:|---:|
| 3 | 6 | 2,000 | 8 |
| 5 | 10 | 2,000 | 1 |
| 7 | 14 | 2,000 | 0 |

**6,000 shots in 24 Parquet shards**; no hard SO-on/off mismatches. Both
confidence scores use those same hard decisions and failure labels. Static
setup took **5.82 s**; sampling, decoding, paired forced solves and storage
**14.29 s**; setup through final audit/plots **32.79 s**. These timings include
validation overhead and are not a decoder performance comparison.

Static graphs:

| d | Detectors | Ordinary merged edges | X-analysis edges |
|---|---:|---:|---:|
| 3 | 56 | 206 | 182 |
| 5 | 264 | 1,174 | 1,102 |
| 7 | 720 | 3,478 | 3,334 |

All three graphs pass internal logical-label balance. The checked gauge puts
opposite logical labels on the two X boundaries. Coordinate classification is
accepted only after that algebraic check. Every shot's ordinary weight agrees
with the lower forced-class weight and its predicted-class weight within
atol1e-8, rtol1e-10. SO-on/off hard weights and predictions agree exactly.

The full raw audit verifies all shards, identities, seeds, strict schema,
independent counts, ordinary failure labels, both class weights and gap,
source ZIP and model hashes, and unchanged external repository states. One
entire saved 250-shot batch per distance replays exactly: 750 replayed shots,
not additional statistical samples. `audit.json` records the replay tasks.

The three standard PDF/PNG pairs and count tables are saved in the run. All
figures were visually checked. The d=7 plots explicitly report no observed
failures, and zero-rate rows remain in Parquet. Nine total failures are too
few for precision tail comparisons; no performance ranking is inferred.

The source notebook stays thin and output-free. Its executed copy and execution
log are under `artifacts/`; all ten code cells execute using the `color_code_so`
kernel, starting from the notebook directory and loading the saved run.

## Retained interpretation and reproducibility limits

The original physical noise circuit is sampled. Both decoders use the existing
example's retained/merged matching graph, including its DEM decomposition and
unsupported-composite filtering behavior. Complementary gap is the absolute
difference of two minimum matching weights, not a posterior or summed-class
LLR. No actual physical observable value enters either score calculation.

Swim uses the modern generic final-defect metric-ball API and the example's
split X-boundary topology. It is not the historical integer-dB CSV output.
Stored scores remain unrounded natural-log costs; dB display is `10/ln(10)`.
The post-selection table is built from raw exact thresholds before conversion.
`swim_bound_certified=False` throughout. Quantized matching costs and metric
floating weights may differ slightly even when their ideal values coincide.

External sources remain clean on `phase2a/swim-distance`:

- PyMatching: `83cee05cc16d6fce9deafdbbf7952b4b96a7f21e`.
- color-code-stim: `ba6f7dc8b7aaab237d98ad5f08825be4225864c6`.

The root is not a Git repository. The run archives its source files, including
all surface modules/scripts/tests/notebook, shared package sources, and the
example source. There is no automatic resume, threshold sweep, larger sampling
campaign, sliding window or open temporal boundary. Any such extension is a
separate task. The color-code theorem claims are unchanged.

## Commands and logs

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run --no-capture-output -n color_code_so python -m pytest surface_code_test/tests -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run --no-capture-output -n color_code_so python -m surface_code_test.scripts.run_memory --distances 3 5 7 --p 0.001 --rounds-factor 2 --shots 2000 --batch-size 250 --workers 3 --analyze
```

`artifacts/tests_final.log`, `artifacts/validation_run.log`,
`artifacts/notebook_execution.log` and `artifacts/final_audit.log` contain the
final acceptance evidence. The analysis CLI can regenerate all three plots
without new sampling; see README for its invocation.
