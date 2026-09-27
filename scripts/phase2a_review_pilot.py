"""Audit saved pilot rows and create review artifacts without further sampling."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from phase2a_diagnostics import retained_curve,binned_ler

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'implementation_artifacts/pilot'
manifest = json.loads((OUT/'manifest.json').read_text())
summary = json.loads((OUT/'summary.json').read_text())
rows = list(csv.DictReader((OUT/'shots.csv').open()))
assert len(rows) == len(summary)*manifest['config']['shots']
assert len({r['shot_id'] for r in rows}) == len(rows)
assert manifest['script_sha256'] == hashlib.sha256((ROOT/'scripts/phase2a_pilot.py').read_bytes()).hexdigest()
assert manifest['diagnostics_sha256'] == hashlib.sha256((ROOT/'scripts/phase2a_diagnostics.py').read_bytes()).hexdigest()
for name,key in [('PyMatching','pymatching_sha'),('color-code-stim','color_code_stim_sha')]:
    assert {r[key] for r in rows} == {manifest['repositories'][name]}
for s in summary:
    group = [r for r in rows if int(r['d']) == s['d'] and float(r['p']) == s['p']]
    scores = np.array([float(r['selected_phi']) for r in group])
    failures = np.array([int(r['failure']) for r in group],dtype=bool)
    cmp_scores = np.array([float(r['comparative_logical_gap']) for r in group])
    cmp_failures = np.array([int(r['comparative_failure']) for r in group],dtype=bool)
    assert int(failures.sum()) == s['failures']
    assert int(cmp_failures.sum()) == s['comparative_failures']
    for r in group:
        assert int(r['failure']) == (r['actual_observable'] != r['predicted_observable'])
        assert int(r['comparative_failure']) == (r['actual_observable'] != r['comparative_prediction'])
        assert float(r['selected_phi']) == float(r['phi_'+r['best_color']])
        for c in 'rgb': assert np.isfinite(float(r['phi_'+c])) and float(r['phi_'+c]) >= 0
    assert retained_curve(scores,failures,manifest['config']['acceptance_fractions']) == s['retained_curve']
    assert retained_curve(cmp_scores,cmp_failures,manifest['config']['acceptance_fractions']) == s['comparative_curve']
    assert binned_ler(scores,failures) == s['bins']

fig,ax = plt.subplots(figsize=(8,4),constrained_layout=True)
labels = [f'd={s["d"]}, p={s["p"]}' for s in summary]
for i,c in enumerate('rgb'):
    values = [s['stage2_timing'][i]['incremental_us_per_shot'] for s in summary]
    ax.bar(np.arange(len(summary))+(i-1)*.24,values,width=.24,label=c)
ax.set_xticks(range(len(summary)),labels,rotation=20)
ax.set(ylabel='Additional microseconds / stage-2 shot',title='Pilot timing: same configured matcher, median of 3 runs')
ax.legend(title='Color')
fig.savefig(OUT/'runtime_overhead.png',dpi=150)
plt.close(fig)
disagreements = sum(r['predicted_observable'] != r['comparative_prediction'] for r in rows)
text = '''# Phase-2A pilot review

All M0–M5 correctness gates were completed before sampling. This is a
pipeline pilot using an explicitly named, uncertified growth convention;
it is not posterior calibration or a full-decoder logical-gap theorem.

3072 paired physical shots: 512 each at d=3,5,7 and p=0.01,0.05,
rounds=1, triangular Z-memory, data-only bit-flip noise. Ordinary SO-off/on
predictions, weights, best colors and failure masks matched for every shot.
All three per-color swim values were finite and nonnegative.

| d | p | Ordinary failures / 512 | Comparative failures / 512 |
|---|---|---|---|
'''
for s in summary:
    text += f'| {s["d"]} | {s["p"]} | {s["failures"]} | {s["comparative_failures"]} |\n'
text += f'''
The decoders differ on {disagreements} individual hard predictions even though their
failure totals agree within each pilot configuration. Their failure labels
are kept separate. Pairing uses the identical physical measurement record;
the extra comparative detector is the ordinary observable parity and is
overwritten by the decoder's forced-class inputs. Tests confirm that flipping
its supplied actual value does not affect comparative decoding.

At p=0.05, d=5 and d=7, the comparative ranking retains fewer observed failures
at some matched acceptance fractions. These small failure counts do not
establish superiority or calibration. Successful shots have larger median
selected swim than failed shots in all configurations with observed failures.
The d=7, p=0.01 configuration has zero observed failures; it supplies no
failure-conditioned distribution. Raw score ties use stable shot order,
independent of failure labels; tiny floating-point differences are not
rounded into ties. Acceptance curves include partial selection within exact
ties, rather than being restricted to unique score thresholds.

The isolated stage-2 timings use the same configured matcher/input, excluding
setup and stage 1 in both measurements. Incremental overhead ranges from
about 0.6 to 4.4 microseconds per color/shot on this machine. These small
measurements are pipeline diagnostics, not scaling or negligible-overhead
claims. End-to-end timings also record ordinary reconstruction versus cached
SO operation separately; that difference must not be interpreted as pure
metric overhead. Peak RSS is cumulative process RSS, not per-matcher memory.

The raw CSV, manifest, six diagnostic panels, summary JSON and runtime plot
are retained here. The audit recomputed all failure counts, selected-color
values, binned Wilson statistics and matched-acceptance curves from CSV;
repository hashes and script hashes match the manifest. One diagnostic panel
was visually inspected. Wilson limits are stored for each reported curve
point even where the compact plot omits error bars.

The initial plotting attempt encountered roundoff at a zero-failure Wilson
endpoint. It is preserved in ../pilot_incomplete_plot_error. Exact endpoint
handling and regression tests repaired the plotting issue before rerunning
the same seeded grid. No decoder correctness gate failed.

Stop here for pilot review. No paper-scale campaign was run or authorized.
'''
(OUT/'REVIEW.md').write_text(text)
print(f'Pilot artifact audit passed: {len(rows)} unique paired rows; {disagreements} hard disagreements.')
