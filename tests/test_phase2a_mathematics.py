"""M5 cross-check against the independent Phase-1 coordinate construction."""
from pathlib import Path
import importlib.util
import itertools
import numpy as np
import pytest
from color_code_stim import ColorCode
from color_code_stim.noise_model import NoiseModel
from color_code_stim.soft_output.pymatching_backend import Stage2Backend
from color_code_stim.soft_output.reference import reference_metric

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('phase1',ROOT/'notes/support/check_phase1.py')
phase1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(phase1)


def independent_graph(d,c):
    cc = ColorCode(d=d,rounds=1,noise_model=NoiseModel(bitflip=.05))
    backend = Stage2Backend(cc.dem_manager,c)
    topo = backend.topology
    h, incidence, edges = phase1.patch(d,c)
    limit = 3*((d-1)//2)
    qubits = [(i,j) for i in range(limit+1) for j in range(limit+1-i) if (i-j)%3 != 2]
    index = {q:i for i,q in enumerate(qubits)}
    col_to_q = {e.column_id:index[((e.coordinates[0]-2*e.coordinates[1])//4,e.coordinates[1])]
                for e in topo.edges}
    assert len(col_to_q) == len(qubits) == len(topo.edges)
    assert len(topo.active_rows)+2 == incidence.shape[0]
    production_incidence = np.zeros_like(incidence)
    weights = np.zeros(len(qubits))
    for label,u,v,w in topo.resolved_edges:
        q = col_to_q[label]
        production_incidence[u,q] ^= 1
        production_incidence[v,q] ^= 1
        weights[q] = w
    signatures = {tuple(row):i for i,row in enumerate(incidence)}
    vertex_map = {u:signatures[tuple(row)] for u,row in enumerate(production_incidence)}
    assert len(set(vertex_map.values())) == len(vertex_map)
    assert vertex_map[topo.terminals[0]] == len(incidence)-2
    assert vertex_map[topo.terminals[1]] == len(incidence)-1
    for label,u,v,w in topo.resolved_edges:
        assert set((vertex_map[u],vertex_map[v])) == set(edges[col_to_q[label]])
        assert w == pytest.approx(np.log(19))
    return cc,backend,h,incidence,edges,weights,col_to_q,vertex_map


@pytest.mark.parametrize('d',[3,5])
@pytest.mark.parametrize('c',['r','g','b'])
def test_physical_logical_witness_and_closed_chains(d,c):
    cc,backend,h,inc,edges,weights,col_to_q,vertex_map = independent_graph(d,c)
    shots,_ = cc.sample(48,seed=98173)
    stage1 = cc.concat_matching_decoder._decode_stage1(shots,c)
    stage2 = shots.copy()
    inactive = np.ones(stage2.shape[1],dtype=bool)
    inactive[cc.detector_ids_by_color[c]] = False
    stage2[:,inactive] = False
    stage2 = np.concatenate((stage2,stage1),axis=1)
    result = backend.matcher.decode_batch_with_soft_output(stage2,include_radii=True)
    for i,radii in enumerate(result.radii):
        independent_radii = np.zeros(len(inc))
        for u,v in vertex_map.items(): independent_radii[v] = radii[u]
        ref = reference_metric(len(inc),tuple((j,*edge,weights[j]) for j,edge in enumerate(edges)),
                               (len(inc)-2,len(inc)-1),radii=independent_radii)
        assert result.soft_outputs[i,0] == pytest.approx(ref.distance,abs=1e-9)
        support = np.zeros(len(edges),dtype=np.uint8)
        support[list(ref.edge_ids)] = 1
        assert not np.any((h @ support)%2)
        assert (inc[-2] @ support)%2 == 1
        assert (inc[-1] @ support)%2 == 1
    closed = [face for face in h if not np.any((inc @ face)%2)]
    assert len(closed) == (d*d-1)//4
    for support in closed:
        assert not np.any((h @ support)%2)
        assert (inc[-2] @ support)%2 == 0


@pytest.mark.parametrize('c',['r','g','b'])
def test_exhaustive_d3_fixed_fibers(c):
    cc,backend,h,inc,edges,weights,col_to_q,vertex_map = independent_graph(3,c)
    chains = np.array(list(itertools.product([0,1],repeat=7)),dtype=np.uint8)
    syndromes = (chains @ inc[:-2].T)%2
    costs = chains @ weights
    parity = (chains @ inc[-2])%2
    decomp = cc.dems_decomposed[c]
    for syndrome in itertools.product([0,1],repeat=inc.shape[0]-2):
        fullshot = np.zeros((1,decomp.Hs[1].shape[0]),dtype=np.uint8)
        for u,row in enumerate(backend.topology.active_rows):
            fullshot[0,row] = syndrome[vertex_map[u]]
        result = backend.matcher.decode_batch_with_soft_output(fullshot,include_radii=True)
        prediction = np.zeros(7,dtype=np.uint8)
        for col,q in col_to_q.items(): prediction[q] = result.predictions[0,col]
        np.testing.assert_array_equal((inc[:-2] @ prediction)%2,syndrome)
        feasible = np.all(syndromes == syndrome,axis=1)
        baseline = costs[feasible].min()
        assert result.solution_weights[0] == pytest.approx(baseline,abs=1e-7)
        opposite = costs[feasible & (parity != (inc[-2] @ prediction)%2)].min()
        assert opposite >= baseline-1e-9
        independent_radii = np.zeros(len(inc))
        for u,v in vertex_map.items(): independent_radii[v] = result.radii[0,u]
        ref = reference_metric(len(inc),tuple((j,*edge,weights[j]) for j,edge in enumerate(edges)),
                               (len(inc)-2,len(inc)-1),radii=independent_radii)
        assert result.soft_outputs[0,0] == pytest.approx(ref.distance,abs=1e-9)
        # The prototype does not export nonnegative odd-cut variables and exact
        # primal/dual equality. The bound assertion is deliberately inapplicable.
