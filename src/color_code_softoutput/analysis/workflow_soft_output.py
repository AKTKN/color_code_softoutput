"""Scatter distributions, conditional rates and retention for saved soft outputs."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.legend_handler import HandlerTuple
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .color_correlated import ColorCorrelatedRun, PARAMETERS, _bp_convergence, _sampling_scope
from .postselection import postselection_curve
from .statistics import CONFIDENCE_LEVEL, grouped_rates, rounded_scores


METRICS = ("swim_distance", "logical_gap")
METRIC_LABELS = {"swim_distance": "SWIM distance", "logical_gap": "Logical gap"}
METRIC_MAIN_COLORS = {"swim_distance": "#1f77b4", "logical_gap": "#d62728"}
DISTANCE_MARKERS = ("o", "s", "^", "D", "v", "P", "X", "<", ">", "h")
DISTANCE_TONE_LIMIT = .34
FIGURE_DPI = 300
_LEGEND_TITLES = {
    "distance": "Code distance",
    "metric": "Soft-output metric",
    "decoder_type": "Decoder type",
    "logical_error": "Outcome",
}


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
        point = self.run._point_dirs[row.point_directory]
        bp = dict(point.decode_options).get("bp_predecoding", False)
        convergence = (_bp_convergence(directory, row.expected_shots).to_numpy(zero_copy_only=False)
                       if bp else None)
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
                    if batch.column(0).null_count or (batch.column(1).null_count and not bp):
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
        if convergence is not None:
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
                scopes = {_sampling_scope(self.run._point_dirs[name]) for name in frame.point_directory}
                if len(scopes) > 1:
                    raise ValueError("Soft-output groups must separate BP sampling scopes; group by decoder_alias")
                key = key if isinstance(key, tuple) else (key,)
                condition = dict(zip(names, key))
                # Distance and decoder type have fixed visual channels in the
                # paper plots.  Never pool either field into an unlabelled
                # series when it varies inside a user-selected group.
                for style_field in ("distance", "decoder_type"):
                    if style_field not in condition:
                        values = frame[style_field].unique()
                        if len(values) != 1:
                            raise ValueError(
                                f"group_by must include {style_field!r} when it varies"
                            )
                        condition[style_field] = values[0]
                data = [self._point(row, current) for row in frame.itertuples()]
                if not any(len(item[0]) for item in data):
                    raise ValueError("No scored shots: BP converged on all selected shots")
                scope = next(iter(scopes))[0]
                series.append((condition | {"metric": current},
                               np.concatenate([item[0] for item in data]),
                               np.concatenate([item[1] for item in data])))
                if scope != "all shots":
                    series[-1][0]["statistics_scope"] = scope
        return series

    @staticmethod
    def _axes(ax, yscale):
        if yscale not in ("linear", "log"):
            raise ValueError("yscale must be 'linear' or 'log'")
        if ax is None:
            figure, ax = plt.subplots(figsize=(7.2, 4.5), dpi=FIGURE_DPI)
        else:
            figure = ax.figure
            figure.set_dpi(FIGURE_DPI)
        ax.set_yscale(yscale)
        return figure, ax

    @staticmethod
    def _tone(color, amount):
        """Lighten a negative amount or darken a positive amount."""
        rgb = np.asarray(to_rgb(color))
        return tuple(rgb * (1 - amount) if amount >= 0
                     else rgb + (1 - rgb) * -amount)

    def _series_colors(self):
        """Use restrained light-to-dark metric hues as distance increases."""
        distances = sorted(self.run.catalog["distance"].unique())
        tones = (np.array([0.0]) if len(distances) == 1 else
                 np.linspace(-DISTANCE_TONE_LIMIT, DISTANCE_TONE_LIMIT, len(distances)))
        return {
            metric: {
                distance: self._tone(METRIC_MAIN_COLORS[metric], tone)
                for distance, tone in zip(distances, tones)
            }
            for metric in METRICS
        }

    def _distance_markers(self):
        distances = sorted(self.run.catalog["distance"].unique())
        if len(distances) > len(DISTANCE_MARKERS):
            raise ValueError(
                f"At most {len(DISTANCE_MARKERS)} distances can be distinguished by marker"
            )
        return dict(zip(distances, DISTANCE_MARKERS))

    def _decoder_sizes(self):
        values = sorted(self.run.catalog["decoder_type"].unique())
        return {value: 42 + 24 * index for index, value in enumerate(values)}

    def _style(self, condition):
        return (self._series_colors()[condition["metric"]][condition["distance"]],
                self._distance_markers()[condition["distance"]],
                self._decoder_sizes()[condition["decoder_type"]])

    @staticmethod
    def _finish(figure, ax):
        # Legends are deliberately separate figures; this keeps the data axes
        # at a stable manuscript size and avoids covering points or bands.
        figure.tight_layout()

    def plot_legends(self, table, *, fontsize=10, row_height=.35,
                     width=3.0, ncol=1, frame_linewidth=.6):
        """Return independent legend figures for the visual encodings.

        Metric is encoded by a blue/red base hue. Distance uses both a clear
        light-to-dark gradient within that hue and a marker shape; the same
        distance has the same marker for both metrics.  (Only when more than
        one is plotted) decoder type uses marker size.  Unsigned
        distribution plots additionally use filled/hollow markers for
        success/error.  Signed distributions need no outcome legend because
        both outcomes deliberately use the same marker and errors lie at
        negative score.
        """
        required = {"distance", "metric", "decoder_type"}
        missing = required - set(table.columns)
        if missing:
            raise ValueError(f"Legend table is missing columns: {sorted(missing)}")
        if (any(not np.isfinite(v) or v <= 0 for v in (fontsize, row_height, width))
                or not np.isfinite(frame_linewidth) or frame_linewidth <= 0):
            raise ValueError("Legend sizes and ncol must be positive")
        if isinstance(ncol, Mapping):
            if (any(name not in _LEGEND_TITLES for name in ncol)
                    or any(isinstance(value, bool) or not isinstance(value, int) or value < 1
                           for value in ncol.values())):
                raise ValueError("Legend sizes and ncol must be positive")
            columns_for = lambda name: ncol.get(name, 1)
        elif isinstance(ncol, bool) or not isinstance(ncol, int) or ncol < 1:
            raise ValueError("Legend sizes and ncol must be positive")
        else:
            columns_for = lambda name: ncol

        series_colors = self._series_colors()
        distance_markers = self._distance_markers()
        decoder_sizes = self._decoder_sizes()
        metrics = [value for value in METRICS if value in set(table["metric"])]

        def distance_handle(value):
            handles = tuple(Line2D([], [], color=series_colors[metric][value], linewidth=2.5,
                                   marker=distance_markers[value], markersize=6)
                            for metric in metrics)
            return handles[0] if len(handles) == 1 else handles

        entries = {
            "distance": (
                sorted(table["distance"].unique()),
                distance_handle,
                lambda value: f"$d={value}$",
            ),
            "metric": (
                metrics,
                lambda value: Line2D([], [], color=METRIC_MAIN_COLORS[value], linewidth=2.5),
                lambda value: METRIC_LABELS[value],
            ),
        }
        decoder_values = sorted(table["decoder_type"].unique())
        if len(decoder_values) > 1:
            entries["decoder_type"] = (
                decoder_values,
                lambda value: Line2D([], [], color="black", marker="o", linestyle="none",
                                     markersize=np.sqrt(decoder_sizes[value])),
                str,
            )
        if ("logical_error" in table
                and not bool(table.get("signed_logical_errors", pd.Series(False)).all())):
            entries["logical_error"] = (
                [False, True],
                lambda value: Line2D([], [], color="black", marker="o", linestyle="none",
                                     markerfacecolor="none" if value else "black", markersize=7),
                lambda value: "Logical error" if value else "Success",
            )

        legends = {}
        for name, (values, handle_for, label_for) in entries.items():
            columns = columns_for(name)
            height = (int(np.ceil(len(values) / columns)) + 1.8) * row_height
            figure, legend_ax = plt.subplots(figsize=(width, height), dpi=FIGURE_DPI)
            legend_ax.axis("off")
            legend = legend_ax.legend(
                [handle_for(value) for value in values],
                [label_for(value) for value in values],
                title=_LEGEND_TITLES[name], loc="center", frameon=True,
                fontsize=fontsize, title_fontsize=fontsize, ncol=columns,
                handler_map={tuple: HandlerTuple(ndivide=None, pad=.5)},
            )
            legend.get_frame().set_edgecolor("black")
            legend.get_frame().set_facecolor("white")
            legend.get_frame().set_alpha(1)
            legend.get_frame().set_linewidth(frame_linewidth)
            legends[name] = (figure, legend_ax)
        return legends

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
        """Return a legend-free figure and its outcome-frequency table.

        Use metrics=['swim_distance', 'logical_gap'] to overlay saved series.
        With neither metric argument, use SWIM alone for compatibility.
        Missing point/metric combinations are omitted in multi-metric views;
        every selected point and every requested metric must have usable data.
        Each metric is joined to its own decoder's logical_error.parquet.

        Metric controls the blue/red base hue. Increasing distance darkens
        that hue within a restrained range and changes marker shape; a given
        distance uses the same marker for both metrics. Decoder type controls
        marker size only when multiple types are present. Unsigned
        views distinguish errors with hollow markers; signed_logical_errors
        negates only error scores for display and uses the same filled marker
        for successes and errors. Storage and selection stay unchanged.
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
        for condition, scores, failures in series:
            rates = grouped_rates(scores, failures, bins=edges, round_digits=round_digits)
            color, marker, marker_size = self._style(condition)
            for failure in (False, True):
                counts = rates.failures if failure else rates.shots - rates.failures
                frequency = counts / len(scores) if normalize_frequency else counts
                display_score = -rates.score if failure and signed_logical_errors else rates.score
                keep = counts > 0
                ax.scatter(display_score[keep], frequency[keep], marker=marker, color=color,
                           facecolors=color if signed_logical_errors or not failure else "none",
                           edgecolors=color, s=marker_size, alpha=.8)
                table = pd.DataFrame(dict(score=display_score, raw_score=rates.score,
                    logical_error=failure, count=counts, shots=counts,
                    failures=counts if failure else np.zeros(len(rates), dtype=int),
                    frequency=frequency, density=frequency, total_shots=len(scores),
                    signed_logical_errors=signed_logical_errors))
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
        self._finish(figure, ax)
        return figure, pd.concat(tables, ignore_index=True)

    @staticmethod
    def _rate_points(ax, x, rates, low, high, *, color, marker, marker_size):
        """Show positive empirical estimates and all Wilson bands, including zero."""
        x = np.asarray(x, dtype=float)
        rates = np.asarray(rates, dtype=float)
        ax.fill_between(x, np.asarray(low, dtype=float), np.asarray(high, dtype=float),
                        color=color, alpha=.18, linewidth=0, zorder=1)
        keep = rates > 0
        # NaNs break the line at unplotted zero-rate bins on both linear and
        # logarithmic axes instead of visually bridging missing estimates.
        ax.plot(x, np.where(keep, rates, np.nan), color=color,
                linewidth=1.4, alpha=.9, zorder=2)
        ax.scatter(x[keep], rates[keep], color=color,
                   marker=marker, s=marker_size, zorder=2)

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
        for condition, scores, failures in series:
            rates = grouped_rates(scores, failures, bins=edges, round_digits=round_digits,
                                  confidence_level=confidence_level)
            color, marker, marker_size = self._style(condition)
            self._rate_points(ax, rates.score, rates.logical_error_rate, rates.low, rates.high,
                              color=color, marker=marker, marker_size=marker_size)
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
        for condition, scores, failures in series:
            curve = postselection_curve(scores, failures, confidence_level, round_digits=round_digits)
            color, marker, marker_size = self._style(condition)
            self._rate_points(ax, curve.abort_rate, curve.residual_logical_error_rate,
                              curve.low, curve.high, color=color, marker=marker,
                              marker_size=marker_size)
            for name, value in condition.items():
                curve[name] = value
            tables.append(curve)
        ax.set(xlabel="Abort rate", ylabel="Post-selection logical error rate", xlim=xlim)
        self._finish(figure, ax)
        return figure, pd.concat(tables, ignore_index=True)
