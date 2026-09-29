from pathlib import Path
from itertools import combinations
from collections import Counter
import json, hashlib
import numpy as np
import pyarrow.parquet as pq
import stim
from color_code_stim import ColorCode
from ldpc import BpDecoder

OUT=Path(__file__).parent
RUN=Path('/home/quantum_teresheys/workspace/color_code_softoutput/results/bpmatching/26_09_29_21_59_45_9926fe3c')
CFG=json.loads((RUN/'run_log.json').read_text())['config']
def code(d,p):
 return ColorCode(**CFG['color_code_options'],d=d,rounds=2,p_depol=p,circuit_type='tri',cnot_schedule='tri_optimal')

saved=[]
for folder in sorted(RUN.glob('decoder*')):
 kv=dict(item.split('=',1) for item in folder.name.split(','))
 vals=pq.read_table(folder/'logical_error.parquet').column('logical_error').to_pylist()
 row=dict(kv,shots=len(vals),failures=sum(v is True for v in vals),nulls=sum(v is None for v in vals))
 if (folder/'bp_converged.parquet').exists():
  conv=pq.read_table(folder/'bp_converged.parquet').column('bp_converged').to_numpy()
  assert np.array_equal(conv,[v is None for v in vals])
 saved.append(row)
(OUT/'saved_counts.json').write_text(json.dumps(saved,indent=2))
print('SAVED',[(r['decoder_alias'],r['d'],r['p'],r['failures'],r['nulls']) for r in saved],flush=True)

structure=[]
for d in (5,7,9):
 c=code(d,.03);proj=c.dem_manager.global_projection;coords=c.circuit.get_detector_coordinates()
 h,p=c.bp_decoder._prepare_bp_inputs()
 assert (h!=proj.H).nnz==0
 row=dict(d=d,detectors=dict(Counter('X' if a[3]==0 else 'Z' for a in coords.values())),global_shape=h.shape,global_mechanisms=len(p),mixed=sum({coords[int(j)][3] for j in h[:,i].nonzero()[0]}=={0,2} for i in range(len(p))),noise=[(x.name,x.gate_args_copy(),len(x.targets_copy())) for x in c.circuit.flattened() if x.name.startswith(('DEPOLARIZE','X_ERROR','Z_ERROR'))])
 structure.append(row)
(OUT/'structure.json').write_text(json.dumps(structure,indent=2));print('STRUCTURE',structure,flush=True)

# Physical Pauli-to-detector/observable maps obtained by fault insertion in Stim,
# independently of the DEM parser and CSS projection.
c=code(5,.03);flat=c.circuit.flattened()
noise_ids=[i for i,x in enumerate(flat) if x.name=='DEPOLARIZE1'];assert len(noise_ids)==1
idx=noise_ids[0];qids=[t.value for t in flat[idx].targets_copy()]
labels=[];dets=[];obs=[]
for q in qids:
 for pauli in ('X','Y','Z'):
  injected=flat[:idx]+stim.Circuit(f'{pauli}_ERROR(1) {q}')+flat[idx+1:]
  dd,oo=injected.compile_detector_sampler(seed=718).sample(3,separate_observables=True)
  assert np.all(dd==dd[0]) and np.all(oo==oo[0])
  labels.append((q,pauli));dets.append(dd[0]);obs.append(oo[0,0])
dets=np.array(dets);obs=np.array(obs)
proj=c.dem_manager.global_projection
physical_keys=[tuple(np.r_[d,o]) for d,o in zip(dets,obs)]
global_keys=[tuple(np.r_[proj.H[:,i].toarray().ravel(),proj.observables[:,i].toarray().ravel()]) for i in range(len(proj.priors))]
assert len(set(physical_keys))==len(global_keys)==57
assert set(physical_keys)==set(global_keys)
source_ids=np.array([global_keys.index(k) for k in physical_keys])
pairs=np.array([(i,j) for i,j in combinations(range(len(labels)),2) if labels[i][0]!=labels[j][0]])
D=np.vstack((dets,dets[pairs[:,0]]^dets[pairs[:,1]]));O=np.r_[obs,obs[pairs[:,0]]^obs[pairs[:,1]]]
np.savez_compressed(OUT/'physical_inputs.npz',detectors=D,observables=O,source_ids=source_ids,pairs=pairs,labels=np.array(labels,dtype=str))
ordinary=c.decode(D,check_validity=True)
rows=[]
for name,bp_params in [('min_sum',dict(bp_method='min_sum')),('product_sum',dict(bp_method='product_sum')),('min_sum_scale_0.625',dict(bp_method='min_sum',ms_scaling_factor=.625))]:
 params=dict(max_iter=20,schedule='parallel',**bp_params)
 pred,extra=c.decode(D,bp_predecoding=True,bp_prms=params,metrics=['logical_error'],actual_observables=O,check_validity=True)
 conv=extra['bp_converged'];bad=pred!=O
 # Direct ldpc oracle: verifies wrapper sends the full matrix and exact options.
 oracle=BpDecoder(proj.H.astype(np.uint8),error_channel=proj.priors,input_vector_type='syndrome',**params)
 for i in range(len(dets)):
  cc=oracle.decode(D[i]);assert bool(oracle.converge)==bool(conv[i])
  if conv[i]: assert bool((proj.observables@cc.astype(np.uint8))[0]%2)==bool(pred[i])
 row=dict(name=name,single_count=len(dets),pair_count=len(pairs),ordinary_single_fail=int(np.sum(ordinary[:57]!=O[:57])),ordinary_pair_fail=int(np.sum(ordinary[57:]!=O[57:])),single_fail=int(bad[:57].sum()),pair_fail=int(bad[57:].sum()),converged=int(conv.sum()),converged_fail=int((bad&conv).sum()),fallback_fail=int((bad&~conv).sum()),bad_indices=np.flatnonzero(bad).tolist())
 rows.append(row);(OUT/'physical_results.json').write_text(json.dumps(rows,indent=2));print('PHYSICAL',row,flush=True)
 np.savez_compressed(OUT/f'physical_{name}.npz',prediction=pred,converged=conv,ordinary=ordinary)
