# Monotone-Y signed-gap sampling and analysis

The user-authorized simulation integration uses the ordinary `color_code_so`
environment. Start with
[`notebooks/monotone_y_getting_started.ipynb`](../../notebooks/monotone_y_getting_started.ipynb).
It mirrors the current path-gap notebook's settings: d=9,13,15, p=.04/.05,
1,000,000 shots per point, eight workers, batch size 2,000, master seed 0.
`RUN_NEW_EXPERIMENT=False` initially loads the latest completed monotone-Y run.
Set it to True to sample; `SMOKE=True` reduces the configured grid to 128
shots per point. The full six-million-shot study was not launched during
implementation. The original path-gap notebook and saved runs are preserved.

## Definition and scope

The public feature adapter computes
`S_Y(E) = min_{L in Y_right} [W(E xor L) - W(E)]` on each decoder's **final**
physical correction. For this experiment, `w_q=log((1-p)/p)` and the circuit
has one independent data-X layer on a triangular Z-memory patch, one round,
`tri_optimal`, odd d in the shared simulation configuration's range 3–15.
The underlying geometry/evaluator also supports larger distances; this
experiment deliberately retains the shared configuration's distance bound.

The accepted geometry certifies monotone-tail separation, permitting exact
minimization within the specified Y family. This upper-bounds the
correction-relative unrestricted logical minimum. Equality with a full
logical-class gap, posterior calibration and post-selection competitiveness
remain unproved. See [theory audit](MONOTONE_Y_THEORY_AUDIT.md) and
[metric documentation](../../external_libs/color-code-stim-monotone-y/docs/monotone_y_signed_gap.md).
Scores stay signed; there is no absolute value, zero clipping, failure-label
sign change, or selected-color rule for this metric.

## APIs

```python
from color_code_softoutput.experiments.monotone_y_test import (
    MonotoneYTestConfig, run_experiment,
)
from color_code_softoutput.analysis.monotone_y import (
    MonotoneYDataset, audit_run, matched_retention, compare_postselection,
)

config = MonotoneYTestConfig(
    distances=(9, 13, 15), near_threshold_ps=(), subthreshold_ps=(.04, .05),
    shots_per_point=128, batch_size=64, num_workers=2, master_seed=0,
)
run = run_experiment(config)
data = MonotoneYDataset(run)
audit = audit_run(data, replay=True)
selection = dict(distance=[9, 13, 15], physical_error_rate=.04)
matched = matched_retention(data, **selection)
comparison = compare_postselection(data, **selection)
```

Use a normal `if __name__ == '__main__':` guard when invoking the parallel
runner from a standalone Python script. The notebook can call it directly.
The CLI retains the shared API default grid, d=5,7,9,11,13,15 and ten p values,
which differs from the current notebook's custom six-point grid:

```bash
conda run --no-capture-output -n color_code_so python \
  -m color_code_softoutput.experiments.monotone_y_test \
  --smoke --workers 2 --batch-size 64 --seed 0
```

This command generates 7,680 shots; omitting `--smoke` uses 100,000 shots per
point by default. The reusable config inherits the path-gap infrastructure
defaults (2,000 shots/batch, six workers, seed 20260912321). The notebook
explicitly supplies the user's settings above.

## Pairing, storage and replay

Both decoders see the same sampled detector data. The comparative bookkeeping
input is zero, never the sampled observable. The true observable is used only
to label failures. Each final correction is passed to `MonotoneYGapAdapter`
after ordinary hard decoding. Array immutability is checked; a bounded prefix
is decoded again to check predictions, weights, selected colors and final
corrections. These checks are separate from recorded decode/metric timings.

| Score column | Failure label |
|---|---|
| `ordinary_monotone_y_gap` | `ordinary_logical_error` |
| `comparative_monotone_y_gap` | `comparative_logical_error` |
| `forced_gap` | `comparative_logical_error` |

Shot schema version 1 records `metric_version="monotone_y_signed_v1"`, stable
config/batch/shot IDs, uint64 batch seeds, physical parameters, actual observable,
and both decoders' predictions, selected colors, solution weights, physical
correction weights and minimizing root/template IDs. A root ID is a canonical
physical **column index**, not a circuit qid or decoder color. Template IDs
index the archived metric's geometry construction. The decoder source and
metric source snapshot permit reconstructing these diagnostics; full witness
supports are not saved per shot.

The worker caches code/adapter objects and the adapter maps/scores in chunks
of at most 256 shots. The existing bounded process scheduler and atomic,
compressed Parquet writer are reused. Every new timestamped directory has
shot shards, raw-count summary, batch timings, configuration, actual imported
package/repository provenance, source hashes and `source_snapshot.zip`.

`require_monotone_y()` loads only the feature metrics/config modules from
`external_libs/color-code-stim-monotone-y` under a private namespace. It does
not replace installed `color_code_stim`, modify `sys.path`, enable SWIM, or
change PyMatching. No metric algorithm is copied into the simulation package.
The external metric/decoder sources were unchanged by this integration.

`audit_run` validates every shard's schema and numerical/failure invariants,
checks all expected batch/shot identities and summary counts, and replays the
first batch of **each** (d,p) when requested. This is not a replay of every
batch. It reports source drift separately from data integrity/replay. Exact
reproduction also requires the same batch size and compatible environment,
not just the same seed. An old SWIM/path-gap dataset lacks these columns and
must not be relabelled as monotone-Y data.

## Shared analyses

The notebook provides fixed-p/fixed-d distributions, success/failure markers,
optional forced-gap overlay, conditional LER with empirical logistic fits,
fit-parameter plots, hard-decoder LER/scaling diagnostics, threshold
post-selection, matched-retention tables and quantitative comparison reports.
The subthreshold-only notebook grid explicitly produces unavailable crossing
and insufficient scaling-fit statuses, rather than inventing a threshold.

Use `metric="ordinary_monotone_y_gap"` or `"comparative_monotone_y_gap"` in
`SwimDistanceDistributionPlotter` and `ConditionalLERAnalyzer`, and explicit
`metrics=(..., "forced_gap")` in `PostSelectionAnalyzer`. The class name of
the shared distribution plotter is historical; its labels and saved filenames
identify the actual metric. Monotone-Y uses green shades, forced gap blue.
All plots and reports use the score's associated hard-decoder failure label.

Threshold curves retain whole ties. Separate matched-retention/abort tables
split only boundary ties by stable shot IDs, independently of outcomes.
Whole-tie reports give actual attainable abort rates, which may differ between
metrics. Default ranking uses unrounded scores; optional `round_digits` applies
to actual scores. Wilson bands are 99% pointwise LER intervals, not confidence
intervals for differences or ratios. Zero-reference ratios stay undefined.
The configurable 1.25 margin and low-count warnings are descriptive, not a
statistical equivalence test. Reports live in `run/monotone_y_comparison/`.

## Validation

Focused integration tests verify direct physical witness costs, syndrome and
logical parity, unchanged hard decisions and installed imports, signed storage,
exact serial/parallel shots and scores, all-point first-batch replay, source
snapshots, explicit failure associations, corruption detection, raw-count
post-selection accounting, whole ties, and the subthreshold-only analysis.
Acceptance commands and the bounded saved run are recorded in `STATUS.md`.

Acceptance: 185 main-project tests pass, including seven new integration
checks. Three targeted plot regressions pass after the final legend layout
adjustment. All 11 notebook code cells execute in `color_code_so` against
`results/20260919_120559_210504_monotone_y_test` (768 shots, 12 batches, six
first-batch replays). Final plots and the report are saved there. The layout
adjustment is the sole source drift since sampling; it changes no numbers.
The run preserves the original sampling snapshot and separately archives
final analysis sources. Logs/hashes: [acceptance evidence](monotone_y_experiment_evidence/acceptance.json).
