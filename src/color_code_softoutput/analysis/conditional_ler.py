"""Empirical conditional rates and success-logit fit parameter figures."""
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.special import expit
from .dataset import METRIC_FAILURES
from .figure_style import RevtexFigureStyle, metric_palette, save_figure
from .selection import select_series
from .statistics import CONFIDENCE_LEVEL, grouped_rates, logistic_fit, rounded_scores


class ConditionalLERAnalyzer:
    """Analyze ordinary failure versus selected swim with shot-level logistic fits.

    Args:
        style: Shared publication style or explicit CI test style.
        confidence_level: Binomial and regression interval coverage, default .99.
    """
    def __init__(self, style=None, confidence_level=CONFIDENCE_LEVEL):
        self.style = style or RevtexFigureStyle()
        self.confidence_level = confidence_level

    def plot(self, dataset, *, distance, physical_error_rate, bins="auto", overlay_fit=True,
             round_digits: int | None = None, output_directory: Path | None = None,
             metric="selected_swim_distance"):
        """Save conditional LER and fit-table Parquet; return figure, bins and fits.

        Args:
            dataset: Validated lazy dataset.
            distance: Scalar/list selection.
            physical_error_rate: Scalar/list selection; at most one list.
            bins: Near-discrete grouping or histogram bins.
            overlay_fit: Draw fitted P(failure)=expit(-k*phi-l) for valid fits.
            round_digits: Round actual scores before grouping and fitting; None keeps prior behavior.
            output_directory: Figure destination, default run/figures.
        Returns:
            Figure with shaded Wilson bands (alpha=.2), empirical count table,
            and coefficient/status table. Zero lower limits are clipped by the
            logarithmic axis; numerical intervals remain unchanged.
        """
        series,suffix = select_series(distance,physical_error_rate)
        failure = METRIC_FAILURES[metric]
        if metric != "selected_swim_distance":
            suffix += f"_{metric}"
        if round_digits is not None:
            suffix += f"_round{round_digits}"
        tables,fits = [],[]
        with self.style.context():
            figure,axes = self.style.figure()
            for item,color in zip(series,metric_palette(metric,len(series))):
                rows = dataset.metric_rows(metric,distance=item.distance,physical_error_rate=item.physical_error_rate)
                scores = rounded_scores(rows[metric], round_digits)
                rates = grouped_rates(rows[metric],rows[failure],bins=bins,confidence_level=self.confidence_level,round_digits=round_digits)
                fit = logistic_fit(scores,rows[failure],self.confidence_level)
                for table in (rates,fit):
                    table["distance"] = item.distance
                    table["physical_error_rate"] = item.physical_error_rate
                    table["varying_parameter"] = item.varying_parameter
                    table["varying_value"] = item.varying_value
                tables.append(rates);fits.append(fit)
                # A zero empirical rate has a meaningful Wilson upper bound, but
                # no finite position on the default logarithmic y-axis. Keep it
                # in ``rates`` and omit only its visual marker.
                positive_rate = rates.logical_error_rate > 0
                axes.fill_between(rates.score, rates.low, rates.high,
                                  color=color, alpha=0.2, linewidth=0, zorder=1)
                axes.plot(rates.score[positive_rate], rates.logical_error_rate[positive_rate],
                          linestyle="none", marker="o", color=color, label=item.label)
                if overlay_fit and fit["fit_status"] == "ok":
                    x = np.linspace(scores.min(),scores.max(),200)
                    fitted_rate = expit(-fit["k"]*x-fit["l"])
                    positive_fit = fitted_rate > 0
                    axes.plot(x[positive_fit], fitted_rate[positive_fit], color=color)
            axes.set(
                xlabel=getattr(dataset, "score_label", r"Selected swim distance $\phi$"),
                ylabel=getattr(dataset, "conditional_ler_label", r"$P(\mathrm{logical\ error}\mid\phi)$"),
                yscale="log",
            )
            if getattr(dataset, "plot_title", None):
                axes.set_title(dataset.plot_title)
            figure.legend(ncol=3,loc="outside upper center")
            save_figure(figure,output_directory or dataset.run_directory / "figures",f"conditional_ler_{suffix}")
        fit_table = pd.DataFrame(fits)
        fit_table.to_parquet(dataset.run_directory / f"logistic_fits_{suffix}.parquet",index=False)
        return figure,pd.concat(tables,ignore_index=True),fit_table

    def plot_parameters(self, fit_table: pd.DataFrame, *, output_directory: Path, suffix: str) -> list:
        """Save separate k and l figures with intervals; return the two figures.

        Args:
            fit_table: Returned shot-level fit table, including statuses and bounds.
            output_directory: Destination for PDF and PNG.
            suffix: Descriptive fixed/varying parameter identity.
        Notes:
            Failed fits stay in the table and are omitted from finite plots.
        """
        valid = fit_table[fit_table.fit_status == "ok"].sort_values("varying_value")
        figures = []
        with self.style.context():
            for key in ("k","l"):
                figure,axes = self.style.figure()
                if len(valid):
                    axes.errorbar(valid.varying_value,valid[key],
                        yerr=np.maximum(0,np.array([valid[key]-valid[f"{key}_low"],valid[f"{key}_high"]-valid[key]])),
                        fmt="o-",color=metric_palette("selected_swim_distance",1)[0])
                else:
                    axes.text(.5,.5,"No identifiable logistic fits",ha="center",transform=axes.transAxes)
                label = "Distance" if fit_table.varying_parameter.iloc[0] == "distance" else "Physical error rate"
                axes.set(xlabel=label,ylabel=f"Fitted ${key}$")
                save_figure(figure,output_directory,f"logit_{key}_{suffix}")
                figures.append(figure)
        return figures
