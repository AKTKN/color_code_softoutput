# Stage-2 prior comparison figure and separate legends

The final manuscript-export section of
`notebooks/color_correlated_decoding.ipynb` reads only
`Stage2_original_perturbation` and `Stage2_perturbed_perturbation` from
`cluster_results/26_09_28_14_38_26_779e2a31`. It uses the existing
`ColorCorrelatedRun.plot_ler` and `plot_legends` APIs. The default export
shows no ordinary baseline and uses colors for d=7,9,11 and markers for the
stage-2 prior choice. The plot uses the source failure labels and Wilson
intervals without pooling shots between the two variants.

## Generated files

Output directory:
`cluster_results/26_09_28_14_38_26_779e2a31/analysis/stage2_prior_comparison/`.

- `stage2_prior_ler.pdf`: vector main plot.
- `stage2_prior_ler_legend_distance.pdf`: distance/color legend.
- `stage2_prior_ler_legend_decoder_alias.pdf`: stage-2 prior/marker legend.
- Corresponding PNGs for quick viewing.
- `figure_stage2_prior.tex`: editable figure placement template.
- `stage2_prior_paragraph.tex`: English paragraph/enum/reference example.
- `preview_stage2_prior.tex` and `.pdf`: compiled one-page layout preview.

The checked-in placement source is `notes/support/stage2_prior_figure.tex`,
and the paragraph source is `notes/support/stage2_prior_figure_paragraph.tex`.
Generated assets are excluded by the project's existing .gitignore.
The PDF assets can be regenerated in the notebook; the TeX templates remain
independent so manuscript-specific placement edits do not affect plotting.

## Preferred: compile a captionless composite PDF

Use `notes/support/stage2_prior_standalone.tex`. Copy it alongside the three
notebook-exported PDFs and run:

```sh
pdflatex -interaction=nonstopmode -halt-on-error stage2_prior_standalone.tex
```

The generated `stage2_prior_standalone.pdf` contains both legends and the plot,
without a caption. `standalone` with `border=0pt` crops the page to the content.
The enclosing minipage has an explicit 170mm width; change StageTwoCanvasWidth
to the intended manuscript width to control final font scaling.
StageTwoVerticalGap (currently 1mm) controls the deliberate legend/plot gap.
There is no figure float inside this standalone file.

The supplied trim removes exactly the existing Matplotlib export padding:
`0.03in = 2.16bp` on each side. For future exports, prefer
`savefig(..., bbox_inches="tight", pad_inches=0)` and set all four trim values
on each includegraphics line to zero. Standalone crops its outer page but
cannot automatically remove whitespace inside imported PDFs. Do not trim
axis labels or legend text. A small border such as 0.5pt may be useful if
viewers visually clip antialiased content at the page boundary.

Copy only the composite PDF into the manuscript's figures/ directory:

```tex
% main.tex preamble
\usepackage{graphicx}

% main.tex body (figure* for a two-column-wide figure)
\begin{figure}[tbp]
    \centering
    \includegraphics[width=\linewidth]{figures/stage2_prior_standalone.pdf}
    \caption{Comparison of original and perturbed priors for stage-2 matching.}
    \label{fig:stage2-prior-comparison}
\end{figure}
```

The caption and label belong in main.tex; put the label after the caption.
The composed PDF remains vector graphics. After editing layout parameters,
recompile the standalone file before compiling main.tex.
The generated captionless PDF was compiled and rendered for visual inspection;
legend and axis labels remain visible with tight outer margins.

## Alternative: compose directly in the manuscript

Copy the three PDFs to the manuscript's `figures/` folder and copy the
placement template to the manuscript folder. Add to its preamble:

```tex
\usepackage{graphicx}
\graphicspath{{figures/}}
```

Insert the template where the figure should be declared:

```tex
\input{stage2_prior_figure.tex}
```

Reference it with `Fig.~\ref{fig:stage2-prior-comparison}`. The label follows
the caption. Compile twice to resolve the reference. The file extension can
be explicit as in the template. The figure uses only standard graphicx and
minipage constructs; it does not require subcaption or caption packages.
For a two-column manuscript, change both `figure` tags to `figure*` for a
full-width figure. Keep `figure` for one-column placement.

## Adjust placement in LaTeX

The template's five commands control the layout:

```tex
\providecommand{\StageTwoPlotWidth}{\linewidth}
\providecommand{\StageTwoDistanceWidth}{0.44\linewidth}
\providecommand{\StageTwoPriorWidth}{0.47\linewidth}
\providecommand{\StageTwoLegendGap}{0.04\linewidth}
\providecommand{\StageTwoVerticalGap}{2mm}
```

- PlotWidth scales the main plot.
- DistanceWidth and PriorWidth scale the independent legend panels.
- LegendGap is the horizontal gap between panels; keep their widths plus
  this gap at or below one linewidth.
- VerticalGap is the gap between the legends and main plot.

`[t]`, `\vspace{0pt}` and minipages align the two legend panels at their top.
The initial widths .44 and .47 give approximately equal font scaling for
these particular exported legend PDFs. Their natural widths are different;
using equal TeX widths would give different visible text sizes.

`width` scales all contents, including fonts and markers. It does not change
only the label fontsize. For unwanted PDF whitespace, graphicx provides:

```tex
\includegraphics[width=\linewidth,
    trim={0pt 2pt 0pt 2pt},clip]{stage2_prior_ler_legend_distance.pdf}
```

The trim order is **left, bottom, right, top**. Start at zero and adjust
small amounts to avoid cropping labels. The exports already use tight
bounding boxes with a small pad.

## Adjust legend contents and fonts in the notebook

Edit the dedicated export cell before rerunning it:

- `stage2_display_labels`: human-readable prior labels; stored aliases stay
  unchanged.
- `legend.get_title().set_text(...)`: legend title.
- `legend.get_title().set_fontsize(...)`: title font size in points.
- `label.set_fontsize(...)`: item font size in points.
- `legend.set_ncols(...)`: number of columns.
- `legend_figure.set_size_inches(width, height)`: independent canvas size.
- `plot_width`/`plot_height`: main axes dimensions in inches.

For example, make just the prior legend vertical with larger text:

```python
legend_figure, legend_axes = stage2_legends["decoder_alias"]
legend = legend_axes.get_legend()
legend.set_ncols(1)
legend.get_title().set_fontsize(12)
for label in legend.get_texts():
    label.set_fontsize(12)
legend_figure.set_size_inches(3.4, 1.2)
legend_figure.savefig(
    stage2_output / "stage2_prior_ler_legend_decoder_alias.pdf",
    bbox_inches="tight", pad_inches=0.03,
)
```

If rebuilding the legend to tune spacing, preserve the existing handles:

```python
handles = legend.legend_handles
labels = [label.get_text() for label in legend.get_texts()]
legend_axes.legend(
    handles, labels, title="Stage-2 prior", loc="center",
    ncol=2, fontsize=11, title_fontsize=11, frameon=False,
    columnspacing=1.2, handletextpad=0.5, labelspacing=0.4,
)
```

These spacings are relative to font size. Re-export the PDF and recompile
LaTeX to see the effect. `plt.close` only closes display windows; figure
objects held in stage2_legends can still be edited and saved.

## Caption and wording

The saved run uses **M=16**, alpha=1, one round, independent bit-flip noise,
d=7/9/11 and 1,000,000 shots per point. M includes the unperturbed baseline
member. Both variants perturb stage 1, and both use unchanged original X/Z
DEM log odds for final selection. Shading shows 99% Wilson intervals.
Use “perturbed” rather than “perturbated” in manuscript prose.
This figure compares stage-2 prior choices; a claim comparing perturbation
with color-correlated decoding needs a separate comparison figure/table.

## Validation

The dedicated notebook plotting code exported 30 source rows (15 physical
conditions times two variants). The layout was compiled with pdflatex and
rendered for visual inspection; it fits on one page, with aligned legends
and readable matching text sizes. Source metrics and simulation code were
unchanged. No new sampling ran.
