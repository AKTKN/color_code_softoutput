"""Diagnostic only: fixed BP, compare XOR/sum aggregation on archived shots."""
import numpy as np
from audit import OUT,ARCHIVE,code,write

if __name__=='__main__':
    results=[]
    for sample,p in [('physical',.03),('paired',.05)]:
        z=np.load(ARCHIVE/f'{sample}_inputs.npz');det=z['detectors'];actual=z['observables']
        ref=np.load(OUT/f'{sample}_min_sum.npz')
        c=code(p=p);plan=c.dem_manager.global_projection
        def summed(q):
            return np.array([min(float(np.sum(np.asarray(q)[ids])),1-1e-14) for ids in plan.sources])
        plan.probabilities=summed
        pred,extra=c.decode(det,bp_predecoding=True,bp_prms=dict(bp_method='min_sum',max_iter=20,schedule='parallel'),
            metrics=['logical_error'],actual_observables=actual,check_validity=True)
        np.testing.assert_array_equal(extra['bp_converged'],ref['converged'])
        hybrid=np.where(ref['converged'],ref['prediction'],ref['ordinary'])
        row=dict(sample=sample,shots=len(det),xor_failures=int((ref['prediction']!=actual).sum()),
            sum_failures=int((pred!=actual).sum()),ordinary_fallback_failures=int((hybrid!=actual).sum()),
            rescued_by_sum=int(((ref['prediction']!=actual)&(pred==actual)).sum()),
            worsened_by_sum=int(((ref['prediction']==actual)&(pred!=actual)).sum()))
        results.append(row);write('aggregation_probe.json',results)
        np.savez_compressed(OUT/f'{sample}_sum.npz',prediction=pred,converged=extra['bp_converged'])
        print(row,flush=True)
