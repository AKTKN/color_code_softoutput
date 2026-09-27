"""Read and compare completed canonical YAML color-code runs."""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ..simulation import config as workflow_config
from ..simulation.planner import plan_points, point_directory_name
from .statistics import wilson_interval


PARAMETERS = (
    "decoder_type", "circuit_type", "distance", "rounds",
    "physical_error_rate", "noise_model", "cnot_schedule",
)
COUNTS = (
    "better_weight_by_color_correlated_decoding",
    "effect_by_color_correlated_decoding",
)
_PAIRED_METRICS = ("logical_error", "default_logical_error", *COUNTS)
_MARKERS = (
    "o", "s", "^", "D", "v", "P", "X", "<", ">", "h",
    "*", "p", "8", "H", "d", "1", "2", "3", "4", "+",
)


def _per_round(rate: float, rounds: int) -> float:
    """Invert 1 - (1 - p_round)**rounds, including rates of zero and one."""
    if rate == 1:
        return 1.0
    return float(-np.expm1(np.log1p(-rate) / rounds))


def _metric_count(path: Path, metric: str, expected_shots: int) -> int:
    """Count a binary metric with bounded batches and verify its shot indices."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing metric file: {path}")
    with pq.ParquetFile(path) as source:
        schema = source.schema_arrow
        expected_type = pa.bool_() if metric in ("logical_error", "default_logical_error") else pa.uint8()
        if (schema.names != ["shot_index", metric]
                or schema.field("shot_index").type != pa.int64()
                or schema.field(metric).type != expected_type
                or source.metadata.num_rows != expected_shots):
            raise ValueError(f"Invalid schema or shot count: {path}")
        count = 0
        offset = 0
        for batch in source.iter_batches(batch_size=65_536):
            indices = batch.column(0).to_numpy()
            values = batch.column(1).to_numpy(zero_copy_only=False)
            if (batch.column(0).null_count or batch.column(1).null_count
                    or not np.array_equal(indices, np.arange(offset, offset + len(batch)))):
                raise ValueError(f"Invalid shot indices or null values: {path}")
            if metric in COUNTS and np.any(values > 1):
                raise ValueError(f"Nonbinary flag values: {path}")
            count += int(np.count_nonzero(values))
            offset += len(batch)
        if offset != expected_shots:
            raise ValueError(f"Incomplete metric file: {path}")
        return count


class ColorCorrelatedRun:
    """Inspect one completed YAML run and aggregate its per-point Parquet files."""

    def __init__(self, run_directory: str | Path):
        self.run_directory = Path(run_directory).expanduser().resolve()
        log_path = self.run_directory / "run_log.json"
        with log_path.open(encoding="utf-8") as stream:
            self.run_log = json.load(stream)
        if not self.run_log.get("simulation_end_time"):
            raise ValueError(f"Run has no completion time: {log_path}")
        self.config = workflow_config.parse_workflow_config(self.run_log["config"])
        points = plan_points(self.config)
        self._point_dirs = {
            point_directory_name(point): point for point in points
        }
        self._cache: dict[str, dict] = {}
        self.catalog = pd.DataFrame([
            {
                "decoder_type": point.decoder_type,
                "circuit_type": point.circuit_type,
                "distance": point.distance,
                "rounds": point.rounds,
                "physical_error_rate": point.physical_error_rate,
                "noise_model": point.noise_model,
                "cnot_schedule": point.cnot_schedule,
                "expected_shots": point.shots,
                "point_directory": name,
                "data_available": (self.run_directory / name / "logical_error.parquet").is_file(),
            }
            for name, point in self._point_dirs.items()
        ])

    def select(self, filter: Mapping[str, object] | None = None) -> pd.DataFrame:
        """Select planned points; a filter value may be a scalar or a nonempty list."""
        if filter is not None and not isinstance(filter, Mapping):
            raise ValueError("filter must be a mapping of parameter names to values")
        selected = self.catalog
        for name, wanted in (filter or {}).items():
            if name not in PARAMETERS:
                raise ValueError(f"Unknown filter: {name}; choose from {PARAMETERS}")
            values = wanted if isinstance(wanted, (list, tuple, set)) else [wanted]
            if not values:
                raise ValueError(f"Empty filter: {name}")
            selected = selected[selected[name].isin(values)]
        if selected.empty:
            raise ValueError("No experiment points match the filters")
        return selected.copy().reset_index(drop=True)

    def _summarize_point(self, name: str) -> dict:
        if name in self._cache:
            return self._cache[name]
        point = self._point_dirs[name]
        directory = self.run_directory / name
        options = dict(point.color_code_options) | dict(point.decoder_options)
        advanced = any(options.get(flag, False) for flag in (
            "enable_colorcorrelated_decoding", "enable_cross_color_relifting",
            "enable_prior_perturbation"))
        paired_paths = [directory / f"{metric}.parquet" for metric in _PAIRED_METRICS[1:]]
        paired_files = [path.is_file() for path in paired_paths]
        if any(paired_files) and not all(paired_files):
            raise FileNotFoundError(f"Incomplete paired metrics: {directory}")
        # Old relifting runs predate these three sidecars. Keep them readable,
        # while requiring the established color-correlated contract.
        paired = advanced and (all(paired_files) or options.get("enable_colorcorrelated_decoding", False))
        metrics = _PAIRED_METRICS if paired else ("logical_error",)
        counts = {
            metric: _metric_count(directory / f"{metric}.parquet", metric, point.shots)
            for metric in metrics
        }
        per_round = point.noise_model == "uniform"
        to_rate = (lambda value: _per_round(value, point.rounds)) if per_round else float
        record = {
            "point_directory": name,
            "shots": point.shots,
            "failures": counts["logical_error"],
            "logical_error_rate_total": counts["logical_error"] / point.shots,
            "logical_error_rate": to_rate(counts["logical_error"] / point.shots),
            "default_failures": counts.get("default_logical_error", pd.NA),
            "default_logical_error_rate_total": (
                counts["default_logical_error"] / point.shots
                if paired else np.nan
            ),
            "default_logical_error_rate": (
                to_rate(counts["default_logical_error"] / point.shots)
                if paired else np.nan
            ),
            "better_weight_count": counts.get(COUNTS[0], pd.NA),
            "effect_count": counts.get(COUNTS[1], pd.NA),
        }
        if paired:
            # B - N = rescued - worsened for paired baseline/new failure bits.
            # The saved effect flag is exactly rescued = B & ~N, so the
            # worsening count follows without another pass over Parquet data.
            worsened = counts["logical_error"] - counts["default_logical_error"] + counts[COUNTS[1]]
            if not (0 <= worsened <= min(counts["logical_error"],
                                          point.shots - counts["default_logical_error"])):
                raise ValueError(f"Inconsistent paired logical-error/effect counts: {directory}")
            record["worsened_count"] = worsened
            record["net_effect_count"] = counts[COUNTS[1]] - worsened
        else:
            record["worsened_count"] = pd.NA
            record["net_effect_count"] = pd.NA
        low, high = wilson_interval(record["failures"], point.shots)
        record["ler_low"] = to_rate(float(low))
        record["ler_high"] = to_rate(float(high))
        if paired:
            low, high = wilson_interval(counts["default_logical_error"], point.shots)
            record["default_ler_low"] = to_rate(float(low))
            record["default_ler_high"] = to_rate(float(high))
        else:
            record["default_ler_low"] = np.nan
            record["default_ler_high"] = np.nan
        self._cache[name] = record
        return record

    def summary(self, filter: Mapping[str, object] | None = None) -> pd.DataFrame:
        """Return per-point counts and Wilson limits; uniform LER is per round."""
        selected = self.select(filter)
        aggregates = pd.DataFrame([
            self._summarize_point(name) for name in selected["point_directory"]
        ])
        result = selected.merge(aggregates, on="point_directory", validate="one_to_one")
        for name in ("default_failures", "better_weight_count", "effect_count",
                     "worsened_count", "net_effect_count"):
            result[name] = result[name].astype("Int64")
        return result.drop(columns=["data_available"]).sort_values(
            ["distance", "physical_error_rate", "decoder_type"]
        ).reset_index(drop=True)

    def count_table(self, filter: Mapping[str, object] | None = None) -> pd.DataFrame:
        """Show the two advanced-decoder flag counts for selected points."""
        columns = [*PARAMETERS, "shots", "better_weight_count", "effect_count"]
        return self.summary(filter)[columns]

    def better_weight_table(self, filter: Mapping[str, object] | None = None) -> pd.DataFrame:
        """Filter per-point strict common-prior weight-improvement counts."""
        return self.count_table(filter)[[*PARAMETERS, "shots", "better_weight_count"]]

    def effect_table(self, filter: Mapping[str, object] | None = None) -> pd.DataFrame:
        """Show rescued, worsened, and net rescued shots against each paired baseline."""
        return self.summary(filter)[[*PARAMETERS, "shots", "effect_count",
                                     "worsened_count", "net_effect_count"]]

    def plot_ler(
        self,
        *,
        filter: Mapping[str, object] | None = None,
        group_by: Sequence[str] = ("distance", "decoder_type"),
        baseline_compare: bool = False,
        yscale: str = "log",
        plot_width: float = 7.4,
        plot_height: float = 4.6,
        legend_fontsize: float = 9,
        legend_row_height: float = 0.48,
        ax=None,
    ):
        """Plot LER below an independent boxed condition legend.

        The main plot keeps its requested physical size as legend rows change.
        Uniform circuit-noise LER is per round, using 1-(1-P_fail)**(1/r).
        On a logarithmic axis, a zero-failure point is displayed at a
        half-failure equivalent (per round for uniform noise);
        the returned table always retains its exact measured rate of zero.
        """
        if yscale not in ("linear", "log"):
            raise ValueError("yscale must be 'linear' or 'log'")
        if any(not np.isfinite(value) or value <= 0 for value in
               (plot_width, plot_height, legend_fontsize, legend_row_height)):
            raise ValueError("Plot and legend sizes must be positive and finite")
        if isinstance(group_by, str):
            raise ValueError("group_by must be a list of up to two parameter names")
        group_by = tuple(group_by)
        if len(group_by) > 2 or len(set(group_by)) != len(group_by):
            raise ValueError("group_by must contain at most two distinct parameters")
        if any(name not in PARAMETERS or name in ("physical_error_rate", "rounds") for name in group_by):
            raise ValueError("group_by must use config parameters other than physical_error_rate and rounds")
        if baseline_compare and "decoder_type" not in group_by:
            raise ValueError("baseline_compare requires decoder_type in group_by")
        table = self.summary(filter)
        if baseline_compare:
            if (table["decoder_type"] == "baseline").any():
                raise ValueError("decoder_type='baseline' is reserved for baseline_compare")
            paired = table["default_failures"].notna()
            if not paired.any():
                raise ValueError("No advanced-decoder points selected for baseline_compare")
            table = table.copy()
            table["source_decoder_type"] = table["decoder_type"]
            table["metric"] = "logical_error"
            baseline = table.loc[paired].copy()
            # Each advanced decoder has its own sampled baseline. Plot one
            # deterministic representative for each physical configuration.
            priority = {"color_correlated": 0, "relifting": 1, "perturbation": 2}
            baseline["_priority"] = baseline["source_decoder_type"].map(priority).fillna(3)
            condition = [name for name in PARAMETERS if name != "decoder_type"]
            baseline = (baseline.sort_values(["_priority", "source_decoder_type"])
                        .drop_duplicates(condition).drop(columns="_priority"))
            baseline["decoder_type"] = "baseline"
            baseline["metric"] = "default_logical_error"
            baseline["failures"] = baseline["default_failures"].astype("int64")
            baseline["logical_error_rate_total"] = baseline["default_logical_error_rate_total"]
            baseline["logical_error_rate"] = baseline["default_logical_error_rate"]
            baseline["ler_low"] = baseline["default_ler_low"]
            baseline["ler_high"] = baseline["default_ler_high"]
            for name in ("better_weight_count", "effect_count", "worsened_count",
                         "net_effect_count"):
                baseline[name] = pd.NA
            table = pd.concat([table, baseline], ignore_index=True).sort_values(
                ["distance", "physical_error_rate", "decoder_type"]
            ).reset_index(drop=True)
        ungrouped = set(PARAMETERS) - {"physical_error_rate", "rounds", *group_by}
        varying = sorted(name for name in ungrouped if table[name].nunique() > 1)
        if varying:
            raise ValueError(f"Filter or group_by the varying parameters: {varying}")
        if table.duplicated([*group_by, "physical_error_rate"]).any():
            raise ValueError("Multiple points share a group and physical error rate")

        first_values = sorted(table[group_by[0]].unique()) if group_by else [None]
        second_values = sorted(table[group_by[1]].unique()) if len(group_by) == 2 else [None]
        if len(second_values) > len(_MARKERS):
            raise ValueError(f"Second group has more than {len(_MARKERS)} marker values")
        if len(first_values) <= 10:
            color_for = {
                value: plt.colormaps["tab10"](i) for i, value in enumerate(first_values)
            }
        else:
            colors = plt.colormaps["turbo"].resampled(len(first_values))
            color_for = {value: colors(i) for i, value in enumerate(first_values)}
        marker_for = {value: _MARKERS[i] for i, value in enumerate(second_values)}
        nrows, ncols = len(first_values), len(second_values)
        labels = [
            ", ".join(f"{name}={value}" for name, value in zip(group_by, pair)) or "selected"
            for pair in ((first, second) for first in first_values for second in second_values)
        ] if len(group_by) == 2 else [
            f"{group_by[0]}={first}" if group_by else "selected" for first in first_values
        ]
        cell_width = max(2.4, max(map(len, labels)) * legend_fontsize / 88)
        figure_width = max(plot_width + 1.35, ncols * cell_width + 1.25)
        legend_height = nrows * legend_row_height
        bottom, gap, top = 0.95, 0.38, 0.30
        figure_height = bottom + plot_height + gap + legend_height + top
        plot_bounds = [0.85 / figure_width, bottom / figure_height,
                       plot_width / figure_width, plot_height / figure_height]
        legend_bounds = [0.55 / figure_width,
                         (bottom + plot_height + gap) / figure_height,
                         (figure_width - 1.1) / figure_width,
                         legend_height / figure_height]
        if ax is None:
            figure = plt.figure(figsize=(figure_width, figure_height))
            ax = figure.add_axes(plot_bounds)
        else:
            figure = ax.figure
            figure.set_size_inches(figure_width, figure_height)
            ax.set_position(plot_bounds)
        legend_ax = figure.add_axes(legend_bounds, label="condition_legend")
        legend_ax.set(xlim=(0, ncols), ylim=(nrows, 0))
        legend_ax.axis("off")
        combinations = {
            tuple(row[name] for name in group_by)
            for _, row in table.iterrows()
        }
        for row_index, first in enumerate(first_values):
            for col_index, second in enumerate(second_values):
                pair = ((first, second) if len(group_by) == 2 else
                        (first,) if group_by else ())
                legend_ax.add_patch(Rectangle(
                    (col_index, row_index), 1, 1,
                    facecolor="white", edgecolor="0.5", linewidth=0.8,
                ))
                label = ", ".join(
                    f"{name}={value}" for name, value in zip(group_by, pair)
                ) or "selected"
                if pair in combinations:
                    legend_ax.plot(
                        [col_index + 0.06, col_index + 0.19],
                        [row_index + 0.5] * 2,
                        color=color_for[first], marker=marker_for[second],
                        markersize=5, linewidth=1.5,
                    )
                else:
                    label += " (no point)"
                legend_ax.text(
                    col_index + 0.25, row_index + 0.5, label,
                    va="center", fontsize=legend_fontsize,
                )
        grouped = (table.groupby(group_by[0] if len(group_by) == 1 else list(group_by),
                                 dropna=False, sort=True) if group_by else [((), table)])
        zero_display = np.array([
            _per_round(0.5 / row.shots, row.rounds)
            if row.noise_model == "uniform" else 0.5 / row.shots
            for row in table.itertuples()
        ])
        display_floor = float(zero_display.min())
        for key, rows in grouped:
            values = key if isinstance(key, tuple) else (key,)
            rows = rows.sort_values("physical_error_rate")
            color = color_for[values[0]] if group_by else color_for[None]
            marker = marker_for[values[1]] if len(group_by) == 2 else marker_for[None]
            x = rows["physical_error_rate"].to_numpy(dtype=float)
            y = rows["logical_error_rate"].to_numpy(dtype=float)
            low = rows["ler_low"].to_numpy(dtype=float)
            if yscale == "log":
                floor_by_row = np.array([
                    _per_round(0.5 / row.shots, row.rounds)
                    if row.noise_model == "uniform" else 0.5 / row.shots
                    for row in rows.itertuples()
                ])
                y = np.where(y == 0, floor_by_row, y)
                low = np.maximum(low, display_floor)
            ax.plot(x, y, marker=marker, color=color)
            ax.fill_between(x, low,
                            rows["ler_high"].to_numpy(dtype=float), color=color, alpha=0.10)
        upper = min(1.0, float(table["ler_high"].max()) * 1.15)
        if yscale == "log":
            ax.set_yscale("log")
            ax.set_ylim(display_floor / 1.5, max(upper, display_floor * 10))
            if (table["failures"] == 0).any():
                figure.text(
                    0.85 / figure_width, 0.12 / figure_height,
                    "Zero-failure points use half-failure display values; table retains LER = 0.",
                    fontsize=8, color="0.35",
                )
        else:
            ax.set_ylim(0, upper)
        ylabel = ("Logical error rate per round" if (table["noise_model"] == "uniform").all()
                  else "Logical error rate")
        ax.set(xlabel="Physical error rate", ylabel=ylabel)
        ax.grid(alpha=0.25)
        return figure, ax, table
