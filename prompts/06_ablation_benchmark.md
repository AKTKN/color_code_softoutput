# Prompt 6 — Adaptive near-optimal decoder ablation benchmark

Prerequisites:

- adaptive color-correlated decoding is stable;
- adaptive cross-color relifting is stable;
- `color_correlated_run.parquet` and `relift_run.parquet` are validated;
- prior perturbation ensemble passes tests.

## Scientific objective

Measure both decoding accuracy and the amount of additional work actually
required after adaptive pruning.

Do not compare strategies only by their nominal maximum branch counts.

## Strategies

Compare:

```text
baseline concat-MWPM

adaptive color-correlated decoding

adaptive cross-color relifting

prior perturbation
  M in {2, 4, 8, 16}
  alpha in {0.25, 0.5, 1.0}
```

Relifting has:

```text
12 canonical logical candidate slots
15 MWPM calls maximum
dynamic actual call count
```

The adaptive color-correlated decoder also has a dynamic actual call count
according to the user's current implementation.

## Required per-point metrics

1. LER + Wilson interval.
2. Paired rescue and regression rates.
3. Nominal maximum MWPM-call budget.
4. Mean actual MWPM calls per shot.
5. Median actual MWPM calls.
6. Tail actual-call quantiles.
7. Measured wall-clock runtime.
8. Candidate-selection composition.
9. Run-class distribution.

## Run-class comparison

For both:

```text
color_correlated_run
relift_run
```

use:

```text
0 = all baseline corrections equal
1 = exactly two equal
2 = all distinct
```

Plot/report the fraction of shots in each class versus:

- code distance;
- physical error rate.

For each class separately report:

- LER;
- rescue/regression;
- actual extra calls;
- selected advanced-candidate fraction.

This will show whether most low-error-regime shots terminate after baseline
decoding.

## Relifting-specific early-exit metrics

Measure:

\[
P(t_{c,\mathrm{relift}} = t_{c,\mathrm{baseline}})
\]

before Stage-2 MWPM.

Also measure:

- number of same-target duplicate Stage-2 syndromes among relift candidates;
- number of actual unique relift Stage-2 solves;
- fraction of all-color anchored slots that add a genuinely new Stage-2
  syndrome;
- fraction selected from:
  - baseline,
  - single relift,
  - all-color relift.

## Baseline multiplicity versus benefit

A key analysis should condition improvement on run class:

```text
class 0: advanced decoder should do no extra work
class 1: reduced-work regime
class 2: full difficult-shot regime
```

Test whether most rescues are concentrated in classes 1/2 and whether class 0
is effectively free.

## Perturbation-specific metrics

Measure versus `(M, alpha)`:

- unique stage-1 hypotheses;
- unique final corrections;
- duplicate-member fraction;
- selected ensemble member;
- saturation with M.

## Weight basis

When feasible evaluate both:

```text
stage2
original_dem
```

Keep basis explicit in every saved table/plot.

## Plots

At minimum:

- LER vs physical error rate;
- LER vs mean actual MWPM calls;
- LER vs measured runtime;
- run-class fractions vs distance/p;
- actual call-count distribution by strategy;
- rescue/regression by run class;
- relift Stage-2 early-exit fraction;
- selected relift candidate kind;
- perturbation performance vs M and alpha.

## Interpretation boundary

Do not call the decoder near-optimal solely from improvement over baseline.
Use that term only relative to an exact or strong near-MWE/MLD reference and
state the tested regime.

Run only a smoke experiment during implementation.
