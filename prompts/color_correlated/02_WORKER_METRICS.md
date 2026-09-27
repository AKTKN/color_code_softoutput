# Codex Task 02 — Worker-Side Sampling, Decoder Construction, and Required Metrics

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
- Use conda environment of `color_code_so`

Implementation discipline:
- Python 3.12 compatibility.
- Prefer typed immutable dataclasses for resolved configurations and work records.
- No silent overwrite.
- No unbounded shot-level accumulation in RAM.
- Worker processes must not write final result files.
- Use multiprocessing `spawn`.
- Keep legacy research data untouched.
- Do not maintain two independent simulation engines if a compatibility wrapper can delegate to the new canonical implementation.

## Prerequisite

Assume Task 01 has established validated resolved simulation-point records.

## Scope

Implement the worker-side computation layer only.

Suggested module:

```text
src/color_code_softoutput/simulation/worker.py
```

Do not implement adaptive scheduling or final Parquet merging yet.

## 1. Worker input/output

Define immutable input records containing at least:

```text
point_id
chunk_id
shot_start
shot_count
seed
resolved simulation point
```

Worker result must contain at least:

```text
point_id
chunk_id
shot_start
shot_count
elapsed_seconds
metric arrays
```

Metric arrays must correspond exactly to the shot interval:

```text
[shot_start, shot_start + shot_count)
```

Workers return data to the main process. Workers must not write final result files.

Measure worker elapsed time around the complete expensive operation relevant to scheduling, including sampling and decoding for that chunk.

## 2. Worker-side object cache

Constructing circuits/decoders can be expensive.

Use a bounded per-process LRU cache keyed by the immutable resolved point's circuit/decoder semantics.

Do not share mutable decoder instances across processes.

Cache design must not grow without bound across a large sweep.

## 3. Sampling

Sample the physical circuit exactly once per chunk.

Keep detector outcomes and actual logical observable values paired.

For multiple observables, define shot-level logical failure as:

```python
np.any(prediction != actual_observable, axis=-1)
```

For one observable:

```python
prediction != actual_observable
```

Return a 1D boolean array with one logical-error value per shot.

## 4. Required final metrics

The storage layer will later save these metrics.

### Always compute

```text
logical_error: bool
```

This refers to the final output of the configured decoder.

### Only when `enable_colorcorrelated_decoding=True`

Also compute:

```text
default_logical_error: bool
better_weight_by_color_correlated_decoding: uint8
effect_by_color_correlated_decoding: uint8
```

Do not use `decoder_type` to decide this. Use the actual resolved decoder option.

## 5. Same-shot ordinary baseline for color-correlated decoding

For a correlated point, the baseline must be the ordinary concatenated matching decoder on the **same sampled detector outcomes**.

A correctness-first implementation may cache two otherwise-identical `ColorCode` objects:

1. ordinary:
   ```python
   enable_colorcorrelated_decoding=False
   ```

2. configured color-correlated:
   ```python
   enable_colorcorrelated_decoding=True
   ```

Before relying on paired decoding, verify that their physical circuit/detector structure is identical. Reuse existing pairing utilities if suitable.

Do not independently resample the baseline.

Repeated baseline matchings are acceptable initially. Do not reach through unstable private state merely for speed.

## 6. Metric definitions

### `default_logical_error`

The ordinary decoder's logical failure for that same shot.

### `better_weight_by_color_correlated_decoding`

Value exactly 1 iff the color-correlated decoder selects a candidate with a strictly smaller **common/base-prior comparison weight** than the selected ordinary three-color solution.

Expected semantics of the current feature branch:

- correlated candidates may be generated with temporary reweighted priors;
- final candidate comparison is done under the original/common stage-2 prior;
- `candidate_generation_weights` must therefore **not** be used for this metric.

Prefer the public `full_output=True` API. Inspect the local implementation and use stable returned fields.

Define a small helper function for the weight comparison and unit-test it. Use exact `<` unless numerical inspection demonstrates that mathematically identical paths can differ by floating-point roundoff; if a tolerance is necessary, make it explicit and small and document it.

### `effect_by_color_correlated_decoding`

Exactly:

```python
(default_logical_error & ~logical_error).astype(np.uint8)
```

It is not “candidate changed”.

## 7. Decoder option forwarding

Build `ColorCode` from:

- resolved sweep fields;
- resolved `NoiseModel`;
- common `color_code_options`;
- decoder-specific constructor `options`.

Pass `decode_options` to `ColorCode.decode`.

Respect current `color-code-stim` incompatibilities. For example, do not force matching-growth SWIM output to coexist with color-correlated decoding if the API rejects it.

## 8. Preserve soft-output code

Do not remove or rewrite:

- current SWIM support;
- current path-gap modules;
- current circuit-level soft-output adapters;
- existing analysis code.

The new worker may ignore those extra fields unless requested by `decode_options`. This task only establishes the minimal required metric set.

## 9. Tests

Add unit/integration tests for:

- one-observable logical-error calculation;
- multi-observable reduction;
- ordinary point returns only `logical_error`;
- correlated point returns all four metrics;
- baseline and correlated decisions use the same physical shots;
- exact `effect = default_fail & ~final_fail`;
- synthetic weight improvement case;
- synthetic weight tie case;
- synthetic no-improvement case;
- generation weight is not used instead of common-prior candidate weight;
- worker result carries correct shot interval and count;
- worker cache is bounded;
- current color-correlated decoder tests still pass;
- relevant existing soft-output tests still pass.

Use only tiny smoke sizes.

## Deliverable

Implement worker-side metric production and tests. Report the exact public worker input/output contract. Stop before adaptive scheduler and storage integration.
