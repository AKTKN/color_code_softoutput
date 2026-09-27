# Phase-1 finite proof checks

The completed closed-memory circuit implementation is documented in
[CIRCUIT_LEVEL_IMPLEMENTATION.md](CIRCUIT_LEVEL_IMPLEMENTATION.md), with its
compact [algorithm section](circuit_level_swim_algorithm.tex) integrated into
the main note. Its component and end-to-end checks are under
`tests/circuit_level/`; the older finite theory checks below remain separate.

Run from the repository root:

```bash
python notes/support/check_phase1.py
```

The checked environment is Python 3.12.7, NumPy 1.26.4 and SciPy 1.13.1.
The script reads no external data and writes no files. It constructs the
note's triangular family directly and verifies:

- Incidence, boundary counts, GF(2) ranks, physical syndrome factorization,
  and the non-c face cycle basis for all three colors at d=3,5,7,9,11.
- All 128 physical supports at d=3 in each color: relative-chain physical
  syndrome and stabilizer/logical classification.
- All 16 stage-2 syndromes at d=3, in three colors and three prescribed
  weight sets (unit, unequal positive, and zero-containing): 144 instances.
- Exhaustive minimum correction and opposite-class costs against the
  nonnegative odd-cut dual LP; covered-weight and representative-gap
  inequalities, including empty syndrome and ties.
- Two heap searches for coverage and shortest path, compared to an
  independent all-pairs metric/explicit interval-subdivision oracle.
  Returned edge-labelled paths have zero physical syndrome and nontrivial
  logical class, including zero-cost paths.
- Partial and overlapping coverage, both-terminal clusters, disconnected
  terminals, and counterexamples to endpoint-ID zeroing and nonoptimal
  dual substitution. The exact d=3 single-red-face example is checked.

Support enumeration and binary linear algebra are exact. HiGHS LP
solutions and real-length comparisons use floating-point arithmetic with
1e-8 tolerances; these are not exact rational certificates. The general
proofs in [the note](../note.tex) establish the theorems. This script is
neither a production decoder nor a performance/calibration experiment.
Its all-pairs oracle and explicit exponential dual are deliberately small.
No public PyMatching dual extraction is implemented.

To rebuild the note from the repository root:

```bash
mkdir -p /tmp/color-code-phase1-build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/color-code-phase1-build notes/note.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/color-code-phase1-build notes/note.tex
cp /tmp/color-code-phase1-build/note.pdf notes/note.pdf
```

No BibTeX pass is needed. Keep intermediate TeX artifacts outside the repo.
The final audited PDF has 25 pages and a warning-free second build pass.

## Circuit-level theory and task documents

New theoretical research prompts and detailed research Markdown live in this
directory. The completed [theory summary](CIRCUIT_LEVEL_THEORY.md) explains the
results of [the prompt](CODEX_CIRCUIT_LEVEL_THEORY_PROMPT.md); the
[sketch](CIRCUIT_LEVEL_THEORY_SKETCH.md) retains its historical proposal status.
The TeX source [circuit_level_theory.tex](circuit_level_theory.tex) is included
by [the integrated note](../note.tex), not a standalone compilation target.
The Phase-1 25-page build record above is historical.

Run the finite theory checks in the project environment, from the root:

```bash
conda run -n color_code_so python notes/support/check_circuit_theory.py
conda run -n color_code_so python notes/support/check_phase1.py
```

The circuit script samples no physical shots and modifies no decoder source.
It exhausts tiny binary mechanism sets, tests cover/cut/gauge and zero-cost
witness logic, compares compatible unit-cost cases with Stim 1.16.0, and
reproduces two current decomposition discrepancies. The d=3,T=1/2 actual
measurement-noise DEMs have 10/13 columns per color; full enumeration is
1024/8192 subsets. The additional uniform circuit-noise d=3,T=2 example has
49 columns and is a matrix/cover audit only, **not** exhaustive enumeration.
These finite checks support the mathematical proofs; they are not a campaign,
performance test, posterior calibration, or production dual certification.

Rebuild the integrated PDF from the project root:

```bash
mkdir -p /tmp/color-code-circuit-build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/color-code-circuit-build notes/note.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/color-code-circuit-build notes/note.tex
cp /tmp/color-code-circuit-build/note.pdf notes/note.pdf
```

Bibliography is embedded in the main TeX; no BibTeX pass is needed. Keep
intermediate build files outside the workspace. The completed integrated
PDF has 39 pages; its final build has no warnings or unresolved references.
All 15 circuit formal-claim labels and citations resolve, and the cover/cut
pages were visually inspected. Both finite-check scripts pass in
`color_code_so`; the circuit output is saved in
[circuit_theory_checks.log](circuit_theory_checks.log).
The current primary-source
ledger and review are [REFERENCES](../../refs/REFERENCES.md) and
[REVIEW](../../REVIEW.md), respectively.
