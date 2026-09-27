# Codex Task 04 — Bounded-Memory Buffering and Final Parquet Storage

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

Assume Tasks 01–03 provide:

- resolved simulation points;
- worker chunk results;
- out-of-order adaptive completion.

## Scope

Implement storage only.

Suggested module:

```text
src/color_code_softoutput/simulation/storage.py
```

Do not implement the full top-level runner in this task.

## 1. Final storage contract

Every final Parquet file must contain an explicit `shot_index: int64` column.

For every point:

### Always

`logical_error.parquet`

Schema:

```text
shot_index: int64
logical_error: bool
```

### Only when `enable_colorcorrelated_decoding=True`

`default_logical_error.parquet`

```text
shot_index: int64
default_logical_error: bool
```

`better_weight_by_color_correlated_decoding.parquet`

```text
shot_index: int64
better_weight_by_color_correlated_decoding: uint8
```

`effect_by_color_correlated_decoding.parquet`

```text
shot_index: int64
effect_by_color_correlated_decoding: uint8
```

No implicit pandas index.

No final per-worker or per-chunk files.

## 2. Point directory

Storage receives the already-validated point directory name from Task 01:

```text
decoder_type={decoder_type},circuit_type={circuit_type},d={distance},r={rounds},p={physical_error_rate},noisemodel={noise_model},cnot_schedule={cnot_schedule}
```

No overwrite.

## 3. Temporary buffer

Inside each point directory:

```text
.buffer/
```

Temporary part files:

```text
.buffer/part_000000.parquet
.buffer/part_000001.parquet
...
```

Use one internal temporary table containing all metrics required for that point.

Workers do not write these files. Main process only.

## 4. Out-of-order chunks

Adaptive workers finish out of order.

Maintain per point:

```text
next_contiguous_shot
waiting completed chunks keyed by shot_start
contiguous in-memory buffer
written interval / part metadata
```

When a chunk arrives:

1. validate point ID and interval;
2. reject overlap/duplicate;
3. hold out-of-order result;
4. when `shot_start == next_contiguous_shot`, append it;
5. advance `next_contiguous_shot`;
6. repeatedly consume waiting chunks that are now contiguous.

Do not sort an entire run in memory at the end.

## 5. Buffer bound

`simulation.buffer_shots` controls approximate maximum contiguous rows retained before disk flush.

When threshold is reached, flush a temporary part atomically.

If a single worker result exceeds `buffer_shots`, handle it safely without multiplying memory unnecessarily.

Temporary writes should preserve exact dtypes.

## 6. Finalization

After all chunks for a point are complete:

1. ensure no interval gap;
2. ensure no unresolved waiting chunk;
3. flush final partial buffer;
4. read temporary parts in numeric order;
5. use `pyarrow.parquet.ParquetWriter` or equivalent streaming output;
6. generate one final file per metric;
7. do not concatenate every part into one DataFrame;
8. write to temporary final paths first;
9. validate;
10. atomically rename final files;
11. only then delete `.buffer/`.

## 7. Validation

For each final file verify:

- exactly configured shot count;
- exactly two columns;
- correct metric column name;
- exact Arrow dtype;
- no nulls;
- `shot_index` exactly `0,1,...,shots-1`.

For correlated points additionally verify all four files have identical shot-index sequences.

Where practical, verify:

```python
effect == default_logical_error & ~logical_error
```

during temporary-part validation or final cross-file validation.

## 8. Failure behavior

On storage/finalization failure:

- preserve `.buffer/`;
- do not leave a misleading successfully named final file;
- propagate the exception.

No resume system is required in this task.

## 9. Tests

Use synthetic chunks, including scrambled completion order.

Test:

- ordered chunks;
- reverse-ordered chunks;
- arbitrary shuffled chunks;
- overlap rejection;
- duplicate rejection;
- gap detection;
- multiple temporary parts;
- exact final row count;
- exact shot index;
- exact dtypes;
- ordinary point creates one final file;
- correlated point creates four;
- finalization removes `.buffer/`;
- injected failure preserves `.buffer/`;
- finalization streams parts instead of collecting the full run into one in-memory object.

## Deliverable

Implement storage and tests only. Report the temporary and final schemas. Stop before top-level runner/CLI integration.
