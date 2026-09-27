# Canonical YAML workflow: Task 06 final audit (2026-09-27)

## Architecture and contracts

- `simulation.config`: one strict YAML parser and immutable simulation, chunking,
  sweep, and decoder settings. Required top-level sections are `simulation`,
  `chunking`, `sweep`, and `decoders`; `color_code_options` is optional.
- `simulation.planner`: Cartesian expansion, immutable `ResolvedPoint` IDs,
  path collision preflight, and the sole canonical run/point path formatters.
- `simulation.noise`: `bitflip -> NoiseModel(bitflip=p)`,
  `depol -> NoiseModel(depol=p)`, and
  `uniform -> NoiseModel.uniform_circuit_noise(p)`.
- `simulation.worker`: one bounded chunk, ordinary same-shot baseline when
  correlated decoding is enabled, and no file writes.
- `simulation.scheduler`: spawn pool, per-point calibration, round-robin
  dispatch, dynamic refill, EWMA chunk sizing and ETA. `chunk_seed` validates
  its arguments and delegates to the shared historical `batch_seed` recipe.
- `simulation.workflow_storage`: main-process bounded temporary parts and
  validated per-point final Parquet files. `simulation.runner` preflights all
  points, connects scheduler to storage, and writes one `run_log.json`.
  `simulation.cli` and `scripts/run_experiment.sh` expose the runner.

The YAML schema and runnable example are in the root README. Run roots are
`YY_MM_DD_HH_MM_SS_{hash8}`. Point directories are
`decoder_type={decoder_type},circuit_type={circuit_type},d={distance},r={rounds},p={physical_error_rate},noisemodel={noise_model},cnot_schedule={cnot_schedule}`.
`p` uses Python `.12g` formatting. The hash covers the validated semantic
configuration, including a relative output root, but omits an absolute output
root for location-independent identity. Existing roots and point directories
are never silently overwritten.

Ordinary points publish only `logical_error.parquet`. Correlated points also
publish `default_logical_error.parquet`,
`better_weight_by_color_correlated_decoding.parquet`, and
`effect_by_color_correlated_decoding.parquet`. Each final file has exactly
`shot_index: int64` (nonnull) and one nonnull metric: Boolean for the two
logical-error columns, uint8 for the two correlated flags. All indices are
contiguous `0..shots-1` and aligned across the four files. No final files are
per chunk. Temporary parts and out-of-order chunks reside under `.buffer/`,
which is removed after successful finalization. The only persistent metadata
file is `run_log.json`; failures retain incomplete point buffers for diagnosis.

Calibration sends `min(calibration_shots, remaining, buffer_shots)` shots per
point. Observed `sps = elapsed_seconds / shot_count`; the first valid
observation initializes it, and later observations use
`sps = alpha * observed_sps + (1-alpha) * previous_sps`. Invalid timing
retains the prior estimate or uses `target_chunk_seconds/calibration_shots`.
Normal chunks use `min(remaining_unscheduled, clamp(round(target_chunk_seconds
/ sps), min_chunk_shots, max_chunk_shots))`, capped by `buffer_shots`.
After every completion the scheduler fills free worker slots. ETA is absent
until all unfinished points have estimates. Then it is
`sum(remaining_shots * sps) / min(workers, total_remaining_shots)`;
`ETA: estimating...` and `ETA: ~ HH:MM:SS` are display forms, not deadlines.
`simulation.verbose: false` suppresses routine progress.

Each chunk uses uint64 `SeedSequence([master_seed,
*little_endian_uint32(SHA256(point_id)), chunk_id])`. Assigned chunk IDs
have stable seeds, but runtime-dependent chunk boundaries can change exact
shot streams across machines or worker counts. The old fixed-grid research
runner retains its own rich shard schema, batch replay and analysis entry
points; it is explicitly historical rather than a second YAML parser or
canonical runner. A wrapper cannot delegate those saved-data contracts to
minimal canonical Parquet output without changing their scientific metrics.
Soft-output calculations remain in their existing decoder/API paths. The
canonical output stores only the four required experiment metrics.

## Cleanup and acceptance

Source search found one YAML parser (`config.load_workflow_config`), one
canonical point/run path formatter pair, one shared seed recipe, and one
adaptive scheduler. Old batch-shard storage is imported only by historical
research experiments. The root README labels fixed Phase-2A grids as
historical. No new persistent metadata format was introduced.

The focused tests cover YAML validation, sweep/path collisions, all three
native noise mappings, multiple named decoders, worker pairing and metric
types, adaptive calibration/refill/ETA, out-of-order bounded storage, exact
final schemas/indices, quiet and verbose runner modes, and no-overwrite and
failure behavior. The main test suite includes existing soft-output,
circuit-level, simulation and analysis tests. Decoder tests run in the local
`color-code-stim` checkout. Only smoke-scale runs were executed.

Commands and results:

```text
conda run -n color_code_so env PYTHONPATH=src:external_libs/color-code-stim/src python -m pytest tests -q
246 passed
conda run -n color_code_so env PYTHONPATH=src:external_libs/color-code-stim/src python -m pytest tests/phase2b/test_workflow_planning.py tests/test_simulation_worker.py tests/test_simulation_scheduler.py tests/test_simulation_workflow_storage.py tests/test_simulation_runner.py -q
61 passed
(from external_libs/color-code-stim) conda run -n color_code_so env PYTHONPATH=src python -m pytest tests -q
127 passed, 2 existing skips
conda run -n color_code_so env PYTHONPATH=src:external_libs/color-code-stim/src ./scripts/run_experiment.sh configs/example.yaml
32 requested shots, 2 points; completed under results/26_09_27_13_21_20_574e38e7
conda run -n color_code_so env PYTHONPATH=src:external_libs/color-code-stim/src ./scripts/run_experiment.sh /tmp/color_code_task06_sweep.yaml
8 requested shots across d=3,5 and p=0.001,0.002; completed under /tmp/color_code_task06_results/26_09_27_13_21_43_2d6fa82b
```

Output inspection confirmed the example's ordinary point has one 16-row
final file and its correlated point has four aligned 16-row final files. The
2-by-2 sweep produced four ordinary point directories with one two-row final
file each. Both runs have one JSON log and no surviving `.buffer/` directory.

The two decoder skips are pre-existing. No mathematical definition, decoder
source, or legacy research data was changed. The outer pipeline created
checkpoint commits; no push or merge was performed. The historical
circuit-memory source snapshot includes the implementation prompt when it is
available locally and also runs without it in a fresh checkout, where
`prompts/` is Git-ignored. Both end-to-end cases pass.
