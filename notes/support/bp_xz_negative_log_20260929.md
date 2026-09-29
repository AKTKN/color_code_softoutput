# BP fallback: negative-log X/Z mechanism weights

Implemented on `codex/global-bp-predecoding-20260929` in the isolated
`color_code_softoutput_bp_global` root and decoder worktrees. The user's
requested transformation point is the projected X/Z DEM mechanism, which
may still be a hyperedge, before the concatenated decoder's color/stage
decomposition.

## Rule

1. Run BP on the unchanged global DEM. Preserve the converged-shot path.
2. For a fallback shot, use `q = expit(-posterior_llr)` without capping at 0.5.
3. Retain existing independent-XOR aggregation into each X/Z mechanism:
   `p = (1-product(1-2*q))/2`, including detector and observable labels.
4. Assign `w=-log(p)` and encode it for the existing log-odds API as
   `p_eff=p/(1+p)`. This algebraic expression is stable at p=0 and p=1.
5. The existing DEM manager floors effective priors at 1e-14 and rebuilds
   aligned color decompositions using these priors. p=1 gives zero weight;
   p=0.5 gives log(2). Zero probabilities receive a finite maximum weight.

The transformation does not commute with aggregation; applying it to global
mechanisms first would define a different decoder. It is not reapplied to
stage-1/stage-2 edges. Their probability combination, candidate scoring,
guide/perturbation rules and SWIM calculations consume the resulting surrogate
DEM through the existing APIs. These effective priors are not the physical
posterior marginals. The retained XOR aggregation differs from official
belief matching's sum approximation. No LER improvement is inferred.

## Files and compatibility

- Decoder `dem_utils/global_dem.py`: opt-in `negative_log_weights` projection.
  Default projection remains the original independent-surrogate marginal.
- Decoder `decoders/belief_concat_matching_decoder.py`: uncap global q and
  request the new projection only for BP fallback.
- Global BP state and run metadata: version 3,
  `weight_rule="negative_log_xz_probability"`. Version-2 states are rejected
  rather than resumed with a silently changed decoding law.
- Native perturbation scheme remains 2; RNG, seed, absolute shot cursor,
  BP parameters, no-BP laws, saved metric schemas and actual-outcome usage
  are unchanged. PyMatching source is unchanged; no rebuild is needed.
- Historical saved runs are unchanged. Use this worktree's source paths in
  PYTHONPATH for new runs and restart already-imported Python processes.

## Validation

Independent small DEM tests distinguish transformation after X/Z aggregation
from transformation before projection or clipping global q at 0.5. They
check target/observable preservation and exact log-odds identities, including
q=0, 1, 0.5, 0.9, 0.99 and very small probabilities.

Fallback decoding is compared with a separately built reference that first
projects raw posteriors, explicitly calculates `-log(p)`, then inverse-maps
the weights into probabilities. Corrections, predictions and scores agree
for ordinary, comparative, color-correlated, relifting, original-DEM and
native-stage-1 perturbation. Full/compact output, physical correction
validity, split batches, save/load, old-state rejection, spawned workers and
run-log law versions are covered.

From the BP worktree root, use:

```bash
export PYTHONPATH="$PWD/src:$PWD/external_libs/color-code-stim/src:$PWD/external_libs/PyMatching/src"
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest -q external_libs/color-code-stim/tests/test_global_bp.py external_libs/color-code-stim/tests/test_global_dem_projection.py tests/test_global_bp_workflow.py
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest -q external_libs/color-code-stim/tests
/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python -m pytest -q tests
```

Focused tests: **62 passed**. Full decoder suite: **345 passed, 2 existing
skips**. Root suite: **386 passed**.

Source review used independent test oracles in the same agent session; it
was not external peer review. No performance or logical-error campaign,
commit, push or main merge was performed.
