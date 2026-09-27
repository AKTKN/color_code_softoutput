Implement a new, modular soft-output metric in https://github.com/AKTKN/color-code-stim.git. Complete the implementation, tests, documentation, a small reproducible evaluation, and the Git workflow described below. The metric is defined here in full; do not substitute the existing swim-distance algorithm or a different logical-gap estimator.

The implementation must extend the installable package under `src/color_code_stim/`. It must use the FINAL correction returned by the decoder, after all color/logical-class selection and any predecoder/fallback/partial-correction composition. The same final correction must be used for all three metric graphs.

Repository context was checked against `main` at commit `0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`. Reinspect the current checkout before editing. At that revision:

- The source uses a `src/` layout and already depends on `python-igraph`, NumPy, PyMatching, Stim, and pytest.
- `ColorCode.decode(..., full_output=True)` returns the final prediction in `extra_outputs["error_preds"]`.
- These predictions use DEM error-mechanism ordering, not data-qubit ordering. `ColorCode.errors_to_qubits` provides an existing conversion for single-round bit-flip noise; inspect and verify its indexing before reuse.
- `tri_optimal` is the CNOT-schedule name, not a `circuit_type`. The circuit type is `"tri"`.
- The branches `phase2a/swim-distance` and `swimdistance` contain earlier work. The phase-2A implementation uses a modified PyMatching soft-output backend. This new metric must work with ordinary upstream PyMatching and must not require that backend.

Read applicable `AGENTS.md` instructions, package configuration, and relevant tests first. Treat the mathematical definition below as authoritative. Previous swim code and notebooks are references only.

Use this Git workflow:

1. Inspect the worktree, remotes, current branch, and applicable instructions. Use an existing checkout when available; otherwise clone the target repository. Preserve unrelated local changes, using a separate worktree if necessary.
2. Fetch `origin`, confirm that it points to `AKTKN/color-code-stim`, and create `feature/final-correction-path-gap` from the current `origin/main`. If that name already exists with unrelated work, choose a unique suffix. Record the base commit. Do not merge the previous swim branches merely to obtain their code.
3. Implement and test on the new branch. Inspect the final diff and stage only changes belonging to this task, including small documentation/evaluation outputs as appropriate. Do not commit generated large datasets, notebook outputs, credentials, caches, or environment directories.
4. Commit the tested changes, push the feature branch with upstream tracking, and create a draft PR against `AKTKN/color-code-stim:main`. Do not merge it, push to the default branch, force-push, or rewrite unrelated history. If authentication or network access blocks publication, complete the local implementation and commit, then report the exact remaining command and the actual blocker.

Limit the first implementation to the following explicit physical model:

- Standard triangular 6.6.6 color code, odd distance `d >= 3`.
- `circuit_type="tri"`, `cnot_schedule="tri_optimal"`, `superdense_circuit=False`, `rounds=1`, Z-memory, and independent data-qubit X errors using `NoiseModel(bitflip=p)`, with `0 < p < 1/2`.
- All other noise channels must be zero, including effective override fields. Stabilizer measurements and gates are noiseless. Verify that the generated experiment contains the intended single data-error layer; do not accidentally suppress it with initialization flags or add a second layer.
- This is the bit-flip CSS sector of the code-capacity model. Depolarizing noise, mixed Pauli sectors, noisy syndrome extraction, multiple rounds, other schedules, and other geometries are outside this initial adapter's scope and must raise informative errors rather than silently produce an incorrectly interpreted score.
- The mathematical core should accept explicit nonnegative finite qubit weights, allowing synthetic nonuniform-weight tests. This does not imply support for additional physical noise models in the `ColorCode` adapter.
- The core must be independent of the decoder that supplied the physical correction. Standard and comparative concatenated-MWPM decoding should both be usable as correction sources within the supported physical model.

Use the monochromatic-lattice notation of Lee, Li, and Bartlett, *Color code decoder with improved scaling for correcting circuit-level noise*, Definition 2 and Appendix A.3:
https://arxiv.org/html/2404.07482v2

For color `c` in `("r", "g", "b")`, the monochromatic lattice has vertices corresponding to c-colored faces and original c-colored lattice edges. Each edge of this monochromatic lattice corresponds to ONE data qubit. Keep two distinct terminals: `s_c`, the corner opposite the c-boundary, and `t_c`, the c-boundary. The c-boundary is the boundary missing c-colored checks. The corner corresponds to the intersection of the other two boundaries. Do not identify these terminals or add an artificial zero-cost link between them.

Suppress each degree-two vertex corresponding to an original c-colored edge. The resulting graph `G_c` has edges representing pairs of physical data qubits. Its initial edge from the corner represents one qubit. For every graph edge `a`, retain its immutable physical support `Q_c(a)`, of size two or one. Preserve parallel edges and their distinct supports. An equivalent unsuppressed graph with one qubit per edge is allowed if equivalence to the required pair-weight construction is established and tested.

Use physical incidence and stable IDs to construct these graphs. Do not use stage-1 syndrome-dependent pairings or stage-2 matching results to define their topology. Construct the two terminals from the physical boundary structure. Do not infer qubit identity from a mutable igraph vertex index after deletion. If redundant loops are removed, explain why they cannot improve a nonnegative shortest path.

For a final physical correction `E` and qubit weights `w_q`, define

\[
w_q=\log\frac{1-p_q}{p_q},\qquad W(E)=\sum_{q\in E}w_q,
\]
\[
\omega_c^E(a)=\sum_{q\in Q_c(a)\setminus E}w_q,
\qquad D_c(E)=\operatorname{dist}_{G_c,\omega_c^E}(s_c,t_c),
\]
\[
\phi_c(E)=D_c(E)-W(E),\qquad
\phi(E)=\min_{c\in\{r,g,b\}}\phi_c(E).
\]

For a two-qubit edge, the updated weight must be `w1+w2`, `w1`, `w2`, or `0`, depending on which of its two qubits belong to E. For the corner edge it is its single qubit's weight or zero. Subtract the weight of the ENTIRE final correction once, using the ORIGINAL qubit weights. Do not substitute the correction's overlap with the path, divide by the number of colors, subtract per-qubit costs twice, take an absolute value, or clip negative results. A negative score is a valid output.

Implement the following architecture and integration:

- Use a dedicated module, for example `src/color_code_stim/metrics/monochromatic_path_gap.py`, with a result type and public exports consistent with the repository. Keep topology construction, correction/weight mapping, and metric evaluation separable. Avoid a broad decoder refactor.
- Provide a reusable evaluator that builds topology and physical-ID mappings once, then evaluates many final corrections. Store immutable original weights separately from per-shot residual weights. Support a single correction and a batch, document array shapes, and handle an empty batch consistently.
- Use `python-igraph`'s supported shortest-path routines, or another already available mature graph package, rather than implementing Dijkstra yourself. Preserve explicit zero-cost edges. Avoid dense all-pairs shortest paths and rebuilding graph topology per shot. A target of O(n log n) time per shot and O(n) working memory is sufficient; report the actual implementation complexity.
- Return at least: `phi`, `phi_by_color`, `distance_by_color`, `correction_weight`, and `color_order=("r","g","b")`. Return the minimizing color with a documented deterministic tie rule. Make physical path witnesses available through an optional diagnostic flag, keeping unnecessary witness storage out of the default batch path.
- Expose a direct physical-qubit API and a small `ColorCode`/decode-output adapter. Prefer postprocessing after `decode(..., full_output=True)` so the final correction is unambiguous. If adding an opt-in decode flag as well, compute the score only after all final output assembly and preserve default behavior and existing outputs.
- In the adapter, read `extra_outputs["error_preds"]` and convert DEM coordinates to canonical physical data-qubit coordinates. Never use individual color candidates, stage-1 predictions, unmerged stage-2 corrections, or `best_colors` to choose which E to apply. All three graphs use the identical mapped final E.
- Recompute `correction_weight` from this physical E and the original physical weights. Do not assume `extra_outputs["weights"]` or a stage-2 matching weight is equal to it.
- Audit error-only DEM column indices versus raw DEM instruction indices, detector IDs, Tanner vertex IDs, and canonical data-qubit IDs. Reuse an existing mapping only if its contract is verified. Validate the map independently using physical check supports and logical-observable parity. Do not silently reinterpret an unrecognized array ordering.
- Keep score calculation read-only with respect to decoder state, predictions, circuit, Tanner graph, and inputs. Results must be independent of prior evaluation order. Validate shape, binary corrections, weight values, and supported configuration. If a graph is malformed or its terminals are disconnected, raise a clear diagnostic; an empty returned path must not become a spurious distance zero.

Add meaningful tests, including independent oracles:

1. Weight accounting: use unequal weights to test all four possibilities on a two-qubit edge and both possibilities for the corner. Verify subtraction of the entire original correction weight exactly once, including a corrected qubit outside the returned path. Preserve a negative score in an explicit fixture.
2. Boundary/topology: for d=3,5,7 verify distinct terminals and an odd, syndrome-free logical support for each reconstructed path. Check `H z = 0` and `logical_Z_support dot z = 1 (mod 2)` using the physical code matrices, not the metric's own graph incidence. Verify correct singleton corner accounting and a fixture where parallel edges with different residual costs must remain distinguishable.
3. Analytic checks with uniform `w`: E empty gives every `D_c=d*w` and `phi=d*w`; E equal to all qubits gives every `D_c=0` and `phi=-n*w`. For arbitrary masks, verify `d-2*|E| <= phi/w <= d-|E|`. If a known c-path support is contained in E, verify `D_c=0`.
4. Independent exact oracle: construct a small d=3 monochromatic topology from independently specified physical face/qubit incidences. Enumerate all simple terminal paths, lift their supports, and calculate `min_P sum_{q in support(P) minus E} w_q` directly for every one of the 2^7 correction masks, with uniform and selected unequal weights. Compare every color and the final score. The oracle must not call the production topology builder or production shortest-path implementation. Include at least one larger, independently checked d=5 case. Do not assert equality with the minimum over ALL logical supports: the path family is restricted.
5. Final-correction regression: construct a deterministic case where per-color intermediate candidates differ and the selected final correction comes from another color. Verify that ALL three metric evaluations use the returned final E. Include a composed/partial-correction fixture at the postprocessing boundary. Replacing irrelevant intermediate metadata must not affect the score when final E is fixed; changing final E must affect a fixture chosen to expose incorrect zeroing.
6. Mapping/integration: independently verify the DEM-to-qubit mapping, including non-error DEM instructions and nontrivial index permutations. On deterministic single-shot and seeded batch cases, verify the final physical syndrome and predicted logical parity. Test ordinary and comparative decoding without replacing their final corrections. Confirm that metric evaluation leaves hard predictions and failure labels unchanged.
7. Batch/cache behavior: single-versus-batch agreement, row permutation, empty batch, repeated calls, and E1/E2/E1 evaluation order. Confirm that originals and caller inputs remain unchanged and residual weights do not leak between shots.
8. Scope validation: reject unsupported rounds, geometry, schedules, superdense circuits, and any nonzero unsupported noise channel, including overrides; reject malformed correction arrays and invalid weights. Test disconnected/malformed topology diagnostics.

Run the new tests and the existing repository test suite. Report pre-existing failures separately using an unmodified-base comparison when needed; do not silently weaken tests. Use normal upstream PyMatching for this implementation's acceptance tests. No test should require the modified swim-distance backend.

Provide a small evaluation script or notebook that imports the implemented module rather than duplicating its algorithm. The objective is to assess this heuristic, not to demonstrate an assumed improvement. Include a quick smoke mode; larger runs must be explicit CLI/notebook parameters.

- Use identical sampled shots, final corrections, and success/failure labels when comparing scores. Compare `phi`, raw `D_min=min_c D_c`, and `-W(E)` as an ablation of the global-weight subtraction. Include the package's comparative-decoding gap only where available and label it as decoder-derived rather than exact. If comparing different hard-decoder settings, report them as separate cohorts.
- For d=3, enumerate all physical X errors to obtain exact class minima. For each syndrome s and logical label b define `m_b(s)=min{W(F): H F=s, logical_label(F)=b}`. Relative to the actual returned E, report both `Delta_class(E)=m_(1-b(E))(s)-m_b(E)(s)` and `Delta_corr(E)=m_(1-b(E))(s)-W(E)`, plus within-class suboptimality `W(E)-m_b(E)(s)`. Keep these signed quantities distinct from the nonnegative optimal-class gap `abs(m_1-m_0)` and from posterior class log-odds. In exhaustive summaries, weight error patterns by their physical probability instead of treating them as equally likely; a class gap is shared by its syndrome/class, but failure probability is not uniform over syndromes.
- Evaluate postselection by retaining shots with score at least a threshold. Report conditional logical failure versus actual retained fraction/abort fraction, conditional failure versus score, and score distributions. Use exact probability sums for exhaustive d=3 analysis and binomial confidence intervals for Monte Carlo results. Use thresholds or label-independent tie breaking for discrete scores. Do not treat zero observed failures as a known zero failure probability or drop inconvenient negative-score samples.
- Add diagnostic plots/data comparing phi with the exact small-code quantities. Rank correlation may be reported, but postselection performance is the primary assessment. At equal abort fraction compare using the same underlying shots. Do not use true errors or failure labels when calculating the metric or choosing threshold tie order.
- Make larger configurations, for example d=5,7,9 and p=0.01,0.03,0.05, configurable. Run only an inexpensive seeded smoke evaluation during this task. Do not claim statistically resolved superiority from a smoke run. Record seed, shots, configuration, decoder mode, base/implementation commit, dependency versions, per-color distances, W(E), phi, failures, and timing. Separate topology setup, decoding, mapping, and metric evaluation costs.
- The previous swim metric is an optional external comparison if already available in the environment. Do not merge another branch or make a modified PyMatching dependency mandatory to complete this task. Provide a documented way to join independently obtained legacy results by shot ID if useful.

Document the mathematical definition, supported configuration, physical ordering contract, terminal construction, input/output shapes, and a minimal runnable usage example. Explain that a path support L has

\[
W(L\setminus E)-W(E)
=\bigl[W(E\triangle L)-W(E)\bigr]-W(E\setminus L).
\]

Thus this score penalizes corrections outside the path and searches only the monochromatic path family. It is a heuristic proxy, not an established exact logical gap, posterior log-odds, or universal bound on the full logical gap. Keep this definition unchanged even if the preliminary numerical result is unfavorable.

Finish with a concise implementation report: public API and usage, final-correction mapping and integration point, changed files, test commands and outcomes, smoke-evaluation observations with limitations, branch/base/commit identifiers, and the pushed branch and draft-PR URLs or precise publication blocker.
