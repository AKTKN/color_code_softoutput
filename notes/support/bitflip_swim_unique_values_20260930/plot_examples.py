"""Plot six verified color witnesses on two overlaid physical patches."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon, Rectangle, Wedge, FancyArrowPatch
from audit import make_code
from color_code_stim.soft_output.reference import reference_metric
from color_code_stim.soft_output.topology import physical_error_map

OUT = Path(__file__).resolve().parent
COLORS = {'r': '#c73642', 'g': '#23824b', 'b': '#266cb5'}
STYLES = {'r': '-', 'g': '--', 'b': ':'}
COVERED = '#f3b557'


def collect_witnesses(code, data):
    manager = code.dem_manager
    physical = physical_error_map(manager)
    examples = data['examples'][:2]
    syndromes = np.zeros((2, manager.H.shape[0]), dtype=bool)
    for i, example in enumerate(examples):
        syndromes[i, example['detectors']] = True
    predictions, extra = code.decode(syndromes, compute_swim_distance=True,
                                     full_output=True, return_candidate_data=True,
                                     check_validity=True)
    w = data['unit_weight']
    output = [{**e, 'witnesses': {}} for e in examples]
    for ci, color in enumerate('rgb'):
        backend = code.concat_matching_decoder._swim_backends[color]
        topology = backend.topology
        s2 = syndromes.copy()
        s2[:, [j for j in range(s2.shape[1])
               if j not in manager.detector_ids_by_color[color]]] = False
        s2 = np.column_stack([s2, extra['candidate_stage1_hypotheses'][0][ci]])
        decoded = backend.matcher.decode_batch_with_soft_output(s2, include_radii=True)
        edge_meta = {edge.column_id: edge for edge in topology.edges}
        edges = {edge[0]: edge for edge in topology.resolved_edges}
        for i, example in enumerate(examples):
            ref = reference_metric(len(backend.config.node_map), topology.resolved_edges,
                                   topology.terminals, radii=decoded.radii[i])
            np.testing.assert_allclose(ref.distance, decoded.soft_outputs[i, 0], atol=1e-11)
            np.testing.assert_allclose(ref.distance/w, example['swims_over_w'][ci], atol=1e-11)
            path = np.zeros(len(topology.edges), dtype=np.uint8)
            path[list(ref.edge_ids)] = 1
            original = manager.dems_decomposed[color].map_errors_to_org_dem(path[None], stage=2)[0]
            assert not np.any(manager.H @ original.astype(np.uint8) % 2)
            assert int((manager.obs_matrix @ original.astype(np.uint8))[0] % 2) == 1
            intervals = []
            node = topology.terminals[0]
            for eid in ref.edge_ids:
                _, u, v, length = edges[eid]
                assert node in (u, v)
                forward = node == u
                node = v if forward else u
                intervals.append([
                    [a/w, b/w] if forward else [(length-b)/w, (length-a)/w]
                    for a, b in ref.coverage[eid] if b-a > 1e-10])
            assert node == topology.terminals[1]
            residuals = [ref.residual_weights[j]/w for j in ref.edge_ids]
            np.testing.assert_allclose(sum(residuals), ref.distance/w, atol=1e-11)
            correction = extra['candidate_original_corrections'][0, ci, i]
            qids = sorted(physical[j]['qid'] for j in np.flatnonzero(correction))
            assert qids == example['candidate_qids'][ci]
            output[i]['witnesses'][color] = dict(
                color=color, path_qids=[edge_meta[j].physical_qubit_id for j in ref.edge_ids],
                path_edge_ids=list(ref.edge_ids), residuals_over_w=residuals,
                covered_intervals_over_w=intervals,
                covered_length_over_w=len(ref.edge_ids)-sum(residuals),
                swim_over_w=ref.distance/w, correction_qids=qids,
                stage2_defect_rows=np.flatnonzero(s2[i]).tolist(),
                radii_over_w=(decoded.radii[i]/w).tolist(),
                node_map=list(backend.config.node_map), final_class=int(predictions[i]))
    return output


def draw_patch(ax, code, pos, example, letter):
    for check in code.tanner_graph.vs.select(pauli='Z'):
        points = np.array([pos[q['qid']] for q in check.neighbors() if q['pauli'] is None])
        center = points.mean(axis=0)
        angles = np.arctan2((points-center)[:, 1], (points-center)[:, 0])
        ax.add_patch(Polygon(points[np.argsort(angles)], facecolor=COLORS[check['color']],
                            alpha=.10, edgecolor='#777777', linewidth=.7))
    segments = defaultdict(list)
    for color, witness in example['witnesses'].items():
        path = witness['path_qids']
        for q0, q1 in zip(path[:-1], path[1:]):
            segments[tuple(sorted((q0, q1)))].append(color)
    # Fan shared segments symmetrically so no color disappears underneath.
    for (q0, q1), colors in segments.items():
        for slot, color in enumerate(colors):
            curvature = (slot-(len(colors)-1)/2)*.18
            ax.add_patch(FancyArrowPatch(
                pos[q0], pos[q1], arrowstyle='-', shrinkA=0, shrinkB=0,
                connectionstyle=f'arc3,rad={curvature}', color=COLORS[color],
                linestyle=STYLES[color], linewidth=2.6, zorder=3))
    for qid, xy in pos.items():
        ax.scatter(*xy, color='white', edgecolor='#999999', s=70, zorder=4)
        for ci, color in enumerate('rgb'):
            if qid in example['witnesses'][color]['path_qids']:
                ax.add_patch(Wedge(xy, .12, 90+120*ci, 210+120*ci,
                                   width=.062, color=COLORS[color], zorder=5))
        ax.text(xy[0], xy[1]+.19, str(qid), ha='center', va='bottom', fontsize=10,
                zorder=7, path_effects=[pe.withStroke(linewidth=2.5, foreground='white')])
    ax.scatter(*np.array([pos[q] for q in example['representative_qids']]).T,
               marker='x', color='#161616', s=160, linewidths=3, zorder=8,
               path_effects=[pe.withStroke(linewidth=5, foreground='white')])
    ax.set_aspect('equal')
    ax.set(xlim=(-.38, 6.38), ylim=(-.5, 5.95))
    ax.axis('off')
    ax.set_title(f"{letter}. X errors = correction: {example['representative_qids']}\n"
                 'All three color witnesses on the same patch', fontsize=13, pad=9)
    phi = example['scalar_swim_over_w']
    mins = '/'.join(color for color, a in example['witnesses'].items()
                    if np.isclose(a['swim_over_w'], phi))
    ax.text(.5, -.02, f"Final correction: {example['final_color']}   |   SWIM minimum: {mins}\n"
            f"Saved SWIM = {phi:g}w   |   Comparative gap = {example['comparative_gap_over_w']:g}w",
            transform=ax.transAxes, ha='center', va='top', fontsize=11, linespacing=1.8)


def draw_strips(ax, example):
    for ci, color in enumerate('rgb'):
        witness = example['witnesses'][color]
        y = 6.0-2.65*ci
        path = witness['path_qids']
        phi = witness['swim_over_w']
        coverage = witness['covered_length_over_w']
        ax.text(0, y+1.4, f"{color.upper()}   SWIM = {len(path)}w - {coverage:g}w = {phi:g}w",
                fontsize=14, color=COLORS[color], fontweight='bold')
        for j, qid in enumerate(path):
            x = j*1.13
            ax.add_patch(Rectangle((x, y), 1, .52, color=COLORS[color], zorder=1))
            for a, b in witness['covered_intervals_over_w'][j]:
                ax.add_patch(Rectangle((x+a, y), b-a, .52, facecolor=COVERED,
                                      edgecolor='#a77529', linewidth=.35, hatch='////', zorder=2))
            ax.add_patch(Rectangle((x, y), 1, .52, fill=False, edgecolor='#777777', linewidth=.5, zorder=3))
            ax.text(x+.5, y+.77, f'q{qid}', ha='center', fontsize=11)
            ax.text(x+.5, y-.35, f"{witness['residuals_over_w'][j]:g}w", ha='center', fontsize=11)
    ax.set(xlim=(-.1, 5.75), ylim=(-.1, 8.0))
    ax.axis('off')


def main():
    data = json.loads((OUT/'audit.json').read_text())
    code = make_code()
    examples = collect_witnesses(code, data)
    (OUT/'examples_all_colors.json').write_text(json.dumps(
        {'unit_weight': data['unit_weight'], 'examples': examples,
         'note': 'One minimizing witness per color; paths may be degenerate.'}, indent=2)+'\n')
    pos = {q['qid']: np.array([q['x']/4, q['y']*np.sqrt(3)/2])
           for q in code.tanner_graph.vs.select(pauli=None)}
    fig, axs = plt.subplots(2, 2, figsize=(14.5, 14.5),
                            gridspec_kw={'width_ratios': [1, 1.22]})
    for row, example in enumerate(examples):
        draw_patch(axs[row, 0], code, pos, example, 'AB'[row])
        draw_strips(axs[row, 1], example)
    fig.suptitle('SWIM witnesses for all three colors in the d = 5 bit-flip code\n'
                 'Two error configurations, six paths; w = ln((1-p)/p), p = 0.04',
                 fontsize=16, y=.985, linespacing=1.6)
    handles = [Line2D([], [], color=COLORS[c], linestyle=STYLES[c], lw=2.6,
                      label=f'{c}-graph witness / residual') for c in 'rgb']
    handles.extend([
        Rectangle((0, 0), 1, 1, facecolor=COVERED, edgecolor='#a77529', hatch='////', label='Cluster-covered (free)'),
        Line2D([], [], marker='x', color='#161616', linestyle='None', markersize=9, markeredgewidth=2, label='X error / correction')])
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .925),
               ncol=3, frameon=False, fontsize=11, columnspacing=2.2, handlelength=3)
    fig.subplots_adjust(left=.045, right=.98, bottom=.12, top=.835, hspace=.40, wspace=.14)
    fig.text(.5, .025, 'Qubit labels are Stim circuit IDs. One minimizing path per color is shown.\n'
             'Patch lines connect ordered witness qubits; they do not represent physical interaction bonds.',
             ha='center', fontsize=10, color='#555555', linespacing=1.6)
    for suffix in ['png', 'pdf']:
        fig.savefig(OUT/f'examples.{suffix}', dpi=200, bbox_inches='tight')
    plt.close(fig)
    for i, example in enumerate(examples):
        print('AB'[i], {color: {'path': a['path_qids'], 'SWIM/w': round(a['swim_over_w'], 8)}
                        for color, a in example['witnesses'].items()})
    print('All six witnesses verified; wrote examples.pdf, examples.png, examples_all_colors.json')


if __name__ == '__main__':
    main()
