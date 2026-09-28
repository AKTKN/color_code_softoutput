from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing

import numpy as np
import pyarrow.parquet as pq
import pytest
from color_code_stim import ColorCode

from color_code_softoutput.simulation.config import parse_workflow_config, resolve_native_seeds
from color_code_softoutput.simulation.planner import plan_points
from color_code_softoutput.simulation.runner import run_experiment
from color_code_softoutput.simulation import worker
from test_simulation_runner import settings


def native_config(tmp_path, *, seed=19, shots=12):
    raw = settings(tmp_path)
    raw['simulation']['shots'] = shots
    raw['sweep'].update(rounds=1, physical_error_rate=.05)
    raw['decoders'] = [{'decoder_alias': 'native', 'type': 'perturbation', 'options': {
        'stage1_perturbation': True, 'perturbation_ensemble_size': 4,
        'perturbation_alpha': 1, 'perturbation_seed': seed,
        'enable_prior_perturbation': False, 'use_original_prior_for_stage2': False,
        'color_correlated_weight_basis': 'original_dem'}}]
    return raw


def test_canonical_flags_validation_and_seed_resolution(tmp_path):
    raw = native_config(tmp_path, seed=None)
    raw['color_code_options'].update(enable_prior_perturbation=False, use_original_prior_for_stage2=False)
    for key in ('enable_prior_perturbation', 'use_original_prior_for_stage2'):
        raw['decoders'][0]['options'].pop(key)
    raw['decoders'].append({'decoder_alias': 'ordinary', 'type': 'concat_mwpm'})
    config = parse_workflow_config(raw)
    opts = dict(config.decoders[0].options)
    assert opts['enable_prior_perturbation'] and opts['use_original_prior_for_stage2']
    assert not dict(config.decoders[1].options)['enable_prior_perturbation']
    resolved = resolve_native_seeds(config)
    seed = dict(resolved.decoders[0].options)['perturbation_seed']
    assert type(seed) is int and 0 <= seed < 2**64
    assert resolve_native_seeds(resolved) == resolved
    assert 'perturbation_seed' not in dict(resolved.decoders[1].options)
    raw = native_config(tmp_path)
    raw['decoders'][0]['options']['stage1_perturbation'] = 'yes'
    with pytest.raises(ValueError, match='boolean'):
        parse_workflow_config(raw)
    raw = native_config(tmp_path, seed=2**64)
    with pytest.raises(ValueError, match='uint64'):
        parse_workflow_config(raw)
    raw = native_config(tmp_path)
    raw['decoders'][0]['options']['enable_cross_color_relifting'] = True
    with pytest.raises(ValueError, match='mutually exclusive'):
        parse_workflow_config(raw)


def test_presampled_chunks_use_absolute_offsets_after_cache_eviction(tmp_path, monkeypatch):
    point = plan_points(parse_workflow_config(native_config(tmp_path)))[0]
    ordinary_pair = worker._construct(point)
    shots, observations = ordinary_pair.configured.sample(12, seed=37)
    prediction, expected = ordinary_pair.configured.decode(shots, full_output=True)
    slices = {100: slice(8, 12), 101: slice(0, 4), 102: slice(4, 8)}
    seen = []
    original_decode = ColorCode.decode
    def sampled(self, count, seed):
        s = slices[seed]
        assert count == s.stop-s.start
        return shots[s], observations[s]
    def decode(self, detectors, **kwargs):
        result = original_decode(self, detectors, **kwargs)
        seen.append((kwargs['perturbation_shot_offset'], result))
        return result
    monkeypatch.setattr(ColorCode, 'sample', sampled)
    monkeypatch.setattr(ColorCode, 'decode', decode)
    try:
        for chunk, seed in enumerate(slices):
            s = slices[seed]
            worker._CODE_CACHE.clear()
            output = worker.run_chunk(worker.WorkerInput(point.point_id, chunk, s.start, 4, seed, point))
            offset, actual = seen[-1]
            assert offset == s.start
            np.testing.assert_array_equal(actual[0], prediction[s])
            for key in ('candidate_weights', 'candidate_original_corrections'):
                np.testing.assert_array_equal(actual[1][key], expected[key][:, :, s])
            np.testing.assert_array_equal(output.metrics['logical_error'], prediction[s] != observations[s])
    finally:
        worker._CODE_CACHE.clear()


def test_spawn_worker_count_has_identical_same_chunk_results(tmp_path):
    point = plan_points(parse_workflow_config(native_config(tmp_path, shots=32)))[0]
    tasks = [worker.WorkerInput(point.point_id, i, 8*i, 8, 83+i, point) for i in range(4)]
    results = []
    for count in (1, 2):
        with ProcessPoolExecutor(max_workers=count, mp_context=multiprocessing.get_context('spawn')) as pool:
            results.append(list(pool.map(worker.run_chunk, tasks)))
    for one, two in zip(*results):
        assert one.metrics.keys() == two.metrics.keys()
        for key in one.metrics:
            np.testing.assert_array_equal(one.metrics[key], two.metrics[key])


def test_native_run_log_and_analysis_with_entropy_seed(tmp_path):
    raw = native_config(tmp_path, seed=None, shots=5)
    raw['simulation']['workers'] = 2
    root = run_experiment(parse_workflow_config(raw), reporter=lambda _: None)
    record = json.loads((root/'run_log.json').read_text())
    opts = record['config']['decoders'][0]['options']
    assert type(opts['perturbation_seed']) is int
    assert opts['enable_prior_perturbation'] and opts['use_original_prior_for_stage2']
    assert record['native_stage1_perturbation']['scheme_version'] == 1
    point_dir = next(root.glob('decoder_alias=native,*'))
    assert pq.read_table(point_dir/'logical_error.parquet').num_rows == 5
    assert pq.read_table(point_dir/'default_logical_error.parquet').num_rows == 5
    from color_code_softoutput.analysis.color_correlated import ColorCorrelatedRun
    table = ColorCorrelatedRun(root).summary()
    assert len(table) >= 1


def test_native_unsupported_prior_rejected_before_run_exists(tmp_path):
    raw = native_config(tmp_path)
    raw['sweep']['physical_error_rate'] = .4
    with pytest.raises(ValueError, match='negative weights'):
        run_experiment(parse_workflow_config(raw), reporter=lambda _: None)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('metric', ['swim_distance', 'logical_gap'])
def test_native_circuit_soft_output_workflow(tmp_path, metric):
    raw = native_config(tmp_path, shots=3)
    raw['sweep'].update(noise_model='uniform', rounds='distance', physical_error_rate=.001)
    if metric == 'swim_distance':
        raw['decoders'][0]['decode_options'] = {'compute_swim_distance': True}
    else:
        raw['decoders'][0]['options']['comparative_decoding'] = True
    root = run_experiment(parse_workflow_config(raw), reporter=lambda _: None)
    path = next(root.glob('decoder_alias=native,*')) / f'{metric}.parquet'
    values = pq.read_table(path).column(metric).to_numpy()
    assert values.shape == (3,) and np.isfinite(values).all() and np.all(values >= 0)
