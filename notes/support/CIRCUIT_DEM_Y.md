# Circuit DEM-Y implementation report — 2026-09-19

Implemented [the requested prompt](../../prompts/codex_circuit_dem_y_gap_integration_prompt.md)
in the existing `external_libs/color-code-stim-monotone-y/` feature worktree.
The reusable APIs, certified family compiler, exact sparse junction evaluator,
optional C++ acceleration, independent oracles, runnable example, timing harness
and standalone paper-style description are complete. The score is exact within
the specified family. **Measured scoring is slower than an ordinary decode;
the intended wall-clock efficiency advantage has not been achieved.** No
post-selection competitiveness or calibration claim follows from these checks.

## Deliverables and supported model

The feature worktree remains on `feature/monotone-y-gap`, based on
`0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`. Its existing, uncommitted code-capacity
monotone-Y implementation was preserved; only its public export file gained
new APIs and its README gained a separate entry. No existing decoder source,
path-gap source, notebook, saved dataset, or installed package was changed.
No commit, push, PR, or large sampling campaign was requested or performed.

Package files, relative to that worktree:

- `src/color_code_stim/metrics/_dem_y_geometry.py`: error-only DEM parsing,
  exact D/O/probability comparison, explicit maps, native operations, separate
  base and enriched pruning, all-path nonreuse and strong cap certificates.
- `src/color_code_stim/metrics/circuit_dem_y_gap.py`: independent evaluator, signed two-parity DAG,
  exact local joins, single/batch APIs, optional winning witnesses and validation.
- `src/color_code_stim/metrics/_dem_y_junction.py`: readable sparse zero-edge/one-edge/wedge solver.
- `src/color_code_stim/metrics/_dem_y_adapter.py`: checked uniform-noise ColorCode snapshot and
  final `error_preds` adapter. No decoder entry points are invoked.
- `src/color_code_stim/metrics/_dem_y_packed.py`, `src/color_code_stim/metrics/_dem_y_native.cpp`, `setup.py`: compact
  immutable arrays and optional native acceleration, with an exact Python fallback.
- `tests/dem_y_oracle.py`, `tests/test_circuit_dem_y_gap.py`,
  `tests/test_circuit_dem_y_junction.py`: independent set/path and Cartesian oracles.
- [API guide](../../external_libs/color-code-stim-monotone-y/docs/circuit_dem_y_gap.md),
  [paper-style PDF](../../external_libs/color-code-stim-monotone-y/docs/circuit_dem_y_algorithm.pdf),
  and [TeX source](../../external_libs/color-code-stim-monotone-y/docs/circuit_dem_y_algorithm.tex).
- [One-decode example](../../external_libs/color-code-stim-monotone-y/examples/circuit_dem_y_gap.py)
  and [bounded benchmark](../../external_libs/color-code-stim-monotone-y/examples/benchmark_circuit_dem_y.py).

Initial adapter scope: triangular 6.6.6 Z memory, odd d >= 3, integer T >= 1
including T != d, the checkout's tri_optimal vector, nonsuperdense extraction,
uniform circuit noise with all granular settings checked, all perfection flags
false, all Pauli detector rows retained, and one target observable. It uses the
actual decoder `dem_xz` and marginal p_j, requiring 0 < p_j < 1/2. It does not
retain the original joint X/Z depolarizing correlations. A column is a DEM
error instruction, not a physical qubit or necessarily one gate location.

Comparative bookkeeping circuits are explicitly unsupported by this initial
adapter. Full-coordinate methods accept any already-produced correction in
the exact compiled ordinary DEM ordering. No automatic cross-model conversion
is inferred from equal array sizes. Standalone `from_dem` checks the algebraic
family on explicit metadata without asserting a physical circuit origin.
The installed checkout's ordinary `ColorCode.decode` has no
`get_swim_distance` keyword; the example calls its actual API without that flag.

## Correctness and audit

The [paper](../../external_libs/color-code-stim-monotone-y/docs/circuit_dem_y_algorithm.pdf)
contains definitions, both algorithms, ten labelled propositions with proofs,
complexity and limitations. The critical proof chain is: exact DEM maps →
endpoint transport identity → all-path nonreuse → strong union cap separation
→ signed parity DAG → exact sparse join → restricted-family minimum. Root
folding, the +4 triple-intersection term, and adding the common root constant
once are all tested independently. Logical parity is the DEM observable,
never physical-qubit weight parity.

For every accepted compiled geometry, the score satisfies
`Delta_E,Z <= S_DEMY`. Equality requires coverage of a sector minimizer.
`S_DEMY = Gamma - eta + rho` separates baseline suboptimality and family
restriction. Comparison to a forced candidate requires that its difference
support belongs to this family, in the same model with outside-sector faults
frozen. Existing decoder `logical_gaps` are not identified with these exact
quantities. The references supply background; the new algorithm and guarantees
are the prompt's proposed construction and the local conditional derivation.

This was a separate same-agent source/logic review supported by independent
executable oracles, not external peer review. Review findings and safeguards:

- The error-only parser preserves separator and duplicate-target XOR semantics;
  it rejects disagreement with the checkout's Boolean matrix parser instead of
  inheriting an incorrect parity/order. Nontrivial invisible columns are rejected.
- The terminal-level cut is essential. A deliberate high→low→sink fixture
  exposes repeated columns when the cut is removed; the compiler reports them.
- An independent oracle initially visited only operation destinations and missed
  a highest source in the adversarial reuse test. It was corrected to enumerate
  paths from every source. Production certificates already checked every source.
- Tail enrichment uses raw base operations; a dedicated fixture has operations
  pruned from G0 that become useful in G1. Base first choices remain separate.
- Strong compatibility is checked against all suffixes. No minimum-tail-only
  certificate or cap-XOR-only relaxation is used. Global union bitsets are
  released after compiling constraints; setup is not claimed to be linear.
- The exact sparse kernel retains zero-valued structural interactions, uses
  bounded local shortlists, and deduplicates triangles by their least option ID.
  Small graph adjacency masks have an exact sparse fallback above 64 options;
  both sides of that boundary are tested. No Cartesian root scan occurs online.
- Weights and geometry are immutable snapshots with separate exact hashes.
  Ordered D/O data, full metadata, target, circuit/settings, policy and compiler
  version enter cache identity. New probabilities cannot reuse old weights.
- Final corrections and hard outputs remain read-only. Optional full syndrome
  validation rejects failed baselines; an explicit false decoder validity flag
  always raises. Actual sampled observables appear only in external evaluation.

## Validation

From the feature worktree:

```bash
PYTHONPATH=src /home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python \
  -m pytest tests/test_circuit_dem_y_gap.py tests/test_circuit_dem_y_junction.py -q
# 56 passed, before the final equivalent triangle-dedup optimization

PYTHONPATH=src /tmp/monotone-y-venv/bin/python -m pytest -q -rs
# Final complete package: 163 passed, 2 existing skips (53.41 s)
```

The temporary venv derives from `color_code_so` and uses ordinary upstream
PyMatching 2.3.1; the installed Conda environment is unchanged. The two existing
skips concern comparative rec_stability. In the workspace root, the existing
monotone-Y experiment regression also passes **7 tests** in 44.65 s. Native
wheel building and a separate extracted-wheel import/decode/witness smoke pass.

The 56 new tests cover 480 random sparse joins against direct cap XOR Cartesian
minima, both native and Python kernels; empty/infinite parts, arbitrary forbidden
pairs, triple/root overlaps, zero sharing costs and isolates; a tiny synthetic
full logical enumeration and independent declared-family enumeration; actual
(d,T)=(3,3),(5,5),(7,7),(3,1),(5,2),(3,5); signed and zero weights; unreachable
parities; full/sector row and column permutations; explicit inverse witness
maps; operation and cap certificates; >5-column signature groups; temporal
movement in both directions; forbidden long stationary stretches; scope and
probability rejection; cache/empty/shape checks; baseline validity; unchanged
extras; and instrumented zero decoder calls during scoring.

Reference observations reproduced independently:

| d=T | Z-sector columns | Base operations r/g/b | Tail operations r/g/b | First options, total / max per root | Interaction edges, total / max degree |
|---|---:|---|---|---|---|
| 3 | 59 | 38 / 41 / 38 | 98 / 106 / 98 | 990 / 34 | 755 / 6 |
| 5 | 329 | 186 / 182 / 198 | 511 / 500 / 545 | 6,379 / 40 | 4,140 / 19 |
| 7 | 973 | 530 / 497 / 586 | 1,495 / 1,403 / 1,656 | 21,973 / 46 | 11,715 / 20 |

All audited roots have surviving first options in every required part. Actual
nonempty groups have at most five columns; that observation is not hard-coded.
The d=3,T=3 oracle obtains **3,337 distinct odd supports**, agreeing for positive,
negative, zero and tied signed costs. Since each color has one spatial face at
d=3, first base operations already terminate; enriching subsequent tails leaves
this count unchanged. The d=5,T=5 independent oracle obtains **70,755 distinct
cap/head tuples**. Native paired endpoints reach a two-round time difference.
All these are finite checks, not all-distance coverage or degree theorems.

The runnable example performs one ordinary decode on **1,000 physical shots**
at d=T=5,p=.001,seed=12345, with all baseline syndromes valid and ten checked
winning witnesses. Hard predictions and original extras are unchanged.
There are two logical failures in external evaluation. This count has no role
in score computation and is not a proxy-quality study.

## Timing and remaining limitations

Native kernel, Intel Core i7-13700H, Linux/WSL, CPU affinity 0, Python 3.12,
100 stored shots per distance, five warm repetitions, median microseconds/shot.
`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`; p=.001 and T=d.

| d | Ordinary decode (µs) | Score only (µs) | Decode + score (µs) | Witness + validation (µs) | Metric setup (s) | Traced compiler peak (MiB) | Process peak RSS (MiB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 3 | 63.6 | 162.4 | 237.1 | 211.0 | 0.047 | 1.05 | 217.4 |
| 5 | 126.5 | 1457.4 | 1625.3 | 1600.5 | 0.336 | 6.27 | 236.8 |
| 7 | 284.3 | 4526.9 | 4989.0 | 4809.9 | 0.993 | 20.49 | 290.5 |

The harness uses identical stored corrections and detector batches, reports
warm repeated measurements, excludes sampling/I/O/build warmup, and measures
score-only and witness validation separately. Geometry setup excludes ordinary
circuit/DEM construction. Compiler memory is measured in a separate traced
run; process peak RSS is also reported and includes imports, ordinary code
objects and allocator history. RSS is a process high-water mark, not a
geometry-only allocation. The support-union bitset estimate alone is much
smaller than total Python compilation memory and must not be presented as the
whole setup cost.

Native C++ acceleration, compact arrays, exact <=64-option adjacency masks,
partial local selection and duplicate-triangle elimination reduce interpreter,
lookup and duplicate-candidate work without changing the family. The before/after
measurements retain system variation; individual changes are not claimed as
isolated wall-clock speedups. The DAG-only diagnostic costs a small fraction of
full scoring: local junction search is the measured bottleneck. The current
implementation is slower than another ordinary decode on this benchmark, so
nominal conditional O(M) scaling does not meet the efficiency objective by
itself. No separate forced/comparative timing or superiority claim is made.

Unresolved scientific limits: restricted support coverage, no uniform
approximation ratio, no full class-gap identity, no class-summed likelihood,
no posterior calibration, no post-selection guarantee, and no original-joint-
noise likelihood interpretation. Engineering limits: float64 arithmetic,
nonlinear offline bitset setup, native performance constants, and the explicitly
narrow adapter scope. Old adapter instances are fixed snapshots; callers must
rebuild after changing models. Larger numerical studies remain user-launched.

Raw evidence: [directory](circuit_dem_y_evidence/), including test logs,
`example.json`, `cap_counts.json`, `timings.json`, the pre-dedup timing record,
wheel build/smoke logs and the pre-existing-source hash audit.
