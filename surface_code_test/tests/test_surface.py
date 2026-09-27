"""Independent gates for surface model, forced classes, paired sampling and plotting."""
from dataclasses import replace
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pymatching
import pytest
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import csc_matrix, hstack, eye
from surface_code_test.model import ROOT, ComplementaryMatcher, model, build_circuit
from surface_code_test.simulation import SurfaceConfig, batch_tasks, sample_batch, validate_shots
from surface_code_test.experiment import run_experiment, audit_run
from surface_code_test.analysis import SurfaceDataset, standard_analysis, plot_postselection
from color_code_softoutput.simulation.parallel_runner import completed_batches
from color_code_softoutput.analysis.figure_style import RevtexFigureStyle
from color_code_stim.soft_output.reference import reference_metric


def tiny_graph(gauge):
    graph = pymatching.Matching()
    for u,v,w,label in ((0,1,2,0),(1,2,3,0),(0,None,4,0),(2,None,5,1),(1,None,6,0)):
        transformed = label ^ gauge[u] ^ (gauge[v] if v is not None else 0)
        if v is None:
            graph.add_boundary_edge(u,weight=w,fault_ids={0} if transformed else set())
        else:
            graph.add_edge(u,v,weight=w,fault_ids={0} if transformed else set())
    return graph


@pytest.mark.parametrize('gauge',list(itertools.product((0,1),repeat=3)))
def test_complementary_against_exhaustive_kernel_classes(gauge):
    graph = tiny_graph(gauge)
    forced = ComplementaryMatcher(graph)
    expected = np.full((8,2),np.inf)
    for bits in itertools.product((0,1),repeat=len(forced.edges)):
        syndrome = np.zeros(3,dtype=np.uint8)
        logical,cost=0,0.
        for bit,(u,v,data) in zip(bits,forced.edges):
            if bit:
                syndrome[u] ^= 1
                if v is not None:
                    syndrome[v] ^= 1
                logical ^= bool(data['fault_ids']); cost += data['weight']
        index = int(syndrome @ [4,2,1])
        expected[index,logical] = min(expected[index,logical],cost)
    shots = np.array(list(itertools.product((0,1),repeat=3)),dtype=np.uint8)
    np.testing.assert_allclose(forced.class_weights(shots),expected,atol=1e-6)


def test_unbalanced_or_absent_class_rejected():
    graph = pymatching.Matching()
    graph.add_edge(0,1,weight=1,fault_ids=0)
    graph.add_edge(1,2,weight=1)
    graph.add_edge(2,0,weight=1)
    with pytest.raises(ValueError,match='unbalanced'):
        ComplementaryMatcher(graph)
    graph = pymatching.Matching()
    graph.add_edge(0,1,weight=1,fault_ids=0)
    graph.add_boundary_edge(0,weight=1)
    with pytest.raises(ValueError,match='opposite'):
        ComplementaryMatcher(graph)


@pytest.mark.parametrize('d',[3,5,7])
def test_actual_hard_invariance_reset_and_class_weights(d):
    decoder = model(d,2*d,.001)
    shots,obs = decoder.circuit.compile_detector_sampler(seed=500+d).sample(24,separate_observables=True)
    result = decoder.decode(shots)
    repeat = decoder.decode(shots[::-1])
    for name in ('prediction','solution_weight','swim_distance','complementary_gap','class_weights','path_gap','path_gap_residual_distance','path_gap_correction_weight'):
        np.testing.assert_array_equal(getattr(result,name),getattr(repeat,name)[::-1])
    one = decoder.decode(shots[5:6])
    np.testing.assert_array_equal(one.swim_distance,result.swim_distance[5:6])
    empty = decoder.decode(shots[:0])
    assert empty.swim_distance.shape == (0,)
    assert decoder.diagnostics['boundary_labels'] == {'0':[0],'1':[1]}
    assert not decoder.diagnostics['swim_bound_certified']


def test_actual_forced_cost_independent_integer_program():
    decoder = model(3,6,.001)
    edges = decoder.complementary.edges
    n,m = decoder.matcher.num_detectors,len(edges)
    # Construct original D,L directly from ordinary edges, without gauge helper.
    D = np.zeros((n+1,m))
    for j,(u,v,data) in enumerate(edges):
        D[u,j] = 1
        if v is not None:
            D[v,j] = 1
        D[n,j] = bool(data['fault_ids'])
    A = hstack((csc_matrix(D),-2*eye(n+1)),format='csc')
    costs = np.r_[decoder.complementary.weights,np.zeros(n+1)]
    shots,_ = decoder.circuit.compile_detector_sampler(seed=151).sample(3,separate_observables=True)
    actual = decoder.complementary.class_weights(shots)
    for i,s in enumerate(shots):
        for bit in (0,1):
            target = np.r_[s,bit]
            solved = milp(costs,integrality=np.ones(m+n+1),
                bounds=Bounds(np.zeros(m+n+1),np.r_[np.ones(m),np.full(n+1,m)]),
                constraints=LinearConstraint(A,target,target),options={'time_limit':30,'mip_rel_gap':0})
            assert solved.success, solved.message
            np.testing.assert_allclose(actual[i,bit],solved.fun,rtol=0,atol=2e-5)


def test_surface_radii_against_independent_interval_reference():
    decoder = model(3,6,.001)
    shots,_ = decoder.circuit.compile_detector_sampler(seed=271).sample(3,separate_observables=True)
    soft = decoder.matcher.decode_batch_with_soft_output(shots,include_radii=True)
    config = decoder.topology
    for i,radii in enumerate(soft.radii):
        reference = reference_metric(len(config.node_map),config.edges,config.terminal_pairs[0],radii=radii)
        np.testing.assert_allclose(soft.soft_outputs[i,0],reference.distance,atol=1e-9)


def test_frozen_example_circuit_and_hard_fixture():
    circuit = build_circuit(5,10,.001)
    import stim
    original = stim.Circuit.from_file(ROOT/'implementation_artifacts/baseline/sc5_10_SE_rds.stim')
    assert circuit == original
    fixture = np.load(ROOT/'implementation_artifacts/baseline/surface_so.npz')
    decoder = model(5,10,.001)
    result = decoder.decode(fixture['detectors'])
    np.testing.assert_array_equal(result.prediction,fixture['predictions'].reshape(-1))


@pytest.mark.parametrize('kwargs',[{'distances':(2,)},{'distances':(3,3)}, {'physical_error_rate':0},
    {'physical_error_rate':float('nan')},{'rounds_factor':0},{'shots_per_point':0},{'batch_size':-1},
    {'num_workers':0},{'master_seed':-1}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError):
        SurfaceConfig(**kwargs)


def test_serial_parallel_and_semantic_rejection(tmp_path):
    config = SurfaceConfig(distances=(3,),shots_per_point=16,batch_size=8,num_workers=2,output_root=tmp_path)
    tasks = list(batch_tasks(config,'fixed'))
    serial = pd.concat([sample_batch(t) for t in tasks],ignore_index=True)
    parallel = pd.concat([f for _,f in completed_batches(tasks,2,worker=sample_batch)],ignore_index=True)
    pd.testing.assert_frame_equal(serial.sort_values('shot_index').reset_index(drop=True),
                                  parallel.sort_values('shot_index').reset_index(drop=True))
    broken = serial.copy(); broken.loc[0,'ordinary_logical_error'] = not broken.loc[0,'ordinary_logical_error']
    with pytest.raises(ValueError,match='failure'):
        validate_shots(broken)
    broken = serial.copy(); broken.loc[0,'complementary_gap'] += 1
    with pytest.raises(AssertionError):
        validate_shots(broken)


def test_saved_run_audit_plots_and_corruption(tmp_path):
    config = SurfaceConfig(distances=(3,),shots_per_point=48,batch_size=24,num_workers=1,output_root=tmp_path)
    run = run_experiment(config,analyze=False,verbose=False)
    dataset = SurfaceDataset(run)
    assert dataset.metadata['status'] == 'complete'
    assert audit_run(run)['shots'] == 48
    rows = dataset.metric_rows('selected_swim_distance')
    np.testing.assert_allclose(rows.selected_swim_distance,dataset.read().swim_distance*10/np.log(10))
    standard_analysis(dataset,style=RevtexFigureStyle(test_mode=True))
    table = pd.read_parquet(run/'postselection_dB.parquet')
    assert set(table.metric) == {'swim_distance','complementary_gap','path_gap'}
    assert set(table.failure_column) == {'ordinary_logical_error'}
    for metric, part in table.groupby('metric'):
        assert len(part) == len(np.unique(dataset.read()[metric]))
        assert part.iloc[0].retained_shots == 48
    assert len(list((run/'figures').glob('surface_*.png'))) == 5
    path = dataset.shards[0]
    import pyarrow as pa
    import pyarrow.parquet as pq
    schema = pq.read_schema(path)
    frame = pd.read_parquet(path)
    frame.loc[0,'batch_seed'] = np.uint64(int(frame.loc[0,'batch_seed'])+1)
    pq.write_table(pa.Table.from_pandas(frame,schema=schema,preserve_index=False),path)
    with pytest.raises(ValueError,match='batch_seed'):
        audit_run(run,replay=False)
    frame.to_parquet(path,index=False)
    with pytest.raises(ValueError,match='schema'):
        SurfaceDataset(run)


def test_one_physical_sample_for_both_scores(monkeypatch):
    import surface_code_test.simulation as simulation
    from types import SimpleNamespace
    task = next(batch_tasks(SurfaceConfig(distances=(3,),shots_per_point=8,num_workers=1),'counted'))
    decoder = model(3,6,.001)
    calls = []
    sampler = decoder.circuit.compile_detector_sampler(seed=task.seed)
    def sample(shots,*,separate_observables):
        calls.append((shots,separate_observables))
        return sampler.sample(shots,separate_observables=separate_observables)
    proxy = SimpleNamespace(circuit=SimpleNamespace(compile_detector_sampler=lambda seed:SimpleNamespace(sample=sample)),decode=decoder.decode)
    monkeypatch.setattr(simulation,'model',lambda *args:proxy)
    frame = simulation.sample_batch(task)
    assert calls == [(8,True)]
    assert len(frame) == 8


def test_saved_gap_never_uses_actual_logical_bit():
    decoder = model(3,6,.001)
    det,obs = decoder.circuit.compile_detector_sampler(seed=847).sample(8,separate_observables=True)
    original = decoder.decode(det)
    obs ^= True
    repeated = decoder.decode(det)
    np.testing.assert_array_equal(original.complementary_gap,repeated.complementary_gap)


def test_postselection_ties_in_raw_units():
    from color_code_softoutput.analysis.postselection import postselection_curve
    scores = np.array([1.,1.,np.nextafter(1.,2.),2.])
    table = postselection_curve(scores,[0,1,0,1])
    assert table.retained_shots.tolist() == [4,2,1]
    assert table.retained_failures.tolist() == [2,1,1]


@pytest.mark.parametrize('d',[3,5,7])
def test_path_gap_actual_graph_independent_networkx(d):
    import networkx as nx
    decoder = model(d,d,.003)
    shots,_ = decoder.circuit.compile_detector_sampler(seed=931+d).sample(12,separate_observables=True)
    result = decoder.decode(shots)
    edges = decoder.matcher.edges()
    keys = {tuple(sorted((u,-1 if v is None else v))):j for j,(u,v,_) in enumerate(edges)}
    for i,shot in enumerate(shots):
        support = {keys[tuple(sorted(pair))] for pair in decoder.matcher.decode_to_edges_array(shot)}
        cost = sum(e[2]['weight'] for j,e in enumerate(edges) if j in support)
        graph = nx.Graph()
        for j,u,v,w in decoder.topology.edges:
            graph.add_edge(u,v,weight=0 if j in support else w)
        a,b = decoder.topology.terminal_pairs[0]
        distance = nx.bellman_ford_path_length(graph,a,b)
        # Python 3.12 sum uses compensated accumulation; C++ adds in edge order.
        np.testing.assert_allclose(result.path_gap_correction_weight[i],cost,rtol=0,atol=1e-12)
        np.testing.assert_allclose(result.path_gap_residual_distance[i],distance,atol=1e-12)
        np.testing.assert_allclose(result.path_gap[i],distance-cost,atol=1e-12)


def test_path_gap_schema_and_legacy_loading(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    from surface_code_test.simulation import LEGACY_SHOT_SCHEMA
    run = run_experiment(SurfaceConfig(distances=(3,),shots_per_point=8,batch_size=8,
                                      num_workers=1,output_root=tmp_path),analyze=False,verbose=False)
    dataset = SurfaceDataset(run)
    frame = dataset.read()
    broken = frame.copy(); broken.loc[0,'path_gap'] += 1
    with pytest.raises(AssertionError):
        validate_shots(broken)
    broken = frame.copy(); broken['path_gap_metric_version'] = 'path_overlap_v2'
    with pytest.raises(ValueError,match='version'):
        validate_shots(broken)
    # A valid negative gap remains signed through storage validation and scaling.
    signed = frame.copy(); signed['path_gap_correction_weight'] += 1000
    signed['path_gap'] = signed.path_gap_residual_distance-signed.path_gap_correction_weight
    validate_shots(signed)
    legacy = frame[LEGACY_SHOT_SCHEMA.names]
    validate_shots(legacy)
    shard = dataset.shards[0]
    schema = LEGACY_SHOT_SCHEMA.with_metadata(pq.read_schema(shard).metadata)
    pq.write_table(pa.Table.from_pandas(legacy,schema=schema,preserve_index=False),shard)
    meta = dataset.metadata; del meta['path_gap_metric_version']
    (run/'metadata.json').write_text(json.dumps(meta))
    old = SurfaceDataset(run)
    assert not old.has_path_gap
    with pytest.raises(ValueError,match='legacy'):
        old.metric_rows('path_gap')
    standard_analysis(old,style=RevtexFigureStyle(test_mode=True))
    assert set(pd.read_parquet(run/'postselection_dB.parquet').metric) == {'swim_distance','complementary_gap'}
