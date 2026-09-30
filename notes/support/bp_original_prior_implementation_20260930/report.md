# BP posterior stage 1 with physical stage 2 and selection

Implemented 2026-09-30 at the user's request. BP fallback now uses posterior
X/Z effective probabilities only for stage-1 candidate generation. Stage 2
is decomposed from original physical X/Z probabilities, with its own correct
column order and source maps. Final selection uses original X/Z log odds.
The physical source probabilities are neither capped nor transformed.

Ordinary no-BP options and behavior are unchanged. BP converged early returns
remain unchanged. BP overrides `use_original_prior_for_stage2=False` and
`color_correlated_weight_basis="stage2"` only inside its fallback wrapper.
Both perturbation modes and color guides retain posterior stage-1 generation;
native per-color random streams, seeds and absolute shot positions are retained.
Global BP state/log version 4 records the policy and rejects earlier states.

## Validation

- Complete decoder suite: 358 passed, two existing skips (39.91 s).
- Complete simulator suite: 399 passed (156.23 s).
- Independent physical-decomposition oracle covers X/Z, comparative and
  superdense circuits, probability-dependent stage-2 order and source maps.
- Stage-1 perturbation draws/weights and guide weights are exactly unchanged.
- Save/load covers original-DEM and native perturbation. Ordinary decoding's
  predictions and RNG progression remain unchanged across BP calls.
- `verify_replay.py` matches an independent preimplementation hybrid-policy
  reference exactly on all 7,740 archived shots; see `replay.json` and
  `provenance.json`. Failure counts: 0/1596 exhaustive d5 single/double faults,
  15/2048 sampled d5, and 18/4096 sampled d7. These are paired bounded checks,
  not evidence of improvement over ordinary concatenated matching.

Run with color_code_so Python and this checkout's root, decoder and PyMatching
src directories on PYTHONPATH. The replay uses archived local NPZ files in the
original workspace; generated physical data are not included in the release.
The preceding hypothesis report and text/JSON evidence are preserved in
`../bp_stage2_original_prior_20260930/`.

## Integration scope

Before this change the native decoder commit `3955196a` and backend commit
`40ef9296` were already ancestors of BP. The only missing native root commit
was `cbe2af2`, containing documentation, timing records and a notebook, with no
Python implementation changes. Integrate its history after publishing this
BP fix. Preserve original workspaces' uncommitted changes and do not merge main.

Integration completed: the root native commit was merged, retaining both sets
of AGENTS/STATUS history after resolving text-only insertion conflicts. The
committed native notebook parses as JSON; root src/tests have no merge changes.
Decoder/backend native histories were already included. No fatal or executable
code conflict occurred. The original dirty workspaces were not modified.
All three remote branch names (bp_predecoding, global BP, native stage 1) are
synchronized by fast-forward publication; main is untouched. Local native
branches checked out in the original workspaces are intentionally not moved.
