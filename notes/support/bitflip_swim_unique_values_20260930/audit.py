"""Bounded deterministic audit; never modifies the notebook or saved run.

Run with color_code_so Python from the repository root.
"""
from pathlib import Path
import json
import subprocess
import numpy as np
import pandas as pd
from color_code_stim import ColorCode, NoiseModel
from color_code_stim.soft_output.topology import physical_error_map
from color_code_stim.soft_output.reference import reference_metric
from pymatching.soft_output import metric_from_radii

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
RUN = ROOT / 'results/bitflip_swim/26_09_30_17_48_23_a219af0b'


def support(a):
    return np.flatnonzero(a).tolist()


def make_code(d=5, p=.04, comparative=False):
    return ColorCode(d=d, rounds=1, circuit_type='tri', cnot_schedule='tri_optimal',
                     temp_bdry_type='Z', noise_model=NoiseModel(bitflip=p),
                     comparative_decoding=comparative,
                     color_correlated_weight_basis='original_dem')


def main():
    archive = []
    for path in sorted(RUN.glob('*/*.parquet')):
        if path.stem not in ('swim_distance', 'logical_gap'):
            continue
        fields = dict(x.split('=') for x in path.parent.name.split(','))
        p = float(fields['p'])
        w = np.log((1-p)/p)
        values = pd.read_parquet(path)[path.stem].to_numpy()
        integers = np.rint(values/w).astype(int)
        counts = pd.Series(integers).value_counts().sort_index()
        archive.append(dict(distance=int(fields['d']), p=p, metric=path.stem,
                            counts={str(k): int(v) for k, v in counts.items()},
                            max_integer_error=float(np.max(abs(values/w-integers)))))

    c = make_code()
    m = c.dem_manager
    physical = physical_error_map(m)
    w = np.log(24)
    active = np.flatnonzero(m.H.getnnz(axis=1))
    assert len(active) == 9 and m.H.shape[1] == 19
    syndromes = np.zeros((512, m.H.shape[0]), dtype=bool)
    syndromes[:, active] = (np.arange(512)[:, None] >> np.arange(9)) & 1
    pred, extra = c.decode(syndromes, full_output=True, compute_swim_distance=True,
                           return_candidate_data=True, check_validity=True)
    compact_pred, compact = c.decode(syndromes, compute_swim_distance=True,
                                     metrics=['swim_distance'])
    assert np.array_equal(pred, compact_pred)
    np.testing.assert_allclose(compact['swim_distance'], extra['class_min_swim_distance'], atol=1e-12)
    plain = c.decode(syndromes)
    assert np.array_equal(pred, plain)
    reverse_pred, reverse = c.decode(syndromes[::-1], compute_swim_distance=True,
                                     metrics=['swim_distance'])
    assert np.array_equal(pred, reverse_pred[::-1])
    np.testing.assert_allclose(compact['swim_distance'], reverse['swim_distance'][::-1], atol=1e-12)

    comp = make_code(comparative=True)
    comp_s = np.column_stack([syndromes, np.zeros(512, dtype=bool)])
    # Audit the appended logical detector and the original physical mechanism order.
    np.testing.assert_array_equal(comp.dem_manager.H.toarray()[:-1], m.H.toarray())
    np.testing.assert_array_equal(comp.dem_manager.H.toarray()[-1], m.obs_matrix.toarray()[0])
    cpred, ce = comp.decode(comp_s, full_output=True, return_candidate_data=True,
                            check_validity=True)

    # Exhaustive independent physical oracle: all 2**19 errors, no decoder.
    masks = np.arange(1 << 19, dtype=np.uint32)
    errors = ((masks[:, None] >> np.arange(19)) & 1).astype(np.uint8)
    signatures = (errors @ m.H[active].T) % 2
    ids = signatures @ (1 << np.arange(9))
    parities = np.asarray(errors @ m.obs_matrix.T).ravel() % 2
    weights = errors.sum(axis=1)
    class_min = np.full(1024, 100, dtype=int)
    np.minimum.at(class_min, 2*ids+parities, weights)
    class_min = class_min.reshape(512, 2)
    # Minimum-weight representative, with binary mask order breaking ties.
    reps = np.full(512, 1 << 19, dtype=int)
    ok = weights == class_min.min(axis=1)[ids]
    np.minimum.at(reps, ids[ok], masks[ok])
    assert (reps < 1 << 19).all()
    exact_gap = np.abs(class_min[:, 1]-class_min[:, 0])
    assert np.all(exact_gap % 2 == 1)
    comp_counts = ce['candidate_original_corrections'].sum(axis=-1).min(axis=1).T
    assert np.all(comp_counts >= class_min)

    candidates = extra['candidate_original_corrections'][0]
    classes = np.asarray(candidates.reshape(-1, 19).astype(np.uint8) @ m.obs_matrix.T).reshape(3, 512) % 2
    swim = extra['swim_distances_by_color'] / w
    eligible = classes.T == pred[:, None]
    chosen = np.argmin(np.where(eligible, swim, np.inf), axis=1)
    scalar = extra['class_min_swim_distance'] / w
    np.testing.assert_allclose(scalar, swim[np.arange(512), chosen], atol=1e-12)
    even = np.rint(scalar).astype(int) % 2 == 0
    rows, details = [], {}
    worst_error = 0.
    for ci, color in enumerate('rgb'):
        backend = c.concat_matching_decoder._swim_backends[color]
        topo = backend.topology
        s2 = syndromes.copy()
        s2[:, [j for j in range(s2.shape[1]) if j not in m.detector_ids_by_color[color]]] = False
        s2 = np.column_stack([s2, extra['candidate_stage1_hypotheses'][0][ci]])
        result = backend.matcher.decode_batch_with_soft_output(s2, include_radii=True)
        edge_meta = {e.column_id: e for e in topo.edges}
        for si in range(512):
            ref = reference_metric(len(backend.config.node_map), topo.resolved_edges,
                                   topo.terminals, radii=result.radii[si])
            native_dist, native_cost = metric_from_radii(backend.config, result.radii[si])
            worst_error = max(worst_error, abs(ref.distance-result.soft_outputs[si, 0]))
            np.testing.assert_allclose(ref.distance, result.soft_outputs[si, 0], atol=1e-11)
            np.testing.assert_allclose(native_cost, [ref.residual_weights[e[0]] for e in topo.resolved_edges], atol=1e-11)
            path = np.zeros(topo.edges.__len__(), dtype=np.uint8)
            path[list(ref.edge_ids)] = 1
            original_path = m.dems_decomposed[color].map_errors_to_org_dem(path[None, :], stage=2)[0]
            assert not np.any(m.H @ original_path.astype(np.uint8) % 2)
            assert int((m.obs_matrix @ original_path.astype(np.uint8))[0] % 2) == 1
            corr = candidates[ci, si]
            opposite = corr ^ original_path.astype(bool)
            residual = [ref.residual_weights[j]/w for j in ref.edge_ids]
            details[f'{si}:{color}'] = dict(
                syndrome_id=si, color=color, stage2_defect_rows=support(s2[si]),
                radii_over_w=(result.radii[si]/w).tolist(),
                nodes=list(backend.config.node_map), terminals=list(topo.terminals),
                edges=[list(e) for e in topo.resolved_edges],
                edge_qubits={str(k): e.physical_qubit_id for k, e in edge_meta.items()},
                correction_qids=sorted(physical[j]['qid'] for j in support(corr)),
                path_edge_ids=list(ref.edge_ids),
                path_qids=[edge_meta[j].physical_qubit_id for j in ref.edge_ids],
                path_residual_over_w=residual,
                path_covered_over_w=len(ref.edge_ids)-sum(residual),
                witness_opposite_qids=sorted(physical[j]['qid'] for j in support(opposite)),
                witness_weight_difference=int(opposite.sum())-int(corr.sum()),
                swim_over_w=ref.distance/w,
            )
    for si in range(512):
        err = errors[reps[si]]
        rows.append(dict(syndrome_id=si, detectors=support(syndromes[si]),
            representative_qids=sorted(physical[j]['qid'] for j in support(err)),
            representative_weight=int(err.sum()),
            final_color='rgb'[extra['best_colors'][si]], swim_color='rgb'[chosen[si]],
            final_qids=sorted(physical[j]['qid'] for j in support(extra['error_preds'][si])),
            candidate_qids=[sorted(physical[j]['qid'] for j in support(candidates[jc, si])) for jc in range(3)],
            candidate_classes=classes[:, si].astype(int).tolist(),
            candidate_weights=candidates[:, si].sum(axis=1).astype(int).tolist(),
            swims_over_w=swim[si].tolist(), scalar_swim_over_w=float(scalar[si]),
            selected_swim_over_w=float(extra['selected_swim_distance'][si]/w),
            exact_class_weights=class_min[si].tolist(),
            comparative_class_weights=comp_counts[si].astype(int).tolist(),
            comparative_gap_over_w=float(ce['logical_gaps'][si]/w),
            exact_gap_over_w=int(exact_gap[si]),
            physical_error_class=int((err @ m.obs_matrix.T)[0] % 2),
            final_class=int(pred[si]), comparative_class=int(cpred[si])))

    examples = []
    for target in (4, 2):
        pool = [r for r in rows if abs(r['scalar_swim_over_w']-target)<1e-9]
        examples.append(min(pool, key=lambda r: (r['representative_weight'], r['syndrome_id'])))
    # An opposite-parity candidate must be excluded from the SWIM reduction.
    examples.append(rows[340])
    for r in examples:
        r['witness'] = details[f"{r['syndrome_id']}:{r['swim_color']}"]
        decomp = m.dems_decomposed[r['swim_color']]
        topo = c.concat_matching_decoder._swim_backends[r['swim_color']].topology
        native_errors = errors[:, [e.original_dem_ids[0] for e in topo.edges]]
        stage2_syndromes = np.asarray(native_errors @ decomp.Hs[1].T) % 2
        required = np.zeros(stage2_syndromes.shape[1], dtype=np.uint8)
        required[r['witness']['stage2_defect_rows']] = 1
        opposite_mask = ((parities != r['final_class'])
                         & np.all(stage2_syndromes == required, axis=1))
        best_opposite = int(weights[opposite_mask].min())
        r['fixed_fiber_opposite_weight'] = best_opposite
        r['fixed_fiber_gap_over_w'] = best_opposite-len(r['witness']['correction_qids'])
        opposite_class = 1-r['final_class']
        comp_corrections = ce['candidate_original_corrections'][opposite_class, :, r['syndrome_id']]
        best = comp_corrections[np.argmin(comp_corrections.sum(axis=1))]
        r['comparative_opposite_qids'] = sorted(physical[j]['qid'] for j in support(best))

    summary = dict(
        unit_weight=w, archive=archive, exhaustive_physical_errors=len(errors), syndromes=512,
        reference_comparisons=1536, max_reference_error=worst_error,
        even_swim_syndromes=int(even.sum()),
        even_swim_counts={str(k):int(v) for k,v in pd.Series(np.rint(scalar[even]).astype(int)).value_counts().items()},
        even_swim_also_hard_selected=int(np.count_nonzero(even & np.isclose(scalar,extra['selected_swim_distance']/w))),
        comparative_nonoptimal_classes=int(np.count_nonzero(comp_counts != class_min)),
        comparative_gap_mismatches=int(np.count_nonzero(~np.isclose(ce['logical_gaps']/w,exact_gap))),
        examples=examples,
        source_commits={str(p):subprocess.check_output(['git','-C',str(ROOT/p),'rev-parse','HEAD'],text=True).strip()
                        for p in [Path('.'),Path('external_libs/color-code-stim'),Path('external_libs/PyMatching')]})
    (OUT/'audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    pd.DataFrame(rows).to_csv(OUT/'d5_all_syndromes.csv',index=False)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('archive','examples')},indent=2))
    for r in examples:
        print('EXAMPLE', json.dumps({k:v for k,v in r.items() if k!='witness'}))
        print('WITNESS',json.dumps({k:v for k,v in r['witness'].items() if k not in ('edges','edge_qubits','nodes','radii_over_w')}))


if __name__ == '__main__':
    main()
