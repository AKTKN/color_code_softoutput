# Updated implementation plan — adaptive execution revision

This bundle supersedes `near_optimal_color_code_implementation_v2`.

The algorithmic definitions remain:

- cross-color relifting:
  - 3 baseline candidates;
  - 6 pairwise relift candidate slots;
  - 3 all-color baseline-anchored candidate slots;
- prior perturbation:
  - perturb the common X/Z-separated DEM;
  - re-decompose that same perturbed DEM for r/g/b;
  - run full two-stage concat-MWPM for each member/color;
- candidate selection:
  - use the same current common-prior weight evaluation path as the latest
    color-correlated implementation.

The important new change is **adaptive execution**.

## Baseline equality class

After the ordinary three color branches are mapped back to the common original
X/Z DEM mechanism ordering, classify each shot:

```text
0 = x_r == x_g == x_b
1 = exactly two of x_r, x_g, x_b are equal
2 = all three are different
```

This is the same semantic classification currently being added for
`color_correlated_run.parquet`.

For relifting, save the analogous code in `relift_run.parquet`.

## Relifting adaptive execution

- Class 0:
  - terminate relifting immediately;
  - no extra relift Stage-2 MWPM call.
- Class 1:
  - collapse the two equal baseline corrections into one source-equivalence
    class;
  - use `r < g < b` to choose the canonical representative;
  - execute only the three nontrivial source directions at most;
  - all-color anchored candidates are aliases and do not require separate
    Stage-2 calls.
- Class 2:
  - expose the full 6 pairwise + 3 all-color logical candidate slots.

Additionally, before every relift Stage-2 MWPM call:

```text
construct exact candidate Stage-2 syndrome
compare it to the baseline target-color Stage-2 syndrome
```

If equal, terminate that instance and reuse the baseline result. Prefer a
general same-target Stage-2-syndrome cache so two relift candidates with the
same syndrome share one solved result.

Therefore 15 MWPM calls is now a **maximum**, not a fixed relifting cost.

## `relift_run.parquet`

Do not invent a new unrelated storage convention. Inspect the current local
implementation of `color_correlated_run.parquet` and mirror:

- shot identity keys;
- row order;
- Arrow dtypes;
- atomic write/shard conventions;
- metadata/provenance conventions.

The relift run-class value is exactly:

```text
0 -> all three mapped baseline corrections equal
1 -> exactly two equal
2 -> all three distinct
```

Also record the actual extra relift Stage-2 call count if the sidecar
architecture supports additional diagnostic columns.

## Repository-state note

The GitHub branch visible during preparation may lag the user's active local
changes. In particular, the user is currently modifying color-correlated
adaptive execution and its sidecar.

Codex must inspect the local working tree first:

```bash
git status --short
git branch --show-current
git log -8 --oneline
git diff
```

Treat local files as authoritative. Do not reset/checkout/rebase or overwrite
in-progress color-correlated changes.

## Prompt order

1. `01_shared_candidate_scoring.md`
2. `02_cross_color_relifting.md`
3. `03_xz_dem_perturbation_ensemble.md`
4. `04_integration_regression.md`
5. `05_softoutput_experiment_integration(1).md`
6. `06_ablation_benchmark.md`

Read `near_optimal_color_code_theory.tex` first.
