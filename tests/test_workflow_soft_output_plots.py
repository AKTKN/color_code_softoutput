"""Scatter plotting and failure association from independent saved-shot fixtures."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PathCollection, PolyCollection
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from scipy.stats import norm

from color_code_softoutput.analysis.workflow_soft_output import WorkflowSoftOutputRun
from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.planner import plan_points, point_directory_name


@pytest.fixture
def saved_scores(tmp_path):
    raw = {
        "simulation": {"output_root": str(tmp_path), "shots": 6, "workers": 1,
                       "master_seed": 7, "buffer_shots": 3, "verbose": False},
        "chunking": {"calibration_shots": 1, "target_chunk_seconds": 1,
                     "min_chunk_shots": 1, "max_chunk_shots": 3,
                     "throughput_ema_alpha": .5},
        "sweep": {"distance": 3, "physical_error_rate": .01, "noise_model": "bitflip",
                  "rounds": 1, "circuit_type": "tri", "cnot_schedule": "tri_optimal"},
        "decoders": [
            {"type": "concat_mwpm", "options": {"comparative_decoding": True}},
            {"type": "color_correlated", "options": {"enable_colorcorrelated_decoding": True}},
        ],
    }
    (tmp_path / "run_log.json").write_text(json.dumps({"config": raw,
        "simulation_start_time": "start", "simulation_end_time": "end"}))
    shots = {
        "swim_distance": (np.array([0., 1, 1, 2, 2, 3]),
                          np.array([True, False, True, False, False, False])),
        "logical_gap": (np.array([0., .5, .5, 1, 1, 2]),
                        np.array([False, True, True, False, False, False])),
    }
    for point in plan_points(parse_workflow_config(raw)):
        directory = tmp_path / point_directory_name(point)
        directory.mkdir()
        metric = "logical_gap" if point.decoder_type == "concat_mwpm" else "swim_distance"
        scores, failures = shots[metric]
        for name, values, dtype in [(metric, scores, pa.float64()),
                                    ("logical_error", failures, pa.bool_())]:
            pq.write_table(pa.table({"shot_index": pa.array(range(6), type=pa.int64()),
                                     name: pa.array(values, type=dtype)}), directory / f"{name}.parquet")
    yield WorkflowSoftOutputRun(tmp_path), shots
    plt.close("all")


def test_signed_distribution_counts_normalization_and_scatter(saved_scores):
    run, shots = saved_scores
    figure, table = run.plot_distribution(metrics=["swim_distance", "logical_gap"],
        signed_logical_errors=True, normalize_frequency=True)
    assert not figure.axes[0].lines and not figure.axes[0].patches
    assert len(figure.axes[0].collections) == 4
    assert all(isinstance(item, PathCollection) for item in figure.axes[0].collections)
    assert figure.axes[0].get_yscale() == "log"
    for metric, (scores, failures) in shots.items():
        rows = table[table.metric == metric]
        assert rows.shots.sum() == 6
        assert rows.frequency.sum() == pytest.approx(1)
        for failure in (False, True):
            outcome = rows[rows.logical_error == failure]
            assert outcome['count'].sum() == np.count_nonzero(failures == failure)
            assert (outcome.score <= 0).all() if failure else (outcome.score >= 0).all()
            for row in outcome.itertuples():
                assert row.count == np.count_nonzero((scores == row.raw_score) & (failures == failure))
                assert row.frequency == row.count / 6
        # Negation changes the view only, never the stored score column.
        point = run.run.catalog[run.run.catalog.decoder_type == rows.decoder_type.iloc[0]].iloc[0]
        np.testing.assert_array_equal(pq.read_table(run.run.run_directory / point.point_directory
                                                    / f"{metric}.parquet")[metric].to_numpy(), scores)


def test_common_histogram_edges_and_single_metric_compatibility(saved_scores):
    run, _ = saved_scores
    _, table = run.plot_distribution(metrics=["swim_distance", "logical_gap"], bins=3)
    for metric in ("swim_distance", "logical_gap"):
        rows = table[table.metric == metric]
        assert rows['count'].sum() == 6
        assert rows.bin_left.unique().tolist() == [0, 1, 2]
        assert rows.bin_right.unique().tolist() == [1, 2, 3]
    _, single = run.plot_distribution(metric="logical_gap", filter={"decoder_type": "concat_mwpm"})
    assert set(single.metric) == {"logical_gap"}
    _, default = run.plot_distribution(filter={"decoder_type": "color_correlated"})
    assert set(default.metric) == {"swim_distance"}


def test_conditional_probability_uses_each_decoders_labels_and_wilson_bands(saved_scores):
    run, shots = saved_scores
    figure, table = run.plot_conditional_ler(metrics=["swim_distance", "logical_gap"])
    ax = figure.axes[0]
    assert not ax.lines
    assert sum(isinstance(item, PolyCollection) for item in ax.collections) == 2
    assert sum(isinstance(item, PathCollection) for item in ax.collections) == 2
    for metric, (scores, failures) in shots.items():
        rows = table[table.metric == metric]
        for row in rows.itertuples():
            keep = scores == row.score
            assert row.shots == np.count_nonzero(keep)
            assert row.failures == np.count_nonzero(failures[keep])
            assert row.logical_error_rate == failures[keep].mean()
        zero = rows[rows.failures == 0]
        assert (zero.low == 0).all() and (zero.high > 0).all()
    half = table[(table.metric == "swim_distance") & (table.score == 1)].iloc[0]
    z = norm.ppf(.995)
    expected_half_width = .5 * z / np.sqrt(2 + z * z)
    assert half.low == pytest.approx(.5 - expected_half_width)
    assert half.high == pytest.approx(.5 + expected_half_width)
    assert table[(table.metric == "logical_gap") & (table.score == .5)].iloc[0].logical_error_rate == 1
    # Zero estimates have bands but no scatter markers.
    scatter = [item for item in ax.collections if isinstance(item, PathCollection)]
    assert all(np.all(item.get_offsets()[:, 1] > 0) for item in scatter)


def test_postselection_scatter_bands_exact_thresholds_and_display_sign_isolation(saved_scores):
    run, shots = saved_scores
    run.plot_distribution(metrics=["swim_distance", "logical_gap"], signed_logical_errors=True)
    figure, table = run.plot_postselection(metrics=["swim_distance", "logical_gap"], xlim=(0, .8))
    ax = figure.axes[0]
    assert not ax.lines
    assert ax.get_xlim() == (0, .8)
    assert sum(isinstance(item, PolyCollection) for item in ax.collections) == 2
    assert sum(isinstance(item, PathCollection) for item in ax.collections) == 2
    for metric, (scores, failures) in shots.items():
        rows = table[table.metric == metric]
        assert rows.threshold.tolist() == np.unique(scores).tolist()
        for row in rows.itertuples():
            retained = scores >= row.threshold
            assert row.retained_shots == retained.sum()
            assert row.retained_failures == failures[retained].sum()
            assert row.abort_rate == pytest.approx(1 - retained.mean())
            assert row.residual_logical_error_rate == failures[retained].mean()
        assert (rows[rows.retained_failures == 0].high > 0).all()
    assert len(table) == 8  # xlim never changes the saved threshold/count table


def test_rounding_changes_ties_only_when_requested_and_styles_agree(saved_scores):
    run, _ = saved_scores
    figure, conditional = run.plot_conditional_ler(metrics=["swim_distance", "logical_gap"], round_digits=0)
    retention_figure, retention = run.plot_postselection(metrics=["swim_distance", "logical_gap"], round_digits=0)
    for metric in ("swim_distance", "logical_gap"):
        assert conditional[conditional.metric == metric].shots.sum() == 6
    assert retention[retention.metric == "logical_gap"].threshold.tolist() == [0, 1, 2]
    colors = lambda fig: [item.get_facecolor()[0] for item in fig.axes[0].collections if isinstance(item, PathCollection)]
    np.testing.assert_array_equal(colors(figure), colors(retention_figure))


@pytest.mark.parametrize("method", ["plot_distribution", "plot_conditional_ler", "plot_postselection"])
def test_metric_selection_errors_are_explicit(saved_scores, method):
    run, _ = saved_scores
    plot = getattr(run, method)
    with pytest.raises(ValueError, match="not both"):
        plot(metric="logical_gap", metrics=["swim_distance"])
    with pytest.raises(ValueError, match="sequence"):
        plot(metrics="logical_gap")
    with pytest.raises(ValueError, match="unique metrics"):
        plot(metrics=[])
    with pytest.raises(FileNotFoundError, match="No requested metric"):
        plot(metric="swim_distance", filter={"decoder_type": "concat_mwpm"})
    with pytest.raises(FileNotFoundError, match="No selected points"):
        plot(metrics=["swim_distance", "logical_gap"], filter={"decoder_type": "color_correlated"})
    with pytest.raises(ValueError, match="yscale"):
        plot(metrics=["swim_distance", "logical_gap"], yscale="unknown")


def test_availability_and_invalid_bins(saved_scores):
    run, _ = saved_scores
    available = run.available_metrics()
    assert available.groupby("decoder_type").logical_gap_available.first().to_dict() == {
        "color_correlated": False, "concat_mwpm": True}
    for bins in (0, True, [0., 1.], [0., 3., 2.], [0., np.inf]):
        with pytest.raises(ValueError, match="bins|bin edges"):
            run.plot_distribution(metrics=["swim_distance", "logical_gap"], bins=bins)
