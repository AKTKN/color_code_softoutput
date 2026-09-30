from dataclasses import replace
import json
import numpy as np
import pyarrow.parquet as pq
import pytest

from color_code_softoutput.simulation import worker
from color_code_softoutput.simulation.task import ResolvedPoint,metric_names
from color_code_softoutput.simulation.planner import point_directory_name
from color_code_softoutput.simulation.workflow_storage import PointStorage
from color_code_softoutput.simulation.config import parse_workflow_config,resolve_native_seeds
from color_code_softoutput.simulation.runner import run_experiment
from color_code_softoutput.analysis.color_correlated import ColorCorrelatedRun
from color_code_softoutput.analysis.workflow_soft_output import WorkflowSoftOutputRun


def point(mode='ordinary',soft='none',full=False):
    options={'temp_bdry_type':'Z'}
    if mode=='correlated':
        options.update(enable_colorcorrelated_decoding=True,color_correlated_b=4)
    if mode=='relift':
        options.update(enable_cross_color_relifting=True,remove_non_edge_like_errors=False)
    if mode in ('native','perturbation'):
        options.update(enable_prior_perturbation=True,stage1_perturbation=mode=='native',
            perturbation_seed=91,perturbation_alpha=1.,perturbation_ensemble_size=3)
    if soft=='comparative': options['comparative_decoding']=True
    decode={'bp_predecoding':True,'bp_prms':(('max_iter',1),),'full_output':full}
    if soft=='swim': decode['compute_swim_distance']=True
    return ResolvedPoint('bp','concat_mwpm',3,.003,'uniform',3,'tri','tri_optimal',20,
                         (),tuple(sorted(options.items())),tuple(sorted(decode.items())))


@pytest.mark.parametrize('mode',['ordinary','correlated','relift','native','perturbation'])
@pytest.mark.parametrize('soft',['none','comparative','swim'])
def test_bp_all_strategies_full_compact_and_parquet(tmp_path,mode,soft):
    results=[]
    for full in (False,True):
        p=point(mode,soft,full)
        worker._CODE_CACHE.clear()
        result=worker.run_chunk(worker.WorkerInput('bp',0,0,20,372,p))
        results.append(result)
        assert set(result.metrics)==set(metric_names(p))
        skipped=result.metrics['bp_converged']
        assert skipped.any() and (~skipped).any()
        for name,values in result.metrics.items():
            if name!='bp_converged':
                np.testing.assert_array_equal(np.ma.getmaskarray(values),skipped)
        store=PointStorage(p,tmp_path/str(full)/point_directory_name(p),7)
        store.accept(result);store.finalize()
        for name,values in result.metrics.items():
            table=pq.read_table(store.point_dir/f'{name}.parquet')
            assert table['shot_index'].to_pylist()==list(range(20))
            expected=skipped if name!='bp_converged' else np.zeros(20,dtype=bool)
            np.testing.assert_array_equal(table[name].is_null().to_numpy(),expected)
    for name in results[0].metrics:
        np.testing.assert_array_equal(results[0].metrics[name],results[1].metrics[name])
    worker._CODE_CACHE.clear()


def test_bp_null_inconsistent_storage_rejected(tmp_path):
    p=point()
    result=worker.run_chunk(worker.WorkerInput('bp',0,0,20,372,p))
    result.metrics['logical_error']=np.zeros(20,dtype=bool)
    store=PointStorage(p,tmp_path/point_directory_name(p),7)
    with pytest.raises(ValueError,match='nulls'):
        store.accept(result)
    worker._CODE_CACHE.clear()


@pytest.mark.parametrize('workers',[1,2])
def test_bp_yaml_roundtrip_spawn_storage_and_nullable_analysis(tmp_path,workers):
    raw=workflow_data(tmp_path,workers)
    config=parse_workflow_config(raw)
    restored=parse_workflow_config(json.loads(json.dumps(config.semantic_dict() | {'simulation':raw['simulation']})))
    assert config.hash8==restored.hash8
    root=run_experiment(config)
    point_dir=next(path for path in root.iterdir() if path.is_dir())
    skipped=pq.read_table(point_dir/'bp_converged.parquet')['bp_converged'].to_numpy()
    logical=pq.read_table(point_dir/'logical_error.parquet')['logical_error']
    run=ColorCorrelatedRun(root)
    summary=run.summary()
    assert summary.shots.iloc[0]==len(skipped)
    assert summary.failures.iloc[0]==sum(logical.drop_null().to_pylist())
    assert summary.statistics_scope.iloc[0]=='all shots'
    soft=WorkflowSoftOutputRun(root)
    scores,failures=soft._point(soft.run.catalog.iloc[0],'swim_distance')
    assert len(scores)==len(failures)==np.count_nonzero(~skipped)


def workflow_data(tmp_path,workers=1):
    return {
        'simulation':{'output_root':str(tmp_path),'shots':20,'workers':workers,
                      'master_seed':42,'buffer_shots':3,'verbose':False},
        'chunking':{'calibration_shots':3,'target_chunk_seconds':.1,
                    'min_chunk_shots':2,'max_chunk_shots':4,'throughput_ema_alpha':.5},
        'sweep':{'distance':3,'physical_error_rate':.003,'noise_model':'uniform',
                 'rounds':'distance','circuit_type':'tri','cnot_schedule':'tri_optimal'},
        'color_code_options':{'temp_bdry_type':'Z'},
        'decoders':[{'type':'concat_mwpm','decode_options':{'bp_predecoding':True,
                        'bp_prms':{'max_iter':1},'compute_swim_distance':True}}]}


@pytest.mark.parametrize('mode',['ordinary','correlated','native'])
def test_all_converged_worker_never_separates_noise_or_builds_css_graphs(monkeypatch,mode):
    def fail(*args,**kwargs):
        raise AssertionError('Converged BP must not prepare CSS decoding')
    monkeypatch.setattr('color_code_stim.dem_utils.dem_manager.separate_depolarizing_errors',fail)
    monkeypatch.setattr('color_code_stim.dem_utils.dem_manager.DemDecomp',fail)
    monkeypatch.setattr('color_code_stim.ColorCode.sample',lambda c,shots,**kwargs:
        (np.zeros((shots,c.circuit.num_detectors),dtype=bool),np.zeros(shots,dtype=bool)))
    worker._CODE_CACHE.clear()
    p=point(mode,'swim')
    result=worker.run_chunk(worker.WorkerInput('bp',0,0,20,372,p))
    assert result.metrics['bp_converged'].all()
    assert all(np.ma.getmaskarray(values).all() for name,values in result.metrics.items() if name!='bp_converged')
    worker._CODE_CACHE.clear()


def test_bp_original_dem_entropy_seed_resolved_before_spawn(tmp_path):
    raw=workflow_data(tmp_path)
    raw['decoders'][0]['type']='perturbation'
    raw['decoders'][0]['options']={'enable_prior_perturbation':True,'perturbation_ensemble_size':3}
    config=parse_workflow_config(raw)
    resolved=resolve_native_seeds(config)
    seed=dict(resolved.decoders[0].options)['perturbation_seed']
    assert type(seed) is int and 0<=seed<2**64
    assert resolve_native_seeds(resolved)==resolved


def test_all_converged_nullable_summary_keeps_physical_denominator(tmp_path,monkeypatch):
    import matplotlib.pyplot as plt
    from color_code_softoutput.simulation.planner import plan_points
    raw=workflow_data(tmp_path)
    config=parse_workflow_config(raw)
    p=plan_points(config)[0]
    root=tmp_path/'completed';root.mkdir()
    monkeypatch.setattr('color_code_stim.ColorCode.sample',lambda c,shots,**kwargs:
        (np.zeros((shots,c.circuit.num_detectors),dtype=bool),np.zeros(shots,dtype=bool)))
    worker._CODE_CACHE.clear()
    result=worker.run_chunk(worker.WorkerInput(p.point_id,0,0,20,372,p))
    store=PointStorage(p,root/point_directory_name(p),7)
    store.accept(result);store.finalize()
    (root/'run_log.json').write_text(json.dumps({'config':config.semantic_dict() | {'simulation':raw['simulation']},
                                              'simulation_end_time':'2026-09-29T00:00:00+00:00'}))
    run=ColorCorrelatedRun(root)
    summary=run.summary().iloc[0]
    assert summary.shots==20 and summary.bp_converged_shots==20 and summary.physical_shots==20
    assert summary.logical_error_rate==0 and np.isfinite(summary.ler_high)
    scores,failures=WorkflowSoftOutputRun(root)._point(run.catalog.iloc[0],'swim_distance')
    assert len(scores)==len(failures)==0
    figure,axes,plotted=run.plot_ler()
    # Zero rates are hidden on the log axis, but retained in its source table.
    assert (plotted.logical_error_rate==0).all()
    assert np.isfinite(plotted.ler_high).all()
    plt.close(figure)
    worker._CODE_CACHE.clear()


@pytest.mark.parametrize('mixed',[False,True])
def test_native_bp_run_log_records_actual_probability_law_version(tmp_path,mixed):
    raw=workflow_data(tmp_path)
    raw['simulation']['shots']=6
    options={'stage1_perturbation':True,'perturbation_ensemble_size':3,
             'perturbation_alpha':1.,'perturbation_seed':19}
    raw['decoders'][0].update(type='perturbation',decoder_alias='BP',options=options)
    if mixed:
        raw['decoders'].append({'type':'perturbation','decoder_alias':'regular',
                               'options':options,'decode_options':{}})
    config=parse_workflow_config(raw)
    root=run_experiment(config)
    record=json.loads((root/'run_log.json').read_text())
    bp=record['global_bp_predecoding']
    assert bp['version']==4
    assert bp['weight_rule']=='negative_log_xz_probability'
    assert bp['aggregation']=='independent_xor'
    assert bp['effective_probability']=='p/(1+p)'
    assert bp['stage1_prior']=='bp_posterior'
    assert bp['stage2_prior']==bp['selection_prior']=='original_physical'
    assert bp['selection_weight_basis']=='original_dem'
    log=record['native_stage1_perturbation']
    assert log['scheme_version']==('mixed' if mixed else 2)
    from color_code_softoutput.simulation.planner import plan_points
    assert log['scheme_version_by_point']=={
        p.point_id:2 if dict(p.decode_options).get('bp_predecoding') else 1
        for p in plan_points(config)}
