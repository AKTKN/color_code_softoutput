# AGENTS.md

## GitHub publication (2026-09-27)

The workspace root is now its own Git repository, published publicly at
`https://github.com/AKTKN/color_code_softoutput` on `main`. Its source release
tracks the package, tests, notebooks, prompts and research notes. The root
`.gitignore` excludes separate external decoder repositories, generated runs,
build artifacts, caches, source-audit paper copies and extracted paper text.
The decoder repositories remain independent Git repositories. See README.md
for installation and the limits of optional feature checkouts.

## Current color-correlated decoder authorization (2026-09-27)

The user requested `codex_color_correlated_decoder_prompt.md`. The opt-in
12-candidate implementation is in the currently checked out
`external_libs/color-code-stim/` branch `phase2a/swim-distance`, preserving
its existing SWIM APIs. It uses original-DEM guide corrections, aligned
source provenance, temporary stage-1/stage-2 priors and common base-prior
selection weights. The `ColorCode` API, focused tests and README were updated.
Use `color_code_so` with that checkout's `src` on `PYTHONPATH`. The full package
has 127 passes and two existing skips. Commit `57a6155` was pushed to
`origin/phase2a/swim-distance`; no campaign was done.
See `STATUS.md`. This user request supersedes earlier fixed-checkout guidance
only for this decoder implementation.

## Current circuit DEM-Y authorization (2026-09-19)

The user requested `prompts/codex_circuit_dem_y_gap_integration_prompt.md`.
The new module lives beside the preserved code-capacity monotone-Y metric in
`external_libs/color-code-stim-monotone-y/`, branch `feature/monotone-y-gap`,
base `0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`. It implements the specified
base-root/enriched-tail circuit DEM family, exact sparse junction solver,
immutable certificates/maps, optional native kernel and final-correction adapter.
Use `color_code_so` with that worktree's `src` on PYTHONPATH. Build the optional
kernel there with `python setup.py build_ext --inplace`; installed packages,
original decoder/path-gap sources, notebooks and datasets stay unchanged.

Support is closed triangular Z memory, odd d>=3, any integer T>=1, tri_optimal,
uniform circuit noise and the prompt's noisy flags. Exactness is within the
certified restricted family in the separated DEM, not a full gap or posterior.
The full package passes 163 tests (two existing skips), the old main monotone-Y
integration passes seven, and the 1,000-shot example and bounded timings pass.
Scoring remains slower than ordinary decoding; no efficiency or post-selection
superiority claim is justified. See `notes/support/CIRCUIT_DEM_Y.md`. No new
campaign, publication, commit or branch push was performed.


## Project title
Efficient soft-output computation for color codes with the concatenated-matching decoder

## Project overview

**Current authorization (2026-09-19): monotone-Y simulation and analysis.**
The user additionally requested sampling integration mirroring the path-gap
notebook and the same analyses as existing metrics. The new workflow is
`notebooks/monotone_y_getting_started.ipynb`, using `color_code_so`, isolated
feature imports, unchanged hard decoding and paired ordinary/comparative
signed scores plus forced gap. The six-point 768-shot smoke passes; a full
six-million-shot study remains user-launched. Keep existing notebooks, saved
data and external sources unchanged. See `notes/support/MONOTONE_Y_EXPERIMENT.md`.

**Current authorization (2026-09-19): monotone-Y signed-gap metric.**
The user requested `prompts/codex_monotone_y_gap_integration_prompt.md`, with
a theory/logic audit before implementation. The isolated feature worktree is
`external_libs/color-code-stim-monotone-y/`, branch `feature/monotone-y-gap`,
based on origin/main `0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`. It contains
the physical geometry/certificate, signed DAG scorer, final-correction adapter,
independent tests and bounded examples. Original decoder/path-gap checkouts,
existing result directories and the installed environment remain unchanged.
Use `color_code_so` with this worktree's `src` on PYTHONPATH; normal upstream
PyMatching acceptance also uses a temporary venv derived from that environment.
See `notes/support/MONOTONE_Y_THEORY_AUDIT.md` and the feature's
`docs/monotone_y_signed_gap.md`. No larger campaign or publication is implied.

**Current authorization (2026-09-19): selectable color-code path-gap v1/v2.**
The user requested a simulation argument selecting full correction-weight
subtraction v1 or path-overlap subtraction v2. `run_experiment` and
`sample_batch` accept `metric_version="v1"` / `"v2"` (API default v2);
the path-gap notebook explicitly selects v1. New runs save canonical metric
versions and support paired serial/parallel sampling and replay in either mode.
External decoder/metric sources and existing result directories stay unchanged.
See `notes/support/PATH_GAP_EXPERIMENT.md` and `STATUS.md`.

**Current authorization (2026-09-19): surface-code path-gap v1.**
The user explicitly authorizes editing the existing `external_libs/PyMatching`
checkout and `surface_code_test` to add global-subtraction path gap alongside
SWIM and complementary gap. This supersedes the fixed-PyMatching restriction
only for this implementation. Keep color-code-stim unchanged. Use
`color_code_so`; retain original ordinary hard decoding, full correction
weight subtraction, signed scores and paired shots. See
`external_libs/PyMatching/docs/path_gap.md` and `surface_code_test/README.md`.

**Current authorization (2026-09-19): path-gap numerical workflow.**
The user requested the same experiment as `notebooks/phase2a_getting_started.ipynb`
with the new path-gap metric and post-selection analysis. Added
`notebooks/path_gap_getting_started.ipynb`, main-package experiment/analysis,
tests and `notes/support/PATH_GAP_EXPERIMENT.md`. This supersedes the previous
stop only for that additional one-round workflow. Acceptance ran the full
60-point grid at 128 shots/point, not the 6-million-shot default. The follow-up
request now uses ordinary `color_code_so`: load the feature metric in an
isolated namespace without replacing the installed SWIM decoder/PyMatching.
The notebook selects the ordinary `color_code_so` kernel.

**Current authorization (2026-09-18): final-correction monochromatic path gap.**
The user requested `prompts/codex_monochromatic_path_gap_prompt.md`, including
package implementation, independent tests, a bounded smoke evaluation,
commit/push and a draft PR. This explicitly permits a new color-code-stim
feature branch based on `origin/main`, without merging the SWIM branches.
Implementation worktree: `external_libs/color-code-stim-path-gap/`, branch
`feature/final-correction-path-gap`, base
`0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`. The original two external checkouts
remain on their fixed SWIM commits. Acceptance uses a temporary venv derived
from `color_code_so` with ordinary upstream PyMatching 2.3.1, leaving the
existing Conda installation unchanged. See the worktree's
`docs/monochromatic_path_gap.md`. Scope is one-round triangular Z-memory,
tri_optimal, pure independent bit-flip noise; this is a heuristic with the
prompt's global correction-weight subtraction, not a new SWIM theorem.

**Surface-code companion (2026-09-16).** The user additionally requested the
surface-code counterpart of the circuit notebook under `surface_code_test/`.
Its modules, scripts, tests, notebook and saved runs live entirely there;
see [usage](surface_code_test/README.md) and
[validation](surface_code_test/VALIDATION.md). It follows the fixed PyMatching
`SO_example` rotated X-memory circuit: p=.001 and 2d explicit extraction rounds
by default. Both swim and complementary gap use the same physical shots and
ordinary hard decisions. The complementary gap is the difference of forced
logical-class minimum matching weights in the actual ordinary graph, not the
color-code comparative decoder or a posterior LLR. Use `color_code_so` and
keep both external repositories unchanged. No sliding windows or threshold
campaign is authorized by this companion task.

**Current authorization (2026-09-16): closed-memory circuit-level implementation.**
The user requested [the implementation prompt](prompts/CODEX_CIRCUIT_LEVEL_SWIM_IMPLEMENTATION_PROMPT.md).
It supersedes the older production-integration stop only for fully terminated
triangular Z-memory experiments, `rounds=d`, `tri_optimal`, and the bounded
uniform-noise validation run. Reusable adapters, original-graph coverage,
gated cut/general cover, witnesses and decoder integration live under
`src/color_code_softoutput/circuit_level/`; the experiment and shared analysis
extensions live under `experiments/` and `analysis/` in that package.
Use [the thin notebook](notebooks/circuit_level_getting_started.ipynb) and
[implementation report](notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md).
The selected score is the unchanged ordinary decoder's selected branch.
Growth remains uncertified; `swim_bound_certified=False`. All nine tested
d=3,5,7/color graphs pass internal balance; this is finite evidence, not a
family-wide theorem. Open temporal boundaries and sliding windows remain
outside the completed implementation. Keep `color_code_so` and both external
repositories fixed on `phase2a/swim-distance`: PyMatching
`83cee05cc16d6fce9deafdbbf7952b4b96a7f21e`, color-code-stim
`ba6f7dc8b7aaab237d98ad5f08825be4225864c6`.

The earlier authorizations and stop boundaries below are historical where
superseded by this closed-memory implementation prompt.

**Current authorization (2026-09-12): circuit-level theory.** The user requested
[the circuit-level prompt](notes/support/CODEX_CIRCUIT_LEVEL_THEORY_PROMPT.md).
It supersedes earlier circuit-level stop boundaries for CL1–CL12 theory,
primary-source audit, finite proof checks and an implementation specification.
The derivation is integrated into [notes/note.tex](notes/note.tex), Part II,
with [source](notes/support/circuit_level_theory.tex) and
[research summary](notes/support/CIRCUIT_LEVEL_THEORY.md). It does not authorize
production circuit-level SO changes, new sampling campaigns or sliding windows.
Keep both external decoder repositories fixed; use `color_code_so`.

The following Phase-2A/2B authorizations and Phase-1 checkpoints are historical;
their stop boundaries are superseded only within the current theory prompt.

**Active authorization: Phase 2B.** The user requested
[src/CODEX_PHASE2B_GETTING_STARTED_NUMERICS_PROMPT.md](src/CODEX_PHASE2B_GETTING_STARTED_NUMERICS_PROMPT.md),
a reusable numerical/analysis package and gated moderate code-capacity study.
This supersedes the historical pilot stop only within that prompt. Use the
Conda environment `color_code_so`. Main reusable source belongs under
`src/color_code_softoutput`; external decoder source remains fixed.


**Active authorization (2026-09-12): Phase 2A implementation.** The user
explicitly requested [the implementation prompt](src/CODEX_PHASE2_IMPLEMENTATION_PROMPT.md).
It supersedes the Phase-1 stop boundary below for its gated implementation,
small validation pilot, and paired comparative workflow only. Read
[implementation report](src/IMPLEMENTATION_REPORT.md),
[integration plan](src/INTEGRATION_PLAN.md), [test plan](src/TEST_PLAN.md),
and [implementation rules](src/AGENTS.md). Stop at failed correctness gates;
no large campaign or circuit-level swim topology is authorized.
Implementation progress and exact commands are in
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).
This project develops a mathematically justified method for extracting an efficient soft output, analogous to the cluster gap / swim distance of Meister, Pattison, and Preskill, from the concatenated-matching decoder for two-dimensional triangular color codes.

**Phase 1 (Research Tasks 1–7) is complete** in
[notes/note.tex](notes/note.tex), with [compiled PDF](notes/note.pdf).
The fixed-color logical theorem and non-c-face cycle basis justify a
cluster-contracted logical distance. Certified nonnegative optimal
matching duals define the clusters and give a fixed-stage-2
minimum-representative gap lower bound. The geometric algorithm handles
partial edge coverage and retains physical logical witnesses at zero cost.

The public external decoder interface has not been instrumented to export
these certificates. The reference LP/checks are research support, not a
production integration or evidence of negligible decoder overhead.
The latest [Tasks 6–7 prompt](prompts/CODEX_TASK_06_07_PHASE1_COMPLETION_AND_AUDIT.md)
requires stopping at this milestone. Wait for a separately authorized
Phase-2 task.

At the current stage, do **not** derive properties of the three-color aggregate output, do **not** claim a relationship to the full comparative/logical gap, and do **not** optimize or benchmark the method. Those are future tasks.

## Scientific scope
Phase-1 scope (Part II states the separately authorized circuit-level scope):
- Standard simply connected triangular 6.6.6 color-code patches of odd distance `d >= 3`, with ordinary color boundaries and perfect syndrome measurements. Other lattice families require a separate boundary audit.
- CSS-separated decoding; one Pauli sector can be analyzed without loss of generality when this is stated explicitly.
- Concatenated MWPM / matching decoder of Lee, Li, and Bartlett, with notation kept as close as possible to that paper.
- Stage-2 `c`-only graph `L_c^*` and the bijection `epsilon_c` between physical data-qubit vertices and stage-2 graph edges.
- Completed tasks: preliminaries, boundary classification, resolved graph, physical chain map, logical/stabilizer correspondence, induced binary complex, certified dual clusters, exact interval contraction, per-color swim distance and certified representative bound.
- MWPM and, where the logic is decoder-independent, Union-Find (UF) cluster growth.

Out of scope for the current theory milestone:
- How the three color branches should be combined into one final soft output.
- Any theorem comparing the proposed quantity with the full forced/comparative logical gap.
- Calibration against a posterior logical-failure probability or LLR.
- Circuit-level production integration and sliding-window decoding (the
  separately authorized fixed-fiber DEM theory is covered in Part II).
- Numerical benchmarking and implementation optimization.
- Claims of decoder optimality or asymptotic optimality.

## Non-negotiable research discipline
1. Distinguish clearly among: (i) statements proved in prior work, (ii) statements proved in this project, (iii) conjectures / hypotheses, and (iv) proposed definitions.
2. Never infer a theorem merely from a geometric picture. Every use of "logical path", "boundary", "stabilizer-equivalent", or "homology class" must be tied to explicit algebraic maps.
3. Do not identify the color code's equivalence to two toric/surface-code copies with the decoder-specific maps used by the concatenated decoder unless an explicit correspondence is proved.
4. Use the two retained stage-2 boundary labels in Lee Appendix A.3 as the source-guided starting point. Their fixed-fiber physical logical inequivalence is proved; preserve that interpretation when adding later metric structure. Do not retain auxiliary zero-cost matching shortcuts in the physical logical metric or introduce a data qubit for an exterior dual triangle.
5. Do not call the proposed quantity an exact logical gap, exact LLR, or posterior confidence unless such a statement is separately proved. The working term is `swim distance`, `cluster gap`, or `soft-output proxy` as appropriate.
6. When transferring a result from the surface code, identify every hypothesis of the original result and verify that it holds for the modified stage-2 color-code graph.
7. Prefer the notation of the primary source when it exists. Record every project-specific deviation in `NOTATIONS.md`.
8. Every substantial mathematical claim should have either a precise citation or an internal lemma/theorem label and proof status.
9. When a source is ambiguous or insufficient, record the issue in `REVIEW.md` rather than silently resolving it from intuition.
10. Keep Phase 1 focused on the per-color stage-2 construction. Do not extend it to aggregation, calibration or full-decoder guarantees without separate authorization.
11. Use the proved fixed-stage-2 quotient `K_c / R_c`, where `R_c = K_c intersect T_c^{-1}(S_X)`. Do not identify bare-graph homology with physical stabilizer equivalence or assume every physical stabilizer preserves the auxiliary stage-1 constraints.
12. Use the specified nonnegative optimal odd-cut certificate or separately defined UF growth data. Covered intervals from boundary-normalized dual radii can be resolved as proved, but arbitrary merged components or solver histories cannot be transferred. Missing growth data do not mean zero radii; the gap theorem requires the exact certificate equality.

## Directory structure

New theoretical research-task prompts and detailed research explanations in
Markdown belong in `notes/support/`, as requested by the user. Keep the main
integrated TeX note at `notes/note.tex`; supporting TeX sections and finite
proof checks may also live in `notes/support/`. Historical prompts under
`prompts/` and implementation specifications under `src/` retain their paths.
The canonical bibliography remains `refs/REFERENCES.md`; do not create root
duplicates of supporting research summaries or the bibliography.

Historical Phase-2 directory inspection: the workspace root had no Git
repository before the 2026-09-27 GitHub publication.
`external_libs/PyMatching/` and `external_libs/color-code-stim/` are separate
Git repositories; both use the dedicated `phase2a/swim-distance` branch.
The supplied implementation documents live under `src/`, not the root.
`tests/` and `paper/` initially contain only `.gitkeep`.
`color_code_so` is the active Conda build/test/notebook environment.
`.venv-phase2a/` is retained as historical Phase-2A provenance.
`src/color_code_softoutput/` holds reusable Phase-2B source; `notebooks/` holds
the thin Getting Started notebook, and `results/` holds timestamped runs.
`implementation_artifacts/baseline/` holds reproduction logs/fixtures;
`implementation_artifacts/pilot/` holds the final pilot and review.
`scripts/phase2a_*.py` reproduce baselines, pairing/statistics, pilot and audit;
`src/phase2a_pilot.json` fixes the pilot grid. Top-level `tests/` now contains
the independent mathematical and pairing/statistics checks; each external
repository also contains its package-specific tests.
The Phase-1 tree below is retained as historical context.
```text
.
├── AGENTS.md              # Operating rules, directory structure, last update, next task
├── STATUS.md              # Current completion state and validation
├── NOTATIONS.md           # Active canonical notation and reserved historical symbols
├── PROJECT_DETAIL.md      # Phase-1 results and Phase-2 scope
├── REVIEW.md              # Claim inventory, audit and retained concerns
├── prompts/
│   ├── CODEX_INITIAL_PROMPT.md
│   ├── CODEX_TASK_01_BOUNDARY_STRUCTURE.md
│   ├── CODEX_TASK_02_03_SPLIT_BOUNDARY_AND_PATH_MAP.md
│   ├── CODEX_TASK_04_05_LOGICAL_TOPOLOGY_AND_MEISTER_GRAPH.md
│   ├── CODEX_TASK_06_07_PHASE1_COMPLETION_AND_AUDIT.md
│   └── CODEX_RESEARCH_TASK_TEMPLATE.md
├── refs/
│   ├── REFERENCES.md      # Canonical audited bibliography
│   ├── efficient soft output.pdf
│   ├── Color code decoder with improved scaling for correcting.pdf
│   └── source_audit/      # Additional primary PDFs
├── notes/
│   ├── note.tex           # Integrated Phase-1 mathematical derivation
│   ├── note.pdf           # Compiled research note
│   ├── support/           # Theory task prompts, detailed Markdown explanations,
│   │                     # supporting TeX, finite checks and reproduction guides
│   ├── deferred_proof_program.md # Historical conditional proposals and audit
│   ├── color_code_swim_distance_report_reviewed.md
│   └── color_code_swim_distance_peer_review.md
├── external_libs/
│   └── color-code-stim/   # External repository with its own Git history
├── paper/                 # Later manuscript placeholder
├── src/                   # Reusable package and historical implementation specs
└── tests/                 # Mathematical, integration and analysis tests
```

The six primary state documents are `AGENTS.md`, `STATUS.md`,
`NOTATIONS.md`, `PROJECT_DETAIL.md`, `REVIEW.md`, and
`refs/REFERENCES.md`. Read all six before research work.
`notes/note.tex` is their reviewed mathematical companion: it contains
the actual Tasks 1–7 definitions and proofs, while the six files track their
status and scope. Reconcile any discrepancy through review.

The bibliography lives under `refs/`; historical prompts are under `prompts/`,
and new theoretical task prompts/explanations belong under `notes/support/`.
Root-level paths in older instructions refer to those moved files; do
not create duplicate root copies. The latest Tasks 6–7 prompt supersedes
earlier stop-before-clusters instructions. It authorizes the completed
metric construction, analytical audit and finite proof checks, but no
three-color aggregation or performance study.

Use `refs/` for local literature. The bibliography records which PDFs are present and which sources were inspected online. Other source filenames in historical notes are not evidence of local availability. Consult the inspected-location ledger before repeating the source audit.

The older reports, peer review, and `notes/deferred_proof_program.md` are historical supporting material to audit against primary sources and the current scope. Their discussion of three-color aggregation does not expand the active milestone or establish a theorem. If supporting material conflicts with the primary project-state documents, the latter take precedence after review.

Use `external_libs/color-code-stim/` to inspect the decoder implementation when needed. Relevant entry points include `src/color_code_stim/graph_builder.py` and `src/color_code_stim/decoders/concat_matching_decoder.py` relative to that external repository. Implementation evidence does not replace mathematical definitions or proofs. Future project code and tests belong in the top-level `src/` and `tests/` directories.

`src/` and `tests/` contain the completed Phase-2 code and validation suites;
`paper/` remains a later manuscript placeholder. The integrated static and
circuit-level theory is in `notes/note.tex` with compiled `notes/note.pdf`.
Keep detailed research Markdown in `notes/support/`; defer `paper/main.tex`.

## Workflow
The intended order is:

1. **Project setup and source audit**: read the six project-state files listed above, inspect the core literature in `refs/` and obtain missing sources as needed, verify notation and scope, and update all six documents at their current paths.
2. **Preliminaries and task formalization**: write a source-grounded mathematical account of triangular color codes and the concatenated-matching decoder sufficient for the proof program; then sharpen the research questions and proof dependencies.
3. **Theory construction**: solve one proof obligation at a time. After each substantive step, perform an independent review before proceeding.
4. **Paper formulation**: retain the integrated Phase-1 note; a publication manuscript and broad motivation are separate later tasks.
5. **Motivation and related work**: perform a broader literature search and write the introduction/positioning after the core theory is settled. This is intentionally deferred to conserve research effort and avoid over-positioning an unstable result.

## Completed proof program and next boundary

1. Tasks 1–3: full boundary classification, resolved graph and exact chain map.
2. Task 4: terminal/physical logical parity, path converse, non-c face basis and induced complex.
3. Task 5: Meister-type topology and inherited weights for one stage-2 fiber.
4. Task 6: normalized matching dual, metric clusters, exact partial-edge contraction and algorithm.
5. Task 7: physical logical minimum, certified representative bound, source and claim audit.

For certified optimal MWPM data,
`W_opp^(2) - W_base^(2) >= phi_c` is proved. It concerns one fixed auxiliary
stage-1 parity fiber, not the full physical syndrome fiber or a summed
logical-class LLR. UF has the geometric construction but no transferred
representative inequality. Equal matching minimizers alone do not
identify growth data. Only the specified boundary-normalized dual has
the proved covered-interval transfer; resolved components are recomputed.

The metric postprocessing is O((|V|+|E|)log|V|) given radii. The explicit
companion LP has exponential representation size; practical instrumented
extraction remains open. These are distinct costs.

Current results are in PROJECT_DETAIL §§8–10 and note §§10–13.
The complete formal-claim inventory and retained concerns are in REVIEW.
Finite sanity checks live in [notes/support](notes/support/README.md).
Older proposals and review history remain in
[notes/deferred_proof_program.md](notes/deferred_proof_program.md).

## Update policy
Whenever work is completed:
- Update `STATUS.md` with what was checked, what was proved, what remains open, and exact source locations when useful.
- Update `NOTATIONS.md` before introducing new symbols elsewhere.
- Update `refs/REFERENCES.md` when a source becomes mathematically relevant, not merely because it is tangentially related.
- Update `PROJECT_DETAIL.md` when the dependency graph, theorem statement, or scope changes.
- Update `REVIEW.md` after an independent audit and keep unresolved blocking issues visible.
- Update the `Last update` and `Next task` fields below.

## Last update

2026-09-27 — Completed Task 04 bounded point storage and final Parquet files.
Out-of-order chunks spool in `.buffer/`; final metric files carry explicit
int64 shot indices and validated exact dtypes. Focused tests pass. Next task:
top-level runner and CLI integration; no campaign.

2026-09-27 — Completed Task 03 adaptive scheduler and progress/ETA. Spawn
workers dispatch by round robin; per-point calibration feeds EWMA chunk sizing.
Results stream to a main-process callback with no final storage. Synthetic and
real-spawn tests pass. Next task: final storage and CLI runner; no campaign.

2026-09-27 — Completed Task 02 worker-side sampling and required metrics.
The worker uses a bounded per-process cache and pairs ordinary/correlated
decisions on one sample. Public contract and tests are recorded in the package
README and STATUS. Next task: scheduler and storage integration; no campaign.

2026-09-27 — Completed Task 01 YAML configuration and sweep planning with
strict option validation, immutable point identities, native noise mapping,
semantic hash and path-collision preflight. Focused and legacy regression
tests pass. Next task: worker adapters; no sampling or runner changes yet.

2026-09-27 — Audited the current simulation architecture and local decoder API
for the staged YAML workflow refactor. The plan is
`src/SIMULATION_WORKFLOW_REFACTOR_PLAN.md`; no runner, scheduler, or storage
refactor was implemented. Correlated decoding plus matching-growth SWIM is
an explicitly unsupported combination. Next task: implement and test strict
configuration/sweep planning and capability validation before worker changes.

2026-09-27 — Published the root package as public
`AKTKN/color_code_softoutput` on GitHub. The initial source commit is
`cdea414`; generated results, local checkouts, build/cache files and
third-party reference papers are ignored. See STATUS.md and README.md.

2026-09-27 — Implemented the color-correlated concatenated decoder in the
existing SWIM checkout. The flag defaults off; 12-candidate selection uses
unmodified stage-2 weights. All 127 package tests pass with two skips, plus
a bounded circuit-noise smoke. Pushed `57a6155` to
`origin/phase2a/swim-distance`. See STATUS.md.

2026-09-19 — Completed the circuit DEM-Y module, exact sparse native/Python
scorer, offline certificates, independent oracles and standalone algorithm
PDF. Full package 163 passes/two existing skips; 1,000-shot example and bounded
timings pass. The measured efficiency advantage remains unmet. See STATUS.md
and `notes/support/CIRCUIT_DEM_Y.md`. Earlier metric sources/data are preserved.

2026-09-19 — Post-selection plots use distinct, fixed marker shapes for each
soft output, including expanded views. Six saved-data figures regenerated
with unchanged numerical tables; see STATUS.md. No new sampling.

2026-09-19 — Added an editable `postselection_xlim` expanded-view cell to the
monotone-Y notebook and optional `xlim` to the shared post-selection plotter.
All three saved-data plots validate with unchanged numerical tables; zoomed
outputs use separate filenames. No sampling was run.

2026-09-19 — Integrated monotone-Y paired sampling, schema/provenance/replay,
shared distributions/conditional LER/post-selection/quantitative comparisons,
and a new Getting Started notebook. It mirrors the reference's d=9,13,15,
p=.04/.05 and 1M shots/point settings with sampling initially disabled. The
bounded 768-shot smoke passes. See STATUS.md for test/notebook acceptance.

2026-09-19 — Implemented the separately authorized monotone-Y metric after
the formulation audit. Exact local coordinate certificates and independent
all-path checks cover the accepted geometries; d=3/5/7 reference support
counts are reproduced. Online scoring is O(n) per shot, preserves signed
values and final hard corrections, and supports bounded-memory batch mapping.
Acceptance and small-batch timing are recorded in STATUS.md and the feature
worktree's `docs/monotone_y_validation.md`.

2026-09-19 — Added `metric_version="v1"` / `"v2"` to the path-gap simulation
API and `--metric-version` to the CLI. Notebook selects v1 and preserves the
user's sampling configuration. New versioned v1/v2 data loads and replays with
the recorded formula; legacy runs keep their original schema. See STATUS.md.

2026-09-19 — Added surface-code path-gap v1 in the existing PyMatching checkout
and surface workflow. 117 backend, 33 surface and 171 main tests pass; 768-shot
bounded smoke/audit/replay passes. See STATUS.md and surface_code_test/VALIDATION.md.

2026-09-19 — Added `include_forced_gap=True` to the distribution plotter and
notebook fixed-p cell, with distinct palettes, per-decoder failure labels and
separate artifact filenames. Saved v2 data reused without sampling. See STATUS.md.

2026-09-19 — User-authorized path-overlap revision on the existing
`feature/final-correction-path-gap` branch: phi_c now subtracts only W(E ∩ L_c)
from the returned residual-Dijkstra path distance. Graphs, decoder, weights and
tie behavior are unchanged. Version `path_overlap_v2`; saved legacy results
remain unchanged. See STATUS.md and the feature worktree's
`docs/path_gap_overlap_v2.md` for acceptance.

2026-09-19 — Added saved-run quantitative post-selection tables/report at the
end of the path-gap notebook. Reports matched abort, reduction rates, residual
LER ratios, count warnings and separate whole-tie threshold policies. User's
4M-shot run analyzed without resampling; see STATUS.md and run-local
`path_gap_comparison/REPORT.md`. No statistical equivalence is claimed.

2026-09-19 — Follow-up: path-gap now runs in ordinary `color_code_so` without
installation or environment switching. The metric's feature source is loaded
separately without changing the active decoder imports or either external
repository. Provenance records both sources. See STATUS.md for validation.

2026-09-19 — Added the path-gap Getting Started experiment and post-selection
workflow. Five feature tests pass; original-environment regression: 158 pass,
3 environment-specific skips. Full-grid 7,680-shot smoke and all 60 replayed
batches pass; final notebook has ten executable code cells. Full study remains
user-launched. All external sources remain unchanged. See STATUS.md.

2026-09-18 — Completed the separately authorized final-correction path-gap
package in the feature worktree. 99 tests pass with upstream PyMatching,
2 existing skips; the bounded smoke and 768-row audit pass. Published branch
`feature/final-correction-path-gap` at `617d1ce` and draft PR
https://github.com/AKTKN/color-code-stim/pull/1. See STATUS.md and the feature
worktree's API/implementation documentation.
2026-09-18 — Added comparative correction-origin analysis to the circuit-level
Getting Started notebook. Deterministic saved-seed replay stores all 2 logical
classes x 3 color candidate weights in separate validated Parquet sidecars and
checks the reconstructed prediction/gap against the original run. On 300,000
shots, baseline/forced colors agree in 185,549 (61.85%) and differ in 114,451
(38.15%). Original shot data and both external repositories remain unchanged.

2026-09-17 — Appended a saved-data scatter cell to the circuit-level Getting
Started notebook: x is the ordinary-selected color's SWIM distance and y is the
paired comparative forced gap, with a black dotted y=x line. The cell verifies
the selected-color reconstruction exactly. All 11 code cells execute on the
existing 300,000-shot run, and the scatter cell also runs standalone in a fresh
kernel; no sampling, decoder, or stored data changed.

2026-09-16 — Added an empirical saved-data notebook comparing selected-color,
minimum, maximum and mean aggregation of the three per-color circuit SWIM
values. Each strategy has separate distribution, conditional-LER and
post-selection artifacts; all use ordinary hard failure labels. The existing
300,000-shot data were reused, with no simulation or decoder change. This does
not establish an optimal three-color rule. Twenty-eight targeted tests and all
155 main-project tests pass. See STATUS.md and REVIEW.md.

2026-09-16 — Wilson intervals in the main package's conditional-LER,
post-selection and physical-error-rate plots now use shaded bands in the
series color at alpha=.2. Numerical intervals and stored data are unchanged;
no sampling or decoder changes. See IMPLEMENTATION_STATUS.md for checks.

2026-09-16 — Added optional actual-score `round_digits` to the circuit notebook's
three plotting APIs; None preserves prior numerical behavior. Rounded ties
are retained together and stored data stays unchanged. Swim uses YlGn and
forced gap Blues; scatter keeps o/x markers with alpha=.75. This is an
analysis-only follow-up with no new sampling or decoder changes.

2026-09-16 — Added the surface-code companion under `surface_code_test/`,
reusing the existing circuit example and shared batching/storage/statistics/
figure style. Exact tiny-graph and independent integer-program checks validate
the complementary gap; interval checks validate the generic swim metric.
All 29 surface tests pass. End-to-end run and notebook acceptance are recorded
in [surface_code_test/VALIDATION.md](surface_code_test/VALIDATION.md).

2026-09-16 — Implemented the closed-memory circuit-level swim pipeline,
with original labelled H2/L2 provenance, cached balance/cut/cover preprocessing,
verified original-column witnesses, exact hard-output invariance, paired
uniform-noise simulation, shared Parquet/analysis and a thin notebook.
362 Python tests pass (two upstream skips); 95 C++ tests pass. The bounded
validation grid is d=3,5,7, rounds=d, p=.003, 2,000 shots per distance.
Run details and final acceptance evidence are in
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md). No external source change
or new mathematical certificate is introduced.

2026-09-12 — Completed the authorized circuit-level theory package in Part II
of `notes/note.tex`: DEM quotient, observable audit, general cover, gated cut,
labelled contraction, controlled Phase-1 reduction, conditional certified gap,
and executable construction/validation specification. Primary-source audit,
finite proof checks and separate same-agent adversarial review are recorded.
The local prism map, universal geometric cut and production certificate remain
open. New theory prompts/detailed Markdown belong in `notes/support/`.

2026-09-12 — Completed the requested post-selection plotting follow-up:
exact unique-score thresholds, whole ties, and markers connected by lines
without subsampling. Analysis validation: 11 passed; one existing integration
test is blocked by d=3 being absent from the current configured grid.
See `IMPLEMENTATION_STATUS.md` for the command and details.

2026-09-12 — Completed Phase 2B in the `color_code_so` Conda environment.
Added the reusable experiment/analysis package and thin notebook. The gated
moderate study saved 4.8 million paired shots in 960 shards; 262 Python tests
pass (two upstream skips), full raw-data/replay audit passes, and all notebook
cells execute. Both external decoder commits remain unchanged and clean.
The primary crossing is unresolved at the upper grid endpoint; numerical
limitations and the missing dual certificate remain explicit in the review.

## Next task

Implement the staged workflow worker adapters after the Task 01 planning
layer, preserving paired shots and existing soft-output definitions.

Circuit DEM-Y is ready for bounded use via the feature worktree
`examples/circuit_dem_y_gap.py`; see `notes/support/CIRCUIT_DEM_Y.md`. Review
the explicit performance limitation before a larger study. Any broader
adapter, performance redesign or empirical campaign requires a new request.

For expanded monotone-Y post-selection plots, run the new cell immediately
after the full-range plots and edit `postselection_xlim` (default `(0.0, 0.2)`).

Monotone-Y sampling and analysis are ready in
`notebooks/monotone_y_getting_started.ipynb`, using the ordinary `color_code_so`
kernel. It currently loads the latest completed monotone-Y run with sampling
disabled. Enable `RUN_NEW_EXPERIMENT=True` to launch the configured study;
`SMOKE=True` uses 128 shots/point. Existing notebooks are unchanged. The
logical-family minimum is certified on each accepted geometry; all-distance
minimum-weight coverage, full-gap equality, calibration and post-selection
superiority remain unproved. No full campaign or branch publication was run.

Path-gap v1/v2 selection is ready. Restart the `color_code_so` notebook kernel,
then use `metric_version = "v1"` (full correction weight) or `"v2"` (path overlap)
in the settings cell. The existing sampling toggle is True; executing the
sampling cell starts the configured study. No full study was run for this edit.

Surface path-gap v1 is ready in `color_code_so`; restart the notebook kernel
to load the rebuilt PyMatching. Existing surface runs lack this score; explicitly
set `RUN_NEW_EXPERIMENT=True` to generate a new paired three-score run. The
current notebook run selection and 300k-shot configuration were preserved.
PyMatching's prior fixed-commit restriction is superseded only for this feature;
its existing checkout is now locally modified. Color-code-stim remains fixed.

Distribution overlay is available in the path-gap notebook's fixed-p plotting
cell. Restart the kernel to load the plotter change, load the saved dataset,
and rerun plotting cells only; no new sampling is needed.

The overlap-v2 implementation is complete; new runs use the versioned overlap
schema. Existing unversioned runs retain global-subtraction v1 semantics;
replaying those requires archived v1 source (saved-data audit: replay=False).
Do not rerun the notebook sampling cell or replace legacy results implicitly.

Quantitative path-gap comparison is available in the appended notebook cells.
Run only those cells to re-analyze the current dataset; the user's earlier
sampling cell remains enabled and should not be rerun unintentionally.

Use the ordinary `color_code_so` kernel for the path-gap notebook; the former
dedicated environment is optional historical validation only.

Path-gap experiment implementation is complete. Review the saved smoke and
launch the full configured study explicitly from its notebook or CLI when
desired. The small acceptance sample cannot establish post-selection superiority.

The final-correction path-gap scope is limited to its implementation prompt;
larger studies, circuit-level adapters and theoretical guarantees require a
new objective. Refer to STATUS.md for its validation and publication state.
The empirical aggregation notebook is complete. A theorem, calibrated model,
or production choice among these strategies requires separate authorization.
The Wilson-band plotting follow-up is complete; rerun plot cells to render
shaded intervals from existing data.
The plot-rounding/palette follow-up is complete; plotting controls are in the
circuit notebook. Existing sampling settings remain user-controlled.
The surface-code companion is a completed closed-memory workflow; review
[its validation record](surface_code_test/VALIDATION.md) before extending it.
Next task: await a new objective before extending color-correlated decoding,
starting larger numerical campaigns, or changing historical metrics. The
separately authorized sliding-window/open-temporal-boundary work remains
open. Continue using `color_code_so`. Review the
[implementation report](notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md),
[integrated note](notes/note.pdf), and [audit](REVIEW.md) first.
