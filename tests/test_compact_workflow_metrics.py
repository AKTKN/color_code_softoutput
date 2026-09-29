"""Same-shot worker and persisted output equivalence with legacy full output."""

from dataclasses import replace

import numpy as np
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.simulation import worker
from color_code_softoutput.simulation.task import ResolvedPoint, metric_names
from color_code_softoutput.simulation.planner import point_directory_name
from color_code_softoutput.simulation.workflow_storage import PointStorage


def point(mode, soft, circuit, identity="compact"):
    opts = {"temp_bdry_type": "Z", "color_correlated_weight_basis": "original_dem"}
    if mode == "correlated":
        opts.update(enable_colorcorrelated_decoding=True, color_correlated_b=2)
    elif mode == "relift":
        opts.update(enable_cross_color_relifting=True, remove_non_edge_like_errors=False)
    elif mode in ("original_dem", "native"):
        opts.update(enable_prior_perturbation=True, stage1_perturbation=mode == "native",
                    perturbation_ensemble_size=3, perturbation_alpha=.25, perturbation_seed=941)
    if soft == "comparative":
        opts["comparative_decoding"] = True
    decode_opts = {"compute_swim_distance": True} if soft == "swim" else {}
    return ResolvedPoint(identity, mode, 3, .003 if circuit else .1,
                         "uniform" if circuit else "bitflip", 3 if circuit else 1,
                         "tri", "tri_optimal", 12, (), tuple(sorted(opts.items())),
                         tuple(sorted(decode_opts.items())))


@pytest.mark.parametrize("mode", ["ordinary", "correlated", "relift", "original_dem", "native"])
@pytest.mark.parametrize("soft", ["none", "comparative", "swim"])
@pytest.mark.parametrize("circuit", [False, True])
def test_worker_and_every_saved_column_match_full_output(tmp_path, mode, soft, circuit):
    compact = point(mode, soft, circuit)
    legacy = replace(compact, decode_options=tuple(sorted(dict(compact.decode_options,
                                                             full_output=True).items())))
    results = []
    try:
        for configured in (legacy, compact):
            worker._CODE_CACHE.clear()
            task = worker.WorkerInput(configured.point_id, 0, 0, 12, 372, configured)
            results.append(worker.run_chunk(task))
        assert set(results[0].metrics) == set(results[1].metrics) == set(metric_names(compact))
        for name in results[0].metrics:
            old, new = (result.metrics[name] for result in results)
            assert old.shape == new.shape == (12,)
            assert old.dtype == new.dtype
            np.testing.assert_array_equal(old, new, err_msg=f"{mode}/{soft}/{name}")
        stores = []
        for index, (configured, result) in enumerate(zip((legacy, compact), results)):
            directory = tmp_path / str(index) / point_directory_name(configured)
            store = PointStorage(configured, directory, buffer_shots=5)
            store.accept(result)
            store.finalize()
            stores.append(directory)
        assert {path.name for path in stores[0].glob('*.parquet')} == {
            path.name for path in stores[1].glob('*.parquet')}
        for path in stores[0].glob('*.parquet'):
            old, new = pq.read_table(path), pq.read_table(stores[1] / path.name)
            assert old.schema == new.schema
            assert old.equals(new)
    finally:
        worker._CODE_CACHE.clear()


@pytest.mark.parametrize("mode", ["correlated", "relift", "native"])
def test_default_worker_never_requests_full_candidate_exports(monkeypatch, mode):
    p = point(mode, "none", False)
    calls = []
    from color_code_stim import ColorCode
    original = ColorCode.decode

    def decode(self, detectors, **kwargs):
        assert kwargs.get("full_output", False) is False
        assert kwargs.get("return_candidate_data", False) is False
        result = original(self, detectors, **kwargs)
        calls.append(kwargs)
        if "metrics" in kwargs:
            assert set(result[1]) == set(metric_names(p))
            assert all(value.shape == (len(detectors),) for value in result[1].values())
        return result

    monkeypatch.setattr(ColorCode, "decode", decode)
    try:
        worker._CODE_CACHE.clear()
        worker.run_chunk(worker.WorkerInput(p.point_id, 0, 0, 12, 372, p))
        assert sum("metrics" in kwargs for kwargs in calls) == 1
    finally:
        worker._CODE_CACHE.clear()


@pytest.mark.parametrize("comparative", [False, True])
def test_superdense_saved_run_configuration_preserves_metrics(comparative):
    compact = point('correlated', 'comparative' if comparative else 'none', True)
    compact = replace(compact, cnot_schedule='superdense_default', physical_error_rate=.001,
                      color_code_options=(("superdense_circuit", True),))
    outputs = []
    try:
        for full in (True, False):
            worker._CODE_CACHE.clear()
            configured = replace(compact, decode_options=(("full_output", full),))
            outputs.append(worker.run_chunk(worker.WorkerInput(configured.point_id, 0, 0, 12, 372, configured)))
        for name in outputs[0].metrics:
            np.testing.assert_array_equal(outputs[0].metrics[name], outputs[1].metrics[name])
    finally:
        worker._CODE_CACHE.clear()


def test_cached_decoder_can_add_swim_without_reconstructing_hard_graphs():
    plain = point('native', 'none', True)
    scored = replace(plain, decode_options=(("compute_swim_distance", True),))
    try:
        worker._CODE_CACHE.clear()
        first = worker.run_chunk(worker.WorkerInput(plain.point_id, 0, 0, 12, 372, plain))
        pair = worker._codes(plain)
        assert pair.circuit_swim is None
        output = worker.run_chunk(worker.WorkerInput(scored.point_id, 0, 0, 12, 372, scored))
        assert worker._codes(scored) is pair
        assert pair.circuit_swim is not None
        np.testing.assert_array_equal(output.metrics['logical_error'], first.metrics['logical_error'])
        assert output.metrics['swim_distance'].shape == (12,)
        legacy = replace(scored, decode_options=(("compute_swim_distance", True), ("full_output", True)))
        worker._CODE_CACHE.clear()
        reference = worker.run_chunk(worker.WorkerInput(legacy.point_id, 0, 0, 12, 372, legacy))
        for name in reference.metrics:
            np.testing.assert_array_equal(reference.metrics[name], output.metrics[name])
    finally:
        worker._CODE_CACHE.clear()
