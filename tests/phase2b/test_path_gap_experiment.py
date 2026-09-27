"""Independent experiment accounting and metric/failure association checks."""
from dataclasses import replace
import json

import numpy as np
import pandas as pd
import pytest

from color_code_softoutput.experiments.path_gap_test import (
    PathGapTestConfig, sample_batch, run_experiment, validate_shots, require_path_gap,
    METRIC_VERSION, LEGACY_METRIC_VERSION,
)
from color_code_softoutput.simulation.config import Phase2ATestConfig, batch_tasks
from color_code_softoutput.analysis.path_gap import PathGapDataset, audit_run, matched_retention
from color_code_softoutput.analysis.postselection import postselection_curve, PostSelectionAnalyzer
from color_code_softoutput.analysis.figure_style import RevtexFigureStyle
from color_code_softoutput.analysis.conditional_ler import ConditionalLERAnalyzer
from color_code_softoutput.analysis.swim_distribution import SwimDistanceDistributionPlotter


def test_notebook_defaults():
    config = PathGapTestConfig()
    assert config.distances == Phase2ATestConfig().distances
    assert config.probabilities == Phase2ATestConfig().probabilities
    assert len(config.distances)*len(config.probabilities)*config.shots_per_point == 6_000_000
    assert (config.batch_size, config.num_workers, config.master_seed) == (2000, 6, 20260912321)


def test_loader_preserves_swim_environment():
    import sys
    import color_code_stim
    from color_code_stim import ColorCode, NoiseModel
    before = (color_code_stim.__file__, tuple(color_code_stim.__path__), tuple(sys.path))
    metric_class = require_path_gap()
    assert before == (color_code_stim.__file__, tuple(color_code_stim.__path__), tuple(sys.path))
    assert color_code_stim.ColorCode is ColorCode
    code = ColorCode(d=3, rounds=1, circuit_type="tri", cnot_schedule="tri_optimal",
                     noise_model=NoiseModel(bitflip=.04))
    detectors, _ = code.sample(32, seed=123)
    prediction, extra = code.decode(detectors, full_output=True)
    phi = metric_class(code).evaluate(extra).phi
    import inspect
    if "compute_swim_distance" in inspect.signature(code.decode).parameters:
        swim_prediction, swim = code.decode(detectors, full_output=True, compute_swim_distance=True)
        np.testing.assert_array_equal(prediction, swim_prediction)
        np.testing.assert_array_equal(phi, metric_class(code).evaluate(swim).phi)
        assert np.isfinite(swim["selected_swim_distance"]).all()


def test_signed_thresholds_keep_whole_ties():
    curve = postselection_curve([-4., -4., 0., 2.], [True, False, True, False])
    assert curve.threshold.tolist() == [-4., 0., 2.]
    assert curve.retained_shots.tolist() == [4, 2, 1]
    assert curve.retained_failures.tolist() == [2, 1, 0]
    assert curve.high.iloc[-1] > 0


@pytest.fixture
def config(tmp_path):
    require_path_gap()
    return PathGapTestConfig(distances=(3, 5), near_threshold_ps=(.088,),
                             subthreshold_ps=(.04,), shots_per_point=33,
                             batch_size=17, num_workers=1, output_root=tmp_path, verbose=False)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_deterministic_batch_and_validation(config, version):
    task = next(batch_tasks(config, "test"))
    first = sample_batch(task, metric_version=version)
    second = sample_batch(task, metric_version=version)
    pd.testing.assert_frame_equal(first, second, check_exact=True)
    corrupt = first.copy()
    corrupt.loc[0, "ordinary_phi_r"] += 1
    with pytest.raises(ValueError, match="subtraction"):
        validate_shots(corrupt)
    corrupt = first.copy()
    corrupt.loc[0, "comparative_logical_error"] = not corrupt.loc[0, "comparative_logical_error"]
    with pytest.raises(ValueError, match="failure"):
        validate_shots(corrupt)
    # Make a valid signed-score fixture independent of any decoder's sample.
    signed = first.copy()
    for decoder in ("ordinary", "comparative"):
        weight = signed[f"{decoder}_correction_weight"] + 100
        signed[f"{decoder}_correction_weight"] = weight
        phi = signed[[f"{decoder}_distance_{c}" for c in "rgb"]].to_numpy()-weight.to_numpy()[:, None]
        for i, c in enumerate("rgb"):
            signed[f"{decoder}_overlap_{c}"] = weight
            signed[f"{decoder}_phi_{c}"] = phi[:, i]
        signed[f"{decoder}_path_gap"] = phi.min(axis=1)
        signed[f"{decoder}_minimizing_color"] = np.array(list("rgb"))[phi.argmin(axis=1)]
    validate_shots(signed)
    assert (signed.ordinary_path_gap < 0).all()


@pytest.mark.parametrize("version,canonical", [("v1", LEGACY_METRIC_VERSION), ("v2", METRIC_VERSION)])
def test_serial_parallel_audit(config, version, canonical):
    serial = PathGapDataset(run_experiment(config, metric_version=version))
    parallel = PathGapDataset(run_experiment(replace(config, num_workers=2), metric_version=version))
    for dataset in (serial, parallel):
        report = audit_run(dataset)
        assert report["shots"] == 132 and report["batches"] == 8
        assert report["replayed_batches"] == 4 and report["exact_source_match"]
    columns = [c for c in serial.read().columns if c != "experiment_id"]
    def ordered(dataset):
        return dataset.read(columns).sort_values(["config_id", "shot_index"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(ordered(serial), ordered(parallel), check_exact=True)
    metadata = json.loads((serial.run_directory / "metadata.json").read_text())
    import color_code_stim, pymatching
    assert "color-code-stim-path-gap" in metadata["imported_package_paths"]["path_gap_metric"]
    assert metadata["imported_package_paths"]["color_code_stim"] == color_code_stim.__file__
    assert metadata["repositories"]["PyMatching"]["version"] == pymatching.__version__
    assert metadata["metric_version"] == canonical
    assert serial.read().metric_version.eq(canonical).all()
    assert metadata["shot_schema_version"] == 2
    assert ("W(E)]" if version == "v1" else "W(E intersect L_c)]") in metadata["metric_description"]
    with pytest.raises(ValueError, match="own decoder"):
        serial.metric_rows("ordinary_path_gap", failure_column="comparative_logical_error")


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_analysis_and_matched_retention(config, version):
    import matplotlib.pyplot as plt
    dataset = PathGapDataset(run_experiment(config, metric_version=version))
    selection = dict(distance=[3, 5], physical_error_rate=.04)
    matched = matched_retention(dataset, **selection)
    assert matched.groupby(["distance", "target_retained"]).retained_shots.nunique().eq(1).all()
    for row in matched.itertuples():
        raw = dataset.metric_rows(row.metric, distance=row.distance, physical_error_rate=row.physical_error_rate)
        ranked = raw.sort_values(row.metric, ascending=False, kind="stable").iloc[:row.retained_shots]
        assert row.retained_failures == ranked[row.failure_column].sum()
    style = RevtexFigureStyle(test_mode=True)
    for metric in ("ordinary_path_gap", "comparative_path_gap"):
        figure, counts = SwimDistanceDistributionPlotter(style).plot(dataset, **selection, metric=metric)
        plt.close(figure)
        assert counts["count"].sum() == 66
        figure, rates, fits = ConditionalLERAnalyzer(style).plot(dataset, **selection, metric=metric)
        plt.close(figure)
        assert rates.shots.sum() == 66
    with pytest.raises(ValueError, match="already signed"):
        SwimDistanceDistributionPlotter(style).plot(dataset, **selection, metric="ordinary_path_gap", signed_logical_errors=True)
    figure, curves = PostSelectionAnalyzer(style).plot(dataset, **selection,
        metrics=("ordinary_path_gap", "comparative_path_gap", "forced_gap"))
    plt.close(figure)
    assert set(curves.metric) == {"ordinary_path_gap", "comparative_path_gap", "forced_gap"}
    assert curves.loc[curves.metric == "comparative_path_gap", "failure_column"].eq("comparative_logical_error").all()


def test_legacy_run_keeps_its_schema_and_definition(config):
    from color_code_softoutput.experiments.path_gap_test import LEGACY_SHOT_SCHEMA
    import pyarrow as pa
    import pyarrow.parquet as pq

    directory = run_experiment(config)
    metadata = json.loads((directory / "metadata.json").read_text())
    metadata.pop("metric_version")
    metadata.pop("shot_schema_version")
    (directory / "metadata.json").write_text(json.dumps(metadata))
    for path in (directory / "shots").glob("*.parquet"):
        schema_metadata = pq.read_schema(path).metadata
        frame = pd.read_parquet(path)[LEGACY_SHOT_SCHEMA.names]
        for decoder in ("ordinary", "comparative"):
            phi = frame[[f"{decoder}_distance_{c}" for c in "rgb"]].to_numpy() - frame[f"{decoder}_correction_weight"].to_numpy()[:, None]
            for c, color in enumerate("rgb"):
                frame[f"{decoder}_phi_{color}"] = phi[:, c]
            frame[f"{decoder}_path_gap"] = phi.min(axis=1)
            frame[f"{decoder}_minimizing_color"] = np.array(list("rgb"))[phi.argmin(axis=1)]
        validate_shots(frame)
        table = pa.Table.from_pandas(frame, schema=LEGACY_SHOT_SCHEMA, preserve_index=False)
        pq.write_table(table.replace_schema_metadata(schema_metadata), path)
    dataset = PathGapDataset(directory)
    assert dataset.metric_version == "global_subtraction_v1"
    assert audit_run(dataset, replay=False)["passed"]
    with pytest.raises(ValueError, match="archived v1 source"):
        audit_run(dataset, replay=True)


def test_versions_use_same_shots_and_corrections(config):
    task = next(batch_tasks(replace(config, distances=(5,), subthreshold_ps=(),
                                   shots_per_point=256, batch_size=256), "paired-versions"))
    v1 = sample_batch(task, metric_version="v1")
    v2 = sample_batch(task, metric_version="v2")
    changed = {"metric_version"}
    for decoder in ("ordinary", "comparative"):
        changed.update({f"{decoder}_path_gap", f"{decoder}_minimizing_color"})
        changed.update(f"{decoder}_phi_{c}" for c in "rgb")
        expected = v1[[f"{decoder}_distance_{c}" for c in "rgb"]].to_numpy() - v1[f"{decoder}_correction_weight"].to_numpy()[:, None]
        np.testing.assert_array_equal(expected, v1[[f"{decoder}_phi_{c}" for c in "rgb"]])
        np.testing.assert_array_equal(expected.min(axis=1), v1[f"{decoder}_path_gap"])
        np.testing.assert_array_equal(np.array(list("rgb"))[expected.argmin(axis=1)], v1[f"{decoder}_minimizing_color"])
        assert (v1[f"{decoder}_path_gap"] < v2[f"{decoder}_path_gap"] - 1e-12).any()
    columns = [c for c in v1 if c not in changed]
    pd.testing.assert_frame_equal(v1[columns], v2[columns], check_exact=True)
    for frame, version in ((v1, LEGACY_METRIC_VERSION), (v2, METRIC_VERSION)):
        validate_shots(frame, metric_version=version)
        corrupt = frame.copy()
        corrupt.loc[0, "metric_version"] = "unknown"
        with pytest.raises(ValueError, match="version"):
            validate_shots(corrupt)
        corrupt = frame.copy()
        corrupt.loc[0, "metric_version"] = METRIC_VERSION if version == LEGACY_METRIC_VERSION else LEGACY_METRIC_VERSION
        with pytest.raises(ValueError, match="version"):
            validate_shots(corrupt, metric_version=version)
    with pytest.raises(ValueError, match="subtraction"):
        validate_shots(v1.assign(metric_version=METRIC_VERSION))


@pytest.mark.parametrize("version", ["v3", "", None])
def test_unknown_version_fails_before_sampling(config, version):
    with pytest.raises(ValueError, match="metric version"):
        run_experiment(config, metric_version=version)
    with pytest.raises(ValueError, match="metric version"):
        sample_batch(next(batch_tasks(config, "bad")), metric_version=version)
    assert not list(config.output_root.iterdir())
