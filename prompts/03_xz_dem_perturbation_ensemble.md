# Prompt 3 — Implement perturbation on the common X/Z-separated DEM

Read `near_optimal_color_code_theory.tex`.

This prompt replaces the earlier "stage-1 perturbation" design.

## Public options

Add:

```python
enable_prior_perturbation: bool = False
perturbation_ensemble_size: int = 1
perturbation_alpha: float = 0.0
perturbation_seed: int | None = None
```

Names may be adjusted minimally to repository conventions, but do not describe
this as "stage-1 perturbation": the perturbation is applied before color
decomposition and therefore changes the induced priors of both concatenated
stages.

Persist the options through `ColorCode.save/load`.

Validate:

```text
ensemble_size >= 1
0 <= alpha <= 1
```

## Initial incompatibilities

For the first independent ablation, reject simultaneous use with:

- cross-color relifting;
- existing color-correlated decoding;
- BP/custom DEM prior updates;
- matching-growth swim output.

Do not silently combine strategies.

Unlike relifting, this strategy does not require
`remove_non_edge_like_errors=False`; re-use the base manager's decomposition
policy.

## Perturb the common X/Z DEM

Use:

```python
dem_manager.dem_xz
dem_manager.probs_xz
```

This is the pre-color-decomposition X/Z-separated DEM.

Do not independently perturb:

```text
dems_decomposed["r"].probs[0]
dems_decomposed["g"].probs[0]
dems_decomposed["b"].probs[0]
```

For ensemble member `m`, create one perturbed original probability vector and
use it for all three colors.

Member 0 is exactly the baseline:

```python
q_m = q_base
```

For `m > 0`:

```python
xi ~ Uniform(-1, 1) independently for each original X/Z DEM mechanism
q_m = clip(q_base * (1 + alpha * xi), eps, 1 - eps)
```

Use an epsilon consistent with existing decoder code.

The perturbation must be fixed by `(seed, member, source_index)` and not depend
on shot ordering or batch partition.

## Rebuild the temporary original DEM

Preserve exactly:

- number of original error mechanisms;
- original source ordering;
- detector targets;
- observable targets;
- non-error DEM instructions.

Only probabilities change.

The current `ColorCorrelatedPriorReweighter` already contains closely related
logic for replacing original X/Z DEM probabilities while preserving targets.
Reuse or extract the common low-level mechanism instead of implementing a
second incompatible builder.

Never mutate the base DEM or `probs_xz`.

## Re-decompose for all three colors

For one member, construct:

```python
DemDecomp(
    org_dem=temporary_xz_dem,
    color=c,
    remove_non_edge_like_errors=dem_manager.remove_non_edge_like_errors,
)
```

for `c in ("r", "g", "b")`.

All three decompositions of one ensemble member must come from the same
temporary X/Z DEM.

Then run the full ordinary concatenated decoder for each color:

```text
temporary stage 1
temporary stage 2
```

Thus one member uses 6 MWPM calls.

## Ensemble semantics

`perturbation_ensemble_size=M` is the total number of members including
baseline member 0.

Therefore:

```text
M=1 -> exactly baseline concat-MWPM
candidates per logical class = 3*M
MWPM calls per logical class = 6*M
```

Perturbed priors are decoder-instance ensemble parameters, not shot-specific
randomness. Reuse them across:

- shots;
- batches;
- logical classes.

## Candidate selection

Temporary priors are for candidate generation only.

After temporary stage 2:

1. use the exact current `align_stage2_to_base(...)` semantics to obtain:
   - mapped original X/Z DEM correction;
   - base-aligned target-color native stage-2 correction;
2. route the candidate through the shared evaluator from Prompt 1.

For `stage2` basis:

```text
temporary native
 -> align to base target-color stage2 ordering
 -> score with base stage2 LLR
```

For `original_dem` basis:

```text
temporary native
 -> map to original X/Z DEM ordering
 -> score with base original DEM LLR
```

The MWPM weight returned under the temporary perturbed member is stored only as
`candidate_generation_weights`.

Never use perturbed-member weights for final selection.

## Candidate metadata

Recommended ordering:

```text
member 0: r, g, b
member 1: r, g, b
...
member M-1: r, g, b
```

Expose:

```python
candidate_labels
candidate_target_colors
candidate_ensemble_members
candidate_weights
candidate_weight_basis
candidate_generation_weights
best_candidate_indices
```

If useful, store a deterministic hash of each member's perturbed `q` rather
than duplicating the full probability vector per shot.

## Tests

Required:

1. `M=1` exactly reproduces baseline;
2. `alpha=0` produces baseline-equivalent members;
3. same seed -> same temporary X/Z priors;
4. different seed with `alpha>0` -> at least one prior differs;
5. one member prior is shared across all three color decompositions;
6. original target/observable/source ordering is unchanged;
7. base DEM/probabilities are never mutated;
8. candidate count is `3*M`;
9. MWPM call count is `6*M` per logical class;
10. one-batch and split-batch decoding agree for fixed seed/configuration;
11. temporary stage-2 order is aligned before base-stage2 scoring;
12. `stage2` and `original_dem` scoring match the shared evaluator;
13. generation weights cannot change final selection;
14. comparative decoding reuses the same ensemble but remains class-local;
15. save/load preserves deterministic ensemble configuration;
16. forbidden strategy combinations raise clear errors.

Run targeted and full tests. Stop here.
