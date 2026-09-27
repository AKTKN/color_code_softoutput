# Simulation workflow refactor: architecture audit (Task 00)

2026-09-27. Planning only; no decoder, metric, sampling, or storage behavior changes.

## Current architecture

- `simulation/config.py` owns a frozen, fixed one-round bit-flip grid, immutable `BatchTask`, deterministic point IDs and `SeedSequence` batch seeds. `circuit_level/experiment.py` has a separate frozen d-round uniform-noise config and worker, but reuses `BatchTask` and seeding.
- `simulation/sampling.py` samples each physical batch once, decodes ordinary SWIM and paired comparative gap, and checks the ordinary hard result on a prefix. The circuit worker uses `CircuitLevelDecoder`, checks its hard output, and keeps its own scientific scope gate. Other path-gap and monotone-Y workers use feature-specific adapters and signed scores.
- `simulation/parallel_runner.py` bounds outstanding `spawn` futures to twice the worker count; the parent receives whole batch DataFrames. `simulation/storage.py` validates a wide shot schema and atomically writes one Parquet *shard per batch*. `simulation/provenance.py` records source/environment identities and writes manifests. `experiments/phase_2a_test.py` and `experiments/circuit_level_memory_test.py` each orchestrate their own run, summary, logging, and audit. The former prints an ETA without saying it is an estimate; the latter prints elapsed time only.
- Existing run layouts contain `shots/*.parquet`, `metadata.json`, `resolved_config.json`, logs, source snapshot, and analysis files. Existing analysis loaders and replay audits depend on that layout. They must continue to read legacy data unchanged.
- The circuit-memory end-to-end test initially failed before sampling because its source snapshot expected `prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md`. The prompt was restored locally. Since `prompts/` is Git-ignored, the snapshot now includes this historical prompt when present and remains runnable without it in a fresh checkout.

## Verified local decoder API and scientific contract

Local `external_libs/color-code-stim` is `phase2a/swim-distance` at `57a6155`. `ColorCode(d=..., rounds=..., circuit_type="tri", cnot_schedule="tri_optimal", noise_model=..., comparative_decoding=..., enable_colorcorrelated_decoding=...)` constructs a code; `sample(shots, seed=...)` returns detector and observable arrays; `decode(detectors, full_output=True, compute_swim_distance=...)` returns predictions and named extras. The `NoiseModel` constructors were checked in `color_code_so`:

| YAML name | Exact constructor | Meaning in local API |
| --- | --- | --- |
| `bitflip` | `NoiseModel(bitflip=p)` | Data bit flips at the start of each round. |
| `depol` | `NoiseModel(depol=p)` | Data depolarization at the start of each round; **not** idle-only noise. |
| `uniform` | `NoiseModel.uniform_circuit_noise(p)` | Uniform reset, measurement, CNOT, and idle rates, with resolved granular rates; data-start `depol` remains zero. |

With `enable_colorcorrelated_decoding=True`, `ConcatMatchingDecoder` forms three baseline plus nine guide-reweighted candidates **per logical class**. Guides are baseline corrections mapped to original DEM columns; two-guide combinations use OR. The nine extra candidates rerun both matching stages with temporary priors. All 12 candidates are rescored using their target color's **original stage-2** log-likelihood weights before selection; temporary-prior generation weights are separately exposed. Comparative `logical_gaps` use these common-prior candidate weights. This matches the prompt's expected semantics. Preserve candidate order, ordinary `best_colors`/`weights` meanings, and the distinction between candidate weights and generation weights.

The current decoder explicitly rejects combining color-correlated decoding with matching-growth `compute_swim_distance`, as well as correlated BP/custom DEM. Existing SWIM is validated only for single-round triangular data-only X noise; the separate circuit-level adapter supports its documented closed-memory uniform-noise setting. A requested metric/decoder/noise combination must pass an explicit capability check before any output directory or shot is created. No automatic fallback or scientific reinterpretation is justified.

## Proposed modules and ownership

| Module | Action and responsibility |
| --- | --- |
| `config.py` | Retain legacy config and seed helpers; add frozen resolved YAML configuration with strict names/types, validated sweep axes, explicit metric requests, `shots`, `workers`, `master_seed`, `output_root`, `buffer_shots`, `verbose`, and canonical serialization. |
| `planner.py` | Add deterministic full-point expansion, duplicate/collision checks, point identities, immutable work records, and directory naming. |
| `noise.py` | Add only the three exact constructor mappings above and capability validation; do not change decoder mathematics. |
| `task.py` | Add typed immutable point/chunk records. Reuse `BatchTask` or adapt it at the boundary; preserve the old seed recipe for legacy wrappers. |
| `worker.py` | Move common physical sampling and named-output assembly behind metric adapters; reuse existing `sample_batch`/`sample_memory_batch` logic and gates. Worker returns bounded data to parent and writes no final files. |
| `scheduler.py` | Evolve `parallel_runner.py`: `spawn`, bounded in-flight work and byte/shot budget, first small chunk per point, measured throughput, adaptive chunk size capped by `buffer_shots` and a duration limit, exact remaining-shot accounting, failure propagation. Keep scheduling independent of scoring. |
| `storage.py` | Retain legacy shard writer/validators. Add a parent-only streaming writer with temporary bounded buffers and one final Parquet per requested metric per point; validate schema, shot IDs, counts and non-overwrite before atomic publication. Never concatenate all shots in RAM. |
| `runner.py` | Add canonical orchestration, one JSON run log with resolved configuration, provenance, progress, failure state and artifact inventory. Adapt `experiments/*` entry points as thin compatibility wrappers, not second engines. |
| `cli.py` | Add YAML path CLI for shell scripts, strict error exit codes and optional verbose progress with **estimated remaining wall time**. Reuse `provenance.py` and `pairing.py`. |

The desired run root is `YY_MM_DD_HH_MM_SS_{hash8}`. Each fully expanded point directory is `decoder_type={decoder_type},circuit_type={circuit_type},d={distance},r={rounds},p={physical_error_rate},noisemodel={noise_model},cnot_schedule={cnot_schedule}`. Canonicalize `p` once from the resolved numeric value; check for duplicate names before creating files. `circuit_type` is mandatory. Create a fresh run root exclusively; retain partial temporary data and mark failure in the JSON log without publishing incomplete final Parquet files. Decide the exact per-metric filenames/schema in the storage stage, with metric-specific failure labels and shared shot identity retained.

## Order and acceptance gates for later tasks

1. **Config and planning:** YAML parsing, validation, capability matrix, deterministic sweep expansion, unique paths, immutable work IDs, and the three noise mappings. No sampling yet.
2. **Worker adapters:** preserve single physical sampling and existing decode calls, selected ordinary color, hard decisions, signed metric values where applicable, and paired comparative inputs. Verify output equivalence against current workers on fixed small seeds.
3. **Scheduler:** small first chunks followed by bounded adaptive chunks; exact shot counts with out-of-order completion, deterministic chunk seeds, `spawn`, worker failure cleanup, and honest ETA. Adaptive chunk boundaries change Stim's seeded sample stream versus the old fixed-batch workflow; preserve *legacy* batch boundaries in compatibility mode and record new boundaries/seeds for replay.
4. **Storage:** parent-only bounded stream, one Parquet per requested metric and point, no silent overwrite, safe atomic finalize, schema/provenance linkage, and failed-run recovery policy. Stream or externally merge ordered records rather than retaining completed chunks in memory.
5. **Runner and CLI:** single canonical orchestration, shell-script example, JSON log, verbose estimated remaining time, and thin legacy wrappers. Migrate readers by schema/layout version while preserving old shard loaders and historical data.

## Tests that protect scientific logic

- Main tests: `tests/phase2b/test_configuration_sampling.py` (seed schedule, selected-color rather than minimum score, one physical sample, comparative alias, serial/parallel equality, schema/replay); `tests/circuit_level/test_experiment.py` and `test_decoder.py` (d-round pairing, hard invariance, topology/method gates); path-gap and monotone-Y experiment tests (metric version, signed scores, independent feature imports, replay and failure labels).
- Decoder tests: `external_libs/color-code-stim/tests/test_swim_decoder.py`, `test_soft_output_reference.py`, `test_soft_output_topology.py`, and `test_color_correlated_decoding.py` (12 candidates, original-prior rescoring, comparative gap, unsupported combinations). Keep small fixed-shot parity tests across old and new entry points; add streaming count, no-overwrite and bounded-memory tests only when those stages are implemented.

## Sinter design reference

Sinter's [v1.13 API](https://github.com/quantumlib/Stim/wiki/Sinter-v1.13-Python-API-Reference) exposes a first fact-finding batch, shot and time batch caps, and progress iteration. Its current [CollectionManager](https://github.com/quantumlib/Stim/blob/main/glue/sample/src/sinter/_collection/_collection_manager.py) separates task accounting from workers and uses `spawn`; the current [ramp-throttled sampler](https://raw.githubusercontent.com/quantumlib/Stim/main/glue/sample/src/sinter/_collection/_sampler_ramp_throttled.py) adjusts batch size from observed duration. Adopt those principles only. Our scheduler must additionally bound returned per-shot data and meet the metric-file contract; Sinter's statistical CSV workflow is not the target output format.
