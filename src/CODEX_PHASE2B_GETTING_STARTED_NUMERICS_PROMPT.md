# Codex Task: Phase 2B — Reproducible code-capacity numerics and reusable soft-output analysis package

We have completed Phase 2A: the fixed-color stage-2 MWPM swim-distance implementation is integrated into `color-code-stim`, independently validated on small codes, and a bounded paired pilot has passed the requested correctness gates.

The next task is **not** to modify the Phase-1 theory or redesign the Phase-2A decoder. The purpose of this task is to build a clean, reusable numerical-experiment and analysis layer, then run a moderately large "Getting Started"-style code-capacity study that:

1. reproduces the known logical-error scaling of the concatenated MWPM decoder at a coarse level;
2. records the newly implemented swim distance on the same shots;
3. records the existing comparative-decoding confidence metric on the same physical shots, which we will call `forced_gap` in this project for the present comparison;
4. provides reusable plotting/analysis classes for later paper-scale studies.

All production modules except the notebook must live under

```text
/home/quantum_teresheys/workspace/color_code_softoutput/src/color_code_softoutput
```

External repositories remain separately managed under

```text
/home/quantum_teresheys/workspace/color_code_softoutput/external_libs
```

Do not copy external package source into the main package.

The implementation language, public API names, comments, docstrings, metadata keys, and analysis labels should be English unless there is a strong compatibility reason otherwise.

---

# 0. Read the project state first

Before modifying source, read the current project and implementation state carefully.

At minimum inspect:

```text
AGENTS.md
IMPLEMENTATION_STATUS.md
PROJECT_DETAIL.md
STATUS.md
REVIEW.md
NOTATIONS.md
```

and all Phase-2A implementation notes/tests available in the repository.

Also inspect the actual current branches and commit hashes of:

```text
external_libs/PyMatching
external_libs/color-code-stim
```

The Phase-2A status reports the completed implementation commits as:

```text
PyMatching:
83cee05cc16d6fce9deafdbbf7952b4b96a7f21e

color-code-stim:
ba6f7dc8b7aaab237d98ad5f08825be4225864c6
```

Verify the actual local HEADs rather than trusting this prompt blindly.

Do not change those external libraries in this task unless a genuine blocking bug is found. If one is found, document it and stop for review before making a nontrivial decoder change.

The numerical/analysis implementation belongs in the main package.

---

# 1. Important scientific scope

## 1.1 Code and noise model

The numerical experiment is restricted to the standard triangular 6.6.6 color code under the data-only bit-flip model used for the code-capacity/perfect-measurement analysis.

Use:

```python
ColorCode(
    d=d,
    rounds=1,
    circuit_type="tri",
    cnot_schedule="tri_optimal",
    noise_model=NoiseModel(bitflip=p),
)
```

unless inspection of the current Phase-2A test implementation establishes an exactly equivalent factory that should be reused.

The experiment must use one QEC round (`T=1`) for this reproduction.

Do not silently switch to:

- circuit-level noise;
- phenomenological measurement noise;
- repeated multi-round data-noise memory;
- Union-Find;
- BP/BP-LSD;
- a different CNOT schedule.

---

## 1.2 Known issue in the original Lee et al. bit-flip result

Before coding the reproduction, inspect:

- Lee, Li, Bartlett, *Color code decoder with improved scaling for correcting circuit-level noise*, Sec. 3.1 and Fig. 3;
- the current `color-code-stim` README/history.

The published Fig. 3 used:

```text
T = 1
d = 3,5,7,...,31
near-threshold LOWESS fits with fraction 2/3
published crossing threshold ~ 8.2%
sub-threshold log-linear fits:
    log(p_fail / T) = G(d) log p + C(d)
```

The paper reports

```text
G(d) = (0.488 ± 0.006)(d - 17) + (8.53 ± 0.05)
C(d) = (1.30 ± 0.02)(d - 17) + (20.6 ± 0.2)
```

with 99% confidence intervals.

However, the current `color-code-stim` repository documents that the historical paper implementation accidentally applied bit-flip noise twice. The corrected implementation changes the expected bit-flip threshold from roughly 8.2% to roughly 8.6% and approximately halves the logical failure rate.

**Do not reintroduce the historical bug to force agreement with Fig. 3.**

For this task:

1. use the **current corrected implementation**;
2. compare the coarse reproduction against:
   - the published Fig. 3 behavior and published 8.2% crossing;
   - the current repository's documented corrected expectation near 8.6%;
3. clearly state the known reason for the systematic difference;
4. treat broad qualitative/scaling agreement as the reproduction target.

If exact reproduction of the historical 8.2% result is desired later, that should be a separate legacy-version experiment using the historical code, not a mutation of the corrected production code.

---

# 2. Experiment grid

Use only

```python
DISTANCES = [3, 5, 7, 9, 11, 13]
```

for this study.

The physical-error-rate sweep should contain approximately half as many points as the corresponding Lee et al. Fig. 3 sweeps.

Before finalizing the grid, inspect the paper and, if available, the original experiment scripts/data to recover the actual p-grid. Do not claim a guessed grid is the exact Lee grid.

Preferred rule:

1. recover the original near-threshold and sub-threshold grids;
2. retain approximately every second point;
3. preserve both endpoints;
4. preserve enough points around the crossing to estimate it;
5. record both the original and reduced grids in metadata.

If the exact source grid cannot be recovered, use the following explicit fallback and label it as a project approximation:

```python
NEAR_THRESHOLD_P = [0.076, 0.080, 0.084, 0.088]
SUBTHRESHOLD_P = [0.02, 0.03, 0.04, 0.05]
```

These fallback values are motivated by the ranges visible in Fig. 3, not asserted to be the exact original sampling grid.

Deduplicate any point if the two grids ever overlap.

---

# 3. Shot count

This is a relatively large validation run, but not yet the final paper-scale campaign.

Implement a configurable fixed shot count per `(d, p)` point.

Recommended default:

```python
shots_per_point = 100_000
```

but expose it as a configuration/CLI argument.

Also provide a `--smoke` or equivalent mode with a much smaller shot count for test execution.

Do not implement an adaptive Wilson-error stopping rule in this task unless it is trivial to add cleanly. The main objective is a simple reproducible fixed-shot study.

The metadata must record the exact shot count for every parameter point.

---

# 4. Paired confidence metrics on the same physical shots

Every physical shot must be sampled only once per `(d,p)` configuration and then used for both confidence pipelines.

Compute:

## 4.1 Swim distance

Run the ordinary concatenated MWPM decoder with the Phase-2A swim integration.

Keep and store:

```text
phi_r
phi_g
phi_b
best_color
selected_swim_distance
```

For this study define

```text
selected_swim_distance
    = phi of the color instance selected by the ordinary hard decoder
```

Do **not** use

```text
min(phi_r, phi_g, phi_b)
```

in the main analysis.

That alternative aggregation strategy is future work.

The selected-color strategy must be tested explicitly so that accidental `min` aggregation cannot occur.

## 4.2 "Forced gap" for this study

The second confidence metric is the existing `color-code-stim` comparative-decoding logical gap.

For the present numerical comparison, expose/store this value under the dataset column name:

```text
forced_gap
```

but metadata and documentation must state explicitly:

```text
forced_gap_source =
"existing color-code-stim comparative-decoding logical gap"
```

Do not pretend this is a newly implemented generic forced-decoding algorithm if the implementation is actually the existing comparative-decoding gap.

Retain the original semantic name internally if that reduces confusion, and provide the `forced_gap` analysis alias at the experiment layer.

## 4.3 Failure labels

The ordinary swim decoder and the comparative decoder can make different hard decisions.

Therefore store both:

```text
ordinary_prediction
ordinary_logical_error

comparative_prediction
comparative_logical_error
```

For confidence analysis:

```text
swim distance -> ordinary_logical_error
forced_gap    -> comparative_logical_error
```

by default.

Never use the forced-gap metric with the ordinary-decoder failure label, or vice versa, unless a plotting API explicitly requests that nonstandard comparison.

Reuse the paired-input mapping already validated in Phase 2A. Do not independently resample physical shots for comparative decoding.

---

# 5. Main package architecture

Implement reusable modules under:

```text
src/color_code_softoutput/
```

A recommended structure is:

```text
src/color_code_softoutput/
├── __init__.py
├── experiments/
│   ├── __init__.py
│   └── phase_2a_test.py
├── simulation/
│   ├── __init__.py
│   ├── config.py
│   ├── parallel_runner.py
│   ├── sampling.py
│   └── storage.py
└── analysis/
    ├── __init__.py
    ├── dataset.py
    ├── figure_style.py
    ├── prior_work.py
    ├── swim_distribution.py
    ├── conditional_ler.py
    └── postselection.py
```

This exact decomposition is not mandatory if the existing project structure suggests a cleaner layout, but preserve the separation of concerns:

```text
experiment definition
simulation/scheduling
storage/reproducibility
dataset loading/validation
metric analysis
figure styling
```

Do not put numerical analysis logic into the notebook.

Do not put plotting logic into the simulation runner.

Do not put color-code decoder internals into the analysis package.

---

# 6. Engineering style requirements

Use conservative, readable software-engineering practices similar to Google's general engineering principles:

- small modules with a single clear responsibility;
- explicit data ownership;
- typed public interfaces;
- dataclasses for configuration/results where useful;
- dependency injection instead of hidden global state;
- no magic row/column indices;
- no duplicated experiment constants across modules;
- deterministic behavior under a fixed seed;
- clear failure modes instead of silent fallback;
- narrow public API;
- tests close to behavior;
- comments explain **why**, not obvious syntax;
- optimize only after the correct behavior is established.

Use modern Python type hints.

Every public class/function must have a complete English docstring including, where relevant:

```text
purpose
Args
Returns
Raises
Notes
valid option values
units
array/dataframe shapes
scientific interpretation
```

Use names that distinguish:

```text
physical error rate
logical error
swim distance
comparative/forced gap
abort rate
retained/residual LER
```

Do not use ambiguous names such as `gap`, `err`, or `data` in public APIs without qualification.

---

# 7. Experiment configuration objects

Implement a typed configuration layer.

For example:

```python
@dataclass(frozen=True)
class Phase2ATestConfig:
    distances: tuple[int, ...]
    near_threshold_ps: tuple[float, ...]
    subthreshold_ps: tuple[float, ...]
    shots_per_point: int
    batch_size: int
    num_workers: int
    master_seed: int
    output_root: Path
    verbose: bool
```

The code/noise setup itself should remain fixed for this experiment:

```text
6.6.6 triangular color code
T=1
tri_optimal
bitflip-only data noise
ordinary concatenated MWPM + swim
paired comparative decoder
```

Do not expose a dozen architecture-changing CLI flags in `phase_2a_test.py`.

Infrastructure parameters such as:

```text
shots
workers
batch size
seed
output root
verbose
smoke
```

should be configurable.

---

# 8. `phase_2a_test.py`

Implement the fixed experiment entry point as:

```text
src/color_code_softoutput/experiments/phase_2a_test.py
```

It must be usable both:

```bash
python -m color_code_softoutput.experiments.phase_2a_test ...
```

and from a notebook/imported Python session.

Responsibilities:

1. create the fixed Lee-style experiment grid;
2. create the reproducible run directory;
3. dispatch batches to the parallel runner;
4. collect/save paired per-shot results;
5. write aggregate summaries and metadata;
6. optionally invoke the standard reproduction analysis after sampling;
7. return a structured run/result object rather than only printing.

Do not embed detailed plotting implementations here.

---

# 9. Output directory and data format

By default, write experiments under a project-level results directory such as:

```text
/home/quantum_teresheys/workspace/color_code_softoutput/results
```

unless an existing repository convention already defines another results root.

Each run directory must be named:

```text
YYYYMMDD_HHMMSS_phase2a_test
```

using a timezone-aware timestamp.

Example:

```text
20260912_154210_phase2a_test/
```

Recommended contents:

```text
20260912_154210_phase2a_test/
├── metadata.json
├── resolved_config.json
├── summary.parquet
├── fit_results.parquet
├── postselection.parquet
├── shots/
│   ├── part-000000.parquet
│   ├── part-000001.parquet
│   └── ...
├── figures/
│   ├── ...
│   └── ...
└── logs/
    └── run.log
```

A partitioned Parquet dataset is acceptable and preferable to holding millions of rows in memory.

Use `pyarrow`/Parquet explicitly.

Do not use pickle for scientific result storage.

---

# 10. Per-shot schema

At minimum store the following columns for every shot:

```text
experiment_id
config_id
batch_id
shot_index
batch_seed

distance
physical_error_rate

actual_observable

ordinary_prediction
ordinary_logical_error
ordinary_selected_color

stage2_weight_r
stage2_weight_g
stage2_weight_b

swim_distance_r
swim_distance_g
swim_distance_b
selected_swim_distance

comparative_prediction
comparative_logical_error
forced_gap
```

If the existing comparative decoder returns useful associated weights/classes, retain them in additional clearly named fields.

Use compact dtypes where safe.

Do not drop the per-color swim values merely because the current plots use only the selected color.

---

# 11. Reproducibility metadata

`metadata.json` must contain enough information to reproduce the run later.

At minimum include:

```text
run timestamp
timezone
experiment name
exact CLI/config values
master seed
batch seed derivation rule
all batch seeds or a deterministic recipe
distance list
p lists
shot counts
batch size
num workers
noise model definition
T/rounds
CNOT schedule
decoder mode
selected-swim aggregation rule
forced-gap semantic definition

main repository git SHA
main repository dirty status
PyMatching git SHA
PyMatching dirty status
color-code-stim git SHA
color-code-stim dirty status

Python version
OS/platform
CPU information when available
dependency versions / pip freeze hash or full list

source script hashes
analysis module version/hash
known theory limitations
known 8.2% versus corrected ~8.6% historical note
```

If a repository is dirty, record the diff status clearly.

Do not silently run a "reference reproduction" from an unrecorded dirty source tree.

---

# 12. Parallel simulation module

Implement a reusable simple CPU pool scheduler inspired by the execution style of `sinter`, but do not attempt to reimplement all of Sinter.

File:

```text
src/color_code_softoutput/simulation/parallel_runner.py
```

The notebook/user must be able to specify:

```python
num_workers=...
```

## Required behavior

Split each `(d,p)` configuration into moderate-size shot batches, e.g. configurable:

```python
batch_size = 5_000 or 10_000
```

Use a process pool with bounded in-flight jobs.

Desired scheduling behavior:

```text
submit an initial pool of batches
when a CPU/worker finishes one batch:
    collect/save it
    immediately submit the next pending batch
continue until all batches finish
```

A `concurrent.futures.ProcessPoolExecutor` implementation is acceptable.

Do not submit every future for a huge paper-scale run at once.

Keep the number of pending jobs bounded, e.g. on the order of:

```text
2 * num_workers
```

or another documented small factor.

## Deterministic seeds

Derive every batch seed deterministically from:

```text
master_seed
config_id
batch_id
```

using a robust seed-sequence mechanism such as NumPy `SeedSequence`.

Parallel execution and serial execution should generate the same set of deterministic batch seeds.

The exact row order does not need to be identical if the dataset has stable `config_id/batch_id/shot_index`.

## Data transfer

Avoid accumulating the complete run in RAM.

Preferred pattern:

1. worker returns one moderate batch result;
2. parent validates it;
3. parent writes a Parquet shard atomically;
4. memory is released.

If worker-side writing is used instead, ensure collision-free deterministic file names and parent-side validation.

## Verbose progress

Implement:

```python
verbose=True
```

with real-time coarse progress information such as:

```text
completed shots / total shots
completed batches / total batches
per-configuration progress
elapsed time
recent throughput
estimated time remaining
active workers
```

Update at batch completion, not per shot.

Do not flood stdout.

Use logging internally so notebook and CLI output can share the same implementation.

---

# 13. Resume / failure behavior

Because this run may contain millions of shots, implement a simple conservative resume mechanism if it can be done cleanly.

Recommended:

- each batch has deterministic identity;
- completed Parquet shards are discoverable;
- restart skips only shards whose metadata/config hash matches exactly;
- mismatched config hashes cause a hard error.

If robust resume would substantially expand this task, implement atomic shard writing first and leave resume as a documented follow-up. Do not implement a fragile partial-resume mechanism.

---

# 14. Prior-work reproduction analysis

Implement:

```text
src/color_code_softoutput/analysis/prior_work.py
```

with a reusable class such as:

```python
class LeeFig3ReproductionAnalyzer:
    ...
```

The name may vary, but the object should make the source comparison explicit.

## 14.1 Near-threshold plot

Plot logical failure rate versus physical error rate for:

```text
d = 3,5,7,9,11,13
```

Use the reduced near-threshold p-grid.

Use the ordinary concatenated decoder's hard decision for the logical-error rate.

Reproduce the paper's basic fitting convention as far as possible:

```text
LOWESS fraction = 2/3
```

Estimate a coarse crossing threshold.

If the paper does not uniquely specify the numerical crossing-extraction algorithm, do not pretend it does.

Instead:

1. document the exact project estimator;
2. choose a stable method such as evaluating LOWESS curves on a dense common p-grid and minimizing their cross-distance/variance, or a well-defined median pairwise crossing;
3. verify it on synthetic curves;
4. label the output as the project reproduction estimate.

Compare the result against:

```text
published: ~0.082
current corrected package expectation: ~0.086
```

and state the known bit-flip implementation correction.

This task is not considered failed merely because the current corrected code does not reproduce 0.082.

## 14.2 Sub-threshold scaling

For each distance, fit the Lee et al. form:

\[
\log p_{\mathrm{fail}}
=
G(d)\log p + C(d)
\]

since `T=1`.

Use only sub-threshold p points intended for this fit.

Handle zero observed failures explicitly.

Do not take `log(0)`.

For the coarse validation run, acceptable strategies include:

- excluding zero-failure points from the log-linear fit while reporting them;
- or using a statistically justified censored/upper-bound treatment.

Do not add an arbitrary epsilon and hide it.

Return fit tables containing:

```text
distance
G
C
standard errors
confidence intervals
points used
points excluded
```

Then regress `G(d)` and `C(d)` versus `d`.

Compare the trends against the published values:

```text
slope of G(d) vs d ~ 0.488
slope of C(d) vs d ~ 1.30
```

with the explicit warning that this run stops at `d=13`, uses fewer p points, and uses a fixed moderate shot count.

Generate a compact reproduction report in Markdown under the run directory.

---

# 15. Analysis package core

Implement a dataset object, for example:

```python
class Phase2ADataset:
    ...
```

Responsibilities:

- open one run directory;
- load metadata;
- lazily/read selected Parquet columns;
- validate schema;
- filter by distance / p / metric;
- expose unique available values;
- keep metric/failure semantics paired correctly.

Do not make every plotting class parse raw files independently.

---

# 16. Common parameter-selection API for plots

For the three main swim-analysis plot types, support the following usage pattern.

The caller can specify:

```python
distance=7
physical_error_rate=[0.02, 0.03, 0.04, 0.05]
```

or

```python
distance=[3, 5, 7, 9, 11, 13]
physical_error_rate=0.04
```

Exactly one of the two should normally be a sequence and the other scalar.

If both are sequences, raise a clear error unless an explicit advanced mode is implemented.

If both are scalar, produce one series.

The varying parameter defines the legend/color series.

This API should be shared rather than reimplemented differently in every plotting class.

---

# 17. Figure style module

Implement:

```text
src/color_code_softoutput/analysis/figure_style.py
```

All analysis figures created in this package must use this style module.

Do not scatter `plt.rcParams.update(...)` across analysis files.

## 17.1 TeX/rsmf setup

Use `rsmf` with:

```python
r"\documentclass[a4paper,reprint,unpublished]{revtex4-2}"
```

The target manuscript base size is 10 pt.

Create a reusable style/context API, e.g.:

```python
class RevtexFigureStyle:
    ...

with style.context():
    ...
```

Avoid permanently mutating global rcParams outside an explicit context if practical.

## 17.2 Point-unit consistency

Matplotlib points are PostScript points (`1/72 in`), whereas TeX points are approximately `1/72.27 in`.

Implement and document the conversion needed for equal physical point sizes:

\[
\mathrm{mpl\_pt}
=
\mathrm{tex\_pt}rac{72}{72.27}.
\]

Use a named helper such as:

```python
tex_pt_to_mpl_pt(...)
```

and unit-test it.

Centralize other physical style quantities as well:

```text
line widths
marker sizes
tick sizes
figure widths
column widths
padding
```

Use `rsmf` for LaTeX-aware figure dimensions/column sizing.

Do not manually tune each figure independently unless a plotting method intentionally overrides a documented style parameter.

## 17.3 Base rcParams

The default publication style should reproduce the intent of:

```python
plt.rcParams.update({
    "axes.labelsize": "large",
    "axes.titlesize": "large",
    "xtick.labelsize": "large",
    "ytick.labelsize": "large",
    "legend.fontsize": "large",
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "axes.linewidth": 1.0,
    "text.usetex": True,
    "font.family": "serif",
})
```

but implement it through the centralized style object and TeX-aware size conversion.

Provide an explicit non-TeX/headless test style for CI only. Publication figures should fail with a useful message if required LaTeX/rsmf dependencies are unavailable rather than silently changing typography.

## 17.4 Palettes

Use Matplotlib `tab20c` as the source.

For swim-distance series, use a **green-dominant sequential palette**, derived from the green group of `tab20c`.

For forced-gap series, use a **blue-dominant sequential palette**, derived from the blue group of `tab20c`.

Centralize palette selection in `figure_style.py`.

Do not hard-code RGB/hex colors independently in plotting modules.

The palette API must support interpolation/reuse for more series than the base four tab20c shades.

---

# 18. Swim-distance distribution plot

Implement a class such as:

```python
class SwimDistanceDistributionPlotter:
    ...
```

Required main method conceptually:

```python
plot(
    dataset,
    *,
    distance: int | Sequence[int],
    physical_error_rate: float | Sequence[float],
    signed_logical_errors: bool = False,
    normalize_frequency: bool = False,
    bins: ... = "auto",
    ...
)
```

## Behavior

Horizontal axis:

```text
selected swim distance phi
```

Vertical axis:

```text
frequency
```

Use scatter-style frequency points rather than a filled histogram.

Color distinguishes the varying parameter (`d` or `p`).

Marker distinguishes logical outcome:

```text
ordinary success: circle
ordinary logical error: x
```

When:

```python
signed_logical_errors=True
```

transform only logical-error shots as:

\[
\phi_{\mathrm{plot}}=-\phi.
\]

Successful shots remain at positive `phi`.

The underlying stored data must never be mutated.

If swim values are effectively discrete in a selected dataset, group exact/near-exact values robustly.

If many unique floating values occur, use configurable bins and plot bin centers against counts.

Document the behavior.

---

# 19. Conditional logical error rate versus swim distance

Implement a class such as:

```python
class ConditionalLERAnalyzer:
    ...
```

Required plot:

```text
x: selected swim distance phi
y: P(logical error | phi)
```

Use the ordinary-decoder failure label.

Support the same scalar/list selection API for `d` and `p`.

For empirical points:

- bin/group phi;
- report number of shots and number of failures per bin;
- use statistically meaningful binomial confidence intervals (Wilson is acceptable);
- do not plot unstable empty bins as finite estimates.

---

# 20. Log-odds regression

For every plotted legend/series, fit:

\[
k\phi+l
=
\ln
rac{P(	ext{not logical error}\mid\phi)}
     {P(	ext{logical error}\mid\phi)}.
\]

The preferred implementation is a shot-level binomial logistic regression with:

```text
success = 1 - logical_error
```

so that

\[
\operatorname{logit}P(	ext{success}\mid\phi)
=
k\phi+l.
\]

Use `statsmodels` or another well-established statistical implementation.

Do not fit the log of empirical zero/one bin probabilities directly.

Return/store:

```text
varying parameter value
k
l
standard errors
confidence intervals
number of shots
number of failures
fit status
```

If a series has zero failures or perfect separation, return an explicit failed/degenerate fit status rather than fabricating finite coefficients.

## Regression plots

Create separate reusable plots for the fit parameters.

At minimum support:

```text
k versus varying parameter
l versus varying parameter
```

For example, if distance varies:

```text
x = d
y = fitted k
```

and separately:

```text
x = d
y = fitted l
```

with error bars when available.

Keeping `k` and `l` in separate figures is preferred because their units/scales differ.

Also allow the fitted logistic curve to be overlaid on the conditional-LER plot.

Save the fit table to Parquet.

---

# 21. Post-selection analysis

Implement a class such as:

```python
class PostSelectionAnalyzer:
    ...
```

For swim distance:

1. sort/threshold from low confidence upward;
2. abort shots with the smallest `selected_swim_distance`;
3. compute:
   ```text
   abort rate
   retained shot count
   retained logical failures
   residual logical error rate
   confidence interval
   ```

Plot:

```text
x = abort rate
y = residual logical error rate after abort
```

Support the same scalar/list selection API for `d` and `p`.

The curve should include the no-abort point when possible.

Handle the near-100%-abort region safely; never divide by zero when zero shots remain.

---

# 22. Forced-gap comparison on the post-selection plot

Add an option such as:

```python
include_forced_gap=True
```

When enabled, add the comparative-decoding/`forced_gap` post-selection curve.

Use:

```text
swim curve:
    selected_swim_distance
    ordinary_logical_error
    green palette

forced-gap curve:
    forced_gap
    comparative_logical_error
    blue palette
```

For both metrics, abort the lowest-confidence shots first.

At matched abort/retention rates, interpolation/resampling may be used only for visual comparison; retain the exact empirical points in the saved analysis table.

Do not silently replace one decoder's failure labels with the other's.

Save the post-selection table to Parquet.

---

# 23. Analysis outputs

For a standard analysis call, save figures in at least:

```text
PDF
PNG
```

PDF is the publication-oriented output.

PNG is for quick inspection.

Use deterministic descriptive filenames containing the fixed/varying parameters.

Examples:

```text
swim_distribution_p0.04_vary_d.pdf
conditional_ler_p0.04_vary_d.pdf
logit_k_p0.04_vary_d.pdf
logit_l_p0.04_vary_d.pdf
postselection_p0.04_vary_d.pdf
```

Do not encode huge floating precision into filenames.

---

# 24. Notebook

Create a thin notebook outside `src`, for example:

```text
notebooks/phase2a_getting_started.ipynb
```

The notebook should contain orchestration and examples only.

Suggested flow:

1. import package;
2. inspect/restate the fixed Phase-2A test config;
3. choose:
   ```text
   shots_per_point
   num_workers
   batch_size
   master_seed
   verbose
   ```
4. run `phase_2a_test` or point to an existing run folder;
5. load the run with the dataset class;
6. show prior-work threshold/scaling reproduction;
7. plot swim distribution:
   - vary `d` at fixed `p`;
   - vary `p` at fixed `d`;
8. plot signed-error swim distribution;
9. plot conditional LER and logistic fit;
10. plot fitted `k` and `l`;
11. plot post-selection;
12. add forced-gap comparison.

Do not define analysis classes/functions inside notebook cells.

A user should be able to change only a few parameters and rerun the workflow.

---

# 25. Tests

Add a proper test suite for the new main package.

At minimum test the following.

## 25.1 Configuration

- invalid even distance rejected;
- `d > 13` rejected by the fixed Phase-2A reproduction config unless an explicit generic config is used;
- invalid p rejected;
- deterministic config IDs.

## 25.2 Seed determinism

- same master seed/config/batch -> same batch seed;
- different batch IDs -> different batch seeds;
- serial/parallel seed sets identical.

## 25.3 Paired sampling

On a small fixture:

- physical shots are sampled once;
- ordinary and comparative inputs correspond to the same shot IDs;
- output row count equals sampled shot count.

## 25.4 Selected swim definition

Construct a fixture where:

```text
best color != argmin(phi_r, phi_g, phi_b)
```

and verify:

```text
selected_swim_distance == phi[best_color]
```

not `min(phi)`.

## 25.5 Forced-gap mapping

Verify:

```text
stored forced_gap == existing comparative logical gap
```

for a deterministic small fixture.

## 25.6 Parquet schema

Round-trip one small dataset and verify:

- dtypes;
- required columns;
- metadata linkage;
- no loss of boolean failure labels.

## 25.7 Parallel runner

Compare a small serial and multi-worker run using deterministic batch seeds.

Sort by:

```text
config_id, batch_id, shot_index
```

and verify equivalent results where the underlying external samplers permit deterministic reproduction.

At minimum verify deterministic seed schedule and total statistics.

## 25.8 Figure-style conversion

Test:

\[
10	imes 72/72.27
\]

against the style helper.

Test palette lengths and stable color ordering.

## 25.9 Plot-selection validation

- scalar/list accepted;
- list/scalar accepted;
- scalar/scalar accepted;
- list/list rejected by default.

## 25.10 Distribution signed mode

Verify only logical-error rows receive negative plotted phi.

## 25.11 Conditional LER

Use synthetic data with known counts and verify binomial estimates.

## 25.12 Logistic fit

Use synthetic data generated from a known logistic model and verify fitted coefficients within statistical tolerance.

Test perfect-separation handling.

## 25.13 Post-selection

Use a tiny hand-constructed dataset and verify every abort-rate/residual-LER point exactly.

Verify metric-specific failure labels for swim versus forced gap.

## 25.14 Prior-work fits

Use synthetic curves to test:

- LOWESS/crossing estimator;
- Eq. (4) log-linear fit;
- zero-failure handling.

---

# 26. Dependencies and packaging

Inspect the main project's existing `pyproject.toml`.

Add only necessary direct dependencies.

Expected candidates include:

```text
numpy
pandas
pyarrow
matplotlib
statsmodels
rsmf
```

and whatever existing scientific dependencies are already present.

Do not duplicate external PyMatching or color-code-stim as vendored code.

If the main package already manages them as editable/local development dependencies, preserve the existing convention.

Document LaTeX/rsmf system requirements separately from Python dependencies.

---

# 27. Performance and memory requirements

This experiment may create millions of rows.

Therefore:

- never accumulate the full shot table from all configurations in RAM during simulation;
- write batch shards incrementally;
- use column projection/filtering when analysis needs only a few columns;
- avoid Python loops over individual shots in analysis where vectorization/grouping is straightforward;
- keep worker payloads reasonably sized.

The analysis package should work on the planned run on a typical workstation without requiring cluster-scale RAM.

---

# 28. Statistical conventions

Use explicit, centralized statistical conventions.

Recommended default:

```text
confidence level: 99% for prior-work reproduction
Wilson interval for empirical binomial rates
```

because the Lee et al. figure uses 99% CIs.

For exploratory conditional-LER/post-selection plots, the same 99% default is preferable for consistency, but expose it as an analysis option.

Do not hide the number of samples/failures behind only error bars.

Analysis result tables must store counts.

---

# 29. Review of the Lee Fig. 3 reproduction

At the end of the first full run, write a concise report in the run directory:

```text
PRIOR_WORK_REPRODUCTION.md
```

It should state:

- exact sampled `d` and `p` grids;
- shots per point;
- current implementation commits;
- estimated coarse threshold;
- comparison to published 8.2%;
- comparison to corrected-current-code expectation near 8.6%;
- fitted subthreshold `G(d)` and `C(d)` trends;
- comparison to published slopes;
- where statistics are too weak;
- whether any discrepancy appears larger than expected from:
  - reduced d range;
  - reduced p grid;
  - fixed shot count;
  - known historical noise-model correction.

Do not claim exact reproduction if the data only show qualitative agreement.

---

# 30. Final implementation review

Before running the full 100k-shot grid, perform a smoke run and review.

Then, after the moderate run completes:

1. validate all Parquet shards;
2. verify row counts exactly;
3. recompute aggregate failure counts independently from raw data;
4. verify selected swim values from per-color fields;
5. verify forced gap against stored comparative output;
6. verify no NaN/inf values unexpectedly entered swim/forced metrics;
7. verify metadata commit hashes;
8. rerun a small sample with the same seed and compare;
9. inspect representative figures;
10. run the complete new test suite.

If any invariant fails, stop and repair before using the plots scientifically.

---

# 31. Out of scope

Do not implement in this task:

- circuit-level swim topology;
- temporal boundary aggregation;
- Union-Find swim distance;
- min-over-three-colors swim aggregation;
- BP/BP-LSD soft output;
- paper-scale HPC scheduling;
- adaptive shot stopping;
- full posterior calibration;
- new theoretical claims connecting selected-color phi to a full-decoder gap.

The current selected-color swim score is an empirical Phase-2 analysis quantity built from the proved per-color Phase-1 metric.

---

# 32. Deliverables

At completion, provide:

## Source

All reusable source under:

```text
/home/quantum_teresheys/workspace/color_code_softoutput/src/color_code_softoutput
```

including:

- experiment config/runner;
- parallel batch scheduler;
- Parquet storage layer;
- dataset loader;
- prior-work reproduction analyzer;
- swim distribution analyzer;
- conditional LER/logistic analyzer;
- post-selection analyzer;
- `figure_style.py`.

## Notebook

```text
notebooks/phase2a_getting_started.ipynb
```

with thin orchestration only.

## Tests

A dedicated test suite for the new package.

## Moderate numerical run

One completed timestamped:

```text
YYYYMMDD_HHMMSS_phase2a_test/
```

run using the agreed reduced Lee-style grid and the configured moderate shot count, unless runtime estimation from the smoke test shows this would be unreasonable on the current machine. If it is unreasonable, report the measured throughput and stop before starting an excessively long run.

## Report

Update/create:

```text
IMPLEMENTATION_STATUS.md
```

and save:

```text
PRIOR_WORK_REPRODUCTION.md
```

inside the result directory.

The final Codex response should summarize:

- files/modules added;
- exact experiment grid;
- shots;
- worker count;
- runtime;
- output directory;
- threshold/scaling reproduction result;
- whether all tests passed;
- any unresolved discrepancy or limitation.

Do not start later Phase-2 extensions automatically.

