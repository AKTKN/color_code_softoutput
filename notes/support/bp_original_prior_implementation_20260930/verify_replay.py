"""Replay the archived independent hybrid hypothesis through production BP."""
import argparse
import json
from pathlib import Path
import hashlib
import inspect
import numpy as np
from color_code_stim import ColorCode
from color_code_stim.decoders.belief_concat_matching_decoder import BeliefConcatMatchingDecoder

OUT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--reference-root',type=Path,default=OUT.parents[3]/'color_code_softoutput'/'notes/support/bp_stage2_original_prior_20260930')
args=parser.parse_args()
results=[]
for name,d,p in [('physical_d5',5,.03),('paired_d5',5,.05),('paired_d7',7,.05)]:
    z=np.load(args.reference_root/f'{name}.npz')
    code=ColorCode(d=d,rounds=2,p_depol=p,perfect_first_syndrome_extraction=True,
                  exclude_non_essential_pauli_detectors=False,temp_bdry_type='Z')
    predicted,extra=code.decode(z['detectors'],bp_predecoding=True,
        bp_prms=dict(bp_method='min_sum',max_iter=20,schedule='parallel'),
        metrics=['logical_error'],actual_observables=z['observables'],check_validity=True)
    np.testing.assert_array_equal(predicted,z['stage2_and_selection'])
    np.testing.assert_array_equal(extra['bp_converged'],z['converged'])
    np.testing.assert_array_equal(extra['logical_error'].compressed(),
        (predicted!=z['observables'])[~z['converged']])
    row=dict(name=name,shots=len(predicted),failures=int((predicted!=z['observables']).sum()),
             independent_reference_prediction_equality=True,
             converged_prediction_equality=True)
    results.append(row);print(row,flush=True)
    (OUT/'replay.json').write_text(json.dumps(results,indent=2)+'\n')
path=inspect.getfile(BeliefConcatMatchingDecoder)
(OUT/'provenance.json').write_text(json.dumps(dict(reference_root=str(args.reference_root),
    bp_version=code.belief_concat_matching_decoder.get_state()['version'],
    sha256={path:hashlib.sha256(Path(path).read_bytes()).hexdigest()}),indent=2)+'\n')
