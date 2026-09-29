from pathlib import Path
import json
import numpy as np
from color_code_stim import ColorCode
OUT=Path(__file__).parent
c=ColorCode(d=5,rounds=2,p_depol=.05,temp_bdry_type='Z',perfect_first_syndrome_extraction=True,color_correlated_weight_basis='original_dem')
D,O=c.sample(2048,seed=2026092922)
ordinary=c.decode(D,check_validity=True)
np.savez_compressed(OUT/'paired_inputs.npz',detectors=D,observables=O,ordinary=ordinary)
rows=[dict(method='ordinary',shots=len(D),failures=int((ordinary!=O).sum()))]
for name,method,scale in [('min_sum','min_sum',1.),('product_sum','product_sum',1.),('min_sum_scale_0.625','min_sum',.625)]:
 pred,ex=c.decode(D,bp_predecoding=True,bp_prms=dict(max_iter=20,schedule='parallel',bp_method=method,ms_scaling_factor=scale),metrics=['logical_error'],actual_observables=O,check_validity=True)
 conv=ex['bp_converged'];fail=pred!=O
 assert np.array_equal(ex['logical_error'].compressed(),fail[~conv])
 row=dict(method=name,shots=len(D),failures=int(fail.sum()),converged=int(conv.sum()),converged_failures=int((fail&conv).sum()),saved_failures=int((fail&~conv).sum()),rescued=int(((ordinary!=O)&~fail).sum()),worsened=int(((ordinary==O)&fail).sum()))
 rows.append(row);print(row,flush=True)
 np.savez_compressed(OUT/f'paired_{name}.npz',prediction=pred,converged=conv)
 (OUT/'paired_results.json').write_text(json.dumps(rows,indent=2))
