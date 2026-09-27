# Color-correlated decoding: conditioning the original X/Z DEM

## Corrected candidate-generation rule

The guide for an extra target-color candidate is the set `G` of mechanisms in
the pre-decomposition X/Z DEM (`DemManager.dem_xz`) selected by one ordinary
color correction, or the Boolean union of two ordinary corrections. The
indices follow that DEM's error-mechanism order. The guide is treated as hard
evidence for candidate generation, not as a calibrated posterior.

Let `q_i` be the unmodified probability of mechanism `i`. Form a temporary
copy of the original DEM with unchanged targets, annotations and mechanism
order, but with

```text
q_i^(G) = 1 - 1e-14   if i is in G
          q_i          otherwise.
```

The value just below one keeps matching log-odds finite. For each target
color, decompose this temporary DEM again and run both stages of concatenated
MWPM with the resulting matrices and probabilities. The stage-1 solution
therefore supplies the virtual syndrome for stage 2 under the same temporary
DEM. Selected mechanisms are conditioned **simultaneously**. For a unit
multiplicity decomposed column with source set `B(a)`, its probability is

```text
p_a^(G) = (1 - product_{i in B(a)} (1 - 2 q_i^(G))) / 2.
```

The former implementation edited already decomposed stage-1/2 columns with
the maximum of several single-source conditional probabilities. That rule
does not generally equal the simultaneous conditional probability above and
does not define a single reweighted original DEM. It has been removed.

## Skip redundant guided candidates

Map the three ordinary color corrections to original X/Z DEM mechanism order
and compare those full binary correction vectors. If all three agree, run no
guided candidate and record `color_correlated_run=0`. If exactly two agree,
run only three: the two repeated-color targets each use the distinct-color
guide, while the distinct-color target uses the first repeated color in
`r,g,b` order; record 1. If all three differ, run all nine guides and record
2. The reported category is for the selected logical class in comparative
decoding. Skipped candidate slots retain `+inf` comparison weights and a
false execution mask, so they cannot win the common-prior minimum. The YAML
workflow stores the category for each shot in `color_correlated_run.parquet`.

## Candidate comparison and provenance

The three ordinary candidates and any executed extra candidates are compared
using one **unmodified** basis per decode call. The default `stage2` basis
uses the target color's original stage-2 log-odds. The optional
`color_correlated_weight_basis="original_dem"` uses the mapped correction's
log-odds in the unmodified `dem_xz`. Re-decomposition can change stage-2
column order; the decoder maps every extra correction back through original
mechanism indices and aligns it to the base stage-2 order before selection.
Temporary generation weights are recorded separately and never used to rank
the candidate set. Neither basis is a posterior logical-class likelihood.

For the standard decomposition, each stage-2 column maps to one original DEM
mechanism. The two selection bases therefore agree up to floating-point
roundoff; the significant correction here is **where the guide conditioning
occurs**, not the optional score representation.

## Validation and saved-data boundary

The color-code-stim suite passed 131 tests with two existing skips. The root
package passed 254 tests. Bounded uniform-circuit checks at `d=3, r=3` and
`d=5, r=5` produced valid corrections. The 16-shot `d=3, r=3` check had 15
nonzero-detector shots and selected an extra candidate twice. These checks
establish implementation consistency for the tested cases, not an advantage
in logical error rate or an efficiency claim. Per-shot re-decomposition adds
work relative to the former direct column updates; no campaign timing claim
has been made.

Saved runs made before the correction used the old candidate-generation
rule. Their logical-error and better-weight counts cannot be reinterpreted
as results of this corrected decoder without rerunning the shots. The
implementation is in the separate `color-code-stim` repository, commit
`7a1eff0` on `phase2a/swim-distance`; the adaptive schedule is commit
`fdf330d` on that branch.
