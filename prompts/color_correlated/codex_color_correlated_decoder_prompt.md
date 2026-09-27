# Codex implementation task: color-correlated concatenated MWPM decoding

Repository: `AKTKN/color-code-stim`

## Goal

Integrate a new **color-correlated decoding workflow** into the existing concatenated MWPM decoder.

The current decoder already implements the two-stage concatenated matching workflow for each color. Do **not** reimplement that workflow from scratch. Add a separate, modular layer that reuses the existing stage-1/stage-2 primitives and existing DEM decomposition/provenance information.

The new feature must be controlled by:

```python
enable_colorcorrelated_decoding: bool = False
```

on the existing `ConcatMatchingDecoder` object. When the option is `False`, existing behavior must remain unchanged. When it is `True`, the decoder must generate the 3 ordinary concatenated-MWPM candidates plus 9 color-correlated candidates, rescore all 12 candidates under a common unmodified prior, and return the minimum-weight candidate.

Before changing code, inspect the **currently checked-out branch**. Do not assume `main`: this repository has experimental branches with soft-output/metric additions. Preserve all APIs and metrics that exist in the checked-out branch.

---

## Existing implementation that must be reused

The important current files are:

- `src/color_code_stim/decoders/concat_matching_decoder.py`
- `src/color_code_stim/dem_utils/dem_decomp.py`
- `src/color_code_stim/dem_utils/dem_manager.py`
- `src/color_code_stim/stim_symbolic.py`
- `src/color_code_stim/utils.py`
- `src/color_code_stim/color_code.py`
- `src/color_code_stim/decoders/belief_concat_matching_decoder.py`
- existing tests under `tests/`

Current behavior on `main`:

1. `ConcatMatchingDecoder.decode()` runs `_decode_stage1()` for every logical class/color.
2. `_decode_stage2()` returns the stage-2 prediction and matching weight.
3. The stage-2 prediction is mapped back to the original DEM ordering by
   `DemDecomp.map_errors_to_org_dem(..., stage=2)`.
4. Candidate weights are stored with shape
   `(num_logical_classes, num_colors, num_samples)`.
5. `_get_final_predictions(weights)` chooses the minimum candidate and computes the
   logical gap by first minimizing over the candidate/color axis inside each logical class.
6. `full_output=True` currently returns at least:
   `best_colors`, `weights`, `error_preds`, and, when applicable,
   `logical_gaps`, `logical_values`, etc.

Important decomposition metadata:

- `DemDecomp.error_map_matrices[0]` maps stage-1 columns to original DEM mechanisms.
- `DemDecomp.error_map_matrices[1]` maps stage-2 columns to original DEM mechanisms.
- The rows of these matrices are aligned with the actual `Hs[stage]` / `probs[stage]`
  column order and therefore should be preferred over reconstructing an ordering from
  the unsorted symbolic objects.
- `DemDecomp.org_prob` stores the original DEM probabilities.
- The current standard decomposition uses source provenance already represented by
  these mapping matrices.

Important warning: do not generate a newly sorted stage-2 DEM and then map the result
with the old static `error_map_matrix2`. If column order changes, the mapping is wrong.
Keep the existing H column order fixed and update only probability arrays aligned with
that order.

---

## Mathematical algorithm

Work in one Pauli sector at a time, exactly as the current decoder does.

Let the three baseline final corrections be

```text
e_r^0, e_g^0, e_b^0
```

in the **original DEM error-mechanism ordering**.

For a target color `c`, let the other colors be `a` and `b`.

Generate three additional target-color candidates:

```text
e_c^[a]
e_c^[b]
e_c^[a OR b]
```

where the guide in the third case is the Boolean union of the original-DEM mechanisms
selected by the two baseline corrections. `OR` means `np.logical_or`, never XOR.

This gives at most 12 nominal candidates:

```text
baseline:
  r
  g
  b

correlated:
  r <- g
  r <- b
  r <- (g OR b)

  g <- r
  g <- b
  g <- (r OR b)

  b <- r
  b <- g
  b <- (r OR g)
```

Do not recursively use correlated candidates as new guides in this version.

Before scheduling guided candidates, map the three ordinary corrections to
the original X/Z DEM mechanism order and compare their full binary vectors.
If all three agree, run no extra candidates and report category 0. If exactly
two agree, run only three extra candidates: each repeated-color target uses
the distinct-color guide, and the distinct-color target uses the first
repeated color in `r,g,b` order; report category 1. If all three differ, run
all nine extra candidates and report category 2. Save the selected logical
class's category per shot as `color_correlated_run.parquet`. Keep skipped
diagnostic candidate slots at `+inf` with an explicit false execution mask.

---

## Correlated prior rule

The guide set `G` contains mechanisms of the **pre-decomposition X/Z DEM**.
Condition all selected original mechanisms on being active, simultaneously:

```text
q_reweighted[i] = 1 - eps  if i in G
                  q_original[i] otherwise
```

Use `eps` only to keep matching log-odds finite. Preserve the original DEM's
error targets, detector annotations and mechanism order while replacing these
probabilities. For each target color, **decompose that reweighted original DEM
again**, then rerun both stage-1 and stage-2 MWPM with the resulting matrices,
probabilities and column ordering. In the unit-multiplicity case, a decomposed
column with original source set `B(a)` therefore has marginal probability

```text
p_reweighted[a] = (1 - product_{i in B(a)} (1 - 2 q_reweighted[i])) / 2
```

Multiple selected sources in the same column are conditioned jointly. Do not
take a maximum of single-source conditionals or edit already decomposed
stage-1/2 probabilities independently. The unmodified DEM and decompositions
remain available for baseline candidates and final common-prior scoring.

### Source-order guard

Verify that the guide's original DEM mechanism indices align with the
probability vector and that every re-decomposed stage-2 correction can be
mapped back to original mechanism indices. Re-decomposition may reorder
stage-2 columns; align candidates to the base ordering before common-prior
scoring. Reject any changed source set that cannot be aligned.

---

## Crucial selection-weight rule

The reweighted matching weights are used **only to generate candidates**.

Do **not** compare the nine correlated candidates using their reweighted matching
weights, because each candidate was generated under a different prior.

For every candidate generated for target color `c`, keep its native stage-2 binary
prediction `x_c` before mapping it to the original DEM.

Rescore it using the target color's **base, unmodified stage-2 probabilities for the
current decode call**:

```python
base_llr_c = np.log((1 - base_p2_c) / base_p2_c)
selection_weight = x_c @ base_llr_c
```

This is intentionally the same weight semantics used by the existing concatenated
decoder.

If no custom prior is active, `base_p2_c` is
`dem_manager.dems_decomposed[c].probs[1]`.

If the checked-out branch later supports another uncorrelated base prior, preserve the
meaning "base prior for this call, before color-correlated reweighting."

The returned `extra_outputs["weights"]` must contain this common-prior selection
weight of the final candidate, never the reweighted generation weight.

---

## Proposed code architecture

Create a new module, for example:

```text
src/color_code_stim/decoders/color_correlated_decoding.py
```

Keep probability/provenance logic out of the already-large
`concat_matching_decoder.py`.

Suggested contents:

```python
@dataclass(frozen=True)
class CandidateSpec:
    target_color: str
    guide_colors: tuple[str, ...]   # empty for baseline
    label: str

class ColorCorrelatedPriorReweighter:
    ...
```

The module should:

1. Keep guide mechanism indices aligned with the original X/Z DEM.
2. Construct a per-shot reweighted original DEM and decompose it for the target color.
3. Never mutate `DemManager`, `DemDecomp`, `Hs`, `probs`, or shared decoder state.
4. Return the rebuilt decomposition's stage-1/2 matrices and probabilities to
   the existing `_decode_stage1()` and `_decode_stage2()` methods.

Because guide corrections differ shot-by-shot, the simplest correct first
implementation may run the nine correlated branches per sample. Correctness and clear
interfaces are more important than premature batching. Keep the implementation
structured so identical guide patterns can be grouped/batched later.

---

## Integration into `ConcatMatchingDecoder`

Add:

```python
def __init__(
    self,
    dem_manager: DemManager,
    enable_colorcorrelated_decoding: bool = False,
):
    ...
    self.enable_colorcorrelated_decoding = enable_colorcorrelated_decoding
```

Do not put the whole new algorithm in `__init__`.

In `decode()`:

1. Run the existing baseline workflow unchanged.
2. Preserve all three baseline target-color candidates for each logical class/sample.
3. If `enable_colorcorrelated_decoding` is `False`, execute exactly the old selection
   path.
4. If `True`, after the three baseline stage-2 candidates are available:
   - use their mapped original-DEM corrections as the three guide sets;
   - generate the nine additional candidates;
   - retain for each candidate:
     - target color,
     - guide label,
     - native stage-2 prediction,
     - mapped original-DEM prediction,
     - generation weight (diagnostic only, optional),
     - common-prior selection weight.
5. Stack candidate weights as:
   `(num_logical_classes, 12, num_samples)`.
6. Reuse `_get_final_predictions()` on this array. Its second axis is conceptually now
   a candidate axis, even though the helper currently calls it a color axis.
7. Select the final mapped error prediction using the returned candidate index.
8. Map candidate index -> target color so that existing `best_colors` semantics remain
   unchanged.
9. Observable prediction logic after final correction selection must remain the same.
10. Comparative decoding:
    - build all 12 candidates independently within each logical class;
    - the minimum of the 12 candidates is the class weight;
    - compute `logical_gaps` exactly as the existing helper does from class minima.

Optional diagnostics under `full_output=True` may add fields such as:

```python
candidate_labels
best_candidate_indices
candidate_weights
```

but do not remove or change existing fields.

---

## Color selection constraint

The proposed algorithm requires all three baseline colors. Therefore, when

```python
enable_colorcorrelated_decoding=True
```

require that the effective color set is exactly `["r", "g", "b"]` (order may be
normalized internally). If the user requests only one or two colors, raise a clear
`ValueError`. Do not silently fabricate missing guides.

---

## `ColorCode` API integration

Expose the feature cleanly through the user-facing object as well.

Preferred behavior:

```python
ColorCode(
    ...,
    enable_colorcorrelated_decoding=False,
)
```

Store the value and pass it when lazily constructing `ConcatMatchingDecoder`.

Update:

- class annotations
- constructor docstring
- lazy decoder construction
- serialization / state restoration code if the class explicitly enumerates stored
  fields
- any user-facing docs/examples needed

If the current checked-out branch has a different configuration pattern, follow that
pattern rather than introducing a conflicting one.

---

## BP/custom DEM compatibility

The current `BeliefConcatMatchingDecoder` supplies only per-stage custom `(H, p)` data
to `ConcatMatchingDecoder`. The color-correlated conditional rule also needs
source-level original probabilities/provenance consistent with the base prior.

Therefore, for the first correct implementation:

- do **not** silently combine color-correlated decoding with BP/custom DEMs using the
  wrong source prior;
- if `custom_dem_data is not None` and color-correlated decoding is enabled, raise a
  clear `NotImplementedError` unless you explicitly extend the custom-data interface to
  carry consistent source probabilities and implement it correctly;
- if `ColorCode(bp_predecoding=True, ...)` would route into this unsupported
  combination, make the incompatibility explicit rather than silently ignoring
  `enable_colorcorrelated_decoding`.

This can be generalized later.

---

## Existing soft-output / metric compatibility

Inspect the checked-out branch before implementing.

There are at least two experimental patterns in this repository:

1. A branch with `compute_swim_distance` integrated into stage-2 PyMatching.
2. A branch with correction-based metrics such as
   `metrics/monochromatic_path_gap.py`.

Requirements:

- When `enable_colorcorrelated_decoding=False`, all existing soft-output behavior must
  be unchanged.
- Correction-based metrics that consume the final mapped correction should continue to
  work because `error_preds_final` remains in original DEM ordering.
- Do **not** silently attach a matching-growth-derived soft output from a baseline
  matching run to a final candidate that was generated by a different reweighted
  matching graph.
- If `compute_swim_distance=True` (or an equivalent matching-state-dependent soft
  output exists on the checked-out branch) and no mathematically consistent
  reweighted-candidate implementation is available, explicitly reject the simultaneous
  option with `NotImplementedError`.
- Preserve all existing output keys, shapes, and semantics when the new option is off.

---

## Erasure predecoding and recursive paths

Preserve existing predecoding behavior.

For samples fully resolved by erasure predecoding, do not run the expensive
color-correlated stage unnecessarily.

For samples that proceed to ordinary stage 2, apply the color-correlated expansion
after the three baseline color candidates exist.

If partial-correction recursion calls `self.decode(...)`, the object-level option must
remain effective without needing to pass a hidden flag manually.

---

## Tests

Add focused unit/integration tests. At minimum:

### Backward compatibility

1. With `enable_colorcorrelated_decoding=False`, predictions, weights, best colors,
   logical gaps, and full-output shapes match the old decoder exactly for deterministic
   test vectors.

### Candidate construction

2. With the option enabled and all three colors:
   - exactly 12 candidate branches are represented internally/diagnostically;
   - candidate target colors are correct;
   - OR guide is logical union, not XOR.

### Reweighting math

3. Original-DEM conditioning tests:
   - unselected original mechanisms retain their prior;
   - selected mechanisms have probability `1-eps`;
   - target-color stage-1/2 decompositions are rebuilt from that DEM;
   - multiple guide sources are conditioned simultaneously, with stage-2
     candidate columns realigned to the base ordering before scoring.

### Common-prior rescoring

4. Construct a small synthetic example where the smallest *generation* weight differs
   from the smallest base-prior selection weight. Verify selection uses the base-prior
   weight.

### Validity

5. Final `error_preds` still satisfy the original detector outcomes under
   `check_validity=True`.

### Comparative decoding

6. When comparative decoding is enabled:
   - class minima are taken over all 12 candidates;
   - logical gap is computed from the two smallest class minima;
   - `best_colors` refers to r/g/b target color, not candidate index.

### Unsupported combinations

7. Assert clear errors for:
   - color-correlated decoding with incomplete color set;
   - unsupported `custom_dem_data` / BP combination;
   - unsupported matching-growth soft output + color-correlated combination, if such a
     soft-output feature exists in the checked-out branch.

Run the existing test suite plus all new tests.

---

## Performance / engineering constraints

Baseline concatenated decoding performs 3 color sub-decodings = 6 MWPM calls per
logical class. The proposed method adds 9 two-stage sub-decodings = 18 additional
MWPM calls, for 24 MWPM calls total per logical class, approximately a 4x branch-count
overhead before batching/parallelization.

Do not optimize by changing the algorithm in the first implementation. Preserve the
exact 12-candidate semantics. The nine correlated branches are embarrassingly parallel
and can be optimized later.

Avoid mutating shared `DemManager` probability arrays because decoder instances may be
reused across batches.

---

## Documentation

Add concise docstrings explaining:

- `enable_colorcorrelated_decoding`;
- baseline vs correlated candidate generation;
- OR-guide semantics;
- why correlated generation weights are not used for final selection;
- known unsupported combinations.

Keep terminology consistent with the existing repository: stage 1 / stage 2,
restricted DEM, monochromatic DEM, original DEM ordering, comparative decoding,
logical gap.

---

## Acceptance criteria

The implementation is complete only if all of the following hold:

1. Existing decoder behavior is unchanged when the option is off.
2. The enabled workflow produces the specified 12 candidates.
3. Both stage 1 and stage 2 are reweighted and rerun for each correlated branch.
4. Guide OR is set union / Boolean OR.
5. Final selection uses base unmodified stage-2 weights, not correlated generation
   weights.
6. Final `error_preds` remain in original DEM ordering.
7. `best_colors`, `weights`, and `logical_gaps` preserve their existing semantics.
8. Unsupported soft-output/BP combinations fail explicitly rather than producing
   silently inconsistent values.
9. Tests cover reweighting mathematics, candidate construction, final rescoring,
   comparative decoding, and backward compatibility.
10. The code is modular: correlated-probability logic lives in a new module instead of
    substantially duplicating `ConcatMatchingDecoder`.
