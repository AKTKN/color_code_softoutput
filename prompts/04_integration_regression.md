# Prompt 4 — Integration and regression hardening with adaptive execution

Prerequisites:

- shared candidate-scoring refactor passes;
- adaptive cross-color relifting passes;
- X/Z-DEM perturbation passes;
- the user's current color-correlated adaptive-pruning changes are preserved.

## Important local-state rule

The user is actively modifying color-correlated decoding. Before editing:

```bash
git status --short
git branch --show-current
git log -8 --oneline
git diff
```

Inspect the current local implementation of:

- baseline-solution equality classification;
- color-correlated branch pruning;
- canonical `r,g,b` representative choice;
- `color_correlated_run.parquet` generation;
- current candidate-weight selection.

Do not overwrite, revert, or independently reimplement those changes.

## Three advanced strategies

The project has:

1. existing color-correlated prior conditioning;
2. adaptive cross-color relifting;
3. X/Z-DEM prior perturbation ensemble.

For the first study they remain mutually exclusive.

## Centralized option validation

At minimum reject:

```text
relifting + color correlation
relifting + perturbation
color correlation + perturbation
advanced modes + incompatible BP/custom DEM
advanced temporary-graph modes + matching-growth swim when unsupported
```

Relifting additionally requires:

```text
remove_non_edge_like_errors=False
```

Do not silently override settings.

## Shared baseline-equivalence helper

Avoid having color-correlated and relifting modes classify the same three
mapped baseline corrections using different logic.

If the local color-correlated work already introduced a helper, reuse it.
Otherwise extract a small common helper operating on:

```text
x_r, x_g, x_b
```

in original X/Z DEM ordering.

Required classification:

```text
0: all three equal
1: exactly two equal
2: all distinct
```

Use exact Boolean-vector equality.

Also expose deterministic equality groups with fixed color order:

```text
r < g < b
```

so both strategies choose identical canonical representatives.

Do not make this helper depend on the downstream strategy.

## Preserve color-correlated semantics

The user's intended adaptive color-correlated behavior is:

### class 0

If:

```text
x_r == x_g == x_b
```

stop color-correlated redecoding for the shot.

### class 1

Example:

```text
x_g == x_b != x_r
```

Use only:

```text
r guided by canonical representative of {g,b} -> g
g guided by r
b guided by r
```

Do not execute the redundant equal-source and redundant multi-guide branches.

The representative among equivalent sources is the earliest in `r,g,b` order.

### class 2

Use the full current color-correlated branch family.

Do not change the user's current local implementation if it already realizes
this.

## Relifting adaptive behavior

The relifting path must use the same baseline class but a different downstream
rule:

### class 0

No extra relift Stage-2 call.

### class 1

Collapse equal sources. At most three nontrivial pairwise relifts remain.
All-color anchored candidates are aliases and do not cause separate Stage-2
calls.

### class 2

Six pairwise + three all-color logical candidate slots are available.

For every actual relift candidate, construct its exact Stage-2 syndrome before
decoding. If it matches the baseline target-color Stage-2 syndrome, reuse the
baseline result with zero additional MWPM call.

Prefer a same-target Stage-2-syndrome cache for exact duplicate relift
syndromes.

## Candidate weight semantics

Do not create strategy-specific final scoring.

All strategies must use the latest committed/local current scoring semantics:

```text
selection basis = stage2 or original_dem
generation weight != selection weight
temporary Stage-2 -> align to base before stage2-basis scoring
```

Keep `candidate_weight_basis` in full output.

If local color-correlated code changed the weight-evaluation helper after this
prompt was authored, use the local helper as source of truth and adapt relifting
and perturbation to it.

## Sidecar/data contract

Do not make `color-code-stim` and `color_code_softoutput` independently invent
different run-class schemas.

Wherever the current local project writes:

```text
color_correlated_run.parquet
```

use that exact infrastructure for:

```text
relift_run.parquet
```

The required relift run-class code is:

```text
0 -> all three mapped baseline corrections equal
1 -> exactly two equal
2 -> all distinct
```

This code is determined before relifting and must not be changed by later
Stage-2 syndrome collisions.

If the existing sidecar supports additional diagnostic columns, add:

```text
extra_stage2_calls
num_candidate_slots
num_unique_stage2_syndromes
```

but do not alter the 0/1/2 meaning.

## Comparative decoding

Classification is per logical class. Never group corrections from different
logical classes.

For each class:

1. baseline decode;
2. classify three baseline corrections;
3. adaptively generate candidates;
4. minimize selection weight.

Then compare class minima and compute the logical gap.

## Documentation

Document:

```text
ordinary concat:
  3 candidates
  6 calls

relifting:
  canonical logical slots: 12
  maximum calls: 15
  actual calls are dynamically pruned

perturbation:
  3*M candidates
  6*M calls

color-correlated:
  document current adaptive branch counts from the local implementation
```

State explicitly that `relift_run` and `color_correlated_run` classify baseline
solution multiplicity, not actual runtime directly.

## Regression tests

Add/retain tests for:

- common 0/1/2 baseline classification;
- deterministic representative selection;
- color-correlated pruning remains exactly as current user implementation;
- relifting class-0 zero-extra-call path;
- relifting class-1 reduced source directions;
- relifting Stage-2 baseline-syndrome early exit;
- relifting same-target duplicate-syndrome cache if implemented;
- correct actual call counters;
- both weight bases;
- comparative class-local behavior;
- sidecar run-class output;
- no historical behavior change when advanced strategies are disabled.

Run the complete repository test suite after targeted tests.

Do not implement K-best matching.
