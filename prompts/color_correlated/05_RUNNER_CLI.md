# Codex Task 05 — Top-Level Runner, Single JSON Log, CLI, and Shell Script

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
## Prerequisites

Assume Tasks 01–04 are complete:

- config/planner;
- worker;
- adaptive scheduler with verbose ETA;
- buffered storage.

## Scope

Integrate these components into the canonical experiment workflow.

Suggested modules/files:

```text
src/color_code_softoutput/simulation/runner.py
src/color_code_softoutput/simulation/cli.py
scripts/run_experiment.sh
configs/example.yaml
```

## 1. Canonical command

The primary command must be:

```bash
./scripts/run_experiment.sh configs/example.yaml
```

The shell script must be thin:

```bash
#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:?usage: $0 CONFIG.yaml}"
shift

python -m color_code_softoutput.simulation.cli --config "$CONFIG" "$@"
```

Make it executable.

Equivalent direct Python invocation should work.

## 2. Run root

At invocation time create exactly one run root:

```text
{output_root}/YY_MM_DD_HH_MM_SS_{hash8}/
```

Use local timezone-aware wall time.

Use `exist_ok=False`.

`hash8` comes from the validated semantic configuration created in Task 01.

## 3. Preflight before sampling

Before launching workers:

1. parse and validate YAML;
2. expand all points;
3. validate point directory names;
4. detect collisions;
5. ensure all point configs can be represented;
6. create run root;
7. create point directories/storage state;
8. write initial `run_log.json`.

Do not begin a partial sweep if preflight already knows configuration is invalid.

## 4. One JSON log only

The new canonical workflow must create one persistent JSON log:

```text
run_log.json
```

Semantic structure:

```json
{
  "config": {},
  "simulation_start_time": "2026-09-27T11:45:03+09:00",
  "simulation_end_time": null
}
```

At start:

- `config` is the fully resolved validated config;
- use timezone-aware ISO 8601 start time;
- `simulation_end_time = null`.

In a `finally` path, on both success and caught failure:

- set timezone-aware `simulation_end_time`;
- atomically rewrite the same JSON.

Do not create new persistent:

- text log file;
- second JSON metadata file;
- source ZIP;
- model dump;
- provenance archive.

Old provenance modules may remain for historical workflows, but this runner must not invoke them.

## 5. Scheduler + storage integration

The runner must:

- instantiate adaptive scheduler state for every expanded point;
- pass completed worker results immediately into the point storage buffer;
- update progress/ETA;
- finalize a point as soon as all its shots are complete and contiguous;
- continue running other points.

Do not wait for every point before finalizing the first completed point.

## 6. Verbose progress

Use:

```yaml
simulation:
  verbose: true
```

When true, display concise progress including:

```text
run directory
number of points
total requested shots
configured workers
completed shots / total
percentage
completed points / total
elapsed
ETA / estimated remaining time
```

Before sufficient calibration:

```text
ETA: estimating...
```

After calibration, show a formatted estimate such as:

```text
ETA ~ 00:12:34
```

This is an estimate derived from measured worker throughput. Do not call it guaranteed completion time.

A reasonable console update cadence is on chunk completion, optionally rate-limited to avoid excessive output. Do not create a persistent text log.

When `verbose: false`, routine progress must be silent except final success path or fatal errors as appropriate.

## 7. Final directory tree

Example:

```text
results/
└── 26_09_27_11_45_03_a1b2c3d4/
    ├── run_log.json
    ├── decoder_type=concat_mwpm,circuit_type=tri,d=3,r=3,p=0.001,noisemodel=uniform,cnot_schedule=tri_optimal/
    │   └── logical_error.parquet
    └── decoder_type=color_correlated,circuit_type=tri,d=3,r=3,p=0.001,noisemodel=uniform,cnot_schedule=tri_optimal/
        ├── logical_error.parquet
        ├── default_logical_error.parquet
        ├── better_weight_by_color_correlated_decoding.parquet
        └── effect_by_color_correlated_decoding.parquet
```

No `.buffer/` should remain after successful point finalization.

## 8. Legacy compatibility

The YAML runner is canonical.

If old experiment entry points are still used by notebooks/tests, either:

- keep them unchanged if they are clearly historical;
- or make them thin wrappers over new reusable components where safe.

Do not preserve two diverging production simulation engines.

Do not rewrite historical result directories.

## 9. Tests / smoke

Run very small end-to-end tests covering:

- one worker;
- multiple workers;
- ordinary decoder;
- color-correlated decoder;
- `bitflip`;
- `depol`;
- `uniform`;
- `verbose=false`;
- `verbose=true` with ETA transition from estimating to finite;
- exact directory naming with `circuit_type`;
- one `run_log.json`;
- final file counts/schemas;
- no `.buffer/` after success.

No large campaign.

## Deliverable

Integrate the complete runnable workflow, provide smoke commands/output directories, and report any legacy wrappers retained.
