# Prompt 1 — Make candidate scoring reusable without changing behavior

Read `near_optimal_color_code_theory.tex`.

Goal: refactor only the current candidate evaluation logic used by
color-correlated decoding so relifting and perturbation can reuse it. Do not add
the new strategies yet.

Inspect:

- `src/color_code_stim/decoders/concat_matching_decoder.py`
- `src/color_code_stim/decoders/color_correlated_decoding.py`
- `src/color_code_stim/dem_utils/dem_decomp.py`
- `src/color_code_stim/dem_utils/dem_manager.py`
- `src/color_code_stim/color_code.py`
- `tests/test_color_correlated_decoding.py`

The inspected version already has:

```python
color_correlated_weight_basis in ("stage2", "original_dem")
align_stage2_to_base(...)
candidate_generation_weights
candidate_weight_basis
```

Do not overwrite a newer local implementation.

## Required semantics

### Stage-2 basis

For target color `c`, score in the unmodified base stage-2 column ordering:

```python
base_p = dem_manager.dems_decomposed[c].probs[1]
base_llr = np.log((1 - base_p) / base_p)
score = base_native.astype(float) @ base_llr
```

If generated from a temporary decomposition, first use current
`align_stage2_to_base(...)`.

### Original-DEM basis

```python
q = dem_manager.probs_xz
llr = np.log((1 - q) / q)
score = mapped_original.astype(float) @ llr
```

### Generation weight

The MWPM weight under a temporary conditioned/perturbed prior is diagnostic
only. It must not select the final candidate.

Extract the smallest safe internal helper(s) so all advanced candidate
generators can return:

- mapped original correction;
- base-aligned native stage-2 correction;
- base-prior selection weight;
- generation weight.

Prefer reusing `align_stage2_to_base` instead of duplicating alignment.

Do not rename/remove `color_correlated_weight_basis` in this task.

## Regression tests

Prove:

1. `stage2` scoring equals base-aligned stage-2 LLR scoring.
2. `original_dem` scoring equals mapped-original LLR scoring.
3. generation weights do not control selection.
4. temporary stage-2 reorderings are aligned correctly.
5. comparative logical gaps use the minimum candidate score in each class.
6. behavior is unchanged when color correlation is disabled.

Run targeted tests and the full existing `color-code-stim` suite. Stop here.
