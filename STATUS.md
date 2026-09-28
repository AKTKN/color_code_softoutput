# Native stage-1 perturbation implementation (2026-09-29)

Completed the user-approved three-package plan. PyMatching supplies shot-major
ensembles from original decomposed stage-1 priors, a pristine solver and a
reusable work solver. Both MatchingGraph and SearchGraph weight slots are
updated with existing quantization/normalization rules; queues and arenas
reset safely, including recovery after failed syndromes. False retains
ordinary/SWIM/path-gap APIs. Native unsupported cases fail explicitly.

ColorCode/decoder `stage1_perturbation=True` canonicalizes effective prior
flags, preserves member 0 and final outputs, shares draws across comparative
classes and reuses original stage-2 matchings. False retains checkpoint
original-DEM perturbation. Seed, scheme and cursor survive save/load; legacy
files default False. Root YAML/planner/worker/metadata integration forwards
absolute shot indices and shares one resolved entropy seed across workers.
The dedicated config is `configs/native_stage1_perturbation_comparison.yaml`;
main.yaml and physical Stim sampling are unchanged.

Before publication: decoder 231 passed/two existing skips, root 318,
PyMatching Python 117 and C++ 95 passed. Final: **root 325; decoder 252/two
existing skips; PyMatching Python 129 and C++ 99 passed**. C++ ASan/UBSan/leak
checks pass. Independent random/fresh matching/full-pipeline oracles,
all candidates/scoring, M1/alpha0, boundaries/ties/>64 fault IDs, recovery,
SWIM/validity, batching, worker 1/2, cache recreation and persistence pass.

Bounded d9/13/17, uniform p=.001, rounds=d, M1/12, alpha1, N1/10, three-repeat
evidence: `notes/support/native_stage1_perturbation_20260929/`. M12/full-output/
10-shot native means are **3.499/10.171/25.956 ms/shot**, **11.61/11.77/11.66x**
faster than same-law fresh stage-1 builds and **24.58/27.72/41.83x** faster
than original-DEM perturbation with fixed stage 2. The latter changes the
candidate law and does not establish a LER improvement. M1 shows no consistent
runtime improvement. Warm native factory/C++ builds are zero in both stages.
Cold setup, profiles, RSS, raw CSVs and source/environment hashes are separate.
Timing programs and temporary checkpoint/data/child JSONs were deleted.

Published checkpoints on `codex/per-shot-runtime-20260929`: root `5c7d355`,
decoder `ddfd777`. All three feature branches are
`codex/native-stage1-perturbation-20260929`, based on these checkpoints and
PyMatching `7a26e6a8e`. Exact dependency SHAs:
`notes/support/native_stage1_perturbation_20260929/dependencies.json`.
No main merge, larger campaign or new soft-output theorem was performed.

# Direct stage-1 perturbation probe (2026-09-28)

Answered the user's performance question with a temporary in-memory sampler
prototype, leaving production decoder source unchanged. d9/d13, M12, uniform
p=.001, rounds=d, full_output=True, steady 10-shot batch: original-DEM perturbation
with original stage2 takes 85.16/250.11 ms per shot; direct stage1-prior
perturbation with original stage2 takes 58.07/150.51 ms, a 1.47/1.66x speedup.
Both still construct 33 new stage1 weighted matchings per shot. Input-array
mutation does not update an already constructed PyMatching object; native
replacement invalidates/prepares the internal MWPM on the next decode.

An additional prototype preserves original-DEM draws and outputs but skips
unused stage2 probability/sorting/map computation: 64.37/191.73 ms per shot,
with every full-output field exactly equal to the current original-stage2
mode. All candidate syndromes in all probe calls pass independent parity
checks. Direct stage1 is a different candidate-generation rule, including
different cross-color prior correlations; no LER conclusion is drawn.
The report, 40 raw rows and environment are in
`notes/support/decoder_runtime_optimization_20260928/stage1_direct_probe.md`.
Program and temporary directory were deleted. No production mode was added,
no commit/push and no campaign. The earlier 6–7x historical slowdown measured
perturbed stage2, not the original-stage2 setting.

# Per-shot perturbation runtime implementation (2026-09-28)

Implemented the corrected runtime prompt locally on
`external_libs/color-code-stim/` main, starting at `072a87d`. Each shot/member
receives a fresh common-X/Z-DEM perturbation shared across colors and logical
hypotheses. RNG/cursor state resumes after save/load; M1/alpha0 retain original
batched arithmetic. Six fixed base matchings, exact dynamic LRU32 plus
current-shot references, symbolic probability/source plans and hard-output
retention reductions remove repeated fixed work while preserving dynamic
column ordering, source maps, candidate scoring/selection, guide and SWIM rules.

Independent fresh DEM/decomposition/matching oracles match all per-shot
outputs; pristine fixtures match all unaffected modes. Final decoder suite:
231 passed, two existing skips; root suite: 318 passed. Mutation/ties,
comparative graph sharing, chunk/empty/single calls, persistence and allocation
regressions pass. PyMatching, configs, saved runs and other feature worktrees
are unchanged. No native weight mutation, new threading or installation.

Bounded d=9/13/17, uniform p=.001, rounds=d timings, environment, raw CSVs
and audit are in `notes/support/decoder_runtime_optimization_20260928/`.
M1 full-output/10shot improves 6.3–9.4x (84–89% shorter) against pristine
main. Same-spec M12 improves 37–64x against uncached per-shot reconstruction.
Historical fixed-ensemble M12 batches are a different comparison: new
full-output/10shot is 6.0–7.1x slower at d9/d13 because it constructs 660
graphs rather than sharing 72 across that batch. Warm/initialization and
resident memory are recorded separately. This is finite runtime evidence,
not an asymptotic/LER claim. Measurement scripts and temporary reference
packages were deleted after execution. No commit/push or campaign was done.

# Historical runtime-optimization prompt correction (2026-09-28)

Created `prompts/codex_decoder_runtime_optimization_prompt.md` from the supplied
optimization prompt. The user requires fresh independent original-X/Z-DEM
perturbations for every shot, with each shot/member draw shared across colors
and comparative hypotheses. Revised cache expectations, bounded dynamic
storage, RNG/chunk/output equivalence tests, persistence checks and benchmark
comparisons accordingly. At this checkpoint the decoder still used a fixed
ensemble; the prompt identifies per-shot resampling as the authorized semantic
correction and requires optimization equivalence against an uncached per-shot
reference using identical draws. Document consistency checks pass. No decoder
implementation, sampling campaign, test suite, or benchmark was run for this
prompt-editing request.

# Decoder timing scaling (2026-09-28)

Measured paired 10-shot wall times at d=9,11,13,15,17 with uniform circuit
noise p=0.001 and rounds=d for perturbation M=12/M=1 and Tesseract. The report,
scaling figure, 215-row summary CSV, 150-row per-shot CSV and initialization
CSV are in `notes/support/decoder_timing_scaling_20260928/`. Includes stagewise
PyMatching API/native call times, graph construction, candidate evaluation,
residual work and per-call averages. All call counts, wrapper prediction/weight
equivalence and CSV arithmetic checks pass. At d=17, Tesseract's mean
166.756 ms is affected by a 931.803 ms shot; its median is 78.216 ms.
Temporary scripts/instrumentation were removed; decoder source and YAML
remain unchanged. These bounded timings do not establish asymptotic scaling.

# Ensemble-size figure (2026-09-28)

Added `analysis/ensemble_size.py` with parameter-based ensemble-size tables
and plots, source provenance, independent distance/decoder legends, 99% Wilson
bands and explicit duplicate/settings/reference checks. The notebook's final
section exports p=0.03 for the primary run 7f861167, importing only Tesseract
from 779e2a31. The existing representative baseline is m12; no counts are
pooled. Exported 21 ensemble and six reference rows in
`cluster_results/26_09_28_15_33_34_7f861167/analysis/ensemble_size/`.
All assets use zero Matplotlib padding; the captionless standalone vector PDF
compiled and passed visual inspection. Templates and usage are under
`notes/support/ensemble_size_*.tex` and `ENSEMBLE_SIZE_FIGURE_USAGE.md`.
Nine focused ensemble/cross-run tests passed. No sampling or decoder changes.

# Captionless stage-2 figure export (2026-09-28)

Added `notes/support/stage2_prior_standalone.tex` and updated
`notes/support/STAGE2_PRIOR_FIGURE_USAGE.md` for standalone composition of
separate legends and the plot, with captions in the manuscript. Zero outer
border and exact removal of the existing 0.03-inch asset padding minimize
whitespace. Compiled and visually inspected the captionless one-page PDF in
`cluster_results/26_09_28_14_38_26_779e2a31/analysis/stage2_prior_comparison/`.
No simulation or source metrics changed.

# STATUS.md

## Stage-2 prior manuscript figure — 2026-09-28

Added a dedicated export section to the existing analysis notebook for the
two stage-2 prior variants in `26_09_28_14_38_26_779e2a31`. It exports the
30-row LER comparison and separate distance/prior vector PDF legends to
that run's `analysis/stage2_prior_comparison/`, with independent display
labels, fonts, columns and canvas controls. TeX placement/paragraph examples
are preserved under notes/support; the generated one-page preview compiles
with pdflatex and passes visual review. Legend panel widths .44/.47 linewidth
keep the fonts at approximately equal scale. The caption uses the actual
M=16, alpha=1, d=7/9/11, one round, 1M shots/point and 99% Wilson bands.
See `notes/support/STAGE2_PRIOR_FIGURE_USAGE.md` for placement and later
legend adjustments. No source data or decoder change and no sampling.


## Selected cross-run decoder reuse — 2026-09-28

Added `analysis/color_correlated_comparison.py::ColorCorrelatedComparison`
with a primary run and `additional_sources` mappings containing a source
run directory, optional point filter and optional analysis-only alias_map.
It reuses the existing LER/improvement/count/effect/legend API and routes
aggregation to each source's unchanged files. Absolute composite point keys
avoid date-folder collisions. Each source keeps its original shot counts
and Wilson intervals. Duplicate alias/condition points or saved files,
conflicting decoder settings under one alias and incompatible recorded
physical circuit options are rejected rather than silently pooled.

The primary run is preferred for representative baselines and figure export.
Paired points retain their own baseline. Summary/count/effect tables expose
source_run/data_directory; improvement tables also expose baseline_source_run
alongside source alias/type and baseline_paired. Imported Tesseract shots
remain independent of the selected baseline. source_manifest records the
composition selections; source_runs retains each original reader/config.
Legacy ColorCorrelatedRun is still available for single-run analysis.

Updated the existing analysis notebook to compose primary
`26_09_28_15_33_34_7f861167` with only alias tesseract from
`26_09_28_14_38_26_779e2a31`. All 120 selected files are present. Notebook
analysis cells execute: 135 LER rows including 15 representative baselines,
and 24 improvement rows at p=.03. All 15 imported Tesseract failure counts
and LERs match the original single-run reader. Its ratio numerator comes
from the primary run's representative (m12 under deterministic alias order),
and all imported Tesseract rows report baseline_paired=False. No source run,
metric file, decoder or simulation campaign changed. Changed-run notebook
outputs were cleared; rerun the first cell then the analysis cells.

Validation in color_code_so: 42 existing analysis/runner/soft-output tests
pass, plus six independent cross-run tests covering selection, primary
baseline preference, own paired baselines, provenance, source-filtered
ratios, alias renaming, duplicate rejection, incompatible flags, conflicting
same-alias settings and different shot counts. Commands use
`MPLBACKEND=Agg PYTHONPATH="$PWD/external_libs/color-code-stim/src:$PWD/src" python -m pytest`
with `tests/test_color_correlated_analysis.py tests/test_simulation_runner.py
tests/test_workflow_soft_output.py tests/test_workflow_soft_output_plots.py`
and separately `tests/test_color_correlated_comparison.py`.
README documents the composition API and reproducible notebook usage.


## Alias-first LER improvement and tables — 2026-09-28

Updated `analysis/color_correlated.py` so LER, improvement-ratio and separate
legend defaults use `(distance, decoder_alias)`. Explicit decoder-type
filters/groups remain supported when they identify unique variants.
Summary, count, better-weight and effect tables retain both alias and type;
the improvement table additionally exposes `baseline_source_decoder_alias`
and `baseline_source_decoder_type`. Paired variants retain their own baseline;
unpaired points identify the selected physical-condition representative.

Updated the existing `notebooks/color_correlated_decoding.ipynb` in place:
its improvement grouping and displayed LER/ratio columns now include aliases,
source-provenance columns and alias-filter examples. Existing user-selected
run path and physical error rate were preserved; stale outputs in changed
code cells were cleared. Rerun the first cell to reload the local modules,
then the desired analysis cells. README includes alias table/ratio examples.

Validation: in `color_code_so`,
`MPLBACKEND=Agg PYTHONPATH="$PWD/external_libs/color-code-stim/src:$PWD/src" python -m pytest tests/test_color_correlated_analysis.py tests/test_simulation_runner.py -q`
passes 27 tests. New independent fixtures give same-type aliases different
paired baseline counts and verify distinct ratios, source provenance, alias
filters, default legends/grouping, explicit ambiguous-type rejection, and
legacy alias fallback. The updated notebook analysis cells executed against
`cluster_results/26_09_28_14_38_26_779e2a31` without exporting over existing
figures: 75 LER rows, 12 improvement rows at p=.03, and 15 rows for each
selected-alias table. No simulation campaign or saved-result edits occurred.


## Saved-run baseline/alias audit — 2026-09-28

Audited `cluster_results/26_09_28_14_38_26_779e2a31`: alias `concat_mwpm`
actually selects `type: color_correlated`, enabled with b=2. The displayed
baseline uses that entry's same-shot ordinary `default_logical_error` at
all 15 physical conditions. All 15 million-shot failure pairs and rescue
sidecars are consistent. Example d=9, p=.04: baseline 4,351 failures, final
3,806, 666 rescued and 121 worsened. A bounded 128-shot/condition code-path
check matches the baseline to ordinary decoding at all 15 conditions.
The saved run contains no independent ordinary concat_mwpm decoder entry.
No production code, saved run configuration or result arrays were changed.
See `notes/support/SAVED_RUN_BASELINE_ALIAS_AUDIT_779e2a31.md` for the code
trace, count table, source/replay limits and corrected future-run entry.


## Decoder main publication — 2026-09-28

At the user's request, `external_libs/color-code-stim/` was switched to
`main`, advanced to `origin/main` (`85f5b6e`), and merged with the
original-stage-2 perturbation change (`04123e0`). Merge commit `072a87d`
was pushed to `origin/main`. Its tree is identical to `04123e0`, and
`PYTHONPATH="$PWD/src" python -m pytest tests/test_prior_perturbation.py -q`
passes all 28 tests in `color_code_so`. The checkout remains on main;
subsequent authorized decoder work uses main until the user changes that
preference. README no longer requires switching to phase2a/swim-distance.


## Perturbation stage-2 prior switch and decoder aliases — 2026-09-28

The user authorized changes to the current `color-code-stim` checkout and the
canonical YAML simulation/analysis package, followed by commit/push.
`ColorCode` and `ConcatMatchingDecoder` now accept
`use_original_prior_for_stage2=False`. False preserves the existing perturbed
stage-1/stage-2 matching. True retains perturbed stage-1 hypotheses but runs
stage 2 on the original X/Z DEM color decomposition. Its correction is already
in base column order and is evaluated accordingly. Member 0, common-base
selection weights, candidate budgets and unchanged-prior SWIM scoring retain
their existing meanings. Save/load persists the option; older saves default
to False. The new constructor parameter is appended to preserve positional
argument compatibility. No per-shot DEM reconstruction is introduced.

Each YAML decoder entry can now supply a unique `decoder_alias` alongside
`type`, `options` and `decode_options`. The alias participates in point IDs,
configuration hashes, saved directory prefixes and logs. Analysis exposes
`decoder_alias` in the catalog, filters, count/effect tables and LER/ratio
plots; the shared soft-output analysis accepts alias filters/groups as well.
Legacy entries retain their hashes/paths and expose their type as the analysis
alias. Repeated types require distinct aliases. Baseline representatives are
matched on physical conditions, excluding both decoder identity fields;
type-only LER grouping rejects ambiguous variants.

`configs/perturbation_stage2_comparison.yaml` provides both modes with M=12,
alpha=1, the same ensemble seed, original-DEM final selection and separate
aliases. README documents valid YAML and alias-based analysis. The adaptive
runner continues to sample physical shots independently per alias/point;
each advanced decoder's stored baseline remains paired within that point.
This bounded configuration is suitable for LER comparison, without claiming
paired cross-alias shots or a decoder-performance advantage.

Validation uses `color_code_so` with the current decoder checkout on
`PYTHONPATH`. Tests cover both priors, ordinary/comparative decoding, both
selection bases, syndrome/observable consistency, batching, persistence,
zero-alpha/member-0 limits, all three noise models at rounds=1 and 3,
alias/hash/path validation, spawn execution, baseline plotting and scored-shot
analysis. The full root run initially exposed a stale historical PyMatching
SHA assertion; it now checks the exact current checkout SHA in saved metadata.
The comparison-YAML smoke ran 8 points with 16 shots each (128 total) and
rendered the alias LER/baseline plot under
`/tmp/perturbation-stage2-smoke-fcg0g01s/`. No larger campaign ran.

Validation commands/results (executed using
`/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python`):

- `PYTHONPATH="$PWD/external_libs/color-code-stim/src:$PWD/src" python -m pytest tests -q`:
  307 passed (117.19 s).
- From `external_libs/color-code-stim`, `PYTHONPATH="$PWD/src" python -m pytest tests -q`:
  178 passed, two existing skips; the subsequently added legacy-save test also
  passed in `python -m pytest tests/test_prior_perturbation.py -q`
  (28 passed, including all new perturbation cases).
- `PYTHONPATH="$PWD/external_libs/color-code-stim/src:$PWD/src" python -m color_code_softoutput.simulation.cli --config /tmp/perturbation-stage2-smoke-fcg0g01s/smoke.yaml`:
  all eight points completed; saved-log reload and alias LER plotting pass.
- `git diff --check` passes in both repositories.

Decoder implementation: commit `04123e0` on `phase2a/swim-distance`.
Main-package changes are on `main`. The existing local edits to
`notebooks/color_correlated_decoding.ipynb` are preserved and excluded from
this change.


## SWIM/logical-gap scatter comparison — 2026-09-28

`analysis/workflow_soft_output.py` now provides scatter distributions,
`plot_conditional_ler`, and scatter post-selection with default 99% Wilson
shades. All three accept `metrics=["swim_distance", "logical_gap"]` alongside
the existing single `metric` argument. Multi-metric views use available
point/metric combinations; each selected point must supply at least one
requested metric and each requested metric must occur in the selection.
`available_metrics(filter)` exposes file availability. Schema, nonnegative
score and shot-index checks remain enforced; every score uses its own
decoder point's hard-failure labels. Overlaying separate YAML decoder
points does not imply paired physical shots.

Distributions use success circles and error crosses. Optional error-score
negation is display-only, and normalized frequencies divide outcome counts
by all shots in their series. Auto score grouping preserves discrete values;
integer bins share edges across series. Conditional probability is empirical
failures/shots by score, without a calibration fit. Post-selection retains
the exact scores >= each threshold, with opt-in rounding/ties. Both rate
views preserve zero estimates in tables and display only their Wilson bands.
SWIM diamonds and gap squares use consistent series colors. Legends sit
above the data to keep scatter points and shades visible.

`notebooks/workflow_swim_soft_output.ipynb` now exposes both metrics and all
three views, including signed/normalized distribution options and separate
PNG/PDF exports. Its d=9, p=.03 saved-data example includes color-correlated
SWIM, stage-2-base SWIM and ordinary comparative gap, with 1,000,000 shots
per series. Conditional counts preserve all shots; post-selection tables
have 21, 21 and 23 threshold rows respectively. Review artifacts are under
`/tmp/workflow-soft-output-scatter-review`. No new sampling campaign ran.

Validation: `PYTHONPATH=src conda run -n color_code_so pytest -q
tests/test_workflow_soft_output_plots.py tests/test_workflow_soft_output.py`
(15 passed). Independent saved-shot fixtures cover frequency/sign handling,
normalization, common bins, decoder-specific failures, Wilson limits, exact
retention counts, rounding, scatter/band artists and metric selection errors.
The updated notebook's analysis cells also executed on the saved cluster run.

## SWIM notebook run-path resolution — 2026-09-28

`notebooks/workflow_swim_soft_output.ipynb` now constructs `run_directory`
from `PROJECT_ROOT`, stepping up from `notebooks/` when that is the kernel's
working directory. The initial cell loads all 150 planned points from the
same cluster run when executed from either the repository root or
`notebooks/`. Figure exports also use this resolved run directory.
The notebook now demonstrates `groups=["decoder_type"]`, explains
filtering versus pooling, and exposes a shared `metric` for both plots.
Its d=9, p=.03 SWIM example selects `concat_mwpm_stage2_base` and
`color_correlated`, each with 1,000,000 saved shots; both histogram and
post-selection calls succeed (42 post-selection rows). The explanation
distinguishes this stage-2-selection decoder from `concat_mwpm`, which
has only the complementary-gap metric in this run. The latter has an
explicit `metric="logical_gap"` example. Export names use the metric.

## Independent plot legends and LER improvement ratios — 2026-09-28

`analysis/color_correlated.py` now keeps the LER figure separate from
`plot_legends(table, group_by=...)`, which returns one independent figure
per field: colored lines for the first field and black markers for the
second, with field titles and individual values. Run-wide value ordering
keeps styles consistent across filters and improvement plots. Zero LER
observations break the plotted line and show only their unchanged 99% Wilson
band; log axes clip the band at the visible lower limit.

`plot_improvement_ratio(physical_error_rate=..., filter=..., x="distance")`
and `improvement_table` use baseline LER divided by decoder LER. Paired
decoders use their own baseline. Unpaired decoders use the representative
baseline at the same physical condition, preferring the selected LER
baseline and falling back to other saved paired points. The table records
`baseline_paired` and `baseline_point_directory`; independent samples are
not represented as paired. Infinite/undefined ratios remain in the table
and have no plotted estimate. No ratio confidence interval is inferred.
Uniform-noise ratios use the existing per-round LER conversion.

`notebooks/color_correlated_decoding.ipynb` exposes independent figure/axes
objects, filters and physical-error-rate selection, and saves main/color/
marker figures separately as PNG and PDF. Existing run-path and decoder
selections were retained; stale saved outputs were cleared. All code cells
executed against the saved cluster run with d=5,7 and p=.01,.015, saving
review figures under `/tmp/color-correlated-plot-review`. Main plots and
both legends were visually inspected. No simulation was run.

Validation: `PYTHONPATH=src conda run -n color_code_so pytest -q
tests/test_color_correlated_analysis.py tests/test_workflow_soft_output.py`
(19 passed), plus `git diff --check`. Package README documents the API.

## Cluster environment and PBS setup — 2026-09-27

`environment.yml` now records the direct Python, analysis and build-tool
versions from the working `color_code_so` environment. The root README uses
the merged default branches of the decoder forks and clones PyMatching's
`pybind11` submodule. `scripts/pbs_run_experiment.sh` provides a single-node
PBS entry point with explicit Anaconda activation and single-threaded BLAS.
Conda's linux-64 dry run, YAML and shell syntax checks, and local `pip check`
pass. The PBS script completed the 64-shot example in a simulated PBS shell.
Cluster execution remains to be checked on the target site's PBS and Anaconda
installation.

## Original stage-2 SWIM in ensemble YAML workflow — 2026-09-27

The original growth-cluster stage-2 SWIM metric is now opt-in for ordinary,
perturbation, color-correlated and relifting YAML points via
`decode_options.compute_swim_distance`. Each generated stage-2 hypothesis is
scored on the original stage-2 matching prior. The saved final value is the
minimum score among candidates with the selected correction's observable
parity; generated hard corrections and their unchanged-prior selection rule
are unchanged. Perturbation's temporary stage-2 graph is not used for the
metric. The spatial path retains its one-round triangular data-only bit-flip
scope. The existing closed `rounds=d` circuit-level growth/residual scorer now
handles bit-flip, depolarizing and uniform noise using the actual effective
DEM, subject to graph and probability gates checked before run creation.
Ordinary comparative decoding writes its own
`logical_gap.parquet` when enabled. `WorkflowSoftOutputRun` and
`notebooks/workflow_swim_soft_output.ipynb` cover distributions and exact
post-selection curves with filters/groups. This is a proxy comparison, not an
LLR or an unrestricted circuit-noise claim. The complete root suite passes
282 tests; the local decoder suite passes 161 tests with two existing skips.
PyMatching SWIM and path-gap focused suites pass 19 tests. The related
decoder commit `ea851ab` and PyMatching commit `7a26e6a8e` were pushed to
their `phase2a/swim-distance` branches. No sampling campaign was launched.
See package README and tests.

## Tesseract YAML decoder integration — 2026-09-27

The canonical simulation workflow accepts `decoders[].type: tesseract` with
native `TesseractConfig` options. It constructs the normal `ColorCode` circuit,
passes its unchanged original X/Z `dem_xz` directly to Tesseract, decodes
sampled detector rows one at a time, and writes only `logical_error.parquet`.
The worker caches the compiled decoder with its circuit. Preflight rejects
color-correlated modes, ColorCode decode options, Y temporal boundaries, and
detector-count mismatch. A real native-extension three-shot end-to-end run
passed using an optional wheel unpacked outside the environment; the checked-in
unit tests also cover DEM identity and hard-output association. This is an
integration smoke, not an LER or speed comparison. The external Tesseract
checkout and simulation environment were not changed. See
`src/color_code_softoutput/README.md` and `tests/test_simulation_tesseract.py`.

## Adaptive benchmark basis compatibility — 2026-09-27

The paired ablation runner now defaults to and accepts only `original_dem` for
new runs, matching the current color-correlated decoder's required final
selection basis. A `stage2` request fails before creating a run directory.
Historical saved `adaptive_v2` results remain readable. The focused benchmark
suite passes three tests. This change resolves two full-root regression
failures caused by the older stage-2 ablation setting. The full root suite
passes 273 tests.

## Paired worsening and signed net effect — 2026-09-27

Saved-run `effect_table` now adds `worsened_count` and `net_effect_count` to
the existing `effect_count` rescue count. For paired baseline/new failures,
`worsened_count = new_failures - baseline_failures + effect_count` and
`net_effect_count = effect_count - worsened_count = baseline_failures -
new_failures`; positive net means fewer failures. The counts derive from the
saved paired outcome and rescue metrics, with consistency bounds checked.
Ordinary and legacy points without paired sidecars retain missing values.
The notebook's table explanation and saved outputs were refreshed for its
current 18-point run; all three effect columns appear. Eight analysis tests
pass, including mixed rescue/worsening and legacy-sidecar cases. No new
simulation was run.

## Power-guide saved-run analysis reload — 2026-09-27

`ColorCorrelatedRun` now calls the workflow config parser through its module,
so reloading that module updates analysis in a live notebook kernel. The first
cell of `notebooks/color_correlated_decoding.ipynb` explicitly reloads config
and analysis before loading a run. The reported run
`results/26_09_27_20_02_55_852c7ea2` loads all six points and produces 12 LER
rows and six rows in each flag table. A simulated stale-parser notebook cell
reloads and loads the same run. Synthetic saved-run regression with
`color_correlated_b: 2.0` and focused validation: eight tests passed. No
simulation data were changed.

## Power-guide stage-1 color-correlated candidates — 2026-09-27

The current color-correlated decoder replaces guide-selected original X/Z DEM
source priors by `q**(1/color_correlated_b)` for stage 1 only. Stage 2 uses
unchanged base matrices/priors; final candidate selection is fixed to the
unchanged original X/Z DEM log odds. The default `b=1` gives no guide
reweighting. The YAML constructor option accepts any positive finite `b` and
rejects an explicit `stage2` selection basis for this decoder. The decoder
reuses fixed symbolic maps, bounded guide-specific stage-1 prior/matcher
caches, and three base stage-2 matchers. A full-decomposition oracle checks
stage-1 equivalence. A bounded 12-guide subroutine timing measured 0.0019 s
versus 0.4047 s for full re-decomposition, without claiming an end-to-end
speedup. Decoder and focused root tests: 213 passed, two existing skips;
subsequent 26-test focused check passed. No new sampling campaign. See
`notes/support/COLOR_CORRELATED_POWER_GUIDE.md`.

## Two ordinary weight bases in one YAML run — 2026-09-27

The workflow accepts `concat_mwpm_stage2_base` as a distinct point label for
ordinary `concat_mwpm` with the `stage2` selection basis. It rejects
`original_dem` under that label. `concat_mwpm` with `original_dem` and the new
stage-2 label can therefore share one YAML run without a path collision.
`configs/example.yaml` and the package README show both entries. Focused
runner/planning tests: 31 passed, including a two-point end-to-end run.
Each point retains its own point-derived sampling seed, so these two saved
rows are independent-shot comparisons even if `master_seed` is shared.

## Ordinary concat-MWPM original-DEM selection basis — 2026-09-27

Ordinary `concat_mwpm` now honors `color_correlated_weight_basis="original_dem"`:
the three unmodified stage-2 matching solutions are mapped to original X/Z
DEM mechanism order and ranked by the sum of unchanged original log odds.
Stage 1 and stage 2 candidate generation remain unchanged. The default
`"stage2"` retains the historical matching-weight selection. The YAML workflow
already accepted this constructor option; `configs/example.yaml` now shows it
for `concat_mwpm`, and a tiny end-to-end runner check validates the path.
Decoder tests: 158 passed, two existing skips; focused decoder/runner/worker
checks: 33 passed, plus ten focused SWIM checks. In a bounded 256-shot
same-shot comparison at d=5 and d=9,
one-round bit-flip p=0.05, both bases produced identical corrections and
observables; maximum selected-weight differences were below 4e-15. For these
conditions, each stage-2 column mapped to one original mechanism with equal
prior. A d=3, three-round uniform-circuit check also found unit source maps
and equal priors for every stage-2 column. No larger sampling campaign was run.
Separate YAML decoder points use
different point-derived sample seeds, even with the same master seed.

## Paired YAML baselines for relifting and perturbation — 2026-09-27

The canonical YAML worker now records `default_logical_error.parquet`,
`better_weight_by_color_correlated_decoding.parquet`, and
`effect_by_color_correlated_decoding.parquet` for relifting and perturbation as
well as color-correlated decoding. The unchanged metric filenames keep one
analysis/storage contract. Relifting reuses its ordinary r/g/b candidates;
perturbation reuses ensemble member 0, which has the unmodified DEM prior.
The decoder exports their native-weight ordinary baseline prediction in full
output; no second baseline decode is needed. Tests compare this prediction
against a separate ordinary `ColorCode.decode` on identical shots for both
selection bases. Saved-run analysis supports all three modes, plots one
deterministic baseline representative per physical condition, and exposes
separate filters for better-weight and rescue tables. Different decoder
points in the YAML workflow may use independent sampled shots, so observed
baseline counts can differ; relifting's required full-decomposition setting
may also differ from other modes. Existing saved runs were not rewritten.
Validation: 267 root tests passed before the final legacy-read compatibility
check; that six-test analysis module passes afterward. Decoder tests: 156
passed with two existing skips. Focused notebook cells compile. No new
campaign was run.

## Color-correlated candidate scheduling and run category — 2026-09-27

The decoder now compares its three ordinary corrections after mapping them
to original X/Z DEM mechanism order. It executes 0 extra guided candidates
if all three agree, 3 if exactly two agree, and 9 if all differ. For an equal
pair, the two repeated-color targets use the distinct-color guide; the
distinct-color target uses the first repeated color in r/g/b order. Skipped
candidate slots have +inf comparison weights and a false execution mask.
The selected logical class's category is exported as `color_correlated_run`
and streamed to a per-shot uint8 `color_correlated_run.parquet` file with
values 0, 1 or 2. Erasure-predecoded shots have no three-way comparison and
remain outside the YAML writer's supported options. The previous saved runs
do not contain this metric and are not modified.
Validation: 131 decoder tests passed with two existing skips; 254 main-package
tests passed. A deterministic 96-shot uniform-circuit test exercised all
three categories and measured exactly 0, 3 or 9 re-decompositions per shot.
Decoder commit `fdf330d` was pushed to `origin/phase2a/swim-distance`.

## Original-DEM candidate-weight option — 2026-09-27

The color-correlated decoder now accepts
`color_correlated_weight_basis="original_dem"` through `ColorCode` and YAML
decoder options. It maps each executed stage-2 candidate to the
pre-decomposition X/Z DEM (`dem_xz`) and scores the mapped correction using
that DEM's unchanged log-odds prior. Candidate selection, reported weights,
comparative logical gaps, and the workflow's better-weight flag use the
selected basis. The default `stage2` behavior is retained. The original-DEM
score is a correction weight, not a posterior class likelihood. Existing
saved runs keep their recorded basis and cannot be rescored from aggregated
counts. Decoder suite: 129 passed, two skipped; worker/runner: 15 passed;
a two-shot d=3, r=3 uniform-circuit smoke completed. No campaign ran.
In a d=3, r=3 uniform-noise
check, every stage-2 column has one original source, and stage-2 versus
original-DEM candidate scores agreed within 5.4e-15 on four shots.

## Original-DEM guide conditioning correction — 2026-09-27

Per the user's clarification, the nine extra candidates now condition the
guide-selected mechanisms of the pre-decomposition X/Z DEM on being active,
rebuild that original DEM with unchanged targets/order, decompose it anew for
the target color, and rerun both matching stages. Simultaneous guide sources
are conditioned jointly. Stage-2 candidates are realigned through original
mechanism indices before base-prior selection. The former direct updates to
decomposed-column probabilities are removed. The implementation prompt and
`Near optimal decoding for the color code/main.tex` were corrected to state
this rule. Decoder suite: 129 passed, two skipped; worker/runner: 15 passed;
the d=3, r=3 uniform-circuit 16-shot validity smoke passed (15 shots with
nonzero detectors, two extra candidates selected), as did a d=5, r=5 shot.
All 253 main-package tests pass. The corrected TeX source compiles with its
bibliography. Saved runs were not changed and no new sampling campaign ran.
Decoder implementation was committed as `7a1eff0` and pushed to
`origin/phase2a/swim-distance` in the separate color-code-stim repository.
The tracked correction specification is
`notes/support/COLOR_CORRELATED_ORIGINAL_DEM.md`.

## Saved color-correlated decoding analysis — 2026-09-27

Added `analysis/color_correlated.py` and the editable
`notebooks/color_correlated_decoding.ipynb`. The module reconstructs planned
conditions from the saved run log, checks bounded Parquet metric batches,
computes per-condition LER and correlated-flag counts, and plots filtered
physical versus logical error rates. Up to two `group_by` keys control line
color and marker. The specified 36-point, 360,000-shot run loads and plots as
six series. Two focused tests pass; all five notebook code cells execute.
The figure is saved under the run's `analysis/` directory. No sampling ran.
The plot now supports a logarithmic vertical axis and a boxed legend grid
above a plot region with fixed physical dimensions. The notebook exposes
editable size and font controls; zero-failure rates remain zero in tables.
The plot also accepts `baseline_compare=True`: each color-correlated point's
`default_logical_error.parquet` supplies a paired `decoder_type=baseline`
series, with source and metric recorded in the returned table. The existing
36-point run now yields nine series and a 3-by-3 legend; three focused tests
pass and all five notebook cells execute. The baseline figure is saved as
`analysis/color_correlated_ler_with_baseline.png`, without new sampling.
For uniform circuit noise, plot and summary LER values and Wilson bounds are
now converted to per-round values using `1-(1-P_fail)^(1/r)`, including the
paired baseline. The measured total rate is retained separately. Round count
is excluded from legend grouping and varying-condition checks; four focused
analysis tests pass, including `rounds: distance`.

## Circuit-memory provenance portability — 2026-09-27

The historical circuit-memory source snapshot now includes the local
implementation prompt when it exists. Because `prompts/` is Git-ignored, a
fresh checkout may lack that prompt; the run and its source archive still
complete using the available tracked sources. The end-to-end test passes both
with and without the prompt (two parameterized cases).

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
have one JSON log, exact point files and no surviving `.buffer/`. No large
campaign was performed. The outer pipeline made a checkpoint commit after
each successful stage; no push or merge was performed.

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
# Adaptive near-optimal pipeline stage 05 (2026-09-27)

The independent decoder now reports pairwise same-baseline Stage-2 syndrome
counts and exact same-target cache skips alongside its existing class,
execution, alias, and common-prior candidate arrays. A new paired benchmark
under `src/color_code_softoutput/simulation/adaptive_benchmark.py` samples
once and runs ordinary, color-correlated, relifting and prior perturbation
decoders on the same detector outcomes. The new `adaptive_v2` result root
contains both `color_correlated_run.parquet` and `relift_run.parquet` with the
existing shot-index/uint8 convention, diagnostic sidecars, candidate-weight
tables and an atomic provenance manifest. Analysis is in
`src/color_code_softoutput/analysis/adaptive_benchmark.py`. Only bounded
smokes were run; the production command is in the package README. Stage-05
acceptance: 33 focused root tests and 37 focused decoder tests pass, both Git
trees pass `git diff --check`, and a 16-shot d=3 original-DEM-basis paired
smoke in four batches produced and reloaded both run-class sidecars plus all
diagnostic and candidate-weight tables. The smoke contains class counts 3/7/6
and its independent candidate-weight audit passes. The saved result is under
`/tmp/adaptive-stage05-final-batched/adaptive_v2/20260927T080530Z_4409f8c3`.
# Stage 06 adaptive ablation benchmark (2026-09-27)

The paired `adaptive_v2` benchmark now records observed MWPM calls, decode
runtime, run classes, candidate selection, relift Stage-2 early exits, and
perturbation hypothesis/member diversity. The report exports Wilson LER,
paired rescue/regression, class-conditioned outcomes, call distributions,
perturbation saturation, and basis-labelled plots. The requested d/p/M/alpha
grid is available but was not launched. See
`notes/support/ADAPTIVE_ABLATION_BENCHMARK.md`. Acceptance:
`PYTHONPATH=src:external_libs/color-code-stim/src conda run -n color_code_so
pytest -q tests/test_adaptive_benchmark.py tests/test_simulation_runner.py
tests/test_simulation_workflow_storage.py` (24 passed), and the decoder's
three focused suites (37 passed). The bounded test run covers both score
bases and a two-shot reduced grid. No commit, push or campaign was performed.
The full root suite passed (260 tests) and the full decoder suite passed
(156 tests, two existing skips). Both repositories passed `git diff --check`.
