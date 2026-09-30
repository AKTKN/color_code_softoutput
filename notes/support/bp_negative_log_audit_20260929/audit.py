"""Bounded saved-run replay and paired checks; never writes experiment data."""
from pathlib import Path
from collections import Counter
from contextlib import contextmanager
import hashlib
import inspect
import importlib.metadata as md
import json

import numpy as np
import pyarrow.parquet as pq
from color_code_stim import ColorCode
from color_code_stim.dem_utils.global_dem import GlobalDemProjection
from color_code_softoutput.simulation.config import parse_workflow_config
from color_code_softoutput.simulation.planner import plan_points, point_directory_name
from color_code_softoutput.simulation.scheduler import chunk_seed
from color_code_softoutput.simulation import worker

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
RUN=ROOT/'results/bpmatching/26_09_29_23_27_44_9926fe3c'
PREVIOUS=ROOT/'results/bpmatching/26_09_29_21_59_45_9926fe3c'
ARCHIVE=OUT.parent/'bp_round2_audit_20260929'
LOG=json.loads((RUN/'run_log.json').read_text())
CONFIG=parse_workflow_config(LOG['config'])

def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n')

@contextmanager
def old_weight_rule():
    project=GlobalDemProjection.project
    def old(self,q,**kwargs):
        return project(self,np.minimum(q,.5))
    GlobalDemProjection.project=old
    try:
        yield
    finally:
        GlobalDemProjection.project=project

def code(d=5,p=.03):
    return ColorCode(**LOG['config']['color_code_options'],d=d,rounds=2,
                     p_depol=p,circuit_type='tri',cnot_schedule='tri_optimal')

if __name__=='__main__':
    counts=[]
    for folder in sorted(RUN.glob('decoder*')):
        key=dict(item.split('=',1) for item in folder.name.split(','))
        row=dict(key)
        for label,base in [('new',RUN),('old',PREVIOUS)]:
            vals=pq.read_table(base/folder.name/'logical_error.parquet')['logical_error'].to_pylist()
            row[label]=dict(shots=len(vals),failures=sum(v is True for v in vals),
                            nulls=sum(v is None for v in vals))
        counts.append(row)
    write('counts.json',counts)
    replay=[]
    for point in plan_points(CONFIG):
        folder=RUN/point_directory_name(point)
        task=worker.WorkerInput(point.point_id,0,0,CONFIG.chunking.calibration_shots,
                               chunk_seed(CONFIG.simulation.master_seed,point.point_id,0),point)
        worker._CODE_CACHE.clear()
        new=worker.run_chunk(task)
        with old_weight_rule():
            worker._CODE_CACHE.clear()
            old=worker.run_chunk(task)
        row=dict(alias=point.decoder_alias,d=point.distance,p=point.physical_error_rate,
                 shots=task.shot_count,metrics={})
        for name,values in new.metrics.items():
            saved=pq.read_table(folder/f'{name}.parquet')[name].to_pylist()[:task.shot_count]
            def serialize(a):
                a=np.ma.asarray(a)
                return [None if masked else val.item() for val,masked in zip(a.data,np.ma.getmaskarray(a))]
            current,legacy=serialize(values),serialize(old.metrics[name])
            assert saved==current,(row,name,saved,current)
            row['metrics'][name]=dict(new_matches_saved=True,
                old_differences=sum(a!=b for a,b in zip(saved,legacy)))
        replay.append(row)
    write('calibration_replay.json',replay)
    print('REPLAY',len(replay),'points; old differences',sum(v['old_differences'] for r in replay for v in r['metrics'].values()),flush=True)

    structure=[]
    for d in (5,7,9):
        c=code(d);plan=c.dem_manager.global_projection;coords=c.circuit.get_detector_coordinates()
        bp_h,priors=c.bp_decoder._prepare_bp_inputs()
        assert (bp_h!=plan.H).nnz==0
        structure.append(dict(d=d,detectors=dict(Counter(str(a[3]) for a in coords.values())),
            global_shape=plan.H.shape,global_priors=np.unique(priors).tolist(),
            mixed=sum(len({coords[int(j)][3] for j in plan.H[:,k].nonzero()[0]})==2 for k in range(len(priors))),
            noise=[(i.name,i.gate_args_copy(),len(i.targets_copy())) for i in c.circuit.flattened()
                   if i.name.startswith(('DEPOLARIZE','X_ERROR','Z_ERROR'))]))
    write('structure.json',structure)

    summaries=[]
    for sample,p in [('physical',.03),('paired',.05)]:
        z=np.load(ARCHIVE/f'{sample}_inputs.npz');det=z['detectors'];obs=z['observables']
        c=code(p=p)
        ordinary=c.decode(det,check_validity=True)
        for method in ('min_sum','product_sum'):
            previous=np.load(ARCHIVE/f'{sample}_{method}.npz')
            pred,extra=c.decode(det,bp_predecoding=True,bp_prms=dict(max_iter=20,bp_method=method,schedule='parallel'),
                metrics=['logical_error'],actual_observables=obs,check_validity=True)
            conv=extra['bp_converged'];fail=pred!=obs;oldfail=previous['prediction']!=obs
            np.testing.assert_array_equal(conv,previous['converged'])
            np.testing.assert_array_equal(extra['logical_error'].compressed(),fail[~conv])
            np.savez_compressed(OUT/f'{sample}_{method}.npz',prediction=pred,converged=conv,ordinary=ordinary)
            row=dict(sample=sample,method=method,shots=len(det),ordinary_failures=int((ordinary!=obs).sum()),
                old_failures=int(oldfail.sum()),new_failures=int(fail.sum()),
                old_new_prediction_differences=int((pred!=previous['prediction']).sum()),
                old_wrong_new_right=int((oldfail&~fail).sum()),old_right_new_wrong=int((~oldfail&fail).sum()),
                converged=int(conv.sum()),converged_failures=int((conv&fail).sum()),
                saved_failures=int((~conv&fail).sum()),bad_indices=np.flatnonzero(fail).tolist())
            if sample=='physical':
                row.update(single_failures=int(fail[:57].sum()),double_failures=int(fail[57:].sum()))
            summaries.append(row);write('paired_comparison.json',summaries)
            print('PAIRED',row,flush=True)

    paths=[inspect.getfile(ColorCode),inspect.getfile(GlobalDemProjection),inspect.getfile(worker)]
    from color_code_stim.decoders.belief_concat_matching_decoder import BeliefConcatMatchingDecoder
    from color_code_stim.decoders.bp_decoder import BPDecoder
    paths.extend([inspect.getfile(BeliefConcatMatchingDecoder),inspect.getfile(BPDecoder)])
    from color_code_stim.decoders.concat_matching_decoder import ConcatMatchingDecoder
    from color_code_stim.decoders.color_correlated_decoding import CandidateEvaluator
    from color_code_stim.decoders.matching_cache import MatchingCache
    from color_code_stim.dem_utils.dem_decomp import DemDecomp
    import pymatching._cpp_pymatching as backend
    paths.extend(inspect.getfile(obj) for obj in
                 (ConcatMatchingDecoder,CandidateEvaluator,MatchingCache,DemDecomp,backend))
    write('provenance.json',dict(run=str(RUN),log=LOG['global_bp_predecoding'],
        versions={n:md.version(n) for n in ('numpy','scipy','stim','ldpc','pymatching')},
        sha256={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths}))
