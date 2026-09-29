"""Paired code-capacity smoke using the unmodified official BeliefMatching.

Requires official BeliefMatching source and upstream PyMatching on PYTHONPATH.
See results/beliefmatching_smoke_20260929/report.md for the pinned environment.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import importlib.metadata as metadata
import json
import subprocess
import time

import numpy as np
import scipy
from scipy.stats import binomtest
import stim
import pymatching
import beliefmatching
from beliefmatching import BeliefMatching


def circuit_for(d, p):
    base = stim.Circuit.generated('surface_code:rotated_memory_z', distance=d, rounds=2).flattened()
    data = [t.value for inst in base if inst.name == 'M' for t in inst.targets_copy()]
    assert len(data) == d*d and len(set(data)) == len(data)
    reference_end = next(i for i, inst in enumerate(base) if inst.name == 'MR') + 1
    noise = stim.Circuit()
    noise.append('DEPOLARIZE1', data, p)
    circuit = base[:reference_end] + noise + base[reference_end:]
    x_ancillas = {t.value for inst in base if inst.name == 'H' for t in inst.targets_copy()}
    coords = {inst.targets_copy()[0].value: tuple(inst.gate_args_copy()[:2])
              for inst in base if inst.name == 'QUBIT_COORDS'}
    x_coords = {coords[q] for q in x_ancillas}
    sectors = {i: 'X' if tuple(c[:2]) in x_coords else 'Z'
               for i, c in circuit.get_detector_coordinates().items()}
    assert set(sectors.values()) == {'X', 'Z'}
    return circuit, base, reference_end, data, sectors


def wilson(failures, shots):
    z=1.959963984540054
    f=failures/shots
    mid=(f+z*z/(2*shots))/(1+z*z/shots)
    radius=z*np.sqrt(f*(1-f)/shots+z*z/(4*shots*shots))/(1+z*z/shots)
    return [float(mid-radius),float(mid+radius)]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--shots', type=int, default=20000)
    parser.add_argument('--output',type=Path,default=Path('surface_code_test/results/beliefmatching_smoke_20260929'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    source=Path(beliefmatching.__file__).resolve().parents[2]
    provenance=dict(beliefmatching_commit=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip(),beliefmatching_path=beliefmatching.__file__,pymatching_path=pymatching.__file__,versions={n:metadata.version(n) for n in ('stim','ldpc','numpy','scipy','pymatching')},beliefmatching_source_sha256=hashlib.sha256((source/'src/beliefmatching/belief_matching.py').read_bytes()).hexdigest(),model='rotated Z memory, two perfect extraction rounds with one intervening data depolarization',p=.05,shots_per_distance=args.shots,distances=[5,7],max_bp_iters=20,schedule='parallel',min_sum_scale=1.0)
    assert metadata.version('pymatching') == '2.3.1'
    (args.output/'provenance.json').write_text(json.dumps(provenance,indent=2))
    results=[]
    for d in (5,7):
        circuit,base,reference_end,data,sectors=circuit_for(d,.05)
        dem=circuit.detector_error_model(decompose_errors=True)
        global_dem=circuit.detector_error_model(decompose_errors=False)
        joint=0;mechanisms=0
        for inst in global_dem:
            if inst.type!='error':continue
            mechanisms+=1
            kinds={sectors[t.val] for t in inst.targets_copy() if t.is_relative_detector_id()}
            joint+=kinds=={'X','Z'}
        assert joint>0
        zero_det,zero_obs=base.compile_detector_sampler(seed=123).sample(16,separate_observables=True)
        assert not zero_det.any() and not zero_obs.any()
        matching=pymatching.Matching.from_detector_error_model(dem)
        decoders={method:BeliefMatching(dem,max_bp_iters=20,bp_method=method,schedule='parallel')
                  for method in ('product_sum','min_sum')}
        # Independent deterministic physical single-Pauli response checks.
        single_failures=Counter()
        for q in data:
            for pauli in ('X','Y','Z'):
                fault=stim.Circuit(f'{pauli}_ERROR(1) {q}')
                injected=base[:reference_end]+fault+base[reference_end:]
                dd,oo=injected.compile_detector_sampler(seed=11).sample(2,separate_observables=True)
                assert np.array_equal(dd[0],dd[1]) and np.array_equal(oo[0],oo[1])
                single_failures['mwpm']+=int(np.any(matching.decode(dd[0])!=oo[0]))
                for method,decoder in decoders.items():
                    single_failures[method]+=int(np.any(decoder.decode(dd[0])!=oo[0]))
        assert not any(single_failures.values()),single_failures
        seed=2026092900+d
        detectors,actual=circuit.compile_detector_sampler(seed=seed).sample(args.shots,separate_observables=True)
        start=time.perf_counter();baseline=matching.decode_batch(detectors);baseline_seconds=time.perf_counter()-start
        baseline_fail=np.any(baseline!=actual,axis=1)
        row=dict(d=d,p=.05,shots=args.shots,seed=seed,detectors=dict(Counter(sectors.values())),global_mechanisms=mechanisms,joint_mechanisms=joint,single_fault_checks=3*d*d,single_fault_failures=dict(single_failures),mwpm_failures=int(baseline_fail.sum()),mwpm_ler=float(baseline_fail.mean()),mwpm_wilson95=wilson(int(baseline_fail.sum()),args.shots),mwpm_seconds=baseline_seconds,bp={})
        arrays=dict(detectors=detectors,actual=actual,mwpm=baseline)
        for method,decoder in decoders.items():
            predicted=np.zeros_like(actual);converged=np.zeros(args.shots,bool)
            start=time.perf_counter()
            for i,shot in enumerate(detectors):
                predicted[i]=decoder.decode(shot)
                converged[i]=decoder._bpd.converge
                if (i+1)%5000==0: print(f'd={d} {method} {i+1}/{args.shots}',flush=True)
            elapsed=time.perf_counter()-start
            fail=np.any(predicted!=actual,axis=1)
            rescued=int((baseline_fail&~fail).sum());worsened=int((~baseline_fail&fail).sum())
            assert int(fail.sum())==int(baseline_fail.sum())-rescued+worsened
            row['bp'][method]=dict(failures=int(fail.sum()),ler=float(fail.mean()),wilson95=wilson(int(fail.sum()),args.shots),converged=int(converged.sum()),converged_failures=int((fail&converged).sum()),fallback_failures=int((fail&~converged).sum()),rescued=rescued,worsened=worsened,paired_exact_pvalue=float(binomtest(rescued,rescued+worsened,.5).pvalue) if rescued+worsened else 1.,seconds=elapsed)
            arrays[method]=predicted;arrays[method+'_converged']=converged
        (args.output/f'd{d}.stim').write_text(str(circuit))
        (args.output/f'd{d}.dem').write_text(str(dem))
        np.savez_compressed(args.output/f'd{d}_shots.npz',**arrays)
        row['circuit_sha256']=hashlib.sha256(str(circuit).encode()).hexdigest()
        row['dem_sha256']=hashlib.sha256(str(dem).encode()).hexdigest()
        results.append(row);(args.output/'results.json').write_text(json.dumps(results,indent=2))
        print('RESULT',json.dumps(row),flush=True)

if __name__=='__main__':main()
