"""Exact metric-threshold curves with decoder-specific failure associations."""
from pathlib import Path
import numpy as np
import pandas as pd
from .dataset import METRIC_FAILURES
from .figure_style import RevtexFigureStyle, metric_palette, save_figure
from .selection import select_series


METRIC_MARKERS = {
    "selected_swim_distance": "D",
    "ordinary_path_gap": "v",
    "comparative_path_gap": "P",
    "ordinary_monotone_y_gap": "o",
    "comparative_monotone_y_gap": "^",
    "forced_gap": "s",
}
from .statistics import CONFIDENCE_LEVEL, wilson_interval, rounded_scores


def postselection_curve(scores, failures, confidence_level=CONFIDENCE_LEVEL, *, round_digits: int | None = None) -> pd.DataFrame:
    """Return one point per unique score threshold, including no abort.

    Args:
        scores: Confidence scores, shape (shots,).
        failures: Associated decoder failure labels.
        confidence_level: Wilson coverage probability.
        round_digits: Round actual scores before forming thresholds/ties; None keeps exact raw scores.
    Returns:
        Ascending thresholds/abort rates, retained counts/failures, LER and limits.
    Notes:
        Retain scores >= threshold; abort scores < threshold. Exact ties are
        retained together, without binning. Rounding is opt-in. Empty retention omitted.
    """
    scores,failures = np.asarray(scores),np.asarray(failures,dtype=bool)
    if scores.ndim != 1 or failures.shape != scores.shape or not len(scores) or not np.isfinite(scores).all():
        raise ValueError("Aligned nonempty finite scores and failures required")
    if round_digits is not None:
        scores = rounded_scores(scores, round_digits)
    order = np.argsort(scores,kind="stable")
    thresholds, first = np.unique(scores[order],return_index=True)
    count = len(scores)-first
    errors = np.cumsum(failures[order][::-1])[::-1][first]
    low,high = wilson_interval(errors,count,confidence_level)
    return pd.DataFrame(dict(threshold=thresholds,abort_rate=1-count/len(scores),retained_shots=count,
        retained_failures=errors,residual_logical_error_rate=errors/count,low=low,high=high))


class PostSelectionAnalyzer:
    """Compare swim and comparative threshold curves against abort rate.

    Args:
        style: Central publication or explicit test style.
        confidence_level: Wilson interval probability.
    """
    def __init__(self, style=None, confidence_level=CONFIDENCE_LEVEL):
        self.style = style or RevtexFigureStyle()
        self.confidence_level = confidence_level

    def plot(self, dataset, *, distance, physical_error_rate, include_forced_gap=False,
             round_digits: int | None = None, output_directory: Path | None = None,
             metrics=None, xlim=(0, 1)):
        """Save exact postselection tables and PDF/PNG, returning figure and table.

        Args:
            dataset: Lazy dataset with stable per-shot identities.
            distance: Scalar or sequence.
            physical_error_rate: Scalar or sequence, at most one parameter varies.
            include_forced_gap: Add blue curves with comparative failure labels.
            round_digits: Round each metric before its thresholds; applies to swim and forced gap.
            output_directory: Default run/figures.
            xlim: Displayed abort-rate interval, with 0 <= lower < upper <= 1.
                Zoomed figures/tables have separate filenames; counts are unchanged.
        Notes:
            Tables retain every unique metric threshold, without binning.
            Figures connect all positive-rate points with markers and lines.
            Marker shapes identify metrics consistently across distances and views.
            Wilson bands use the series color at alpha=.2, including upper
            bounds for zero-failure rows; zero lower limits clip at the log axis.
        """
        series,suffix = select_series(distance,physical_error_rate)
        if len(xlim) != 2 or not np.isfinite(xlim).all() or not 0 <= xlim[0] < xlim[1] <= 1:
            raise ValueError("xlim must satisfy 0 <= lower < upper <= 1")
        if tuple(xlim) != (0, 1):
            suffix += f"_xlim{xlim[0]:g}-{xlim[1]:g}"
        if round_digits is not None:
            suffix += f"_round{round_digits}"
        if metrics is None:
            metrics = ["selected_swim_distance"] + (["forced_gap"] if include_forced_gap else [])
        else:
            metrics = tuple(metrics)
            if include_forced_gap or not metrics or len(set(metrics)) != len(metrics) or any(m not in METRIC_FAILURES for m in metrics):
                raise ValueError("Supply unique known metrics without include_forced_gap")
            suffix += "_" + "_".join(metrics)
        tables = []
        with self.style.context():
            figure,axes = self.style.figure()
            for metric in metrics:
                for item,color in zip(series,metric_palette(metric,len(series))):
                    rows = dataset.metric_rows(metric,distance=item.distance,physical_error_rate=item.physical_error_rate)
                    table = postselection_curve(rows[metric],rows[METRIC_FAILURES[metric]],self.confidence_level,round_digits=round_digits)
                    table["metric"] = metric
                    table["failure_column"] = METRIC_FAILURES[metric]
                    table["distance"] = item.distance
                    table["physical_error_rate"] = item.physical_error_rate
                    tables.append(table)
                    # Exact zero residual rates remain available in the saved
                    # table but have no position on a logarithmic y-axis.
                    positive_rate = table.residual_logical_error_rate > 0
                    axes.fill_between(table.abort_rate, table.low, table.high,
                                      color=color, alpha=0.2, linewidth=0, zorder=1)
                    display_name = ("forced gap" if metric == "forced_gap" else
                                    getattr(dataset, "metric_display_name", "swim"))
                    if metric.endswith(("path_gap", "monotone_y_gap")):
                        display_name = metric.replace("_", " ")
                    if metric.endswith("monotone_y_gap"):
                        display_name = metric.split("_", 1)[0] + " monotone-Y"
                    legend_label = item.label if display_name is None else f"{item.label}, {display_name}"
                    axes.plot(table.abort_rate[positive_rate], table.residual_logical_error_rate[positive_rate],color=color,
                              marker=METRIC_MARKERS[metric],
                              linestyle="--" if metric == "forced_gap" else "-",
                              label=legend_label)
            axes.set(
                xlabel="Abort rate",
                ylabel="Residual logical error rate",
                xlim=xlim,
                yscale="log",
            )
            if getattr(dataset, "plot_title", None):
                axes.set_title(dataset.plot_title)
            legend_columns = 2 if any(m.endswith("monotone_y_gap") for m in metrics) else 3
            figure.legend(ncol=legend_columns,loc="outside upper center")
            stem = f"postselection_{suffix}" + ("_paired" if include_forced_gap else "")
            save_figure(figure,output_directory or dataset.run_directory / "figures",stem)
        result = pd.concat(tables,ignore_index=True)
        result.to_parquet(dataset.run_directory / f"{stem}.parquet",index=False)
        return figure,result
