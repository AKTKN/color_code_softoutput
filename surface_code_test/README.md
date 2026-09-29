# Surface-code circuit-level soft-output workflow

This is the surface-code counterpart of the color-code circuit notebook. It
samples one physical X-memory experiment per batch and computes swim distance, complementary gap and global-subtraction path gap v1 on exactly those shots. The generic path-gap implementation lives in PyMatching; surface-specific sampling and analysis live here.

Open [notebooks/circuit_level_getting_started.ipynb](notebooks/circuit_level_getting_started.ipynb)
with the **Python (color_code_so)** kernel. It defaults to loading the latest
completed run. Set `RUN_NEW_EXPERIMENT=True` to use the editable distance,
noise, round, shot, worker, batch and seed settings. No sampling happens merely
by opening or loading the notebook.

## Run and analyze

From the workspace root:

```bash
conda run --no-capture-output -n color_code_so python -m surface_code_test.scripts.run_memory --distances 3 5 7 --p 0.001 --rounds-factor 2 --shots 2000 --batch-size 250 --workers 3 --analyze
conda run --no-capture-output -n color_code_so python -m surface_code_test.scripts.analyze_run surface_code_test/results/RUN_DIRECTORY --replay
conda run --no-capture-output -n color_code_so python -m pytest surface_code_test/tests -q
```

Both scripts also support direct execution by absolute path from any working
directory. The analysis script takes `--units natural` or `--units dB` and
`--archived-sources` to allow current source changes while still verifying the
archived source snapshot. Resume is not implemented: every sampling run gets
a new timestamped directory, and failed runs retain their completed shards.
The default 6,000-shot grid is a validation example, not a precision study.

## Circuit and decoder conventions

The physical circuit is built by the existing
[`external_libs/PyMatching/SO_example`](../external_libs/PyMatching/SO_example/readme.md):
`Rotated_surface_code`, `X_init(cleaness=False)`, `SE_round(cleaness=False)`
repeated `rounds` times, then `X_meas(cleaness=False)`. All have the common
noise parameter `p`. The default **p=.001 and rounds=2d** follow that example,
including its gate order, noisy preparation, gates, idle layer and readout.
`X_init` itself includes another noisy extraction, so `rounds` records only
the explicit `SE_round` calls, exactly as in the example's script. This is not
the color-code uniform-noise constructor or Stim's generated memory circuit.
The d=5, rounds=10, p=.001 circuit matches the saved baseline circuit exactly.

Hard decoding uses `so_sampler.construct_decoder` and its actual retained
`DEM.prune_post_selected` model. The upstream parser/merged matching graph is
an approximation to the original correlated circuit noise and can omit
unsupported composite mechanisms. We preserve that behavior and archive both
the physical circuit/DEM and the actual merged matching edges. No extra
herald filtering or physical-shot rejection is enabled.

Swim uses the current generic PyMatching `configure_soft_output` and
`decode_batch_with_soft_output` API, with the example's split upper/lower
X-boundary topology. Z-boundary half-edges are omitted from this X-logical
analysis metric as in the example. Logical consistency of the two terminals
is checked from the actual edge labels after an internal balance test. Hard
predictions and ordinary solution weights must match SO-off exactly on every
shot. This uses the established Phase-2A final-defect metric-ball convention,
not the old CSV sampler's rounded integer output. Growth remains uncertified:
**`swim_bound_certified=False`**.

Complementary gap is **`abs(W1 - W0)`**, where `Wb` is the minimum matching
weight in logical class `b` for the same ordinary graph and syndrome. A checked
spanning-forest potential gauges the internal logical labels to zero. Each
gauged logical half-edge connects to an extra constrained detector row. For
class `b`, that row's syndrome is `b XOR (potential · physical_syndrome)`.
Both forced solves retain the original edge weights and observable labels;
minimum class weight and the ordinary predicted-class weight must agree with
the ordinary solution within backend floating tolerance (atol 1e-8, rtol 1e-10).
This is the balanced-cut algebra of the existing project theory, applied to
this frozen graph. Unbalanced or absent-class inputs fail explicitly.

All three scores use the **same ordinary MWPM prediction and failure label**. No
color-code comparative decoder or physical observable bit is used to compute
the gap. The complementary gap is a minimum-representative cost difference,
not a summed logical-class likelihood ratio. Backend weight quantization can
produce tiny differences between scores even where their mathematical costs
coincide. No theorem equating the two confidence scores is asserted.

## Plots and stored data

The standard figures include:

- Swim-distance distributions, marking successful and failed shots.
- Conditional logical error rate versus swim distance, with 99% Wilson
  intervals and count tables; no fitted calibration curve is drawn.
- Paired post-selection curves for swim, complementary gap and path gap v1, with residual
  LER versus abort fraction. Every exact unique **raw** score is a threshold;
  retain scores `>= threshold`, with entire ties retained.

Raw scores are unrounded natural-log matching costs. Plot units default to
dB via `10/ln(10)`, without integer rounding. Distribution/conditional plots
reuse the existing binning utilities; post-selection does not bin, round or
subsample thresholds. Zero empirical rates and intervals remain in the saved
Parquet tables and are omitted from log-scale markers. A distance with no
observed failures is explicitly annotated; it does not demonstrate zero LER.
Rare failures at p=.001 may require substantially more samples for precision.

Each timestamped `results/` run contains atomic Parquet shot shards, summary
counts, configuration/environment/source metadata, source ZIP, frozen circuit
and graph models, an audit record, PDF/PNG plots and analysis tables. Every
new shot stores both class weights, all three scores, the ordinary prediction, actual
observable, failure label, seed and stable batch/shot identity. Audit checks
all shards and model/source hashes, reconstructs summary counts, and can
replay one exact saved batch per distance. Replays are not additional samples.

## Modules

- `model.py`: external circuit adapter, checked topology and forced-class matcher.
- `simulation.py`: configuration, deterministic task stream and paired sampling.
- `experiment.py`: shared worker/storage/provenance orchestration and full audit.
- `analysis.py`: surface dataset adapter and three shared-style plot families.
- `scripts/`: simulation CLI and saved-run analysis CLI.
- `notebooks/`: thin interactive workflow.
- `tests/`: exhaustive tiny-graph and actual integer-program gap oracles,
  independent interval metric, frozen circuit/hard regression, state reset,
  serial/parallel equality, single sampling, storage/audit and plots.

The main package's batching, seeds, atomic storage, provenance, statistics and
figure style are reused without editing the color-code implementation.
The scope is fully terminated X memory. Sliding windows, threshold estimates,
posterior calibration and large-scale paper reproduction are not included.
See [VALIDATION.md](VALIDATION.md) for the completed local validation record.

## Path-gap v1 extension (2026-09-19)

Use the ordinary `color_code_so` kernel, restarting it after the PyMatching
rebuild. The notebook's existing settings and selected saved run are preserved.
Set `RUN_NEW_EXPERIMENT=True` to sample a new run with all three metrics. Old
runs load and plot their original two scores; path gap is never fabricated
from SWIM or the complementary gap, nor added by resampling on load.

`path_gap = path_gap_residual_distance - path_gap_correction_weight`.
On the same original split-X-boundary topology as SWIM, zero exactly the
ordinary correction's edges and use Dijkstra. Subtract the original floating
weight of the **entire** correction, including its Z-check component. No
clusters/radii, absolute value, clipping, or overlap-only subtraction is used.
The negative portion of the distribution is meaningful to this definition.
Backend quantized `ordinary_solution_weight` remains separate. Version is
`global_subtraction_v1`, saved in metadata and every shot.

New runs automatically produce five PDF/PNG pairs: SWIM and path-gap
distributions, SWIM and path-gap conditional LER, and three-metric
post-selection (green SWIM, blue complementary, purple path-gap). Raw signed
thresholds preserve whole ties. Use `plot_distribution(dataset,
metric="path_gap")` and `plot_conditional_ler(dataset, metric="path_gap")`
for the new figures; `plot_postselection(dataset)` includes path gap when
present. All metrics use the same sample and ordinary failure label.

See [PyMatching API](../external_libs/PyMatching/docs/path_gap.md). Native
backend sources are now included in each new run's source ZIP, together with
repository identity and diff hash. This is an empirical proxy; no new bound,
posterior interpretation, or comparative ranking is asserted.

## Official BeliefMatching code-capacity smoke

The separate [smoke report](results/beliefmatching_smoke_20260929/report.md)
compares ordinary upstream PyMatching with the unmodified official
BeliefMatching library on shared depolarizing code-capacity shots. It uses
two perfect Stim-generated extraction rounds with one intervening data-noise
layer and both X/Z detector sectors. Both product_sum and min_sum improve
on ordinary MWPM at the tested d=5/7, p=.05 points. All failures, including
BP-converged failures, are counted. Reproduction, pinned dependency setup
and limitations are in the report; the executable is
[scripts/beliefmatching_smoke.py](scripts/beliefmatching_smoke.py).
