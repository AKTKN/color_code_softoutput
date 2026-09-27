# Codex Task 01 — YAML Configuration, Noise Adapter, Sweep Planner, and Path Naming

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


- Use conda environment of `color_code_so`
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

## Scope

Implement only the configuration/planning layer for the new canonical simulation workflow.

Do not implement multiprocessing, worker decoding, Parquet buffering, or the top-level runner in this task.

Suggested modules:

```text
src/color_code_softoutput/simulation/config.py
src/color_code_softoutput/simulation/noise.py
src/color_code_softoutput/simulation/planner.py
src/color_code_softoutput/simulation/task.py
```

Reuse existing files when practical instead of duplicating functionality.

## 1. YAML schema

Support a configuration close to:

```yaml
simulation:
  output_root: results
  shots: 100000
  workers: 16
  master_seed: 20260927
  buffer_shots: 50000
  verbose: true

chunking:
  calibration_shots: 8
  target_chunk_seconds: 1.0
  min_chunk_shots: 1
  max_chunk_shots: 4096
  throughput_ema_alpha: 0.25

sweep:
  distance: [3, 5, 7]
  physical_error_rate: [0.001, 0.002]
  noise_model: [uniform]
  rounds: distance
  circuit_type: [tri]
  cnot_schedule: [tri_optimal]

color_code_options:
  temp_bdry_type: Z
  superdense_circuit: false
  perfect_logical_initialization: false
  perfect_logical_measurement: false
  perfect_first_syndrome_extraction: false
  perfect_init_final: false
  remove_non_edge_like_errors: true

decoders:
  - type: concat_mwpm
    options:
      comparative_decoding: false
      enable_colorcorrelated_decoding: false
    decode_options:
      colors: all

  - type: color_correlated
    options:
      comparative_decoding: false
      enable_colorcorrelated_decoding: true
    decode_options:
      colors: all
```

Add `PyYAML` as a dependency if needed.

Normalize useful scalar forms to one-element tuples/lists. `rounds` may be:

- integer;
- list of integers;
- special string `distance`.

`simulation.shots` means shots **per fully expanded simulation point**.

`simulation.verbose` must be a validated boolean and is part of the resolved run configuration.

## 2. Decoder labels and options

`decoders[].type` is a user-defined stable label and becomes `decoder_type`.

Do not infer behavior from the string. Behavior comes from `options` and `decode_options`.

Reject filesystem-unsafe labels containing at least:

```text
/  \  ,  =
```

Keep constructor and decode options separate.

Define deterministic precedence and reject ambiguous conflicts. Values resolved from sweep dimensions (`d`, `rounds`, `circuit_type`, `cnot_schedule`, `noise_model`) must not be silently contradicted by `color_code_options` or decoder `options`.

## 3. Noise mapping

Implement exactly:

```python
bitflip -> NoiseModel(bitflip=p)
depol   -> NoiseModel(depol=p)
uniform -> NoiseModel.uniform_circuit_noise(p)
```

Reject unknown names.

Unit-test the resolved native `NoiseModel` parameters, not just class type.

## 4. Sweep expansion

Expand the Cartesian product of at least:

- distance;
- physical error rate;
- noise model;
- rounds;
- circuit type;
- CNOT schedule;
- decoder configuration.

For `rounds: distance`, resolve the round count independently for each distance.

Create an immutable resolved point record containing all parameters needed later by a worker.

Assign each point a deterministic internal `point_id` derived from canonical semantic content.

## 5. Run hash

The run-directory name later uses:

```text
YY_MM_DD_HH_MM_SS_{hash8}
```

Implement deterministic `hash8` as the first eight lowercase hex characters of SHA-256 over the canonicalized **validated semantic config**.

Requirements:

- YAML key order does not matter;
- YAML comments do not matter;
- hash parsed/resolved values, not raw YAML bytes;
- use deterministic JSON serialization, e.g. `sort_keys=True` and compact separators;
- document whether relative `output_root` participates in the hash and why;
- machine-specific resolved absolute paths should not accidentally make equivalent scientific configs hash differently.

## 6. Per-point directory name

Implement exactly:

```text
decoder_type={decoder_type},circuit_type={circuit_type},d={distance},r={rounds},p={physical_error_rate},noisemodel={noise_model},cnot_schedule={cnot_schedule}
```

Use deterministic physical-error formatting such as:

```python
format(p, ".12g")
```

No locale-dependent formatting.

Preflight all expanded point paths and reject collisions before any simulation is allowed to start.

## 7. Tests

Add focused tests for:

- YAML scalar/list normalization;
- missing required fields;
- invalid probability;
- invalid distance/round count;
- unknown noise model;
- unsafe decoder type;
- `rounds: distance`;
- Cartesian product;
- deterministic `point_id`;
- deterministic hash;
- YAML comments/key order preserving hash;
- semantic change modifying hash;
- exact directory-string formatting including `circuit_type`;
- path-collision preflight;
- exact `depol -> NoiseModel(depol=p)` mapping;
- `simulation.verbose` validation.

Do not change soft-output mathematical tests.

## Deliverable

Implement and test only this configuration/planning layer. Provide a short report listing new public types/functions and test results. Stop before worker/scheduler/storage implementation.
