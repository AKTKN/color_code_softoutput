"""Saved-run analysis checks with independently constructed Parquet points."""

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.analysis.color_correlated import ColorCorrelatedRun
from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.planner import plan_points, point_directory_name


def _run(tmp_path, *, uniform=False):
    raw = {
        "simulation": {"output_root": str(tmp_path), "shots": 3, "workers": 1,
                       "master_seed": 7, "buffer_shots": 3, "verbose": False},
        "chunking": {"calibration_shots": 1, "target_chunk_seconds": 1,
                     "min_chunk_shots": 1, "max_chunk_shots": 3,
                     "throughput_ema_alpha": .5},
        "sweep": {"distance": [3, 5], "physical_error_rate": [.01, .02],
                  "noise_model": "uniform" if uniform else "depol",
                  "rounds": "distance" if uniform else 1, "circuit_type": "tri",
                  "cnot_schedule": "tri_optimal"},
        "decoders": [
            {"type": "concat_mwpm"},
            {"type": "color_correlated",
             "options": {"enable_colorcorrelated_decoding": True}},
        ],
    }
    (tmp_path / "run_log.json").write_text(json.dumps({
        "config": raw, "simulation_start_time": "start",
        "simulation_end_time": "end",
    }))
    for point in plan_points(parse_workflow_config(raw)):
        directory = tmp_path / point_directory_name(point)
        directory.mkdir()
        correlated = point.decoder_type == "color_correlated"
        values = {
            "logical_error": [False, False, False],
            "default_logical_error": [False, True, False],
            "better_weight_by_color_correlated_decoding": [0, 1, 1],
            "effect_by_color_correlated_decoding": [0, int(correlated), 0],
        }
        for metric in (values if correlated else ("logical_error",)):
            array = pa.array(values[metric], type=pa.bool_() if metric.endswith("logical_error") else pa.uint8())
            pq.write_table(pa.table({"shot_index": pa.array([0, 1, 2], type=pa.int64()),
                                     metric: array}), directory / f"{metric}.parquet")
    return ColorCorrelatedRun(tmp_path)


def test_catalog_filter_counts_and_plot_encodings(tmp_path):
    run = _run(tmp_path)
    assert len(run.catalog) == 8 and run.catalog.data_available.all()
    selected = run.select({"distance": 3, "decoder_type": ["color_correlated"]})
    assert len(selected) == 2
    counts = run.count_table()
    correlated = counts[counts.decoder_type == "color_correlated"]
    ordinary = counts[counts.decoder_type == "concat_mwpm"]
    assert set(correlated.better_weight_count) == {2}
    assert set(correlated.effect_count) == {1}
    assert ordinary.better_weight_count.isna().all()
    assert len(run.count_table(filter={"distance": 3})) == 4
    figure, axes, table = run.plot_ler(group_by=["distance", "decoder_type"])
    assert len(table) == 8 and len(axes.lines) == 4
    assert len({line.get_color() for line in axes.lines}) == 2
    assert len({line.get_marker() for line in axes.lines}) == 2
    assert axes.get_yscale() == "log"
    assert len(figure.axes) == 2
    assert len(figure.axes[1].patches) == 4
    assert axes.get_position().y1 < figure.axes[1].get_position().y0
    for line in axes.lines:
        np.testing.assert_allclose(line.get_xdata(), [.01, .02])
        assert np.all(line.get_ydata() > 0)
    plt.close(figure)
    figure, axes, table = run.plot_ler(filter={"distance": 3}, group_by=["decoder_type"])
    assert len(table) == 4 and len(axes.lines) == 2
    assert axes.get_position().width * figure.get_figwidth() == pytest.approx(7.4)
    plt.close(figure)
    figure, axes, _ = run.plot_ler(group_by=["distance", "decoder_type"], yscale="linear")
    assert axes.get_yscale() == "linear"
    assert axes.get_ylim()[0] == 0
    plt.close(figure)


def test_rejects_hidden_varying_conditions_and_bad_data(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(ValueError, match="at most two"):
        run.plot_ler(group_by=["distance", "decoder_type", "noise_model"])
    with pytest.raises(ValueError, match="yscale"):
        run.plot_ler(yscale="unknown")
    with pytest.raises(ValueError, match="varying parameters"):
        run.plot_ler(group_by=["distance"])
    with pytest.raises(ValueError, match="requires decoder_type"):
        run.plot_ler(group_by=["distance"], baseline_compare=True)
    with pytest.raises(ValueError, match="No color-correlated points"):
        run.plot_ler(filter={"decoder_type": "concat_mwpm"},
                     group_by=["distance", "decoder_type"], baseline_compare=True)
    with pytest.raises(ValueError, match="Unknown filter"):
        run.select({"unknown": 3})
    with pytest.raises(ValueError, match="No experiment points"):
        run.select({"distance": 7})
    name = run.catalog.iloc[0].point_directory
    path = tmp_path / name / "logical_error.parquet"
    table = pq.read_table(path)
    pq.write_table(table.set_column(0, "shot_index", pa.array([0, 2, 1])), path)
    run = ColorCorrelatedRun(tmp_path)
    with pytest.raises(ValueError, match="shot indices"):
        run.summary({"distance": int(run.catalog.iloc[0].distance),
                     "decoder_type": str(run.catalog.iloc[0].decoder_type),
                     "physical_error_rate": float(run.catalog.iloc[0].physical_error_rate)})


def test_baseline_uses_paired_default_metric(tmp_path):
    run = _run(tmp_path)
    figure, axes, table = run.plot_ler(
        group_by=["distance", "decoder_type"], baseline_compare=True)
    assert len(table) == 12
    assert len(axes.lines) == 6
    assert len(figure.axes[1].patches) == 6
    baseline = table[table.decoder_type == "baseline"]
    correlated = table[table.decoder_type == "color_correlated"]
    assert len(baseline) == len(correlated) == 4
    assert set(baseline.metric) == {"default_logical_error"}
    assert set(baseline.source_decoder_type) == {"color_correlated"}
    assert set(baseline.failures) == {1}
    assert set(baseline.logical_error_rate) == {1 / 3}
    assert set(correlated.failures) == {0}
    plt.close(figure)
    figure, axes, table = run.plot_ler(
        filter={"distance": 3, "decoder_type": "color_correlated"},
        group_by=["decoder_type"], baseline_compare=True)
    assert set(table.decoder_type) == {"color_correlated", "baseline"}
    assert len(axes.lines) == 2
    plt.close(figure)


def test_uniform_ler_is_per_round_and_rounds_do_not_split_legend(tmp_path):
    run = _run(tmp_path, uniform=True)
    figure, axes, table = run.plot_ler(
        group_by=["distance", "decoder_type"], baseline_compare=True)
    assert axes.get_ylabel() == "Logical error rate per round"
    assert len(axes.lines) == 6
    assert len(figure.axes[1].patches) == 6
    baseline = table[table.decoder_type == "baseline"]
    assert set(baseline.logical_error_rate_total) == {1 / 3}
    for row in baseline.itertuples():
        assert row.logical_error_rate == pytest.approx(1 - (2 / 3) ** (1 / row.rounds))
        assert row.ler_low < row.logical_error_rate < row.ler_high
    plt.close(figure)
    with pytest.raises(ValueError, match="rounds"):
        run.plot_ler(group_by=["distance", "rounds"])
