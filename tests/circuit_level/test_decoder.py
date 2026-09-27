"""Actual growth, hard-result invariance, temporal pairing and state-reset gates."""
import numpy as np
import pytest
from color_code_stim import ColorCode, NoiseModel
from color_code_stim.soft_output.reference import reference_metric
from pymatching.soft_output import metric_from_radii
from color_code_softoutput.circuit_level.decoder import CircuitLevelDecoder
from color_code_softoutput.circuit_level.model import RowRole
from color_code_softoutput.simulation.pairing import validate_pairing


@pytest.fixture(scope="module", params=[3,5,7])
def configured(request):
    d = request.param
    options = dict(d=d, rounds=d, circuit_type="tri", cnot_schedule="tri_optimal",
                   noise_model=NoiseModel.uniform_circuit_noise(.003))
    code = ColorCode(**options)
    return code, CircuitLevelDecoder(code), options


def test_all_hard_outputs_and_branch_replay(configured):
    code, decoder, _ = configured
    shots, actual = code.sample(32, seed=416)
    pred, on = decoder.decode(shots, return_witness=True, include_debug=True)
    old, off = decoder.decode(shots, compute_swim_distance=False)
    np.testing.assert_array_equal(pred, old)
    for key in off:
        np.testing.assert_array_equal(on[key], off[key])
    np.testing.assert_array_equal(pred != actual, old != actual)
    for index, c in enumerate("rgb"):
        branch = on["branches"][c]
        # The private methods are an independent test oracle, never production dependencies.
        stage1 = code.concat_matching_decoder._decode_stage1(shots, c)
        corr, weights = code.concat_matching_decoder._decode_stage2(shots, stage1, c)
        np.testing.assert_array_equal(stage1, branch.stage1_predictions)
        np.testing.assert_array_equal(corr, branch.corrections)
        np.testing.assert_array_equal(weights, branch.solution_weights)
        assert len(on["witnesses_by_color"][c]) == len(shots)
        backend = decoder.backends[c]
        for i in (0, 1):
            _, native_residual = metric_from_radii(backend.growth_config, branch.radii[i])
            np.testing.assert_allclose(native_residual, branch.residual_weights[i], atol=1e-12)
            if code.d == 3:
                g = backend.graph
                ref = reference_metric(g.num_vertices, backend.growth_config.edges,
                                       (0,g.b_star), radii=branch.radii[i])
                np.testing.assert_allclose(list(ref.residual_weights.values()), branch.residual_weights[i], atol=1e-12)
    np.testing.assert_array_equal(on['selected_swim_distance'],
        on['swim_distances_by_color'][np.arange(len(shots)), off['best_colors']])
    assert not on['swim_bound_certified']


def test_repeat_reorder_single_empty_and_invalid(configured):
    code, decoder, _ = configured
    shots, _ = code.sample(9, seed=711)
    a, first = decoder.decode(shots, include_debug=True)
    b, reverse = decoder.decode(shots[::-1])
    _, single = decoder.decode(shots[3])
    np.testing.assert_array_equal(a, b[::-1])
    np.testing.assert_array_equal(first['swim_distances_by_color'], reverse['swim_distances_by_color'][::-1])
    np.testing.assert_array_equal(single['swim_distances_by_color'][0], first['swim_distances_by_color'][3])
    _, repeated = decoder.decode(shots, include_debug=True)
    for c in 'rgb':
        np.testing.assert_array_equal(first['branches'][c].radii, repeated['branches'][c].radii)
    p, empty = decoder.decode(shots[:0])
    assert p.shape == (0,) and empty['swim_distances_by_color'].shape == (0,3)
    with pytest.raises(ValueError, match='detector'):
        decoder.decode(shots[:,:-1])


def test_uniform_circuit_comparative_pairing(configured):
    code, _, options = configured
    comp = ColorCode(**options, comparative_decoding=True)
    assert validate_pairing(code.circuit, comp.circuit)['physical_operations_equal']
    records = code.circuit.compile_sampler(seed=187).sample(40)
    det, obs = code.circuit.compile_m2d_converter().convert(measurements=records,separate_observables=True)
    det2, obs2 = comp.circuit.compile_m2d_converter().convert(measurements=records,separate_observables=True)
    np.testing.assert_array_equal(np.column_stack((det,obs)), det2)
    np.testing.assert_array_equal(obs, obs2)
    a, x = comp.decode(det2,full_output=True)
    det2[:,-1] ^= True
    b, y = comp.decode(det2,full_output=True)
    np.testing.assert_array_equal(a,b)
    np.testing.assert_array_equal(x['logical_gaps'],y['logical_gaps'])


def test_temporal_spatial_hook_virtual_coverage_categories():
    code = ColorCode(d=5, rounds=5, noise_model=NoiseModel.uniform_circuit_noise(.003))
    decoder = CircuitLevelDecoder(code)
    kinds = set()
    for backend in decoder.backends.values():
        for e in backend.graph.mechanisms:
            rows = [backend.graph.rows[r] for r in e.endpoint_rows]
            if any(r.role == RowRole.VIRTUAL for r in rows):
                kinds.add('virtual')
            coords = [x for r in rows for x in r.coordinates]
            if coords:
                times, sites = {x[2] for x in coords}, {x[:2] for x in coords}
                if len(times) == 1:
                    kinds.add('spatial')
                elif len(sites) == 1:
                    kinds.add('timelike')
                else:
                    kinds.add('diagonal_hook')
    assert kinds == {'virtual','spatial','timelike','diagonal_hook'}


def test_stale_graph_and_unsupported_scope():
    code = ColorCode(d=3,rounds=3,noise_model=NoiseModel.uniform_circuit_noise(.003))
    decoder = CircuitLevelDecoder(code)
    code.dems_decomposed['r'].probs[1][0] *= .9
    with pytest.raises(ValueError,match='changed'):
        decoder.decode(np.zeros((1,code.circuit.num_detectors)))
    code = ColorCode(d=3,rounds=1,noise_model=NoiseModel.uniform_circuit_noise(.003))
    with pytest.raises(NotImplementedError,match='d-round'):
        CircuitLevelDecoder(code)
