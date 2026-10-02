"""Draw the audited physical supports and fractional path costs."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from audit import make_code

OUT = Path(__file__).resolve().parent
data = json.loads((OUT/'audit.json').read_text())
code = make_code()
qubits = {q['qid']: q for q in code.tanner_graph.vs.select(pauli=None)}
pos = {qid: np.array([q['x']/4, q['y']*np.sqrt(3)/2]) for qid,q in qubits.items()}
fig, axs = plt.subplots(2, 2, figsize=(12.6, 8), gridspec_kw={'width_ratios':[1,1.2]})
face_colors = dict(r='#ee8a83', g='#9ad9a6', b='#92bce8')
for row, example in enumerate(data['examples'][:2]):
    left, right = axs[row]
    for check in code.tanner_graph.vs.select(pauli='Z'):
        points = np.array([pos[q['qid']] for q in check.neighbors() if q['pauli'] is None])
        center = points.mean(axis=0)
        points = points[np.argsort(np.arctan2(*(points-center)[:,::-1].T))]
        left.add_patch(Polygon(points, facecolor=face_colors[check['color']], alpha=.28,
                               edgecolor='gray', linewidth=.6))
    path = example['witness']['path_qids']
    left.plot(*np.array([pos[q] for q in path]).T, color='#2878b5', lw=2.8, alpha=.7)
    left.scatter(*np.array(list(pos.values())).T, color='white', edgecolor='#777', s=90,zorder=4)
    for qid,(x,y) in pos.items():
        left.text(x,y+.16,str(qid),ha='center',va='bottom',fontsize=9,zorder=7)
    left.scatter(*np.array([pos[q] for q in path]).T, color='#2878b5',s=42,zorder=5)
    left.scatter(*np.array([pos[q] for q in example['representative_qids']]).T,
                 marker='x',color='#bc2727',s=135,linewidths=2.6,zorder=6)
    left.set_aspect('equal');left.axis('off')
    left.set_title(f"{'AB'[row]}. X errors = correction: {example['representative_qids']}\n"
                   f"Blue: {example['swim_color']}-graph logical witness",fontsize=12)
    witness = example['witness']
    # Reconstruct the interval orientation, starting at the side terminal.
    edges = {e[0]:e for e in witness['edges']}
    from color_code_stim.soft_output.reference import reference_metric
    w = data['unit_weight']
    radii = np.array(witness['radii_over_w'])*w
    ref = reference_metric(len(witness['nodes']), witness['edges'],
                           tuple(witness['terminals']), radii=radii)
    node = witness['terminals'][0]
    for j,eid in enumerate(witness['path_edge_ids']):
        _,u,v,length = edges[eid]
        assert node in (u,v)
        forward = node==u
        node = v if forward else u
        x = j*1.1
        right.add_patch(Rectangle((x,1),1,.6,color='#2878b5'))
        for a,b in ref.coverage[eid]:
            if b-a < 1e-10:continue
            a,b = (a/w,b/w) if forward else (1-b/w,1-a/w)
            right.add_patch(Rectangle((x+a,1),b-a,.6,color='#ef9b36'))
        right.text(x+.5,1.86,f'q{path[j]}',ha='center',fontsize=11)
        right.text(x+.5,.71,f"{witness['path_residual_over_w'][j]:g}w",ha='center',fontsize=11)
    swim=round(example['scalar_swim_over_w'])
    right.text(2.7,2.62,f"SWIM = {len(path)}w - {witness['path_covered_over_w']:g}w = {swim}w",
               ha='center',fontsize=15,fontweight='bold')
    right.text(2.7,2.21,'Orange: covered length    Blue: remaining length',ha='center',fontsize=10)
    right.text(2.7,.15,f"Ordinary r/g/b SWIM: {np.rint(example['swims_over_w']).astype(int).tolist()} w\n"
               f"Final color: {example['final_color']}; SWIM color: {example['swim_color']}\n"
               f"Comparative gap = {example['comparative_gap_over_w']:g}w",
               ha='center',va='top',fontsize=12,linespacing=1.7)
    right.set(xlim=(-.25,5.65),ylim=(-1,3));right.axis('off')
fig.suptitle('Why SWIM takes even multiples of w in the d = 5 bit-flip code\n'
             'w = ln((1-p)/p); p = 0.04; qubit numbers are Stim circuit IDs',fontsize=14)
fig.tight_layout(rect=(0,0,1,.93))
for suffix in ['png','pdf']:
    fig.savefig(OUT/f'examples_selected.{suffix}',dpi=180,bbox_inches='tight')
plt.close(fig)
