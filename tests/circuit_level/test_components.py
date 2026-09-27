"""Independent exact subset and interval-union oracles for M1–M7."""
from dataclasses import replace
import itertools
import math
import numpy as np
import pytest
from color_code_stim import ColorCode, NoiseModel
from color_code_stim.soft_output.reference import reference_metric
from color_code_softoutput.circuit_level import (
    adapt_stage2, preprocess_topology, residual_weights, compute_circuit_level_swim,
)
from color_code_softoutput.circuit_level.graph import build_graph, incidence_matrix
from color_code_softoutput.circuit_level.logical_topology import rank_class_exists, build_cut
from color_code_softoutput.circuit_level.model import RowRole, SwimStatus, TopologyMethod
from color_code_softoutput.circuit_level.validation import validate_witness, validate_correction


def make_graph(n, columns, labels, weights=None):
    D = np.zeros((n, len(columns)), dtype=np.uint8)
    for i, endpoints in enumerate(columns):
        D[list(endpoints), i] = 1
    return build_graph(D, labels, np.ones(len(columns)) if weights is None else weights)


def brute(graph, weights):
    D = incidence_matrix(graph).toarray()
    L = np.array([e.logical_label for e in graph.mechanisms], dtype=np.uint8)
    best = math.inf
    for bits in itertools.product((0, 1), repeat=len(weights)):
        z = np.array(bits, dtype=np.uint8)
        if not np.any(D @ z % 2) and L @ z % 2:
            best = min(best, float(np.asarray(weights) @ z))
    return best


@pytest.mark.parametrize("n,columns,labels,expected,balanced", [
    (3, [(0,1),(1,2),(0,2)], [1,0,0], 3, False),
    (3, [(0,1),(1,2),(0,2)], [1,1,0], math.inf, True),
    (0, [()], [1], 1, True),
    (1, [(0,), (0,)], [0,1], 2, True),
    (5, [(0,1),(1,2),(0,2),(3,4)], [1,0,0,0], 3, False),
    (2, [(0,1)], [1], math.inf, True),  # Cross-sheet multisource gives the WRONG value 1.
    (1, [()], [0], math.inf, True),
    (2, [(0,1),(0,1)], [0,1], 2, False),
    (0, [], [], math.inf, True),
])
def test_exact_examples(n, columns, labels, expected, balanced):
    graph = make_graph(n, columns, labels)
    top = preprocess_topology(graph)
    assert top.balance_passed == balanced
    assert top.class_exists == rank_class_exists(graph) == math.isfinite(expected)
    result = compute_circuit_level_swim(top, graph.weights)
    assert result.phi == expected == brute(graph, graph.weights)
    assert compute_circuit_level_swim(top, graph.weights, force_cover=True).phi == expected
    if math.isfinite(expected):
        validate_witness(graph, result.witness, graph.weights, expected)
    else:
        assert result.status == SwimStatus.NO_OPPOSITE_CLASS and result.witness is None
        assert top.analysis is None and result.method is None
    if not balanced:
        with pytest.raises(ValueError, match="balance"):
            build_cut(graph)


def test_boundary_root_only_would_be_wrong():
    graph = make_graph(3, [(0,), (0,1),(1,2),(0,2)], [0,1,0,0], [10,1,1,1])
    result = compute_circuit_level_swim(preprocess_topology(graph), graph.weights)
    assert result.phi == 3
    assert result.witness.column_ids == (1,2,3)


@pytest.mark.parametrize("seed", range(35))
def test_random_exact_enumeration_gauge_and_cut(seed):
    rng = np.random.default_rng(seed)
    n, m = 4, 8
    columns = [tuple(sorted(rng.choice(n, int(rng.integers(3)), replace=False))) for _ in range(m)]
    labels, weights = rng.integers(2, size=m), rng.integers(5, size=m)
    graph = make_graph(n, columns, labels, weights)
    top = preprocess_topology(graph)
    expected = brute(graph, weights)
    assert top.class_exists == rank_class_exists(graph) == math.isfinite(expected)
    assert compute_circuit_level_swim(top, weights).phi == expected
    assert compute_circuit_level_swim(top, weights, force_cover=True).phi == expected
    D = incidence_matrix(graph, original_rows=True).toarray()
    gauge = rng.integers(2, size=n)
    transformed = build_graph(D, (labels + gauge @ D) % 2, weights)
    assert compute_circuit_level_swim(preprocess_topology(transformed), weights).phi == expected


@pytest.fixture(scope="module", params=[3,5,7])
def memory(request):
    d = request.param
    return ColorCode(d=d, rounds=d, circuit_type="tri", cnot_schedule="tri_optimal",
                     noise_model=NoiseModel.uniform_circuit_noise(.003))


@pytest.mark.parametrize("color", list("rgb"))
def test_actual_adapter_incidence_metadata_rank_and_cut_cover(memory, color):
    graph = adapt_stage2(memory.dem_manager, color)
    decomp = memory.dems_decomposed[color]
    H, p = decomp.Hs[1], decomp.probs[1]
    assert (incidence_matrix(graph, original_rows=True) != H).nnz == 0
    np.testing.assert_array_equal([e.logical_label for e in graph.mechanisms], decomp.obs_matrix_stage2.toarray().ravel())
    np.testing.assert_array_equal(graph.weights, np.log((1-p)/p))
    assert len({e.stable_id for e in graph.mechanisms}) == H.shape[1]
    assert graph == adapt_stage2(memory.dem_manager, color)
    assert sorted(e.unsorted_column_id for e in graph.mechanisms) == list(range(H.shape[1]))
    coords = memory.circuit.get_detector_coordinates()
    for row in graph.rows:
        assert row.coordinates == tuple(tuple(coords[d]) for d in row.detector_ids)
        assert row.times == tuple(c[2] for c in row.coordinates)
        assert row.colors == tuple("rgb"[int(c[4])] for c in row.coordinates)
        if row.active:
            assert row.role in (RowRole.PHYSICAL, RowRole.VIRTUAL)
    assert {t for r in graph.rows for t in r.times} >= {0., float(memory.rounds)}
    top = preprocess_topology(graph)
    assert top.class_exists and rank_class_exists(graph)  # Mandatory measured-sector gate.
    a = compute_circuit_level_swim(top, graph.weights)
    b = compute_circuit_level_swim(top, graph.weights, force_cover=True)
    assert a.phi == pytest.approx(b.phi)
    for result in (a, b):
        validate_witness(graph, result.witness, graph.weights, result.phi)


@pytest.mark.parametrize("color", list("rgb"))
def test_small_actual_submodels_against_brute_force(color):
    cc = ColorCode(d=3, rounds=3, noise_model=NoiseModel.uniform_circuit_noise(.003))
    graph = adapt_stage2(cc.dem_manager, color)
    result = compute_circuit_level_swim(preprocess_topology(graph), graph.weights)
    chosen = sorted(set(result.witness.column_ids) | set(range(8)))[:12]
    D = incidence_matrix(graph).toarray()[:, chosen]
    sub = build_graph(D, [graph.mechanisms[i].logical_label for i in chosen],
                      [graph.weights[i] for i in chosen])
    assert compute_circuit_level_swim(preprocess_topology(sub), sub.weights, force_cover=True).phi == pytest.approx(brute(sub, sub.weights))


@pytest.mark.parametrize("seed", range(15))
def test_residual_interval_union_reference(seed):
    rng = np.random.default_rng(seed)
    graph = make_graph(4, [(0,1),(1,2),(0,2),(2,3),(3,),(),(3,)],
                       [1,0,0,0,1,1,0], rng.uniform(.1,8,7))
    radii = rng.uniform(0, 5, graph.num_vertices)
    residual = residual_weights(graph, radii)
    edges = [(e.column_id,*e.endpoints,e.weight) for e in graph.mechanisms]
    reference = reference_metric(graph.num_vertices, edges, (0,graph.b_star), radii=radii)
    np.testing.assert_allclose(residual, list(reference.residual_weights.values()), atol=1e-12)
    top = preprocess_topology(graph)
    result = compute_circuit_level_swim(top, residual)
    assert result.phi == pytest.approx(brute(graph, residual))


def test_partial_loop_parallel_and_covered_odd_witness():
    line = make_graph(2, [(0,1)], [0], [5])
    np.testing.assert_array_equal(residual_weights(line, [1,2,0]), [2])
    loop = make_graph(0, [()], [1], [5])
    np.testing.assert_array_equal(residual_weights(loop, [1]), [3])
    graph = make_graph(1, [(0,),(0,)], [0,1], [2,2])
    residual = residual_weights(graph, [2,0])
    result = compute_circuit_level_swim(preprocess_topology(graph), residual)
    assert result.phi == 0 and result.witness.column_ids == (0,1)
    validate_witness(graph, result.witness, residual, 0)
    with pytest.raises(ValueError, match="Growth unavailable"):
        residual_weights(graph, None)


def test_reject_invalid_or_open_models_and_witnesses():
    with pytest.raises(NotImplementedError, match="Open"):
        build_graph([[1]], [1], [1], closed_temporal_boundary=False)
    with pytest.raises(ValueError, match="graphlike"):
        build_graph([[1],[1],[1]], [1], [1])
    with pytest.raises(ValueError, match="nonnegative"):
        build_graph([[1]], [1], [-1])
    graph = make_graph(1, [(0,),(0,)], [0,1])
    with pytest.raises(ValueError, match="D f"):
        validate_correction(graph, [[1,0]], [[0]])
    result = compute_circuit_level_swim(preprocess_topology(graph), graph.weights)
    with pytest.raises(ValueError, match="cost"):
        validate_witness(graph, replace(result.witness, cost=99), graph.weights, result.phi)


def test_source_label_mismatch_refused():
    cc = ColorCode(d=3, rounds=3, noise_model=NoiseModel.uniform_circuit_noise(.003))
    decomp = cc.dems_decomposed['r']
    old = decomp.obs_matrix_stage2
    decomp.obs_matrix_stage2 = old.tolil()
    decomp.obs_matrix_stage2[0,0] = not bool(old[0,0])
    decomp.obs_matrix_stage2 = decomp.obs_matrix_stage2.tocsc()
    with pytest.raises(ValueError, match="observable map"):
        adapt_stage2(cc.dem_manager, 'r')


def test_adapter_column_permutation_retains_source_ids():
    cc = ColorCode(d=3,rounds=3,noise_model=NoiseModel.uniform_circuit_noise(.003))
    before = adapt_stage2(cc.dem_manager,'r')
    d = cc.dems_decomposed['r']
    order = np.random.default_rng(911).permutation(d.Hs[1].shape[1])
    d.Hs = (d.Hs[0], d.Hs[1][:,order])
    d.probs = (d.probs[0], d.probs[1][order])
    d.obs_matrix_stage2 = d.obs_matrix_stage2[:,order]
    d.error_map_matrices = (d.error_map_matrices[0], d.error_map_matrices[1][order,:])
    d.stage2_edges = tuple(replace(d.stage2_edges[j],column_id=i) for i,j in enumerate(order))
    after = adapt_stage2(cc.dem_manager,'r')
    assert [e.stable_id for e in after.mechanisms] == [before.mechanisms[i].stable_id for i in order]
    assert [e.source_dem_ids for e in after.mechanisms] == [before.mechanisms[i].source_dem_ids for i in order]
    a = compute_circuit_level_swim(preprocess_topology(before),before.weights)
    b = compute_circuit_level_swim(preprocess_topology(after),after.weights)
    assert a.phi == pytest.approx(b.phi)


def test_row_permutation_and_padding_have_identical_objective():
    D = np.array([[1,1,0,0],[0,1,1,0],[0,0,0,0]],dtype=np.uint8)
    a = build_graph(D,[0,1,0,1],[3,2,4,9])
    b = build_graph(D[[2,0,1]], [0,1,0,1],[3,2,4,9])
    assert np.array_equal(incidence_matrix(b,original_rows=True).toarray(),D[[2,0,1]])
    assert compute_circuit_level_swim(preprocess_topology(a),a.weights).phi == compute_circuit_level_swim(preprocess_topology(b),b.weights).phi
