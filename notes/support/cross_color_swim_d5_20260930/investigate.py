"""Deterministic d=5 cross-color SWIM study, independent physical oracle.

All algorithm scores use only ordinary decoder products and physical weights.
The comparative decoder and exhaustive oracle enter evaluation only.
No production decoder, notebook, or saved experiment is changed.
"""
from pathlib import Path
from heapq import heappop, heappush
from itertools import combinations
import json
import sys
import hashlib
import subprocess

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(OUT.parent/'bitflip_swim_unique_values_20260930'))
from audit import make_code
from color_code_stim.soft_output.reference import reference_metric
from color_code_stim.soft_output.topology import physical_error_map


def bits_mask(bits):
    return sum(1 << int(j) for j in np.flatnonzero(bits))


def shortest(edges, terminals, weights):
    """Nonnegative Dijkstra with deterministic node and original edge order."""
    adjacency = [[] for _ in range(max(max(u, v) for _, u, v, _ in edges)+1)]
    for eid, u, v, _ in edges:
        assert weights[eid] >= -1e-10
        adjacency[u].append((v, eid, max(0., weights[eid])))
        adjacency[v].append((u, eid, max(0., weights[eid])))
    source, target = terminals
    distances = [np.inf]*len(adjacency)
    distances[source] = 0.
    queue = [(0., source)]
    prev = {}
    while queue:
        distance, u = heappop(queue)
        if distance != distances[u]:
            continue
        if u == target:
            break
        for v, eid, weight in adjacency[u]:
            new = distance+weight
            if new < distances[v]-1e-12:
                distances[v] = new
                prev[v] = (u, eid)
                heappush(queue, (new, v))
    u, path = target, []
    while u != source:
        u, eid = prev[u]
        path.append(eid)
    return distances[target], tuple(reversed(path))


def simple_paths(edges, terminals):
    adj = [[] for _ in range(max(max(u, v) for _, u, v, _ in edges)+1)]
    for eid, u, v, _ in edges:
        adj[u].append((v, eid))
        adj[v].append((u, eid))
    output = []
    def visit(u, seen, path):
        if u == terminals[1]:
            output.append(tuple(path))
            return
        for v, eid in adj[u]:
            if v not in seen:
                visit(v, seen|{v}, [*path, eid])
    visit(terminals[0], {terminals[0]}, [])
    return sorted(output)


def oracle(manager):
    """All physical error configurations, also their weight enumerators."""
    n = manager.H.shape[1]
    masks = np.arange(1 << n, dtype=np.uint32)
    errors = ((masks[:, None] >> np.arange(n)) & 1).astype(np.uint8)
    active = np.flatnonzero(manager.H.getnnz(axis=1))
    syndromes = np.asarray(errors @ manager.H[active].T) % 2
    ids = syndromes @ (1 << np.arange(len(active)))
    parity = np.asarray(errors @ manager.obs_matrix.T).ravel() % 2
    weights = errors.sum(axis=1).astype(int)
    enumerator = np.zeros((512, 2, n+1), dtype=np.int64)
    np.add.at(enumerator, (ids, parity, weights), 1)
    class_min = np.full((512, 2), n+1, dtype=int)
    np.minimum.at(class_min, (ids, parity), weights)
    assert np.all(np.abs(class_min[:, 1]-class_min[:, 0]) % 2 == 1)
    representatives = np.full(512, 1 << n, dtype=int)
    keep = weights == class_min.min(axis=1)[ids]
    np.minimum.at(representatives, ids[keep], masks[keep])
    return enumerator, class_min, representatives, errors, ids, parity


def compute(p, truth, representative_masks, errors, error_syndromes, error_parities):
    code = make_code(p=p)
    manager = code.dem_manager
    phy = physical_error_map(manager)
    n = manager.H.shape[1]
    observable_mask = bits_mask(manager.obs_matrix.toarray()[0])
    def logical_parity(mask):
        return (mask & observable_mask).bit_count() % 2
    active = np.flatnonzero(manager.H.getnnz(axis=1))
    syndromes = np.zeros((512, manager.H.shape[0]), dtype=bool)
    syndromes[:, active] = (np.arange(512)[:, None] >> np.arange(9)) & 1
    pred, extra = code.decode(syndromes, full_output=True, compute_swim_distance=True,
                             return_candidate_data=True, check_validity=True)
    comp = make_code(p=p, comparative=True)
    np.testing.assert_array_equal(comp.dem_manager.H.toarray()[:-1], manager.H.toarray())
    cpred, ce = comp.decode(np.column_stack([syndromes, np.zeros(512, dtype=bool)]),
                           full_output=True, return_candidate_data=True, check_validity=True)
    comp_weights = ce['candidate_original_corrections'].sum(axis=-1).min(axis=1).T
    np.testing.assert_array_equal(comp_weights, truth)
    w = np.log((1-p)/p)
    np.testing.assert_allclose(ce['logical_gaps']/w, abs(truth[:, 1]-truth[:, 0]), atol=1e-9)
    candidates = extra['candidate_original_corrections'][0]
    classes = np.asarray(candidates.reshape(-1, n).astype(np.uint8) @ manager.obs_matrix.T).reshape(3, 512) % 2
    final = [bits_mask(x) for x in extra['error_preds']]
    np.testing.assert_array_equal([x.bit_count() for x in final], truth[np.arange(512), pred.astype(int)])
    topologies, mappings, residuals, native_paths, paths_all = [], [], [], [], []
    max_ref_error, snap_error = 0., 0.
    for ci, color in enumerate('rgb'):
        backend = code.concat_matching_decoder._swim_backends[color]
        topo = backend.topology
        mapping = np.array([e.original_dem_ids[0] for e in topo.edges], dtype=int)
        assert sorted(mapping.tolist()) == list(range(n))
        s2 = syndromes.copy()
        s2[:, [j for j in range(s2.shape[1]) if j not in manager.detector_ids_by_color[color]]] = False
        s2 = np.column_stack([s2, extra['candidate_stage1_hypotheses'][0][ci]])
        decoded = backend.matcher.decode_batch_with_soft_output(s2, include_radii=True)
        residual = np.zeros((512, n))
        native = []
        for si in range(512):
            ref = reference_metric(len(backend.config.node_map), topo.resolved_edges,
                                   topo.terminals, radii=decoded.radii[si])
            max_ref_error = max(max_ref_error, abs(ref.distance/w-extra['swim_distances_by_color'][si, ci]/w))
            raw = np.array([ref.residual_weights[j]/w for j in range(n)])
            rounded = np.round(raw, 12)
            snap_error = max(snap_error, float(np.max(abs(raw-rounded))))
            residual[si, mapping] = rounded
            native.append(sum(1 << int(mapping[eid]) for eid in ref.edge_ids))
        topologies.append(topo)
        mappings.append(mapping)
        residuals.append(residual)
        native_paths.append(native)
        allp = simple_paths(topo.resolved_edges, topo.terminals)
        for path in allp:
            mask = sum(1 << int(mapping[eid]) for eid in path)
            assert error_syndromes[mask] == 0 and error_parities[mask] == 1
        paths_all.append(allp)
    residuals = np.array(residuals)
    # Face stabilizers for a bounded, strictly-decreasing local polish.
    by_qid = {q['qid']: col for col, q in phy.items()}
    face_masks = sorted(set(sum(1 << by_qid[q['qid']] for q in check.neighbors() if q['pauli'] is None)
                            for check in code.tanner_graph.vs.select(pauli='X')))
    assert len(face_masks) == 9
    assert all(error_syndromes[x] == 0 and error_parities[x] == 0 for x in face_masks)
    face_products = {}
    for depth in (2, 3):
        group = {0: ()}
        for size in range(1, depth+1):
            for faces in combinations(face_masks, size):
                group[int(np.bitwise_xor.reduce(faces))] = faces
        face_products[depth] = group

    scores, signed_scores, records, witnesses = {}, {}, [], {}
    families_per_shot = {}
    tie_checks = []
    def save(name, value):
        scores.setdefault(name, []).append(float(value))
    def qids(mask):
        return sorted(phy[j]['qid'] for j in range(n) if mask >> j & 1)
    for si in range(512):
        eligible = classes[:, si] == pred[si]
        orig = residuals[:, si]
        cand_masks = [bits_mask(candidates[ci, si]) for ci in range(3)]
        baseline = extra['class_min_swim_distance'][si]/w
        save('baseline', baseline)
        save('hard_selected', extra['selected_swim_distance'][si]/w)
        save('median_eligible', np.median(extra['swim_distances_by_color'][si, eligible]/w))
        save('odd_floor', max(1., 2*np.floor((baseline+1e-9-1)/2)+1))
        save('odd_ceil', max(1., 2*np.ceil((baseline-1e-9-1)/2)+1))
        paths_by_method = {}
        costs_by_method = {}
        def run_graphs(name, physical_costs):
            pathmasks, distances = [], []
            for ci in range(3):
                local = physical_costs[ci, mappings[ci]]
                distance, path = shortest(topologies[ci].resolved_edges, topologies[ci].terminals, local)
                # Enumerating 15 paths independently validates every Dijkstra value.
                expected = min(sum(local[j] for j in pp) for pp in paths_all[ci])
                assert abs(distance-expected) < 1e-9
                mask = sum(1 << int(mappings[ci][j]) for j in path)
                assert error_syndromes[mask] == 0 and error_parities[mask] == 1
                pathmasks.append(mask)
                distances.append(distance)
            paths_by_method[name] = pathmasks
            costs_by_method[name] = distances
            save(name, min(x for x, ok in zip(distances, eligible) if ok))
        run_graphs('original_graph', orig)
        assert abs(scores['original_graph'][-1]-baseline) < 1e-9
        shared = orig.min(axis=0)
        run_graphs('coverage_max', np.tile(shared, (3, 1)))
        run_graphs('coverage_same_class', np.minimum(orig, orig[eligible].min(axis=0)))
        run_graphs('coverage_mean', np.tile(orig.mean(axis=0), (3, 1)))
        run_graphs('coverage_median', np.tile(np.median(orig, axis=0), (3, 1)))
        run_graphs('coverage_min', np.tile(orig.max(axis=0), (3, 1)))
        for alpha in (.25, .5, .75):
            run_graphs(f'coverage_blend_{alpha}', (1-alpha)*orig+alpha*shared)
        base_paths = paths_by_method['original_graph']
        path_cover = np.ones((3, n))
        for ci, path in enumerate(base_paths):
            for j in range(n):
                if path >> j & 1:
                    path_cover[ci, j] = orig[ci, j]
        run_graphs('witness_coverage_max', np.minimum(orig, path_cover.min(axis=0)))
        intersect = np.array([sum((path >> j) & 1 for path in base_paths) >= 2 for j in range(n)])
        intersection_costs = orig.copy()
        intersection_costs[:, intersect] = 0
        run_graphs('intersection_zero', intersection_costs)
        # Ordinary physical correction erased, followed by physical rescoring.
        erased = np.array([1-((final[si] >> j) & 1) for j in range(n)], dtype=float)
        run_graphs('correction_erased', np.tile(erased, (3, 1)))

        families = {
            'rescore_native3': [native_paths[ci][si] for ci in range(3)],
            'rescore_original3': base_paths,
            'rescore_transferred3': paths_by_method['coverage_max'],
            'rescore_union6': base_paths+paths_by_method['coverage_max'],
            'rescore_erased3': paths_by_method['correction_erased'],
        }
        families['rescore_original3_xor'] = base_paths+[base_paths[0]^base_paths[1]^base_paths[2]]
        union = sorted(set(families['rescore_union6']))
        families['rescore_union6_odd_xor'] = [
            int(np.bitwise_xor.reduce(combo))
            for count in range(1, len(union)+1, 2) for combo in combinations(union, count)]
        for k in (1, 2, 3, 5, 15):
            selected = []
            for ci in range(3):
                local = orig[ci, mappings[ci]]
                ranked = sorted(paths_all[ci], key=lambda path: (sum(local[j] for j in path), path))
                selected.extend(sum(1 << int(mappings[ci][j]) for j in path) for path in ranked[:k])
            families[f'rescore_k{k}'] = selected
        ties = []
        ties_per_color = []
        for ci in range(3):
            local = orig[ci, mappings[ci]]
            costs = np.array([sum(local[j] for j in path) for path in paths_all[ci]])
            color_ties = [sum(1 << int(mappings[ci][j]) for j in path)
                          for path, cost in zip(paths_all[ci], costs) if np.isclose(cost, costs.min(), atol=1e-9)]
            ties.extend(color_ties)
            ties_per_color.append(color_ties)
        families['rescore_all_shortest'] = ties

        # Exact sensitivity to independently choosing ANY minimizing simple
        # path in each of the three original residual graphs. Hard correction
        # is fixed. This diagnostic does not choose a production candidate.
        other_candidates = [x for x in cand_masks if logical_parity(x) != pred[si]]
        other_existing = min([(x ^ face).bit_count() for x in other_candidates
                              for face in [0, *face_masks]]+[100])
        outcomes = [[min((final[si] ^ path ^ face).bit_count() for face in [0, *face_masks])
                     for path in color_paths] for color_paths in ties_per_color]
        best_op = min(other_existing, *(min(a) for a in outcomes))
        worst_op = min(other_existing, *(max(a) for a in outcomes))
        tie_checks.append(dict(syndrome_id=si, shortest_path_counts=[len(x) for x in ties_per_color],
                               best_opposite_weight=best_op, worst_opposite_weight=worst_op,
                               exact_opposite_weight=int(truth[si, 1-int(pred[si])])))
        for depth in (2, 3):
            other_existing_depth = min([(x ^ face).bit_count() for x in other_candidates
                                        for face in face_products[depth]]+[100])
            values = [[min((final[si] ^ path ^ face).bit_count() for face in face_products[depth])
                       for path in color_paths] for color_paths in ties_per_color]
            tie_checks[-1][f'worst_opposite_weight_{depth}_faces'] = min(other_existing_depth, *(max(a) for a in values))

        # Each family is scored both about the fixed final correction alone,
        # and using all three ordinary corrections as anchors.
        def evaluate_pool(name, paths, all_anchors=False, polish=False):
            anchors = cand_masks if all_anchors else [final[si]]
            pool = set(cand_masks)
            for path in paths:
                assert error_syndromes[path] == 0 and error_parities[path] == 1
                pool.update(anchor ^ path for anchor in anchors)
            polish_traces = []
            if polish:
                refined = set()
                for correction in sorted(pool):
                    start = correction
                    flips = []
                    while True:
                        depth = {'two_faces':2, 'three_faces':3}.get(polish)
                        group = face_products[depth] if depth else {0: (), **{face:(face,) for face in face_masks}}
                        choices = [correction ^ face for face in group]
                        best = min(choices, key=lambda mask: (mask.bit_count(), mask))
                        if best.bit_count() >= correction.bit_count():
                            break
                        flips.extend(qids(face) for face in group[best ^ correction])
                        correction = best
                        if polish == 'one_step' or depth:
                            break
                    refined.add(correction)
                    if flips:
                        polish_traces.append(dict(start_qids=qids(start), face_flips=flips,
                                                  result_qids=qids(correction)))
                pool.update(refined)
            assert all(error_syndromes[x] == si for x in pool)
            best = [min((x for x in pool if logical_parity(x) == parity), key=lambda x: (x.bit_count(), x))
                    for parity in (0, 1)]
            weights = [x.bit_count() for x in best]
            delta = weights[1-int(pred[si])]-weights[int(pred[si])]
            save(name, abs(delta))
            signed_scores.setdefault(name, []).append(delta)
            return dict(path_count=len(set(paths)), correction_count=len(pool),
                        best_qids=[qids(x) for x in best], class_weights=weights,
                        signed_gap_over_w=delta, polish_traces=polish_traces)
        family_info = {}
        for name, paths in families.items():
            family_info[name] = evaluate_pool(name, paths)
        family_info['rescore_union6_all_anchors'] = evaluate_pool('rescore_union6_all_anchors', families['rescore_union6'], True)
        family_info['rescore_union6_face_polish'] = evaluate_pool('rescore_union6_face_polish', families['rescore_union6'], True, True)
        for name, paths, anchors, polish in (
            ('rescore_original3_all_anchors', base_paths, True, False),
            ('rescore_original3_final_face_polish', base_paths, False, True),
            ('rescore_original3_all_face_polish', base_paths, True, True),
            ('rescore_original3_one_face', base_paths, False, 'one_step'),
            ('rescore_union6_one_face', families['rescore_union6'], True, 'one_step'),
            ('rescore_erased3_face_polish', families['rescore_erased3'], False, True),
            ('rescore_all_shortest_one_face', ties, False, 'one_step'),
            ('rescore_original3_two_faces', base_paths, False, 'two_faces'),
            ('rescore_native3_two_faces', families['rescore_native3'], False, 'two_faces'),
            ('rescore_union6_two_faces', families['rescore_union6'], False, 'two_faces'),
            ('rescore_all_shortest_two_faces', ties, False, 'two_faces'),
            ('rescore_original3_three_faces', base_paths, False, 'three_faces'),
            ('rescore_union6_odd_xor_all_anchors', families['rescore_union6_odd_xor'], True, False)):
            family_info[name] = evaluate_pool(name, paths, anchors, polish)
        families_per_shot[si] = family_info
        records.append(dict(p=p, syndrome_id=si, detectors=np.flatnonzero(syndromes[si]).tolist(),
                            representative_qids=qids(int(representative_masks[si])),
                            final_qids=qids(final[si]), final_class=int(pred[si]),
                            comparative_class=int(cpred[si]),
                            final_color='rgb'[int(extra['best_colors'][si])],
                            candidate_qids=[qids(x) for x in cand_masks],
                            candidate_classes=classes[:, si].astype(int).tolist(),
                            exact_class_weights=truth[si].tolist(),
                            target_gap_over_w=int(abs(truth[si, 1]-truth[si, 0]))))
        if si in (0, 54, 88, 340) or pred[si] != cpred[si]:
            witnesses[str(si)] = dict(record=records[-1],
                original_residuals_by_qid={str(phy[j]['qid']): orig[:, j].tolist() for j in range(n)},
                transferred_residuals_by_qid={str(phy[j]['qid']): float(shared[j]) for j in range(n)},
                path_qids={name: [qids(mask) for mask in paths] for name, paths in paths_by_method.items()},
                per_color_costs=costs_by_method, families=family_info)
    score_frame = pd.DataFrame(scores)
    assert (score_frame.coverage_max <= score_frame.baseline+1e-9).all()
    assert (score_frame.intersection_zero <= score_frame.baseline+1e-9).all()
    meta = dict(p=p, reference_error=max_ref_error, normalization_rounding_error=snap_error,
                paths_per_color=[len(x) for x in paths_all],
                ordinary_comparative_disagreements=int(np.count_nonzero(pred != cpred)),
                physical_qubit_columns={str(k):v['qid'] for k,v in phy.items()},
                witness_examples=witnesses,
                family_path_counts={name: [min(a[name]['path_count'] for a in families_per_shot.values()),
                                          max(a[name]['path_count'] for a in families_per_shot.values()),
                                          np.mean([a[name]['path_count'] for a in families_per_shot.values()])]
                                    for name in families_per_shot[0]},
                family_class_weight_mismatches={name: int(sum(np.count_nonzero(np.array(a[name]['class_weights']) != truth[si])
                                                          for si, a in families_per_shot.items()))
                                               for name in families_per_shot[0]},
                family_max_face_flips={name: max([len(t['face_flips'])
                                                 for a in families_per_shot.values()
                                                 for t in a[name]['polish_traces']]+[0])
                                       for name in families_per_shot[0]})
    pd.concat([pd.DataFrame(records), score_frame], axis=1).to_csv(OUT/f'syndromes_p{p:g}.csv', index=False)
    pd.DataFrame(signed_scores).to_csv(OUT/f'signed_gaps_p{p:g}.csv', index=False)
    pd.DataFrame(tie_checks).to_csv(OUT/f'shortest_path_ties_p{p:g}.csv', index=False)
    meta['one_face_any_shortest_tie_wrong_syndromes'] = [a['syndrome_id'] for a in tie_checks
        if a['worst_opposite_weight'] != a['exact_opposite_weight']]
    for depth in (2,3):
        meta[f'{depth}_faces_any_shortest_tie_wrong_syndromes'] = [a['syndrome_id'] for a in tie_checks
            if a[f'worst_opposite_weight_{depth}_faces'] != a['exact_opposite_weight']]
    (OUT/f'details_p{p:g}.json').write_text(json.dumps(meta, indent=2)+'\n')
    return score_frame, pred.astype(int), meta


def main():
    OUT.mkdir(exist_ok=True)
    base = make_code()
    enumerator, truth, reps, errors, ids, parity = oracle(base.dem_manager)
    assert enumerator.sum() == 524288
    np.savez_compressed(OUT/'physical_weight_enumerators.npz', enumerator=enumerator, class_min=truth)
    target = abs(truth[:, 1]-truth[:, 0])
    summary, metadata = [], []
    score_results = {}
    for p in (.02, .04):
        scores, pred, meta = compute(p, truth, reps, errors, ids, parity)
        score_results[p] = scores
        metadata.append(meta)
        probability_by_weight = p**np.arange(20)*(1-p)**(19-np.arange(20))
        joint = np.einsum('slk,k->sl', enumerator, probability_by_weight)
        probability = joint.sum(axis=1)
        np.testing.assert_allclose(probability.sum(), 1., atol=1e-12)
        failures = joint[np.arange(512), 1-pred]
        # Same hard prediction for all strategies. No target values in algorithms.
        np.savez_compressed(OUT/f'syndrome_probabilities_p{p:g}.npz', probability=probability,
                            failure_probability=failures)
        original_error = abs(scores.baseline.to_numpy()-target)
        for method in scores:
            value = scores[method].to_numpy()
            error = value-target
            absolute = abs(error)
            equal = np.isclose(value, target, atol=1e-8)
            improved = absolute < original_error-1e-8
            worsened = absolute > original_error+1e-8
            below = error < -1e-8
            above = error > 1e-8
            # Pair-order agreement conditional on unequal reference gaps.
            reference_order = target[:, None]-target[None, :]
            score_order = value[:, None]-value[None, :]
            pair_weights = probability[:, None]*probability[None, :]
            unequal = reference_order != 0
            discordant = reference_order*score_order < -1e-8
            score_tie = abs(score_order) < 1e-8
            order_error = np.sum(pair_weights*(discordant+.5*(score_tie & unequal)))/np.sum(pair_weights*unequal)
            summary.append(dict(p=p, method=method, equal_syndromes=int(equal.sum()),
                uniform_mae_w=float(absolute.mean()), probability_equal=float(probability@equal),
                weighted_mae_w=float(probability@absolute), weighted_bias_w=float(probability@error),
                under_syndromes=int(below.sum()), over_syndromes=int(above.sum()),
                probability_under=float(probability@below), probability_over=float(probability@above),
                zero_syndromes=int(np.isclose(value, 0).sum()),
                improved_syndromes=int(improved.sum()), worsened_syndromes=int(worsened.sum()),
                probability_improved=float(probability@improved), probability_worsened=float(probability@worsened),
                weighted_order_error=float(order_error), max_absolute_error_w=float(absolute.max()),
                example_88=float(value[88]), example_54=float(value[54]), example_340=float(value[340])))
        print(f'p={p}: all 512 syndromes complete', flush=True)
    frame = pd.DataFrame(summary)
    frame.to_csv(OUT/'summary.csv', index=False)
    core = ['baseline','intersection_zero','coverage_max','witness_coverage_max',
            'coverage_mean','coverage_median','coverage_min','rescore_original3',
            'rescore_union6','rescore_original3_xor','rescore_union6_odd_xor',
            'rescore_all_shortest','rescore_k2','rescore_k3','rescore_k5','rescore_k15',
            'rescore_union6_all_anchors','rescore_union6_face_polish']
    print(frame[(frame.p==.04)&frame.method.isin(core)][['method','equal_syndromes','probability_equal',
          'weighted_mae_w','zero_syndromes','example_88','example_54']].to_string(index=False))
    (OUT/'provenance.json').write_text(json.dumps(dict(
        command='python notes/support/cross_color_swim_d5_20260930/investigate.py',
        scope='d=5, rounds=1, uniform independent X, exact enumeration, no fitting',
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        commits={str(p): subprocess.check_output(['git','-C',str(ROOT/p),'rev-parse','HEAD'],text=True).strip()
                 for p in (Path('.'),Path('external_libs/color-code-stim'),Path('external_libs/PyMatching'))},
        normalized_score_changes_between_p={name:int(np.count_nonzero(~np.isclose(score_results[.02][name],score_results[.04][name])))
                                            for name in score_results[.02]},
        checks=dict(physical_configurations=524288, syndrome_count=512,
                    per_color_reference_checks=3072,
                    dijkstra_checked_against_all_simple_paths=True,
                    all_candidate_syndromes_and_path_parities_checked=True),
        metadata=[{k:v for k,v in m.items() if k!='witness_examples'} for m in metadata]),indent=2)+'\n')


if __name__ == '__main__':
    main()
