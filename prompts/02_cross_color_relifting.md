# Prompt 2 — Implement adaptive cross-color relifting with all-color anchored candidates

Read `near_optimal_color_code_theory.tex` completely.

Prerequisite: Prompt 1 is complete and the current color-correlated weight
selection tests pass.

## Public option

Add:

```python
enable_cross_color_relifting: bool = False
```

There is no relifting `level` or `max_level` parameter.

Persist through `ColorCode.save/load` with backward-compatible default `False`,
and pass it to `ConcatMatchingDecoder`.

## Hard support condition

Relifting is unsupported when:

```python
remove_non_edge_like_errors=True
```

Raise a clear error before decoding. Check this at the public `ColorCode`
configuration level when practical and defensively inside the decoder.

Do not silently change `remove_non_edge_like_errors`.

With `remove_non_edge_like_errors=False`, verify that the full stage-1/stage-2
decompositions are graphlike enough for the current PyMatching path. If not,
raise an explicit unsupported-configuration error.

## Initial incompatibilities

For the first ablation, reject simultaneous use with:

- existing `enable_colorcorrelated_decoding`;
- prior perturbation ensemble;
- BP/custom DEM priors;
- matching-growth swim output.

Relifting requires all three colors.

## Dedicated module

Create or update:

```text
src/color_code_stim/decoders/cross_color_relifting.py
```

Keep only relifting candidate construction, baseline-equivalence classification,
stage-2-syndrome deduplication, and metadata there. Use the shared candidate
scoring path from Prompt 1.

---

# 1. Baseline decode and canonical physical representation

First run ordinary concatenated MWPM for all three colors and obtain:

```text
x_r
x_g
x_b
```

after mapping each final stage-2 solution back to the common original X/Z DEM
mechanism ordering.

All equality decisions in this prompt are based on these mapped Boolean vectors,
not on color-local native stage-2 indices.

Use exact Boolean equality.

Define per shot:

```python
n_unique = number_of_distinct_rows([x_r, x_g, x_b])

if n_unique == 1:
    relift_run_class = 0
elif n_unique == 2:
    relift_run_class = 1
else:
    relift_run_class = 2
```

This classification is fixed and must not depend on later relift-stage
coincidences.

Use fixed color order:

```text
r < g < b
```

for deterministic representative selection when equal source corrections exist.

---

# 2. Pairwise relifting

For source baseline correction `x_source` in original X/Z DEM ordering:

```python
A1 = dem_manager.dems_decomposed[target].error_map_matrices[0]
u_relift = ((x_source.astype(np.uint8) @ A1.T) % 2).astype(bool)
```

This is XOR/parity.

Do not use `guide_union`.
Do not use Boolean OR.

Check that the relifted vector reproduces the target stage-1 syndrome. Under
the supported full-decomposition mode, a failure is an
implementation/decomposition error.

---

# 3. All-color baseline-anchored relifting

For target `c`, let `d,e` be the other colors.

Given baseline stage-1 vector `u_c` and pairwise relifts
`u_c_from_d`, `u_c_from_e`, define:

```python
delta_d = u_c ^ u_c_from_d
delta_e = u_c ^ u_c_from_e
u_all = u_c ^ delta_d ^ delta_e
```

equivalently:

```python
u_all = u_c ^ u_c_from_d ^ u_c_from_e
```

Do not use OR.
Do not use unanchored `u_c_from_d ^ u_c_from_e`.

Verify the target stage-1 syndrome explicitly.

---

# 4. Adaptive candidate generation from baseline equality

This is required. Do not blindly execute all 9 extra relift branches.

## Case 0: all three baseline original-DEM corrections are equal

Example:

```text
x_r == x_g == x_b
```

Then stop relifting immediately for that shot.

Do not run any additional relift stage-2 MWPM instance.

The final result is selected from/reuses the ordinary baseline result according
to the existing baseline selection semantics.

Set:

```text
relift_run_class = 0
extra_relift_stage2_calls = 0
```

## Case 1: exactly two baseline corrections are equal

Example:

```text
x_g == x_b != x_r
```

Exploit source equivalence exactly.

For target `r`:

- sources `g` and `b` are equivalent;
- choose only the earliest source in `r,g,b` order, therefore `g`;
- consider only `r<-g`.

For target `g`:

- source `b` is equal to target baseline `x_g`, so it adds no new source
  hypothesis;
- consider only `g<-r`.

For target `b`:

- source `g` is equal to target baseline `x_b`;
- consider only `b<-r`.

Generalize this rule rather than hard-coding the specific colors.

Do not execute separate all-color candidates in the 1:2 case. Algebraically
they are aliases of either the baseline or the one nontrivial single-source
relift.

Before stage-2-syndrome early termination, the maximum additional stage-2 calls
for this class is therefore 3.

Set:

```text
relift_run_class = 1
```

and record the actual call count separately.

## Case 2: all three baseline corrections differ

Generate the full relift family:

```text
6 single-source relifts
3 all-color anchored relifts
```

Set:

```text
relift_run_class = 2
```

Maximum extra stage-2 calls before syndrome deduplication: 9.

---

# 5. Mandatory stage-2-syndrome early termination

This is a central requirement.

For each target color `c`, the baseline decoder already solved one exact
stage-2 problem. Construct/store the exact Boolean stage-2 syndrome that was
passed to PyMatching:

```text
baseline_stage2_syndrome[c]
```

For every proposed pairwise or all-color relift hypothesis, construct its full
target stage-2 syndrome **before** invoking `_decode_stage2` / PyMatching.

The comparison must use the complete vector actually passed to stage 2:

```text
target-color physical detector portion
+
appended virtual detector / stage-1 prediction portion
```

If:

```python
candidate_stage2_syndrome == baseline_stage2_syndrome[c]
```

then stop that candidate immediately.

Reason: target color, matching graph, base prior, and syndrome are identical,
so deterministic MWPM must return the same target baseline result.

Reuse the already computed baseline:

- native stage-2 correction;
- mapped original correction;
- observable prediction;
- selection weight;
- any other candidate metadata.

Do **not** invoke stage-2 MWPM.

## General same-target syndrome cache

Implement the above preferably as a generic same-target cache:

```python
cache[(target_color, packed_stage2_syndrome)] = solved_candidate_result
```

Initialize it with the baseline target-color stage-2 problems.

If a later relift candidate for the same target color has the exact same
stage-2 syndrome as any previously solved relift candidate, reuse the cached
result instead of rerunning MWPM.

This is a safe deterministic deduplication and should be implemented if it does
not complicate the architecture.

At minimum, comparison against the baseline target stage-2 syndrome is required.

---

# 6. Logical candidate slots versus actual executed instances

For compatibility and analysis, keep a canonical 12-slot candidate description:

```text
baseline:
r
g
b

single-source:
r<-g
r<-b
g<-r
g<-b
b<-r
b<-g

all-color anchored:
r<-g,b[anchored]
g<-r,b[anchored]
b<-r,g[anchored]
```

However, many slots can be aliases and should not cause MWPM execution.

Examples:

- run class 0: every extra slot is redundant;
- run class 1: only three canonical nontrivial source directions remain before
  stage-2 syndrome deduplication;
- a candidate whose stage-2 syndrome equals baseline aliases the baseline slot;
- two relift candidates with equal target-color stage-2 syndrome alias the
  first solved candidate.

For aliased slots, copy/reuse the already computed candidate's:

- mapped original correction;
- base-aligned native stage-2 correction;
- selection weight;
- generation weight if semantically meaningful;
- observable prediction.

Also record alias/execution metadata so benchmarks can count actual work.

Do not count an alias as an MWPM call.

The theoretical maximum remains:

```text
baseline       6
single relift  6
all-color      3
total         15
```

but actual per-shot cost is dynamic and can be lower.

---

# 7. Selection weights

Use the shared current scoring implementation.

Support both currently implemented bases:

```text
stage2
original_dem
```

Relifting itself uses the base decomposition and prior.

Do not introduce a third score.

Skipped/aliased candidates must inherit the score of the candidate whose
stage-2 problem they exactly duplicate.

---

# 8. Comparative decoding

Baseline equality classification and relifting must be performed separately
inside each logical class.

Never compare or deduplicate source corrections across different logical
classes.

For each class:

1. obtain its three mapped baseline corrections;
2. compute that class's `relift_run_class`;
3. execute/prune relift candidates;
4. minimize candidate weight inside that class.

Then compare logical-class minima.

---

# 9. Full-output metadata

Expose at least:

```python
candidate_labels
candidate_target_colors
candidate_source_colors
candidate_anchor_colors
candidate_kinds
candidate_weights
candidate_weight_basis
candidate_generation_weights
candidate_stage1_validity
candidate_executed
candidate_alias_of
best_candidate_indices

relift_run_class
relift_extra_stage2_calls
```

Kinds:

```text
baseline
single_relift
all_color_relift
```

`candidate_executed` must mean that a new stage-2 MWPM was actually invoked for
that slot, not merely that the logical candidate slot exists.

---

# 10. Tests

Required:

1. disabled path unchanged;
2. `remove_non_edge_like_errors=True` raises;
3. supported full decomposition passes graphlike validation;
4. synthetic mapping proves XOR rather than OR;
5. all generated pairwise/all-color hypotheses preserve target stage-1 syndrome;
6. anchored formula exactly matches
   `u_c ^ u_c_from_d ^ u_c_from_e`;
7. baseline mapped-correction classification:
   - all same -> class 0;
   - exactly two same -> class 1;
   - all distinct -> class 2;
8. class 0 executes zero extra relift stage-2 calls;
9. class 1 chooses canonical equal-source representative by `r,g,b` order and
   has at most 3 extra calls before stage-2-syndrome deduplication;
10. class 2 exposes full 12 logical candidate slots;
11. if a relifted stage-2 syndrome equals baseline stage-2 syndrome, no new
    stage-2 MWPM call occurs and the candidate aliases baseline;
12. if generic same-target syndrome cache is implemented, duplicate relift
    syndromes produce only one actual MWPM call;
13. maximum full-distinct/no-collision call count is 15 total MWPM calls;
14. selected weight is minimum under current common scoring basis;
15. all finite mapped candidates are original-syndrome valid;
16. comparative decoding is class-local;
17. save/load preserves option;
18. incompatible combinations raise.

Use monkeypatch/counters to test actual stage-2 calls; do not infer call count
from wall-clock time.

Run targeted and full tests. Stop here.
