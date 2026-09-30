We need to optimize the decoding runtime of the current `color-code-stim` repository:

https://github.com/AKTKN/color-code-stim.git

IMPORTANT USER CORRECTION:
Perturbations must be randomly resampled independently for EACH SHOT. They
must NOT be fixed across shots, a batch, or a decoder instance. This instruction
supersedes the fixed-ensemble assumptions in the original optimization prompt
and any earlier perturbation specification.

The highest-priority goal is to eliminate redundant PyMatching graph
construction and unnecessary full-output allocations while preserving the
corrected per-shot perturbation semantics.

This task includes ONE explicitly authorized semantic correction: changing
fixed-across-shots perturbations to per-shot resampling wherever the current
implementation still fixes them. All remaining work is a performance refactor.
Do not execute this task using the old fixed-ensemble behavior as its target.

============================================================
0. NON-NEGOTIABLE REQUIREMENT: PRESERVE THE CORRECTED DECODING LOGIC
============================================================

Except for the explicit per-shot perturbation correction above, decoded hard
decisions, candidate generation, candidate selection, weights used for
selection, tie behavior, logical gaps, comparative-decoding behavior,
color-correlated semantics, and all public outputs must remain exactly
equivalent to the current implementation.

For perturbation, exact equivalence means equivalence to a simple uncached
reference that uses the SAME per-shot random draws and otherwise retains the
current candidate generation, mapping, scoring, selection, and tie rules.
Predictions from the old fixed-ensemble implementation are not the required
reference for M>1 and alpha>0. Public field names, shapes, and meanings remain
unchanged; their per-shot values must follow the corrected draws.

Do not introduce an approximation.

Do not change:
- the order of candidate evaluation if this can affect tie-breaking,
- the definitions of candidate weights,
- the use of the original DEM versus temporary/perturbed priors,
- stage-1/stage-2 prior rules for a given sampled original-DEM perturbation,
- logical-class handling,
- color ordering r/g/b,
- perturbation member ordering,
- candidate_schedule behavior,
- error mappings between decomposed DEMs and the original DEM,
- `use_original_prior_for_stage2`,
- comparative decoding,
- swim-distance semantics,
- cross-color-relifting semantics,
- existing public API behavior, except for the required per-shot resampling.

Before modifying code, inspect the current implementation and tests carefully.

The main relevant files are expected to include:

- `src/color_code_stim/decoders/concat_matching_decoder.py`
- `src/color_code_stim/decoders/prior_perturbation.py`
- `src/color_code_stim/decoders/color_correlated_decoding.py`
- `src/color_code_stim/dem_utils/...`
- `tests/test_prior_perturbation.py`
- `tests/test_color_correlated_decoding.py`
- `tests/test_cross_color_relifting.py`

Also inspect the exact PyMatching version/fork used by this project. Do not assume an API for mutating weights exists.

============================================================
1. CURRENT PERFORMANCE PROBLEM
============================================================

At present `_decode_stage1()` and `_decode_stage2()` repeatedly do something equivalent to:

    weights = np.log((1 - p) / p)
    matching = pymatching.Matching.from_check_matrix(H, weights=weights)
    matching.decode_batch(...)

This reconstructs the PyMatching graph repeatedly even though:

- graph/check-matrix structure may be reusable when verified identical, even
  when probabilities change; audit probability-dependent decomposition and
  parallel-edge merging before assuming this;
- the ordinary decoder has six fixed matching problems:
    r stage 1
    r stage 2
    g stage 1
    g stage 2
    b stage 1
    b stage 2
- perturbation member 0 is fixed, but members m>0 have NEW priors for every
  shot; their weighted Matching objects are not generally reusable across shots;
- with `use_original_prior_for_stage2=True`, perturbation stage 2 uses fixed
  base priors and can reuse the ordinary stage-2 matchings; otherwise perturbed
  stage-2 weights are dynamic too;
- the base color-correlated stage-2 matching uses the unchanged prior;
- repeated Monte Carlo chunks unnecessarily reconstruct fixed base matchings
  and may repeat immutable preprocessing.

Recent profiling shows graph construction is a substantial fraction of runtime.
Remove redundant construction from the shot/chunk hot path. For genuinely new
per-shot perturbation weights, construction may remain necessary unless the
exact installed PyMatching API supports a safe, equivalent alternative. Do
not sacrifice per-shot randomness to meet a graph-construction target.

============================================================
2. TASK A: PRECOMPILE / CACHE MATCHING OBJECTS
============================================================

Implement a clean internal matching-cache abstraction.

The cache must distinguish at least:

- color: r/g/b
- stage: 1/2
- graph/check-matrix structure
- the exact probability/weight vector used for that matching

A matching object must only be reused when doing so is mathematically identical
to constructing

    pymatching.Matching.from_check_matrix(H, weights=np.log((1-p)/p))

with the current H and p.

Do not accidentally reuse a matching object with a different prior.

------------------------------------------------------------
2.1 Ordinary concatenated MWPM
------------------------------------------------------------

For ordinary concatenated MWPM, construct the six fixed weighted Matching
objects once per decoder instance (eagerly or lazily) and reuse them for all
subsequent `decode()` calls and all shot batches.

The hot path of repeated decoding should not call
`Matching.from_check_matrix()` again for these six fixed graphs.

Also precompute and cache structural preprocessing that currently happens every
call, where applicable, e.g.:

- stage-1 `checks_to_keep`
- filtered H
- fixed LLR vectors
- any immutable mapping/index arrays

Do not mutate shared cached objects during decoding unless PyMatching explicitly
documents that decoding mutates state in a way that makes reuse unsafe.
Check this explicitly.

------------------------------------------------------------
2.2 Prior perturbation: resample for EVERY SHOT
------------------------------------------------------------

`PriorPerturbationEnsemble` must represent per-shot sampling configuration,
not a permanent collection of perturbed probabilities/decompositions.

For every shot s, independently generate a fresh ensemble of size M:

- member 0 is the exact unperturbed baseline;
- for each member m=1,...,M-1 and original X/Z DEM mechanism i, sample
  xi[s,m,i] independently from Uniform(-1, 1);
- retain the existing perturbation formula and matching epsilon:

      q[s,m,i] = clip(q_base[i] * (1 + alpha * xi[s,m,i]), eps, 1 - eps)

- retain the existing alpha=0 special case: use an exact copy of q_base,
  without introducing clipping changes to the baseline;
- perturb the common pre-decomposition X/Z DEM, retaining original mechanism
  order, targets, observable targets, and the current decomposition policy;
- all three colors for the SAME (shot, member) use the SAME sampled original
  probability vector;
- both matching stages use the induced perturbed priors, except that
  `use_original_prior_for_stage2=True` keeps stage 2 at the original base prior;
- all comparative logical-class hypotheses for the SAME (shot, member) use
  the SAME sampled perturbation. Do not redraw for each color, matching stage,
  or logical-class hypothesis.

Do not reuse a previous shot's ensemble. Do not use one perturbation ensemble
for an entire batch. Identical detector data in different shot positions still
receive fresh independent draws. Do not key randomness to syndrome contents.
Random draws may happen to be equal; do not force them to differ.

RNG and chunk invariance:

- Initialize decoder-owned randomness once from `perturbation_seed` and
  advance it across decode calls; do not reseed at each shot or batch.
- Define sampling in shot-major, then member-major, then original-mechanism
  order, or use an equally explicit shot-indexed scheme with the same
  independence and reproducibility properties.
- Preserve candidate evaluation/member/color order even if sampling order
  differs from the evaluation loop order.
- Batch partitioning must not change the perturbations assigned to the same
  ordered stream of shots. Maintain a stream position across decode calls.
- `full_output`, cache hits/evictions, comparative-class enumeration, and
  optional diagnostics must not change the draws for the same shot.
- Empty batches consume no shot positions. Any fast path for M=1 or alpha=0
  must have documented, reproducible RNG consumption.
- With a fixed seed and the same initial RNG state/shot position, decoding is
  reproducible. Consecutive calls on the same decoder consume new shot
  positions; equal results across such calls are not a general requirement.

Cache consequences:

- Compile/cache the six fixed base matchings and immutable preprocessing.
  Member 0 should reuse these ordinary cached matchings.
- For M>1 and alpha>0, stage-1 weighted matchings are generally different for
  each (shot, member, color).
- When `use_original_prior_for_stage2=False`, stage-2 weighted matchings are
  generally different for each (shot, member, color) as well.
- When `use_original_prior_for_stage2=True`, always reuse the three base
  stage-2 matchings for all shots and all members.
- M=1 and alpha=0 can reuse exactly identical weighted graphs, provided all
  public candidate slots, candidate order, and tie behavior are preserved.
- Any cross-shot cache of dynamic weighted matchings must be bounded and keyed
  by exact graph/prior identity. Do not retain all historical shot/member
  decompositions, probability vectors, or Matching objects.
- Within a shot, reuse the same weighted graph across logical hypotheses
  whenever graph structure and weights are identical. Include any
  logical-class-dependent structural differences in the cache identity.
- Cache probability-independent decomposition/mapping/preprocessing only
  after proving equivalence to rebuilding and decomposing the temporary DEM.
  Do not assume that probability changes leave decomposition choices or
  merged-edge behavior unchanged.

There is NO lifetime bound of 6M fixed weighted matchings. For N shots in the
standard three-color/two-stage setup, there can be up to 6(M-1)N distinct
nonbaseline weighted graph requests when both stages are perturbed, or
3(M-1)N when stage 2 uses the base prior, in addition to the six base graphs.
These describe possible distinct requests, not required persistent storage;
logical-class/option-dependent structures must be audited separately.
For M=12, 72 is not a bound on distinct weighted graphs over all shots.

IMPORTANT:
Candidate SELECTION must still use the existing `CandidateEvaluator` semantics.
The temporary/perturbed prior is for candidate GENERATION. It must not
silently replace the common-prior scoring basis.

------------------------------------------------------------
2.3 Color-correlated decoding
------------------------------------------------------------

Color-correlated decoding uses guide-dependent stage-1 priors. Both these
guided priors and per-shot perturbation priors are dynamic; their generation
rules and stage-2 prior rules differ and must remain distinct.

Current semantics must be preserved:

- baseline stage-1/stage-2 graphs use the base prior;
- guided reweighting affects stage 1 only;
- guided stage 2 uses the unchanged base prior;
- final candidate selection uses the existing common prior basis.

Always reuse the three base stage-2 Matching objects.

For guided stage-1 priors:

- retain/use a bounded LRU cache of compiled weighted Matching objects keyed by
  the exact stage-1 prior (and graph identity);
- do not create an unbounded cache;
- repeated identical guide priors should reuse the same Matching object;
- precompute graph-structural data independent of the guide prior.

There is already related caching logic in
`_color_correlated_stage1_matchings`; audit it rather than blindly adding a
second independent cache.

Consolidate duplicated cache mechanisms if appropriate, but preserve all
existing behavior.

------------------------------------------------------------
2.4 IMPORTANT: inspect PyMatching before choosing implementation
------------------------------------------------------------

First inspect the exact PyMatching fork/API used by the environment.

Preferred possibilities, in order:

A. If PyMatching provides an officially supported, semantics-preserving way to
   compile graph topology once and change only edge weights cheaply, use it.

B. If it does NOT provide such an API, DO NOT invent unsafe in-place edge
   mutation.

   Instead cache the fully constructed weighted
   `pymatching.Matching` objects.

Caching fully constructed objects removes redundant construction for ordinary
base priors, perturbation member 0, original-prior stage 2, and exact repeated
dynamic priors. Newly sampled perturbation weights may still require graph
construction. Audit and report this limitation explicitly; never freeze,
quantize, or approximate sampled priors to improve cache hit rates.

Do not modify the external PyMatching repository as part of this task unless
there is absolutely no alternative. Keep this optimization inside
`color-code-stim`.

Be especially careful about duplicate/parallel graph edges: if PyMatching's
check-matrix construction may merge edges based on weights, then topology cannot
automatically be assumed independent of weights. Audit this before attempting a
"structure-only" cache.

============================================================
3. TASK B: MAKE full_output=False A REAL FAST PATH
============================================================

Currently several decoder modes construct large arrays/dictionaries even when

    full_output=False

and only the final logical prediction is returned.

Refactor the implementation so that diagnostic data are only retained when
they are actually required.

The output contract must remain:

    full_output=False
        -> return only logical prediction(s)

    full_output=True
        -> return the same public information, with values following the
           corrected per-shot perturbation semantics where applicable.

Do not change the public return type.

------------------------------------------------------------
3.1 Important distinction: computation vs retention
------------------------------------------------------------

Do NOT incorrectly remove computations that are necessary for the hard
decision.

In particular, for

    color_correlated_weight_basis == "original_dem"

and for prior perturbation using original-DEM candidate scoring, mapping a
stage-2 correction into original-DEM mechanism ordering is REQUIRED to evaluate

    correction @ original_dem_llr

and therefore is part of the decoding algorithm.

That mapping/reconstruction must remain.

However, when `full_output=False`, it usually does NOT need to be retained for
every candidate after its score and logical effect have been extracted.

This task is primarily about:
- avoiding unnecessary storage,
- avoiding diagnostic copies,
- avoiding construction of large output tensors/dictionaries,
- avoiding data that are never used by hard decoding.

Do not change the mathematical scoring procedure.

------------------------------------------------------------
3.2 Data that are generally diagnostic
------------------------------------------------------------

Audit all modes, especially perturbation and color-correlated decoding.

When `full_output=False` and no other requested option requires them, avoid
retaining data such as:

- `candidate_native_stage2_preds`
- `candidate_stage1_hypotheses`
- `candidate_original_corrections`
- complete per-candidate physical-correction tensors after their scores have
  already been consumed
- `candidate_generation_weights` if not required by selection
- diagnostic candidate labels/metadata arrays
- full selected physical correction if only the final logical observable is
  required and neither validity checking nor another option needs it

But do not assume each item is removable. Trace dependencies first.

If the hard decision can be computed in a streaming fashion, it is acceptable
to process one candidate at a time and retain only the state necessary to
reproduce exactly the current `_get_final_predictions()` result.

If implementing streaming selection:
- preserve candidate ordering;
- preserve exact tie behavior;
- preserve logical-class minima;
- preserve logical-gap semantics in comparative mode;
- use strict/equivalent comparison rules matching the existing implementation;
- add explicit tests for ties.

If preserving the full weight tensor is simpler and cheap relative to the
correction tensor, that is acceptable. Correctness is more important than
micro-optimization.

------------------------------------------------------------
3.3 Options may require additional internal data
------------------------------------------------------------

Determine minimal required data based on options including:

- `full_output`
- `check_validity`
- `compute_swim_distance`
- `return_candidate_data`
- `comparative_decoding`
- `erasure_matcher_predecoding`
- `partial_correction_by_predecoding`

Do not silently change the semantics of combinations of these flags.

If an option requires candidate corrections or stage-1 hypotheses, retain them.

A good implementation may derive internal booleans such as:

    need_selected_physical_correction
    need_all_candidate_corrections
    need_candidate_stage1
    need_native_candidates
    need_generation_weights
    need_candidate_metadata

and allocate only what is necessary.

Do not make the code unreadable merely to reduce a few allocations.

============================================================
4. DO NOT OPTIMIZE AWAY PHYSICAL CORRECTION MAPPING YET
============================================================

Do NOT make "remove physical correction reconstruction" a separate optimization
in this task.

For original-DEM common-prior scoring, physical/original-DEM candidate
corrections are algorithmically needed at least transiently.

The only requested optimization here is:

1. cache/precompile matching objects and immutable preprocessing;
2. avoid storing/returning unnecessary full-output data when
   `full_output=False`.

If you identify an obviously redundant physical-correction copy, you may remove
the copy, but not the required correction mapping/scoring operation.

============================================================
5. CACHE OWNERSHIP / LIFETIME
============================================================

Caches should belong to a `ConcatMatchingDecoder` instance or another
appropriate decoder-owned object.

They should:
- survive repeated `decode()` calls;
- survive different shot chunk sizes;
- keep fixed caches independent of shot data;
- use bounded caches for dynamic perturbation or guided priors;
- keep transient shot-specific probabilities/decompositions bounded by the
  current processing window rather than the total shots processed;
- not mutate the underlying `DemManager`;
- not modify the base DEM probabilities;
- preserve public configuration and serialization compatibility while adding
  any RNG state required for the corrected per-shot sampling behavior.

Check `ColorCode.save/load`.

If cached PyMatching objects should not be serialized, recreate them lazily
after loading rather than storing fragile implementation objects in persistent
files.

Preserve backward compatibility with old saved `ColorCode` objects.
Persist per-shot sampling configuration. If save/load resumes an active
sampling stream, preserve its RNG state or effective seed plus shot position;
rebuilding a matching cache must not reset that stream. Define and test the
initial state for legacy objects without RNG state/shot position. A legacy
fixed ensemble must not silently restore fixed-across-shots behavior.

============================================================
6. REQUIRED REGRESSION TESTS
============================================================

This optimization is only acceptable if semantic equivalence to the corrected
per-shot reference is strongly tested. First establish a simple fresh-build
per-shot reference with explicit random draws, then verify the optimized path
against it using exactly the same draws/RNG state.

Extend the existing tests rather than replacing them. Tests that explicitly
require the superseded fixed-across-shots ensemble must be updated with an
explanation of the authorized semantic correction.

At minimum test the following.

------------------------------------------------------------
6.1 full_output equivalence
------------------------------------------------------------

For every relevant decoder mode:

    hard = decoder_hard.decode(shots, full_output=False)
    hard_full, extra = decoder_full.decode(shots, full_output=True)

Here decoder_hard and decoder_full must start with identical configuration,
seed, and RNG state/shot position, or replay exactly the same sampled priors.
Do not make two successive calls on an advancing stochastic decoder and
mistake their different perturbations for a full_output regression.

assert bitwise equality:

    hard == hard_full

Test at least:

1. ordinary concat MWPM
2. perturbation M=1
3. perturbation M>1
4. perturbation with alpha=0
5. perturbation with `use_original_prior_for_stage2=False`
6. perturbation with `use_original_prior_for_stage2=True`
7. color-correlated decoding
8. comparative decoding
9. both weight bases where supported:
   - stage2
   - original_dem
10. multi-shot batches and single-shot input

Use fixed seeds and matched initial RNG state/shot position. Check that output
flags do not affect sampled priors or subsequent RNG advancement.

------------------------------------------------------------
6.2 full_output=True regression
------------------------------------------------------------

`full_output=True` must preserve all current public fields and their meanings.
For stochastic perturbation, compare values to the corrected uncached per-shot
reference under identical random draws. For unaffected modes, compare to the
current implementation as before.

For perturbation compare at least:

- prediction
- `weights`
- `error_preds`
- `baseline_predictions`
- `candidate_weights`
- `candidate_generation_weights`
- `candidate_native_stage2_preds`
- `best_candidate_indices`
- `candidate_original_corrections`
- `candidate_stage1_hypotheses`
- `logical_gaps` when comparative

For color-correlated decoding compare the corresponding existing public fields.

Do not loosen equality tolerances unnecessarily.
Boolean/integer data should be exactly equal.
Floating-point weights generated by identical operations should ideally remain
exactly equal; otherwise justify any tiny numerical difference.

------------------------------------------------------------
6.3 chunk invariance
------------------------------------------------------------

For fixed sampled detector data, use two decoders initialized with the same
seed and initial RNG state/shot position:

    decoder_all.decode(all_shots)

must equal concatenation of

    decoder_split.decode(chunk_1), decoder_split.decode(chunk_2), ...

The split decoder advances its stream across chunks. Do not compare to a
single decoder already advanced by the all-shot call. Assert equality of the
per-shot sampled priors as well as predictions. Include uneven chunks,
single-shot inputs, an empty chunk, and comparative decoding.

for both:
- `full_output=False`
- the relevant selected fields under `full_output=True`

This is important because Monte Carlo simulation processes shots in chunks.

------------------------------------------------------------
6.4 cache construction-count tests
------------------------------------------------------------

Add tests that monkeypatch or wrap

    pymatching.Matching.from_check_matrix

and count graph construction calls.

Do not measure wall time in unit tests.

Expected behavior after caches are warm:

Ordinary decoder:
- first decode may construct the six fixed graphs;
- a second decode on the same decoder instance must construct zero additional
  ordinary matchings.

Perturbation:
- member 0 and identical base weighted graphs must reuse ordinary caches;
- M=1 and alpha=0 should add no graph constructions after fixed caches warm;
- with `use_original_prior_for_stage2=True`, base stage-2 matchings must not be
  rebuilt per shot/member;
- identical dynamic graph/prior requests within an active processing window
  should reuse cached matchings where applicable; test exact repeated priors
  deliberately using controlled draws;
- NEW per-shot priors may cause NEW weighted Matching constructions. Do not
  assert zero new constructions for M>1, alpha>0;
- assert that distinct priors never reuse stale weighted matchings;
- cross-shot dynamic caches remain bounded even over many distinct draws.

There is no fixed 72-object lifetime upper bound for M=12, nor a fixed
3M+3-object lifetime bound for original-prior stage 2. Report base reuse and
dynamic constructions separately.

Color-correlated:
- base stage-2 graphs must be reused;
- repeated identical guide priors should hit the bounded stage-1 matching
  cache;
- the cache must remain bounded.

Tests should verify behavior, not depend too strongly on private implementation
details.

------------------------------------------------------------
6.5 existing test suite
------------------------------------------------------------

Run the complete existing test suite.

Especially preserve:

- `tests/test_prior_perturbation.py`
- `tests/test_color_correlated_decoding.py`
- `tests/test_cross_color_relifting.py`
- swim tests
- comparative decoding tests
- persistence tests

Do not modify existing tests merely to make failures disappear. Changes are
allowed for implementation details made obsolete by the refactor or tests
that explicitly enforce the superseded fixed-ensemble sampling rule; explain
which case applies and retain independent tests of the preserved behavior.

Add per-shot sampling regressions using captured priors/controlled draws:
- consecutive shots with identical syndromes receive independent draws;
- repeated decode calls continue the random stream rather than reseeding;
- same seed and starting position reproduce the full per-shot sequence;
- different seeds with alpha>0 produce different sampled priors;
- all three colors, both stages, and comparative hypotheses share the correct
  (shot, member) original-DEM draw under the stage-2 option;
- M=1 and alpha=0 remain exact baseline behavior;
- save/load sampling-stream behavior and legacy initialization are explicit.
Do not require hard decisions to differ whenever sampled priors differ.

============================================================
7. PERFORMANCE BENCHMARK
============================================================

After correctness is established, add or run a small reproducible benchmark.

Report fixed decoder/cache initialization separately from steady-state decode
time. Dynamic per-shot sampling, required decomposition, and new weighted
Matching construction are part of steady-state decoding and must be included.

Measure separately:

A. decoder / cache construction or first-use warmup
B. first decode
C. repeated steady-state decode on the same decoder instance

Use a representative circuit-level setup:

    circuit_type = "tri"
    cnot_schedule = "tri_optimal"
    noise = uniform circuit noise
    p = 0.001
    rounds = d

At least test:
- d = 9
- d = 13
and d = 17 if runtime is reasonable.

Compare:
- ordinary / perturbation M=1
- perturbation M=12

Test multiple batch sizes if practical:
- 1 shot
- 10 shots
- ~100 shots

Report:
- total wall time
- ms/shot
- number of `Matching.from_check_matrix` constructions
- approximate peak/resident memory if easy to obtain

Do not make scientific performance claims from tiny samples.
This benchmark verifies that redundant fixed-prior graph construction has
left the hot path and measures the remaining dynamic-prior cost. Warmup cannot
precompile future random priors. Include per-shot random sampling and any
required decomposition in steady-state time; do not move them outside the
measurement to make performance appear better.

For before/after optimization comparisons, use the uncached corrected per-shot
reference and replay identical detector data and per-shot perturbations in the
optimized decoder. If also reporting the old fixed-ensemble implementation,
label it historical with different sampling semantics and do not attribute
that comparison solely to cache optimization.

============================================================
8. IMPLEMENTATION STYLE
============================================================

Keep the architecture simple.

Prefer a small internal helper/dataclass for a compiled stage matching, e.g.
conceptually:

    CompiledMatching:
        checks_to_keep
        matching
        probability/weight identity
        structural identity

or an equivalent clean design.

Avoid scattered ad-hoc dictionaries.

Avoid hashing huge sparse matrices on every shot.
Establish fixed structural identities when decoder/decomposition objects are
created, and reuse them only where graph structure is verified independent of
priors. Establish dynamic identities when each sampled prior/decomposition is
created; do not assume a member number identifies fixed weights across shots.

Probability-array cache keys may use immutable bytes/fingerprints when needed,
but avoid expensive repeated serialization if an object identity or
precomputed fingerprint is sufficient and safe.

Do not introduce global mutable caches across independent ColorCode objects.

Do not introduce threading in this task.

============================================================
9. FIRST PRODUCE AN AUDIT, THEN IMPLEMENT
============================================================

Before editing, briefly summarize:

1. every current location where
   `pymatching.Matching.from_check_matrix()` is invoked during decoding;
2. which calls use fixed priors and which use dynamic priors, explicitly
   distinguishing legacy fixed ensembles from the required per-shot rule;
3. which matching objects can safely be reused;
4. whether the installed PyMatching API supports cheap in-place reweighting;
5. which large arrays are currently allocated even when `full_output=False`;
6. which of those arrays are mathematically required versus diagnostic only;
7. where random draws currently occur, how to resample per shot while sharing
   each draw across colors/stages/logical hypotheses, and how RNG state and
   chunk invariance will be maintained;
8. how probability changes affect decomposition, graph structure, source
   alignment, and the feasibility of exact structural preprocessing reuse.

Then implement the per-shot sampling correction and refactor. Clearly separate
the authorized sampling correction from equivalence-preserving optimization.

============================================================
10. FINAL REPORT
============================================================

After implementation, report:

1. files changed;
2. cache architecture;
3. exact number/type of fixed base matchings, dynamic cache limits, and
   observed dynamic constructions/hits for:
   - ordinary decoder,
   - per-shot perturbation M,
   - per-shot perturbation M with original stage-2 prior,
   - color-correlated decoder;
   do not describe dynamic perturbation weights as 6M lifetime-fixed graphs;
4. what allocations are skipped when `full_output=False`;
5. what could NOT be removed because it is mathematically required;
6. tests added/changed;
7. complete test results;
8. benchmark before/after;
9. any remaining major runtime bottlenecks.

Most importantly, explicitly confirm with regression evidence that:
- perturbations are freshly and independently resampled for every shot;
- colors/stages/comparative hypotheses share the intended per-shot draw;
- fixed seeds and matched stream positions give chunk-invariant results;
- hard decisions and all `full_output=True` values match the uncached
  corrected per-shot reference under the same draws;
- all unaffected decoding modes retain their previous semantics.

Disclose the fixed-ensemble-to-per-shot correction explicitly. Do not claim
bitwise equivalence to legacy fixed-ensemble outputs for M>1 and alpha>0.
