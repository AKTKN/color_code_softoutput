"""Saved-run analysis checks with independently constructed Parquet points."""

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.analysis.color_correlated import ColorCorrelatedRun
from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.planner import plan_points, point_directory_name


def _run(tmp_path, *, uniform=False, advanced=False, color_b=None, tesseract=False):
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
    if tesseract:
        raw["decoders"].append({"type": "tesseract"})
    if advanced:
        raw["decoders"].extend([
            {"type": "relifting", "options": {"enable_cross_color_relifting": True,
                                               "remove_non_edge_like_errors": False}},
            {"type": "perturbation", "options": {"enable_prior_perturbation": True,
                                                  "perturbation_ensemble_size": 2}},
        ])
    if color_b is not None:
        raw["decoders"][1]["options"]["color_correlated_b"] = color_b
    (tmp_path / "run_log.json").write_text(json.dumps({
        "config": raw, "simulation_start_time": "start",
        "simulation_end_time": "end",
    }))
    for point in plan_points(parse_workflow_config(raw)):
        directory = tmp_path / point_directory_name(point)
        directory.mkdir()
        paired = point.decoder_type not in ("concat_mwpm", "tesseract")
        values = {
            "logical_error": [False, False, False],
            "default_logical_error": [False, True, False],
            "better_weight_by_color_correlated_decoding": [0, 1, 1],
            "effect_by_color_correlated_decoding": [0, int(paired), 0],
        }
        for metric in (values if paired else ("logical_error",)):
            array = pa.array(values[metric], type=pa.bool_() if metric.endswith("logical_error") else pa.uint8())
            pq.write_table(pa.table({"shot_index": pa.array([0, 1, 2], type=pa.int64()),
                                     metric: array}), directory / f"{metric}.parquet")
    return ColorCorrelatedRun(tmp_path)


def test_saved_power_guide_run_loads_and_summarizes(tmp_path):
    run = _run(tmp_path, color_b=2.0)
    assert dict(run.config.decoders[1].options)["color_correlated_b"] == 2.0
    table = run.summary()
    assert len(table) == 8
    assert run.catalog.data_available.all()


def test_effect_table_counts_rescues_worsening_and_signed_net(tmp_path):
    run = _run(tmp_path)
    point = run.catalog[run.catalog.decoder_type == "color_correlated"].iloc[0]
    directory = tmp_path / point.point_directory
    # Baseline fails on shot 1; new decoder fails on shots 0 and 2.
    # Thus there is one rescue, two worsened shots, and net effect -1.
    pq.write_table(pa.table({"shot_index": pa.array([0, 1, 2], type=pa.int64()),
                             "logical_error": pa.array([True, False, True])}),
                   directory / "logical_error.parquet")
    run = ColorCorrelatedRun(tmp_path)
    table = run.effect_table({"distance": int(point.distance),
                              "physical_error_rate": float(point.physical_error_rate)})
    row = table[table.decoder_type == "color_correlated"].iloc[0]
    assert (row.effect_count, row.worsened_count, row.net_effect_count) == (1, 2, -1)
    summary = run.summary({"distance": int(point.distance),
                           "physical_error_rate": float(point.physical_error_rate)})
    correlated = summary[summary.decoder_type == "color_correlated"].iloc[0]
    assert correlated.net_effect_count == correlated.default_failures - correlated.failures
    ordinary = table[table.decoder_type == "concat_mwpm"].iloc[0]
    assert pd.isna(ordinary.worsened_count)
    assert pd.isna(ordinary.net_effect_count)
    pq.write_table(pa.table({"shot_index": pa.array([0, 1, 2], type=pa.int64()),
                             "effect_by_color_correlated_decoding": pa.array([1, 1, 1], type=pa.uint8())}),
                   directory / "effect_by_color_correlated_decoding.parquet")
    with pytest.raises(ValueError, match="Inconsistent paired"):
        ColorCorrelatedRun(tmp_path).effect_table({"distance": int(point.distance),
                                                  "physical_error_rate": float(point.physical_error_rate)})


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
    assert figure.axes == [axes]
    legends = run.plot_legends(table, group_by=["distance", "decoder_type"])
    assert set(legends) == {"distance", "decoder_type"}
    assert len({id(figure), *(id(pair[0]) for pair in legends.values())}) == 3
    for name, (legend_figure, legend_axes) in legends.items():
        legend = legend_axes.get_legend()
        assert legend.get_title().get_text() == name
        assert len(legend.get_texts()) == 2
        plt.close(legend_figure)
    for line in axes.lines:
        np.testing.assert_allclose(line.get_xdata(), [.01, .02])
        assert np.isnan(line.get_ydata()).all()
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
    with pytest.raises(ValueError, match="No advanced-decoder points"):
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
    assert figure.axes == [axes]
    baseline = table[table.decoder_type == "baseline"]
    correlated = table[table.decoder_type == "color_correlated"]
    assert len(baseline) == len(correlated) == 4
    assert set(baseline.metric) == {"default_logical_error"}
    assert set(baseline.source_decoder_type) == {"color_correlated"}
    assert set(baseline.failures) == {1}
    assert set(baseline.logical_error_rate) == {1 / 3}
    assert set(correlated.failures) == {0}
    assert baseline[["effect_count", "worsened_count", "net_effect_count"]].isna().all().all()
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
    assert figure.axes == [axes]
    baseline = table[table.decoder_type == "baseline"]
    assert set(baseline.logical_error_rate_total) == {1 / 3}
    for row in baseline.itertuples():
        assert row.logical_error_rate == pytest.approx(1 - (2 / 3) ** (1 / row.rounds))
        assert row.ler_low < row.logical_error_rate < row.ler_high
    plt.close(figure)
    with pytest.raises(ValueError, match="rounds"):
        run.plot_ler(group_by=["distance", "rounds"])


def test_multiple_advanced_types_share_one_plotted_baseline_and_filter_tables(tmp_path):
    run = _run(tmp_path, advanced=True)
    figure, axes, table = run.plot_ler(
        group_by=["distance", "decoder_type"], baseline_compare=True)
    assert len(table) == 20  # 16 decoder points + one baseline per four conditions
    assert len(axes.lines) == 10
    baseline = table[table.decoder_type == "baseline"]
    assert len(baseline) == 4
    assert set(baseline.source_decoder_type) == {"color_correlated"}
    assert set(run.summary({"decoder_type": "relifting"}).default_failures) == {1}
    assert set(run.summary({"decoder_type": "perturbation"}).default_failures) == {1}
    assert len(run.better_weight_table({"decoder_type": "relifting", "distance": 3})) == 2
    assert len(run.effect_table({"decoder_type": "perturbation", "distance": 5})) == 2
    assert set(run.effect_table({"decoder_type": "perturbation"}).effect_count) == {1}
    plt.close(figure)


def test_legacy_relifting_points_remain_readable_without_new_sidecars(tmp_path):
    run = _run(tmp_path, advanced=True)
    old_point = run.catalog[run.catalog.decoder_type == "relifting"].iloc[0]
    directory = tmp_path / old_point.point_directory
    for metric in ("default_logical_error",
                   "better_weight_by_color_correlated_decoding",
                   "effect_by_color_correlated_decoding"):
        (directory / f"{metric}.parquet").unlink()
    run = ColorCorrelatedRun(tmp_path)
    selected = run.summary({"decoder_type": "relifting"})
    assert selected.default_failures.isna().sum() == 1
    assert selected.default_failures.notna().sum() == 3
    assert selected.worsened_count.isna().sum() == 1
    assert selected.net_effect_count.isna().sum() == 1


def _write_errors(run, decoder, failures, *, baseline=None, rescues=None):
    for row in run.catalog[run.catalog.decoder_type == decoder].itertuples():
        values = {"logical_error": failures}
        if baseline is not None:
            values.update(default_logical_error=baseline,
                          effect_by_color_correlated_decoding=rescues)
        for metric, errors in values.items():
            pq.write_table(pa.table({"shot_index": pa.array([0, 1, 2], type=pa.int64()),
                                     metric: pa.array(errors, type=pa.bool_() if metric.endswith("logical_error") else pa.uint8())}),
                           run.run_directory / row.point_directory / f"{metric}.parquet")
    run._cache.clear()


def test_zero_points_break_lines_and_keep_exact_wilson_shade(tmp_path):
    run = _run(tmp_path)
    row = run.catalog[(run.catalog.distance == 3)
                      & (run.catalog.decoder_type == "concat_mwpm")
                      & (run.catalog.physical_error_rate == .02)].iloc[0]
    pq.write_table(pa.table({"shot_index": pa.array([0, 1, 2], type=pa.int64()),
                             "logical_error": pa.array([True, False, False])}),
                   tmp_path / row.point_directory / "logical_error.parquet")
    for scale in ("linear", "log"):
        fig, ax, table = run.plot_ler(filter={"distance": 3, "decoder_type": "concat_mwpm"},
                                     group_by=["decoder_type"], yscale=scale)
        assert np.isnan(ax.lines[0].get_ydata()[0])
        assert ax.lines[0].get_ydata()[1] == pytest.approx(1 / 3)
        assert table.iloc[0].logical_error_rate == table.iloc[0].ler_low == 0
        assert len(ax.collections) == 1
        assert any(np.any(path.vertices[:, 1] == 0) for path in ax.collections[0].get_paths())
        assert not fig.texts
        plt.close(fig)


def test_improvement_ratio_baselines_and_shared_filtered_encodings(tmp_path):
    run = _run(tmp_path, tesseract=True)
    _write_errors(run, "color_correlated", [True, False, False],
                  baseline=[False, True, True], rescues=[0, 1, 1])
    _write_errors(run, "tesseract", [True, False, False])
    selection = {"decoder_type": ["color_correlated", "tesseract"]}
    ler_fig, ler_ax, ler = run.plot_ler(filter=selection, baseline_compare=True)
    ratio_fig, ratio_ax, ratio = run.plot_improvement_ratio(physical_error_rate=.01, filter=selection)
    assert len(ratio) == 4
    assert set(ratio.improvement_ratio) == {2.0}
    assert ratio_ax.get_xlabel() == "Code distance"
    assert ratio_fig.axes == [ratio_ax]
    assert ratio[ratio.decoder_type == "color_correlated"].baseline_paired.all()
    assert not ratio[ratio.decoder_type == "tesseract"].baseline_paired.any()
    assert set(ratio.baseline_point_directory) == set(
        run.catalog[(run.catalog.decoder_type == "color_correlated")
                    & (run.catalog.physical_error_rate == .01)].point_directory)
    ler_styles = {(line.get_color(), line.get_marker()) for line in ler_ax.lines}
    assert all((line.get_color(), line.get_marker()) in ler_styles for line in ratio_ax.lines[:-1])
    subfig, subax, subtable = run.plot_improvement_ratio(
        physical_error_rate=.01, filter={"decoder_type": "tesseract", "distance": 5})
    matching = [line for line in ratio_ax.lines[:-1]
                if line.get_xdata()[0] == 5 and line.get_marker() == subax.lines[0].get_marker()]
    assert len(matching) == 1
    assert subax.lines[0].get_color() == matching[0].get_color()
    legends = run.plot_legends(ler)
    color_legend = legends["distance"][1].get_legend()
    marker_legend = legends["decoder_type"][1].get_legend()
    assert [h.get_marker() for h in color_legend.legend_handles] == ["None", "None"]
    assert all(h.get_linestyle() == "None" for h in marker_legend.legend_handles)
    assert len(marker_legend.legend_handles) == 3
    for fig in [ler_fig, ratio_fig, subfig, *(pair[0] for pair in legends.values())]:
        plt.close(fig)


def test_improvement_undefined_ratios_and_validation(tmp_path):
    run = _run(tmp_path)
    figure, ax, table = run.plot_improvement_ratio(physical_error_rate=.01,
                                                 filter={"decoder_type": "color_correlated"})
    assert np.isposinf(table.improvement_ratio).all()
    assert all(np.isnan(line.get_ydata()).all() for line in ax.lines[:-1])
    plt.close(figure)
    _write_errors(run, "color_correlated", [False, False, False],
                  baseline=[False, False, False], rescues=[0, 0, 0])
    assert run.improvement_table(physical_error_rate=.01).improvement_ratio.isna().all()
    with pytest.raises(ValueError, match="conflicts"):
        run.improvement_table(physical_error_rate=.01, filter={"physical_error_rate": .02})
    with pytest.raises(ValueError, match="varying parameters"):
        run.plot_improvement_ratio(physical_error_rate=.01, group_by=["distance"])
    with pytest.raises(ValueError, match="yscale"):
        run.plot_improvement_ratio(physical_error_rate=.01, yscale="bad")


def test_unpaired_ratio_uses_same_selected_baseline_as_ler(tmp_path):
    run = _run(tmp_path, advanced=True, tesseract=True)
    _write_errors(run, "perturbation", [True, False, False],
                  baseline=[False, True, True], rescues=[0, 1, 1])
    _write_errors(run, "tesseract", [True, False, False])
    selection = {"decoder_type": ["perturbation", "tesseract"]}
    figure, ax, ler = run.plot_ler(filter=selection, baseline_compare=True)
    ratio = run.improvement_table(physical_error_rate=.01, filter=selection)
    assert set(ratio.improvement_ratio) == {2.0}
    baseline = ler[(ler.decoder_type == "baseline") & (ler.physical_error_rate == .01)]
    assert set(ratio.baseline_point_directory) == set(baseline.point_directory)
    assert set(baseline.source_decoder_type) == {"perturbation"}
    plt.close(figure)


def test_uniform_ratio_uses_per_round_rates_and_keeps_custom_axes(tmp_path):
    run = _run(tmp_path, uniform=True)
    _write_errors(run, "color_correlated", [True, False, False],
                  baseline=[False, True, True], rescues=[0, 1, 1])
    custom_figure, custom_axes = plt.subplots(figsize=(5, 3))
    old_bounds = custom_axes.get_position().bounds
    figure, ax, table = run.plot_improvement_ratio(
        physical_error_rate=.01, filter={"decoder_type": "color_correlated"}, ax=custom_axes)
    assert figure is custom_figure and ax is custom_axes
    assert tuple(figure.get_size_inches()) == (5, 3)
    assert ax.get_position().bounds == old_bounds
    for row in table.itertuples():
        assert row.improvement_ratio == pytest.approx(
            (1 - (1 / 3) ** (1 / row.rounds)) / (1 - (2 / 3) ** (1 / row.rounds)))
    legends = run.plot_legends(table)
    legends["distance"][0].set_size_inches(8, 6)
    assert tuple(figure.get_size_inches()) == (5, 3)
    for fig in [figure, *(pair[0] for pair in legends.values())]:
        plt.close(fig)
