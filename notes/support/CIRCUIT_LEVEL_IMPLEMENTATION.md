# Closed-memory circuit-level implementation

## Comparative correction-origin follow-up (2026-09-18)

The original shot schema stored the comparative logical gap but not the six
logical-class/color candidate weights from which it was formed.  A new local
sidecar worker uses the unchanged external decoder's public forced-class and
single-color controls to recover those weights under deterministic saved-seed
replay.  It stores separate strict-schema Parquet shards and validates stable
shot identity, class-major/rgb-minor tie behavior, reconstructed comparative
prediction, and reconstructed gap against the original data.  The final
Getting Started cell reports whether the minimizing color agrees between the
selected baseline class and its complementary forced class.

For the existing 300,000-shot d=3,5,7, p=.003 run, same/different color totals
are 185,549/114,451 (61.85%/38.15%); per-distance same-color fractions are
84.13%, 55.67%, and 45.75%.  The 600 sidecars occupy 22 MiB.  Original shot
Parquet and both external repositories remain unchanged.  This is correction
provenance for the existing comparative gap, not a new confidence definition
or color-aggregation theorem.  All 156 main-project tests pass.

Authority: [implementation prompt](../../prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md).
Environment: `color_code_so`. The root is not a Git repository. Starting external
branches are `phase2a/swim-distance`, clean, at PyMatching
`83cee05cc16d6fce9deafdbbf7952b4b96a7f21e` and color-code-stim
`ba6f7dc8b7aaab237d98ad5f08825be4225864c6`.

## Phase A review gate

The [compact algorithm](circuit_level_swim_algorithm.tex) is integrated after
the full construction specification. Same-agent review, before production
implementation: all eight requested checks pass. Its objective is precisely
`def:cl-swim`; class existence uses `thm:cl-quotient`; balance gates
`thm:cl-cut`, with `thm:cl-cover` as the fallback. `thm:cl-transport` is applied
to original-graph coverage before either transform. Half-edges, labelled loops,
parallel columns and zero-cost odd cycles remain present. Detector metadata
supplies provenance, never logical labels. Hard matrices and selection are
unchanged. Open temporal boundaries and sliding windows are excluded.
No proof or certified-dual claim is added.

## M0 baseline

Initial suite: 256 passed, 2 skipped, 8 failed. All failures are the known
Phase-2B grid/validation mismatch: default distances were changed to 5–15 while
small tests require 3 and a stale test rejects 15. Validation now accepts odd
3–15 independently of the unchanged default grid; the out-of-range test uses
17. The surface fixture also exposed missing `sinter`; install the version
matching installed Stim (1.16.0) in `color_code_so`.
Logs are under `implementation_artifacts/circuit_level/baseline/`.


Repaired baseline: **264 passed, two upstream skips**. The unchanged C++ test
binary passed **95 tests**; the frozen surface fixture passed 64 shots. The
code-capacity fixture is included in the Python suite. `sinter==1.16.0` is now
recorded in `environment.yml`. No decoder source was changed to repair baseline.

## Implementation and file inventory

The compact algorithm is included by `notes/note.tex`; its compiled PDF has
40 pages and no unresolved references or LaTeX warnings. The theory's existing
executable specification now points to this implementation section. No Phase-1
statement or circuit theorem has changed.

Under `src/color_code_softoutput/circuit_level/`:

- `model.py`, `graph.py`: immutable typed metadata, algebraic boundary roles,
  completed multigraph, stable unsorted-column provenance and exact incidence.
- `dem_adapter.py`: read-only public DemManager/DemDecomp H2, L2, probabilities,
  source/sort maps and full physical/virtual detector metadata validation.
- `logical_topology.py`: class existence, independent GF(2) rank oracle,
  spanning-forest balance potential, cached cut or general binary cover.
- `coverage.py`: original completed-graph metric balls and residual intervals.
- `swim.py`, `validation.py`: exact residual minimum, original-column XOR
  witnesses, parity/cost checks, correction feasibility and hard invariance.
- `decoder.py`: unchanged ordinary hard decode plus cached frozen-matrix replay
  for the existing generic PyMatching radius export. Public hard weights,
  correction, prediction and selected color must agree exactly on every shot.
- `experiment.py`: bounded closed-memory configuration, deterministic shared
  batch tasks, one physical sampling call and validated comparative pairing.
- `README.md`, `__init__.py`: public usage and scientific semantics.

`experiments/circuit_level_memory_test.py` reuses the shared worker pool,
seed function, atomic Parquet writer, provenance/archive helpers and RunResult.
`analysis/circuit_level.py` extends the existing dataset and reuses all three
plot classes; it audits every shard and can replay stored witness examples.
Shared `simulation/storage.py`, `simulation/provenance.py` and
`analysis/dataset.py` gained optional schema/provenance/dimension support with
existing defaults preserved. `simulation/config.py` and its old grid test were
repaired as described above. No alternative simulation framework was created.
The notebook `notebooks/circuit_level_getting_started.ipynb` only orchestrates
these reusable APIs. It defaults to loading the latest completed run and stays
output-free; the executed copy is in `implementation_artifacts/circuit_level/`.

## Component and regression acceptance

**Final full Python suite: 362 passed, two upstream skips, 110.44 seconds.**
This consists of the repaired 264-test baseline and 98 new circuit tests:
77 graph/adapter/topology/coverage tests, 11 decoder tests and 10 experiment
configuration/storage/audit tests. Full log:
`implementation_artifacts/circuit_level/final_tests.log`.

The tests cover exact matrix round trips, original observable/source identity,
probability and sort alignment, row padding/permutation and column permutation,
all colors at d=3,5,7, packed GF(2) rank versus odd-witness class existence,
synthetic balance/unbalance, loops, parallel edges, disconnected graphs and
absent classes. Tiny brute-force kernel enumeration checks the cover on both
synthetic graphs and actual retained subgraphs. Cut and cover agree on all
balanced tested graphs. Explicit counterexamples reject arbitrary cross-sheet
multisource distance and boundary-root-only search. A missing class builds no
analysis topology and returns infinity with no witness.

Residual checks use an independent interval oracle and selected native C++
residual exports, including temporal, diagonal, virtual, half-edge, parallel,
loop, partial-coverage and zero-cost odd-witness cases. Original logical labels
survive zero residual length. Tests include repeated/reordered/single/empty
batches, frozen matrix mutation rejection, unsupported memory rejection, exact
hard invariance, single physical sampling, comparative record mapping,
forced-bit independence, serial/parallel determinism and corrupt schema checks.
Every computed shortest path is witness-verified even when witness output is
omitted. Cost tolerance is absolute 1e-9 plus relative 1e-10; hard fields use
exact equality. These are finite correctness checks, not a universal proof
about the external effective-model generation.

## Actual static graph findings

Vertices include the artificial matching vertex. Mechanisms are original H2
columns. Every row below has an opposite class, passes internal balance, uses
`two_boundary`, and has zero internal odd-cycle obstructions and zero retained
zero-detector loops. Synthetic tests separately exercise such loops.

| d = rounds | Color | Vertices | Mechanisms | Half-edges |
|---|---|---:|---:|---:|
| 3 | r | 37 | 81 | 43 |
| 3 | g | 37 | 81 | 43 |
| 3 | b | 37 | 81 | 43 |
| 5 | r | 248 | 549 | 196 |
| 5 | g | 247 | 549 | 196 |
| 5 | b | 249 | 549 | 206 |
| 7 | r | 779 | 1729 | 507 |
| 7 | g | 789 | 1729 | 507 |
| 7 | b | 781 | 1729 | 535 |

These nine graphs are implementation evidence only. The general exact fallback
remains necessary for other retained labelled graphs. Full diagnostics and
frozen graph/source metadata are saved with the run and in
`implementation_artifacts/circuit_level/topology.json`.

## Completed small memory experiment

Saved run: [`results/20260916_182739_909527_circuit_level_memory_test`](../../results/20260916_182739_909527_circuit_level_memory_test/metadata.json).
Fully terminated triangular Z memory, `tri_optimal`, `rounds=d`, d=3,5,7,
`NoiseModel.uniform_circuit_noise(0.003)`, 2,000 shots per point, three workers,
250-shot batches, master seed 20260916. The value .003 is the prompt's default
implementation-validation point, not a threshold or paper-reproduction claim.

There are **6,000 paired physical shots in 24 Parquet shards**. Static setup
was **2.7855 s**; sampling, decoding, growth replay, residual computation,
shortest paths, all-shot witness checks and writes took **42.5960 s** including
worker teardown. Setup plus that phase was **45.3833 s**. These timings exclude
subsequent audit, saved-seed replay and plotting, and do not establish negligible
soft-output overhead. All **18,000 branch-shots used the cut; zero used the
cover** in this run.

| d | Shots | Ordinary failures | Comparative failures | Hard disagreements |
|---|---:|---:|---:|---:|
| 3 | 2,000 | 89 | 89 | 0 |
| 5 | 2,000 | 61 | 62 | 9 |
| 7 | 2,000 | 50 | 49 | 13 |
| Total | 6,000 | 200 | 200 | 22 |

The equal total failure counts do not imply equal hard predictions. The 22
comparative disagreements retain separate failure labels. On/off swim hard
invariance has **zero mismatches on all 6,000 shots**, including ordinary
prediction, weight, selected color, correction and derived failure label.
Selected swim is exactly the ordinary selected branch, never the color minimum.

The full raw-data audit verifies every shard, task seed, shot ID, field schema,
selected score, comparative alias, method/class/balance flags, independent
counts and summary, frozen model files, source ZIP hashes and external state.
One full saved 250-shot batch per distance was reproduced exactly (750 replayed
shots, not additional statistical samples). Metadata records the resolved
noise dictionary, circuit/schedule/perfect-boundary flags, conversion options,
physical/comparative circuits, effective DEM, typed stage-2 graphs, sources,
versions, root non-Git state and TeX algorithm hash.

Three PDF/PNG plot pairs show selected-score distributions, conditional LER
and paired postselection using the existing figure style and analysis classes.
Postselection uses every exact score threshold and whole ties. Zero-failure
rows remain in saved tables; they cannot be displayed on a logarithmic axis.
No fit, posterior calibration or performance ranking is inferred from this
small sample. All 10 notebook code cells executed without errors in the `color_code_so`
kernel. The notebook also replays three disagreement/failure examples
and verifies their logical witnesses. The source notebook remains output-free.
The distribution/conditional/postselection figures and algorithm pages were
visually checked; the final TeX build has no unresolved references or warnings.

## Review and practical limitations

A separate same-agent adversarial review followed implementation; this is not
external peer review. It checked the source-map/observable factorization,
probability rounding, no-class branch, coverage order, zero-cost witness,
cover endpoints, selected-color semantics, cached replay and metadata. The
probability validator reproduces the upstream singleton odd-parity formula
rather than replacing it by a mathematically equal but bitwise different
source probability. The no-class path was corrected to build no cut or cover
before the final tests. The dummy pair `(b_star,b_star)` used only to enable
the existing generic radius export supplies no logical score or shortcut;
its zero output is discarded and original-graph coverage is used.

The retained effective H2/L2 graph is authoritative. It does not restore
correlations discarded by X/Z separation or mechanisms filtered before stage 1;
existing source-map fallback limitations remain documented in REVIEW. Detector
coordinates/time/color are provenance and diagnostics, not logical labels.
The replay backend reads public matrices and never monkeypatches the hard
path. Its extra matching work is a current implementation cost.

Current radii use `sparse_blossom_final_defect_metric_balls_v1`; coverage uses
`original_completed_labelled_stage2_graph_v1`. **`swim_bound_certified=False`**
throughout. Exact residual minimization does not turn these radii into an
optimal odd-cut certificate or the score into a full-decoder gap or LLR.
No family-wide balance theorem, threshold sweep, open future boundary,
sliding window, temporal escape confidence or new aggregation is implemented.

Both external repositories remain clean on `phase2a/swim-distance` at the
SHAs recorded above; no new external branch or commit was needed. The main
workspace is not Git-tracked; its source archive is the reproducibility record.
Next task: **separately authorized sliding-window/open-temporal-boundary
integration**. Stop here pending that authorization.

## Reproduction

From the workspace root, using `color_code_so`:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run --no-capture-output -n color_code_so python -m pytest tests external_libs/PyMatching/tests external_libs/color-code-stim/tests -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLBACKEND=Agg conda run --no-capture-output -n color_code_so python -m color_code_softoutput.experiments.circuit_level_memory_test --shots 2000 --workers 3 --batch-size 250 --analyze
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=implementation_artifacts/circuit_level/tex notes/note.tex
```

Baseline, smoke, final test, notebook, TeX and validation-run logs are under
`implementation_artifacts/circuit_level/`. Replaying saved seeds is preferable
to resampling when checking this completed run.
