"""Tesseract integration checks independent of the optional native extension."""

from types import SimpleNamespace

import numpy as np
import pytest

from color_code_softoutput.simulation import tesseract as adapter, worker
from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.runner import _preflight_point
from color_code_softoutput.simulation.runner import run_experiment
from color_code_softoutput.simulation.planner import plan_points
import pyarrow.parquet as pq


def _config():
    return {
        "simulation": {"output_root": "results", "shots": 3, "workers": 1,
                       "master_seed": 1, "buffer_shots": 3, "verbose": False},
        "chunking": {"calibration_shots": 1, "target_chunk_seconds": 1.0,
                     "min_chunk_shots": 1, "max_chunk_shots": 3,
                     "throughput_ema_alpha": 0.5},
        "sweep": {"distance": 3, "physical_error_rate": .001, "noise_model": "bitflip",
                  "rounds": 1, "circuit_type": "tri", "cnot_schedule": "tri_optimal"},
        "color_code_options": {"temp_bdry_type": "Z"},
        "decoders": [{"type": "tesseract", "options": {"det_beam": 7}}],
    }


def test_config_routes_native_options_and_rejects_other_decoder_controls():
    raw = _config()
    point = plan_points(parse_workflow_config(raw))[0]
    assert point.decoder_type == "tesseract"
    assert dict(point.decoder_options) == {"det_beam": 7}
    raw["decoders"][0]["options"] = {"color_correlated_b": 2}
    with pytest.raises(ValueError, match="Unsupported"):
        parse_workflow_config(raw)
    raw["decoders"][0]["options"] = {}
    raw["decoders"][0]["decode_options"] = {"colors": "all"}
    with pytest.raises(ValueError, match="decode_options"):
        parse_workflow_config(raw)
    raw["decoders"][0].pop("decode_options")
    raw["color_code_options"]["temp_bdry_type"] = "Y"
    with pytest.raises(ValueError, match="XYZ"):
        parse_workflow_config(raw)


def test_worker_uses_original_dem_and_single_shot_predictions(monkeypatch):
    point = plan_points(parse_workflow_config(_config()))[0]
    seen = []
    dem = SimpleNamespace(num_observables=1, num_detectors=2)

    class FakeCode:
        def __init__(self, **options):
            assert "det_beam" not in options
            self.dem_xz = dem
            self.temp_bdry_type = "Z"
            self.circuit = SimpleNamespace(num_detectors=2)

        def sample(self, shots, seed):
            assert shots == 3
            return np.array([[0, 0], [1, 0], [0, 1]], dtype=bool), np.array([0, 0, 1], dtype=bool)

        def decode(self, *_args, **_kwargs):
            raise AssertionError("ColorCode.decode must not be used")

    class FakeDecoder:
        def decode(self, syndrome):
            seen.append(syndrome.copy())
            return np.array([bool(syndrome[0])])

    def compile_fake(actual_dem, options):
        assert actual_dem is dem
        assert dict(options) == {"det_beam": 7}
        return FakeDecoder()

    monkeypatch.setattr(worker, "ColorCode", FakeCode)
    monkeypatch.setattr(adapter, "compile_tesseract", compile_fake)
    worker._CODE_CACHE.clear()
    try:
        _preflight_point(point)
        result = worker.run_chunk(worker.WorkerInput(point.point_id, 0, 0, 3, 5, point))
        assert result.metrics.keys() == {"logical_error"}
        assert result.metrics["logical_error"].tolist() == [False, True, True]
        assert len(seen) == 3
    finally:
        worker._CODE_CACHE.clear()


def test_tesseract_end_to_end_when_installed(tmp_path):
    pytest.importorskip("tesseract_decoder")
    raw = _config()
    raw["simulation"]["output_root"] = str(tmp_path)
    root = run_experiment(parse_workflow_config(raw), reporter=lambda _message: None)
    points = list(root.glob("decoder_type=tesseract,*"))
    assert len(points) == 1
    assert {path.name for path in points[0].iterdir()} == {"logical_error.parquet"}
    table = pq.read_table(points[0] / "logical_error.parquet")
    assert table.column("shot_index").to_pylist() == [0, 1, 2]
    assert len(table.column("logical_error")) == 3
