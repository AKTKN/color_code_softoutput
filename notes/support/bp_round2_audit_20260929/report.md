# Two-round global-BP audit — 2026-09-29

## Result

The new run's circuit options are correct for a perfect reference extraction
followed by one depolarizing layer and a second extraction. Both X/Z detector
sectors reach BP, with joint mechanisms retained. No additional source-order,
CSS-projection, observable, or option-forwarding bug was found in the checks
below. The existing full-LER storage omission remains.

The implemented BP/fallback rule still makes logical errors on weight-two
physical Pauli patterns that ordinary concatenated matching corrects. Thus,
restoring X detectors was necessary for the intended correlation comparison,
but was not evidence that it would remove the observed accuracy degradation.
The previous circuit observation did not establish the cause of degradation.

This audit adds independent fault-insertion inputs, a bounded paired check,
and in-process diagnostic variants. Production sources, YAML, notebooks and
saved runs were not changed. No large campaign or branch publication occurred.

## Saved run and actual inputs

Run: `results/bpmatching/26_09_29_21_59_45_9926fe3c`.

Saved options include `rounds=2`, `perfect_first_syndrome_extraction=True`,
`exclude_non_essential_pauli_detectors=False`, Z memory, regular triangular
tri_optimal extraction, depol noise and original_dem candidate scoring.
BP is still parallel min_sum, max_iter=20. The installed ldpc 2.4.1 default
min-sum scaling factor is 1.0; no scaling factor was specified in this run.
The BP wrapper forwards all these saved BP parameters to ldpc.

Sources are the separate `color_code_softoutput_bp_global` worktree:
root 666ade3, color-code-stim 65ef2ad, PyMatching 0f143d6. Full commits,
package versions and source SHA256 are in `verification.json`. Decoder
source hashes match those inspected in the previous one-round audit.
The run itself has no full source snapshot, so this is a reconstruction from
saved configuration and the matching current worktree, not a hash-certified
replay of the historical process.

| d | X detectors | Z detectors | global mechanisms | mixed X/Z mechanisms |
|---|---:|---:|---:|---:|
| 5 | 9 | 27 | 57 | 19 |
| 7 | 18 | 54 | 111 | 37 |
| 9 | 30 | 90 | 183 | 61 |

Each circuit has exactly one DEPOLARIZE1 instruction acting on all data
qubits. BP's actual parity-check matrix equals the global DEM matrix,
including the X detector rows. `structure.json` records these checks.

All 36 points were read directly from Parquet (`saved_counts.json`); nullable
logical_error masks equal the saved BP convergence flags. For p=.05, saved
failure counts are:

| d | MWPM | BP_MWPM | MWPM perturbation | BP perturbation |
|---|---:|---:|---:|---:|
| 5 | 71 | 136 | 96 | 124 |
| 7 | 30 | 92 | 36 | 108 |
| 9 | 24 | 65 | 19 | 52 |

Each denominator is 10,000. BP counts exclude converged-shot failures, so
these are not full hybrid failure counts. Different aliases use independent
physical samples; these rows do not form paired improvement measurements.

## Physical fault insertion: exhaustive weight one and two at d5

At p=.03, replace the circuit's sole depolarizing layer by each deterministic
single-qubit X/Y/Z error. Stim sampling gives deterministic detector/observable
responses, independently of the package's DEM-to-matrix parser. All 57 such
responses match the global DEM columns, including logical labels. Each was
checked with three sampler shots to verify deterministic detection outcomes.

XOR these physical responses for every pair of distinct data qubits and each
of their nine Pauli combinations: C(19,2)*9 = 1,539 weight-two patterns.
No two faults on the same qubit are counted as weight two. The decoder sees
only detectors; actual observables enter scoring only.

| Method | single failures / 57 | double failures / 1539 | converged failures | fallback failures |
|---|---:|---:|---:|---:|
| Ordinary concat MWPM | 0 | 0 | — | — |
| Saved min_sum, scale 1 | 0 | 23 | 0 | 23 |
| product_sum | 0 | 12 | 6 | 6 |
| min_sum, scale .625 | 0 | 6 | 0 | 6 |

All BP variants use parallel scheduling and 20 iterations. The .625 value is
one diagnostic scaling choice, not an optimum or a recommended universal
setting. product_sum does not eliminate all failures for this corrected
circuit, unlike the earlier one-round weight-two test.

For all 1,596 inputs and each of the three BP settings, a separate direct
ldpc decoder matches the wrapper's convergence flags and all converged
logical predictions. Syndrome checks pass. Physical inputs, labels, source
IDs, predictions and convergence flags are retained in the NPZ files.
The verifier casts corrections to uint8 before sparse parity multiplication;
Boolean sparse multiplication would use Boolean arithmetic and is unsuitable
for a parity oracle. This cast fixes the diagnostic oracle, not decoder code.

## Trace of the 23 min_sum failures

`trace.py` audits every failing input:

- Global-to-CSS groups independently match physical X/Y and Z/Y source pairs.
- Projected probabilities match direct two-source XOR arithmetic.
- Fresh direct decoding of the posterior DEM exactly reproduces the wrapper.
- Every exported color candidate satisfies the original physical syndrome.
- Observable parity and minimum-score color selection match independent
  matrix calculations.

Of 23 failures, **19 have the wrong logical result in all three candidates**.
Only four contain a correct candidate. Rescoring the same candidates with
physical prior weights rescues two. Hence this cannot generally be repaired
by changing only the final color-selection rule.

Example: X on physical qubits 0 and 24 gives detectors 11,13,16 and actual
observable True. The ordinary decoder returns True; all three BP-posterior
color candidates return False. For this input, no global posterior exceeds
0.5, so global capping is inactive and cannot explain this counterexample.

Across all 23 failures, the global cap is active on 20. Removing both the
global and projected caps (retaining finite regularization and log odds)
rescues **none of these 23**. This subset-only check does not measure new
errors that uncapping might introduce elsewhere. Full per-input data are in
`failure_traces.json`; summary in `trace_summary.json`.

## Bounded paired physical sampling

One set of 2,048 Stim samples, d5, p=.05, seed 2026092922, is decoded by all
methods. All failure counts use final predictions on **every** shot, including
BP-converged shots. This is new bounded diagnostic sampling, not a replay of
saved shots or a statistically precise performance study.

| Method | total failures | converged failures | fallback failures | rescued vs ordinary | worsened vs ordinary |
|---|---:|---:|---:|---:|---:|
| Ordinary | 15 | — | — | — | — |
| min_sum, scale 1 | 25 | 1 | 24 | 5 | 15 |
| product_sum | 19 | 5 | 14 | 6 | 10 |
| min_sum, scale .625 | 17 | 1 | 16 | 3 | 5 |

The small sample supports reproducibility of the issue but does not establish
accurate LER ratios or a robust ordering of the close-performing variants.
In particular, current storage would show only 14 failures for product_sum
versus 15 for ordinary, even though its actual total is 19. The convergence
mask cannot be treated as logical success. The user's all-shot denominator
was kept; full failure labels must also be retained for valid total-LER use.

## Weight objective probe

The earlier source audit found that the official BeliefMatching implementation
uses a different edge-probability aggregation and -log(p) weights. See the
[earlier source comparison](../bp_predecoding_audit_20260929/report.md#2-本家との相違)
and [official source](https://github.com/oscarhiggott/BeliefMatching/blob/main/src/beliefmatching/belief_matching.py).

A temporary in-process probe replaces log odds by -log(p) in both matching
stages and final candidate scoring, retaining min_sum BP, the .5 cap, XOR
aggregation, and all input shots. It gives 18 weight-two failures (versus 23)
and 20 paired failures (versus 25), with all single errors corrected.
BP convergence flags are unchanged. This isolates one objective change; it
is **not** a faithful port of the surface-code algorithm, since the cap,
aggregation and concatenated graph construction remain different. It also
does not eliminate degradation against ordinary on these inputs.

## Disposition

- The new circuit options are correct and the missing-X-detector issue is
  resolved. Merely increasing rounds without perfect-first is not what this
  run did; the saved perfect-first flag is present and effective.
- No new decoder wiring bug was found in the bounded checks. These are not
  a proof of correctness for every supported mode.
- Current min_sum settings and posterior-driven candidate construction do
  cause reproducible low-weight logical failures. Supported option choices
  can materially change this behavior, but no single tested change repairs
  everything. Do not promise improvement from product_sum or scale .625.
- `use_original_prior_for_stage2=True` in BP perturbation refers to the
  posterior DEM passed into that shot's concatenated decoder; it does not
  bypass BP and restore the physical channel prior for stage 2. This is the
  existing implementation's meaning, not an option forwarding failure.
- Full total logical_error recording remains a real evaluation defect. The
  nullable concat-diagnostic schema is intentional, but the full prediction
  already returned by the decoder is discarded by the BP worker path.
- Native perturbation was inspected through saved configuration and source
  semantics; the new paired/fault tests above target ordinary BP_MWPM.
  They are not a new exhaustive validation of the native perturbation backend.

Production fixes or a new probability/weight rule were not introduced by this
audit. A complete comparison should first retain total failure outcomes, then
compare explicitly specified BP and fallback rules on the same syndromes.

## Reproduction

From the original workspace root:

```bash
export PYTHONPATH=/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/color-code-stim/src:/home/quantum_teresheys/workspace/color_code_softoutput_bp_global/external_libs/PyMatching/src
```

Using `/home/quantum_teresheys/anaconda3/envs/color_code_so/bin/python`, run
these programs in order in this directory:

1. `audit.py` — saved counts, circuit structure, physical single/double faults.
2. `trace.py` — independent projection/candidate/selection checks.
3. `paired.py` — one 2,048-shot sample with paired variants and total failures.
4. `weight_probe.py` — isolated -log(p) objective ablation on stored inputs.
5. `verify.py` — direct ldpc oracle and unchanged source hashes.

The programs write only these audit artifacts. They do not alter the saved
run, production decoder or user configuration.
