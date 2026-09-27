"""Small end-to-end checks for the canonical YAML runner."""

from datetime import datetime
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.runner import run_experiment


def settings(tmp_path, *, noise="bitflip", workers=1, verbose=False):
    return {
        "simulation": {"output_root": str(tmp_path), "shots": 5, "workers": workers,
                       "master_seed": 42, "buffer_shots": 2, "verbose": verbose},
        "chunking": {"calibration_shots": 2, "target_chunk_seconds": .1,
                     "min_chunk_shots": 1, "max_chunk_shots": 2,
                     "throughput_ema_alpha": .5},
        "sweep": {"distance": 3, "physical_error_rate": .001, "noise_model": noise,
                  "rounds": "distance", "circuit_type": "tri", "cnot_schedule": "tri_optimal"},
        "color_code_options": {"temp_bdry_type": "Z"},
        "decoders": [{"type": "concat_mwpm"},
                     {"type": "color_correlated", "options": {"enable_colorcorrelated_decoding": True}}],
    }


@pytest.mark.parametrize("noise,workers,verbose", [
    ("bitflip", 1, False), ("depol", 2, True), ("uniform", 2, False)])
def test_runner_end_to_end(tmp_path, noise, workers, verbose):
    raw = settings(tmp_path, noise=noise, workers=workers, verbose=verbose)
    config = parse_workflow_config(raw)
    messages = []
    root = run_experiment(config, reporter=messages.append)
    assert root.name.endswith(config.hash8)
    assert root.name[:17] == datetime.fromisoformat(
        json.loads((root / "run_log.json").read_text())["simulation_start_time"]
    ).strftime("%y_%m_%d_%H_%M_%S")
    assert len(list(root.glob("*.json"))) == 1
    log = json.loads((root / "run_log.json").read_text())
    assert log["config"]["simulation"]["output_root"] == str(tmp_path)
    assert datetime.fromisoformat(log["simulation_end_time"]).tzinfo is not None
    assert len(list(root.iterdir())) == 3
    for name, expected in (("concat_mwpm", {"logical_error": pa.bool_()}),
                           ("color_correlated", {"logical_error": pa.bool_(),
                             "default_logical_error": pa.bool_(),
                             "better_weight_by_color_correlated_decoding": pa.uint8(),
                             "effect_by_color_correlated_decoding": pa.uint8(),
                             "color_correlated_run": pa.uint8()})):
        point_dir = root / (f"decoder_type={name},circuit_type=tri,d=3,r=3,p=0.001,"
                            f"noisemodel={noise},cnot_schedule=tri_optimal")
        assert point_dir.is_dir()
        assert not (point_dir / ".buffer").exists()
        assert {p.name for p in point_dir.iterdir()} == {f"{metric}.parquet" for metric in expected}
        for metric, dtype in expected.items():
            table = pq.read_table(point_dir / f"{metric}.parquet")
            assert table.schema == pa.schema([pa.field("shot_index", pa.int64(), nullable=False),
                                               pa.field(metric, dtype, nullable=False)])
            assert table.num_rows == 5
            assert table.column("shot_index").to_pylist() == list(range(5))
            if metric == "color_correlated_run":
                assert set(table.column(metric).to_pylist()) <= {0, 1, 2}
    if verbose:
        assert any("ETA: estimating..." in line for line in messages)
        assert any("ETA: ~" in line for line in messages)
        assert any("run directory:" in line and "configured workers:" in line for line in messages)
    else:
        assert messages == []


def test_preflight_rejects_before_creating_run(tmp_path):
    raw = settings(tmp_path)
    raw["sweep"]["physical_error_rate"] = [.001, .001]
    with pytest.raises(ValueError, match="collision"):
        run_experiment(parse_workflow_config(raw))
    assert list(tmp_path.iterdir()) == []

    raw = settings(tmp_path)
    raw["sweep"]["cnot_schedule"] = "unknown_schedule"
    with pytest.raises((ValueError, KeyError, NotImplementedError)):
        run_experiment(parse_workflow_config(raw))
    assert list(tmp_path.iterdir()) == []


def test_original_dem_weight_basis_option(tmp_path):
    raw = settings(tmp_path)
    raw["decoders"][0]["options"] = {"color_correlated_weight_basis": "original_dem"}
    raw["decoders"][1]["options"]["color_correlated_weight_basis"] = "original_dem"
    config = parse_workflow_config(raw)
    assert dict(config.decoders[0].options)["color_correlated_weight_basis"] == "original_dem"
    assert dict(config.decoders[1].options)["color_correlated_weight_basis"] == "original_dem"
    raw["decoders"][1]["options"]["color_correlated_weight_basis"] = "unknown"
    with pytest.raises(ValueError, match="color_correlated_weight_basis"):
        parse_workflow_config(raw)
    raw["decoders"][1]["options"]["color_correlated_weight_basis"] = "stage2"
    with pytest.raises(ValueError, match="requires original_dem"):
        parse_workflow_config(raw)
    raw["decoders"][1]["options"]["color_correlated_weight_basis"] = "original_dem"
    raw["decoders"][1]["options"]["color_correlated_b"] = 2.0
    assert dict(parse_workflow_config(raw).decoders[1].options)["color_correlated_b"] == 2.0
    raw["decoders"][1]["options"]["color_correlated_b"] = 0
    with pytest.raises(ValueError, match="color_correlated_b"):
        parse_workflow_config(raw)


def test_ordinary_original_dem_runner(tmp_path):
    raw = settings(tmp_path)
    raw["simulation"]["shots"] = 2
    raw["decoders"] = [{"type": "concat_mwpm", "options": {
        "color_correlated_weight_basis": "original_dem"},
        "decode_options": {"colors": "all"}}]
    root = run_experiment(parse_workflow_config(raw), reporter=lambda _: None)
    point_dir = next(root.glob("decoder_type=concat_mwpm,*"))
    assert pq.read_table(point_dir / "logical_error.parquet").num_rows == 2


def test_two_ordinary_weight_bases_have_distinct_points(tmp_path):
    raw = settings(tmp_path)
    raw["simulation"]["shots"] = 2
    raw["decoders"] = [
        {"type": "concat_mwpm", "options": {
            "color_correlated_weight_basis": "original_dem"},
            "decode_options": {"colors": "all"}},
        {"type": "concat_mwpm_stage2_base", "options": {
            "color_correlated_weight_basis": "stage2"},
            "decode_options": {"colors": "all"}},
    ]
    root = run_experiment(parse_workflow_config(raw), reporter=lambda _: None)
    assert len(list(root.glob("decoder_type=concat_mwpm,*"))) == 1
    assert len(list(root.glob("decoder_type=concat_mwpm_stage2_base,*"))) == 1
    for path in root.glob("decoder_type=concat_mwpm*,*"):
        assert pq.read_table(path / "logical_error.parquet").num_rows == 2

    raw["decoders"][1]["options"]["color_correlated_weight_basis"] = "original_dem"
    with pytest.raises(ValueError, match="requires color_correlated_weight_basis: stage2"):
        parse_workflow_config(raw)


def test_relifting_option_validation(tmp_path):
    raw = settings(tmp_path)
    raw["decoders"] = [{"type": "relifting", "options": {
        "enable_cross_color_relifting": True, "remove_non_edge_like_errors": False}}]
    assert dict(parse_workflow_config(raw).decoders[0].options)["enable_cross_color_relifting"]
    raw["decoders"][0]["options"]["enable_colorcorrelated_decoding"] = True
    with pytest.raises(ValueError, match="mutually exclusive"):
        parse_workflow_config(raw)
    del raw["decoders"][0]["options"]["enable_colorcorrelated_decoding"]
    raw["decoders"][0]["options"]["remove_non_edge_like_errors"] = True
    with pytest.raises(ValueError, match="remove_non_edge_like_errors"):
        parse_workflow_config(raw)


def test_relifting_runner_writes_run_class_sidecar(tmp_path):
    raw = settings(tmp_path, noise="uniform")
    raw["simulation"]["shots"] = 2
    raw["sweep"]["physical_error_rate"] = .03
    raw["decoders"] = [{"type": "relifting", "options": {
        "enable_cross_color_relifting": True, "remove_non_edge_like_errors": False}}]
    root = run_experiment(parse_workflow_config(raw), reporter=lambda _: None)
    sidecars = list(root.glob("*/relift_run.parquet"))
    assert len(sidecars) == 1
    table = pq.read_table(sidecars[0])
    assert table.column_names == ["shot_index", "relift_run"]
    assert table.column("shot_index").to_pylist() == [0, 1]
    assert set(table.column("relift_run").to_pylist()) <= {0, 1, 2}
    point_dir = sidecars[0].parent
    assert {p.stem for p in point_dir.glob("*.parquet")} == {
        "logical_error", "default_logical_error",
        "better_weight_by_color_correlated_decoding",
        "effect_by_color_correlated_decoding", "relift_run"}


def test_perturbation_runner_writes_paired_metrics(tmp_path):
    raw = settings(tmp_path, noise="uniform")
    raw["simulation"]["shots"] = 2
    raw["decoders"] = [{"type": "perturbation", "options": {
        "enable_prior_perturbation": True, "perturbation_ensemble_size": 2,
        "perturbation_alpha": .25, "perturbation_seed": 11}}]
    root = run_experiment(parse_workflow_config(raw), reporter=lambda _: None)
    point_dir = next(root.glob("decoder_type=perturbation,*"))
    assert {p.stem for p in point_dir.glob("*.parquet")} == {
        "logical_error", "default_logical_error",
        "better_weight_by_color_correlated_decoding",
        "effect_by_color_correlated_decoding"}
    default = pq.read_table(point_dir / "default_logical_error.parquet").column(
        "default_logical_error").to_numpy()
    logical = pq.read_table(point_dir / "logical_error.parquet").column(
        "logical_error").to_numpy()
    effect = pq.read_table(point_dir / "effect_by_color_correlated_decoding.parquet").column(
        "effect_by_color_correlated_decoding").to_numpy()
    assert (effect == (default & ~logical).astype("uint8")).all()


def test_failure_still_closes_single_log(tmp_path, monkeypatch):
    config = parse_workflow_config(settings(tmp_path))

    def fail(*args, **kwargs):
        raise RuntimeError("test failure")

    monkeypatch.setattr("color_code_softoutput.simulation.runner.run_scheduler", fail)
    with pytest.raises(RuntimeError, match="test failure"):
        run_experiment(config)
    roots = list(tmp_path.iterdir())
    assert len(roots) == 1
    assert len(list(roots[0].glob("*.json"))) == 1
    log = json.loads((roots[0] / "run_log.json").read_text())
    assert log["simulation_end_time"] is not None
