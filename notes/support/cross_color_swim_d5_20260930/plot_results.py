"""Figures and complete Markdown tables from the exhaustive experiment."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
table = pd.read_csv(OUT/'summary.csv')
detail = json.loads((OUT/'details_p0.04.json').read_text())
methods = {
    'baseline': 'Current SWIM',
    'coverage_max': 'Share maximum coverage',
    'witness_coverage_max': 'Share coverage on witnesses',
    'intersection_zero': 'Zero witness intersections',
    'rescore_original3': 'Rescore 3 physical paths',
    'rescore_union6_odd_xor_all_anchors': '6-path odd XOR + 3 anchors',
    'rescore_original3_one_face': '3 paths + at most 1 face *',
    'rescore_original3_two_faces': '3 paths + at most 2 faces',
    'rescore_all_shortest_two_faces': 'All tied paths + at most 2 faces',
}
fig, axes = plt.subplots(1, 2, figsize=(14, 6.8), gridspec_kw={'width_ratios': [1.2, 1]})
y = np.arange(len(methods))
for i,p in enumerate((.02,.04)):
    selected = table[table.p==p].set_index('method').loc[list(methods)]
    axes[0].barh(y+(i-.5)*.32, 100*selected.probability_equal, height=.3,
                 color=['#7aaed1','#235b86'][i],label=f'p = {p:g}')
axes[0].set(yticks=y, yticklabels=list(methods.values()), xlim=(0,106),
            xlabel='Exact agreement with comparative gap (%)')
axes[0].invert_yaxis()
fig.legend(*axes[0].get_legend_handles_labels(), loc='upper center',
           bbox_to_anchor=(.58,.925), ncol=2, frameon=False)
selected = table[table.p==.04].set_index('method').loc[list(methods)]
axes[1].barh(y, selected.weighted_mae_w, color='#d88646',height=.55)
for i,value in enumerate(selected.weighted_mae_w):
    axes[1].text(value+.01, i, f'{value:.4f}', va='center',fontsize=10)
axes[1].set(yticks=y, yticklabels=['']*len(y),xlim=(0,.89),
            xlabel='Mean absolute error / w (p = 0.04)')
axes[1].invert_yaxis()
for ax in axes:
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='x',alpha=.18)
    ax.set_axisbelow(True)
fig.suptitle('Cross-color SWIM strategies: all 512 syndromes of d = 5',fontsize=15)
fig.text(.5,.025,'Exact physical-probability weighting over all 524,288 X-error patterns.\n'
         '* One-face scalar gaps all agree, but one syndrome has the wrong class-weight ordering.',
         ha='center',fontsize=10,linespacing=1.6)
fig.tight_layout(rect=(0,.11,1,.87))
for ext in ('pdf','png'):
    fig.savefig(OUT/f'comparison.{ext}',dpi=200,bbox_inches='tight')
plt.close(fig)

fig, axes = plt.subplots(2, 1, figsize=(14, 6.4))
for ax,sid,label in zip(axes,['88','54'],['A: central error {20}', 'B: two errors {16,17}']):
    record=detail['witness_examples'][sid]
    qs=sorted(map(int,record['original_residuals_by_qid']))
    costs=np.array([record['original_residuals_by_qid'][str(q)] for q in qs]).T
    costs=np.row_stack([costs,[record['transferred_residuals_by_qid'][str(q)] for q in qs]])
    ax.imshow(costs,cmap='Blues',vmin=0,vmax=1,aspect='auto')
    for i in range(4):
        for j in range(len(qs)):
            ax.text(j,i,f'{costs[i,j]:g}',ha='center',va='center',fontsize=10,
                    color='white' if costs[i,j]>.7 else '#222222')
    ax.set(xticks=np.arange(len(qs)),xticklabels=[f'q{q}' for q in qs],
           yticks=range(4),yticklabels=['r','g','b','Transferred'],title=label)
    ax.tick_params(length=0)
fig.suptitle('Residual edge weights / w before and after maximum-coverage transfer',fontsize=14)
fig.text(.5,.015,'Each column identifies the same physical qubit in all three graphs.\n'
         'Transferred residual = min(r, g, b); 0 means fully covered, 1 means uncovered.',
         ha='center',fontsize=10,linespacing=1.5)
fig.tight_layout(rect=(0,.12,1,.94),h_pad=2)
for ext in ('pdf','png'):
    fig.savefig(OUT/f'coverage_transfer.{ext}',dpi=200,bbox_inches='tight')
plt.close(fig)

# Markdown table is generated solely from saved measurements.
columns=['method','equal_syndromes','probability_equal','weighted_mae_w','weighted_order_error','zero_syndromes']
lines=['# 全戦略の比較表','',
       '一致確率・MAE・順位誤差は全物理エラーの確率で重み付けした値。MAE の単位は w。',
       '順位誤差は真の gap が異なる2ショットについて逆転を1、同点を0.5と数える。','']
for p in (.02,.04):
    lines += [f'## p が {p:g} の場合','',
              '| 戦略 | 一致 / 512 | 一致確率 | MAE / w | 順位誤差 | ゼロ値の数 |',
              '|---|---:|---:|---:|---:|---:|']
    for r in table[table.p==p].itertuples():
        lines.append(f'| `{r.method}` | {r.equal_syndromes} | {r.probability_equal:.8f} | {r.weighted_mae_w:.8f} | {r.weighted_order_error:.8f} | {r.zero_syndromes} |')
    lines.append('')
(OUT/'all_strategies.md').write_text('\n'.join(lines)+'\n')
print('Wrote comparison/coverage PDF and PNG, and full strategy tables.')
