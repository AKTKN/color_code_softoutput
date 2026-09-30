from pathlib import Path
import json
from collections import Counter
from copy import copy
import numpy as np
from scipy.special import expit
from color_code_stim import ColorCode
from color_code_stim.decoders.concat_matching_decoder import ConcatMatchingDecoder
from color_code_stim.stim_utils import dem_to_parity_check
OUT=Path(__file__).parent
z=np.load(OUT/'physical_inputs.npz');D=z['detectors'];O=z['observables'];src=z['source_ids'];labels=z['labels'];pairs=z['pairs']
a=np.load(OUT/'physical_min_sum.npz');bad=np.flatnonzero(a['prediction']!=O)
c=ColorCode(d=5,rounds=2,p_depol=.03,temp_bdry_type='Z',perfect_first_syndrome_extraction=True,color_correlated_weight_basis='original_dem');plan=c.dem_manager.global_projection
corr,llr,conv=c.decode_bp(D[bad],max_iter=20,bp_method='min_sum',schedule='parallel')
assert not conv.any()
rows=[]
for j,i in enumerate(bad):
 q=np.minimum(expit(-llr[j]),.5)
 # Independently check CSS source grouping from the physical Pauli identities.
 expected_groups=set()
 for k in range(len(labels)//3):
  ix,iy,iz=src[3*k:3*k+3]
  expected_groups.add(frozenset((int(ix),int(iy))))
  expected_groups.add(frozenset((int(iz),int(iy))))
 assert {frozenset(map(int,s)) for s in plan.sources}==expected_groups
 expected=np.array([q[s[0]]+q[s[1]]-2*q[s[0]]*q[s[1]] for s in plan.sources])
 np.testing.assert_allclose(plan.probabilities(q),expected,atol=1e-15,rtol=1e-12)
 local=c.dem_manager.with_dem(plan.project(q));dec=ConcatMatchingDecoder(local,color_correlated_weight_basis='original_dem')
 pred,e=dec.decode(D[i:i+1],full_output=True,return_candidate_data=True,check_validity=True)
 assert pred[0]==a['prediction'][i]
 candidates=e['candidate_original_corrections'][0,:,0,:].astype(np.uint8)
 assert np.all((candidates@local.H.T)%2==D[i])
 candobs=np.asarray((candidates@local.obs_matrix.T)%2).ravel().astype(bool)
 score=candidates@np.log((1-local.probs_xz)/local.probs_xz)
 assert candobs[np.argmin(score)]==pred[0]
 # Prior-based candidate selection, aligning source identities by detector+observable.
 original=c.dem_manager
 def keys(m):
  return [tuple(np.r_[m.H[:,k].toarray().ravel(),m.obs_matrix[:,k].toarray().ravel()]) for k in range(len(m.probs_xz))]
 basekeys=keys(original);loc_keys=keys(local)
 physical_prior=np.array([original.probs_xz[basekeys.index(k)] for k in loc_keys])
 base_score=candidates@np.log((1-physical_prior)/physical_prior)
 # Uncap global and projected probabilities while preserving the current log-odds objective.
 raw=np.clip(expit(-llr[j]),1e-14,1-1e-14);uncap=copy(original);uncap.dem_xz=plan.project(raw)
 uncap.H,uncap.obs_matrix,uncap.probs_xz=dem_to_parity_check(uncap.dem_xz);uncap.dems_decomposed=uncap._decompose_dems()
 up=ConcatMatchingDecoder(uncap,color_correlated_weight_basis='original_dem').decode(D[i:i+1],check_validity=True)
 row=dict(index=int(i),faults=labels[pairs[i-57]].tolist(),actual=bool(O[i]),prediction=bool(pred[0]),detectors=np.flatnonzero(D[i]).tolist(),global_above_half=int((llr[j]<0).sum()),candidate_observables=candobs.tolist(),posterior_scores=score.tolist(),physical_prior_scores=base_score.tolist(),candidate_contains_correct=bool(np.any(candobs==O[i])),prior_selection_correct=bool(candobs[np.argmin(base_score)]==O[i]),uncapped_correct=bool(up[0]==O[i]))
 rows.append(row)
(OUT/'failure_traces.json').write_text(json.dumps(rows,indent=2))
summary=dict(failures=len(rows),all_candidates_wrong=sum(not r['candidate_contains_correct'] for r in rows),has_correct_candidate=sum(r['candidate_contains_correct'] for r in rows),rescored_prior_correct=sum(r['prior_selection_correct'] for r in rows),uncapped_correct=sum(r['uncapped_correct'] for r in rows),projection_group_audit='passed',direct_fallback_equality='passed',candidate_syndrome_and_selection_audit='passed')
(OUT/'trace_summary.json').write_text(json.dumps(summary,indent=2));print(summary)
