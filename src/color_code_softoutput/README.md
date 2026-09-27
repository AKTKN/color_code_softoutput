# Reproducible paired code-capacity study

The saved-data notebook
`notebooks/circuit_level_swim_selection_strategies.ipynb` compares four
three-color circuit-level output strategies: ordinary selected color, minimum,
maximum and arithmetic mean. Its reusable implementation is
`analysis/swim_selection.py`. It runs distribution, conditional-LER and
post-selection separately for each strategy while preserving the same ordinary
hard decisions and failure labels. It does not sample new shots or define a
production aggregation rule.

Use the Conda environment **color_code_so**. The main package contains experiment,
storage and analysis code. The modified external decoders stay in their own
repositories; installing public PyMatching alone does not provide the required API.

From the project root:

```bash
conda activate color_code_so
# If creating the environment on another machine:
# conda env create -f environment.yml
DEBUG=0 CMAKE_BUILD_PARALLEL_LEVEL=4 python -m pip install --no-build-isolation -e external_libs/PyMatching -e external_libs/color-code-stim -e '.[test,notebook]'
python -m ipykernel install --user --name color_code_so --display-name 'Python (color_code_so)'
python -m pytest tests/phase2b -q
python -m color_code_softoutput.experiments.phase_2a_test --smoke --workers 4
# After smoke review and throughput estimation:
python -m color_code_softoutput.experiments.phase_2a_test --shots 100000 --workers 4 --batch-size 5000
```

The fixed factory uses T=1, triangular 6.6.6, tri_optimal, and only bit-flip noise.
Distances are 3,5,7,9,11,13. The explicit fallback grids are near-threshold
0.076,0.080,0.084,0.088 and subthreshold 0.02,0.03,0.04,0.05. These are project
approximations, not a recovered historical grid. The paper and current/historical
notebooks were inspected; they did not supply the exact original p-grid.

The historical paper version applied bit-flip noise twice; the repository reports
a correction from an 8.2% to about 8.6% threshold and roughly halved LER. This study
uses the corrected local commits. It targets qualitative scaling, not exact old
numbers. See `refs/REFERENCES.md` for the inspected source ledger.

`run_experiment(Phase2ATestConfig(...))` returns a `RunResult`. Shards are written
atomically as batches complete; at most twice the worker count is pending. Stable
config/batch/shot identities and SeedSequence-derived seeds make serial and
parallel schedules equivalent. Changing batch size changes sampling and is recorded.
Resume is intentionally not implemented: failed runs preserve completed shards and
an exception manifest. Restart in a new directory; never stitch runs implicitly.

`Phase2ADataset` projects/filter Parquet columns. `audit_run(dataset)` independently
validates all shards and summary counts, checks current source identities, and
replays one full batch. `standard_analysis(run_directory)` creates PDF/PNG plots,
Parquet analyses and `PRIOR_WORK_REPRODUCTION.md`. Classes for each analysis also
work separately; examples are in `notebooks/phase2a_getting_started.ipynb`.

Publication figures use rsmf and RevTeX dimensions and fail if TeX is unavailable.
System requirements: a TeX distribution with revtex4-2, type1cm, cm-super/type1ec,
and dvipng. `RevtexFigureStyle(test_mode=True)` is an explicit CI-only alternative.
Point sizes convert TeX to Matplotlib with 72/72.27. The style restores rcParams.

Statistics use 99% Wilson intervals with retained counts. Conditional-LER,
post-selection (including forced gap), and physical-error-rate plots show
these intervals as shaded bands in the series color with `alpha=0.2`.
Zero-failure upper bounds remain visible; zero lower bounds clip at the
logarithmic axis boundary without altering stored values. Scaling is unweighted
log-OLS with Student-t intervals and explicit exclusion of zero-failure points;
three positive-rate points are required. Crossing is minimum cross-distance
variance of LOWESS (fraction 2/3, it=3) curves interpolated onto 2001 common-grid
points. Endpoint minima are flagged, and no threshold CI is fabricated. Four-point
LOWESS and distances only through 13 limit the inference.

Conditional logit fits predict success: logit P(success|phi)=k phi+l. Degenerate,
separated and nonconverged fits retain explicit statuses and NaN coefficients.
These empirical fits do not establish posterior calibration. Near-discrete values
are grouped after rounding to 10 decimals for distributions/conditional rates;
continuous scores use configurable histogram bins. Empty bins are omitted.

Frequency, conditional-LER, and post-selection plots use a logarithmic y-axis
by default. Zero empirical rates remain in the saved tables with their Wilson
limits, but are omitted from the log-scale artists because zero has no finite
logarithm. The Lee Fig. 3 near-threshold plot deliberately stays linear in y;
the sub-threshold reproduction uses log-log axes. Coefficient plots stay linear
because fitted coefficients can be signed.

Postselection uses every exact unique metric value as a threshold, sorted in
ascending order, without binning or rounding by default. At threshold `t`, scores `< t`
are aborted and scores `>= t` are retained together, including all exact ties.
Tables include the threshold, abort rate, retained counts, residual LER and Wilson
limits; the minimum threshold gives no abort. Figures connect all positive-rate
points with circle markers and lines, without subsampling.
All three plot methods accept `round_digits=None` (the existing numerical
behavior) or an integer number of decimal places. For example,
`round_digits=1` applies Python `round(value, 1)` to each actual score before
counting, fitting or thresholding; negative digits are also supported. Auto
bins then group every distinct rounded score, while explicit histogram bins
still take precedence. Post-selection keeps whole ties in the rounded scores,
including for forced gap. This never modifies stored shot values. Rounded
figure/table filenames include `_roundN`, keeping them separate from defaults.
The circuit notebook exposes one `round_digits` setting for its three plots.

Swim series use `YlGn`; three series take colors at .4, .7 and .95 in selection
order. Forced-gap series use `Blues` at the same positions. Distribution scatter
markers remain `o` (success) and `x` (error), with alpha=.75.

Swim uses ordinary failures; forced_gap uses comparative failures.
The latter is an alias of the existing comparative logical gap, also stored under
its source name for verification. Selected swim always uses the ordinary decoder's
chosen color, never minimum-over-colors aggregation.

The backend convention remains uncertified final defect metric balls. Missing
nonnegative optimal odd-cut variables and exact primal/dual equality prevent
applying the Phase-1 representative bound to these numerical scores. No full
three-color logical-gap, LLR, or circuit-level theorem is claimed.
