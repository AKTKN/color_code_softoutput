# REVIEW.md

## Ensemble stage-2 SWIM integration audit — 2026-09-27

The `ba6f7dc` color-code-stim stage-2 backend and PyMatching `83cee05cc`
labelled metric graph were compared with the legacy PyMatching
`color-code-so` `SoftOutputDijkstra::reweight` path. Both use matching-growth
radii to reduce cluster-covered edge costs before a shortest path; the new
adapter preserves the two physical stage-2 terminals and does not use the
path-gap correction-edge zeroing path. The historical
`selected_swim_distance` contract is retained for old Phase 2B sampling;
the new same-logical-class minimum is exposed separately and is the YAML
sidecar value. Every candidate metric uses the original base stage-2 prior.
The circuit integration routes closed triangular `rounds=d` points through
the existing completed-graph cut/cover scorer. It uses each generated
stage-1 hypothesis for original-prior stage-2 matching and growth, then
uses the generated correction parity for the same-class reduction. The
bit-flip, depolarizing and uniform DEMs pass bounded d=3 checks for ordinary
and ensemble strategies. Other custom DEMs still need to pass the graph and
probability gates; open windows and family-wide topology correctness are
not established.
For perturbation, a base-prior rematch of the candidate's stage-1 hypothesis
can have a different stage-2 correction from the generated perturbed-prior
candidate; the metric is associated by the generated correction's observable
parity. This convention is explicit and should be revisited if interpreting
candidate-specific matching clusters becomes the scientific objective.
No theorem relates this ensemble reduction to a forced gap or posterior.

## Circuit DEM-Y audit — 2026-09-19

Separate same-agent source/proof review with independent set/path enumeration,
Cartesian cap-XOR oracles and native/Python cross-checks; not external peer review.
The full report is `notes/support/CIRCUIT_DEM_Y.md`. No correctness blocker
remains within the accepted, per-geometry certified family. Performance remains
an explicit unresolved objective: scoring is slower than ordinary decoding.

The audit verifies error-instruction-only indexing, full matrix/probability
comparison, sector maps, invisible/mixed-column rejection, actual face/time
identities, terminal-level cuts, raw-base temporal enrichment before independent
pruning, and all-path nonreuse. Strong cap checks use full suffix unions, not
selected tails. The oracle's initial destination-only traversal missed a highest
source in the deliberate reuse fixture; visiting every source repaired that
oracle. The production certificate already covered all sources.

The sparse join retains zero-cost structural edges, folds the root sign, uses
+4 for triple intersections and adds the root constant exactly once. All three
interaction cases and unavailable parity states agree with direct Cartesian XOR
oracles; 64-option masks and the larger sparse fallback are both tested.
Triangle deduplication uses a canonical existing wedge center, preserving the
family. There is no full root-product scan or per-root length-m cost vector.
Final witnesses satisfy full H/O and direct correction-weight differences;
score-only and witness outputs agree. Instrumented decoder methods receive zero
calls from scoring. Hard predictions, original extras and earlier metrics remain
unchanged. Model/probability/ordering caches and immutable weights are checked.

Acceptance: 163 package passes/two existing skips; seven existing main
monotone-Y integration passes; 1,000-shot example, wheel smoke and bounded
setup/memory/timings. Proved restricted-family exactness and correction-relative
inequalities do not establish all-distance degree/coverage bounds, original
joint-noise likelihoods, full class-gap equality, calibration, or post-selection
equivalence. No claim of meeting the efficiency objective is made.


## Monotone-Y simulation/analysis audit — 2026-09-19

Same-agent source review and independent physical/count tests verify that
sampling passes only final corrections to the metric, never true observables,
and keeps hard predictions, selected colors, weights and final corrections
unchanged. Circuit pairing is checked; comparative bookkeeping receives zero.
Signed scores and their own decoder failure labels survive storage/replay.
The physical witness oracle uses canonical column IDs (not circuit qids) and
integer parity arithmetic. Exact serial/parallel replay passes.

Shared analysis accepts explicit named metrics. Raw-count tests verify
matched-abort and whole-tie policies separately; conditional fits stay
empirical, intervals pointwise, and zero-reference ratios undefined. The
empty near-threshold grid in the reference configuration exposed a plotter
error; it now emits an unavailable-data panel and the existing insufficient
crossing status. Regression covers this subthreshold-only configuration.
The 768-shot smoke validates plumbing, not post-selection competitiveness.
All original decoder sources, feature metric sources and existing notebooks
were unchanged by this integration. See `STATUS.md` for acceptance evidence.

## Monotone-Y theory and implementation audit — 2026-09-19

Same-agent rederivation before implementation, followed by a separate source
review and independent executable oracles; not external peer review. The
pre-implementation disposition and reasoning are in
`notes/support/MONOTONE_Y_THEORY_AUDIT.md`. No formulation blocker was found.

The essential separation premise is certified for every compiled geometry by
local coordinate cones for the tail of each qubit's unique directed pair.
Using the incident face in that argument is insufficient, because it can be
an incoming edge head. The final certificate checks all offset patterns and
the full first-edge neighborhood, even when local XOR cancels a qubit.
An independent reachability-union checker considers every path and detects a
deliberately corrupted, potentially unselected continuation with a shared
qubit. Acyclicity alone is never used to claim tail independence.

All d=3 corrections and selected d=5/7 signed-weight cases agree with direct
physical-XOR family enumeration. Physical logical-coset enumeration independently
reproduces minimum-weight coverage counts at d=3/5/7. Rank, check, observable,
parallel pair, boundary, witness and unknown-real-state checks pass. Exact
physical class-gap identities are checked separately from decoder logical_gaps.

Mapping counts flattened error instructions only, validates full physical
detector/observable signatures and probabilities, and cross-checks unique
single-X locations with Stim circuit propagation. The actual observable is
resolved from measurement records; comparative bookkeeping accounts for the
absolute SHIFT_COORDS time. Only fully assembled final error_preds are used.
An initial test oracle incorrectly used Boolean matrix multiplication for
parity; casting to integer repaired the oracle, without changing the metric.

The final source review fixed whole-batch temporary allocation in binary
validation and DEM mapping; normal scoring now uses chunks. A dedicated test
enforces the mapping chunk bound. Witness recovery scans canonical columns
instead of sorting per shot. Original sources, installed packages, notebook
settings and stored results are preserved. Remaining limitations are float64
arithmetic, non-linear setup audits, one-layer adapter scope, no all-distance
minimum-support coverage theorem, no posterior calibration or performance
ranking. Exact acceptance/timing evidence is in the feature worktree's
`docs/monotone_y_validation.md`.

## Path-overlap implementation audit — 2026-09-19

Same-agent adversarial diff review verifies edge-ID witness recovery, canonical
qubit-level overlap, unchanged igraph residual-weight tie behavior, and color
selection only after all three signed scores. Exhaustive independent physical
path enumeration checks returned witnesses under ties rather than minimizing
postprocessed scores across them. A dedicated unequal-overlap tie fixture
confirms this distinction. Legacy outputs are preserved; new schemas carry
`path_overlap_v2`. This is an implementation definition change, not a new
full-gap theorem or an empirical superiority claim. See feature-worktree
`docs/path_gap_overlap_v2.md` for test evidence.

## Post-selection competitiveness audit — 2026-09-19

Saved-data-only analysis uses explicitly associated hard-decoder failures and
checks identical shot identities across metrics. Reduction rates use each
decoder's own no-selection LER; residual-LER ratios compare final performance.
Synthetic independent counts verify adverse reduction, exact ties, differing
whole-tie abort rates and undefined zero-denominator ratios. The 1.25 margin
flags point estimates only; no bootstrap or noninferiority confidence claim
is made. Wilson intervals are pointwise LER intervals, not reduction/ratio
intervals. Low-count warnings prevent interpreting zero/zero as equality.
The user's p=.04 results are heterogeneous; no global competitive/superiority
claim follows. No sampling or source-decoder mutation occurred. Existing
notebook outputs and user sampling settings were preserved when appending cells.

## color_code_so coexistence follow-up — 2026-09-19

The main experiment now uses the installed SWIM decoder/backend with the
feature metric loaded under a private namespace. The loader does not patch
sys.path, color_code_stim.__path__, or replace ColorCode; source-level isolation
is tested together with SWIM and path-gap evaluation in the same process.
Metadata records metric source separately from decoder/backend source.
Original external sources are unchanged. Full-grid smoke outputs match the
prior upstream-environment rows exactly, excluding run ID; this finite check
does not establish universal backend tie equivalence.

## Path-gap experiment audit — 2026-09-19

Separate same-agent implementation review, not external peer review. No metric
algorithm is duplicated: both decoder cohorts call ColorCodePathGap on the
existing final result. Tests verify seed/schedule invariance, serial/parallel
equality, strict signed-score reconstruction, failure associations, metadata,
streaming completeness and exact replay. All 60 smoke batches replay exactly.
Actual feature imports/upstream PyMatching provenance are distinguished from
the unchanged original SWIM checkouts. Old main-analysis tests still pass.

Threshold curves preserve whole raw-score ties. The explicitly separate
matched-retention table splits boundary ties by outcome-independent shot ID.
Comparative path-gap and forced gap share failure labels; ordinary path-gap
does not. Negative path gaps are not clipped or outcome-negated. Raw zero
failure counts and Wilson upper bounds are preserved. Logistic fits, coarse
crossings and smoke rankings are exploratory, not calibrated probabilities
or evidence of superiority. All original external sources remain unchanged.
The full 6-million-shot default was not run. Usage and limitations are in
`notes/support/PATH_GAP_EXPERIMENT.md`.

## Final-correction path-gap review — 2026-09-18

Separate same-agent source/diff review, supported by independent executable
oracles; not external peer review. The prompt is authoritative for this new
heuristic. Its phi is not the existing certified/geometric SWIM phi.
All 99 package tests pass with upstream PyMatching 2.3.1 (2 existing skips).

Physical topology uses stable qids and colored primal incidence, partitions
all qubits into pair/singleton supports, and preserves parallel/zero-cost
edges and distinct corner/side terminals. d=3 exhaustive unsuppressed-path
enumeration and d=5 independent coordinates validate suppression; physical
H/logical supports independently validate d=3,5,7 witnesses. This finite
validation does not substitute for a new full-decoder gap theorem.

The adapter reads only final `error_preds`, after existing composition, and
checks its error-only DEM mapping against full physical detector/logical
signatures. Raw DEM instruction indices are not used as columns. Matching
weights and candidate colors never replace W(E) or the final E. All other
noise channels/overrides, suppressed/doubled data layers and unsupported
configurations are rejected. Original state and both SWIM checkouts are intact.

An evaluation-review finding corrected an exact-enumeration tie-order bias:
patterns sharing a score now have the same randomized acceptance probability,
so physical pattern order cannot influence equal-retention LER. Whole-threshold
curves remain primary. Exact sums use physical probabilities; MC uses Wilson
intervals including zero-failure upper limits. Signed exact class/correction
quantities remain distinct. The smoke is small and cannot resolve superiority;
negative scores are explicitly tested and preserved. Full evidence is in the
[feature report](external_libs/color-code-stim-path-gap/docs/path_gap_implementation_report.md).

## Comparative correction-origin review — 2026-09-18

The original circuit Parquet retained only the final comparative prediction and
gap, so it could not identify the colors supplying the two class minima.  The
new sidecar worker uses the external decoder's existing public `logical_value`
and `colors` controls for all six candidates; no external source was patched.
Tests and the full saved-data audit independently compare the reconstructed
baseline class and gap to the original stored outputs.  Stable shot IDs must
match one-to-one, sidecar schemas/config hashes are checked, and raw shards are
never rewritten.  Deliberate validation covers malformed shapes, identities,
summaries, and exact tie order through the six-weight reconstruction.

The 300,000-shot replay produced 600 sidecars and passed all linkage checks.
Same/different counts sum to every group and fractions sum to one.  All 156
main-project tests pass.  The observed distance dependence is descriptive;
it does not prove a preferred aggregation or a relationship between SWIM and
the comparative gap beyond the existing stored-pair semantics.

## Three-color selection analysis review — 2026-09-16

Reviewed the new aggregation layer independently from its notebook assembly.
Tests verify all four formulas on deliberate branch values, source-frame
immutability, stable identities, ordinary failure-label association, invalid
colors/nonfinite inputs, and exact reconstruction of the stored selected-color
score. Every strategy writes separate artifacts and uses the existing plot
statistics. The complete main-project suite passes 155 tests. The 300,000-shot
notebook execution completes without importing or calling a simulation entry
point.

Interpretation remains bounded: minimum, maximum and mean are post-hoc proposed
scores. Their empirical curves do not prove decoder optimality, calibration,
or a relation to the full comparative/logical gap. The ordinary selected color
and hard prediction are never recomputed. No theoretical blocker is resolved by
this analysis, and no production aggregation rule is adopted.

## Plot-rounding follow-up review — 2026-09-16

Checked that optional rounding is applied to actual score copies before counts,
fits and thresholds, with whole rounded ties for both metrics and unchanged
failure-label associations. None retains the prior numerical behavior; explicit
histogram bins remain explicit. Rounded artifacts have distinct filenames.
Twenty-one targeted tests pass, including decimal/negative precision, more than
64 rounded groups, independent expected counts, fit inputs, palette positions,
marker paths and alpha. The three notebook plot cells pass on saved data with
None and 1; no new simulation runs. The signed scatter was visually checked.
No mathematical claim, decoder change or new confidence aggregation is introduced.

## Surface-code companion review — 2026-09-16

Separate same-agent review, supported by independent numerical oracles; not
external peer review. The requested surface workflow is confined to
`surface_code_test/`. Key findings:

- The upstream example's logical labels can lie on internal edges. A checked
  spanning-forest detector-row gauge is necessary before imposing the extra
  logical-parity row. The forced bit must include potential dot syndrome.
  Eight exhaustive tiny gauges and six actual integer-program solves pass.
- Complementary gap uses the same merged ordinary graph, original weights and
  hard decisions as swim. It uses no actual observable and is not the color-code
  comparative-decoder alias or a summed-class posterior gap.
- The physical d=5/10/.001 circuit exactly matches the frozen example. The
  original parser's approximation/filtering is retained, not silently repaired.
  The generic metric uses the example's split X boundaries and passes an
  independent interval reference. All-shot hard invariance is mandatory.
- Original float scores are retained; dB is display-only. Postselection groups
  exact raw ties before display conversion. All-zero-failure log plots are
  handled explicitly; zero rows/intervals are retained in tables.
- 29 tests, the 6,000-shot raw/source audit, 750-shot replay and ten-cell notebook
  execution pass. All external sources remain clean and unchanged.

No blocker remains for this closed-memory companion. Rare failures (8,1,0 at
d=3,5,7) limit the validation plots; no confidence-method ranking is asserted.
Growth remains uncertified and windows are unsupported. See the
[validation report](surface_code_test/VALIDATION.md) for source identities,
commands, runtime, completed run and detailed limits.


## Closed-memory implementation adversarial review — 2026-09-16

Method: separate same-agent review after implementation, source inspection,
independent GF(2)/brute-force/interval oracles and saved-shot replay. This is not
external peer review. The requested closed-memory implementation is now
complete; earlier production deferrals below are historical within this scope.

| Item | Finding and disposition |
|---|---|
| Actual model | Public H2/L2, source probability/sort maps and physical/virtual metadata are validated, with exact incidence round trips and source observable factorization. No coordinate-derived logical labels. Existing effective-model filtering/correlation limits remain. |
| Floating probability identity | Upstream singleton odd-parity formula can differ from the source probability by ~2.8e-17. Validation reproduces its formula; actual hard weights are never replaced. |
| No opposite class | Review caught unnecessary analysis topology construction. Fixed before final suite: explicit no-class status, infinity, no witness and no cut/cover. |
| Cut/cover gate | Internal balance is cached, never presumed from termination. Synthetic odd cycles trigger the cover; same-base endpoints are mandatory. All nine actual small graphs pass; this is not a family-wide theorem. |
| Coverage order | Radii are mapped to original constrained rows; absent data fail. Residuals are computed before cut/cover. Fully covered odd mechanisms keep labels and can supply zero-cost witnesses. Independent interval/native residual comparisons pass. |
| Growth enabling pair | The generic backend's dummy (b_star,b_star) pair only enables radius export. Its zero score is discarded; no logical shortcut enters the analysis graph. |
| Hard invariance | Frozen public-matrix replay must match the ordinary hard path exactly. All 6,000 shots preserve prediction, weight, selected color, correction and failure label; repeated/reordered/empty tests pass. Extra replay overhead is explicit. |
| Paired experiment | One physical sample per batch; comparative representation mapping and forced-bit independence are tested. Separate decoder failure labels remain on 22 disagreement shots. |
| Reproducibility | Full 24-shard audit, source/model archives and external state pass; one 250-shot saved batch per distance replays exactly. Both external repos remain unchanged. |
| Scientific interpretation | Exact minimization of the defined residual objective does not certify the exported growth. Certification stays false. No LLR, exact full gap, posterior fit, universal balance or threshold result. |

Final tests: 362 Python passes, two existing skips; 95 unchanged C++ passes.
All 98 new circuit tests and end-to-end gates pass. Full diagnostic and run
report: [notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md](notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md).
No unresolved blocker remains for this bounded closed-memory scope. Retained
limitations are uncertified growth, effective DEM filtering/correlation loss,
frozen-matrix replay cost and unimplemented open temporal boundaries. Next task
is separately authorized sliding-window/open-temporal-boundary integration.


## Circuit-level theory adversarial review — 2026-09-12

Reviewed [Part II](notes/support/circuit_level_theory.tex) after drafting,
separately from the derivation pass. Method: same-agent rederivation, explicit
counterexample construction, current-source inspection and independent
exhaustive subset/Stim oracles. This is **not external peer review**. The
following findings supersede older circuit-level deferral statements only for
the authorized theory package. Production integration remains deferred.

### Findings and the fifteen requested checks

| Check | Adversarial finding and disposition |
|---|---|
| 1. Effective versus original DEM | The quotient is exact for the retained effective D,L, and the hard frame agrees only under the checked manager source map. Original correlated likelihood is not preserved by assumption. |
| 2. Compression labels | Paper full-target compression includes observables. Detector-only compression of two parallel mechanisms with labels 0,1 would erase their odd kernel vector. The code fallback uses full keys but overwrites duplicate source lists: .1 and .2 give .2 rather than .26 in the reproducer. Record this domain limit; no external patch. |
| 3. Filtering minimum/quotient | Two identical three-detector columns with labels 0,1 have an odd invisible sum. Removing both annihilates the logical image. Filtering therefore cannot be called logically equivalent to the full model. |
| 4. X/Z statistics | Circuit-level depolarizing replacement reproduces sector marginals within its probability domain, but discards cross-sector dependence. It also has a ≤1e-15 cutoff. A predicted stage-1 fiber is not an independent physical noise distribution. |
| 5. Temporal half-edge labels | First/final record equations and the final observable supply labels. An ancilla measurement flip can have two time-separated detectors and no observable; a final data flip can affect the observable and become a stage-2 half-edge. Coordinates or surviving row type alone are insufficient. |
| 6. Artificial boundary shortcuts | Completing every half-edge at b_* preserves ker D by handshake. Logical labels must survive. No artificial sheet-changing or terminal-joining zero edge is added. Zero-detector odd loops are real retained mechanisms, not fabricated shortcuts. |
| 7. Virtual checks | v_N is a constrained stage-1 prediction, indexed by a restricted target set. It is not a new measured check. Its entire coordinate provenance is retained; no physical location is guessed. |
| 8. Cut encodes all chains | Proved under internal-cycle balance by an explicit potential and boundary incidence identity. A general correlation-surface drawing supplies neither this condition nor matching endpoints. Universal geometric cut remains open. |
| 9. Hidden odd cycle | Odd triangle joined by a weight-10 bridge has phi=3 but boundary-rooted cover distance=23. Boundary-only search is rejected unless the cut hypothesis holds. A covered odd cycle additionally shows why unlabelled contraction loses zero-cost logical witnesses. |
| 10. Cover and free boundaries | Full even incidence is equivalent to zero real incidence; all invisible supports decompose into cycles, one odd. Minimize opposite sheets over the same base vertex, then over all vertices. Arbitrary cross-sheet multisource endpoints fail on a single labelled internal edge. |
| 11. Contraction transport | Residuals are computed once on the declared original metric and copied by mechanism ID. Cover contraction occurs on lifted covered components, or all zero-cost labelled edges are retained. Boundary splitting preserves certified coverage using r_s≤distance(s,b_*); arbitrary production growth does not automatically commute. |
| 12. Phase-1 limit | One data-X layer before ideal extraction gives first-layer Hq, later zero detector differences, final side label, and exactly the physical c-edge virtual rows. Weights and coverage are explicitly identical. Multiple noisy layers, zero-probability columns kept at finite cost, or independently chosen duals are excluded from this equality. |
| 13. CNOT schedule | DEM algebra/cover need no particular schedule. Readout witness needs the stated final detector identities and retained readout effects. Local prism/correlation-surface identification and model columns depend on the circuit schedule. No all-schedule geometric isomorphism is proved. |
| 14. Family restriction | All-distance static reduction/readout witness use the audited odd-distance triangular 6.6.6 family. The matrix quotient and graph algorithms hold for any supplied finite one-observable graphlike model; they do not identify its physical meaning without a source map. |
| 15. Open future boundary | Removing future detector rows enlarges the kernel and can add temporal logical or escape classes. The closed-memory observable and Phase-1 reduction cannot be carried into sliding windows unchanged. No sliding-window rule is derived. |

Additional source issue: the code filters mechanisms before restricted
probabilities are accumulated, unlike paper Algorithm 1. An error with one
non-c and two c targets contributes to the paper's restricted model but not
the code's. The reproducer has p1=.1 versus paper p1=.26. This can change
stage 1, so the final algorithm explicitly consumes the unchanged actual hard
matrices and does not silently substitute the paper reference construction.

### Formal claim inventory and independent reasoning

| Label | Status/class | Review argument |
|---|---|---|
| `def:cl-dem` | Direct adaptation of Stim/DEM definitions | Typed binary target maps; offsets and repeated targets are parity-normalized; separators remain event grouping. |
| `def:cl-stage2` | Direct adaptation of Lee Algorithm 1 | Explicit retained columns, constrained physical/virtual rows, weights and padding. |
| `prop:cl-faithful` | Our derivation | Basis labels unchanged; full-target XOR projection intertwines B,L. Explicit filtering counterexample establishes limits. |
| `thm:cl-quotient` | Standard linear-algebra adaptation | Kernel/image first-isomorphism proof and annihilator/rank criterion, valid on every nonempty affine fiber. |
| `prop:cl-memory` | Our derivation using Phase 1 | Final readout effects contain the static side-path witness for every d,T under explicit retention hypotheses. |
| `def:cl-complex` | Proposed algebraic complex with proved pairing | Choose basis of R; DA_R=0 and A_R^T lambda=0. No claim that R has a local-cell basis. |
| `prop:cl-product` | Direct tensor-product adaptation, proof supplied | Explicit interval augmentation, inclusion, path homotopy and characteristic-two cancellation; no metric isometry follows. |
| `def:cl-swim` | Proposed circuit extension of established swim objective | Domain is Dz=0,Lz=1 with transported nonnegative residual costs; empty minimum is infinity. |
| `lem:cl-boundary` | Our derivation | Missing boundary row is sum of all real rows, including loops and parallel edges. |
| `thm:cl-cover` | Standard voltage-cover adaptation with our DEM proof | Walk sheet parity; odd cycle in any even odd-labelled support; projection reduces repeated edges; both inequalities prove optimality and witness. n searches, not one. |
| `thm:cl-cut` | Our conditional derivation | Fundamental-cycle test yields potential. Gauged half-edge label equals terminal incidence on kernel; contained-path proof. Internal odd cycle proves necessity for this boundary-only construction. |
| `cor:cl-gauge` | Direct cochain adaptation | Detector coboundary vanishes on kernel; explicit cover sheet permutation; costs kept fixed. |
| `thm:cl-transport` | Graph-metric adaptation of Phase 1/Meister | Endpoint-entry interval proof, subdivision XOR labels and cover-component lifting retain all logical information. |
| `thm:cl-gap` | Adaptation of Phase-1 covered-weight proof | Edge-disjoint trails permit shared vertices; odd-cut loads imply covered cost≥Y. Exact equality kills base residual; XOR and fundamental minimum finish proof. |
| `thm:cl-limit` | Our controlled-limit derivation | Explicit fault effects, virtual-row and qubit-column bijections; Phase-1 side parity and identical edge coverage give metric equality. |

The algebraic record/correlation pairing is the composition identity
`L=P_obs A_rec`. Its physical pullback needs a fault lift with matching
logical and detector identities. A compression source membership vector is
not such a lift. The inspected geometric literature does not discharge this
extra hypothesis for Lee's whole compressed model. The source registry
previously named a nonexistent circuit TeX file; that source now exists and
is integrated into the user's note.

### Supporting checks and acceptance boundary

The finite script `notes/support/check_circuit_theory.py` uses a Gray-code
exhaustive subset oracle, a heap cover solver, a spanning-forest cut gate,
GF(2) rank checks and Stim's count-minimum search. Results: 400 random tiny
labelled multigraphs, 211 valid cuts, gauge and integer residual checks;
all-color Phase-1 graphs at d=3,5,7; six fully enumerated d=3 measurement-noise
DEMs at T=1,2 (1024 or 8192 subsets each), with logical-source-map identity and
compatible Stim comparisons; explicit boundary-source, wrong-sheet-endpoint,
zero-logical-cycle and source-discrepancy reproducers. Integer graph weights
and binary parity are exact; library probability comparisons are floating
sanity checks. This is not a production certificate test.

A separate matrix-only full circuit-noise example at d=3,T=2 has 23 completed
vertices and 49 retained mechanisms per color. Its unit-cost cut and cover
both give 2; it was **not exhaustively enumerated**. This is a retained-model
fact, not a physical distance claim. No Monte Carlo shots were generated.
No universal cut theorem is inferred from these examples.

**Accept the circuit-level theory package within its stated conditions.**
The general graph fallback, exact controlled reduction, conditional gap theorem
and executable metadata contract meet the prompt's completion criteria. The
stronger unresolved issues remain explicit: local prism/fault-complex lift,
universal geometric cut for all schedules, production certificate extraction,
and arbitrary mixed-sector/compression compatibility. Production hard invariance
is a specified future gate, not a test claimed to have passed in this theory
run. Both external repositories remain unchanged. Stop at theory handoff.

---

Audit date: 2026-09-12. Phase-1 Tasks 1–7 second-pass audit of
[the integrated manuscript](notes/note.tex), primary sources, and all six state files.

Method: a separate same-agent pass after integration, with the purpose of
finding counterexamples and checking citations. This is not independent
external peer review. Findings below were written before applying the
second-pass editorial/citation repairs. Finite checks are supporting
evidence; the general proofs were rederived separately.

## Findings recorded before repairs

| ID | Finding | Required disposition |
|---|---|---|
| P1-01 | The Sparse Blossom draft citation points to §3.2, but its signed singleton dual is in §2.5.2, p. 8, Eqs. (4)–(6). | Correct location; retain the distinction between signed backend potentials and nonnegative odd-cut radii. |
| P1-02 | The implementation bibliography originally listed only graph_builder.py, although the integrated text also cites _decode_stage2. The long literal API call overflows the PDF margin. | Add the decoder source path/lines and break the API presentation. |
| P1-03 | Older state documents and notation introduction still say Tasks 6–7 are deferred. | Synchronize current state; preserve dated history as history. |
| P1-04 | Research-log wording remains in the integrated §6/§8 introductions and several theorem captions. | Remove task labels and redundant setup while preserving definitions/proofs. |
| P1-05 | An arbitrary merged component must not be lifted wholesale. Only covered physical edge portions agree under the normalized radius bound r_u≤distance(u,B). | Verified in Proposition prop:dual; recompute connected components on the resolved graph, including separate terminal contacts. This is not unrestricted growth commutation. |
| P1-06 | Meister's vertex-disjoint path convention is too restrictive for a general feasible stage-2 chain. | The separate half-edge pairing proof in lem:coverage uses edge-disjoint trails, permits shared vertices, and counts every syndrome endpoint once. No assumption that minima have degree≤2 remains. |
| P1-07 | Endpoint cluster IDs do not determine uncovered edge length. A long edge can have endpoints in the same cluster through another route. | Formula eq:partial and subdivision proof are necessary. The triangle sanity case retains the long edge's weight while the alternate route has zero cost. |
| P1-08 | A shortest empty quotient route when both terminals contract must still have a physical logical witness. | thm:swim retains original terminals and expands a path inside the cluster; degree-two subdivision parity restores whole physical edges. |
| P1-09 | The new representative bound would fail for a nonoptimal feasible dual or omitted growth data. | Require Y_c=weight(f_c); explicit d=3 zero-dual counterexample has gap 1 and swim 3. Never substitute zero radii for missing data. |
| P1-10 | The small support script is not a PyMatching integration or a performance study. Explicit dual enumeration is exponential, despite near-linear metric postprocessing. | State both costs and keep production extraction/calibration open. |
| P1-11 | Online Kishi HTML served a different manuscript date from the retained v1 PDF. | Cite the actually inspected February 2026 v1 PDF for theorem numbering; do not silently mix revisions. |
| P1-12 | The full decoder gap and a class probability sum have different feasible sets/objectives from the fixed-fiber representative gap. | Keep the class-sum formula and explicit Phase-2 scope; no probability calibration or aggregation claim. |

## Resumed-run findings recorded before final repairs

The interrupted run had already integrated the mathematics and written the
first audit above, but STATUS, AGENTS and the bibliography were stale. A
fresh same-agent read and execution on 2026-09-12 found:

| ID | Finding | Required repair |
|---|---|---|
| P1-13 | Four locally retained primary sources were cited in TeX but missing from the active bibliography; later-source entries still described incomplete earlier reads. | Complete edition-specific source/assumption comparisons and availability ledger before declaring completion. |
| P1-14 | The support script computes the second shortest path with all-pairs Floyd–Warshall, although the review says it verifies the two-Dijkstra algorithm. It does not inspect a returned physical witness or test disconnected inputs. | Exercise the actual second heap search and edge-labelled predecessor witness against the independent subdivision oracle; add the disconnected case. |
| P1-15 | Sparse Blossom §2.5.2 also explains on pp. 10–11 why its metric-path-graph growth avoids negative singleton radii. Citing only unrestricted signed potentials could imply this is impossible for the actual backend. | Include that qualification; retain the unimplemented boundary-normalization/export obligation, not a claim that PyMatching radii must be signed. |
| P1-16 | The search finds Dincă–Chan–Benjamin's explicit fractional-edge swim definition and Chen et al.'s instrumented PyMatching construction for RP2 cultivation, beyond ordinary planar memory. Smith–Brown–Bartlett also discuss an exclusive UF cluster gap. | Inspect originals, document overlap and differences, and cite the directly overlapping constructions. Do not claim that instrumentation or nonplanar soft output is new here. |
| P1-17 | P1-03 contains the self-contradictory phrase that §8.3 is an incorrect locator but is §8.3. | Retain the stale-state finding; remove the erroneous locator allegation. |
| P1-18 | Floating-point LP checks support the proof but are not exact rational certificates. | Document tolerances and package versions; distinguish exhaustive support enumeration from exact LP arithmetic. |

No counterexample was found to the stated fixed-fiber topology, interval
lifting, odd-cut coverage lemma or certified representative inequality.
The second-pass checks explicitly allow shared vertices in trail decompositions,
both-terminal contraction, zero original lengths, and multiple dual optima.

## Exhaustive formal-claim classification

“Imported directly” means the named definition is transcribed into the
project's notation. “Straightforward adaptation” means an explicit
translation/restriction. “New derivation” means a proof supplied here,
not a claim of literature priority. No theorem-level item is unresolved.
The classification below includes every Definition, Lemma, Proposition,
Corollary, and Theorem; remarks are counted for the printed numbering.

| Claim | Class | Independent check / source |
|---|---|---|
| Definition 1.1 (def:physical) | Straightforward adaptation | Lee §2.1, boundary colors; explicit degree-two corner qualification. |
| Definition 1.2 (def:checks) | Imported directly | Lee Eq. (1), Bombín Eq. (1); binary support notation and HJ=0 checked. |
| Definition 3.1 (def:coords) | Straightforward adaptation | Author coordinate realization fixed as family definition; face polygons and rotation checked symbolically. |
| Definition 3.2 (def:local) | Straightforward adaptation | Typed incidence sets of the specified physical family. |
| Lemma 3.3 (lem:incidence) | New derivation | Both qubit residues, side-loss tests, edge lists, all corners, color rotation, d side count; rank/incidence checks through d=11. |
| Definition 4.1 (def:stage1) | Imported directly | Lee §3 Definition 1; physical c edges label restricted edges. |
| Definition 4.2 (def:stage2) | Straightforward adaptation | Lee §3 Definition 2 with explicit labels and proved missing-object conditions. |
| Definition 5.1 (def:classes) | Straightforward adaptation | Partition names encode incidence deficits, not physical connectivity. |
| Lemma 5.2 (lem:dangling) | New derivation | Incidence table excludes (0,0) and multiplicities; dangling iff count sum one. |
| Proposition 5.3 (prop:classification) | New derivation | Missing face iff closed c side; missing edge iff opposite corner; edge bijection gives counts. |
| Proposition 5.5 (prop:merging) | New derivation | Sum of separate endpoint rows, with provenance retained in labels. |
| Definition 6.1 (def:resolved) | Straightforward adaptation | Lee A.3 two retained boundary labels plus proved side/corner incidence. |
| Definition 6.2 (def:quotient) | Straightforward adaptation | Explicit labelled graph quotient identifying only terminals. |
| Lemma 6.3 (lem:connected) | New derivation | Red face descent decreases n, base reaches b0; every edge vertex and corner leaf attach; rotation handles other colors. |
| Definition 6.4 (def:chains) | Straightforward adaptation | Binary incidence and relative vertex quotient have explicit domains. |
| Lemma 6.5 (lem:quotient) | New derivation | Check each edge basis vector under endpoint identification, then delete terminal rows. |
| Proposition 6.6 (prop:optimization) | New derivation | Weight-preserving edge bijection and equal real constraints; parity-constrained d=3 counterexample checked. |
| Definition 7.1 (def:physicalmap) | Straightforward adaptation | Lee A.1 edge/hyperedge basis inverse on all chains; Tc and ordinary inverse are typed separately. |
| Lemma 7.2 (lem:linearity) | New derivation | Basis linearity; pure-sector commuting Pauli factors cancel exactly. |
| Definition 7.3 (def:syndromemap) | Straightforward adaptation | Lee A.1/A.3 factorization expressed on real physical coordinates, including auxiliary Mc. |
| Lemma 7.4 (lem:syndrome) | New derivation | Non-c face partition into c edges proves HTc=Lambda Dc on every basis vector; checked all finite samples. |
| Proposition 7.5 (prop:paths) | New derivation | Walk incidence telescopes modulo two; Lambda gives physical endpoints; no logical conclusion used. |
| Definition 8.1 (def:equivalence) | Straightforward adaptation | Physical equivalence restricted to K; denominator is intersection, not all physical stabilizers. |
| Lemma 8.2 (lem:sideparity) | New derivation | Terminal row equals physical Qc overlap; k=1 and independently known side Z replace arbitrary logical Z by stabilizer difference. |
| Theorem 8.3 (thm:logical) | New derivation | Nonzero logical-Z pairing has kernel SX on ZX; handshake gives beta; connectivity provides a nonzero image. No cycle-basis premise. |
| Corollary 8.4 (cor:representatives) | New derivation | Odd-degree endpoints lie in one support component; remove contained simple path; claim is class-level, not every physical support in K. |
| Definition 8.5 (def:facemap) | Straightforward adaptation | Canonical inverse image of real non-c face stabilizers, no invented two-cells. |
| Proposition 8.6 (prop:facebasis) | New derivation | Inclusion from HJ=0 and Mc parity; independent real face supports from k=1; exact family count equals connected graph cycle rank. |
| Definition 8.7 (def:complex) | Straightforward adaptation | Delfosse binary-complex convention; all three chain-map identities explicitly checked. |
| Proposition 9.1 (prop:meister) | Straightforward adaptation | Meister §II.B.1 structure verified only after physical topology; effective checks Dc differ from H. |
| Corollary 9.2 (cor:pathcost) | New derivation | Every beta-one chain contains a path; nonnegative weights allow removal. |
| Definition 10.1 (def:dual) | Straightforward adaptation | Meister radius formula with Edmonds–Johnson nonnegative odd-cut dual and explicit free-boundary constraints. |
| Proposition 10.2 (prop:dual) | New derivation | Metric closure with one matching boundary, even T including boundary iff needed; expand/reduce T-joins; odd-cut shore normalization; radius cannot grow positively past boundary. |
| Definition 10.3 (def:clusters) | Straightforward adaptation | Meister Definition 1 on resolved metric; selected optimal dual supplies radii, terminal points not merged. |
| Definition 11.1 (def:contraction) | Straightforward adaptation | Meister Definition 9/Appendix B interval quotient with physical labels retained. |
| Lemma 11.2 (lem:metric) | New derivation | Every route to an interior point enters via an endpoint; interval union gives clipped sum; subdivision/contraction/suppression preserve distance. |
| Definition 11.3 (def:swim) | Straightforward adaptation | Meister logical shortest distance applied to the proved color-code quotient and specified clusters. |
| Theorem 11.4 (thm:swim) | New derivation | Contained path theorem identifies minimum; cluster expansion preserves original boundary; new degree-two vertices enforce whole-edge binary lifting. |
| Lemma 12.1 (lem:coverage) | New derivation | Rebuild Meister Lemmas 11–12 with half-edge pairing, one endpoint per defect, edge-disjoint trails, free terminal endpoints and odd-cut counting. |
| Definition 12.2 (def:gap) | Straightforward adaptation | Minimum-representative comparison within one Dc fiber; opposite class measured relative to actual fc. |
| Theorem 12.3 (thm:gap) | New derivation | Covered cost≥Y=base cost; base uncovered cost zero; opposite XOR is beta one, so outside cost≥phi. No noise or square-lattice premise. |

## Independent rederivation and boundary of acceptance

The old results were rederived in dependency order: local incidence →
resolved connectivity → exact physical syndrome map → physical side
overlap → logical quotient → non-c face basis. The k=1 physical input
is independent of graph cycles. The bare relative graph still has
dimension t(t+1)+1, while the induced physical quotient has dimension
one. The physical c-side support need not lie in K_c; physical c-face
stabilizers need not preserve a fixed stage-1 auxiliary fiber.

The new dual reduction uses a complete graph on syndrome vertices and
one matching boundary, with odd set T augmented by that boundary iff
the syndrome cardinality is odd. Complementing cuts to exclude the
boundary produces exactly the displayed dual; it does not add a
physical edge. Edmonds–Johnson pp. 93–95 supply integrality and the
nonnegative dual. This closes existence, rather than merely assuming
that an arbitrary Blossom backend exports compatible radii.

Metric coverage was independently derived by entering an edge interval
through either endpoint. Quotient lifting retains all original chain
incidences, including zero-length physical edges. The coverage lemma
requires only edge-disjoint trails, which can share vertices. At each
odd cut at least one endpoint pair crosses; boundary-ended trails
supply precisely the radius constraint. Strong duality makes every
optimal correction's uncovered cost zero, and applying the physical
logical-path theorem to the XOR supplies the gap inequality.
This repairs the two source-transfer obligations rather than importing
Meister's surface-code theorem verbatim.

Unnumbered claims also checked: Lee's two-round validity is conditional
on feasible rounds; Dc surjectivity follows from connectivity; the
side/string comparisons are class-level; UF is a separately specified
growth convention with parity-feasible covered components; the
two-Dijkstra radius algorithm uses a temporary source only for distance
computation. No history-dependent UF/MWPM equivalence is asserted.
Near-linear postprocessing excludes dual extraction; the explicit LP
fallback has exponential representation size.

## Finite supporting checks

[check_phase1.py](notes/support/check_phase1.py), Python 3.12.7, NumPy 1.26.4 and SciPy 1.13.1:
15 family/color incidence and rank checks at d=3,5,7,9,11; all 128
physical supports at d=3 in all colors; 144 complete fixed-fiber
instances across unit, nonuniform positive, and zero-containing weights.
Every optimal dual value equalled the exhaustive optimum; every
representative inequality and covered-weight inequality passed.
Independent all-pairs interval subdivision agreed with the heap-based
two-pass metric. Partial coverage, merged/both-terminal clusters,
same-cluster endpoint and nonoptimal-dual counterexamples passed.
Heap predecessor paths were also checked for zero physical syndrome and
nontrivial physical logical class in every tested fiber; disconnected
terminals return infinity without a witness. These are deterministic finite
checks, not calibration data. Support enumeration and binary ranks are
exact; the HiGHS LP and metric comparisons use floating arithmetic with
1e-8 tolerances, not exact rational certification.

## Final disposition after repairs

**Accept Phase 1 within its stated hypotheses.** The resumed-run findings
P1-13–P1-18 and earlier P1-01–P1-12 have been addressed. The note remains
one continuous development with 41 formal claims, all classified above.
The final source pass corrected Smith's locator to Appendix E in the
retained v1 PDF and used Chen's §VI/Fig. 12 page locations rather than
HTML equation numbering. New source comparisons do not import their
performance claims or identify their region data with our certificate.
The stale reserved-phi statement in NOTATIONS was also removed.

The final 25-page PDF compiled twice without warnings, undefined
references/citations, or overfull/underfull boxes. A label/citation scan
and claim-count comparison passed. The dual, physical-lifting and
representative-bound pages were visually checked. The support script
passed with the additional actual heap path and disconnected tests.
All active source assumptions agree with the six state documents;
historical audits below retain their original, explicitly dated scope.

Consistency checks: Lee's two graph bijections and conditional validity
are preserved; physical boundary strings agree with the incidence table;
Delfosse's projection and Kubica's unfolding remain different maps;
Meister's metric objective is adapted only after topology is proved,
and its analytical argument is rederived with exact dual and path
hypotheses. None of these sources is cited as proving the project's
fixed-color physical parity identity. Completion does not close the
implementation or later-phase concerns listed next.

## Retained open concerns

- The external PyMatching backend has not been instrumented to export
  this certificate. A companion exact dual solver is a defined
  alternative, not evidence of negligible overhead.
- Exact theorem hypotheses do not automatically apply to floating
  residual tolerances, signed solver potentials, reweighted/correlated
  matching, missing cluster information, or circuit-level DEM edges.
- No UF representative-gap inequality is proved.
- No summed logical-class LLR bound, physical stage-1 success assertion,
  three-color aggregation theorem, full comparative/forced gap bound,
  or novelty claim is established.
- Generalized boundaries, other colex families, circuit noise and
  numerical calibration remain outside Phase 1.

The following Tasks 4–5 review is retained as a dated historical audit.
Its “next” and “open” statements describe that earlier checkpoint and
are superseded by the Phase-1 findings above.

---

# Historical Tasks 4–5 review

Audit date: 2026-09-12. Reviewed the extended [note](notes/note.tex),
all six state files, and the proof-critical primary source passages.

Method: a separate adversarial pass after drafting Tasks 4–5, by the
same agent. It sought counterexamples to the theorem and to stronger
unstated claims; it is not external peer-review certification.
The proof was checked symbolically across the defined family, not by
a finite simulation or performance experiment.

**Disposition: Tasks 4 and 5 accepted in the exact fixed-stage-2 scope.
Cluster construction and analytical transfer remain open.**
Prior audit details are preserved in
[the historical program](notes/deferred_proof_program.md).

## The 13 requested adversarial checks

| Question | Finding and evidence |
|---|---|
| 1. Are all chain groups and maps defined? | Yes. G_c, partial_c, rho_c, D_c and T_c retain their typed Tasks 2–3 definitions. Definition 8.7 specifies both maps of the induced complex and the full chain-map triple to the physical complex. |
| 2. Is the stabilizer quotient correct? | Yes. It starts with K_c intersect T_c^{-1}(S_X). Theorem 8.3 proves equality with closed graph chains, and Proposition 8.6 independently identifies the canonical non-c physical face basis by inclusion, independence and dimension. |
| 3. Are corners handled? | Yes. Q_c includes both side corners, while the opposite corner alone gives b_c^1. The incidence identity and family counts include all three. No additional boundary generator is omitted. |
| 4. Could a terminal path be a stabilizer? | No. It has beta=1 and therefore odd commutation with the known physical logical Z on Q_c. Every physical stabilizer commutes with that Z. |
| 5. Could a nontrivial logical lack a representative? | Not in the one-qubit class: connectivity supplies a terminal path whose physical class is nonzero, so every nonzero physical class equals it. However not every individual physical support is itself in K_c; Q_c is an explicit counterexample to that stronger claim. |
| 6. Could a closed resolved cycle be logical? | No, closed incidence gives beta=0 and the one-qubit physical parity detector then makes its class zero. This applies to arbitrary binary closed chains. A merged-graph cycle can instead be logical after lifting; the theorem uses the resolved graph. |
| 7. Is the proof circular? | No. It imports the physical side logical and k=1, proves terminal overlap from the pre-existing incidence classification, and only then concludes the graph theorem. The non-c face generation proof follows that theorem; it is not used as its premise. |
| 8. Does it depend on one drawing? | No. The parity identity uses the proven all-distance incidence classification. The cycle-basis count uses symbolic t, exact face/qubit/edge counts and connected incidence rank. |
| 9. Does it cover the intended family? | Yes, the explicit standard triangular 6.6.6 family at every odd d≥3. It does not claim all triangular 2-colexes or boundary types. |
| 10. Is stage-1 virtual syndrome irrelevant? | Its numerical value does not enter K_c or the proof, so all fixed real-syndrome fibers have the same topology. The fiber restriction is essential: true physical errors need not have the predicted auxiliary parity. This limitation is explicit in §8.3. |
| 11. Is global two-toric-code equivalence overused? | No. No local Clifford or folded-layer map is used to prove the result. |
| 12. Is projection conflated with concatenated matching? | No. The proof uses T_c and Lambda_c, while Delfosse's restricted projection remains a separate source construction. |
| 13. Is Meister invoked only afterward? | Yes. The independent color-code proof, physical generators and converse precede §9. Its proposition identifies fixed-stage-2 topology, not the full physical decoder or source probability bounds. |

## R-029 — Physical parity detector and proof sufficiency

**Resolved.** The missing argument was the exact identity between incidence
at b_c^0 and physical overlap with Q_c. Q_c is independently known to
support logical Z. Since the code has one logical qubit, that parity
detects the whole pure-X logical quotient. Replacing Q_c by any other
nontrivial logical-Z representative changes it by a physical stabilizer,
which has zero pairing with every T_c z of z in K_c.
No guessed surface-code geometry enters this argument.

## R-030 — Strong converse versus arbitrary physical representatives

**Resolved by the correct domain.** The proven isomorphism is
K_c/R_c to the physical logical quotient. The tempting statement
“every nontrivial physical support is a relative graph chain” is false.
The logical X on Q_c has H Q_c=0 but M_c Q_c nonzero.
The other two physical side representatives are simple terminal paths;
all nontrivial physical classes can be deformed to them.
The note explicitly separates class representation from a given support.

## R-031 — Full physical stabilizers versus fixed-fiber cycles

**Resolved.** The non-c real faces form an independent basis of the
resolved cycle space. Their inclusion follows from HJ=0 and even c-edge
parity; the rank follows from n, face and edge counts plus physical k=1.
The dimension is t(t+1), with two such generators at d=3.
A c-face stabilizer is outside K_c, since otherwise independence would
express it in the non-c face span. Thus dropping the fixed-fiber
intersection would give a false cycle characterization.

## R-032 — Relative homology and physical relations

**Resolved with an explicit induced complex.** Bare-graph relative H_1
equals K_c, of dimension t(t+1)+1; at d=3 it is three-dimensional,
not the one-dimensional physical logical quotient.
Definition 8.7 adds precisely the canonical non-c physical-face map
A_c and proves its image, producing the right H_1. No arbitrary
two-cells are chosen merely to force a desired answer, and no geometric
CW realization is asserted.

## R-033 — Scope of the Meister correspondence and weights

**Resolved structurally; growth and bounds remain deferred.**
The graph's effective parity map is D_c, including auxiliary edge rows,
not H. The proved logical structure matches the relevant modified-graph
requirements on relative differences. It does not identify an entire
surface-code decoder or preserve solver growth.
Nonnegative weights suffice for the unmodified path-minimum equality;
strict positivity is required for the source's later edge-length metric.
No cluster-modified cost, posterior statement or source bound is imported.

## R-034 — Small-distance and boundary checks

**Resolved within scope.** For t=1, n=7, each face color has one face,
each E_c has three edges, the resolved graph has six vertices and seven
edges, its cycle rank is two and dim K_c is three. The two non-c face
images generate those cycles, leaving one logical class.
The corner-to-side path necessarily has odd physical boundary overlap.
These are exact symbolic base-case counts, not a numerical benchmark.
The excluded d=1 patch has different incidences and is not inserted
into the theorem.

## Earlier issue dispositions

- R-001–R-003, R-023: physical logical inequivalence and cycle triviality
  are now proved on K_c; the original geometric-only caveat is superseded.
- R-004–R-005, R-024–R-025, R-028: source distinctions, typed maps and
  syndrome factorization remain valid and were rechecked.
- R-006, R-014: the bare-graph/full-stabilizer shortcuts remain rejected;
  the corrected induced complex and exact generator space are now proved.
- R-007, R-011, R-019: the selected family and corner coloring remain
  explicit; other colexes still require separate audits.
- R-008, R-020–R-021: fixed-fiber scope and recoverable edge provenance
  remain essential even though logical topology is now established.
- R-009–R-010, R-015–R-016, R-026: actual growth, metric coverage and
  analytical probability transfer remain deferred. Equal matching
  minimizer sets supply no automatic growth equivalence.
- R-012–R-013, R-022, R-027: exact edge identities, no fictitious qubits,
  separate graph feasibility and binary walk conventions remain valid.
- R-017–R-018: the latest prompt authorizes the theorem and graph
  interpretation; state and directory paths now point to Tasks 4–5.
  Initial swim proposals remain historical.

## Next review gate

No unresolved dependency was found in the stated Tasks 4–5 results.
The remaining gate is Tasks 6–7: actual decoder-growth realization,
cluster contraction, partial-edge coverage and a justified swim
construction. Source noise, path-decomposition and optimal-dual
hypotheses need separate review before any analytical bound.


## Phase-2A implementation audit — 2026-09-12

This separately authorized implementation was reviewed by a same-agent second
source/diff pass and independent executable oracles; it is not external peer
review. Full evidence and commands are in IMPLEMENTATION_STATUS.md.

| Finding | Disposition |
|---|---|
| Prototype overwrites ordinary matching weight with SO | New structured API returns separate products; legacy internal extraction keeps ordinary weights separate. Hard/weight regression passed. |
| Parallel mechanisms can be collapsed before SO | New analysis config preserves explicit labelled edges independently of the hard graph's historical merging. Duplicate edge IDs are refused. |
| Historical H2 contains inert non-c and repeated-time rows | Preserve H2; type non-c zero rows as INACTIVE_PADDING and retain physical/virtual source coordinates. All active rows have the requested semantic roles. |
| Raw radius convention is not an exact odd-cut certificate | Explicit final-defect metric-ball convention; debug radii and independent geometry checks; bound-certified flag remains false. No representative-bound validation claim. |
| Topology must survive permutations and retain physical labels | All-color d=3,5,7 boundary/provenance and permutation tests pass; independent d=3,d=5 graph/witness checks pass. |
| SO can change hard branch selection if its value replaces weight | Frozen baseline and pilot preserve every ordinary prediction, weight, selected color and failure mask. |
| Comparative circuit has an additional detector | Absolute measurement-record audit and common-record conversion establish observable-parity mapping; forced input-bit independence checked. |
| First pilot plotting failed at a zero-failure Wilson endpoint | Exact endpoint handling and tests fixed a roundoff issue; partial attempt retained, same small seeded grid rerun. No decoder gate failed. |

Final gates: 95 C++ and 238 Python tests passed across the separate final
suites, with two upstream color-code skips. The saved pilot contains 3072
unique paired shots. CSV re-audit reproduced failure counts, selected values,
bins and acceptance curves, and verified repository/script hashes.

Retained limitations: the exact dual certificate remains unexported; the
new convention is not identified with all legacy fill-region soft scores;
float roundoff/quantization is not exact certificate arithmetic; inactive-row
metadata extends the literal two-type specification to avoid false labels;
only single-round triangular data-only X / Z-memory is validated; performance
measurements are a small local pilot. No confidence calibration, full-decoder
inequality, large-scale performance result or circuit-level swim theorem is
established. Stop for pilot review before any scaling.

## Phase-2B implementation audit — 2026-09-12

Reviewed package boundaries and tested simulation/analysis independently of
the external decoder source. Existing 238 Python regression tests pass in
`color_code_so` (two upstream skips). New tests exercise deterministic parallel
rows, one-sample pairing, selected-color versus minimum aggregation, comparative
alias preservation, schema/config linkage, source archives, statistics and plots.

Statistical conventions are explicit: metric-specific failure labels; stable
shot-order exact ties; 99% Wilson intervals with counts; nonempty retained
prefixes; zero-failure exclusion from log-OLS; explicit logistic separation
statuses. No posterior calibration or certified-dual implication is inferred.
The original p-grid is unresolved and recorded as unknown rather than invented.
Published .082 and corrected README .086 are distinct comparison targets.

A real rsmf side effect was found during tests (global backend/style changes).
The style wrapper now queries rsmf dimensions in a cached isolated subprocess,
with typography applied inside rc_context. Publication PDF/PNG uses installed
TeX; CI style is explicit. A smoke gate passed 48,000 paired rows, exact counts
and same-seed replay before the moderate study was considered.

### Completed moderate-study audit

The final run results/20260912_145540_phase2a_test passes all 960 shard checks,
exactly 4,800,000 rows, source/metadata/archive checks and a full 5,000-shot replay.
Raw independent failure totals are 208,918 ordinary and 205,479 comparative,
with 33,491 paired hard disagreements. All 262 Python tests pass (two upstream
skips); the notebook executes and representative figures were inspected.
Review is by the implementing agent with independent tests/recounting, not an
external peer review.

The primary all-distance crossing minimum is p=.088 at the search endpoint:
this is an unresolved threshold, not a measurement of an 8.8% threshold.
Post hoc sensitivity restricted to d>=7 or d>=9 yields .086458 or .085660;
these checks do not replace the original estimator. Subthreshold G/C trends
are broadly compatible with the published slopes, but one observed failure at
d=13,p=.02 weakens the high-distance regression. No invariant failure indicates
a decoder change is required. Finite-size/grid/statistical limitations prevent
stronger conclusions. The final reproduction report explicitly records these
limits; no additional grid or later-phase extension was run.

## Surface path-gap v1 implementation audit (2026-09-19)

Separate same-agent review, with independent numerical oracles (not external
peer review): original merged edge IDs and incidence/weight validation prevent
using arbitrary SWIM graph IDs as correction identities. The correction is
XOR support, verified against syndrome and ordinary observable. Dijkstra only
uses nonnegative original/zero costs; full original correction weight is
subtracted afterwards and negative outputs are valid. Correction components
outside the X-terminal metric still contribute to subtraction. A disconnected
fixture distinguishes this from overlap-v2. Growth data never enter this API.

Independent simple-path enumeration and actual d=3,5,7 Bellman–Ford checks,
existing backend/main regressions, paired failure labels, signed schema and
legacy reader tests pass. Original floating correction cost is explicitly
separate from quantized backend solution weight. No theorem identifies this
heuristic with SWIM, complementary gap, or a posterior LLR. Only implicit hard
boundaries and finite nonnegative original weights are supported. The metric
uses the existing surface X-boundary topology and merged-graph approximation;
no wider topology/general-noise claim is introduced. The batch API currently
uses two ordinary deterministic solves, so no low-overhead claim is made.
See surface_code_test/VALIDATION.md for tests and bounded-run evidence.
