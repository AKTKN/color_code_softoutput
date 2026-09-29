"""Scatter distributions, conditional rates and retention for saved soft outputs."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .color_correlated import ColorCorrelatedRun, PARAMETERS
from .postselection import postselection_curve
from .statistics import CONFIDENCE_LEVEL, grouped_rates, rounded_scores


METRICS = ("swim_distance", "logical_gap")
METRIC_MARKERS = {"swim_distance": "D", "logical_gap": "s"}
METRIC_LABELS = {"swim_distance": "SWIM distance", "logical_gap": "Logical gap"}


class WorkflowSoftOutputRun:
    """Load scored shots with their own decoder's hard-failure labels."""

    def __init__(self, run_directory: str | Path):
        self.run = ColorCorrelatedRun(run_directory)

    def _groups(self, filter: Mapping[str, object] | None,
                group_by: Sequence[str]) -> tuple[pd.DataFrame, tuple[str, ...]]:
        if isinstance(group_by, str):
            raise ValueError("group_by must be a sequence of parameter names")
        names = tuple(group_by)
        if len(names) != len(set(names)) or any(name not in PARAMETERS for name in names):
            raise ValueError(f"group_by must contain unique names from {PARAMETERS}")
        return self.run.select(filter), names

    def _point(self, row, metric: str) -> tuple[np.ndarray, np.ndarray]:
        if metric not in METRICS:
            raise ValueError(f"metric must be one of {METRICS}")
        directory = self.run.run_directory / row.point_directory
        arrays = []
        masks = []
        for name, dtype in ((metric, pa.float64()), ("logical_error", pa.bool_())):
            path = directory / f"{name}.parquet"
            with pq.ParquetFile(path) as source:
                schema = source.schema_arrow
                if (schema.names != ["shot_index", name]
                        or schema.field("shot_index").type != pa.int64()
                        or schema.field(name).type != dtype
                        or source.metadata.num_rows != row.expected_shots):
                    raise ValueError(f"Invalid soft-output file: {path}")
                index = []
                nulls = []
                values = []
                for batch in source.iter_batches(batch_size=65_536):
                    if batch.column(0).null_count or (batch.column(1).null_count and not (directory / "bp_converged.parquet").is_file()):
                        raise ValueError(f"Null values in {path}")
                    nulls.append(batch.column(1).is_null().to_numpy(zero_copy_only=False))
                    index.append(batch.column(0).to_numpy(zero_copy_only=False))
                    values.append(batch.column(1).to_numpy(zero_copy_only=False))
                shot_index = np.concatenate(index)
                if not np.array_equal(shot_index, np.arange(row.expected_shots)):
                    raise ValueError(f"Invalid shot indices in {path}")
                arrays.append(np.concatenate(values))
                masks.append(np.concatenate(nulls))
        if not np.array_equal(masks[0],masks[1]):
            raise ValueError("Soft-output and failure null masks disagree")
        if (directory / "bp_converged.parquet").is_file():
            convergence = pq.read_table(directory / "bp_converged.parquet")["bp_converged"].to_numpy()
            if not np.array_equal(masks[0],convergence):
                raise ValueError("Soft-output null masks disagree with BP convergence")
        scores, failures = arrays[0][~masks[0]].astype(float), arrays[1][~masks[1]].astype(bool)
        if not np.isfinite(scores).all() or np.any(scores < 0):
            raise ValueError(f"Invalid {metric} values in {directory}")
        return scores, failures

    @staticmethod
    def _metrics(metric, metrics):
        if metric is not None and metrics is not None:
            raise ValueError("Specify metric or metrics, not both")
        if isinstance(metrics, str):
            raise ValueError("metrics must be a sequence, e.g. ['swim_distance', 'logical_gap']")
        requested = tuple(metrics) if metrics is not None else (metric if metric is not None else "swim_distance",)
        if (not requested or len(set(requested)) != len(requested)
                or any(name not in METRICS for name in requested)):
            raise ValueError(f"Supply unique metrics from {METRICS}")
        return requested

    def available_metrics(self, filter=None):
        """Return selected catalog rows with saved-metric availability flags."""
        table = self.run.select(filter)
        for metric in METRICS:
            table[f"{metric}_available"] = [
                (self.run.run_directory / name / f"{metric}.parquet").is_file()
                for name in table.point_directory
            ]
        return table

    def _series(self, metric, metrics, filter, group_by):
        requested = self._metrics(metric, metrics)
        selected, names = self._groups(filter, group_by)
        # The comparison can span decoder points that save different metrics.
        # Never relabel a score or borrow another decoder's failure labels.
        for row in selected.itertuples():
            if not any((self.run.run_directory / row.point_directory / f"{m}.parquet").is_file()
                       for m in requested):
                raise FileNotFoundError(
                    f"No requested metric {requested} saved for {row.point_directory}; "
                    "select scored points using available_metrics(filter)")
        series = []
        for current in requested:
            available = selected[[
                (self.run.run_directory / name / f"{current}.parquet").is_file()
                for name in selected.point_directory
            ]]
            if available.empty:
                raise FileNotFoundError(f"No selected points have {current}.parquet")
            groups = available.groupby(list(names), sort=True, dropna=False) if names else [((), available)]
            for key, frame in groups:
                key = key if isinstance(key, tuple) else (key,)
                data = [self._point(row, current) for row in frame.itertuples()]
                series.append((dict(zip(names, key)) | {"metric": current},
                               np.concatenate([item[0] for item in data]),
                               np.concatenate([item[1] for item in data])))
        return series

    @staticmethod
    def _axes(ax, yscale):
        if yscale not in ("linear", "log"):
            raise ValueError("yscale must be 'linear' or 'log'")
        if ax is None:
            figure, ax = plt.subplots(figsize=(7.2, 4.5))
        else:
            figure = ax.figure
        ax.set_yscale(yscale)
        return figure, ax

    @staticmethod
    def _color(index, count):
        cmap = plt.colormaps["tab10"] if count <= 10 else plt.colormaps["turbo"].resampled(count)
        return cmap(index)

    @staticmethod
    def _finish(figure, ax, *, legend_columns=1):
        # Keep score points and Wilson bands visible beneath the legend.
        ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.02),
                  ncol=legend_columns, fontsize=8, frameon=False)
        figure.tight_layout()

    @staticmethod
    def _label(condition):
        return METRIC_LABELS[condition["metric"]] + ", " + (
            ", ".join(f"{name}={value}" for name, value in condition.items() if name != "metric") or "all")

    @staticmethod
    def _score_label(series):
        metrics = {condition["metric"] for condition, _, _ in series}
        return METRIC_LABELS[next(iter(metrics))] if len(metrics) == 1 else "Soft-output score"

    @staticmethod
    def _bins(series, bins, round_digits):
        """Share histogram edges across series, preserving discrete auto groups."""
        scores = np.concatenate([rounded_scores(values, round_digits) for _, values, _ in series])
        if isinstance(bins, str):
            if bins != "auto":
                raise ValueError("bins must be 'auto', a positive integer or increasing edges")
            if round_digits is not None or len(np.unique(np.round(scores, 10))) <= 64:
                return "auto"
            return np.histogram_bin_edges(scores, bins="auto")
        if isinstance(bins, (int, np.integer)) and not isinstance(bins, (bool, np.bool_)):
            if bins < 1:
                raise ValueError("bins must be a positive integer")
            return np.histogram_bin_edges(scores, bins=int(bins))
        edges = np.asarray(bins, dtype=float)
        if (edges.ndim != 1 or len(edges) < 2 or not np.isfinite(edges).all()
                or np.any(np.diff(edges) <= 0) or edges[0] > scores.min() or edges[-1] < scores.max()):
            raise ValueError("bin edges must be finite, increasing and cover all selected scores")
        return edges

    def plot_distribution(self, *, metric: str | None = None,
                          metrics: Sequence[str] | None = None,
                          filter: Mapping[str, object] | None = None,
                          group_by: Sequence[str] = ("decoder_type",), bins="auto",
                          signed_logical_errors: bool = False,
                          normalize_frequency: bool = False, density: bool | None = None,
                          round_digits: int | None = None, yscale="log", ax=None):
        """Return (figure, outcome-frequency table) with success o/error x points.

        Use metrics=['swim_distance', 'logical_gap'] to overlay saved series.
        With neither metric argument, use SWIM alone for compatibility.
        Missing point/metric combinations are omitted in multi-metric views;
        every selected point and every requested metric must have usable data.
        Each metric is joined to its own decoder's logical_error.parquet.

        signed_logical_errors negates only error scores for display, after
        grouping the nonnegative scores; storage and selection stay unchanged.
        normalize_frequency divides outcome counts by all shots in each
        series. Legacy density is an alias for this normalization. Tables keep
        empty outcome rows; only positive counts are plotted. Auto grouping
        and opt-in rounding follow the existing circuit notebook conventions.
        """
        if density is not None:
            if normalize_frequency and not density:
                raise ValueError("density conflicts with normalize_frequency")
            normalize_frequency = density
        series = self._series(metric, metrics, filter, group_by)
        edges = self._bins(series, bins, round_digits)
        figure, ax = self._axes(ax, yscale)
        tables = []
        for index, (condition, scores, failures) in enumerate(series):
            rates = grouped_rates(scores, failures, bins=edges, round_digits=round_digits)
            color = self._color(index, len(series))
            for failure, marker in ((False, "o"), (True, "x")):
                counts = rates.failures if failure else rates.shots - rates.failures
                frequency = counts / len(scores) if normalize_frequency else counts
                display_score = -rates.score if failure and signed_logical_errors else rates.score
                keep = counts > 0
                ax.scatter(display_score[keep], frequency[keep], marker=marker, color=color,
                           alpha=.75, label=self._label(condition) + (", error" if failure else ", success"))
                table = pd.DataFrame(dict(score=display_score, raw_score=rates.score,
                    logical_error=failure, count=counts, shots=counts,
                    failures=counts if failure else np.zeros(len(rates), dtype=int),
                    frequency=frequency, density=frequency, total_shots=len(scores)))
                # For exact grouping the interval degenerates to the actual score.
                if isinstance(edges, str):
                    table["bin_left"] = rates.score
                    table["bin_right"] = rates.score
                else:
                    centers = (edges[:-1] + edges[1:]) / 2
                    positions = np.searchsorted(centers, rates.score)
                    table["bin_left"] = edges[positions]
                    table["bin_right"] = edges[positions + 1]
                for name, value in condition.items():
                    table[name] = value
                tables.append(table)
        ax.set(xlabel=self._score_label(series) + (" (errors negated)" if signed_logical_errors else ""),
               ylabel="Relative frequency" if normalize_frequency else "Frequency")
        self._finish(figure, ax, legend_columns=2)
        return figure, pd.concat(tables, ignore_index=True)

    @staticmethod
    def _rate_points(ax, x, rates, low, high, *, color, marker, label):
        """Show positive empirical estimates and all Wilson bands, including zero."""
        ax.fill_between(np.asarray(x, dtype=float), np.asarray(low, dtype=float),
                        np.asarray(high, dtype=float), color=color, alpha=.2, linewidth=0, zorder=1)
        keep = np.asarray(rates) > 0
        ax.scatter(np.asarray(x)[keep], np.asarray(rates)[keep], color=color,
                   marker=marker, label=label, zorder=2)

    def plot_conditional_ler(self, *, metric: str | None = None,
                             metrics: Sequence[str] | None = None,
                             filter: Mapping[str, object] | None = None,
                             group_by: Sequence[str] = ("decoder_type",), bins="auto",
                             round_digits: int | None = None,
                             confidence_level: float = CONFIDENCE_LEVEL,
                             yscale="log", ax=None):
        """Scatter P(logical error | score) with 99% Wilson bands by default.

        Return (figure, table) with score, shots, failures, logical_error_rate,
        low/high and group/metric identifiers. No fitted calibration is implied.
        Zero-rate bins retain their Wilson bands but have no plotted estimate.
        Score signs are unchanged; error negation is a distribution option.
        """
        series = self._series(metric, metrics, filter, group_by)
        edges = self._bins(series, bins, round_digits)
        figure, ax = self._axes(ax, yscale)
        tables = []
        for index, (condition, scores, failures) in enumerate(series):
            rates = grouped_rates(scores, failures, bins=edges, round_digits=round_digits,
                                  confidence_level=confidence_level)
            self._rate_points(ax, rates.score, rates.logical_error_rate, rates.low, rates.high,
                              color=self._color(index, len(series)),
                              marker=METRIC_MARKERS[condition["metric"]], label=self._label(condition))
            for name, value in condition.items():
                rates[name] = value
            tables.append(rates)
        ax.set(xlabel=self._score_label(series), ylabel="P(logical error | score)")
        self._finish(figure, ax)
        return figure, pd.concat(tables, ignore_index=True)

    def plot_postselection(self, *, metric: str | None = None,
                           metrics: Sequence[str] | None = None,
                           filter: Mapping[str, object] | None = None,
                           group_by: Sequence[str] = ("decoder_type",),
                           round_digits: int | None = None,
                           confidence_level: float = CONFIDENCE_LEVEL,
                           yscale="log", xlim=(0, 1), ax=None):
        """Scatter exact score-threshold retention curves with Wilson bands.

        Retain scores >= threshold and use each decoder's own failure labels.
        Distribution-only error negation is never used for selection. Opt-in
        round_digits rounds scores before forming thresholds/ties. Empty
        retention is omitted. Zero residual LER has a band but no point.
        """
        if len(xlim) != 2 or not np.isfinite(xlim).all() or not 0 <= xlim[0] < xlim[1] <= 1:
            raise ValueError("xlim must satisfy 0 <= lower < upper <= 1")
        series = self._series(metric, metrics, filter, group_by)
        figure, ax = self._axes(ax, yscale)
        tables = []
        for index, (condition, scores, failures) in enumerate(series):
            curve = postselection_curve(scores, failures, confidence_level, round_digits=round_digits)
            self._rate_points(ax, curve.abort_rate, curve.residual_logical_error_rate,
                              curve.low, curve.high, color=self._color(index, len(series)),
                              marker=METRIC_MARKERS[condition["metric"]], label=self._label(condition))
            for name, value in condition.items():
                curve[name] = value
            tables.append(curve)
        ax.set(xlabel="Abort rate", ylabel="Post-selection logical error rate", xlim=xlim)
        self._finish(figure, ax)
        return figure, pd.concat(tables, ignore_index=True)
