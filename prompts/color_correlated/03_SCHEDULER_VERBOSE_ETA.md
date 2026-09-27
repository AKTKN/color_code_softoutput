# Codex Task 03 — Adaptive Sinter-Like Scheduler, Verbose Progress, and ETA

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

Assume:

- Task 01 provides validated expanded simulation points.
- Task 02 provides a picklable worker function and typed chunk/result records.

## Scope

Implement only the main-process adaptive scheduler and progress reporting.

Suggested module:

```text
src/color_code_softoutput/simulation/scheduler.py
```

Do not implement final Parquet storage or the complete CLI runner yet. Make the scheduler storage-agnostic via callbacks/iterators where practical.

## 1. Scheduling model

Use Sinter as a design reference:

- small initial fact-finding work;
- previous timing to estimate shots per target wall time;
- dynamic assignment when CPUs become free.

Do not depend on Sinter private internals.

Use multiprocessing with `spawn`.

Keep at most `simulation.workers` worker jobs actively executing.

Do not use synchronized “waves” where all workers must finish before new work is dispatched.

Whenever one future completes, process it and immediately fill the free slot.

## 2. Per-point scheduling state

Track at least:

```text
next_shot_to_schedule
completed_shots
remaining_shots
next_chunk_id
seconds_per_shot estimate
calibration status
```

Shot ranges must be disjoint and exhaustive.

`shot_index` assignment must depend on the planned interval, never on completion order.

## 3. Calibration

For each simulation point, the first chunk must use:

```text
chunking.calibration_shots
```

clamped to the total remaining shots.

Do not normally dispatch additional chunks for a point until one timing observation exists for that point.

Different points may calibrate concurrently.

If there are fewer points than workers, once a point has calibrated it may have multiple disjoint chunks in flight so CPUs are not left idle.

## 4. Adaptive chunk size

Maintain `seconds_per_shot`.

For a completed chunk:

```python
observed_sps = elapsed_seconds / shot_count
```

If no prior estimate exists:

```python
sps = observed_sps
```

Otherwise use the configured EWMA:

```python
sps = alpha * observed_sps + (1 - alpha) * previous_sps
```

where:

```text
alpha = chunking.throughput_ema_alpha
```

Then choose approximately:

```python
raw = round(target_chunk_seconds / sps)
chunk_shots = clamp(raw, min_chunk_shots, max_chunk_shots)
chunk_shots = min(chunk_shots, remaining_unscheduled_shots)
```

Handle zero, sub-resolution, NaN, or invalid elapsed times defensively.

Keep this logic in a pure independently testable helper.

## 5. Fairness

Use a clear fair policy across ready points, for example:

- round robin;
- or least-progress-first.

Document it.

The scheduler must not starve a slow point indefinitely.

## 6. Deterministic seeds

Each chunk seed must be a deterministic function of:

```text
master_seed
point_id
chunk_id
```

Use a stable cryptographic hash plus `numpy.random.SeedSequence` or an equivalently explicit recipe.

Document the actual reproducibility guarantee:

- shot ranges are deterministic from scheduler decisions;
- chunk seeds are deterministic once chunk IDs are assigned;
- because adaptive chunk boundaries depend on measured runtime, changing machine load / worker count / timing can change chunk partitioning and therefore the exact random sample stream;
- do not claim bitwise schedule-independent reproducibility unless a finer scheme is implemented.

## 7. Verbose option

`simulation.verbose` was added in Task 01.

When false:

- scheduler should avoid routine progress output.

When true:

print concise progress information during the simulation.

At minimum display:

```text
completed shots / total shots
percentage complete
active workers / configured workers
completed points / total points
elapsed wall time
estimated remaining time (ETA)
```

You may additionally display current adaptive chunk sizes or per-point progress if concise.

Do not print one line per shot.

Use one logical progress reporter that can later be called by the runner.

## 8. ETA / expected time

The user explicitly requires expected time.

Call it an estimate, e.g.:

```text
ETA ~ 00:18:42
```

Do not present it as a deadline guarantee.

Preferred estimate after calibration:

1. Each calibrated point has `seconds_per_shot_i`.
2. Estimate remaining worker-seconds:

```python
remaining_cpu_seconds = sum(
    remaining_shots_i * seconds_per_shot_i
)
```

3. Approximate remaining wall time as:

```python
eta_seconds = remaining_cpu_seconds / effective_parallelism
```

where a reasonable first approximation is:

```python
effective_parallelism = min(workers, number_of_points_or_chunks_with_remaining_work)
```

Alternatively, use a scheduler-aware estimate based on active + pending chunks if you can keep it simple and testable.

Before enough points are calibrated, print:

```text
ETA: estimating...
```

rather than fabricating an exact value.

Optionally combine this with global observed throughput after enough work is complete, but keep the formula documented.

Provide a pure ETA helper and unit tests.

## 9. Tests

Use fake workers / synthetic durations; avoid real `sleep`-based tests.

Test:

- calibration is first;
- no premature normal chunk for an uncalibrated point;
- fast point grows chunk size;
- slow point shrinks chunk size;
- min/max clamps;
- EWMA formula;
- max in-flight jobs never exceeds `workers`;
- free worker gets refilled without waiting for other workers;
- all requested shot ranges are scheduled once;
- no overlap;
- no gap in scheduled intervals;
- fairness;
- deterministic seed helper;
- `verbose=False` suppresses progress;
- `verbose=True` emits progress;
- ETA says “estimating” before calibration;
- ETA becomes finite and decreases in a controlled synthetic scenario.

## Deliverable

Implement scheduler + progress/ETA tests. Do not wire final storage or CLI in this task. Report the chunk-sizing and ETA formulas used.
