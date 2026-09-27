# STATUS.md

## YAML workflow final regression and audit — 2026-09-27

Task 06 regression, README and cleanup audit completed. The canonical YAML
workflow retains one parser, point/run naming implementation, shared seed
recipe and adaptive scheduler. Historical fixed-grid shard experiments remain
separate because their saved-data and analysis schemas differ. The root README
now specifies the full minimal YAML, exact noise/output contracts, adaptive
scheduling, ETA and reproducibility limit. The package README's stale stage
statements and calibration-cap description were corrected. Progress displays
`ETA: estimating...` before all unfinished points have timing estimates.
Scientific soft-output logic and legacy data were unchanged. See
`notes/support/SIMULATION_WORKFLOW_FINAL_AUDIT.md` for architecture, schemas,
formulas and acceptance evidence.

Validation: 246 main tests passed; 61 focused workflow tests passed; 127 local
decoder tests passed with two existing skips. The 32-shot shell example
completed at `results/26_09_27_13_21_20_574e38e7/`. An eight-shot
d=3,5 by p=.001,.002 sweep completed under
`/tmp/color_code_task06_results/26_09_27_13_21_43_2d6fa82b/`. Both runs
have one JSON log, exact point files and no surviving `.buffer/`. No large campaign or
Git history operation was performed.

## YAML workflow runner stage — 2026-09-27

Integrated the validated planner, native-constructor preflight, spawn scheduler,
bounded point storage, single atomic `run_log.json`, CLI, shell command and
tiny example YAML. Points finalize from the result callback as soon as their
shots become contiguous and complete. Historical experiment entry points and
result directories remain unchanged. The 32-shot example completed with an
estimating-to-finite ETA transition; focused end-to-end tests cover 1/2 workers,
ordinary/correlated decoding, all three noise models, verbosity, exact names,
schemas, counts, clean buffers and failure log closure. No campaign or decoder
change was performed.

Validation: `conda run -n color_code_so env PYTHONPATH=src:external_libs/color-code-stim/src python -m pytest tests -q`
passed 246 tests. Focused runner/scheduler tests passed 13 tests. The example
command completed at `results/26_09_27_13_14_30_574e38e7/`.

## YAML workflow storage stage — 2026-09-27

Added bounded main-process point storage in
`src/color_code_softoutput/simulation/workflow_storage.py`, exported via
`simulation.storage.PointStorage`. Out-of-order chunks spool under `.buffer/`;
contiguous rows flush to numbered temporary parts. Finalization streams parts
to explicit two-column per-metric Parquet files, validates schemas, counts,
indices and correlated effect, then publishes and removes `.buffer/`. Legacy
shard storage is unchanged. Focused storage, worker, scheduler and planning
tests pass (56 total); the full root test suite passes (241 tests).
No top-level runner, CLI or campaign was run.

## YAML workflow scheduler stage — 2026-09-27

Added a spawn-based main-process adaptive scheduler with per-point calibration,
EWMA throughput, bounded in-flight jobs, round-robin dispatch, deterministic
chunk seeds, progress and approximate ETA. It streams completed worker results
to a caller callback and writes no files. Synthetic scheduling and real-spawn
tests pass (44 focused; 229 full package). The scheduler formula
and reproducibility limit are in `src/color_code_softoutput/README.md`.
Final Parquet storage and the complete CLI runner remain the next stage. No
large simulation, decoder change, commit or publication was performed.

## YAML workflow worker stage — 2026-09-27

Added an isolated one-chunk worker with a four-entry process-local decoder
cache, same-shot ordinary baseline for correlated decoding, common-prior
weight-improvement and exact failure-prevention metrics. The worker samples
once and returns only bounded per-chunk arrays; it creates no result files.
Public input/output contract is in `src/color_code_softoutput/README.md`.
Tiny worker and local correlated-decoder tests pass (16 total); the combined
planning, sampling, circuit decoder/experiment, worker and correlated-decoder
regression passes 80 tests. Adaptive scheduling and final storage remain the
next stage.

## YAML workflow planning stage — 2026-09-27

Implemented strict YAML parsing, immutable resolved settings/points, exact
native noise mapping, Cartesian sweep expansion, semantic hash and point/run
path naming. Planning rejects option conflicts, unsupported correlated SWIM
requests and path collisions before creating output. No worker, scheduler,
storage, runner or sampling change was made. Focused planning tests: 28 passed;
full main-package suite: 213 passed.
Next stage: worker adapters, preserving current decode and pairing semantics.

## Simulation workflow architecture audit — 2026-09-27

Completed the read-only architecture and local API audit for the planned YAML
simulation workflow. The staged module plan, scientific compatibility gates,
legacy data strategy, and Sinter design references are in
`src/SIMULATION_WORKFLOW_REFACTOR_PLAN.md`. The `color_code_so` environment
confirmed the exact `bitflip`, `depol`, and `uniform` noise constructors.
Correlated candidate selection uses the original stage-2 prior; the decoder
currently rejects correlated decoding with matching-growth SWIM. No workflow
implementation, sampling campaign, or external source edit was performed.
The focused regression initially had 43 passes and one circuit end-to-end
failure because a provenance prompt was absent from its expected path. The
prompt was restored to `prompts/`, and the end-to-end test passes again.

## GitHub source publication — 2026-09-27

Initialized the workspace root as a separate Git repository and published
`AKTKN/color_code_softoutput` publicly on `main`. The initial source commit
`cdea414` contains 129 files (package source, tests, notebooks, prompts and
research notes). `.gitignore` excludes `external_libs/`, saved `results/`,
implementation and surface artifacts, caches, builds, reference PDFs and
source-audit paper text. A staged-content scan found no credential patterns;
the pushed commit and remote `main` matched. See README.md for setup using
the independent decoder forks. No PyPI release was made.

## Color-correlated concatenated MWPM — 2026-09-27

Implemented `codex_color_correlated_decoder_prompt.md` in the currently checked
out `external_libs/color-code-stim/` branch `phase2a/swim-distance`. The
opt-in `enable_colorcorrelated_decoding` flag is exposed through `ColorCode`
and `ConcatMatchingDecoder`. Each logical class now has three baseline and
nine guide-reweighted candidates; the two-guide case uses Boolean OR.
Source provenance is read from aligned decomposition mapping matrices, and
both matching stages rerun with temporary probabilities. Selection and the
comparative logical gap use the original stage-2 prior for every candidate.
The original-DEM correction and existing `best_colors`/`weights` meanings are
preserved. BP/custom DEM and matching-growth swim combinations are rejected.

Validation: `conda run -n color_code_so env PYTHONPATH=src pytest -q tests`
in the external checkout: **127 passed, 2 existing skips**. Focused tests
cover prior conditioning, 12-candidate order, OR guides, common-prior
rescoring, comparative gaps, output validity, erasure recursion, persistence,
and unsupported combinations. A bounded d=3, rounds=3 circuit-noise smoke
also passed with four valid outputs. Commit `57a6155` was pushed to
`origin/phase2a/swim-distance`; no sampling campaign or publication was
performed. A pre-existing comparative `check_validity` false
case on one sampled shot remains identical with the option off and on.

## Circuit DEM-Y metric — completed 2026-09-19

Implemented [the prompt](prompts/codex_circuit_dem_y_gap_integration_prompt.md)
as separate public `CircuitDemYGeometry`, `CircuitDemYGapEvaluator` and
`CircuitDemYGapAdapter` APIs in the existing monotone-Y feature worktree.
The exact error-only DEM maps, offline all-path/cap certificates, two-parity
signed DAGs and exact sparse zero-edge/one-edge/wedge solver are implemented.
The optional C++ kernel uses compact arrays and exact adjacency-mask/sparse
fallbacks; it never scans the Cartesian root triples or invokes a decoder.
Existing code-capacity functionality and ordinary hard decoding are preserved.

Acceptance: **163 package tests passed, two existing upstream skips**; the
existing main-package monotone-Y experiment regression passes **7 tests**.
Independent oracles reproduce 59/329/973 sector columns, d=5 tail counts
511/500/545, all 3,337 d=3 logical supports and 70,755 d=5 cap/head tuples.
A 1,000-shot ordinary d=T=5 example verifies final baselines, hard invariance
and winning witnesses. Native wheel build and isolated wheel smoke also pass.
No stored dataset or notebook was changed; no full campaign was launched.

The [implementation report](notes/support/CIRCUIT_DEM_Y.md) links the runnable
example, API guide, seven-page algorithm/proof PDF, focused tests, exact commands,
setup/memory figures and raw timings. **Native scoring is still slower than
ordinary decoding; the intended wall-clock efficiency advantage is not met.**
Correctness within the retained family does not imply full-gap equality,
posterior calibration, all-distance coverage or post-selection superiority.


## Distinct post-selection markers — 2026-09-19

Post-selection markers now identify the soft-output metric consistently across
all distances and full/expanded views: ordinary monotone-Y `o`, comparative
monotone-Y `^`, forced gap `s`, SWIM `D`, ordinary path gap `v`, comparative
path gap `P`. Colors, line styles, confidence bands and numerical tables are
unchanged. The six monotone-Y smoke figures were regenerated from saved shots;
marker identities and exact equality to the previous tables were checked.
The existing marker/threshold regression was updated for the requested style.
Restart the notebook kernel and rerun plotting cells to refresh inline figures.

## Notebook post-selection zoom — 2026-09-19

Added an expanded-view cell immediately after the three monotone-Y
post-selection plots. Edit `postselection_xlim=(0.0, 0.2)` to set the abort-rate
range for all three comparisons. `PostSelectionAnalyzer.plot(..., xlim=...)`
keeps the existing full-range default and saves zoomed figures/tables under
separate filenames. The new cell was executed on the saved 768-shot smoke;
all three axes match the requested limits and the returned tables exactly
match the original full-range tables. Invalid bounds are rejected. No
sampling or existing notebook settings were changed.

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


## Monotone-Y signed-gap metric — 2026-09-19

Implemented `prompts/codex_monotone_y_gap_integration_prompt.md` after reading
the six state documents and completing the requested theory/logic check.
The pre-implementation audit is
`notes/support/MONOTONE_Y_THEORY_AUDIT.md`. No formulation blocker was found;
the essential separation premise is certified for each compiled geometry,
not inferred from acyclicity or finite random-weight experiments.

New installable package modules live in the isolated worktree
`external_libs/color-code-stim-monotone-y/`, branch `feature/monotone-y-gap`,
base origin/main `0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`. Public API:
`MonotoneYGapGeometry`, `MonotoneYGapEvaluator`, and `MonotoneYGapAdapter` in
`color_code_stim.metrics`. The adapter scores fully assembled `error_preds`
after ordinary or comparative decoding, with the same physical E in all
three signed DAGs. It never calls a decoder or changes a hard correction.
Canonical qids, physical incidence/observable verification, unique error-only
DEM mapping, circuit fault-location evidence, cached local XOR templates,
negative scores, optional physical witnesses and chunked mapping/scoring
are implemented. Existing decoder/path-gap sources, installed packages,
notebook settings and saved results remain unchanged.

Theory: signed costs are W(E xor L)-W(E). The local coordinate certificate
proves all-path tail separation on every accepted geometry; pair partition
and logical validity then justify exact minimization within the declared
monotone-Y family. S_Y upper-bounds correction-relative Delta_E, with
S_Y=Gamma-eta+rho_Y; no unconditional class-gap or posterior claim follows.
Independent geometry/all-path checks pass d=3,5,7,9,15,31. Physical logical
coset enumeration reproduces 8/69/308 distinct Y supports and 7/36/140
covered minimum-weight supports at d=3/5/7. These are finite coverage facts.

Validation, run from the feature worktree:

```bash
PYTHONPATH=src /tmp/monotone-y-venv/bin/python -m pytest -q -rs
# 107 passed, 2 pre-existing rec_stability comparative skips (37.76 s)
PYTHONPATH=src /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python \
  -m pytest tests/test_monotone_y_gap.py tests/test_monotone_y_adapter.py -q
# 65 passed (10.43 s)
```

The temporary venv is derived from color_code_so and locally uses the normal
PyMatching 2.3.1 wheel, without replacing the installed backend. Tests include
all 128 d=3 corrections, unequal/zero weights, direct d=5/7 family enumeration,
physical witnesses, exact class identities, deliberate separation/geometry
failures, DEM permutations/non-error instructions/shifts, final/composed
corrections, unchanged hard outputs, empty/order/cache/immutability behavior
and bounded mapping chunks. The complete existing package suite passes.

The runnable d=7,p=.01,100-shot example (five warm repetitions) measures
about 22.05 us/shot for the core metric on fixed E, 24.28 us/shot including
mapping, 50.51 us/shot for ordinary decode and 106.26 us/shot for comparative
decode. Geometry setup is 12.79 ms (3.72 ms coordinate separation), mapping
and circuit audit 9.24 ms, evaluator setup 1.00 ms. These are small-batch
measurements, not universal speedup or post-selection evidence. Online cost
is O(n) per shot with O(chunk_size*n) workspace; physical rank/incidence
audits and optional all-path reachability have separate non-linear setup costs.

Usage/proofs: `external_libs/color-code-stim-monotone-y/docs/monotone_y_signed_gap.md`.
Exact commands, source hashes, logs, geometry audit and timing:
`external_libs/color-code-stim-monotone-y/docs/monotone_y_validation.md`.
Run `PYTHONPATH=src .../color_code_so/bin/python examples/monotone_y_gap.py`
from that worktree. Adapter scope is one-round triangular Z-memory with one
independent data-X layer; full-gap equality, all-distance minimum-support
coverage, calibration and post-selection competitiveness remain unproved.
No full sampling campaign or branch publication was performed.

## Selectable color-code path-gap v1/v2 — 2026-09-19

Added `metric_version="v1"` / `"v2"` (also canonical version names) to
`experiments/path_gap_test.py:run_experiment` and `sample_batch`, plus CLI
`--metric-version`. V1 subtracts the full physical correction weight W(E)
from each public residual distance; v2 retains returned-path overlap
subtraction. Hard decoder outputs, paired shots, paths and weights are shared.
The API/CLI default remains v2. `notebooks/path_gap_getting_started.ipynb`
explicitly selects v1 and passes that setting to the runner; existing grid,
shot count, seed, workers, True sampling toggle and saved-run path are preserved.
The two changed code cells have stale outputs cleared; other saved figures
remain identified as previous results. No notebook sampling cell was executed.

New runs record canonical metric version and `shot_schema_version=2`, with
actual overlap diagnostics in either mode. `analysis/path_gap.py` loads and
replays either new version using its recorded subtraction rule. Historical
unversioned v1 data retains its old schema and archived-source replay gate.
The external decoder/metric sources and saved result directories are unchanged.
No new mathematical claim or performance comparison is introduced.

Validation in `color_code_so`:

```bash
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest tests/phase2b/test_path_gap_experiment.py tests/phase2b/test_path_gap_comparison.py -q
# 21 passed in 55.82 s
```

Checks cover both formulas on paired shots, unchanged hard outputs/distances,
signed-score fixtures, malformed/mixed versions, serial/parallel equality,
metadata, replay, analysis and legacy schema compatibility. The notebook
passes nbformat validation and all code cells compile; CLI help exposes the
selector. Existing v1 run `20260919_002159_907598_path_gap_test` (2,000 shards)
and v2 run `20260919_082109_498604_path_gap_test` (1,600 shards) both load
read-only. Only small test fixtures were sampled in pytest temporary storage;
no full study was launched. Usage: `notes/support/PATH_GAP_EXPERIMENT.md`.

## Surface-code global-subtraction path gap v1 — 2026-09-19

Implemented `Matching.decode_batch_with_path_gap` in the existing PyMatching
checkout, rebuilt in `color_code_so`. Signed score is original-graph residual
Dijkstra distance minus the entire original-weight ordinary correction; no
SWIM radii or path-overlap subtraction. Separate residual/correction costs and
`global_subtraction_v1` are saved with the paired SWIM and complementary gap.
Surface notebook now includes path-gap distribution/conditional LER and a
three-metric post-selection plot, preserving user sampling settings and legacy
run selection. Legacy two-metric data still loads; no stored run was replaced.

Validation: **117 PyMatching + 33 surface + 171 main tests pass**. New bounded
run `surface_code_test/results/20260919_103105_369356_surface_code_memory` has 768 shots/12 shards,
full audit, 192-shot saved-seed replay and zero hard mismatches. Negative path
gaps are retained. The 300k-shot user study was not rerun. See
`surface_code_test/VALIDATION.md` and `external_libs/PyMatching/docs/path_gap.md`.
PyMatching is locally modified on its existing branch; color-code-stim remains
unchanged. No new theorem, posterior claim or performance ranking is made.


## Forced-gap distribution overlay — 2026-09-19

Added opt-in `include_forced_gap=True` to
`analysis/swim_distribution.py`. The path-gap notebook's fixed-p distribution
cell enables this option; False restores the original view. Blue forced-gap
series use comparative failure labels; green path-gap series use their own
decoder labels. Each metric/parameter series normalizes separately. Returned
counts include `metric` and `failure_column`; tiny floating-point splits use
the existing near-discrete grouping. Raw score units are retained.

The saved-data cell was run on `20260919_082109_498604_path_gap_test` at p=.04,
d=5,7,9,11: 200,000 shots per metric/distance, frequency sums exactly one,
forced-gap level counts 3,4,5,6. New `_with_forced_gap` figures and
`path_gap_with_forced_gap_distribution_counts.parquet` preserve the previous
single-metric files. Notebook preview updated; no sampling or decoder changes.
Analysis suite: 13 passed; the overlay-specific test was rerun after the
legend layout adjustment. See `notes/support/PATH_GAP_EXPERIMENT.md`.

## Returned-path overlap v2 — 2026-09-19

Implemented the user-requested post-Dijkstra subtraction on the existing
`feature/final-correction-path-gap` branch, commit `ab0ac66`. Per-color score
is now D_c(E)-W(E intersect L_c), with the same final physical correction E
in all colors. Edge-ID witnesses retain parallel-edge identity; qubits are
counted once. Nonnegative residual search, igraph path ties, graph construction,
decoder, model gates, caching and input immutability are preserved. All three
postprocessed scores precede minimization; negative scores remain valid.

New API: `overlap_weight_by_color`, `metric_version="path_overlap_v2"`, and
exported `METRIC_VERSION`. `phi_by_color`, `phi`, and `minimizing_color` now
use overlap subtraction; `correction_weight` remains total W(E). The feature
commit includes code, independent oracle/fixture tests, versioned example
outputs and docs. It is committed locally, not merged or pushed.

Validation in unchanged `color_code_so`:
- Feature worktree: `PYTHONPATH=src .../color_code_so/bin/python -m pytest -q`:
  **102 passed, 2 existing skips** (38.50 s).
- Workspace: `PYTHONPATH=src .../color_code_so/bin/python -m pytest tests -q`:
  **170 passed** (130.19 s).
- Fresh 768-row bounded smoke at `/tmp/path-gap-overlap-v2-smoke-20260919`,
  explicitly versioned; no old evaluation output was overwritten or relabelled.
- `git diff --check` clean; original SWIM checkouts unchanged and clean.

The unversioned surrounding workspace also updates the runner/schema, legacy
reader/audit, tests, notebook description and documentation. New runs store
metric version plus `{decoder}_overlap_{r,g,b}`. Saved v1 runs still use their
original schema/formula; replay requires archived v1 source, while
`replay=False` audits saved data. Read-only loading of the user's 4M-shot run's
2,000 legacy shards succeeds. The existing notebook sampling setting and all
stored results/outputs are preserved. No superiority or new theory claim is
made. Details: `external_libs/color-code-stim-path-gap/docs/path_gap_overlap_v2.md`.

## Saved-run post-selection competitiveness — 2026-09-19

Appended quantitative comparison to `notebooks/path_gap_getting_started.ipynb`,
using `analysis/path_gap_comparison.py`. It reports actual abort rate, baseline
and residual LER, reduction rate/factor, retained failures, 99% Wilson limits
and ratios to forced gap. Matched-abort boundary-tie splitting and whole-tie
threshold-budget tables are separate. Zero reference failures give undefined
ratios; fewer than 20 retained failures trigger a diagnostic warning, not a
statistical verdict. No sampling or external decoder changes were performed.

Analyzed the user's completed 4M-shot run
`results/20260919_002159_907598_path_gap_test/`, at the notebook selection
p=.04,d=5,7,9,11 (100,000 shots each). Results and generated report are under
that run's `path_gap_comparison/`. At 10% abort, ordinary/forced residual-LER
ratios are 1.027, 2.630, 1.350, 1.000, with retained-failure counts
421/410, 71/27, 27/20, 8/8 respectively. Thus the score is not uniformly
forced-gap-competitive; rankings depend on distance and abort rate. Equality
at d=11 is low-count point evidence, not established statistical equivalence.
Seven new independent accounting/zero-count/invalid-input tests pass. The
appended notebook cell is tested independently without executing the user's
`RUN_NEW_EXPERIMENT=True` cell; existing cells, settings and outputs are preserved.

## Ordinary color_code_so support — 2026-09-19

The path-gap notebook now runs directly with **Python (color_code_so)**.
No package reinstall, branch merge, external edit or separate environment is
required. The main runner loads the feature's existing metric/config source
in a private namespace while leaving active color_code_stim and PyMatching
imports and package search paths untouched. Spawned workers do the same.
Metadata now distinguishes active decoder/backend provenance from metric-source
provenance, and archives both decoder and metric Python sources.

The complete main test suite passes in `color_code_so` (162 tests, no skips),
including path-gap integration and same-process SWIM/path-gap coexistence.
New smoke: `results/20260919_001816_473771_path_gap_test/`, 7,680 shots / 60
batches. All shot fields except run ID exactly match the original upstream
environment's smoke. The notebook's ten code cells and all 60 replayed batches
are validated in the ordinary environment. The original external repositories
and feature worktree remain unchanged. Old isolated-environment instructions
below are historical; see the updated usage guide for the default workflow.

## Path-gap Getting Started experiment — 2026-09-19

Added [the notebook](notebooks/path_gap_getting_started.ipynb) and reusable
`experiments/path_gap_test.py` / `analysis/path_gap.py` under
`src/color_code_softoutput/`. The current reference notebook's executable
defaults are reproduced: d=5,7,9,11,13,15; ten probabilities; 100,000 shots
per point (6 million total), batch size 2,000, six workers, seed 20260912321.
Only the bounded full-grid smoke was run, not the full study.

Ordinary and comparative decode the same physical shots. Each final
correction receives its own public-package path-gap evaluation. Signed
per-color scores, residual distances, global correction weights, decoder
predictions and distinct failure labels are retained in strict Parquet.
Shared analysis now accepts explicit named metrics while preserving SWIM
defaults. The notebook includes distributions, conditional LER/logistic fits,
prior-work plots, whole-tie threshold post-selection and equal-retention
comparisons. Comparative path-gap vs forced gap supplies a same-hard-decoder
comparison; ordinary path-gap vs forced gap compares complete pipelines.

Acceptance: **5 new tests pass** in the upstream-PyMatching feature environment;
**158 pass, 3 feature-environment skips** in the unchanged original Conda
environment. The smoke at `results/20260918_235857_951358_path_gap_test/`
contains 7,680 physical shots / 60 batches (128 per point), with complete
raw-count audit and exact replay of all 60 batches, no source drift. All ten
code cells of the final notebook execute on saved smoke data, with replay
enabled for acceptance. The notebook default disables sampling and replay.
Both original external repositories and the feature worktree remain clean.

Smoke statistics are not sufficient for performance conclusions. For example,
d=5,p=.04 has 2/128 ordinary failures before selection; the 50%-retained
path-gap sample has 0/64, whose 99% Wilson upper bound is still about 9.39%.
Zero observed failures must not be presented as zero underlying LER.
See [reproduction and usage](notes/support/PATH_GAP_EXPERIMENT.md).

## Final-correction monochromatic path gap — 2026-09-18

Implemented the separately requested
[prompt](prompts/codex_monochromatic_path_gap_prompt.md) in the installable
color-code-stim feature worktree `external_libs/color-code-stim-path-gap/`,
branch `feature/final-correction-path-gap`, based on origin/main `0eb3593`.
The core uses suppressed physical pair/singleton supports and igraph shortest
paths; the postprocessor validates and maps the FINAL DEM correction, applies
it to every color and subtracts its entire original physical weight once.
No earlier SWIM branch was merged and both original checkouts remain fixed.

Acceptance: **99 tests pass, 2 existing skips**, with normal upstream
PyMatching 2.3.1 in an isolated venv derived from `color_code_so`.
Independent all-mask d=3 path enumeration, d=5 incidence/path oracle,
d=3,5,7 physical logical witnesses, final-correction/mapping/cache/scope checks
and statistical-accounting tests pass. The bounded smoke uses exact d=3
probability sums and 256 seeded d=5 shots per decoder cohort. d=3 LER is
0.0164181; d=5 has 1 failure in 256 for each cohort, with wide uncertainty.
No statistically resolved superiority or new gap theorem is claimed.

Source commit `05ccbe4`; saved smoke source includes the plot-only `c147e60`.
See [implementation report](external_libs/color-code-stim-path-gap/docs/path_gap_implementation_report.md),
[usage](external_libs/color-code-stim-path-gap/docs/monochromatic_path_gap.md),
and [metadata](external_libs/color-code-stim-path-gap/examples/path_gap_smoke/metadata.json).
Published to `origin/feature/final-correction-path-gap`, final commit `617d1ce`,
with [draft PR #1](https://github.com/AKTKN/color-code-stim/pull/1) against
AKTKN/color-code-stim:main. The final follow-up normalizes CSV line endings;
all CSV records were checked unchanged. Saved artifact audit verifies 768
rows, all score/threshold formulas, source identity and paired physical shots.

## Comparative correction-origin colors — completed 2026-09-18

The circuit-memory simulation layer can now replay a saved batch and export all
six comparative candidate weights (logical classes 0/1 times colors r/g/b) to
validated sidecar Parquet shards.  The existing external decoder and original
shot Parquet remain unchanged.  The analysis reconstructs the existing
comparative prediction and forced gap exactly, then compares the color attaining
the minimum in the selected baseline logical class with the color attaining the
minimum in the complementary forced class.  Ties follow the decoder's existing
class-then-rgb `argmin` order.

The final cell of
[the circuit-level Getting Started notebook](notebooks/circuit_level_getting_started.ipynb)
calls the reusable analysis and displays overall and per-distance counts and
fractions.  For the configured 300,000-shot run, the colors are the same in
185,549 shots (61.85%) and different in 114,451 (38.15%).  The corresponding
same/different counts are 84,131/15,869 at d=3, 55,667/44,333 at d=5, and
45,751/54,249 at d=7.  Six hundred sidecar shards (22 MiB) and the summary
Parquet were written under the run directory.  All 156 main-project tests pass.

## Selected-color SWIM versus forced-gap scatter — completed 2026-09-17

Appended a plotting cell to
[the circuit-level Getting Started notebook](notebooks/circuit_level_getting_started.ipynb).
It reconstructs each shot's `phi` from `ordinary_selected_color` and the matching
`swim_distance_r/g/b` column, checks exact equality with the stored
`selected_swim_distance`, and plots it against the comparative-decoding
`forced_gap`. The plot distinguishes distances and includes a black dotted
`y=x` reference line with equal axis scales.

The cell also runs independently in a fresh kernel: it reuses `dataset` when
defined and otherwise loads the notebook's configured saved run itself. The
full notebook (11 code cells) executes successfully in `color_code_so` on the
existing 300,000-shot run. No sampling, saved data, decoder, or reusable
analysis code was changed; the scatter is descriptive and adds no gap theorem
or calibration claim.


## Three-color SWIM output-selection notebook — completed 2026-09-16

Added [the saved-data notebook](notebooks/circuit_level_swim_selection_strategies.ipynb)
and reusable [strategy analysis module](src/color_code_softoutput/analysis/swim_selection.py).
They compare selected-color, minimum, maximum and arithmetic-mean scalar scores
using separate distribution, conditional-LER and post-selection plots for each
strategy. All strategies reuse identical physical shots and ordinary hard
failure labels; no experiment is rerun and no hard decoder output changes.

The notebook defaults to the latest completed circuit-memory run and was
executed successfully on the existing 300,000-shot run. It saved 12 PDF/PNG
plot pairs plus count/rate tables in separate strategy directories under
`implementation_artifacts/circuit_level/swim_output_selection/`. Twenty-eight
targeted analysis tests pass; one sampling-bearing integration test was
deliberately deselected, and the complete main test suite passes 155 tests.
These are empirical comparisons only: no optimal
aggregation, full-gap or posterior-confidence claim is introduced.


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


## Plot rounding and palette follow-up — 2026-09-16

Added `round_digits=None|int` to all three circuit-notebook plotting APIs and
`standard_memory_analysis`. Rounding acts on actual scores before groups,
logistic fits and postselection thresholds, including forced gap. None retains
previous numerical behavior; stored shots are unchanged. Rounded output names
are separate. Swim colors now use YlGn(.4,.7,.95) for three ordered series;
forced gap uses Blues. Distribution keeps o/x markers and alpha=.75.
The notebook preserves the user's sampling settings and run toggle; plot-only
validation loads the existing 6,000-shot run without a new experiment.
See `IMPLEMENTATION_STATUS.md` for validation evidence.


## Surface-code circuit-memory companion — completed 2026-09-16

Added the requested [surface workflow](surface_code_test/README.md), with
modules, scripts, tests and a [thin notebook](surface_code_test/notebooks/circuit_level_getting_started.ipynb)
under `surface_code_test/`. It uses the unmodified PyMatching SO_example
rotated X-memory circuit, p=.001 and 2d explicit extraction rounds by default.
Both swim and complementary gap use the same physical shots and ordinary hard
failure labels. The gap comes from two checked forced logical-class solves.

29 surface tests pass. The 6,000-shot validation at d=3,5,7 saves 24 shards,
three PDF/PNG plot pairs and full raw/source/replay audit; zero hard mismatches.
There are 8,1,0 failures respectively, so rare-error plots are explicitly sparse.
Setup 5.82 s; sampling/decoding/storage 14.29 s; through audit/plots 32.79 s.
All ten notebook code cells execute. See [validation record](surface_code_test/VALIDATION.md)
for the run, commands, exact oracle checks and limits. External repositories
and existing color-code sources are unchanged. Growth remains uncertified;
no new theorem, threshold result or sliding-window scope is introduced.


## Closed-memory circuit-level implementation — completed 2026-09-16

Implemented [the requested prompt](prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md).
The [algorithm note](notes/support/circuit_level_swim_algorithm.tex) is integrated
into the 40-page [PDF](notes/note.pdf). Modular source, component tests,
paired simulation, shared analysis and the
[thin notebook](notebooks/circuit_level_getting_started.ipynb) are complete.
**362 Python tests pass, two upstream skips; 95 C++ tests pass.** The earlier
d=3 grid-validation issue is repaired without changing the configured default grid.

Saved [results/20260916_182739_909527_circuit_level_memory_test](results/20260916_182739_909527_circuit_level_memory_test/metadata.json):
6,000 physical shots, d=3,5,7, rounds=d, uniform circuit noise p=.003,
2,000/point, three workers, 24 shards; setup 2.79 s and sampling/decoding/storage
42.60 s. Full raw audit and one 250-shot saved-seed replay per distance pass.
All 6,000 hard results are unchanged. All nine graphs pass internal balance;
18,000 branch-shots use the cut, zero use the cover. The cover is independently
tested against tiny exact oracles. Both external sources remain clean and fixed. All 10 notebook code cells
execute; three standard PDF/PNG figure pairs and verified witness examples
are saved.

See [full implementation report](notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md)
for commands, files, diagnostics, failure counts, review and limits. Growth
remains uncertified (`swim_bound_certified=False`); no new theorem, threshold
claim or aggregation rule is added. Next task is separately authorized
sliding-window/open-temporal-boundary integration. Older milestones below are
historical; their production stop was superseded only for this closed-memory task.


Historical theory milestone: 2026-09-12.

## Circuit-level theory — completed within stated conditions

Implemented the newly authorized
[circuit-level prompt](notes/support/CODEX_CIRCUIT_LEVEL_THEORY_PROMPT.md).
The user's [note](notes/note.tex) now integrates static and circuit-level
parts; supporting source is
[circuit_level_theory.tex](notes/support/circuit_level_theory.tex), with
[readable summary](notes/support/CIRCUIT_LEVEL_THEORY.md).

Proved: typed DEM/observable maps and retained-model syndrome factorization;
fixed-fiber quotient and exact rank criterion; sufficient all-distance final
readout logical witness; algebraic correlation pairing; general binary-cover
minimum with witnesses; conditional two-terminal cut and gauge invariance;
label-preserving interval contraction; exact controlled Phase-1 reduction;
and the representative bound under an exact optimal odd-cut certificate.
The final TeX section specifies the complete executable metadata/decoder pipeline.

Primary literature and current source were audited separately. The paper/code
filtering difference and duplicate-target fallback overwrite have explicit
reproducers; effective-model exactness is not original-noise exactness.
A universal geometric cut and local prism/fault-complex lift remain open.
Current production growth radii remain uncertified; no numerical integration
or sliding-window decoding was performed. The prompt permits these stronger
claims to be explicitly withheld while using the proved general cover.

Validation in `color_code_so`: 400 exhaustive tiny graph cases, including
211 valid cuts, gauge/residual/witness tests and counterexamples; static
all-color d=3,5,7 graph reduction; six fully enumerated d=3 measurement-noise
DEMs at T=1,2 with compatible Stim and logical-map checks. The separate full
circuit-noise matrix-only example is not exhaustive. Review is a separate
same-agent adversarial pass, not external peer review. Reproduction and exact
limits are in [notes/support/README.md](notes/support/README.md) and [REVIEW.md](REVIEW.md).
Both external decoder repositories are unchanged.

The integrated PDF has 39 pages and builds without warnings or unresolved
references. All 15 circuit formal-claim labels and citations resolve; the
cover/cut pages were visually checked. The Phase-1 finite checks also pass.

`AGENTS.md` now places new theoretical task prompts and detailed research
Markdown under `notes/support/`, while retaining the canonical state files
and bibliography at their existing paths. Stop at this theory handoff;
future production integration requires a new task.

The following records retain earlier numerical and theoretical milestones.

## Post-selection threshold follow-up — 2026-09-12

Updated `src/color_code_softoutput/analysis/postselection.py` at the user's
request: every exact unique score is a threshold, accepting scores >= threshold
and aborting scores < threshold. Exact ties stay together, without binning,
rounding or plot subsampling; positive residual-LER points use markers and lines.
Tables include thresholds and retain zero rates with Wilson intervals.
Validation in `color_code_so`: 11 analysis tests passed; one existing integration
test fails before plotting because its d=3 fixture is excluded by the current
`simulation/config.py` distance grid (5,7,9,11,13,15).
Details: [implementation record](IMPLEMENTATION_STATUS.md).

## Phase-2B — completed

Implemented the reusable package under src/color_code_softoutput and the thin
notebook in notebooks/phase2a_getting_started.ipynb. All work uses the
`color_code_so` Conda environment; external decoder commits remain unchanged.
The gated moderate run contains 4.8 million paired shots, 100,000 per point,
four workers, 960 shards, and completed sampling in 93.58 seconds. All raw-data
invariants, source hashes, independent counts and same-seed replay pass.
262 Python tests pass with two upstream skips; all notebook cells execute.

The all-distance crossing objective reaches the upper p=.088 endpoint and
therefore does not resolve a threshold. Exploratory larger-distance subsets
are near .086, while G/C scaling slopes .4547/1.165 are broadly compatible with
the published trends. The d=13,p=.02 point has only one failure. Missing dual
certificates and empirical-fit limitations remain unchanged.

See [implementation record](IMPLEMENTATION_STATUS.md). The historically
referenced study review at
`results/20260912_145540_phase2a_test/FINAL_REVIEW.md` is absent from the
current workspace (checked during the circuit-theory documentation audit).
Stop after this study; no later extension is authorized by the completed prompt.

The following sections retain prior Phase-2A and Phase-1 checkpoints.


## Phase-2A implementation — completed 2026-09-12

The user authorized `src/CODEX_PHASE2_IMPLEMENTATION_PROMPT.md`. The generic
PyMatching API now separates hard predictions, ordinary weights and soft
values; color-code-stim preserves typed stage-2 provenance and exposes opt-in
per-color/selected swim output. Historical hard decisions and weights are
unchanged. Original H2 and inputs are retained, with inactive padding marked
explicitly in metadata. No third repository was modified.

Validation: 95 C++ tests; 105 PyMatching Python tests; 119 color-code tests
with two upstream skips; nine independent d=3/d=5 mathematical checks;
five pairing/statistics tests. These include d=3,5,7 boundary geometry in
all colors, randomized interval metrics, physical logical witnesses and
exhaustive d=3 fibers. The gap-bound assertion is not applicable: exported
final defect radii are not the specified exact optimal odd-cut certificate.
No Phase-1 proof was changed or extended.

The 3072-shot pilot and paired comparative workflow passed hard invariance,
finite/range checks and saved-data audit. Exact SHAs, commands, conventions
and limitations: [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).
Pilot findings: [review](implementation_artifacts/pilot/REVIEW.md).
Stop for pilot review; no larger campaign or circuit-level swim is authorized.

The following records the completed Phase-1 milestone and its original
stop boundary; Phase 2A supersedes that boundary only within its explicit scope.

## Current state

**Phase 1 complete: Research Tasks 1–7.** Resumed the interrupted
[Tasks 6–7 implementation](prompts/CODEX_TASK_06_07_PHASE1_COMPLETION_AND_AUDIT.md),
retained and rechecked its mathematical work, and completed the source,
claim and consistency audits.

Deliverables: [integrated TeX note](notes/note.tex),
[25-page PDF](notes/note.pdf), [claim audit](REVIEW.md),
[audited bibliography](refs/REFERENCES.md), and
[finite checks and reproduction instructions](notes/support/README.md).
All six primary state documents are synchronized.

## Proved results

Scope throughout: standard triangular 6.6.6 patches at every odd d≥3,
ordinary colored boundaries, one encoded qubit, perfect measurements,
one CSS sector and one fixed color/stage-2 auxiliary syndrome fiber.

- Boundary classification, resolved graph and exact physical chain map:
  one qubit-labelled edge per physical qubit, two free terminals,
  matching compatibility, and $HT_c=\Lambda_cD_c$ on all chains.
- Logical topology (Theorem 8.3, Corollary 8.4):
  $K_c/R_c\cong Z_X/S_X\cong\mathbb F_2$; terminal parity detects the
  physical logical class. Nontrivial relative chains contain a simple
  terminal path. Not every physical support belongs to this fiber.
- Complete non-c face cycle basis and induced binary complex
  (Proposition 8.6, Definition 8.7); bare graph relative homology is
  explicitly distinguished from the physical logical quotient.
- Free-boundary optimal nonnegative odd-cut dual (Proposition 10.2),
  with a concrete companion LP and proof of certificate existence.
  Radius balls are resolved without joining the terminals artificially.
- Exact partial-edge contraction (Lemma 11.2), with
  $\bar\omega_c(uv)=\max(0,\omega_c(uv)-h_u-h_v)$.
- Swim-distance theorem (Theorem 11.4):
  $\phi_c=\operatorname{dist}_{\bar G_c}(b_c^0,b_c^1)
  =\min_{z\in K_c,\beta_c(z)=1}\bar\omega_c(z)$.
  Quotient routes lift to physical logical paths, including when the
  terminals lie in one contracted cluster and the distance is zero.
- Certified stage-2 MWPM bound (Theorem 12.3):
  $W_{c,\mathrm{opp}}^{(2)}-W_{c,\mathrm{base}}^{(2)}\ge\phi_c$.
  The proof supplies free-boundary endpoints and edge-disjoint trails
  explicitly, rather than assuming a surface-code proof applies verbatim.

With radii supplied, the two-Dijkstra algorithm takes
O((|V|+|E|)log|V|) time and O(|V|+|E|) storage. Nonuniform weights,
partial coverage, merged clusters, one/both-terminal contacts and
labelled zero-length edges are handled. Disconnected terminal components
would return infinity with no witness; the specified family is connected.

## Conditional statements and retained limitations

The representative inequality requires an optimal correction and a
compatible nonnegative dual with exact equality
$\sum_S y_S=\omega_c(f_c)$. Such data exist mathematically, but the
inspected external PyMatching call returns only predictions and weights.
Certificate export/conversion or a companion optimization is necessary.
The explicit reference dual LP has exponential representation size;
near-linear geometric postprocessing does not establish low total overhead.
Floating-point sanity checks are not exact rational certificates.

Arbitrary radii, incomplete growth data, nonoptimal duals and UF outputs
have no proved representative-gap bound. The note gives a separately
specified UF geometric construction and a d=3 counterexample to using
zero radii in place of certified data. Equal matching minimizer sets do
not imply arbitrary merged/resolved growth equivalence.

The swim value is an exact fixed-fiber geometric minimum and a confidence
proxy. It is not an exact logical-class posterior LLR, a posterior
failure probability, or the full concatenated decoder's comparative gap.
Physical independent-error log-odds support only the stated ratio of two
specific representatives. Stage-1 success is not assumed or established.

## Validation and literature audit

All 41 formal definitions/results are classified and checked in REVIEW.
The separate same-agent adversarial pass recorded findings before repairs;
this is not external peer-review certification. Citation-dependent inputs
were checked against original passages, with precise edition/location and
scope comparisons in the bibliography. Direct overlaps include fractional
swim metrics, exclusive UF surviving distance, bounded/extra-cluster
variants, customized PyMatching on RP2 cultivation, and general-QLDPC
confidence/postselection. No priority claim is made.

The finite script passes 15 family/color incidence and binary-rank cases
through d=11, every d=3 support in all colors, and 144 exhaustive
fiber/weight/color instances. It also verifies physical logical witnesses,
interval-subdivision equivalence and the stated counterexamples. These
checks support the proofs and are not a numerical performance study.

The final TeX compiled successfully twice. The second log contains no
warnings, unresolved citations/references, or overfull/underfull boxes.
Labels are unique, all 41 review entries match the manuscript, and
extracted PDF text has no unresolved reference markers. The dual,
logical-lifting and gap-theorem pages were visually inspected. Local
Markdown links were checked. Build artifacts other than notes/note.pdf
are in /tmp/color-code-phase1-build; reproduction commands are in the
support README. The external repository remains clean at commit
0eb35935c1e5ff30ba3db9def30a9d35bca2f16d.

## Phase 2 boundary

Stop here. A separately authorized next task may address practical dual
extraction, stage-1 uncertainty/failures, aggregation of the three colors,
interaction with final branch selection, full comparative/forced gaps,
posterior calibration, circuit-level extensions, or BP-LSD/hypergraphs.
None of those later tasks was implemented by this Phase-1 completion run.
