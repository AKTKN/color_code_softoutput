"""Temporary in-process objective ablation; does not change any decoder file."""
from pathlib import Path
import json
from unittest.mock import patch
import numpy as np
import pymatching
from color_code_stim import ColorCode
from color_code_stim.decoders.matching_cache import MatchingCache,CompiledMatching
from color_code_stim.decoders.color_correlated_decoding import CandidateEvaluator
OUT=Path(__file__).parent
init=CandidateEvaluator.__init__
def negative_log_compile(structure,p):
 return CompiledMatching(structure,pymatching.Matching.from_check_matrix(structure.matrix,weights=-np.log(p)))
def negative_log_evaluator(self,manager,basis):
 init(self,manager,basis)
 for color in self._stage2_llr:
  self._stage2_llr[color]=-np.log(manager.dems_decomposed[color].probs[1])
 if self._original_llr is not None:self._original_llr=-np.log(manager.probs_xz)
rows=[]
with patch.object(MatchingCache,'compile',staticmethod(negative_log_compile)),patch.object(CandidateEvaluator,'__init__',negative_log_evaluator):
 for kind,p in [('physical',.03),('paired',.05)]:
  z=np.load(OUT/f'{kind}_inputs.npz');D=z['detectors'];O=z['observables']
  c=ColorCode(d=5,rounds=2,p_depol=p,temp_bdry_type='Z',perfect_first_syndrome_extraction=True,color_correlated_weight_basis='original_dem')
  pred,extra=c.decode(D,bp_predecoding=True,bp_prms=dict(max_iter=20,bp_method='min_sum',schedule='parallel'),metrics=['logical_error'],actual_observables=O,check_validity=True)
  conv=extra['bp_converged'];bad=pred!=O
  orig=np.load(OUT/f'{kind}_min_sum.npz')
  assert np.array_equal(conv,orig['converged'])
  row=dict(inputs=kind,count=len(D),failures=int(bad.sum()),converged_failures=int((bad&conv).sum()),fallback_failures=int((bad&~conv).sum()),changed=int((pred!=orig['prediction']).sum()))
  if kind=='physical':row.update(single_fail=int(bad[:57].sum()),pair_fail=int(bad[57:].sum()))
  rows.append(row);print(row,flush=True)
  (OUT/'weight_probe.json').write_text(json.dumps(rows,indent=2))
  np.savez_compressed(OUT/f'{kind}_neglog.npz',prediction=pred,converged=conv)
