"""Outcome-marked frequency points for selected-color swim distance."""
from pathlib import Path
import numpy as np
import pandas as pd
from .figure_style import RevtexFigureStyle, metric_palette, save_figure
from .selection import select_series
from .statistics import grouped_rates
from .dataset import METRIC_FAILURES


def signed_scores(scores, failures) -> np.ndarray:
    """Return a copy with only logical-error scores negated; never mutate storage."""
    return np.where(np.asarray(failures,dtype=bool), -np.asarray(scores), np.asarray(scores))


class SwimDistanceDistributionPlotter:
    """Plot scatter-style outcome frequencies using shared parameter selections.

    Args:
        style: Publication style by default; explicit test style is supported.
    """
    def __init__(self, style: RevtexFigureStyle | None = None):
        self.style = style or RevtexFigureStyle()

    def plot(self, dataset, *, distance, physical_error_rate, signed_logical_errors=False,
             normalize_frequency=False, bins="auto", round_digits: int | None = None, output_directory: Path | None = None,
             metric="selected_swim_distance", include_forced_gap=False):
        """Save PDF/PNG frequency points and return (figure, count table).

        Args:
            dataset: Phase2ADataset supplying projected rows.
            distance: Scalar or sequence; both parameters cannot be sequences.
            physical_error_rate: Scalar or sequence of grid probabilities.
            signed_logical_errors: Negate error scores for display only.
            normalize_frequency: Divide outcome counts by all shots in that series.
            bins: Shared grouped_rates rule; near-discrete scores rounded to 10 decimals.
            round_digits: Round actual scores before counting; None preserves current grouping.
            include_forced_gap: Overlay forced gap with its comparative failure labels.
                Each metric is normalized separately; forced gap uses blue shades.
            output_directory: Defaults to the run's figures directory.
        Returns:
            Figure and table with series, outcome, plotted score, count and frequency.
        """
        series, suffix = select_series(distance,physical_error_rate)
        metrics = (metric, "forced_gap") if include_forced_gap and metric != "forced_gap" else (metric,)
        names = {"selected_swim_distance": "SWIM", "ordinary_path_gap": "Ordinary path gap",
                 "comparative_path_gap": "Comparative path gap",
                 "ordinary_monotone_y_gap": "Ordinary monotone-Y gap",
                 "comparative_monotone_y_gap": "Comparative monotone-Y gap", "forced_gap": "Forced gap"}
        if metric.endswith(("path_gap", "monotone_y_gap")) and signed_logical_errors:
            raise ValueError("These scores are already signed; do not negate failure scores")
        if round_digits is not None:
            suffix += f"_round{round_digits}"
        tables = []
        with self.style.context():
            figure, axes = self.style.figure(aspect=.85 if len(metrics) > 1 else .65)
            for current_metric in metrics:
                failure_column = METRIC_FAILURES[current_metric]
                colors = metric_palette(current_metric, len(series))
                for item,color in zip(series,colors):
                    rows = dataset.metric_rows(current_metric,distance=item.distance,physical_error_rate=item.physical_error_rate)
                    rates = grouped_rates(rows[current_metric],rows[failure_column],bins=bins,round_digits=round_digits)
                    for failure,marker in ((False,"o"),(True,"x")):
                        count = rates.failures if failure else rates.shots-rates.failures
                        score = -rates.score if failure and signed_logical_errors else rates.score
                        frequency = count/len(rows) if normalize_frequency else count
                        mask = count > 0
                        axes.scatter(score[mask],frequency[mask],marker=marker,color=color,alpha=0.75,
                                     label=(f"{names[current_metric]}, " if len(metrics) > 1 else "") + f"{item.label}, {'error' if failure else 'success'}")
                        tables.append(pd.DataFrame(dict(distance=item.distance,physical_error_rate=item.physical_error_rate,
                            metric=current_metric,failure_column=failure_column,
                            logical_error=failure,score=score,count=count,frequency=frequency)))
            axes.set(
                xlabel=("Soft-output score" if len(metrics) > 1 else "Forced gap" if metric == "forced_gap"
                        else getattr(dataset, "score_label", r"Selected swim distance $\phi$"))
                    + (" (errors negated)" if signed_logical_errors else ""),
                ylabel="Relative frequency" if normalize_frequency else "Frequency",
                yscale="log",
            )
            if getattr(dataset, "plot_title", None):
                axes.set_title(dataset.plot_title)
            if len(metrics) > 1:
                figure.legend(ncol=2, loc="outside upper center", fontsize=8)
            else:
                figure.legend(ncol=3,loc="outside upper center")
            stem = f"swim_distribution_{suffix}" + ("_signed" if signed_logical_errors else "") + ("_normalized" if normalize_frequency else "")
            if metric != "selected_swim_distance":
                stem = stem.replace("swim_distribution", f"{metric}_distribution")
            if len(metrics) > 1:
                stem += "_with_forced_gap"
            save_figure(figure, output_directory or dataset.run_directory / "figures", stem)
        return figure,pd.concat(tables,ignore_index=True)
