# Prompt 5 — Integrate adaptive run classes into `AKTKN/color_code_softoutput`

This prompt applies to `color_code_softoutput` after the decoder changes exist
in the local `color-code-stim` checkout.

Read the local `AGENTS.md`, project-status documents, and the current
color-correlated experiment changes before editing.

## Do not overwrite active work

The user is currently adding:

```text
color_correlated_run.parquet
```

with per-shot values:

```text
0 = all three baseline mapped corrections equal
1 = exactly two equal
2 = all three distinct
```

Inspect the actual local writer/schema first. Reuse its infrastructure rather
than creating a parallel convention.

## Goal

Add the analogous:

```text
relift_run.parquet
```

and use adaptive runtime diagnostics in the paired decoder benchmark.

## Relift run-class definition

After baseline concat-MWPM, map all three color solutions to the common
original X/Z DEM mechanism ordering.

For each shot:

```python
if x_r == x_g == x_b:
    relift_run = 0
elif exactly_two_are_equal(x_r, x_g, x_b):
    relift_run = 1
else:
    relift_run = 2
```

This classification must exactly match the shared helper used inside
`color-code-stim`.

Do not derive it from:

- selected candidate;
- number of relift calls;
- final LER;
- Stage-2 syndrome collisions.

## Sidecar schema

Mirror the current `color_correlated_run.parquet` conventions exactly for:

- stable shot IDs;
- configuration IDs;
- batch IDs;
- row ordering;
- Arrow dtype of the run-class field;
- atomic writes;
- resume/error handling;
- source/provenance metadata.

Rename only what is necessary for relifting.

If the current sidecar stores just one integer plus identity columns, do the
same.

If it supports additional diagnostics, add compatible relifting fields such as:

```text
extra_stage2_calls
num_unique_stage2_syndromes
```

but preserve the mandatory 0/1/2 run-class field.

## Paired experiment workflow

For every physical shot, run/record:

1. baseline concat-MWPM;
2. existing adaptive color-correlated decoder;
3. adaptive cross-color relifting;
4. prior perturbation ensemble.

Use the same sampled detector/observable outcome for all strategies.

Never substitute independent sampling.

## Relifting runtime diagnostics

Record:

- `relift_run`;
- actual additional relift Stage-2 MWPM calls;
- total MWPM calls if available;
- number of logical candidate slots;
- number of actually solved unique target Stage-2 syndromes;
- count of aliases to baseline;
- count of aliases to another relift candidate;
- selected candidate kind:
  - `baseline`
  - `single_relift`
  - `all_color_relift`.

This is important because the logical candidate set can have 12 slots while
the actual execution cost is much lower.

## Relifting diagnostic analyses

Report by `relift_run` class:

```text
shot fraction
LER
rescue rate
regression rate
mean/median actual extra Stage-2 calls
selected-candidate composition
```

Also report overall:

- fraction of pairwise relift Stage-2 syndromes equal to the baseline target
  Stage-2 syndrome;
- fraction of relift candidates skipped due to same-target syndrome cache;
- distribution of unique solved Stage-2 problems per shot.

## Color-correlated diagnostics

Do not modify the semantics of the user's current
`color_correlated_run.parquet`.

Use it in the same analysis style so the two adaptive strategies can be
compared by baseline multiplicity class.

## Candidate weight basis

`color-code-stim` is the source of truth.

Store/read:

```text
candidate_weights
candidate_weight_basis
weights
```

Do not recompute production selection weights independently in
`color_code_softoutput`.

On a bounded audit subset, independently verify the formulas.

## Historical data safety

Use a new result root/schema version.
Do not overwrite SWIM/path-gap/previous color-correlated datasets.

## Smoke test only

Run a bounded smoke experiment sufficient to produce and validate both:

```text
color_correlated_run.parquet
relift_run.parquet
```

Do not launch production-scale sampling.

Report the production command only.
