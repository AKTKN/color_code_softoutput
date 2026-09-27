"""Independent pairing, physical witnesses, storage/replay and analysis checks."""

from dataclasses import replace
import sys
import zipfile

import numpy as np
import pandas as pd
import pytest

from color_code_softoutput.experiments.monotone_y_test import (
    MonotoneYTestConfig,
    require_monotone_y,
    sample_batch,
    run_experiment,
    validate_shots,
    METRIC_VERSION,
    _models,
)
from color_code_softoutput.simulation.config import batch_tasks
from color_code_softoutput.analysis.monotone_y import (
    MonotoneYDataset,
    METRICS,
    audit_run,
    matched_retention,
    compare_postselection,
)
from color_code_softoutput.analysis.figure_style import RevtexFigureStyle
from color_code_softoutput.analysis.swim_distribution import (
    SwimDistanceDistributionPlotter,
)
from color_code_softoutput.analysis.conditional_ler import ConditionalLERAnalyzer
from color_code_softoutput.analysis.postselection import (
    PostSelectionAnalyzer,
    postselection_curve,
)


@pytest.fixture
def config(tmp_path):
    return MonotoneYTestConfig(
        distances=(3, 5),
        near_threshold_ps=(0.088,),
        subthreshold_ps=(0.04,),
        shots_per_point=33,
        batch_size=17,
        num_workers=1,
        output_root=tmp_path,
        verbose=False,
    )


def test_loader_preserves_installed_decoder_and_path_gap():
    import color_code_stim
    from color_code_softoutput.experiments.path_gap_test import require_path_gap

    before = (
        color_code_stim.__file__,
        tuple(color_code_stim.__path__),
        tuple(sys.path),
        color_code_stim.ColorCode,
    )
    adapter = require_monotone_y()
    path_adapter = require_path_gap()
    assert adapter.__module__.startswith("_color_code_softoutput_monotone_y.")
    assert before == (
        color_code_stim.__file__,
        tuple(color_code_stim.__path__),
        tuple(sys.path),
        color_code_stim.ColorCode,
    )
    code, _, metric, _ = _models(3, 0.04)
    detectors, _ = code.sample(8, seed=31)
    pred, extra = code.decode(detectors, full_output=True)
    swim_pred, swim = code.decode(
        detectors, full_output=True, compute_swim_distance=True
    )
    np.testing.assert_array_equal(pred, swim_pred)
    np.testing.assert_array_equal(
        metric.evaluate_decode_output(extra).signed_gap,
        metric.evaluate_decode_output(swim).signed_gap,
    )
    assert np.isfinite(path_adapter(code).evaluate(extra).phi).all()
    assert np.isfinite(swim["selected_swim_distance"]).all()


def test_samples_match_direct_physical_witnesses_and_hard_outputs(config):
    task = next(batch_tasks(replace(config, distances=(5,)), "physical-check"))
    frame = sample_batch(task)
    pd.testing.assert_frame_equal(frame, sample_batch(task), check_exact=True)
    ordinary, comparative, metric, comparative_metric = _models(
        task.distance, task.physical_error_rate
    )
    detectors, actual = ordinary.sample(task.shots, seed=task.seed)
    np.testing.assert_array_equal(
        frame.actual_observable, np.asarray(actual).reshape(-1)
    )
    for name, code, adapter, inputs in (
        ("ordinary", ordinary, metric, detectors),
        (
            "comparative",
            comparative,
            comparative_metric,
            np.column_stack((detectors, np.zeros(task.shots, bool))),
        ),
    ):
        prediction, extra = code.decode(inputs, full_output=True)
        physical = adapter.to_physical(extra)
        result = adapter.evaluator.evaluate_batch(physical, return_witness=True)
        g = adapter.geometry
        unit = np.log1p(-task.physical_error_rate) - np.log(task.physical_error_rate)
        np.testing.assert_array_equal(
            frame[f"{name}_prediction"], np.asarray(prediction).reshape(-1)
        )
        np.testing.assert_array_equal(
            frame[f"{name}_selected_color"], np.array(list("rgb"))[extra["best_colors"]]
        )
        np.testing.assert_array_equal(
            frame[f"{name}_solution_weight"], extra["weights"]
        )
        np.testing.assert_array_equal(frame[f"{name}_root_id"], result.root_id)
        np.testing.assert_array_equal(frame[f"{name}_template_id"], result.template_id)
        np.testing.assert_array_equal(
            frame[f"{name}_monotone_y_gap"], result.signed_gap
        )
        for i, witness in enumerate(result.witness):
            support = np.zeros(len(g.qubit_ids), dtype=bool)
            support[list(witness)] = True
            assert not np.any((g.H_Z @ support.astype(int)) % 2)
            assert int(g.logical_z @ support.astype(int)) % 2 == 1
            direct = unit * (
                np.count_nonzero(physical[i] ^ support) - np.count_nonzero(physical[i])
            )
            assert frame[f"{name}_monotone_y_gap"].iloc[i] == pytest.approx(direct)
        if name == "comparative":
            np.testing.assert_array_equal(frame.forced_gap, extra["logical_gaps"])


def test_validation_preserves_negative_scores_and_rejects_corruption(config):
    task = next(batch_tasks(config, "signed"))
    frame = sample_batch(task)
    _, _, adapter, _ = _models(task.distance, task.physical_error_rate)
    # A full physical support is a valid correction; its returned minimum is negative.
    # This tests storage validation independently of the sampled decoder's minimizer.
    negative = adapter.evaluator.evaluate(np.ones(len(adapter.qubit_ids), dtype=bool))
    assert negative.signed_gap < 0
    signed = frame.copy()
    for name in ("ordinary", "comparative"):
        signed[f"{name}_monotone_y_gap"] = negative.signed_gap
        signed[f"{name}_correction_weight"] = negative.correction_weight
        signed[f"{name}_root_id"] = negative.root_id
        signed[f"{name}_template_id"] = negative.template_id
    validate_shots(signed)
    assert (signed.ordinary_monotone_y_gap < 0).all()
    for key, value, message in (
        ("metric_version", "unknown", "version"),
        ("ordinary_monotone_y_gap", np.nan, "nonnull"),
        ("ordinary_monotone_y_gap", -1e6, "bounds"),
        (
            "comparative_logical_error",
            not frame.comparative_logical_error.iloc[0],
            "failure",
        ),
        ("ordinary_root_id", 1000, "root"),
        ("ordinary_template_id", -1, "integer"),
    ):
        bad = frame.copy()
        bad.loc[0, key] = value
        with pytest.raises(ValueError, match=message):
            validate_shots(bad)
    curve = postselection_curve([-4.0, -4.0, 0.0, 2.0], [True, False, True, False])
    assert curve.retained_shots.tolist() == [4, 2, 1]


@pytest.fixture
def dataset(config):
    return MonotoneYDataset(run_experiment(config))


def test_serial_parallel_replay_provenance(config, dataset):
    parallel = MonotoneYDataset(run_experiment(replace(config, num_workers=2)))
    for data in (dataset, parallel):
        audit = audit_run(data)
        assert audit["shots"] == 132 and audit["batches"] == 8
        assert audit["replayed_batches"] == 4 and audit["exact_source_match"]
        assert data.metadata["metric_version"] == METRIC_VERSION
    columns = [c for c in dataset.read() if c != "experiment_id"]

    def ordered(data):
        return (
            data.read(columns)
            .sort_values(["config_id", "shot_index"])
            .reset_index(drop=True)
        )

    pd.testing.assert_frame_equal(ordered(dataset), ordered(parallel), check_exact=True)
    import color_code_stim

    assert (
        dataset.metadata["imported_package_paths"]["color_code_stim"]
        == color_code_stim.__file__
    )
    assert (
        "color-code-stim-monotone-y"
        in dataset.metadata["imported_package_paths"]["monotone_y_metric"]
    )
    with zipfile.ZipFile(dataset.run_directory / "source_snapshot.zip") as snapshot:
        assert any(n.endswith("metrics/monotone_y_gap.py") for n in snapshot.namelist())
        assert any(
            n.endswith("experiments/monotone_y_test.py") for n in snapshot.namelist()
        )
    with pytest.raises(ValueError, match="own decoder"):
        dataset.metric_rows(METRICS[0], failure_column="comparative_logical_error")
    with pytest.raises(ValueError, match="own decoder"):
        dataset.metric_rows("ordinary_path_gap")


def test_analysis_matches_raw_counts_and_tie_policies(dataset):
    import matplotlib.pyplot as plt

    selection = dict(distance=[3, 5], physical_error_rate=0.04)
    matched = matched_retention(dataset, **selection)
    assert (
        matched.groupby(["distance", "target_retained"])
        .retained_shots.nunique()
        .eq(1)
        .all()
    )
    comparison = compare_postselection(
        dataset, **selection, abort_rates=(0.0, 0.1, 0.5)
    )
    assert (
        "Monotone-Y" in comparison["report"] and "path-gap" not in comparison["report"]
    )
    counts = comparison["counts"]
    for row in counts.itertuples():
        raw = dataset.metric_rows(
            row.metric,
            distance=row.distance,
            physical_error_rate=row.physical_error_rate,
        )
        if row.policy == "matched_abort":
            retained = raw.sort_values(row.metric, ascending=False, kind="stable").iloc[
                : row.retained_shots
            ]
        else:
            retained = raw[raw[row.metric] >= row.threshold]
        assert len(retained) == row.retained_shots
        assert retained[row.failure_column].sum() == row.retained_failures
    style = RevtexFigureStyle(test_mode=True)
    for metric in METRICS[:2]:
        figure, distribution = SwimDistanceDistributionPlotter(style).plot(
            dataset,
            **selection,
            metric=metric,
            include_forced_gap=True,
            normalize_frequency=True,
        )
        plt.close(figure)
        assert distribution.groupby("metric")["count"].sum().eq(66).all()
        figure, rates, fits = ConditionalLERAnalyzer(style).plot(
            dataset, **selection, metric=metric
        )
        plt.close(figure)
        assert rates.shots.sum() == 66
    with pytest.raises(ValueError, match="already signed"):
        SwimDistanceDistributionPlotter(style).plot(
            dataset, **selection, metric=METRICS[0], signed_logical_errors=True
        )
    figure, curves = PostSelectionAnalyzer(style).plot(
        dataset, **selection, metrics=METRICS
    )
    plt.close(figure)
    assert set(curves.metric) == set(METRICS)
    assert (
        curves.loc[curves.metric == METRICS[0], "failure_column"]
        .eq("ordinary_logical_error")
        .all()
    )
    assert (
        curves.loc[curves.metric != METRICS[0], "failure_column"]
        .eq("comparative_logical_error")
        .all()
    )


def test_audit_detects_changed_score(dataset):
    path = dataset.shards[0]
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pq.read_schema(path)
    frame = pd.read_parquet(path)
    frame.loc[0, "ordinary_monotone_y_gap"] -= 0.01  # valid bounds, incorrect minimum
    pq.write_table(
        pa.Table.from_pandas(frame, schema=schema, preserve_index=False), path
    )
    with pytest.raises(AssertionError):
        audit_run(dataset)


def test_subthreshold_only_reference_grid_can_be_analyzed(config):
    from color_code_softoutput.analysis.prior_work import LeeFig3ReproductionAnalyzer

    dataset = MonotoneYDataset(
        run_experiment(
            replace(config, near_threshold_ps=(), subthreshold_ps=(0.04, 0.05))
        )
    )
    report = LeeFig3ReproductionAnalyzer(RevtexFigureStyle(test_mode=True)).analyze(
        dataset
    )
    assert report["crossing"]["status"] == "insufficient_curves"
    assert report["fits"].fit_status.eq("insufficient_nonzero_points").all()
