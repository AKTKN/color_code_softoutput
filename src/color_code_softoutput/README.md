# Reproducible paired code-capacity study

## Paired adaptive decoder benchmark (schema `adaptive_v2`)

Run a bounded smoke with
`PYTHONPATH=src:external_libs/color-code-stim/src python -m color_code_softoutput.simulation.adaptive_benchmark --output-root results --shots 16 --distance 3`.
This command samples each physical detector/observable outcome once, then
decodes the identical batch with ordinary concat-MWPM, adaptive
color-correlated decoding, adaptive cross-color relifting and the fixed
pre-decomposition prior perturbation ensemble. All four constructors use
`remove_non_edge_like_errors=False`; circuit equality is checked before
sampling. The decoder supplies `candidate_weights`,
`candidate_weight_basis`, and selected `weights`; the benchmark saves and
reads these with unchanged-prior scoring audits on up to four shots.

The command creates a fresh `results/adaptive_v2/<timestamp>_<id>/` root.
`manifest.json` contains the semantic configuration ID, ordered batch seeds,
batch size and count,
source digest, decoder elapsed times, selected-kind codes, and score basis. Each metric file has
`shot_index: int64` and one value in the same row order as the existing
`color_correlated_run.parquet` sidecar. Run classes are `uint8` values 0, 1,
or 2 from the shared original-DEM baseline-equality helper. The additional
relifting sidecars store actual extra Stage-2 calls, total calls, 12 logical
slots, unique solved Stage-2 syndromes, alias counts, selected kind, six
pairwise baseline-syndrome comparisons and same-target cache skips. Total
calls and unique solved problems count the one logical class used by this
benchmark. Files are atomically promoted; the manifest is written last,
and an interrupted write cannot be opened by `AdaptiveBenchmarkRun`.

`analysis.adaptive_benchmark.AdaptiveBenchmarkRun(path)` validates identities,
types, paired run classes and saved candidate weights. `by_class("relift")`
reports class shot fractions, LER, rescue and regression rates, mean and
median extra calls, and selected-kind composition. `by_class("color_correlated")`
reports matching class outcomes, extra Stage-2 calls and baseline/guided
selection composition. `overall_relift()` reports the fraction
of all six pairwise target syndromes equal to their baseline targets,
the cache-skip fraction among proposed relift problems, and the distribution
of unique solved Stage-2 problems.

Production command (reported only; no campaign launched):

```bash
PYTHONPATH=src:external_libs/color-code-stim/src python -m color_code_softoutput.simulation.adaptive_benchmark --output-root results --shots 1000000 --batch-shots 256 --distance 7 --physical-error-rate 0.003 --ensemble-size 3 --alpha 0.2 --weight-basis original_dem
```

## Canonical YAML simulation

For the original stage-2 cluster SWIM metric, set
`decoders[].decode_options.compute_swim_distance: true`. The workflow writes
`swim_distance.parquet` alongside each decoder's `logical_error.parquet`.
Ordinary `concat_mwpm` can separately set
`decoders[].options.comparative_decoding: true` to write `logical_gap.parquet`.
These options require separate runs. The one-round spatial stage-2 SWIM path
supports triangular Z-memory with data-only bit-flip noise. The established
closed-memory circuit-level extension supplies the metric for triangular
`rounds=d`, `tri_optimal` Z-memory with bit-flip, depolarizing or uniform
circuit noise. The circuit path consumes the actual X/Z-separated DEM and
checks the graph structure and probabilities before a run starts. Other
circuit geometries, schedules and open temporal boundaries remain outside
the current metric. SWIM scores every generated stage-2 hypothesis
on the unchanged base-prior stage-2 graph, then reports the smallest score
among candidates whose mapped correction has the selected hard decision's
observable parity. For perturbation, this evaluation rematches that
hypothesis on the base graph; its generated hard correction still comes from
the perturbed member. The distance is an exploratory proxy, not a posterior
LLR or a full-decoder logical gap.

`analysis.workflow_soft_output.WorkflowSoftOutputRun(run_path)` provides
`plot_distribution`, `plot_conditional_ler` and `plot_postselection`, each
returning a Matplotlib figure and a count/rate table. Supply
`metrics=["swim_distance", "logical_gap"]` to overlay the available metric/
decoder combinations, or `metric="logical_gap"` for one score. With neither
argument the existing single-SWIM default is retained. `available_metrics`
shows saved metric files per selected point. Every selected point must have
one requested metric, and every requested metric must be present somewhere
in the selection. Each series uses its own decoder's failure labels; separate
YAML decoder points do not imply paired physical shots.

Distributions show success `o` and logical-error `x` frequency points.
`signed_logical_errors=True` negates error scores for display only;
`normalize_frequency=True` divides outcome counts by all shots in the series.
The older `density` argument is now an alias for that normalization, without
division by bin width. The returned table has `logical_error`, `raw_score`,
display `score`, outcome `count`/`shots`, `frequency` and bin boundaries.
`bins="auto"` preserves near-discrete score groups; integer bins share edges
across plotted series. `round_digits` optionally rounds before grouping.

Conditional logical error probability uses failures / shots at each score
group. Conditional and post-selection figures use scatter points and 99%
Wilson shades, with consistent series colors and diamond SWIM/square gap
markers. Zero rates retain their bands but have no plotted point. Log axes
are the default; use `yscale="linear"` to change the scale. Post-selection
retains scores >= each exact threshold, keeps ties together and omits empty
retention. `round_digits` changes threshold ties only when supplied; the
distribution sign option never changes conditional rates or selection.
`xlim=(0, 1)` controls the visible abort-rate range without changing the table.
See `notebooks/workflow_swim_soft_output.ipynb` for all three comparison views.

Run `./scripts/run_experiment.sh configs/example.yaml` in `color_code_so`, or
`python -m color_code_softoutput.simulation.cli --config configs/example.yaml`.
The example requests 16 shots for each of three d=3 superdense uniform-noise
points. Relifting requires a separate ordinary-circuit configuration, shown as
commented YAML because this superdense decomposition is not graphlike for it.
The runner validates and constructs every point before creating a timestamped
run directory. It writes one `run_log.json`, streams completed chunks into
bounded point storage, and finalizes each point when its shots are complete.
Successful points contain one Parquet file per metric and no `.buffer/`.
Existing notebook experiment entry points remain historical and unchanged.

## Saved adaptive-decoder run analysis

`analysis.color_correlated.ColorCorrelatedRun(run_path)` reads the canonical
`run_log.json` and planned point directories. `catalog` previews available
conditions; `summary(filter=...)` streams each selected Parquet metric into
per-point shot/failure counts and logical error rates. `count_table(filter=...)`
reports both advanced-decoder flags per condition, with missing values for
ordinary decoder points. `better_weight_table(filter=...)` and
`effect_table(filter=...)` allow separate selections. The effect table reports
rescued shots (`effect_count`), worsened shots (`worsened_count`), and signed
net improvement (`net_effect_count = effect_count - worsened_count`) against
each point's paired ordinary baseline. Positive net counts mean fewer logical
failures; no new simulation sidecar is required.
`plot_ler(filter=..., group_by=[...])`
plots physical versus logical error rate with 99% Wilson bands. The first
group key controls color and the optional second key controls marker. The
main figure contains only the data axes. `plot_legends(table, group_by=...)`
returns `{field: (figure, axes)}` for separate color and marker legends, each
with a field title and individual values. Style, resize and save each figure
independently. The assignments use run-wide ordering and stay consistent
when filters change. Set `yscale="log"` or `"linear"`; zero-failure observations
have Wilson shading only, with no marker or line point. On log axes the band
is clipped at the visible lower limit. Other varying conditions must be fixed
by `filter`. See
`notebooks/color_correlated_decoding.ipynb` for an editable example.
`plot_improvement_ratio(physical_error_rate=..., filter=..., x="distance")`
returns a figure, axes and table of **baseline LER / decoder LER**. Values above
1 mean improvement. Its default distance colors and decoder markers match LER
plots; use `plot_legends` for independent legend figures. Each paired decoder
uses its own saved baseline. Unpaired decoders use the representative baseline
at the same physical conditions, preferring the selection used for the LER
plot, then other available paired points if needed. `baseline_paired` and
`baseline_point_directory` record the source. Infinite and undefined ratios
remain in the table but are omitted from the plot. No ratio confidence interval
is inferred from the marginal Wilson bands. Uniform rates use per-round values.

With `baseline_compare=True` and `decoder_type` in `group_by`, the plot also
adds `decoder_type=baseline` from a selected advanced point's paired
`default_logical_error.parquet`. When multiple decoder types cover the same
physical configuration, it plots one representative, preferring
color-correlated, then relifting, then perturbation. These modes can have
different sampled shots in the YAML workflow, so their measured baseline
counts need not be identical. Relifting also requires the full decomposition
(`remove_non_edge_like_errors=False`), which can differ from another mode's
ordinary decoder setting. The returned table records `metric` and
`source_decoder_type`. Ordinary `concat_mwpm` points remain separate samples.
For `noise_model=uniform`, `logical_error_rate` and its Wilson limits are
reported per round as `1 - (1 - P_fail) ** (1 / rounds)`; the measured
whole-experiment rate remains in `logical_error_rate_total`. The plot ignores
`rounds` as a legend condition, so `rounds: distance` works with distance
and decoder type as the two grouping keys. Multiple round counts for the
same plotted condition still require a separate selection.

## YAML workflow point storage

By default, the YAML worker requests only the metric names required by the
point's saved schema from `ColorCode.decode(metrics=..., full_output=False)`.
The decoder computes the scalar statistics and returns one `(shots,)` array
per requested metric. It does not export all candidate corrections, stage-1
hypotheses or generation weights. Circuit SWIM uses the existing geometry
backend during candidate generation and returns the same parity-filtered
minimum. Actual observables are used only for failure statistics.
Explicit `decode_options: {full_output: true}` retains the diagnostic path
and produces the same final metric columns. The on-disk schema is unchanged.
Detailed paired candidate audits and historical per-color studies retain
their explicitly requested diagnostics.

`simulation.storage.PointStorage(point, point_dir, buffer_shots)` creates one
new point directory whose name matches `point_directory_name(point)`.
Call `accept(WorkerResult)` in the scheduler's main-process callback and
`finalize()` after all point chunks complete. The YAML runner handles this in
its scheduler callback.
Overlapping or duplicate intervals are rejected. Out-of-order chunks spool
under `.buffer/`, while contiguous rows flush as numbered `part_*.parquet`
files at `buffer_shots` rows per part. Each temporary part has nonnull
`shot_index: int64` plus all metrics for the point: `logical_error: bool`
always, and for color-correlated, relifting, or perturbation also
`default_logical_error: bool`,
`better_weight_by_color_correlated_decoding: uint8`, and
`effect_by_color_correlated_decoding: uint8`. The historical metric filenames
are retained for all three modes. The baseline for relifting and perturbation
comes from their already computed ordinary r/g/b candidates; perturbation's
member 0 has the unmodified prior. `better_weight` means a strict reduction
in the selected common-prior score relative to those three candidates;
`effect_by` means a baseline failure rescued by the advanced decision.
Color-correlated decoding additionally writes `color_correlated_run: uint8`.
Its value is 0 when the three ordinary original-DEM corrections agree,
1 when exactly two agree, and 2 when all differ. These cases run 0, 3 and 9
extra guided candidates, respectively.
Relifting additionally writes `relift_run: uint8` with the same 0/1/2
baseline-multiplicity definition. Perturbation has no run-class sidecar.

Finalization streams parts into one two-column Parquet file per metric, with
the metric name as filename and data column. Every file has explicit nonnull
`shot_index: int64` covering `0..shots-1`, no pandas index, and the same metric
type as the temporary table. Final files are validated before publication;
`.buffer/` remains on failure and is removed on success. Point directories
and final files are never intentionally overwritten.

## YAML workflow scheduler API

`simulation.scheduler.run_scheduler(config, points, on_result)` accepts the
validated `WorkflowConfig` and expanded `ResolvedPoint` records. It uses a
`spawn` process pool and calls `on_result(WorkerResult)` in the main process as
each chunk finishes. The callback must consume or persist the bounded result
before returning. The scheduler writes no files and retains at most `workers`
chunk results. Its return value is a tuple of immutable `PointProgress` records.
The canonical runner connects this callback to `PointStorage` and finalizes
each point when its complete shot interval is available.

Scheduling visits ready points round robin. Each point first runs
`min(calibration_shots, shots, buffer_shots)` shots; only after that result returns can it
receive more work, including concurrent disjoint chunks. For later chunks,
`observed_sps = elapsed_seconds / shot_count` and
`sps = alpha * observed_sps + (1 - alpha) * previous_sps` (the first valid
observation initializes `sps`). Zero, nonfinite, or sub-resolution timing
retains the previous estimate or falls back to
`target_chunk_seconds / calibration_shots`. Chunk size is
`min(remaining_unscheduled, clamp(round(target_chunk_seconds / sps),
min_chunk_shots, max_chunk_shots))`, additionally capped by `buffer_shots` per
returned result. The initial calibration chunk is also capped by `buffer_shots`.

With `simulation.verbose=True`, one reporter prints aggregate progress after
each completed chunk and an estimated remaining time. ETA is unavailable
until every unfinished point has a timing estimate and displays
`ETA: estimating...`. Thereafter it is the sum
of `remaining_shots * seconds_per_shot` divided by
`min(workers, total remaining shots)`, an approximate worker capacity, not a
deadline. `verbose=False` suppresses routine progress output.

Chunk seeds use SHA256 of the point ID, then NumPy `SeedSequence` over the
master seed, digest words, and chunk ID. Shot intervals follow scheduling
decisions, and seeds are deterministic once chunk IDs are assigned. Machine
load, worker count, and timing can change adaptive chunk boundaries and the
exact random sample stream; schedule-independent bitwise replay is not claimed.

## YAML workflow worker API

`simulation.worker.WorkerInput(point_id, chunk_id, shot_start, shot_count,
seed, point)` is the immutable one-chunk request; `point` is a planned
`ResolvedPoint`, and `point_id` must match it. `run_chunk(input)` returns a
`WorkerResult` with the same identity and interval, `elapsed_seconds` for
construction/cache lookup, sampling and decoding, and `metrics`, a dictionary
of 1D arrays in shot order for `[shot_start, shot_start + shot_count)`.
`logical_error` is always boolean. If the resolved constructor enables color
correlated decoding, the result also contains boolean `default_logical_error`
and uint8 `better_weight_by_color_correlated_decoding` and
`effect_by_color_correlated_decoding` and `color_correlated_run`. The ordinary
baseline decodes the same
detectors. The weight flag compares the selected common-prior candidate with
the best of the three ordinary candidates under that same prior using exact
`<`; temporary candidate-generation weights are excluded. Effect is exactly
`default_logical_error & ~logical_error`.
For each extra color-correlated candidate, guide-selected original X/Z DEM
mechanism priors become `q**(1/color_correlated_b)` for stage 1. Stage 2
uses the unchanged base matrix and prior. Final selection always uses the
unchanged original X/Z DEM prior; that mode requires `original_dem`.
Set `decoders[].options.color_correlated_weight_basis: original_dem` to score
and select ordinary, color-correlated, relifting, or perturbation candidates by
their mapped correction under the unchanged pre-decomposition X/Z DEM prior.
The default for other modes is `stage2`. For ordinary `concat_mwpm`, this option changes only
the final comparison among the three color corrections; both matching stages
still use their usual priors. For color-correlated decoding, the better-weight
flag compares the twelve candidates with the ordinary three using the same
selected basis. Saved runs cannot be reinterpreted under a
different basis without decoding their shots again.

To save both ordinary bases in one run, use `type: concat_mwpm` with
`color_correlated_weight_basis: original_dem` and
`type: concat_mwpm_stage2_base` with `color_correlated_weight_basis: stage2`.
The latter is a workflow label for the same ordinary decoder; its basis is
validated. These are separate points with point-derived sampling seeds, so
the two saved LER rows are not a paired same-shot comparison.

The worker holds at most four circuit/decoder pairs in a per-process LRU cache
and writes no files. The scheduler uses multiprocessing `spawn` and bounds
submitted chunks to the configured worker count.

`type: tesseract` selects the optional Tesseract Python decoder. Install a
compatible `tesseract_decoder` build in the simulation environment first.
Its `options` map directly to `TesseractConfig` arguments except `dem`, which
the worker supplies as the unchanged `ColorCode.dem_xz`. For example:

```yaml
- type: tesseract
  options:
    det_beam: 5
    beam_climbing: false
    det_order_method: Index
```

The worker compiles Tesseract once per cached point and decodes each sampled
syndrome with its single-shot API. It saves only the resulting
`logical_error.parquet`. An explicit X or Z `temp_bdry_type` is required for
noise configurations where `ColorCode` would otherwise choose Y. Tesseract
points do not accept `decode_options` or color-correlated modes. Sweep points
use distinct shot seeds, so LER comparisons across decoder types are unpaired.

## YAML workflow planning API

`load_workflow_config(path)` and `parse_workflow_config(mapping)` return
an immutable `WorkflowConfig`; `plan_points(config)` returns immutable
`ResolvedPoint` records after checking every per-point directory name for
collisions. `make_noise_model(name, p)` maps `bitflip`, `depol`, and `uniform`
to the corresponding native `color_code_stim.NoiseModel` constructor.
`point_directory_name(point)` gives the exact point component, and
`run_directory_name(config, timestamp)` formats
`YY_MM_DD_HH_MM_SS_{hash8}`. Planning does not create directories or sample.

The eight-character run hash covers the validated semantic configuration,
including shots, worker/chunk settings, decoder options, verbose, and a
relative `output_root`. A relative root is an intentional destination choice;
an absolute root is excluded from the hash so equivalent configurations on
different machines retain the same identity. YAML comments and key order have
no effect. Duplicate expanded point paths are rejected before execution.

The saved-data notebook
`notebooks/circuit_level_swim_selection_strategies.ipynb` compares four
three-color circuit-level output strategies: ordinary selected color, minimum,
maximum and arithmetic mean. Its reusable implementation is
`analysis/swim_selection.py`. It runs distribution, conditional-LER and
post-selection separately for each strategy while preserving the same ordinary
hard decisions and failure labels. It does not sample new shots or define a
production aggregation rule.

Use the Conda environment **color_code_so**. The main package contains experiment,
storage and analysis code. The modified external decoders stay in their own
repositories; installing public PyMatching alone does not provide the required API.

From the project root:

```bash
conda activate color_code_so
# If creating the environment on another machine:
# conda env create -f environment.yml
DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=4 python -m pip install --no-build-isolation -e external_libs/PyMatching -e external_libs/color-code-stim -e '.[test,notebook]'
python -m ipykernel install --user --name color_code_so --display-name 'Python (color_code_so)'
python -m pytest tests/phase2b -q
python -m color_code_softoutput.experiments.phase_2a_test --smoke --workers 4
# After smoke review and throughput estimation:
python -m color_code_softoutput.experiments.phase_2a_test --shots 100000 --workers 4 --batch-size 5000
```

The fixed factory uses T=1, triangular 6.6.6, tri_optimal, and only bit-flip noise.
Distances are 3,5,7,9,11,13. The explicit fallback grids are near-threshold
0.076,0.080,0.084,0.088 and subthreshold 0.02,0.03,0.04,0.05. These are project
approximations, not a recovered historical grid. The paper and current/historical
notebooks were inspected; they did not supply the exact original p-grid.

The historical paper version applied bit-flip noise twice; the repository reports
a correction from an 8.2% to about 8.6% threshold and roughly halved LER. This study
uses the corrected local commits. It targets qualitative scaling, not exact old
numbers. See `refs/REFERENCES.md` for the inspected source ledger.

`run_experiment(Phase2ATestConfig(...))` returns a `RunResult`. Shards are written
atomically as batches complete; at most twice the worker count is pending. Stable
config/batch/shot identities and SeedSequence-derived seeds make serial and
parallel schedules equivalent. Changing batch size changes sampling and is recorded.
Resume is intentionally not implemented: failed runs preserve completed shards and
an exception manifest. Restart in a new directory; never stitch runs implicitly.

`Phase2ADataset` projects/filter Parquet columns. `audit_run(dataset)` independently
validates all shards and summary counts, checks current source identities, and
replays one full batch. `standard_analysis(run_directory)` creates PDF/PNG plots,
Parquet analyses and `PRIOR_WORK_REPRODUCTION.md`. Classes for each analysis also
work separately; examples are in `notebooks/phase2a_getting_started.ipynb`.

Publication figures use rsmf and RevTeX dimensions and fail if TeX is unavailable.
System requirements: a TeX distribution with revtex4-2, type1cm, cm-super/type1ec,
and dvipng. `RevtexFigureStyle(test_mode=True)` is an explicit CI-only alternative.
Point sizes convert TeX to Matplotlib with 72/72.27. The style restores rcParams.

Statistics use 99% Wilson intervals with retained counts. Conditional-LER,
post-selection (including forced gap), and physical-error-rate plots show
these intervals as shaded bands in the series color with `alpha=0.2`.
Zero-failure upper bounds remain visible; zero lower bounds clip at the
logarithmic axis boundary without altering stored values. Scaling is unweighted
log-OLS with Student-t intervals and explicit exclusion of zero-failure points;
three positive-rate points are required. Crossing is minimum cross-distance
variance of LOWESS (fraction 2/3, it=3) curves interpolated onto 2001 common-grid
points. Endpoint minima are flagged, and no threshold CI is fabricated. Four-point
LOWESS and distances only through 13 limit the inference.

Conditional logit fits predict success: logit P(success|phi)=k phi+l. Degenerate,
separated and nonconverged fits retain explicit statuses and NaN coefficients.
These empirical fits do not establish posterior calibration. Near-discrete values
are grouped after rounding to 10 decimals for distributions/conditional rates;
continuous scores use configurable histogram bins. Empty bins are omitted.

Frequency, conditional-LER, and post-selection plots use a logarithmic y-axis
by default. Zero empirical rates remain in the saved tables with their Wilson
limits, but are omitted from the log-scale artists because zero has no finite
logarithm. The Lee Fig. 3 near-threshold plot deliberately stays linear in y;
the sub-threshold reproduction uses log-log axes. Coefficient plots stay linear
because fitted coefficients can be signed.

Postselection uses every exact unique metric value as a threshold, sorted in
ascending order, without binning or rounding by default. At threshold `t`, scores `< t`
are aborted and scores `>= t` are retained together, including all exact ties.
Tables include the threshold, abort rate, retained counts, residual LER and Wilson
limits; the minimum threshold gives no abort. Figures connect all positive-rate
points with circle markers and lines, without subsampling.
All three plot methods accept `round_digits=None` (the existing numerical
behavior) or an integer number of decimal places. For example,
`round_digits=1` applies Python `round(value, 1)` to each actual score before
counting, fitting or thresholding; negative digits are also supported. Auto
bins then group every distinct rounded score, while explicit histogram bins
still take precedence. Post-selection keeps whole ties in the rounded scores,
including for forced gap. This never modifies stored shot values. Rounded
figure/table filenames include `_roundN`, keeping them separate from defaults.
The circuit notebook exposes one `round_digits` setting for its three plots.

Swim series use `YlGn`; three series take colors at .4, .7 and .95 in selection
order. Forced-gap series use `Blues` at the same positions. Distribution scatter
markers remain `o` (success) and `x` (error), with alpha=.75.

Swim uses ordinary failures; forced_gap uses comparative failures.
The latter is an alias of the existing comparative logical gap, also stored under
its source name for verification. Selected swim always uses the ordinary decoder's
chosen color, never minimum-over-colors aggregation.

The backend convention remains uncertified final defect metric balls. Missing
nonnegative optimal odd-cut variables and exact primal/dual equality prevent
applying the Phase-1 representative bound to these numerical scores. No full
three-color logical-gap, LLR, or circuit-level theorem is claimed.
