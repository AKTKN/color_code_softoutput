"""Saved-data-only gates for three-color SWIM output aggregation."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from color_code_softoutput.analysis.figure_style import RevtexFigureStyle
from color_code_softoutput.analysis.swim_selection import (
    STRATEGIES,
    STRATEGY_LABELS,
    SwimSelectionDataset,
    analyze_swim_selection_strategies,
    select_swim_output,
)


def fixture_rows() -> pd.DataFrame:
    """Return three distances with stable identities and deliberate score ties."""
    rows = []
    for distance in (3, 5, 7):
        for shot, (scores, color, failure) in enumerate((
            ((1., 4., 7.), "r", False),
            ((5., 2., 8.), "g", True),
            ((9., 6., 3.), "b", False),
            ((2., 8., 5.), "g", True),
        )):
            selected = scores["rgb".index(color)]
            rows.append(dict(config_id=f"d{distance}", batch_id=0,
                shot_index=shot, distance=distance, physical_error_rate=.003,
                swim_distance_r=scores[0], swim_distance_g=scores[1],
                swim_distance_b=scores[2], ordinary_selected_color=color,
                ordinary_logical_error=failure,
                selected_swim_distance=selected))
    return pd.DataFrame(rows)


class MemoryDataset:
    """Minimal immutable source dataset used by existing plotter interfaces."""

    def __init__(self, rows: pd.DataFrame, directory: Path):
        self.rows = rows
        self.run_directory = directory
        self.metadata = {"experiment_name": "fixture"}

    def available_values(self):
        return {"distance": [3, 5, 7], "physical_error_rate": [.003]}

    def read(self, columns=None, *, distance=None, physical_error_rate=None, **kwargs):
        del kwargs
        frame = self.rows
        if distance is not None:
            values = [distance] if np.isscalar(distance) else list(distance)
            frame = frame[frame.distance.isin(values)]
        if physical_error_rate is not None:
            values = [physical_error_rate] if np.isscalar(physical_error_rate) else list(physical_error_rate)
            frame = frame[frame.physical_error_rate.isin(values)]
        return frame.copy() if columns is None else frame[columns].copy()


def test_four_strategy_definitions_and_no_mutation():
    rows = fixture_rows().iloc[:4].copy()
    before = rows.copy(deep=True)
    np.testing.assert_array_equal(select_swim_output(rows, "selected_color"), [1, 2, 3, 8])
    np.testing.assert_array_equal(select_swim_output(rows, "minimum"), [1, 2, 3, 2])
    np.testing.assert_array_equal(select_swim_output(rows, "maximum"), [7, 8, 9, 8])
    np.testing.assert_array_equal(select_swim_output(rows, "mean"), [4, 5, 6, 5])
    pd.testing.assert_frame_equal(rows, before)


def test_invalid_strategy_columns_values_and_selected_color():
    rows = fixture_rows().iloc[:2].copy()
    with pytest.raises(ValueError, match="Unknown"):
        select_swim_output(rows, "median")
    with pytest.raises(ValueError, match="three"):
        select_swim_output(rows.drop(columns="swim_distance_b"), "minimum")
    rows.loc[0, "swim_distance_r"] = np.inf
    with pytest.raises(ValueError, match="finite"):
        select_swim_output(rows, "maximum")
    rows = fixture_rows().iloc[:2].copy()
    rows.loc[0, "ordinary_selected_color"] = "x"
    with pytest.raises(ValueError, match="r, g, b"):
        select_swim_output(rows, "selected_color")


def test_strategy_view_preserves_identities_failures_and_checks_stored_selected(tmp_path):
    source = MemoryDataset(fixture_rows(), tmp_path)
    for strategy in STRATEGIES:
        view = SwimSelectionDataset(source, strategy, tmp_path / strategy)
        result = view.metric_rows("selected_swim_distance", distance=5,
                                  physical_error_rate=.003)
        assert len(result) == 4
        assert result.ordinary_logical_error.tolist() == [False, True, False, True]
        assert result.shot_index.tolist() == [0, 1, 2, 3]
        assert view.plot_title == STRATEGY_LABELS[strategy]
    broken = fixture_rows()
    broken.loc[0, "selected_swim_distance"] += 1
    with pytest.raises(AssertionError):
        SwimSelectionDataset(MemoryDataset(broken, tmp_path), "selected_color",
                             tmp_path / "broken").metric_rows("selected_swim_distance")


def test_all_strategies_generate_separate_standard_analyses(tmp_path):
    source = MemoryDataset(fixture_rows(), tmp_path)
    original = source.rows.copy(deep=True)
    results = analyze_swim_selection_strategies(
        source, output_directory=tmp_path / "analysis", round_digits=1,
        style=RevtexFigureStyle(test_mode=True),
    )
    try:
        assert tuple(results) == STRATEGIES
        for strategy, result in results.items():
            assert result.directory == tmp_path / "analysis" / strategy
            assert result.distribution_figure.axes[0].get_title() == STRATEGY_LABELS[strategy]
            assert result.conditional_figure.axes[0].get_title() == STRATEGY_LABELS[strategy]
            assert result.postselection_figure.axes[0].get_title() == STRATEGY_LABELS[strategy]
            assert [line.get_label() for line in result.postselection_figure.axes[0].lines] == [
                "d=3", "d=5", "d=7"
            ]
            assert result.distribution_table["count"].sum() == 12
            assert result.conditional_table.shots.sum() == 12
            assert result.postselection_table.iloc[0].retained_shots == 4
            assert len(list((result.directory / "figures").glob("*.png"))) == 3
            assert len(list(result.directory.glob("*_counts_round1.parquet"))) == 3
    finally:
        for result in results.values():
            plt.close(result.distribution_figure)
            plt.close(result.conditional_figure)
            plt.close(result.postselection_figure)
    pd.testing.assert_frame_equal(source.rows, original)


@pytest.mark.parametrize("strategies", [(), ("minimum", "minimum"), ("median",)])
def test_invalid_strategy_sets(strategies, tmp_path):
    with pytest.raises(ValueError):
        analyze_swim_selection_strategies(
            MemoryDataset(fixture_rows(), tmp_path), output_directory=tmp_path,
            strategies=strategies, style=RevtexFigureStyle(test_mode=True),
        )
