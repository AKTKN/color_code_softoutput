from pathlib import Path
import json
import numpy as np
from color_code_stim import ColorCode
out=Path(__file__).parent
c=ColorCode(d=5,rounds=1,p_depol=.03,temp_bdry_type='Z',color_correlated_weight_basis='original_dem')
plan=c.dem_manager.global_projection
n=len(plan.priors)
assert n==19
patterns=((np.arange(1<<n,dtype=np.uint32)[:,None]>>np.arange(n))&1).astype(np.uint8)
syn=np.asarray((patterns@plan.H.T)%2,dtype=np.uint8)
obs=np.asarray((patterns@plan.observables.T)%2).ravel()
weight=patterns.sum(axis=1)
unique,inverse=np.unique(syn,axis=0,return_inverse=True)
counts=np.bincount((inverse*2+obs)*(n+1)+weight.astype(int),minlength=len(unique)*2*(n+1)).reshape(len(unique),2,n+1)
np.savez_compressed(out/'exact_d5_syndrome_counts.npz',syndromes=unique,counts=counts)
del patterns,syn,inverse,weight,obs
rows=[]
for physical in (.03,.05):
 c=ColorCode(d=5,rounds=1,p_depol=physical,temp_bdry_type='Z',color_correlated_weight_basis='original_dem')
 q=2*physical/3
 joint=counts@(q**np.arange(n+1)*(1-q)**(n-np.arange(n+1)))
 assert np.isclose(joint.sum(),1)
 for method in ('ordinary','min_sum','product_sum'):
  if method=='ordinary': pred=c.decode(unique);conv=np.zeros(len(unique),bool)
  else:
   pred,extra=c.decode(unique,bp_predecoding=True,bp_prms=dict(max_iter=20,bp_method=method,schedule='parallel'),metrics=['bp_converged'],check_validity=True)
   conv=extra['bp_converged']
  fail=joint[np.arange(len(unique)),1-pred.astype(int)]
  row=dict(d=5,p=physical,method=method,syndromes=len(unique),exact_ler=float(fail.sum()),converged_failure_mass=float(fail[conv].sum()),saved_failure_mass=float(fail[~conv].sum()),convergence_probability=float(joint[conv].sum()),ml_ler=float(joint.min(axis=1).sum()))
  rows.append(row);print(json.dumps(row),flush=True)
  (out/'exact_d5.json').write_text(json.dumps(rows,indent=2))
