import json, sys
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from color_code_stim import ColorCode
from scipy.special import expit
out=Path(__file__).parent
root=Path('/home/quantum_teresheys/workspace/color_code_softoutput')
rows=[]
for point in sorted((root/'results/bpmatching/26_09_29_20_26_20_449d8157').glob('decoder*')):
    kv=dict(x.split('=',1) for x in point.name.split(','))
    v=pq.read_table(point/'logical_error.parquet').column('logical_error').to_pylist()
    rows.append(dict(kv,failures=sum(x is True for x in v),nulls=sum(x is None for x in v),shots=len(v)))
(out/'saved_counts.json').write_text(json.dumps(rows,indent=2))
print('SAVED',json.dumps(rows),flush=True)
results=[]
for d in (5,7,9):
    c=ColorCode(d=d,rounds=1,p_depol=.03,temp_bdry_type='Z',color_correlated_weight_basis='original_dem')
    plan=c.dem_manager.global_projection
    det=plan.H.T.toarray().astype(bool); obs=plan.observables.T.toarray().ravel().astype(bool)
    pred,llr,conv=c.decode_bp(det,max_iter=20,bp_method='min_sum',schedule='parallel')
    ordinary=c.decode(det)
    bp,ex=c.decode(det,bp_predecoding=True,bp_prms=dict(max_iter=20,bp_method='min_sum',schedule='parallel'),metrics=['logical_error'],actual_observables=obs,check_validity=True)
    row=dict(d=d,H_shape=plan.H.shape, mechanisms=len(obs),converged=int(conv.sum()),ordinary_fail=int(np.sum(ordinary!=obs)),bp_fail=int(np.sum(bp!=obs)),bp_converged_fail=int(np.sum((bp!=obs)&conv)),bad_ids=np.flatnonzero(bp!=obs).tolist(),nonconv_above_half=int(np.sum(expit(-llr[~conv])>.5)),nonconv=int((~conv).sum()))
    print('SINGLE',json.dumps(row),flush=True);results.append(row)
(out/'single_mechanisms.json').write_text(json.dumps(results,indent=2))
