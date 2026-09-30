"""Recount artifacts and saved masks independently, record a distinguishing replay."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from audit import OUT,ARCHIVE,RUN,CONFIG,plan_points,point_directory_name,chunk_seed,worker,old_weight_rule,write

checked=0
for point in plan_points(CONFIG):
    folder=RUN/point_directory_name(point)
    error=pq.read_table(folder/'logical_error.parquet')
    assert error['shot_index'].to_pylist()==list(range(10000))
    if dict(point.decode_options).get('bp_predecoding'):
        conv=pq.read_table(folder/'bp_converged.parquet')['bp_converged'].to_numpy()
        np.testing.assert_array_equal(error['logical_error'].is_null().to_numpy(),conv)
    else:
        assert error['logical_error'].null_count==0
    checked+=1
for row in json.loads((OUT/'paired_comparison.json').read_text()):
    actual=np.load(ARCHIVE/f"{row['sample']}_inputs.npz")['observables']
    vals=np.load(OUT/f"{row['sample']}_{row['method']}.npz")
    failures=vals['prediction']!=actual
    assert int(failures.sum())==row['new_failures']
    assert int((failures&vals['converged']).sum())==row['converged_failures']
    assert np.flatnonzero(failures).tolist()==row['bad_indices']
for path,digest in json.loads((OUT/'provenance.json').read_text())['sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest

point=next(p for p in plan_points(CONFIG) if p.decoder_alias=='BP_MWPM' and p.distance==5 and p.physical_error_rate==.05)
task=worker.WorkerInput(point.point_id,0,0,10,chunk_seed(CONFIG.simulation.master_seed,point.point_id,0),point)
worker._CODE_CACHE.clear();new=worker.run_chunk(task)
with old_weight_rule():
    worker._CODE_CACHE.clear();old=worker.run_chunk(task)
saved=pq.read_table(RUN/point_directory_name(point)/'logical_error.parquet')['logical_error'].to_pylist()[:10]
details=[]
for i in range(10):
    if not new.metrics['bp_converged'][i] and bool(new.metrics['logical_error'][i])!=bool(old.metrics['logical_error'][i]):
        assert bool(new.metrics['logical_error'][i])==saved[i]
        details.append(dict(shot_index=i,saved=saved[i],new_rule=bool(new.metrics['logical_error'][i]),old_rule=bool(old.metrics['logical_error'][i])))
result=dict(saved_mask_and_shot_order_points=checked,source_hashes_unchanged=True,
    distinguishing_point=point_directory_name(point),distinguishing_shots=details,
    replay_scope='first calibration chunk only; adaptive later chunk sizes are not saved')
write('verification.json',result);print(result)
