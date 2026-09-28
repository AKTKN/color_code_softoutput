# Ensemble-size manuscript figure

The last section of `notebooks/color_correlated_decoding.ipynb` creates the
figure at p=0.03 without sampling. It uses
`analysis.ensemble_size.plot_ensemble_size(run, physical_error_rate=0.03)`.
The function returns `(figure, axes, table, legends)`; legends maps distance
and decoder to separate `(figure, axes)` pairs. `ensemble_size_table` also
provides the data alone, including aliases, actual M from saved options,
counts, Wilson intervals, and source provenance. Selection supports filter
and reference_alias for a renamed imported Tesseract alias. Include both
ensemble and reference aliases when filtering by decoder_alias.

The primary run is `26_09_28_15_33_34_7f861167`; Tesseract is selected from
`26_09_28_14_38_26_779e2a31` with ColorCorrelatedComparison. Baseline uses the
existing deterministic representative rule (m12 in this run), not pooled
failure counts. Per-M baselines were independently sampled; a single
representative is drawn as a horizontal reference, with its own interval.
Different decoder settings besides ensemble size and duplicate distance/M
points are rejected instead of silently combining them. Uniform-noise LER
uses the existing per-round conversion; this run is one-round bit-flip noise.

Exports are in the primary run's `analysis/ensemble_size/`:

- ensemble_size_ler.pdf/png: plot without legends.
- ensemble_size_legend_distance.pdf/png and ensemble_size_legend_decoder.pdf/png.
- ensemble_size_ler.csv: 21 ensemble and six reference rows, with provenance.
- ensemble_size_standalone.tex/pdf: composed captionless vector figure.
- main_tex_inclusion.tex: manuscript inclusion and caption example.

All Matplotlib exports use bbox_inches="tight", pad_inches=0. The standalone
class uses border=0pt; no trimming of these source PDFs is necessary. Edit
EnsembleCanvasWidth (170mm), EnsembleDistanceWidth, EnsembleDecoderWidth,
EnsembleLegendGap and EnsembleVerticalGap in the output TeX, then recompile
with `pdflatex -interaction=nonstopmode -halt-on-error ensemble_size_standalone.tex`.
The notebook copies the template only when absent, preserving layout edits.
Its last cell requires pdflatex on PATH and recompiles the layout each time.
Distance/decoder legend widths are proportional to their natural PDF widths,
so their displayed text sizes are approximately equal.

Copy ensemble_size_standalone.pdf into your manuscript's figures/ and use
`notes/support/ensemble_size_main_inclusion.tex` (also exported beside the PDF).
Keep caption and label in main.tex; use figure* for full-width two-column
placement. Edit legend fonts, columns and text on the returned legend axes
before saving. No data is pooled or interpolated; straight segments join
only observed M values. Zero LER observations have intervals only.
