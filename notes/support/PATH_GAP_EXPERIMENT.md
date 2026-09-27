# Final-correction path-gap experiment

Entry point: [Getting Started notebook](../../notebooks/path_gap_getting_started.ipynb).
Implementation: `src/color_code_softoutput/experiments/path_gap_test.py` and
`src/color_code_softoutput/analysis/path_gap.py`.

## What is the same as the reference notebook?

The current executable defaults of `phase2a_getting_started.ipynb`, not its
historical 4.8-million-shot prose, are reproduced:

- d = 5, 7, 9, 11, 13, 15;
- subthreshold p = .02, .03, .04, .05;
- near-threshold p = .082, .084, .085, .086, .087, .088;
- 100,000 shots per point, 2,000 per batch, 6 workers, seed 20260912321;
- one round, triangular Z memory, tri_optimal, pure independent bit flips.

This is **6,000,000 physical shots**, each decoded twice, not two independent
sets of 6,000,000 shots. The sampling/seed recipe, streaming Parquet machinery,
plot style, conditional-LER fits, prior-work comparison and 99% Wilson intervals
are shared with the reference workflow. The new external checkout is based on
upstream main; it does not contain SWIM instrumentation. Old saved SWIM shots
are not silently reused or claimed to be bitwise paired with this new run.
Exact replay requires the same Stim version, batch size and compatible machine
instructions as well as the same seed.

## Environment and launch

**Current default (2026-09-19): use ordinary `color_code_so`.** No package
installation or environment switching is needed:

```bash
conda activate color_code_so
python -m color_code_softoutput.experiments.path_gap_test --smoke --workers 2
```

The notebook now selects **Python (color_code_so)**. Restart an already open
kernel once after this update. The installed SWIM decoder and modified
PyMatching remain unchanged. If the installed package has no metrics module,
`require_path_gap()` loads the existing feature worktree's metrics and config
under an isolated private namespace. It does not alter `sys.path`, the installed
`color_code_stim` module or its package search path, and does not copy the
algorithm. Worker processes perform the same automatic load. Both the active
decoder source and the separate metric source are recorded and archived.
The feature worktree must remain at `external_libs/color-code-stim-path-gap`.

For the full configured experiment, omit `--smoke`. Set `RUN_NEW_EXPERIMENT=True` in the notebook to launch sampling, or False
to analyze saved data. The user's existing toggle is preserved.

### Historical isolated environment (optional)

The feature package and original SWIM package share the same import name.
The original upstream-PyMatching validation used a separate environment.
It is **no longer required**. The following recreates that historical
acceptance environment and Jupyter kernel (the
temporary directory may disappear after a system cleanup):

```bash
cd /home/quantum_teresheys/workspace/color_code_softoutput
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m venv --system-site-packages /tmp/color-code-path-gap-env
/tmp/color-code-path-gap-env/bin/python -m pip install --ignore-installed --no-deps pymatching==2.3.1
/tmp/color-code-path-gap-env/bin/python -m pip install --no-deps -e external_libs/color-code-stim-path-gap
/tmp/color-code-path-gap-env/bin/python -m ipykernel install --user --name color-code-path-gap --display-name 'Python (color-code path gap)'
```

For a permanent environment, substitute a dedicated persistent venv path in
all four commands. The venv inherits the main package's analysis dependencies
from `color_code_so`. In a different installation, also install this workspace
editable with its `notebook` and `test` extras.

Quick smoke: full grid, **128 shots/point**, 7,680 physical shots total:

```bash
/tmp/color-code-path-gap-env/bin/python -m color_code_softoutput.experiments.path_gap_test --smoke --workers 2
```

Full experiment, only when explicitly launched:

```bash
/tmp/color-code-path-gap-env/bin/python -m color_code_softoutput.experiments.path_gap_test
```

Choose the score when launching a new run:

```python
run_directory = run_experiment(config, metric_version="v1")  # subtract full W(E)
# run_experiment(config, metric_version="v2")  # subtract path overlap
```

The notebook's `metric_version = "v1"` setting is passed to this keyword.
Canonical names `global_subtraction_v1` and `path_overlap_v2` also work.
The Python API and CLI retain v2 as their default for existing callers;
CLI selection is `--metric-version v1` or `--metric-version v2`.
`sample_batch(task, metric_version="v1")` provides the same switch for direct
batch calls. Invalid versions fail before sampling or creating a run directory.
Existing notebook grid, shot counts, seed, workers, sampling toggle and saved-run
selection are preserved; the toggle currently enables new sampling.

CLI overrides: `--shots`, `--workers`, `--batch-size`, `--seed`, `--output-root`,
`--metric-version`.
Custom scientific grids use `PathGapTestConfig` in Python. Each launch creates
a unique `results/*_path_gap_test/` directory; no automatic resume or overwrite.
Failed runs preserve completed atomic shards and record failure status.

Use **Python (color_code_so)** normally, or the optional dedicated kernel only
when explicitly testing the upstream-PyMatching environment. With sampling
disabled and `existing_run=None`, it opens the newest completed path-gap run. Set `existing_run` to pin
a particular dataset. Set `RUN_NEW_EXPERIMENT=True` for a new run;
`SMOKE=True` reduces only shots per point. `REPLAY=True` re-decodes the first
saved batch of every (d,p) using its recorded seed.

## Scientific and storage semantics

Both versions consume residual distances and physical correction weights from
the package's public `ColorCodePathGap` for the **final** physical correction E:

- `global_subtraction_v1`: `phi(E) = min_c [D_c(E) - W(E)]`.
- `path_overlap_v2`: `phi(E) = min_c [D_c(E) - W(E intersect L_c)]`.

The simulation adapter selects only the final subtraction and recomputes the
minimizing color (exact ties r, g, b). Graph construction, nonnegative residual
Dijkstra, igraph path ties, ordinary hard decoding and physical sampling are
identical in both modes. V1 uses the full physical correction weight, not the
ordinary decoder's solution weight. The feature checkout remains v2; the
adapter uses its public distance/weight diagnostics to compute v1 without
changing or duplicating the search algorithm.

New shards in either mode include canonical `metric_version` plus per-color
`ordinary_overlap_{r,g,b}` / `comparative_overlap_{r,g,b}`. Overlap fields always
mean the actual returned-path overlap; they are diagnostics for v1. Metadata
records the chosen formula and `shot_schema_version=2`. The configuration hash
continues to identify the sampling configuration, with metric version recorded
separately. Parallel workers and saved-seed replay receive the selected version.

Saved runs without a metric version remain `global_subtraction_v1` with their
original schema; their data and outputs are unchanged. The dataset reader
selects the appropriate schema. New versioned v1 and v2 runs support replay.
Unversioned legacy replay still requires its archived metric source; use
`replay=False` for those saved-data audits. The notebook displays the loaded
run's actual metric version; changing its selector never reinterprets old data.
New runs always write a fresh timestamped directory. Negative scores remain
signed and unclipped. These are heuristics, not exact logical-class gaps,
SWIM bounds, posterior LLRs, or calibrated confidence.

Stored fields have explicit names:

| Score | Failure label | Meaning |
| --- | --- | --- |
| ordinary_path_gap | ordinary_logical_error | Path gap of ordinary final correction |
| comparative_path_gap | comparative_logical_error | Path gap of comparative final correction |
| forced_gap | comparative_logical_error | Existing comparative logical gap |

Each decoder additionally stores prediction, hard-selected color, original
solution weight, physical correction weight, minimizing color, and all three
residual distances and per-color phi values. Hard-selected color is **not**
the path-gap minimizing color. Raw truth and stable shot/batch/seed identities
are retained. Metric calls are checked not to mutate decoder result arrays;
a prefix is re-decoded to check hard prediction, weight and color invariance.
Comparative inputs use an audited detector prefix plus a dummy zero detector;
the forced decoder overwrites it. Ground-truth observables are never provided
as decoder inputs.

`summary.parquet` stores raw count summaries. `timings.parquet` separates
per-batch model/cache setup, decoding and metric evaluation; these timings
exclude audit-prefix overhead and are not a rigorous decoder benchmark.
Metadata captures actual imported source paths, the feature worktree Git
state, upstream PyMatching version, original SWIM checkout states, environment,
configuration hash and source hashes. `source_snapshot.zip` archives the main
package and feature package Python sources. No original external source changes.

## Post-selection interpretation

### Quantitative comparison appended to the notebook

`analysis.path_gap_comparison.compare_postselection(dataset, **selection)`
saves `path_gap_comparison/{counts,comparison}.{csv,parquet}`, settings and
`REPORT.md`. It tabulates 0%, 1%, 2.5%, 5%, 10%, 15%, 20%, 25%, 30%, 50%
abort budgets, each decoder's baseline/residual LER, reduction rate
`1-residual/baseline`, reduction factor and residual-LER ratios to forced gap.
`competitive_margin=1.25` is a configurable descriptive convention, not a
noninferiority test. Counts below 20 trigger a warning, not a formal inference.
Zero denominators are undefined. Whole-tie-budget and exact matched-retention
tables are separate; check actual abort rates when interpreting the former.
The cell uses the existing `dataset` and `selection` without sampling. If the
earlier sampling cell has been enabled, run only the appended analysis cells.

Threshold curves retain `score >= threshold` and retain all exact ties together.
`round_digits=None` preserves raw thresholds. Distribution/conditional bins
retain the existing near-discrete grouping convention (10 decimal places);
this does not change raw score storage or post-selection thresholds. Set
`round_digits` explicitly and consistently if rounded thresholds are desired.

The separate matched-retention table uses 100%, 90%, 75%, 50% retained counts.
Only this table splits boundary ties by stable shot identity, independent of
logical outcome. Its tie rule is saved in each row. Compare ordinary path-gap
against forced gap as **two complete decoder/confidence pipelines**, not as
two scores of the same hard decision. Comparative path-gap versus forced gap
provides the same-hard-decoder comparison. Wilson bands are pointwise binomial
intervals, not simultaneous bands or intervals for paired differences. A zero
observed failure count is not proof of zero LER; its upper bound is retained.

The notebook saves signed-score distributions, conditional rates and logistic
fits, post-selection figures/tables and matched-retention tables. Logistic
fits are exploratory and may be unidentifiable on small smoke data. Larger
studies are needed to infer performance; the acceptance smoke is only a
functional/accounting check.

## Validation commands

```bash
/tmp/color-code-path-gap-env/bin/python -m pytest tests/phase2b/test_path_gap_experiment.py -q
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest tests -q
```

All tests, including feature integration and coexistence tests, now run in
`color_code_so` without environment-specific skips. The separate feature
environment remains optional for checking upstream-PyMatching compatibility.


## Overlaying the forced-gap distribution

The fixed-p distribution cell offers `include_forced_gap = True`. Its call to
`SwimDistanceDistributionPlotter.plot(..., metric="ordinary_path_gap",
include_forced_gap=include_forced_gap, normalize_frequency=True)` overlays
forced gap in blue and path gap in green. Both retain success/error markers;
each metric uses its own decoder failure labels and normalizes by all shots
in its parameter series. The existing near-discrete grouping removes tiny
floating-point splits (10 decimal places by default); the horizontal axis
remains the raw score, not a count of physical errors.

The returned table includes `metric` and `failure_column`. Overlay plots use
`_with_forced_gap` filenames, and the notebook saves the combined table as
`path_gap_with_forced_gap_distribution_counts.parquet`, preserving the previous
single-metric artifacts. Set the option to False for the original view. This
cell analyzes saved shots only.
