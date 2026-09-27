"""Coarse Lee Fig. 3 comparison with explicit project fitting estimators."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.nonparametric.smoothers_lowess import lowess
from .statistics import CONFIDENCE_LEVEL, wilson_interval
from .figure_style import RevtexFigureStyle, metric_palette, save_figure
from ..simulation.config import HISTORICAL_NOTE


def crossing_estimate(summary: pd.DataFrame, points: int = 2001) -> dict:
    """Minimize cross-distance variance of LOWESS/interpolated LER curves.

    Args:
        summary: Rows with distance, physical_error_rate, shots, ordinary_failures.
        points: Dense common-grid resolution, default 2001.
    Returns:
        Project estimate, variance and status; not a confidence interval.
    Notes:
        LOWESS uses fraction 2/3, it=3; linear interpolation follows smoothing.
        Only the common p range is searched. Endpoint minima are flagged.
        With four input probabilities LOWESS has little smoothing information.
    """
    curves = []
    groups = list(summary.groupby("distance"))
    if len(groups) < 2 or any(len(g) < 2 for _,g in groups):
        return dict(threshold=None,status="insufficient_curves",variance=None)
    lower = max(g.physical_error_rate.min() for _,g in groups)
    upper = min(g.physical_error_rate.max() for _,g in groups)
    if lower >= upper:
        return dict(threshold=None,status="no_common_range",variance=None)
    grid = np.linspace(lower,upper,points)
    for _,group in groups:
        smooth = lowess(group.ordinary_failures/group.shots,group.physical_error_rate,frac=2/3,it=3,return_sorted=True)
        curves.append(np.interp(grid,smooth[:,0],smooth[:,1]))
    variance = np.var(curves,axis=0)
    best = int(np.argmin(variance))
    return dict(threshold=float(grid[best]), variance=float(variance[best]),
                status="endpoint_minimum" if best in (0,points-1) else "interior_minimum",
                estimator="minimum variance across LOWESS frac=2/3 curves on 2001-point common linear grid",
                search_interval=[float(lower),float(upper)])


def scaling_fits(summary: pd.DataFrame, confidence_level=CONFIDENCE_LEVEL) -> pd.DataFrame:
    """Fit log(LER)=G log(p)+C by unweighted OLS, excluding reported zero failures.

    Args:
        summary: Subthreshold count rows only.
        confidence_level: Student-t OLS interval coverage, default .99.
    Returns:
        Per-distance estimates, SEs, intervals, used/excluded counts and statuses.
    Notes:
        No epsilon is added. At least three nonzero points are required for
        finite residual degrees of freedom. Finite-count log-rate bias remains.
    """
    records = []
    for distance,group in summary.groupby("distance"):
        keep = group.ordinary_failures > 0
        used = group[keep]
        record = dict(distance=distance,points_used=int(keep.sum()),points_excluded=int((~keep).sum()),
                      excluded_probabilities=json.dumps(group.loc[~keep,"physical_error_rate"].tolist()),
                      fit_status="ok", total_failures=int(group.ordinary_failures.sum()))
        record.update({key:np.nan for key in ("G","C","G_se","C_se","G_low","G_high","C_low","C_high")})
        if len(used) < 3:
            record["fit_status"] = "insufficient_nonzero_points"
        else:
            fit = sm.OLS(np.log(used.ordinary_failures.to_numpy()/used.shots.to_numpy()),
                         sm.add_constant(np.log(used.physical_error_rate.to_numpy()))).fit()
            bounds = fit.conf_int(alpha=1-confidence_level)
            for index,key in enumerate(("C","G")):
                record.update({key:fit.params[index],f"{key}_se":fit.bse[index],
                               f"{key}_low":bounds[index,0],f"{key}_high":bounds[index,1]})
        records.append(record)
    return pd.DataFrame(records)


def scaling_trends(fits: pd.DataFrame, confidence_level=CONFIDENCE_LEVEL) -> pd.DataFrame:
    """Regress valid G(d) and C(d) against d; return slope/intercept and t intervals."""
    valid = fits[fits.fit_status == "ok"]
    records = []
    for key in ("G","C"):
        record = dict(parameter=key,distances_used=len(valid),fit_status="insufficient_distances",
                      slope=np.nan,intercept=np.nan,slope_se=np.nan,slope_low=np.nan,slope_high=np.nan)
        if len(valid) >= 3:
            fit = sm.OLS(valid[key].to_numpy(),sm.add_constant(valid.distance.to_numpy())).fit()
            bounds = fit.conf_int(alpha=1-confidence_level)
            record.update(fit_status="ok",slope=fit.params[1],intercept=fit.params[0],slope_se=fit.bse[1],
                          slope_low=bounds[1,0],slope_high=bounds[1,1])
        records.append(record)
    return pd.DataFrame(records)


class LeeFig3ReproductionAnalyzer:
    """Generate near-threshold/scaling figures, fit tables and a bounded comparison.

    Args:
        style: Publication style unless explicitly set to CI test mode.
        confidence_level: Wilson and OLS interval coverage probability.
    """
    def __init__(self, style=None, confidence_level=CONFIDENCE_LEVEL):
        self.style = style or RevtexFigureStyle()
        self.confidence_level = confidence_level

    def analyze(self, dataset) -> dict:
        """Analyze stored ordinary counts; save PDF/PNG, Parquet and Markdown report.

        Args:
            dataset: Audited Phase2ADataset; summary.parquet must match raw counts.
        Returns:
            Crossing result, scaling fit table and trend table.
        Notes:
            This reduced-grid estimate is not an exact historical reproduction.
        """
        directory = dataset.run_directory
        summary = pd.read_parquet(directory / "summary.parquet")
        summary["ordinary_logical_error_rate"] = summary.ordinary_failures/summary.shots
        summary["ordinary_low"], summary["ordinary_high"] = wilson_interval(summary.ordinary_failures,summary.shots,self.confidence_level)
        summary["confidence_level"] = self.confidence_level
        summary.to_parquet(directory / "empirical_rates.parquet",index=False)
        config = dataset.metadata["resolved_config"]
        near = summary[summary.physical_error_rate.isin(config["near_threshold_ps"])]
        sub = summary[summary.physical_error_rate.isin(config["subthreshold_ps"])]
        crossing = crossing_estimate(near)
        fits = scaling_fits(sub,self.confidence_level)
        trends = scaling_trends(fits,self.confidence_level)
        fits.to_parquet(directory / "fit_results.parquet",index=False)
        trends.to_parquet(directory / "scaling_trends.parquet",index=False)
        (directory / "crossing.json").write_text(json.dumps(crossing,indent=2)+"\n")
        with self.style.context():
            for name,subset in (("near_threshold",near),("subthreshold",sub)):
                figure,axes = self.style.figure()
                if subset.empty:
                    axes.text(.5, .5, f"No {name.replace('_', ' ')} samples configured",
                              ha="center", transform=axes.transAxes)
                    axes.set(xlabel="Physical error rate", ylabel="Ordinary logical error rate")
                    save_figure(figure, directory / "figures", f"lee_fig3_{name}")
                    import matplotlib.pyplot as plt
                    plt.close(figure)
                    continue
                for (distance,group),color in zip(subset.groupby("distance"),metric_palette("selected_swim_distance",subset.distance.nunique())):
                    group = group.sort_values("physical_error_rate")
                    rate = group.ordinary_failures/group.shots
                    low,high = wilson_interval(group.ordinary_failures,group.shots,self.confidence_level)
                    axes.fill_between(group.physical_error_rate,low,high,
                                      color=color,alpha=0.2,linewidth=0,zorder=1)
                    visible = rate > 0 if name == "subthreshold" else np.ones(len(rate),dtype=bool)
                    axes.plot(group.physical_error_rate[visible],rate[visible],
                              linestyle="none",marker="o",color=color,label=f"d={distance}")
                    if name == "near_threshold":
                        smooth = lowess(rate,group.physical_error_rate,frac=2/3,it=3)
                        axes.plot(smooth[:,0],smooth[:,1],color=color)
                    else:
                        fit = fits[fits.distance == distance].iloc[0]
                        if fit.fit_status == "ok":
                            x = np.linspace(group.physical_error_rate.min(),group.physical_error_rate.max(),100)
                            axes.plot(x,np.exp(fit.G*np.log(x)+fit.C),color=color)
                axes.set(xlabel="Physical error rate",ylabel="Ordinary logical error rate")
                if name == "subthreshold":
                    axes.set(xscale="log",yscale="log")
                else:
                    # Fig. 3's near-threshold crossing view is the deliberate
                    # exception to the package's logarithmic-y default.
                    axes.set_yscale("linear")
                    for reference,label,style in ((.082,r"Published $8.2\%$",":"),(.086,r"Corrected expectation $8.6\%$","--")):
                        axes.axvline(reference,color=metric_palette("forced_gap",1)[0],linestyle=style,label=label)
                figure.legend(ncol=3,loc="outside upper center")
                save_figure(figure,directory / "figures",f"lee_fig3_{name}")
                import matplotlib.pyplot as plt
                plt.close(figure)
            for key in ("G","C"):
                figure,axes = self.style.figure()
                valid = fits[fits.fit_status == "ok"]
                axes.errorbar(valid.distance,valid[key],yerr=np.maximum(0,np.array([valid[key]-valid[f"{key}_low"],valid[f"{key}_high"]-valid[key]])),fmt="o",color=metric_palette("selected_swim_distance",1)[0])
                trend = trends[trends.parameter == key].iloc[0]
                if trend.fit_status == "ok":
                    axes.plot(valid.distance,trend.slope*valid.distance+trend.intercept,color=metric_palette("selected_swim_distance",1)[0])
                axes.set(xlabel="Distance",ylabel=f"${key}(d)$")
                save_figure(figure,directory / "figures",f"lee_fig3_{key}_trend")
                plt.close(figure)
        threshold = crossing["threshold"]
        estimate = f"{threshold:.5f}" if threshold is not None else "unavailable"
        lines = ["# Prior-work reproduction", "", f"Distances: {config['distances']}. Near-threshold p: {config['near_threshold_ps']}. Subthreshold p: {config['subthreshold_ps']}.",
                 f"Fixed shots per point: {config['shots_per_point']}; workers: {config['num_workers']}; sampling wall time: {dataset.metadata.get('elapsed_seconds',0):.1f} s.",
                 "", "The grid is the explicit project fallback; the original exact sampling grid was not recovered from the paper or inspected current/historical notebooks.",
                 "", f"Project coarse crossing estimate: **{estimate}** ({crossing['status']}). Estimator: LOWESS fraction 2/3, followed by linear interpolation and minimum cross-distance variance on 2001 common-grid points. No threshold confidence interval is inferred.",
                 "", HISTORICAL_NOTE,
                 "Sources: [Lee et al., Sec. 3.1 and Fig. 3](https://quantum-journal.org/papers/q-2025-01-27-1609/) and the [corrected package README](https://github.com/seokhyung-lee/color-code-stim/blob/ba6f7dc8b7aaab237d98ad5f08825be4225864c6/README.md).",
                 "", "| d | G | C | Points used / excluded |", "|---|---|---|---|"]
        for row in fits.itertuples():
            lines.append(f"| {row.distance} | {row.G:.4g} | {row.C:.4g} | {row.points_used} / {row.points_excluded} |")
        for row in trends.itertuples():
            published = .488 if row.parameter == "G" else 1.30
            lines += ["",f"{row.parameter}(d) slope: {row.slope:.4g}, 99% interval [{row.slope_low:.4g}, {row.slope_high:.4g}]; published slope {published}. Status: {row.fit_status}."]
        weak = sub[sub.ordinary_failures < 20][["distance","physical_error_rate","ordinary_failures"]]
        lines += ["",f"Subthreshold points with fewer than 20 observed failures: {weak.to_dict(orient='records')}.",
                  "Zero-failure points are excluded explicitly from log fits; their Wilson upper limits remain in empirical summaries. No log epsilon is used.",
                  "", f"This study ends at d={max(config['distances'])}, with {len(config['near_threshold_ps'])} near-threshold and {len(config['subthreshold_ps'])} subthreshold probabilities. Unweighted log-OLS is susceptible to finite-count bias; its t intervals do not incorporate all Monte Carlo uncertainty. Sparse LOWESS and finite-distance drift limit crossing precision. These data support only a coarse comparison.",
                  dataset.metadata.get("metric_description", "Selected swim and forced gap retain different decoder failure labels. Swim uses uncertified final defect metric balls: no posterior calibration or full-decoder bound follows."), "", "Implementation commits:"]
        for name in ("PyMatching","color-code-stim"):
            lines.append(f"- {name}: `{dataset.metadata['repositories'][name]['sha']}`")
        (directory / "PRIOR_WORK_REPRODUCTION.md").write_text("\n".join(lines)+"\n")
        return dict(crossing=crossing,fits=fits,trends=trends)
