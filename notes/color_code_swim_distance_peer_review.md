# Internal Peer-Review Audit: Color-Code Swim Distance Report

**Reviewed manuscript:** `color_code_swim_distance_report_reviewed.md`  
**Review date:** 2026-09-11  
**Recommendation:** Conceptually promising; suitable as a research-starting formulation after the revisions documented below. A publication-level theorem still requires explicit proof of the stage-2 logical-chain/boundary correspondence and transfer of the Meister MWPM-cluster lemmas.

## 1. Summary of the proposed contribution

The report proposes a Meister-style cluster-geometric soft output for the concatenated MWPM color-code decoder. The core construction computes a per-color swim quantity \(\phi_c\) on the second-stage \(c\)-only matching graph and combines the three color branches using their actual decoder weights and logical predictions:

\[
\Phi_{\mathrm{CC}}
=
\min_c\left[W_c-W_*+\mathbf1(\lambda_c=\lambda_*)\phi_c\right].
\]

The report deliberately interprets this as a lower-bound-type proxy for a **fixed-stage-1 conditional complementary gap**, not as an already-proved lower bound on the full concatenated comparative gap.

## 2. Major review comments and corrections applied

### Major comment 1: A naive per-color minimum does not model the concatenated decoder decision

**Problem identified.** An initial natural idea would be \(\min_c\phi_c\). This ignores that concatenated MWPM selects among three final stage-2 candidates with different baseline weights \(W_c\), and different branches may already predict different logical classes.

**Correction incorporated.** The final report defines

\[
\Phi_{\mathrm{CC}}
=
\min_c[W_c-W_*+\mathbf1(\lambda_c=\lambda_*)\phi_c].
\]

This incorporates both inter-color competition and within-color topological ambiguity.

**Status:** resolved at formulation level.

### Major comment 2: The Meister theorem cannot be transferred to the full color-code decoder without qualifications

**Problem identified.** Meister et al. prove a surface-code MWPM result involving the MWPM correction and the minimum-weight correction in the opposite equivalence class. Concatenated MWPM is not one monolithic MWPM on the original color-code error model; it contains a first-stage matching whose result changes the second-stage syndrome.

**Correction incorporated.** The final report introduces \(\Delta_{\mathrm{cond}}\), where ordinary stage-1 outputs are held fixed. Only under an explicit per-stage-2 Meister-type assumption is

\[
\Phi_{\mathrm{CC}}\le\Delta_{\mathrm{cond}}
\]

claimed. No general inequality to \(\Delta_{\mathrm{full}}\) is claimed.

**Status:** resolved; remaining theorem proof explicitly listed as future work.

### Major comment 3: Stage-1 failure modes cannot be ignored

**Problem identified.** Lee–Li–Bartlett exhibit concatenated-MWPM failure mechanisms in which the first restricted-lattice matching is wrong; their asymptotic construction permits errors of order \(3d/7\). Therefore a large stage-2 swim gap does not necessarily imply high confidence in the full two-stage decoder.

**Correction incorporated.** The final report adds a separate stage-1 confidence signal \(\chi_c\), recommends evaluating \((\Phi_{\rm CC},\chi_{\min})\), and reserves a coupled two-stage optimization \(\Psi_c\) for a second phase.

**Status:** resolved as a stated limitation and experimental ablation; not theoretically solved.

### Major comment 4: Stage-1 and stage-2 weights must not be naively summed as physical likelihoods

**Problem identified.** The circuit-level concatenated decoder forms projected/decomposed DEMs. A physical fault can influence both derived subproblems. Summing stage-1 and stage-2 matching weights can therefore double-count evidence. Inspection of current `color-code-stim` confirms that final candidate selection uses the stage-2 returned weights.

**Correction incorporated.** The primary metric uses only the same \(W_c\) that drives the existing final color selection. The proposed two-stage \(\Psi_c\) is explicitly called a decoder-internal deformation cost unless one maps back to original DEM mechanisms and assigns physical cost once.

**Status:** resolved.

### Major comment 5: Boundary contraction used for ordinary MWPM destroys information needed by swim distance

**Problem identified.** Concatenated MWPM can contract equivalent/zero-cost boundary vertices because ordinary matching does not need their distinction. Meister soft output, however, relies on inequivalent boundaries or an equivalent logical-topology representation.

**Correction incorporated.** The report makes the logical-label formulation primary:

\[
B_cz=0,\qquad \ell_c^Tz=1,
\]

and treats boundary-to-boundary Dijkstra as a simplified case that must first be justified. An observable-labelled two-sheet covering graph is proposed for robust implementation.

**Status:** resolved at definition level; explicit triangular-boundary lemma remains to be proved.

### Major comment 6: Projection-decoder topology and two-toric-code unfolding must not be conflated

**Problem identified.** Both involve surface-code/toric-code-like structures, but Delfosse projection onto three restricted lattices and the local equivalence of the color code to two toric-code copies are distinct mappings.

**Correction incorporated.** The report uses the two-copy equivalence only as topological background and treats the projection/concatenation chain maps independently.

**Status:** resolved.

### Major comment 7: “Swim distance = exact confidence” would overstate the source theorem

**Problem identified.** Meister's theorem gives a lower bound on the log-likelihood ratio between the MWPM representative and a minimum-weight representative in the opposite logical class. It does not prove equality or a general constant-factor upper bound for surface codes; it also does not include logical-class degeneracy.

**Correction incorporated.** The report explicitly distinguishes:

1. posterior logical-class LLR;
2. minimum-representative complementary/logical gap;
3. cluster-gap/swim proxy.

**Status:** resolved.

### Major comment 8: Asymptotic performance of concatenated MWPM must be stated cautiously

**Problem identified.** The main paper numerically observes approximately \(p^{d/2}\) scaling over simulated ranges, but its appendix constructs possible \(O(3d/7)\) uncorrectable families and cautions that the asymptotic exponent may approach \(3/7\).

**Correction incorporated.** The report does not call the concatenated decoder asymptotically optimal and explicitly uses the stage-1 adversarial family as a stress test.

**Status:** resolved.

## 3. Mathematical audit

### 3.1 Exact target

The definition

\[
W_\lambda(s)=\min_{e:He=s,Le=\lambda}w^Te
\]

and for one logical bit

\[
\Delta_{\rm comp}=W_{1-\lambda_*}-W_{\lambda_*}
\]

is internally consistent with nondegenerate minimum-weight comparative decoding.

**Caveat:** for correlated/non-independent DEM mechanisms or true degenerate MLD, \(w^Te\) is not the full class log-likelihood. The report correctly limits this interpretation.

### 3.2 Per-color swim optimization

The proposed

\[
\phi_c=\min_{z:B_cz=0,\ell_c^Tz=1}\bar W_c(z)
\]

is a valid decoder-relative topological optimization provided:

1. \(B_c\) is the incidence/check matrix after treating allowed boundary endpoints correctly;
2. \(\ell_c\) is inherited consistently from the physical observable;
3. \(\bar W_c\) is the quotient metric induced by the actual MWPM dual clusters, not merely by the support of the returned correction.

These conditions are correctly highlighted.

### 3.3 Global aggregation inequality

Let

\[
LB_c=
\begin{cases}
W_c,&\lambda_c\neq\lambda_*,\\
W_c+\phi_c,&\lambda_c=\lambda_*.
\end{cases}
\]

If \(LB_c\le W^{(2)}_{c,1-\lambda_*}\) for every color, then

\[
\min_cLB_c-W_*
\le
\min_cW^{(2)}_{c,1-\lambda_*}-W_*
=\Delta_{\rm cond}.
\]

Thus the proposed corollary is algebraically correct under its stated per-color premise.

**Status:** verified.

### 3.4 Nonnegativity

Because \(W_*\) is the minimum over ordinary color candidates, \(W_c-W_*\ge0\), and quotient edge costs are nonnegative under ordinary \(p_e<1/2\) matching weights. Hence \(\Phi_{\rm CC}\ge0\).

**Caveat:** if reweighted decoding ever permits negative edge weights, the shortest-path/cluster construction needs modification. This is outside the current scope.

## 4. Literature audit

The following claims were checked against the supplied sources and current public literature.

- Color-code elementary Pauli errors are three-check/hyperedge-like: supported by Lee–Li–Bartlett and color-code topology literature.
- Projection decoding maps to restricted surface-code-like lattices and uses lifting: supported by Delfosse and later circuit-level projection work.
- Concatenated MWPM performs two matchings per color and selects the least-weight final prediction: supported by Lee–Li–Bartlett and current implementation.
- Circuit-level concatenated MWPM creates restricted/only-color DEMs and stage-1 virtual detectors: supported by Lee–Li–Bartlett.
- Meister soft output contracts final clusters and finds the shortest nontrivial logical path; their MWPM theorem provides a one-sided lower bound: supported directly by Meister–Pattison–Preskill.
- Current `color-code-stim` supports comparative decoding/logical gap: supported by repository documentation and source inspection.
- Direct published work explicitly defining a Meister-style cluster gap/swim distance on concatenated-MWPM color-code stage-2 graphs was not found in the search performed on 2026-09-11.

**Priority caution:** the final item is only a search result, not proof of nonexistence. The manuscript should use “to our knowledge” only after an additional targeted scholar/arXiv/Crossref search before submission.

## 5. Remaining proof obligations before publication

1. Prove the exact relative-homology/logical-label structure of each triangular \(G_c\), including boundary treatment.
2. Show that the MWPM dual-cluster lemmas used by Meister transfer to \(G_c\) with the chosen boundary/logical representation.
3. Determine whether DEM compression or correlated physical faults affect the interpretation of the per-edge log-likelihood weights used by \(\phi_c\).
4. Quantify \(\Delta_{\rm full}-\Delta_{\rm cond}\), especially when logical forcing changes stage-1 matching.
5. Test adversarial \(O(3d/7)\)-type patterns to determine whether stage-1 confidence is necessary in practice.
6. Verify that the observable-labelled double-cover shortest path is exactly equivalent to the desired relative-chain optimization for the concrete decoder graph implementation.

## 6. Final assessment

The strongest defensible initial paper claim is not “we generalized the exact logical gap to color codes.” It is:

> We construct a cluster-geometric soft output tailored to the two-stage and three-color decision structure of the concatenated MWPM decoder, derive a conditional relation to complementary decoding under explicit matching-graph assumptions, and benchmark it against full comparative logical-gap decoding.

The mathematical novelty is concentrated in the mapping from final color-code logical ambiguity to the stage-2 matching graphs and in the three-color aggregation rule. The largest technical risk is stage-1 ambiguity. The proposed experimental plan is capable of deciding early whether that risk is negligible in the operational regime or whether a genuinely coupled two-stage confidence metric is required.

