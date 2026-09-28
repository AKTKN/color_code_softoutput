"""Read and compare completed canonical YAML color-code runs."""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Mapping, Sequence

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ..simulation import config as workflow_config
from ..simulation.planner import plan_points, point_directory_name
from .statistics import wilson_interval


PARAMETERS = (
    "decoder_alias", "decoder_type", "circuit_type", "distance", "rounds",
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
                "decoder_alias": point.decoder_alias or point.decoder_type,
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
            ["distance", "physical_error_rate", "decoder_alias"]
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

    def _ler_table(self, filter, baseline_compare=False):
        table = self.summary(filter)
        if baseline_compare:
            if (table["decoder_type"] == "baseline").any() or (table["decoder_alias"] == "baseline").any():
                raise ValueError("decoder_type/decoder_alias='baseline' is reserved for baseline_compare")
            paired = table["default_failures"].notna()
            if not paired.any():
                raise ValueError("No advanced-decoder points selected for baseline_compare")
            table = table.copy()
            table["source_decoder_type"] = table["decoder_type"]
            table["source_decoder_alias"] = table["decoder_alias"]
            table["metric"] = "logical_error"
            baseline = table.loc[paired].copy()
            # Each advanced decoder has its own sampled baseline. Plot one
            # deterministic representative for each physical configuration.
            priority = {"color_correlated": 0, "relifting": 1, "perturbation": 2}
            baseline["_priority"] = baseline["source_decoder_type"].map(priority).fillna(3)
            condition = [name for name in PARAMETERS if name not in ("decoder_type", "decoder_alias")]
            baseline = (baseline.sort_values(["_priority", "source_decoder_type", "source_decoder_alias"])
                        .drop_duplicates(condition).drop(columns="_priority"))
            baseline["decoder_type"] = "baseline"
            baseline["decoder_alias"] = "baseline"
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
                ["distance", "physical_error_rate", "decoder_alias"]
            ).reset_index(drop=True)
        return table

    def _styles(self, table, group_by):
        """Use run-wide value ordering so filters and plots share encodings."""
        names = tuple(group_by)
        value_lists = [sorted(set(self.catalog[name]) | set(table[name])
                              | ({"baseline"} if name in ("decoder_type", "decoder_alias") else set()))
                       for name in names]
        first = value_lists[0] if names else [None]
        second = value_lists[1] if len(names) == 2 else [None]
        if len(second) > len(_MARKERS):
            raise ValueError(f"Second group has more than {len(_MARKERS)} marker values")
        cmap = plt.colormaps["tab10"] if len(first) <= 10 else plt.colormaps["turbo"].resampled(len(first))
        return ({value: cmap(i) for i, value in enumerate(first)},
                {value: _MARKERS[i] for i, value in enumerate(second)})

    @staticmethod
    def _groups(table, group_by, x):
        if isinstance(group_by, str):
            raise ValueError("group_by must be a list of up to two parameter names")
        names = tuple(group_by)
        if len(names) > 2 or len(set(names)) != len(names):
            raise ValueError("group_by must contain at most two distinct parameters")
        if any(name not in PARAMETERS or name in ("physical_error_rate", "rounds") for name in names):
            raise ValueError("group_by must use config parameters other than physical_error_rate and rounds")
        ungrouped = set(PARAMETERS) - {x, "rounds", *names}
        # A grouped alias identifies its type. Legacy type grouping also works
        # when each type has exactly one alias; repeated types require aliases.
        for identity, dependent in (("decoder_alias", "decoder_type"),
                                    ("decoder_type", "decoder_alias")):
            if identity in names and table.groupby(identity)[dependent].nunique().max() <= 1:
                ungrouped.discard(dependent)
        varying = sorted(name for name in ungrouped if table[name].nunique() > 1)
        if varying:
            raise ValueError(f"Filter or group_by the varying parameters: {varying}")
        if table.duplicated(list(dict.fromkeys([*names, x]))).any():
            raise ValueError(f"Multiple points share a group and {x}")
        return names

    @staticmethod
    def _axes(ax, plot_width, plot_height):
        if any(not np.isfinite(v) or v <= 0 for v in (plot_width, plot_height)):
            raise ValueError("Plot sizes must be positive and finite")
        if ax is not None:
            return ax.figure, ax
        # Sizes describe the main axes, in inches, independently of legends.
        width, height = plot_width + 1.35, plot_height + 1.25
        figure = plt.figure(figsize=(width, height))
        return figure, figure.add_axes([.85 / width, .95 / height,
                                        plot_width / width, plot_height / height])

    def plot_legends(self, table, *, group_by=("distance", "decoder_type"),
                     fontsize=10, row_height=.35, width=3.0, ncol=1):
        """Return {field: (figure, axes)} with independent color/marker legends.

        Each legend shows only values present in table, under its field name.
        The first field uses colored lines, the second black markers. Figures
        can be styled, resized and saved independently of the data plot.
        """
        if (isinstance(group_by, str) or len(group_by) > 2
                or len(set(group_by)) != len(group_by)
                or any(name not in PARAMETERS for name in group_by)):
            raise ValueError("group_by must contain at most two distinct config parameters")
        if (any(not np.isfinite(v) or v <= 0 for v in (fontsize, row_height, width))
                or isinstance(ncol, bool) or not isinstance(ncol, int) or ncol < 1):
            raise ValueError("Legend sizes and ncol must be positive")
        color_for, marker_for = self._styles(table, group_by)
        legends = {}
        for index, name in enumerate(group_by):
            values = sorted(table[name].unique())
            handles = [Line2D([], [], color=color_for[v], linewidth=2)
                       if index == 0 else
                       Line2D([], [], color="black", marker=marker_for[v],
                              linestyle="none", markersize=7) for v in values]
            height = (int(np.ceil(len(values) / ncol)) + 1.8) * row_height
            figure, ax = plt.subplots(figsize=(width, height))
            ax.axis("off")
            ax.legend(handles, [str(v) for v in values], title=name,
                      loc="center", frameon=False, fontsize=fontsize,
                      title_fontsize=fontsize, ncol=ncol)
            legends[name] = (figure, ax)
        return legends

    def _draw(self, table, ax, group_by, x, y, *, intervals=False, yscale="linear"):
        colors, markers = self._styles(table, group_by)
        grouped = (table.groupby(group_by[0] if len(group_by) == 1 else list(group_by),
                                 dropna=False, sort=True) if group_by else [((), table)])
        for key, rows in grouped:
            values = key if isinstance(key, tuple) else (key,)
            rows = rows.sort_values(x)
            color = colors[values[0]] if group_by else colors[None]
            marker = markers[values[1]] if len(group_by) == 2 else markers[None]
            observed = rows[y].to_numpy(dtype=float)
            # NaN breaks the line at zero/undefined observations, including on
            # linear axes. No artificial positive failure rate is plotted.
            visible = np.isfinite(observed)
            if intervals or yscale == "log":
                visible &= observed > 0
            ax.plot(rows[x].to_numpy(dtype=float), np.where(visible, observed, np.nan),
                    color=color, marker=marker)
            if intervals:
                ax.fill_between(rows[x].to_numpy(dtype=float),
                                rows["ler_low"].to_numpy(dtype=float),
                                rows["ler_high"].to_numpy(dtype=float),
                                color=color, alpha=.10)
        ax.set_yscale(yscale)
        ax.grid(alpha=.25)

    def plot_ler(self, *, filter=None, group_by=("distance", "decoder_type"),
                 baseline_compare=False, yscale="log", plot_width=7.4,
                 plot_height=4.6, ax=None):
        """Return (figure, axes, table); use plot_legends for separate figures.

        Zero LER observations have Wilson shading only, on both axis scales.
        Uniform circuit-noise rates and Wilson limits are converted per round.
        A log axis clips bands at its lower visible limit without changing the
        returned interval endpoints or inserting a positive point estimate.
        """
        if yscale not in ("linear", "log"):
            raise ValueError("yscale must be 'linear' or 'log'")
        if baseline_compare and not {"decoder_type", "decoder_alias"}.intersection(group_by):
            raise ValueError("baseline_compare requires decoder_type or decoder_alias in group_by")
        table = self._ler_table(filter, baseline_compare)
        names = self._groups(table, group_by, "physical_error_rate")
        figure, ax = self._axes(ax, plot_width, plot_height)
        self._draw(table, ax, names, "physical_error_rate", "logical_error_rate",
                   intervals=True, yscale=yscale)
        upper = min(1.0, float(table.ler_high.max()) * 1.15)
        if yscale == "log":
            positive = table.loc[table.ler_low > 0, "ler_low"]
            floor = min(float(table.ler_high.min()) / 10,
                        float(positive.min()) if len(positive) else np.inf)
            ax.set_ylim(floor / 1.5, max(upper, floor * 10))
        else:
            ax.set_ylim(0, upper)
        ax.set(xlabel="Physical error rate",
               ylabel="Logical error rate per round" if (table.noise_model == "uniform").all()
               else "Logical error rate")
        return figure, ax, table

    def improvement_table(self, *, physical_error_rate, filter=None):
        """Baseline LER / decoder LER at one physical error rate.

        Paired decoders use their own default_logical_error metric. Others use
        the same deterministic representative as plot_ler's baseline, matched
        on every physical condition, including rounds. Independent samples
        are labelled in baseline_paired. Positive/zero yields inf; 0/0 yields
        NaN. These are empirical ratios, with no inferred confidence interval.
        """
        if not np.isfinite(physical_error_rate) or physical_error_rate <= 0:
            raise ValueError("physical_error_rate must be positive and finite")
        selection = dict(filter or {})
        if "physical_error_rate" in selection:
            wanted = selection["physical_error_rate"]
            values = wanted if isinstance(wanted, (list, tuple, set)) else [wanted]
            if physical_error_rate not in values:
                raise ValueError("physical_error_rate conflicts with filter")
        selection["physical_error_rate"] = physical_error_rate
        table = self.summary(selection)
        reference_filter = {k: v for k, v in selection.items() if k not in ("decoder_type", "decoder_alias")}
        references = self._ler_table(reference_filter, True)
        references = references[references.decoder_type == "baseline"]
        condition = [name for name in PARAMETERS if name not in ("decoder_type", "decoder_alias")]
        if table.default_failures.notna().any():
            selected_references = self._ler_table(selection, True)
            selected_references = selected_references[selected_references.decoder_type == "baseline"]
            references = (pd.concat([selected_references, references], ignore_index=True)
                          .drop_duplicates(condition))
        reference = references.set_index(condition)
        table = table.copy()
        rates, sources, paired_flags = [], [], []
        for row in table.itertuples():
            paired = not pd.isna(row.default_failures)
            if paired:
                rates.append(row.default_logical_error_rate)
                sources.append(row.point_directory)
            else:
                key = tuple(getattr(row, name) for name in condition)
                if key not in reference.index:
                    raise ValueError(f"No matching baseline for {row.point_directory}")
                match = reference.loc[key]
                rates.append(match.logical_error_rate)
                sources.append(match.point_directory)
            paired_flags.append(paired)
        table["baseline_logical_error_rate"] = rates
        table["baseline_point_directory"] = sources
        table["baseline_paired"] = paired_flags
        with np.errstate(divide="ignore", invalid="ignore"):
            table["improvement_ratio"] = (table.baseline_logical_error_rate.to_numpy(dtype=float)
                                          / table.logical_error_rate.to_numpy(dtype=float))
        return table

    def plot_improvement_ratio(self, *, physical_error_rate, filter=None,
                               x="distance", group_by=("distance", "decoder_type"),
                               yscale="linear", plot_width=7.4, plot_height=4.6, ax=None):
        """Return (figure, axes, table) with shared LER color/marker encodings.

        Infinite and undefined ratios are retained in the table and omitted
        from the plot. The reference line at 1 denotes no improvement.
        """
        if x not in ("distance", "rounds", "physical_error_rate"):
            raise ValueError("x must be distance, rounds or physical_error_rate")
        if yscale not in ("linear", "log"):
            raise ValueError("yscale must be 'linear' or 'log'")
        table = self.improvement_table(physical_error_rate=physical_error_rate, filter=filter)
        names = self._groups(table, group_by, x)
        figure, ax = self._axes(ax, plot_width, plot_height)
        self._draw(table, ax, names, x, "improvement_ratio", yscale=yscale)
        ax.axhline(1, color="0.5", linestyle="--", linewidth=1)
        ax.set(xlabel="Code distance" if x == "distance" else x.replace("_", " ").capitalize(),
               ylabel="LER improvement ratio (baseline / decoder)")
        if x == "distance":
            ax.set_xticks(sorted(table.distance.unique()))
        return figure, ax, table
