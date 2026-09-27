"""Pilot statistics and explicit ordinary/comparative shot pairing."""
from math import sqrt
import numpy as np
import stim


def wilson(failures, total, z=1.959963984540054):
    if total <= 0 or not 0 <= failures <= total:
        raise ValueError('Wilson interval needs valid nonempty counts')
    p = failures/total
    denominator = 1+z*z/total
    center = (p+z*z/(2*total))/denominator
    half = z*sqrt(p*(1-p)/total+z*z/(4*total*total))/denominator
    return (0. if failures == 0 else max(0.,center-half),
            1. if failures == total else min(1.,center+half))


def retained_curve(scores, failures, fractions):
    scores, failures = np.asarray(scores), np.asarray(failures,dtype=bool)
    if scores.ndim != 1 or failures.shape != scores.shape or not np.isfinite(scores).all():
        raise ValueError('Scores/failures must be aligned finite one-dimensional arrays')
    # Deterministic shot-order tie break, independent of success/failure labels.
    order = np.argsort(-scores,kind='stable')
    records = []
    for fraction in fractions:
        if not 0 < fraction <= 1: raise ValueError('Acceptance fraction must be in (0,1]')
        count = max(1,int(np.floor(len(scores)*fraction))) if len(scores) else 0
        if not count: continue
        errors = int(failures[order[:count]].sum())
        low,high = wilson(errors,count)
        records.append(dict(acceptance=count/len(scores),accepted=count,failures=errors,
                            ler=errors/count,low=low,high=high))
    return records


def binned_ler(scores, failures, bins=6):
    scores, failures = np.asarray(scores), np.asarray(failures,dtype=bool)
    if scores.shape != failures.shape or scores.ndim != 1 or not len(scores):
        raise ValueError('Need aligned nonempty score and failure arrays')
    edges = np.linspace(scores.min(),scores.max(),bins+1)
    if edges[0] == edges[-1]: edges = np.array([edges[0],edges[0]+1])
    assignment = np.clip(np.searchsorted(edges,scores,side='right')-1,0,len(edges)-2)
    output = []
    for i in range(len(edges)-1):
        mask = assignment == i
        n = int(mask.sum())
        if not n: continue
        errors = int(failures[mask].sum())
        low,high = wilson(errors,n)
        output.append(dict(lower=float(edges[i]),upper=float(edges[i+1]),shots=n,
                           failures=errors,ler=errors/n,low=low,high=high))
    return output


def measurement_relations(circuit):
    """Canonical absolute record parities; include measurement location timing."""
    measurement_count = 0
    operations, detectors, observables = [], [], {}
    for instruction in circuit.flattened():
        if instruction.name in ('DETECTOR','OBSERVABLE_INCLUDE'):
            parity = set()
            for target in instruction.targets_copy():
                if not target.is_measurement_record_target:
                    raise ValueError('Only record-parity annotations are supported')
                index = measurement_count + target.value
                parity.symmetric_difference_update((index,))
            if instruction.name == 'DETECTOR':
                detectors.append(frozenset(parity))
            else:
                obs = int(instruction.gate_args_copy()[0])
                observables.setdefault(obs,set()).symmetric_difference_update(parity)
        else:
            operations.append(str(instruction))
            one = stim.Circuit()
            one.append(instruction)
            measurement_count += one.num_measurements
    return operations,detectors,{k:frozenset(v) for k,v in observables.items()}


def validate_pairing(ordinary, comparative):
    ops_a,dets_a,obs_a = measurement_relations(ordinary)
    ops_b,dets_b,obs_b = measurement_relations(comparative)
    if ops_a != ops_b or obs_a != obs_b or dets_b[:len(dets_a)] != dets_a:
        raise ValueError('Circuits do not share the same physical record and detector prefix')
    if ordinary.num_observables != 1 or len(dets_b) != len(dets_a)+1 or dets_b[-1] != obs_a[0]:
        raise ValueError('Comparative extra detector is not exactly the ordinary observable parity')
    return {'physical_operations_equal':True,'detector_prefix_equal':True,
            'extra_detector':'ordinary observable 0','ordinary_detectors':len(dets_a),
            'comparative_detectors':len(dets_b)}


def paired_detector_shots(detectors, observables):
    observables = np.asarray(observables).reshape(-1,1)
    return np.concatenate((detectors,observables),axis=1)
