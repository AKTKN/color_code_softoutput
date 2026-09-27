# Monotone-Y formulation audit — 2026-09-19

Authority: `prompts/codex_monotone_y_gap_integration_prompt.md`. This audit
preceded implementation. Method: same-agent algebraic rederivation, source
inspection, and an independent coordinate/reachability prototype. It is not
external peer review. All six project state documents were inspected.

**Disposition: proceed within the specified one-round physical scope.** No
counterexample to the formulation was found. The crucial separation premise
is not inferred from DAG acyclicity: it will be certified at geometry setup.

1. For every binary L, signed support cost is exactly W(E xor L)-W(E).
   Translation by E bijects logical supports with opposite-class corrections,
   so Delta_E=m_1-W(E)=Gamma-eta. Restriction adds rho_Y>=0. Therefore the
   score bounds Delta_E from above, without an unconditional bound on Gamma.
2. Pair syndromes telescope along each color arm to the root's real check.
   All virtual endpoints are unconstrained. XOR with the root cancels the
   full physical syndrome. Odd cardinality excludes even-weight stabilizers;
   the one-qubit self-dual CSS quotient then implies nontriviality. The actual
   physical observable must still be independently checked.
3. Signed DAG minimization is valid, including zero original weights. Independent
   tails yield the exact restricted minimum only when their physical supports
   are disjoint from each other and the complete first-edge neighborhood.
4. Independent coordinate construction reproduced distinct-family counts
   8/69/308 and weight-d counts 7/36/140 at d=3/5/7. All-path reachability
   separation checks passed at d=3,5,7,9,15,31. These are finite observations;
   unrestricted minimum-support counts will be checked separately.
5. A stronger, local coordinate certificate also passed these geometries.
   For each participating qubit x let T_c(x) be the tail of its unique
   directed c-pair edge. A continuation from t can include x only if
   h_c(T_c(x))<=h_c(t) and all other h coordinates are >= those of t.
   Record the finite local offset types T_c(x)-h(x). For each template,
   exclude every first-edge/root qubit from each tail cone; for each pair
   of tail cones and every local offset type, prove that the induced three
   coordinate intervals are disjoint or cannot sum to B. This is a sufficient
   certificate for all paths, using bounded local work. It does not enumerate
   production paths or assume that arbitrary lattices satisfy separation.
   An independent reachability-union checker will cross-check the certificate.
6. The package coordinates agree with the prompt, including the g/r/b face
   residue convention and shifted check drawing coordinates. `errors_to_qubits`
   enumerates raw DEM instructions and cannot serve as a general error-column
   permutation. New mapping must count only flattened error instructions and
   check detector, observable, probability, and circuit-location evidence.
7. `error_preds` is assembled after final selection and predecoder composition.
   Postprocessing it permits ordinary or comparative correction sources with
   no metric-driven hard correction changes. Existing matching weights and
   `logical_gaps` are not substituted for physical weights or exact class gaps.

The references supply code/check/boundary structure, not the proposed signed
recurrence: Lee Definition 2 and Appendix A, Kesselring color boundaries,
Meister's distinct SWIM construction, and qecsim's triangular coordinate
conventions. Fresh primary pages were checked; existing local primary-source
and theorem ledgers remain authoritative. No priority or performance claim.

The implementation and final evidence are linked from STATUS.md and the feature
worktree's `docs/monotone_y_signed_gap.md` and `docs/monotone_y_validation.md`.
