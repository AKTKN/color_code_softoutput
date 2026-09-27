"""Empirical comparison of four ways to aggregate three color SWIM values.

This module changes only the analyzed scalar score. Every strategy retains the
ordinary concatenated decoder's hard prediction, selected color, and logical
failure label. It establishes no theorem about the best aggregation rule.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
import pandas as pd

from .conditional_ler import ConditionalLERAnalyzer
from .figure_style import RevtexFigureStyle
from .postselection import PostSelectionAnalyzer
from .swim_distribution import SwimDistanceDistributionPlotter


STRATEGIES: Final[tuple[str, ...]] = ("selected_color", "minimum", "maximum", "mean")
STRATEGY_LABELS: Final[dict[str, str]] = {
    "selected_color": "Selected-color output",
    "minimum": "Minimum across colors",
    "maximum": "Maximum across colors",
    "mean": "Mean across colors",
}
SCORE_LABELS: Final[dict[str, str]] = {
    "selected_color": r"Selected-color SWIM distance $\phi_{\mathrm{sel}}$",
    "minimum": r"Minimum SWIM distance $\phi_{\min}$",
    "maximum": r"Maximum SWIM distance $\phi_{\max}$",
    "mean": r"Mean SWIM distance $\bar{\phi}$",
}
_COLOR_COLUMNS: Final[list[str]] = [f"swim_distance_{color}" for color in "rgb"]
_IDENTITY_COLUMNS: Final[list[str]] = [
    "config_id", "batch_id", "shot_index", "distance", "physical_error_rate"
]


def select_swim_output(frame: pd.DataFrame, strategy: str) -> np.ndarray:
    """Compute one empirical scalar score per shot from the three color values.

    Args:
        frame: Rows containing swim_distance_r/g/b and, for selected_color,
            ordinary_selected_color. Values use the experiment's stored units.
        strategy: One of selected_color, minimum, maximum, or mean.
    Returns:
        New float array of shape (shots,); the input frame is never modified.
    Raises:
        ValueError: Unknown strategy, missing/invalid values, or selected color.
    Scientific semantics:
        Only selected_color is the implemented decoder output. The other three
        are post-hoc empirical aggregation rules evaluated against the same
        ordinary hard-decoder failure labels.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown SWIM selection strategy: {strategy}")
    if not set(_COLOR_COLUMNS).issubset(frame.columns):
        raise ValueError("All three color-specific SWIM columns are required")
    values = frame[_COLOR_COLUMNS].to_numpy(dtype=float, copy=True)
    if values.ndim != 2 or values.shape[1] != 3 or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Color-specific SWIM values must be finite and nonnegative")
    if strategy == "minimum":
        return values.min(axis=1)
    if strategy == "maximum":
        return values.max(axis=1)
    if strategy == "mean":
        return values.mean(axis=1)
    if "ordinary_selected_color" not in frame:
        raise ValueError("Selected-color strategy requires ordinary_selected_color")
    selected = frame.ordinary_selected_color.map({color: index for index, color in enumerate("rgb")})
    if selected.isna().any():
        raise ValueError("ordinary_selected_color must be one of r, g, b")
    return values[np.arange(len(values)), selected.to_numpy(dtype=int)]


class SwimSelectionDataset:
    """Read-only strategy view compatible with the existing three plotters.

    Args:
        dataset: Existing circuit/code-capacity dataset with per-color scores.
        strategy: One of STRATEGIES.
        output_directory: Dedicated directory for this strategy's artifacts.
    Notes:
        ``selected_swim_distance`` is a compatibility alias in projected rows;
        the original Parquet data are neither changed nor rewritten.
    """

    def __init__(self, dataset, strategy: str, output_directory: Path) -> None:
        if strategy not in STRATEGIES:
            raise ValueError(f"Unknown SWIM selection strategy: {strategy}")
        self.dataset = dataset
        self.strategy = strategy
        self.run_directory = Path(output_directory)
        (self.run_directory / "figures").mkdir(parents=True, exist_ok=True)
        self.metadata = dataset.metadata
        self.plot_title = STRATEGY_LABELS[strategy]
        self.score_label = SCORE_LABELS[strategy]
        # The strategy already appears as the title; repeat only distance in the
        # legend so long strategy names cannot clip a three-series figure.
        self.metric_display_name = None

    def available_values(self) -> dict[str, list]:
        """Delegate the immutable experimental grid to the source dataset."""
        return self.dataset.available_values()

    def metric_rows(self, metric: str, *, distance=None, physical_error_rate=None,
                    failure_column: str | None = None) -> pd.DataFrame:
        """Project derived score plus ordinary failure labels and stable identities.

        Args:
            metric: Must be selected_swim_distance for plotter compatibility.
            distance, physical_error_rate: Existing dataset filters.
            failure_column: None or ordinary_logical_error.
        Returns:
            Sorted rows with derived selected_swim_distance in stored score units.
        Raises:
            ValueError: Unsupported metric/failure association or selected-score
                inconsistency in the source data.
        """
        if metric != "selected_swim_distance":
            raise ValueError("Strategy views expose only selected_swim_distance")
        if failure_column not in (None, "ordinary_logical_error"):
            raise ValueError("Every strategy must use ordinary_logical_error")
        columns = _IDENTITY_COLUMNS + _COLOR_COLUMNS + [
            "ordinary_selected_color", "ordinary_logical_error"
        ]
        rows = self.dataset.read(columns, distance=distance,
                                 physical_error_rate=physical_error_rate)
        derived = select_swim_output(rows, self.strategy)
        if self.strategy == "selected_color":
            saved = self.dataset.read(
                _IDENTITY_COLUMNS + ["selected_swim_distance"],
                distance=distance, physical_error_rate=physical_error_rate,
            ).sort_values(_IDENTITY_COLUMNS)
            ordered = rows.assign(_derived=derived).sort_values(_IDENTITY_COLUMNS)
            np.testing.assert_array_equal(ordered._derived.to_numpy(), saved.selected_swim_distance.to_numpy())
        result = rows[_IDENTITY_COLUMNS + ["ordinary_logical_error"]].copy()
        result["selected_swim_distance"] = derived
        return result.sort_values(_IDENTITY_COLUMNS).reset_index(drop=True)


@dataclass(frozen=True)
class StrategyAnalysis:
    """One strategy's three open figures and saved numerical tables."""

    strategy: str
    directory: Path
    distribution_figure: object
    distribution_table: pd.DataFrame
    conditional_figure: object
    conditional_table: pd.DataFrame
    fit_table: pd.DataFrame
    postselection_figure: object
    postselection_table: pd.DataFrame


def analyze_swim_selection_strategy(dataset, strategy: str, *, output_directory: Path,
                                    round_digits: int | None = None,
                                    signed_logical_errors: bool = False,
                                    normalize_frequency: bool = False,
                                    bins="auto", style: RevtexFigureStyle | None = None) -> StrategyAnalysis:
    """Generate and save the standard three analyses for one aggregation rule.

    Args:
        dataset: Existing dataset; no sampling API is called.
        strategy: One of STRATEGIES.
        output_directory: Parent; artifacts go in its strategy-named child.
        round_digits: Existing optional score rounding before all analyses.
        signed_logical_errors: Existing distribution display convention.
        normalize_frequency: Existing distribution normalization option.
        bins: Existing distribution/conditional grouping option.
        style: Shared publication style or explicit test style.
    Returns:
        StrategyAnalysis with open figures for notebook display and all tables.
    Scientific semantics:
        Distribution and conditional LER use ordinary decoder failures.
        Post-selection retains scores >= threshold and also uses ordinary
        failures. Wilson bands and exact rounded/raw tie behavior are inherited.
    """
    directory = Path(output_directory) / strategy
    view = SwimSelectionDataset(dataset, strategy, directory)
    values = view.available_values()
    selection = dict(distance=values["distance"],
                     physical_error_rate=values["physical_error_rate"][0])
    figure_style = style or RevtexFigureStyle()
    distribution, counts = SwimDistanceDistributionPlotter(figure_style).plot(
        view, **selection, signed_logical_errors=signed_logical_errors,
        normalize_frequency=normalize_frequency, bins=bins,
        round_digits=round_digits,
    )
    conditional, rates, fits = ConditionalLERAnalyzer(figure_style).plot(
        view, **selection, bins=bins, overlay_fit=False,
        round_digits=round_digits,
    )
    postselection, retention = PostSelectionAnalyzer(figure_style).plot(
        view, **selection, include_forced_gap=False, round_digits=round_digits,
    )
    suffix = "" if round_digits is None else f"_round{round_digits}"
    counts.to_parquet(directory / f"distribution_counts{suffix}.parquet", index=False)
    rates.to_parquet(directory / f"conditional_ler_counts{suffix}.parquet", index=False)
    retention.to_parquet(directory / f"postselection_counts{suffix}.parquet", index=False)
    return StrategyAnalysis(strategy, directory, distribution, counts,
                            conditional, rates, fits, postselection, retention)


def analyze_swim_selection_strategies(dataset, *, output_directory: Path,
                                      strategies=STRATEGIES, **kwargs) -> dict[str, StrategyAnalysis]:
    """Run the three saved-data analyses separately for every requested strategy.

    Args:
        dataset: Existing dataset; never sampled or mutated.
        output_directory: Parent for separate strategy directories.
        strategies: Unique subset/order of STRATEGIES.
        **kwargs: Options accepted by analyze_swim_selection_strategy.
    Returns:
        Ordered insertion-preserving mapping from strategy to analysis result.
    Raises:
        ValueError: Empty, duplicate, or unknown strategy selection.
    """
    strategies = tuple(strategies)
    if not strategies or len(set(strategies)) != len(strategies) or any(s not in STRATEGIES for s in strategies):
        raise ValueError("Choose a nonempty unique subset of known strategies")
    return {strategy: analyze_swim_selection_strategy(
        dataset, strategy, output_directory=output_directory, **kwargs
    ) for strategy in strategies}
