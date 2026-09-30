"""Independent artifact recount and exhaustive checks of restored-prior stage 2."""
import json
import sys
import hashlib
from pathlib import Path
import numpy as np
from scipy.special import expit
from probe import OUT,ARCHIVE,BP,METHODS,code,write,mechanism_keys,stage1_keys
from color_code_stim.decoders.concat_matching_decoder import ConcatMatchingDecoder

checked=[]
for name in ('physical_d5','paired_d5','paired_d7'):
    data=np.load(OUT/f'{name}.npz');summary=json.loads((OUT/f'{name}.json').read_text())
    actual=data['observables'];conv=data['converged'];current=data['current']!=actual
    assert len(actual)==summary['shots']
    for method in METHODS:
        fail=data[method]!=actual;record=summary['methods'][method]
        assert int(fail.sum())==record['failures']
        assert int((fail&~conv).sum())==record['fallback_failures']
        assert int((current&~fail).sum())==record['rescued']
        assert int((~current&fail).sum())==record['worsened']
        assert int(((data['ordinary']!=actual)&~fail).sum())==record['rescued_vs_ordinary']
        assert int(((data['ordinary']==actual)&fail).sum())==record['worsened_vs_ordinary']
        np.testing.assert_array_equal(data[method][conv],data['current'][conv])
    if name in ('physical_d5','paired_d5'):
        prefix=name.split('_')[0];old=np.load(ARCHIVE/f'{prefix}_inputs.npz')
        np.testing.assert_array_equal(data['detectors'],old['detectors'])
        np.testing.assert_array_equal(actual,old['observables'])
        previous=np.load(OUT.parent/'bp_negative_log_audit_20260929'/f'{prefix}_min_sum.npz')
        np.testing.assert_array_equal(data['current'],previous['prediction'])
    else:
        det,obs=code(7,.05).sample(4096,seed=2026093007)
        np.testing.assert_array_equal(det,data['detectors']);np.testing.assert_array_equal(obs,actual)
    checked.append(dict(name=name,shots=len(actual),all_counts_and_converged_predictions_match=True))

# Reuse the independent GF(2) affine-space enumerator from the preceding audit.
sys.path.insert(0,str(OUT.parent/'bp_negative_log_audit_20260929'))
from trace import exact_graph_minimum
data=np.load(OUT/'physical_d5.npz');bad=np.flatnonzero(data['current']!=data['observables'])
c=code(5,.03);base=c.dem_manager;plan=base.global_projection
decoder=ConcatMatchingDecoder(base,color_correlated_weight_basis='original_dem')
base_keys=mechanism_keys(base);lookup={k:j for j,k in enumerate(base_keys)}
_,llrs,conv=c.decode_bp(data['detectors'][bad],**BP);assert not conv.any()
stage_checks=0
for j,i in enumerate(bad):
    det=data['detectors'][i:i+1]
    local=base.with_dem(plan.project(expit(-llrs[j]),negative_log_weights=True))
    local_decoder=ConcatMatchingDecoder(local,color_correlated_weight_basis='original_dem')
    to_base=np.array([lookup[k] for k in mechanism_keys(local)])
    candidates=[]
    for color in 'rgb':
        bd=base.dems_decomposed[color];ld=local.dems_decomposed[color]
        mapping={k:n for n,k in enumerate(stage1_keys(bd,np.arange(len(base_keys))))}
        perm=np.array([mapping[k] for k in stage1_keys(ld,to_base)])
        first=local_decoder._decode_stage1(det,color)
        original_first=np.zeros_like(first);original_first[:,perm]=first
        second,_=decoder._decode_stage2(det,original_first,color)
        syndrome=det[0].copy()
        syndrome[np.setdiff1d(np.arange(det.shape[1]),base.detector_ids_by_color[color])]=False
        target=np.r_[syndrome,original_first[0]]
        exact_graph_minimum(bd.Hs[1],bd.probs[1],target,second[0])
        stage_checks+=1
        candidates.append((bd.map_errors_to_org_dem(second,stage=2).astype(np.uint8)%2)[0])
    candidates=np.array(candidates);cost=candidates@np.log((1-base.probs_xz)/base.probs_xz)
    labels=np.asarray((candidates@base.obs_matrix.T)%2).ravel()
    assert bool(labels[np.argmin(cost)])==bool(data['stage2_and_selection'][i])==bool(data['observables'][i])
for path,digest in json.loads((OUT/'provenance.json').read_text())['sha256'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
result=dict(datasets=checked,exhaustive_restored_prior_stage2_checks=stage_checks,
            previous_physical_failures_all_corrected=len(bad),production_source_hashes_unchanged=True)
write('verification.json',result);print(result)
