# Reproducible paired code-capacity study

## Canonical YAML simulation

Run `./scripts/run_experiment.sh configs/example.yaml` in `color_code_so`, or
`python -m color_code_softoutput.simulation.cli --config configs/example.yaml`.
The example requests 16 shots for each of two d=3 uniform-noise points.
The runner validates and constructs every point before creating a timestamped
run directory. It writes one `run_log.json`, streams completed chunks into
bounded point storage, and finalizes each point when its shots are complete.
Successful points contain one Parquet file per metric and no `.buffer/`.
Existing notebook experiment entry points remain historical and unchanged.

## Saved color-correlated run analysis

`analysis.color_correlated.ColorCorrelatedRun(run_path)` reads the canonical
`run_log.json` and planned point directories. `catalog` previews available
conditions; `summary(filter=...)` streams each selected Parquet metric into
per-point shot/failure counts and logical error rates. `count_table(filter=...)`
reports the two color-correlated flags per experiment condition, with missing
values for ordinary decoder points. `plot_ler(filter=..., group_by=[...])`
plots physical versus logical error rate with 99% Wilson bands. The first
group key controls color and the optional second key controls marker. The
legend is a boxed grid above a separately sized plot. Set `yscale="log"`
or `"linear"`; zero-failure points use 0.5/shots only for log-axis display,
while the returned table keeps their measured rate of zero. Other varying
conditions must be fixed by `filter`. See
`notebooks/color_correlated_decoding.ipynb` for an editable example.
With `baseline_compare=True` and `decoder_type` in `group_by`, the plot also
adds `decoder_type=baseline` from each selected color-correlated point's
`default_logical_error.parquet`. This uses the same shots as that point's
`logical_error.parquet`; the returned plot table records `metric` and
`source_decoder_type`. Ordinary `concat_mwpm` points remain separate samples.
For `noise_model=uniform`, `logical_error_rate` and its Wilson limits are
reported per round as `1 - (1 - P_fail) ** (1 / rounds)`; the measured
whole-experiment rate remains in `logical_error_rate_total`. The plot ignores
`rounds` as a legend condition, so `rounds: distance` works with distance
and decoder type as the two grouping keys. Multiple round counts for the
same plotted condition still require a separate selection.

## YAML workflow point storage

`simulation.storage.PointStorage(point, point_dir, buffer_shots)` creates one
new point directory whose name matches `point_directory_name(point)`.
Call `accept(WorkerResult)` in the scheduler's main-process callback and
`finalize()` after all point chunks complete. The YAML runner handles this in
its scheduler callback.
Overlapping or duplicate intervals are rejected. Out-of-order chunks spool
under `.buffer/`, while contiguous rows flush as numbered `part_*.parquet`
files at `buffer_shots` rows per part. Each temporary part has nonnull
`shot_index: int64` plus all metrics for the point: `logical_error: bool`
always, and for color-correlated decoding also
`default_logical_error: bool`,
`better_weight_by_color_correlated_decoding: uint8`, and
`effect_by_color_correlated_decoding: uint8`.

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
`effect_by_color_correlated_decoding`. The ordinary baseline decodes the same
detectors. The weight flag compares the selected common-prior candidate with
the best of the three ordinary candidates under that same prior using exact
`<`; temporary candidate-generation weights are excluded. Effect is exactly
`default_logical_error & ~logical_error`.
For each extra color-correlated candidate, guide-selected mechanisms are
conditioned in a temporary copy of the pre-decomposition X/Z DEM. That DEM
is decomposed anew for the target color before both matching stages run.
Set `decoders[].options.color_correlated_weight_basis: original_dem` to score
and select color-correlated candidates by their mapped correction under the
unchanged pre-decomposition X/Z DEM prior. The default is `stage2`. The
weight flag always compares all twelve candidates with the ordinary three
using the same selected basis. Saved runs cannot be reinterpreted under a
different basis without decoding their shots again.

The worker holds at most four circuit/decoder pairs in a per-process LRU cache
and writes no files. The scheduler uses multiprocessing `spawn` and bounds
submitted chunks to the configured worker count.

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
