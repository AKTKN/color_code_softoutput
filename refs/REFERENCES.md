# REFERENCES.md

## Belief-matching implementation audit — 2026-09-29

Higgott, Bohdanowicz, Kubica, Flammia and Campbell, *Improved decoding of
circuit noise and fragile boundaries of tailored surface codes*,
Phys. Rev. X **13**, 031007 (2023), arXiv:2203.04948.
Inspected [Appendix C and its footnotes](https://arxiv.org/html/2203.04948#A3)
and the [official implementation](https://github.com/oscarhiggott/BeliefMatching/blob/main/src/beliefmatching/belief_matching.py)
on 2026-09-29. Sources establish sum aggregation / negative-log weights and
the official product_sum default; they do not validate the local capped
log-odds concatenated adaptation. Finite local evidence and limitations:
`../notes/support/bp_predecoding_audit_20260929/report.md`.

## Circuit DEM-Y source audit — 2026-09-19

Reopened the primary [Lee v2](https://arxiv.org/html/2404.07482v2),
[Stim DEM format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md),
and [Meister record](https://arxiv.org/abs/2405.07433), using the edition/location
ledger below for background. Lee Sec. 4 and Algorithm 1 motivate the separated
DEM construction; Stim specifies error instructions, target parity and
separator semantics; Meister supplies soft-output motivation. None is cited
as proving the new base-root/enriched-tail family, strong cap certificate,
signed parity DAG or sparse junction solver. Those follow the user's explicit
prompt and the ten local propositions in the new standalone algorithm note.
No new literature-priority or exhaustive related-work claim is made.

Local implementation source audit at color-code-stim base
`0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`: `color_code.py`, `config.py`,
`graph_builder.py`, `noise_model.py`, `dem_utils/dem_manager.py`,
`stim_utils.py:dem_to_parity_check`, and
`decoders/concat_matching_decoder.py`. Confirmed tri_optimal's actual stored
vector; detector Pauli/color and face shifts; effective granular noise fallbacks;
separate_depolarizing_errors → dem_xz; error-only matrix columns; final original-
DEM correction selection and predecoder composition. The new parser verifies
parity and separators independently instead of assuming the legacy Boolean
parser handles duplicate/separated targets. The original decoder is unchanged.
See `../notes/support/CIRCUIT_DEM_Y.md` and the feature's standalone paper/API guide.


## Monotone-Y source audit — 2026-09-19

Rechecked [Lee v2](https://arxiv.org/html/2404.07482v2), Definition 2
(HTML lines 185–188) and Appendix A.3 (547–553), for physical qubit/graph and
boundary conventions. Existing inspected Kesselring and Meister sources below
remain background for physical boundaries and the distinct SWIM construction;
their primary records were reopened. No cited paper is claimed to prove the
user's monotone-Y signed recurrence, separation certificate or performance.

New directly relevant coordinate reference:
[qecsim Color666Code documentation](https://qecsim.github.io/api/models/color.html),
`is_plaquette`, `is_site`, `is_in_bounds` and `bound` (page labelled 1.0b9).
Its plaquette congruence is equivalent to (u+v)%3=2. The map from package
drawing coordinates and g/r/b residue convention is independently verified
against local `graph_builder.py`, not inferred from numeric color labels.

Implementation sources inspected at color-code-stim origin/main
`0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`: `color_code.py` (decode and
errors_to_qubits), `graph_builder.py`, `circuit_builder.py` (single X layer,
observable records, comparative detector), `noise_model.py` (effective
overrides), `dem_utils/dem_manager.py`, `stim_utils.py` (error-only columns
and pure-X identity), and final correction composition in
`decoders/concat_matching_decoder.py`. Stim 1.16.0 circuit error explanations
supply independently executed location evidence. Acceptance uses the normal
PyMatching 2.3.1 wheel in a temporary venv derived from color_code_so.
The separate feature and its new proofs are documented in
`../external_libs/color-code-stim-monotone-y/docs/monotone_y_signed_gap.md`.

## Final-correction path-gap source audit — 2026-09-18

Reinspected [Lee 2404.07482v2](https://arxiv.org/html/2404.07482v2), Definition 2
and Appendix A.3 (HTML lines 185–189 and 547–555). They specify the physical
qubit/monochromatic-edge correspondence and the two retained boundary labels.
The new score and global correction-weight subtraction come from the user's
implementation prompt, not a claim imported from Lee. Existing bibliography
entries remain the mathematical source ledger; no new bound or novelty claim.

Inspected color-code-stim origin/main `0eb35935c1e5ff30ba3db9def30a9d35bca2f16d`:
`graph_builder.py`, `noise_model.py`, `circuit_builder.py`, `color_code.py`
(`errors_to_qubits`, decode), `dem_utils/dem_manager.py`, and final selection/
partial-correction composition in `decoders/concat_matching_decoder.py`.
New code is in a separate feature worktree. Acceptance uses ordinary PyMatching
2.3.1 from its distribution wheel rather than the SWIM extension. DEM column
mapping is checked against physical face incidence and logical support;
the older helper's raw-instruction enumeration is not reused.

## Surface-code example audit — 2026-09-16

Inspected the fixed local PyMatching `SO_example/readme.md`,
`sampling_SE_surface_codes_SO.py`, `circuit_gadget.py`, `surface_codes.py`,
`dem_parsor.py`, `so_sampler.py`, and the two-page
`SoftOutput_vs_complementary_gap_test_results.pdf` (Zihan Chen, 25 February 2025).
The PDF specifies X memory, p=.001 and 2d explicit rounds between initialization
and final measurement, and historical rounded-dB figures. No precision/timing
claim from that example is imported into the new validation.

The [surface companion](../surface_code_test/README.md) uses the same physical
circuit and ordinary graph source, with the existing generic PyMatching SO API
and unrounded storage. Forced-class complementary costs are validated against
independent exact finite oracles. Existing balanced-cut algebra supplies the
checked row-gauge relation; no new literature theorem is claimed. Sources are
local at PyMatching `83cee05cc16d6fce9deafdbbf7952b4b96a7f21e`, unchanged/clean.
The new run archives the inspected example Python sources and readme.


## Circuit implementation source audit — 2026-09-16

No new mathematical literature claim is introduced by the closed-memory
implementation. It uses the already audited circuit theory and these fixed
local implementation sources (both clean on `phase2a/swim-distance`):

- color-code-stim `ba6f7dc8b7aaab237d98ad5f08825be4225864c6`:
  `dem_utils/dem_manager.py`, `dem_utils/dem_decomp.py`,
  `decoders/concat_matching_decoder.py`, public ColorCode and uniform NoiseModel.
  These define the actual retained H2/L2, probability/sort/source maps, ordinary
  branch rule, comparative gap and physical sampling circuit. The effective
  model is not relabelled as the paper's literal algorithm or correlated law.
- PyMatching `83cee05cc16d6fce9deafdbbf7952b4b96a7f21e`: existing generic
  `decode_batch_soft_output` radius export and Phase-2A reference metric.
  These define practical final-defect growth conventions, not an optimal
  odd-cut certificate. No external source modification was needed.

Exact baseline remotes/editable installs and test logs are in
`../implementation_artifacts/circuit_level/baseline/`; the saved run archives
main sources and fixed graph/circuit metadata. See
[implementation report](../notes/support/CIRCUIT_LEVEL_IMPLEMENTATION.md).
The source edition/location ledger below remains authoritative for theorem citations.


Last audit: 2026-09-16. This is the canonical bibliography at its current path. Locations below refer to the editions actually inspected; PDF page numbers are printed page numbers, not zero-based indices. A source citation supports its stated input; the project logical-path theorem is proved separately from the physical side parity and the verified incidence maps.

## Core sources and exact reuse

### [Lee2025] Concatenated matching

Seok-Hyung Lee, Andrew Li, and Stephen D. Bartlett, *Color code decoder with improved scaling for correcting circuit-level noise*, Quantum **9**, 1609 (2025).
[Publisher/DOI](https://doi.org/10.22331/q-2025-01-27-1609);
[arXiv:2404.07482v2](https://arxiv.org/abs/2404.07482v2);
[local PDF](<Color code decoder with improved scaling for correcting.pdf>).

Metadata verified against the arXiv record, including the journal reference and DOI. The supplied PDF is the v2 article with Quantum layout. Inspected Secs. 2.1–2.2, Sec. 3 definitions/algorithm, and Appendix A.1–A.3 in detail; also visually checked Fig. 2 and the nested boundary set on p. 23. Numerical sections and Appendix A.4 performance comparisons are not imported.

| Source location | Reusable fact | Limit |
|---|---|---|
| Sec. 2.1, Eq. (1), Fig. 1, pp. 3–4 | Qubits on vertices; paired X/Z face checks; triangular patch, one qubit, boundary logical representatives | General lattice-family claims need explicit patch assumptions |
| Sec. 2.2, p. 4 and footnote 1 | Matching parity excludes virtual boundary checks; restricted-boundary merging is a matching convention | Zero-cost matching identifications do not establish logical equivalence |
| Sec. 3, Definitions 1–2, p. 7 | Restricted and monochromatic graphs; bijections $\epsilon_{\neg c}$ and $\epsilon_c$; exact two-round set equations | Main-text graphs merge boundaries |
| Appendix A.1, pp. 21–22, Eq. (10) | Hypergraph complex; stage-2 edge/hyperedge identification; $\pi_0^{(c)}$, projectors, $p_{\rm edge}^{(c)}$, $p_{\rm vert}^{(c)}$ | Initially stated without boundaries |
| Appendix A.2, Claim 1, Eqs. (11)–(12), p. 22 | Valid stage-1 and stage-2 matchings give the physical syndrome | Validity does not imply successful logical correction |
| Appendix A.3, pp. 22–23, Claim 2, Eq. (13) | Three augmented dual boundary vertices; two retained stage-2 boundary vertices; syndrome validity modulo boundary spaces | No boundary-to-logical-class iff theorem is stated here |

The source already specifies the stage-2 boundary set
$\{v_{\rm bdry}^c,\{v_{\rm bdry}^{c_1},v_{\rm bdry}^{c_2}\}\}$.
This corrects the scaffold's suggestion that a finer partition might be entirely absent from the source. Task 1 now proves the physical side/corner origins in note Proposition 5.3. Tasks 2–3 now realize those labels and prove the full physical chain/syndrome map. Task 4 now proves the logical interpretation and exact non-c-face stabilizer characterization in note §8.

Transcription notes: Sec. 3 occasionally uses membership notation for subsets. We use subsets/chain vectors explicitly. Appendix A.1's hyperface description is read as the incidence set of hyperedges around a dual vertex, consistent with its stated maps and Delfosse Definition 4.1; do not interpret a hyperface as merely a set of ordinary dual edges. The supplied PDF produced cross-reference warnings during extraction; the critical boundary formula was checked against the rendered page. An [author HTML edition](https://arxiv.org/html/2404.07482v2) is also available.

### [Meister2024] Surface-code soft output

Nadine Meister, Christopher A. Pattison, and John Preskill, *Efficient soft-output decoders for the surface code*, arXiv:2405.07433v2 (2024).
[Versioned record](https://arxiv.org/abs/2405.07433v2);
[local PDF](<efficient soft output.pdf>).

Authors, title, and version verified against arXiv. The checked record lists v2 dated 1 June 2024 and no journal reference; retain the arXiv citation rather than inventing a publication venue.

Inspected Sec. II A–C, Sec. III A–B, and Appendix B, including the proofs of Theorem 10, Lemmas 11–12, and Theorem 13. Applications and numerical results are not foundations for the color-code theorem.

| Source location | Reusable fact | Hypothesis/limit |
|---|---|---|
| Sec. II B.1, pp. 2–3, Fig. 1 | Modified graph with inequivalent boundary nodes and trivial graph cycles | This is a surface-code logical structure to verify for $G_c$ |
| Definition 1, Eq. (1); Appendix B, p. 16 | Clusters are connected components of a union of metric balls; edges are intervals | Partial-edge coverage matters |
| Sec. II C.1; Definition 7, Eq. (6), p. 4 | MWPM radii from the matching dual variables | Final optimal dual data are needed for the analytical result |
| Algorithm 1, Definition 8, p. 5 | UF growth and terminal radii | Displayed UF algorithm assumes uniform weights; not final-correction components |
| Definition 9, Algorithm 2, p. 6 | Contract each cluster; shortest logical path, implemented between two boundaries | The note proves that topology before applying the same quotient strategy |
| Theorem 10, Eq. (7), pp. 6–7 | Exact conditional success/failure log ratio for odd-length repetition code and UF | Independent bit flips, uniform log-odds, one-dimensional complementary error pair |
| Lemmas 11–12, Eqs. (12), (20), pp. 7–8 | Lower bounds on weighted intersection with clusters using the optimal dual | Source assumes vertex-disjoint paths; the note rederives coverage with edge-disjoint trails and free boundary ends |
| Theorem 13, Eq. (26), p. 8 | MWPM representative/opposite minimum representative log ratio lower-bounds $\phi$ | Stochastic bit-flip surface code; actual MWPM correction and clusters; not summed logical-class probabilities |

Theorem 13 states
$\log[\Pr(E=F\mid\sigma)/\Pr(E=M\mid\sigma)]\ge\phi(\sigma)$.
Its probability terms concern specific error representatives. The discussion following Eq. (34) explicitly reports no constant-factor upper bound. Theorem 10 is not a general surface-code or color-code UF theorem. The initial transfer checklist is preserved in [the deferred proof program](../notes/deferred_proof_program.md). The final Phase-1 transfer below supersedes its open status.

### [Kesselring2018] Color boundaries and corners

Markus S. Kesselring, Fernando Pastawski, Jens Eisert, and Benjamin J. Brown, *The boundaries and twist defects of the color code and their applications to topological quantum computation*, Quantum **2**, 101 (2018).
[DOI](https://doi.org/10.22331/q-2018-10-19-101);
[arXiv:1806.02820v3](https://arxiv.org/abs/1806.02820v3);
[local PDF](source_audit/kesselring.pdf).

Metadata verified against arXiv. Inspected Secs. 3.3–3.4, 4.1–4.3, and the color-boundary portion of Sec. 9; visually checked Fig. 6.

Reuse: Secs. 3.3–3.4, Eqs. (11)–(13), explain colored string charges and fusion. Secs. 4.2–4.3, Fig. 6(a,c,f), and Table 2 specify same-color condensation and corners with one remaining face of the third color. Sec. 9, Table 6 and Fig. 31, discusses folded layers. These support physical endpoint conventions, not a theorem about Lee's stage-2 graph. The Pauli-boundary and twist families are outside the selected patch class.

### [Delfosse2014] Hypergraph complexes and projection

Nicolas Delfosse, *Decoding color codes by projection onto surface codes*, Physical Review A **89**, 012317 (2014).
[DOI](https://doi.org/10.1103/PhysRevA.89.012317);
[arXiv:1308.6207v1](https://arxiv.org/abs/1308.6207v1);
[local PDF](source_audit/delfosse.pdf).

Metadata verified against arXiv. Inspected Secs. 3.1–3.2, 4.1–4.3, and 5.2–5.3. Definition 3.1/Proposition 3.2 define the binary complex/CSS convention; Definitions 4.1–4.2, Eqs. (5)–(6), and Table 4 give qubits as hyperedges and stabilizers as hyperface boundaries. Lemma 4.3 supplies self-duality. Definition 5.5/Theorem 5.6 give the projection chain map to the restricted surface graphs.

Limit: Sec. 4 assumes a 3-regular, face-colored surface tiling with no loops or multiple edges. These closed-tiling projection statements are not automatically boundary results for the triangular patch. His Z-error convention is translated explicitly in [NOTATIONS.md](../NOTATIONS.md). The projection map is not Lee's stage-2 support inverse.

### [Kubica2015] Unfolding with boundaries

Aleksander Kubica, Beni Yoshida, and Fernando Pastawski, *Unfolding the color code*, New Journal of Physics **17**, 083026 (2015).
[DOI](https://doi.org/10.1088/1367-2630/17/8/083026);
[arXiv:1503.02065v1](https://arxiv.org/abs/1503.02065v1);
[local PDF](source_audit/kubica.pdf).

The arXiv record verifies authors/title and links the journal DOI; the inspected 46-page arXiv edition is v1, not v2. Inspected Theorem 1's scope and Sec. III A–B, especially Eq. (44), Figs. 8–10, and Theorem 3 on pp. 25–27. The triangular code becomes one folded surface-code patch with two boundaries of each surface-code type; the layers attach along the third color boundary. The construction uses a local Clifford transformation. It does not identify either layer with Lee's monochromatic graph or its qubit-edge map.

### [Bombin2006] Original triangular code and string-nets

Héctor Bombín and Miguel A. Martín-Delgado, *Topological Quantum Distillation*, Physical Review Letters **97**, 180501 (2006).
[DOI](https://doi.org/10.1103/PhysRevLett.97.180501);
[arXiv:quant-ph/0605138v3](https://arxiv.org/abs/quant-ph/0605138v3);
[local PDF](source_audit/bombin.pdf).

Added as the foundational source needed for physical logical representatives. Title/authors/journal metadata checked against the arXiv record; the downloaded author version is v3 (29 March 2007). Inspected pp. 2–3: Eqs. (1), (4)–(6), Figs. 2–3, and the triangular-code construction. These provide face stabilizers, equivalence modulo the stabilizer group, colored string deformations, matching-color termination, and three-string logical operators. The standard triangular construction encodes one qubit; the anticommuting three-string representatives are also described. Closed-surface string homology is not a substitute for the proposed decoder-specific quotient.

## Directly relevant later work checked

### [Kishi2026]

Kaito Kishi, Riki Toshio, Jun Fujisaki, Hirotaka Oshima, Shintaro Sato, and Keisuke Fujii, *Even More Efficient Soft-Output Decoding with Extra-Cluster Growth and Early Stopping*, arXiv:2602.03336v1 (2026).
[Record](https://arxiv.org/abs/2602.03336v1);
[local PDF](source_audit/kishi.pdf).

Metadata and PDF version verified. Inspected §II A–C, §III A–B,
Definitions 1–4, Theorems 1–4 and their proofs, pp. 3–7. Definition 1
is Meister's cluster gap. The no-cluster-graph extra-growth score is a
bottleneck connectivity value, at most the cluster gap when defined;
Theorem 2 guarantees detection below the cutoff. The graph-assisted
score is a restricted shortest-path value, at least the full gap when
defined and equal below the cutoff (Theorems 3–4).

Comparison: these are different objectives/early-stopping variants on
an already logically identified graph. Our full interval quotient shares
the baseline metric, but we do not implement or transfer their variants,
runtime estimates, or calibration. Their surface-code setting does not
provide Lee's fixed-fiber physical correspondence. The inspected PDF
says 4 February 2026; do not mix it with differently dated HTML rendering.

### [LeeEnglishBartlett2026]

Seok-Hyung Lee, Lucas H. English, and Stephen D. Bartlett,
*Efficient post-selection for general quantum LDPC Codes*,
npj Quantum Information **12**, 96 (2026).
[Publisher](https://doi.org/10.1038/s41534-026-01242-x);
[inspected arXiv:2510.05795v2](https://arxiv.org/abs/2510.05795v2);
[local manuscript](source_audit/postselection.pdf).

The publisher supplies publication metadata and the middle initial;
the retained October 2025 author manuscript prints Lucas English.
Read §§2–3, especially the representative logical-gap Eq. (2),
Definitions 1–2 and Strategies 1–2. It proposes cluster-size and
cluster-LLR norm heuristics for general QLDPC clustering decoders,
including BP+LSD, without searching logical paths. Its class-restricted
decoder weight comparison is distinguished from exact class likelihood.
The paper numerically evaluates postselection, not a universal
fixed-branch inequality of the form proved here.

Comparison: broader code/decoder applicability with heuristic scores;
our exact path interpretation and certified representative inequality
have narrower graph/fiber hypotheses. No posterior guarantee is imported.
The previous cookie-page download failure is superseded by this retained
versioned author PDF; it is not a claim that the publisher PDF is local.

### [Wills2026] General-code forced gap

Adam Wills, Theodore J. Yoder, and Isaac Chuang,
*Forced Gap Post-Selection for Quantum LDPC Codes and their Operations*.
[arXiv:2605.20346v1](https://arxiv.org/abs/2605.20346v1);
[local PDF](source_audit/forced_gap.pdf).

Read Methods, pp. 2–3, Eqs. (1)–(5). It separates exact class-summed
likelihood from practical decoder-found representative likelihoods,
reruns with individual observable constraints, and defines a gap among
the distinct classes found. Failed forced runs have an explicit convention.
This addresses general QLDPC decoding and operations rather than a
single Lee stage-2 fiber. The same need to distinguish representatives
from class sums applies here; the score and its feasible sets are different.
No forced-gap theorem or empirical performance is transferred.

### [Smith2024] Exclusive UF surviving distance

Samuel C. Smith, Benjamin J. Brown, and Stephen D. Bartlett,
*Mitigating errors in logical qubits*, Communications Physics **7**, 386 (2024).
[DOI](https://doi.org/10.1038/s42005-024-01883-4);
[arXiv:2405.03766v1](https://arxiv.org/abs/2405.03766v1);
[local PDF](source_audit/smith.pdf).

Read Appendix E, p. 20, Eqs. (E1)–(E3). The exclusive UF decoder uses
surviving distance: the minimum logical weight outside the final erasure
clusters. It proves a correct-or-abort criterion for Pauli-plus-erasure
noise under its UF growth analysis. This is directly overlapping prior
work on the uncovered-logical-cost strategy. Our weighted metric has
the same geometric objective when coverage is a whole-edge erasure set;
our certified MWPM weight-difference theorem has different hypotheses.
Its UF correct-or-abort claim is not imported.

### [Dinca2026] Fractional-edge swim and decoder confidence

Maria Dincă, Tim Chan, and Simon C. Benjamin,
*Error mitigation for logical circuits using decoder confidence*.
[arXiv:2512.15689v3](https://arxiv.org/abs/2512.15689v3);
[local PDF](source_audit/dinca.pdf).

Read §II.1–II.2 and §III, especially Definitions 4–5, p. 3.
Definition 5 explicitly removes only the covered fraction of an edge.
Its swim objective is geometrically equivalent to ours once the
logical graph and cluster set are supplied. The paper compares scores
to logical error risk by tensor-network calculations for surface-code
noise and uses an instrumented implementation from Chen et al.
Neither fractional coverage nor the term swim distance is new here.
Its empirical risk estimates do not establish our fixed-fiber theorem
or calibrate the concatenated color-code decoder. The versioned PDF
is used instead of the differently dated HTML served during the search.

### [Chen2025] Instrumented soft output beyond planar memory

Zi-Han Chen, Ming-Cheng Chen, Chao-Yang Lu, and Jian-Wei Pan,
*Efficient Magic State Cultivation on RP2*.
[arXiv:2503.18657v1](https://arxiv.org/abs/2503.18657v1);
[local PDF](source_audit/chen_cultivation.pdf).

Read §VI, pp. 10–12, Fig. 12: customized PyMatching exports final
fill-region information, subtracts endpoint local radii from edge
weights with clipping, and runs logical shortest-path searches.
It splits both planar boundaries and antipodal detector pairs in the
RP2 cultivation graph. This directly overlaps decoder instrumentation,
weight reduction and nonplanar soft output.

Comparison: its local radius formula has the same clipped endpoint form
as our formula when those radii equal our h-values. Equality between
its combined fill-region convention and the selected odd-cut certificate
is not proved here (the PDF's region definition uses a minimum over
sources, while our union coverage is derived by a maximum). Its
antipodal cuts differ from the color-side/opposite-corner split.
No implementation or source theorem is used as proof of our topology
or certificate. No novelty is claimed for these shared methods.

### [EdmondsJohnson1973] Exact nonnegative parity dual

Jack Edmonds and Ellis L. Johnson, *Matching, Euler tours and the
Chinese postman*, Mathematical Programming **5**, 88–124 (1973).
[DOI](https://doi.org/10.1007/BF01580113);
[local PDF](source_audit/edmonds_johnson.pdf).

Read §3, pp. 90–95, especially (3.2), (3.5)–(3.9) and the integrality
argument, plus the opening of §4. The parity polyhedron consists of
nonnegative edge variables meeting every T-odd cut with load at least
one. Its nonnegative odd-cut dual has optimum equal to minimum T-join
cost; the source gives a blossom algorithm producing primal/dual optima.
Our Proposition 10.2 adapts this imported theorem to the syndrome metric
closure with a free matching boundary. Complementing cut shores removes
the boundary from dual sets. This supplies existence and strong duality;
it is not a claim that our companion LP is computationally efficient.

### [SparseBlossom2025] Solver dual conventions

Oscar Higgott and Craig Gidney, *Sparse Blossom: correcting a million
errors per core second with minimum-weight matching*, Quantum **9**, 1600 (2025).
[DOI](https://doi.org/10.22331/q-2025-01-20-1600);
[arXiv:2303.15933v2](https://arxiv.org/abs/2303.15933v2);
[local PDF](source_audit/sparse_blossom.pdf).

Read §§2.4–2.5.2 and §3's graph-fill-region definitions. The ordinary
perfect-matching LP has unrestricted singleton duals (p. 8, Eqs. (4)–(6));
pp. 10–11 explain why metric-path-graph growth can preserve nonnegative
singleton radii. Thus the note does not allege that PyMatching necessarily
produces negative radii. Region/blossom data still need a verified
boundary-normalization and original-syndrome-set interpretation to
instantiate our certificate. The source does not document the required
public export interface or prove our color-code logical correspondence.

## Implementation inspection

[seokhyung-lee/color-code-stim](https://github.com/seokhyung-lee/color-code-stim), local commit
0eb35935c1e5ff30ba3db9def30a9d35bca2f16d.

Read the README, the triangular-construction entry point in
[graph_builder.py](../external_libs/color-code-stim/src/color_code_stim/graph_builder.py),
and the two matching methods in
[concat_matching_decoder.py](../external_libs/color-code-stim/src/color_code_stim/decoders/concat_matching_decoder.py).

The graph builder records physical boundary labels and uses odd distances. The current decoder consumes decomposed DEM check matrices, combines real color detector outcomes with stage-1 predictions, and returns predictions/weights from PyMatching. These methods do not return the dual radii needed here. This is a source-code inspection, not an execution or a proof that the DEM columns retain the perfect-measurement qubit bijection. No external decoder experiment was performed; the separate Phase-1 finite checks use independently constructed perfect-measurement graphs.

The [official PyMatching API](https://pymatching.readthedocs.io/en/stable/api.html),
page labelled 2.1.0 and inspected 12 September 2026, documents decode
predictions and optional returned weights. No compatible dual/radius
certificate is promised by the inspected public interface. Sparse Blossom
and Chen's custom implementation are audited above. This is an interface
limitation of the inspected setup, not a claim that instrumentation is
impossible or unprecedented.

## Search scope and source availability

On 2026-09-11, searched the local workspace for relevant PDFs and made targeted web queries including:

- “monochromatic” “color code” “logical” boundary concatenated;
- “c-only” “boundary” “logical” color code;
- site:arxiv.org “color code” “monochromatic” “logical”;
- site:arxiv.org “color code” “relative homology” boundaries;
- site:arxiv.org “concatenated” “swim” color code;
- the exact Meister title with “published journal”.

The source-level audit covered the locations listed above, not all papers citing them. Lee Appendix A.3 provides a direct boundary construction; no direct proof of the proposed endpoint-parity/physical-logical-class theorem was located in these inspected passages or targeted results. This is a limited search outcome, not a novelty or nonexistence claim. Tangential fractal-code and 3D-code search results were not used.

The two original PDFs remain in refs/. The source_audit directory now retains twelve additional primary PDFs, with canonical links above. The old availability list incorrectly implied that several other PDFs were already present; that list is superseded. Bibliographic verification and mathematical support are recorded separately; only the specifically inspected results above count as audited.

## Phase-1 completion audit — 2026-09-12

Repeated primary-source searches for color-code logical boundaries,
projection and unfolding, concatenated matching with logical gap or
postselection, swim distance, bounded/extra-cluster gaps, and general-code
confidence. Search results led to the originals documented above; search
snippets and secondary summaries were not proof inputs. In addition to
the earlier six core papers, the resumed run inspected the later score
constructions, the parity polyhedron and the actual implementation/API.

| Claim family | Exact comparison with prior work |
|---|---|
| Physical code, colored strings and corners | Lee, Bombín and Kesselring supply physical inputs; explicit all-distance incidence is derived in the note. |
| Decoder maps and validity | Lee Definitions 1–2/A.1–A.3 are translated without changing physical edge labels or conditional validity; Lambda is essential. |
| Logical quotient | Physical side parity plus k=1 proves the decoder-specific iff; Delfosse projection and Kubica unfolding are different maps, neither stronger nor weaker versions of this fiber statement. |
| Dual clusters | Meister Definition 7 supplies the radius rule; Edmonds–Johnson supplies a precise nonnegative free-boundary LP. This is a boundary adaptation, not arbitrary Blossom-history equivalence. |
| Contraction and logical minimum | Same metric strategy as Meister Definition 9, Smith's whole-erasure objective and Dincă's fractional definition; our physical lifting theorem justifies its use on this graph. |
| Representative inequality | Meister Lemmas 11–12/Theorem 13 inspire the proof. Our edge-disjoint-trail and free-boundary proof handles the stated weighted stage-2 setting explicitly; no summed-class or full-decoder result is inferred. |
| Later variants and nonplanar applications | Kishi, Chen and general-QLDPC postselection preclude broad priority claims. Their extra-growth, region, antipodal-cut and cluster-statistics conventions are not silently identified with our certificate. |

Source issues retained: Meister's displayed singleton equalities do not
formally dualize to nonnegative singleton variables; our T-join-dominant
LP removes that ambiguity. Its path-set convention is vertex-disjoint;
our proof requires only edge-disjoint trails. Appendix B says positive
while displaying a nonnegative inequality; we state the positive metric
and labelled zero-weight pseudometric cases separately. No source typo
is used as an additional hypothesis or hidden proof step.

The audit is bounded to the listed original passages and targeted searches,
not an exhaustive proof of absence from the literature. No novelty claim
is made. The following sections retain earlier checkpoints; references to
then-deferred tasks do not override the completed Phase-1 results above.

## Research Task 1 source-to-result update — 2026-09-11

The standalone [note](../notes/note.tex) reuses the editions above.
No new primary paper was needed beyond the retained audit. The literature
supports physical boundary conventions and the source graph construction;
the following all-distance combinatorial classification is our derivation,
not a theorem attributed to one of those papers.

| Note location | Evidence used | Status and limit |
|---|---|---|
| §§1–2 | Lee §2.1, pp. 3–4; Bombín pp. 2–3, Eqs. (1), (4)–(6); Kesselring §§3.3–3.4, 4.2–4.3 | Physical checks, one-qubit logical representatives, colored strings, condensation, and remaining-face corner convention are imported background |
| Definition 3.1 | Local graph_builder.py, _build_triangular_graph and _add_tanner_edges, same pinned commit | Coordinates use x=4i+2j, y=j; the six Tanner offsets give the stated cyclic face supports. This is a specification of the selected standard family, not proof by code execution |
| Lemma 3.3 | Explicit coordinate inequalities, two residue classes, and rotation in the note | Our proof for every odd d≥3; no drawing or finite numerical enumeration used |
| §4, Definitions 4.1–4.2, Eqs. (1)–(2) | Lee §3, Definitions 1–2 and two-round algorithm | Exact ordinary merged graph definitions and correction equations |
| §4.3 validity argument | Lee Appendix A.2 Claim 1 and A.3 Claim 2, Eqs. (11)–(13) | Conditional on feasible round outputs. These claims alone do not supply a separate feasibility/connectivity proof; a draft overstatement was removed |
| Lemma 5.2, Proposition 5.3 | Our local incidence proof plus Lee Definition 2 | Dangling criterion and missing-face side / missing-edge opposite-corner partition; sizes d and 1 |
| Remark 5.4 | Lee Appendix A.3, pp. 22–23, retained source boundary set | Identifies the two proven physical origins with the source labels; no split graph constructed |
| Proposition 5.5 | Binary incidence at the ordinary virtual node | Our elementary parity statement; not a logical-equivalence theorem |
| §4.4 | Delfosse §§4–5; Kubica §III.B, Eq. (44), Theorem 3; Meister §II.B.1 | Documents why projection, unfolding, and surface-code logical-boundary results cannot be identified with the stage-2 map without proof |

Lee's exact local rule is that a stage-2 edge joins the incident c face and
c primal edge, or the one present object to the matching boundary.
The coordinate proof verifies the hypotheses of that rule at all
corners. The physical boundary-edge color uses the one real-face color
and the boundary-sector color, not two fictitious real faces.

The bibliography's earlier broad source audit remains historical evidence
for later work. Task 1 does not reactivate its soft-output proposals or
extend any source theorem to the color-code graph.

## Research Tasks 2–3 source-to-result update — 2026-09-11

Rechecked the retained Lee PDF text at Appendix A.1–A.3 and the
[primary author HTML edition](https://arxiv.org/html/2404.07482v2).
Eq. (10), the two retained boundary labels, and Claim 2 / Eq. (13) directly
support the source chain identification and boundary-space convention.
The project states their physical real-row form explicitly and proves
it locally for all binary chains.

| New note location | Source or derivation | Precise scope |
|---|---|---|
| Definition 6.1, Eq. (5) | Task 1 Proposition 5.3 plus Lee Definition 2 and Appendix A.3 | Two terminal vertices with one physical edge per qubit; realizes retained source labels without auxiliary physical shortcuts |
| Definition 6.2, Lemma 6.5 | Our typed quotient construction | Terminal identification preserves edge labels and commutes with graph incidence |
| Lemma 6.3 | Our coordinate descent in the Task 1 family | All-distance connectivity, including d=3; not a logical-path theorem |
| Proposition 6.6 | Our real-row constraint identity; compare Lee §2.2 footnote 1 and Appendix A.3 matching-boundary convention | Same feasible chains, costs and minimizers only under identical weights and two free terminal rows |
| Definition 7.1, Lemma 7.2 | Lee Appendix A.1 edge/hyperedge basis identification, expressed on physical supports | Linear inverse on all binary chains and pure-sector Pauli multiplication; not a new source bijection theorem |
| Definition 7.3, Lemma 7.4, Eqs. (9)–(11) | Lee Eq. (10), Claim 2 / Eq. (13), plus our explicit real-row incidence proof | $HT_c=\Lambda_cD_c$ for all chains; source virtual vertices are removed as syndrome coordinates, auxiliary c-edge parity is translated through restricted incidence |
| Proposition 7.5 | Our endpoint-incidence consequence | Task 3 establishes zero syndrome only; Task 4 now supplies the physical classification in Theorem 8.3 |
| Former Open issue 8.1 in the Tasks 2–3 note | Historical Task 4 target, now proved as Theorem 8.3 | No source was cited as already proving the decoder-specific logical-parity identity |

The source equality involving $C_1(\mathcal L_{\neg c}^*)$ with retained
boundary labels uses an augmented restricted graph, including its virtual
edge between the non-c boundary vertices. The ordinary physical-edge
bijection $\epsilon_{\neg c}$ does not create that extra edge. NOTATIONS
§3 now names that convention explicitly; the resolved graph's physical
edge set is always just $Q$.

Delfosse's closed-setting projection chain map, Bombín's physical strings
and stabilizer deformation, Kesselring's physical boundary conventions,
and Kubica's local-Clifford unfolding retain the limits recorded above.
None is substituted for the resolved-graph support map or for Task 4.
No further primary source was needed for these constructions, and no
claim of literature novelty or exhaustive nonexistence is made.

## Research Tasks 4–5 source-to-result update — 2026-09-12

Conducted focused primary-source searches for triangular logical boundary
operators, color-code condensation and string-nets, binary complexes and
projection, concatenated matching, unfolding, and Meister's modified graph.
Exact-title and arXiv-domain searches returned the retained core sources.
An additional abstract on Bhagoji–Sarvepalli's two-surface-code mapping
appeared in search results but supplies no input to this proof; it was not
substituted for the decoder-specific map. No novelty claim is made.

Re-extracted and inspected the retained primary PDFs. The supplied Lee PDF
again emitted xref reconstruction warnings; its readable p. 4 boundary
logical statement and the previously audited graph definitions agree.
The proof-critical imported facts are these two independent physical facts:

- Lee §2.1, p. 4: a product of X or Z on any complete physical color
  boundary is the corresponding logical representative, with weight d.
- Bombín–Martín-Delgado p. 3: removing a vertex and the surrounding
  links/faces from the spherical construction gives one encoded qubit.
  The same page describes logical three-string nets and stabilizer
  deformation. These are physical-code inputs, not a stage-2 theorem.

| Note result | Evidence | Limit |
|---|---|---|
| Lemma 8.2, terminal/physical parity | Task 1 terminal incidence plus the two imported physical facts above | New direct overlap derivation on K_c; no surface-code proof used |
| Theorem 8.3, Corollary 8.4 | Our parity proof, physical one-qubit quotient, connectivity and binary graph parity | Full fixed-fiber iff and converse; not every physical representative lies in K_c |
| Proposition 8.6, non-c face cycle basis | Our local M_c parity argument, exact coordinate counts, physical k=1 and connected incidence rank | New all-distance generation and independence proof; no corner relation assumed |
| Definition 8.7, induced complex | Our A_c and chain-map identities; compare Delfosse Definition 3.1 for the binary-complex convention | Algebraic complex with relative vertex coordinates; no unspecified CW attachment or bare-graph homology shortcut |
| §8.3, physical cross-checks | Lee p. 4; Bombín pp. 2–3, Eqs. (4)–(6); Kesselring §§4.2–4.3 | Side/string/string-net consistency; changing physical representatives may change the stage-1 fiber |
| Proposition 9.1, Meister-type graph | Meister §II.B.1, pp. 2–3, compared after the independent color-code proof | Same relative logical structure, inherited weights and quotient; effective checks are D_c, not all physical checks H |
| Corollary 9.2, unmodified path cost | Our contained-simple-path extraction and nonnegative weights | Fixed-color relative-chain minimum; no cluster contraction or unrestricted physical weighted distance claim |

Meister §II.B.1 defines the modified graph by resolving boundary vertices
so that distinct-terminal paths carry logical action and cycles are sums
of X stabilizers, with ordinary graph recovery by identifying boundaries.
The note verifies this structure on the effective stage-2 parity problem.
Meister §II.B.2 uses **positive** weights for the edge-interval metric.
Definitions 7–8, Lemmas 11–12 and Theorem 13 require additional growth,
path, optimal-dual and noise hypotheses; Task 5 does not import them as
established color-code results.

Delfosse Definition 5.5 / Theorem 5.6 remains a projection to restricted
graphs. Kubica §III.B, Theorem 3 remains a local Clifford unfolding to an
attached/folded surface-code structure. Neither is the chain map
$(\iota_{\neg c},T_c,\Lambda_c)$ constructed here.
The retained editions suffice; no new primary paper was needed for the
proof. Scope is the explicit ordinary-boundary odd-distance 6.6.6 family.


## Phase-2A implementation source ledger — 2026-09-12

No new mathematical literature was needed. Local primary-source inspection
and execution used the reference PyMatching fork
`Zihan-Chen-PhMA/PyMatching`, reference `2abf455ef58ee67c4232e7896e1468e7c983f372`,
actual starting HEAD `2fe1b19cabeb05afd073b9ffed20242264f8ca20` (README-only delta).
The completed local implementation is `83cee05cc16d6fce9deafdbbf7952b4b96a7f21e`.
Inspected source: `sparse_blossom/driver/mwpm_decoding.cc`, `user_graph.cc/.h`,
`user_graph.pybind.cc`, `gap_dijkstra/dijkstra_graph.cc/.h`,
`flooder/graph.cc`, `flooder/detector_node.cc`, Python `matching.py`, and
`SO_example/so_sampler.py`, relative to external_libs/PyMatching/src/pymatching
except the repository-level example. The new generic metric lives in
`gap_dijkstra/metric_graph.h`; it does not supply an odd-cut certificate.

Color-code-stim starting HEAD was `3f9f2d447bebdedb43e7d43adee47d2c9fce4afd`
(README-only delta from the earlier inspected reference). Completed local
implementation: `ba6f7dc8b7aaab237d98ad5f08825be4225864c6`. Read/executed
`dem_utils/dem_decomp.py`, `dem_manager.py`, `graph_builder.py`,
`decoders/concat_matching_decoder.py`, `color_code.py`, `simulation/simulator.py`,
and the new `soft_output` package. Typed boundary classification was checked
against independent Tanner incidence and the Phase-1 coordinate construction.
These are implementation results, not new imported mathematical theorems.

Both repositories use dedicated `phase2a/swim-distance` branches. Exact
commands, source deltas and validation are in ../IMPLEMENTATION_STATUS.md;
pilot source hashes are also saved with the per-shot data. Earlier statements
that no decoder experiment was run refer to the Phase-1 checkpoint.

## Phase-2B numerical source audit — 2026-09-12

Reinspected local Lee PDF, Sec. 3.1 and Fig. 3 (printed p. 6): T=1, odd
d=3 through 31, LOWESS fraction 2/3, 99% Student-t intervals for log-linear
scaling coefficients, published crossing about 8.2%, G slope .488 and C slope
1.30. Current local color-code-stim README at ba6f7dc, lines 6 onward, documents
historical duplicate bit-flip injection before and after extraction, and the
corrected expectation about 8.6% with roughly halved LER.

Inspected current getting_started.ipynb and the historical notebook/tree at
53b60e9efb5a691ccdc0a8d1ecab2fb7b76cf301. No exact original Fig. 3 p-grid was
recovered. Use the explicitly authorized fallback, with unknown original arrays
recorded as null in metadata. No historical noise bug was reintroduced.
Primary links: https://quantum-journal.org/papers/q-2025-01-27-1609/ and
https://github.com/seokhyung-lee/color-code-stim/blob/ba6f7dc8b7aaab237d98ad5f08825be4225864c6/README.md .

rsmf 0.2.1 installed source was inspected: RevtexFormatter supplies column
widths; AbstractFormatter construction changes global backend/style. The main
package queries dimensions in an isolated cached subprocess to avoid those
side effects. No new theoretical source or claim is introduced.

## Circuit-level theory audit — 2026-09-12

Authority: [circuit-level prompt](../notes/support/CODEX_CIRCUIT_LEVEL_THEORY_PROMPT.md).
The integrated derivation is Part II of [the note](../notes/note.tex), sourced in
[circuit_level_theory.tex](../notes/support/circuit_level_theory.tex). The new
sources below were already present in `source_audit/circuit_level/` when this
run inspected them; their presence alone was not treated as an audit. We read
the passages listed here and freshly checked primary online records. Older
Phase-1 statements that circuit-level theory is deferred are historical.

| Source / inspected edition | Passages inspected and use | Explicit limitation |
|---|---|---|
| [Lee, 2404.07482v2](https://arxiv.org/html/2404.07482v2), retained original PDF | §4.1 Eqs. (6)–(7); §4.2 Algorithm 1 lines 1–28 and accompanying prose; exact single-Pauli depolarization decomposition | Sector separation discards correlations; stage-1 and stage-2 filters differ; line 6 omits empty-detector parts; same-target compression includes observable targets. Appendix A's static proof is not substituted for circuit algebra. |
| [Meister, 2405.07433v2](https://arxiv.org/abs/2405.07433v2), retained original PDF | Fig. 2 caption p. 6 explicitly mentions a 3D decoding graph for faulty measurements; Definitions 7,9, Lemmas 11–12, Theorem 13 and Appendix B as audited above | Dimension-independent coverage transfers; a color-code logical map and exact certificate are still needed. |
| [Stim DEM format](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md) | Error target parity, logical frame changes, separators, detector shifts and repeats | Separator components are not independent mechanisms. Circuit-to-DEM approximation options must be recorded. |
| [Stim API source](https://github.com/quantumlib/Stim/blob/main/src/stim/dem/detector_error_model.pybind.cc), installed Stim **1.16.0** docstring | `DetectorErrorModel.shortest_graphlike_error`, arguments, examples and return semantics | Minimizes number of mechanisms/components, ignores positive probability magnitudes, skips zero probabilities; cannot validate general weighted log-odds minima. Docstring says “less than two” symptoms while explicitly accepting two-detector errors; use ≤2. Versioned 1.15/1.16 documentation web URLs failed, so they are not claimed as inspected. |
| [Hillmann et al., 2410.12963v2](https://arxiv.org/abs/2410.12963v2), [PDF](source_audit/circuit_level/hillmann_v2.pdf) | pp. 1–3, Eqs. (1)–(6), fault-complex definition, tensor product and logical correlation/error pairing | Defines an algebraic fault complex for foliation/repeated QEC; explicitly distinguishes Bombín's geometric fault-tolerant complexes. Does not identify Lee virtual detectors with product cells. |
| [Delfosse–Paetznick, 2304.05943v2](https://arxiv.org/abs/2304.05943v2), [PDF](source_audit/circuit_level/spacetime_v2.pdf) | Introduction/Theorems 1–3 overview; §3.4 Proposition 3 and its forward/backward commutator proof, p. 12 | Adjoint propagation supports the record-parity pairing. Its spacetime decoder correspondence requires the corresponding fault model, not independent Lee reweighting. |
| [Bombín et al., 2308.07844v1](https://arxiv.org/abs/2308.07844v1), [PDF](source_audit/circuit_level/fault_tolerant_v1.pdf) | §IV resource/syndrome complexes and diagonal/correlated faults; Appendix F Definition 7, p. 14 | Color-code fusion complexes have 3-colorable vertices and triangular 2-skeletons; not a proof of a local cellular representation of a compressed matching graph. |
| [Herzog et al., 2607.05501v1](https://arxiv.org/abs/2607.05501v1), [PDF](source_audit/circuit_level/herzog_v1.pdf) | §III.A–B, Figs. 5–6; standalone triangular prism, preparation/readout faces, vertical logical representatives | This recent preprint supports the protocol-level prism picture. Its d-round standard block, uncolored vertical walls and star-shaped correlation surfaces do not identify Lee matching boundary classes. |
| [Derks et al., 2407.13826v2](https://arxiv.org/abs/2407.13826v2), [PDF](source_audit/circuit_level/derks_v2.pdf) | §2 Definitions 2.6, 2.8–2.9, detector matrix factorization and observable parity, pp. 5–7 | We distinguish record-check matrix from fault-incidence matrix. Online current record is v3; this audit uses the retained **v2**, not uninspected v3 theorem numbering. |
| [Chambers–Erickson–Fox–Nayyeri, *Minimum cuts in surface graphs*](https://ekfox.web.illinois.edu/publications/min-cut-surfaces/min-cut-surfaces.pdf), [retained author PDF](source_audit/circuit_level/homology_covers.pdf) | §5.1, pp. 18–19, voltage-cover vertices/darts, inherited edge weights and path lifting | Direct prior overlap for the cover method. Their surface-homology signatures and advanced complexity results are not imported into the arbitrary DEM graph theorem. Online PDF retrieval timed out; the actual retained PDF was inspected. |

Hillmann's current record lists Phys. Rev. A **112**, L040401 (2025),
[DOI](https://doi.org/10.1103/cjb4-l57n); the retained PDF is v2, dated
October 2025. Herzog authors are Laura S. Herzog, Gilad Kishony, Robert Wille,
and Austin Fowler. The arXiv v1 record is dated 6 July 2026. Bombín's retained
PDF prints eight authors (including Terry Farrelly); shorthand “et al.” avoids
copying an incomplete metadata list. No later edition is silently substituted.

### Fresh overlap search

Fresh web queries included the eight requested arXiv identifiers, “color code
circuit soft output”, “color-code swim distance”, “detector error model shortest
logical cover”, “observable double cover decoding”, “signed graph shortest
unbalanced cycle double cover”, and “logical correlation surface decoding”.
The inspected primary overlaps are Stim's undetected graphlike-error search,
Chambers et al.'s voltage/homology covers, the already audited fractional swim
and nonplanar instrumentation papers, and the five spacetime/DEM sources above.
Searches also returned irrelevant results; they supplied no proof input.
This bounded audit does not establish absence of circuit-level color-code
soft-output prior work. **No novelty or priority claim is made.**

### Current implementation source audit

Read at color-code-stim `ba6f7dc8b7aaab237d98ad5f08825be4225864c6`:
`dem_utils/dem_manager.py:_generate_dem`,
`dem_utils/dem_decomp.py:decompose_org_dem`,
`stim_utils.py:separate_depolarizing_errors` and `dem_to_parity_check`,
`stim_symbolic.py:to_dem`, and
`decoders/concat_matching_decoder.py:_decode_stage1/_decode_stage2` and its
outer observable projection. All are relative to `src/color_code_stim/`.

The manager extracts a DEM after circuit-level X/Z depolarizing separation.
The selected sector marginals have explicit probability formulas; intersector
correlations change and components at ≤1e-15 are omitted. The decomposition
uses complete target dictionary keys but overwrites duplicate keys in its
fallback; joint graphlike filtering precedes stage-1 probability accumulation.
Both discrepancies have read-only finite reproducers in
[check_circuit_theory.py](../notes/support/check_circuit_theory.py).
Stage-2 probability sorting and source-map permutation agree on the ordinary
already-separated unique-target domain. These are implementation observations,
not proof of exact correlated-noise preservation or an exported dual certificate.
