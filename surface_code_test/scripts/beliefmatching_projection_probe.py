"""Isolate posterior cap/aggregation on archived surface-code inputs.

BP, early termination, graph topology, -log edge weights and shots are fixed.
Production decoder sources are never modified.
"""
from pathlib import Path
import json
import numpy as np
import stim
import pymatching
from beliefmatching import BeliefMatching

BASE=Path('surface_code_test/results/beliefmatching_smoke_20260929')
OUT=BASE/'projection_probe'
OUT.mkdir(exist_ok=True)
results=[]
for d in (5,7):
 c=stim.Circuit((BASE/f'd{d}.stim').read_text());dem=stim.DetectorErrorModel((BASE/f'd{d}.dem').read_text())
 z=np.load(BASE/f'd{d}_shots.npz');D=z['detectors'];actual=z['actual']
 # Independent geometric sector projection, checked against the official map.
 coords=c.get_detector_coordinates()
 qc={i.targets_copy()[0].value:tuple(i.gate_args_copy()[:2]) for i in c if i.name=='QUBIT_COORDS'}
 x_anc={t.value for i in c if i.name=='H' for t in i.targets_copy()}
 xcoords={qc[q] for q in x_anc}
 sectors={i:'X' if tuple(a[:2]) in xcoords else 'Z' for i,a in coords.items()}
 for method in ('product_sum','min_sum'):
  decoder=BeliefMatching(dem,max_bp_iters=20,bp_method=method,schedule='parallel')
  m=decoder._matrices;A=m.hyperedge_to_edge_matrix.tocsr()
  keys=[(tuple(m.edge_check_matrix[:,k].nonzero()[0]),tuple(m.edge_observables_matrix[:,k].nonzero()[0])) for k in range(A.shape[0])]
  assert len(set(keys))==len(keys)
  expected=np.zeros(A.shape,dtype=np.uint8)
  for k in range(A.shape[1]):
   dets=m.check_matrix[:,k].nonzero()[0];obs=tuple(m.observables_matrix[:,k].nonzero()[0])
   for sector in ('X','Z'):
    key=(tuple(i for i in dets if sectors[int(i)]==sector),obs if sector=='Z' else ())
    if key!=((),()):expected[keys.index(key),k]=1
  assert np.array_equal(expected,A.toarray())
  groups=[A.indices[A.indptr[i]:A.indptr[i+1]] for i in range(A.shape[0])]
  # Per-edge product via vectorized grouped reduction; groups are nonempty.
  assert all(len(g)>0 for g in groups)
  variants=('official_sum','cap_sum','xor','cap_xor')
  predictions={v:np.zeros_like(actual) for v in variants}
  conv=np.zeros(len(D),bool);above_half=0
  for i,s in enumerate(D):
   official=decoder.decode(s)
   conv[i]=decoder._bpd.converge
   if conv[i]:
    for v in variants:predictions[v][i]=official
    continue
   q=1/(1+np.exp(decoder._bpd.log_prob_ratios))
   above_half+=int(np.any(q>.5))
   for variant in variants:
    qq=np.minimum(q,.5) if variant.startswith('cap_') else q
    if variant.endswith('sum'):p=A@qq
    else:p=(1-np.multiply.reduceat(1-2*qq[A.indices],A.indptr[:-1]))/2
    p=np.clip(p,1e-14,1-1e-14)
    matching=pymatching.Matching.from_check_matrix(m.edge_check_matrix,weights=-np.log(p),faults_matrix=m.edge_observables_matrix,use_virtual_boundary_node=True)
    predictions[variant][i]=matching.decode(s)
   assert np.array_equal(predictions['official_sum'][i],official)
  assert np.array_equal(predictions['official_sum'],z[method])
  assert np.array_equal(conv,z[method+'_converged'])
  official_bad=np.any(predictions['official_sum']!=actual,axis=1)
  row=dict(d=d,method=method,shots=len(D),fallback_shots=int((~conv).sum()),fallback_above_half=above_half,independent_CSS_projection_equals_official_map=True,variants={})
  for variant in variants:
   bad=np.any(predictions[variant]!=actual,axis=1)
   row['variants'][variant]=dict(failures=int(bad.sum()),converged_failures=int((bad&conv).sum()),fallback_failures=int((bad&~conv).sum()),changed_vs_official=int(np.any(predictions[variant]!=predictions['official_sum'],axis=1).sum()),rescued_vs_official=int((official_bad&~bad).sum()),worsened_vs_official=int((~official_bad&bad).sum()))
  results.append(row);(OUT/'results.json').write_text(json.dumps(results,indent=2))
  np.savez_compressed(OUT/f'd{d}_{method}.npz',**predictions,converged=conv)
  print(json.dumps(row),flush=True)
