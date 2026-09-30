"""Independent saved BP fixtures; no decoder execution or feature imports."""

import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.analysis.color_correlated import ColorCorrelatedRun
from color_code_softoutput.analysis.color_correlated_comparison import ColorCorrelatedComparison
from color_code_softoutput.analysis.workflow_soft_output import WorkflowSoftOutputRun
from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.planner import plan_points, point_directory_name


def _write(directory, metric, values, dtype=None, indices=None):
    dtype = dtype or (pa.bool_() if metric in (
        "logical_error", "default_logical_error", "bp_converged") else
        pa.float64() if metric == "swim_distance" else pa.uint8())
    pq.write_table(pa.table({
        "shot_index": pa.array(list(range(6)) if indices is None else indices, type=pa.int64()),
        metric: pa.array(values, type=dtype),
    }), directory / f"{metric}.parquet", row_group_size=2)


def _saved_run(root, *, all_converged=False, mismatched_bp=False):
    root.mkdir(exist_ok=True)
    decoders = []
    for alias, bp, paired in (("MWPM", False, False), ("BP_MWPM", True, False),
                              ("MWPM_perturbation", False, True),
                              ("BP_MWPM_perturbation", True, True)):
        entry = {"decoder_alias": alias, "type": "perturbation" if paired else "concat_mwpm",
                 "decode_options": {"compute_swim_distance": True, "bp_predecoding": bp}}
        if bp:
            entry["decode_options"]["bp_prms"] = {"max_iter": 2 if mismatched_bp and paired else 1}
        if paired:
            entry["options"] = {"enable_prior_perturbation": True,
                                "perturbation_ensemble_size": 2}
        decoders.append(entry)
    raw = {
        "simulation": {"output_root": str(root), "shots": 6, "workers": 1,
                       "master_seed": 7, "buffer_shots": 6, "verbose": False},
        "chunking": {"calibration_shots": 1, "target_chunk_seconds": 1,
                     "min_chunk_shots": 1, "max_chunk_shots": 6,
                     "throughput_ema_alpha": .5},
        "sweep": {"distance": 3, "physical_error_rate": .05, "noise_model": "bitflip",
                  "rounds": 1, "circuit_type": "tri", "cnot_schedule": "tri_optimal"},
        "decoders": decoders,
    }
    (root / "run_log.json").write_text(json.dumps({"config": raw,
        "simulation_start_time": "start", "simulation_end_time": "end"}))
    for point in plan_points(parse_workflow_config(raw)):
        directory = root / point_directory_name(point)
        directory.mkdir()
        bp = dict(point.decode_options)["bp_predecoding"]
        mask = [True] * 6 if all_converged else [True, False, True, False, False, True]
        if bp:
            _write(directory, "bp_converged", mask)
        values = {"logical_error": [False, False, False, True, False, False],
                  "default_logical_error": [True, True, False, True, False, False],
                  "better_weight_by_color_correlated_decoding": [0, 1, 0, 0, 0, 0],
                  "effect_by_color_correlated_decoding": [1, 1, 0, 0, 0, 0],
                  "swim_distance": [10., 1., 20., 2., 3., 30.]}
        for metric, bits in values.items():
            if point.decoder_type != "perturbation" and metric not in ("logical_error", "swim_distance"):
                continue
            _write(directory, metric, [None if bp and mask[i] else bit for i, bit in enumerate(bits)])
    return root


def test_bp_metadata_roundtrip_and_validation(tmp_path):
    root = _saved_run(tmp_path)
    raw = json.loads((root / "run_log.json").read_text())["config"]
    config = parse_workflow_config(raw)
    # Hash serialization intentionally omits machine-specific absolute roots.
    canonical = json.loads(json.dumps(config.semantic_dict()))
    canonical["simulation"]["output_root"] = raw["simulation"]["output_root"]
    assert parse_workflow_config(canonical) == config
    assert config.semantic_dict()["decoders"][1]["decode_options"]["bp_prms"] == {"max_iter": 1}
    raw["decoders"][1]["decode_options"]["bp_predecoding"] = "true"
    with pytest.raises(ValueError, match="must be boolean"):
        parse_workflow_config(raw)
    raw["decoders"][1]["decode_options"]["bp_predecoding"] = True
    raw["decoders"][1]["decode_options"]["bp_prms"] = {"typo": 1}
    with pytest.raises(ValueError, match="Unknown bp_prms"):
        parse_workflow_config(raw)


def test_bp_summary_denominator_and_baselines(tmp_path):
    root = _saved_run(tmp_path)
    run = ColorCorrelatedComparison(root)
    summary = run.summary().set_index("decoder_alias")
    assert summary.loc["MWPM", "statistics_scope"] == "all shots"
    assert summary.loc["BP_MWPM", "statistics_scope"] == "all shots"
    assert summary.loc["BP_MWPM", "shots"] == 6
    assert summary.loc["BP_MWPM", "physical_shots"] == 6
    assert summary.loc["BP_MWPM", "bp_converged_shots"] == 3
    assert summary.loc["BP_MWPM", "logical_error_rate"] == pytest.approx(1 / 6)
    # Baseline selection retains the original physical-condition rule.
    ratios = run.improvement_table(physical_error_rate=.05).set_index("decoder_alias")
    assert ratios.loc["MWPM", "baseline_source_decoder_alias"] == "BP_MWPM_perturbation"
    assert ratios.loc["BP_MWPM", "baseline_source_decoder_alias"] == "BP_MWPM_perturbation"
    assert ratios.loc["MWPM", "baseline_logical_error_rate"] == pytest.approx(2 / 6)
    assert ratios.loc["BP_MWPM", "baseline_logical_error_rate"] == pytest.approx(2 / 6)
    assert ratios.loc["MWPM_perturbation", "baseline_logical_error_rate"] == pytest.approx(3 / 6)
    assert not ratios.loc["BP_MWPM", "baseline_paired"]
    assert ratios.loc["BP_MWPM_perturbation", "baseline_paired"]
    figure, ax, table = run.plot_ler(group_by=("decoder_alias",), baseline_compare=True)
    assert set(table[table.decoder_type == "baseline"].decoder_alias) == {"baseline"}
    assert "nonconverged" not in ax.get_ylabel()
    plt.close(figure)


def test_baseline_selection_does_not_filter_by_bp_settings(tmp_path):
    root = _saved_run(tmp_path, mismatched_bp=True)
    run = ColorCorrelatedRun(root)
    ratio = run.improvement_table(physical_error_rate=.05, filter={"decoder_alias": "BP_MWPM"}).iloc[0]
    assert ratio.baseline_source_decoder_alias == "BP_MWPM_perturbation"
    assert ratio.baseline_logical_error_rate == pytest.approx(2 / 6)


def test_all_converged_keeps_total_shot_denominator(tmp_path):
    root = _saved_run(tmp_path, all_converged=True)
    run = ColorCorrelatedRun(root)
    bp = run.summary({"decoder_alias": "BP_MWPM"}).iloc[0]
    assert bp.shots == 6 and bp.failures == 0
    assert bp.logical_error_rate == bp.ler_low == 0
    assert bp.ler_high > 0
    figure, _, _ = run.plot_ler(filter={"decoder_alias": "BP_MWPM"}, group_by=("decoder_alias",))
    plt.close(figure)
    with pytest.raises(ValueError, match="No scored shots"):
        WorkflowSoftOutputRun(root).plot_distribution(filter={"decoder_alias": "BP_MWPM"})


@pytest.mark.parametrize("corruption", ["indices", "dtype", "null", "metric_mask", "score_mask", "missing"])
def test_corrupted_bp_files_are_rejected(tmp_path, corruption):
    root = _saved_run(tmp_path)
    run = ColorCorrelatedRun(root)
    directory = root / run.select({"decoder_alias": "BP_MWPM"}).iloc[0].point_directory
    mask = [True, False, True, False, False, True]
    if corruption == "indices":
        _write(directory, "bp_converged", mask, indices=[0, 2, 1, 3, 4, 5])
    elif corruption == "dtype":
        _write(directory, "bp_converged", [1, 0, 1, 0, 0, 1], pa.uint8())
    elif corruption == "null":
        _write(directory, "bp_converged", [None, False, True, False, False, True])
    elif corruption == "metric_mask":
        _write(directory, "logical_error", [False, None, None, True, False, None])
    elif corruption == "score_mask":
        _write(directory, "swim_distance", [1., None, None, 2., 3., None])
    else:
        (directory / "bp_converged.parquet").unlink()
    if corruption != "score_mask":
        with pytest.raises((ValueError, FileNotFoundError)):
            run.summary({"decoder_alias": "BP_MWPM"})
    with pytest.raises((ValueError, FileNotFoundError)):
        WorkflowSoftOutputRun(root)._point(run.select({"decoder_alias": "BP_MWPM"}).iloc[0], "swim_distance")


def test_bp_scores_and_postselection_use_only_unskipped_shots(tmp_path):
    root = _saved_run(tmp_path)
    run = WorkflowSoftOutputRun(root)
    row = run.run.select({"decoder_alias": "BP_MWPM"}).iloc[0]
    scores, failures = run._point(row, "swim_distance")
    np.testing.assert_array_equal(scores, [1., 2., 3.])
    np.testing.assert_array_equal(failures, [False, True, False])
    for method in (run.plot_distribution, run.plot_conditional_ler, run.plot_postselection):
        figure, table = method(filter={"decoder_alias": "BP_MWPM"}, group_by=("decoder_alias",))
        assert set(table.statistics_scope) == {"BP-nonconverged shots"}
        plt.close(figure)
    with pytest.raises(ValueError, match="separate BP sampling scopes"):
        run.plot_distribution(group_by=("decoder_type",))


def test_additional_bp_source_retains_counts_and_provenance(tmp_path):
    first, second = _saved_run(tmp_path / "first"), _saved_run(tmp_path / "second")
    run = ColorCorrelatedComparison(first, additional_sources=[{
        "run_directory": str(second), "filter": {"decoder_alias": "BP_MWPM_perturbation"},
        "alias_map": {"BP_MWPM_perturbation": "older_BP"}}])
    summary = run.summary({"decoder_alias": "older_BP"}).iloc[0]
    assert summary.shots == 6 and summary.physical_shots == 6
    assert summary.source_run == str(second.resolve())
    ratio = run.improvement_table(physical_error_rate=.05, filter={"decoder_alias": "older_BP"}).iloc[0]
    assert ratio.baseline_paired and ratio.baseline_source_run == str(second.resolve())


def test_non_bp_nulls_still_rejected_even_with_stray_sidecar(tmp_path):
    root = _saved_run(tmp_path)
    run = WorkflowSoftOutputRun(root)
    row = run.run.select({"decoder_alias": "MWPM"}).iloc[0]
    directory = root / row.point_directory
    _write(directory, "bp_converged", [True, False, False, False, False, False])
    _write(directory, "logical_error", [None, False, False, True, False, False])
    _write(directory, "swim_distance", [None, 1., 2., 3., 4., 5.])
    with pytest.raises(ValueError, match="Null values"):
        run._point(row, "swim_distance")
    with pytest.raises(ValueError, match="null values"):
        run.run.summary({"decoder_alias": "MWPM"})
