# color-code-softoutput

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

The stage-2 prior option requires the updated `color-code-stim` checkout on
`phase2a/swim-distance`. After cloning, select it with
`git -C external_libs/color-code-stim checkout phase2a/swim-distance`
before installing the editable package.

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
