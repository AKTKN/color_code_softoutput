# Audit of the version-3 BP experiment

Run: `results/bpmatching/26_09_29_23_27_44_9926fe3c`.
Implementation: sibling `color_code_softoutput_bp_global` worktree, branch
`codex/global-bp-predecoding-20260929`. This audit changes no production
decoder, options, saved experiment files or analysis denominator.

## Findings

The negative-log X/Z mechanism rule is active. The specified options reach
the decoder. No implementation defect was found in the checked conversion,
source mapping, syndrome/observable propagation, candidate selection or
matching minimization. Bounded counterexamples show that the resulting
posterior-derived objective itself favors the wrong logical class, even
when optimized exactly over the CSS sector. This is evidence about the
BP/projection/weighting heuristic, not a physical limitation of color codes
or an exact decoding result for the depolarizing channel.

## Saved experiment and replay

The run records version 3, `negative_log_xz_probability`, independent XOR,
and effective probability `p/(1+p)`. The `probability_cap: 0.5` field refers
to effective matching priors; the global BP posteriors are not capped.

All 36 conditions have 10,000 ordered shot indices. BP null masks agree with
`bp_converged`; ordinary runs have no null logical-error entries.
For all 36 conditions, the deterministic first calibration chunk (10 shots)
was replayed using the saved configuration and seed derivation. Every saved
metric agrees. A reconstruction of version-2 weighting differs in a
discriminating case:

- `BP_MWPM`, d=5, p=0.05, zero-based `shot_index=1`.
- Saved logical_error: True; new rule: True; old rule: False.

This checks an actual worker output, not just the runner's version label.
Only the first calibration chunks are exactly replayed: later adaptive chunk
sizes are not saved. Source paths and hashes from the audit are recorded in
`provenance.json`; the original experiment does not contain complete worker
source snapshots. Do not claim bit-for-bit replay of all 360,000 shots.

The directory suffix is a configuration hash. Equal `9926fe3c` suffixes do
not imply equal implementation versions or paired physical samples. Adaptive
chunk sizing can change sampling even at the same master seed. Ordinary
failure counts also changed between the two runs.

## Options and circuit

- `rounds=2`, `perfect_first_syndrome_extraction=True`, Z memory,
  `exclude_non_essential_pauli_detectors=False`.
- One `DEPOLARIZE1(p)` instruction on all data qubits; no extra bit-flip or
  circuit noise instruction was found. The simulator's depol configuration
  constructs the expected circuit.
- d=5: 9 X / 27 Z detectors, global H shape 36 x 57, 19 mechanisms involving
  both sectors. d=7: 18 X / 54 Z, 72 x 111, 37 mixed mechanisms.
  d=9: 30 X / 90 Z, 120 x 183, 61 mixed mechanisms.
- `bp_method=min_sum`, `max_iter=20`, `schedule=parallel` reach LDPC.
  Direct LDPC outputs and LLRs agree on every traced failure.
- Native perturbation is M=4, alpha=0.6, resolved seed 20260929 and
  `use_original_prior_for_stage2=True`. Here “original” means the unperturbed
  base of the shot-local posterior DEM; it does not restore pre-BP physical
  priors. Its version-2 perturbation law is separate from global-BP version 3.

## Controlled same-input results

Reuse the previous audit's archived physical inputs; no campaign was run.
The first set contains all 57 single-Pauli faults and all 1,539 weight-two
Pauli faults on distinct data qubits for d=5, p=0.03. All methods below pass
the single faults; the table shows double-fault failures.

| Decoder | Double-fault failures / 1,539 | Failures / 2,048 archived sampled shots at p=0.05 |
|---|---:|---:|
| Ordinary concatenated MWPM | 0 | 15 |
| Previous BP min_sum weighting | 23 | 25 |
| Current BP min_sum weighting | 21 | 24 |
| Current BP min_sum, diagnostic sum aggregation | 23 | 22 |
| BP min_sum early return + ordinary fallback, diagnostic | 0 | 15 |

For the 2,048-shot sample the new rule changes seven min_sum predictions:
four failures are rescued, three previously correct shots fail. Convergence
flags do not change. Thus the implementation does affect decoding, but the
net change on this bounded sample is small. These counts do not establish a
statistically significant performance ranking.

As a separate option check, product_sum changes double-fault failures from
12 to 9 and sampled failures from 19 to 20 under the new weighting. Six of
its nine double-fault failures are already BP-converged. The min_sum choice
matters, but changing it alone does not recover the ordinary decoder's
double-fault behavior in these examples.

## Independent failure audit

Re-injected all 57 physical single-Pauli faults into the current Stim circuit.
Their detector/observable labels agree with archived input maps. They match
the global DEM columns, and identify the expected X/Y and Z/Y contributors
to each projected CSS mechanism. The source groups preserve logical labels.

For all 21 current min_sum double-fault failures:

1. Recompute BP directly with LDPC. Corrections, convergence and LLRs agree
   with the wrapper, including full global checks.
2. Independently compute the two-source parity probability as
   `q_a*(1-q_b)+(1-q_a)*q_b`. Build the X/Z DEM directly with `p/(1+p)`.
   It agrees with the production projection and reproduces its prediction.
3. Check actual log odds equal `-log(p)` up to the documented 1e-14 effective
   prior floor. Source alignment, mapped candidate syndromes and selection
   by summed X/Z weights are consistent.
4. Solve each connected component of every stage-1 and stage-2 graph by
   enumerating its GF(2) affine solution space. All **126 stage solves**
   (21 faults x 3 colors x 2 stages) attain the minimum weight. The tolerance
   is 1e-5 for numerical matching quantization; no smaller-cost correction
   violating that tolerance was found.
5. Enumerate all syndrome-compatible corrections in the Z-detector CSS
   sector, including both logical classes, without using MWPM or the
   concatenated decoder. The **wrong logical class is strictly cheaper in
   all 21 cases**. The smallest class-cost separation is about 0.009945,
   larger than the stage-check tolerance. The other CSS sector does not
   carry this memory observable and its independent minimum adds equally
   to both classes.

Of the 21 failures, all three concatenated candidates are wrong in 15;
six include a correct candidate but select a lower-cost wrong candidate.
Replacing concatenated candidate generation with exact minimization of
this same CSS objective therefore would not repair these 21 cases.

Concrete example (physical input index 90): X faults on data IDs 0 and 24.
The actual logical bit is 1. The minimum costs of logical classes 0 and 1
are **5.97126184** and **9.17988116**. Candidate logical bits are [0,1,0],
with costs [5.97126184,9.17988116,5.97126184]. The program selects class 0
as required by its objective; the physical correction is in class 1.

This does not say that the exact physical posterior prefers the wrong
class. The calculation is exact only for the specified separable CSS
negative-log objective derived from BP approximations.

## Remaining limits

The most directly supported location of degradation is the combination of
BP posterior estimates, independent CSS aggregation and chosen weight rule.
The checks do not distinguish all contributions from loopy BP approximation,
discarded conditional correlations, or the surrogate objective. The sum-only
ablation does not fix the issue. A surface-code result does not guarantee
improvement for this concatenated construction; no physical explanation is
claimed from these implementation checks alone.

Saved BP `logical_error` still omits converged-shot failures. This known
limitation is unchanged and cannot explain an *overestimate* of BP failure
counts relative to ordinary decoding. The controlled tables above instead
use returned predictions for every shot. For the sampled min_sum run,
one of 24 failures is converged; the saved non-null failure count is 23.

## Reproduction and artifacts

Run from the original workspace with the BP worktree selected:

```bash
export PYTHONPATH="/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/src:/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/color-code-stim/src:/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/PyMatching/src"
export OPENBLAS_NUM_THREADS=1
```

Use `/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python` to run
`audit.py`, then `trace.py`, `aggregation_probe.py`, and `verify.py` in this
directory. The sum/old-rule probes are process-local diagnostics only.
`counts.json`, `calibration_replay.json`, `structure.json`,
`paired_comparison.json`, `failure_traces.json`, `trace_summary.json`,
`aggregation_probe.json`, `verification.json` and prediction arrays retain
the evidence. `verify.py` independently checks counts, masks and hashes.

This is a same-agent audit with independent numerical oracles, not external
peer review. No decoder fix, source-policy change, commit or push was made.
