from pathlib import Path
from math import comb
import json, hashlib, importlib.metadata as md, subprocess
import numpy as np
from color_code_stim import ColorCode
out=Path(__file__).parent
z=np.load(out/'exact_d5_syndrome_counts.npz'); counts=z['counts']; syn=z['syndromes']
assert counts.sum()==2**19
assert np.array_equal(counts.sum(axis=(0,1)),[comb(19,k) for k in range(20)])
c=ColorCode(d=5,rounds=1,p_depol=.03,temp_bdry_type='Z',color_correlated_weight_basis='original_dem')
plan=c.dem_manager.global_projection
keys={sum(int(x)<<j for j,x in enumerate(s)):i for i,s in enumerate(syn)}
cols=[sum(1<<int(j) for j in plan.H[:,i].nonzero()[0]) for i in range(19)]
obs=plan.observables.toarray().ravel().astype(int)
independent=np.zeros_like(counts)
# Independent Gray-code XOR update; does not use a matrix product or the saved inverse index.
mask=0;logical=0;weight=0;previous=0
for i in range(1<<19):
 gray=i^(i>>1)
 if i:
  change=gray^previous;j=change.bit_length()-1
  mask^=cols[j];logical^=int(obs[j]);weight+=1 if gray&change else -1
 independent[keys[mask],logical,weight]+=1
 previous=gray
assert np.array_equal(counts,independent)
structure=[]
for d in (5,7,9):
 c=ColorCode(d=d,rounds=1,p_depol=.03,temp_bdry_type='Z',color_correlated_weight_basis='original_dem');p=c.dem_manager.global_projection;m=c.dem_manager
 assert (p.H!=m.H).nnz==0 and (p.observables!=m.obs_matrix).nnz==0
 np.testing.assert_array_equal(p.priors,m.probs_xz)
 assert all(len(s)==1 for s in p.sources)
 coords=p.dem.get_detector_coordinates(); active=np.flatnonzero(p.H.getnnz(axis=1))
 assert all(coords[int(i)][3]==2 for i in active)
 structure.append(dict(d=d,shape=p.H.shape,active_rows=len(active),pauli_metadata=2,global_equals_css=True,projection_groups_singleton=True))
base=Path('/home/quantum_teresheys/workspace/color_code_softoutput_bp_global')
files=[base/'external_libs/color-code-stim/src/color_code_stim'/x for x in ['decoders/bp_decoder.py','decoders/belief_concat_matching_decoder.py','decoders/concat_matching_decoder.py','dem_utils/global_dem.py','dem_utils/dem_manager.py','decoders/matching_cache.py']]
result=dict(independent_gray_code_enumeration='passed',pattern_count=2**19,structure=structure,versions={name:md.version(name) for name in ('numpy','scipy','stim','ldpc','pymatching')},sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},commits={str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (base,base/'external_libs/color-code-stim',base/'external_libs/PyMatching')})
(out/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
