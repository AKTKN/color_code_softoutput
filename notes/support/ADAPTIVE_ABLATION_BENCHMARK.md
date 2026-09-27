# Adaptive decoder ablation benchmark

Stage 06 adds a paired `adaptive_v2` benchmark under
`src/color_code_softoutput/simulation/adaptive_benchmark.py`. Each point samples
physical shots once and decodes the same detector batch with ordinary
concat-MWPM, adaptive color-correlated decoding, adaptive cross-color
relifting, and one fixed prior-perturbation ensemble. The requested grid is
`d={3,5}`, `p={0.005,0.01}`, the `original_dem` score basis,
`M={2,4,8,16}`, and `alpha={0.25,0.5,1.0}`. It is available through
`--ablation`, but has not been launched. The implementation smoke uses only
eight shots at the original-DEM basis and a two-shot reduced grid. Earlier
stage-2 benchmark plans predate the color-correlated decoder's requirement
for original-DEM final selection; new paired runs reject `stage2`.

Run one bounded point with:

```bash
PYTHONPATH=src:external_libs/color-code-stim/src conda run -n color_code_so \
  python -m color_code_softoutput.simulation.adaptive_benchmark \
  --shots 16 --ensemble-size 2 --alpha 0.25 --weight-basis original_dem
```

Summarize completed run directories with:

```bash
PYTHONPATH=src:external_libs/color-code-stim/src conda run -n color_code_so \
  python -m color_code_softoutput.analysis.adaptive_benchmark \
  results/adaptive_report results/adaptive_v2/<run-directory> [...]
```

The report writes basis-labelled point, class, call distribution, early-exit,
selected-member, and perturbation-saturation CSV files and the requested plot
families. Each point row contains Wilson LER limits, paired rescue/regression,
nominal and actual call counts, runtime, and selected candidate fractions.
Run-class rows condition the same measures on baseline correction multiplicity.
Class 0 has zero extra calls by the adaptive schedule; class 1 and class 2
retain their observed costs. Rescue concentration in classes 1/2 is an
empirical result to inspect, not an invariant assumed by the benchmark.

Call accounting: ordinary decoding uses six MWPM calls; each executed guided
color-correlated candidate uses a Stage-1 and Stage-2 call (maximum 24 total);
relifting uses six baseline calls plus unique additional target Stage-2 solves
(maximum 15); perturbation uses `6M` calls. Runtime is timed around each
strategy's decoder invocation, including Python control flow but excluding
circuit sampling and result serialization. Relift equality counts compare all
six pairwise projected Stage-1 hypotheses with their target baseline before
Stage-2 solving. Cache skips count same-target syndromes among scheduled
candidates, and the all-color new fraction uses three canonical anchored
slots per shot. Perturbation stage-1 diversity sums per-target distinct
hypotheses, because stage-1 column order differs by color. A duplicate member
has the same ordered triple of original-DEM final corrections as an earlier
member. Saturation tables give changes against the preceding M at fixed
distance, p, alpha, and score basis.

These are comparisons against ordinary decoding, not evidence of near-MWE or
MLD decoding. Any near-optimal claim requires an exact or strong reference in
the tested regime.
