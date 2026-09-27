# Codex Task 06 — Regression Tests, Documentation, Cleanup, and Final Audit

# Shared Project Contract

Repository:
- `https://github.com/AKTKN/color_code_softoutput`
- external decoder package: `https://github.com/AKTKN/color-code-stim`
- inspect the local checkout before editing; local `AGENTS.md` and current working tree take precedence over assumptions from GitHub.

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
- Use conda environment of `color_code_so`
## Prerequisite

Assume Tasks 01–05 implemented the new canonical YAML workflow.

## Scope

Do not add new scientific functionality.

This task is for regression protection, documentation, and removal of accidental duplication introduced during refactoring.

## 1. Regression test suite

Run and fix relevant tests without weakening scientific assertions.

At minimum include:

- new configuration/planner tests;
- new worker/metric tests;
- new scheduler/ETA tests;
- new storage tests;
- new runner smoke tests;
- existing soft-output tests;
- existing circuit-level tests affected by imports;
- current `color-code-stim` color-correlated decoder tests;
- existing simulation/analysis tests whose imports changed.

If some historical test intentionally targets the old workflow, keep it clearly separated rather than silently rewriting its scientific expectation.

## 2. README documentation

Update README documentation with a concise canonical-workflow section.

Include:

### Minimal YAML

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

### Run command

```bash
./scripts/run_experiment.sh configs/example.yaml
```

### Noise semantics

Document exactly:

```text
bitflip -> NoiseModel(bitflip=p)
depol   -> NoiseModel(depol=p)
uniform -> NoiseModel.uniform_circuit_noise(p)
```

### Run root

```text
YY_MM_DD_HH_MM_SS_{hash8}
```

### Point directory

```text
decoder_type={decoder_type},circuit_type={circuit_type},d={distance},r={rounds},p={physical_error_rate},noisemodel={noise_model},cnot_schedule={cnot_schedule}
```

### Final Parquet files

Document the exact two-column schemas.

### Adaptive scheduling

Explain:

- initial calibration;
- per-point seconds/shot;
- target chunk duration;
- min/max chunk sizes;
- dynamic refill;
- EWMA update.

### Verbose/ETA

Explain:

- `simulation.verbose`;
- progress fields;
- ETA is estimated from measured runtime;
- `ETA: estimating...` before sufficient timing information;
- ETA is not a guaranteed completion time.

### Reproducibility

State the actual chunk-seeding contract and the limitation that adaptive runtime-dependent chunk boundaries can change the exact random stream across machines/worker counts unless a finer shot-level seed scheme was implemented.

### Soft-output preservation

State that the scientific soft-output implementations remain available; the new minimal canonical storage currently writes only the required experiment metrics.

## 3. Cleanup audit

Check for:

- two independent YAML parsers;
- duplicate path-format logic;
- duplicate seed logic;
- duplicate scheduler logic;
- obsolete canonical references to fixed Phase-2A grids;
- accidental production use of old batch-shard storage;
- new persistent metadata files besides `run_log.json`.

Do not delete historical research artifacts solely because they are not part of the new canonical workflow.

## 4. Acceptance audit

Verify all final requirements:

1. YAML specifies simulation.
2. Shell script launches it.
3. distance/p sweeps work.
4. `bitflip`, `depol`, `uniform` semantics are correct.
5. multiple named decoder configs work.
6. run root uses timestamp + hash8.
7. point path includes `decoder_type`, `circuit_type`, `d`, `r`, `p`, `noisemodel`, `cnot_schedule`.
8. ordinary point produces only required logical-error final file.
9. correlated point produces four required files.
10. final outputs are not per chunk.
11. shot indices are contiguous and aligned.
12. memory is bounded with temporary parts.
13. `.buffer/` is removed after success.
14. new workflow creates one JSON log.
15. adaptive calibration/chunk sizing works.
16. worker slots are dynamically refilled.
17. verbose progress can be disabled.
18. verbose progress displays expected remaining time after calibration.
19. existing soft-output science tests pass.
20. only smoke-scale runs were executed.

## 5. Final implementation report

Return:

- files changed;
- final module architecture;
- YAML schema;
- noise mapping;
- exact directory formats;
- Parquet schemas;
- chunk-size formula;
- ETA formula;
- seeding/reproducibility guarantee;
- compatibility wrappers;
- test commands/results;
- smoke commands/output paths;
- unresolved issues.

Do not commit/push unless separately requested.
