# color-code-softoutput

Global DEM BP predecoding is available on
`codex/global-bp-predecoding-20260929` in this repository and both external
decoder/backend repositories. Set `decode_options.bp_predecoding: true` and
optionally `bp_prms: {max_iter: 10}`. See
[`configs/global_bp_example.yaml`](configs/global_bp_example.yaml) and the
[implementation report](notes/support/global_bp_predecoding_20260929/report.md).
The workflow adds boolean `bp_converged.parquet`; all concatenated metrics
are null on converged shots. Analysis explicitly reports statistics over BP
nonconverged shots and the physical/converged shot counts.

For this isolated checkout, activate `color_code_so`, install `ldpc>=2,<3`,
and select its sources without changing the installed original checkouts:

```bash
export PYTHONPATH="$PWD/src:$PWD/external_libs/color-code-stim/src:$PWD/external_libs/PyMatching/src"
./scripts/run_experiment.sh configs/global_bp_example.yaml
```

Native BP perturbation requires the compiled backend from this branch. Build
it from `external_libs/PyMatching` with `env -u DEBUG
CMAKE_BUILD_PARALLEL_LEVEL=4 python setup.py build_ext --inplace`; its submodules
must be initialized. The local `color_code_so` environment has ldpc 2.4.1.

The YAML simulation now defaults to requested scalar metrics with
`full_output=False`. The decoder returns only the `(shots,)` arrays required
by the saved point schema; candidate diagnostics are available through an
explicit `decode_options: {full_output: true}`. Predictions, metric meanings,
Parquet columns and perturbation sampling are preserved. See
[`simulation output contract`](src/color_code_softoutput/README.md#yaml-workflow-point-storage).
The [validation and measurement report](notes/support/compact_experiment_metrics_20260929/report.md)
records identical saved values and reduced allocation peaks, with mixed decode
time results.

Native stage-1 perturbation is available through
[`configs/native_stage1_perturbation_comparison.yaml`](configs/native_stage1_perturbation_comparison.yaml).
Set `stage1_perturbation: true` under a `type: perturbation` decoder; M includes
the unperturbed member. Stage 2 always uses cached original priors. False keeps
the original-DEM perturbation workflow. The new mode changes candidate
generation, while final scoring and existing output semantics are retained.

Use the `codex/native-stage1-perturbation-20260929` branches of both external
repositories for this option. In the `color_code_so` environment, rebuild the
PyMatching backend with
`CMAKE_BUILD_PARALLEL_LEVEL=4 python -m pip install --no-build-isolation -e external_libs/PyMatching`.
The decoder must also be imported from the corresponding editable checkout.
See the decoder's
[native mode guide](https://github.com/AKTKN/color-code-stim/blob/codex/native-stage1-perturbation-20260929/docs/native_stage1_perturbation.md)
and PyMatching's
[API guide](https://github.com/AKTKN/PyMatching/blob/codex/native-stage1-perturbation-20260929/docs/native_perturbation.md).

The workflow saves the resolved native seed and RNG scheme version and uses
absolute per-point shot indices, so worker scheduling/cache reconstruction
does not change perturbations for the same supplied shots. Stim sampling and
its existing chunk-seed policy remain unchanged. Timing reports separate
same-prior-specification acceleration from comparisons against the old mode.
The [implementation and timing report](notes/support/native_stage1_perturbation_20260929/report.md)
records regression tests, cold/warm timings, graph counts, memory and exact
dependency commits. YAML aliases use independent physical samples; the
report includes the pre-resampling fixed-ensemble measurements as a separate
baseline. Native decoder timings use identical presampled shots within each
measured condition.

## Canonical YAML simulation

Run in the `color_code_so` environment. This minimal configuration sweeps two
distances at one physical error rate:

```yaml
simulation:
  output_root: results
  shots: 1000
  workers: 4
  master_seed: 20260927
  buffer_shots: 5000
  verbose: true

chunking:
  calibration_shots: 8
  target_chunk_seconds: 1.0
  min_chunk_shots: 1
  max_chunk_shots: 4096
  throughput_ema_alpha: 0.25

sweep:
  distance: [3, 5]
  physical_error_rate: [0.001]
  noise_model: [uniform]
  rounds: distance
  circuit_type: [tri]
  cnot_schedule: [tri_optimal]

color_code_options:
  temp_bdry_type: Z

decoders:
  - type: concat_mwpm
    options:
      enable_colorcorrelated_decoding: false
      comparative_decoding: false
      # Optional: compare ordinary color corrections using the base X/Z DEM.
      # The default is the historical stage-2 matching-weight comparison.
      color_correlated_weight_basis: original_dem
    decode_options:
      colors: all
  - type: concat_mwpm_stage2_base
    options:
      color_correlated_weight_basis: stage2
    decode_options:
      colors: all
```

Save it as `configs/example.yaml` (the repository's example file is a smaller
ordinary/correlated smoke), then run:

```bash
./scripts/run_experiment.sh configs/example.yaml
```

Sweep axes accept scalar or list values; `rounds: distance` sets rounds to each
point's distance. Named decoder configurations are selected with `decoders`.
Noise is passed to the native decoder exactly as follows:

```text
bitflip -> NoiseModel(bitflip=p)
depol   -> NoiseModel(depol=p)
uniform -> NoiseModel.uniform_circuit_noise(p)
```

The run root is `YY_MM_DD_HH_MM_SS_{hash8}` under `output_root`, where the
hash covers the validated semantic configuration. Each point directory is:

```text
decoder_type={decoder_type},circuit_type={circuit_type},d={distance},r={rounds},p={physical_error_rate},noisemodel={noise_model},cnot_schedule={cnot_schedule}
```

Ordinary points produce `logical_error.parquet`. Set
`decoders[].decode_options.compute_swim_distance: true` to additionally write
`swim_distance.parquet`. This accepts one-round triangular data-only bit-flip
points and closed triangular `rounds=distance` memory points with any of the
workflow's bit-flip, depolarizing or uniform noise models, subject to the
original DEM's graph and probability checks.
Set `decoders[].options.comparative_decoding: true` on ordinary concat MWPM
to write `logical_gap.parquet` instead. See
[the analysis notebook](notebooks/workflow_swim_soft_output.ipynb) for score
frequency points, conditional logical error probability and post-selection
scatter plots with Wilson shades, filters and groups. All three views accept
`metrics=["swim_distance", "logical_gap"]` for comparison; distribution errors
can optionally be displayed at negative scores.
Correlated points produce
that file plus `default_logical_error.parquet`,
`better_weight_by_color_correlated_decoding.parquet`, and
`effect_by_color_correlated_decoding.parquet`. Every final file has exactly two
nonnull columns: `shot_index: int64` and its filename's metric column.
`logical_error` and `default_logical_error` are Boolean;
`better_weight_by_color_correlated_decoding` and
`effect_by_color_correlated_decoding` are uint8. Indices cover `0..shots-1`
in every file. Files are per point, never per chunk. The main process uses
bounded temporary parts under `.buffer/` and removes that directory after a
successful point finalization. A run creates one `run_log.json`.

Each point starts with a calibration chunk. Measured `seconds_per_shot` is
updated by an exponential moving average with `throughput_ema_alpha`.
Subsequent chunk size is `min(remaining, clamp(round(target_chunk_seconds /
seconds_per_shot), min_chunk_shots, max_chunk_shots))`, also capped by
`buffer_shots`. Free worker slots are refilled as chunks finish. With
`simulation.verbose: true`, progress prints completed/total shots, percent,
active/configured workers, completed/total points, elapsed time, and ETA.
Before all unfinished points have timing information it prints
`ETA: estimating...`; the displayed `ETA: ~ HH:MM:SS` thereafter is estimated
from measured runtime, not a guaranteed completion time. Set `verbose: false`
to suppress routine progress.

Each chunk seed is a uint64 NumPy `SeedSequence` output from
`[master_seed, *little_endian_uint32(SHA256(point_id)), chunk_id]`. Seeds are
deterministic for assigned chunk identities. Adaptive chunk boundaries depend
on runtime, so machines or worker counts can produce a different exact random
stream. The scientific soft-output implementations remain available through
their existing APIs; this minimal canonical storage writes only the required
experiment metrics.

Research code for paired color-code soft-output experiments and analysis. The
Python package is in `src/color_code_softoutput/`; reproducible workflows are in
`notebooks/`, with tests in `tests/`. The mathematical notes and implementation
records are in `notes/`, `STATUS.md`, and `REVIEW.md`.

## Comparing decoder parameters by alias

The stage-2 prior option is available on `color-code-stim` main. Use its
updated `main` checkout when installing the editable package.

Give each decoder configuration a unique `decoder_alias`. `type` still selects
its implementation; the alias identifies the parameter variant in saved paths,
run logs, tables and plot legends. Omitted aliases default to the type in
analysis and retain the existing directory names and configuration hashes.
Repeated types need distinct aliases.

```yaml
decoders:
  - decoder_alias: Stage2_original_perturbation
    type: perturbation
    options: &perturbation_options
      enable_prior_perturbation: true
      perturbation_ensemble_size: 12
      perturbation_alpha: 1.0
      perturbation_seed: 20260927
      color_correlated_weight_basis: original_dem
      remove_non_edge_like_errors: true
      use_original_prior_for_stage2: true
  - decoder_alias: Stage2_perturbed_perturbation
    type: perturbation
    options:
      <<: *perturbation_options
      use_original_prior_for_stage2: false
```

`use_original_prior_for_stage2` defaults to `false`: both matching stages use
the perturbed X/Z DEM's color decomposition. `true` uses that decomposition
only for stage 1, then runs stage 2 with the original X/Z DEM's color
decomposition and its column order. Candidate selection uses unchanged base
priors in both modes. Member 0 remains ordinary decoding.

[configs/perturbation_stage2_comparison.yaml](configs/perturbation_stage2_comparison.yaml)
is a complete bounded comparison configuration. Run it with:

```bash
python -m color_code_softoutput.simulation.cli --config configs/perturbation_stage2_comparison.yaml
```

```python
from color_code_softoutput.analysis.color_correlated import ColorCorrelatedRun

run = ColorCorrelatedRun("results/<completed-run>")
run.summary({"decoder_alias": ["Stage2_original_perturbation",
                               "Stage2_perturbed_perturbation"]})
fig, ax, table = run.plot_ler(group_by=("distance", "decoder_alias"))
# Also supported: baseline_compare=True and plot_improvement_ratio(...).
```

LER, improvement-ratio plots and their separate legends default to
`group_by=("distance", "decoder_alias")`. Summary/count/effect tables retain
both alias and implementation type; all accept alias filters. Improvement
tables also expose `baseline_source_decoder_alias` and
`baseline_source_decoder_type`, so the numerator's source is explicit.
Paired variants each keep their own baseline; unpaired decoders identify the
representative baseline they use.

```python
selection = {"decoder_alias": ["Stage2_original_perturbation",
                               "Stage2_perturbed_perturbation"]}
ratios = run.improvement_table(physical_error_rate=0.03, filter=selection)
fig, ax, ratios = run.plot_improvement_ratio(physical_error_rate=0.03,
                                            filter=selection)
run.better_weight_table(selection)
run.effect_table(selection)
```

SWIM/logical-gap distribution, conditional LER and post-selection APIs in
`WorkflowSoftOutputRun` likewise accept `filter={"decoder_alias": ...}` and
`group_by=("decoder_alias",)` when those metrics were saved. Type-only LER
grouping requires filtering to one alias per type to avoid mixing variants.

Aliases and parameters participate in point identities and sampling seeds.
The adaptive YAML runner samples each alias independently; this is an LER
comparison, with each advanced decoder's baseline evaluated on its own shots.
The same `perturbation_seed` fixes the same perturbed-prior ensemble across the
two modes. For a paired physical-shot comparison, sample once with `ColorCode`
and pass that detector array to both decoder configurations directly.

## Reusing decoders from earlier runs

Compose a primary run with selected historical points using the existing
LER/improvement/table API. This reads the original files without copying
shots, resampling or pooling dates:

```python
from pathlib import Path
from color_code_softoutput.analysis.color_correlated_comparison import ColorCorrelatedComparison

root = Path("cluster_results")  # resolve relative to the repository root
run = ColorCorrelatedComparison(
    root / "26_09_28_15_33_34_7f861167",
    additional_sources=[{
        "run_directory": root / "26_09_28_14_38_26_779e2a31",
        "filter": {"decoder_alias": "tesseract"},
    }],
)
run.plot_ler(baseline_compare=True)
run.plot_improvement_ratio(physical_error_rate=0.03)
run.effect_table({"decoder_alias": "m16"})
```

The primary run is the figure-export destination and has priority when
choosing a representative baseline at matching distance, physical error
rate, noise model, rounds, circuit type and schedule. Paired decoders retain
their own saved baseline. Imported Tesseract has independent shots: its
ratio uses the preferred matching baseline and reports `baseline_paired=False`.
`source_run`/`data_directory` identify the original observations;
`baseline_source_run`/`baseline_source_decoder_alias`/`baseline_source_decoder_type`
identify the ratio numerator. Count/effect tables retain source provenance
and cannot invent paired effects for a decoder without paired sidecars.

`run.source_manifest` lists each source's selection and
`run.source_runs` exposes the underlying single-run readers/configurations.
Source filters use the usual parameter/alias keys. The reader rejects
duplicate alias/condition points, duplicate saved files, incompatible
recorded physical circuit options and different decoder settings sharing an
alias. It preserves each source's shot count and Wilson intervals.
To compare different configurations that share a saved alias, give the
additional source an analysis-only rename:

```python
{"run_directory": root / "<older-run>",
 "filter": {"decoder_alias": "tesseract"},
 "alias_map": {"tesseract": "tesseract_previous"}}
```

The original logs and metric files remain unchanged. Additional grid points
may be imported, but an improvement ratio requires an available baseline at
each plotted physical condition. Comparability checks use the settings
recorded in the saved logs; the canonical logs do not certify historical
cluster source versions. `notebooks/color_correlated_decoding.ipynb` now
uses the two-run example above; set `additional_sources = []` for one run.

## Setup

This project uses modified decoder forks with APIs that are absent from the
standard PyMatching and color-code-stim releases. The three repositories now
contain the required changes on their default branches. Clone the decoders into
the ignored `external_libs/` directory, including PyMatching's `pybind11`
submodule:

```bash
git clone https://github.com/AKTKN/color_code_softoutput.git
cd color_code_softoutput
mkdir -p external_libs
git clone --recurse-submodules https://github.com/AKTKN/PyMatching.git external_libs/PyMatching
git clone https://github.com/AKTKN/color-code-stim.git external_libs/color-code-stim
conda env create -f environment.yml
conda run -n color_code_so env DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=4 python -m pip install --no-build-isolation -e external_libs/PyMatching -e external_libs/color-code-stim -e '.[test,notebook]'
conda run -n color_code_so python -m pytest tests -q
```

`environment.yml` records Python 3.12 and the package versions used in the
local `color_code_so` environment. It does not embed editable installs, so
clone the repositories before the final `pip install`. PyMatching needs a
C++20-capable compiler, CMake and Ninja at install time. On a machine with an
existing environment, use `conda env update -f environment.yml --prune` before
reinstalling the three editable packages. Anaconda must be on `PATH` for these
commands; a site module or the full path to `conda` may be needed on a cluster.

### PBS cluster jobs

Create the environment and install the packages on the cluster first, using
the commands above. Then submit from the repository root, with the cluster's
Anaconda base directory and a YAML configuration:

```bash
qsub -v CONDA_BASE=/path/to/anaconda3,CONFIG_FILE=configs/example.yaml scripts/pbs_run_experiment.sh
```

The [PBS script](scripts/pbs_run_experiment.sh) activates `color_code_so` in
the batch shell and runs the YAML simulation. Adjust its `#PBS` resource lines
to the site's queue syntax and workload. Set `simulation.workers` in the YAML
to no more than the requested `ncpus`; the example requests two CPUs and uses
two workers. Set `simulation.output_root` to a writable shared or scratch path
for production runs. The default `results/` is relative to the submission
directory. The example script uses one node because the simulation uses local
processes and does not distribute work across nodes.

The path-gap, monotone-Y, and surface-code path-gap experiments use separate
feature checkouts and, in some cases, local work in progress. Their source
paths and validation state are recorded in `STATUS.md` and the corresponding
`notes/support/` reports. The command above sets up the main SWIM workflow;
it does not install those optional feature variants.

Start with `notebooks/phase2a_getting_started.ipynb` for code-capacity
experiments or `notebooks/circuit_level_getting_started.ipynb` for closed-memory
circuit experiments. The package-level usage guide is
[`src/color_code_softoutput/README.md`](src/color_code_softoutput/README.md).

## Repository contents

This repository tracks source code, tests, notebook documents, prompts, and
research notes. Local decoder checkouts, build outputs, caches, saved results,
and third-party reference PDFs and extracted paper text are excluded by
`.gitignore`. Generated notebook
outputs already embedded in the notebook documents are retained. The TeX source
for project notes is included; generated PDFs are not. GitHub publication is a
source release, not a PyPI upload or a claim of calibrated confidence scores.
