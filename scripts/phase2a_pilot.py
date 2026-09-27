"""Bounded data-only pipeline pilot. Run only after the documented M0–M5 gates."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import platform
import resource
import subprocess
from time import perf_counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pymatching
import stim
from color_code_stim import ColorCode
from color_code_stim.noise_model import NoiseModel
from color_code_stim.soft_output.results import GROWTH_CONVENTION
from phase2a_diagnostics import validate_pairing,paired_detector_shots,retained_curve,binned_ler

ROOT = Path(__file__).resolve().parents[1]


def repository_state(name):
    path = ROOT/'external_libs'/name
    sha = subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
    dirty = subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True).strip()
    if dirty:
        raise RuntimeError(f'{name} has uncommitted changes; freeze a reviewable source commit before collecting pilot data')
    return sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'src/phase2a_pilot.json')
    parser.add_argument('--output',type=Path,default=ROOT/'implementation_artifacts/pilot')
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if config['rounds'] != 1 or config['circuit_type'] != 'tri' or config['shots'] > 10000:
        raise ValueError('This runner is limited to the authorized small single-round pilot')
    if any(d not in (3,5,7) for d in config['distances']):
        raise ValueError('Only validated pilot distances 3,5,7 are allowed')
    if not config['shots'] > 0 or any(not 0 < p < .5 for p in config['physical_error_rates']):
        raise ValueError('Invalid shots or bit-flip probability')
    out = args.output
    if out.exists() and any(out.iterdir()):
        raise FileExistsError('Choose an empty output directory; pilot results are not overwritten')
    shas = {name:repository_state(name) for name in ('PyMatching','color-code-stim')}
    out.mkdir(parents=True,exist_ok=True)
    manifest = dict(config=config,repositories=shas,python=platform.python_version(),
                    numpy=np.__version__,stim=stim.__version__,pymatching=pymatching.__version__,
                    growth_convention=GROWTH_CONVENTION,bound_certified=False,
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    diagnostics_sha256=hashlib.sha256((ROOT/'scripts/phase2a_diagnostics.py').read_bytes()).hexdigest(),
                    ties='Stable shot-order tie break, independent of failure labels',
                    scope='Pipeline validation only; no posterior or full-decoder gap claim')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    rows, summaries = [], []
    for d in config['distances']:
        for p in config['physical_error_rates']:
            seed = config['seed']+len(summaries)
            tag = f'd{d}_p{p:g}'
            kwargs = dict(d=d,rounds=1,circuit_type='tri',cnot_schedule=config['cnot_schedule'],
                          noise_model=NoiseModel(bitflip=p))
            t = perf_counter()
            cc = ColorCode(**kwargs)
            _ = cc.dem_manager
            construction = perf_counter()-t
            dets, actual = cc.sample(config['shots'],seed=seed)
            start = perf_counter()
            baseline, off = cc.decode(dets,full_output=True)
            ordinary_pipeline = perf_counter()-start
            # Configure the static stage-2 matchers explicitly to separate setup.
            from color_code_stim.soft_output.pymatching_backend import Stage2Backend
            start = perf_counter()
            for c in 'rgb':
                cc.concat_matching_decoder._swim_backends[c] = Stage2Backend(cc.dem_manager,c)
            topology_setup = perf_counter()-start
            start = perf_counter()
            prediction, on = cc.decode(dets,full_output=True,compute_swim_distance=True)
            swim_pipeline = perf_counter()-start
            np.testing.assert_array_equal(prediction,baseline)
            for field in ('best_colors','weights','error_preds'):
                np.testing.assert_array_equal(on[field],off[field])
            assert np.isfinite(on['swim_distances_by_color']).all()
            assert (on['swim_distances_by_color'] >= 0).all()
            cmp = ColorCode(**kwargs,comparative_decoding=True)
            pairing = validate_pairing(cc.circuit,cmp.circuit)
            cmp_pred, cmp_extra = cmp.decode(paired_detector_shots(dets,actual),full_output=True)
            failure = prediction != actual
            cmp_failure = cmp_pred != actual
            selected = on['selected_swim_distance']
            gaps = cmp_extra['logical_gaps']
            assert np.isfinite(gaps).all()
            for i in range(config['shots']):
                record = dict(shot_id=f'{tag}:{i}',shot_index=i,d=d,p=p,seed=seed,
                              actual_observable=int(actual[i]),predicted_observable=int(prediction[i]),
                              failure=int(failure[i]),best_color='rgb'[int(on['best_colors'][i])],
                              ordinary_weight=float(on['weights'][i]),selected_phi=float(selected[i]),
                              comparative_prediction=int(cmp_pred[i]),comparative_failure=int(cmp_failure[i]),
                              comparative_logical_gap=float(gaps[i]),pymatching_sha=shas['PyMatching'],
                              color_code_stim_sha=shas['color-code-stim'])
                for j,c in enumerate(on['color_order']):
                    record[f'weight_{c}'] = float(on['stage2_weights_by_color'][i,j])
                    record[f'phi_{c}'] = float(on['swim_distances_by_color'][i,j])
                rows.append(record)
            fractions = config['acceptance_fractions']
            curve = retained_curve(selected,failure,fractions)
            comparative_curve = retained_curve(gaps,cmp_failure,fractions)
            bins = binned_ler(selected,failure)
            # Fair incremental stage-2 timing: same configured matcher/input,
            # excluding construction and stage-1 decoding in both measurements.
            timing = []
            for c in 'rgb':
                dec = cc.concat_matching_decoder
                stage1 = dec._decode_stage1(dets,c)
                masked = dets.copy()
                mask = np.ones(masked.shape[1],dtype=bool)
                mask[cc.detector_ids_by_color[c]] = False
                masked[:,mask] = False
                stage2 = np.concatenate((masked,stage1),axis=1)
                backend = dec._swim_backends[c]
                ordinary_times,soft_times = [],[]
                for repeat in range(config['timing_repeats']):
                    order = ('ordinary','soft') if repeat%2 == 0 else ('soft','ordinary')
                    for mode in order:
                        start = perf_counter()
                        if mode == 'ordinary':
                            backend.matcher.decode_batch(stage2,return_weights=True)
                            ordinary_times.append(perf_counter()-start)
                        else:
                            backend.matcher.decode_batch_with_soft_output(stage2)
                            soft_times.append(perf_counter()-start)
                ordinary_time,soft_time = map(float,(np.median(ordinary_times),np.median(soft_times)))
                timing.append(dict(color=c,ordinary_seconds=ordinary_time,soft_seconds=soft_time,
                                   incremental_us_per_shot=(soft_time-ordinary_time)/config['shots']*1e6))
            summary = dict(d=d,p=p,shots=config['shots'],seed=seed,failures=int(failure.sum()),
                           comparative_failures=int(cmp_failure.sum()),pairing=pairing,
                           median_success=float(np.median(selected[~failure])) if (~failure).any() else None,
                           median_failure=float(np.median(selected[failure])) if failure.any() else None,
                           bins=bins,retained_curve=curve,comparative_curve=comparative_curve,
                           construction_seconds=construction,topology_setup_seconds=topology_setup,
                           ordinary_pipeline_seconds=ordinary_pipeline,swim_pipeline_seconds=swim_pipeline,
                           stage2_timing=timing,process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            summaries.append(summary)
            # Persist each completed batch before plotting so diagnostics errors
            # cannot discard valid paired-shot data.
            with (out/'shots.csv').open('w',newline='') as f:
                writer = csv.DictWriter(f,fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
            (out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
            fig,ax = plt.subplots(2,2,figsize=(10,7),constrained_layout=True)
            ax[0,0].hist(selected,bins=12,color='steelblue');ax[0,0].set(title='Selected swim distribution',xlabel='Swim distance',ylabel='Shots')
            for mask,label in ((~failure,'Success'),(failure,'Failure')):
                if mask.any(): ax[0,1].hist(selected[mask],bins=12,histtype='step',label=label)
            ax[0,1].legend();ax[0,1].set(title='Conditioned distributions',xlabel='Swim distance',ylabel='Shots')
            x = [(b['lower']+b['upper'])/2 for b in bins]
            y = np.array([b['ler'] for b in bins])
            ax[1,0].errorbar(x,y,yerr=[y-np.array([b['low'] for b in bins]),np.array([b['high'] for b in bins])-y],fmt='o')
            ax[1,0].set(title='Binned conditional LER (95% Wilson)',xlabel='Swim distance',ylabel='Logical error rate')
            for points,label in ((curve,'Swim / ordinary decoder'),(comparative_curve,'Comparative gap / comparative decoder')):
                ax[1,1].plot([b['acceptance'] for b in points],[b['ler'] for b in points],'o-',label=label)
            ax[1,1].legend(fontsize=8);ax[1,1].set(title='Paired shots at matched acceptance',xlabel='Retained fraction',ylabel='Conditional LER')
            fig.suptitle(f'Pipeline pilot: d={d}, p={p}, {config["shots"]} shots; uncertified growth convention')
            fig.savefig(out/f'{tag}.png',dpi=140);plt.close(fig)
            print(f'{tag}: {int(failure.sum())}/{config["shots"]} ordinary failures; {int(cmp_failure.sum())} comparative',flush=True)
    with (out/'shots.csv').open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    print(f'Saved {len(rows)} paired shots in {out}')


if __name__ == '__main__':
    main()
