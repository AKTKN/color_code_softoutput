"""Exact center-occupation audit for all d=5 bit-flip errors.

Run from the repository root with the color_code_so Python interpreter.
"""
from pathlib import Path
import json
import sys
import subprocess

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(OUT.parent / 'bitflip_swim_unique_values_20260930'))
from audit import make_code
from color_code_stim.soft_output.topology import physical_error_map


def main():
    code = make_code()
    manager = code.dem_manager
    physical = physical_error_map(manager)
    qids = np.array([physical[j]['qid'] for j in range(19)])
    center = int(np.flatnonzero(qids == 20)[0])
    active = np.flatnonzero(manager.H.getnnz(axis=1))
    syndromes = np.zeros((512, manager.H.shape[0]), dtype=bool)
    syndromes[:, active] = (np.arange(512)[:, None] >> np.arange(9)) & 1
    masks = np.arange(1 << 19, dtype=np.uint32)
    errors = ((masks[:, None] >> np.arange(19)) & 1).astype(np.uint8)
    ids = ((errors @ manager.H[active].T) % 2) @ (1 << np.arange(9))
    parity = np.asarray(errors @ manager.obs_matrix.T).ravel() % 2
    weights = errors.sum(axis=1).astype(int)
    has_center = errors[:, center].astype(bool)

    # A known face stabilizer toggles the center while preserving both syndrome
    # and logical class. Verify the bijection on every physical error.
    stabilizer_qids = [4, 5, 12, 15, 20, 21]
    stab = np.isin(qids, stabilizer_qids).astype(np.uint8)
    assert not np.any(manager.H @ stab % 2)
    assert not np.any(manager.obs_matrix @ stab % 2)
    stab_mask = int(stab @ (1 << np.arange(19)))
    partner = masks ^ stab_mask
    np.testing.assert_array_equal(ids, ids[partner])
    np.testing.assert_array_equal(parity, parity[partner])
    np.testing.assert_array_equal(has_center, ~has_center[partner])

    rows, summaries, examples = [], [], []
    previous_score = None
    for p in (.02, .04):
        code = make_code(p=p)
        pred, extra = code.decode(syndromes, full_output=True,
                                 compute_swim_distance=True,
                                 return_candidate_data=True, check_validity=True)
        w = np.log((1-p)/p)
        raw = extra['class_min_swim_distance'] / w
        score = np.rint(raw).astype(int)
        np.testing.assert_allclose(raw, score, atol=1e-10)
        compact_pred, compact = code.decode(syndromes, metrics=['swim_distance'],
                                             compute_swim_distance=True)
        np.testing.assert_array_equal(pred, compact_pred)
        np.testing.assert_allclose(compact['swim_distance'], raw*w, atol=1e-10)
        if previous_score is not None:
            np.testing.assert_array_equal(score, previous_score)
        previous_score = score
        physical_score = score[ids]
        probability = p**weights * (1-p)**(19-weights)
        np.testing.assert_allclose(probability.sum(), 1.)
        even = physical_score % 2 == 0
        summaries.append(dict(p=p,
            probability_even=float(probability[even].sum()),
            probability_center_given_even=float(probability[even & has_center].sum()/probability[even].sum()),
            probability_even_given_center=float(probability[even & has_center].sum()/p),
            probability_even_given_no_center=float(probability[even & ~has_center].sum()/(1-p))))
        for k in np.unique(score):
            take = physical_score == k
            mass = probability[take].sum()
            for central in (False, True):
                subset = take & (has_center == central)
                best_weight = int(weights[subset].min())
                best_mask = int(np.flatnonzero(subset & (weights == best_weight))[0])
                rows.append(dict(p=p, swim_over_w=int(k), center=central,
                    syndromes=int(np.count_nonzero(score == k)),
                    error_configurations=int(subset.sum()),
                    probability=float(probability[subset].sum()),
                    conditional_center_state_probability=float(probability[subset].sum()/mass),
                    min_error_weight=best_weight,
                    example_qids=sorted(qids[errors[best_mask].astype(bool)].tolist())))
        if p == .04:
            for error_qids in ([16,17], [20], [4,5,12,15,21], [1,20]):
                err = np.isin(qids, error_qids).astype(np.uint8)
                mask = int(err @ (1 << np.arange(19)))
                sid = int(ids[mask])
                examples.append(dict(error_qids=error_qids, syndrome_id=sid,
                    detectors=np.flatnonzero(syndromes[sid]).tolist(),
                    physical_logical_class=int(parity[mask]),
                    final_qids=sorted(qids[extra['error_preds'][sid].astype(bool)].tolist()),
                    scalar_swim_over_w=int(score[sid]),
                    per_color_swim_over_w=(extra['swim_distances_by_color'][sid]/w).tolist()))

    # Counts conditioned on the minimum physical weight for each syndrome.
    minima = np.full(512, 20, dtype=int)
    np.minimum.at(minima, ids, weights)
    minimum_rows = []
    for sid in np.flatnonzero(previous_score % 2 == 0):
        take = (ids == sid) & (weights == minima[sid])
        minimum_rows.append(dict(syndrome_id=int(sid), swim_over_w=int(previous_score[sid]),
            minimum_weight=int(minima[sid]), center_minimum_count=int((take & has_center).sum()),
            no_center_minimum_count=int((take & ~has_center).sum())))
    pd.DataFrame(rows).to_csv(OUT/'center_statistics.csv', index=False)
    pd.DataFrame(minimum_rows).to_csv(OUT/'even_syndrome_minima.csv', index=False)
    result = dict(error_configurations=len(errors), syndromes=len(syndromes),
        central_qid=20, center_toggling_stabilizer=stabilizer_qids,
        verified_probabilities=[.02,.04], summaries=summaries, examples=examples,
        source_commits={str(path):subprocess.check_output(['git','-C',str(ROOT/path),'rev-parse','HEAD'],text=True).strip()
                        for path in [Path('.'),Path('external_libs/color-code-stim'),Path('external_libs/PyMatching')]})
    (OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == '__main__':
    main()
