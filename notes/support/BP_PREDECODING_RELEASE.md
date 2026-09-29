# bp_predecoding publication — 2026-09-30

The user requested commit/push of the implementation and correction series
to branch `bp_predecoding` in all three independent repositories:

- `AKTKN/color_code_softoutput`: BP YAML workflow, versioned experiment logs,
  nullable metric storage, saved-run analysis, example configuration and audits.
- `AKTKN/color-code-stim`: global-DEM BP before CSS decomposition, converged
  early return, shot-local fallback and negative-log X/Z weighting version 3,
  commit `bd2ed2a` (on top of the initial BP implementation `65ef2ad`).
- `AKTKN/PyMatching`: opt-in native probability clipping for BP perturbations,
  commit `0f143d6f9`; the implementation was already committed and needs no
  artificial additional commit to publish the new branch.

The final weighting rule is global posterior -> independent-XOR X/Z
aggregation -> -log(p) -> effective probability p/(1+p) -> color/stage
decomposition. Raw global posteriors are not capped. Native perturbation
retains scheme version 2, while global BP state/logs use version 3. Old BP
states cannot silently replay under the changed weighting law.

The later user-requested analysis correction is included: LER divides saved
True counts by **all physical shots**, preserving original baseline selection.
Missing converged-shot failure labels are not reconstructed. Soft-output
statistics use only scored shots and reject pooled incompatible BP scopes.
Historical reports describing conditional LER are superseded by
[saved-run analysis](BP_SAVED_RUN_ANALYSIS.md) and the current tests.

For depolarizing code capacity with one data-noise layer and both detector
sectors, use rounds=2, perfect_first_syndrome_extraction=True and
exclude_non_essential_pauli_detectors=False; see README.md.

The original workspace's execution-only notebook changes and generated
experiment data are not part of this release. Audit scripts, JSON summaries
and reports are included; raw NPZ/Parquet inputs and the surface smoke's
generated results remain local and are not bundled. Historical scripts may
require those archived inputs and the recorded workspace paths. This is not
a claim that every historical run can be replayed from a clean clone.

Validation and final acceptance counts are recorded in STATUS.md. The
PyMatching source is unchanged from its prior Python/C++ acceptance. No main
merge or force push is part of this publication.
