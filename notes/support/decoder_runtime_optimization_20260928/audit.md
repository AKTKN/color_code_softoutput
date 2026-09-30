# Runtime refactor audit — 2026-09-28

The target is `external_libs/color-code-stim`, current branch `main`, starting
at `072a87d294ed2e9388d1843a1065b41aff043ba4`. The user explicitly corrects
fixed-ensemble sampling to independent per-shot resampling. Other generation,
selection, ordering, logical-class, guide, relifting and SWIM rules are retained.

## Before implementation

- `concat_matching_decoder.py::_decode_stage1` built one weighted graph per
  invocation after filtering empty checks. Only guided color-correlated priors
  had a bounded 32-entry matching LRU. Ordinary/member-0 matchings were rebuilt.
- `_decode_stage2` contained two construction paths: cached base graphs for
  color-correlated decoding, and unconditional construction for all other
  modes/custom priors. The base stage-2 graph can be reused by every ordinary
  and original-stage-2 perturbation candidate; syndromes change, graphs do not.
- `prior_perturbation.py` sampled all nonbaseline members once in its constructor
  and stored their temporary DEMs/decompositions across every shot. This is the
  explicitly superseded behavior, not the equivalence reference.
- Perturbation always allocated mapped corrections of shape
  `(logical classes, 3M, shots, original sources)`, all native corrections and
  stage-1 hypotheses, generation weights and metadata. Ordinary/color-correlated
  decoding retained every candidate correction; guided native tensors and
  diagnostic arrays were also retained for hard output. Relifting used full
  candidate tensors to retrieve aliases, although aliases require only the
  current shot's results.
- Original-DEM correction reconstruction, candidate scoring, and the three
  original corrections used for guide schedules are algorithmically required.
  SWIM requires candidate hypotheses and corrections; validity checking requires
  selected corrections. The new implementation conservatively retains all
  corrections when these options need them. Diagnostic retention can be skipped
  for ordinary hard-output decoding.

## Installed PyMatching audit

`color_code_so` imports PyMatching `2.2.dev2` from the separate
`external_libs/PyMatching/src/pymatching` checkout, commit
`7a26e6a8ef20080e9eab7240ce33581cc3880d03`. It was left unchanged.
`matching.py::from_check_matrix` defaults to `merge_strategy='smallest-weight'`.
A probability-dependent parallel-edge winner also determines its fault IDs;
changing just the weight of an already merged edge is insufficient.

`add_edge(..., merge_strategy='replace')` is public, but this is not a bulk,
column-aware reweighting interface. `sparse_blossom/driver/user_graph.cc` marks
MWPM as requiring reconstruction after edge changes and `get_mwpm` calls
`update_mwpm`/`to_mwpm`. No verified cheap whole-vector reweighting path preserves
check-matrix merging and tie rules. The chosen implementation caches complete
weighted matching objects; it introduces no native/internal weight mutation.

Reusing an unchanged matching is supported by `decode_batch` processing multiple
syndromes on one object and by the existing guide cache. The native decoder
extracts/shatters the active blossoms and clears/recycles shot state in
`sparse_blossom/driver/mwpm_decoding.cc`. Repeated-call, chunk and pristine-output
regressions independently verify reuse for this installed fork.

## Symbolic decomposition audit

`DemDecomp.decompose_org_dem` determines symbolic source terms and target topology
from targets, detector coordinates and `remove_non_edge_like_errors`; it does
not use source probability values for its decomposition choices.
`stim_symbolic.py::_DemSymbolic.to_dem` evaluates
`(1 - prod(1 - 2 * multipliers * q[source_indices])) / 2` in source-term order.
Stage 1 retains symbolic row order. Stage 2 uses
`argsort(probabilities, kind='stable')[::-1]`, so its column order **is dynamic**.

A decoder-owned plan caches these symbolic terms and the unsorted stage-2
columns/maps. Equal-length symbolic rows are vectorized without padding or
changing their product order. Every draw evaluates probabilities and reproduces
stage-2 sorting and source-map permutation. Every new weighted matching is still
constructed by `Matching.from_check_matrix`, preserving parallel-edge merging.
Source-alignment checks are validated once for each immutable plan, while the
original-DEM reconstruction and common-prior scoring still occur per candidate.
Independent actual DEM reconstruction/decomposition tests require exact equality
of probabilities, check matrices, source maps and all decoder output values.

## Fixed-prior numerical compatibility

M=1 and alpha=0 have no stochastic priors. An additional pristine comparison
found that unnecessarily scoring them one shot at a time changes some dense
floating-point dot products by approximately 1e-15 to 1e-14 compared with the
historical batched operations. They therefore retain the original whole-batch
candidate evaluation and candidate/class order, with cached fixed matchings.
The shot cursor advances by the batch length and no random numbers are consumed.
Pristine output fixtures cover both cases, including comparative decoding;
the stochastic M>1, alpha>0 reference continues to score each shot separately.

## Cache identity and final source review

Public custom matrices/probabilities are fingerprinted by current content,
including inputs that alias base arrays. Internal symbolic plans and guide
priors use prepared structural identities; they do not hash large matrices
on each shot. A regression mutates both the weights and a sparse matrix and
compares with a fresh PyMatching construction. PyMatching may remove explicit
zero entries from that input matrix, so the test restores all sparse arrays.

The pristine fixtures are version-gated to NumPy 1.26.4, Stim 1.16.0 and
PyMatching 2.2.dev2. The independent reconstruction/decomposition oracle and
cache/random-stream tests remain executable in other supported environments.
The review and independent test oracles were performed by the same agent;
this is not an external peer review.
