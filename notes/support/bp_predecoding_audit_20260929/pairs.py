from pathlib import Path
from itertools import combinations
from copy import copy
import json
import numpy as np
from scipy.special import expit
from color_code_stim import ColorCode
from color_code_stim.decoders.concat_matching_decoder import ConcatMatchingDecoder
from color_code_stim.stim_utils import dem_to_parity_check
out=Path(__file__).parent
results=[]
for d in (5,7,9):
 c=ColorCode(d=d,rounds=1,p_depol=.03,temp_bdry_type='Z',color_correlated_weight_basis='original_dem')
 plan=c.dem_manager.global_projection
 pairs=np.array(list(combinations(range(len(plan.priors)),2)))
 h=plan.H.T.toarray().astype(bool); o=plan.observables.T.toarray().ravel().astype(bool)
 det=h[pairs[:,0]]^h[pairs[:,1]]; obs=o[pairs[:,0]]^o[pairs[:,1]]
 ordinary=c.decode(det)
 for method in ('min_sum','product_sum'):
  bp,ex=c.decode(det,bp_predecoding=True,bp_prms=dict(max_iter=20,bp_method=method,schedule='parallel'),metrics=['logical_error'],actual_observables=obs,check_validity=True)
  pred,llr,conv=c.decode_bp(det,max_iter=20,bp_method=method,schedule='parallel')
  row=dict(d=d,method=method,pairs=len(pairs),ordinary_fail=int(np.sum(ordinary!=obs)),bp_fail=int(np.sum(bp!=obs)),converged=int(conv.sum()),converged_fail=int(np.sum((bp!=obs)&conv)),fallback_fail=int(np.sum((bp!=obs)&~conv)),nonconv_above_half_shots=int(np.sum(np.any(llr[~conv]<0,axis=1))),bad_pairs=pairs[bp!=obs].tolist())
  if d==5 and method=='min_sum':
   variants={name:bp.copy() for name in ('uncapped','prior_fallback')}
   for i in np.flatnonzero(~conv):
    variants['prior_fallback'][i]=ordinary[i]
    q=np.clip(expit(-llr[i]),1e-14,1-1e-14)
    local=copy(c.dem_manager);local.dem_xz=plan.project(q)
    local.H,local.obs_matrix,local.probs_xz=dem_to_parity_check(local.dem_xz)
    local.dems_decomposed=local._decompose_dems()
    variants['uncapped'][i]=ConcatMatchingDecoder(local,color_correlated_weight_basis='original_dem').decode(det[i:i+1],check_validity=True)[0]
   row['variants']={name:dict(fail=int(np.sum(p!=obs)),changed=int(np.sum(p!=bp))) for name,p in variants.items()}
   bad=np.flatnonzero(bp!=obs)
   if len(bad):
    i=int(bad[0]);row['example']=dict(pair=pairs[i].tolist(),detectors=np.flatnonzero(det[i]).tolist(),actual=bool(obs[i]),pred=bool(bp[i]),converged=bool(conv[i]),llrs=llr[i].tolist(),source_priors=plan.priors.tolist())
  results.append(row); print(json.dumps(row),flush=True)
  (out/'pairs.json').write_text(json.dumps(results,indent=2))
