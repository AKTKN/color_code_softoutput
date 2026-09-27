"""Distribution and post-selection plots for canonical YAML soft-output files."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .color_correlated import ColorCorrelatedRun, PARAMETERS
from .postselection import postselection_curve


METRICS = ("swim_distance", "logical_gap")


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
                values = []
                for batch in source.iter_batches(batch_size=65_536):
                    if any(column.null_count for column in batch.columns):
                        raise ValueError(f"Null values in {path}")
                    index.append(batch.column(0).to_numpy(zero_copy_only=False))
                    values.append(batch.column(1).to_numpy(zero_copy_only=False))
                shot_index = np.concatenate(index)
                if not np.array_equal(shot_index, np.arange(row.expected_shots)):
                    raise ValueError(f"Invalid shot indices in {path}")
                arrays.append(np.concatenate(values))
        scores, failures = arrays
        if not np.isfinite(scores).all() or np.any(scores < 0):
            raise ValueError(f"Invalid {metric} values in {directory}")
        return scores, failures

    def _iter_groups(self, metric, filter, group_by):
        selected, names = self._groups(filter, group_by)
        if metric not in METRICS:
            raise ValueError(f"metric must be one of {METRICS}")
        if names:
            groups = selected.groupby(list(names), sort=True, dropna=False)
        else:
            groups = [((), selected)]
        for key, frame in groups:
            key = key if isinstance(key, tuple) else (key,)
            data = [self._point(row, metric) for row in frame.itertuples()]
            yield dict(zip(names, key)), np.concatenate([x[0] for x in data]), np.concatenate([x[1] for x in data])

    def plot_distribution(self, *, metric: str = "swim_distance",
                          filter: Mapping[str, object] | None = None,
                          group_by: Sequence[str] = ("decoder_type",),
                          bins: int = 40, density: bool = True, ax=None):
        """Plot per-group score histograms and return counts by score interval."""
        if type(bins) is not int or bins < 1:
            raise ValueError("bins must be a positive integer")
        groups = list(self._iter_groups(metric, filter, group_by))
        all_scores = np.concatenate([scores for _, scores, _ in groups])
        low, high = float(all_scores.min()), float(all_scores.max())
        edges = np.linspace(low, high if high > low else low + 1, bins + 1)
        if ax is None:
            figure, ax = plt.subplots(figsize=(7.2, 4.5))
        else:
            figure = ax.figure
        rows = []
        for condition, scores, failures in groups:
            counts, _ = np.histogram(scores, bins=edges)
            widths = np.diff(edges)
            heights = counts / (len(scores) * widths) if density else counts
            label = ", ".join(f"{name}={value}" for name, value in condition.items()) or "all"
            ax.stairs(heights, edges, label=label)
            failed, _ = np.histogram(scores[failures], bins=edges)
            for index in range(bins):
                rows.append(condition | dict(metric=metric, bin_left=edges[index],
                    bin_right=edges[index + 1], shots=int(counts[index]),
                    failures=int(failed[index]), density=float(heights[index])))
        ax.set(xlabel=metric.replace("_", " "), ylabel="Density" if density else "Shots")
        ax.legend()
        figure.tight_layout()
        return figure, pd.DataFrame(rows)

    def plot_postselection(self, *, metric: str = "swim_distance",
                           filter: Mapping[str, object] | None = None,
                           group_by: Sequence[str] = ("decoder_type",),
                           round_digits: int | None = None, ax=None):
        """Abort scores below each threshold; show retained logical-error rate."""
        groups = self._iter_groups(metric, filter, group_by)
        if ax is None:
            figure, ax = plt.subplots(figsize=(7.2, 4.5))
        else:
            figure = ax.figure
        tables = []
        for condition, scores, failures in groups:
            curve = postselection_curve(scores, failures, round_digits=round_digits)
            for name, value in condition.items():
                curve[name] = value
            curve["metric"] = metric
            tables.append(curve)
            label = ", ".join(f"{name}={value}" for name, value in condition.items()) or "all"
            ax.plot(curve.abort_rate, curve.residual_logical_error_rate, label=label)
        ax.set(xlabel="Abort rate", ylabel="Post-selection logical error rate", xlim=(0, 1))
        ax.legend()
        figure.tight_layout()
        return figure, pd.concat(tables, ignore_index=True)
