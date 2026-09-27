# Codex Task 00 — Architecture Audit and Refactor Plan

# Shared Project Contract

Repository:
- `https://github.com/AKTKN/color_code_softoutput`
- external decoder package: `https://github.com/AKTKN/color-code-stim`
- inspect the local checkout before editing; local `AGENTS.md` and current working tree take precedence over assumptions from GitHub.
- Use conda environment of `color_code_so`

Before editing, read:
- `AGENTS.md`
- `STATUS.md`
- `README.md`
- `src/color_code_softoutput/README.md`

Scientific constraint:
- Preserve the existing soft-output calculation logic and scientific definitions.
- Do not redesign SWIM / cluster-gap / path-gap mathematics in this refactor.
- Do not reinterpret existing soft-output values as exact logical gaps or posterior probabilities.
- Do not run a large numerical campaign.
- Do not commit, push, merge, or open a PR unless separately requested.

Implementation discipline:
- Python 3.12 compatibility.
- Prefer typed immutable dataclasses for resolved configurations and work records.
- No silent overwrite.
- No unbounded shot-level accumulation in RAM.
- Worker processes must not write final result files.
- Use multiprocessing `spawn`.
- Keep legacy research data untouched.
- Do not maintain two independent simulation engines if a compatibility wrapper can delegate to the new canonical implementation.

## Purpose

This task is intentionally read-mostly. Do **not** perform the complete workflow refactor yet.

The eventual target is a YAML-driven simulation workflow with:

1. configuration/sweep expansion;
2. `color-code-stim` construction and per-shot metric generation;
3. Sinter-like adaptive chunk scheduling;
4. bounded-memory temporary buffering;
5. one final Parquet file per requested metric;
6. a single JSON run log;
7. shell-script execution;
8. optional verbose progress with an estimated remaining time.

The implementation will be split across later Codex tasks. This task exists to prevent a large one-shot rewrite.

## Required inspection

Inspect at minimum:

- `src/color_code_softoutput/simulation/config.py`
- `src/color_code_softoutput/simulation/parallel_runner.py`
- `src/color_code_softoutput/simulation/sampling.py`
- `src/color_code_softoutput/simulation/storage.py`
- `src/color_code_softoutput/simulation/provenance.py`
- `src/color_code_softoutput/circuit_level/experiment.py`
- `src/color_code_softoutput/experiments/circuit_level_memory_test.py`
- current simulation-related tests
- current soft-output tests

Inspect the local `color-code-stim` API, especially:

- `ColorCode`
- `NoiseModel`
- `ConcatMatchingDecoder`
- color-correlated decoding
- `ColorCode.decode`
- relevant tests

Also inspect Sinter as a design reference:

- https://github.com/quantumlib/Stim/wiki/Sinter-v1.13-Python-API-Reference
- current `CollectionManager`
- current ramp-throttled sampler

Do not copy Sinter internals. Extract only the design principles needed here.

## Scientific/API facts to verify explicitly

Verify locally that the current API supports:

```python
NoiseModel(bitflip=p)
NoiseModel(depol=p)
NoiseModel.uniform_circuit_noise(p)
```

For this project, the configuration-level noise names have exactly these meanings:

```text
bitflip -> NoiseModel(bitflip=p)
depol   -> NoiseModel(depol=p)
uniform -> NoiseModel.uniform_circuit_noise(p)
```

This is a correction to an earlier draft. Do **not** map `depol` to idle-only noise.

Verify the color-correlated decoder's candidate-weight semantics. The expected current behavior is that correlated candidates can be generated under temporary reweighted priors but are selected/comparable using the original/common stage-2 prior. If the local implementation differs, document the discrepancy.

## Target module structure

Recommend a concrete decomposition close to:

```text
src/color_code_softoutput/simulation/
    config.py
    planner.py
    noise.py
    task.py
    worker.py
    scheduler.py
    storage.py
    runner.py
    cli.py
```

The exact filenames may differ if existing modules should be reused.

## Output-directory target

Run root:

```text
YY_MM_DD_HH_MM_SS_{hash8}
```

Per fully expanded simulation point:

```text
decoder_type={decoder_type},circuit_type={circuit_type},d={distance},r={rounds},p={physical_error_rate},noisemodel={noise_model},cnot_schedule={cnot_schedule}
```

`circuit_type` is required in the directory name.

## Verbose / ETA target

The YAML simulation options will include at least:

```yaml
simulation:
  shots: 100000
  workers: 16
  master_seed: 20260927
  output_root: results
  buffer_shots: 50000
  verbose: true
```

When `verbose: true`, the eventual runner must display progress and an **estimated** remaining wall time. It must be labeled as an estimate, not as a guaranteed completion time.

## Deliverable

Create or update a concise implementation-plan Markdown file in the repository that states:

1. current architecture;
2. modules to retain;
3. modules to replace/refactor;
4. compatibility risks;
5. dependency/order between later implementation stages;
6. exact local `color-code-stim` API assumptions;
7. tests that protect existing scientific logic.

Do not yet implement the full scheduler, storage layer, or runner.

Stop after the architecture plan and report any conflict that would materially change the later tasks.
