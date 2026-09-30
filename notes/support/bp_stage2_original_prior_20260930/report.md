# BP stage 1 with original-prior stage 2 — 2026-09-30

## Result

The user's hypothesis is supported by this bounded comparison **when both
stage-2 matching and final candidate selection use the original physical
prior**. The existing BP stage-1 solution is retained exactly. All 21 previous
d=5 double-fault failures disappear. On shared random inputs, failures change
24 -> 15 at d=5 and 30 -> 18 at d=7, matching the ordinary concatenated
decoder's counts in both samples. This does not establish improvement over
ordinary concatenated MWPM or an asymptotic threshold advantage.

Restoring only stage-2 matching while keeping BP-weighted candidate selection
gives much smaller changes. The two operations must be distinguished.

## Defined variants

All BP variants use the same global BP, min_sum, 20 iterations, parallel
schedule, convergence flags and converged-shot predictions. For a fallback
shot, posterior generation and stage 1 are the current version-3 implementation:
global posterior -> independent-XOR X/Z aggregation -> -log(p), encoded as
p/(1+p) for the existing color decomposition.

| Variant | Stage 1 | Stage 2 matching | Final selection over colors |
|---|---|---|---|
| Current | BP-derived | BP-derived | BP-derived X/Z objective |
| Stage 2 only | BP-derived | Physical prior | BP-derived X/Z objective |
| Selection only | BP-derived | BP-derived | Physical X/Z prior |
| Stage 2 and selection | BP-derived | Physical prior | Physical X/Z prior |
| Ordinary fallback | Ordinary for fallback | Physical prior | Physical prior |

“Physical prior” means the original pre-BP circuit's X/Z DEM and its normal
log-odds weights, not the unperturbed posterior DEM inside the BP wrapper.
The existing native `use_original_prior_for_stage2` option refers to that
wrapper-local base and by itself does not implement this hypothesis.

The ordinary-fallback control still returns converged BP predictions; the
ordinary baseline does not run BP at all. No perturbation ensemble is used
in this ablation. Actual observable outcomes are used only for validation,
trace selection and final statistics, never to select a correction.

## Inputs and results

All circuits are Z memory, rounds=2, perfect_first_syndrome_extraction=True,
exclude_non_essential_pauli_detectors=False, with one data depolarizing layer.
The d=5 physical and random inputs are reused from the prior audit. The d=7
sample has 4,096 shots with seed 2026093007. Every method sees identical
detector and observable arrays within each input set.

| Decoder | d=5: all 1,539 double-Pauli faults, prior p=.03 | d=5: 2,048 sampled shots, p=.05 | d=7: 4,096 sampled shots, p=.05 |
|---|---:|---:|---:|
| Ordinary concatenated MWPM | 0 | 15 | 18 |
| Current BP | 21 | 24 | 30 |
| Stage 2 only restored | 18 | 21 | 27 |
| Final selection only restored | 15 | 23 | 29 |
| **Stage 2 and final selection restored** | **0** | **15** | **18** |
| BP early return + ordinary fallback | 0 | 15 | 18 |

All 57 physical single-Pauli faults also pass in all variants. Double-fault
enumeration is exhaustive over distinct data-qubit pairs and their nine Pauli
choices, not a random sample; no sampling p-value is assigned to that set.

The main hybrid rescues 12 and worsens 3 shots relative to current BP at d=5;
at d=7 it rescues 20 and worsens 8. Relative to ordinary concatenated MWPM,
it rescues/worsens 1/1 shots at d=5 and 5/5 at d=7. Equal aggregate counts
therefore do not mean identical predictions or that stage 1 was bypassed.
Unadjusted paired-binomial diagnostic p-values against current BP are about
.0352 and .0357; these are exploratory comparisons across several variants,
not a broad performance or threshold claim.

Counts include **all** predicted outcomes, including BP-converged failures.
There is one converged failure in the d=5 random sample and none in the other
two sets. It is unchanged across variants. This avoids the existing saved
nullable-metric limitation when evaluating the hybrid pipeline.

## Implementation and independent checks

This is a diagnostic implementation in `probe.py`; production packages,
default behavior, options, branches and saved experiments were not modified.

For each fallback shot:

1. Construct the exact current posterior DEM and solve each BP-weighted
   stage-1 matching once, using the existing decoder method.
2. Identify original and posterior stage-1 columns by detector support plus
   their mapped X/Z source mechanisms. Transfer the same selected bits into
   the original graph's column order. Validate a bijection and identical H1.
3. Execute stage 2 on the original physical-prior graph, using those translated
   stage-1 bits as its virtual syndrome. Map the returned correction through
   that graph's own source map.
4. Evaluate the three color candidates under either the original physical
   X/Z weights or BP-derived X/Z weights, as specified by the variant.

An independent construction keeps the posterior graph's ordering and replaces
only its stage-2 probabilities with original values aligned by source IDs.
Full H2 matrices agree under the corresponding row/column permutations. For
**12,087 color/shot solves**, both constructions give equal minimum weights
within 1e-5 numerical tolerance and identical logical outputs. Their correction
vectors need not be identical when stabilizer-degenerate minimizers exist.
Every mapped candidate satisfies the original physical detector syndrome.

The reconstructed current-BP predictions and flags agree exactly with the
public production API on all three datasets. Archived d=5 predictions are
also reproduced. Independent artifact verification checks all counts, paired
changes, converged predictions and the new d=7 sampling seed.

For the 21 formerly failing physical patterns, all 63 restored-prior stage-2
matching solutions were also checked by independent GF(2) affine-space
enumeration. They attain the true stage-2 minimum, and original-prior final
selection returns the correct logical bit in every case.

Concrete example: X faults on data IDs 0 and 24. BP-weighted selection favors
the wrong candidate at cost 5.9713 over a correct candidate at 9.1799.
Original-prior scores instead assign 11.6755 to that wrong candidate and
7.7836 to a correct candidate. Restoring generation weights alone does not
remove the BP preference in the final comparison.

## Scope and reproduction

The evidence supports keeping BP information in stage 1 while protecting
stage 2 and final selection from this BP-derived objective, in the tested
min_sum code-capacity setting. It does not isolate why BP's estimates behave
this way, establish an all-distance result, or evaluate circuit-level noise,
product_sum or perturbation ensembles for the hybrid. It does not show an
improvement over ordinary concatenated matching in the random samples.

From the original workspace:

```bash
export PYTHONPATH="/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/src:/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/color-code-stim/src:/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/PyMatching/src"
export OPENBLAS_NUM_THREADS=1
```

Use `/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python` to run
`probe.py physical_d5`, `probe.py paired_d5`, `probe.py paired_d7`, then
`verify.py` from this report's directory. Historical d=5 NPZ inputs are required
at the previous audit's recorded location. Summaries, prediction/input arrays,
failure traces, source hashes and verification output are stored alongside
this report. No campaign, production integration, commit or push was performed.
