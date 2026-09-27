"""Small reproducible M0 fixtures; run before changing decoder source."""
from pathlib import Path
import importlib.util
import json
import os
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'implementation_artifacts' / 'baseline'
SEED = 20260912
SHOTS = 64


def color_fixture():
    from color_code_stim import ColorCode
    from color_code_stim.noise_model import NoiseModel
    cc = ColorCode(d=3, rounds=1, circuit_type='tri', cnot_schedule='tri_optimal',
                   noise_model=NoiseModel(bitflip=0.05))
    dets, obs = cc.sample(SHOTS, seed=SEED)
    pred, extra = cc.decode(dets, full_output=True, check_validity=True)
    np.savez(OUT / 'color_d3.npz', detectors=dets, actual_observable=obs,
             predictions=pred, best_colors=extra['best_colors'],
             weights=extra['weights'], failures=pred != obs)
    print('color baseline:', SHOTS, 'shots,', int(np.count_nonzero(pred != obs)), 'failures')


def surface_fixture():
    # Execute the included example's actual main/circuit and sampler setup.
    # Replace only its billion-shot collector with one small seeded batch.
    sys.path.insert(0, str(ROOT / 'external_libs/PyMatching/SO_example'))
    import sampling_SE_surface_codes_SO as example
    import sinter
    from so_sampler import CompiledSOXSampler

    def small_collect(*, tasks, **kwargs):
        records = []
        for task in tasks:
            sampler = CompiledSOXSampler.from_task(task)
            sampler.sampler = task.circuit.compile_detector_sampler(seed=SEED)
            stats = sampler.sample(SHOTS)
            assert sum(stats.custom_counts.values()) == SHOTS - stats.discards
            assert stats.custom_counts
            records.append(dict(shots=stats.shots, errors=stats.errors,
                                discards=stats.discards, counts=dict(stats.custom_counts)))
            dets, obs = task.circuit.compile_detector_sampler(seed=SEED).sample(
                SHOTS, separate_observables=True)
            keep = ~np.any(dets & sampler._mask, axis=1)
            dets = dets[keep]
            pred, soft = sampler.decoder.decode_batch_soft_output(dets, return_weights=True)
            pred2, soft2 = sampler.decoder.decode_batch_soft_output(dets, return_weights=True)
            assert np.isfinite(soft).all()
            np.testing.assert_array_equal(pred, pred2)
            np.testing.assert_array_equal(soft, soft2)
            np.savez(OUT / 'surface_so.npz', detectors=dets, predictions=pred, soft_outputs=soft)
        (OUT / 'surface_summary.json').write_text(json.dumps(records, indent=2) + '\n')
        print('surface example:', records)
        return records

    original = sinter.collect
    previous = Path.cwd()
    try:
        sinter.collect = small_collect
        os.chdir(OUT)
        example.main()
    finally:
        sinter.collect = original
        os.chdir(previous)


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ['surface']:
        surface_fixture()
    else:
        color_fixture()
