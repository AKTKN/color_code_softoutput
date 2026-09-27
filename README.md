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

Ordinary points produce only `logical_error.parquet`. Correlated points produce
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

## Setup

This project uses modified decoder forks with APIs that are absent from the
standard PyMatching and color-code-stim releases. Clone them into the ignored
`external_libs/` directory before running the code-capacity and circuit-level
SWIM workflows:

```bash
git clone https://github.com/AKTKN/color_code_softoutput.git
cd color_code_softoutput
mkdir -p external_libs
git clone --branch phase2a/swim-distance https://github.com/AKTKN/PyMatching.git external_libs/PyMatching
git clone --branch phase2a/swim-distance https://github.com/AKTKN/color-code-stim.git external_libs/color-code-stim
conda env create -f environment.yml
conda run -n color_code_so env DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=4 python -m pip install --no-build-isolation -e external_libs/PyMatching -e external_libs/color-code-stim -e '.[test,notebook]'
conda run -n color_code_so python -m pytest tests -q
```

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
