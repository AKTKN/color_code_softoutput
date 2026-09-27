# Implementation status

## Monotone-Y simulation and analysis integration — 2026-09-19

Implemented the user's follow-up with a new thin notebook,
`notebooks/monotone_y_getting_started.ipynb`, and reusable modules
`src/color_code_softoutput/experiments/monotone_y_test.py` and
`src/color_code_softoutput/analysis/monotone_y.py`. It uses ordinary
`color_code_so` and the existing feature adapter in an isolated namespace.
No decoder/metric source, installed package, original notebook or prior result
was modified. The reference notebook's d=9,13,15; p=.04/.05; 1M shots/point;
eight workers; batch size 2,000; seed 0 are copied into the new notebook.
Sampling starts disabled. No six-million-shot study was launched.

Each physical shot saves ordinary/comparative signed monotone-Y scores on
their final physical corrections, paired forced gap, each hard decoder's
failure label, correction weights and minimizing root/template diagnostics.
Version is `monotone_y_signed_v1`. Shared bounded scheduling, atomic Parquet,
source snapshots and all-point first-batch replay are reused. Hard outputs
are checked before/after scoring. Shared analysis now accepts both named
monotone-Y scores for distributions, conditional LER/logistic fits,
post-selection, matched retention and quantitative reports. The empty
near-threshold configuration is displayed as unavailable instead of causing
a plotting error. Long monotone-Y legends use two columns to avoid clipping.

Validation in `/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python`:

```bash
python -m pytest tests/phase2b/test_monotone_y_experiment.py -q
# 7 passed (38.98 s)
python -m pytest tests -q
# 185 passed (189.88 s), including the new integration tests
python -m pytest \
  tests/phase2b/test_monotone_y_experiment.py::test_analysis_matches_raw_counts_and_tie_policies \
  tests/phase2b/test_path_gap_experiment.py::test_analysis_and_matched_retention -q
# 3 passed (41.17 s), after the final legend-only correction
```

The bounded run is
`results/20260919_120559_210504_monotone_y_test`: d=9,13,15; p=.04/.05;
128 shots/point; batch size 64; two workers; seed 0; **768 shots in 12 batches**.
Sampling took about 14.1 s. Initial audit passed with exact source match;
all six first-batch replays matched exactly. The final replay still passes.
Only `analysis/postselection.py` changed afterward for the legend layout;
this source drift is explicitly recorded. The original sampling snapshot is
preserved, with final plotting sources separately archived in
`analysis_source_snapshot.zip` and `analysis_source_hashes.json`.

All **11 executable notebook cells** run successfully against those saved
shots in `color_code_so` with sampling disabled. PDF/PNG distributions,
conditional LER/parameter plots, post-selection curves, Parquet count/fit
and matched-retention tables, and `monotone_y_comparison/REPORT.md` are saved.
The distribution and corrected post-selection renderings were inspected.
The two-point subthreshold grid correctly reports insufficient crossing/
scaling coverage. Smoke counts validate the workflow, not calibration or
post-selection superiority; theory claims remain unchanged.

Usage: `notes/support/MONOTONE_Y_EXPERIMENT.md`. Logs, notebook/reference
hashes and the acceptance manifest:
`notes/support/monotone_y_experiment_evidence/`. Enable
`RUN_NEW_EXPERIMENT=True` in the new notebook for the configured full study,
or also set `SMOKE=True` for 128 shots/point. Existing path-gap/SWIM datasets
lack this score; select a new monotone-Y run.


## Selectable path-gap v1/v2 — 2026-09-19

`run_experiment(config, metric_version="v1")` subtracts the full physical
correction weight; `"v2"` keeps path-overlap subtraction. Both canonical names
are accepted, with the same selector available in `sample_batch` and CLI
`--metric-version`. The notebook selects v1; API/CLI defaults remain v2.
Parallel workers, metadata, schema validation and new-run replay follow the
selected version. External sources and existing results are unchanged.

Acceptance: `color_code_so/bin/python -m pytest
 tests/phase2b/test_path_gap_experiment.py
 tests/phase2b/test_path_gap_comparison.py -q`: **21 passed (55.82 s)**.
Notebook schema/code compilation, CLI help and read-only loading of existing
v1/v2 runs also pass. Only bounded test fixtures were sampled; notebook sampling
settings were preserved and no full study was run. Details: `STATUS.md` and
`notes/support/PATH_GAP_EXPERIMENT.md`.

## color_code_so path-gap compatibility — 2026-09-19

The ordinary environment now runs path-gap without installs or switching:
`conda activate color_code_so`, then the existing CLI or notebook. The notebook
kernel is `color_code_so`. The loader uses feature metric/config sources under
a private namespace while preserving the installed SWIM decoder/PyMatching.
Provenance captures both source trees and the actual active backend Git state.

Validation: `color_code_so/bin/python -m pytest tests -q`: 162 passed, no skips.
CLI smoke `--smoke --workers 2` saved 7,680 shots to
`results/20260919_001816_473771_path_gap_test/`. All fields except run ID match
the prior upstream-environment smoke exactly. All ten notebook code cells
execute in the ordinary kernel with replay enabled for all 60 saved batches.
Both SWIM repos and the feature worktree remain unchanged.

## Path-gap Getting Started experiment — completed 2026-09-19

Entry point: `notebooks/path_gap_getting_started.ipynb`; reusable code:
`src/color_code_softoutput/experiments/path_gap_test.py` and
`src/color_code_softoutput/analysis/path_gap.py`. Reproduction/environment
instructions: `notes/support/PATH_GAP_EXPERIMENT.md`.

Acceptance commands:

```bash
/tmp/color-code-path-gap-env/bin/python -m pytest tests/phase2b/test_path_gap_experiment.py -q
# 5 passed
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest tests -q
# 158 passed, 3 feature-environment skips
/tmp/color-code-path-gap-env/bin/python -m color_code_softoutput.experiments.path_gap_test --smoke --workers 2
# results/20260918_235857_951358_path_gap_test; 7,680 physical shots, 60 batches
```

`analysis.path_gap.audit_run(PathGapDataset(run_directory), replay=True)` passes
with exact replay of all 60 batches and no source drift. The final notebook's
ten code cells execute using nbclient and kernel `color-code-path-gap`, with
replay enabled in memory for acceptance. Notebook sampling and replay defaults
remain False. Whole-threshold curves and matched-retention tables are saved;
all scores are signed and associated with their own decoder's failure labels.
Only the smoke was run, not the default 6-million-shot study. All three
external worktrees are unchanged and clean. No new theorem or significant
post-selection performance improvement is claimed from these small counts.

## Comparative correction-origin analysis — completed 2026-09-18

`circuit_level.experiment` now provides a public-control replay of all six
comparative candidates, using `logical_value` and single-color decoding without
editing `external_libs/color-code-stim`.  It stores a separate strict-schema
Parquet sidecar per original batch with the six weights, baseline/forced logical
classes, their minimizing colors and weights, and the reconstructed gap.
`analysis.circuit_level` validates every sidecar against stable shot identities,
the saved comparative prediction and the saved gap before counting same versus
different colors.  The CLI is
`python -m color_code_softoutput.experiments.comparative_color_origin RUN`.

The existing 300,000-shot p=.003 run was replayed from its 600 saved seeds, not
resampled as a new statistical experiment.  Same-color/different-color results:
overall 185,549/114,451 (61.85%/38.15%); d=3 84,131/15,869; d=5
55,667/44,333; d=7 45,751/54,249.  Sidecars occupy 22 MiB under
`comparative_candidates/`; `comparative_correction_color_summary.parquet` holds
the aggregate table.  Original shot shards and both external repositories are
unchanged.  The final Getting Started cell invokes this analysis.  Validation:
99 circuit tests and all 156 main-project tests pass.

## Selected-color SWIM/forced-gap scatter — completed 2026-09-17

The final cell of `notebooks/circuit_level_getting_started.ipynb` now plots the
ordinary-decoder-selected branch's SWIM distance against the paired comparative
forced gap, grouped by code distance, with a black dotted `y=x` line. The cell
derives the selected value directly from `ordinary_selected_color` and the three
per-color columns, then asserts exact agreement with `selected_swim_distance`.

The cell is self-contained with respect to loading: it reuses `dataset` when
available and otherwise opens the configured saved run. It passes both a fresh-
kernel standalone execution and a full 11-code-cell notebook execution under
`color_code_so` using the existing 300,000-shot run. No simulation, decoder,
stored result, or shared analysis API was changed.


## Three-color output-selection analysis — completed 2026-09-16

New notebook:
`notebooks/circuit_level_swim_selection_strategies.ipynb`. New reusable module:
`src/color_code_softoutput/analysis/swim_selection.py`. The read-only adapter
derives selected-color, min, max or mean from the three stored per-color SWIM
columns while preserving stable shot IDs and `ordinary_logical_error`. For the
selected-color strategy it checks exact equality with the stored
`selected_swim_distance`.

Each strategy receives its own distribution, conditional-LER and post-selection
figure/table directory. Existing rounding, YlGn palette, 99% Wilson bands,
whole-tie thresholds, figure style and distance selections are reused. Plot
titles and score-axis labels identify the aggregation; post-selection legends
remain compact because the strategy is already the title.

Validation: 28 targeted tests pass, one sampling integration test deselected;
the complete main-project suite passes **155 tests in 81.70 s**.
The output definitions, input immutability, invalid inputs, identity/failure
association, selected-score reconstruction, isolated artifacts and all twelve
plot paths are checked. All nine notebook code cells execute on the existing
300,000-shot run without sampling. Executed notebook and logs are under
`implementation_artifacts/circuit_level/`; analysis artifacts are under
`implementation_artifacts/circuit_level/swim_output_selection/20260916_212315_582740_circuit_level_memory_test/`.

This task authorizes an empirical aggregation comparison only. It does not
change production selection, prove one strategy optimal, or identify any score
as a full logical gap, LLR or calibrated posterior.


## Wilson interval shading — 2026-09-16

Updated the main package's conditional-LER, post-selection (swim and forced
comparative gap), and Lee physical-error-rate plots to use series-colored
Wilson confidence bands with alpha=.2. Conditional/physical-rate markers are
retained; Wilson error bars are replaced by bands. Fitted-parameter intervals
are not Wilson intervals and keep their previous rendering. Numerical bounds,
rounding and stored shot values are unchanged. Zero-failure upper bounds are
shaded too, with zero lower bounds clipped by logarithmic axes.

Validation: 21 targeted plotting/statistics checks pass, with the simulation
integration test deselected. Saved-data rendering and zero-failure rendering
checks are recorded in `implementation_artifacts/circuit_level/wilson_bands*`.
No new sampling or external decoder edits.


## Circuit notebook plotting follow-up — 2026-09-16

User-requested `round_digits` is available on `SwimDistanceDistributionPlotter.plot`,
`ConditionalLERAnalyzer.plot`, `PostSelectionAnalyzer.plot`, the statistical
helpers, and `standard_memory_analysis`. The notebook shares one setting,
initially None. Integers apply Python round to actual values, before groups,
fits or thresholds. Auto grouping preserves every rounded value even above
64 unique scores. Explicit histogram bins remain explicit. Raw values remain
unchanged; rounded ties are kept whole for both swim and forced gap. Rounded
plots/counts/fits use separate `_roundN` filenames.

Shared palettes are now YlGn for swim and Blues for forced gap, at .4,.7,.95
for three series. Scatter remains o/x with alpha=.75. No external source or
simulation changes. The user's 100,000-shot settings and enabled run toggle
were preserved; validation did not execute that simulation cell.

Validation: 21 targeted plotting/statistics tests pass (one simulation-bearing
integration test deliberately deselected). Notebook plot cells 7–9 are exercised
on the saved 6,000-shot validation with None and 1; the standard wrapper is
exercised with 0. Artifacts/logs are under
`implementation_artifacts/circuit_level/plot_rounding*`. No new samples are drawn.
Source notebook: `notebooks/circuit_level_getting_started.ipynb`.


## Surface-code companion — completed 2026-09-16

User-requested simulation modules, scripts and notebook now live under
`surface_code_test/`; [README](surface_code_test/README.md) and
[validation report](surface_code_test/VALIDATION.md) provide usage and evidence.
The notebook is the surface counterpart of the circuit-level Getting Started
workflow and uses the same statistics and figure style. It provides swim
histograms, conditional LER and paired postselection including complementary gap.
The current generic PyMatching SO API uses the example's X-boundary topology;
complementary gap is abs(W1-W0) on the actual ordinary graph after a checked
label gauge. Both scores share ordinary hard decisions and physical shots.

29 new tests pass; tiny exhaustive and actual integer-program gap oracles,
independent interval metric, frozen example, state reset and data/plot gates
pass. A 6,000-shot run (d=3,5,7; explicit rounds=2d; p=.001; 2,000/point)
completed in 32.79 s including setup/audit/plots; sampling/decoding/storage was
14.29 s. Full raw audit and 750-shot saved-seed replay pass. Hard mismatches:0.
Ten notebook code cells execute. Run:
[surface_code_test/results/20260916_202936_323053_surface_code_memory](surface_code_test/results/20260916_202936_323053_surface_code_memory/metadata.json).
The 8,1,0 failure counts require caution about empirical tails; no ranking is
asserted. The zero-failure plotting case is handled explicitly.

Both external commits/branches remain unchanged and clean; all surface source,
notebook and artifacts are under the requested directory. No shared color-code
source changed. Growth certification remains false, with no new sampling
campaign or open-boundary/sliding-window extension beyond this validation.


## Circuit-level closed-memory implementation — completed 2026-09-16

The active prompt is now
[prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md](prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md).
Full current report: [notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md](notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md).
This supersedes the historical Phase-2B status below only within closed-memory scope.

- New modular package: `src/color_code_softoutput/circuit_level/`.
- Runner: `experiments/circuit_level_memory_test.py`; shared analysis adapter:
  `analysis/circuit_level.py`; notebook: `notebooks/circuit_level_getting_started.ipynb`.
- Baseline repaired: 264 Python passes, two upstream skips; final: **362 passes,
  two skips**, 110.44 s; unchanged C++ suite: **95 passes**. Frozen surface and
  code-capacity regressions pass. The old d=3 validator failure is resolved;
  missing `sinter==1.16.0` is installed and recorded in `environment.yml`.
- Run: [results/20260916_182739_909527_circuit_level_memory_test](results/20260916_182739_909527_circuit_level_memory_test/metadata.json),
  6,000 paired physical shots, 24 shards, d=3,5,7, rounds=d, p=.003,
  three workers, batch 250, seed 20260916. Setup 2.7855 s;
  sampling/decoding/growth replay/storage 42.5960 s, excluding audit/plots.
- Raw and archived-source audits pass; 750 saved shots replay exactly.
  200 ordinary failures, 200 comparative failures, 22 hard disagreements;
  **zero swim on/off hard mismatches**. Each metric retains its own failure label.
- All nine static graphs are balanced; 18,000 cut branch-shots, zero cover
  branch-shots. Cover/brute-force and cut/cover tests pass; no all-distance claim.
- External repos unchanged/clean on `phase2a/swim-distance`: PyMatching
  `83cee05cc16d6fce9deafdbbf7952b4b96a7f21e`, color-code-stim
  `ba6f7dc8b7aaab237d98ad5f08825be4225864c6`. Root remains non-Git.
- `swim_bound_certified=False`; actual effective DEM and original-graph growth
  convention remain explicit. Selected score is the ordinary selected branch.

All 10 notebook code cells execute without errors; three standard PDF/PNG plot
pairs and three verified witness examples are saved. The integrated 40-page
note builds without LaTeX warnings or unresolved references.

Logs and executed notebook are in `implementation_artifacts/circuit_level/`.
Exact commands and full topology table are in the linked report. No production
external changes, sliding windows, threshold campaign or new color aggregation.
Next task: separately authorized sliding-window/open-temporal-boundary integration.


Historical Phase-2B task: `src/CODEX_PHASE2B_GETTING_STARTED_NUMERICS_PROMPT.md`, explicitly
authorized with the `color_code_so` Conda environment. External decoder commits
remain unchanged and clean at 83cee05 (PyMatching) and ba6f7dc (color-code-stim).
The main workspace remains non-Git; per-file source hashes replace a main SHA.

Environment: installed Python 3.12.14 into the previously empty `color_code_so`
Conda environment; rebuilt both editable external packages with DEBUG=0 and
installed the new main package. The notebook kernel is `color_code_so`.
The historical `.venv-phase2a` is retained as provenance, not used for Phase 2B.

Current gate: 238 existing Python tests passed with two upstream skips in the
Conda environment. The 23 new tests passed, covering configuration, pairing,
selected-color semantics, Parquet, parallel equivalence, synthetic statistics,
fit degeneracy and every plot family. A style side-effect failure was repaired
before sampling: rsmf formatter construction switches the global backend, so
dimensions are queried in an isolated cached subprocess. Publication rendering
uses the real installed TeX stack; no typography fallback is implicit.

New source is entirely under `src/color_code_softoutput/`; packaging is in
`pyproject.toml`, environment instructions in `environment.yml` and the package
README. Thin orchestration: `notebooks/phase2a_getting_started.ipynb`.
New tests: `tests/phase2b/`. Smoke: `results/20260912_145105_phase2a_test`, 48,000 paired shots, 48 shards,
8.60 s, four workers. Independent raw-data audit and replay passed. Throughput
projects about 14 minutes for the requested full grid, which is reasonable.
The 24 new tests include source-archive integrity and schema-hash rejection.
The moderate run is complete; see the final Phase-2B record immediately below. Atomic shard writes are implemented; resume is
explicitly deferred rather than silently stitching incomplete runs.

## Phase-2B completed result

Output: [results/20260912_145540_phase2a_test](results/20260912_145540_phase2a_test/FINAL_REVIEW.md).
Report: [PRIOR_WORK_REPRODUCTION.md](results/20260912_145540_phase2a_test/PRIOR_WORK_REPRODUCTION.md).
The grid is d=3,5,7,9,11,13 and p=.02,.03,.04,.05,.076,.080,.084,.088.
There are 100,000 shots at each of 48 points: **4,800,000 paired shots**, four
workers, 5,000-shot batches, 960 Parquet shards. Simulation took **93.58 seconds**;
initial independent audit plus standard analysis took **41.75 seconds**.
The exact seed is 20260912 with the recorded SeedSequence batch recipe.

All raw-shard invariants and independent totals pass: 208,918 ordinary and
205,479 comparative failures; 33,491 hard-decision disagreements retain separate
labels. Selected swim, comparative alias, finite/nonnegative confidence values,
identities, exact counts, source states and a full 5,000-shot replay pass.
Main source hashes match the saved ZIP snapshot. Both external commits remain
unchanged and clean on phase2a/swim-distance:

- PyMatching: `83cee05cc16d6fce9deafdbbf7952b4b96a7f21e`.
- color-code-stim: `ba6f7dc8b7aaab237d98ad5f08825be4225864c6`.

**Final tests: 262 passed, two upstream skips** (238 existing plus 24 new).
All notebook cells executed under the `color_code_so` kernel; the source notebook
stays thin and output-free, with the executed copy under implementation_artifacts.
Nineteen PDF/PNG figure pairs include the standard analyses and notebook examples.
Representative threshold/scaling/distribution/conditional/postselection figures
were visually inspected. Final figure tests also treat layout warnings as errors.

The main all-distance crossing estimator reaches p=.088, the upper grid endpoint:
**no interior threshold is resolved**. Post hoc larger-distance sensitivity gives
.086458 (d>=7) and .085660 (d>=9), documented separately from the primary result.
Subthreshold G(d) and C(d) slopes are .4547 and 1.165, with 99% intervals
[.2303,.6790] and [.4455,1.8847]. These are broadly compatible with published
.488 and 1.30. Only one failure at d=13,p=.02 limits that fit. Do not claim exact
historical reproduction, posterior calibration or a certified swim bound.

Reusable source inventory (all under src/color_code_softoutput):

- `simulation/config.py`, `sampling.py`, `pairing.py`: fixed grid, seed recipe,
  single-sample pairing and selected-color/alias checks.
- `simulation/parallel_runner.py`, `storage.py`, `provenance.py`: bounded CPU
  scheduling, atomic typed Parquet, source archives and environment manifests.
- `experiments/phase_2a_test.py`: CLI/imported runner and structured RunResult.
- `analysis/dataset.py`, `selection.py`, `statistics.py`: projected dataset access,
  metric/failure semantics, shared selection, Wilson/logistic conventions.
- `analysis/figure_style.py`: isolated rsmf dimensions, scoped TeX units and palettes.
- `analysis/prior_work.py`, `swim_distribution.py`, `conditional_ler.py`,
  `postselection.py`: reusable plots, tables and explicit fit statuses.
- `analysis/audit.py`, `workflow.py`: independent raw validation/replay and
  standard figure orchestration. Package init files and README complete the API.

Other deliverables: pyproject.toml, environment.yml,
notebooks/phase2a_getting_started.ipynb, tests/phase2b/test_configuration_sampling.py,
tests/phase2b/test_analysis.py, and synchronized project-state documentation.
No third repository, Phase-1 proof or external decoder implementation changed.

Reproduction from the project root:

```bash
conda activate color_code_so
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg
python -m pytest tests external_libs/PyMatching/tests external_libs/color-code-stim/tests -q
python -m color_code_softoutput.experiments.phase_2a_test --smoke --shots 1000 --workers 4 --batch-size 1000
# After smoke review:
python -m color_code_softoutput.experiments.phase_2a_test --shots 100000 --workers 4 --batch-size 5000
```

Load the returned run directory with Phase2ADataset, then call audit_run and
standard_analysis, as shown in the notebook. New runs use new timestamped folders;
existing results are not overwritten. Resume remains explicitly deferred.

Logs and frozen environment exports are under implementation_artifacts/phase2b:
conda_baseline_tests.log, new_tests_before_full.log, figure_review_regression.log,
final_tests.log, smoke_run.log, moderate_run.log, moderate_audit_analysis.log,
notebook_execution.log, pip_freeze.txt and color_code_so_environment.yml.

**Stop here.** This completes the authorized Phase-2B study. The unresolved
all-distance crossing and missing optimal-dual certificate remain visible for
review; no larger grid, circuit-level topology or later extension was started.

## Plot-scale follow-up — 2026-09-12

The default y-axis is now logarithmic for swim-frequency, conditional-LER and
post-selection plots. Saved result tables still retain zero observed rates and
their Wilson intervals; only zero-valued artists are omitted from a logarithmic
axis. The Fig. 3 near-threshold view remains linear by design; its sub-threshold
companion remains log-log. Signed coefficient plots remain linear because their
values can be negative. The revised code passed all 24 Phase-2B tests. Updated
publication-style previews from the completed dataset are in
`implementation_artifacts/phase2b/log_y_preview/`; historical run figures were
left intact with their original source snapshot.

## Post-selection threshold follow-up — 2026-09-12

User-requested analysis change: `postselection_curve` now emits one row per
exact unique metric threshold, sorted ascending. Retain scores >= threshold;
abort scores < threshold. Cumulative failure counts include complete ties,
with no rounding or binning. The minimum threshold is the no-abort point.
The returned/saved table now includes `threshold`. Plots show all positive-rate
points with circle markers connected by lines (solid swim, dashed forced gap),
removing the previous 1000-point cap. Zero rates remain in tables with intervals.

Validation command:

```bash
conda run -n color_code_so python -m pytest tests/phase2b/test_analysis.py -q
```

Result: **11 passed, 1 failed**. Exact threshold counts and Wilson intervals
were checked against direct threshold masks, including ties, shot permutations,
and adjacent floating-point values. Both plotted metrics preserve all 1005
synthetic thresholds with markers and lines. The existing
`test_all_plot_families_and_metric_labels` fails during configuration, before
plotting: its d=3 fixture is excluded by the current `DISTANCES=(5,7,9,11,13,15)`.
The simulation configuration and existing study outputs were not modified.

---

# Phase-2A implementation status

Authorized 2026-09-12 by `src/CODEX_PHASE2_IMPLEMENTATION_PROMPT.md`.
Acceptance specification: `src/TEST_PLAN.md`. Work stops at failed
correctness gates; no paper-scale campaign or circuit-level swim is allowed.

## Repositories and environment

The workspace root is not a Git repository. Both external checkouts were
clean before work, and dedicated `phase2a/swim-distance` branches were created.

| Repository | Actual starting HEAD | Cited source reference |
|---|---|---|
| PyMatching | `2fe1b19cabeb05afd073b9ffed20242264f8ca20` | `2abf455ef58ee67c4232e7896e1468e7c983f372` |
| color-code-stim | `3f9f2d447bebdedb43e7d43adee47d2c9fce4afd` | `0eb35935c1e5ff30ba3db9def30a9d35bca2f16d` |

Each actual HEAD adds only two README lines to the cited reference; source
and tests therefore match. No upstream history was changed. The third
repository is untouched.

Environment: `.venv-phase2a`, Python 3.12.7, NumPy 1.26.4, CMake 3.31.10,
Ninja 1.13.2. Full dependency versions are recorded in the pilot manifest.
Build uses `DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=4`. The first install attempt
failed because the inherited `DEBUG=release` is not accepted by prototype
`setup.py`; this is an environment issue, retried without source changes.

## Milestones

- M0–M5: passed before pilot sampling; certificate-bound validation is explicitly not applicable without the required dual data.
- M6–M7: completed and audited; 3,072 paired shots across six configurations.
- Final verification: 95 C++ tests and 238 Python tests passed, with two upstream skips.
- Stopped at the requested pilot-review boundary. No large campaign was run.

Both dedicated branches are committed and clean:

| Repository | Final implementation SHA |
|---|---|
| PyMatching | `83cee05cc16d6fce9deafdbbf7952b4b96a7f21e` |
| color-code-stim | `ba6f7dc8b7aaab237d98ad5f08825be4225864c6` |

The sections below retain the source trace and milestone history; the final
pilot section records the completed deliverable.

## Baseline source trace

All paths below are relative to `external_libs/PyMatching/`.

- `src/pymatching/sparse_blossom/driver/mwpm_decoding.cc`:
  `decode_detection_events_soft_output` runs `process_timeline_until_completion`,
  then `SoftOutput`, then shatters blossoms/extracts ordinary matches. It
  finally overwrites the extracted weight with SO (line 252). The 2D variant
  similarly overwrites its outputs. This is a prototype API defect M1 must fix.
- `gap_dijkstra/dijkstra_graph.cc` under `src/pymatching/sparse_blossom/`:
  local radius is zero if `region_that_arrived_top` is null; otherwise it is
  `radius.y_intercept() + wrapped_radius_cached`. `reweight` subtracts both
  endpoint local radii from internal edges, clips at zero, and subtracts
  only the detector radius on a boundary half-edge.
- Boundary attachment requires `neighbors[0] == nullptr`. `MatchingGraph::add_boundary_edge`
  (`flooder/graph.cc:60`) enforces a unique half-edge and inserts it first.
  However `UserGraph::to_matching_or_search_graph_helper` already reduces
  parallel boundary edges to the minimum-weight one. This API addresses a
  detector, not an original error-mechanism ID, so it cannot recover discarded
  physical mechanisms. Explicit labelled analysis edges are needed.
- `mwpm_to_dijkstra_graph` tests `boost::edge(source,target)` before insertion,
  and `add_edge_from_mwpm_to_graph` searches by endpoint. Thus distinct parallel
  mechanisms are not distinguished by this analysis representation.
- `SoftOutput` initializes distances, reweights, computes the minimum over
  configured pairs, then calls `reweight_reset`. Reset restores local radii
  and neighbor flooded weights for flooded nodes and refreshes their incident
  analysis edges. Dijkstra distances are reset after each pair. Exception
  paths do not provide an equivalent reset guarantee.
- `user_graph.pybind.cc` divides the returned integer value by
  `mwpm.flooder.graph.normalising_constant` once per shot. The Dijkstra
  normalizer member is used in debug printing, not ordinary SO return.
- `UserGraph::SO_calculator_setup` rebuilds the analysis graph by calling
  `mwpm_to_dijkstra_graph`, which appends to `nodes` without clearing it;
  repeated setup and graph invalidation need regression coverage.

This trace is implementation evidence, not a verification that raw fill-region
radii satisfy the Phase-1 boundary-normalized optimal odd-cut certificate.

## Commands and artifacts

Logs are in `implementation_artifacts/baseline/`.

```bash
python -m venv .venv-phase2a
.venv-phase2a/bin/python -m pip install 'numpy<2' 'cmake<4' ninja setuptools wheel pytest stim sinter
DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=4 .venv-phase2a/bin/python -m pip install --no-build-isolation -e external_libs/PyMatching -e external_libs/color-code-stim
```

Changed project documentation: `AGENTS.md`, `IMPLEMENTATION_STATUS.md`.

The missing pinned `pybind11` submodule was initialized with
`git -C external_libs/PyMatching submodule update --init --recursive` at
`964c49978f7e7227f2968c359f4f05255d2b54f4`; no source patch was needed.
Both editable packages built successfully. Baseline results so far:
color-code-stim 42 passed / 2 upstream skips; d=3 fixture 64 shots, seed
20260912, p=0.05, 4 failures. The actual included surface example's main and
sampler ran with a bounded collector (64 seeded shots instead of one billion),
producing finite outputs identical on repeated decoding. Saved data and
summaries are in the baseline directory. `scripts/phase2a_baseline.py`
reproduces these runs. PyMatching's first Python run passed 85 / skipped 13
due to optional rustworkx; installing that dependency to exercise all tests.

## M0 passed

- `pymatching_tests`: 92 passed, no ASan/UBSan findings in the test log.
- PyMatching Python suite with rustworkx installed: 98 passed, no skips.
- color-code-stim: 42 passed, 2 upstream unsupported-mode skips.
- Seeded color baseline and bounded surface example passed as above.
- C++ build uses `implementation_artifacts/pymatching-build`, Release,
  GCC 11, source-provided AddressSanitizer/UndefinedBehaviorSanitizer/coverage
  flags on the test target. Its pinned Stim/GoogleTest sources are retained
  in the build directory's `_deps`.

```bash
.venv-phase2a/bin/cmake -S external_libs/PyMatching -B implementation_artifacts/pymatching-build -DCMAKE_BUILD_TYPE=Release -DPYTHON_EXECUTABLE="$PWD/.venv-phase2a/bin/python"
.venv-phase2a/bin/cmake --build implementation_artifacts/pymatching-build --target pymatching_tests -j 4
(cd external_libs/PyMatching && ../../implementation_artifacts/pymatching-build/pymatching_tests)
.venv-phase2a/bin/python -m pytest external_libs/PyMatching/tests -q
.venv-phase2a/bin/python -m pytest external_libs/color-code-stim/tests -q
.venv-phase2a/bin/python scripts/phase2a_baseline.py
.venv-phase2a/bin/python scripts/phase2a_baseline.py surface
```

## M1 implementation

New generic API: `SoftOutputConfig` and `decode_batch_with_soft_output` return
`predictions`, `solution_weights`, `soft_outputs`, and optional debug `radii`.
One output column is returned per configured terminal pair. Configuration
stores every explicitly labelled analysis edge, including parallel mechanisms;
node maps associate analysis vertices with matcher vertices or -1 for terminals.
The hard graph and its historical edge-merge policy are unchanged.

Convention: read final radii at original syndrome centers before blossom
shattering, including their wrapped radii, rescale to ordinary weight units,
and propagate the corresponding metric balls on the explicit analysis graph.
This convention is named explicitly and is **not** an exported/verified
nonnegative optimal odd-cut certificate. M2 must independently check geometry.

Analysis data are local to each shot. No second hard correction is computed.
Mutation invalidates setup; repeated setup replaces topology. SO is explicit
across constructors. Negative original matching/analysis weights are rejected.
The old prototype methods retain their existing tuple meaning for compatibility,
with that unusual meaning documented; their internal ordinary weight is now
kept separate instead of overwritten. Existing surface SO values remain equal
to the M0 fixture.

Files changed in PyMatching:
- `CMakeLists.txt`
- `src/pymatching/matching.py`, `src/pymatching/soft_output.py`
- `src/pymatching/sparse_blossom/driver/mwpm_decoding.cc` and `.h`
- `src/pymatching/sparse_blossom/driver/user_graph.cc`, `.h`, `.pybind.cc`
- `src/pymatching/sparse_blossom/gap_dijkstra/metric_graph.h`, `.test.cc`
- `tests/matching/soft_output_test.py`

Checks so far: 105 Python tests passed; frozen surface fixture, hard prediction,
ordinary weight and finite separate SO all passed on 64 shots. This includes
multiple pairs, reordered/repeated/single/empty batches, >64 observables,
boundary-free matching, setup invalidation, invalid inputs, labelled parallel
edges and the weight-5 partial-coverage example. The final legacy signature cleanup passed all 95 C++ tests. Stale generated gcov profiles were
removed before rebuilding; their timestamp warning is a coverage-artifact issue.

Build development loop (after successful baseline editable install):

```bash
.venv-phase2a/bin/cmake --build implementation_artifacts/pymatching-build --target _cpp_pymatching -j 3
cp implementation_artifacts/pymatching-build/_cpp_pymatching.cpython-312-x86_64-linux-gnu.so external_libs/PyMatching/src/pymatching/
.venv-phase2a/bin/python -m pytest external_libs/PyMatching/tests -q
.venv-phase2a/bin/python scripts/phase2a_check_surface.py
```

## M1–M5 passed, pilot preparation

- Final M1 C++ suite: 95 passed, no sanitizer findings. Python: 105 passed.
- M2 independent reference: 55 passed. The Python oracle explicitly unions
  interval intersections using all-pairs distances, independently of the C++
  propagation implementation. Actual decoding exports the radii for comparison.
- M3: 108 passed / 2 upstream skips including all prior color tests, metric
  tests, all d=3,5,7/color boundary checks, provenance, permutation robustness,
  preserved circuit time metadata, and refusal of unclassified circuit topology.
- M4: 119 passed / 2 upstream skips. Frozen historical fixture, hard result,
  ordinary weights, best color, validity and failure mask match. All-color,
  subset, single-color, direct stage-2, repeated/reordered and empty outputs
  pass. Configured stage-2 matchers are cached only for the standard path;
  custom DEMs are explicitly rejected with SO.
- M5: `tests/test_phase2a_mathematics.py`: 9 passed. Independent Phase-1
  coordinate graphs match edge labels, vertex incidence, terminals and weights
  at d=3,5 for all colors. 48 selected shots per case yield zero-syndrome,
  nontrivial-logical witnesses. All 16 real stage-2 syndromes per color at d=3
  are compared with all 128 physical chains and opposite-class representatives.
  Closed non-c face witnesses also pass. The representative-bound check is
  **not applicable**: no original odd-set dual variables, feasibility proof,
  or exact primal/dual equality are exported. Float/integer normalization
  also does not supply an exact rational certificate.

Implementation clarification to the requested two-row-role specification:
historical H2 contains other-color zero padding rows (e.g. d=3 red H2 is 9x7,
with only four active rows). Labelling these physical-c or stage-1 virtual
would be false. We retain them as `INACTIVE_PADDING`, assert they are zero,
and require one of the two requested roles on every active row. This is a
metadata extension, not a change to H2 or the hard-decoder input. The resolved
analysis graph omits inert vertices and carries an explicit source-row map.

Same-agent source/diff review: ordinary hard decoding still constructs the
same graph/weights and passes the same stage-2 input; SO only reads growth
before the existing extraction. Analysis code never produces a second hard
correction. Exact physical topology and arbitrary-radius geometry are kept
separate from the unavailable certified-bound interpretation.

New color-code source: `soft_output/{topology,reference,pymatching_backend,results}.py`,
package init/README, typed metadata in `dem_utils/dem_decomp.py`, support flag
in `dem_utils/dem_manager.py`, opt-in plumbing in `color_code.py` and
`decoders/concat_matching_decoder.py`. New external test files are
`test_soft_output_reference.py`, `test_soft_output_topology.py`, and
`test_swim_decoder.py`. TannerGraphBuilder required no modification; its
existing physical adjacency/coordinates supply the independent audit.

Paired-workflow preparation: `tests/test_phase2a_diagnostics.py` has 5 passing
tests covering known statistical counts and d=3,5,7 pairing. Comparison of
absolute measurement-record parity sets and physical operations proves that
the extra comparative detector is ordinary observable 0. Converting one
shared measurement batch through both circuits verifies the same mapping.
Flipping the supplied extra bit leaves forced-class decoding unchanged.
No independent simulations are substituted for paired physical shots.

Reproduce added gates:

```bash
.venv-phase2a/bin/python -m pytest external_libs/color-code-stim/tests -q
.venv-phase2a/bin/python -m pytest tests/test_phase2a_mathematics.py tests/test_phase2a_diagnostics.py -q
```

## M6–M7 completed: paired pilot and review

The reproducible configuration is [src/phase2a_pilot.json](src/phase2a_pilot.json).
The runner [scripts/phase2a_pilot.py](scripts/phase2a_pilot.py) samples once per
configuration, validates the ordinary/comparative measurement-parity mapping,
checks SO-off/on invariance, and saves per-shot records before plotting.
The independent artifact audit is
[scripts/phase2a_review_pilot.py](scripts/phase2a_review_pilot.py).

Results: [pilot review](implementation_artifacts/pilot/REVIEW.md),
[raw CSV](implementation_artifacts/pilot/shots.csv),
[manifest](implementation_artifacts/pilot/manifest.json), and
[diagnostic summary](implementation_artifacts/pilot/summary.json).
Six distribution/conditional-LER/retention panels and a runtime plot are saved
alongside them. The manifest records both committed repository SHAs,
dependency versions, script hashes and seeds.

512 shots each at d=3,5,7 and p=0.01,0.05 yielded 3,072 paired rows. All ordinary
hard predictions, weights, selected colors and failure flags were identical
with SO off/on. All per-color swim values were finite and nonnegative.
Ordinary failure counts in grid order were 1,27,1,13,0,6; comparative totals
matched, with two individual prediction disagreements. Retention comparisons
use matched accepted fractions and separate failure labels. The small pilot
does not establish metric superiority or probability calibration.

Isolated stage-2 timing excludes construction and stage 1 in both modes:
observed incremental cost was approximately 0.6–4.4 microseconds per color/shot
on this machine. This is a diagnostic, not a scaling or negligible-overhead
claim. End-to-end timings include different construction/cache behavior and
are identified separately.

The first plotting attempt exposed Wilson-interval endpoint roundoff at zero
failures. Exact endpoint handling and a regression test repaired it; the same
seeded grid was rerun. The incomplete attempt is retained under
`implementation_artifacts/pilot_incomplete_plot_error/`. No decoder correctness
gate failed. The final artifact audit recomputed counts, selected scores,
conditional statistics and acceptance curves from all CSV rows and checked
source/script hashes. One diagnostic panel was visually inspected.

Final test totals: PyMatching 105 Python + 95 C++; color-code-stim 119 Python
+ two upstream skips; independent mathematical tests 9; pairing/statistics
5. Thus 238 Python and 95 C++ tests pass. Detailed logs are retained under
`implementation_artifacts/`.

Reproduction from the installed environment (use an empty output directory):

```bash
.venv-phase2a/bin/python scripts/phase2a_pilot.py --output implementation_artifacts/pilot_reproduction
.venv-phase2a/bin/python scripts/phase2a_review_pilot.py
```

The review script audits the delivered `implementation_artifacts/pilot/`
directory; it performs no additional sampling. Baseline scripts are historical
fixture generators and should not overwrite the saved pre-change fixtures.

Root deliverables additionally include the baseline/surface regression scripts,
`phase2a_diagnostics.py`, both independent test files, this status record, and
updates to all six project-state documents. The theory note is unchanged.

### Remaining limitations and stop boundary

The backend exports final defect-centered metric balls, named
`sparse_blossom_final_defect_metric_balls_v1`. It does not export nonnegative
optimal odd-cut variables with checked feasibility and exact primal/dual
objective equality. Therefore `swim_bound_certified=False`; the Phase-1
representative inequality has not been validated for these production data.
The topology and interval metric are checked independently of that missing
certificate. Three-color selection has no new theoretical guarantee.

Circuit-level swim topology, custom DEM SO, comparative-mode SO, BP/predecoded
SO, calibration and paper-scale simulations remain outside this implementation.
Circuit metadata and unclassified boundary roles are preserved. Practical
certificate extraction remains open. Implementation and bounded pilot are
complete; stop for review before any scaling or later-phase extension.
