from pathlib import Path
import json,hashlib,subprocess,importlib.metadata as md
import numpy as np
from ldpc import BpDecoder
from color_code_stim import ColorCode
OUT=Path(__file__).parent
z=np.load(OUT/'physical_inputs.npz');D=z['detectors'];O=z['observables']
c=ColorCode(d=5,rounds=2,p_depol=.03,temp_bdry_type='Z',perfect_first_syndrome_extraction=True,color_correlated_weight_basis='original_dem');proj=c.dem_manager.global_projection
checks=[]
for name,method,scale in [('min_sum','min_sum',1.),('product_sum','product_sum',1.),('min_sum_scale_0.625','min_sum',.625)]:
 data=np.load(OUT/f'physical_{name}.npz')
 oracle=BpDecoder(proj.H.astype(np.uint8),error_channel=proj.priors,input_vector_type='syndrome',max_iter=20,bp_method=method,schedule='parallel',ms_scaling_factor=scale)
 assert oracle.ms_scaling_factor==scale
 for i in range(len(D)):
  correction=oracle.decode(D[i]).astype(np.uint8)
  assert bool(oracle.converge)==bool(data['converged'][i])
  if oracle.converge:
   assert np.array_equal((proj.H@correction)%2,D[i])
   assert bool((proj.observables@correction)[0]%2)==bool(data['prediction'][i])
 checks.append(dict(method=name,direct_ldpc_convergence_and_prediction_checks=len(D)))
base=Path('/home/quantum_teresheys/workspace/color_code_softoutput_bp_global')
old=json.loads((OUT.parent/'bp_predecoding_audit_20260929/verification.json').read_text())
for path,digest in old['sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
result=dict(direct_ldpc=checks,sources_unchanged_since_first_audit=True,versions={n:md.version(n) for n in ('numpy','scipy','stim','ldpc','pymatching')},source_sha256=old['sha256'],commits={str(p):subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for p in (base,base/'external_libs/color-code-stim',base/'external_libs/PyMatching')},paired_seed=2026092922,paired_shots=2048)
(OUT/'verification.json').write_text(json.dumps(result,indent=2));print(result)
